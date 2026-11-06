# Orca orchestration dispatch

Auto-detected when Orca injects its pane environment (`ORCA_PANE_KEY`, `ORCA_TAB_ID`, `ORCA_WORKTREE_ID`); a dispatch preamble containing Task and Dispatch IDs means this session is itself an Orca worker. Resolve `ORCA` to the Orca executable hosting this session. Orca owns workspaces, worktrees, agent lifecycle, and wake-ups; all child roles use Pi (`--agent pi`, `--model` only from the resolved role pair).

## Start workers

- `ORCA orchestration worker-start --spec "<bounded brief>" --worktree current --agent pi` shares this workspace; use `--worktree new-top-level --repo id:<repoId> --name <lane>` only when sharing would conflict (`ORCA repo list --json` gives the id). The spec is the complete cold-start packet from the brief reference. On failure read `failedStage` and follow the recovery guidance; never rerun `worker-start` blindly.
- Orca owns placement: never create, move, or hand-place a worker checkout. Record the returned dispatch/run/workspace identity and verify repository and base in the worker's no-write preflight. The Git handoff recipe needs a shared Git database with the parent repository; otherwise use patch-only recovery.
- Read-only reviewers run with `--worktree current`, the read-only role contract, and no-project-edit instructions.

## Wake-driven coordination

- Start every independent worker, then end the turn; Orca wakes this coordinator. Never poll, run watch scripts, or steer through a worker's terminal.
- A `worker_done` settles its task: summarize its evidence and verify the actual result per the handoff rules; never mark a reported failure completed. An `escalation` with `stopReason` means the worker stopped without reporting — steer with `ORCA orchestration send --to dispatch:<id> --subject "<topic>" --body "<message>"`, or stop/retry it. Follow any `worker-list` receipt that carries a `next`.
- Worker questions arrive as `question` messages: answer with `ORCA orchestration reply --id <message_id> --body "<answer>"` only when it follows from approved criteria or user instructions, otherwise escalate to the human. Lost mail: `ORCA orchestration inbox --terminal run:<run_id> --limit 50`.
