---
name: orchestrate-implementation
description: Use when implementing a project or feature from ADRs, specifications, issues, or plans, especially when work spans multiple tasks, reviewers, worktrees, repositories, or Pi sessions.
---

# Orchestrate Implementation

> Worktree isolation patterns are adapted from [`using-git-worktrees`](https://github.com/obra/superpowers/blob/b36e0829c6d0140e93cfef2ca599b1b07d4a7797/skills/using-git-worktrees/SKILL.md) and David Ondrej's [`git-worktree`](https://github.com/davidondrej/skills/blob/11dee2ebc2d045806b686ba0b57746f1e3d7e331/skills/agent-orchestration/git-worktree/SKILL.md). Test-seam patterns are adapted from Matt Pocock's [`tdd`](https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/engineering/tdd/SKILL.md), [`tests`](https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/engineering/tdd/tests.md), and [`mocking`](https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/engineering/tdd/mocking.md) guidance (all MIT). Exact pins are recorded in `sources.json`.
>
> Shared-write separation, smallest-safe-decomposition, and bounded child context are adapted from Cursor's [`poteto-mode`](https://github.com/cursor/plugins/tree/93b00b89ef425a9c1bac0d0b317dfc49c930ac99/pstack/skills/poteto-mode) at commit `93b00b89ef425a9c1bac0d0b317dfc49c930ac99` (MIT, Copyright (c) 2026 Cursor).

## Overview

The current session is the orchestrator. Keep user intent, scope, authority, routing, candidate assembly, and final acceptance here. Delegate bounded evidence gathering and implementation; do not turn a collection of chat sessions into an implicit scheduler.

The parent owns every child's work: review the diff yourself and write the final conclusion; a child's self-report is input, not acceptance. Delegate large outputs and bulk exploration, but hand children bounded file references and a task contract rather than accumulated conversation history.

**REQUIRED SUB-SKILL:** Use `pi-subagents` for child lifecycle, fresh contexts, managed worktrees, artifacts, missions, review, and recovery.

Use `pi-intercom` only for explicitly named, persistent read-only peers or visible cross-project peers. Spawned children use Pi's native supervisor channel for decisions and progress.

## Modes

Choose one mode from the request or configured default:

- **`plan-only`**: normalize inputs, create the manifest and task briefs, and make no source edits.
- **`supervised`** (default): run workers, validation, fresh review, and accepted fix/re-review cycles; pause before cherry-picking or publication.
- **`autonomous`**: run the same loop and cherry-pick accepted commits when clean; pause on conflicts, unresolved decisions, failed gates, missing required peers, push, PR merge, deploy, or release.

If the user does not specify a mode, use `supervised` and state that choice briefly.

## Intake and preflight

Read all supplied ADRs, specifications, issues, plans, and approved designs before dispatching a writer. Preserve them as source material. Extract:

- constraints, invariants, and non-goals;
- acceptance criteria and validation evidence;
- source seams and claimed files/contracts;
- task dependencies and candidate-assembly order; and
- unresolved owner decisions.

Stop before mutation when inputs conflict or a material acceptance criterion is missing. Ask for the exact owner decision instead of selecting one silently.

Require a git repository for mutation modes. Verify repository, cwd, base ref, cleanliness, and worktree support before allocating writers. Detect whether the harness already provides isolation; never create nested or manually registered worktrees when managed child worktrees are available. A non-git directory may use `plan-only`; it must not receive mutation-capable workers.

Before dispatch, run or record the repository's baseline checks. If the baseline is red, separate pre-existing failures from task obligations and ask whether to investigate or proceed; never attribute them to a worker later. Each mutation lane gets one managed worktree and one writer. Follow the plan's smallest safe decomposition: separate shared write targets into distinct lanes before serializing writers on one target, and prefer one writer when the work cannot decompose safely. The orchestrator owns managed lane cleanup and candidate assembly. `merge-worktree` separately owns target-branch integration and cleanup of the completed source worktree.

Normalize different plan formats with a read-only scout. Preserve the planner's source documents; do not require every planning skill to emit one new format.

## Test obligations

Every task receives exactly one obligation during preflight:

- `new-test`: meaningful behavior, bug regression, branching/state, parsing/validation, security, permissions, money, destructive data handling, concurrency, public contracts, or behavior without existing coverage. Test behavior through a public seam with an independently derived expected value; require one vertical slice at a time: failing test → observed intended failure → minimal implementation → passing focused checks → refactor while green.
- `existing-check`: existing tests already exercise the affected behavior. Add no redundant test; run and report the named focused checks.
- `no-new-test`: documentation, formatting, comments, static metadata, generated artifacts, typo correction, or another change where a new test proves little. Run the smallest meaningful lint, parse, build, diff, or manual validation.

State the assigned obligation, rationale, commands, and results in each brief and report. A worker may challenge the assignment after inspection but must report why; it may not silently skip validation. Evidence is always mandatory; a new test is not.

## Execution references

Before dispatch, read [manifest and briefs](references/manifest-and-briefs.md). For native child/worktree mechanics, read [Pi dispatch](references/pi-dispatch.md). Before accepting work or recovering a failed lane, read [review and recovery](references/review-and-recovery.md).

## Quick reference

| Situation | Action |
|---|---|
| Non-git directory | `plan-only`; no mutation workers |
| Conflicting sources | Stop before dispatch; request owner decision |
| Independent writers | Managed worktree per writer |
| High-risk or dependency-defining task | Immediate review |
| Low-risk completed task | Queue on its lane for cumulative `lastReviewedSha..laneHeadSha` review at the next boundary |
| Dependent tasks | Serial handoff with explicit interface |
| Spawned child question | Native supervisor channel |
| Persistent specialist | Named read-only intercom peer |
| Missing optional peer | Fresh advisor fallback |
| Missing required peer | Pause |
| Review blocker | Resumable writer with intact worktree fixes; otherwise fresh fix worker replays the durable prior handoff patch; fresh re-review |
| Candidate-assembly conflict | Pause and preserve ownership |
| Push/merge/deploy/release | Separate authority gate |

## Common mistakes

- Treating intercom messages as durable state instead of using missions and artifacts.
- Calling persistent sessions "clean" despite retained history.
- Running parallel writers in one checkout.
- Giving every worker the whole plan and accumulated reports.
- Letting a reviewer or worker become the final scope or publication authority.
- Starting a replacement writer before failed-lane ownership is resolved.
- Assuming a completed child's worktree or cwd still exists at fix time; durable handoff patch paths, not child session survival, are the recovery boundary.
- Calling autonomous candidate-assembly permission to integrate or publish.
