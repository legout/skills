---
name: terminal-session-control
description: Safely read output, send authorized input, or wait on existing terminals and agents in the Herdr desktop app/herdr-core (herdr-app, hc), legacy Herdr TUI (herdr), or cmux when the user names the tool and target.
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

## Select the backend

- **Herdr desktop app / herdr-core:** `herdr-app` maps spaces/tabs/panes to terminals; `hc` reads and controls those terminals. Neither requires `HERDR_ENV=1`. `$HC_TERMINAL_ID`, when present, is your terminal address, not a pane ID.
- **Legacy Herdr TUI:** `herdr` is a different program. Only this branch requires `HERDR_ENV=1`; read [references/herdr-tui.md](references/herdr-tui.md) before using it.
- **cmux:** use its branch below. If “Herdr” is ambiguous, identify app/core versus TUI from live context or ask; a missing legacy variable alone is not evidence of no access.

## Herdr app / core

Read the installed interfaces, then discover existing targets:

```bash
herdr-app --help
hc --help
herdr-app ls
herdr-app status
hc ls --json
```

Do not invoke bare `herdr-app`, `herdr`, or `hc`: they open/raise or attach UI. If the requested app/core is unavailable, report that; do not start or restart it. For app configuration/API questions read `$HERDR_APP_HOME/AGENTS.md` if set, otherwise `~/.config/herdr-app/AGENTS.md`; the app rewrites it, so never edit it.

Map the user-named space/tab/pane from `herdr-app ls` to its **terminal** address. Confirm with `hc get`; preserve remote qualifiers such as `oracle/t7`. A mod pane has no terminal. Resolve ambiguity before reading unrelated terminals. `hc ls` may show launch cwd; `hc get` exposes current cwd under `foreground.cwd`.

```bash
hc get --help
hc read --help
hc get <terminal-address> --json
hc read <terminal-address> --lines 0 --json
```

Start with the visible screen. If needed, request bounded history with `--lines 120`; history reads can scroll full-screen programs temporarily. Inspect `complete`/`why`: while working, blocked or errored, a history read may return only the screen. Do not claim complete logs from incomplete output.

For authorized input or waiting, check `hc send --help`, `hc keys --help` or `hc wait --help` first. `hc send` pastes **and presses Enter**; use only the explicit terminal address and approved text. Never use `--force` to bypass a blocked prompt. Check live foreground/state before sending; an old agent identity is not proof the agent is foreground. `hc wait` uses seconds; `--output` matches future output, not existing screen text. A wait proves only its reported condition, not task correctness. After timeouts or delivery errors, read state/output before retrying to avoid duplicate input. Do not change app focus, labels, layout or terminal keep settings to inspect output.

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

For provenance and upstream pins, read [references/sources.md](references/sources.md). Installed help and the generated app guide are authoritative for current commands.
