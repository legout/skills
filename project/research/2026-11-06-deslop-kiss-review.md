# Deslop and a proposal-first KISS workflow

Status: research, 2026-11-06; the user subsequently authorized proposal-first behavior with an explicit direct-cleanup exception. That bounded change is now reflected in the catalog's `deslop` and routing guidance; installation remains manual. Baseline catalog inspected at `55f04e9cb46cdb2bbe3e328b92a1b10507ddf010`. Planning-contract version: 1. Work stays in the catalog; installation is explicitly reserved to the user.

## Existing skills (historical comparison)

The catalog already adapts the linked Cursor skill: `skills/engineering/deslop/SKILL.md` cites `cursor-team-kit/skills/deslop/SKILL.md` at `93b00b89ef425a9c1bac0d0b317dfc49c930ac99`; `sources.json` records the same origin. This is an adaptation, not a verbatim copy. [S1, S2]

The current upstream file was read at main revision `2776ddd2355d6d6c8747d3964600f28daf62f049`. It tells the agent to inspect the diff against main and remove unnecessary comments, abnormal defensive checks on trusted paths, type-bypass casts, deep nesting, and inconsistent patterns. It applies edits directly. Its behavior-preservation rule makes an exception for clear bug fixes. It has no proposal-selection gate or workflow-artifact handoff. [S3]

Our `deslop` is substantially broader: file/directory/module/repository targets, whole-repository default, reachability analysis, dead/duplicate/overcomplex/fragmented-code classification, incremental edits, and completion validation. Its explicit per-change validation and final list including focused/full tests are heavier than the user's requested minimal, claim-matched verification. These defaults should be replaced rather than supplemented with another checklist if the skill is revised. [S1]

Our `simplify-code` targets settled changed code, accepts named scope, and uses three separate Reuse/Quality/Efficiency review passes (parallel reviewers when available, otherwise sequential). It then applies accepted small fixes itself. It already protects behavior and deliberate structural decisions, but it is not a read-only proposal menu and its fixed three-pass workflow is not necessary for every simplification. [S4]

`review-codebase-architecture` already demonstrates the desired report/select/design boundary, but focuses on module depth and seams rather than everyday code simplification. It ranks candidates without editing, then routes a selected candidate to `shape-design`. [S5]

## User's desired contract

- Preserve existing functionality while reducing unnecessary code, concepts, indirection, and reader effort. Prefer clear structure over compressed syntax or line-count targets.
- Support current diff, one file, directories, or the entire project. Reading adjacent callers may establish safety without authorizing edits outside the selected scope. An unspecified target should not silently trigger whole-project cleanup.
- Analyze and propose first. The user selects individual changes for implementation or for further shaping/planning.
- Remain in the catalog; do not install or synchronize agent copies.

## Recommendation and approved follow-up

Reshape the existing `deslop` into the proposal-first KISS entry point rather than importing a third cleanup skill. Reuse its concrete simplification criteria and the architecture review's selection boundary; remove the automatic cleanup loop and broad validation defaults. `simplify-code` remains a separate explicitly requested changed-code cleanup tool, not an automatic next stage.

The user confirmed: concrete proposals followed by selection is the default; an explicit request for direct changes skips that selection round, without relaxing behavior, scope, or approval boundaries. Use one bounded analysis pass by default, not a mandatory adversarial panel. A proposal must identify the concrete complexity cost and a demonstrably simpler alternative; AI authorship, aesthetic preference, and low line count alone are not evidence. Preserve useful module boundaries, necessary error handling, security checks, public/persisted contracts, and intentional structures. Bug fixes are separate proposals, not an exception allowing silent behavior changes.

For each candidate report: a stable selection ID, source locations, current complexity, the smallest proposed change, why it improves comprehension, behavior/invariants to preserve, supporting evidence or uncertainty, and the smallest relevant verification. Rank by practical benefit and risk; no quota. A whole-project pass must disclose areas not inspected rather than imply exhaustive coverage.

After user selection:

