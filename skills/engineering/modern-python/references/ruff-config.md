# Ruff Configuration Reference

Ruff is an extremely fast Python linter and formatter written in Rust. It replaces flake8, black, isort, pyupgrade, pydocstyle, and many other tools.

## Basic Setup

Add to `pyproject.toml`:

```toml
[tool.ruff]
line-length = 100
target-version = "py311"
src = ["src"]

[tool.ruff.lint]
select = ["ALL"]
ignore = [
    "D",        # pydocstyle
    "COM812",   # trailing comma (formatter conflict)
    "ISC001",   # string concat (formatter conflict)
]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
docstring-code-format = true
```

## Running Ruff

```bash
# Lint
uv run ruff check .
uv run ruff check --fix .        # Auto-fix
# Preview first; unsafe fixes can change behavior and require explicit review
uv run ruff check --unsafe-fixes .

# Format
uv run ruff format .
uv run ruff format --check .     # Check only
uv run ruff format --diff .      # Show diff
```

## Rule Categories

Using `select = ["ALL"]` enables all rules. Common categories:

| Code | Category | Description |
|------|----------|-------------|
| `E`, `W` | pycodestyle | Style errors and warnings |
| `F` | Pyflakes | Logical errors |
| `I` | isort | Import sorting |
| `N` | pep8-naming | Naming conventions |
| `D` | pydocstyle | Docstring conventions |
| `UP` | pyupgrade | Python upgrade suggestions |
| `B` | flake8-bugbear | Bug detection |
| `S` | flake8-bandit | Security issues |
| `A` | flake8-builtins | Built-in shadowing |
| `C4` | flake8-comprehensions | Comprehension improvements |
| `DTZ` | flake8-datetimez | Timezone-aware datetime |
| `T10` | flake8-debugger | Debugger statements |
| `T20` | flake8-print | Print statements |
| `PT` | flake8-pytest-style | Pytest style |
| `Q` | flake8-quotes | Quote consistency |
| `SIM` | flake8-simplify | Simplification suggestions |
| `TID` | flake8-tidy-imports | Import hygiene |
| `ARG` | flake8-unused-arguments | Unused arguments |
| `ERA` | eradicate | Commented-out code |
| `PL` | Pylint | Pylint rules |
| `RUF` | Ruff-specific | Ruff's own rules |
| `ANN` | flake8-annotations | Type annotation checks |

## Recommended Ignores

### Always Ignore (Formatter Conflicts)

```toml
ignore = [
    "COM812",   # missing-trailing-comma
    "ISC001",   # single-line-implicit-string-concatenation
]
```

### Common Ignores

```toml
ignore = [
    "D",        # Docstrings (enable selectively)
    "ANN401",   # Dynamically typed Any
    "TD002",    # Missing TODO author
    "TD003",    # Missing TODO link
    "FIX002",   # Line contains TODO
]
```

## Per-File Ignores

```toml
[tool.ruff.lint.per-file-ignores]
# Tests
"tests/**/*.py" = [
    "S101",     # assert usage
    "PLR2004",  # magic values
    "ANN",      # type annotations
    "D",        # docstrings
]

# Scripts
"scripts/**/*.py" = [
    "T20",      # print statements
    "INP001",   # implicit namespace package
]

# __init__.py
"__init__.py" = [
    "F401",     # unused imports (re-exports)
]

# Migrations
"**/migrations/*.py" = [
    "ALL",      # ignore all
]
```

## Import Sorting (isort)

```toml
[tool.ruff.lint.isort]
force-single-line = false
known-first-party = ["myproject"]
required-imports = ["from __future__ import annotations"]
section-order = [
    "future",
    "standard-library",
    "third-party",
    "first-party",
    "local-folder",
]
```

## Docstring Style (pydocstyle)

If enabling docstring checks:

```toml
[tool.ruff.lint]
select = ["D"]
ignore = [
    "D100",     # Missing module docstring
    "D104",     # Missing public package docstring
    "D203",     # 1 blank line before class docstring (conflicts D211)
    "D213",     # Multi-line summary second line (conflicts D212)
]

[tool.ruff.lint.pydocstyle]
convention = "google"  # or "numpy", "pep257"
```

## Formatter Configuration

```toml
[tool.ruff.format]
quote-style = "double"           # or "single"
indent-style = "space"           # or "tab"
skip-magic-trailing-comma = false
line-ending = "auto"             # or "lf", "crlf"
docstring-code-format = true
docstring-code-line-length = 80
```

## Type Checking

Ruff does NOT do type checking. Use **ty** (from Astral, the same team behind ruff and uv):

```bash
# Add ty to dev dependencies
uv add --group dev ty

# Run type checking
uv run ty check src/
```

Use ty only when it fits the project's supported Python versions and diagnostics; compare it with the existing checker before migration.

## CI Configuration

```yaml
# GitHub Actions
- name: Lint
  run: uv run ruff check --output-format=github .

- name: Format check
  run: uv run ruff format --check .
```

## Migration from Other Tools

### From flake8

Ruff covers many flake8 plugins. Translate configuration, compare diagnostics, and remove flake8 or plugin packages only after parity and cleanup approval.

### From black

Compare `ruff format` output with Black, then remove Black and its configuration only after compatibility and cleanup approval.

### From isort

Ruff includes import sorting. Translate isort settings to `[tool.ruff.lint.isort]`, compare output, and remove isort only after parity and cleanup approval.

## Code Modernization

Run pyupgrade rules to modernize syntax to your target Python version:

```bash
uv run ruff check --select=UP --fix .  # Auto-fix upgrades
uv run ruff check --select=UP .        # Preview only
```

Common modernizations include:
- `typing.Optional[X]` → `X | None`
- `typing.List[X]` → `list[X]`
- `super(ClassName, self)` → `super()`
- Format strings and other syntax upgrades

## Line Length Migration

If migrating from 120 to 100 char lines, expect manual fixes.
For less churn during initial migration, keep existing:

```toml
line-length = 120  # Match existing; tighten later
```
