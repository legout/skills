# Manifest and briefs

## Small parent-owned run state

Keep one compact record outside every disposable worker worktree. Prefer existing native mission state or host artifacts; otherwise use a stable parent-owned run directory accessible to the selected host. Link reports and logs instead of copying them. Record only coordination facts:

- canonical source repository, expected shared worktree root, approved run base, mode, and applicable execution/integration/publication authority;
- source references with approved scope/revision and approval reference, planning-contract version/provenance (or `unknown`), capture-checkpoint outcome, and task readiness;
- tasks, dependencies, owned files/contracts, selected Pi host, each role's complete model/thinking pair and per-field source, backend-effective representation, child/workspace/session IDs, actual canonical cwd with run/lane/role/attempt mapping, and result channel;
- per lane: pinned base ref/SHA, result ref/SHA/tree, validation/review artifact references, prior reviewed endpoint when fixing, and blocker/next action;
- candidate path/branch/base/head and source-result mapping; and
- actual terminal/ownership/cleanup state, any root/model/thinking blocked-before-launch reason, skipped checks, and residual risks.

Add patch path/digest and reconstructed identities only for patch recovery. Keep native runtime IDs in native artifacts; do not maintain another lane board, scheduler, or evidence ledger with duplicate state. Persistent Pi peers are optional named read-only consultants, not mandatory architecture/domain/quality checkpoints.

## Worker brief

Give a fresh Pi worker one cold-start packet:

1. Task goal, relevant source reference/revision, acceptance criteria, and non-goals.
2. Exact repository/common Git directory, expected shared root and host-bound cwd/branch (runtime-supplied for native managed children), complete role model/thinking pair with sources/effective form, pinned base ref/SHA, and unique authorized result ref.
3. Owned files/contracts, upstream interfaces, relevant written conventions and real callers/inputs/environment.
4. Assigned `new-test`, `existing-check`, or `no-new-test` obligation; named failure mode, focused command, and any required project checks.
5. Allowed actions, explicit no-publication boundary, report destination outside the worktree, and host-specific escalation route.

Paste these guardrails into initial and fix briefs; do not send only a link:

```text
Approved scope outranks reviewer suggestions. Use the smallest safe change; dependencies and abstractions need a job today. Follow the supplied written conventions, not unwritten taste. Run the assigned focused validation; expected values come from approved criteria or an independent oracle, not copied implementation output. Bug repros fail before the fix; behavior-affecting refactors pin current behavior before mutation. Challenge an unsuitable obligation with evidence rather than silently skipping it.
You are the sole writer in the supplied isolated checkout. Before writes, report/verify actual registered cwd beneath the expected root, canonical repository, branch, base, and runtime-effective model/thinking against the packet. Stop on material requirement ambiguity, scope/interface changes, edits beyond your owned surface, missing prerequisites, irreversible operations, or unapproved integration/publication. Do not grant permissions, install dependencies, or choose another runtime/model/host to bypass a blocker.
Only the parent dispositions review findings and authorizes fixes/rechecks. Apply only its accepted small in-scope fixes; challenge a finding contradicted by source. One fix pass and one delta recheck; do not expand or restart review. Do not delegate further. Do not run memo or write shared memory; the parent owns durable capture.
Commit intended changes, freeze only the unique parent-authorized result ref before finalization, and return the actual commit/tree, cleanliness, changed files, validation results, and open decisions. Relinquish write ownership when reporting completion. Do not call your own report acceptance or publication authority.
```

Supply the Git handoff recipe in the packet when the worker cannot access the installed reference. For a patch-only transport, supply the recovery capture recipe instead; do not claim a result ref exists across different Git databases.

## Reviewer brief

Reviewers are fresh Pi agents with a read-only role/tool contract and explicit no-project-edit instructions. Returning findings through the configured host artifact is allowed. Provide exact repository/workspace, direct base/head endpoints, the approved criteria, worker evidence, written conventions, and real-use context. A stable diff artifact is acceptable if the host cannot read the Git objects; include required surrounding source, not an unbounded pasted diff. Missing context is unverified, not a guessed pass.

Paste the entire filled contract into **every** reviewer prompt, including fixes and candidate reviews:

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
Finish when agreed criteria, real risks, and written rules are covered; zero findings is success. Verdict: pass or fix-first (small in-scope repairs), with any unverified criterion or required human decision explicitly stated. A pass does not clear those decisions or authorize acceptance/publication. Then stop. Do not run memo or write shared memory.
```
<!-- reviewer-contract:end -->

For the one recheck, replace only the opening scope: `Re-review only <priorResultSha>..<fixedResultSha>, the parent-accepted findings <list>, and the behavior the fixes change. Do not re-review settled parts. Report surviving or new material blockers in this delta, then stop; no third round.` For sibling patch reconstructions use the direct prior/replacement endpoints, not merge-base/triple-dot.

For candidate review, supply prior review evidence and source-result correspondence. Review previously unreviewed changes and integration effects, without reopening settled findings or resetting the correction budget. The parent still inspects the final combined diff.

## Result report and questions

Return status (`completed`, `blocked`, or `failed`), actual result identities and clean-check evidence, changed files, focused commands/results with artifact paths, and unresolved decisions/residual risks. For a new test, identify its independent expectation source; for repro/pinning, provide the before/after evidence. Name the approved task and compare the result in one sentence. The parent chooses `accept / fix / hand back / ask`.

Use the selected route: native Pi supervisor for native children; intercom `ask`/`send` to the verified parent session for Herdr; host follow-up for Paseo; a new `delegate_task` round for T3. Connected Paseo/T3 Pi sessions may use intercom for interactive questions when explicitly configured with a verified parent target. Without such a channel, preserve work and finish blocked with the exact question. Neither an ask timeout nor a delivered message permits guessing an owner decision.
