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
for reference in herdr-dispatch manifest-and-briefs; do
    awk '
        /^```bash$/ { block = 1; next }
        block && /^```$/ { exit }
        block { print }
    ' "$ROOT/skills/workflow/orchestrate-implementation/references/$reference.md" >"$RECIPE_DIR/$reference.sh"
    test -s "$RECIPE_DIR/$reference.sh" || fail "missing $reference recipe"
    bash -n "$RECIPE_DIR/$reference.sh"
done

export GIT_CONFIG_GLOBAL="$TMP/gitconfig"
export GIT_CONFIG_SYSTEM=/dev/null
export GIT_CONFIG_NOSYSTEM=1
export GIT_TERMINAL_PROMPT=0
: >"$GIT_CONFIG_GLOBAL"

# Real submodule commits remain available outside disposable worker checkouts.
module_origin="$TMP/submodule-origin"
git init -q "$module_origin"
git -C "$module_origin" config user.name test
git -C "$module_origin" config user.email test@example.invalid
printf 'first\n' >"$module_origin/version.txt"
git -C "$module_origin" add .
git -C "$module_origin" commit -qm first
module_base=$(git -C "$module_origin" rev-parse HEAD)
printf 'second\n' >"$module_origin/version.txt"
git -C "$module_origin" commit -qam second
module_head=$(git -C "$module_origin" rev-parse HEAD)

REPO="$TMP/repo"
mkdir -p "$REPO"
git -C "$REPO" init -q
git -C "$REPO" config user.name test
git -C "$REPO" config user.email test@example.invalid
git -C "$REPO" -c protocol.file.allow=always submodule add -q "$module_origin" submodule
git -C "$REPO/submodule" checkout -q "$module_base"
# Patch identities must not depend on attributes in either checkout.
printf '*.patch -text\ncrlf.txt -text\n' >"$REPO/.gitattributes"
printf 'before\r\nold\r\nafter\r\n' >"$REPO/crlf.txt"
printf 'before\nkeep\nafter\n' >"$REPO/keep.txt"
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
    (cd "${2:-$REPO}" && exec bash "$1") >"$TMP/recipe.log" 2>&1
}

export run lane base_sha
unset worker_branch candidate_branch
run_recipe "$RECIPE_DIR/block1.sh" || fail "base pin failed"
test "$(git -C "$REPO" rev-parse "$base_ref")" = "$base_sha" || fail "wrong base pin"

export worker_path="$worker"
run_recipe "$RECIPE_DIR/herdr-dispatch.sh" || fail "Herdr lane allocation failed"
printf '*.patch text\ncrlf.txt -text\n' >"$worker/.gitattributes"
printf 'before\r\nnew\r\nafter\r\n' >"$worker/crlf.txt"
printf 'before\nchanged  \nafter\n' >"$worker/keep.txt"
git -C "$worker" update-index --cacheinfo "160000,$module_head,submodule"
mkdir "$worker/module"
printf 'nested\n' >"$worker/module/nested.txt"
rm "$worker/remove.txt"
printf '\000\001binary\000\377' >"$worker/data.bin"
chmod +x "$worker/mode.sh"
ln -s target.txt "$worker/link"
git -C "$worker" add -A
git -C "$worker" commit -qm worker
worker_sha=$(git -C "$worker" rev-parse HEAD)
expected_tree=$(git -C "$worker" rev-parse 'HEAD^{tree}')
export base_ref patch
printf 'unstaged\n' >>"$worker/keep.txt"
if run_recipe "$RECIPE_DIR/manifest-and-briefs.sh" "$worker"; then fail "captured dirty worker"; fi
test ! -e "$patch" || fail "dirty worker emitted handoff"
git -C "$worker" restore keep.txt
# Git's display preference must not hide work from capture and later cleanup.
git -C "$REPO" config status.showUntrackedFiles no
printf 'uncommitted work\n' >"$worker/untracked.txt"
if run_recipe "$RECIPE_DIR/manifest-and-briefs.sh" "$worker"; then fail "captured hidden untracked work"; fi
test ! -e "$patch" || fail "untracked worker emitted handoff"
rm "$worker/untracked.txt"
git -C "$REPO" config --unset status.showUntrackedFiles
# Gitlink display formats can silently omit the submodule pointer, while
# zero-context diffs cannot be replayed by the documented apply command.
for format in log diff context-zero; do
    if [ "$format" = context-zero ]; then
        git -C "$REPO" config diff.context 0
    else
        git -C "$REPO" config diff.submodule "$format"
    fi
    format_patch="$TMP/$format.patch"
    patch="$format_patch" run_recipe "$RECIPE_DIR/manifest-and-briefs.sh" "$worker" || fail "$format capture failed"
    patch_digest=$(git -C "$REPO" hash-object --no-filters "$format_patch")
    patch="$format_patch" expected_tree="$expected_tree" \
      review_path="$TMP/$format-review" review_branch="orchestrator/$run/format/$format" \
      patch_digest="$patch_digest" run_recipe "$RECIPE_DIR/block2.sh" || fail "$format handoff did not reconstruct the worker tree"
    if [ "$format" = context-zero ]; then
        git -C "$REPO" config --unset diff.context
    else
        git -C "$REPO" config --unset diff.submodule
    fi
