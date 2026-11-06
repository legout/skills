---
name: write-implementation-plan
description: Turn an approved specification or multi-step requirement into an executable, verifiable implementation plan before code changes.
---

# Implementation Planning

> Adapted from [`obra/superpowers`](https://github.com/obra/superpowers/tree/b36e0829c6d0140e93cfef2ca599b1b07d4a7797/skills/writing-plans) at commit `b36e0829c6d0140e93cfef2ca599b1b07d4a7797` (MIT). Verifiable-unit sequencing and migration cleanup are adapted from Cursor's [`poteto-mode`](https://github.com/cursor/plugins/tree/93b00b89ef425a9c1bac0d0b317dfc49c930ac99/pstack/skills/poteto-mode) at commit `93b00b89ef425a9c1bac0d0b317dfc49c930ac99` (MIT, Copyright (c) 2026 Cursor). Tracer-bullet slicing and the wide-refactor expand–contract exception are adapted from Matt Pocock's [`to-tickets`](https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/engineering/to-tickets/SKILL.md) at commit `3cca18b368ae95cdbdebbff572ccafa662551015` (MIT, Copyright (c) 2026 Matt Pocock).

Write for an implementer with no conversational context. Specifications own behavior; this plan owns only execution decomposition, per the scoped authority in [`planning-contract`](../planning-contract/SKILL.md) (Contract version: 1). If that contract skill is not installed, stop and request installing `planning-contract` rather than planning on inherited or invented rules; never assume automatic dependency resolution.

## Artifact policy

- For one bounded change under one owner, skip a plan file and pass the approved in-chat design directly to `orchestrate-implementation`; the capture-checkpoint outcome still applies proportionately.
- For architectural or multi-step work, write the smallest plan that exposes dependencies, ownership, integration order, and verification.
- Split independent subsystems into separate plans instead of producing one huge plan.
- When a plan file is needed, use the [`planning-contract`](../planning-contract/SKILL.md) filename convention `YYYY-MM-DD-NNNN-slug.md`. Reuse the source specification's exact prefix for its plan; otherwise allocate the next number from the shared sequence across the project's specs and plans directories (`project/specs/` and `project/plans/`; legacy `docs/specs/` and `docs/plans/`).
- Create tracker tickets only when the user asks for them, an established tracker requires them, or coordination must outlive the current run. Publish each task as a ticket; tickets own the canonical task bodies, and a thin overview may link to them, but never maintain duplicate editable task definitions.

## Lean verification default

Plan the smallest evidence set that establishes the acceptance criteria and addresses concrete material risks. Do not add a test, verification step, reviewer, or review boundary unless it covers a distinct reachable failure mode; if that failure cannot be named, omit the assurance work.

**Verification before tests.** The default evidence is empirical verification of the real artifact: launch it and drive the actual CLI/UI/protocol journey, comparing against independently derived expectations (approved criteria, hand-worked example, or trusted reference), per `project-verification`; where a `verify-<project>` recipe is installed, select its bounded journeys instead of inventing a procedure. Author a new test only for a named regression risk that must be caught repeatedly after this plan is done; if verification or an existing check already proves the behavior, add neither a test nor a duplicate verification stage for the same claim.

Assign each validation unit as a minimal chain: the named failure it protects → the independent oracle for its expected result (approved criteria, hand-worked example, trusted reference, or real bug) → one focused check, or explicit reuse of applicable existing evidence → the delta that would invalidate that evidence. Reject generic per-layer or per-phase matrices and certification checklists; a named mandatory project/CI gate overrides this default and is carried into the plan as-is.

Classify each validation unit once:

- **low risk** — documentation, mechanical edits, generated output, or internal refactoring with unchanged behavior: use an existing check or the smallest smoke, parse, build, or diff inspection; add no test, no verification journey, and no review;
- **normal risk** — ordinary behavior changes and bug fixes: one empirical verification or existing check at the cheapest stable seam; a focused regression test only for a named recurring regression risk; no review; do not duplicate the same behavior across unit, integration, API, and browser layers; or
- **high risk** — authentication, permissions, secrets, money, destructive data handling, migrations, concurrency, distributed behavior, or public contracts: verify the named threats or failure modes immediately at that boundary instead of deferring to the final verification; add a review only where later tasks consume the result before that verification can run.

**Verification timing.** Per task, plan only the smallest check that keeps the repository coherent for the next task. The thorough verification happens once, after all implementation tasks, in a final verification task — not after every task. Verify earlier only when later tasks would obscure the evidence (expand–contract intermediates, destructive migration steps) or when high risk compounds unseen; behavior-free mechanical work gets no final verification journey at all.

A validation unit may cover several tightly related tasks. Reuse required repository CI instead of restating its full test, lint, and typecheck matrix in each task. Asking for a test is a finding too: name the real reachable scenario and violated criterion. Written conventions are binding, unwritten preferences never block. Identify the actual callers, input provenance, environment, and applicable instruction/style/lint rules (or none found) so fresh workers/reviewers do not invent context.

Security review activates only for untrusted/external input, credentials, auth, or dependency changes, and needs a named asset, realistic attacker, and attack path through actual use. Trusted internal callers and user-owned local files are not hostile by default; services use the real deployment boundary. Stolen-secret, broken-TLS, malicious-admin, and generic-hardening stories are not findings. Untouched boundary: `security: n/a`; missing facts on security work: `unverified` — ask, never invent a threat model. Preserve written safety guarantees.

**Reviews are the exception, not the default.** Spend the evidence budget on empirical and formal verification — running the real artifact against independent expectations, plus types, schemas, and static checks where they carry the claim — not adversarial review in the abstract, which drowns in nitpicks and yagnis. Plan a review only where execution evidence cannot reach: conformance to written conventions or approved criteria, unreviewed high-risk integration effects, or an explicit user/project requirement. Scope each planned review to named criteria; unwritten taste never blocks. At most one parent-authorized fix pass and one delta-only recheck; remaining blockers go to the human, not another round. Do not add evidence ledgers, review sign-offs, or a second lifecycle.

## Preflight

1. Read the approved specification, project instructions, relevant code/tests, and any established domain glossary or decision records.
2. **Readiness gate:** require an approved behavioral source per `planning-contract` — an approved specification or its bounded-change equivalent; research findings and probe verdicts are evidence, not sources. If it is missing, stop, report the specific missing prerequisite, and route the work back to `shape-design`.
3. Stop if requirements conflict or a material owner decision is unresolved.
4. A material behavior, interface, or scope change discovered during planning returns to `shape-design`: update the source, obtain approval for the changed scope and revision, and block affected tasks until the source and decomposition are reconciled per the contract's readiness rule.
5. Identify files, responsibilities, interfaces, dependencies, and integration order; find blocking first steps, independent workstreams, shared write targets, and the smallest safe decomposition. Combine steps that share one behavior and validation boundary; prefer one sequential owner when decomposition adds review or coordination overhead. Mark tasks ready for parallel execution only per the contract's parallel-execution rule.
6. Follow established project conventions; do not hide unrelated refactoring in the plan.

Use the repository's established plan location. If none exists, propose a location or a runtime-managed artifact and get approval before creating a new documentation convention.

## Plan header

Link rather than restating specification content. Include:

- goal;
- source specification path, its approval reference, and the exact approved scope and revision;
- the capture-checkpoint outcome;
- only the architecture constraints and non-goals needed to sequence work;
- technology/runtime assumptions;
- a requirement-to-task map pointing to the specification's acceptance criteria; and
- the smallest global validation commands not already implied by required repository CI, plus the final verification journeys when a `verify-<project>` recipe is installed.

## Tasks

### Tracer-bullet slices

Decompose into **vertical slices**: each task cuts a narrow but complete path through every layer it touches (schema, API, UI, tests) and is demoable or verifiable on its own. Never decompose into horizontal layer tasks (a schema task, then an API task, then a UI task) whose intermediate states deliver no observable behavior. A completed slice still leaves the repository coherent and green.

Make the change easy, then make the easy change: when a slice would fight the current code shape, plan an explicit prefactoring task before the behavior task rather than hiding the prefactoring inside it.

**Wide refactors are the exception.** One mechanical change (rename a column, retype a shared symbol) whose blast radius spans the codebase has no green vertical slice. Sequence it as expand–contract: add the new form beside the old; migrate call sites in batches sized by blast radius, each batch its own task blocked by the expand and green because the old form still exists; delete the old form in a final task blocked by every migrate batch. If even batches cannot stay green, keep the sequence on a shared integration branch and promise green only at the final integrate-and-verify task; judge per-task coherence against that branch, not main.

A task is the smallest coherent deliverable that exposes a real dependency, ownership boundary, or independently useful behavior. Do not split work merely to create more review or verification points. Every task needs a runnable coherence check, but related tasks may share one validation unit, and thorough verification is not repeated per task. For each task specify:

- exact files to create or modify;
- interfaces consumed and produced;
- prerequisites;
- behavior and edge cases;
- its minimal validation unit — verification, existing check, or test obligation (`new-test`, `existing-check`, or `no-new-test`) — with the distinct failure mode it covers and, when reusing evidence, the applicable prior result and what invalidates it;
- only the focused commands and expected evidence not already supplied by required CI; and
- a completion criterion.

Use checkbox steps. Assign `new-test` only for a named regression risk that outlives the plan; prefer one focused test at the cheapest stable public seam. For `new-test`, show the focused test, its independently derived expectation, and the verification command; show the failing-first sequence only for bug repros and behavior pinning before refactors. Include code snippets only where exact signatures or non-obvious logic prevent ambiguity; do not invent large implementations in prose.

End the plan with one **final verification task** when the change has user-observable behavior: launch to a usable state, drive the bounded journeys that map to the acceptance criteria on the real surface, compare against independently derived expectations, and read back persisted state where relevant; prefer an installed `verify-<project>` recipe. This task owns the plan's thorough verification; per-task checks stay minimal. A plan of only low-risk mechanical work ends without one.

Internal migrations sequence replacement, caller migration, verification, legacy-path deletion, and a stale-reference search inside one cleanup; any transitional compatibility names its real consumer and its removal condition.

## Quality gate

Before handoff:

1. Map every requirement to at least one task.
2. Search for placeholders such as `TBD` or `TODO`, vague error handling, unnamed tests, and undefined interfaces.
3. Check names and types across dependent tasks.
4. Confirm each task leaves the repository in a coherent, green state.
5. Remove duplicate checks, repeated coverage of the same behavior, per-task verification that belongs in the final verification task, and any review or validation step without a named reachable failure mode.
6. State residual risks and only the manual checks needed for them.
7. Record the contract version and the available installed provenance, or `unknown`, for the handoff.

Present the plan for user approval. After approval, hand it to `orchestrate-implementation` with the approved source reference, capture-checkpoint outcome, and contract provenance recorded; do not create a second execution router.
