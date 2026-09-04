---
name: write-implementation-plan
description: Turn an approved specification or multi-step requirement into an executable, testable implementation plan before code changes.
---

# Implementation Planning

> Adapted from [`obra/superpowers`](https://github.com/obra/superpowers/tree/b36e0829c6d0140e93cfef2ca599b1b07d4a7797/skills/writing-plans) at commit `b36e0829c6d0140e93cfef2ca599b1b07d4a7797` (MIT). Verifiable-unit sequencing and migration cleanup are adapted from Cursor's [`poteto-mode`](https://github.com/cursor/plugins/tree/93b00b89ef425a9c1bac0d0b317dfc49c930ac99/pstack/skills/poteto-mode) at commit `93b00b89ef425a9c1bac0d0b317dfc49c930ac99` (MIT, Copyright (c) 2026 Cursor).

Write for an implementer with no conversational context. The specification remains authoritative; the plan is a compact execution map, not a rewritten specification.

## Artifact policy

- For one bounded change under one owner, skip a plan file and pass the approved in-chat design directly to `orchestrate-implementation`.
- For architectural or multi-step work, write the smallest plan that exposes dependencies, ownership, integration order, and verification.
- Split independent subsystems into separate plans instead of producing one huge plan.
- Create tracker tickets only when the user asks for them, an established tracker requires them, or coordination must outlive the current run. Publish each task as a ticket and treat that ticket set as the plan; do not maintain a duplicate full plan.

ADRs explain **why**, specifications define **what**, and plans or tickets define the executable next units.

## Preflight

1. Read the approved specification, project instructions, relevant code/tests, and any established domain glossary or decision records.
2. Stop if requirements conflict or a material owner decision is unresolved.
3. Split independent subsystems into separate plans.
4. Identify files, responsibilities, interfaces, dependencies, and integration order. Identify blocking first steps, independent workstreams, shared write targets, and the smallest safe decomposition; when work cannot decompose safely, plan one sequential owner.
5. Follow established project conventions; do not hide unrelated refactoring in the plan.

Use the repository's established plan location. If none exists, propose a location or a runtime-managed artifact and get approval before creating a new documentation convention.

## Plan header

Link rather than restating specification content. Include:

- goal;
- source specification path;
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

Present the plan for user approval. After approval, hand it to `orchestrate-implementation`; do not create a second execution router.
