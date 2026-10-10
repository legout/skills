# Review and recovery

Every newly allocated parent review/reconstruction and candidate checkout uses the shared XDG state root resolved under `SKILL.md`, just like worker/fix worktrees. Use distinct source-checkout/run/lane/role paths and verify the expected repository/common Git directory; never adopt another checkout's resources merely because they share the root. Apply `SKILL.md`'s physical-path/symlink/collision preflight before allocation. If the path cannot be registered there, preserve artifacts and block. Never relocate an existing checkout or retry off-root.

## Disposition before repair

The parent inspects each finding at the exact reviewed head. Require a named requirement/written-rule violation, a change-caused or worsened defect, real reachability, material impact, and a proportionate response. Written conventions bind; taste does not. Security/test demands also pass the inline reviewer contract in the brief reference.

- **Reject** failed gates in one line with evidence.
- **Fix** small in-scope defects in one authorized batch to the lane's sole writer.
- **Hand back** large/out-of-scope repairs with the human decision needed; do not quietly accept a material defect.
- **Ask** about unverified material criteria, including missing facts at a genuinely touched security boundary.

One fix pass, one delta recheck. No third round, no renewed budget at candidate assembly, and no loop for optional polish. Recheck only the fix and affected behavior; surviving or new material blockers require a human decision. Parent inspection applies to all results; independent review happens before high-risk/contract consumption or once on the candidate. Candidate review covers unreviewed changes and integration effects, not settled findings again. Explicit project/user review requirements still bind.

## Ordinary fixes and interruptions

Prefer a descendant fix commit on the prior frozen committed result. Resume a writer only after verifying its identity, runtime resumability, checkout, and exclusive ownership; otherwise stop/resolve the old writer and start a fresh one from the frozen result ref. Retain the original result and review evidence. Only parent-accepted findings belong in its brief; apply the same verification and delta review to the new attempt.

Attention, timeout, or idle state is not failure or ownership release. Interrupt/cancel through the host when needed, preserve available work and partial logs, then confirm no writer remains active before retrying. Do not require a finished handoff before stopping a runaway writer. Cancellation does not authorize worktree removal, artifact deletion, pane closure, or a substitute runtime.

Infrastructure failures remain blockers. Inspect the focused error and actual cwd/ref state; verify cleanliness or capture partial work before a same-protocol retry. Never use a foreground/CLI/other-host fallback without owner approval.

## Patch-only recovery

Read this section only when a committed result is unavailable or a host transfers patches instead of shared Git objects. Keep the original pinned base, unique external patch, digest, expected clean worker tree, cleanliness evidence, and cleanup state. Patch artifacts must survive worker finalization. A missing/partial/dirty handoff blocks acceptance. A digest proves artifact identity, not semantic correctness or reviewer acceptance.

### Capture the patch

Run after committing all intended work. The parent supplies a unique external `patch` path and the pinned base. A fix produces a new full replacement from the original pinned base and never overwrites prior artifacts.

```bash
set -euo pipefail
set -o noclobber
stop() { printf 'handoff refusal: %s\n' "$*" >&2; exit 1; }
: "${base_ref:?pinned ref}" "${base_sha:?recorded base sha}" "${patch:?external handoff path}"
test "$(git rev-parse "$base_ref^{commit}")" = "$base_sha" || stop "base pin missing or moved"
status=$(git status --porcelain --untracked-files=all --ignore-submodules=none) || stop "worker status check failed"
test -z "$status" || stop "worker checkout is dirty"
worker_sha=$(git rev-parse HEAD)
expected_tree=$(git rev-parse 'HEAD^{tree}')
git diff --no-ext-diff --no-textconv --binary --full-index --unified=3 --submodule=short --no-color --no-relative --ignore-submodules=none --src-prefix=a/ --dst-prefix=b/ "$base_sha" "$worker_sha" >"$patch"
patch_digest=$(git hash-object --no-filters "$patch")
printf 'worker_sha=%s\nexpected_tree=%s\npatch_digest=%s\n' "$worker_sha" "$expected_tree" "$patch_digest"
```

