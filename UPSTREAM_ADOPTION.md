# Upstream skill adoption review

This review compares the requested skills from `davidondrej/skills`, `mattpocock/skills`, and `obra/superpowers`, then assigns one local owner to each workflow transition. Pins and file-level mappings are in [`sources.json`](sources.json).

## Selection method

- Enumerated each repository at a fixed commit and read every named skill plus referenced companion files.
- Searched the public registry with `npx --yes skills find` by capability, not only by skill name.
- Preferred canonical authors over translations and mirrors.
- Used install counts as directional adoption evidence, not a quality guarantee.
- Preferred runtime fit, safety, and non-overlap over popularity.

Registry counts below are the archival snapshot returned by `npx --yes skills find` on 2026-09-04. They are directional evidence, not live statistics. Obra was dominant for brainstorming, worktrees, debugging, and completion verification; Matt Pocock was dominant for TDD, grilling, architecture review, and general research.

| Capability | Canonical candidate | Snapshot installs | Notable alternative |
| --- | ---: | ---: | --- |
| Debugging | `obra/superpowers@systematic-debugging` | 247.5K | `addyosmani/agent-skills@debugging-and-error-recovery` 30.3K |
| TDD | `mattpocock/skills@tdd` | 836.3K | `affaan-m/ecc@tdd-workflow` 10.4K |
| Brainstorming | `obra/superpowers@brainstorming` | 350.8K | Anthropic `product-brainstorming` 4.9K |
| Worktrees | `obra/superpowers@using-git-worktrees` | 181.5K | `ce-worktree` 2.6K |
| Architecture | `mattpocock/skills@improve-codebase-architecture` | 864K | `architecture-patterns` 21.6K |
| Grilling | `mattpocock/skills@grilling` | 621.4K | small aliases and translations |
| Verification | `obra/superpowers@verification-before-completion` | 199.7K | `verification-loop` 8.9K |
| General research | `mattpocock/skills@research` | 441.8K | backend-specific Firecrawl/Parallel/Tavily skills |

## Workflow architecture

```text
architecture survey ─┐
project vision ──────┼─> shape-design ──> write-implementation-plan
                    │        | spike               |
                    │        v                     v
                    └── prototype-question   orchestrate-implementation
                                             |
                                             v
                                      merge-worktree

unexpected failure -> systematic-debugging
completion claim   -> verification-before-completion
```

No standalone skill may compete with `orchestrate-implementation` for worker or worktree lifecycle, or with `merge-worktree` for integration and cleanup.

## David Ondrej requests

Source pin: `davidondrej/skills@11dee2ebc2d045806b686ba0b57746f1e3d7e331`.

| Requested skill | Decision | Destination and rationale |
| --- | --- | --- |
| `herdr` | Merge | `terminal-session-control`; retain the `HERDR_ENV` guard, caller-context discovery, read-before-send, and native waits. Remove unsafe auto-approval, invented session targeting, and personal model advice. Canonical Herdr is also cited. |
| `bb-cli` | Reject | A fast-moving privileged product manual should come from BB's installed CLI skill and live `bb help`, not a small third-party snapshot. It would also overlap orchestration. |
| `cmux` | Merge | `terminal-session-control`; retain explicit live target discovery, read-before-send, focus preservation, and live-help authority. Omit browser cookies, personal settings, topology mutation, and socket internals. Canonical cmux is reference-only because its source is GPL. |
| `git-worktree` | Merge | Safety and bootstrap rules move into `orchestrate-implementation`; no second worktree creator. |
| `pi-custom-model` | Adapt | Retain the narrow Pi-specific registration workflow and companion manual-invocation metadata, but replace static provider, fallback, schema, and restart claims with installed-version discovery and a verify-before-default gate. |
| `global-agent-guardrails` | Defer | Cross-runtime enforcement would require real adapters, installation logic, explicit fail modes, and end-to-end tests. Prose alone must not imply protection. |
| `deep-research` | Defer | The requested skill depends on DeepAPI. More popular alternatives are backend-specific and require an explicit spend, privacy, and provider decision. |
| `brain-to-docs` | Adapt | `capture-project-vision`; retain the interview loop and vision/decision separation while discovering local documentation conventions and requiring approval before writes. |
| `save-idea` | Reject | Personal home-directory taxonomy plus automatic commit/push authority is not portable. |
| `stop-overthinking` | Reject | A personal response-style shortcut, not an independent reusable capability. |

