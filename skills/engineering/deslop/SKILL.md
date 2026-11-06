---
name: deslop
description: Find and apply behavior-preserving KISS simplifications in a diff, file, directory, or project. Use for simplify, deslop, cleanup proposals, explicit direct cleanup, or an accepted completion-boundary pass; not bug fixing or architecture-only audits.
---

> Adapted from [`cursor/plugins`](https://github.com/cursor/plugins/tree/93b00b89ef425a9c1bac0d0b317dfc49c930ac99), `cursor-team-kit/skills/deslop/SKILL.md`, at commit `93b00b89ef425a9c1bac0d0b317dfc49c930ac99` (MIT, Copyright (c) 2026 Cursor). Subtraction-first, caller-migration, legacy-deletion, and behavior-pin principles are additionally adapted from `pstack/skills/poteto-mode` at the same commit.

# Deslop: simpler code, same behavior

Reduce unnecessary code, concepts, indirection, and reader effort. Prefer clear structure over fewer lines; a clever one-liner or another helper layer is not automatically simpler. Load `agent-guardrails` before analysis or changes; it owns evidence and validation budgets.

## Intent and scope

- **Default: propose, then wait.** A bare `deslop` or a request to inspect, simplify, or suggest improvements produces concrete proposals without editing project files. Do not create planning artifacts or run validation suites just to produce the report.
- **Explicit direct cleanup: apply.** “Simplify this directly”, “clean up src/ now”, or “apply S1 and S3” authorizes bounded behavior-preserving edits without another selection round. State the scope and proceed. Ambiguous intent stays proposal-only; material scope, behavior, or architectural decisions still require approval.
- At a completion boundary, name the settled diff and whether the offered pass proposes changes or also applies them. Acceptance authorizes only that stated action, not a broader cleanup. Skip docs-only, generated, mechanical, or trivial changes.
- Honor named targets: current diff, a file, one or more directories/modules, or the whole project. Resolve ambiguous paths before analysis. Read adjacent callers for evidence; editing outside the named scope needs approval.
- Without a target, use the current diff, not the whole repository. Include staged and unstaged tracked changes; for branch work include commits since the verified base. State the comparison range. Do not guess a base or silently ignore local changes. If no meaningful diff exists, ask for a target.
- Preserve pre-existing user changes. Exclude generated/vendor code, caches, build artifacts, and user-owned untracked files unless explicitly included. A whole-project pass must name uninspected areas instead of claiming exhaustive coverage.

## Find worthwhile simplifications

Read project instructions, deliberate design decisions, relevant code, and actual callers. Use one bounded pass across these three perspectives; zero worthwhile proposals is valid. Additional reviewers are optional, only when explicitly requested or required by project rules and delegation is authorized; then read [the review brief](references/review.md).

- **Reuse:** demonstrably equivalent duplicate logic or work already done by a helper, standard library, framework, or platform guarantee. Cite the alternative; different contracts need not be merged.
- **Quality:** dead code/state, narration comments, needless nesting, pass-through wrappers, parameter sprawl, and fragmented ownership. Check exports, routes, registrations, configuration, reflection, and external consumers before deleting; missing imports or a single caller are not proof. Prefer direct data flow and locality, while preserving deliberate wrappers, meaningful modules, and intentional duplication.
- **Efficiency:** concrete repeated computation/reads, unused work, or overly broad operations. Show the actual cost and behavior-equivalent reduction; do not turn a hypothetical speedup into a concurrency or interface change.

For each candidate, explain the current complexity cost and the smallest simpler alternative. AI authorship, style preference, file count, and line-count reduction alone are not reasons. Keep uncertain deletions as questions rather than recommendations to remove code. Separate discovered bugs from cleanup; do not silently fix behavior under a simplification request.

## Proposals and selection

Rank useful proposals by benefit and risk, with no quota. Give each a stable ID and:

- file/symbol locations, supporting evidence, and the concrete change;
- why the result is easier to understand or review;
- behavior/contracts to preserve, dependencies, risks, and uncertainty;
- the smallest verification needed, or applicable evidence to reuse; and
- whether it is a bounded edit or needs design first.

In proposal mode, stop here and ask which IDs to apply or develop through the workflow skills. Keep proposals in the conversation unless the user requests a saved report. In direct mode, use the same criteria internally, apply only authorized bounded changes, and report the result rather than requiring a proposal approval round.

## Apply authorized changes

1. Recheck selected proposals against current code; missing IDs or changed assumptions require clarification. Inspect the working tree and preserve unrelated edits.
2. Subtract before introducing structure. Keep interfaces, error semantics, persisted data, resource cleanup, concurrency, performance obligations, security, and accessibility intact. Never remove boundary validation or data-loss-preventing handling as “slop”. Add an abstraction only when it removes concrete complexity.
3. Make small coherent edits. For internal replacements, migrate all supported callers, remove the obsolete path, and check stale references within the approved scope. Retain compatibility required by real public, persisted, deployed, external, or dependent-branch consumers; request scope expansion rather than leave a broken caller.
4. Use applicable existing evidence or establish the smallest behavior pin before a risky rewrite. Verify the combined selected changes after implementation; check earlier only when a dependency or disappearing evidence makes it necessary. Prefer claim-matched real-artifact verification; an existing focused test may already be sufficient. No automatic full suites, new tests per edit, or duplicate live checks. Required project gates remain binding.
5. Follow `agent-guardrails` on failures: investigate the named failure, one fix pass and one delta recheck, then ask. Never weaken assertions or delete tests for still-supported behavior to force green.

Report what changed, what stayed, actual verification and its limits, and residual risks. No automatic commit, push, installation, or cleanup of unrelated resources.

## Workflow handoff

Small understood edits need only the user's scoped approval, not an ADR/spec/plan ceremony. For selected architectural or multi-step proposals, load [`planning-contract`](../../workflow/planning-contract/SKILL.md) (Contract version: 1), then route to [`shape-design`](../../workflow/shape-design/SKILL.md). If the contract is unavailable, stop the handoff and request it rather than inventing approval rules.

Carry selected IDs, evidence, affected surfaces, behavior-preservation criteria, unresolved choices, and authorization state. Findings are evidence, not approved designs. `shape-design` uses `domain-modeling` for qualifying ADRs or vocabulary; [`write-implementation-plan`](../../workflow/write-implementation-plan/SKILL.md) decomposes approved behavior and creates tickets only when requested or required for coordination. Never fabricate approval or maintain duplicate task bodies. Record contract version and available provenance, or `unknown`, in the handoff.

Architecture-only seam analysis belongs to `review-codebase-architecture`; bug diagnosis belongs to `systematic-debugging`, not an implicit cleanup fix.
