# Poteto principles integration plan

## Goal

Integrate the highest-value, portable principles from Cursor pstack's `poteto-mode` into the existing canonical skills without adding `poteto-mode`, duplicating workflow ownership, or importing Cursor-specific orchestration.

## Source specification

- User-approved scope from the 2026-09-04 conversation: distribute selected Poteto principles across existing skills.
- Upstream source: `cursor/plugins` at commit `93b00b89ef425a9c1bac0d0b317dfc49c930ac99`.
- Durable adoption decision: `UPSTREAM_ADOPTION.md` will be updated in Task 6.

## Architecture summary

Keep the current owners and strengthen them in place:

- `simplify-code` owns cleanup of settled changed code.
- `deslop` owns explicit broad codebase cleanup.
- `verification-before-completion` owns proof before completion, commit, or PR.
- `systematic-debugging` owns evidence-driven bug and performance diagnosis.
- `shape-design` owns design and domain-shape decisions.
- `prototype-question` owns disposable empirical experiments.
- `write-implementation-plan` owns executable task decomposition.
- `orchestrate-implementation` owns delegated execution and shared-write coordination.
- `effective-agent-skills` and `improve-skill` own durable agent-instruction improvements.
- `AGENTS.md` owns only completion-boundary routing, not implementation detail.

No new dispatcher or workflow owner is introduced.

## Constraints and non-goals

- Preserve one canonical owner per workflow transition.
- Do not vendor the 45-file `poteto-mode` package, its scripts, `poteto-agent`, or its 23 playbooks.
- Do not add mandatory subagents, fixed models, mandatory todo lists, automatic PR creation, blanket external-action authority, or global punctuation rules.
- Do not require architecture review for every function boundary, a custom tool for every non-trivial task, or multiple prototypes for routine work.
- Keep `simplify-code` and `deslop` distinct. Do not run both automatically.
- Preserve explicit approval gates for product decisions, publication, destructive actions, deployment, and remote integration.
- Preserve unrelated working-tree changes. The repository is already undergoing a category-layout migration on `main`; never restore old flat paths or clean untracked files.
- Adapt ideas into the catalog's concise voice. Do not copy large upstream sections verbatim.

## Runtime assumptions

- Bash and Python 3 are available.
- Network access is required only for the pinned source checker.
- The catalog remains under `skills/<category>/<skill>/SKILL.md`.
- `sources.json` version 2 remains the authoritative file-level provenance manifest.

## Acceptance criteria

- [ ] No `poteto-mode` skill or competing dispatcher is added.
- [ ] `simplify-code` explicitly covers narrating comments, reader load, behavior pins, subtraction-first cleanup, and separation of behavior changes.
- [ ] `deslop` explicitly covers deletion-first broad cleanup, target structure, safe caller migration, legacy-path deletion, and behavior pins.
- [ ] `verification-before-completion` requires evidence from the same surface as the claim and rejects compilation or unit tests as proxies for unrelated runtime claims.
- [ ] `systematic-debugging` rejects speculative fixes and removes changes motivated by disproven hypotheses.
- [ ] `shape-design` applies domain modeling, boundary discipline, idempotency, and shared-state analysis only when the problem warrants them.
- [ ] `prototype-question` distinguishes empirically answerable uncertainty from product or preference decisions.
- [ ] `write-implementation-plan` requires verifiable units and complete internal migration cleanup.
- [ ] `orchestrate-implementation` preserves parent ownership, bounded context, smallest safe decomposition, and shared-write isolation.
- [ ] `effective-agent-skills` and `improve-skill` prefer executable enforcement when repeated prose instructions are insufficient.
- [ ] `AGENTS.md` offers `simplify-code` once at a completion boundary and escalates to `deslop` only when broader scope is explicitly accepted.
- [ ] Routing prompts preserve the distinction between `simplify-code`, `deslop`, debugging, design, and verification.
- [ ] Every materially adapted upstream relationship is recorded at the pinned commit in `sources.json` and `THIRD_PARTY_NOTICES.md`.
- [ ] Catalog, routing, Markdown-link, provenance, shell, and diff checks pass.

