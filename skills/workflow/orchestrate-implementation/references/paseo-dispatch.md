# Paseo dispatch

Read the installed `paseo` skill before using this backend. Verify the selected daemon, tools/CLI, provider, and permissions; do not start a daemon or install dependencies implicitly. The current recipe requires the daemon to access the same repository, pinned refs, and parent-owned artifact paths. A remote checkout needs an owner-approved source/artifact transport plan first; local paths and refs do not transfer themselves.

Use the shared ownership, handoff, reconstruction, and reviewer contracts in [Pi dispatch](pi-dispatch.md) and [manifest and briefs](manifest-and-briefs.md).

## Profiles and isolation

- With MCP, call `list_profiles`, read the notes, and materialize the selected profile: `provider/model` into `provider`, `modeId` into `settings.modeId`, `thinkingOptionId` into `settings.thinkingOptionId`, and `featureValues` into `settings.features`. Omit absent values. If none fits, disclose the fallback and use provider discovery. CLI-only callers must request the profile values or approval to use `paseo provider ls/models/diagnostic` when profile discovery is unavailable; never guess or silently drop unsupported settings.
- Before mutation, pin the collision-checked named base with the shared recipe. Bind `create_workspace` to the approved repository through the live schema's `projectPath` or explicit project selector, choose `isolation: "worktree"` and `mode: "branch-off"`, and supply a unique `branchName` plus the pinned `baseBranch`. Never rely on the caller's default project/workspace. CLI equivalent, with installed help authoritative:

```bash
paseo workspace create --isolation worktree --path "$repo" --mode branch-off \
  --new-branch "orchestrator/$run/worker/$lane" \
  --base "refs/heads/orchestrator/$run/base/$lane" --json
```

- Record the returned workspace ID/path/branch. Verify its Git repository and clean initial HEAD match the recorded base SHA before launching a writer. Give one fresh agent sole write ownership of that workspace; Paseo owns allocation, not the parent.

## Dispatch and result collection

- **Agent-scoped MCP:** call `create_agent` with `title`, `provider`, the explicit `workspaceId`, `initialPrompt`, and `notifyOnFinish: true`. Parentage/callbacks require an agent-scoped caller; being a Pi session with Paseo tools does not establish that scope. Follow-ups use `send_agent_prompt` with the recorded agent ID and explicit background/notification choices. Yield for the documented native callback rather than polling.
- **CLI/top-level:** do not assume parent callbacks. Use `paseo run --workspace <workspace-id> --provider <provider/model> --title <lane-title> <brief>` and collect its blocking result, or retain an explicit `paseo wait <agent-id>`/log collection step for a background run. A wait timeout leaves the agent potentially active; idle or a successful CLI exit is not semantic acceptance. Read the final report and inspect permissions/errors through the supported tools before deciding the lane's state. Follow-ups use `paseo send`, which waits by default; `--no-wait` also requires explicit result collection.
- Paste the same bounded brief and worker guardrails, with external report/patch paths. Do not assume Pi tools exist in the worker runtime. For an owner decision, require the worker to preserve state and finish with a blocked report containing the exact question; answer through `send_agent_prompt` or `paseo send`. A product question is not a permission prompt; never auto-approve provider permissions.

## Advisors and reviewers

Read-only advisors can use an explicitly selected existing workspace with a self-contained brief ending: `This is analysis only. Do NOT edit, create, or delete any files. Do NOT write code.` They need no mutation worktree or patch. Load `paseo-advisor` when using that pattern. Advisor opinions never replace required review; a Paseo reviewer, if explicitly selected, must be fresh, read-only, and receive the same full inline reviewer contract and exact diff.

A requested committee may use the contrasting-profile/no-edits briefing from `paseo-committee`, but not its open-ended convergence loop: collect one response per member and bring unresolved disagreement to the parent. Extra advisory agents must have an approved job; selecting Paseo does not automatically request a committee.

## Fixes and cleanup

Resume the same agent only after confirming its ID, workspace, and exclusive ownership. Otherwise resolve the old writer, allocate a fresh workspace/branch from the original pinned base, replay the prior full patch, and dispatch a fresh agent. Backend and full-patch transport never reset the one-fix/one-delta-recheck budget.

Acceptance uses the parent-owned reconstruction, not the live workspace or agent verdict. Archive only the recorded lane-owned workspace after the verified handoff survives outside it, no writer owns it, no consumer needs it, and cleanup is authorized. `archive_workspace`/`paseo workspace archive` archives its agents and terminals as well; never archive an existing workspace used only for advice. Preserve failed/uncertain lanes and check actual archive/cleanup results.
