---
name: marimo-notebook
description: Write a marimo notebook in a Python file in the right format.
---

> Adapted from [`marimo-team/skills`](https://github.com/marimo-team/skills/tree/6454470960d3cd57151aaeffb1176dd55f598b18) at commit `6454470960d3cd57151aaeffb1176dd55f598b18` (Apache-2.0).

# Notes for marimo Notebooks

marimo uses Python to create notebooks, unlike Jupyter which uses JSON. Here's an example notebook:

```python
# /// script
# dependencies = [
#     "marimo",
#     "numpy==2.4.3",
# ]
# requires-python = ">=3.14"
# ///

import marimo

__generated_with = "0.20.4"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import numpy as np

    return mo, np


@app.cell
def _():
    print("hello world")
    return


@app.cell
def _(np, slider):
    np.array([1,2,3]) + slider.value
    return


@app.cell
def _(mo):
    slider = mo.ui.slider(1, 10, 1, label="number to add")
    slider
    return (slider,)


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()

```

Notice how the notebook is structured with functions can represent cell contents. Each cell is defined with the `@app.cell` decorator and the inputs/outputs of the function are the inputs/outputs of the cell. marimo usually takes care of the dependencies between cells automatically.

## Running Marimo Notebooks

```bash
# Run as script (non-interactive, for testing)
uv run <notebook.py>

# Run interactively in browser
uv run marimo run <notebook.py>

# Edit interactively
uv run marimo edit <notebook.py>
```

## Script Mode Detection

Use `mo.app_meta().mode == "script"` to detect CLI vs interactive:

```python
@app.cell
def _(mo):
    is_script_mode = mo.app_meta().mode == "script"
    return (is_script_mode,)
```

## Core rules

Read [core patterns](references/CORE-PATTERNS.md) before writing notebook cells. Keep cells reactive, avoid duplicate definitions and imperative cross-cell mutation, let errors surface, and leave renderable expressions as the cell's final expression.

Use the existing focused references for UI, state, SQL, testing, deployment, exports, expensive work, top-level imports, columns, anywidget, configuration, and file watching. Run `marimo check <notebook.py>` and the relevant tests before delivery.
