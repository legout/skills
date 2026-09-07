#!/usr/bin/env bash
set -euo pipefail

# Offline lifecycle regression: the durable handoff recipe documented in
# orchestrate-implementation/references/pi-dispatch.md must actually replay,
# reconstruct, and assemble a lane after the managed worker resources are gone,
# and must refuse corrupted inputs before mutating anything.
#
# The documented command blocks are extracted from the reference and executed
# as external bash processes so their exit status is observable even under
# shell conditional execution. This suite is static/offline Git evidence, not
# live native-runtime evidence.

ROOT=$(cd "$(dirname "$0")/.." && pwd)
RECIPE_DOC="$ROOT/skills/workflow/orchestrate-implementation/references/pi-dispatch.md"

fail() {
    printf 'FAIL: %s\n' "$*" >&2
    [ -f "$recipe_log" ] && tail -n 20 "$recipe_log" >&2
    exit 1
}

TMP=$(mktemp -d "${TMPDIR:-/tmp}/orchestrator-handoff.XXXXXX")
recipe_log="$TMP/recipe.log"
cleanup() {
    status=$?
    if [ "$status" -eq 0 ]; then
        rm -rf "$TMP"
    else
        printf 'fixture preserved for recovery: %s\n' "$TMP" >&2
    fi
    exit "$status"
}
trap cleanup EXIT

# Isolate the fixture from the invoking user's Git configuration.
export GIT_CONFIG_GLOBAL="$TMP/gitconfig"
export GIT_CONFIG_SYSTEM=/dev/null
export GIT_CONFIG_NOSYSTEM=1
export GIT_TERMINAL_PROMPT=0
: >"$GIT_CONFIG_GLOBAL"

# Extract the runnable ```bash blocks of the documented "Durable lifecycle
# recipe" section. The test consumes the documented recipe itself, never a
# separately corrected duplicate.
RECIPE_DIR="$TMP/recipes"
mkdir -p "$RECIPE_DIR"
awk -v dir="$RECIPE_DIR" '
    /^## Durable lifecycle recipe$/ { in_section = 1; next }
    in_section && /^## / { exit }
    in_section && /^```bash$/ { in_block = 1; n++; next }
    in_block && /^```$/ { in_block = 0; next }
    in_block { print > (dir "/block" n ".sh") }
' "$RECIPE_DOC"
for expected in 1 2 3; do
    [ -s "$RECIPE_DIR/block$expected.sh" ] || fail "runnable recipe block $expected missing from $RECIPE_DOC"
    bash -n "$RECIPE_DIR/block$expected.sh" || fail "documented recipe block $expected does not parse"
done
PIN_RECIPE="$RECIPE_DIR/block1.sh"
RECONSTRUCT_RECIPE="$RECIPE_DIR/block2.sh"
CANDIDATE_RECIPE="$RECIPE_DIR/block3.sh"
grep -q "update-ref" "$PIN_RECIPE" || fail "pin recipe does not create the base ref"
grep -q "apply --index" "$RECONSTRUCT_RECIPE" || fail "reconstruct recipe does not replay the patch"
grep -q "cherry-pick" "$CANDIDATE_RECIPE" || fail "candidate recipe does not assemble commits"

# Execute a documented recipe block as an external bash process from the
# fixture repository; its own exit status is the observable result.
run_recipe() {
    (
        cd "$REPO"
        exec bash "$1"
    ) >"$recipe_log" 2>&1
}

expect_refusal() {
    description=$1
    if run_recipe "$2"; then
        fail "$description was accepted (recipe exited 0)"
    fi
}

drop_worktree() {
    # These exact disposable resources were created by an expected refusal probe.
    git -C "$REPO" worktree remove --force "$1" >/dev/null || fail "probe worktree cleanup failed: $1"
    git -C "$REPO" branch -D "$2" >/dev/null || fail "probe branch cleanup failed: $2"
}

REPO="$TMP/repo"
mkdir -p "$REPO"
git -C "$REPO" init -q
git -C "$REPO" config user.name "orchestrator test"
git -C "$REPO" config user.email "orchestrator-test@example.invalid"

printf 'keep\n' >"$REPO/keep.txt"
printf 'delete me\n' >"$REPO/remove.txt"
printf '#!/bin/sh\necho base\n' >"$REPO/mode.sh"
printf 'target\n' >"$REPO/link-target.txt"
git -C "$REPO" add keep.txt remove.txt mode.sh link-target.txt
git -C "$REPO" commit -qm "base fixture"
BASE_SHA=$(git -C "$REPO" rev-parse HEAD)
BASE_TREE=$(git -C "$REPO" rev-parse HEAD^{tree})

