# T3-hosted Pi dispatch

Use app-owned children only inside a T3 thread. Query `orchestrator_capabilities`; select a provider instance with `driverKind: "pi"`, `canRunChildTask: true`, and no blocking constraints. Resolve the role's complete model/thinking pair under `SKILL.md`'s per-field policy and prove it executable through the live catalog before creation. Take the exact instance ID, Pi model ID, and matching thinking option from that catalog; unsupported pairs block, without alias inference, omitted thinking, or downgrade. An available Codex/OpenCode/other driver is not a Pi fallback. Pi model-provider names do not change the runtime. Child permissions never exceed the parent.

## Placement: currently read-only

`delegate_task` currently inherits the parent's bound workspace and exposes no documented per-child workspace/cwd binding. Naming another worktree in a prompt or asking for `cd` does not establish tool placement. Therefore this adapter is **currently read-only**: use fresh Pi scouts/reviewers against a stable bound workspace, not parallel mutation lanes in parent-allocated worktrees.

For implementation, pause and ask for an explicitly selected mutation-capable Pi host. A native Pi child with supported explicit placement may be an option, but do not substitute it silently. If a future documented child-binding API exists, verify it and the actual child cwd/repository/branch/base in a no-write preflight before admitting mutation; capability metadata alone does not establish placement.

Do not call `t3_thread_launch`/`create_threads` for ordinary child tasks. They create top-level conversations. Use them only for separately authorized top-level work with a supported `workspaceStrategy`, not as an implicit delegation fallback. Honor host instructions preferring native same-provider delegation when it supports the requested model, unless explicitly requesting app-owned children.

## Dispatch, questions, and control

- Call `delegate_task` with the selected Pi target, a task-only bounded prompt, read-only role, and inline role contract. Keep result/diff artifacts bounded; provide exact endpoints and relevant source context, not an unbounded pasted diff or parent history.
- Use `mode: "async"`; retain `taskId` and yield for completion notification. Read `task_status` when a result/ownership decision is needed. A `mode: "wait"` timeout does not cancel the child. Check `workState`, final `summary`, errors, and `hasPendingChildRuns`; an idle/completed turn with live nested work does not release ownership.
- `childThreadId` is backing storage, never a follow-up dispatch target. Every subsequent review/fix/recheck round uses a new `delegate_task`, with original brief, prior findings/responses, and unresolved objections. Use a distinct `clientRequestId` per round, stable across retries of that round. Keep the task IDs separately; do not send to the child thread to reset review.
- There is no native interactive ask tool here. Explicitly connected Pi intercom endpoints may carry questions to a verified parent target; otherwise finish blocked with the exact question. Answer it in the next delegated round, not by guessing.
- Use `task_cancel` when interruption is needed, even before a final report exists. Cancellation is not cleanup: preserve available artifacts/work, inspect status, and confirm no current or queued child writer remains before replacement. Never require a successful handoff before stopping a runaway task.

## Acceptance and cleanup

Read-only outputs still require parent inspection, exact review context, and the common evidence gates. Every recheck gets the full inline contract and only its accepted fix delta; task round-trips do not reset the one-fix budget. A provider failure or incomplete report is a blocker, not empty success.

App-owned task lifecycle does not authorize deleting Git artifacts, moving workspace bindings, or closing other threads. Preserve evidence until consumers finish. Do not claim this adapter's isolated mutation support or a live acceptance pass without exercising an actual supported binding API.