## Global validation

Run from the repository root:

```bash
bash -n tests/skills_test.sh
bash tests/skills_test.sh
bash scripts/check-skill-sources.sh
git diff --check
```

Also run `lens_diagnostics` in `all` mode for the edited Markdown, JSON, and shell files before completion.

## Task 0: Capture the baseline and protect the active migration

**Files:** no production changes.

**Prerequisites:** none.

**Test obligation:** `existing-check`. This task establishes the baseline and prevents unrelated cleanup.

- [ ] Record `git status --short`, the current branch, and the current category-layout paths.
- [ ] Confirm all target files exist under their current categorized paths.
- [ ] Run `bash -n tests/skills_test.sh`.
- [ ] Run `bash tests/skills_test.sh` and record any pre-existing failure without fixing unrelated work.
- [ ] Run `git diff --check`.
- [ ] Confirm the pinned upstream commit still resolves to `93b00b89ef425a9c1bac0d0b317dfc49c930ac99`.

**Expected evidence:** baseline commands and exit codes are recorded; no file outside this plan's scope is modified.

**Completion criterion:** the implementer can distinguish pre-existing migration changes from this integration.

## Task 1: Strengthen the two cleanup owners and their trigger boundary

**Files:**

- `skills/engineering/simplify-code/SKILL.md`
- `skills/engineering/deslop/SKILL.md`
- `AGENTS.md`
- `tests/routing_prompts.json`
- `tests/skills_test.sh`

**Upstream inputs:**

- `pstack/skills/poteto-mode/SKILL.md`
- `pstack/skills/poteto-mode/playbooks/refactoring.md`
- `pstack/skills/poteto-mode/playbooks/opening-a-pr.md`

**Behavior:**

- `simplify-code` keeps its Reuse, Quality, and Efficiency reviews; do not add a fourth reviewer.
- Extend Quality to flag narrating or phase-label comments while retaining comments that explain a non-obvious reason, invariant, compatibility constraint, or safety boundary.
- Add reader-load evidence: unnecessary layers, one-caller wrappers, hidden state, broad mutable scope, and scattered shape assumptions.
- Require the smallest behavior pin, characterization test, snapshot, or equivalence check before a risky structural rewrite when current coverage cannot establish preservation.
- Require discovered behavior changes to be split from the simplification rather than smuggled into it.
- Run a subtraction pass before proposing a replacement abstraction. A state machine, table, reducer, registry, or typed model is justified only when it removes branches, duplicated assumptions, or invalid states.
- `deslop` applies the same principles across a broad requested scope, with stronger reachability and migration requirements.
- For internal API replacement, migrate callers, verify them, delete the legacy path, and search for stale references in one cleanup. Preserve compatibility when a demonstrated public, persisted, deployed, or external consumer requires it.
- `AGENTS.md` remains a short router: offer `simplify-code` once for substantive settled code; suggest `deslop` only when findings show broader systemic scope and require acceptance before widening.
- Never chain both cleanup skills by default.

**Test obligation:** `new-test`.

- [ ] Add static contract assertions to `tests/skills_test.sh` for the concepts `non-obvious why`, `reader load`, `behavior pin`, `subtract`, and `legacy` in the correct owners.
- [ ] Add a positive `simplify-code` routing prompt for removing narrating comments from a completed diff.
- [ ] Add a negative `simplify-code` prompt for a repository-wide cleanup.
- [ ] Add a positive `deslop` prompt for broad caller migration and legacy-path removal.
- [ ] Add a negative `deslop` prompt for a small settled diff.
- [ ] Run `bash tests/skills_test.sh` before editing the skills and confirm the new assertions fail.
- [ ] Make the minimum skill edits.
- [ ] Rerun `bash tests/skills_test.sh` and confirm it passes.

**Completion criterion:** the cleanup skills are complementary, comments are handled inside cleanup rather than by a new skill, and scope escalation is explicit.