RUN_ID="test-run"
LANE="lane-a"
BASE_REF="refs/heads/orchestrator/$RUN_ID/base/$LANE"
WORKER_BRANCH="orchestrator/$RUN_ID/worker/$LANE"
REVIEW_BRANCH="orchestrator/$RUN_ID/review/$LANE"
FIX_BRANCH="orchestrator/$RUN_ID/fix/$LANE"
FIX_REVIEW_BRANCH="orchestrator/$RUN_ID/review/$LANE-r2"
CANDIDATE_BRANCH="orchestrator/$RUN_ID/candidate"
WORKER="$TMP/worker"
REVIEW="$TMP/review"
FIX="$TMP/fix"
FIXREVIEW="$TMP/fix-review"
CANDIDATE="$TMP/candidate"
PATCH="$TMP/lane.patch"
FIX_PATCH="$TMP/fix.patch"

# The orchestrator pins a named base before allocating the worker, using the
# documented pin recipe. Creation must be collision-checked and must accept the
# approved lane base (which may itself include reviewed upstream changes).
export run="$RUN_ID" lane="$LANE" base_sha="$BASE_SHA"
run_recipe "$PIN_RECIPE" || fail "documented base pin recipe failed"
[ "$(git -C "$REPO" rev-parse "$BASE_REF")" = "$BASE_SHA" ] || fail "base ref was not pinned"

git -C "$REPO" worktree add -q -b "$WORKER_BRANCH" "$WORKER" "$BASE_REF"

printf 'worker change\n' >>"$WORKER/keep.txt"
printf 'replacement\n' >"$WORKER/new.txt"
rm "$WORKER/remove.txt"
printf '\000\001\002\003binary\000\377' >"$WORKER/data.bin"
chmod +x "$WORKER/mode.sh"
ln -s "link-target.txt" "$WORKER/link"
git -C "$WORKER" add -A
git -C "$WORKER" commit -qm "worker lane"
WORKER_SHA=$(git -C "$WORKER" rev-parse HEAD)
WORKER_TREE=$(git -C "$WORKER" rev-parse HEAD^{tree})
git -C "$WORKER" diff --quiet || fail "worker is not clean"
git -C "$REPO" diff --binary "$BASE_SHA" "$WORKER_SHA" >"$PATCH"
PATCH_DIGEST=$(git -C "$REPO" hash-object "$PATCH")
grep -q '^GIT binary patch$' "$PATCH" || fail "binary data was not preserved in handoff patch"
grep -q '^new file mode 120000$' "$PATCH" || fail "symlink mode was not preserved in handoff patch"
grep -q '^old mode 100644$' "$PATCH" || fail "mode change was not preserved in handoff patch"

# Normal child cleanup may remove both the worktree and its branch.
git -C "$REPO" worktree remove "$WORKER"
git -C "$REPO" branch -D "$WORKER_BRANCH" >/dev/null
[ ! -d "$WORKER" ] || fail "worker worktree still exists"
if git -C "$REPO" show-ref --verify --quiet "refs/heads/$WORKER_BRANCH"; then
    fail "worker branch still exists"
fi

# Move the parent after the worker completed. Recovery must not use this HEAD.
printf 'parent-only\n' >"$REPO/parent-only.txt"
git -C "$REPO" add parent-only.txt
git -C "$REPO" commit -qm "unrelated parent movement"
PARENT_SHA=$(git -C "$REPO" rev-parse HEAD)
[ "$PARENT_SHA" != "$BASE_SHA" ] || fail "parent did not move"

# An existing pin is never silently overwritten: re-running the pin recipe with
# a different claimed base must refuse and leave the pin unchanged.
export base_sha="$PARENT_SHA"
expect_refusal "base pin overwrite" "$PIN_RECIPE"
[ "$(git -C "$REPO" rev-parse "$BASE_REF")" = "$BASE_SHA" ] || fail "existing base pin was overwritten"
# The pin recipe does accept a genuinely approved lane base that is not parent
# HEAD (for example a reviewed upstream candidate base) for a fresh lane.
[ "$(git -C "$REPO" rev-parse HEAD)" != "$WORKER_SHA" ] || fail "approved upstream probe base is current HEAD"
export lane="lane-b" base_sha="$WORKER_SHA"
run_recipe "$PIN_RECIPE" || fail "pin recipe refused an approved non-HEAD lane base"
[ "$(git -C "$REPO" rev-parse "refs/heads/orchestrator/$RUN_ID/base/lane-b")" = "$WORKER_SHA" ] || fail "approved lane base pin was not created"
git -C "$REPO" update-ref -d "refs/heads/orchestrator/$RUN_ID/base/lane-b"
export lane="$LANE" base_sha="$BASE_SHA"

