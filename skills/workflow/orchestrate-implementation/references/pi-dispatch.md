# Pi implementation dispatch

## Lane ownership

- Parallel mutation requires separate managed worktrees.
- One writer owns each worktree and source seam.
- Dependent tasks wait for upstream handoffs.
- Read-only children may share a checkout only when they cannot change project state.
- Each worker makes focused commits.
- The orchestrator cherry-picks only accepted commits.
- A conflict pauses candidate assembly; it never starts another writer against uncertain ownership.

Record a lane board before parallel mutation:

```text
Lane | repo/cwd | task decision | claimed files/contract | worktree | authority | next gate | handoff
```

## Native Pi dispatch recipe

For a coordinated wave, make exactly one top-level `subagent` call with `async: true` and a `workflowScript`.

- Use `runs.run` for dependent stages.
- Use `runs.all` for independent read-only work.
- Use `runs.lanes` for predeclared serial stages across independent lanes.
- Use stable keys and distinct managed output paths.
- Set fresh context for scouts, workers, reviewers, and validators.
- Set `worktree: true` on parallel mutation-capable children.
- Give `new-test` workers the embedded public-seam, behavior-first red/green contract; require evidence matching the assigned test obligation in each report.
- Do not set hard tool budgets on mutation-capable workers.
- Return output references, commit IDs, and handoffs instead of copying full reports into later prompts.

A worker launch names the brief path, repo/cwd/ref, authority, claimed seam, validation, commit requirement, output, and escalation rules. A reviewer launch names the same brief, worker report, and exact diff package.
