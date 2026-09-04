---
name: terminal-session-control
description: Safely inspect or interact with an existing Herdr session or cmux workspace when the user explicitly names that tool and target. Use for reading output, sending a prompt, or waiting for an already-running terminal or agent.
---

# Terminal Session Control

Operate only the terminal tool the user explicitly requested. This skill coordinates existing work; it does not create sessions, workspaces, tabs, panes, surfaces, worktrees, or agents.

## Safety Contract

1. Confirm the requested tool, target, and action.
2. Run the installed binary's top-level and relevant command-group help. Installed help is authoritative because these CLIs evolve.
3. Discover live identifiers; never infer them from examples, titles, sidebar order, or a previously closed target.
4. Read before writing. If inspection answers the request, do not send input.
5. Keep focus unchanged unless the user asks to switch it.
6. Never close, kill, restart, release, interrupt, or reconfigure a terminal target without separate explicit approval.
7. Treat approval prompts, password prompts, and agent questions as blocked states. Show them to the user instead of answering on their behalf.

## Herdr

Proceed only inside a Herdr-managed pane:

```bash
test "${HERDR_ENV:-}" = 1
herdr --help
herdr agent
herdr pane
```

If `HERDR_ENV` is not `1`, stop. The installed `herdr` command addresses the caller's current session; do not invent or require a session-name flag.

Discover current state with the supported forms shown by help, typically:

```bash
herdr pane current --current
herdr agent list
herdr pane list --workspace "$HERDR_WORKSPACE_ID"
```

Use a unique live agent name or explicit pane ID from the JSON response. For an agent, prefer the agent surface because it understands lifecycle state:

```bash
herdr agent get <agent-name-or-pane-id>
herdr agent read <agent-name-or-pane-id> --source recent-unwrapped --lines 120
herdr agent prompt <agent-name-or-pane-id> "<prompt>" --wait --timeout 120000
```

For an ordinary process, use the pane commands advertised by the installed help, such as `pane read`, `pane run`, and `pane wait-output`. Prefer `--current` or an explicit pane ID over UI focus. Parse returned IDs and state from JSON rather than guessing.

A successful wait means the requested lifecycle or output condition was observed; it does not prove semantic correctness. If an agent is `blocked` or `unknown`, inspect its state and recent output, then ask the user what to do.

## cmux

Verify caller context and current syntax first:

```bash
cmux --help
cmux identify --json
```

Use the installed help to list existing windows, workspaces, panes, and surfaces. Resolve the user-named target to one live identifier. If the name is ambiguous or missing, stop and ask rather than selecting one.

Read before sending:

```bash
cmux read-screen --surface <surface-ref> --lines 120
```

Before any write, confirm the current `send` or `send-key` syntax from help. Then send only to the resolved surface and only the text or key the user authorized. Preserve literal text, quoting, and multiline boundaries; do not use shell interpolation to construct untrusted payloads.

Do not split, move, reorder, create, close, or focus cmux surfaces under this workflow. Those topology operations require a separate explicit request and the canonical cmux guidance for the installed version.

## Completion

Report:

- tool and resolved target;
- whether the action was read-only or mutating;
- observed state or output condition;
- any timeout, ambiguity, or blocked prompt; and
- whether user input is still required.

## Sources and Adaptations

Herdr behavior is based on the canonical Apache-2.0 [`herdr` skill](https://github.com/herdrdev/herdr/blob/3150bd92d6162ba248bc28fd4d40bd0d6238e1af/skills/herdr/SKILL.md). cmux command vocabulary is fact-checked against the canonical GPL-3.0 [`cmux` skill](https://github.com/manaflow-ai/cmux/blob/4256df053a63339d7e786157a9846a765762b4cf/skills/cmux/SKILL.md) without copying its text. The narrow existing-target workflow adapts MIT guidance from David Ondrej's [`herdr`](https://github.com/davidondrej/skills/blob/11dee2ebc2d045806b686ba0b57746f1e3d7e331/skills/agent-orchestration/herdr/SKILL.md) and [`cmux`](https://github.com/davidondrej/skills/blob/11dee2ebc2d045806b686ba0b57746f1e3d7e331/skills/agent-orchestration/cmux/SKILL.md) skills. Exact relationships and pins are recorded in `sources.json`.