# Refusal probe: a digest mismatch must abort before creating anything.
export patch="$PATCH" patch_digest="0000000000000000000000000000000000000000" expected_tree="$WORKER_TREE" review_path="$REVIEW" review_branch="$REVIEW_BRANCH"
expect_refusal "handoff patch digest mismatch" "$RECONSTRUCT_RECIPE"
[ ! -e "$REVIEW" ] || fail "digest mismatch still created a review worktree"
git -C "$REPO" show-ref --verify --quiet "refs/heads/$REVIEW_BRANCH" && fail "digest mismatch still created a review branch"

# Refusal probe: a moved named base must abort before creating anything; there
# is no fallback to the parent's current HEAD.
git -C "$REPO" update-ref "$BASE_REF" "$PARENT_SHA"
export patch_digest="$PATCH_DIGEST"
expect_refusal "moved base pin" "$RECONSTRUCT_RECIPE"
[ ! -e "$REVIEW" ] || fail "moved base still created a review worktree"
git -C "$REPO" show-ref --verify --quiet "refs/heads/$REVIEW_BRANCH" && fail "moved base still created a review branch"
git -C "$REPO" update-ref "$BASE_REF" "$BASE_SHA"
[ "$(git -C "$REPO" rev-parse "$BASE_REF")" = "$BASE_SHA" ] || fail "base pin was not restored"

# Refusal probe: a corrupt patch whose digest matches the corrupt bytes must
# abort at apply --check, before any commit exists on the review branch.
printf 'not a git patch\n' >"$TMP/corrupt.patch"
export patch="$TMP/corrupt.patch" patch_digest="$(git -C "$REPO" hash-object "$TMP/corrupt.patch")" review_path="$REVIEW" review_branch="$REVIEW_BRANCH"
expect_refusal "corrupt handoff patch" "$RECONSTRUCT_RECIPE"
[ "$(git -C "$REPO" rev-parse "$REVIEW_BRANCH" 2>/dev/null)" = "$BASE_SHA" ] || fail "corrupt patch left a commit on the review branch"
drop_worktree "$REVIEW" "$REVIEW_BRANCH"

# Refusal probe: a staged tree that differs from the expected clean worker tree
# must abort before the reconstruction commit.
export patch="$PATCH" patch_digest="$PATCH_DIGEST" expected_tree="$BASE_TREE" review_path="$REVIEW" review_branch="$REVIEW_BRANCH"
expect_refusal "wrong expected tree" "$RECONSTRUCT_RECIPE"
[ "$(git -C "$REPO" rev-parse "$REVIEW_BRANCH" 2>/dev/null)" = "$BASE_SHA" ] || fail "wrong tree still produced a review commit"
drop_worktree "$REVIEW" "$REVIEW_BRANCH"

# Reconstruct a parent-owned review checkout at the pinned base using the
# documented recipe.
export expected_tree="$WORKER_TREE" review_path="$REVIEW" review_branch="$REVIEW_BRANCH"
run_recipe "$RECONSTRUCT_RECIPE" || fail "documented reconstruction recipe failed"
[ "$(git -C "$REVIEW" rev-parse HEAD)" != "$BASE_SHA" ] || fail "reconstruction made no commit"
[ ! -e "$REVIEW/parent-only.txt" ] || fail "review checkout included moved parent content"
[ "$(git -C "$REVIEW" rev-parse HEAD^{tree})" = "$WORKER_TREE" ] || fail "reconstructed tree differs from worker tree"
git -C "$REVIEW" diff --quiet || fail "review checkout is dirty"
REVIEW_SHA=$(git -C "$REVIEW" rev-parse HEAD)
git -C "$REPO" merge-base --is-ancestor "$BASE_SHA" "$REVIEW_SHA" || fail "review commit is not rooted at the pinned base"

# A fresh fix worker replays the full patch from the same base. Its complete
# replacement patch supersedes, rather than incrementally extends, the lane patch.
git -C "$REPO" worktree add -q -b "$FIX_BRANCH" "$FIX" "$BASE_REF"
git -C "$FIX" apply --index "$PATCH"
printf 'reviewed and fixed\n' >>"$FIX/new.txt"
git -C "$FIX" add new.txt
git -C "$FIX" commit -qm "fix lane-a review"
FIX_SHA=$(git -C "$FIX" rev-parse HEAD)
FIX_TREE=$(git -C "$FIX" rev-parse HEAD^{tree})
git -C "$FIX" diff --quiet || fail "fix worker is not clean"
git -C "$REPO" diff --binary "$BASE_SHA" "$FIX_SHA" >"$FIX_PATCH"
FIX_DIGEST=$(git -C "$REPO" hash-object "$FIX_PATCH")
[ "$FIX_DIGEST" != "$PATCH_DIGEST" ] || fail "fix patch did not replace the prior handoff"
grep -q 'reviewed and fixed' "$FIX_PATCH" || fail "replacement patch omitted the fix"