## Task 2: Strengthen proof and diagnosis

**Files:**

- `skills/workflow/verification-before-completion/SKILL.md`
- `skills/engineering/systematic-debugging/SKILL.md`
- `tests/routing_prompts.json`
- `tests/skills_test.sh`

**Upstream inputs:**

- `pstack/skills/poteto-mode/SKILL.md`
- `pstack/skills/poteto-mode/playbooks/bug-fix.md`
- `pstack/skills/poteto-mode/playbooks/perf-issue.md`

**Behavior:**

- Verification must exercise the same surface named by the completion claim.
- State explicitly that compilation proves compilation and a unit test proves only the behavior it exercises.
- Give concise examples: rendered UI for UI claims, built or installed CLI for CLI claims, restart-and-read for persistence, and transformed data plus stale-path checks for migrations.
- Preserve the existing requirements reread, exit-code inspection, diff inspection, and no-completion-claim gate.
- Debugging must trace shipped changes to observed evidence.
- A guard that might help is a hypothesis, not a fix.
- Remove production changes and instrumentation motivated only by disproven hypotheses.
- Performance work requires a baseline and the same measurement after the change.

**Test obligation:** `new-test`.

- [ ] Add static assertions for `same surface`, `compilation proves`, `disproven hypothesis`, and `baseline`.
- [ ] Add one verification positive prompt that distinguishes a runtime claim from a successful typecheck.
- [ ] Add one debugging negative prompt for speculative defensive hardening without reproduction.
- [ ] Run the catalog test and confirm the new assertions fail.
- [ ] Edit the two owners and rerun the test to green.

**Completion criterion:** completion evidence matches the claim, and debugging cannot ship speculative code.

## Task 3: Strengthen design and empirical-decision routing

**Files:**

- `skills/workflow/shape-design/SKILL.md`
- `skills/workflow/prototype-question/SKILL.md`
- `tests/routing_prompts.json`
- `tests/skills_test.sh`

**Upstream inputs:**

- `pstack/skills/poteto-mode/SKILL.md`
- `pstack/skills/poteto-mode/playbooks/feature.md`
- `pstack/skills/poteto-mode/playbooks/prototype.md`

**Behavior:**

- For stateful or branch-heavy work, name the data shape and the simplest organizing structure that removes repeated assumptions or illegal states.
- For new architectural requirements, describe the target as if the requirement had been foundational, then compare it with the minimum safe migration from current code.
- Validate external input at boundaries and keep trusted internal logic direct; do not duplicate boundary guards throughout the core.
- Address retries and idempotency for commands, jobs, migrations, and lifecycle operations when applicable.
- Try to remove shared mutation before adding locks or serialization.
- Route observable uncertainty to `prototype-question`: behavior, timing, layout, compatibility, output, or performance.
- Continue asking the user about product intent, preferences, acceptable trade-offs, and irreversible decisions.
- Compare multiple prototypes only when alternatives are genuinely viable; do not mandate them for routine work.

**Test obligation:** `new-test`.

- [ ] Add static assertions for `data shape`, `boundary`, `idempotent`, and `observable uncertainty`.
- [ ] Add a positive prototype prompt for measuring an empirical fork instead of asking the user.
- [ ] Add a negative prototype prompt for a product-preference decision requiring the user.
- [ ] Add a shape-design positive prompt involving scattered booleans and retry semantics.
- [ ] Run the catalog test red, make the edits, and rerun green.

**Completion criterion:** design rigor is conditional on actual complexity, and experiments answer facts without replacing user decisions.

## Task 4: Strengthen planning and orchestration

**Files:**

- `skills/workflow/write-implementation-plan/SKILL.md`
- `skills/workflow/orchestrate-implementation/SKILL.md`
- `tests/skills_test.sh`

**Upstream inputs:**

- `pstack/skills/poteto-mode/SKILL.md`
- `pstack/skills/poteto-mode/playbooks/multi-phase-plan.md`
- `pstack/skills/poteto-mode/playbooks/orchestrate.md`
- `pstack/skills/poteto-mode/playbooks/feature.md`

