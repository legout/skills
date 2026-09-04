# Skills

Reusable agent skills published by [legout](https://github.com/legout) for installation with the [Agent Skills CLI](https://skills.sh/).

## Install

Install all skills for Pi:

```bash
npx skills add legout/skills \
  --skill orchestrate-implementation \
  --skill merge-worktree \
  --skill make-release \
  --skill handoff \
  --skill effective-agent-skills \
  --skill agent-md-refactor \
  --global --agent pi --yes --copy
```

Or install one:

```bash
npx skills add legout/skills --skill orchestrate-implementation --global --agent pi --yes --copy
npx skills add legout/skills --skill merge-worktree --global --agent pi --yes --copy
npx skills add legout/skills --skill make-release --global --agent pi --yes --copy
npx skills add legout/skills --skill handoff --global --agent pi --yes --copy
npx skills add legout/skills --skill effective-agent-skills --global --agent pi --yes --copy
npx skills add legout/skills --skill agent-md-refactor --global --agent pi --yes --copy
```

## Skills

### `orchestrate-implementation`

Executes plans, specifications, ADRs, and tickets with isolated Pi workers, explicit test obligations, adaptive independent review, durable handoffs, and orchestrator-owned integration. It uses `pi-subagents` for child lifecycle and optionally consults named read-only `pi-intercom` peers.

### `merge-worktree`

Integrates a registered Git worktree locally or through an automatically merged GitHub pull request. It commits pending source changes, validates on an isolated integration branch, attempts intent-preserving conflict resolution, pushes and verifies the target, and optionally removes the merged worktree with `--clean-up`.

Required companion skills:

- `github` for pull-request operations
- [`resolving-merge-conflicts`](https://skills.sh/mattpocock/skills/resolving-merge-conflicts) for conflicts

Install the conflict resolver:

```bash
npx skills add mattpocock/skills \
  --skill resolving-merge-conflicts \
  --global --agent pi --yes --copy
```

### `make-release`

Creates patch, minor, or major releases for Python/uv and Node projects. It previews the release, updates versions and changelogs, validates build artifacts, commits and pushes, creates an immutable version tag and GitHub Release, and optionally publishes Python packages to PyPI.

Required companion skills:

- `update-changelog`
- `commit`
- `github`
- `uv` for Python releases

### `agent-md-refactor`

Refactors bloated `AGENTS.md`, `CLAUDE.md`, or similar instruction files into concise roots with linked, progressive-disclosure documentation.

### Adopted upstream skills

These two general-purpose skills are adopted from [David Ondrej's `skills` repository](https://github.com/davidondrej/skills) at pinned commit [`11dee2e`](https://github.com/davidondrej/skills/tree/11dee2ebc2d045806b686ba0b57746f1e3d7e331). They are MIT-licensed; see [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).

- `handoff` — creates a compact, redacted handoff for a fresh agent when context or sessions change.
- `effective-agent-skills` — guidance for authoring, composing, testing, and securing `SKILL.md` files.

## Source updates

`sources.json` records each adopted source and commit. Check it manually or from CI:

```bash
bash scripts/check-skill-sources.sh
```

The check is read-only. A non-zero exit means a pinned upstream branch moved or a local adopted file is missing; inspect the printed compare URL before updating any copy. Links alone are not enough for skill discovery, so adopted skills stay vendored and pinned.

## Usage

```text
/skill:orchestrate-implementation supervised path/to/plan.md
/skill:merge-worktree local /path/to/worktree --clean-up
/skill:merge-worktree pr /path/to/worktree
/skill:make-release patch --dry-run
/skill:make-release minor
/skill:agent-md-refactor CLAUDE.md
```

## Development

```bash
bash -n tests/skills_test.sh
bash tests/skills_test.sh
```

## License

[MIT](LICENSE)
