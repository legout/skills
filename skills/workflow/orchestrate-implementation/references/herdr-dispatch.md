# Herdr Pi pane dispatch

Read the installed `pi-intercom` skill and current Herdr help. Verify the caller's own Herdr pane is reachable (`herdr pane current --current`), not merely that other panes exist. Missing support blocks this host. Intercom carries messages; Herdr owns pane lifecycle and the parent owns worktree/result acceptance.

## Allocate the lane

After pinning the base, create one new registered lane branch/worktree outside the active checkout and Pi extension auto-discovery. Use the supplied canonical repository; verify the returned common Git directory, clean initial HEAD, branch, and exclusive ownership before writes. Do not move managed/other people's worktrees.

```bash
set -euo pipefail
stop() { printf 'Herdr lane refusal: %s\n' "$*" >&2; exit 1; }
: "${run:?run id}" "${lane:?lane id}" "${base_sha:?recorded base sha}" "${worker_path:?new lane path}"
base_ref="refs/heads/orchestrator/$run/base/$lane"
worker_branch=${worker_branch:-"orchestrator/$run/worker/$lane"}
test "$(git rev-parse "$base_ref^{commit}")" = "$base_sha" || stop "base pin missing or moved"
git worktree add -b "$worker_branch" "$worker_path" "$base_ref" || stop "lane path or branch unavailable"
```

## Register a fresh Pi session

1. Discover the parent's intercom session ID and snapshot `intercom({ action: "list-cwd", cwd: "<worker_path>" })`. An existing session there is an ownership conflict, not the next worker.
2. Send only a registration request with `cwd: "<worker_path>", openProjectPaneIfMissing: true, focus: false`: report session ID, actual cwd/repository/branch/base, Pi model/options, and tools to the parent; do not edit yet. This opens Pi but can reuse a session that registered since the snapshot.
3. Require `Opened Herdr project pane ...`/`openedProjectPane: true`, record the returned paneId, and refresh the roster. In the fresh roster, match a previously absent session at the exact cwd to the pane actually launched. Confirm its reported placement and required tools/options **before sending the mutation brief**. A reused, missing, or ambiguous identity pauses dispatch. Pin the intercom session ID; address later messages with `to` plus `cwd`, never a pane ID or guessed alias.

Intercom opening does not select a model. Explicit model/options require a supported Pi launch/configuration route and reported effective values. For a requested tab, use current `herdr tab create --help` and `herdr pane run` to start a fresh `pi` at the lane path without stealing focus, then use the same registration handshake. Do not resume an unrelated old session.

Deliver the bounded common brief/inline role contract only after admission. Check ignored local Pi configuration/tool dependencies explicitly; they do not automatically appear in a worktree. New tasks and reviewers use fresh sessions. If the user changes scope in the visible pane, reconcile approval before proceeding.

## Results, fixes, and cleanup

Workers use intercom `send` for progress/completion and `ask` for blocking questions; the parent uses `reply`. An ask timeout preserves state and stops guessing. Messages and idle turns prove neither result validity nor ownership release.

Commit and freeze the authorized result ref before the completion report, then release write ownership. The parent verifies Git identities and the exact diff/checks; reconstruction is only for patch-only recovery. Resume a fix only after verifying the same session, cwd, and sole ownership; otherwise resolve the old writer and create a fresh lane from the frozen result ref with a new result ref.

Interruption through Herdr's supported agent controls is separate from cleanup. Confirm the writer stopped; preserve available work. Remove only recorded clean worktrees after durable handoff, consumer completion, and applicable authorization. Never force removal. Closing a visible pane/tab needs separate approval.
