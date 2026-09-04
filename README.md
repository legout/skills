# Skills

Reusable agent skills published by [legout](https://github.com/legout) for installation with the [Agent Skills CLI](https://skills.sh/).

## Install

Install both skills for Pi:

```bash
npx skills add legout/skills \
  --skill merge-worktree \
  --skill make-release \
  --global --agent pi --yes --copy
```

Or install one:

```bash
npx skills add legout/skills --skill merge-worktree --global --agent pi --yes --copy
npx skills add legout/skills --skill make-release --global --agent pi --yes --copy
```

## Skills

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

## Usage

```text
/skill:merge-worktree local /path/to/worktree --clean-up
/skill:merge-worktree pr /path/to/worktree
/skill:make-release patch --dry-run
/skill:make-release minor
```

## Development

```bash
bash -n tests/skills_test.sh
bash tests/skills_test.sh
```

## License

[MIT](LICENSE)