## Matt Pocock requests

Source pin: `mattpocock/skills@3cca18b368ae95cdbdebbff572ccafa662551015`.

| Requested skill | Decision | Destination and rationale |
| --- | --- | --- |
| `grill-me` | Reject alias | Alias-only wrapper; its target behavior is merged into `shape-design`. |
| `grilling` | Merge | `shape-design`; retain dependency-frontier questioning, recommendations, and fact/decision separation. |
| `grill-with-docs` | Reject alias | Composition wrapper; `shape-design` directly owns domain and documentation effects. |
| `writing-for-agents` | Merge | `agent-md-refactor`; retain context pointers, information hierarchy, completion criteria, environment-as-source, and pruning. |
| `wait-what` | Reject | Personal manual re-pitch shortcut with an unestablished ASD/context convention. |
| `diagnosing-bugs` | Merge | `systematic-debugging`; its tight red-capable loop, minimization, ranked hypotheses, redaction, and cleanup strengthen Obra's canonical base. |
| `domain-modeling` | Merge | `shape-design`; retain ambiguity challenges, concrete scenarios, glossary updates, and the strict ADR threshold without fixed paths. |
| `improve-codebase-architecture` | Adapt | `review-codebase-architecture`; keep hotspot selection, deletion test, and ranking, but make the skill report-only. |
| `prototype` | Adapt | `prototype-question`; preserve one-question logic/UI branches and durable verdict, while keeping artifacts explicitly disposable. |
| `tdd` | Merge | `orchestrate-implementation`'s `new-test` obligation; retain public seams, independent expected values, boundary mocks, and vertical red/green slices without creating another implementation router. |

## Obra/Superpowers requests

Source pin: `obra/superpowers@b36e0829c6d0140e93cfef2ca599b1b07d4a7797`.

| Requested skill | Decision | Destination and rationale |
| --- | --- | --- |
| `brainstorming` | Merge | Canonical base for `shape-design`; retain spike/bounded/architectural classification, scaled artifacts, approval gate, alternatives, and self-review. |
| `finish-a-development-branch` | Correct and merge | Upstream name is `finishing-a-development-branch`; landing choice, base confirmation, safe discard, and ownership-aware cleanup move into `merge-worktree`. |
| `using-git-worktrees` | Correct name and merge fragments | Isolation detection and baseline safeguards move into `orchestrate-implementation`. Manual worktree creation remains subordinate to Pi's managed worktrees. |
| `writing-plans` | Adapt | `write-implementation-plan`; retain file/responsibility maps, task contracts, test cycles, and self-review with neutral project paths. |
| `verification-before-completion` | Direct vendor | Canonical, self-contained evidence-before-claim gate. |
| `triage` | Reject | No `triage` skill exists in the reviewed Obra pin. Matt's tracker-specific triage was inspected but requires repository label/setup conventions not present here. |
| `systematic-debugging` | Merge | Canonical base for the sole debugging skill, enriched with Matt's stronger feedback-loop requirements. |

## Alternatives not adopted

- Mirrors, translations, and clone copies lose to canonical Obra and Matt sources.
- `ce-worktree` conflicts with managed-worktree ownership.
- `verification-loop` and `local-action-verification` duplicate the selected verification primitive.
- `debugging-and-error-recovery` duplicates the selected debugging owner.
- Anthropic's `product-brainstorming` is authoritative but duplicates the more adopted Obra workflow.
- `architecture-patterns` and Anthropic's `architecture` overlap the selected Matt-derived survey.
- Notion/Obsidian capture skills target external stores, not repository vision capture.
- Firecrawl, Parallel, Tavily, and other deep-research packages remain candidates only after provider, spend, and privacy requirements are chosen.