done

# Capture from a package cwd with user-facing diff preferences enabled.
git -C "$REPO" config color.diff always
git -C "$REPO" config diff.relative true
run_recipe "$RECIPE_DIR/manifest-and-briefs.sh" "$worker/module" || fail "handoff capture failed"
git -C "$REPO" apply --check "$patch" || fail "capture emitted an incomplete or colored patch"
git -C "$REPO" config --unset color.diff
git -C "$REPO" config --unset diff.relative
patch_digest=$(git -C "$REPO" hash-object --no-filters "$patch")
for identity in "worker_sha=$worker_sha" "expected_tree=$expected_tree" "patch_digest=$patch_digest"; do
    grep -Fx "$identity" "$TMP/recipe.log" >/dev/null || fail "capture metadata mismatch: $identity"
done
if run_recipe "$RECIPE_DIR/manifest-and-briefs.sh" "$worker"; then fail "overwrote existing handoff"; fi
test "$(git -C "$REPO" hash-object --no-filters "$patch")" = "$patch_digest" || fail "refused overwrite changed patch"
# Simulate native finalization before the parent reconstructs the final handoff.
git -C "$REPO" worktree remove "$worker"
# Retain the old worker branch as recovery evidence while allocating its fix.

# Recovery must reject a tampered patch before creating review resources.
export patch expected_tree review_path="$review" review_branch
export patch_digest=0000000000000000000000000000000000000000
if run_recipe "$RECIPE_DIR/block2.sh"; then fail "accepted bad patch digest"; fi
test ! -e "$review" || fail "bad digest created review worktree"

# Recovery must reject a moved pin rather than falling back to parent HEAD.
printf 'parent\n' >"$REPO/parent.txt"
printf '*.patch text\ncrlf.txt -text\n' >"$REPO/.gitattributes"
git -C "$REPO" add parent.txt .gitattributes
git -C "$REPO" commit -qm parent
parent_sha=$(git -C "$REPO" rev-parse HEAD)
git -C "$REPO" update-ref "$base_ref" "$parent_sha"
patch_digest=$(git -C "$REPO" hash-object --no-filters "$patch")
if run_recipe "$RECIPE_DIR/block2.sh"; then fail "accepted moved base pin"; fi
test ! -e "$review" || fail "moved pin created review worktree"
git -C "$REPO" update-ref "$base_ref" "$base_sha"

