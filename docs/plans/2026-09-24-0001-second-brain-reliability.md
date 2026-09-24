# Second-Brain Reliability Implementation Plan

**Status:** Approved for implementation
**Date:** 2026-09-24

## Goal

Make the second-brain CLI reliably create formatted Markdown, maintain its human-readable document graph and separate FTS index, and support handwritten personal notes as read-only ingestion sources.

## Approved source and scope

- **Behavioral source:** the user's 2026-09-24 request and approved pre-implementation design in this session (`clarify`: “Approve and proceed”).
- **Approved scope:** standard Markdown links (not `[[wikilinks]]`); root and per-content-directory `index.md` files and `index.db` are all first-class outputs, with `index.db` used only for FTS; `sb add` produces well-formatted Markdown; handwritten files live under `personal/` and can be ingested by an agent on request without altering originals.
- This is an approved bounded change; no separate behavior specification is required.
- **Capture checkpoint:** no glossary term needs adding. The link syntax, graph/index distinction, and personal-source behavior are owner decisions recorded here. No ADR is warranted: these are explicit, bounded, reversible workflow choices. Security review: n/a; this work uses trusted local files and adds no external boundary or dependency.

## Current context

- `skills/second-brain/scripts/sb.py` is a standalone stdlib-only CLI. `cmd_add` writes the body verbatim; `cmd_index` rebuilds only SQLite FTS; `ensure_bundle` creates one placeholder root index; `lint` ignores wikilinks; `orphans` currently counts index links as graph edges.
- `skills/second-brain/SKILL.md` describes `index.md` as curated-only, asks for an occasional FTS rebuild after manual notes, and does not require related-note links on normal adds.
- `sb.py selftest` is the focused executable test seam. `tests/skills_test.sh` is the repository's established catalog check.
- Baseline: `sb.py selftest` passes 26 checks; worktree was clean on `main`.

## Design and constraints

- Use ordinary relative Markdown links everywhere. `sb add --related PATH` creates explicit, auditable graph edges; supersession links remain automatic. The agent chooses related targets after searching instead of the CLI guessing from title/tag similarity.
- Treat directory indexes as navigation, not semantic relationships. Orphan checks must ignore all `index.md` links.
- `sb index` deterministically regenerates every content directory's index and the SQLite FTS database. Preserve human-authored text outside a marked generated block. Base content directories (`notes/`, `topics/`, `personal/`) always receive indexes; nested directories with Markdown content do too.
- `lint` reports broken internal Markdown links, untyped non-personal concepts, index drift, and health counts. `lint --fix` may rebuild derived indexes only; it must never rewrite note bodies or neutralize links.
- `sb add` keeps `--body`, adds a multiline body-file/stdin path, normalizes and formats plain prose, preserves structured Markdown, emits a stable heading/spacing/frontmatter layout, and rejects detectable malformed structures before writing. No new parser dependency.
- `personal/` Markdown is indexed/searchable and catalogued but is source material, not an OKF concept requiring `type:`. On request, the agent reads personal files, creates distilled `reference` notes with local source links and explicit related links, and leaves originals untouched.
- Keep the change within `sb.py`, its skill instructions, the existing test runner, and this plan. Do not add an ingest service/command, embeddings, a new database, dependency, or lock subsystem.

## Acceptance criteria

- [ ] `sb add` from `--body`, body file, and stdin emits a normalized multi-line Markdown note; one-line prose is wrapped; existing headings, lists, links, and fenced code survive formatting.
- [ ] Detectable invalid body structure is rejected before a note is created.
- [ ] `sb add --related` writes valid, resolving standard Markdown links; supersession links remain valid.
- [ ] `sb index` creates/updates root, base-folder, and nested content-folder `index.md` files and rebuilds FTS from all Markdown notes, including `personal/`.
- [ ] Human-authored index text outside generated markers survives repeated rebuilds; identical input produces identical generated index content.
- [ ] `lint` detects broken Markdown links and index drift; it does not report `[[wikilinks]]` as valid links, and `--fix` never edits source notes.
- [ ] `orphans` counts links between notes as graph edges but ignores structural links from any `index.md`; personal source documents are not concept-orphan candidates.
- [ ] Untyped Markdown under `personal/` is included in FTS without an OKF `type` warning; other untyped concept files remain warned.
- [ ] The skill documents related-link creation, index rebuild/check workflow, Markdown input/format guarantees, personal-note placement, and safe requested ingestion.
- [ ] Focused and repository checks pass; no dependency is added.

## Execution tasks

### Task 1 — Add regression checks for note formatting and explicit graph edges

**Files:** `skills/second-brain/scripts/sb.py` (self-test section only initially).

**Validation unit:** `new-test`; catches the real CLI regression where one-line input is written as an unformatted one-line body and related links are omitted.

