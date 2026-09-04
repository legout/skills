# Implementation review and recovery

## Review policy

Choose one review policy per run:

- `adaptive` (default): immediate review for high-risk/dependency-defining work; queue low-risk work for wave review.
- `strict`: immediate task review plus final review.
- `wave`: review only completed waves plus final review.
- `final-only`: explicit opt-in for prototypes, mechanical work, or another owner-approved low-risk slice.

Immediate-review triggers:

```text
public API/schema/shared contract; security/auth/permissions/secrets; money/data-loss/migration; concurrency/distributed behavior; broad cross-cutting diff; weak or missing checks; worker uncertainty/scope expansion; candidate-assembly conflict; a task whose contract will be consumed before the next wave review
```

Review boundaries are branch-scoped. For each mutation lane, record `laneBaseSha`, `laneHeadSha`, and `lastReviewedSha`. Review that lane's exact `lastReviewedSha..laneHeadSha` range in its managed worktree; never use the orchestrator's `HEAD` to represent unintegrated parallel lanes. After a clean verdict, advance only that lane's `lastReviewedSha`.

At a wave boundary, review every completed lane with pending changes before fan-in. Send the complete accepted finding list for one lane to one fix worker, then revalidate and re-review that lane's affected range. After accepted commits are assembled on an explicit candidate branch, record `candidateBaseSha` and `candidateHeadSha` and run a fresh cumulative review of `candidateBaseSha..candidateHeadSha`. No lane or candidate boundary may advance based on a review of another branch.

## Execution loop

1. Read source artifacts.
2. Preflight constraints, dependencies, conflicts, and repository state; classify each task's risk and assign its test obligation.
3. Consult configured persistent peers when useful.
4. Create the manifest, briefs, lane board, and gates; record the review policy and each lane's initial `laneBaseSha` and `lastReviewedSha`.
5. Run fresh scouts for load-bearing context.
6. Dispatch workers in safe serial or parallel waves with their per-task test obligations.
7. Run focused validation in each worker worktree matching the assigned obligation.
8. Record each completed lane's `laneHeadSha`; route its exact branch range to immediate review or that lane's pending-review queue.
9. At each boundary — end of a wave, before fan-in, when a lane diff becomes incoherent, or before integration/publication — review every lane's exact pending range. Advance only the clean lane boundaries. Send one lane's complete accepted finding list to one fix worker, then revalidate and re-review that lane.
10. Return valid blockers to the same writer for fix/re-review when its managed worktree still exists and the child is resumable; otherwise launch a fresh fix worker in a new managed worktree from the exact original base, apply the durable prior handoff patch, then apply accepted findings.
11. After every candidate lane is clean, assemble accepted commits according to mode on an explicit candidate branch and record its base and head.
12. Run a final fresh review of the exact candidate range and whole resulting branch before handing target integration to `merge-worktree` or requesting publication.
13. Run final typecheck, lint, tests, and project acceptance commands.
14. Keep push, PR merge, deploy, and release behind separate authority gates.

Cap review loops. Stop when no blocking fix remains, an owner decision is required, or the configured cap is reached. Do not loop for optional polish.

## Findings and recovery

Classify each finding against the exact reviewed head:

- **valid blocker**: fix and revalidate now;
- **valid non-blocker**: record or defer explicitly;
- **stale**: absent at current head;
- **invalid**: contradicted by source, tests, or approved scope;
- **speculative**: lacks a reachable failure or contract; or
- **out of scope/policy**: needs owner authority.

Treat `needs_attention` as a control signal, not proof of failure. Preserve stopped or failed worktrees and artifacts until ownership is clear. Do not launch a replacement while the original writer may still own the seam. Inspect exact head and focused logs before classifying a failed gate.

A completed child's managed worktree may be removed automatically before a later resume. Child cwd or session survival is never the recovery boundary; durable handoff patch paths recorded in the manifest are. If the managed worktree still exists and the child is resumable, resume the same writer; otherwise launch a fresh fix worker in a new managed worktree from the exact original base and apply the durable prior handoff patch before the accepted findings.

Escalate product, architecture, credential, merge, release, and publication choices instead of guessing.

## Completion evidence

Before accepting a run, verify:

- final diff contains only intended files;
- focused validation covers changed behavior per its assigned obligation;
- every lane's exact pending range is clean before fan-in, and the exact candidate range is clean before target integration or publication;
- accepted findings were fixed and revalidated;
- every lane is terminal or blocked with a named next action;
- handoffs are durable before worktree cleanup; and
- skipped validation and residual risks are explicit.

Reviewer reports, CI checks, and receipts are evidence, not publication authority.
