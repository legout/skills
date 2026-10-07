# Pi implementation dispatch

Default worker backend (`pi-subagents`). `herdr-pane` and `paseo` lanes reuse this file's lane-ownership rules and durable lifecycle recipe; their dispatch references substitute only the allocation, delivery, signaling, and cleanup mechanics.

- [Lane ownership](#lane-ownership)
- [Native Pi dispatch recipe](#native-pi-dispatch-recipe)
- [Reviewer dispatch contract](#reviewer-dispatch-contract)
- [Durable lifecycle recipe](#durable-lifecycle-recipe)

## Lane ownership

- Mutation requires separate isolated worktrees allocated by the selected backend.
- One writer owns each worktree and source seam.
- Dependent tasks wait for upstream handoffs.
- Read-only children may share a checkout only when they cannot change project state.
- Each worker makes focused commits.
- The orchestrator assembles only reconstructed lane commits whose required lane gates passed; deferred review runs on the candidate before acceptance. A worker report alone is never the assembled tree.
- A conflict pauses candidate assembly; it never starts another writer against uncertain ownership.
- Before mutation, create a collision-checked named base ref and record its resolved SHA. Use that supported named ref for managed allocation; do not use a raw SHA or moving parent `HEAD` as a recovery base.
- A lane handoff must include the full binary-capable patch path and digest, worker commit/tree/cleanliness, and runtime cleanup status. A missing or dirty handoff is blocked, not an accepted empty lane.

The runtime boundary was rechecked against `pi-subagents` 0.66.0. Managed workers accept supported named `baseRef` values, and normal completion may remove the worker worktree/branch. The orchestrator therefore treats the captured handoff patch and pinned base ref as durable recovery inputs. It does not depend on an undocumented retention option and does not alter the Pi runtime.

Record a lane board before parallel mutation:

```text
Lane | repo/cwd | task decision | claimed files/contract | worktree | authority | next gate | handoff
```

## Native Pi dispatch recipe

Read the installed `pi-subagents` skill and current tool guide first. For the native portion of a coordinated wave, write one fenced `js workflow` block and call `subagent({ workflow: true, async: true })` in the same reply, or use `workflow: "./path/to/script.js"`. Keep Herdr/Paseo dispatch outside the native workflow; they are not `runs.run` children.

### Root and model preflight

Resolve the physical Git top-level path and derive `<repo-parent>/worktrees/<repo-basename>/`. Use unique worker/fix, review, and candidate branch/path leaves, including run/lane/role/attempt where the selected allocator supports naming. Record the exact mapping; never relocate an allocator-managed path to impose a naming scheme. Validate every existing path component, reject symlinks and unsafe locations, and check each proposed leaf and branch are unused before allocation. Create only the expected root after validation. Do not relocate old worktrees.

Keep the configured Pi-subagents allocator. Read its effective `worktreeProvider`, `worktreeBaseDir`, and `PI_SUBAGENTS_WORKTREE_DIR` before dispatch. A configured base directory/environment variable selects native allocation and cannot be combined with explicit `worktrunk`; never set it just to force a provider change. With native allocation and no configured base, the dedicated root is the repository parent's `worktrees/` directory and the leaf adds the repository basename, which yields the required shared root. If a configured native base exists, require its resulting `<base>/<repo-basename>` to be the expected root. Repositories inside Pi extension auto-discovery may be relocated by the runtime and must block if the resulting path is not the expected root.

If the resolved provider is Worktrunk, inspect its effective path template with `wt config show` in the repository and account for `WORKTRUNK_WORKTREE_PATH`. Require every branch-derived path to resolve beneath the expected root; a suitable template is `{{ repo_path }}/../worktrees/{{ repo }}/{{ branch | sanitize }}` (see [Worktrunk config](https://worktrunk.dev/config/)). Do not edit user/project Worktrunk config or set a temporary path to switch allocators. `auto` may resolve according to pi-subagents' documented provider selection; record the resolved allocator. An unavailable explicitly selected Worktrunk provider or an unevaluable/off-root path blocks before `runs.run`.

For each worker or reviewer, resolve model and thinking fields independently (run/lane → project → global → spec default). Call `subagent({ action: "models" })` to confirm the exact `provider/model` ID, then pass the complete role pair in the documented per-run form `model: "provider/model:thinking-level"` (`:off` is also explicit). Do not use an agent name as a model ID, strip an existing thinking suffix, or infer a provider alias. If a suffix conflicts with the selected thinking field, or the backend cannot run the exact ID/level, block. The worker's first instruction is a no-write preflight: verify its actual cwd is the expected registered path and report the runtime-effective model/thinking before touching files; a mismatch returns blocked without mutation. Verify the returned runtime path and model evidence in the parent before accepting the lane.

- Use `runs.run` for dependent stages.
- Use `runs.all` for independent read-only work.
- Use `runs.lanes` for predeclared serial stages across independent lanes.
- Use stable keys, short behavior labels on workflow children/stages, and distinct runtime-bound `output` paths.
- Set fresh context for scouts, workers, reviewers, and validators.
- Set `worktree: true` and the pinned named `baseRef` on mutation-capable children; pass the exact worker/reviewer `model: "provider/model:thinking-level"` value on each launch.
- Give `new-test` workers the embedded public-seam, independence-first test contract (failing-first only for bug repros and refactor pinning); require evidence matching the assigned test obligation in each report.
- Do not set hard tool budgets on mutation-capable workers.
- Return output references, commit IDs, and handoffs instead of copying full reports into later prompts.

A worker launch names the brief path, repo/cwd/ref, authority, claimed seam, validation, commit requirement, output, and escalation rules. Include the worker guardrails from the brief reference directly in its task. A reviewer launch names the same brief, worker report, and exact diff package **and pastes the entire contract below into the task every time**, including rechecks and candidate reviews. Fresh reviewers may never load project instruction files; links alone are not delivery.

## Reviewer dispatch contract

Fill the placeholders from the approved task and actual source inspection. Name applicable instruction/style/lint/config rules, or state that no written conventions were found; never substitute taste. Include real callers, input provenance, and runtime/deployment assumptions. Missing security-critical facts remain unverified and go to the parent.

<!-- reviewer-contract:start -->
```text
Review <base>..<head> against <approved criteria and non-goals>.
Written conventions: <named sources and relevant rules, or none found>.
Real use: <callers, input provenance, environment, touched boundaries>.
Priority: agreed feature, then correctness, then proven risk. Project written conventions are binding; violations are must-fix. Unwritten taste never blocks.
Report only a violation of a named requirement or written rule that this change caused or worsened, reachable through real callers, inputs, and environment, with material impact and a proportionate response. Cite the rule, changed location, scenario, impact, and response.
Security activates only for touched boundaries: untrusted or external input (files, queries, network), credentials, auth, dependency changes. Require a named asset, realistic attacker, and an attack path through real use. Stories requiring stolen secrets, broken TLS, malicious admins, or generic extra hardening are not findings. No boundary touched: write "security: n/a". Security facts missing: mark the criterion unverified; never invent a threat model. Trusted internal callers and user-owned local files are not hostile by default; written safety guarantees still bind.
Test requests are findings too: name a reachable real scenario or drop them. Coverage percentage is not a reason.
Large or out-of-scope fixes: one line with the owner decision needed, not an automatic fix-first item. Unrelated issues: one line max, non-blocking. Do not fix, dispatch workers, or start re-reviews; the parent dispositions findings before repair.
Finish when agreed criteria, real risks, and written rules are covered; zero findings is success. Verdict: pass or fix-first (small in-scope repairs), with any unverified criterion or required human decision explicitly stated. A pass does not clear those decisions or authorize acceptance/publication. Then stop.
```
<!-- reviewer-contract:end -->

For the one allowed recheck, replace the opening scope with: `Re-review only <priorReviewSha>..<replacementReviewSha>, the accepted findings <list>, and the behavior those fixes address. Do not re-review the rest of the change. Report any surviving blocker, then stop for the human; no third round.` Paste the full contract as well. A reconstructed sibling commit is compared directly with `git diff <priorReviewSha> <replacementReviewSha>` (two endpoints, not merge-base/triple-dot).

For candidate review after lane reviews, supply the exact candidate base/head and prior review evidence; scope attention to previously unreviewed changes and integration effects. Verify tree/diff correspondence before reusing evidence; never copy a verdict across branches blindly or reopen settled findings just to fill another review. Missing correspondence is an unverified gate for the parent, not permission to reset the correction budget.

## Durable lifecycle recipe

Each block below is a runnable command example with inputs supplied as environment variables (`run`, `lane`, `base_sha`, and the artifact paths/digests). Every block defines its own `stop` refusal and runs `set -euo pipefail`. Pin/digest failures abort before allocating review resources; applicability or staged-tree failures abort before the reconstruction commit and preserve the review checkout for inspection.

**Pin the named base before allocation.** `base_sha` is the approved lane base: the checked-out base for a first wave, or a reviewed upstream candidate base for a dependent lane. It is never the moving parent `HEAD`, and creation never overwrites an existing pin.

```bash
stop() { printf 'lifecycle refusal: %s\n' "$*" >&2; exit 1; }
set -euo pipefail
: "${run:?run id}" "${lane:?lane id}" "${base_sha:?approved lane base}"
base_ref="refs/heads/orchestrator/$run/base/$lane"
if git show-ref --verify --quiet "$base_ref"; then
    # Collision-checked reuse: the existing pin must still resolve to the recorded base.
    test "$(git rev-parse "$base_ref")" = "$base_sha" || stop "base pin moved; preserve artifacts for an owner decision"
else
    # Create-only: the empty old-value argument refuses to overwrite an existing pin.
    git update-ref "$base_ref" "$base_sha" "" || stop "base pin creation lost the collision check"
fi
# allocate the managed worker from the named ref; capture a complete binary-capable patch,
# its digest, and the worker-reported clean tree before allowing child finalization
```

**Replay and reconstruct after cleanup.** Verify the pin and the patch digest before creating anything; never fall back to the parent's current `HEAD`. Replay without whitespace rewriting (also for a fresh fix worker). Verify the staged tree before committing, then the committed tree and checkout cleanliness: hooks can change either after the first check. Unexpected changes block acceptance and preserve the checkout; do not bypass required hooks or checks to force a result.

```bash
stop() { printf 'lifecycle refusal: %s\n' "$*" >&2; exit 1; }
set -euo pipefail
: "${run:?run id}" "${lane:?lane id}" "${base_sha:?recorded base sha}" "${expected_root:?canonical shared root}"
: "${patch:?handoff patch path}" "${patch_digest:?patch digest}" "${expected_tree:?expected clean worker tree}"
: "${review_path:?registered review worktree path}"
case "$review_path" in "$expected_root"/*) ;; *) stop "review path is outside the shared root" ;; esac
base_ref="refs/heads/orchestrator/$run/base/$lane"
review_branch=${review_branch:-"orchestrator/$run/review/$lane"}
git rev-parse --verify --quiet "$base_ref^{commit}" >/dev/null || stop "base pin is missing"
test "$(git rev-parse "$base_ref")" = "$base_sha" || stop "base pin moved; preserve artifacts for an owner decision"
test "$(git hash-object --no-filters "$patch")" = "$patch_digest" || stop "handoff patch digest mismatch"
git worktree add -b "$review_branch" "$review_path" "$base_ref" || stop "review worktree creation failed"
git -C "$review_path" apply --check --whitespace=nowarn "$patch" || stop "handoff patch does not apply cleanly to the pinned base"
git -C "$review_path" apply --index --whitespace=nowarn "$patch" || stop "handoff patch could not be staged"
# worker reports are supporting evidence; verify both sides of the commit boundary
test "$(git -C "$review_path" write-tree)" = "$expected_tree" || stop "staged tree differs from the expected worker tree"
git -C "$review_path" commit -qm "reconstruct $lane for review" || stop "reconstruction commit failed"
test "$(git -C "$review_path" rev-parse 'HEAD^{tree}')" = "$expected_tree" || stop "committed tree differs from the expected worker tree"
status=$(git -C "$review_path" status --porcelain --untracked-files=all --ignore-submodules=none) || stop "review status check failed"
test -z "$status" || stop "review checkout is dirty"
# initial review: "$base_sha"..HEAD; fix recheck: priorReviewSha..replacementReviewSha
# advance lastReviewedSha on this reconstruction only after the required review/recheck
```

**Assemble reconstructed commits after required lane gates.** Run only when candidate assembly is authorized by the mode/owner. Create the candidate once, then rerun for subsequent independent or dependent lanes in the planned order. It consumes reconstructed commits, never a live worker SHA; apply deferred candidate review before acceptance. If an assembled lane is replaced, preserve the prior candidate and supply a distinct `candidate_branch` and new `candidate_path`; rebuild from the approved base with the current accepted reconstruction of every lane in order. Never append the full replacement to its superseded lane. Changed dependency bases require reconciliation, not bypassing the ancestry check; rebuilding does not reset review state or the correction budget.

```bash
stop() { printf 'lifecycle refusal: %s\n' "$*" >&2; exit 1; }
set -euo pipefail
: "${run:?run id}" "${lane:?lane id}" "${base_sha:?recorded base sha}" "${expected_root:?canonical shared root}"
: "${reviewed_sha:?reconstructed reviewed commit}" "${candidate_path:?registered candidate worktree path}"
case "$candidate_path" in "$expected_root"/*) ;; *) stop "candidate path is outside the shared root" ;; esac
base_ref="refs/heads/orchestrator/$run/base/$lane"
test "$(git rev-parse "$base_ref")" = "$base_sha" || stop "base pin moved before candidate assembly"
candidate_branch=${candidate_branch:-"orchestrator/$run/candidate"}
if [ ! -e "$candidate_path" ]; then
    git worktree add -b "$candidate_branch" "$candidate_path" "$base_ref" || stop "candidate worktree creation failed"
fi
candidate_path=$(cd "$candidate_path" && pwd -P) || stop "candidate path is not a directory"
git worktree list --porcelain | grep -Fx -- "worktree $candidate_path" >/dev/null || stop "candidate is not registered in this repository"
test "$(git -C "$candidate_path" symbolic-ref --quiet HEAD)" = "refs/heads/$candidate_branch" || stop "candidate branch mismatch"
status=$(git -C "$candidate_path" status --porcelain --untracked-files=all --ignore-submodules=none) || stop "candidate status check failed"
test -z "$status" || stop "candidate checkout is dirty"
git -C "$candidate_path" merge-base --is-ancestor "$base_sha" HEAD || stop "candidate does not contain the lane base"
git -C "$candidate_path" cherry-pick "$reviewed_sha" >/dev/null || stop "candidate assembly failed"
# apply the selected candidate policy to base..head, reusing verified prior evidence
# for settled code and reviewing integration effects; then hand merge-worktree the
# candidate path, branch, base/head, checks, review evidence, and authorization state
```

The examples are intentionally recipes, not calls to a retention API. Use a binary-capable patch format, verify the digest before applying it, and preserve artifacts and owned refs when any check fails. A fix worker's replacement patch supersedes the prior full lane patch: preserve the prior materialized review ref/SHA, then replay from the same pinned base with a distinct `review_branch`. Verify the full reconstructed tree, but review only `priorReviewSha..replacementReviewSha` and affected behavior. Advance `lastReviewedSha` to the replacement only after that recheck passes; reconstruction never resets the one-fix/one-recheck budget.
