"""Bundle initialization and knowledge write operations."""

from __future__ import annotations

import argparse
import datetime as dt
import getpass
import hashlib
import json
import os
import re
import shutil
import sys
import urllib.parse
from pathlib import Path
from .common import (
    ACTOR,
    CLI_PATH,
    HOOK_BLOCK,
    PAGE_FOLDERS,
    RESERVED,
    VALID_STATUS,
    _capture_fields,
    atomic_write_text,
    dated_path,
    deprecate,
    ensure_bundle,
    file_sha256,
    format_markdown_body,
    markdown_link,
    md_links,
    now_utc,
    parse_note,
    preserved_original,
    project_origins,
    resolve_link,
    slugify,
    source_link,
    write_log,
)
from .index import (
    cmd_index,
)

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
    note = dated_path(vault, "notes", args.title, dt.date.today().isoformat())
    tags = [t.strip() for t in args.tags.split(",") if t.strip()]
    origins = project_origins(args)
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
    if origins:
        fm += f"origin_projects: {json.dumps(origins)}\n"
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
    digest = hashlib.sha256(old).hexdigest() if old is not None else ""
    if old is None and (args.expect_sha256 or args.reason):
        sys.exit("[sb] new page does not accept --expect-sha256 or --reason")
    if old is not None:
        if not args.expect_sha256 or not args.reason or args.expect_sha256 != digest:
            sys.exit(f"[sb] page exists; revision requires --expect-sha256 {digest} and --reason")
        if parse_note(page, vault)["title"] != title:
            sys.exit("[sb] slug collision: existing page has a different title")
    origins = project_origins(args, _capture_fields(page).get("origin_projects", "") if old is not None else "")
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
    if origins:
        fm += f"origin_projects: {json.dumps(origins)}\n"
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
    archive: Path | None = None
    if old is not None:
        archive = vault / ".history" / page.parent.name / page.stem / f"{now_utc().replace(':', '')}-{digest[:12]}.txt"
        archive.parent.mkdir(parents=True, exist_ok=True)
        archive.write_bytes(old)
    atomic_write_text(page, rendered)
    if archive is not None:
        write_log(vault, "Wiki revision", f"`{page.relative_to(vault)}`: {args.reason} — prior `{archive.relative_to(vault)}` (SHA-256 {digest})")
    else:
        write_log(vault, "Wiki page", f"`{page.relative_to(vault)}` created")
    print(f"[sb] wiki page: {page}")
    return cmd_index(vault)

def cmd_capture(vault: Path, args: argparse.Namespace) -> int:
    """Keep supplied source text as an immutable, repeat-safe Markdown snapshot."""
    vault = vault.resolve()
    ensure_bundle(vault)
    title = args.title.strip()
    if not title or any(c in title for c in "\r\n"):
        sys.exit("[sb] capture title must be a single nonempty line")
    capture_day = dt.date.today().isoformat()
    origins = project_origins(args)
    archive_original = getattr(args, "archive_original", False)
    if archive_original and not args.original:
        sys.exit("[sb] capture: --archive-original requires --original")
    original = Path(args.original).expanduser().resolve() if args.original else None
    if original is None and args.source.startswith("file://"):
        original = Path(urllib.parse.unquote(args.source[7:])).expanduser()
        original = (original if original.is_absolute() else vault / original).resolve()
    if original is not None and not original.is_file():
        sys.exit(f"[sb] capture: original file not found: {original}")
    try:
        body = sys.stdin.read() if args.body_file == "-" else Path(args.body_file).expanduser().read_text(encoding="utf-8")
        if not body.strip():
            raise ValueError("source text must not be empty")
        original_hash = file_sha256(original) if original is not None else ""
    except (OSError, ValueError) as exc:
        sys.exit(f"[sb] capture: {exc}")
    body_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()
    previous = None
    archived_copy = (original if archive_original and original is not None
                     and any(original.is_relative_to(vault / folder) for folder in ("_raw", "raw")) else None)
    for path in (vault / "sources").rglob("*.md"):
        if path.name in RESERVED:
            continue
        meta = _capture_fields(path)
        if archive_original and archived_copy is None and meta.get("original_sha256") == original_hash:
            archived_copy = preserved_original(vault, path, meta, original_hash)
        if (meta.get("source_uri") != args.source or meta.get("capture_scope") not in ("full", "excerpt")
                or not re.fullmatch(r"[0-9a-f]{64}", meta.get("content_sha256", ""))):
            continue  # Ignore unrelated and unmarked or malformed captures.
        if previous is None or path.stat().st_mtime_ns > previous.stat().st_mtime_ns:
            previous = path
        if (meta["content_sha256"] == body_hash and meta["capture_scope"] == args.scope
                and meta.get("original_sha256", "") == original_hash
                and set(meta.get("origin_projects", "").split(", ") if meta.get("origin_projects") else []) == set(origins)
                and (not archive_original or preserved_original(vault, path, meta, original_hash) is not None)):
            print(f"[sb] existing capture: {path}")
            return 0
    snapshot = dated_path(vault, "sources", title, capture_day)
    try:
        link = source_link(vault, snapshot, args.source, 1)
    except ValueError as exc:
        sys.exit(f"[sb] capture: {exc}")
    frontmatter = (f'type: "source"\n'
                   f'generated: {{ by: {ACTOR}, at: {now_utc()} }}\n'
                   f'capture_scope: {json.dumps(args.scope)}\n'
                   f'source_uri: {json.dumps(args.source, ensure_ascii=False)}\n'
                   f'content_sha256: {body_hash}\n'
                   f'original_sha256: {original_hash}\n'
                   f'sources:\n  - {{ resource: {json.dumps(args.source, ensure_ascii=False)} }}\n')
    if origins:
        frontmatter += f"origin_projects: {json.dumps(origins)}\n"
    original_links = [f"- {link}"]
    if original is not None:
        frontmatter += f'original_uri: {json.dumps(original.as_uri(), ensure_ascii=False)}\n'
        if archive_original:
            if archived_copy is None:
                archived_copy = vault / "_raw" / f"{snapshot.parent.name}-{snapshot.stem}" / original.name
                archived_copy.parent.mkdir(parents=True, exist_ok=True)
                try:
                    with original.open("rb") as source_file, archived_copy.open("xb") as target_file:
                        shutil.copyfileobj(source_file, target_file)
                except OSError as exc:
                    sys.exit(f"[sb] capture: cannot preserve original without overwriting: {exc}")
            frontmatter += f'preserved_original: {json.dumps(archived_copy.relative_to(vault).as_posix(), ensure_ascii=False)}\n'
            original_links.append(f"- {markdown_link(snapshot, archived_copy, 'Preserved original')}")
        elif original.as_uri() != args.source:
            original_links.append(f"- {source_link(vault, snapshot, original.as_uri(), 2)}")
    sections = [f"# {title}", body, "## Original", "\n".join(original_links)]
    if previous is not None:
        sections.extend(("## Previous capture", f"- {markdown_link(snapshot, previous, parse_note(previous, vault)['title'])}"))
    snapshot.parent.mkdir(parents=True, exist_ok=True)
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
    print(HOOK_BLOCK.format(vault=hook_vault, sb=str(CLI_PATH)))
    return cmd_index(vault)
