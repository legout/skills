# Dependabot: Automated Dependency Updates

[Dependabot](https://docs.github.com/en/code-security/dependabot) automatically creates pull requests to keep your dependencies up to date. GitHub hosts it natively—no external service required.

## Why Use Dependabot?

- **Security**: Automatically patches known vulnerabilities
- **Freshness**: Keeps dependencies current without manual tracking
- **Visibility**: PRs show changelogs and compatibility notes

## Configuration

After the user approves automated dependency PRs, adapt [templates/dependabot.yml](../templates/dependabot.yml) to the repository and validate it against current GitHub documentation before writing `.github/dependabot.yml`.

The template includes:
- Weekly update schedule for pip and GitHub Actions
- 7-day cooldown for supply chain protection
- Grouping to reduce PR noise

## Supply Chain Protection

The `cooldown.default-days: 7` setting delays version-update PRs for newly published versions. It can reduce immediate exposure, but it does not detect or prevent a compromised package.

**Why this matters:**
- Attackers sometimes publish malicious versions of legitimate packages
- A 7-day delay allows time for detection and removal
- Combined with weekly schedules, this balances security with freshness

## Common Options

| Option | Description |
|--------|-------------|
| `interval` | `daily`, `weekly`, or `monthly` |
| `cooldown.default-days` | Days to wait before updating new releases |
| `ignore` | Skip specific dependencies or versions |
| `groups` | Group related updates into single PRs |
| `reviewers` | Auto-assign reviewers to PRs |

## See Also

- [GitHub Dependabot docs](https://docs.github.com/en/code-security/dependabot/dependabot-version-updates/configuration-options-for-the-dependabot.yml-file)
- [security-setup.md](./security-setup.md) - Security tooling overview
- [prek.md](./prek.md) - Pre-commit hooks (complementary tool)
