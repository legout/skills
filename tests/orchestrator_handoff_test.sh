#!/usr/bin/env bash
set -euo pipefail

# One focused integration test for the documented durable handoff recipe:
# preserve a complete worker tree after cleanup, reject tampered identity, and
# assemble only the reconstructed commit.

ROOT=$(cd "$(dirname "$0")/.." && pwd)
DOC="$ROOT/skills/workflow/orchestrate-implementation/references/pi-dispatch.md"
TMP=$(mktemp -d "${TMPDIR:-/tmp}/orchestrator-handoff.XXXXXX")
trap 'rm -rf "$TMP"' EXIT

fail() {
    printf 'FAIL: %s\n' "$*" >&2
    exit 1
}

RECIPE_DIR="$TMP/recipes"
mkdir -p "$RECIPE_DIR"
awk -v dir="$RECIPE_DIR" '
    /^## Durable lifecycle recipe$/ { section = 1; next }
    section && /^## / { exit }
    section && /^```bash$/ { block = 1; n++; next }
    block && /^```$/ { block = 0; next }
    block { print > (dir "/block" n ".sh") }
' "$DOC"
for n in 1 2 3; do
    test -s "$RECIPE_DIR/block$n.sh" || fail "missing recipe block $n"
    bash -n "$RECIPE_DIR/block$n.sh"
done

export GIT_CONFIG_GLOBAL="$TMP/gitconfig"
export GIT_CONFIG_SYSTEM=/dev/null
export GIT_CONFIG_NOSYSTEM=1
export GIT_TERMINAL_PROMPT=0
: >"$GIT_CONFIG_GLOBAL"

REPO="$TMP/repo"
mkdir -p "$REPO"
git -C "$REPO" init -q
git -C "$REPO" config user.name test
git -C "$REPO" config user.email test@example.invalid
printf 'keep\n' >"$REPO/keep.txt"
printf 'delete\n' >"$REPO/remove.txt"
printf '#!/bin/sh\n' >"$REPO/mode.sh"
printf 'target\n' >"$REPO/target.txt"
git -C "$REPO" add .
git -C "$REPO" commit -qm base

run=test lane=api
base_sha=$(git -C "$REPO" rev-parse HEAD)
base_ref="refs/heads/orchestrator/$run/base/$lane"
worker="$TMP/worker"
review="$TMP/review"
candidate="$TMP/candidate"
patch="$TMP/lane.patch"
review_branch="orchestrator/$run/review/$lane"

run_recipe() {
    (cd "$REPO" && exec bash "$1") >"$TMP/recipe.log" 2>&1
}

export run lane base_sha
run_recipe "$RECIPE_DIR/block1.sh" || fail "base pin failed"
test "$(git -C "$REPO" rev-parse "$base_ref")" = "$base_sha" || fail "wrong base pin"

git -C "$REPO" worktree add -q -b "orchestrator/$run/worker/$lane" "$worker" "$base_ref"
printf 'changed\n' >>"$worker/keep.txt"
rm "$worker/remove.txt"
printf '\000\001binary\000\377' >"$worker/data.bin"
chmod +x "$worker/mode.sh"
ln -s target.txt "$worker/link"
git -C "$worker" add -A
git -C "$worker" commit -qm worker
worker_sha=$(git -C "$worker" rev-parse HEAD)
expected_tree=$(git -C "$worker" rev-parse 'HEAD^{tree}')
git -C "$REPO" diff --binary "$base_sha" "$worker_sha" >"$patch"
patch_digest=$(git -C "$REPO" hash-object "$patch")
git -C "$REPO" worktree remove "$worker"
git -C "$REPO" branch -D "orchestrator/$run/worker/$lane" >/dev/null

# Recovery must reject a tampered patch before creating review resources.
export patch expected_tree review_path="$review" review_branch
export patch_digest=0000000000000000000000000000000000000000
if run_recipe "$RECIPE_DIR/block2.sh"; then fail "accepted bad patch digest"; fi
test ! -e "$review" || fail "bad digest created review worktree"

# Recovery must reject a moved pin rather than falling back to parent HEAD.
printf 'parent\n' >"$REPO/parent.txt"
git -C "$REPO" add parent.txt
git -C "$REPO" commit -qm parent
parent_sha=$(git -C "$REPO" rev-parse HEAD)
git -C "$REPO" update-ref "$base_ref" "$parent_sha"
patch_digest=$(git -C "$REPO" hash-object "$patch")
if run_recipe "$RECIPE_DIR/block2.sh"; then fail "accepted moved base pin"; fi
test ! -e "$review" || fail "moved pin created review worktree"
git -C "$REPO" update-ref "$base_ref" "$base_sha"

# The valid artifact reconstructs the exact worker tree, including modes,
# deletion, symlink, and binary content.
run_recipe "$RECIPE_DIR/block2.sh" || fail "reconstruction failed"
reviewed_sha=$(git -C "$review" rev-parse HEAD)
test "$(git -C "$review" rev-parse 'HEAD^{tree}')" = "$expected_tree" || fail "tree mismatch"
test ! -e "$review/parent.txt" || fail "recovery used moving parent HEAD"
test -x "$review/mode.sh" || fail "mode lost"
test -L "$review/link" || fail "symlink lost"
test ! -e "$review/remove.txt" || fail "deletion lost"

# Candidate assembly consumes the reconstructed commit, not the vanished worker.
export reviewed_sha candidate_path="$candidate"
run_recipe "$RECIPE_DIR/block3.sh" || fail "candidate assembly failed"
test "$(git -C "$candidate" rev-parse 'HEAD^{tree}')" = "$expected_tree" || fail "candidate tree mismatch"
git -C "$REPO" worktree list --porcelain | grep -F "branch refs/heads/orchestrator/$run/candidate" >/dev/null || fail "candidate is not registered"

printf 'orchestrator handoff test passed\n'
