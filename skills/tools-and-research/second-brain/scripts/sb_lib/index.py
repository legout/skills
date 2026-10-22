"""Markdown catalog and FTS5 indexing, search, and evaluation."""

from __future__ import annotations

import datetime as dt
import json
import os
import sqlite3
import sys
import tempfile
import urllib.parse
from pathlib import Path
from .common import (
    INDEX_END,
    INDEX_START,
    PAGE_FOLDERS,
    _mask_fenced_code,
    atomic_write_text,
    connect,
    db_path,
    ensure_bundle,
    markdown_link,
    note_files,
    parse_instant,
    parse_note,
)

def index_catalog(vault: Path) -> dict[Path, list[dict]]:
    """Read each note once for navigation and FTS, grouped by its owning directory."""
    catalog = {vault: [], **{vault / name: [] for name in
               ("notes", "sources", *PAGE_FOLDERS.values(), "personal")}}
    for note in note_files(vault):
        catalog.setdefault(note.parent, []).append(parse_note(note, vault))
        directory = note.parent
        while directory != vault:
            directory = directory.parent
            catalog.setdefault(directory, [])
    return dict(sorted(catalog.items(), key=lambda item:
                       (len(item[0].relative_to(vault).parts), item[0].as_posix())))

def index_block(vault: Path, directory: Path, catalog: dict[Path, list[dict]]) -> str:
    index = directory / "index.md"
    notes = catalog[directory]
    children = [path for path in catalog if path.parent == directory]
    lines = [INDEX_START, "## Documents", ""]
    special = [f"- {markdown_link(index, vault / 'schema.md', 'Wiki schema')}"] if directory == vault else []
    if notes or special:
        lines.extend(special)
        for meta in notes:
            kind = f" — `{meta['type']}`" if meta["type"] else ""
            lines.append(f"- {markdown_link(index, vault / meta['path'], meta['title'])}{kind}")
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

def render_index(vault: Path, directory: Path, catalog: dict[Path, list[dict]]) -> str:
    path = directory / "index.md"
    title = f"{vault.name} — Knowledge Index" if directory == vault else f"{directory.name} — Index"
    existing = path.read_text(encoding="utf-8", errors="replace") if path.exists() else f"# {title}\n"
    existing = existing.replace("\r\n", "\n").replace("\r", "\n")
    # Preserve removal of legacy German placeholders during index migration.
    existing = existing.replace("* [Titel](notes/<slug>.md) - Einzeiler-Claim\n", "")
    existing = existing.replace("Kuratierte Einstiegszeilen (OKF §8-Form):\n\n", "")
    block = index_block(vault, directory, catalog)
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
    catalog = index_catalog(vault)
    rows = sorted((row for notes in catalog.values() for row in notes), key=lambda row: Path(row["path"]))
    untyped = [r["path"] for r in rows if not r["type"] and not r["path"].startswith("personal/")]
    indexes = [(directory / "index.md", render_index(vault, directory, catalog))
               for directory in catalog]
    for path, text in indexes:
        if not path.exists() or path.read_text(encoding="utf-8", errors="replace") != text:
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
                        "INSERT INTO notes(path, title, type, tags, relevance, status, stale_after, verified, body, aliases) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (row["path"], row["title"], row["type"], row["tags"], row["relevance"], row["status"], row["stale_after"], row["verified"], row["body"], row["aliases"]),
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
        " FROM notes WHERE notes MATCH ? AND (? OR status != 'deprecated') ORDER BY rank LIMIT ?",
        (query, show_all, limit),
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
    for i, (line_no, query, _) in enumerate(cases):
        rank = ranks[i]
        print(f"[sb] eval line {line_no}: {'rank=' + str(rank) if rank else 'MISS'} q={json.dumps(query, ensure_ascii=False)}")
    score = " ".join(f"recall@{k}={sum(rank is not None and rank <= k for rank in ranks) / len(ranks):.1%}"
                     for k in (1, 3, 5, 10))
    mrr = sum(1 / rank for rank in ranks if rank is not None) / len(ranks)
    print(f"[sb] eval: {len(ranks)} cases, {score} MRR@10={mrr:.3f}")
    return 0
