# Security Setup

Security tooling for Python projects: pre-commit hooks, CI auditing, and dependency scanning.

## Tool Installation

Install these tools before running the quick setup commands below.

### prek (pre-commit runner)

```bash
# Homebrew (recommended)
brew install prek

# Cargo
cargo install prek

# Standalone installer
# Confirm the current command and checksum in prek's official documentation,
# inspect the script, and obtain approval before executing a download.
```

### Security tools

Pre-commit hooks auto-install tools when run via prek. For manual CLI usage:

```bash
# Homebrew (macOS/Linux)
brew install actionlint shellcheck

# Python tools via uv
uv tool install detect-secrets
uv tool install zizmor
```

Alternative installation methods:

- **actionlint**: `go install github.com/rhysd/actionlint/cmd/actionlint@latest`
- **zizmor**: `cargo install zizmor`
- **detect-secrets**: `pipx install detect-secrets`

## Quick Setup

```bash
# 1. Install security hooks
prek install

# 2. Initialize secrets baseline
detect-secrets scan > .secrets.baseline

# 3. Audit existing workflows
actionlint .github/workflows/
zizmor .github/workflows/
```

See [templates/pre-commit-config.yaml](../templates/pre-commit-config.yaml) for a complete hook configuration.

## Tool Matrix

| Tool | Runs | Catches |
|------|------|---------|
| **shellcheck** | pre-commit | Shell script bugs, quoting issues |
| **detect-secrets** | pre-commit | Leaked API keys, passwords, tokens |
| **actionlint** | pre-commit, CI | Workflow syntax errors, invalid refs |
| **zizmor** | pre-commit, CI | Workflow security issues, excessive permissions |
| **uv audit** | CI, manual | Known vulnerabilities in locked dependencies |
| **Dependabot** | scheduled | Outdated dependencies with vulnerabilities |

## Pre-commit Hooks

These run locally before each commit via prek.

### shellcheck - Shell Script Linting

Catches common shell scripting errors: unquoted variables, undefined variables, deprecated syntax.

```yaml
# In .pre-commit-config.yaml
- repo: https://github.com/koalaman/shellcheck-precommit
  rev: <latest>  # https://github.com/koalaman/shellcheck-precommit/tags
  hooks:
    - id: shellcheck
      args: [--severity=error]  # Start strict, adjust if needed
```

Common findings:

- `SC2086`: Unquoted variable expansion (word splitting risk)
- `SC2046`: Unquoted command substitution
- `SC2155`: Declare and assign separately to avoid masking return values

### detect-secrets - Secret Detection

Prevents accidentally committing API keys, passwords, and tokens.

```yaml
- repo: https://github.com/Yelp/detect-secrets
  rev: <latest>  # https://github.com/Yelp/detect-secrets/releases
  hooks:
    - id: detect-secrets
      args: [--baseline, .secrets.baseline]
```

**First-time setup:**

```bash
# Generate baseline of existing "secrets" (false positives to ignore)
detect-secrets scan > .secrets.baseline

# Review with the installed detect-secrets audit command; do not print
# suspected secret values into shared logs or chat.
detect-secrets audit .secrets.baseline
```

**When hook fails:**

```bash
# View the finding (non-interactive)
detect-secrets audit --report .secrets.baseline
```

If false positive: update baseline with `detect-secrets scan --update .secrets.baseline`
If real secret: remove from code and rotate the credential.

## CI Security

These run in GitHub Actions on every push/PR.

### actionlint - Workflow Syntax Validation

Catches syntax errors, invalid action references, and type mismatches before they fail in CI.

```yaml
- repo: https://github.com/rhysd/actionlint
  rev: <latest>  # https://github.com/rhysd/actionlint/releases
  hooks:
    - id: actionlint
```

Run manually:

```bash
actionlint .github/workflows/
```

Common findings:

- Invalid event triggers
- Undefined workflow inputs
- Shell syntax errors in `run:` blocks
- Invalid action version references

### zizmor - Workflow Security Audit

Finds security issues in GitHub Actions workflows: excessive permissions, injection risks, untrusted inputs.

```yaml
- repo: https://github.com/zizmorcore/zizmor-pre-commit
  rev: <latest>  # https://github.com/zizmorcore/zizmor-pre-commit/releases
  hooks:
    - id: zizmor
      args: [--persona=regular, --min-severity=medium, --min-confidence=medium]
```

Run manually:

```bash
zizmor .github/workflows/
```

**Fixing `excessive-permissions`:**

Repository defaults can grant broader permissions than a job needs. Declare the smallest explicit permissions:

```yaml
# Read-only workflows (lint, test, audit)
permissions:
  contents: read

# Workflows that push or create releases
permissions:
  contents: write

# Workflows that comment on PRs
permissions:
  contents: read
  pull-requests: write
```

Common findings:

- `excessive-permissions`: No `permissions:` block
- `template-injection`: Using `${{ github.event.* }}` unsafely
- `unpinned-action`: Actions not pinned to SHA
- `dangerous-triggers`: `pull_request_target` with checkout

## Dependency Security

### Dependency Vulnerability Scanning

Prefer uv's built-in audit command when the installed version provides it:

```bash
uv audit --locked
```

This queries a vulnerability service; confirm network/privacy policy before using a custom or sensitive dependency set. If the installed uv has no audit command, use `pip-audit` only after reading its current help and documentation. Do not run automatic vulnerability fixes without reviewing the proposed dependency changes.

**When vulnerabilities found:**

1. Check if the CVE affects your usage (many are in unused code paths)
2. Review and test a targeted upgrade, for example `uv lock --upgrade-package <package>`
3. If no fix available: evaluate risk, consider alternatives, or add to ignore list

### Dependabot - Automated Updates

Automatically creates PRs for outdated dependencies.

Copy [templates/dependabot.yml](../templates/dependabot.yml) to `.github/dependabot.yml`.

**How auditing and Dependabot work together:**

| Tool | Trigger | Scope |
| --- | --- | --- |
| `uv audit` | Every CI run | Known vulnerabilities in current locked dependencies |
| Dependabot | Weekly schedule | Dependency updates through reviewable PRs |

- **Auditing** detects a vulnerable locked version.
- **Dependabot** proposes updates for review.

The 7-day cooldown delays version-update PRs for new releases; it can reduce immediate exposure but is not a substitute for review or auditing.

See [dependabot.md](./dependabot.md) for advanced configuration.

See [prek.md](./prek.md) for complete pre-commit hook configuration including security hooks.