**Behavior:**

- Every implementation task ends with a runnable check and leaves the repository coherent.
- Internal migrations explicitly sequence replacement, caller migration, verification, legacy deletion, and stale-reference search.
- Transitional compatibility names its real consumer and removal condition.
- Plans identify blocking steps, independent workstreams, shared write targets, and the smallest safe decomposition.
- Orchestration separates shared write targets before resorting to serialization.
- One worker is preferred when work cannot decompose safely.
- The parent remains responsible for reviewing child diffs and producing the final conclusion.
- Large outputs and bulk exploration may be delegated, but children receive bounded file references and task contracts rather than accumulated conversation history.
- Preserve current mission, worktree, artifact, review, and publication-authority rules.

**Test obligation:** `new-test`.

- [ ] Add static assertions for `runnable check`, `removal condition`, `smallest safe decomposition`, and `review the diff`.
- [ ] Run the catalog test red.
- [ ] Make the minimum edits and rerun green.

**Completion criterion:** plans and delegated work remain verifiable without importing pstack's fixed agents, models, or autopilot machinery.

## Task 5: Turn repeated agent guidance into durable enforcement

**Files:**

- `skills/skill-authoring/effective-agent-skills/SKILL.md`
- `skills/skill-authoring/improve-skill/SKILL.md`
- `tests/routing_prompts.json`
- `tests/skills_test.sh`

**Upstream inputs:**

- `pstack/skills/poteto-mode/SKILL.md`
- `pstack/skills/poteto-mode/playbooks/eval.md`
- `pstack/skills/poteto-mode/playbooks/authoring-a-skill.md`

**Behavior:**

- When the same correction recurs, decide whether it belongs in concise prose, routing metadata, an evaluation, or executable enforcement.
- Prefer a lint rule, schema, metadata constraint, test, or script when prose alone repeatedly fails.
- Do not automate subjective preferences that still require judgment.
- Test description routing separately from workflow execution.
- Compare pre-change and post-change behavior before promoting a skill change.

**Test obligation:** `new-test`.

- [ ] Add static assertions for `executable enforcement`, `routing`, and `pre-change` or equivalent stable language.
- [ ] Add an `improve-skill` positive prompt for converting repeated session corrections into a tested guard.
- [ ] Add a negative prompt for a one-off preference that should not become infrastructure.
- [ ] Run the catalog test red, edit the owners, and rerun green.

**Completion criterion:** recurring lessons become proportionate, testable structure rather than prompt accumulation.

## Task 6: Record distributed adoption and file-level provenance

**Files:**

- `sources.json`
- `THIRD_PARTY_NOTICES.md`
- `UPSTREAM_ADOPTION.md`
- `README.md` only if its existing ownership summaries need clarification after implementation

**Prerequisites:** Tasks 1 through 5 complete.

**Behavior:**

- Record that `poteto-mode` was evaluated but not adopted as a standalone owner.
- Explain that selected principles were distributed to existing canonical owners.
- Add `adapted` relationships only for source files materially used by each local skill.
- Use repository `https://github.com/cursor/plugins`, branch `main`, commit `93b00b89ef425a9c1bac0d0b317dfc49c930ac99`, license `MIT`, and copyright `Copyright (c) 2026 Cursor`.
- Add multiple relationships to one local skill when distinct upstream playbooks materially shaped it.
- Do not add an `AGENTS.md` relationship because the current provenance validator requires a skill owner; document its routing adaptation in `UPSTREAM_ADOPTION.md` instead.
- Keep the existing `deslop` and `humanizer` Cursor relationships intact.

**Expected relationship map:**

