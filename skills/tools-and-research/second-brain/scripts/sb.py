#!/usr/bin/env python3
"""sb.py — second-brain CLI: OKF v0.2 bundle + SQLite FTS5 index.

Stdlib only (codegraph shells out to ast-grep if installed). The bundle
(default ~/second-brain) is the source of truth and a valid Open Knowledge
Format v0.2 bundle. Human-readable directory indexes and index.db are
separate materialized views; `sb index` rebuilds both, and index.db contains FTS only.

OKF v0.2 mapping:
  notes/, sources/, concepts/, entities/, references/, topics/, playbooks/ -> OKF concepts
  personal/**/*.md         -> handwritten source documents (type optional)
  raw/**                  -> original source files, not indexed as concepts
  index.md / log.md / schema.md -> navigation, history and owner conventions, not FTS
  type: <value>            -> OKF type (free-form, not centrally registered)
  status/stale_after/verified/generated/sources -> OKF lifecycle/trust/provenance

Claim updates are supersessions, never silent rewrites:
  sb add "New title" --supersedes notes/2026-01-01/old.md ...

Usage:
  sb [--vault PATH] init              create OKF bundle + print AGENTS.md hook
  sb [--vault PATH] index | rebuild   rebuild Markdown directory indexes + FTS5
  sb [--vault PATH] search QUERY [-n N] [--all]
  sb [--vault PATH] eval CASES.jsonl   measure current FTS5 ranking (read-only)
  sb [--vault PATH] add "Title" [-t TYPE] [-g TAGS] [-r RELEVANCE] [-b BODY | --body-file FILE]
                      [--related PATH]... [--status draft] [--supersedes PATH] [--source URL]...
                      (TYPE is free-form per OKF §4.1; common: observation/decision/insight/failure/reference)
  sb [--vault PATH] page concept|entity|reference|topic|playbook "Title" --body-file FILE
                       [--source URL]... [--related PATH]...
                       [--expect-sha256 HASH --reason TEXT]  create/revise a canonical wiki page
  sb [--vault PATH] capture "Title" --source URL --body-file FILE [--original FILE] [--scope full|excerpt]
  sb [--vault PATH] verify PATH [--by ACTOR]   record OKF verification (default human:$USER)
  sb [--vault PATH] idea "Text"       quick-capture as draft insight
  sb [--vault PATH] lint [--fix]      links, index/FTS drift + OKF/health report
  sb [--vault PATH] orphans           concepts without semantic Markdown inbound links
  sb [--vault PATH] dedup [-t 0.75]   near-duplicate concept pairs
  sb [--vault PATH] codegraph [--root DIR]  symbol/import map via ast-grep
  sb [--vault PATH] stats             bundle + index statistics
  sb selftest                         round-trip checks in a temp bundle
"""

from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import getpass
import hashlib
import io
import json
import os
import posixpath
import re
import shutil
import sqlite3
import subprocess
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


# ── concept parsing (tolerant frontmatter, no yaml dep) ─────────────────────

