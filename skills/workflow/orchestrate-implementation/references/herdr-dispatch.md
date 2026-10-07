# Herdr pane dispatch

Use for explicitly selected visible Pi workers. Read the installed `pi-intercom` skill and verify the caller's current Herdr pane is reachable (`herdr pane current --current`); seeing some other Herdr-hosted session in the intercom roster is not enough. Missing Herdr/intercom support blocks this backend, not permission for a terminal fallback.

Use the shared ownership, handoff, reconstruction, and reviewer contracts in [Pi dispatch](pi-dispatch.md) and [manifest and briefs](manifest-and-briefs.md).

## Allocate the lane

The parent derives the canonical checkout's `<repo-parent>/worktrees/<repo-basename>/` root and validates it, every existing path component, symlinks, permissions, and branch/path collisions before allocation. `worker_path` must be a unique canonical path beneath that root, with run/lane/worker-or-fix/attempt encoded in its leaf, outside the active checkout and Pi extension auto-discovery. Do not move an existing worktree or retry elsewhere. After pinning the base with the shared recipe, run in the source repository:

```bash
set -euo pipefail
stop() { printf 'Herdr lane refusal: %s\n' "$*" >&2; exit 1; }
: "${run:?run id}" "${lane:?lane id}" "${base_sha:?recorded base sha}" "${expected_root:?canonical shared root}" "${worker_path:?new lane path}"
base_ref="refs/heads/orchestrator/$run/base/$lane"
worker_branch=${worker_branch:-"orchestrator/$run/worker/$lane"}
case "$worker_path" in "$expected_root"/*) ;; *) stop "lane path is outside the shared root" ;; esac
test "$(git rev-parse "$base_ref^{commit}")" = "$base_sha" || stop "base pin missing or moved"
git worktree add -b "$worker_branch" "$worker_path" "$base_ref" || stop "lane path or branch unavailable"
git -C "$worker_path" rev-parse --show-toplevel | grep -Fx -- "$worker_path" >/dev/null || stop "allocated path is not the expected checkout"
git worktree list --porcelain | grep -Fx -- "worktree $worker_path" >/dev/null || stop "allocated path is not registered"
```

For a fresh fix, supply a distinct `worker_branch` (for example `orchestrator/<run>/fix/<lane>`) and new `worker_path` beneath the same shared root; keep the original lane ID and base pin, and preserve the prior branch. Record the branch/path and give the pane session sole write ownership. It must not create another worktree or edit the source checkout. Check that Pi at the lane path can load `pi-intercom` and required worker tools; ignored project-local settings/packages do not automatically appear in a new worktree. Missing dependencies pause for setup approval, never trigger silent global installs.

## Start a fresh session

1. List the parent's intercom identity and snapshot the lane roster with `intercom({ action: "list-cwd", cwd: "<worker_path>" })`. An existing session at that path is an ownership conflict; do not send it a new lane.
2. Start with a registration-only message: `intercom({ action: "send", cwd: "<worker_path>", openProjectPaneIfMissing: true, focus: false, message: "Register for lane <run>/<lane>; report your session ID, cwd, and available tools to <parent-session-id>. Do not edit or start work yet." })`. This opens a split pane, but the API can reuse a session that registered since the snapshot.
3. Require successful delivery explicitly reporting `Opened Herdr project pane ...` (`openedProjectPane: true` when metadata is exposed), not merely `Message sent`; otherwise intercom reused a session and dispatch must pause. Record the returned paneId from the launch response and refresh `list-cwd`. In that fresh roster, verify a session absent from the snapshot at the exact lane cwd whose resolved Herdr pane matches the launch, then confirm its reported session ID, required tools, and runtime-effective model/thinking exactly match the resolved worker or reviewer pair **before sending the mutation brief**. `intercom` does not select a model; if the fresh session cannot be configured through a documented launch path or cannot attest the exact pair, block without mutation. Missing/ambiguous pane identity blocks dispatch. Pin its intercom session ID in the manifest; address later messages with both `to` and `cwd`, not a guessed pane ID or ambiguous alias.

For a requested tab rather than a split, read the installed `herdr tab create --help`, create an unfocused tab at `worker_path`, record its returned pane, and run a fresh `pi --model "provider/model:thinking-level"` there using `herdr pane run` when that is the documented supported launch form. Verify the resulting session actually uses the exact resolved role pair. Apply the registration-only handshake and refreshed-roster identity checks against that explicitly created pane before dispatch; do not resume an old Pi session.

Deliver the bounded brief and pasted worker guardrails to the verified session ID. Include the parent's intercom ID, the existing lane worktree, and the external handoff paths. New lanes and read-only reviewers need fresh sessions; only an authorized fix continues the same lane's retained context. If the human changes lane scope through the visible session, reconcile the approved sources before continuing.

## Completion, fixes, and cleanup

- Workers send progress/completion through intercom `send`, and blocking questions through `ask`; the parent uses `reply`. An ask timeout stops work and preserves state rather than authorizing a guessed decision.
- Capture the clean full handoff at the parent-owned paths before cleanup. Completion means the worker has relinquished write ownership until an authorized fix; a delivered message or idle turn alone proves neither cleanliness nor acceptance.
- Resume a fix only after verifying the same session's identity, checkout, and ownership. Otherwise resolve the old writer first, then allocate a fresh branch/path from the original pinned base, replay the prior full patch, and dispatch a fresh session. Keep the one-fix/one-delta-recheck budget.
- Remove only the recorded clean worktree after the verified handoff survives outside it, no writer owns it, no consumer needs it, and cleanup is authorized. Never force removal; preserve failed/uncertain lanes. Closing a visible pane/tab requires separate user approval.
