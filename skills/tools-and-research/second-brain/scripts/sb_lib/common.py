"""Bundle paths, Markdown parsing, and shared file operations."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import sqlite3
import sys
import tempfile
import textwrap
import unicodedata
import urllib.parse
from pathlib import Path

DB_NAME = "index.db"

RESERVED = {"index.md", "log.md", "schema.md"}

PAGE_FOLDERS = {
    "concept": "concepts", "entity": "entities", "reference": "references",
    "topic": "topics", "playbook": "playbooks",
}

VALID_STATUS = ("draft", "stable", "deprecated")

VALID_TYPES = ("observation", "decision", "insight", "failure", "reference")

VALID_RELEVANCE = ("low", "medium", "high", "critical")

ACTOR = "second-brain/1.0"

LINK_RE = re.compile(
    r"(?<!!)\[(?P<label>(?:\\.|[^\\\]])+)\]\(\s*"
    r"(?P<destination><[^>]+>|[^\s)]+)(?:\s+(?:\"[^\"]*\"|'[^']*'))?\s*\)"
)

WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")

EXTERNAL_SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")

def vault_root() -> Path:
    env = os.environ.get("SECOND_BRAIN_DIR", "").strip()
    return Path(env).expanduser() if env else Path.home() / "second-brain"

def now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def parse_instant(s: str) -> dt.datetime | None:
    try:
        instant = dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
        return instant.replace(tzinfo=dt.timezone.utc) if instant.tzinfo is None else instant
    except ValueError:
        return None

def db_path(vault: Path) -> Path:
    return vault / DB_NAME

def connect(vault: Path, target: Path | None = None) -> sqlite3.Connection:
    con = sqlite3.connect(target or db_path(vault))
    try:
        con.execute(
            "CREATE VIRTUAL TABLE IF NOT EXISTS notes USING fts5("
            "path, title, type, tags, relevance, status, stale_after, verified, body,"
            " tokenize='porter unicode61')"
        )
    except sqlite3.OperationalError as exc:
        con.close()
        sys.exit(f"[sb] FTS5 unavailable ({exc}). Grep fallback: rg -i <term> {vault}")
    return con

def _frontmatter_fields(lines: list[str]) -> dict[str, str]:
    fields: dict[str, str] = {}
    for index, line in enumerate(lines):
        km = re.match(r"^(\w[\w-]*):\s*(.*)$", line.strip())
        if km:
            raw = km.group(2).strip()
            if km.group(1) == "origin_projects" and not raw:
                items = []
                for entry in lines[index + 1:]:
                    item = re.fullmatch(r"\s*-\s+(.+)", entry.rstrip("\r\n"))
                    if not item:
                        break
                    items.append(item.group(1).strip().strip("'\""))
                raw = json.dumps(items)
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                parsed = raw.strip("'\"[]")
            if isinstance(parsed, list):
                parsed = ", ".join(str(value) for value in parsed)
            fields[km.group(1)] = str(parsed)
    return fields

CLI_PATH = Path(__file__).resolve().parent.parent / "sb.py"

def _capture_fields(path: Path) -> dict[str, str]:
    with path.open(encoding="utf-8", errors="replace") as stream:
        if stream.readline().strip() != "---":
            return {}
        header = []
        for line in stream:
            if line.strip() == "---":
                return _frontmatter_fields(header)
            header.append(line)
    return {}

def parse_note(path: Path, vault: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", text, re.S)
    meta, body = (m.group(1), m.group(2)) if m else ("", text)
    fields = _frontmatter_fields(meta.splitlines())
    title_m = re.search(r"^#\s+(.+)$", body, re.M)
    ntype = fields.get("type", "")
    status = "" if ntype == "source" else fields.get("status") or "stable"
    return {
        "path": str(path.relative_to(vault)),
        "title": (title_m.group(1).strip() if title_m else path.stem),
        "type": ntype,
        "tags": fields.get("tags", ""),
        "relevance": fields.get("relevance") or "medium",
        "status": status,
        "stale_after": fields.get("stale_after", ""),
        "verified": _verified_field(fields, meta),
        "capture_scope": fields.get("capture_scope", "unknown"),
        "source_uri": fields.get("source_uri", ""),
        "content_sha256": fields.get("content_sha256", ""),
        "original_sha256": fields.get("original_sha256", ""),
        "body": body.strip(),
    }

def _verified_field(fields: dict[str, str], meta: str) -> str:
    """Read verified as raw text, including flow maps and multiline lists."""
    verified = fields.get("verified", "")
    if "verified" in fields and not verified:
        vm = re.search(r"^verified:\s*\n((?:[ \t]+- .*\n?)+)", meta, re.M)
        if vm:
            verified = vm.group(1)
    return verified

def note_files(vault: Path) -> list[Path]:
    # Current and legacy original archives stay intact and outside knowledge indexes.
    files = [p for p in vault.rglob("*.md") if p.name not in RESERVED
             and p.relative_to(vault).parts[0] not in ("_raw", "raw", ".history")]
    return sorted(files)

def md_links(text: str) -> list[tuple[str, str]]:
    """Markdown file links outside code; external URLs and anchors are filtered."""
    out = []
    for line in markdown_outside_code(text).splitlines():
        for match in LINK_RE.finditer(line):
            target = match.group("destination").strip("<>")
            if not target.startswith("#") and not EXTERNAL_SCHEME_RE.match(target):
                out.append((match.group("label"), target.split("#", 1)[0]))
    return [(label, target) for label, target in out if target]

def _mask_fenced_code(text: str) -> tuple[list[str], bool]:
    fence: tuple[str, int] | None = None
    out = []
    for line in text.splitlines():
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
        if fence is None and marker:
            fence = (marker.group(1)[0], len(marker.group(1)))
            out.append("")
            continue
        if fence is not None:
            closing = re.match(r"^ {0,3}(`+|~+)\s*$", line)
            if closing and closing.group(1)[0] == fence[0] and len(closing.group(1)) >= fence[1]:
                fence = None
            out.append("")
            continue
        out.append(line)
    return out, fence is not None

def markdown_outside_code(text: str) -> str:
    lines, _ = _mask_fenced_code(text)
    return "\n".join(re.sub(r"`+[^`]*`+", "", line) for line in lines)

def resolve_link(vault: Path, src: Path, target: str) -> Path:
    """OKF §6.1: '/x.md' is bundle-relative; other paths are relative to the linking file."""
    target = urllib.parse.unquote(target.split("?", 1)[0])
    if target.startswith("/"):
        return vault / target.lstrip("/")
    return Path(os.path.normpath(src.parent / target))

def format_markdown_body(text: str, title: str) -> str:
    """Normalize a Markdown fragment without flattening its block structure."""
    text = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not text:
        return (
            "## Summary\n\nAdd one concise, reusable fact.\n\n"
            "## Details\n\n- Context:\n- Evidence:\n- Consequence:"
        )

    lines = text.splitlines()
    _, unclosed_fence = _mask_fenced_code(text)
    if unclosed_fence:
        raise ValueError("unclosed fenced code block")

    if lines and re.match(r"^#\s+", lines[0]):
        heading = re.sub(r"^#\s+", "", lines[0]).strip()
        if heading.casefold() != title.casefold():
            raise ValueError("body must not start with a different H1; pass the title as the first argument")
        lines = lines[1:]
        text = "\n".join(lines).strip()

    blocks = re.split(r"\n[ \t]*\n+", text)
    formatted = []
    block_line = re.compile(
        r"^(?: {0,3}(?:#{1,6}\s|>\s?|[-+*]\s+|\d+[.)]\s+)"
        r"|(?:---+|___+|\*\*\*+)\s*$| {4}|\t|\|.*\|$)"
    )
    inline_markup = re.compile(r"`|\[[^\]]+\]\(|\*\*|__|~~")
    for block in blocks:
        block_lines = [line.rstrip() for line in block.splitlines()]
        if not any(line.strip() for line in block_lines):
            continue
        if any(block_line.match(line) for line in block_lines) or inline_markup.search(block):
            formatted.append("\n".join(block_lines))
        else:
            paragraph = " ".join(line.strip() for line in block_lines)
            formatted.append(textwrap.fill(
                paragraph, width=88, break_long_words=False, break_on_hyphens=False,
            ))
    return "\n\n".join(formatted)

INDEX_START = "<!-- sb:index:start -->"

INDEX_END = "<!-- sb:index:end -->"

def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.",
            suffix=".tmp", delete=False,
        ) as stream:
            temp_path = Path(stream.name)
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_path, path)
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)

def slugify(title: str) -> str:
    s = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    # All-non-Latin titles must not all compete for the same canonical "note.md".
    return (s or "note-" + hashlib.sha256(title.encode("utf-8")).hexdigest()[:10])[:80]

def dated_path(vault: Path, folder: str, title: str, day: str) -> Path:
    directory = vault / folder / day
    stem = slugify(title)
    path = directory / f"{stem}.md"
    suffix = 2
    while path.exists() or path.name in RESERVED:
        path = directory / f"{stem}-{suffix}.md"
        suffix += 1
    return path

def write_log(vault: Path, label: str, message: str) -> None:
    """OKF §9: date-grouped entries, newest group first, without frontmatter."""
    log = vault / "log.md"
    if not log.exists():
        log.write_text("# Update Log\n", encoding="utf-8")
    text = log.read_text(encoding="utf-8")
    # Older CLI versions added frontmatter to log.md. On the first new entry,
    # migrate it once to the OKF §9 format.
    text = re.sub(r"^---\s*\n.*?\n---\s*\n?", "", text, count=1, flags=re.S)
    if not text.startswith("# "):
        text = "# Update Log\n\n" + text.lstrip()
    today = dt.date.today().isoformat()
    line = f"* **{label}**: {message}"
    if f"## {today}\n" in text:
        text = text.replace(f"## {today}\n", f"## {today}\n{line}\n", 1)
    else:
        m = re.match(r"^(# .*\n)", text)
        head = m.group(1) if m else ""
        text = head + f"\n## {today}\n{line}\n" + text[len(head):]
    log.write_text(text, encoding="utf-8")

DEFAULT_SCHEMA = """# Wiki schema

