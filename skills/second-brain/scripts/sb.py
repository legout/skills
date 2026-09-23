#!/usr/bin/env python3
"""sb.py — second-brain CLI: OKF v0.2 bundle + SQLite FTS5 index.

Stdlib only (codegraph shells out to ast-grep if installed). The bundle
(default ~/second-brain) is the source of truth and a valid Open Knowledge
Format v0.2 bundle; index.db inside it is derived state and can be deleted
any time (`sb index`/`sb rebuild` rebuilds it).

OKF v0.2 mapping:
  notes/*.md, topics/*.md  -> concepts (required frontmatter: type)
  index.md / log.md        -> reserved (listing / update history), not indexed
  type: <value>            -> OKF type (free-form, not centrally registered)
  status/stale_after/verified/generated/sources -> OKF lifecycle/trust/provenance

Claim updates are supersessions, never silent rewrites:
  sb add "New title" --supersedes notes/2026-01-01-old.md ...

Usage:
  sb [--vault PATH] init              create OKF bundle + print AGENTS.md hook
  sb [--vault PATH] index | rebuild   (re)build the FTS5 index
  sb [--vault PATH] search QUERY [-n N] [--all]
  sb [--vault PATH] add "Title" [-t TYPE] [-g TAGS] [-r RELEVANCE] [-b BODY]
                      [--status draft] [--supersedes PATH] [--source URL]...
                      (TYPE ist frei per OKF §4.1; ueblich: observation/decision/insight/failure/reference)
  sb [--vault PATH] verify PATH [--by ACTOR]   OKF-verified vermerken (Default human:$USER)
  sb [--vault PATH] idea "Text"       quick-capture as draft insight
  sb [--vault PATH] lint [--fix]      broken links + OKF/health report
  sb [--vault PATH] orphans           concepts without inbound links
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
import unicodedata
from pathlib import Path

DB_NAME = "index.db"
RESERVED = {"index.md", "log.md"}
VALID_STATUS = ("draft", "stable", "deprecated")
VALID_TYPES = ("observation", "decision", "insight", "failure", "reference")
VALID_RELEVANCE = ("low", "medium", "high", "critical")
ACTOR = "second-brain/1.0"

LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
EXTERNAL_PREFIXES = ("http://", "https://", "mailto:", "#")


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


def connect(vault: Path) -> sqlite3.Connection:
    con = sqlite3.connect(db_path(vault))
    try:
        con.execute(
            "CREATE VIRTUAL TABLE IF NOT EXISTS notes USING fts5("
            "path, title, type, tags, relevance, status, stale_after, verified, body,"
            " tokenize='porter unicode61')"
        )
    except sqlite3.OperationalError as exc:
        con.close()
        sys.exit(f"[sb] FTS5 nicht verfuegbar ({exc}). Grep-Fallback: rg -i <term> {vault}")
    return con


# ── concept parsing (tolerant frontmatter, no yaml dep) ─────────────────────

def parse_note(path: Path, vault: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", text, re.S)
    meta, body = (m.group(1), m.group(2)) if m else ("", text)
    fields: dict[str, str] = {}
    for line in meta.splitlines():
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
        "body": body.strip(),
    }


def _verified_field(fields: dict[str, str], meta: str) -> str:
    """verified als Rohstring — Flow-Map direkt, Listenform via Folgezeilen."""
    verified = fields.get("verified", "")
    if "verified" in fields and not verified:
        vm = re.search(r"^verified:\s*\n((?:[ \t]+- .*\n?)+)", meta, re.M)
        if vm:
            verified = vm.group(1)
    return verified


def note_files(vault: Path) -> list[Path]:
    # Jedes .md im Bundle ist ein Konzept (OKF), reservierte Dateien ausgenommen.
    files = [p for p in vault.rglob("*.md") if p.name not in RESERVED]
    return sorted(files)


def md_links(text: str) -> list[tuple[str, str]]:
    """Alle Markdown-Links (text, target); externe/Anker werden gefiltert."""
    out = []
    for label, target in LINK_RE.findall(text):
        if not target.startswith(EXTERNAL_PREFIXES):
            out.append((label, target.split("#")[0]))
    return [(label, target) for label, target in out if target]


def resolve_link(vault: Path, src: Path, target: str) -> Path:
    """OKF §6.1: '/x.md' ist bundle-relativ, sonst Pfad relativ zur verlinkenden Datei."""
    if target.startswith("/"):
        return vault / target.lstrip("/")
    return Path(os.path.normpath(src.parent / target))


# ── index / search ────────────────────────────────────────────────────────────

def cmd_index(vault: Path) -> int:
    vault = vault.resolve()
    ensure_bundle(vault)
    # Index ist abgeleiteter Zustand: Datei wegwerfen und frisch aufbauen.
    db_path(vault).unlink(missing_ok=True)
    con = connect(vault)
    rows = [parse_note(p, vault) for p in note_files(vault)]
    untyped = [r["path"] for r in rows if not r["type"]]
    with con:
        for r in rows:
            con.execute(
                "INSERT INTO notes(path, title, type, tags, relevance, status, stale_after, verified, body) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (r["path"], r["title"], r["type"], r["tags"], r["relevance"], r["status"], r["stale_after"], r["verified"], r["body"]),
            )
    con.close()
    print(f"[sb] {len(rows)} Konzepte indexiert -> {db_path(vault)}")
    if untyped:
        print(f"[sb] OKF-WARNUNG: {len(untyped)} Datei(en) ohne 'type' (OKF verlangt type):")
        for p in untyped[:10]:
            print(f"    {p}")
    return 0


def cmd_search(vault: Path, query: str, limit: int, show_all: bool) -> int:
    if limit < 1:
        sys.exit("[sb] --limit muss mindestens 1 sein")
    db = db_path(vault)
    if not db.exists():
        print(f"[sb] Kein Index. Erst 'sb index' ausfuehren (oder rg -i {query!r} {vault}).")
        return 1
    con = sqlite3.connect(db)
    # Deprecated-Filter in SQL (nicht limit*3 + Python-Filter: sonst silently < -n Treffer).
    # show_all umgeht den Filter via Sentinel '' — status ist nie leer.
    status_filter = "" if show_all else "deprecated"
    try:
        rows = con.execute(
            "SELECT path, title, type, tags, relevance, status, stale_after, verified,"
            " snippet(notes, 8, '>>', '<<', '…', 12)"
            " FROM notes WHERE notes MATCH ? AND status != ? ORDER BY rank LIMIT ?",
            (query, status_filter, limit),
        ).fetchall()
    except sqlite3.OperationalError as exc:
        con.close()
        sys.exit(f"[sb] Suchfehler ({exc}). Index veraltet? 'sb index' ausfuehren.")
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
                extra = f" ({hidden} deprecated versteckt, --all zeigt sie)"
        con.close()
        print(f"[sb] Keine Treffer fuer {query!r}.{extra}")
        return 1
    con.close()
    return 0


# ── add / idea / init ─────────────────────────────────────────────────────────

def slugify(title: str) -> str:
    s = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return (s or "note")[:80]  # Cap: 255-Byte-Dateinamen-Limit, lange idea-Texte


def write_log(vault: Path, label: str, message: str) -> None:
    """OKF §9: datumsgruppierte Eintraege, neueste Gruppe oben, keine Frontmatter."""
    log = vault / "log.md"
    if not log.exists():
        log.write_text("# Update Log\n", encoding="utf-8")
    text = log.read_text(encoding="utf-8")
    # Alte CLI-Versionen erzeugten log.md mit Frontmatter. Beim ersten neuen
    # Eintrag einmalig auf das OKF-§9-Format migrieren.
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


def ensure_bundle(vault: Path) -> bool:
    """Fehlende OKF-Bundle-Struktur anlegen; True nur bei neuem index.md."""
    vault.mkdir(parents=True, exist_ok=True)
    (vault / "notes").mkdir(exist_ok=True)
    (vault / "topics").mkdir(exist_ok=True)
    index = vault / "index.md"
    created = not index.exists()
    if created:
        index.write_text(
            "---\nokf_version: \"0.2\"\n---\n\n"
            f"# {vault.name} — Knowledge Index\n\n"
            "Kuratierte Einstiegszeilen (OKF §8-Form):\n\n"
            "* [Titel](notes/<slug>.md) - Einzeiler-Claim\n",
            encoding="utf-8",
        )
    if not (vault / "log.md").exists():
        (vault / "log.md").write_text("# Update Log\n", encoding="utf-8")
    if created:
        write_log(vault, "Initialization", f"Bundle erstellt — {now_utc()} by {ACTOR}")
    return created


def deprecate(vault: Path, target: Path, successor_rel: str, successor_title: str) -> None:
    """OKF-Claim-Update: alt bleibt lesbar, wird aber als veraltet markiert."""
    text = target.read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?", text, re.S)
    if not m:
        sys.exit(f"[sb] deprecate: kein Frontmatter: {target.name}")
    meta = m.group(1)
    # Nur Frontmatter anfassen — Body-Zeilen wie 'status: …' duerfen nie getroffen werden.
    if re.search(r"^status:", meta, re.M):
        meta = re.sub(r"^status:.*$", "status: deprecated", meta, count=1, flags=re.M)
    else:
        meta = "status: deprecated\n" + meta
    # OKF §5.2: Deprecation ist eine wesentliche Aenderung -> generated.at mitbumpen.
    meta = re.sub(r"^generated:.*$", f"generated: {{ by: {ACTOR}, at: {now_utc()} }}",
                  meta, count=1, flags=re.M)
    text = f"---\n{meta}\n---\n" + text[m.end():]
    text = text.rstrip("\n") + (
        f"\n\nSuperseded by [{successor_title}]({successor_rel}) ({now_utc()}).\n"
    )
    target.write_text(text, encoding="utf-8")
    rel = target.relative_to(vault.resolve())
    write_log(vault, "Deprecation", f"`{rel}` -> `{successor_rel}` — {now_utc()} by {ACTOR}")


def cmd_add(vault: Path, args: argparse.Namespace) -> int:
    vault = vault.resolve()  # Einmal normalisieren: Target-Links sind resolved
    ensure_bundle(vault)
    args.title = args.title.strip()
    args.type = args.type.strip()
    if not args.title or any(c in args.title for c in "\r\n"):
        sys.exit("[sb] Titel darf nicht leer oder mehrzeilig sein")
    if not args.type or any(c in args.type for c in "\r\n"):
        sys.exit("[sb] --type darf nicht leer oder mehrzeilig sein")
    if args.status not in VALID_STATUS:
        sys.exit(f"[sb] --status muss einer von {VALID_STATUS} sein")
    date = dt.date.today().isoformat()
    stem = f"{date}-{slugify(args.title)}"
    note = vault / "notes" / f"{stem}.md"
    n = 2  # Slug-Kollision am selben Tag: Suffix statt Abbruch (auch fuer non-ASCII-Slugs)
    while note.exists():
        note = vault / "notes" / f"{stem}-{n}.md"
        n += 1
    tags = [t.strip() for t in args.tags.split(",") if t.strip()]
    sources = [url.strip() for url in args.source if url.strip()]
    supersedes_link = ""
    predecessor = None
    if args.supersedes:
        target = (vault / args.supersedes).resolve()
        if (not target.is_relative_to(vault) or not target.is_file()
                or target.name in RESERVED):
            sys.exit(f"[sb] --supersedes: kein regelmaessiges Konzept im Bundle: {args.supersedes}")
        if not re.match(r"^---\s*\n.*?\n---\s*\n?", target.read_text(encoding="utf-8"), re.S):
            sys.exit(f"[sb] --supersedes: Konzept hat kein Frontmatter: {args.supersedes}")
        predecessor = target
        # Datei-relativer Link (OKF §6.1): beide liegen i.d.R. in notes/ -> bloer Dateiname.
        supersedes_link = f"\nSupersedes [{target.stem}]({os.path.relpath(target, note.parent)})."
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
    body = args.body if args.body else "(Hier Body ergaenzen: Was war der Sachverhalt? Pfade, Kommandos, Fehlertexte.)"
    note.parent.mkdir(parents=True, exist_ok=True)
    note.write_text(f"---\n{fm}---\n# {args.title}\n{supersedes_link}\n{body}\n", encoding="utf-8")
    if predecessor is not None:
        # Erst erfolgreich schreiben, dann deprecieren — kein verwaistes 'deprecated' ohne Nachfolger.
        deprecate(vault, predecessor, os.path.relpath(note, predecessor.parent), args.title)
    print(f"[sb] Konzept angelegt: {note}")
    return cmd_index(vault)


def cmd_idea(vault: Path, text: str, args: argparse.Namespace) -> int:
    # argparse setzt Defaults nur des aufgerufenen Subparsers: fehlende Felder ergaenzen.
    args.title = text.strip().rstrip(".")
    args.type = "insight"
    args.status = "draft"
    args.body = text
    args.relevance = getattr(args, "relevance", "low")
    args.supersedes = getattr(args, "supersedes", "")
    args.source = getattr(args, "source", [])
    return cmd_add(vault, args)


def cmd_verify(vault: Path, rel: str, by: str) -> int:
    """OKF §5.2/§5.3: Verifikations-Eintrag anhaengen (Trust-Tier human-reviewed)."""
    vault = vault.resolve()
    if not by:
        by = f"human:{getpass.getuser()}"
    by = by.strip()
    if not re.fullmatch(r"[\w@./:+-]+", by):
        sys.exit("[sb] --by darf nur Buchstaben, Zahlen und @./:+- enthalten")
    target = (vault / rel).resolve()
    if not target.is_relative_to(vault) or not target.is_file() or target.name in RESERVED:
        sys.exit(f"[sb] verify: kein regelmaessiges Konzept im Bundle: {rel}")
    text = target.read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?", text, re.S)
    if not m:
        sys.exit(f"[sb] verify: kein Frontmatter: {rel}")
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
- Projektwissen liegt in `{vault}` (OKF v0.2 Bundle, git-getrackt).
- Vor nicht-trivialen Aufgaben: `uv run {sb} --vault "{vault}" search "<Begriffe>"` (Fallback: rg).
- Dauerhafte Fakten festhalten: `… --vault "{vault}" add "Titel" -t decision -g tags` (niemals Secrets).
- Claims nie stillschweigend umschreiben — superseden: `… --vault "{vault}" add "Neu" --supersedes notes/alt.md` (Pfad relativ zum Bundle); bei Recall status/stale_after beachten.
"""


