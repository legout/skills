"""Bundle validation, graph checks, deduplication, and statistics."""

from __future__ import annotations

import datetime as dt
import json
import os
import posixpath
import re
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path
from .common import (
    ACTOR,
    PATTERNS,
    WIKILINK_RE,
    db_path,
    markdown_outside_code,
    md_links,
    note_files,
    now_utc,
    parse_instant,
    parse_note,
    resolve_link,
    write_log,
)
from .index import (
    cmd_index,
    index_directories,
    render_index,
)

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
