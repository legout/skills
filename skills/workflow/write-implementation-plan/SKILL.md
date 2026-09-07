---
name: write-implementation-plan
description: Turn an approved specification or multi-step requirement into an executable, testable implementation plan before code changes.
---

# Implementation Planning

> Adapted from [`obra/superpowers`](https://github.com/obra/superpowers/tree/b36e0829c6d0140e93cfef2ca599b1b07d4a7797/skills/writing-plans) at commit `b36e0829c6d0140e93cfef2ca599b1b07d4a7797` (MIT). Verifiable-unit sequencing and migration cleanup are adapted from Cursor's [`poteto-mode`](https://github.com/cursor/plugins/tree/93b00b89ef425a9c1bac0d0b317dfc49c930ac99/pstack/skills/poteto-mode) at commit `93b00b89ef425a9c1bac0d0b317dfc49c930ac99` (MIT, Copyright (c) 2026 Cursor).

Write for an implementer with no conversational context. Specifications own behavior; this plan owns only execution decomposition, per the scoped authority in [`planning-contract`](../planning-contract/SKILL.md) (Contract version: 1). The plan is a compact execution map, not a rewritten specification. If that contract skill is not installed, stop and request installing `planning-contract` rather than planning on inherited or invented rules; never assume automatic dependency resolution.

## Artifact policy

- For one bounded change under one owner, skip a plan file and pass the approved in-chat design directly to `orchestrate-implementation`; the capture-checkpoint outcome still applies proportionately.
- For architectural or multi-step work, write the smallest plan that exposes dependencies, ownership, integration order, and verification.
- Split independent subsystems into separate plans instead of producing one huge plan.
- Create tracker tickets only when the user asks for them, an established tracker requires them, or coordination must outlive the current run. Publish each task as a ticket; tickets own the canonical task bodies, and a thin overview may link to them, but never maintain duplicate editable task definitions.

ADRs explain **why**, specifications define **what**, and plans or tickets define the executable next units.

## Preflight

1. Read the approved specification, project instructions, relevant code/tests, and any established domain glossary or decision records.
2. **Readiness gate:** require an approved behavioral source — an approved specification, or the bounded-change equivalent of an explicitly approved issue or short design with acceptance criteria. Research reports, probe verdicts, and draft specifications are evidence, not sources: stop, report the specific missing prerequisite, and route the work back to `shape-design`. An owner's acceptance of research findings is not approval to build.
3. Stop if requirements conflict or a material owner decision is unresolved.
4. A material behavior, interface, or scope change discovered during planning returns to `shape-design`: update the source, obtain approval for the changed scope and revision, and block affected tasks until the source and decomposition are reconciled. Unaffected tasks need no reapproval; cosmetic edits need no new behavioral approval.
5. Split independent subsystems into separate plans.
6. Identify files, responsibilities, interfaces, dependencies, and integration order. Identify blocking first steps, independent workstreams, shared write targets, and the smallest safe decomposition; when work cannot decompose safely, plan one sequential owner. Mark tasks ready for parallel execution only when dependencies are satisfied, consumed interfaces are stable, and ownership does not conflict; distinct ticket files alone never justify parallel writers, and contract-defining tasks are accepted before dependent tasks consume them.
7. Follow established project conventions; do not hide unrelated refactoring in the plan.

Use the repository's established plan location. If none exists, propose a location or a runtime-managed artifact and get approval before creating a new documentation convention.

## Plan header

Link rather than restating specification content. Include:

- goal;
- source specification path, its approval reference, and the exact approved scope and revision;
- the capture-checkpoint outcome;
- only the architecture constraints and non-goals needed to sequence work;
- technology/runtime assumptions;
- a requirement-to-task map pointing to the specification's acceptance criteria; and
- exact global validation commands.

## Tasks

A task is the smallest independently reviewable deliverable with its own verification cycle; every task ends with a runnable check and leaves the repository coherent. For each task specify:

- exact files to create or modify;
- interfaces consumed and produced;
- prerequisites;
- behavior and edge cases;
- test obligation (`new-test`, `existing-check`, or `no-new-test`) with rationale;
- exact commands and expected evidence; and
- a completion criterion.

Use checkbox steps. For `new-test`, show the red → minimal green → verification sequence. Include code snippets only where exact signatures or non-obvious logic prevent ambiguity; do not invent large implementations in prose.

Internal migrations sequence replacement, caller migration, verification, legacy-path deletion, and a stale-reference search inside one cleanup; any transitional compatibility names its real consumer and its removal condition.

## Quality gate

Before handoff:

1. Map every requirement to at least one task.
2. Search for placeholders such as `TBD` or `TODO`, vague error handling, unnamed tests, and undefined interfaces.
3. Check names and types across dependent tasks.
4. Confirm each task leaves the repository in a coherent, testable state.
5. State residual risks and manual checks.
6. Record the contract version and the available installed provenance, or `unknown`, for the handoff.

Present the plan for user approval. After approval, hand it to `orchestrate-implementation` with the approved source reference, capture-checkpoint outcome, and contract provenance recorded; do not create a second execution router.