# A repository hook may stage generated content or leave tracked edits behind.
# Neither may pass as the clean, exact reconstruction that was just verified.
for hook_mode in staged unstaged; do
    printf '%s\n' '#!/bin/sh' "printf 'generated by hook\\n' > keep.txt" >"$REPO/.git/hooks/pre-commit"
    if [ "$hook_mode" = staged ]; then
        printf '%s\n' 'git add keep.txt' >>"$REPO/.git/hooks/pre-commit"
    fi
    chmod +x "$REPO/.git/hooks/pre-commit"
    review_path="$TMP/$hook_mode-hook-review"
    review_branch="orchestrator/$run/hook/$hook_mode"
    if run_recipe "$RECIPE_DIR/block2.sh"; then fail "accepted $hook_mode hook mutation"; fi
    test -d "$review_path" || fail "hook refusal discarded review checkout"
    if [ "$hook_mode" = staged ]; then
        grep -F 'committed tree differs from the expected worker tree' "$TMP/recipe.log" >/dev/null || fail "staged hook refusal was not tree verification"
    else
        grep -F 'review checkout is dirty' "$TMP/recipe.log" >/dev/null || fail "unstaged hook refusal was not cleanliness verification"
    fi
    rm "$REPO/.git/hooks/pre-commit"
done
review_path="$review"
review_branch="orchestrator/$run/review/$lane"

# Replay must preserve intentional whitespace even when Git normally fixes it.
git -C "$REPO" config apply.whitespace fix
# The valid artifact reconstructs the exact worker tree, including modes,
# deletion, symlink, nested content, binary content, and whitespace.
run_recipe "$RECIPE_DIR/block2.sh" || fail "reconstruction failed"
reviewed_sha=$(git -C "$review" rev-parse HEAD)
test "$(git -C "$review" rev-parse 'HEAD^{tree}')" = "$expected_tree" || fail "tree mismatch"
test ! -e "$review/parent.txt" || fail "recovery used moving parent HEAD"
test -x "$review/mode.sh" || fail "mode lost"
test -L "$review/link" || fail "symlink lost"
test ! -e "$review/remove.txt" || fail "deletion lost"

# Deferred candidate review can find a fix after the original was assembled.
export reviewed_sha candidate_path="$candidate"
run_recipe "$RECIPE_DIR/block3.sh" || fail "initial candidate assembly failed"
prior_candidate="$candidate"
prior_candidate_sha=$(git -C "$candidate" rev-parse HEAD)
prior_candidate_tree=$(git -C "$candidate" rev-parse 'HEAD^{tree}')

# A fix is transported as a full replacement from the original base. Preserve
# the old materialized review and compare endpoints, not their merge-base:
# otherwise settled binary/mode/deletion changes reappear in the re-review.
prior_reviewed_sha=$reviewed_sha
fix_worker="$TMP/fix-worker"
export worker_path="$fix_worker" worker_branch="orchestrator/$run/fix/$lane"
run_recipe "$RECIPE_DIR/herdr-dispatch.sh" || fail "replacement worker allocation failed"
unset worker_branch
test "$(git -C "$REPO" rev-parse "orchestrator/$run/worker/$lane")" = "$worker_sha" || fail "replacement changed retained worker branch"
git -C "$fix_worker" apply --index --whitespace=nowarn "$patch"
test "$(git -C "$fix_worker" write-tree)" = "$expected_tree" || fail "fix replay changed prior tree"
printf 'fix\n' >>"$fix_worker/keep.txt"
git -C "$fix_worker" add keep.txt
git -C "$fix_worker" commit -qm fix
expected_tree=$(git -C "$fix_worker" rev-parse 'HEAD^{tree}')
patch="$TMP/replacement.patch"
run_recipe "$RECIPE_DIR/manifest-and-briefs.sh" "$fix_worker" || fail "replacement capture failed"
patch_digest=$(git -C "$REPO" hash-object --no-filters "$patch")
git -C "$REPO" worktree remove "$fix_worker"
git -C "$REPO" branch -D "orchestrator/$run/fix/$lane" >/dev/null
review_path="$TMP/replacement-review"
review_branch="orchestrator/$run/replacement/$lane"
run_recipe "$RECIPE_DIR/block2.sh" || fail "replacement reconstruction failed"
reviewed_sha=$(git -C "$review_path" rev-parse HEAD)
test "$(git -C "$REPO" diff --name-only "$prior_reviewed_sha" "$reviewed_sha")" = keep.txt || fail "recheck included settled changes"
test "$(git -C "$review" rev-parse HEAD)" = "$prior_reviewed_sha" || fail "prior review was discarded"
test "$(git -C "$review_path" rev-parse 'HEAD^{tree}')" = "$expected_tree" || fail "replacement tree mismatch"

