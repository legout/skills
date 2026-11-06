---
name: project-formal-verification
description: Create or update a project-local verification recipe for a named invariant, model check, or code-level proof. Use when explicitly asked to generate or maintain such a skill, or reconcile its model with changed code; not for ordinary runtime verification or a whole-repo audit.
---

# Project Formal Verification Recipes

> Adapted from Cursor pstack's [create-formal-verification-skill](https://github.com/cursor/plugins/blob/2776ddd2355d6d6c8747d3964600f28daf62f049/pstack/skills/create-formal-verification-skill/SKILL.md) and [maintain-formal-verification-skill](https://github.com/cursor/plugins/blob/2776ddd2355d6d6c8747d3964600f28daf62f049/pstack/skills/maintain-formal-verification-skill/SKILL.md) (MIT, Copyright (c) 2026 Lauren Tan). Automatic tool installation, mandatory statechart rendering, and ceremonial reruns are not adopted.

This explicitly requested generator/maintainer owns verification artifacts, not product repairs. Load `agent-guardrails` for scope, evidence, and correction limits; if unavailable, stop and request it without installing anything. `verification-before-completion` owns completion claims. Skill creation grants no dependency installation, production access, service restart, product-code repair, or publication authority. Temporary fault injection needs authorization covering the isolated scratch work.

## Select the property and method

Start with the named area, or resolve one bounded area from the request; do not scan the whole repo for a harder problem. Identify one promise, its independent source, and a reachable harmful violation. Ask only about missing intent or authority. If the promise conflicts with approved requirements, return to `shape-design` rather than choosing a new contract.

Prefer an existing check and tool. Use a small model for ordering or protocol questions, a code-level verifier for properties of actual code, and a deductive proof when finite bounds cannot establish the required claim. Explain the cheapest suitable choice. Generated-input tests against real code are an empirical alternative, not a formal proof; do not silently substitute them or a hand-copied function model for the requested claim. A missing tool blocks execution, not permission to install one.

## Create mode

1. Inspect the relevant callers, state writers, failure paths, and atomic or transactional boundaries. Map each modeled action to actual code; do not make several interruptible operations atomic to obtain a pass.
2. Generate `.agents/skills/verify-<project>-<area>/SKILL.md` using [the recipe template](references/recipe-template.md). Respect existing names and verification directories. Without an established location, keep owned model/harness files with the recipe; ask before adopting another layout. Reuse existing helpers; add no generic runner.
3. Fill actual paths, property source, method, assumptions, bounds, tool version/configuration, command, result interpretation, code correspondence, and change triggers. Keep unknowns explicit. An unexecuted recipe is a draft, never proof of the property.
4. Within the authorized budget, follow the generated recipe as a cold-start user once. Include one targeted negative control for the selected property and restore the starting state afterward; retain evidence outside disposable scratch. Without execution or fault-injection authority, report the exact unproved part instead of performing it.

## Negative control and code correspondence

For a code-level verifier, a relevant defect in isolated code must trigger the intended property failure, not a parse error, crash, or timeout. For a separate model, demonstrate both that the corresponding modeled defect violates the property and that the recipe identifies the source change requiring correspondence review. An unchanged model cannot detect an arbitrary code edit by itself. Label these two observations separately; never present model mutation as automatic code-regression coverage.

If the current property already fails, preserve that baseline finding. A new negative control must be distinguishable from it; otherwise report the control as unverified. Restoration returns to the original result, not necessarily to green. No mutation campaign or repeat-until-green loop.

## Update mode

Read the affected diff before deciding to rerun: since the last confirmed correspondence, include relevant working-tree changes, moved functions, and new writers of guarded state. A missing sync commit means correspondence is unknown; the last edit to a model is not evidence of alignment. Ignore proven no-effect changes and reuse still-applicable results.

Update models and harnesses from the code, not from the desired result. Change a property or narrow its scope only against approved changed requirements or an explicit owner decision; tests, comments, and commit messages alone do not grant that authority. Report old and new meaning or bounds. Run only the affected check; repeat the negative control when its detection path changed, not after every edit.

Confirm correspondence before advancing its recorded commit. A relevant dirty diff remains explicitly unsynced; do not label HEAD as the checked dirty artifact. Alignment may be confirmed even when a property fails: synchronization and a passing result are different facts. A blocked alignment check does not advance the marker. Keep this metadata in the recipe, not in a new lifecycle or evidence ledger.

## Interpret and hand off

Report what is in sync or updated, any counterexample or confirmed code bug, and any blocked or unverified part. A trace becomes a code finding only after checking its steps against real callers, inputs, atomicity, and environment; otherwise report the modeling mismatch or unknown. Never weaken the property to hide a violation or repair product code under maintenance authority.

State the property, method, command, scope/assumptions, correspondence, result, evidence location, and exclusions in plain language. Preserve failed, unknown, and incomplete outcomes. A successful recipe demonstration does not imply that the product satisfies its property. Use an optional diagram only when it clarifies the trace; do not require or install `statechart` or a renderer.

For runtime journeys, use `project-verification`. For an existing recipe, follow it rather than recreating it. Offer another property only when a concrete nearby need justifies it.