These owner-editable rules govern knowledge placement. `sb init` and `sb index`
do not replace this file. Read it before ingesting or revising content.

## Sources and history

- `_raw/`: newly received attachments or downloads that lack an existing
  permanent project location and need a managed home. Use `--original` plus
  `--archive-original` to preserve eligible assets here. Existing project files,
  including files under `data/`, stay at their original paths and are referenced
  from `sources/`; never archive a duplicate. Reuse known originals.
  Legacy `raw/` remains supported without migration. Both archives are excluded
  from knowledge indexes.
- `personal/`: owner-authored original notes; never change them during ingestion.
- `sources/YYYY-MM-DD/slug.md`: new dated, append-only source text or
  explicitly labeled excerpts, with the original URI and, when applicable,
  a link to a preserved original. Keep the exact capture timestamp in
  `generated.at`; source captures have no lifecycle `status`, and `verified`
  records review separately. Leave legacy flat captures in place.
- `notes/YYYY-MM-DD/slug.md`: new atomic observations, decisions, failures and
  research drafts, grouped by local creation day. Leave legacy flat notes in
  place. Correct factual claims by supersession, not silent rewriting.

## Maintained wiki

- `entities/`: concrete people, organizations, products, places or projects.
- `concepts/`: abstract ideas, methods, patterns and mental models.
- `references/`: current factual lookups, such as API rules, prices or
  specifications; do not confuse them with an individual source.