A runtime patch may be reused only when its completeness, recorded identities, and cleanup behavior satisfy this contract. Do not call a worker-authored patch a runtime-generated artifact. An empty patch is not proof that the task was implemented; establish any legitimate no-op against the criteria instead of forcing an empty reconstruction.

### Reconstruct and verify

Run in the parent repository, in a new registered review worktree outside the active checkout/extension auto-discovery. Pin/digest failures occur before allocation; replay/staged-tree failures occur before commit and preserve diagnostic work. Do not bypass hooks, rewrite whitespace, or fall back to parent HEAD.

```bash
set -euo pipefail
stop() { printf 'recovery refusal: %s\n' "$*" >&2; exit 1; }
: "${run:?run id}" "${lane:?lane id}" "${base_sha:?recorded base sha}"
: "${patch:?patch path}" "${patch_digest:?patch digest}" "${expected_tree:?expected clean worker tree}"
: "${review_path:?new review worktree path}" "${expected_root:?canonical shared root}"
case "$review_path" in "$expected_root"/*) ;; *) stop "review path is outside the shared root" ;; esac
base_ref="refs/heads/orchestrator/$run/base/$lane"
review_branch=${review_branch:-"orchestrator/$run/review/$lane"}
test "$(git rev-parse "$base_ref^{commit}")" = "$base_sha" || stop "base pin missing or moved"
test "$(git hash-object --no-filters "$patch")" = "$patch_digest" || stop "patch digest mismatch"
git worktree add -b "$review_branch" "$review_path" "$base_ref" || stop "review worktree creation failed"
git -C "$review_path" apply --check --whitespace=nowarn "$patch" || stop "patch does not apply cleanly"
git -C "$review_path" apply --index --whitespace=nowarn "$patch" || stop "patch could not be staged"
test "$(git -C "$review_path" write-tree)" = "$expected_tree" || stop "staged tree differs from the expected worker tree"
git -C "$review_path" commit -qm "reconstruct $lane for review" || stop "reconstruction commit failed"
test "$(git -C "$review_path" rev-parse 'HEAD^{tree}')" = "$expected_tree" || stop "committed tree differs from the expected worker tree"
status=$(git -C "$review_path" status --porcelain --untracked-files=all --ignore-submodules=none) || stop "review status check failed"
test -z "$status" || stop "review checkout is dirty"
```

Inspect the reconstructed diff and run/reuse actual checks on that exact tree/environment, not a worker's pass claim. Record worker provenance separately from the materialized review ref/SHA/tree. A clean initial review covers the pinned base to reconstructed head. For a full replacement preserve the prior materialized endpoint and use `git diff <priorReviewSha> <replacementReviewSha>`: the recheck range is `priorReviewSha..replacementReviewSha`, not merge-base/triple-dot or the full original task. Missing prior review evidence requires an owner decision, not a review restart.

A full replacement is not an incremental fix. Rebuild an already assembled candidate from the original run base with current lane results, rather than appending the replacement. Reconcile downstream prerequisites affected by changed upstream code. Preserve the prior candidate/ref and the one-fix budget.

## Acceptance and cleanup

Before parent acceptance verify the final intended diff, criteria, focused/project checks, required fresh review, fixed accepted findings, exact source/candidate correspondence, and every child's terminal or blocked state. Restate the task, compare the result, and choose `accept / fix / hand back / ask`. A `pass` with an unverified material criterion or owner decision is not acceptance.

Before parent-requested cleanup, verify retained refs or patch recovery, recheck the live checkout's reported HEAD and explicit clean status, confirm no writer/consumer needs it, and obtain applicable cleanup authority. Preserve failed/uncertain resources. Automatic native finalization may happen earlier; record its actual outcome and require the retained result ref or documented complete patch handoff. Cleanup is never a prerequisite for acceptance, and review evidence never grants integration/publication authority.
