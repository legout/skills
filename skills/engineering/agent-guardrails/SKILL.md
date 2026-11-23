---
name: agent-guardrails
description: Scope and evidence gates for implementing, testing, reviewing, and verifying code. Read before any code change, test design or run, review, reviewer dispatch, review-finding repair, or completion claim.
---

# Agent Guardrails

Compose with project rules and specialized skills. Explicit user requirements and written project conventions still bind.

## Scope

- Priority: agreed task, then correctness, then proven risk. Written conventions are binding, so violations are must-fix. Unwritten taste never blocks.
- Make the smallest safe change. A new dependency or abstraction needs a job today. Extra ideas get one line in the report, not code.

## Findings gate

Every finding (review comment, test request, rerun request, security concern) needs all five of these, or it is dropped:

1. the named requirement or written rule it violates;
2. caused or worsened by this change;
3. reachable through real callers, inputs, and environment;
4. material impact;
5. a proportionate response.

Never drop a real reachable defect, a required test, or a written convention just to reduce noise. When the proven fix is large or out of scope, tell the human in one sentence. Do not hide it, and do not fix it automatically.

**Security** applies only when the change touches a boundary: untrusted or external input (files, queries, network), credentials, auth, or dependency changes. A security finding needs a named asset, a realistic attacker, and a working attack path through real use. Stolen-secret, broken-TLS, malicious-admin, and generic-hardening stories are not findings. When no boundary is touched, write `security: n/a`. When a genuine boundary lacks the facts to judge it, mark it `unverified` and ask. Written safety rules always apply.

## Tests and evidence

- **Justify each check**: name a reachable failure, give an independently justified expected result, and use the cheapest stable seam that catches the failure.
- **Test-first**: for new non-trivial behavior, write one failing test first when practical. Write one focused test per uncovered behavior, and none when existing coverage applies. Before writing a new test, search the existing ones and extend or sharpen one instead.
- **Independent oracle**: expected values come from requirements, hand-worked examples, a trusted reference, or a real bug. Never copy them from implementation output or from another agent's agreement. Assert observable behavior. Use mocks or private-shape assertions only where a contract requires them.
- **No ceremony**: no automatic broad suites, coverage quotas, certification matrices, mutation campaigns, or repeat-until-green. Mandatory project or CI gates and explicit authorization still bind. Raise a budget conflict before running anything.
- **Reuse evidence**: passing evidence stays valid across handoffs, commits, and identical-content merges as long as the relevant code, tests, inputs, and environment still match. Rerun only for a relevant change or a specific hypothesis, never to earn a "final" label. Formatting or prose changes keep behavioral proof valid unless that text is itself the tested contract.
- **A failure authorizes nothing broader**: investigate the named failure. Do not widen the suite or weaken expectations. Stop or escalate instead of looping.
- **Retiring tests**: retire a test only for behavior that was itself retired, or when a surviving assertion is mapped to it. AI authorship is not evidence for deletion. To slim a suite, use `test-diet`.

## Verification claims

- Evidence must match the claim. Drive the real artifact through its actual surface (CLI, UI, protocol). Read back persisted state when it matters, and confirm the installed or built identity.
- Compilation, an mtime, a running process, a toast, or an agent's assertion proves nothing on its own. A static check proves structure only.
- Bind each piece of evidence to its surface: CLI proof is not MCP or deployment proof. A claim about the current state needs a current observation.
- Expected results come from requirements; exploring the app cannot redefine them.
- A strong automated test can be the whole proof, so do not add a duplicate live stage. Pick one necessary bounded journey from a feature map rather than all of it.
- Report the narrower scope you actually verified, plus any failed, blocked, or unverified prerequisites.

## Review loop

1. **Dispatch**: paste the Reviewer Dispatch block below into the fresh reviewer's prompt, filled in with the criteria, written rules, and real-use context. A link is not enough, because fresh agents may not read AGENTS.md or this skill.
2. **Reviewer**: returns findings and a verdict of `pass` or `fix-first`, then stops. It never repairs code or starts a re-review.
3. **Disposition, before any repair**: when a finding fails the gate, reject it in one line. When it needs a small in-scope fix, fix it. When the right fix is large or out of scope, hand it to the human.
4. **One fix pass, then one delta recheck** covering only the fix and the behavior it changes. If the same finding survives an honest fix, ask the human. There is no third round.
5. **Close**: restate the approved task in one sentence, compare the result against it, and choose accept / fix / hand back / ask. Do not create evidence ledgers or sign-off artifacts.

## Authority

Creating or maintaining a skill grants none of the following: product repair, approval, access to production data or the user's browser, dependency installs, restarts, pushes, PRs, releases, or new capabilities.

## Reviewer Dispatch

Paste this block into **every fresh-context reviewer prompt**, replacing the placeholders:

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
Tests: request one only for a named reachable scenario and regression
that no existing test covers; prefer sharpening an existing test.
Coverage percentage is not a reason.
Reruns: passing evidence survives this handoff while the relevant code, tests,
inputs, and environment still match; request a rerun only for a relevant
delta or specific hypothesis, never a fresh label or ceremony. A failing
check does not authorize broader suites or weakened assertions.
Out-of-scope issues: one line max, never blocking; if the right fix is big,
say so in the verdict rather than listing it as fix-first.
Cover the criteria, real risks and written rules; verdict: pass or fix-first.
Then stop. Do not make repairs or start re-reviews.
```

For a re-review, replace the first line with: `Re-review only the fix in <commit/diff> and the behavior it changes against <original finding>. Do not re-review settled parts of the change.`
