#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)

assert_contains() {
  grep -F -- "$2" "$1" >/dev/null || {
    echo "missing in $1: $2" >&2
    exit 1
  }
}

validate_frontmatter() {
  local skill="$1" name="$2"
  test -f "$skill"
  test "$(head -n 1 "$skill")" = "---"
  assert_contains "$skill" "name: $name"
  assert_contains "$skill" "description:"
}

merge="$ROOT/skills/merge-worktree/SKILL.md"
release="$ROOT/skills/make-release/SKILL.md"

validate_frontmatter "$merge" merge-worktree
for term in github resolving-merge-conflicts 'git merge --no-ff' 'gh pr checks --watch' 'gh pr merge --merge' --clean-up 'git worktree remove' 'git worktree prune' 'temporary integration branch' 'Never use `rm -rf`'; do
  assert_contains "$merge" "$term"
done

validate_frontmatter "$release" make-release
for term in update-changelog commit github uv patch minor major pyproject.toml package.json 'uv build' 'uvx twine check' UV_PUBLISH_TOKEN PYPI_API_TOKEN 'id-token: write' --dry-run 'explicit approval' 'gh run watch <run-id>' 'gh release create' --notes-file mktemp 'fresh temporary uv environment' 'chore(release): <version>' --no-verify; do
  assert_contains "$release" "$term"
done

printf 'all skills valid\n'