def _frontmatter_fields(lines: list[str]) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in lines:
        km = re.match(r"^(\w[\w-]*):\s*(.*)$", line.strip())
        if km:
            raw = km.group(2).strip()
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                parsed = raw.strip("'\"[]")
            if isinstance(parsed, list):
                parsed = ", ".join(str(value) for value in parsed)
            fields[km.group(1)] = str(parsed)
    return fields


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
    return {
        "path": str(path.relative_to(vault)),
        "title": (title_m.group(1).strip() if title_m else path.stem),
        "type": fields.get("type", ""),
        "tags": fields.get("tags", ""),
        "relevance": fields.get("relevance") or "medium",
        "status": fields.get("status") or "stable",
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
    # raw/ originals stay byte-for-byte intact, even if they happen to be Markdown.
    files = [p for p in vault.rglob("*.md") if p.name not in RESERVED
             and p.relative_to(vault).parts[0] not in ("raw", ".history")]
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


# ── index / search ────────────────────────────────────────────────────────────

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


def index_directories(vault: Path) -> list[Path]:
    directories = {vault, *(vault / name for name in ("notes", "sources", *PAGE_FOLDERS.values(), "personal"))}
    for note in note_files(vault):
        directory = note.parent
        while directory.is_relative_to(vault):
            directories.add(directory)
            if directory == vault:
                break
            directory = directory.parent
    return sorted(directories, key=lambda path: (len(path.relative_to(vault).parts), path.as_posix()))


def index_block(vault: Path, directory: Path, directories: list[Path]) -> str:
    index = directory / "index.md"
    notes = [path for path in note_files(vault) if path.parent == directory]
    children = [path for path in directories if path.parent == directory]
    lines = [INDEX_START, "## Documents", ""]
    special = [f"- {markdown_link(index, vault / 'schema.md', 'Wiki schema')}"] if directory == vault else []
    if notes or special:
        lines.extend(special)
        for note in notes:
            meta = parse_note(note, vault)
            kind = f" — `{meta['type']}`" if meta["type"] else ""
            lines.append(f"- {markdown_link(index, note, meta['title'])}{kind}")
    else:
        lines.append("_No documents yet._")
    lines.extend(("", "## Folders", ""))
    if children:
        for child in children:
            lines.append(f"- {markdown_link(index, child / 'index.md', child.name + '/')}")
    else:
        lines.append("_No subfolders._")
    lines.append(INDEX_END)
    return "\n".join(lines)


def render_index(vault: Path, directory: Path, directories: list[Path]) -> str:
    path = directory / "index.md"
    title = f"{vault.name} — Knowledge Index" if directory == vault else f"{directory.name} — Index"
    existing = path.read_text(encoding="utf-8", errors="replace") if path.exists() else f"# {title}\n"
    existing = existing.replace("\r\n", "\n").replace("\r", "\n")
    # Preserve removal of legacy German placeholders during index migration.
    existing = existing.replace("* [Titel](notes/<slug>.md) - Einzeiler-Claim\n", "")
    existing = existing.replace("Kuratierte Einstiegszeilen (OKF §8-Form):\n\n", "")
    block = index_block(vault, directory, directories)
    lines = existing.splitlines(keepends=True)
    visible, _ = _mask_fenced_code(existing)
    ranges = []
    start = None
    for i, line in enumerate(visible):
        marker = line.strip()
        if marker == INDEX_START and start is None:
            start = i
        elif marker == INDEX_END and start is not None:
            ranges.append((start, i))
            start = None
    if len(ranges) == 1:
        start, end = ranges[0]
        return "".join(lines[:start]) + block + "\n" + "".join(lines[end + 1:])
    remove = {i for first, last in ranges for i in range(first, last + 1)}
    remove.update(i for i, line in enumerate(visible) if line.strip() in {INDEX_START, INDEX_END})
    existing = "".join(line for i, line in enumerate(lines) if i not in remove)
    return existing.rstrip() + "\n\n" + block + "\n"


def cmd_index(vault: Path) -> int:
    vault = vault.resolve()
    ensure_bundle(vault)
    rows = [parse_note(p, vault) for p in note_files(vault)]
    untyped = [r["path"] for r in rows if not r["type"] and not r["path"].startswith("personal/")]
    directories = index_directories(vault)
    indexes = [(directory / "index.md", render_index(vault, directory, directories))
               for directory in directories]
    for path, text in indexes:
        atomic_write_text(path, text)

    fd, temp_name = tempfile.mkstemp(prefix=".index.db.", suffix=".tmp", dir=vault)
    os.close(fd)
    temp_db = Path(temp_name)
    try:
        con = connect(vault, temp_db)
        try:
            with con:
                for row in rows:
                    con.execute(
                        "INSERT INTO notes(path, title, type, tags, relevance, status, stale_after, verified, body) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (row["path"], row["title"], row["type"], row["tags"], row["relevance"], row["status"], row["stale_after"], row["verified"], row["body"]),
                    )
        finally:
            con.close()
        os.replace(temp_db, db_path(vault))
    finally:
        temp_db.unlink(missing_ok=True)
    print(f"[sb] indexed {len(rows)} Markdown files in {len(indexes)} directory indexes + FTS")
    print(f"[sb] FTS: {db_path(vault)}")
    if untyped:
        print(f"[sb] OKF WARNING: {len(untyped)} file(s) without 'type' (required by OKF):")
        for p in untyped[:10]:
            print(f"    {p}")
    return 0


def ranked_rows(con: sqlite3.Connection, query: str, limit: int, show_all: bool) -> list[tuple]:
    # One ranking/filter path for interactive search and evaluation.
    return con.execute(
        "SELECT path, title, type, tags, relevance, status, stale_after, verified,"
        " snippet(notes, 8, '>>', '<<', '…', 12)"
        " FROM notes WHERE notes MATCH ? AND status != ? ORDER BY rank LIMIT ?",
        (query, "" if show_all else "deprecated", limit),
    ).fetchall()


def cmd_search(vault: Path, query: str, limit: int, show_all: bool) -> int:
    if limit < 1:
        sys.exit("[sb] --limit must be at least 1")
    db = db_path(vault)
    if not db.exists():
        print(f"[sb] No index. Run 'sb index' first (or rg -i {query!r} {vault}).")
        return 1
    con = sqlite3.connect(db)
    try:
        rows = ranked_rows(con, query, limit, show_all)
    except sqlite3.OperationalError as exc:
        con.close()
        sys.exit(f"[sb] Search error ({exc}). Stale index? Run 'sb index'.")
    now = dt.datetime.now(dt.timezone.utc)
    for path, title, ntype, tags, rel, status, stale_after, verified, snip in rows:
        stale = ""
        if stale_after:
            inst = parse_instant(stale_after)
            if inst and now >= inst:
                stale = " [STALE]"
        trust = "human-verified" if "human:" in verified else "machine-verified" if verified else ""
        meta = " ".join(x for x in (ntype, rel, trust, status if status != "stable" else "", tags) if x)
        print(f"{vault / path}\n    {title}  [{meta}]{stale}\n    …{snip}…")
    if not rows:
        extra = ""
        if not show_all:
            hidden = con.execute(
                "SELECT count(*) FROM notes WHERE notes MATCH ? AND status = 'deprecated'", (query,)
            ).fetchone()[0]
            if hidden:
                extra = f" ({hidden} deprecated entries hidden; use --all to show them)"
        con.close()
        print(f"[sb] No matches for {query!r}.{extra}")
        return 1
    con.close()
    return 0


def cmd_eval(vault: Path, cases_file: Path) -> int:
    """Evaluate the current non-deprecated FTS ranking without modifying the vault."""
    cases = []
    try:
        lines = cases_file.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        sys.exit(f"[sb] eval: cannot read cases: {exc}")
    for line_no, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            case = json.loads(line)
        except json.JSONDecodeError as exc:
            sys.exit(f"[sb] eval line {line_no}: invalid JSON: {exc}")
        if not isinstance(case, dict) or not isinstance(case.get("q"), str) or not case["q"].strip():
            sys.exit(f"[sb] eval line {line_no}: expected nonempty q string")
        gold = case.get("gold")
        if (not isinstance(gold, list) or not gold or any(
                not isinstance(p, str) or not p.endswith(".md") or Path(p).is_absolute()
                or ".." in Path(p).parts or Path(p).as_posix() != p for p in gold)):
            sys.exit(f"[sb] eval line {line_no}: gold must be nonempty vault-relative Markdown paths")
        cases.append((line_no, case["q"], set(gold)))
    if not cases:
        sys.exit("[sb] eval: no cases")
    db = db_path(vault)
    if not db.exists():
        sys.exit("[sb] eval: no index; run 'sb index' first")
    ranks = []
    try:
        con = sqlite3.connect(f"file:{urllib.parse.quote(str(db.resolve()))}?mode=ro", uri=True)
        try:
            for line_no, query, gold in cases:
                try:
                    paths = [row[0] for row in ranked_rows(con, query, 10, False)]
                except sqlite3.OperationalError as exc:
                    sys.exit(f"[sb] eval line {line_no}: search error: {exc}")
                ranks.append(next((i for i, path in enumerate(paths, 1) if path in gold), None))
        finally:
            con.close()
    except sqlite3.Error as exc:
        sys.exit(f"[sb] eval: cannot read index: {exc}")
    for (line_no, query, _), rank in zip(cases, ranks, strict=True):
        print(f"[sb] eval line {line_no}: {'rank=' + str(rank) if rank else 'MISS'} q={json.dumps(query, ensure_ascii=False)}")
    score = " ".join(f"recall@{k}={sum(rank is not None and rank <= k for rank in ranks) / len(ranks):.1%}"
                     for k in (1, 3, 5, 10))
    mrr = sum(1 / rank for rank in ranks if rank is not None) / len(ranks)
    print(f"[sb] eval: {len(ranks)} cases, {score} MRR@10={mrr:.3f}")
    return 0


# ── add / idea / init ─────────────────────────────────────────────────────────

def slugify(title: str) -> str:
    s = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    # All-non-Latin titles must not all compete for the same canonical "note.md".
    return (s or "note-" + hashlib.sha256(title.encode("utf-8")).hexdigest()[:10])[:80]


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

- `raw/`: unchanged originals, including binary assets. `sb capture --original`
  copies them here; read the source before deriving wiki claims. Originals are
  not indexed as concepts.
- `personal/`: owner-authored original notes; never change them during ingestion.
- `sources/`: dated, append-only source text or explicitly labeled excerpts,
  with the original URI and, when available, a link to `raw/`.
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
    (vault / "raw").mkdir(exist_ok=True)
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


def cmd_add(vault: Path, args: argparse.Namespace) -> int:
    vault = vault.resolve()  # Normalize once; target links are resolved paths.
    ensure_bundle(vault)
    args.title = args.title.strip()
    args.type = args.type.strip()
    if not args.title or any(c in args.title for c in "\r\n"):
        sys.exit("[sb] Title must be nonempty and single-line")
    if not args.type or any(c in args.type for c in "\r\n"):
        sys.exit("[sb] --type must be nonempty and single-line")
    if args.status not in VALID_STATUS:
        sys.exit(f"[sb] --status must be one of {VALID_STATUS}")
    date = dt.date.today().isoformat()
    stem = slugify(args.title)
    daily_notes = vault / "notes" / date
    note = daily_notes / f"{stem}.md"
    n = 2  # Same-day slug collisions use a suffix, including non-ASCII slugs.
    while note.exists() or note.name in RESERVED:
        note = daily_notes / f"{stem}-{n}.md"
        n += 1
    tags = [t.strip() for t in args.tags.split(",") if t.strip()]
    sources = [url.strip() for url in args.source if url.strip()]
    raw_body = getattr(args, "body", "")
    body_file = getattr(args, "body_file", None)
    if body_file is not None:
        if raw_body:
            sys.exit("[sb] --body and --body-file cannot be used together")
        try:
            raw_body = sys.stdin.read() if body_file == "-" else Path(body_file).expanduser().read_text(encoding="utf-8")
        except OSError as exc:
            sys.exit(f"[sb] cannot read --body-file {body_file}: {exc}")
    try:
        body = format_markdown_body(raw_body, args.title)
    except ValueError as exc:
        sys.exit(f"[sb] invalid Markdown body: {exc}")
    if args.status != "draft":
        for label, target in md_links(body):
            resolved = resolve_link(vault, note, target).resolve()
            if not resolved.is_relative_to(vault) or not resolved.exists():
                sys.exit(f"[sb] invalid Markdown body: link target not found in bundle: [{label}]({target})")

    related: list[tuple[Path, str]] = []
    seen_related: set[Path] = set()
    for raw_path in getattr(args, "related", []) or []:
        target = (vault / raw_path).resolve()
        if (not target.is_relative_to(vault) or not target.is_file()
                or target.name in RESERVED or target.suffix.lower() != ".md"):
            sys.exit(f"[sb] --related must point to a Markdown note inside the bundle: {raw_path}")
        if target not in seen_related:
            related.append((target, parse_note(target, vault)["title"]))
            seen_related.add(target)

    predecessor = None
    if args.supersedes:
        target = (vault / args.supersedes).resolve()
        if (not target.is_relative_to(vault) or not target.is_file()
                or target.name in RESERVED):
            sys.exit(f"[sb] --supersedes: not a regular concept file in the bundle: {args.supersedes}")
        if not re.match(r"^---\s*\n.*?\n---\s*\n?", target.read_text(encoding="utf-8"), re.S):
            sys.exit(f"[sb] --supersedes: concept has no frontmatter: {args.supersedes}")
        predecessor = target
    fm = f"type: {json.dumps(args.type, ensure_ascii=False)}\n"
    if args.status != "stable":
        fm += f"status: {args.status}\n"
    fm += f"generated: {{ by: {ACTOR}, at: {now_utc()} }}\nrelevance: {args.relevance}\n"
    if tags:
        fm += f"tags: {json.dumps(tags, ensure_ascii=False)}\n"
    if sources:
        src = "\n".join(
            f"  - {{ resource: {json.dumps(url, ensure_ascii=False)} }}"
            for url in sources
        )
        fm += f"sources:\n{src}\n"
    sections = [f"# {args.title}", body]
    if predecessor is not None:
        sections.extend((
            "## Supersedes",
            f"- {markdown_link(note, predecessor, parse_note(predecessor, vault)['title'])}",
        ))
    if related:
        sections.extend((
            "## Related",
            "\n".join(f"- {markdown_link(note, target, title)}" for target, title in related),
        ))
    try:
        source_links = [source_link(vault, note, source, i) for i, source in enumerate(sources, 1)]
    except ValueError as exc:
        sys.exit(str(exc))
    if source_links:
        sections.extend(("## Sources", "\n".join(f"- {link}" for link in source_links)))
    note.parent.mkdir(parents=True, exist_ok=True)
    rendered_sections = "\n\n".join(sections)
    note.write_text(f"---\n{fm}---\n\n{rendered_sections}\n", encoding="utf-8")
    if predecessor is not None:
        # Write successfully before deprecation; never leave a predecessor without a successor.
        successor_rel = urllib.parse.quote(
            os.path.relpath(note, predecessor.parent).replace(os.sep, "/"), safe="/-._~",
        )
        deprecate(vault, predecessor, successor_rel, args.title)
    print(f"[sb] Created concept: {note}")
    return cmd_index(vault)


def cmd_page(vault: Path, args: argparse.Namespace) -> int:
    """Create or explicitly revise one stable-path wiki page; synthesis is the agent's job."""
    vault = vault.resolve()
    ensure_bundle(vault)
    title = args.title.strip()
    if not title or any(c in title for c in "\r\n"):
        sys.exit("[sb] page title must be a single nonempty line")
    page = vault / PAGE_FOLDERS[args.kind] / f"{slugify(title)}.md"
    old = page.read_bytes() if page.exists() else None
    if old is None and (args.expect_sha256 or args.reason):
        sys.exit("[sb] new page does not accept --expect-sha256 or --reason")
    if old is not None:
        digest = hashlib.sha256(old).hexdigest()
        if not args.expect_sha256 or not args.reason or args.expect_sha256 != digest:
            sys.exit(f"[sb] page exists; revision requires --expect-sha256 {digest} and --reason")
        if parse_note(page, vault)["title"] != title:
            sys.exit("[sb] slug collision: existing page has a different title")
    if not args.source and not args.related:
        sys.exit("[sb] page requires at least one --source or --related evidence path")
    try:
        raw_body = sys.stdin.read() if args.body_file == "-" else Path(args.body_file).expanduser().read_text(encoding="utf-8")
        if not raw_body.strip():
            raise ValueError("page body must not be empty")
        body = format_markdown_body(raw_body, title)
    except (OSError, ValueError) as exc:
        sys.exit(f"[sb] page body: {exc}")
    for label, target in md_links(body):
        resolved = resolve_link(vault, page, target).resolve()
        if not resolved.is_relative_to(vault) or not resolved.is_file():
            sys.exit(f"[sb] page link target not found: [{label}]({target})")
    related: list[str] = []
    for rel in dict.fromkeys(args.related):
        target = (vault / rel).resolve()
        if (not target.is_relative_to(vault) or not target.is_file()
                or target.name in RESERVED or target == page or target.suffix != ".md"):
            sys.exit(f"[sb] page related target must be a different Markdown file in the bundle: {rel}")
        related.append(markdown_link(page, target, parse_note(target, vault)["title"]))
    try:
        sources = [source_link(vault, page, source, i) for i, source in enumerate(args.source, 1)]
    except ValueError as exc:
        sys.exit(str(exc))
    fm = f"type: {json.dumps(args.kind)}\nstatus: {args.status}\n"
    fm += f"generated: {{ by: {ACTOR}, at: {now_utc()} }}\n"
    if args.tags.strip():
        fm += f"tags: {json.dumps([t.strip() for t in args.tags.split(',') if t.strip()], ensure_ascii=False)}\n"
    if args.source:
        fm += "sources:\n" + "".join(
            f"  - {{ resource: {json.dumps(source, ensure_ascii=False)} }}\n" for source in args.source
        )
    sections = [f"# {title}", body]
    if related:
        sections.extend(("## Related", "\n".join(f"- {link}" for link in related)))
    if sources:
        sections.extend(("## Sources", "\n".join(f"- {link}" for link in sources)))
    rendered = f"---\n{fm}---\n\n" + "\n\n".join(sections) + "\n"
    if old is not None:
        archive = vault / ".history" / page.parent.name / page.stem / f"{now_utc().replace(':', '')}-{digest[:12]}.txt"
        archive.parent.mkdir(parents=True, exist_ok=True)
        archive.write_bytes(old)
    atomic_write_text(page, rendered)
    if old is not None:
        write_log(vault, "Wiki revision", f"`{page.relative_to(vault)}`: {args.reason} — prior `{archive.relative_to(vault)}` (SHA-256 {digest})")
    else:
        write_log(vault, "Wiki page", f"`{page.relative_to(vault)}` created")
    print(f"[sb] wiki page: {page}")
    return cmd_index(vault)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def cmd_capture(vault: Path, args: argparse.Namespace) -> int:
    """Keep supplied source text as an immutable, repeat-safe Markdown snapshot."""
    vault = vault.resolve()
    ensure_bundle(vault)
    title = args.title.strip()
    if not title or any(c in title for c in "\r\n"):
        sys.exit("[sb] capture title must be a single nonempty line")
    base = f"{dt.date.today().isoformat()}-{slugify(title)}"
    snapshot = vault / "sources" / f"{base}.md"
    original = Path(args.original).expanduser() if args.original else None
    if original is not None and not original.is_file():
        sys.exit(f"[sb] capture: original file not found: {original}")
    try:
        body = sys.stdin.read() if args.body_file == "-" else Path(args.body_file).expanduser().read_text(encoding="utf-8")
        if not body.strip():
            raise ValueError("source text must not be empty")
        link = source_link(vault, snapshot, args.source, 1)
        original_hash = file_sha256(original) if original is not None else ""
    except (OSError, ValueError) as exc:
        sys.exit(f"[sb] capture: {exc}")
    body_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()
    previous = None
    for path in (vault / "sources").glob("*.md"):
        if path.name in RESERVED:
            continue
        meta = _capture_fields(path)
        if (meta.get("source_uri") != args.source or meta.get("capture_scope") not in ("full", "excerpt")
                or not re.fullmatch(r"[0-9a-f]{64}", meta.get("content_sha256", ""))):
            continue  # Ignore unrelated and unmarked or malformed captures.
        if previous is None or path.stat().st_mtime_ns > previous.stat().st_mtime_ns:
            previous = path
        if (meta["content_sha256"] == body_hash and meta["capture_scope"] == args.scope
                and meta.get("original_sha256", "") == original_hash):
            raw_dir = vault / "raw" / path.stem
            if original is None or (raw_dir.is_dir() and any(
                    file_sha256(copy) == original_hash for copy in raw_dir.iterdir() if copy.is_file())):
                print(f"[sb] existing capture: {path}")
                return 0
    number = 2
    while snapshot.exists():
        snapshot = vault / "sources" / f"{base}-{number}.md"
        number += 1
    frontmatter = (f'type: "source"\nstatus: draft\n'
                   f'generated: {{ by: {ACTOR}, at: {now_utc()} }}\n'
                   f'capture_scope: {json.dumps(args.scope)}\n'
                   f'source_uri: {json.dumps(args.source, ensure_ascii=False)}\n'
                   f'content_sha256: {body_hash}\n'
                   f'original_sha256: {original_hash}\n'
                   f'sources:\n  - {{ resource: {json.dumps(args.source, ensure_ascii=False)} }}\n')
    original_links = [f"- {link}"]
    if original is not None:
        copy = vault / "raw" / snapshot.stem / original.name
        copy.parent.mkdir(parents=True, exist_ok=True)
        try:
            with original.open("rb") as source_file, copy.open("xb") as target_file:
                shutil.copyfileobj(source_file, target_file)
        except OSError as exc:
            sys.exit(f"[sb] capture: cannot preserve original without overwriting: {exc}")
        original_links.append(f"- {markdown_link(snapshot, copy, 'Preserved original')}")
    sections = [f"# {title}", body, "## Original", "\n".join(original_links)]
    if previous is not None:
        sections.extend(("## Previous capture", f"- {markdown_link(snapshot, previous, parse_note(previous, vault)['title'])}"))
    try:
        with snapshot.open("x", encoding="utf-8") as output:
            output.write(f"---\n{frontmatter}---\n\n" + "\n\n".join(sections) + "\n")
    except OSError as exc:
        sys.exit(f"[sb] capture: cannot create snapshot: {exc}")
    write_log(vault, "Source capture", f"`{snapshot.relative_to(vault)}` from {args.source}")
    print(f"[sb] captured: {snapshot}")
    return cmd_index(vault)


def cmd_idea(vault: Path, text: str, args: argparse.Namespace) -> int:
    # argparse only sets the selected subparser's defaults; supply missing fields.
    args.title = text.strip().rstrip(".")
    args.type = "insight"
    args.status = "draft"
    args.body = text
    args.relevance = getattr(args, "relevance", "low")
    args.supersedes = getattr(args, "supersedes", "")
    args.source = getattr(args, "source", [])
    return cmd_add(vault, args)


def cmd_verify(vault: Path, rel: str, by: str) -> int:
    """OKF §5.2/§5.3: append a verification entry in the human-reviewed trust tier."""
    vault = vault.resolve()
    if not by:
        by = f"human:{getpass.getuser()}"
    by = by.strip()
    if not re.fullmatch(r"[\w@./:+-]+", by):
        sys.exit("[sb] --by may contain only letters, numbers and @./:+-")
    target = (vault / rel).resolve()
    if not target.is_relative_to(vault) or not target.is_file() or target.name in RESERVED:
        sys.exit(f"[sb] verify: not a regular concept file in the bundle: {rel}")
    text = target.read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?", text, re.S)
    if not m:
        sys.exit(f"[sb] verify: missing frontmatter: {rel}")
    meta = m.group(1)
    new_entry = f"{{ by: {json.dumps(by, ensure_ascii=False)}, at: {now_utc()} }}"
    vm = re.search(r"^verified:[^\n]*(?:\n[ \t]+[^\n]*)*", meta, re.M)
    if vm:
        block = vm.group(0)
        inline = re.fullmatch(r"verified:\s*(\{[^}]*\})\s*", block)
        new_block = (f"verified:\n  - {inline.group(1)}\n  - {new_entry}" if inline
                     else block.rstrip() + f"\n  - {new_entry}")
        meta = meta.replace(block, new_block, 1)
    else:
        meta = meta.rstrip("\n") + f"\nverified: {new_entry}\n"
    target.write_text(f"---\n{meta}\n---\n" + text[m.end():], encoding="utf-8")
    write_log(vault, "Update", f"verified `{target.relative_to(vault)}` by {by} — {now_utc()}")
    print(f"[sb] verified: {rel} (by {by})")
    return cmd_index(vault)


HOOK_BLOCK = """## Second Brain (project knowledge)
- Project knowledge belongs in `{vault}` (OKF v0.2 bundle).
- Before non-trivial work: `uv run {sb} --vault "{vault}" search "<terms>"` (fallback: rg).
- Read `schema.md`; preserve originals with `uv run {sb} --vault "{vault}" capture "Title" --source "<URI>" --body-file "<text-file>" --original "<original>"` when applicable. Keep originals in `raw/`, captures in `sources/` and maintained knowledge in `entities/`, `concepts/`, `references/`, `topics/`, `playbooks/`.
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


def cmd_init(vault: Path) -> int:
    """Create missing OKF bundle structure and print the AGENTS.md hook."""
    vault = vault.resolve()
    ensure_bundle(vault)
    try:
        hook_vault = vault.relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        hook_vault = str(vault)
    print(f"[sb] OKF v0.2 bundle ready: {vault}")
    print("[sb] Add this block to the project's AGENTS.md:\n")
    print(HOOK_BLOCK.format(vault=hook_vault, sb=str(Path(__file__).resolve())))
    return cmd_index(vault)


# ── lint / orphans / dedup ────────────────────────────────────────────────────

def iter_concepts(vault: Path):
    for p in note_files(vault):
        yield p, p.read_text(encoding="utf-8", errors="replace")


def index_drift(vault: Path) -> list[Path]:
    directories = index_directories(vault)
    return [directory / "index.md" for directory in directories
            if not (directory / "index.md").exists()
            or (directory / "index.md").read_text(encoding="utf-8", errors="replace")
            != render_index(vault, directory, directories)]


def fts_drift(vault: Path) -> bool:
    db = db_path(vault)
    if not db.exists():
        return True
    columns = ("path", "title", "type", "tags", "relevance", "status", "stale_after", "verified", "body")
    try:
        con = sqlite3.connect(db)
        try:
            indexed = {row[0]: tuple(row[1:]) for row in con.execute(
                "SELECT " + ", ".join(columns) + " FROM notes"
            )}
        finally:
            con.close()
    except sqlite3.DatabaseError:
        return True
    current = {}
    for path in note_files(vault):
        note = parse_note(path, vault)
        current[note["path"]] = tuple(note[column] for column in columns[1:])
    return indexed != current


def cmd_lint(vault: Path, fix: bool) -> int:
    vault = vault.resolve()
    broken: list[tuple[Path, str, str]] = []
    untyped, unsupported_wikilinks, drafts, deprecated, stale = [], [], 0, 0, 0
    now = dt.datetime.now(dt.timezone.utc)
    for p, text in iter_concepts(vault):
        meta = parse_note(p, vault)
        if not meta.get("type") and not p.relative_to(vault).parts[0] == "personal":
            untyped.append(p.relative_to(vault))
        unsupported_wikilinks.extend((p, target) for target in WIKILINK_RE.findall(markdown_outside_code(text)))
        if meta.get("status") == "draft":
            drafts += 1
        if meta.get("status") == "deprecated":
            deprecated += 1
        sa = meta.get("stale_after") or ""
        inst = parse_instant(sa) if sa else None
        if inst and now >= inst:
            stale += 1
        for label, target in md_links(text):
            resolved = resolve_link(vault, p, target).resolve()
            if not resolved.is_relative_to(vault) or not resolved.exists():
                broken.append((p, label, target))
    for directory in index_directories(vault):
        index = directory / "index.md"
        if not index.exists():
            continue
        text = index.read_text(encoding="utf-8", errors="replace")
        for label, target in md_links(text):
            resolved = resolve_link(vault, index, target).resolve()
            if not resolved.is_relative_to(vault) or not resolved.exists():
                broken.append((index, label, target))
    drifted_indexes = index_drift(vault)
    stale_fts = fts_drift(vault)
    print(f"[sb] lint: {len(broken)} broken links, {len(unsupported_wikilinks)} unsupported wikilinks, "
          f"{len(drifted_indexes)} index drift, FTS {'drift' if stale_fts else 'current'}, "
          f"{len(untyped)} without type, {drafts} draft, {deprecated} deprecated, {stale} stale")
    for p, label, target in broken:
        print(f"    broken: {p.relative_to(vault)} -> [{label}]({target})")
    for p, target in unsupported_wikilinks:
        print(f"    unsupported wikilink: {p.relative_to(vault)} -> [[{target}]]; use [text](path.md)")
    for rel in untyped:
        print(f"    without type: {rel}")
    for path in drifted_indexes:
        print(f"    index drift: {path.relative_to(vault)}")
    if stale_fts:
        print(f"    FTS drift: {db_path(vault).name} missing or does not match Markdown files")
    if fix and (drifted_indexes or stale_fts):
        print("[sb] --fix: rebuilding generated indexes and FTS; source notes are unchanged")
        cmd_index(vault)
    return 0


def cmd_orphans(vault: Path) -> int:
    vault = vault.resolve()
    inbound: set[str] = set()
    files = [p for p in note_files(vault) if p.relative_to(vault).parts[0] != "personal"]
    for p, text in iter_concepts(vault):
        for _, target in md_links(text):
            resolved = resolve_link(vault, p, target).resolve()
            if resolved.is_relative_to(vault):
                inbound.add(os.path.realpath(resolved))
    orphans = [p for p in files if os.path.realpath(p) not in inbound]
    print(f"[sb] {len(orphans)} orphan(s) without inbound links (integration candidates):")
    for p in orphans:
        print(f"    {p.relative_to(vault)}")
    return 0


def shingles(text: str, n: int = 3) -> set[tuple[str, ...]]:
    # Drop the H1: duplicates often have different titles but identical bodies.
    text = re.sub(r"^#\s+.+$\n?", "", text, count=1, flags=re.M)
    words = re.findall(r"\w+", text.lower())
    return {tuple(words[i:i + n]) for i in range(max(0, len(words) - n + 1))}


def cmd_dedup(vault: Path, threshold: float) -> int:
    # Find candidate pairs through a shingle inverted index, then use Jaccard.
    # Only candidate pairs incur O(n²) work; suitable for a few thousand concepts.
    if not 0 <= threshold <= 1:
        sys.exit("[sb] --threshold must be between 0 and 1")
    vault = vault.resolve()
    entries = []
    index: dict[tuple[str, ...], list[int]] = {}
    for p in note_files(vault):
        meta = parse_note(p, vault)
        if meta.get("status") == "deprecated":
            continue
        i = len(entries)
        entries.append((p, shingles(meta.get("body", ""))))
        for sh in entries[-1][1]:
            index.setdefault(sh, []).append(i)
    pairs: set[tuple[int, int]] = set()
    for bucket in index.values():
        for a in range(len(bucket)):
            for b in range(a + 1, len(bucket)):
                pairs.add((bucket[a], bucket[b]))
    found = 0
    for a, b in sorted(pairs):
        sa, sb = entries[a][1], entries[b][1]
        if not sa or not sb:
            continue
        jac = len(sa & sb) / len(sa | sb)
        if jac >= threshold:
            found += 1
            print(f"    {jac:.0%}  {entries[a][0].relative_to(vault)}  ~  {entries[b][0].relative_to(vault)}")
    print(f"[sb] {found} duplicate pair(s) >= {threshold:.0%} similarity "
          "(resolve by supersession, not deletion)")
    return 0


# ── codegraph (ast-grep) ──────────────────────────────────────────────────────

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


def find_ast_grep() -> str | None:
    for binname in ("ast-grep", "sg"):
        path = shutil.which(binname)
        if path:
            return binname
    return None


def run_pattern(binary: str, pattern: str, lang: str, root: Path) -> list[dict]:
    cmd = [binary, "run", "-p", pattern, "-l", lang, "--json", str(root)]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120,
                              check=False)
    except subprocess.TimeoutExpired:
        sys.exit(f"[sb] ast-grep timed out for language {lang}")
    if proc.returncode not in (0, 1):  # ast-grep: 1 means a valid pattern with no matches.
        sys.exit(f"[sb] ast-grep failed: {proc.stderr.strip()[:300]}")
    if not proc.stdout.strip():
        return []
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        sys.exit(f"[sb] ast-grep returned invalid JSON: {exc}")


def meta_name(match: dict) -> str:
    mv = match.get("metaVariables") or {}
    single = mv.get("single") or {}
    node = single.get("NAME") or {}
    if isinstance(node, dict):
        return str(node.get("text", "?"))
    return str(match.get("metaName", "?"))


def line_of(match: dict) -> int:
    try:
        return int(match["range"]["start"]["line"]) + 1  # 0-based
    except (KeyError, TypeError, ValueError):
        return 0


def match_file(root: Path, match: dict) -> str:
    path = Path(str(match.get("file", "?")))
    path = path if path.is_absolute() else root / path
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        return str(path)


def resolve_import(lang: str, mod: str, importer: str,
                   known_files: dict[str, Path]) -> Path | None:
    mod = mod.strip().strip("'\"")
    if lang == "python":
        dots = len(mod) - len(mod.lstrip("."))
        name = mod[dots:].replace(".", "/")
        base = posixpath.dirname(importer)
        for _ in range(max(0, dots - 1)):
            base = posixpath.dirname(base)
        rel = posixpath.normpath(posixpath.join(base, name)) if dots else name
        for cand in (f"{rel}.py", f"{rel}/__init__.py"):
            hit = known_files.get(cand)
            if hit:
                return hit
    else:
        base = (posixpath.normpath(posixpath.join(posixpath.dirname(importer), mod))
                if mod.startswith(".") else mod.rstrip("/"))
        extensions = (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs")
        candidates = ((base,) if base.endswith(extensions) else
                      tuple(f"{base}{ext}" for ext in extensions)
                      + tuple(f"{base}/index{ext}" for ext in extensions))
        for cand in candidates:
            hit = known_files.get(cand)
            if hit:
                return hit
    return None


def cmd_codegraph(vault: Path, root: Path) -> int:
    """Map code symbols/imports through ast-grep into an OKF concept.

    Supports Python and TS/JS functions, classes and imports. Import resolution
    uses basename/path heuristics, not a type resolver. LSP cross-references
    would be a possible future extension if needed.
    """
    binary = find_ast_grep()
    if not binary:
        sys.exit("[sb] ast-grep not found. Install: npm i -g @ast-grep/cli (or brew install ast-grep)")
    root = root.resolve()
    if not root.is_dir():
        sys.exit(f"[sb] --root is not a directory: {root}")
    vault = vault.resolve()
    known: dict[str, Path] = {}
    extensions = {".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"}
    ignored = {".git", ".venv", "venv", "node_modules", "dist", "build",
               "coverage", "__pycache__", ".mypy_cache", ".pytest_cache", ".ruff_cache"}
    for directory, dirs, names in os.walk(root):
        dirs[:] = [name for name in dirs if name not in ignored]
        base = Path(directory)
        for name in names:
            p = base / name
            if p.suffix in extensions:
                known[p.relative_to(root).as_posix()] = p
    sections: list[str] = []
    for lang, pats in PATTERNS.items():
        symbols: dict[str, list[str]] = {}
        imports: dict[str, set[str]] = {}
        for kind, patterns in pats.items():
            if kind not in ("import", "from"):
                for pattern in patterns:
                    for m in run_pattern(binary, pattern, lang, root):
                        f = match_file(root, m)
                        symbols.setdefault(f, []).append(f"{kind} `{meta_name(m)}` (L{line_of(m)})")
            else:
                for pattern in patterns:
                    for m in run_pattern(binary, pattern, lang, root):
                        f = match_file(root, m)
                        mv = (m.get("metaVariables") or {}).get("single", {})
                        node = mv.get("MOD") or {}
                        mod = node.get("text") if isinstance(node, dict) else None
                        if mod:
                            target = resolve_import(lang, str(mod), f, known)
                            if target:
                                # Use inline code, not a link: the target is outside the
                                # bundle and would create permanently broken wiki links.
                                imports.setdefault(f, set()).add(f"`{mod}` -> `{target.relative_to(root)}`")
                            else:
                                imports.setdefault(f, set()).add(f"`{mod}` -> (external)")
        for f in sorted(set(symbols) | set(imports)):
            lines = [f"## {f}"]
            lines += [f"- {s}" for s in sorted(symbols.get(f, []))]
            lines += [f"- import {i}" for i in sorted(imports.get(f, []))]
            sections.append("\n".join(lines) + "\n")
    if not sections:
        print("[sb] No matches; is --root a Python/TS/JS project?")
        return 1
    out = vault / "topics" / "code-graph.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        f"---\ntype: code-graph\ngenerated: {{ by: {ACTOR}, at: {now_utc()} }}\n"
        f"resource: {root}\nrelevance: low\n---\n\n# Code-Graph: {root.name}\n\n"
        + "\n".join(sections),
        encoding="utf-8",
    )
    write_log(vault, "Update", f"code graph updated: {root} — {now_utc()} by {ACTOR}")
    print(f"[sb] Code graph written: {out}")
    return cmd_index(vault)


# ── stats / selftest ──────────────────────────────────────────────────────────

def cmd_stats(vault: Path) -> int:
    files = note_files(vault)
    # Parse frontmatter, not whole-file regexes; body lines like 'status: …' must not affect counts.
    concepts = [p for p in files if p.relative_to(vault).parts[0] != "personal"]
    deprecated = sum(1 for p in concepts if parse_note(p, vault).get("status") == "deprecated")
    print(f"Bundle:      {vault} (OKF v0.2)")
    print(f"Markdown:    {len(files)} files ({len(concepts)} concepts, {len(files) - len(concepts)} personal)")
    print(f"Navigation:  {len(index_directories(vault))} directory indexes ({len(index_drift(vault))} drift)")
    fts = "stale" if fts_drift(vault) else "current"
    print(f"FTS only:    {db_path(vault)} ({fts})")
    return 0


def _ns(**kw):
    return argparse.Namespace(**kw)


def cmd_selftest() -> int:
    with tempfile.TemporaryDirectory() as td:
        vault = Path(td) / "vault"
        rc0 = cmd_init(vault)
        rc1 = cmd_add(vault, _ns(title="UV Workspace Gotcha", type="failure", tags="python, uv",
                                 relevance="high", status="stable", supersedes=None, source=[],
                                 body="uv sync ignores workspace members without an explicit source. Fix: set tool.uv.sources."))
        old = next(vault.glob("notes/*/uv-workspace*"))
        rc2 = cmd_add(vault, _ns(title="UV Workspace Final", type="decision", tags="python, uv",
                                 relevance="high", status="stable",
                                 supersedes=str(old.relative_to(vault)), source=[],
                                 body="Final solution: tool.uv.sources + workspace members."))
        rc3 = cmd_idea(vault, "Marimo batch reporting as the default", _ns(tags="", relevance="low", supersedes=None, source=[]))
        rc3b = cmd_add(vault, _ns(title="Marimo Batch Reporting Copy", type="insight", tags="",
                                  relevance="low", status="stable", supersedes=None, source=[],
                                  body="Marimo batch reporting as the default"))
        rc4 = cmd_add(vault, _ns(title="UV Duplicate", type="failure", tags="python",
                                 relevance="medium", status="stable", supersedes=None, source=["https://docs.astral.sh/uv/"],
                                 body="uv sync ignores workspace members without an explicit source. Fix: set tool.uv.sources."))
        manual_broken_link = vault / "notes" / "manual-broken-link.md"
        manual_broken_link.write_text(
            "---\ntype: observation\n---\n# Manual Broken Link\n\nSee [Documentation](not-there.md).\n",
            encoding="utf-8",
        )
        final_note = next(vault.glob("notes/*/uv-workspace-final*"))
        rc2v = cmd_verify(vault, str(final_note.relative_to(vault)), "human:test")
        block_note = vault / "notes" / "block-verified.md"
        block_note.write_text(
            "---\ntype: observation\nverified:\n  - by: human:old\n"
            "    at: 2026-01-01T00:00:00Z\n---\n# Block Verified\nBody\n",
            encoding="utf-8",
        )
        rc2vb = cmd_verify(vault, str(block_note.relative_to(vault)), "human:new")
        rc_t = cmd_add(vault, _ns(title="Custom Type Test", type="code-graph", tags="",
                                  relevance="low", status="stable", supersedes=None, source=[],
                                  body="Free-form OKF type."))
        long_body = "Plain prose should wrap into readable Markdown paragraphs. " * 4
        rc_format = cmd_add(vault, _ns(title="Formatted Plain Body", type="observation", tags="",
                                       relevance="medium", status="stable", supersedes=None,
                                       source=[], related=[], body=long_body))
        formatted_note = next(vault.glob("notes/*/formatted-plain-body*"))
        formatted_body = parse_note(formatted_note, vault)["body"]
        body_file = Path(td) / "body.md"
        body_file.write_text("## Context\n\n- first item\n- second item\n\n"
                             "```python\nprint('ok')\n```\n", encoding="utf-8")
        body_file_proc = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--vault", str(vault),
             "add", "Body File Markdown", "--body-file", str(body_file),
             "--related", str(old.relative_to(vault))],
            capture_output=True, text=True,
        )
        body_file_note = next(vault.glob("notes/*/body-file-markdown*"), None)
        stdin_proc = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--vault", str(vault),
             "add", "Stdin Body Markdown", "--body-file", "-",
             "--related", str(old.relative_to(vault))],
            input="A stdin body with enough words to verify Markdown input.\n",
            capture_output=True, text=True,
        )
        stdin_note = next(vault.glob("notes/*/stdin-body-markdown*"), None)
        bad_fence_proc = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--vault", str(vault),
             "add", "Malformed Fence", "--body-file", "-"],
            input="## Unclosed\n\n```python\nprint('broken')\n",
            capture_output=True, text=True,
        )
        bad_link_proc = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--vault", str(vault),
             "add", "Broken Markdown Link", "-b", "See [missing](missing-note.md)."],
            capture_output=True, text=True,
        )
        idea_vault = Path(td) / "idea-vault"
        idea_link_proc = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--vault", str(idea_vault),
             "idea", "Capture [draft link](later.md)"],
            capture_output=True, text=True,
        )
        bad_source_proc = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--vault", str(vault),
             "add", "Missing Local Source", "--source", "file://personal/missing.md"],
            capture_output=True, text=True,
        )
        graph_vault = Path(td) / "graph-vault"
        with contextlib.redirect_stdout(io.StringIO()):
            cmd_init(graph_vault)
        (graph_vault / "index.md").write_text(
            "# Human index\n\nKeep root curation.\n\n```html\n"
            "<!-- sb:index:start -->\nPreserve quoted markers.\n<!-- sb:index:end -->\n````\n\n"
            "[Missing curated target](curated-missing.md)\n",
            encoding="utf-8",
        )
        nested = graph_vault / "topics" / "research"
        nested.mkdir(parents=True)
        (nested / "index.md").write_text("# Research notes\n\nKeep folder curation.\n", encoding="utf-8")
        nested_note = nested / "deep note.md"
        nested_note.write_text("---\ntype: reference\n---\n# Deep Note\n\nNested index token.\n", encoding="utf-8")
        node_a = graph_vault / "notes" / "node-a.md"
        node_b = graph_vault / "notes" / "node-b.md"
        node_a.write_text("---\ntype: observation\n---\n# Node A\n\nSee [Node B](node-b.md).\n", encoding="utf-8")
        node_b.write_text(
            "---\ntype: observation\n---\n# Node B\n\n```md\n[Not a real link](not-real.md)\n```\n",
            encoding="utf-8",
        )
        broken_note = graph_vault / "notes" / "broken.md"
        broken_note.write_text("---\ntype: observation\n---\n# Broken\n\n[Missing](missing.md)\n", encoding="utf-8")
        wiki_note = graph_vault / "notes" / "wiki-syntax.md"
        wiki_note.write_text("---\ntype: observation\n---\n# Wiki Syntax\n\n[[Node A]]\n", encoding="utf-8")
        personal = graph_vault / "personal" / "handwritten.md"
        personal.parent.mkdir(parents=True, exist_ok=True)
        personal.write_text("# Handwritten\n\nquartzsource personal-only term.\n", encoding="utf-8")
        personal_original = personal.read_bytes()
        ingest_proc = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--vault", str(graph_vault),
             "add", "Ingested Personal Source", "--source", "file://personal/handwritten.md",
             "--related", "notes/node-a.md", "-b", "A durable fact distilled from the handwritten source."],
            capture_output=True, text=True,
        )
        ingested_note = next(graph_vault.glob("notes/*/ingested-personal-source*"), None)
        untyped_concept = graph_vault / "notes" / "untyped.md"
        untyped_concept.write_text("# Untyped concept\n\nThis still needs OKF type metadata.\n", encoding="utf-8")
        index_output_buf = io.StringIO()
        with contextlib.redirect_stdout(index_output_buf):
            rc_graph_index = cmd_index(graph_vault)
        index_report = index_output_buf.getvalue()
        root_index = graph_vault / "index.md"
        notes_index = graph_vault / "notes" / "index.md"
        topics_index = graph_vault / "topics" / "index.md"
        personal_index = graph_vault / "personal" / "index.md"
        nested_index = nested / "index.md"
        first_index = root_index.read_text(encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()):
            cmd_index(graph_vault)
        repeated_index = root_index.read_text(encoding="utf-8")
        node_b.write_text(node_b.read_text(encoding="utf-8") + "\nManual edit that must make FTS stale.\n", encoding="utf-8")
        root_index.write_text(repeated_index.replace("notes/index.md", "notes/missing-index.md", 1), encoding="utf-8")
        lint_buf = io.StringIO()
        with contextlib.redirect_stdout(lint_buf):
            rc_graph_lint = cmd_lint(graph_vault, fix=False)
        drift_report = lint_buf.getvalue()
        original_broken_note = broken_note.read_bytes()
        original_node_b = node_b.read_bytes()
        fix_buf = io.StringIO()
        with contextlib.redirect_stdout(fix_buf):
            rc_graph_fix = cmd_lint(graph_vault, fix=True)
        fix_report = fix_buf.getvalue()
        orphan_buf = io.StringIO()
        with contextlib.redirect_stdout(orphan_buf):
            rc_graph_orphans = cmd_orphans(graph_vault)
        graph_search_buf = io.StringIO()
        with contextlib.redirect_stdout(graph_search_buf):
            rc_personal_search = cmd_search(graph_vault, "quartzsource", 5, False)
        graph_orphans = orphan_buf.getvalue()
        personal_search = graph_search_buf.getvalue()
        proc = subprocess.run(  # Regression: exercise idea through argparse, not injected namespaces.
            [sys.executable, str(Path(__file__).resolve()), "--vault", str(vault),
             "idea", "Subprocess Idea Regression"],
            capture_output=True, text=True,
        )
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc5 = cmd_search(vault, "workspace", 10, False)
            rc6 = cmd_search(vault, "workspace", 10, True)
            rc7 = cmd_lint(vault, fix=False)
            rc8 = cmd_orphans(vault)
            rc9 = cmd_dedup(vault, 0.75)
        out = buf.getvalue()
        migration_vault = Path(td) / "migration"
        migration_vault.mkdir()
        (migration_vault / "log.md").write_text(
            "---\ntype: changelog\n---\n# Old Log\n\n- old entry\n", encoding="utf-8")
        write_log(migration_vault, "Update", "new entry")
        migrated_log = (migration_vault / "log.md").read_text(encoding="utf-8")
        init_entries = (vault / "log.md").read_text(encoding="utf-8").count("**Initialization**")
        with contextlib.redirect_stdout(io.StringIO()):
            rc0b = cmd_init(vault)
        init_entries_after = (vault / "log.md").read_text(encoding="utf-8").count("**Initialization**")
        known = {"src/b.ts": Path("src/b.ts")}
        wiki_vault = Path(td) / "wiki-vault"
        with contextlib.redirect_stdout(io.StringIO()):
            cmd_init(wiki_vault)
        schema = wiki_vault / "schema.md"
        initial_schema = schema.read_text(encoding="utf-8") if schema.exists() else ""
        if schema.exists():
            schema.write_text(initial_schema + "\nOwner convention.\n", encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()):
            cmd_init(wiki_vault)
        source = wiki_vault / "personal" / "field-notes.md"
        source.write_text("# Field notes\n\nA measured claim.\n", encoding="utf-8")
        first_capture = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--vault", str(wiki_vault),
             "capture", "Research agent study", "--source", "https://example.org/study",
             "--body-file", "-"], input="Measured: bounded tasks succeed.",
            capture_output=True, text=True,
        )
        captured = wiki_vault / "sources" / f"{dt.date.today().isoformat()}-research-agent-study.md"
        original_capture = captured.read_bytes() if captured.exists() else b""
        second_capture = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--vault", str(wiki_vault),
             "capture", "Research agent counterstudy", "--source", "https://example.org/counterstudy",
             "--body-file", "-"], input="Contrary finding: bounded tasks often fail.",
            capture_output=True, text=True,
        )
        counterstudy = wiki_vault / "sources" / f"{dt.date.today().isoformat()}-research-agent-counterstudy.md"
        original = Path(td) / "primary paper.md"
        original.write_bytes(b"# Original\n\nUnmodified source bytes.\n")
        original_capture_proc = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--vault", str(wiki_vault),
             "capture", "Primary paper", "--source", original.as_uri(),
             "--original", str(original), "--body-file", "-"],
            input="Extracted primary text.", capture_output=True, text=True,
        )
        copied_original = wiki_vault / "raw" / f"{dt.date.today().isoformat()}-primary-paper" / original.name
        source_with_original = wiki_vault / "sources" / f"{dt.date.today().isoformat()}-primary-paper.md"
        before_index = copied_original.read_bytes() if copied_original.exists() else b""
        occupied_copy = wiki_vault / "raw" / f"{dt.date.today().isoformat()}-protected-original" / original.name
        occupied_copy.parent.mkdir(parents=True)
        occupied_copy.write_bytes(b"User-owned original bytes")
        protected_capture = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--vault", str(wiki_vault),
             "capture", "Protected original", "--source", original.as_uri(),
             "--original", str(original), "--body-file", "-"],
            input="Excerpt.", capture_output=True, text=True,
        )
        capture_vault = Path(td) / "capture-vault"
        with contextlib.redirect_stdout(io.StringIO()):
            cmd_init(capture_vault)
        capture_original = Path(td) / "capture-original.txt"
        capture_original.write_bytes(b"original revision one")
        capture_url = "https://example.org/evidence"

        def capture_case(body: str, *, title: str = "Evidence", source: str = capture_url,
                         scope: str = "full", body_file: str = "-") -> subprocess.CompletedProcess:
            return subprocess.run(
                [sys.executable, str(Path(__file__).resolve()), "--vault", str(capture_vault),
                 "capture", title, "--source", source, "--body-file", body_file,
                 "--original", str(capture_original), "--scope", scope],
                input=body if body_file == "-" else None, capture_output=True, text=True,
            )

        first_body = "first source text\n\n"
        captured_first = capture_case(first_body)
        capture_first_path = capture_vault / "sources" / f"{dt.date.today().isoformat()}-evidence.md"
        capture_first_bytes = capture_first_path.read_bytes() if capture_first_path.exists() else b""
        capture_log_before = (capture_vault / "log.md").read_bytes()
        capture_index_before = (capture_vault / "index.db").stat().st_ino
        captured_repeat = capture_case(first_body, title="Another title")
        capture_repeat_unchanged = (
            (capture_vault / "log.md").read_bytes() == capture_log_before
            and (capture_vault / "index.db").stat().st_ino == capture_index_before
            and len([p for p in (capture_vault / "sources").glob("*.md") if p.name not in RESERVED]) == 1
        )
        captured_changed = capture_case("second source text")
        capture_second_path = capture_vault / "sources" / f"{dt.date.today().isoformat()}-evidence-2.md"
        captured_other_uri = capture_case(first_body, source="https://other.example/evidence")
        captured_excerpt = capture_case(first_body, scope="excerpt")
        capture_original.write_bytes(b"original revision two")
        captured_new_original = capture_case(first_body)
        captured_bad_body = capture_case("", body_file=str(Path(td) / "no-such-body.md"))
        capture_pages = [p for p in (capture_vault / "sources").glob("*.md") if p.name not in RESERVED]
        legacy_capture = capture_vault / "sources" / "legacy.md"
        legacy_capture.write_text("---\ntype: source\nstatus: draft\n---\n\n# Legacy\n\nOld capture.\n", encoding="utf-8")
        eval_vault = Path(td) / "eval-vault"
        with contextlib.redirect_stdout(io.StringIO()):
            cmd_init(eval_vault)
        alpha = eval_vault / "notes" / "alpha.md"
        beta = eval_vault / "notes" / "beta.md"
        retired = eval_vault / "notes" / "retired.md"
        alpha.write_text("---\ntype: reference\n---\n# Alpha\n\nfirsttoken cobalt cobalt cobalt cobalt cobalt.\n", encoding="utf-8")
        beta.write_text("---\ntype: reference\n---\n# Beta\n\ncobalt.\n", encoding="utf-8")
        retired.write_text("---\ntype: reference\nstatus: deprecated\n---\n# Retired\n\nretiredtoken.\n", encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()):
            cmd_index(eval_vault)
        eval_cases = Path(td) / "cases.jsonl"
        eval_cases.write_text("\n".join(json.dumps(case) for case in (
            {"q": "firsttoken", "gold": ["notes/alpha.md"]},
            {"q": "cobalt", "gold": ["notes/beta.md"]},
            {"q": "missingtoken", "gold": ["notes/alpha.md"]},
            {"q": "retiredtoken", "gold": ["notes/retired.md"]},
        )) + "\n", encoding="utf-8")
        eval_before = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in
                       (alpha, beta, retired, eval_vault / "index.md", eval_vault / "log.md", eval_vault / "index.db")}
        eval_proc = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--vault", str(eval_vault),
             "eval", str(eval_cases)], capture_output=True, text=True,
        )
        eval_search = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--vault", str(eval_vault),
             "search", "cobalt", "-n", "10"], capture_output=True, text=True,
        )
        eval_unchanged = all((p.read_bytes(), p.stat().st_mtime_ns) == old for p, old in eval_before.items())
        bad_cases = Path(td) / "bad-cases.jsonl"
        bad_cases.write_text('{"q":"cobalt","gold":[]}\n', encoding="utf-8")
        eval_bad = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--vault", str(eval_vault),
             "eval", str(bad_cases)], capture_output=True, text=True,
        )
        page_command = [sys.executable, str(Path(__file__).resolve()), "--vault", str(wiki_vault),
                        "page", "concept", "Research agents"]
        page_create = subprocess.run(
            [*page_command, "--body-file", "-", "--source", "file://personal/field-notes.md"],
            input="Research agents assist with bounded tasks [Source](../personal/field-notes.md).",
            capture_output=True, text=True,
        )
        page = wiki_vault / "concepts" / "research-agents.md"
        first_page = page.read_bytes() if page.exists() else b""
        digest = hashlib.sha256(first_page).hexdigest()
        page_unchanged = subprocess.run(
            [*page_command, "--body-file", "-", "--source", "file://personal/field-notes.md"],
            input="Another claim", capture_output=True, text=True,
        )
        page_wrong_digest = subprocess.run(
            [*page_command, "--body-file", "-", "--source", "file://personal/field-notes.md",
             "--expect-sha256", "0" * 64, "--reason", "New evidence"],
            input="Changed claim", capture_output=True, text=True,
        )
        unchanged_after_rejections = page.read_bytes() if page.exists() else b""
        page_bad_link = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--vault", str(wiki_vault),
             "page", "topic", "Broken topic", "--body-file", "-", "--related", f"sources/{captured.name}"],
            input="Claim [without evidence](../sources/absent.md).", capture_output=True, text=True,
        )
        page_update = subprocess.run(
            [*page_command, "--body-file", "-", "--source", "file://personal/field-notes.md",
             "--related", f"sources/{captured.name}", "--related", f"sources/{counterstudy.name}",
             "--expect-sha256", digest, "--reason", "New field evidence"],
            input=(f"One [study](../sources/{captured.name}) reports success; "
                   f"another [study](../sources/{counterstudy.name}) reports failures.\n\n"
                   "## Offen\n\nWhich conditions explain the difference?"),
            capture_output=True, text=True,
        )
        page_after = page.read_text(encoding="utf-8") if page.exists() else ""
        topic_create = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--vault", str(wiki_vault),
             "page", "topic", "Research workflows", "--body-file", "-", "--related", "concepts/research-agents.md"],
            input="A workflow summarized from [research agents](../concepts/research-agents.md).",
            capture_output=True, text=True,
        )
        other_pages = []
        for kind, folder, title in (
            ("entity", "entities", "Research Lab"),
            ("reference", "references", "Model Pricing"),
            ("playbook", "playbooks", "Research Procedure"),
        ):
            result = subprocess.run(
                [sys.executable, str(Path(__file__).resolve()), "--vault", str(wiki_vault),
                 "page", kind, title, "--body-file", "-", "--related", f"sources/{captured.name}"],
                input=f"{title} documented in [source](../sources/{captured.name}).",
                capture_output=True, text=True,
            )
            other_pages.append((result.returncode, wiki_vault / folder / f"{slugify(title)}.md", kind))
        wiki_search_buf = io.StringIO()
        if topic_create.returncode == 0:
            with contextlib.redirect_stdout(wiki_search_buf):
                cmd_search(wiki_vault, "workflow", 5, False)
        wiki_lint_buf = io.StringIO()
        if topic_create.returncode == 0:
            with contextlib.redirect_stdout(wiki_lint_buf):
                cmd_lint(wiki_vault, fix=False)
        # Daily writers must coexist with legacy flat notes and older day folders.
        def add_note_fixture(target: Path, title: str, body: str, *, note_type: str = "observation",
                             supersedes: str | None = None) -> int:
            with contextlib.redirect_stdout(io.StringIO()):
                return cmd_add(target, _ns(
                    title=title, type=note_type, tags="", relevance="low", status="stable",
                    supersedes=supersedes, source=[], body=body))

        legacy = vault / "notes" / "2000-01-01-legacy.md"
        legacy_bytes = b"---\ntype: observation\n---\n# Legacy\n\nKeep this original note.\n"
        legacy.write_bytes(legacy_bytes)
        prior = vault / "notes" / "2000-01-01-prior.md"
        prior.write_text("---\ntype: observation\n---\n# Prior\n\nOriginal flat claim.\n", encoding="utf-8")
        prior_day = vault / "notes" / "2000-01-02" / "prior.md"
        prior_day.parent.mkdir(parents=True)
        prior_day.write_text("---\ntype: observation\n---\n# Prior day\n\nOriginal daily claim.\n", encoding="utf-8")
        daily_notes = vault / "notes" / dt.date.today().isoformat()
        rc_collision1 = add_note_fixture(vault, "Daily collision", "First observation.")
        collision = daily_notes / "daily-collision.md"
        collision_original = collision.read_bytes() if collision.exists() else b""
        rc_collision2 = add_note_fixture(vault, "Daily collision", "Second observation.")
        rc_legacy_replace = add_note_fixture(
            vault, "Flat replacement", "Current flat successor.",
            note_type="decision", supersedes=str(prior.relative_to(vault)))
        rc_day_replace = add_note_fixture(
            vault, "Daily replacement", "Current daily successor.",
            note_type="decision", supersedes=str(prior_day.relative_to(vault)))
        compatibility_lint = io.StringIO()
        with contextlib.redirect_stdout(compatibility_lint):
            cmd_lint(vault, fix=False)
        legacy_search = io.StringIO()
        with contextlib.redirect_stdout(legacy_search):
            rc_legacy_search = cmd_search(vault, "legacy", 5, False)
        reserved_notes_preserved = []
        for title in ("Index", "Log", "Schema"):
            reserved_vault = Path(td) / f"reserved-{title.lower()}"
            add_note_fixture(reserved_vault, title, "Preserve this captured content.")
            reserved_note = reserved_vault / "notes" / dt.date.today().isoformat() / f"{title.lower()}-2.md"
            before = reserved_note.read_bytes() if reserved_note.exists() else b""
            add_note_fixture(reserved_vault, "Ordinary note", "A subsequent capture.")
            reserved_search = io.StringIO()
            with contextlib.redirect_stdout(reserved_search):
                rc_reserved_search = cmd_search(reserved_vault, title.lower(), 5, False)
            reserved_notes_preserved.append(
                bool(before) and reserved_note.read_bytes() == before
                and reserved_note in note_files(reserved_vault)
                and rc_reserved_search == 0 and str(reserved_note) in reserved_search.getvalue())
        date_only = parse_instant("2000-01-01")
        uv_dup = next(vault.glob("notes/*/uv-duplicate*"))
        custom_type = next(vault.glob("notes/*/custom-type-test*"))
        checks = {
            "add and idea use day folders without dating their titles":
                old.parent == vault / "notes" / dt.date.today().isoformat()
                and old.name == "uv-workspace-gotcha.md"
                and parse_note(old, vault)["title"] == "UV Workspace Gotcha"
                and (vault / "notes" / dt.date.today().isoformat() / "marimo-batch-reporting-as-the-default.md").exists(),
            "daily note collisions preserve earlier bytes": rc_collision1 == 0 and rc_collision2 == 0
                and collision_original and collision.read_bytes() == collision_original
                and (daily_notes / "daily-collision-2.md").is_file(),
            "reserved daily filenames remain searchable captures": all(reserved_notes_preserved),
            "legacy flat notes remain unmigrated and searchable": legacy.read_bytes() == legacy_bytes
                and legacy in note_files(vault)
                and rc_legacy_search == 0 and str(legacy) in legacy_search.getvalue()
                and "2000-01-01-legacy.md" in (vault / "notes" / "index.md").read_text(encoding="utf-8"),
            "supersession links work across legacy and daily layouts": rc_legacy_replace == 0 and rc_day_replace == 0
                and parse_note(prior, vault)["status"] == "deprecated"
                and parse_note(prior_day, vault)["status"] == "deprecated"
                and ("Prior", "../2000-01-01-prior.md") in md_links((daily_notes / "flat-replacement.md").read_text(encoding="utf-8"))
                and ("Prior day", "../2000-01-02/prior.md") in md_links((daily_notes / "daily-replacement.md").read_text(encoding="utf-8"))
                and "1 broken links" in compatibility_lint.getvalue(),
            "day folders have navigable indexes": (daily_notes / "index.md").is_file()
                and f"{dt.date.today().isoformat()}/index.md" in (vault / "notes" / "index.md").read_text(encoding="utf-8"),
            "script guidance is English and leaves wiki language to the owner":
                initial_schema.startswith("# Wiki schema\n")
                and "The template language does not set the wiki content language." in initial_schema
                and "Capture is not compilation" in HOOK_BLOCK,
            "project hook and new schema distinguish capture from compilation":
                "Capture is not compilation" in initial_schema
                and "compilation or justified deferral" in HOOK_BLOCK
                and "capture-only" in HOOK_BLOCK
                and "read-only" in HOOK_BLOCK,
            "project hook scopes every documented CLI action": all(
                f'--vault "{{vault}}" {verb}' in HOOK_BLOCK
                for verb in ("search", "capture", "page", "add", "index", "lint")
            ),
            "wiki schema and category directories": all((wiki_vault / name).is_dir() for name in
                ("raw", "entities", "references", "playbooks"))
                and all(label in initial_schema for label in (
                    "raw/", "entities/", "references/", "playbooks/",
                    "## Write for people and agents", "reading views",
                ))
                and schema.read_text(encoding="utf-8") == initial_schema + "\nOwner convention.\n"
                and "schema.md" in (wiki_vault / "index.md").read_text(encoding="utf-8")
                and schema not in note_files(wiki_vault),
            "capture preserves original outside FTS": original_capture_proc.returncode == 0
                and before_index == original.read_bytes()
                and copied_original.read_bytes() == before_index
                and urllib.parse.quote(copied_original.name) in source_with_original.read_text(encoding="utf-8")
                and not any(p.is_relative_to(wiki_vault / "raw") for p in note_files(wiki_vault)),
            "capture never overwrites a raw original": protected_capture.returncode != 0
                and occupied_copy.read_bytes() == b"User-owned original bytes"
                and not (wiki_vault / "sources" / f"{dt.date.today().isoformat()}-protected-original.md").exists(),
            "source capture is a distinct immutable input": first_capture.returncode == 0
                and second_capture.returncode == 0
                and b"type: \"source\"" in original_capture
                and b"Measured: bounded tasks succeed." in original_capture
                and captured.read_bytes() == original_capture,
            "capture is repeat-safe and retains honest source revisions": captured_first.returncode == 0
                and captured_repeat.returncode == 0 and captured_changed.returncode == 0
                and captured_other_uri.returncode == 0 and captured_excerpt.returncode == 0
                and captured_new_original.returncode == 0 and captured_bad_body.returncode != 0
                and capture_repeat_unchanged and len(capture_pages) == 5
                and str(capture_first_path) in captured_repeat.stdout
                and capture_first_path.read_bytes() == capture_first_bytes
                and b'capture_scope: "full"' in capture_first_bytes
                and hashlib.sha256(first_body.encode("utf-8")).hexdigest().encode() in capture_first_bytes
                and b"first source text\n\n\n\n## Original" in capture_first_bytes
                and b'capture_scope: "excerpt"' in b"".join(p.read_bytes() for p in capture_pages)
                and capture_second_path.exists()
                and any(target == capture_first_path.name for _, target in md_links(
                    capture_second_path.read_text(encoding="utf-8")))
                and (capture_vault / "raw" / capture_first_path.stem / capture_original.name).read_bytes()
                    == b"original revision one"
                and parse_note(legacy_capture, capture_vault)["capture_scope"] == "unknown",
            "eval measures real search ranking without writes": eval_proc.returncode == 0
                and eval_search.returncode == 0
                and [line for line in eval_search.stdout.splitlines() if line.startswith(str(eval_vault))]
                    == [str(alpha), str(beta)]
                and eval_unchanged and eval_proc.stdout.count("rank=1") == 1
                and eval_proc.stdout.count("rank=2") == 1
                and "recall@1=25.0%" in eval_proc.stdout
                and "recall@10=50.0%" in eval_proc.stdout
                and "MRR@10=0.375" in eval_proc.stdout,
            "eval rejects empty gold instead of scoring a miss": eval_bad.returncode != 0
                and "gold" in eval_bad.stderr,
            "wiki concept created with source": page_create.returncode == 0
                and b"type: \"concept\"" in first_page and b"status: draft" in first_page
                and b"field-notes.md" in first_page,
            "wiki update requires revision": page_unchanged.returncode != 0
                and page_wrong_digest.returncode != 0 and page_update.returncode == 0
                and unchanged_after_rejections == first_page,
            "invalid wiki link rejected before creation": page_bad_link.returncode != 0
                and not (wiki_vault / "topics" / "broken-topic.md").exists(),
            "wiki revision preserves old content": b"bounded tasks" in first_page
                and "## Offen" in page_after and counterstudy.name in page_after
                and "New field evidence" in (wiki_vault / "log.md").read_text(encoding="utf-8")
                and any(p.read_bytes() == first_page for p in (wiki_vault / ".history" / "concepts" / "research-agents").glob("*.txt")),
            "wiki topic navigable and searchable": topic_create.returncode == 0
                and (wiki_vault / "topics" / "research-workflows.md").exists()
                and (wiki_vault / "concepts" / "index.md").exists()
                and (wiki_vault / "sources" / "index.md").exists()
                and "topics/research-workflows.md" in wiki_search_buf.getvalue()
                and "0 broken links" in wiki_lint_buf.getvalue(),
            "additional page kinds": all(rc == 0 and path.exists()
                and parse_note(path, wiki_vault)["type"] == kind
                and f"{path.parent.name}/index.md" in (wiki_vault / "index.md").read_text(encoding="utf-8")
                for rc, path, kind in other_pages) and "0 broken links" in wiki_lint_buf.getvalue(),
            "non-Latin page slugs are distinct": slugify("知识") != slugify("研究")
                and slugify("知识") == slugify("知识"),
            "init ok": rc0 == 0 and rc0b == 0 and (vault / "index.md").exists(),
            "init idempotent": init_entries == init_entries_after,
            "add ok": rc1 == 0 and rc2 == 0 and rc4 == 0,
            "idea ok": rc3 == 0 and any(vault.glob("notes/*/marimo-batch-reporting-as-the-default*")),
            "idea is draft": "status: draft" in next(vault.glob("notes/*/marimo-batch-reporting-as-the-default*")).read_text(encoding="utf-8"),
            "source ok": "https://docs.astral.sh/uv/" in uv_dup.read_text(encoding="utf-8"),
            "search ok": rc5 == 0 and rc6 == 0,
            "deprecated entries are hidden": "UV Workspace Gotcha" not in out.split("UV Workspace Final")[0],
            "superseded entries visible with --all": out.count("UV Workspace Gotcha") >= 1,
            "deprecated status recorded": "status: deprecated" in old.read_text(encoding="utf-8"),
            "verification recorded": rc2v == 0 and "human:test" in final_note.read_text(encoding="utf-8") and "verified:" in final_note.read_text(encoding="utf-8"),
            "verification preserves block mappings": rc2vb == 0 and "human:old" in block_note.read_text(encoding="utf-8") and "human:new" in block_note.read_text(encoding="utf-8"),
            "custom type supported": rc_t == 0 and parse_note(custom_type, vault)["type"] == "code-graph",
            "plain body is wrapped": rc_format == 0 and max(map(len, formatted_body.splitlines())) <= 88,
            "body-file preserves Markdown": body_file_proc.returncode == 0 and body_file_note is not None
                and "## Context" in body_file_note.read_text(encoding="utf-8")
                and "- first item\n- second item" in body_file_note.read_text(encoding="utf-8")
                and "```python\nprint('ok')\n```" in body_file_note.read_text(encoding="utf-8"),
            "related links use standard Markdown": body_file_note is not None
                and ("UV Workspace Gotcha", old.name) in md_links(body_file_note.read_text(encoding="utf-8")),
            "body-file stdin works": stdin_proc.returncode == 0 and stdin_note is not None
                and "A stdin body with enough words" in stdin_note.read_text(encoding="utf-8"),
            "unclosed fence rejected before write": bad_fence_proc.returncode != 0
                and "unclosed fenced code block" in bad_fence_proc.stderr.lower()
                and not any(vault.glob("notes/*/malformed-fence*")),
            "broken body links rejected before write": bad_link_proc.returncode != 0
                and "link target not found" in bad_link_proc.stderr.lower()
                and not any(vault.glob("notes/*/broken-markdown-link*")),
            "idea captures unresolved links": idea_link_proc.returncode == 0
                and any(idea_vault.glob("notes/*/capture-draft-link*")),
            "missing local source rejected": bad_source_proc.returncode != 0
                and "source" in bad_source_proc.stderr.lower()
                and not any(vault.glob("notes/*/missing-local-source*")),
            "all content directories have indexes": all(path.exists() for path in (
                root_index, notes_index, topics_index, personal_index, nested_index,
            )),
            "generated indexes preserve curation and link documents": "Keep root curation." in first_index
                and "Preserve quoted markers." in first_index
                and "Keep folder curation." in nested_index.read_text(encoding="utf-8")
                and "notes/index.md" in first_index and "node-a.md" in notes_index.read_text(encoding="utf-8")
                and "deep%20note.md" in nested_index.read_text(encoding="utf-8"),
            "index rebuild is deterministic": first_index == repeated_index,
            "lint detects index drift and broken links": rc_graph_lint == 0
                and "index drift" in drift_report.lower() and "FTS drift" in drift_report
                and "missing.md" in drift_report and "curated-missing.md" in drift_report
                and "deep%20note.md" not in drift_report,
            "lint fix repairs only generated artifacts": rc_graph_fix == 0
                and broken_note.read_bytes() == original_broken_note
                and node_b.read_bytes() == original_node_b
                and "notes/index.md" in root_index.read_text(encoding="utf-8")
                and "Keep root curation." in root_index.read_text(encoding="utf-8")
                and "curated-missing.md" in root_index.read_text(encoding="utf-8")
                and "missing-index.md" not in root_index.read_text(encoding="utf-8"),
            "orphan check excludes catalogs and personal sources": rc_graph_orphans == 0
                and "topics/research/deep note.md" in graph_orphans and "notes/node-b.md" not in graph_orphans
                and "personal/handwritten.md" not in graph_orphans,
            "personal sources are FTS searchable": rc_personal_search == 0
                and "personal/handwritten.md" in personal_search,
            "personal ingestion creates source and graph links": ingest_proc.returncode == 0
                and ingested_note is not None
                and ("Handwritten", "../../personal/handwritten.md") in md_links(ingested_note.read_text(encoding="utf-8"))
                and ("Node A", "../node-a.md") in md_links(ingested_note.read_text(encoding="utf-8"))
                and personal.read_bytes() == personal_original,
            "personal source exempt but concepts still require type": rc_graph_index == 0
                and "personal/handwritten.md" not in index_report and "notes/untyped.md" in index_report,
            "lint reports unsupported wikilinks, not code samples": "[[Node A]]" in drift_report
                and "not-real.md" not in drift_report,
            "idea through the actual CLI": proc.returncode == 0 and any(vault.glob("notes/*/subprocess-idea-regression*")),
            "supersession links intact": out.count("    broken:") == 1,  # Only the intentionally missing fixture.
            "log uses OKF §9 groups": f"## {dt.date.today().isoformat()}" in (vault / "log.md").read_text(encoding="utf-8"),
            "log migrates frontmatter": not migrated_log.startswith("---") and "old entry" in migrated_log,
            "verification is visible": "human-verified" in out,
            "log written": (vault / "log.md").exists(),
            "OKF type recorded": parse_note(old, vault)["type"] == "failure",
            "lint finds broken links": rc7 == 0 and "not-there.md" in out,
            "orphans runs": rc8 == 0,
            "dedup finds the pair": rc3b == 0 and rc9 == 0 and "marimo-batch-reporting-as-the-default" in out and "marimo-batch-reporting-copy" in out and "~" in out,
            "meta_name parser": meta_name({"metaVariables": {"single": {"NAME": {"text": "my_fn"}}}}) == "my_fn",
            "date-only stale_after": date_only is not None and date_only.tzinfo is not None,
            "relative import": resolve_import("typescript", "./b", "src/a.ts", known) == Path("src/b.ts"),
            "Markdown parser handles labels and excludes non-links": md_links(
                "[Missing](missing.md) and [A \\[B\\]](node-b.md) "
                "and [space](<space note.md>) and [web](https://example.com/a).\n"
                "```md\n[Code](ignored.md)\n```"
            ) == [
                ("Missing", "missing.md"),
                (r"A \[B\]", "node-b.md"),
                ("space", "space note.md"),
            ],
        }
        failed = [k for k, v in checks.items() if not v]
        if failed:
            sys.exit(f"[sb] selftest FAILED: {failed}\n{out}")
    print(f"[sb] selftest OK ({len(checks)} checks: init/add/idea/verify/cli/capture/supersede/search/eval/lint/orphans/dedup/log)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(prog="sb", description="second-brain CLI (OKF v0.2 + sqlite FTS5)")
    ap.add_argument("--vault", help="Bundle path (default: $SECOND_BRAIN_DIR or ~/second-brain)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init", help="create an OKF bundle and print the AGENTS.md hook")
    sub.add_parser("index", help="rebuild Markdown directory indexes and the FTS5 index")
    sub.add_parser("rebuild", help="alias for index (complete rebuild)")
    sp = sub.add_parser("search", help="full-text search (FTS5 MATCH syntax)")
    sp.add_argument("query")
    sp.add_argument("-n", "--limit", type=int, default=5)
    sp.add_argument("--all", action="store_true", help="include deprecated entries")
    ap_eval = sub.add_parser("eval", help="read-only recall@k and MRR@10 for current FTS ranking")
    ap_eval.add_argument("cases", help="JSONL with q and gold vault-relative Markdown paths")
    ap_add = sub.add_parser("add", help="create a dated OKF note with sources and links")
    ap_add.add_argument("title")
    ap_add.add_argument("-t", "--type", default="observation",
                        help=f"free-form OKF type (OKF §4.1); common: {', '.join(VALID_TYPES)}")
    ap_add.add_argument("-g", "--tags", default="")
    ap_add.add_argument("-r", "--relevance", default="medium", choices=VALID_RELEVANCE)
    body_input = ap_add.add_mutually_exclusive_group()
    body_input.add_argument("-b", "--body", default="")
    body_input.add_argument("--body-file", help="Markdown fragment file, or '-' to read stdin")
    ap_add.add_argument("--related", action="append", default=[],
                        help="related Markdown path relative to the bundle (repeatable)")
    ap_add.add_argument("--status", default="stable", choices=VALID_STATUS)
    ap_add.add_argument("--supersedes", default="", help="bundle-relative path of the concept being replaced")
    ap_add.add_argument("--source", action="append", default=[], help="OKF source URL (repeatable)")
    ap_page = sub.add_parser("page", help="create or explicitly revise a canonical wiki page")
    ap_page.add_argument("kind", choices=tuple(PAGE_FOLDERS))
    ap_page.add_argument("title")
    ap_page.add_argument("--body-file", required=True, help="complete Markdown body; '-' reads stdin")
    ap_page.add_argument("--source", action="append", default=[], help="source URL or file:// path (repeatable)")
    ap_page.add_argument("--related", action="append", default=[], help="bundle-relative evidence/related note (repeatable)")
    ap_page.add_argument("--tags", default="")
    ap_page.add_argument("--status", choices=("draft", "stable"), default="draft")
    ap_page.add_argument("--expect-sha256", default="", help="required to revise an existing page")
    ap_page.add_argument("--reason", default="", help="required change reason for revisions")
    ap_capture = sub.add_parser("capture", help="repeat-safe source snapshot; never overwrite older captures")
    ap_capture.add_argument("title")
    ap_capture.add_argument("--source", required=True, help="original URL or existing file:// path")
    ap_capture.add_argument("--body-file", required=True, help="captured source text, '-' reads stdin")
    ap_capture.add_argument("--original", help="copy the original file unchanged into raw/")
    ap_capture.add_argument("--scope", choices=("full", "excerpt"), default="excerpt",
                            help="attested completeness of supplied text (default: excerpt)")
    ap_idea = sub.add_parser("idea", help="capture an idea as a dated draft insight")
    ap_idea.add_argument("text")
    ap_idea.add_argument("-g", "--tags", default="")
    ap_v = sub.add_parser("verify", help="record verification (OKF §5.2/§5.3 trust tier)")
    ap_v.add_argument("path", help="bundle-relative concept path")
    ap_v.add_argument("--by", default="", help="actor (default human:$USER, e.g. human:vse)")
    ap_lint = sub.add_parser("lint", help="broken links and OKF/health report")
    ap_lint.add_argument("--fix", action="store_true", help="rebuild generated indexes and FTS only")
    sub.add_parser("orphans", help="concepts without inbound links")
    ap_dd = sub.add_parser("dedup", help="find near-duplicate pairs")
    ap_dd.add_argument("-t", "--threshold", type=float, default=0.75)
    ap_cg = sub.add_parser("codegraph", help="symbol/import graph through ast-grep as an OKF concept")
    ap_cg.add_argument("--root", default=".", help="code project root")
    sub.add_parser("stats", help="bundle and index statistics")
    sub.add_parser("selftest", help="round-trip checks in a temporary bundle")
    args = ap.parse_args()

    if args.cmd == "selftest":
        return cmd_selftest()
    vault = Path(args.vault).expanduser() if args.vault else vault_root()
    return {
        "init": lambda: cmd_init(vault),
        "index": lambda: cmd_index(vault),
        "rebuild": lambda: cmd_index(vault),
        "search": lambda: cmd_search(vault, args.query, args.limit, args.all),
        "eval": lambda: cmd_eval(vault, Path(args.cases).expanduser()),
        "add": lambda: cmd_add(vault, args),
        "page": lambda: cmd_page(vault, args),
        "capture": lambda: cmd_capture(vault, args),
        "idea": lambda: cmd_idea(vault, args.text, args),
        "verify": lambda: cmd_verify(vault, args.path, args.by),
        "lint": lambda: cmd_lint(vault, args.fix),
        "orphans": lambda: cmd_orphans(vault),
        "dedup": lambda: cmd_dedup(vault, args.threshold),
        "codegraph": lambda: cmd_codegraph(vault, Path(args.root).expanduser()),
        "stats": lambda: cmd_stats(vault),
    }[args.cmd]()


if __name__ == "__main__":
    sys.exit(main())