## Documentation skills

| Capability | Decision | Local owner |
| --- | --- | --- |
| Documentation structure and quality | Adapt | `documentation-writer`, based on `github/awesome-copilot@documentation-writer` at `7b1ebe6333397841ca918dec904d24d4695fe953` |
| Collaborative document creation | Adapt | `doc-coauthoring`, based on `anthropics/skills@doc-coauthoring` at `41bbe19d1a1a7eaab5e7bb9050a417e5c6cffc8f` |

`documentation-writer` owns Diátaxis classification and quality constraints. `doc-coauthoring` consumes that classification and owns context gathering, iterative drafting, and independent-reader testing for substantial documents. The local versions add conditional Python/Zensical checks and API/library grounding. The Anthropic source does not state a license for `doc-coauthoring`; its local version independently implements the workflow idea without redistributing upstream wording.

## Additional catalog adoption

`modern-python` was added concurrently from Trail of Bits' canonical `trailofbits/skills` package at `d3323cefbcf645678b8dc481de204b02ad3d02dc`. A 2026-09-04 `npx --yes skills find "modern python"` snapshot ranked it first at 7.3K installs, ahead of the broader `python-pro` (888) and `poetry-uv-advisor` (169) alternatives. The canonical, focused source was preferred over mirrors and broader Python advisors.

The complete 14-file package is tracked as adapted under CC-BY-SA-4.0. Local changes preserve Zensical support while adding installed-CLI discovery, migration parity and cleanup approval gates, current uv audit/lock guidance, explicit documentation-stack preservation, and a handoff to `make-release` for publication.

## Requested expansion

The installed `~/.agents/skills` packages were checked before adoption. Support files are kept when the skill depends on them; frontmatter is normalized for this catalog's validator.