# Replace the full lane in a new candidate, not on top of the superseded lane.
candidate="$TMP/replacement-candidate"
export reviewed_sha candidate_path="$candidate" candidate_branch="orchestrator/$run/replacement-candidate"
run_recipe "$RECIPE_DIR/block3.sh" || fail "replacement candidate assembly failed"
test "$(git -C "$candidate" rev-parse 'HEAD^{tree}')" = "$expected_tree" || fail "candidate tree mismatch"
git -C "$REPO" worktree list --porcelain | grep -Fx "branch refs/heads/$candidate_branch" >/dev/null || fail "candidate is not registered"
test "$(git -C "$prior_candidate" rev-parse HEAD)" = "$prior_candidate_sha" || fail "prior candidate head lost"
test "$(git -C "$prior_candidate" rev-parse 'HEAD^{tree}')" = "$prior_candidate_tree" || fail "prior candidate tree lost"

# A second independent lane must extend the existing candidate, not recreate it
# or discard the first lane's binary/mode/deletion changes.
first_candidate_sha=$(git -C "$candidate" rev-parse HEAD)
lane=ui
run_recipe "$RECIPE_DIR/block1.sh" || fail "second lane base pin failed"
base_ref="refs/heads/orchestrator/$run/base/$lane"
second_worker="$TMP/second-worker"
git -C "$REPO" worktree add -q -b "orchestrator/$run/worker/$lane" "$second_worker" "$base_ref"
printf 'second lane\n' >"$second_worker/second.txt"
git -C "$second_worker" add second.txt
git -C "$second_worker" commit -qm second
expected_tree=$(git -C "$second_worker" rev-parse 'HEAD^{tree}')
patch="$TMP/second.patch"
run_recipe "$RECIPE_DIR/manifest-and-briefs.sh" "$second_worker" || fail "second lane capture failed"
patch_digest=$(git -C "$REPO" hash-object --no-filters "$patch")
review_path="$TMP/second-review"
review_branch="orchestrator/$run/review/$lane"
run_recipe "$RECIPE_DIR/block2.sh" || fail "second lane reconstruction failed"
reviewed_sha=$(git -C "$review_path" rev-parse HEAD)
git -C "$REPO" config status.showUntrackedFiles no
printf 'uncommitted candidate work\n' >"$candidate/untracked.txt"
if run_recipe "$RECIPE_DIR/block3.sh"; then fail "assembled on hidden untracked candidate work"; fi
test "$(git -C "$candidate" rev-parse HEAD)" = "$first_candidate_sha" || fail "dirty candidate advanced"
test -f "$candidate/untracked.txt" || fail "dirty candidate work lost"
rm "$candidate/untracked.txt"
git -C "$REPO" config --unset status.showUntrackedFiles
run_recipe "$RECIPE_DIR/block3.sh" || fail "second lane candidate assembly failed"
git -C "$candidate" merge-base --is-ancestor "$first_candidate_sha" HEAD || fail "first candidate history lost"
cmp "$candidate/keep.txt" "$TMP/replacement-review/keep.txt" || fail "first lane content lost"
cmp "$candidate/data.bin" "$TMP/replacement-review/data.bin" || fail "first lane binary lost"
test -x "$candidate/mode.sh" || fail "first lane mode lost"
test ! -e "$candidate/remove.txt" || fail "first lane deletion lost"
cmp "$candidate/second.txt" "$second_worker/second.txt" || fail "second lane content missing"

printf 'orchestrator handoff test passed\n'
