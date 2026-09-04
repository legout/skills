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

orchestrate="$ROOT/skills/orchestrate-implementation/SKILL.md"
handoff="$ROOT/skills/handoff/SKILL.md"
effective="$ROOT/skills/effective-agent-skills/SKILL.md"
agent_md_refactor="$ROOT/skills/agent-md-refactor/SKILL.md"
merge="$ROOT/skills/merge-worktree/SKILL.md"
release="$ROOT/skills/make-release/SKILL.md"

validate_frontmatter "$agent_md_refactor" agent-md-refactor
for term in 'progressive disclosure' 'AGENTS.md' 'CLAUDE.md' '## Verification'; do
  assert_contains "$agent_md_refactor" "$term"
done

validate_frontmatter "$handoff" handoff
assert_contains "$handoff" "davidondrej/skills"
test -f "$ROOT/skills/handoff/agents/openai.yaml"

validate_frontmatter "$effective" effective-agent-skills
assert_contains "$effective" "davidondrej/skills"

for term in 'agent-md-refactor' '/skill:agent-md-refactor'; do
  assert_contains "$ROOT/README.md" "$term"
done

validate_frontmatter "$orchestrate" orchestrate-implementation
for term in new-test existing-check no-new-test adaptive lastReviewedSha '## Test obligations' '## Review policy' 'durable handoff patch paths'; do
  assert_contains "$orchestrate" "$term"
done
test -f "$ROOT/skills/orchestrate-implementation/evals/evals.json"
test -f "$ROOT/skills/orchestrate-implementation/evals/fixtures/conflicting-inputs.md"
test -f "$ROOT/skills/orchestrate-implementation/evals/fixtures/feature-plan.md"

validate_frontmatter "$merge" merge-worktree
for term in github resolving-merge-conflicts 'git merge --no-ff' 'gh pr checks --watch' 'gh pr merge --merge' --clean-up 'git worktree remove' 'git worktree prune' 'temporary integration branch' 'Never use `rm -rf`'; do
  assert_contains "$merge" "$term"
done

validate_frontmatter "$release" make-release
for term in update-changelog commit github uv patch minor major pyproject.toml package.json 'uv build' 'uvx twine check' UV_PUBLISH_TOKEN PYPI_API_TOKEN 'id-token: write' --dry-run 'explicit approval' 'gh run watch <run-id>' 'gh release create' --notes-file mktemp 'fresh temporary uv environment' 'chore(release): <version>' --no-verify; do
  assert_contains "$release" "$term"
done

bash -n "$ROOT/scripts/check-skill-sources.sh"
python3 - "$ROOT/sources.json" <<'PY'
import json
import sys

manifest = json.load(open(sys.argv[1]))
assert manifest["version"] == 1
assert len(manifest["sources"]) == 2
assert all(len(item["commit"]) == 40 for item in manifest["sources"])
PY

test -f "$ROOT/THIRD_PARTY_NOTICES.md"
assert_contains "$ROOT/THIRD_PARTY_NOTICES.md" "Copyright (c) 2026 David Ondrej"

printf 'all skills valid\n'