# The fix worker's managed resources are also gone before recovery.
git -C "$REPO" worktree remove "$FIX"
git -C "$REPO" branch -D "$FIX_BRANCH" >/dev/null
[ ! -d "$FIX" ] || fail "fix worktree still exists"
if git -C "$REPO" show-ref --verify --quiet "refs/heads/$FIX_BRANCH"; then
    fail "fix branch still exists"
fi

# Refusal probe for the reviewed artifact itself: replacing the replacement
# patch with plain text containing the reviewed marker must be refused. The
# reconstruction consumes only the durable artifact, never a live worker SHA.
cp "$FIX_PATCH" "$TMP/fix.patch.pristine"
printf 'reviewed and fixed\n' >"$FIX_PATCH"
export patch="$FIX_PATCH" patch_digest="$FIX_DIGEST" expected_tree="$FIX_TREE" review_path="$FIXREVIEW" review_branch="$FIX_REVIEW_BRANCH"
expect_refusal "plain-text replacement artifact" "$RECONSTRUCT_RECIPE"
[ ! -e "$FIXREVIEW" ] || fail "plain-text artifact still created a review worktree"
git -C "$REPO" show-ref --verify --quiet "refs/heads/$FIX_REVIEW_BRANCH" && fail "plain-text artifact still created a review branch"
mv "$TMP/fix.patch.pristine" "$FIX_PATCH"
[ "$(git -C "$REPO" hash-object "$FIX_PATCH")" = "$FIX_DIGEST" ] || fail "replacement patch was not restored"

# The replacement patch is a full replacement: it must not apply on top of the
# prior lane result.
if git -C "$REVIEW" apply --check "$FIX_PATCH" 2>/dev/null; then
    fail "replacement patch applied incrementally onto the prior lane result"
fi

# Reconstruct the replacement from the pinned base; its review boundary resets
# to the pinned base and covers the complete replacement range.
run_recipe "$RECONSTRUCT_RECIPE" || fail "documented replacement reconstruction recipe failed"
FIX_REVIEW_SHA=$(git -C "$FIXREVIEW" rev-parse HEAD)
[ "$(git -C "$FIXREVIEW" rev-parse HEAD^{tree})" = "$FIX_TREE" ] || fail "replacement tree differs from fix worker tree"
git -C "$REPO" merge-base --is-ancestor "$BASE_SHA" "$FIX_REVIEW_SHA" || fail "replacement review is not rooted at the pinned base"
git -C "$REPO" diff "$BASE_SHA" "$FIX_REVIEW_SHA" -- keep.txt | grep -q 'worker change' || fail "replacement range lost the lane change"
git -C "$REPO" diff "$BASE_SHA" "$FIX_REVIEW_SHA" -- new.txt | grep -q 'reviewed and fixed' || fail "replacement range lost the fix"

# Candidate assembly uses a separate registered checkout and only the
# reconstructed reviewed commit, never a deleted worker path or live worker SHA.
export reviewed_sha="$FIX_REVIEW_SHA" candidate_path="$CANDIDATE"
run_recipe "$CANDIDATE_RECIPE" || fail "documented candidate assembly recipe failed"
CANDIDATE_SHA=$(git -C "$CANDIDATE" rev-parse HEAD)
[ "$(git -C "$CANDIDATE" rev-parse HEAD^{tree})" = "$FIX_TREE" ] || fail "candidate tree differs from accepted fix tree"
git -C "$CANDIDATE" diff --quiet || fail "candidate checkout is dirty"
git -C "$REPO" merge-base --is-ancestor "$BASE_SHA" "$CANDIDATE_SHA" || fail "candidate is not rooted at the pinned base"
[ "$(git -C "$REPO" rev-list --count "$BASE_SHA..$CANDIDATE_SHA")" = "1" ] || fail "candidate assembled more than the reconstructed reviewed commit"
[ -e "$CANDIDATE/.git" ] || fail "candidate checkout was not registered"
git -C "$REPO" worktree list --porcelain | grep -F "branch refs/heads/$CANDIDATE_BRANCH" >/dev/null || fail "candidate missing from worktree registry"
[ "$(git -C "$REPO" rev-parse "$BASE_REF")" = "$BASE_SHA" ] || fail "base pin moved during the run"

printf 'orchestrator handoff test passed\n'
