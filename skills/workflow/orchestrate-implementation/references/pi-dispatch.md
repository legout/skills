# Native Pi dispatch

Use `pi-subagents` only after delegation is authorized. Read its installed skill and current tool guide (`subagent({ action: "guide", topic: "tool-reference" })`), then discover agents and resolved settings. Select a native Pi profile: a role named `worker` or `reviewer` is not sufficient if a project override uses an `external-cli` or external-job runner. An unavailable Pi profile/model/tool dependency blocks dispatch; do not launch another runtime or install packages silently.

## Launch and placement

For one bounded task use a direct `{ agent, task }` call with explicit `cwd`, fresh context, `async: true`, runtime-bound `output`, and the required mutation isolation. Use a workflow only for useful keys, dependencies, branching, or fanout: one fenced `js workflow` block followed by `subagent({ workflow: true, async: true })`, or a script file. Use `runs.run` for dependent steps and `runs.all` for independent ones; use `runs.lanes` only when a predeclared staged plan benefits from it. Give workflow children stable keys, short behavior labels, and distinct outputs. Never wrap one task merely to obtain a workflow label.

- Mutation: `worktree: true`, explicit repo/cwd, and the parent's pinned named `baseRef`. Managed allocation binds the child tools; give conditional write authority only after the child's no-write preflight verifies actual registered cwd/repository/branch and initial base against runtime-supplied allocation metadata. Do not invent a managed path/branch before allocation. Record that evidence for parent verification before acceptance.
- Read-only: fresh context and the resolved read-only role/tool contract; share only a stable checkout and prohibit project edits. Runtime-persisted review output is allowed.
- Pass explicitly requested model/thinking options in the installed tool's supported form; otherwise retain configured Pi role settings. Do not guess aliases or impose package model defaults.
- Do not impose hard tool/usage budgets on mutation-capable workers. Bound scope, and request checkpoints after active tool calls finish.
- Paste the common worker/reviewer contract from the brief reference; paths alone are not delivery of reviewer gates.

## Handoff and questions

The worker commits intended changes and creates the unique parent-authorized result ref with the Git handoff recipe **before native finalization**. The parent receives its actual commit/tree and clean-check evidence through runtime-bound output. Native managed cleanup may remove the worker checkout and branch; the separate frozen result ref must remain. Verify it in the shared repository and inspect the result directly, without mandatory patch reconstruction.

Use `artifactPaths`, `outputReference`, and the documented runtime handoff instead of scraping combined chat. If only a runtime patch survives, verify its complete identity/cleanliness metadata and use patch recovery. Native auto-capture may include uncommitted changes; that does not waive this skill's committed-clean result requirement.

Children ask via `contact_supervisor`; the parent answers with `subagent_supervisor`. Native supervisor questions/progress and completion notifications do not require `pi-intercom`. Generic intercom needs explicitly loaded child tools and a verified external target; do not assume it was injected as a fallback.

## Completion, fixes, and cleanup

Prefer async completion notifications and yield when no safe parent work remains. Use status only when a result/ownership decision is needed, not polling or `bg_wait` merely to wait for ordinary native completion. Attention and wait expiry leave ownership unresolved.

Use installed native status/control tools for interruption and confirm writer release before a replacement. For a fix, verify retained-child resumability and checkout ownership; otherwise launch a fresh native Pi writer from the prior frozen result ref. Preserve the original endpoint and give the fix a new result ref. Recheck only the fix delta.

Keep native artifacts and frozen refs until all consumers finish. Parent cleanup uses the runtime's documented reviewed cleanup route and applicable authority; never force removal or assume a completed child's cwd still exists. A runtime/setup failure remains a native lane blocker, not permission for a foreground CLI fallback.
