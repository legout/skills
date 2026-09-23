---
name: agent-guardrails
description: Scope and evidence gates for implementing, testing, and reviewing code. Read before any code change, test design or execution, review, reviewer dispatch, or review-finding repair; prevents speculative security/test findings and endless review loops without weakening real requirements.
---
## When to Use
Use on every coding task involving implementation, tests, or code review, including fixes after a review and dispatching a fresh-context reviewer. Compose with project rules and specialized skills; written project conventions and explicit user requirements still bind.

## Procedure
1. Before acting, identify the agreed task, written rules/conventions, real callers, inputs, environment, and any genuine security boundary. Priority: agreed feature, correctness, then proven risk. Written convention violations are must-fix; unwritten reviewer taste does not block. Prefer the smallest safe change. For new non-trivial behavior, one failing test first when practical; use existing focused checks when sufficient. New dependencies and abstractions need a job today.
2. Only report or accept a finding that names the violated requirement or written rule, shows this change caused or worsened it, demonstrates a reachable scenario in real use, explains material impact, and offers a proportionate response. Do not hide an actual defect because it is security-related or out of scope: flag a proven large/out-of-scope issue to the human.
3. Security findings require a touched boundary (untrusted or external input through files, queries or network; credentials; auth; dependency changes), a named asset, a realistic attacker, and a working attack path through real callers, inputs, and environment. Do not invent stolen-secret, broken-TLS, malicious-admin or generic hardening stories. If no boundary is touched, say 'security: n/a'. If a genuine security task lacks facts, mark the criterion unverified and ask rather than inventing a threat model. Apply written safety rules even if they are not security findings.
4. A request for a test is a finding: name the reachable scenario and the regression it would catch. Coverage percentage or unreachable states alone do not justify new tests; run relevant existing checks and report what they actually prove.
5. When dispatching a fresh reviewer, put the complete dispatch contract below IN the prompt with the specific criteria, written conventions and real-use context. A path or link to this skill is not enough. Reviewer only returns findings and a pass/fix-first verdict; the parent alone decides fixes and re-reviews.
6. Before repairing reviewer feedback, disposition each finding: fails a gate -> reject in one line; passes with a small in-scope fix -> fix; passes but the right fix is large/out of scope -> hand back to the human in one sentence. Never treat reviewer opinion as authority over the approved task.
7. A review ends once agreed criteria, real risks and written rules are covered. After a fix, re-review ONLY the fix and the behavior it changes. One fix pass and one delta recheck; if the same finding survives an honest fix, stop and ask the human rather than starting round three.
8. After each coding task, restate the approved task in one sentence, compare the result, and choose accept / fix / hand back / ask. Record extra ideas in one line, not code. Do not create evidence ledgers or sign-off artifacts for this process.

## Pitfalls
- Fresh reviewer agents may not read AGENTS.md or this skill; send the contract inline every time. Do not assume a skill description is an enforcement mechanism.
- Do not reject reachable security bugs, required tests or documented conventions in the name of avoiding noise. Missing evidence on a genuinely security-sensitive task is unverified, not a pass.
- Do not reopen the whole change during a delta recheck or let a reviewer initiate an unbounded fix cycle.

## Verification
1. Check the final change against the agreed task and written project rules, and run the smallest relevant checks; inspect results before claiming success.
2. Verify each reviewer finding and each new test demand names a reachable scenario; the review ends with pass or fix-first.
3. If re-reviewed, verify the prompt scoped the recheck to the fix and that no third round was launched.

## Reviewer Dispatch
Paste this block into **every fresh-context reviewer prompt**, replacing placeholders and adding relevant project conventions and real-use context. Never send only a link:

```text
Review <base>..<head> against: <approved criteria>.
Real callers/inputs/environment: <facts>. Written project rules: <paths/rules>.
Written conventions are binding; their violation is must-fix. Unwritten
preferences are taste and never block. Report only a named requirement or
written-rule violation that this change caused or worsened, is reachable in
real use, matters, and has a proportionate response.
Security: review only a touched boundary (untrusted/external input,
credentials, auth, dependency changes). A finding needs a named asset,
realistic attacker and actual attack path through real callers, inputs and
environment. Otherwise say "security: n/a". Do not report stolen-secret,
broken-TLS, malicious-admin or generic-hardening stories. If a genuine
security boundary lacks facts, mark that criterion unverified.
Tests: request one only for a named reachable scenario and regression;
coverage percentage is not a reason.
Out-of-scope issues: one line max, never blocking; if the right fix is big,
say so in the verdict rather than listing it as fix-first.
Cover the criteria, real risks and written rules; verdict: pass or fix-first.
Then stop. Do not make repairs or start re-reviews.
```

For a fresh-context re-review, send the same contract above but replace the first line with: `Re-review only the fix in <commit/diff> and the behavior it changes against <original finding>. Do not re-review settled parts of the change.` One fix pass, one delta recheck; then ask the human if unresolved.