def cmd_init(vault: Path) -> int:
    """OKF-Bundle-Skeleton anlegen und den AGENTS.md-Hook ausgeben."""
    vault = vault.resolve()
    ensure_bundle(vault)
    try:
        hook_vault = vault.relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        hook_vault = str(vault)
    print(f"[sb] OKF v0.2 Bundle bereit: {vault}")
    print("[sb] Diesen Block in die Projekt-AGENTS.md einfuegen:\n")
    print(HOOK_BLOCK.format(vault=hook_vault, sb=str(Path(__file__).resolve())))
    return cmd_index(vault)


# ── lint / orphans / dedup ────────────────────────────────────────────────────

def iter_concepts(vault: Path):
    for p in note_files(vault):
        yield p, p.read_text(encoding="utf-8", errors="replace")


def cmd_lint(vault: Path, fix: bool) -> int:
    vault = vault.resolve()
    broken: list[tuple[Path, str, str]] = []
    untyped, drafts, deprecated, stale = [], 0, 0, 0
    now = dt.datetime.now(dt.timezone.utc)
    for p, text in iter_concepts(vault):
        meta = parse_note(p, vault)
        if not meta.get("type"):
            untyped.append(p.relative_to(vault))
        if meta.get("status") == "draft":
            drafts += 1
        if meta.get("status") == "deprecated":
            deprecated += 1
        sa = meta.get("stale_after") or ""
        inst = parse_instant(sa) if sa else None
        if inst and now >= inst:
            stale += 1
        for label, target in md_links(text):
            resolved = resolve_link(vault, p, target)
            if not resolved.exists():
                broken.append((p, label, target))
        if fix and any(b[0] == p for b in broken):
            def _neutralize(m: re.Match, _p: Path = p) -> str:
                label, target = m.group(1), m.group(2)
                if target.startswith(EXTERNAL_PREFIXES):
                    return m.group(0)
                if resolve_link(vault, _p, target).exists():
                    return m.group(0)
                return f"{label} <!-- broken-link: {target} -->"
            new_text = LINK_RE.sub(_neutralize, text)
            if new_text != text:
                p.write_text(new_text, encoding="utf-8")
    print(f"[sb] lint: {len(broken)} kaputte Links, {len(untyped)} ohne type, "
          f"{drafts} draft, {deprecated} deprecated, {stale} stale")
    for p, label, target in broken:
        print(f"    kaputt: {p.relative_to(vault)} -> [{label}]({target})")
    for rel in untyped:
        print(f"    ohne type: {rel}")
    if fix and broken:
        print("[sb] --fix: kaputte Links neutralisiert (Text bleibt, Link als Kommentar markiert)")
    # OKF §6.1: kaputte Links sind tolerierbar ("not-yet-written knowledge"),
    # deshalb ist lint nur Report; --fix ist bewusst konservativ.
    return 0


