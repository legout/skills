---
name: review-codebase-architecture
description: Review architecture, module seams, and implicit state machines without editing code. Use for architecture audits, lifecycle analysis, or testability and navigability problems.
---

> Adapted from [`mattpocock/skills`](https://github.com/mattpocock/skills/tree/3cca18b368ae95cdbdebbff572ccafa662551015) at commit `3cca18b368ae95cdbdebbff572ccafa662551015` (MIT). Change-coupling analysis additionally adapts [`caldoai/skills`'s `untangle-codebase`](https://github.com/caldoai/skills/blob/f3cf47774975a7d9fca45730babf4ff7ad765ada/skills/untangle-codebase/SKILL.md) (MIT, Copyright (c) 2026 Maze).

# Architecture review

Use repository domain terms and ADRs. Vocabulary: module, interface, implementation, depth, deep, shallow, seam, adapter, leverage, and locality.

## Scope

Use the named area; otherwise start with recent change hotspots. Trace callers and tests; Git co-change supports, but does not prove, coupling.

Look for evidence of:

- shallow modules whose interface nearly matches their implementation;
- pieces that must change together but are scattered or implicitly linked;
- pieces that change independently but are coupled, including stable modules depending on volatile details;
- implicit state machines across flags, callbacks, or status fields; for stateful flows, read [state lifecycles](references/state-lifecycles.md);
- duplicated orchestration around a missing deep interface;
- tests reaching through internals or test-only helpers reducing locality; and
- implementation details leaking to callers.

Apply the deletion test: deleting a good deep module should expose and concentrate meaningful complexity, not merely move its name.

## Report

Rank evidence-backed candidates: files, observations, current interface, hidden complexity, proposed deeper module/seam, benefits, risks, affected ADRs, blast radius; strength `Strong`, `Worth exploring`, or `Speculative`.

Default to Markdown. For requested or materially useful visuals, follow [the HTML report guide](references/html-report.md); write outside the repository unless asked otherwise.

End with one recommendation and a justified do-nothing option.

## Boundary

Do not edit code or settle interfaces. Ask which candidate to explore; route it to `shape-design`, then `write-implementation-plan` only after design approval.
