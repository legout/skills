---
name: marimo-pair
description: Drive a live marimo notebook as a workspace—run Python in the user's kernel, inspect state, and commit durable notebook changes.
---

> Adapted from [`marimo-team/marimo-pair`](https://github.com/marimo-team/marimo-pair/tree/de98ee4e268df1b44fa777f360aa58e241a7a635) at commit `de98ee4e268df1b44fa777f360aa58e241a7a635` (Apache-2.0).

marimo is a reactive Python runtime for building reproducible Python programs
(marimo notebooks). Cells are connected by the variables they define and
reference. Running a cell re-executes dependents in dataflow order. The active
runtime holds the kernel namespace, cell state, and dataflow graph. The
notebook (`.py` file) is the artifact the kernel writes from that state while a
session is running.

A user interacts with the same runtime via a notebook UI with cells, outputs,
and widgets.

**WARNING. The active runtime is the source of truth.** During a session, you
SHOULD NOT modify the associated `.py` file directly. File edits WILL NOT reach
the active kernel or user, and the kernel may overwrite them on save. Use
`marimo._code_mode` (`cm`) for notebook changes. Reading disk is fine, but
prefer `ctx.cells[...].code` for current cell code.

The harness reports the absolute path to this `SKILL.md`. Resolve bundled
`scripts/...` and `reference/...` paths from its parent directory, even when
the current working directory is a notebook workspace. In command examples,
replace `/absolute/path/to/marimo-pair` with that directory.

## Required first kernel command

Start every code-mode session with this dedicated command:

```bash
bash /absolute/path/to/marimo-pair/scripts/execute-code.sh \
  --url http://localhost:2718 \
  -c "import marimo._code_mode as cm; help(cm)"
```

Follow this order for each kernel, including read-only tasks:

1. Run the inspection command once.
2. Wait for successful `help(cm)` output.
3. Then use `cm.get_context()` or another `cm` API in a later call.

Do not run task-specific `cm` code before the inspection command succeeds.

## Connect to a Notebook

Use the bundled `execute-code.sh` from the reported skill directory or MCP
(`execute_code(...)`) to run Python in a live marimo kernel.

`execute-code.sh` always takes `--url`. If the user provides a notebook URL,
run the required inspection against it directly:

```bash
bash /absolute/path/to/marimo-pair/scripts/execute-code.sh \
  --url http://localhost:2718 \
  -c "import marimo._code_mode as cm; help(cm)"
```

After that command succeeds, pass task code with `-c CODE`, `-` for stdin, or
a file path:

```bash
bash /absolute/path/to/marimo-pair/scripts/execute-code.sh \
  --url http://localhost:2718 - <<'PY'
import marimo._code_mode as cm

async with cm.get_context() as ctx:
    cid = ctx.create_cell("x = df.head()")
    ctx.run_cell(cid)
PY
```

If the user gives no URL, find or start a notebook. Look for a running server
with `bash /absolute/path/to/marimo-pair/scripts/discover-servers.sh`, MCP
`list_sessions()`, or local process context, and pass the `url` it reports to
`--url`. With one notebook open, the script targets it automatically; with
several, pass `--file` with the notebook's file key.

If no server is running and the user wants a notebook, start marimo with
`--no-token` (and without `--headless`) so it auto-registers for discovery. The
notebook UI must be open for `execute-code` to target it. The right invocation
depends on context (project tooling, global install, sandbox mode). If the
notebook file contains a PEP 723 `#
/// script` header, it MUST be opened with `--sandbox` — otherwise marimo
ignores the inline dependencies. See
[finding-marimo.md](reference/finding-marimo.md) for the full decision tree and
[execution-context.md](reference/execution-context.md) for selector resolution,
scripts, MCP, and shell quoting.

## Code-mode work

After connection, read [code-mode](reference/code-mode.md) before inspecting or changing cells. The active kernel is authoritative: do not edit its `.py` file directly. Use `marimo._code_mode` for durable changes, run affected cells, inspect outputs, and persist through the live session.

## References

- [Finding marimo](reference/finding-marimo.md) for discovery and startup.
- [Execution context](reference/execution-context.md) for kernel execution details.
- [Code mode](reference/code-mode.md) for scratchpad, cell, UI, and persistence rules.
- [Gotchas](reference/gotchas.md) for failures.
- [Notebook improvements](reference/notebook-improvements.md) and [rich representations](reference/rich-representations.md) when requested.
