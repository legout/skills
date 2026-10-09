# Paseo-hosted Pi dispatch

Read the installed `paseo` skill and current MCP schema/CLI help. Verify daemon access, caller scope, Pi availability, and permissions; do not start a daemon or install dependencies implicitly. The daemon must access the repository and result artifacts. A remote Git database needs an owner-approved source/result transport plan; local refs, paths, and intercom connectivity do not transfer themselves.

## Shared-root preflight

Paseo's [`worktrees.root`](https://paseo.sh/docs/worktrees) is daemon-global in `$PASEO_HOME/config.json`; the allocator adds a checkout hash and workspace slug. Verify effective daemon-side configuration (local: `paseo daemon config get worktrees.root --json`, relative paths resolve from `PASEO_HOME`) and access to the canonical source repository before `create_workspace`. The root must be the expected shared root or a directory beneath it; local CLI settings do not prove remote daemon settings. Do not edit global configuration during dispatch. An unverifiable/off-root allocator blocks, without off-root retry.

## Pi profile and workspace

- With MCP, read `list_profiles` notes and consider only profiles whose provider is `pi`. Materialize the selected `provider/model` as `pi/<Pi model ID>`, with supplied `modeId`, `thinkingOptionId`, and `featureValues` mapped through the installed schema. A Pi model using OpenAI/ZAI is still Pi; a `codex` or `glm-acp-agent` runtime is not.
- Resolve the complete role pair under `SKILL.md`'s per-field precedence. Prove the exact Pi model and `thinkingOptionId` through profile notes or `inspect_provider`/`list_models`; do not map `high` to an arbitrary option. If no Pi profile fits, disclose that and use Pi provider/model discovery. CLI/top-level callers can use installed `paseo provider ls/models/diagnostic`; no extra approval is needed for read-only discovery. An unsupported pair must block before agent creation. Non-Pi profiles are not fallbacks; do not broaden permissions.
- After pinning the base, call `create_workspace` with the explicit repository (`projectPath` or supported selector), `isolation: "worktree"`, `mode: "branch-off"`, unique `branchName` and `worktreeSlug` (run/lane/worker-or-fix/attempt), and pinned `baseBranch`. Preserve the configured allocator.
- Record workspace ID/path/branch and verify canonical registration beneath the shared root, repository/common Git directory, clean initial base, and actual child cwd before writes. A mismatch blocks agent creation and preserves the workspace. One fresh Pi agent owns that workspace; never rely on a default project/workspace or a path merely mentioned in the prompt.

## Dispatch and collection

**Agent-scoped MCP:** `create_agent` uses the verified Pi provider/model/settings, explicit `workspaceId`, bounded `initialPrompt`, and `notifyOnFinish: true`. Agent-scoped parentage/callbacks are not established by mere tool presence. Follow-ups use `send_agent_prompt` with the recorded agent ID and explicit background/notification choices. Yield for callbacks rather than polling.

**CLI/top-level:** use the installed `paseo run` syntax with the explicit workspace and verified Pi provider/model/settings, including `--thinking <verified-option-id>` when supported. Installed help or an exact preconfigured profile must prove both model and thinking are applied; otherwise block before agent creation. Collect its blocking result, or retain a specific `paseo wait <agent-id>`/log collection step for background work; top-level tools need the same explicit collection. A wait timeout does not cancel the agent, and idle/CLI success is not semantic acceptance. Inspect final report, permission/error state, and writer ownership. `paseo send --no-wait` likewise needs result collection.

Paste the common bounded brief and inline role contract. Reviewers are fresh Pi agents with a read-only contract, not committees or other-runtime advisors. Existing shared workspaces are suitable only for read-only work on a stable tree.

For questions, use intercom only when both Pi endpoints have connected tools, a reachable broker, and a verified parent session target. Otherwise preserve work and finish blocked with the exact question; the parent answers through `send_agent_prompt`/`paseo send`. Product decisions are not provider permission prompts; never auto-approve either.

## Results, fixes, and cleanup

Freeze the authorized committed result ref before reporting completion; with a shared repository the parent verifies the actual result, not the agent verdict. Different Git databases require the approved transport and corresponding verification, not an assumed local ref. A complete patch-only handoff uses recovery.

Resume a fix only after confirming the agent's identity, workspace, and exclusive ownership. Otherwise resolve the old writer and allocate a fresh Pi agent/workspace from the frozen result with a new result ref. Preserve the prior reviewed endpoint and correction budget.

Use documented host control to stop execution when needed, then confirm writer release and preserve available work. Archiving/removal is a separate authorized cleanup: `archive_workspace`/`paseo workspace archive` also archives agents and terminals. Never archive a shared/advisor workspace or assume archive preserves a managed worktree. Durable handoffs and finished consumers precede cleanup; uncertain lanes are preserved.