def cmd_orphans(vault: Path) -> int:
    vault = vault.resolve()
    inbound: set[str] = set()
    files = note_files(vault)
    for p, text in iter_concepts(vault):
        for _, target in md_links(text):
            inbound.add(os.path.realpath(resolve_link(vault, p, target)))
    # Links aus jedem index.md zaehlen als Inbound (OKF §8: index auf jeder Ebene).
    for idx in vault.rglob("index.md"):
        for _, target in md_links(idx.read_text(encoding="utf-8", errors="replace")):
            inbound.add(os.path.realpath(resolve_link(vault, idx, target)))
    orphans = [p for p in files if os.path.realpath(p) not in inbound]
    print(f"[sb] {len(orphans)} Orphan(s) ohne Inbound-Links (Kandidaten fuer /dream):")
    for p in orphans:
        print(f"    {p.relative_to(vault)}")
    return 0


def shingles(text: str, n: int = 3) -> set[tuple[str, ...]]:
    # H1-Zeile entfernen: Duplikate haben oft unterschiedliche Titel, gleiche Body.
    text = re.sub(r"^#\s+.+$\n?", "", text, count=1, flags=re.M)
    words = re.findall(r"\w+", text.lower())
    return {tuple(words[i:i + n]) for i in range(max(0, len(words) - n + 1))}


