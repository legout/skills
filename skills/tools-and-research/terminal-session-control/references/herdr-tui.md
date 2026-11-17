# Legacy Herdr TUI (`herdr`)

Use only for an explicitly requested legacy TUI target, not the desktop app/core.
Proceed inside its managed pane (`HERDR_ENV=1`). If absent, report the missing
legacy context; do not use this gate to reject Herdr app/core access.

```bash
test "${HERDR_ENV:-}" = 1
herdr --help
herdr agent --help
herdr pane --help
```

The installed `herdr` command addresses the caller's current session. Do not
invent or require a session-name flag. Confirm exact syntax from installed help.
Discover live state using the supported forms, typically:

```bash
herdr pane current --current
herdr agent list
herdr pane list --workspace "$HERDR_WORKSPACE_ID"
```

Resolve a unique live agent name or explicit pane ID from JSON, never UI order.
For agents prefer the lifecycle-aware surface:

```bash
herdr agent get <agent-name-or-pane-id>
herdr agent read <agent-name-or-pane-id> --source recent-unwrapped --lines 120
herdr agent prompt <agent-name-or-pane-id> "<authorized prompt>" --wait --timeout 120000
```

For ordinary programs inspect the installed `pane read`, `pane run`, and
`pane wait-output` help. Prefer an explicit ID or `--current` over UI focus.
A retained agent identity can belong to a suspended process while a shell is
foreground: read before sending. For `blocked` or `unknown`, inspect state and
output, then ask the user. Never answer approval prompts on their behalf.

A successful wait proves only the requested lifecycle/output condition.
After timeout or `agent_prompt_stalled`, inspect state and output before retrying:
the prompt may already have arrived. Never send it twice just because waiting failed.
