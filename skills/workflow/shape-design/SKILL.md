---
name: shape-design
description: Shape an idea into an approved bounded design or architectural specification before implementation, using targeted questions, alternatives, and explicit gates.
---

# Design Shaping

> Consolidates [`obra/superpowers` brainstorming](https://github.com/obra/superpowers/blob/b36e0829c6d0140e93cfef2ca599b1b07d4a7797/skills/brainstorming/SKILL.md), [`mattpocock/skills` grilling](https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/productivity/grilling/SKILL.md), and Matt Pocock's [`domain-modeling`](https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/engineering/domain-modeling/SKILL.md) terminology/decision-record guidance (all MIT). Exact pins are recorded in `sources.json`.
>
> Data-shape, boundary, idempotency, and shared-state analysis are adapted from Cursor's [`poteto-mode`](https://github.com/cursor/plugins/tree/93b00b89ef425a9c1bac0d0b317dfc49c930ac99/pstack/skills/poteto-mode) at commit `93b00b89ef425a9c1bac0d0b317dfc49c930ac99` (MIT, Copyright (c) 2026 Cursor).

Classify the request before implementation:

- **Spike:** classify and approve a feasibility question, then hand the disposable probe to `prototype-question`.
- **Bounded:** change an existing, understood flow with a short in-chat design.
- **Architectural:** create or reshape modules, interfaces, or cross-cutting behavior; produce a written specification.

When unsure, take the heavier path. Hidden complexity upgrades the path.

## Shared intake

1. Read project instructions, relevant files, recent changes, and any established context map or decision records.
2. Separate facts the agent can inspect from decisions the user owns.
3. Model dependent choices as a decision tree. Ask each round's full frontier, with a recommendation for every question; defer questions whose prerequisites remain open.
4. Challenge ambiguous domain terms with concrete scenarios. Update the established glossary as terms settle. Offer an ADR only for a hard-to-reverse, surprising decision chosen from real alternatives.
5. State non-goals and observable success criteria.

## Spike

Present the question and cheapest valid probe in 2–3 sentences, then get approval. Invoke `prototype-question` with the approved question, evidence threshold, constraints, and cleanup expectation. Consume its verdict as design evidence and return to shaping. Keeping prototype code is a new bounded or architectural request; `shape-design` owns that reclassification.

## Bounded change

Ask only material questions. Present a short design covering behavior, files, error cases, and tests. Obtain explicit approval before mutation. Then hand the approved in-chat design to `orchestrate-implementation`; do not implement it here.

## Architectural change

1. Propose 2–3 viable approaches with trade-offs; recommend one.
2. Present the design in reviewable sections: architecture, interfaces, data flow, failures, migration, and testing.
3. Obtain approval for the complete design.
4. Write the approved specification to the repository's established location.
5. Self-review for placeholders, contradictions, ambiguity, and excess scope.
6. Ask the user to review the written specification.
7. After approval, invoke `write-implementation-plan`—not an implementation skill.

## Design quality

Each module should have one clear purpose, a small stable interface, explicit dependencies, and an independently testable seam. Follow existing patterns unless a targeted change is needed for the approved goal. Apply YAGNI to every approach.

Apply the heavier techniques below only when the problem warrants them; routine bounded changes keep boring local code:

- For stateful or branch-heavy behavior, name the data shape first and the simplest organizing structure that removes repeated shape assumptions or makes illegal states unrepresentable — a state machine, table, typed model, or reducer. Never add structure that does not delete branches, assumptions, or invalid states.
- For a new requirement reshaping an existing design, describe the target as if the requirement had been foundational, then compare it with the minimum safe migration from current code.
- Validate external input at each system boundary and keep trusted internal logic direct; do not duplicate boundary guards throughout the core.
- For commands, jobs, migrations, and lifecycle operations, address retries and make the operation idempotent — an accidental re-run converges to the same end state.
- Try to remove shared mutable state before adding locks or serialization.

The artifact scales with task size; the approval gate does not.
