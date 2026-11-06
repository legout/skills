# BB child-thread dispatch

Auto-detected when `BB_THREAD_ID` is set (with `BB_SERVER_URL`/`BB_HOST_DAEMON_PORT`); verify with `bb status`. The parent orchestrates its BB child threads; BB owns thread lifecycle, environments, and placement. All child roles use Pi: pass `--provider pi` with the resolved `--model` and `--reasoning-level` proven through `bb provider models`; an unsupported pair blocks before spawn, without alias guessing or a non-Pi provider fallback.

## Worker placement

- Spawn one writer per lane: `bb thread spawn --prompt-file - --parent-self --title <run/lane/role/attempt> --new-environment worktree --base-branch refs/heads/orchestrator/<run>/base/<lane> --provider pi --model <resolved> --reasoning-level <level> --parent-notifications stuck --json`. Feed the complete cold-start packet from the brief reference as the prompt; `--parent-self` links the child as a subthread, and `stuck` notifications wake this parent when the child blocks on an approval or question.
- BB's worktree environment provider owns placement: record the returned thread and environment IDs and the reported workspace path; verify repository, branch, and base in the child's no-write preflight instead of assuming a path. Never relocate, reconfigure, or hand-place an environment during dispatch; a mismatched environment blocks mutation.
- The worker commits and freezes its parent-authorized result ref with the Git handoff recipe inside its environment before reporting. BB worktrees of the same repository share the Git database: verify the common Git directory matches the recorded canonical one, and use patch-only recovery when it does not.
- Read-only reviewers share a stable checkout: spawn with `--environment <parent environment or stable path>`, `--provider pi`, and the read-only role contract — never a writer's environment.

## Collect, fix, and stop

- Prefer parent notifications; use `bb thread wait <id> --status idle` only when a result or ownership decision is needed, never as polling. Collect the report with `bb thread output <id>` and verify the actual result ref and diff; a child's report alone is not verified evidence.
- Steer or fix with `bb thread tell <id> <message>` carrying the fix brief; recheck only the fix delta.
- Interrupt with `bb thread stop <id>`. Cancellation is not cleanup: preserve the environment and frozen refs; `bb environment cleanup`/`delete` and thread archive/delete are separate post-acceptance actions on owned resources only.