def cmd_dedup(vault: Path, threshold: float) -> int:
    # ponytail: Kandidatenpaare via Shingle-Inverted-Index, dann Jaccard;
    # O(n²) nur noch fuer Kandidaten — reicht bis einige Tausend Konzepte.
    if not 0 <= threshold <= 1:
        sys.exit("[sb] --threshold muss zwischen 0 und 1 liegen")
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
    print(f"[sb] {found} Duplikat-Paar(e) >= {threshold:.0%} Aehnlichkeit "
          "(Loesung: superseden, nicht loeschen)")
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
        sys.exit(f"[sb] ast-grep Timeout fuer Sprache {lang}")
    if proc.returncode not in (0, 1):  # ast-grep: 1 = gueltiges Muster, keine Treffer
        sys.exit(f"[sb] ast-grep fehlgeschlagen: {proc.stderr.strip()[:300]}")
    if not proc.stdout.strip():
        return []
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        sys.exit(f"[sb] ast-grep lieferte ungueltiges JSON: {exc}")


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
    """Codebasis-Symbol-/Importgraph via ast-grep als OKF-Konzept.

    ponytail: v1 mappt python + ts/js (functions/classes/imports); Import-
    Aufloesung ist Heuristik (Basename/Pfadmatch), kein Typ-Resolver.
    Upgrade-Pfad: tatsaechliche Cross-References via LSP, wenn noetig.
    """
    binary = find_ast_grep()
    if not binary:
        sys.exit("[sb] ast-grep nicht gefunden. Install: npm i -g @ast-grep/cli (oder brew install ast-grep)")
    root = root.resolve()
    if not root.is_dir():
        sys.exit(f"[sb] --root ist kein Verzeichnis: {root}")
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
                                # Inline-Code, kein Link: Ziel liegt ausserhalb des Bundles,
                                # Links dorthin wuerden lint/dream dauerhaft vergiften.
                                imports.setdefault(f, set()).add(f"`{mod}` -> `{target.relative_to(root)}`")
                            else:
                                imports.setdefault(f, set()).add(f"`{mod}` -> (extern)")
        for f in sorted(set(symbols) | set(imports)):
            lines = [f"## {f}"]
            lines += [f"- {s}" for s in sorted(symbols.get(f, []))]
            lines += [f"- import {i}" for i in sorted(imports.get(f, []))]
            sections.append("\n".join(lines) + "\n")
    if not sections:
        print("[sb] Keine Treffer — ist --root ein python/ts/js Projekt?")
        return 1
    out = vault / "topics" / "code-graph.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        f"---\ntype: code-graph\ngenerated: {{ by: {ACTOR}, at: {now_utc()} }}\n"
        f"resource: {root}\nrelevance: low\n---\n\n# Code-Graph: {root.name}\n\n"
        + "\n".join(sections),
        encoding="utf-8",
    )
    write_log(vault, "Update", f"code-graph aktualisiert: {root} — {now_utc()} by {ACTOR}")
    print(f"[sb] Code-Graph geschrieben: {out}")
    return cmd_index(vault)


