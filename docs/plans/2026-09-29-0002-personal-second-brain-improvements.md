# Personal Second-Brain Improvements — Proposed Implementation Plan

**Status:** Approved plan; implementation has not been authorized. **Date:** 2026-09-29. **Planning contract:** v1; installed catalog revision unknown. **Approval:** Owner replied “approve” on 2026-09-29 to the proposed behavioral contract and execution map, draft SHA-256 `549f9855d204f05e59c4d7e9c295c3ce2ce59b9e6ed5541c0cf2ef62521caf02` (only approval/status text changed afterward).

## Goal and source

Improve the **personal** second-brain's evidence-backed answers, honest capture and refresh workflow, repeat-safe source snapshots, and measurable retrieval without adding a service or changing its Markdown-first architecture.

**Behavioral source:** The owner's 2026-09-29 request for a plan, followed by selection of **“Core + measured tooling”**: answer/evidence contract, capture completeness, targeted freshness, idempotent capture, and a small retrieval evaluation. The detailed acceptance examples below are the approved bounded-change design based on [the five-project research](../../project/research/2026-09-29-second-brain-landscape-and-company-brain.md). Research alone did not grant approval; the owner approved this design in the follow-up conversation. Company-brain work is expressly out of scope.

**Capture checkpoint:** No new domain vocabulary needs a glossary. Exact source identity (original URL + extracted bytes rather than aggressive URL normalization) is a bounded, reversible choice documented here; no ADR is warranted unless the owner wants identity shared across systems. The behavior and non-goals below are approved; no material design decision remains open.

## Approved behavioral contract

- **Answers:** On a question about the vault, search relevant pages, inspect their original evidence, cite supporting sources near material claims, disclose draft/stale/unknown status, and distinguish wiki evidence from general model knowledge. If none supports an answer, say so rather than laundering a synthesis page into independent evidence. No always-on recall hook.
- **Captures:** `sb capture` retains source text as an immutable snapshot and records whether the operator/agent attests that the supplied local text is **full** or **an excerpt**; the CLI cannot prove completeness. Default conservatively to excerpt for new captures. A URL-only pointer is **not** a read or source capture: record it explicitly as an unexamined pointer using existing note/source-link workflow; do not create an empty source snapshot. Existing captures with no scope remain **unknown**, without migration or inferred labels.
- **Repeat behavior:** For a new snapshot, use the exact supplied source URI plus SHA-256 of supplied text, capture scope, and, when provided, original-file bytes. Recapturing identical inputs returns the existing snapshot without copying the original, appending a log entry, or rebuilding indexes. Same source URI with changed text/scope/original bytes creates a new immutable snapshot with a normal Markdown predecessor link; different URIs remain distinct even when their content matches. Do not normalize URLs or mutate old captures. Validate input before treating a capture as a duplicate.
- **Refresh and ingest response:** Recheck changeable claims when relevant, using existing `status`, `stale_after`, human verification, and sources; retain dated history, propose corrections, and do not auto-rewrite conflicting facts. Each ingest response briefly identifies captured source, pages created/revised, meaningful links, conflicts, skipped material, and open gaps—no extra persistent report artifact.
- **Retrieval evaluation:** A read-only CLI mode consumes JSONL cases (`q`, nonempty list of acceptable vault-relative `gold` paths), queries the **same** FTS5 ranking/default deprecated filter used by `sb search`, and reports per-case top-k hit/miss plus aggregate recall@k and MRR. It never modifies the vault. A small disposable fixture tests the evaluator; real questions are supplied later by the owner. Measuring misses does not itself authorize ranking changes.

## Constraints and current seams

- Markdown pages and `raw/` originals remain authoritative; generated `index.md`/`index.db` remain rebuildable views. Keep standard relative Markdown links; no Obsidian wikilinks, new runtime dependency, embeddings, inbox directory, browser extension, scheduler, MCP server, graph engine, or company features.
- `skills/tools-and-research/second-brain/SKILL.md` owns the agent answer/ingest/refresh protocol. `scripts/sb.py` owns `cmd_capture`, FTS5 search, and its built-in `selftest`. `tests/skills_test.sh` already invokes that self-test. Both installed and catalog skill copies may exist; edit the tracked catalog source and use the ordinary installation process later, not an ad hoc second writer.
- Real callers: an agent follows `SKILL.md`; users/agents call `sb capture --source ... --body-file ... [--original ...]` and `sb search`; `sb selftest` operates in disposable bundles. Keep existing CLI calls working. Existing `sb page` CAS+history, `sb add --supersedes`, `lint --fix`, and `personal/` read-only behavior must survive.
- Security boundary: externally fetched text may contain instructions that try to corrupt wiki content. Preserve the existing rule that fetched material is **data**, never instructions; the asset is integrity of personal notes and originals. The new CLI only hashes and stores supplied bytes—no execution or new network fetch. Existing URL/path validation and no-overwrite behavior remain binding. No generic hardening or fabricated attacker scenarios.

## Tasks (one sequential writer; each slice leaves the catalog coherent)

### 1. Specify and exercise the agent-facing workflow

**Files:** `skills/tools-and-research/second-brain/SKILL.md` only. **Prerequisite:** owner approves the behavioral contract above. **Unit:** low-risk `existing-check` + direct scenario inspection; no new code test.

