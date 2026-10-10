---
name: orchestrate-implementation
description: Orchestrate approved plans or GitHub issues with Pi implementers and reviewers. Use when the user requests delegated implementation or coordinated Pi sessions; not for design, plan writing, or ordinary direct coding.
---

# Orchestrate Implementation

> Worktree isolation patterns are adapted from [`using-git-worktrees`](https://github.com/obra/superpowers/blob/b36e0829c6d0140e93cfef2ca599b1b07d4a7797/skills/using-git-worktrees/SKILL.md) and David Ondrej's [`git-worktree`](https://github.com/davidondrej/skills/blob/11dee2ebc2d045806b686ba0b57746f1e3d7e331/skills/agent-orchestration/git-worktree/SKILL.md). Test-seam patterns are adapted from Matt Pocock's [`tdd`](https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/engineering/tdd/SKILL.md), [`tests`](https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/engineering/tdd/tests.md), and [`mocking`](https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/engineering/tdd/mocking.md) guidance (all MIT). Exact pins are recorded in `sources.json`.
>
> Shared-write separation, smallest-safe-decomposition, and bounded child context are adapted from Cursor's [`poteto-mode`](https://github.com/cursor/plugins/tree/93b00b89ef425a9c1bac0d0b317dfc49c930ac99/pstack/skills/poteto-mode) at commit `93b00b89ef425a9c1bac0d0b317dfc49c930ac99` (MIT, Copyright (c) 2026 Cursor).

## Ownership and authority

The current session is the parent. It owns scope, decisions, routing, finding disposition, acceptance, candidate assembly, and the final conclusion. Children implement or review bounded tasks; their reports are evidence, not acceptance or publication authority. Delegate only when the current request or applicable instructions authorize it. All child roles use Pi, including workers, fixes, scouts, reviewers, and advisors. Hosts manage placement and lifecycle; model providers inside Pi are not alternative agent runtimes.

Use the smallest safe decomposition. One bounded issue can have one writer; parallel writers need independent owned surfaces and separate worktrees. Scout only when context gathering has a concrete job. Do not add workflows, specialists, reviews, or checks merely to fill stages. Children do not delegate further unless the parent explicitly authorizes fanout.

## Modes

State the requested/configured mode, otherwise `supervised`:

- **`plan-only`**: read inputs and outline tasks/briefs; no source edits, worktrees, or child launches.
- **`supervised`**: implement, validate, and review, including disposable candidate assembly; pause before target integration.
- **`autonomous`**: keep the same loop moving while safe work is ready; neither the label nor candidate assembly grants target integration or publication authority.

An execution request authorizes isolated candidate preparation, not changing the user's target branch. Explicit user restrictions override this default. Target integration, push, issue comments/closure, PR creation/merge, deploy, and release each require applicable authority. Hand approved integration to `merge-worktree`; do not treat a mode as publication permission.

## 1. Read and authorize

Load [planning-contract](../planning-contract/SKILL.md) (Contract version: 1). It alone owns artifact classification, approval, the capture checkpoint, and execution readiness. If missing, request installation and refuse writer dispatch. Read the supplied plan, issue, and linked approved behavioral sources; preserve them rather than manufacturing another planning format. An approved bounded issue may satisfy the contract without a separate spec or plan.

For GitHub, fetch the exact issue with an explicit repository (for example `gh issue view <number> --repo <owner/repo> --json number,url,title,body,updatedAt`), check that repository against the checkout, and record the source URL/revision and owner authorization. Relevant comments are context, not automatic scope or permission changes. If a project selects Epiq in `project/agents/issue-tracker.md` (legacy `docs/agents/issue-tracker.md`), load its workflow and use only `epiq_*` MCP tools; do not initialize a board implicitly.

Stop on conflicting criteria or unresolved material decisions. Route missing behavior/approval to `shape-design`, missing decomposition to `write-implementation-plan`. Recheck readiness only for tasks affected by a material source/interface/scope change. Never infer execution authority from a file location or assistant-written status.

## 2. Select the Pi host

Resolve explicit per-role/lane selection, then the requested/configured run default, then the verified current host. In T3 use its child-capable **Pi** instance; in an agent-scoped Paseo session use its **Pi** provider; in Herdr use a fresh Pi pane; otherwise use available native Pi subagents. Tool presence alone is not host detection. Record the chosen host and the evidence that it can perform the requested role; ask if ambiguous. A detected or selected host without the required capability blocks that role, not permission to silently switch hosts or runtimes.

Read only the selected adapter and its installed runtime guidance before dispatch:

- [Native Pi dispatch](references/pi-dispatch.md): `pi-subagents`, native Pi children only.
- [Herdr dispatch](references/herdr-dispatch.md): `herdr-pane`, fresh visible Pi sessions.
- [Paseo dispatch](references/paseo-dispatch.md): `paseo`, Pi provider and explicitly bound workspace.
- [T3 dispatch](references/t3-dispatch.md): `t3-delegate`, Pi driver; currently read-only until supported isolated mutation placement exists.

Resolve each role's model and thinking fields independently: explicit run/lane → project → global → spec default. Defaults are worker `zai/glm-5.3`/`high` and reviewer `openai-codex/gpt-6.1-sol`/`high`. `inherit` removes that field's override and resolves from global or spec default, not the parent session. Pass the complete effective pair explicitly, even when project profile objects shadow global objects. Filter profiles for Pi before matching the role. Prove the exact model/thinking and child tool dependencies before agent creation; do not guess aliases, omit thinking, downgrade, install prerequisites, or switch hosts silently. Record each value/source, backend-effective pair, and blocker in existing run state.

## 3. Prepare ownership and validation

Mutation requires Git. Verify the canonical repository, clean approved base, and selected host's worktree support. Record a small run state using [manifest and briefs](references/manifest-and-briefs.md); link existing host/mission artifacts rather than duplicating their contents. Read [Git handoff](references/git-handoff.md) before allocating writers: pin supported named bases and preserve committed results before disposable workspaces can disappear.

Use the shared state root `${XDG_STATE_HOME:-$HOME/.local/state}/worktrees/` for all newly allocated worker/fix, parent review/reconstruction, and candidate worktrees. Resolve it once on the allocation host and record its absolute canonical path; a non-absolute state directory or unavailable host-side path blocks. Allow allocator-supported subdirectories: native Pi adds the repository basename and run identity; Paseo adds a checkout hash and workspace slug. Parent-created checkouts use a collision-checked source-checkout identity plus run/lane/role/attempt naming, so unrelated repositories and same-named clones cannot reuse a path. Record actual repository/common Git directory and path mappings; a shared root does not imply shared ownership.

Before allocation, validate physical path components/symlinks, permissions, collisions, and exclusion from the active checkout and Pi extension auto-discovery; create only the validated root. Preserve the configured allocator; an incompatible root requires a separate owner-approved configuration change, never reconfiguration during dispatch or an off-root retry. Never migrate existing worktrees as part of this policy change; retain their recorded locations and lifecycle ownership. An unsafe/unsupported root blocks new allocation.

Use one writer per isolated registered worktree. Verify every returned canonical path is beneath the shared root and belongs to the expected repository/base, with exclusive ownership, before granting writes. A path in a prompt is not workspace placement. Confirm actual child cwd/repository/branch and effective model/thinking in a no-write preflight; mismatches block mutation.

Run or record the smallest useful baseline. Distinguish pre-existing failures from task obligations; a red baseline requires an owner decision before implementation. Assign focused validation to each coherent unit, not every checkbox:

- `existing-check`: existing coverage exercises the named changed behavior; run it without adding redundant tests.
- `new-test`: a named reachable failure lacks coverage; add one focused test with expected values from the approved criteria or an independent oracle, never copied from implementation output. Bug repros fail before the fix; behavior-affecting refactors pin current behavior before mutation. Add more only for distinct material failure modes.
- `no-new-test`: docs, metadata, or mechanical/behavior-neutral work; use the meaningful parse, build, smoke, or diff check.

Choose the cheapest stable seam that catches the named failure, never mock the unit under test, and do not relax assertions to force green. Reuse verified focused-check evidence only when the exact tree and relevant environment match. A worker's pass claim alone is not verified evidence. Run required repository checks and affected acceptance checks, not every available command.

## 4. Dispatch and collect

Give fresh children the bounded brief and inline role contract from [manifest and briefs](references/manifest-and-briefs.md). Use a direct child for one task; scripts are for useful sequencing, fanout, or branching. Read-only children can share a stable checkout if they do not modify project state. Send exact diff endpoints and real-use context to reviewers, not the whole chat history.

Prefer asynchronous host completion notifications. Keep independent safe work moving; yield when only children remain. A timeout, idle turn, message receipt, or attention signal is not terminal success. Use the host's status/control API to resolve ownership before a replacement writer. Cancellation stops execution and preserves available work; cleanup is a separate decision.

Use `pi-intercom` for Herdr registration, progress, questions, and explicitly named Pi peers. Paseo/T3 Pi sessions may also use it if both endpoints have connected tools and the same reachable broker. Native children use their supervisor channel by default. Intercom is messaging, not workspace placement, lifecycle authority, or proof of completion; remote hosts do not inherit local paths or broker connectivity.

## 5. Verify, review, and correct

Verify the committed result and inspect its actual diff; keep its ref frozen while consumers need it. A surviving worktree can be inspected directly once writer ownership is released. If only a patch-only handoff is available, read [review and recovery](references/review-and-recovery.md) and reconstruct it against the pinned base with digest/tree/cleanliness checks. Do not require patch reconstruction for an already verified committed result.

Parent inspection applies to every result. Independently review high-risk changes and contracts before dependent writers consume them; otherwise review the assembled candidate once (parent inspection is sufficient for low-risk-only work unless project/user rules require independence). Candidate preparation may consume validated, parent-inspected lanes whose independent review is deferred; they are not accepted until that review passes. Candidate review covers unreviewed changes and integration effects, not settled findings again.

Disposition findings before repair: reject failed evidence gates in one line, authorize small in-scope fixes, hand large/out-of-scope repairs to the human, or ask about an unverified criterion. Use the full inline reviewer contract. One fix pass, one delta recheck; no third round or budget reset at candidate assembly. Prefer a fix commit on the frozen result; review only the prior-result-to-fix delta and affected behavior. Patch replacement recovery follows the same budget.

## 6. Deliver and clean up

Assemble in an isolated candidate worktree in dependency order, using accepted upstream candidate commits as dependent lane bases. Preserve source/result refs and record candidate base/head. Validate the combined behavior; reuse prior evidence only where it still applies. Conflicts or changed dependency bases pause for reconciliation, not another writer or automatic scope expansion.

Before acceptance, inspect the exact final diff and evidence, resolve every material criterion, and account for every child as terminal or blocked with a next action. Restate the approved task, compare the result, and choose `accept / fix / hand back / ask`; extra ideas get one line, not code. Report skipped checks and residual risks. A reviewer verdict does not authorize target integration or publication.

Remove only owned resources after writer ownership is released, handoffs are durable, consumers are finished, and cleanup is authorized. Preserve failed/uncertain work and refs; do not force removal, close visible panes, or archive shared/advisor workspaces implicitly. Native automatic finalization is adapter-owned and must leave its documented handoff. Supervised delivery pauses with the reviewed candidate and its `merge-worktree` handoff, not before candidate review.
