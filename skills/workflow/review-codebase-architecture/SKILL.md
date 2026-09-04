---
name: review-codebase-architecture
description: Review a codebase for high-value module-deepening and seam improvements without changing code; use for architecture audits or testability and navigability problems.
---

> Adapted from [`mattpocock/skills`](https://github.com/mattpocock/skills/tree/3cca18b368ae95cdbdebbff572ccafa662551015) at commit `3cca18b368ae95cdbdebbff572ccafa662551015` (MIT).

# Architecture review

Review architecture without editing code or defining final interfaces. Use the repository's domain terms and existing ADRs. Use this vocabulary consistently: module, interface, implementation, depth, deep, shallow, seam, adapter, leverage, and locality.

## Scope

Use the user's named area. Otherwise inspect recent history for repeatedly changed hotspots before scanning broadly. Follow actual call paths and tests.

Look for evidence of:

- shallow modules whose interface nearly matches their implementation;
- one concept scattered across many files;
- duplicated orchestration around a missing deep interface;
- tests that reach through internals because no stable public seam exists;
- details leaking between coupled modules; and
- extracted helpers that improve unit-test access but reduce locality.

Apply the deletion test: deleting a good deep module should expose and concentrate meaningful complexity, not merely move its name.

## Report

Rank only evidence-backed candidates. For each include files, observations, current interface, hidden complexity, proposed deeper module or seam, benefits, risks, affected ADRs, blast radius, and one strength: `Strong`, `Worth exploring`, or `Speculative`.

Use Markdown by default. When the user asks for a visual report or diagrams materially clarify the relationships, follow [the HTML report guide](references/html-report.md) and write the result outside the repository unless the user asks otherwise.

End with one recommendation and a justified do-nothing option.

## Boundary

Do not edit code or settle interfaces. Ask which candidate to explore, then route the selected candidate to `shape-design`. Use `write-implementation-plan` only after the design is approved.