- `simplify-code` from `poteto-mode/SKILL.md`, `playbooks/refactoring.md`, and `playbooks/opening-a-pr.md`.
- `deslop` from `poteto-mode/SKILL.md` and `playbooks/refactoring.md`.
- `verification-before-completion` from `poteto-mode/SKILL.md`.
- `systematic-debugging` from `playbooks/bug-fix.md` and `playbooks/perf-issue.md`.
- `shape-design` from `poteto-mode/SKILL.md` and `playbooks/feature.md`.
- `prototype-question` from `playbooks/prototype.md`.
- `write-implementation-plan` from `poteto-mode/SKILL.md` and `playbooks/multi-phase-plan.md`.
- `orchestrate-implementation` from `poteto-mode/SKILL.md`, `playbooks/orchestrate.md`, and `playbooks/feature.md`.
- `effective-agent-skills` from `poteto-mode/SKILL.md` and `playbooks/authoring-a-skill.md`.
- `improve-skill` from `poteto-mode/SKILL.md` and `playbooks/eval.md`.

**Test obligation:** `existing-check`. Provenance validation already exercises schema, pins, source existence, local ownership, and notices.

- [ ] Update `sources.json` without duplicate identities.
- [ ] Add the pinned repository and commit to each affected skill's attribution block or a concise shared attribution line that satisfies owner lookup.
- [ ] Update `THIRD_PARTY_NOTICES.md` with the distributed adaptation.
- [ ] Update `UPSTREAM_ADOPTION.md` with adopted and rejected parts.
- [ ] Run `python3 -m json.tool sources.json >/dev/null`.
- [ ] Run `bash tests/skills_test.sh`.
- [ ] Run `bash scripts/check-skill-sources.sh` and confirm every new source path resolves at the pinned commit.

**Completion criterion:** provenance is complete, pinned, non-duplicated, and validated.

## Task 7: Final integration verification

**Files:** all files changed by Tasks 1 through 6.

**Prerequisites:** Tasks 1 through 6 complete.

**Test obligation:** `existing-check` plus manual review.

- [ ] Run all global validation commands.
- [ ] Run `lens_diagnostics` in `all` mode on edited files.
- [ ] Search the catalog for `poteto-agent`, fixed pstack model names, mandatory automatic PR language, blanket external-action authority, and duplicate cleanup ownership; none should have been introduced.
- [ ] Search for stale references to the old flat skill paths; do not fix unrelated migration findings in this change.
- [ ] Review the final diff for copied prose, excessive instruction growth, contradictory triggers, and unrelated formatting churn.
- [ ] Confirm `simplify-code` remains the normal completion-boundary pass and `deslop` remains the explicit broad pass.
- [ ] Report changed files, rules adopted, rules rejected, validation evidence, and residual risks.

**Expected evidence:** all commands exit zero, diagnostics contain no blocking errors in edited files, and the final diff implements every acceptance criterion without a new skill.

**Completion criterion:** the plan's requirement matrix is fully satisfied and the result is ready for user review before commit or orchestration.

## Requirement mapping

- Cleanup comments and reader load: Task 1.
- Broad dead-code and structural cleanup: Task 1.
- Real-artifact verification: Task 2.
- Evidence-only fixes and measured performance: Task 2.
- Domain shape, boundaries, retries, and shared state: Task 3.
- Empirical uncertainty routing: Task 3.
- Verifiable task sequencing and migration cleanup: Task 4.
- Delegation ownership and context control: Task 4.
- Durable skill-learning enforcement: Task 5.
- Attribution and adoption record: Task 6.
- Trigger boundaries and final safety review: Tasks 1 and 7.

## Residual risks and manual checks

- Static routing fixtures prove catalog coverage, not model behavior. Manually review the positive and negative prompts for ambiguity.
- Repeating upstream principles across several skills can increase prompt size. Prefer one concise rule per owner and references to existing sections over new essays.
- `sources.json` may gain many relationships to the same upstream file. Add only material relationships and rely on the owning skill's attribution text.
- The active category-layout migration creates conflict risk. Execute against the categorized paths in this plan and preserve all pre-existing changes.
- Upstream pstack is Cursor-specific and fast-moving. Keep the pin fixed until a deliberate update review.
