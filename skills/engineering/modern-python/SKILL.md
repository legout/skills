---
name: modern-python
description: Configures Python projects with modern tooling (uv, ruff, ty). Use when creating projects, writing standalone scripts, or migrating from pip/Poetry/mypy/black.
---

# Modern Python

Before changing a project, read its instructions and current configuration, preserve supported Python versions, and run installed CLI help. Do not replace a working toolchain unless the user requests migration and the replacement reaches validation parity.

## Route

- Standalone script with dependencies: read [PEP 723 scripts](references/pep723-scripts.md).
- New project or package: read [pyproject](references/pyproject.md), [Ruff config](references/ruff-config.md), and [testing](references/testing.md).
- Existing project migration: read [migration checklist](references/migration-checklist.md) before editing.
- uv command detail: read [uv commands](references/uv-commands.md).
- Security tooling: read [security setup](references/security-setup.md), [Dependabot](references/dependabot.md), and [prek](references/prek.md) only when requested or already used.

## Defaults for new work

- Manage dependencies with `uv add`, `uv remove`, and `uv sync`; run commands with `uv run`.
- Use dependency groups for development tools.
- Use Ruff for lint and format, ty for type checks, and pytest for tests unless project constraints require otherwise.
- Prefer `uv_build` for ordinary new packages.
- Never manually activate or manage a virtualenv.

## Minimal project

```bash
uv init myproject
cd myproject
uv add requests
uv add --group dev pytest ruff ty
uv run ruff check .
uv run ty check
uv run pytest
```

For repository documentation, follow its existing system. If it uses Zensical, validate with `uv run zensical build`; use `uv run zensical serve` only for interactive preview.

## Verification

Run the project's existing checks plus Ruff, ty, and tests when configured. During migration, compare old and new validation results before deleting legacy configuration. Hand versioning or publication to `make-release`.

## Source

Adapted under CC-BY-SA-4.0 from Trail of Bits' [`modern-python` package](https://github.com/trailofbits/skills/tree/d3323cefbcf645678b8dc481de204b02ad3d02dc/plugins/modern-python/skills/modern-python), pinned to commit `d3323cefbcf645678b8dc481de204b02ad3d02dc`. See `sources.json` and `THIRD_PARTY_NOTICES.md`.