- [ ] Add a compact answer contract: search/read source, cite, expose trust/freshness, separate background knowledge, and abstain on missing evidence. Demonstrate against one sourced draft, one stale note, and one no-evidence question in a disposable or known-safe vault; inspect the answers rather than counting citations.
- [ ] Document full/excerpt/URL-pointer distinctions without claiming the new CLI option exists until Task 2 lands; then update its command example. State that old captures have unknown scope and a user declaration is not automated verification.
- [ ] Describe targeted refresh, meaningful source/contradiction links in ordinary Markdown, and the short ingest response. Preserve `schema.md` authority, human verification, source-text-as-data, and the existing revision procedure; avoid a second taxonomy or duplicate maintenance checklist.
- [ ] Confirm frontmatter and local references with `bash tests/skills_test.sh`; check the shortest existing `search → capture → compare → synthesize → check` path remains usable.

**Evidence:** A reader can tell what the skill will do for supported, stale and unsupported questions, and can distinguish an excerpt from an unread URL; no nonexistent command is presented as shipped. Task 2 may make the CLI example change in the same reviewable delta if needed.

### 2. Add honest, repeat-safe source capture

**Files:** `skills/tools-and-research/second-brain/scripts/sb.py`, the Task 1 CLI example in `SKILL.md`. **Prerequisite:** Task 1 contract. **Unit:** normal-risk `new-test` in the existing `cmd_selftest`; distinct failure is repeated ingestion generating duplicate or misleading snapshots.

- [ ] First add one focused failing self-test scenario with variants: same URI/body/scope/original creates no second page or log/index change; same URI with changed content creates a linked successor and leaves the old bytes intact; same body at a different URI stays distinct; excerpt is marked and a legacy unmarked capture is not presented as full. Include `--original` to catch an accidental skip when original bytes differ.
- [ ] Add the minimum CLI scope argument for new full/excerpt captures, keeping `--body-file` required. Store scope, exact source URI, content digest and optional raw-file digest in source frontmatter. Compare only captures with trustworthy identity metadata; old captures remain readable and are not rewritten. On duplicate, print/reuse the prior path; on a true revision, add the predecessor link without deprecating historical sources.
- [ ] Reject missing/invalid input before a duplicate result or any raw copy; keep `raw/` originals untouched and prevent failed writes from falsely reporting success. Rebuild navigation/FTS once for a newly created snapshot, not for a duplicate. Update skill command examples and rerun self-test green.

**Evidence:** The test demonstrates no duplicate artifacts or log entries, historical source preservation, honest scope metadata, and ordinary link resolution. No new dependency or vault migration.

### 3. Measure retrieval before changing it

**Files:** `skills/tools-and-research/second-brain/scripts/sb.py`, brief usage in `SKILL.md`. **Prerequisite:** Task 2 may run first for one writer, but eval has no data dependency on it. **Unit:** normal-risk `new-test` at the CLI/self-test seam; distinct failure is an eval reporting a hit the real search would not return.

- [ ] First add a failing self-test with a disposable FTS5 bundle: one top-1 hit, one lower-ranked acceptable hit, one miss, and a deprecated-only page excluded by default. Keep one or more gold paths per case and verify recall@k/MRR arithmetic and read-only behavior.
- [ ] Implement a small `sb eval CASES.jsonl` path sharing the search SQL/default status filter rather than parsing human-formatted `search` output or creating a second ranking algorithm. Validate malformed cases and report them clearly; bound per-query output. Ship only the evaluator, no tuned weights or embeddings.
- [ ] Document how to curate **real** questions later, compare top-k misses, and separately inspect answer citation correctness. Do not claim the disposable fixture proves real-vault retrieval quality.

**Evidence:** The self-test is red before implementation, green afterward; CLI output and `sb search` agree on ranked paths, and evaluation does not alter source/index files.

### 4. Integrate and hand off the approved scope

**Files:** changed tracked files only. **Unit:** one normal-risk candidate review of newly changed behavior, followed by `existing-check` for the repository. No separate reviewer task for prose-only Task 1.

- [ ] Run `bash tests/skills_test.sh` (includes `sb.py selftest`), `bash scripts/check-skill-sources.sh`, and `git diff --check`; inspect the complete changed skill and CLI help against the approved criteria.
- [ ] In a disposable vault, exercise one full capture, one excerpt, a duplicate, a changed-source successor, `sb index`, `sb lint`, and `sb eval`; check historical files and `personal/` content bytes remain intact. Review only concrete regressions or written-rule violations; at most one fix and delta recheck.
- [ ] Report exact evidence and residual limitations. Do not commit, publish, change the installed skill copy, or enable background automation without separate authorization. Before a substantive code handoff, offer the repository-required optional `simplify-code` pass; run it only if accepted.

## Requirement map and gates

- Sourced answer/abstention, freshness and concise ingest reporting → Task 1; manual evidence scenarios.
- Honest full/excerpt capture, unchanged legacy status and repeat-safe snapshots → Task 2; one focused regression scenario with variants.
- Retrieval evaluation without a search rewrite → Task 3; ranked-path regression scenario.
- Preserved Markdown, CAS, history, originals, no new dependencies, and coherent help/skill surface → Task 4 and existing self-test.

**Not planned now:** structured relation fields, a new `lint --strict`, uncited-claim heuristics, inbox, title/alias ranking, embeddings and all company-brain work. Revisit one only after a concrete personal-vault failure or real-question eval establishes its value; that would need a separately approved scope.

**Execution gate:** Approval covers the behavioral contract and plan, not permission to start code work, commit, install, or publish. Obtain execution authority before implementation. If a material rule changes, reconcile this plan with its approved behavioral source first. All work is sequential because Tasks 1–3 touch the same skill/CLI and parallel writers add unnecessary overlap.
