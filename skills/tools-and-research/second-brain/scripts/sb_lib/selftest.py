"""Temporary-bundle integration checks for the Second Brain CLI."""

from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import hashlib
import io
import json
import sqlite3
import subprocess
import sys
import tempfile
import urllib.parse
from pathlib import Path
from .common import (
    CLI_PATH,
    HOOK_BLOCK,
    RESERVED,
    _capture_fields,
    db_path,
    file_sha256,
    md_links,
    note_files,
    parse_instant,
    parse_note,
    slugify,
    write_log,
)
from .index import (
    cmd_index,
    cmd_search,
    index_directories,
)
from .write import (
    cmd_add,
    cmd_idea,
    cmd_init,
    cmd_verify,
)
from .maintenance import (
    cmd_dedup,
    cmd_lint,
    cmd_orphans,
    meta_name,
    resolve_import,
)

def _ns(**kw):
    return argparse.Namespace(**kw)

def cmd_selftest() -> int:
    with tempfile.TemporaryDirectory() as td:
        vault = Path(td) / "vault"
        rc0 = cmd_init(vault)
        rc1 = cmd_add(vault, _ns(title="UV Workspace Gotcha", type="failure", tags="python, uv",
                                 origin_project=["featherbi", "featherbi"],
                                 relevance="high", status="stable", supersedes=None, source=[],
                                 body="uv sync ignores workspace members without an explicit source. Fix: set tool.uv.sources."))
        old = next(vault.glob("notes/*/uv-workspace*"))
        rc2 = cmd_add(vault, _ns(title="UV Workspace Final", type="decision", tags="python, uv",
                                 relevance="high", status="stable",
                                 supersedes=str(old.relative_to(vault)), source=[],
                                 body="Final solution: tool.uv.sources + workspace members."))
        rc3 = cmd_idea(vault, "Marimo batch reporting as the default", _ns(tags="", relevance="low", supersedes=None, source=[], origin_project=["featherbi"]))
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
            [sys.executable, str(CLI_PATH), "--vault", str(vault),
             "add", "Body File Markdown", "--body-file", str(body_file),
             "--related", str(old.relative_to(vault))],
            capture_output=True, text=True,
        )
        body_file_note = next(vault.glob("notes/*/body-file-markdown*"), None)
        stdin_proc = subprocess.run(
            [sys.executable, str(CLI_PATH), "--vault", str(vault),
             "add", "Stdin Body Markdown", "--body-file", "-",
             "--related", str(old.relative_to(vault))],
            input="A stdin body with enough words to verify Markdown input.\n",
            capture_output=True, text=True,
        )
        stdin_note = next(vault.glob("notes/*/stdin-body-markdown*"), None)
        bad_fence_proc = subprocess.run(
            [sys.executable, str(CLI_PATH), "--vault", str(vault),
             "add", "Malformed Fence", "--body-file", "-"],
            input="## Unclosed\n\n```python\nprint('broken')\n",
            capture_output=True, text=True,
        )
        bad_link_proc = subprocess.run(
            [sys.executable, str(CLI_PATH), "--vault", str(vault),
             "add", "Broken Markdown Link", "-b", "See [missing](missing-note.md)."],
            capture_output=True, text=True,
        )
        idea_vault = Path(td) / "idea-vault"
        idea_link_proc = subprocess.run(
            [sys.executable, str(CLI_PATH), "--vault", str(idea_vault),
             "idea", "Capture [draft link](later.md)"],
            capture_output=True, text=True,
        )
        bad_source_proc = subprocess.run(
            [sys.executable, str(CLI_PATH), "--vault", str(vault),
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
            [sys.executable, str(CLI_PATH), "--vault", str(graph_vault),
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
            [sys.executable, str(CLI_PATH), "--vault", str(vault),
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
            [sys.executable, str(CLI_PATH), "--vault", str(wiki_vault),
             "capture", "Research agent study", "--source", "https://example.org/study",
             "--body-file", "-"], input="Measured: bounded tasks succeed.",
            capture_output=True, text=True,
        )
        capture_day = dt.date.today().isoformat()
        captured = wiki_vault / "sources" / capture_day / "research-agent-study.md"
        original_capture = captured.read_bytes() if captured.exists() else b""
        second_capture = subprocess.run(
            [sys.executable, str(CLI_PATH), "--vault", str(wiki_vault),
             "capture", "Research agent counterstudy", "--source", "https://example.org/counterstudy",
             "--body-file", "-"], input="Contrary finding: bounded tasks often fail.",
            capture_output=True, text=True,
        )
        counterstudy = wiki_vault / "sources" / capture_day / "research-agent-counterstudy.md"
        captured_rel = captured.relative_to(wiki_vault).as_posix()
        counterstudy_rel = counterstudy.relative_to(wiki_vault).as_posix()
        original = Path(td) / "primary paper.md"
        original.write_bytes(b"# Original\n\nUnmodified source bytes.\n")
        original_capture_proc = subprocess.run(
            [sys.executable, str(CLI_PATH), "--vault", str(wiki_vault),
             "capture", "Primary paper", "--source", original.as_uri(),
             "--original", str(original), "--archive-original", "--body-file", "-"],
            input="Extracted primary text.", capture_output=True, text=True,
        )
        copied_original = wiki_vault / "_raw" / f"{dt.date.today().isoformat()}-primary-paper" / original.name
        source_with_original = wiki_vault / "sources" / capture_day / "primary-paper.md"
        before_index = copied_original.read_bytes() if copied_original.exists() else b""
        protected_original = Path(td) / "protected-original.md"
        protected_original.write_bytes(b"A distinct incoming original for the collision test.")
        occupied_copy = wiki_vault / "_raw" / f"{dt.date.today().isoformat()}-protected-original" / protected_original.name
        occupied_copy.parent.mkdir(parents=True)
        occupied_copy.write_bytes(b"User-owned original bytes")
        protected_capture = subprocess.run(
            [sys.executable, str(CLI_PATH), "--vault", str(wiki_vault),
             "capture", "Protected original", "--source", protected_original.as_uri(),
             "--original", str(protected_original), "--archive-original", "--body-file", "-"],
            input="Excerpt.", capture_output=True, text=True,
        )
        capture_vault = Path(td) / "capture-vault"
        with contextlib.redirect_stdout(io.StringIO()):
            cmd_init(capture_vault)
        capture_original = Path(td) / "capture-original.txt"
        capture_original.write_bytes(b"original revision one")
        capture_url = "https://example.org/evidence"

        def capture_case(body: str, *, title: str = "Evidence", source: str = capture_url,
                         scope: str = "full", body_file: str = "-",
                         origin_project: str | None = None) -> subprocess.CompletedProcess:
            return subprocess.run(
                [sys.executable, str(CLI_PATH), "--vault", str(capture_vault),
                 "capture", title, "--source", source, "--body-file", body_file,
                  "--original", str(capture_original), "--archive-original", "--scope", scope,
                  *(["--origin-project", origin_project] if origin_project is not None else [])],
                input=body if body_file == "-" else None, capture_output=True, text=True,
            )

        first_body = "first source text\n\n"
        captured_first = capture_case(first_body)
        capture_first_path = capture_vault / "sources" / capture_day / "evidence.md"
        capture_first_bytes = capture_first_path.read_bytes() if capture_first_path.exists() else b""
        capture_log_before = (capture_vault / "log.md").read_bytes()
        capture_index_before = (capture_vault / "index.db").stat().st_ino
        captured_repeat = capture_case(first_body, title="Another title")
        capture_repeat_unchanged = (
            (capture_vault / "log.md").read_bytes() == capture_log_before
            and (capture_vault / "index.db").stat().st_ino == capture_index_before
            and len([p for p in (capture_vault / "sources").rglob("*.md") if p.name not in RESERVED]) == 1
        )
        captured_changed = capture_case("second source text")
        capture_second_path = capture_vault / "sources" / capture_day / "evidence-2.md"
        captured_other_uri = capture_case(first_body, source="https://other.example/evidence")
        captured_excerpt = capture_case(first_body, scope="excerpt")
        capture_original.write_bytes(b"original revision two")
        captured_new_original = capture_case(first_body)
        captured_bad_body = capture_case("", body_file=str(Path(td) / "no-such-body.md"))
        capture_pages = [p for p in (capture_vault / "sources").rglob("*.md") if p.name not in RESERVED]
        reserved_capture = capture_case("Reserved capture filename.", title="Index",
                                        source="https://example.org/reserved-capture")
        reserved_capture_path = capture_vault / "sources" / capture_day / "index-2.md"
        origin_url = "https://example.org/project-evidence"
        origin_capture = capture_case("Project evidence.", title="Project evidence", source=origin_url,
                                      origin_project="featherbi")
        origin_path = capture_vault / "sources" / capture_day / "project-evidence.md"
        origin_verify_output = io.StringIO()
        with contextlib.redirect_stdout(origin_verify_output):
            origin_verify_rc = cmd_verify(
                capture_vault, str(origin_path.relative_to(capture_vault)), "human:test")
        origin_bytes = origin_path.read_bytes() if origin_path.exists() else b""
        origin_repeat = capture_case("Project evidence.", source=origin_url, origin_project="featherbi")
        origin_other = capture_case("Project evidence.", title="Project evidence", source=origin_url,
                                    origin_project="skills")
        origin_other_path = origin_path.with_stem(origin_path.stem + "-2")
        origin_invalid = capture_case("Project evidence.", source=origin_url, origin_project="/local/project")
        legacy_capture = capture_vault / "sources" / "legacy.md"
        legacy_capture.write_text("---\ntype: source\nstatus: draft\n---\n\n# Legacy\n\nOld capture.\n", encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()):
            cmd_index(capture_vault)
        index_con = sqlite3.connect(db_path(capture_vault))
        try:
            indexed_origin_status = index_con.execute(
                "SELECT status FROM notes WHERE path = ?", (origin_path.relative_to(capture_vault).as_posix(),)
            ).fetchone()[0]
            indexed_legacy_status = index_con.execute(
                "SELECT status FROM notes WHERE path = ?", (legacy_capture.relative_to(capture_vault).as_posix(),)
            ).fetchone()[0]
        finally:
            index_con.close()
        source_lint_output = io.StringIO()
        with contextlib.redirect_stdout(source_lint_output):
            cmd_lint(capture_vault, fix=False)
        legacy_capture_vault = Path(td) / "legacy-capture-vault"
        with contextlib.redirect_stdout(io.StringIO()):
            cmd_init(legacy_capture_vault)
        legacy_flat_capture = legacy_capture_vault / "sources" / "2000-01-01-evidence.md"
        legacy_body = "Legacy source text."
        legacy_flat_capture.write_text(
            f'---\ntype: source\nstatus: draft\ncapture_scope: "excerpt"\n'
            f'source_uri: {json.dumps(capture_url)}\n'
            f'content_sha256: {hashlib.sha256(legacy_body.encode()).hexdigest()}\n'
            'original_sha256: ""\n---\n\n# Evidence\n\nLegacy source text.\n',
            encoding="utf-8",
        )
        legacy_flat_bytes = legacy_flat_capture.read_bytes()
        with contextlib.redirect_stdout(io.StringIO()):
            cmd_index(legacy_capture_vault)
        legacy_repeat = subprocess.run(
            [sys.executable, str(CLI_PATH), "--vault", str(legacy_capture_vault),
             "capture", "Evidence", "--source", capture_url, "--body-file", "-"],
            input=legacy_body, capture_output=True, text=True,
        )
        legacy_revision = subprocess.run(
            [sys.executable, str(CLI_PATH), "--vault", str(legacy_capture_vault),
             "capture", "Evidence", "--source", capture_url, "--body-file", "-"],
            input="Updated source text.", capture_output=True, text=True,
        )
        legacy_dated_capture = legacy_capture_vault / "sources" / capture_day / "evidence.md"
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
            [sys.executable, str(CLI_PATH), "--vault", str(eval_vault),
             "eval", str(eval_cases)], capture_output=True, text=True,
        )
        eval_search = subprocess.run(
            [sys.executable, str(CLI_PATH), "--vault", str(eval_vault),
             "search", "cobalt", "-n", "10"], capture_output=True, text=True,
        )
        eval_unchanged = all((p.read_bytes(), p.stat().st_mtime_ns) == old for p, old in eval_before.items())
        bad_cases = Path(td) / "bad-cases.jsonl"
        bad_cases.write_text('{"q":"cobalt","gold":[]}\n', encoding="utf-8")
        eval_bad = subprocess.run(
            [sys.executable, str(CLI_PATH), "--vault", str(eval_vault),
             "eval", str(bad_cases)], capture_output=True, text=True,
        )
        page_command = [sys.executable, str(CLI_PATH), "--vault", str(wiki_vault),
                        "page", "concept", "Research agents"]
        page_create = subprocess.run(
            [*page_command, "--body-file", "-", "--source", "file://personal/field-notes.md",
             "--origin-project", "featherbi"],
            input="Research agents assist with bounded tasks [Source](../personal/field-notes.md).",
            capture_output=True, text=True,
        )
        page = wiki_vault / "concepts" / "research-agents.md"
        first_page = page.read_bytes() if page.exists() else b""
        # Owner-authored block lists must survive CLI revisions too.
        first_page = first_page.replace(b'origin_projects: ["featherbi"]', b'origin_projects:\n  - featherbi')
        if page.exists():
            page.write_bytes(first_page)
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
            [sys.executable, str(CLI_PATH), "--vault", str(wiki_vault),
            "page", "topic", "Broken topic", "--body-file", "-", "--related", captured_rel],
            input="Claim [without evidence](../sources/absent.md).", capture_output=True, text=True,
        )
        page_update = subprocess.run(
            [*page_command, "--body-file", "-", "--source", "file://personal/field-notes.md",
             "--related", captured_rel, "--related", counterstudy_rel,
             "--expect-sha256", digest, "--reason", "New field evidence",
             "--origin-project", "skills", "--origin-project", "featherbi"],
            input=(f"One [study](../{captured_rel}) reports success; "
                   f"another [study](../{counterstudy_rel}) reports failures.\n\n"
                   "## Offen\n\nWhich conditions explain the difference?"),
            capture_output=True, text=True,
        )
        page_after = page.read_text(encoding="utf-8") if page.exists() else ""
        origin_page_revision = subprocess.run(
            [*page_command, "--body-file", "-", "--source", "file://personal/field-notes.md",
             "--related", captured_rel, "--related", counterstudy_rel,
             "--expect-sha256", hashlib.sha256(page_after.encode()).hexdigest(),
             "--reason", "Clarified wording without new origin"],
            input=(f"One [study](../{captured_rel}) reports success; "
                   f"another [study](../{counterstudy_rel}) reports failures under other conditions."),
            capture_output=True, text=True,
        )
        topic_create = subprocess.run(
            [sys.executable, str(CLI_PATH), "--vault", str(wiki_vault),
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
                [sys.executable, str(CLI_PATH), "--vault", str(wiki_vault),
                 "page", kind, title, "--body-file", "-", "--related", captured_rel],
                input=f"{title} documented in [source](../{captured_rel}).",
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
        local_vault = Path(td) / "local-original-vault"
        local_document = Path(td) / "existing-document.txt"
        local_document.write_bytes(b"Existing local version one.")
        local_original_hash = file_sha256(local_document)
        local_capture = subprocess.run(
            [sys.executable, str(CLI_PATH), "--vault", str(local_vault),
             "capture", "Local original", "--source", local_document.as_uri(),
             "--original", str(local_document), "--body-file", "-"],
            input="Source excerpt.", capture_output=True, text=True,
        )
        local_sources = [p for p in (local_vault / "sources").rglob("*.md") if p.name not in RESERVED]
        implicit_local_capture = subprocess.run(
            [sys.executable, str(CLI_PATH), "--vault", str(local_vault),
             "capture", "Local file URI", "--source", local_document.as_uri(), "--body-file", "-"],
            input="Source excerpt.", capture_output=True, text=True,
        )
        missing_archive_original = subprocess.run(
            [sys.executable, str(CLI_PATH), "--vault", str(local_vault),
             "capture", "Invalid archive", "--source", local_document.as_uri(),
             "--archive-original", "--body-file", "-"],
            input="Source excerpt.", capture_output=True, text=True,
        )
        implicit_local_source_count = len([p for p in (local_vault / "sources").rglob("*.md") if p.name not in RESERVED])
        local_first_bytes = local_sources[0].read_bytes() if local_sources else b""
        local_document.write_bytes(b"Existing local version two.")
        changed_local_capture = subprocess.run(
            [sys.executable, str(CLI_PATH), "--vault", str(local_vault),
             "capture", "Local version update", "--source", local_document.as_uri(), "--body-file", "-"],
            input="Source excerpt.", capture_output=True, text=True,
        )
        changed_local_sources = [p for p in (local_vault / "sources").rglob("*.md") if p.name not in RESERVED]
        local_archive_files = [p for name in ("raw", "_raw") for p in (local_vault / name).rglob("*") if p.is_file()]
        archive_vault = Path(td) / "archive-exclusion-vault"
        with contextlib.redirect_stdout(io.StringIO()):
            cmd_init(archive_vault)
        for archive_name in ("raw", "_raw"):
            archive_dir = archive_vault / archive_name
            archive_dir.mkdir(exist_ok=True)
            (archive_dir / "original.md").write_text("Unchanged original bytes.\n", encoding="utf-8")
        legacy_asset_vault = Path(td) / "legacy-original-vault"
        with contextlib.redirect_stdout(io.StringIO()):
            cmd_init(legacy_asset_vault)
        legacy_asset_source = legacy_asset_vault / "sources" / "2000-01-01-legacy-asset.md"
        legacy_asset = legacy_asset_vault / "raw" / legacy_asset_source.stem / original.name
        legacy_asset.parent.mkdir(parents=True)
        legacy_asset.write_bytes(original.read_bytes())
        legacy_body = "Previously captured source text."
        legacy_asset_uri = "https://example.org/legacy-asset"
        legacy_asset_source.write_text(
            f'---\ntype: source\nstatus: draft\ncapture_scope: excerpt\nsource_uri: {json.dumps(legacy_asset_uri)}\n'
            f'content_sha256: {hashlib.sha256(legacy_body.encode()).hexdigest()}\noriginal_sha256: {file_sha256(original)}\n---\n'
            f'\n# Legacy asset\n\n{legacy_body}\n\n[Original](../raw/{legacy_asset_source.stem}/{urllib.parse.quote(original.name)})\n',
            encoding="utf-8",
        )
        legacy_asset_before = legacy_asset_source.read_bytes()
        reused_legacy_asset = subprocess.run(
            [sys.executable, str(CLI_PATH), "--vault", str(legacy_asset_vault),
             "capture", "Legacy asset", "--source", legacy_asset_uri,
             "--original", str(original), "--archive-original", "--body-file", "-"],
            input=legacy_body, capture_output=True, text=True,
        )
        uv_dup = next(vault.glob("notes/*/uv-duplicate*"))
        custom_type = next(vault.glob("notes/*/custom-type-test*"))
        checks = {
            "provided original paths are hashed without copying by default": local_capture.returncode == 0
                and len(local_sources) == 1 and not local_archive_files
                and _capture_fields(local_sources[0]).get("original_sha256") == local_original_hash,
            "local file URIs preserve provenance without extra original flags": implicit_local_capture.returncode == 0
                and str(local_sources[0]) in implicit_local_capture.stdout
                and _capture_fields(local_sources[0]).get("original_uri") == local_document.resolve().as_uri()
                and implicit_local_source_count == 1,
            "local version changes create honest captures without archived copies": changed_local_capture.returncode == 0
                and len(changed_local_sources) == 2 and not local_archive_files
                and local_sources[0].read_bytes() == local_first_bytes
                and any(_capture_fields(p).get("original_sha256") == file_sha256(local_document) for p in changed_local_sources),
            "archiving requires an explicitly supplied original": missing_archive_original.returncode != 0
                and "--archive-original requires --original" in missing_archive_original.stderr,
            "recaptures reuse stored bytes across excerpts and source URIs":
                len([p for p in (capture_vault / "_raw").rglob("*") if p.is_file()]) == 2
                and len(capture_pages) == 5,
            "legacy raw originals and source links are reused without migration": reused_legacy_asset.returncode == 0
                and legacy_asset_source.read_bytes() == legacy_asset_before
                and legacy_asset.read_bytes() == original.read_bytes()
                and not any(p.is_file() for p in (legacy_asset_vault / "_raw").rglob("*")),
            "new and legacy original archives are excluded from knowledge indexes": not note_files(archive_vault)
                and archive_vault / "_raw" not in index_directories(archive_vault)
                and archive_vault / "raw" not in index_directories(archive_vault),
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
                and "sources/YYYY-MM-DD/slug.md" in initial_schema
                and "stay where they are" in HOOK_BLOCK
                and "compilation or justified deferral" in HOOK_BLOCK
                and "capture-only" in HOOK_BLOCK
                and "read-only" in HOOK_BLOCK,
            "project hook scopes every documented CLI action": all(
                f'--vault "{{vault}}" {verb}' in HOOK_BLOCK
                for verb in ("search", "capture", "page", "add", "index", "lint")
            ),
            "wiki schema and category directories": all((wiki_vault / name).is_dir() for name in
                ("_raw", "entities", "references", "playbooks"))
                and all(label in initial_schema for label in (
                    "_raw/", "sources/YYYY-MM-DD/slug.md", "entities/", "references/", "playbooks/",
                    "source captures have no lifecycle `status`", "records review separately",
                    "Existing project files", "`data/`", "## Write for people and agents", "reading views",
                ))
                and schema.read_text(encoding="utf-8") == initial_schema + "\nOwner convention.\n"
                and "schema.md" in (wiki_vault / "index.md").read_text(encoding="utf-8")
                and schema not in note_files(wiki_vault),
            "capture preserves original outside FTS": original_capture_proc.returncode == 0
                and before_index == original.read_bytes()
                and copied_original.read_bytes() == before_index
                and urllib.parse.quote(copied_original.name) in source_with_original.read_text(encoding="utf-8")
                and not any(p.is_relative_to(wiki_vault / "_raw") for p in note_files(wiki_vault)),
            "capture never overwrites a raw original": protected_capture.returncode != 0
                and occupied_copy.read_bytes() == b"User-owned original bytes"
                and not (wiki_vault / "sources" / capture_day / "protected-original.md").exists(),
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
                and (capture_vault / "_raw" / f"{capture_day}-{capture_first_path.stem}" / capture_original.name).read_bytes()
                    == b"original revision one"
                and parse_note(legacy_capture, capture_vault)["capture_scope"] == "unknown",
            "new captures use day folders and legacy flat captures remain linkable":
                captured.parent == wiki_vault / "sources" / capture_day
                and captured.name == "research-agent-study.md"
                and legacy_repeat.returncode == 0 and str(legacy_flat_capture) in legacy_repeat.stdout
                and legacy_flat_capture.read_bytes() == legacy_flat_bytes
                and legacy_revision.returncode == 0 and legacy_dated_capture.is_file()
                and legacy_flat_capture.read_bytes() == legacy_flat_bytes
                and ("Evidence", "../2000-01-01-evidence.md") in md_links(
                    legacy_dated_capture.read_text(encoding="utf-8")),
            "source capture names avoid reserved folder indexes": reserved_capture.returncode == 0
                and reserved_capture_path.is_file()
                and b"Reserved capture filename." in reserved_capture_path.read_bytes(),
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
            "project source captures retain immutable provenance": origin_capture.returncode == 0
                and origin_repeat.returncode == 0 and str(origin_path) in origin_repeat.stdout
                and origin_other.returncode == 0 and origin_path.read_bytes() == origin_bytes
                and _capture_fields(origin_path).get("origin_projects") == "featherbi"
                and origin_other_path.exists()
                and _capture_fields(origin_other_path).get("origin_projects") == "skills"
                and origin_path.name in origin_other_path.read_text(encoding="utf-8")
                and origin_invalid.returncode != 0 and "stable lowercase project ID" in origin_invalid.stderr,
            "source captures have no lifecycle status": origin_verify_rc == 0
                and "status" not in _capture_fields(origin_path)
                and "human:test" in parse_note(origin_path, capture_vault)["verified"]
                and parse_note(origin_path, capture_vault)["status"] == ""
                and parse_note(legacy_capture, capture_vault)["status"] == ""
                and indexed_origin_status == indexed_legacy_status == ""
                and "0 draft" in source_lint_output.getvalue(),
            "wiki revisions merge and retain project origins": page_create.returncode == 0
                and page_update.returncode == 0 and origin_page_revision.returncode == 0
                and 'origin_projects: ["featherbi", "skills"]' in page_after
                and _capture_fields(page).get("origin_projects") == "featherbi, skills",
            "ideas accept project provenance": rc3 == 0
                and _capture_fields(next(vault.glob("notes/*/marimo-batch-reporting-as-the-default*"))).get("origin_projects") == "featherbi",
            "project origin is distinct from tags and deduplicated":
                _capture_fields(old).get("origin_projects") == "featherbi"
                and _capture_fields(old).get("tags") == "python, uv"
                and "origin_projects" not in _capture_fields(final_note),
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
