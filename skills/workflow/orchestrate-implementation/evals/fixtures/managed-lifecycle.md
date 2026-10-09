# Managed lifecycle acceptance fixture (live run PENDING)

This fixture requires actual native Pi child execution in a disposable Git repository. **Status: PENDING — not executed.** Offline Git recipe tests and instruction-text checks do not prove this live runtime boundary. Run only when explicitly authorized to execute this fixture; never use a real project's checkout for its mutations.

## Setup and authority

Use the installed native Pi skill/tool guide, discovered native Pi profiles, and supported request shapes. Missing runtime, credentials, placement, or protocol support means `BLOCKED`, not permission for a CLI/other-host fallback. Do not import private runtime modules or invent retention options.

```bash
set -euo pipefail
run_root=$(mktemp -d "${TMPDIR:-/tmp}/managed-lifecycle.XXXXXX")
mkdir -p "$run_root/repo"
git -C "$run_root/repo" init -q
git -C "$run_root/repo" config user.name "managed lifecycle fixture"
git -C "$run_root/repo" config user.email "fixture@example.invalid"
printf 'seed\n' > "$run_root/repo/seed.txt"
git -C "$run_root/repo" add seed.txt
git -C "$run_root/repo" commit -qm "fixture base"
```

This fixture authorizes isolated implementation, review, one deliberate repair scenario, and candidate assembly in **supervised** mode. It does not authorize target integration, push, issue/PR mutation, deploy, or release. Record parent-owned worktree paths under `run_root`; runtime-managed checkouts/artifacts may live elsewhere only with verified ownership in this disposable repository. Resolve every checkout's physical common Git directory before granting writes. Preserve failures; no forced cleanup.

## Committed-result scenario

1. Discover native Pi profiles, current runtime versions, model/options, and worker tool dependencies. Record actual launch/role choices.
2. Pin a named lane base with the Git handoff recipe. Record repository/base identity and approval: the fixture itself is the bounded behavioral source and execution authority; vocabulary/ADR capture has no new content.
3. Launch one fresh managed Pi writer with `worktree: true`, that named `baseRef`, bounded owned files, external report output, and a unique parent-authorized result ref. Its fixture task is to create `answer.txt` containing exactly `ready\n`. A focused independent check compares those bytes.
4. To exercise real finding disposition, explicitly instruct this fixture writer to prepare the single deliberate defect `ready!\n`, report the expected check failure honestly, commit it, and freeze its result ref before native finalization. This is an authorized synthetic defect, never a production instruction or a fabricated pass. No automatic green gate should reject the intentionally red fixture before its handoff is collected.
5. Let normal native finalization run. Collect actual report, clean-check evidence, runtime handoff references, and cleanup outcome. Verify the frozen result commit/tree survives even if the managed worker branch/checkout is removed. Do not assume removal or request undocumented retention.
6. Advance the disposable parent's HEAD with an unrelated committed file. Verify/review the frozen result, not current parent HEAD. Use a read-only checkout at the result ref if the worker checkout disappeared; do not replay a patch or create a synthetic reconstruction on this happy path.
7. Dispatch one fresh Pi reviewer with the complete inline contract, exact base/result endpoints, real fixture callers, criterion, and honest failed check. It should identify the byte mismatch as the one small in-scope defect. The parent dispositions it and authorizes one fix pass.
8. Launch a fresh managed Pi fix writer from the prior frozen result ref. Correct only the mismatch, run the focused check, and freeze a distinct result-attempt ref. Record actual finalization. Verify the original result remains unchanged and the fixed result descends from it.
9. Perform one fresh delta recheck of `priorResultSha..fixedResultSha` and the byte criterion, with the full inline contract. Do not reopen the full task or dispatch a third round. Unresolved/new material blockers stop for the human.
10. Assemble the fixed source range in an isolated candidate, run the meaningful combined check, and inspect source/tree correspondence. Complete candidate review as required without reopening settled code. Supervised mode pauses **after** this reviewed candidate exists, before target integration. Hand its path/branch/base/head, checks/review, authority, and residual risks to `merge-worktree` without invoking integration.

## Patch recovery scenario

Separately exercise the optional patch-only path in fixture-owned resources: capture a complete binary-capable patch and independent expected worker tree, simulate loss of the disposable result checkout/ref, and reconstruct from the original pinned base. Record patch digest, staged/committed tree, cleanliness, and exact review endpoints. Do not relabel worker-created patches as runtime-generated artifacts.

Exercise refusal cases on separate paths: moved base/digest mismatch before review allocation; corrupt matching-digest patch or wrong staged tree before reconstruction commit; hook-mutated committed tree/dirty checkout blocking acceptance. Preserve diagnostic artifacts. A full patch replacement must use a new artifact/review endpoint and direct prior-to-replacement delta; do not append the replacement to its superseded candidate or reset correction limits.

## Required evidence and verdict

Use existing runtime artifacts and one concise fixture result, not a new evidence ledger. Record actual runtime/model/profile discovery; worker/fix/reviewer run IDs and requests; canonical repository/workspaces; named base; original/fixed result refs, SHAs, trees and cleanliness; native finalization; parent HEAD movement; focused failed-before/passed-after checks; review/recheck endpoints and verdicts; candidate handoff; patch/refusal outcomes; and cleanup/blocker state.

`PASS` requires the actual committed-result, supervised-candidate, and recovery/refusal scenarios to pass. `BLOCKED` names the missing native prerequisite; failed assertions are `FAIL`. A supervised stop before **target integration**, with all fixture criteria established, is the intended success boundary, not an early assembly approval request. Keep this fixture's live status `PENDING` until executed and its evidence recorded; never substitute offline success.