- [ ] Extend `cmd_selftest` with expected failures for multiline body-file/stdin handling, plain-text wrapping, stable Markdown structure, malformed-fence rejection, and a resolving `--related` link.
- [ ] Run `python3 skills/second-brain/scripts/sb.py selftest`; confirm the new checks fail for the missing behavior, not due to test setup.
- [ ] Implement a single body renderer/validator and wire `--body-file` (`-` means stdin) mutually exclusively with `--body`; retain the existing `--body` option.
- [ ] Add repeatable `--related` paths, validate they resolve inside the vault, and render them as standard Markdown links in a `## Related` section. Keep automatic predecessor/successor links.
- [ ] Rerun the focused self-test and confirm formatting, rejection, and link checks pass.

**Completion criterion:** every CLI-created note has a normalized Markdown envelope and explicit related-note links are generated deterministically.

### Task 2 — Rebuild human indexes and FTS as separate first-class outputs

**Files:** `skills/second-brain/scripts/sb.py`.

**Validation unit:** same focused self-test; distinct reachable failures are stale catalogs, lost curated content, structural links masking orphans, and destructive lint fixes.

- [ ] Add failing checks for deterministic root and nested indexes, marker preservation, FTS inclusion, drift reporting, safe `lint --fix`, and orphan classification.
- [ ] Run self-test red and verify each new assertion exposes existing behavior.
- [ ] Make `cmd_index` render root and per-content-directory indexes from the current file tree, preserving text outside generated markers; create the standard `personal/` directory and its index.
- [ ] Stage generated text and the FTS database before replacement so an interrupted rebuild does not leave a partially written artifact.
- [ ] Make `lint` compare actual and expected generated indexes, check standard Markdown links, and report drift. Make `--fix` rebuild only generated indexes/FTS.
- [ ] Make `orphans` count only links from content notes, ignore `index.md` navigation, and exclude `personal/` source files from concept-orphan candidates.
- [ ] Verify add/verify/codegraph flows still call the unified index rebuild and rerun self-test green.

**Completion criterion:** one `sb index` converges all derived views; catalogs cannot hide missing semantic links; no fix mode edits source content.

### Task 3 — Define personal-source ingestion and update skill contract

**Files:** `skills/second-brain/scripts/sb.py`, `skills/second-brain/SKILL.md`, `tests/skills_test.sh`.

**Validation unit:** `new-test` for source-folder indexing/type behavior; existing catalog test for skill structure and links.

- [ ] Add failing checks showing personal Markdown is searchable/indexed, untyped personal files do not trigger concept warnings, and untyped notes/topics still do.
- [ ] Run self-test red, implement the source-folder distinction, then rerun green.
- [ ] Update the skill’s bundle tree, CLI reference, and record/index instructions. Require the agent to search for and link related notes before adding a concept.
- [ ] Add a “Personal notes and ingestion” protocol: handwritten Markdown belongs in `personal/`; ingest only when asked; preserve the original; distill durable facts into `reference` notes with `--source` and `--related` links; do not duplicate already represented facts.
- [ ] Clarify root/per-folder indexes are generated navigation, index.db is FTS-only, and `sb index`/`sb lint` are the rebuild/audit path.
- [ ] Add a focused invocation of the second-brain self-test to `tests/skills_test.sh`; verify YAML/frontmatter and repository link checks remain satisfied.

**Completion criterion:** an agent can find personal notes and follow a safe, source-attributed ingestion workflow without a new subsystem.

### Task 4 — Candidate review and final verification

**Files:** all changed files.

**Validation unit:** `existing-check` plus candidate review.

- [ ] Run `python3 skills/second-brain/scripts/sb.py selftest`.
- [ ] Run `bash -n tests/skills_test.sh`, `bash tests/skills_test.sh`, `bash tests/orchestrator_handoff_test.sh`, `bash scripts/check-skill-sources.sh`, and `git diff --check`.
- [ ] Review the full diff against every acceptance criterion; inspect generated root/nested index samples in a disposable vault and verify FTS query results.
- [ ] Confirm no generated index link is counted as a semantic edge and `lint --fix` leaves source note bytes unchanged.
- [ ] Report changed files, verification output, and any residual edge cases. Do not commit or publish.

**Completion criterion:** all acceptance criteria have executable or directly inspected evidence and the final diff stays within scope.

## Requirement map

- Standard Markdown graph links and explicit related edges: Tasks 1–2.
- Root/subfolder indexes plus independent FTS index: Task 2.
- Well-formatted `sb add` output: Task 1.
- `personal/` placement and requested ingestion: Task 3.
- Linter, deterministic rebuild, safe repair, and orphan semantics: Tasks 2–4.
- Prior-art borrowings adopted: derived deterministic indexes, link/index/orphan audit, explicit preservation of curated text, structured Markdown input, and conservative repair.

## Residual risks

- The stdlib-only validator intentionally checks a documented Markdown subset (including fenced blocks and local links), not every CommonMark extension; the writer preserves valid structured content rather than attempting lossy auto-repair.
- Concurrent CLI writers are not serialized. Atomic artifact replacement prevents partial files, but a writer racing a rebuild can still require a subsequent `sb index`; defer a lock until concurrent writes are a demonstrated failure mode.
