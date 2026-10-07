# Managed lifecycle acceptance fixture (executable, live run PENDING)

This is a bounded **executable** native Pi acceptance fixture for `orchestrate-implementation`. Unlike the offline suite (`tests/orchestrator_handoff_test.sh`, which replays the documented recipe against a synthetic Git fixture), this fixture must be run live through the native Pi runtime. **Status: PENDING — it has not been executed yet.** A green offline suite is not evidence for this fixture; do not claim it passed without the evidence fields below.

## Hard boundaries

- All Git mutations must belong to the **disposable Git repository** created for this run (see setup). Never use, mutate, or publish from an unrelated project checkout.
- Use the `orchestrate-implementation` skill and native Pi subagent tooling (`pi-subagents`); discovering agents/capabilities first is part of the run.
- Execute this fixture in **autonomous** mode: authorization to run this disposable evaluation includes assembly of accepted reconstructed commits in its candidate checkout, but no target integration, push, PR, deploy, release, or publication. If the owner instead selects supervised mode, pause before assembly and report **AWAITING APPROVAL**, not PASS or an infrastructure failure.
- **Fail closed:** if any native prerequisite is unavailable (runtime not installed, no configured model credentials, no disposable-repo execution permission, protocol mismatch), report the run as **BLOCKED** with the exact error and stop. Never switch to a CLI/foreground fallback mode to force a result, and never report a blocked run as success.
- Do not import private runtime modules or invent runtime APIs; only documented native request shapes.

## Disposable setup

```bash
set -euo pipefail
run_root=$(mktemp -d "${TMPDIR:-/tmp}/managed-lifecycle.XXXXXX")
run_root=$(cd "$run_root" && pwd -P)
mkdir -p "$run_root/repo"
git -C "$run_root/repo" init -q
git -C "$run_root/repo" config user.name "managed lifecycle fixture"
git -C "$run_root/repo" config user.email "managed-lifecycle-fixture@example.invalid"
printf 'seed\n' > "$run_root/repo/seed.txt"
git -C "$run_root/repo" add seed.txt && git -C "$run_root/repo" commit -qm "fixture base"
```

The canonical repository root is `$run_root/repo`; the required shared worktree root is `$run_root/worktrees/repo/`. Put the native managed worker/fix worktrees and parent-created review/candidate checkouts beneath that root. Verify the configured Pi allocator predicts this root before dispatch; do not set `worktreeBaseDir` to switch an explicitly selected Worktrunk provider. If the selected allocator cannot honor the root, mark the fixture BLOCKED before launching a writer. Handoff/report artifacts must remain outside every disposable worker worktree; record their exact paths and ownership rather than copying a report in place of the captured patch. Verify every mutation checkout's canonical path, registration beneath the shared root, and `git rev-parse --git-common-dir` ownership by `$run_root/repo/.git` before mutation. Only this fixture's recorded resources may be cleaned up; preserve failed or uncertain artifacts.

## Scenario

This fixture uses one explicit controlled fault so the repair path is exercised without inventing a review finding: the first worker adds executable `render.sh` that prints `ready ` followed by a newline, plus `test_render.sh` that requires executable permission and exact stdout bytes `ready\n`. The test must fail on the known trailing-space defect, and the worker must report that failure honestly. The approved finding is only that `render.sh` violates the byte-exact output criterion; the fresh fix worker removes the space, reruns the test successfully, and replaces the full patch. Do not manufacture a finding if the reviewer misses this reachable failure; record fixture FAIL and stop.

The test oracle must compare bytes without trimming output; for example:

```bash
set -euo pipefail
actual=$(mktemp)
trap 'rm -f "$actual"' EXIT
test -x ./render.sh
./render.sh > "$actual"
printf 'ready\n' | cmp - "$actual"
```

