# Paseo dispatch

Read the installed `paseo` skill before using this backend. Verify the selected daemon, tools/CLI, provider, and permissions; do not start a daemon or install dependencies implicitly. The daemon must access the same canonical repository and pinned refs. A remote checkout needs an owner-approved source/artifact transport plan first; local paths and refs do not transfer themselves. Before any workspace or agent creation, prove the daemon's worktree root and repository access match the required shared root; otherwise block.

Use the shared ownership, handoff, reconstruction, and reviewer contracts in [Pi dispatch](pi-dispatch.md) and [manifest and briefs](manifest-and-briefs.md).

## Profiles and isolation

- Paseo's [`worktrees.root`](https://paseo.sh/docs/worktrees) is daemon-global in `$PASEO_HOME/config.json`, defaults to `$PASEO_HOME/worktrees`, and is followed by a source-checkout hash and the workspace slug. The [configuration docs](https://paseo.sh/docs/configuration) document no per-project root override. `worktreeSlug` controls only the leaf; include the run, lane, worker/fix role, and fix attempt in each unique slug. Read the effective root on the daemon host (for a local daemon, `paseo daemon config get worktrees.root --json`; relative values resolve from `PASEO_HOME`) and require the canonical root to be the expected shared root or a directory beneath it. Do not edit this global setting during dispatch. Because it is not project-scoped, a root configured for one checkout does not authorize worktree creation for a different checkout. If the root cannot be verified or does not match this project's `<repo-parent>/worktrees/<repo-name>/`, block before `create_workspace`. A remote daemon needs daemon-side evidence for both its root and access to the same canonical repository; the local CLI's config is not proof of remote settings.
- Resolve the worker or reviewer model and thinking fields independently (run/lane → project → global → spec default). Defaults are worker `zai/glm-5.3`/`high` and reviewer `openai-codex/gpt-6.1-sol`/`high`. With MCP, call `list_profiles`, read all relevant notes, and use `inspect_provider`/`list_models` to prove an exact `provider/model` plus supported `thinkingOptionId` corresponds to the requested pair. Materialize `provider/model` into `create_agent.provider` and the exact option into `settings.thinkingOptionId`; copy `modeId` and `featureValues` only when they are part of the selected profile. Do not infer provider aliases or map `high` to an arbitrary option. If no explicit profile/provider evidence establishes the exact pair, block before agent creation. CLI-only launch is permitted only if installed help exposes an exact way to pass both values; `--provider` alone does not prove thinking. Do not fall back to a different model or omit thinking.
- Before mutation, pin the collision-checked named base with the shared recipe. Bind `create_workspace` to the approved repository through the live schema's `projectPath` or explicit project selector, choose `isolation: "worktree"` and `mode: "branch-off"`, and supply a unique `branchName` plus the pinned `baseBranch`. Never rely on the caller's default project/workspace. CLI equivalent, with installed help authoritative:

```bash
paseo workspace create --isolation worktree --path "$repo" --mode branch-off \
  --new-branch "orchestrator/$run/worker/$lane" \
  --worktree-slug "orchestrator-$run-$lane-worker" \
  --base "refs/heads/orchestrator/$run/base/$lane" --json
```

- Record the returned workspace ID/path/branch. Before `create_agent` or `paseo run`, canonicalize the returned path and verify it is registered beneath the expected shared root, belongs to the requested repository, and has a clean initial HEAD matching the recorded base SHA. A mismatch blocks agent creation and preserves the workspace; never retry off-root. Give one fresh agent sole write ownership of the verified workspace; Paseo owns allocation, not the parent.

## Dispatch and result collection

- **Agent-scoped MCP:** call `create_agent` with `title`, exact `provider` (`provider/model`), `settings: { thinkingOptionId: <verified option> }`, the explicit `workspaceId`, `initialPrompt`, and `notifyOnFinish: true`. Parentage/callbacks require an agent-scoped caller; being a Pi session with Paseo tools does not establish that scope. Follow-ups use `send_agent_prompt` with the recorded agent ID and explicit background/notification choices. Yield for the documented native callback rather than polling.
- **CLI/top-level:** do not assume parent callbacks. Use `paseo run --workspace <workspace-id> --provider <provider> --model <model> --thinking <verified-option-id> --title <lane-title> <brief>` only when installed CLI help or an exact preconfigured profile proves the same requested thinking option is applied; otherwise block before `paseo run`. Collect its blocking result, or retain an explicit `paseo wait <agent-id>`/log collection step for a background run. A wait timeout leaves the agent potentially active; idle or a successful CLI exit is not semantic acceptance. Read the final report and inspect permissions/errors through the supported tools before deciding the lane's state. Follow-ups use `paseo send`, which waits by default; `--no-wait` also requires explicit result collection.
- Paste the same bounded brief and worker guardrails, with external report/patch paths. Do not assume Pi tools exist in the worker runtime. For an owner decision, require the worker to preserve state and finish with a blocked report containing the exact question; answer through `send_agent_prompt` or `paseo send`. A product question is not a permission prompt; never auto-approve provider permissions.

## Advisors and reviewers

Read-only advisors can use an explicitly selected existing workspace with a self-contained brief ending: `This is analysis only. Do NOT edit, create, or delete any files. Do NOT write code.` They need no mutation worktree or patch. Load `paseo-advisor` when using that pattern. Advisor opinions never replace required review; a Paseo reviewer, if explicitly selected, must be fresh, read-only, and receive the same full inline reviewer contract and exact diff.

A requested committee may use the contrasting-profile/no-edits briefing from `paseo-committee`, but not its open-ended convergence loop: collect one response per member and bring unresolved disagreement to the parent. Extra advisory agents must have an approved job; selecting Paseo does not automatically request a committee.

## Fixes and cleanup

Resume the same agent only after confirming its ID, workspace, and exclusive ownership. Otherwise resolve the old writer, allocate a fresh workspace/branch from the original pinned base, replay the prior full patch, and dispatch a fresh agent. Backend and full-patch transport never reset the one-fix/one-delta-recheck budget.

Acceptance uses the parent-owned reconstruction, not the live workspace or agent verdict. Archive only the recorded lane-owned workspace after the verified handoff survives outside it, no writer owns it, no consumer needs it, and cleanup is authorized. `archive_workspace`/`paseo workspace archive` archives its agents and terminals as well; never archive an existing workspace used only for advice. Preserve failed/uncertain lanes and check actual archive/cleanup results.
