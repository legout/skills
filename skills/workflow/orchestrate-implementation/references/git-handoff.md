# Git handoff

- [Pin the lane base](#pin-the-lane-base)
- [Freeze a committed result](#freeze-a-committed-result)
- [Verify the result](#verify-the-result)
- [Assemble the candidate](#assemble-the-candidate)

Use these recipes for the ordinary committed-result path on every mutation-capable Pi host. The parent supplies collision-checked names, canonical paths, and recorded identities. Run in the intended repository/worker checkout; output paths belong outside disposable worktrees. A result is transport and provenance, not a review verdict.

## Pin the lane base

The first lane uses the approved run base. A dependent lane uses the accepted upstream **candidate commit**, not a sibling source commit whose hash changed during cherry-picking. Verify readiness and ownership before allocation. Managed native Pi requires a supported named `baseRef`, so keep this pin until all consumers finish.

```bash
set -euo pipefail
stop() { printf 'handoff refusal: %s\n' "$*" >&2; exit 1; }
: "${run:?run id}" "${lane:?lane id}" "${base_sha:?approved lane base}"
base_ref="refs/heads/orchestrator/$run/base/$lane"
git check-ref-format "$base_ref" || stop "invalid base ref"
test "$(git rev-parse "$base_sha^{commit}")" = "$base_sha" || stop "base is not an exact commit"
if git show-ref --verify --quiet "$base_ref"; then
    test "$(git rev-parse "$base_ref")" = "$base_sha" || stop "base pin moved"
else
    git update-ref "$base_ref" "$base_sha" "" || stop "base pin collision"
fi
```

## Freeze a committed result

Commit intended changes and run assigned validation first. Before finalization, the worker creates only the parent-authorized `result_ref`, such as `refs/heads/orchestrator/<run>/result/<lane>/<attempt>`. This protects the actual commits even when native cleanup removes its worker branch and checkout. Never reuse or move that result ref for a fix: use a distinct attempt ref. The worker may update this one approved ref in the shared Git database, not other lanes' refs.

Run this block in the worker checkout **before finalization**. `repo_git_dir` is the parent's physical canonical common Git directory, recorded before launch (resolve `git rev-parse --path-format=absolute --git-common-dir` with `pwd -P`). Capture the emitted identities in the host-bound final report, then relinquish write ownership.

```bash
set -euo pipefail
stop() { printf 'handoff refusal: %s\n' "$*" >&2; exit 1; }
: "${base_ref:?pinned base}" "${base_sha:?recorded base sha}"
: "${result_ref:?unique approved result ref}" "${repo_git_dir:?canonical common Git directory}"
case "$result_ref" in refs/heads/orchestrator/*/result/*) ;; *) stop "result ref outside approved namespace" ;; esac
git check-ref-format "$result_ref" || stop "invalid result ref"
common_dir=$(git rev-parse --path-format=absolute --git-common-dir)
test "$(cd "$common_dir" && pwd -P)" = "$repo_git_dir" || stop "wrong repository"
test "$(git rev-parse "$base_ref^{commit}")" = "$base_sha" || stop "base pin missing or moved"
status=$(git status --porcelain --untracked-files=all --ignore-submodules=none) || stop "worker status failed"
test -z "$status" || stop "worker checkout is dirty"
result_sha=$(git rev-parse HEAD)
result_tree=$(git rev-parse 'HEAD^{tree}')
git merge-base --is-ancestor "$base_sha" "$result_sha" || stop "result does not descend from base"
test -z "$(git rev-list --merges "$base_sha..$result_sha")" || stop "lane contains merge commits; assembly needs an owner decision"
git update-ref "$result_ref" "$result_sha" "" || stop "result ref already exists"
printf 'result_ref=%s\nresult_sha=%s\nresult_tree=%s\n' "$result_ref" "$result_sha" "$result_tree"
```

## Verify the result

The parent verifies the actual object, ref, and diff, not just the report. This check works after worker checkout/branch removal and after parent HEAD movement. Record clean checkout evidence from the worker/host separately; a Git object cannot prove that an abandoned checkout had no uncommitted files. Missing cleanliness evidence or mismatched identities block acceptance. If the committed result is unavailable, use patch recovery rather than current parent HEAD.

```bash
set -euo pipefail
stop() { printf 'handoff refusal: %s\n' "$*" >&2; exit 1; }
: "${base_ref:?pinned base}" "${base_sha:?recorded base sha}"
: "${result_ref:?frozen result ref}" "${result_sha:?reported commit}" "${result_tree:?reported tree}"
test "$(git rev-parse "$base_ref^{commit}")" = "$base_sha" || stop "base pin missing or moved"
test "$(git rev-parse "$result_ref^{commit}")" = "$result_sha" || stop "result pin missing or moved"
test "$(git rev-parse "$result_sha^{tree}")" = "$result_tree" || stop "result tree mismatch"
git merge-base --is-ancestor "$base_sha" "$result_sha" || stop "result ancestry mismatch"
git diff --no-ext-diff --no-textconv --stat "$base_sha" "$result_sha"
```

Inspect `base_sha..result_sha`, run/reuse verified checks on that exact tree, and apply required review before acceptance. To check an available released worker checkout, verify its registered repository/branch, clean status with the explicit flags above, and HEAD equal to `result_sha`. Otherwise create a registered read-only review checkout at the result ref; no patch replay or synthetic commit is needed.

For a fix, retain the prior result/ref and review evidence. Resume the writer only if its runtime, cwd, and sole ownership are verified. Otherwise allocate a fresh writer from the prior frozen result ref. It makes a descendant fix commit and freezes a new attempt ref. Recheck the direct `priorResultSha..fixedResultSha` delta, not the whole original task.

## Assemble the candidate

The parent owns a separate registered candidate branch/path and records its original run base. Both execution modes allow this isolated preparation unless the user forbids it. Initial assembly consumes the lane's `base_sha..result_sha`; a descendant fix consumes only `priorResultSha..fixedResultSha` after confirming the prior result is already represented in this candidate. Set `assembly_from` accordingly and record that correspondence before running the recipe. Deferred independent review follows assembly, before acceptance or target integration.

Run in the source repository. Supply a new `candidate_path`/`candidate_branch` for the first assembly; an existing path must be the recorded candidate in this repository. Verify the result with the recipe above first. No merges are inferred or resolved automatically.

```bash
set -euo pipefail
stop() { printf 'assembly refusal: %s\n' "$*" >&2; exit 1; }
: "${base_ref:?pinned base}" "${base_sha:?recorded lane base}"
: "${result_sha:?verified lane result}" "${assembly_from:?base or prior represented result}"
: "${candidate_path:?candidate path}" "${candidate_branch:?candidate branch}"
test "$(git rev-parse "$base_ref^{commit}")" = "$base_sha" || stop "base pin moved"
git merge-base --is-ancestor "$base_sha" "$assembly_from" || stop "assembly boundary precedes lane base"
git merge-base --is-ancestor "$assembly_from" "$result_sha" || stop "replacement is not a descendant; rebuild candidate"
test -z "$(git rev-list --merges "$assembly_from..$result_sha")" || stop "merge commits need an owner decision"
if [ ! -e "$candidate_path" ]; then
    git worktree add -b "$candidate_branch" "$candidate_path" "$base_ref" || stop "candidate creation failed"
fi
candidate_path=$(cd "$candidate_path" && pwd -P)
git worktree list --porcelain | grep -Fx -- "worktree $candidate_path" >/dev/null || stop "candidate is not registered in this repository"
test "$(git -C "$candidate_path" symbolic-ref --quiet HEAD)" = "refs/heads/$candidate_branch" || stop "candidate branch mismatch"
status=$(git -C "$candidate_path" status --porcelain --untracked-files=all --ignore-submodules=none) || stop "candidate status failed"
test -z "$status" || stop "candidate checkout is dirty"
git -C "$candidate_path" merge-base --is-ancestor "$base_sha" HEAD || stop "candidate lacks the lane base"
commits=$(git rev-list --reverse "$assembly_from..$result_sha")
if [ -n "$commits" ]; then
    git -C "$candidate_path" cherry-pick $commits || stop "assembly conflict; preserve candidate"
fi
status=$(git -C "$candidate_path" status --porcelain --untracked-files=all --ignore-submodules=none) || stop "candidate status failed"
test -z "$status" || stop "candidate hook left a dirty checkout"
```

Inspect the assembled diff/tree correspondence and focused evidence after cherry-picking: hooks and combined changes can invalidate prior evidence. Never copy a verdict to an altered tree blindly. Record the candidate base/head, source-result mapping, checks, review, and authority in the `merge-worktree` handoff.

A patch-reconstructed full replacement may be a sibling, not a descendant fix. Preserve the old candidate and rebuild from the original run base using current lane results in dependency order; do not append a full replacement to the superseded result. If downstream lanes were based on replaced code, reconcile their prerequisites before reuse. Rebuilding does not reset the review budget.
