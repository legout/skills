---
name: project-verification
description: Create or update a project-specific verification recipe skill under .agents/skills (verify-PROJECT) that documents how to launch the project and prove one real user-facing journey with independently derived expectations. Use when asked to create, generate, update, or maintain a project verification skill, recipe, or feature map, or to record how to verify this project's startup, UI, CLI, or persistence behavior. Not a test policy, automatic verifier, scheduled audit, or product-repair authority.
---

# Project Verification Recipes

> Adapted from Cursor's [`pstack`](https://github.com/cursor/plugins/tree/f713f14203cd6420cec13cd7c55c32d598dbab68/pstack) `create-verification-skill` and `maintain-verification-skill` at commit `f713f14203cd6420cec13cd7c55c32d598dbab68` (MIT, Copyright (c) 2026 Lauren Tan). Pstack's daily-cadence, verifier-swarm, and full-feature-map defaults are deliberately not adopted.

A manual, explicitly invoked generator and maintainer. It produces project-specific operating knowledge only: the installed `agent-guardrails` skill owns whether a check is justified, its oracle, and its budget, and `verification-before-completion` owns whether evidence supports a completion claim. Creating or updating a recipe grants no product repair, source approval, admission, production-data or user-browser access, dependency installation, service restart, PR/push/release, or new-capability authority.

## Create mode

1. Interview the repository before asking the user anything: documented startup commands, the real user surface (CLI, UI, protocol), existing driving harnesses and checks, observable evidence, and isolation constraints. Prefer existing harnesses and fixtures; never generate a custom control CLI or install a framework.
2. Confirm with the user: the target project name, the one important journey to start from, and whether execution is already authorized in this session.
3. Generate `.agents/skills/verify-<project>/SKILL.md` from [the recipe template](references/recipe-template.md): target identity (how to confirm the correct installed/build identity), prerequisites and permissions including what is not authorized, launch to a usable state (not merely an answering process) with teardown, a read-only readiness check, concrete drive commands or selectors on the user-facing surface, independently derived expected outcomes, evidence capture including side effects and persisted-state read-back, and cleanup of only owned resources. Add `features/` files only when separate recipes genuinely earn their own file.
4. Demonstrate once, end to end, only if execution is already authorized: record command, output, exit code, and the read-back observation, then clean up owned resources. Otherwise label the generated skill clearly as a draft whose instructions are unproved, and state exactly what remains unverified.

## Update mode

Run only for changed or proven drift, never on a schedule. Compare each affected recipe against the current documented surface and distinguish documentation drift (the recipe is stale), harness gaps, and product regressions. Fix drift and harness gaps in the recipe; report a product regression — never rewrite an expected outcome to match observed behavior. Scope the pass to the affected recipes: no full-map audit, verifier swarm, or daily default. Keep run notes as scratch; do not commit an evidence ledger or a lifecycle on top of the recipe.

## Rules

- A feature map is a menu: consumers select one necessary bounded journey, and several actions (write, reopen, read) may form that single proof. Possessing a recipe never obligates a full-app pass.
- Expected and observed stay separate; source or app exploration cannot redefine correctness. Bind every proof to its surface, scenario, artifact, and relevant environment — CLI proof is not MCP or deployment proof, and current-state claims need current observation.
- Recipe authority stops at the recipe files and any owned scratch state. Reuse an existing authorization only when it genuinely covers the selected action; otherwise report the missing prerequisite and stop.
- Independent expectations come from requirements, approved examples, or a trusted reference — never from running the implementation and copying its output.