- A small understood change can be implemented directly within the explicitly authorized scope. No ADR/spec/plan is required merely to remove a redundant wrapper.
- A consequential architectural choice routes through `shape-design`, with `domain-modeling` only for qualifying ADRs or vocabulary; `write-implementation-plan` follows approved behavior. Tickets are created only when requested or needed for coordination, per `planning-contract`. Findings themselves are evidence, not approved specifications or execution authority. [S5–S7]
- Apply minimal claim-matched verification to selected changes. Reuse applicable evidence, add a test only for a concrete uncovered risk, and verify the combined result without duplicating per-edit checks. A strong existing test can already be sufficient verification. Required repository gates still bind. [S8]

The bounded follow-up covers the catalog's `deslop`, its routing in README/AGENTS and simplify-code's intake, and three evaluation prompts for default proposals, explicit direct cleanup, and selective application/design handoff. No product code, installation, publication, or rewrite of simplify-code's three-axis execution workflow is included.

## Evidence and limits

This source comparison and instruction update are not an execution evaluation of the skills. The evaluation prompts are prepared, not agent-run; structural checks cannot prove model compliance. `bash tests/skills_test.sh` passed (44 skills and the bundled Second Brain selftest); evaluation JSON parsing and `git diff --check` also passed. The final diff was inspected against the default, direct-request, selective-application, and workflow-handoff criteria. No cleanup agents, installations, commits, or pushes are part of this follow-up. A preliminary query of the existing wiki index/hot cache and configured lexical search found no relevant compiled page; the conclusion rests on the primary sources below. This research note is the durable capture under the project's artifact contract, not a duplicate global wiki note.

## Approved consolidation — 2026-11-06

A subsequent owner request supersedes the two-skill boundary above: consolidate under `deslop` and update its callers. Settled changes, files, directories and projects are scopes of one behavior-preserving capability. Proposal-first and explicit direct-cleanup modes stay; an accepted completion-boundary offer grants only its stated action and scope. Reuse, Quality and Efficiency are perspectives in one pass, with optional explicitly requested or project-required reviewers behind a linked brief. Retire the separate invocation, preserve provenance, and migrate installed copies manually. No installation, commit, push or release is included in this request. Existing analysis and execution evidence above remain historical; prepared prompts are not runtime proof.

Consolidation verification: the catalog check passed for 44 skills plus its bundled selftest; the moved reviewer contract remains checked, and the retired entrypoint is rejected. Shell syntax, JSON, local source paths/deduplication, whitespace and the six affected pinned source relationships passed. Seven evaluation scenarios are prepared, not agent-run. The reference audit found a live external caller at `~/.pi/agent/prompts/simplify-code.md` and old installed skill copies; these remain unchanged for owner-managed migration. Active catalog routing no longer invokes the old skill; remaining repository mentions record migration, provenance, superseded plans, or the retirement assertion. LSP confirmation was unavailable for the large source manifest and inconclusive for the shell runner; parser and execution checks supply the stated evidence instead.

## Sources

- S1: [Catalog deslop](../../skills/engineering/deslop/SKILL.md).
- S2: [Catalog source manifest](../../sources.json), deslop entry.
- S3: [Cursor deslop, pinned current revision](https://github.com/cursor/plugins/blob/2776ddd2355d6d6c8747d3964600f28daf62f049/cursor-team-kit/skills/deslop/SKILL.md).
- S4: [Historical catalog simplify-code](https://github.com/legout/skills/blob/55f04e9cb46cdb2bbe3e328b92a1b10507ddf010/skills/engineering/simplify-code/SKILL.md); current cleanup owner: [deslop](../../skills/engineering/deslop/SKILL.md).
- S5: [Catalog architecture review](../../skills/workflow/review-codebase-architecture/SKILL.md).
- S6: [Catalog shape-design](../../skills/workflow/shape-design/SKILL.md), [domain-modeling](../../skills/workflow/domain-modeling/SKILL.md).
- S7: [Catalog planning-contract](../../skills/workflow/planning-contract/SKILL.md).
- S8: [Catalog agent-guardrails](../../skills/engineering/agent-guardrails/SKILL.md).