# ── stats / selftest ──────────────────────────────────────────────────────────

def cmd_stats(vault: Path) -> int:
    files = note_files(vault)
    # Frontmatter-basiert (parse_note), nicht Ganzdatei-Regex: Body-Zeilen wie 'status: …' faelschen sonst die Zahl.
    deprecated = sum(1 for p in files if parse_note(p, vault).get("status") == "deprecated")
    print(f"Bundle:      {vault} (OKF v0.2)")
    print(f"Konzepte:    {len(files)} ({deprecated} deprecated)")
    print(f"Index:       {db_path(vault)} ({'vorhanden' if db_path(vault).exists() else 'fehlt - sb index'})")
    return 0


def _ns(**kw):
    return argparse.Namespace(**kw)


def cmd_selftest() -> int:
    with tempfile.TemporaryDirectory() as td:
        vault = Path(td) / "vault"
        rc0 = cmd_init(vault)
        rc1 = cmd_add(vault, _ns(title="UV Workspace Gotcha", type="failure", tags="python, uv",
                                 relevance="high", status="stable", supersedes=None, source=[],
                                 body="uv sync ignoriert workspace-members ohne explicit source. Fix: tool.uv.sources setzen."))
        old = next(vault.glob("notes/*uv-workspace*"))
        rc2 = cmd_add(vault, _ns(title="UV Workspace Final", type="decision", tags="python, uv",
                                 relevance="high", status="stable",
                                 supersedes=str(old.relative_to(vault)), source=[],
                                 body="Endgueltige Loesung: tool.uv.sources + workspace members."))
        rc3 = cmd_idea(vault, "Marimo batch reporting als Standardweg", _ns(tags="", relevance="low", supersedes=None, source=[]))
        rc3b = cmd_add(vault, _ns(title="Marimo Batch Reporting Kopie", type="insight", tags="",
                                  relevance="low", status="stable", supersedes=None, source=[],
                                  body="Marimo batch reporting als Standardweg"))
        rc4 = cmd_add(vault, _ns(title="UV Duplikat", type="failure", tags="python",
                                 relevance="medium", status="stable", supersedes=None, source=["https://docs.astral.sh/uv/"],
                                 body="uv sync ignoriert workspace-members ohne explicit source. Fix: tool.uv.sources setzen. Siehe [Doku](nicht-da.md)."))
        final_note = next(vault.glob("notes/*uv-workspace-final*"))
        rc2v = cmd_verify(vault, str(final_note.relative_to(vault)), "human:test")
        block_note = vault / "notes" / "block-verified.md"
        block_note.write_text(
            "---\ntype: observation\nverified:\n  - by: human:old\n"
            "    at: 2026-01-01T00:00:00Z\n---\n# Block Verified\nBody\n",
            encoding="utf-8",
        )
        rc2vb = cmd_verify(vault, str(block_note.relative_to(vault)), "human:new")
        rc_t = cmd_add(vault, _ns(title="Custom Typ Test", type="code-graph", tags="",
                                  relevance="low", status="stable", supersedes=None, source=[],
                                  body="Freier OKF-Typ."))
        proc = subprocess.run(  # Regression N1: idea via echtem CLI (argparse, nicht Namespace-Injektion)
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
        date_only = parse_instant("2000-01-01")
        uv_dup = next(vault.glob("notes/*uv-duplikat*"))
        custom_type = next(vault.glob("notes/*custom-typ-test*"))
        checks = {
            "init ok": rc0 == 0 and rc0b == 0 and (vault / "index.md").exists(),
            "init idempotent": init_entries == init_entries_after,
            "add ok": rc1 == 0 and rc2 == 0 and rc4 == 0,
            "idea ok": rc3 == 0 and any(vault.glob("notes/*marimo-batch-reporting-als-standardweg*")),
            "idea ist draft": "status: draft" in next(vault.glob("notes/*marimo-batch-reporting-als-standardweg*")).read_text(encoding="utf-8"),
            "source ok": "https://docs.astral.sh/uv/" in uv_dup.read_text(encoding="utf-8"),
            "search ok": rc5 == 0 and rc6 == 0,
            "deprecated versteckt": "UV Workspace Gotcha" not in out.split("UV Workspace Final")[0],
            "supersede sichtbar mit --all": out.count("UV Workspace Gotcha") >= 1,
            "deprecated markiert": "status: deprecated" in old.read_text(encoding="utf-8"),
            "verify schreibt": rc2v == 0 and "human:test" in final_note.read_text(encoding="utf-8") and "verified:" in final_note.read_text(encoding="utf-8"),
            "verify behaelt Block-Mapping": rc2vb == 0 and "human:old" in block_note.read_text(encoding="utf-8") and "human:new" in block_note.read_text(encoding="utf-8"),
            "freier Typ": rc_t == 0 and parse_note(custom_type, vault)["type"] == "code-graph",
            "idea via echtem CLI": proc.returncode == 0 and any(vault.glob("notes/*subprocess-idea-regression*")),
            "supersede-Links ganz": out.count("    kaputt:") == 1,  # nur der absichtliche nicht-da.md
            "log §9-Gruppen": f"## {dt.date.today().isoformat()}" in (vault / "log.md").read_text(encoding="utf-8"),
            "log migriert Frontmatter": not migrated_log.startswith("---") and "old entry" in migrated_log,
            "verify sichtbar": "human-verified" in out,
            "log geschrieben": (vault / "log.md").exists(),
            "okf type vorhanden": parse_note(old, vault)["type"] == "failure",
            "lint findet kaputten Link": rc7 == 0 and "nicht-da.md" in out,
            "orphans laeuft": rc8 == 0,
            "dedup findet Paar": rc3b == 0 and rc9 == 0 and "marimo-batch-reporting-als-standardweg" in out and "marimo-batch-reporting-kopie" in out and "~" in out,
            "meta_name parser": meta_name({"metaVariables": {"single": {"NAME": {"text": "my_fn"}}}}) == "my_fn",
            "date-only stale_after": date_only is not None and date_only.tzinfo is not None,
            "relativer Import": resolve_import("typescript", "./b", "src/a.ts", known) == Path("src/b.ts"),
        }
        failed = [k for k, v in checks.items() if not v]
        if failed:
            sys.exit(f"[sb] selftest FEHLGESCHLAGEN: {failed}\n{out}")
    print(f"[sb] selftest OK ({len(checks)} Checks: init/add/idea/verify/freetyp/cli/source/supersede/search/lint/orphans/dedup/log)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(prog="sb", description="second-brain CLI (OKF v0.2 + sqlite FTS5)")
    ap.add_argument("--vault", help="Bundle-Pfad (Default: $SECOND_BRAIN_DIR oder ~/second-brain)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init", help="OKF-Bundle anlegen + AGENTS.md-Hook ausgeben")
    sub.add_parser("index", help="FTS5-Index aus dem Bundle neu aufbauen")
    sub.add_parser("rebuild", help="Alias fuer index (kompletter Neuaufbau)")
    sp = sub.add_parser("search", help="Volltextsuche (FTS5 MATCH Syntax)")
    sp.add_argument("query")
    sp.add_argument("-n", "--limit", type=int, default=5)
    sp.add_argument("--all", action="store_true", help="auch deprecated zeigen")
    ap_add = sub.add_parser("add", help="Konzept anlegen + indexieren (OKF)")
    ap_add.add_argument("title")
    ap_add.add_argument("-t", "--type", default="observation",
                        help=f"OKF-Typ, frei (OKF §4.1); ueblich: {', '.join(VALID_TYPES)}")
    ap_add.add_argument("-g", "--tags", default="")
    ap_add.add_argument("-r", "--relevance", default="medium", choices=VALID_RELEVANCE)
    ap_add.add_argument("-b", "--body", default="")
    ap_add.add_argument("--status", default="stable", choices=VALID_STATUS)
    ap_add.add_argument("--supersedes", default="", help="Pfad des zu ersetzenden Konzepts (relativ zum Bundle)")
    ap_add.add_argument("--source", action="append", default=[], help="OKF-Quelle (URL), wiederholbar")
    ap_idea = sub.add_parser("idea", help="Idee als draft-insight festhalten")
    ap_idea.add_argument("text")
    ap_idea.add_argument("-g", "--tags", default="")
    ap_v = sub.add_parser("verify", help="Verifikation vermerken (OKF §5.2/§5.3 Trust-Tier)")
    ap_v.add_argument("path", help="Konzept-Pfad relativ zum Bundle")
    ap_v.add_argument("--by", default="", help="Aktor (Default human:$USER, z.B. human:vse)")
    ap_lint = sub.add_parser("lint", help="Kaputte Links + OKF/Health-Report")
    ap_lint.add_argument("--fix", action="store_true", help="kaputte Links neutralisieren")
    sub.add_parser("orphans", help="Konzepte ohne Inbound-Links")
    ap_dd = sub.add_parser("dedup", help="Near-Duplicate-Paare finden")
    ap_dd.add_argument("-t", "--threshold", type=float, default=0.75)
    ap_cg = sub.add_parser("codegraph", help="Symbol-/Importgraph via ast-grep als OKF-Konzept")
    ap_cg.add_argument("--root", default=".", help="Wurzel des Codeprojekts")
    sub.add_parser("stats", help="Bundle-/Index-Statistik")
    sub.add_parser("selftest", help="Round-Trip-Checks in temporaerem Bundle")
    args = ap.parse_args()

    if args.cmd == "selftest":
        return cmd_selftest()
    vault = Path(args.vault).expanduser() if args.vault else vault_root()
    return {
        "init": lambda: cmd_init(vault),
        "index": lambda: cmd_index(vault),
        "rebuild": lambda: cmd_index(vault),
        "search": lambda: cmd_search(vault, args.query, args.limit, args.all),
        "add": lambda: cmd_add(vault, args),
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