- `topics/`: evolving cross-source thematic syntheses. Do not create another
  `syntheses/` folder with the same role.
- `playbooks/`: repeatable procedures, not executable agent skills or commands.

Search existing pages and aliases before creating a page. Compare new evidence
with existing claims, retain uncertainty and disagreements, and cite material
claims inline. Use `sb page` with a complete body for maintained pages; revisions
require the current hash and a reason. A draft is not verified knowledge.
`index.md` is navigation, `log.md` is change history, `.history/` preserves prior
page bytes, and `index.db` is a rebuildable search index.

## Project provenance

Use `origin_projects: ["project-id"]` for the projects where knowledge arose,
not where it applies. Supply known stable lowercase IDs with repeatable
`--origin-project` on `add`, `idea`, `capture` and `page`; never use local paths
or URLs. Tags remain topical. A maintained page preserves existing origins
and merges explicitly supplied origins from evidence that contributed to its
claims, not merely from the current editing project. Capture provenance is
immutable; different origin sets create linked snapshots. Do not create a
parallel per-project folder schema or bulk-retag existing pages. Provenance
never changes project/global vault routing.

## Capture and compilation

Capture is not compilation: `add` and `idea` always write to `notes/`; this also
applies to `add -t reference`. The kind passed to `page` selects the maintained
folder. Confirmations and presentation changes do not each need another note.

At a completed topic block, integrate supported reusable outcomes into suitable
maintained pages or create one when needed. Name the reason and intended target
for deferred integration. Preserve notes as history; compilation alone neither
deprecates them nor verifies their claims. Do not merely move notes, create a
page per table row or fill every folder. Open questions remain drafts; explicit
capture-only and read-only requests retain their scope. Report captures,
compiled pages and deferrals separately. Focus the hot index on current
maintained pages, not every capture.

## Write for people and agents

- Make authored pages, source summaries and reading views understandable
  without the original conversation. Introduce the subject, scope and caveats.
