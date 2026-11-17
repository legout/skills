---
name: test-diet
description: Slim an existing test suite to the tests that prove real behavior, with evidence for every deletion. Use for too many tests, test bloat, pruning, consolidating or auditing a suite, or when tests grow faster than code; not for writing new tests or production-code cleanup (deslop).
---

# Test diet: keep the tests that prove behavior

Load `agent-guardrails` first; it owns evidence budgets, reruns, review rounds and authority. Propose first: deleting, merging or rewriting tests needs the owner's approval of the concrete list. Never optimize for a target count or treat AI authorship as evidence of waste.

## 1. Inventory (read-only)

- Collected cases per file, test functions, test lines against production lines, the slowest files, and the project's required gates (CI, verify or release scripts). Parametrized cases are cheap; counts are context, not the goal. Collect-only is not execution proof.
- Growth markers: files named after review rounds, issues or tasks; copied fixtures and stubs; repeat loops such as `range(n)`; many tests with identical setup and one assertion each.

## 2. Proof map

List what must be proven from approved specs, acceptance criteria and real user journeys, not from the code: public contracts, journeys, permissions, persistence, migration and rollback, security boundaries, races, domain and numerical rules. Give each item the highest seam that is still fast and deterministic:

- User journey: one end-to-end, browser or route-level test with real temporary storage.
- Library contract: public API with spec examples; property tests for invariants; differential tests against a frozen reference or the old system.
- UI: one rendered or browser check with measurable criteria (contrast, focus, overflow, accessibility tree) per theme and viewport; at most a few owner-approved screenshots.
- Pure rules: table or property tests.

## 3. Classify each test

| Class | Signals | Action |
|---|---|---|
| keep | sole proof of a map item; independent oracle; permission, persistence, safety boundary, race or migration case; reproduces a real bug | keep |
| merge | same seam and setup as a sibling, one assertion each | one test with several assertions or one table; parametrizing alone removes no cases |
| replace | narrow tests that together approximate one journey | add the journey test at the higher seam, then remove them |
| delete | asserts source text, CSS class names, private helpers or framework behavior; mock-only self-confirmation; consumer copy of a library test; repeat loop without controlled interleaving; retired behavior | delete after evidence |
| flaky | passes or fails without a code change | fix the root cause, or delete with a written reason; never retries or sleeps |
| unsure | anything else | keep |

A test that never failed is not therefore useless.

## 4. Evidence for every delete, merge or replace

- Name the surviving test and the exact assertion that covers the same reachable production behavior.
- Per-test coverage (for example coverage.py contexts via `pytest --cov-context=test`) only finds candidates: equal coverage does not mean equal inputs, assertions or oracles.
- Confirm with a fault: a mutation tool on the suspect lines, or a deliberate one-line defect that is reverted afterwards. The survivor must fail on it; otherwise keep the test or move its assertion first. Installing a mutation tool needs approval.
- Library and consumer: finish the library's reductions first. Delete a consumer copy only after mapping it to an assertion in that final library candidate and confirming the consumer's pin installs that candidate; a test-only library commit does not move the pin.

## 5. Proposal, then stop

One table per file: test, class, surviving test and assertion, fault and result. Add before and after counts, lines and runtime of the touched files. Wait for owner approval.

## 6. Apply

- Small batches per behavior or file, test-only commits. A bug found on the way is a separate finding, not a silent production fix.
- After each batch run the touched tests and the required project gates; reuse still-applicable evidence per `agent-guardrails`.
- A survivor that misses its mapped fault blocks that deletion.

## 7. Prevent regrowth

Check that project or global agent instructions carry the test-hygiene rules: search existing tests before adding one, file tests by behavior rather than review round, let review findings sharpen existing tests, no assertions on source text or CSS class names. Propose missing rules; edit instruction files only with approval.

## Report

Restate the approved scope; list deletions with mapped survivors and faults, suspicious tests kept, gates run with results, and what stays unverified (mutation not run, simulated network or file I/O reported as offline behavior, not live proof).
