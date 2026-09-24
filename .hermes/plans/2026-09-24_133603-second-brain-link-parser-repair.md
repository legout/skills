# Second-Brain Link Parser Repair Implementation Plan

> **For Hermes:** Implement this bounded repair directly; do not expand scope or commit without a request.

**Goal:** Restore standard Markdown link recognition so the seven currently failing `sb.py selftest` checks pass.

**Architecture:** The existing `md_links` parser is shared by `cmd_add`, `cmd_lint`, and `cmd_orphans`. Repair its existing `LINK_RE` label group rather than adding parsers or caller-specific workarounds; verify the writer-generated links, link rejection, lint, and orphan behavior through the existing self-test.

**Tech Stack:** Python stdlib (`re`), existing `sb.py selftest`; no dependencies.

---

## Evidence and scope

- `python3 skills/second-brain/scripts/sb.py selftest` exits 1 with seven failures: related links, broken-body-link rejection, index/link lint, orphan classification, personal ingestion links, supersede links, and broken-link lint.
- Read-only import/probe shows `md_links("See [Missing](missing.md).") == []` and even `[Yes](ok.md)` after a fenced code block is missed. The current pattern at `skills/second-brain/scripts/sb.py:64-67` is the shared choke point; both ordinary and escaped-label probes fail. The recent label-group change is the leading root-cause hypothesis, to confirm by a red/green probe before editing.
- Real callers: `cmd_add` body validation (line 534), `cmd_lint` concept and directory-index checks (723, 729), and `cmd_orphans` (759); `markdown_link` emits the standard syntax that these readers consume (477-481). `resolve_link` handles local path resolution separately (183-188).
- The broader approved reliability plan is `docs/plans/2026-09-24-0001-second-brain-reliability.md`. Preserve its standard-Markdown-only policy and existing in-progress edits.

## Steps

1. **Focused red probe.** In the existing `cmd_selftest` checks in `skills/second-brain/scripts/sb.py`, add one direct parser assertion covering a plain link, an escaped-bracket label, an angle-bracket destination if the existing regex claims it, an external URL that must be ignored, and a fenced-code link that must be ignored. Run `python3 skills/second-brain/scripts/sb.py selftest`; confirm the parser check and original seven checks fail for link recognition, not test setup. If an existing check already covers an input, reuse it instead of duplicating it.
2. **Minimal root fix.** Change only `LINK_RE`'s label subpattern around line 65 to consume either a backslash-escaped character or one character other than a backslash/closing bracket. The candidate `(?P<label>(?:\\.|[^\]\\])+)` passed a read-only regex probe for both `[Missing](missing.md)` and `[A \[B\]](node-b.md)`; test it in the full expression before applying. Do not replace `md_links`, touch the three callers, or introduce a Markdown library. If the full-pattern probe falsifies this hypothesis, inspect regex match groups and adjust only the faulty part based on evidence.
3. **Green and integration.** Rerun `python3 skills/second-brain/scripts/sb.py selftest` and confirm exit 0 with all checks, including the seven previously failing. Run `bash tests/skills_test.sh`, `bash -n tests/skills_test.sh`, and `git diff --check`. Inspect the diff to ensure the repair is limited to the parser and one focused assertion; do not disturb other uncommitted work.

**Files likely to change:** `skills/second-brain/scripts/sb.py` only. **Non-goals:** full CommonMark parser, wikilinks, broader graph/index refactor, new helper/abstraction/dependency. **Risk:** regex-only parsing still has the documented Markdown-subset ceiling; do not broaden support without a failing real-use case. **Stop condition:** if the parser probe turns green but any self-test remains red, isolate that failure before changing another path; report the residual issue rather than stacking speculative fixes.

**Status:** Implemented. The focused `sb.py selftest` passes all 43 checks. `bash tests/orchestrator_handoff_test.sh`, shell syntax checks, Python AST parsing, and `git diff --check` pass. Repository checks remain blocked by skill path validation errors and a vendored-source mismatch in `skills/workflow/domain-modeling/references/adr-format.md`, outside this parser change.
