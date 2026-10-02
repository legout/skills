#!/usr/bin/env python3
"""sb.py — second-brain CLI: OKF v0.2 bundle + SQLite FTS5 index.

Stdlib only (codegraph shells out to ast-grep if installed). The bundle
(default ~/second-brain) is the source of truth and a valid Open Knowledge
Format v0.2 bundle. Human-readable directory indexes and index.db are
separate materialized views; `sb index` rebuilds both, and index.db contains FTS only.

OKF v0.2 mapping:
  notes/, sources/, concepts/, entities/, references/, topics/, playbooks/ -> OKF concepts
  personal/**/*.md         -> handwritten source documents (type optional)
  _raw/**, legacy raw/**  -> acquired original assets, not indexed as concepts
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
  sb [--vault PATH] capture "Title" --source URL --body-file FILE [--original FILE]
                             [--archive-original] [--scope full|excerpt]
  sb [--vault PATH] verify PATH [--by ACTOR]   record OKF verification (default human:$USER)
  sb [--vault PATH] idea "Text"       quick-capture as draft insight
  sb [--vault PATH] lint [--fix]      links, index/FTS drift + OKF/health report
  sb [--vault PATH] orphans           concepts without semantic Markdown inbound links
  sb [--vault PATH] dedup [-t 0.75]   near-duplicate concept pairs
  sb [--vault PATH] codegraph [--root DIR]  symbol/import map via ast-grep
  sb [--vault PATH] stats             bundle + index statistics
  sb selftest                         round-trip checks in a temp bundle

Keep the adjacent sb_lib/ package with this entry point when distributing the skill.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sb_lib.common import (
    PAGE_FOLDERS,
    VALID_RELEVANCE,
    VALID_STATUS,
    VALID_TYPES,
    vault_root,
)
from sb_lib.index import (
    cmd_eval,
    cmd_index,
    cmd_search,
)
from sb_lib.write import (
    cmd_add,
    cmd_capture,
    cmd_idea,
    cmd_init,
    cmd_page,
    cmd_verify,
)
from sb_lib.maintenance import (
    cmd_codegraph,
    cmd_dedup,
    cmd_lint,
    cmd_orphans,
    cmd_stats,
)
from sb_lib.selftest import cmd_selftest


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
    ap_capture.add_argument("--original", help="original file for hashing/linking; left in place by default")
    ap_capture.add_argument("--archive-original", action="store_true",
                            help="preserve an attached/downloaded original in _raw/; requires --original")
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
    for writer in (ap_add, ap_page, ap_capture, ap_idea):
        writer.add_argument("--origin-project", action="append", default=[],
                            help="origin project ID, not applicability or vault scope (repeatable)")
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