- Use descriptive headings, short paragraphs and purposeful lists or tables.
  Include only meaningful sections; do not invent facts or template filler.
- Separate source statements, observations, interpretation, limitations and
  open questions. Keep evidence and qualifications beside their claims.
- Preserve meaning, numbers, units, ranges, technical names and identifiers.
  Readability must neither reduce precision nor conceal uncertainty.
- Follow the owner's wiki language; preserve metadata structure, stable paths
  and original quotations. The template language does not set the wiki content language.
- Keep originals and verbatim captures unchanged. Label derived summaries,
  translations and reading views and link their evidence. Do not rewrite
  append-only captures or present their hash as a translated view's hash.
"""

def ensure_bundle(vault: Path) -> bool:
    """Create missing OKF structure; return True only for a newly created index.md."""
    vault.mkdir(parents=True, exist_ok=True)
    (vault / "notes").mkdir(exist_ok=True)
    (vault / "sources").mkdir(exist_ok=True)
    for folder in PAGE_FOLDERS.values():
        (vault / folder).mkdir(exist_ok=True)
    (vault / "personal").mkdir(exist_ok=True)
    (vault / "_raw").mkdir(exist_ok=True)
    schema = vault / "schema.md"
    if not schema.exists():
        schema.write_text(DEFAULT_SCHEMA, encoding="utf-8")
    index = vault / "index.md"
    created = not index.exists()
    if created:
        index.write_text(
            "---\nokf_version: \"0.2\"\n---\n\n"
            f"# {vault.name} — Knowledge Index\n\n"
            "## Curated\n\n<!-- Keep human-written entry points here. -->\n",
            encoding="utf-8",
        )
    if not (vault / "log.md").exists():
        (vault / "log.md").write_text("# Update Log\n", encoding="utf-8")
    if created:
        write_log(vault, "Initialization", f"Bundle created — {now_utc()} by {ACTOR}")
    return created

def deprecate(vault: Path, target: Path, successor_rel: str, successor_title: str) -> None:
    """OKF claim update: retain the previous claim and mark it deprecated."""
    text = target.read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?", text, re.S)
    if not m:
        sys.exit(f"[sb] deprecate: missing frontmatter: {target.name}")
    meta = m.group(1)
    # Modify only frontmatter, never body lines such as 'status: …'.
    if re.search(r"^status:", meta, re.M):
        meta = re.sub(r"^status:.*$", "status: deprecated", meta, count=1, flags=re.M)
    else:
        meta = "status: deprecated\n" + meta
    # OKF §5.2: deprecation is a material change; update generated.at as well.
    meta = re.sub(r"^generated:.*$", f"generated: {{ by: {ACTOR}, at: {now_utc()} }}",
                  meta, count=1, flags=re.M)
    text = f"---\n{meta}\n---\n" + text[m.end():]
    text = text.rstrip("\n") + (
        f"\n\nSuperseded by [{successor_title}]({successor_rel}) ({now_utc()}).\n"
    )
    target.write_text(text, encoding="utf-8")
    rel = target.relative_to(vault.resolve())
    write_log(vault, "Deprecation", f"`{rel}` -> `{successor_rel}` — {now_utc()} by {ACTOR}")

def markdown_link(source: Path, target: Path, label: str) -> str:
    rel = os.path.relpath(target, source.parent).replace(os.sep, "/")
    rel = urllib.parse.quote(rel, safe="/-._~")
    label = label.replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]")
    return f"[{label}]({rel})"

def source_link(vault: Path, note: Path, source: str, number: int) -> str:
    local = source[7:] if source.startswith("file://") else source
    candidate = Path(urllib.parse.unquote(local)).expanduser()
    if not candidate.is_absolute():
        candidate = vault / candidate
    try:
        target = candidate.resolve()
    except OSError:
        target = None
    if target and target.is_relative_to(vault) and target.is_file():
        return markdown_link(note, target, parse_note(target, vault)["title"])
    if target and target.is_file() and source.startswith("file://"):
        return f"[Source {number}](<{source.replace(' ', '%20').replace('>', '%3E')}>)"
    if EXTERNAL_SCHEME_RE.match(source) and not source.startswith("file://"):
        url = source.replace(" ", "%20").replace(">", "%3E")
        return f"[Source {number}](<{url}>)"
    raise ValueError(f"[sb] --source local file must exist inside the bundle: {source}")

def project_origins(args: argparse.Namespace, existing: str = "") -> list[str]:
    """Explicit provenance only; never infer scope or project identity from cwd."""
    projects = list(dict.fromkeys(
        [p.strip() for p in existing.split(",") if p.strip()]
        + list(getattr(args, "origin_project", []) or [])
    ))
    if any(not re.fullmatch(r"[a-z0-9][a-z0-9._-]*", p) for p in projects):
        sys.exit("[sb] --origin-project must be a stable lowercase project ID, not a path or URL")
    return projects

def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def preserved_original(vault: Path, capture: Path, fields: dict[str, str], checksum: str) -> Path | None:
    """Find a verified current or legacy archived original without relocating it."""
    candidates = []
    if fields.get("preserved_original"):
        candidates.append(vault / fields["preserved_original"])
    for folder in ("_raw", "raw"):
        directory = vault / folder / capture.stem
        if directory.is_dir():
            candidates.extend(directory.iterdir())
    for candidate in dict.fromkeys(candidates):
        resolved = candidate.resolve()
        if (any(resolved.is_relative_to(vault / folder) for folder in ("_raw", "raw"))
                and resolved.is_file() and file_sha256(resolved) == checksum):
            return resolved
    return None

HOOK_BLOCK = """## Second Brain (project knowledge)
- Project knowledge belongs in `{vault}` (OKF v0.2 bundle).
- Before non-trivial work: `uv run {sb} --vault "{vault}" search "<terms>"` (fallback: rg).
- Read `schema.md`; analyze existing local files in place and compile their supported findings, without copying them. Use `uv run {sb} --vault "{vault}" capture "Title" --source "<URI>" --body-file "<text-file>"` for a useful excerpt/summary; local file sources are hashed. New captures use `sources/YYYY-MM-DD/slug.md` with the exact capture timestamp in `generated.at`; leave legacy flat captures in place. Keep maintained knowledge in `entities/`, `concepts/`, `references/`, `topics/`, `playbooks/`.
- Only archive newly received/downloaded originals that lack an existing permanent project location and need a managed home: `uv run {sb} --vault "{vault}" capture "Title" --source "<URI>" --body-file "<text-file>" --original "<file>" --archive-original`. Existing project files stay where they are and are referenced from `sources/`; `--original` alone only hashes/references. Reuse preserved originals in `_raw/` or legacy `raw/`; never migrate old files or links implicitly.
- `uv run {sb} --vault "{vault}" page concept "Title" --body-file "<complete-page>" --expect-sha256 "<hash>" --reason "<reason>"` revises maintained pages; prior bytes remain in `.history/`.
- Preserve distinct durable facts with `… --vault "{vault}" add "Title" -t decision -g tags --related notes/YYYY-MM-DD/related.md` (never secrets). New notes use day folders; do not move existing flat notes.
- Capture is not compilation: `add`/`idea` write to `notes/`; so does `add -t reference`. `page` selects the maintained folder. Do not recapture confirmations of unchanged claims.
- Normal completion requires compilation or justified deferral after a topic block. Integrate supported reusable outcomes into maintained pages, or state the deferral's reason and target. Report captures, compiled pages and open questions separately; focus the hot index on current maintained pages.
- Explicit capture-only/open-question requests retain their scope; read-only checks authorize neither writes nor synthesis. Preserve historical notes; compilation is not verification or automatic status promotion.
- Never silently rewrite factual claims; supersede with `… --vault "{vault}" add "Replacement" --supersedes notes/YYYY-MM-DD/old.md` (bundle-relative path; legacy flat paths also work). Respect status and stale_after during recall.
- Owner-authored Markdown belongs in `personal/`; read it only on request and leave it unchanged.
- Follow the owner's wiki language; English skill instructions do not determine content language.
- Preserve human-curated text outside generated index blocks; `index.db` is FTS only. After manual edits run `uv run {sb} --vault "{vault}" index`; check links and drift with `uv run {sb} --vault "{vault}" lint`.
"""

PATTERNS = {
    "python": {
        "def": ["def $NAME($$$ARGS): $$$BODY"],
        "class": ["class $NAME($$$BASES): $$$BODY", "class $NAME: $$$BODY"],
        "import": ["import $MOD"],
        "from": ["from $MOD import $$$NAMES"],
    },
    "typescript": {
        "function": ["function $NAME($$$ARGS) { $$$BODY }"],
        "class": ["class $NAME $$$HERITAGE { $$$BODY }"],
        "arrow": ["const $NAME = ($$$ARGS) => $$$BODY"],
        "import": ["import $$$CLAUSES from '$MOD'", 'import $$$CLAUSES from "$MOD"'],
    },
}

PATTERNS["javascript"] = PATTERNS["typescript"]
