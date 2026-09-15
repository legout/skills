---
name: simplify-code
description: Simplify settled recently changed code without behavior change. Use on explicit request or before PR or handoff; use deslop for broad cleanup.
---

Use when the user requests simplification, or when the model offers one completion-boundary pass before commit, PR, or handoff. Do not run automatically on every edit.

> Narrating-comment, reader-load, behavior-pin, and subtraction-first cleanup principles are adapted from Cursor's [`poteto-mode`](https://github.com/cursor/plugins/tree/93b00b89ef425a9c1bac0d0b317dfc49c930ac99/pstack/skills/poteto-mode) at commit `93b00b89ef425a9c1bac0d0b317dfc49c930ac99` (MIT, Copyright (c) 2026 Cursor).

# Simplify Code

Refine a settled change without altering behavior. Three reviewers — **Reuse**, **Quality**, **Efficiency** — examine the same scope from different angles; you disposition their findings against approved scope, apply only accepted fixes, and verify. Zero findings is success, not a reason to keep searching.

The premise is **exact functionality preservation**. Never relax assertions, weaken type signatures, or skip tests to make checks pass. Never simplify away a safety check — input validation at trust boundaries, data-loss-preventing error handling, security checks, and accessibility affordances stay even when a finding frames them as removable boilerplate.

## When to use / skip

Use: a feature is finished and settling, before PR/commit/handoff, or on AI-generated code that works but feels heavy (its highest-yield use).

Skip: mechanical diffs (formatting, dependency bumps, lint autofixes, generated artifacts); tiny diffs (a couple of lines — review overhead exceeds yield); code the user asked to keep as written.

## 1. Resolve the scope

Priority order — **user-named scope is authoritative and never widened**:

1. Explicit argument: file path, or a description ("the changes I made to X") — resolve descriptions to concrete files before proceeding.
2. Branch diff vs base: detect the base (`git merge-base HEAD origin/main` or the repo's default branch), then `git diff <base>...HEAD`.
3. Staged + unstaged work: `git diff HEAD`.
4. Files recently edited in this conversation.
5. Neither yields a non-empty scope → **ask rather than guess**.

**Self-guard:** if the resolved scope contains no substantive code — docs/Markdown-only, generated, vendored, lockfile, or purely mechanical churn — stop with a short "nothing to simplify" note instead of dispatching reviewers. On a mixed diff, narrow to the code files.

## 2. Capture the diff

Run the diff command once and keep the output plus the changed-file list. This is the exact input all three reviewers receive — do not hand them a description of the diff, hand them the command (and file list) so they can reproduce and expand context themselves.

## 3. Dispatch three reviewers in parallel

Run three reviewers in parallel when the `simplify-reviewer` agent is available. Otherwise run the same three axis briefs sequentially yourself or with available read-only reviewers. One axis per review; never combine them. Each prompt must include:

- The diff command and changed-file list from step 2 (or the user-named scope).
- The axis brief below, pasted in full — the reviewer has no other access to it.
- The output contract from the subagent definition (one line per finding, confidence tag, under 400 words).
- The complete contract below, with the approved simplification criteria, named written conventions (or none found), and real callers/input provenance/environment filled in. Do not rely on the reviewer loading an instruction file. The axis brief is a search lens, not permission to turn preferences into findings.

<!-- reviewer-contract:start -->
```text
Review <base>..<head or exact user scope> against <approved simplification criteria and behavior-preservation constraints>.
Written conventions: <named sources and relevant rules, or none found>.
Real use: <callers, input provenance, environment, touched boundaries>.
Priority: agreed feature, then correctness, then proven risk. Project written conventions are binding; violations are must-fix. Unwritten taste never blocks.
Report only a violation of a named requirement or written rule that this change caused or worsened, reachable through real callers, inputs, and environment, with material impact and a proportionate response. Cite the rule, changed location, scenario, impact, and response. For explicit cleanup, name the authorized cleanup criterion and demonstrate the concrete duplication/cost; the criterion does not authorize behavior changes.
Security activates only for touched boundaries: untrusted or external input (files, queries, network), credentials, auth, dependency changes. Require a named asset, realistic attacker, and an attack path through real use. Stories requiring stolen secrets, broken TLS, malicious admins, or generic extra hardening are not findings. No boundary touched: write "security: n/a". Security facts missing: mark the criterion unverified; never invent a threat model. Trusted internal callers and user-owned local files are not hostile by default; written safety guarantees still bind.
Test requests are findings too: name a reachable real scenario or drop them. Coverage percentage is not a reason.
Large or out-of-scope fixes: one line with the owner decision needed, not an automatic fix-first item. Unrelated issues: one line max, non-blocking. Do not fix, dispatch workers, or start re-reviews; the parent dispositions findings before repair.
Finish when agreed criteria, real risks, and written rules are covered; zero findings is success. Verdict: pass or fix-first (small in-scope repairs), with any unverified criterion or required human decision explicitly stated. A pass does not clear those decisions or authorize acceptance/publication. Then stop.
```
<!-- reviewer-contract:end -->

**Reuse brief:** Search the repo for existing utilities and helpers the new code duplicates. Flag: new functions that near-duplicate existing ones (cite the existing implementation — no citation, no finding); inline logic that could use an existing utility; diff code that reimplements a language standard-library or runtime primitive (only when behavior-equivalent — exclude UX-changing swaps); code that hand-maintains a guarantee the platform, framework, or a downstream layer already provides.

**Quality brief:** Flag: redundant state; parameter sprawl; copy-paste with slight variation (check the duplicated construct can actually be eliminated before proposing a merge); leaky abstractions; stringly-typed values where an enum/union/branded type already exists; unnecessary single-use wrappers; reader load — extra layers between a reader's question and its answer, hidden state, mutable scope broader than the behavior needs, and the same shape assumption restated across the diff instead of named once; deeply nested conditionals that flatten with early returns; comments that restate WHAT well-named code already says, and narrating or phase-label comments that caption the code underneath — keep a comment only when it explains a non-obvious why: a reason, invariant, compatibility constraint, or safety boundary the code cannot show; dead code — unused imports, unreferenced exports, unreachable paths; context-bound vocabulary — names that only make sense if you followed the conversation; pre-release compatibility scaffolding (aliases, fallback shapes) for superseded forms of *this unshipped change* — only when no deployed, persisted, public, external, or dependent-branch consumer exists.

**Efficiency brief:** Flag: redundant computations and repeat reads; sequential independent operations that could run concurrently; hot-path bloat; recurring no-op updates (state writes without change detection); TOCTOU pre-checks; obvious memory issues; overly broad operations (fetching/mutating more than needed).

## 4. Aggregate and apply fixes

Read all three reports. Then, as orchestrator:

- **Dedupe** overlapping findings across axes.
- **Disposition before repair:** reject any failed gate in one line; authorize and apply small in-scope fixes only after checking all gates; hand a large/out-of-scope repair to the human with one sentence. An unverified material criterion requires an answer, not invented certainty. Raw reviewer output is not a work order.
- **Honor structure pins:** if the user, a plan, or project docs marked a structural decision as deliberate (an intentional duplication, a deliberate wrapper), it stays. A settled decision isn't collapsed just because it looks reducible in isolation.
- **Pin risky structure:** before reshaping behavior-bearing code that current coverage cannot prove preserved, add the smallest behavior pin — a characterization test, snapshot, or equivalence check — and keep it green through the move.
- **Split behavior changes out:** a discovered bug or missing behavior is its own change; a simplification that smuggles in a behavior change loses its safety net.
- **Subtract before replacing:** run a subtraction pass before proposing a replacement abstraction. Add a state machine, table, reducer, registry, or typed model only when it removes branches, duplicated assumptions, or invalid states; otherwise keep the boring local shape.
- Prefer the smallest edit that resolves the finding. Do not introduce new abstractions to fix duplication unless the shared shape is real.

## 5. Verify behavior preservation

Discover the project's check commands from its config (`package.json` scripts, `Makefile`, CI config, `pyproject.toml`, etc.):

Run required repository checks and the smallest focused check proving behavior preservation. Name the real scenario each added check covers; no coverage targets or full-project typecheck/lint matrix unless project policy or the changed seam requires it. Broaden only for a distinct reachable risk (for example an affected consumer of a heavily-imported utility).

On failure: fix the underlying break the simplification introduced, or **revert that specific simplification**. Never relax assertions, weaken type signatures, or skip tests to make checks pass. Surface any remaining failure with the check name and relevant output. One fix pass, one delta recheck, then ask the human; no third round. If a reviewer recheck is needed, only the parent starts it, pastes the full contract, and scopes it to the accepted fix and affected behavior, never the whole original change.

## 6. Summarize

Restate the approved task in one sentence, compare the result, and choose `accept / fix / hand back / ask` without restarting the correction limit. Extra ideas get one line, not code. End with a compact report:

- **What was good as-is** — brief.
- **What changed** — per fix: finding (axis), file, one-line description.
- **Skipped** — false positives and pinned structures, one line each.
- **Checks** — which ran, pass/fail.
- **Impact** — fixes applied per axis (reuse/quality/efficiency), net line change.