| Request | Decision | Local owner |
| --- | --- | --- |
| Chrome CDP | Adapt | `chrome-cdp`, from `pasky/chrome-cdp-skill@ffea76a24b0471663ddd9d9f24335bbc442b6266` |
| Matt Pocock architecture improvement | Merge | `review-codebase-architecture` owns the read-only review and optional HTML report; selected candidates route to `shape-design` |
| Codebase simplification / overcomplexity removal | Keep two distinct scopes | `deslop` is the Cursor-derived broad cleanup workflow; `simplify-code` is the local completion-boundary diff pass |
| AI-writing cleanup | Merge | `humanizer` owns the rewrite workflow and a shared pattern catalog incorporates the useful Cursor-derived plain-speech checks |
| Marimo notebooks | Adapt | `marimo-notebook` (the requested “marimo-notebooks” package) and `marimo-pair` |
| Recent community research | Adapt | `last30days`, including its engine, references, and runtime assets |
| Architecture HTML diagrams | Adapt | `archify`, including renderer, schemas, examples, and validation assets |
| Draw.io diagrams | Adapt | `drawio-skill` (the installed package's canonical name), including scripts, references, styles, and shape data |
| Excalidraw diagrams | Adapt | `excalidraw`, including its helper and schema reference |
| Skill improvement from transcripts | Add local material | `improve-skill`, including its session extractor |

The visual report from the requested architecture package is now an optional reference under `review-codebase-architecture`; design interrogation routes to `shape-design` instead of duplicating it. The requested `deslop` URL resolves to Cursor's `cursor-team-kit/skills/deslop`; useful material from `pstack/skills/unslop` is merged into `humanizer`. `codebase-deslop` was removed because it duplicated `deslop` exactly. `simplify-code` remains the distinct recent-diff simplifier copied from the installed Pi skill set.

Trigger either cleanup workflow only on an explicit user request or as one model-offered pass at the completion boundary before commit, PR, or handoff. Do not run either on every edit, documentation-only work, generated artifacts, or mechanical changes.

## Cursor pstack `poteto-mode` review

Source pin: `cursor/plugins@93b00b89ef425a9c1bac0d0b317dfc49c930ac99`, `pstack/skills/poteto-mode`.

`poteto-mode` is a 45-file Cursor-specific package with 23 playbooks, a mandatory todolist ritual, fixed per-role models, a `poteto-agent` subagent wrapper, and autopilot/babysit/shipping orchestration. It was evaluated in full and **not adopted as a standalone owner**: vendoring it would add a second dispatcher competing with `orchestrate-implementation`, `shape-design`, and the cleanup pair. Selected portable principles were distributed to the existing canonical owners instead:

| Local owner | Materially used upstream files |
| --- | --- |
| `simplify-code` | `poteto-mode/SKILL.md`, `playbooks/refactoring.md`, `playbooks/opening-a-pr.md` |
| `deslop` | `poteto-mode/SKILL.md`, `playbooks/refactoring.md` |
| `verification-before-completion` | `poteto-mode/SKILL.md` |
| `systematic-debugging` | `playbooks/bug-fix.md`, `playbooks/perf-issue.md` |
| `shape-design` | `poteto-mode/SKILL.md`, `playbooks/feature.md` |
| `prototype-question` | `playbooks/prototype.md` |
| `write-implementation-plan` | `poteto-mode/SKILL.md`, `playbooks/multi-phase-plan.md` |
| `orchestrate-implementation` | `poteto-mode/SKILL.md`, `playbooks/orchestrate.md`, `playbooks/feature.md` |
| `effective-agent-skills` | `poteto-mode/SKILL.md`, `playbooks/authoring-a-skill.md` |
| `improve-skill` | `poteto-mode/SKILL.md`, `playbooks/eval.md` |

The `AGENTS.md` completion-boundary routing (offer `simplify-code` once; widen to `deslop` only when findings show broader systemic scope and the user accepts) adapts the package's deslop-before-commit habit. It has no `sources.json` relationship because the provenance validator requires a skill owner; this note records that routing adaptation.

**Adopted:** narrating- and phase-label comment cleanup with non-obvious-why retention; reader-load evidence; smallest behavior pins before risky rewrites; subtraction-first cleanup with earn-your-place structure; behavior-change separation; migrate-callers-then-delete-legacy sequencing with compatibility only for demonstrated consumers; same-surface verification with concrete surface examples and compilation-proves-compilation; evidence-traced fixes with speculative-guard rejection, disproven-hypothesis reverts, and baseline-plus-after performance measurement; conditional data-shape, boundary, idempotency, and shared-state analysis; observable-uncertainty routing to prototypes without displacing user-owned decisions; runnable-check task sequencing with removal conditions; smallest safe decomposition with shared-write separation and parent-owned review of child diffs; bounded child context; recurring-correction executable enforcement with pre-change/post-change comparison.

**Rejected:** the `poteto-mode` skill, `poteto-agent`, and all 23 playbooks as units; mandatory todolists and principle-citation rituals; fixed per-role model assignments; mandatory subagents and design exploration for every function boundary; a custom tool for every non-trivial task; automatic PR creation, always-ready PR policy, and `gh`/Origin/Graphite forge machinery; blanket external-action authority ("use any MCP tool", "never block on the human") overriding this catalog's approval gates; mandatory multi-prototype comparisons for routine work; `control-cli`/`control-ui` control skills; babysit, autopilot, hillclimb, and shipping orchestration; swarm/arena/interrogate fan-out; global punctuation and prose-style rules; the `/goal`-armed program skeleton and audit ticks. The catalog's static assertions in `tests/skills_test.sh` already serve the encode-lessons-in-structure role without a plan-format checker script.

## Safety and licensing decisions

- Runtime CLI help is authoritative for BB, Herdr, cmux, and Pi.
- `terminal-session-control` interacts only with explicitly identified existing targets in the caller's Herdr session or cmux workspace and never launches agents or uses permission-bypass flags.
- The canonical cmux repository is GPL-3.0-or-later. It is cited as factual authority only; no cmux source text is copied.
- All copied or materially adapted MIT content has an in-skill source block, a `sources.json` relationship, and a notice in `THIRD_PARTY_NOTICES.md`.