1. **Discover:** list available agents/capabilities through the native protocol; record the runtime version and effective worktree allocator.
2. **Resolve:** capture the effective worker and reviewer model/thinking fields (run/lane → project → global → spec defaults), their sources, and exact `provider/model:thinking-level` launch forms. Verify both model IDs and thinking levels are supported before any writer starts; if not, exercise the blocked no-launch path.
3. **Pin:** create the collision-checked named base `refs/heads/orchestrator/<run>/base/api` at the approved lane base with the documented pin recipe; record the resolved SHA.
4. **Worker:** launch one small managed mutation worker with fresh context from the named `baseRef`, a bounded brief containing the exact worker pair and expected root, the controlled-fault requirement/test above, and a declared report output path. The worker's first action is a no-write check of its actual registered path and effective model/thinking; mismatch returns blocked without editing. Run `bash test_render.sh`, report its expected failure without claiming success, and let normal child finalization run — do not request retention of the worktree.
5. **Handoff:** consume the actual runtime handoff artifact: complete binary-capable patch path, digest, worker-reported commit/tree/cleanliness, and recorded cleanup state (worktree removed/preserved).
6. **Move parent:** commit an unrelated change on the parent branch so its HEAD advances past the pinned base.
7. **Reconstruct:** run the documented byte-preserving replay recipe in a registered parent-owned review worktree beneath the shared root: verify the pin/digest, verify the staged tree equals the reported clean worker tree, commit, then verify the committed tree and checkout cleanliness. Run `bash test_render.sh` there and record the expected trailing-space failure; do not replace that required live evidence with an offline or worker report.
8. **Review:** dispatch a fresh read-only reviewer using the exact reviewer model/thinking pair against the exact `base..reconstructed-head` range with the full inline reviewer contract and the byte-exact output criterion; record the verdict. It must identify the reachable trailing-space failure as `fix-first`. Preserve the materialized review ref/SHA.
9. **Fix:** launch a fresh managed fix worker from the same verified pinned base with the exact worker pair, replaying the full prior patch and removing only the accepted trailing-space defect; run `bash test_render.sh` successfully, capture its complete replacement patch and digest, and let finalization clean up.
10. **Replace:** reconstruct the replacement patch from the pinned base on a distinct review branch under the shared root; verify it is a full replacement (not incremental). Recheck only the direct `priorReviewSha..replacementReviewSha` delta and the accepted finding's behavior. One fix pass, one recheck; unresolved findings stop for the human, never reset the budget or re-review settled code.
11. **Candidate:** assemble the reconstructed reviewed commit in a registered candidate worktree beneath the shared root; record the handoff fields for `merge-worktree`; stop before integration.

## Required evidence fields

| Field | Meaning |
|---|---|
| `runtime_version` | Actual Pi/`pi-subagents` version used |
| `expected_root` | Canonical `<repo-parent>/worktrees/<repo-name>/` path and allocator preflight evidence |
| `worker_model`, `worker_thinking`, `worker_sources` | Exact worker pair and per-field resolution sources |
| `reviewer_model`, `reviewer_thinking`, `reviewer_sources` | Exact reviewer pair and per-field resolution sources |
| `backend_effective_pair` | Exact model/thinking observed in each launched role or the precise blocker |
| `agents_discovered` | Agent/capability discovery result |
| `run_id`, `lane_id` | Run and lane identifiers, terminal worker/fix/reviewer IDs, and native request shapes |
| `base_ref`, `base_sha` | Named base pin and resolved SHA (before/after checks) |
| `patch_path`, `patch_digest` | Complete handoff patch and digest; same for the replacement |
| `worker_report` | Worker-reported commit/tree/cleanliness |
| `finalization_state` | Runtime cleanup result: worktree/branch removed or preserved; exact managed paths and disposable-repository ownership checks |
| `parent_moved_sha` | Parent HEAD after movement |
| `review_ref`, `review_sha`, `review_tree` | Materialized reconstruction identities |
| `review_range`, `review_verdict` | Exact reviewed range and verdict |
| `replacement_digest`, `prior_review_sha`, `recheck_range` | Full replacement digest, preserved prior materialized review SHA, and exact delta recheck endpoints |
| `candidate_ref`, `candidate_path`, `candidate_base`, `candidate_head` | Registered candidate handoff |
| `handoff_fields` | Fields handed to `merge-worktree` |
| `cleanup_evidence` | What was cleaned up, what was preserved, and why |
| `blocker` | Exact infrastructure failure, or `none` |

## Verdict

Before PASS, exercise the refusal cases on separate fixture-owned review paths: a moved base or digest mismatch must abort before creating a review worktree/branch; a corrupt patch with its matching digest must abort at applicability checking without creating a reconstruction commit. A wrong expected tree must also refuse before commit, preserving the staged review checkout for inspection. Record exit statuses, refs, and preserved artifacts for each case.

PASS requires every evidence field populated from actual live execution, every refusal boundary above honored, and final validation plus fresh review on the exact candidate tree, checking integration effects and verifying correspondence to prior review evidence without reopening settled findings. Missing native prerequisites produce **BLOCKED** with the exact error; a failed required assertion produces **FAIL**. A supervised approval pause is **AWAITING APPROVAL**. None is PASS or permission for a fallback run. This fixture's live status remains **PENDING** until executed and its evidence recorded.
