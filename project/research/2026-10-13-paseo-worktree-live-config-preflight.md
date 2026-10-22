# Paseo worktree preflight: persisted configuration is not the live allocator

Date: 2026-10-13. Research/repair note requested by the owner during Ariadne orchestration; **no skill implementation, installation, commit or publication performed**. planning-contract v1; installed skill provenance unknown.

## Observed failure and root cause

Ariadne's required shared root was `${XDG_STATE_HOME:-$HOME/.local/state}/worktrees/`, resolving to `/home/volker/.local/state/worktrees`. `paseo daemon config get worktrees.root --json` reported that configured value. However, agent-scoped `create_workspace` created a registered clean checkout at `/home/volker/.paseo/worktrees/079pxy11/intake-duckdb-20261013-implementation`. Its physical canonical path was outside the required root; no worker was launched.

The affected standalone local daemon used `/home/volker/.paseo`. Its process had started before the config edit. The following read/apply check established the missing lifecycle step without changing configuration:

```text
paseo daemon reload --home /home/volker/.paseo --json
appliedPaths: []
restartRequiredPaths: [worktrees.root]
overrideControlledPaths: []
```

Official documentation states that `config get` reports configured values and that worktree allocation requires a restart. The saved value was correct; the running allocator had not adopted it. This was not proof of an unsupported configuration key or a reason to silently relocate a workspace or change execution host.

## Recovery and evidence

The owner explicitly chose fixing Paseo rather than a native-host fallback and subsequently authorized `paseo daemon restart --home /home/volker/.paseo`. The restart's tool return was interrupted, so no CLI exit-code claim is retained. Follow-up checks established a new live daemon PID/start time, a successful reload with **no restart-required paths**, and a new independently registered checkout:

```text
/home/volker/.local/state/worktrees/079pxy11/intake-duckdb-20261013-allocation-check
```

The physical canonical path was beneath the required root, its common Git directory matched Ariadne, and clean HEAD equaled the pinned base `a8d24b18d16854058e6b2b97bd1801cb0687ffbd`. The daemon reported 0.11.1 before and 0.11.2 after; no update/install command was issued in this repair. Existing worktrees were not moved, forced away or implicitly archived. The off-root allocation was preserved without an agent or source writes.

## Proposed small skill correction

Primary target: [`orchestrate-implementation`'s Paseo adapter](../../skills/workflow/orchestrate-implementation/references/paseo-dispatch.md), currently calling `daemon config get` an effective daemon-side configuration check. The installed `paseo` / `paseo-help` skills own general lifecycle guidance; their source location must be resolved separately before editing. This note's confirmed catalog target is the adapter linked above.

Clarify the preflight, without creating another root policy or an automatic restart mechanism:

1. Establish the affected daemon/home/host. A local configured value does not prove a remote host or a running allocator's value.
2. Treat `daemon config get` as persisted configuration, **not** proof of runtime effectiveness. Inspect the installed reload command and its `restartRequiredPaths` / `overrideControlledPaths` result when diagnosing a mismatch. Reload itself applies runtime-safe changes, so it is not a read-only probe to run indiscriminately against unrelated pending configuration.
3. If the required root is saved but still restart-required, stop writer dispatch. Request explicit owner permission to restart the correct daemon; account for active sessions and persist the handoff first. Do not silently change host, allocator or global settings.
4. After the authorized lifecycle action, validate a new allocation's **physical canonical path**, registered repository/common Git directory, branch, clean state and pinned base before granting mutation. A matching config value, process restart or “reload succeeded” alone is not allocation proof.
5. Preserve old/mismatched worktrees and writer ownership. Cleanup has its own authority; do not move them as a side effect of correcting future allocation.

Suggested concise adapter wording:

> `daemon config get` reads persisted configuration. A saved `worktrees.root` change may still require a daemon restart; it is not proof of the live allocator. On mismatch, diagnose the selected daemon's reload/restart-required state and obtain explicit permission for lifecycle changes. Only a newly allocated, physically verified registered path beneath the required root clears placement preflight; preserve existing worktrees.

Validation for a later skill patch: `no-new-test` for the factual prose correction plus the existing catalog/link checks; use a focused scenario checking “saved correct root, live old root” if the repository already has an orchestration instruction evaluator. Do not add a new daemon integration framework just for this note. Preserve the current no-implicit-restart, no-fallback and root-before-write gates.

## Primary sources

- [Paseo configuration: configured values, reload categories and worktree allocation](https://paseo.sh/docs/configuration.md)
- [Paseo troubleshooting: reload and restart-required changes](https://paseo.sh/docs/troubleshooting.md)
- [Paseo worktree layout and existing-worktree preservation](https://paseo.sh/docs/worktrees.md)
- Installed CLI `paseo daemon --help`, `daemon reload --help`, status/reload results and the before/after registered workspace allocations in the owner-authorized Ariadne session.

The owner permitted either this note or a separate Paseo skill-fix project. This note is the selected minimal delivery; it does not claim the source/installed skills have been corrected.
