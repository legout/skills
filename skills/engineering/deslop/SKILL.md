---
name: deslop
description: Evidence-driven cleanup that removes dead code, duplication, unnecessary indirection, and accidental complexity while preserving supported behavior.
---

> Adapted from [`cursor/plugins`](https://github.com/cursor/plugins/tree/93b00b89ef425a9c1bac0d0b317dfc49c930ac99), `cursor-team-kit/skills/deslop/SKILL.md`, at commit `93b00b89ef425a9c1bac0d0b317dfc49c930ac99` (MIT, Copyright (c) 2026 Cursor). Subtraction-first, caller-migration, legacy-deletion, and behavior-pin principles are additionally adapted from `pstack/skills/poteto-mode` at the same commit.

Use for an explicit broad codebase cleanup request, or when the model offers a cleanup pass at a commit or PR boundary. Do not run it automatically on every edit.

# Deslop code safely

Make the requested scope materially smaller and easier to understand without changing its supported behavior.

## Resolve the scope

1. Treat every supplied target as a scope item. Accept repository roots, directories, package/module names, and files.
2. Resolve paths relative to the current working directory. Resolve module names through the project's language conventions and code search.
3. If no target is supplied, use the current Git repository root, or the current directory when outside Git.
4. If a target is missing or resolves to multiple places, ask the user before editing.
5. Inspect callers, dependents, tests, configuration, entry points, and documentation outside the scope when needed to prove safety. Keep production edits inside the requested scope unless a directly dependent file must change to preserve correctness. Explain any necessary scope expansion.
6. Exclude vendored dependencies, generated output, caches, build artifacts, and user-owned untracked files unless the user explicitly includes them.

## Establish evidence first

Before editing:

- Read repository instructions and architecture/domain documentation.
- Record the working tree and preserve pre-existing user changes.
- Identify the relevant validation commands from project configuration and CI.
- Run a representative baseline with deployment-specific environment variables isolated when they would make local validation non-hermetic.
- Record baseline file counts and line counts for the requested scope.
- Map runtime entry points and reachability using imports, exports, routes, registrations, configuration, dynamic loading, reflection, and external/public API commitments.

A test-only reference does not by itself prove that a production seam is live. Conversely, absence from ordinary imports does not prove code is dead when the project uses plugins, reflection, configuration, templates, or generated registration.

## Classify cleanup candidates

Remove or simplify code only when evidence supports at least one classification:

- **Dead:** unreachable from supported runtime entry points and not part of a documented public contract.
- **Duplicate:** repeats behavior already owned elsewhere and can use one canonical implementation.
- **Overcomplex:** abstractions, modes, branches, layers, deeply nested control flow, callback pyramids, or interacting boolean states exceed the behavior the application actually supports.
- **Boilerplate/slop:** narration comments, milestone notes, placeholder metadata, redundant docstrings, needless wrappers, defensive handling for impossible trusted states, type-system bypasses, speculative compatibility paths, or tests that preserve deleted implementation seams rather than behavior.
- **Fragmented:** a small module or file adds navigation cost without providing a meaningful boundary and can be merged into its natural owner.

When evidence is uncertain, keep the code or ask the user. Do not label code dead merely because its name looks old.

## Refactor incrementally

1. Start with the highest-confidence, lowest-risk deletions.
2. Subtract before adding: delete dead weight, collapse one-caller wrappers, and drop redundant validators before introducing any new shape. Name the target structure — what the code would look like if built today — and prefer fewer concepts, modes, fields, branches, and files.
3. Flatten nested control flow with guard clauses, early exits, simpler state models, and direct data flow. Remove unnecessary `else` branches after exits.
4. Extract a helper only when it creates a meaningful boundary or names a coherent operation. Moving nested code into tiny wrappers does not reduce complexity.
5. Keep interfaces as narrow as their real callers allow.
6. For an internal API replacement, migrate every caller, verify the migrated callers, delete the legacy path, and search for stale references to it in one cleanup. Keep a compatibility path only for a demonstrated public, persisted, deployed, or external consumer.
7. Update directly affected tests and documentation to describe current behavior, not removed compatibility seams.
8. Inspect each diff for accidental churn, formatting noise, behavior changes, and unrelated edits.
9. Run focused validation after each coherent change and fix failures before continuing.

Do not replace removed complexity with compatibility shims, aliases, silent fallbacks, TODOs, broad exception handling, suppressions, hidden assumptions, or another abstraction layer.

## Preserve behavior

- Before a structural rewrite that existing coverage cannot establish, add the smallest behavior pin — a characterization test, snapshot, or equivalence check — and keep it green through the move.
- Preserve supported runtime behavior and public interfaces unless the user explicitly authorizes a change.
- Never delete or weaken tests just to make validation pass. Remove tests only when they exclusively exercise code proven dead; retain or add coverage for the surviving behavior.
- Keep security, authentication, authorization, input validation, resource bounds, error semantics, data integrity, and concurrency behavior intact.
- Do not discard, overwrite, stage, commit, or reformat unrelated user changes.
- Prefer the simplest design that remains robust. Do not remove necessary validation, error handling, resource cleanup, or concurrency safeguards merely to flatten code.
- Do not chase line-count reduction at the expense of clarity. A smaller design matters more than compressed syntax.

## Validate completion

Run all validation relevant to the affected scope, including the repository's existing local CI command when available:

- focused and full tests
- formatter and lint checks
- type checks and language-server diagnostics
- build/package checks
- application, CLI, rendering, or generated-artifact smoke checks
- stale-reference searches for deleted files and symbols
- final diff and working-tree audit

If credentials, services, hardware, network access, or a product decision prevent required validation, stop without claiming completion. Report what was attempted, the exact blocker, the unverified requirements, and the input needed.

## Report

Finish with:

- structural simplifications and ownership changes
- files removed, merged, or retained despite review
- dead, duplicated, or overcomplex behavior removed
- behavior-preservation and validation evidence
- exact diff statistics: lines added, lines removed, and net change
- scope file count and line count before and after
- any intentionally untouched user changes or unavailable live checks

Keep working while a safe, evidence-backed cleanup or required verification step remains. Mark a long-running goal complete only after mapping every requirement to fresh evidence.
