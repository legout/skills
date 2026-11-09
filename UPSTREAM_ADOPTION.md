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
| Codebase simplification / overcomplexity removal | Consolidate | `deslop` owns proposal-first simplification and authorized edits for settled diffs, files, directories, and projects |
| AI-writing cleanup | Merge | `humanizer` owns the rewrite workflow and a shared pattern catalog incorporates the useful Cursor-derived plain-speech checks |
| Marimo notebooks | Adapt | `marimo-notebook` (the requested “marimo-notebooks” package) and `marimo-pair` |
| Recent community research | Adapt | `last30days`, including its engine, references, and runtime assets |
| Architecture HTML diagrams | Adapt | `archify`, including renderer, schemas, examples, and validation assets |
| Draw.io diagrams | Adapt | `drawio-skill` (the installed package's canonical name), including scripts, references, styles, and shape data |
| Excalidraw diagrams | Adapt | `excalidraw`, including its helper and schema reference |
| Skill improvement from transcripts | Add local material | `improve-skill`, including its session extractor |
| Active domain language and ADR maintenance | Adapt | `domain-modeling`, including its CONTEXT.md and ADR formats |
| Decision-tree stress testing | Merge wrappers | `grilling`; `grill-me` is its plain mode and `grill-with-docs` composes it with `domain-modeling` |
| Durable primary-source research | Adapt | `research`; `last30days` remains the separate recent-community owner |
| Working-preference mining | Adapt | `workflow-from-chats`; `improve-skill` remains the owner for one skill from a specific session |

The visual report from the requested architecture package is now an optional reference under `review-codebase-architecture`; design interrogation routes to `shape-design` instead of duplicating it. The requested `deslop` URL resolves to Cursor's `cursor-team-kit/skills/deslop`; useful material from `pstack/skills/unslop` is merged into `humanizer`. `codebase-deslop` was removed because it duplicated `deslop` exactly. The local recent-diff simplifier formerly shipped as `simplify-code` is now consolidated into `deslop`, including its Reuse/Quality/Efficiency perspectives and optional reviewer contract.

Use `deslop` on a cleanup request or after acceptance of one completion-boundary offer. The offer states the action and scope; proposal-only work does not authorize edits. Do not run it automatically on every edit, documentation-only work, generated artifacts, or mechanical changes.

### Cleanup consolidation — 2026-11-06

The owner approved one cleanup entrypoint: scope is an input, not a second skill. The default remains one bounded proposal pass; selected proposals or explicit direct-cleanup authority permit edits. Reuse, Quality, and Efficiency remain search perspectives, not mandatory reviewer jobs. Only an explicit request or project requirement with applicable delegation authority activates the optional review brief. Behavior preservation, independent expectations, deliberate structures, and approval gates remain binding.

The `simplify-code` invocation is retired without a wrapper. Update active callers and manually migrate installed copies; catalog edits do not authorize installation. This incompatible invocation change requires a minor release while the catalog is 0.x. Existing source pins remain unchanged and the old adaptations move to `deslop` and its review reference. Earlier plans and research retain their historical names with explicit supersession notes.

### Change-coupling analysis — 2026-11-09

Selectively adapt [`caldoai/skills`'s `untangle-codebase`](https://github.com/caldoai/skills/blob/f3cf47774975a7d9fca45730babf4ff7ad765ada/skills/untangle-codebase/SKILL.md) (MIT, Copyright (c) 2026 Maze) into existing owners, not a new skill. `deslop` gains hidden/needless coupling checks and groups related symptoms under a root-cause proposal; `review-codebase-architecture` examines scattered co-changing pieces, unnecessary coupling, and dependencies on volatile details. Actual callers and optional Git co-change history support analysis; history alone is not proof. Keep legitimate special cases and all existing scope, behavior-preservation, and approval gates. Do not adopt fix-everything authority, mandatory decision logs, special-case-count targets, or repeat-until-empty reviewer loops. Catalog-only changes do not authorize installation.

### Implicit lifecycle analysis — 2026-11-09

The owner supplied an X-post prompt about discovering implicit state machines and improving UX/DX/AX; its original author, URL, and popularity are unverified. The independently authored `review-codebase-architecture/references/state-lifecycles.md` turns that idea into scoped, evidence-backed lifecycle inspection and concrete trade-offs, not an all-three-always guarantee. The existing architecture-review entrypoint owns discovery and routes consequential redesigns through its unchanged approval handoff. No new skill, dependency, formal-check mandate, or change to `shape-design` or `deslop` is needed.

## Selective upstream refresh

Keep pins per file rather than replacing adapted packages wholesale. This pass adopts safer treatment of input text from `blader/humanizer` and marimo's cell-boundary and dataflow guidance from `marimo-team/marimo-pair`. It also records the existing local ADR-path edits as an adaptation, without overwriting them. The large script and asset changes in `last30days`, `archify`, and the relocated `Agents365-ai/365-skills` packages need separate reviews; their existing pins remain valid. Other upstream drift is not a reason to change catalog versions or discard local workflows. See `sources.json` for the exact file-level pins.

`bash scripts/check-skill-sources.sh` validates pinned source availability and
vendored hashes. A moved upstream branch is an informational warning by default,
not a pin-integrity failure. Use `--strict-upstream` for a deliberate freshness
audit. Review the emitted compare links and selectively update relationships only
when adopting changes; do not bump pins to make the warning disappear.

## Catalog-wide source review (2026-10-22)

Read the 43 skill entrypoints and relevant companion guidance, compared the content of all 503 pinned file relationships against their recorded branches across 16 repositories, and checked external documentation links. This is a source/instruction review, not an exhaustive runtime audit of every bundled script or an agent-behavior evaluation.

All 503 pinned sources were available and all six vendored hash pairs matched. At the original source paths, 190 relationships changed, 135 were unchanged, and 178 were absent at the current branch head. Those counts include multiple local adaptations of the same source file. Missing current paths do not invalidate historical pins:

- Draw.io moved to [Agents365-ai/drawio-skill](https://github.com/Agents365-ai/drawio-skill/tree/57270820d3cd71cbdf4fb6b2f7091d4fb37bb019/skills/drawio-skill). All 61 mapped files exist there; 40 have identical Git blob content and 21 differ. The [changelog](https://github.com/Agents365-ai/drawio-skill/blob/57270820d3cd71cbdf4fb6b2f7091d4fb37bb019/CHANGELOG.md) confirms retirement of marketplace distribution.
- Archify moved 88 of the 112 missing mapped paths out of `archify/` into the repository root; the other 24 were not found at that corresponding location. Its new diagram types and renderer changes require a coordinated package migration, not just a new `SKILL.md`.
- David Ondrej's Pi-model and vision-interview sources disappeared at their old paths; retain their available pins and local installed-version/approval contracts.
- Matt Pocock renamed `CONTEXT-FORMAT.md` to `GLOSSARY-FORMAT.md`; retain local project-configured context ownership rather than renaming users' documents.
- last30days removed `scripts/lib/reddit_rss.py` at the checked head and changed substantial engine/provider behavior. Retain the coherent existing package pending a scoped runtime upgrade.

### Disposition by local owner

| Skills | Decision |
| --- | --- |
| `effective-agent-skills` | Adopt concise front-loaded descriptions, discovery-budget awareness, actual-load evidence, and near-miss trigger tests. Remove unsupported routing percentages and universal restart claims. |
| `systematic-debugging` | Adopt proof that a deliberately injected red-state mutation actually landed. Keep local feedback-loop and evidence gates. |
| `terminal-session-control` | Refresh canonical Herdr factual guidance: retained identities can be backgrounded, waits do not prove background work finished, and failed waits must not trigger duplicate submissions. Do not add remote-machine management or topology authority. |
| `modern-python` | Adopt display metadata only; retain local migration safety and CC-BY-SA attribution. |
| `humanizer` | Adopt structural-pattern refinements and align the pattern catalog with the existing voice-preservation rule; no blanket dash ban or deletion of real three-part facts. |
| `document-to-markdown` | Clarify LiteParse placeholders versus extracted image assets and anydoc's whole-document hosted-OCR boundary; hosted OCR remains prohibited. |
| `drawio-skill` | Adopt selected geometry/render-verification guidance and cite the standalone source; retain bundled script pins. No new importers, MCP server, or runtime migration. |
| `archify`, `last30days` | Defer substantial runtime/asset upgrades; no claim that the bundled engines are current. |
| `domain-modeling`, `grilling`, `shape-design`, `write-implementation-plan`, `orchestrate-implementation`, `prototype-question`, `review-codebase-architecture` | Retain local artifact paths, workflow owners, scoped verification, approval gates, and report-only boundaries. Upstream filename changes, ticket defaults, broader delegation, and implementation authority are not portable updates. |
| `deslop`, `improve-skill`, `verification-before-completion` | Retain selected pstack principles and local guardrails. Do not import its expanded orchestration, mandatory rituals, or autonomy policy. |
| `handoff`, `excalidraw`, `marimo-pair` | Retain local adaptations: upstream prose/metadata changes do not justify invocation-policy changes; marimo cell-boundary/dataflow guidance is already in the local references. |
| `agent-md-refactor`, `project-verification`, `workflow-from-chats`, `chrome-cdp`, `marimo-notebook`, `research`, `merge-worktree`, `doc-coauthoring`, `documentation-writer` | Referenced source file content unchanged; no pin bump for unrelated repository commits. |
| `pi-custom-model`, `capture-project-vision` | Retain usable historical pins despite absent current paths. |
| `agent-guardrails`, `planning-contract`, `make-release`, `second-brain`, `document-extract`, `docx`, `pdf`, `pptx`, `xlsx` | Local owners with no imported-file relationship to update. Keep local contracts; review relevant cited documentation rather than inventing an upstream package. |

The Markdown URL inventory contained 145 distinct links: 62 fetched successfully, 52 immutable provenance links were classified separately, 18 were local/examples, 11 were illustrative citations or runtime endpoints, and two remained unverified after HTTP 403 responses ([ReportLab](https://docs.reportlab.com/reportlab/userguide/) and [OpenAI brand](https://openai.com/brand/)). A successful fetch proves reachability, not correctness of every claim or permission to upload data. Retain those blocked links rather than guessing replacements. Office/PDF, document-parser, Agent Skills, Codex, Diátaxis, wiki-format, and terminal/worktree documentation informed the selective review; external examples never override local permission gates.

Only adopted relationships advance in `sources.json`; this review does not install skills, update parser dependencies, rebuild real vaults, or authorize publication.

## Cursor pstack `poteto-mode` review

Source pin: `cursor/plugins@93b00b89ef425a9c1bac0d0b317dfc49c930ac99`, `pstack/skills/poteto-mode`.

`poteto-mode` is a 45-file Cursor-specific package with 23 playbooks, a mandatory todolist ritual, fixed per-role models, a `poteto-agent` subagent wrapper, and autopilot/babysit/shipping orchestration. It was evaluated in full and **not adopted as a standalone owner**: vendoring it would add a second dispatcher competing with `orchestrate-implementation`, `shape-design`, and the cleanup entrypoint. Selected portable principles were distributed to the existing canonical owners instead:

| Local owner | Materially used upstream files |
| --- | --- |
| `deslop` (including its optional review brief) | `poteto-mode/SKILL.md`, `playbooks/refactoring.md`, `playbooks/opening-a-pr.md` |
| `verification-before-completion` | `poteto-mode/SKILL.md` |
| `systematic-debugging` | `playbooks/bug-fix.md`, `playbooks/perf-issue.md` |
| `shape-design` | `poteto-mode/SKILL.md`, `playbooks/feature.md` |
| `prototype-question` | `playbooks/prototype.md` |
| `write-implementation-plan` | `poteto-mode/SKILL.md`, `playbooks/multi-phase-plan.md` |
| `orchestrate-implementation` | `poteto-mode/SKILL.md`, `playbooks/orchestrate.md`, `playbooks/feature.md` |
| `effective-agent-skills` | `poteto-mode/SKILL.md`, `playbooks/authoring-a-skill.md` |
| `improve-skill` | `poteto-mode/SKILL.md`, `playbooks/eval.md` |

The `AGENTS.md` completion-boundary routing (offer one scoped `deslop` pass; run only the accepted action and scope) adapts the package's deslop-before-commit habit. File-level relationships for skill-owned adaptations are recorded in `sources.json`; this note also records the repository-level routing adaptation.

**Adopted:** narrating- and phase-label comment cleanup with non-obvious-why retention; reader-load evidence; smallest behavior pins before risky rewrites; subtraction-first cleanup with earn-your-place structure; behavior-change separation; migrate-callers-then-delete-legacy sequencing with compatibility only for demonstrated consumers; same-surface verification with concrete surface examples and compilation-proves-compilation; evidence-traced fixes with speculative-guard rejection, disproven-hypothesis reverts, and baseline-plus-after performance measurement; conditional data-shape, boundary, idempotency, and shared-state analysis; observable-uncertainty routing to prototypes without displacing user-owned decisions; runnable-check task sequencing with removal conditions; smallest safe decomposition with shared-write separation and parent-owned review of child diffs; bounded child context; recurring-correction executable enforcement with pre-change/post-change comparison.

**Rejected:** the `poteto-mode` skill, `poteto-agent`, and all 23 playbooks as units; mandatory todolists and principle-citation rituals; fixed per-role model assignments; mandatory subagents and design exploration for every function boundary; a custom tool for every non-trivial task; automatic PR creation, always-ready PR policy, and `gh`/Origin/Graphite forge machinery; blanket external-action authority ("use any MCP tool", "never block on the human") overriding this catalog's approval gates; mandatory multi-prototype comparisons for routine work; `control-cli`/`control-ui` control skills; babysit, autopilot, hillclimb, and shipping orchestration; swarm/arena/interrogate fan-out; global punctuation and prose-style rules; the `/goal`-armed program skeleton and audit ticks. The catalog's static assertions in `tests/skills_test.sh` already serve the encode-lessons-in-structure role without a plan-format checker script.

## Cursor pstack verification-recipe review

Source pin: `cursor/plugins@f713f14203cd6420cec13cd7c55c32d598dbab68`, `pstack/skills/create-verification-skill` and `pstack/skills/maintain-verification-skill` (MIT, Copyright (c) 2026 Lauren Tan).

**Adopted:** the repository-interview-first generator discipline (documented startup, real user surface, preference for existing harnesses); the generated recipe shape — target identity, prerequisites and permissions, launch to a usable state with teardown, read-only readiness, concrete drive commands or selectors, evidence including side effects and persisted-state read-back, and cleanup of only owned resources; the one-journey bounded demonstration labeled draft/unproved when execution is not already authorized; and the doc-drift / harness-gap / product-regression split in maintenance, with regressions reported rather than masked. File-level mappings are recorded in `sources.json`; the notice is in `THIRD_PARTY_NOTICES.md`.

**Rejected as workflow defaults:** daily scheduled maintenance, verifier swarms, fresh per-PR shipping verification, full-feature-map audits, and any product-repair or execution authority derived from creating or maintaining a verifier. The new `project-verification` skill is a manual, explicitly invoked generator/maintainer of project-local `verify-<project>` recipes; whether a check is justified, its oracle, and its budget stay in `agent-guardrails`, and what evidence supports a completion claim stays in `verification-before-completion`.

## Cursor pstack formal-verification recipes

Source pin: `cursor/plugins@2776ddd2355d6d6c8747d3964600f28daf62f049`, `pstack/skills/create-formal-verification-skill` and `pstack/skills/maintain-formal-verification-skill` (MIT, Copyright (c) 2026 Lauren Tan).

**Adopted:** one explicit generator/maintainer, `project-formal-verification`, with one named property, independently grounded expectations, tool choice driven by the claim, real atomic boundaries, code/model correspondence, stated assumptions and bounds, one authorized negative control, and affected-diff maintenance. A model result is not automatically a code result; correspondence and a passing property are separate facts. Product violations remain findings, and property/scope changes require approved intent. Project-local recipes own concrete commands; planning and orchestration select them within existing validation units and evidence-reuse rules.

**Adapted:** create/update share one skill under `skill-authoring`; output uses portable `.agents/skills/verify-<project>-<area>`. Missing tools or authority yield an explicit draft/blocker, not installation or repair. Dirty changes, moved functions and new state writers invalidate correspondence when relevant. A negative control on a separate model demonstrates both the modeled violation and the source-change alignment check, not automatic code-regression coverage. Generator success and product correctness remain separate claims.

**Not adopted:** a new universal verification stage, repo-wide invariant audits, automatic dependency installation, mandatory `statechart`/Java/TLC/Pele tooling, routine reruns after identical merges, mutation campaigns, product repair, or publication authority. Runtime routing and a real formal-verification pilot remain unqualified until separately exercised; static catalog checks do not prove agent behavior.

The existing normal creator, maintainer and feature-map examples are unchanged between the prior `f713f14203cd6420cec13cd7c55c32d598dbab68` pin and this source snapshot. Their pins remain unchanged. The empirical recipe now makes isolation, stand-in setup gaps, dry-run side effects, readiness recovery and surviving cleanup evidence explicit, without changing its one-journey/menu policy. File-level provenance is in `sources.json`; the shared Lauren Tan notice is in `THIRD_PARTY_NOTICES.md`.

## Post-ADR artifact policy

An ADR explains why a durable decision was made; it is not a behavioral specification. Bounded changes proceed from an approved in-chat design directly to orchestration. Architectural or behavior-heavy changes get a written specification with observable acceptance examples, followed by the smallest executable plan. Tracker tickets are created only for established tracker workflows, explicit requests, or coordination that must outlive one run; the ticket set replaces rather than duplicates the implementation plan. Independent subsystems become separate plans or ticket groups instead of one oversized plan.

## Source refresh — 2026-11-09

Compared all 508 existing file relationships with the recorded branch heads across 17 repositories for the 44-skill catalog. At the original source paths, 135 relationships were content-identical, 198 differed, and 175 were absent. These are source comparisons, not 198 required local changes: adapted workflows may already incorporate the useful material. Historical pins remain valid when current paths disappear.

| Local owners | Disposition |
| --- | --- |
| `drawio-skill` | Selectively synchronized with standalone `Agents365-ai/drawio-skill@053600a8996159f256470dd49ac8d783e5fde588`. Migrated 60 existing relationships to the maintained repository and added the exact vendored `drawio_cli.py` helper. Retained the historical PR-bot reference and corrected its helper-copy requirement. |
| `grilling`, `research` | Adopted fresh-context child guidance from `mattpocock/skills@4ae2317ddb22b046e26455e4f9c9b3aaaf62212d`; `grilling` also words questions so yes accepts the recommendation. Existing artifact and approval gates remain. |
| `agent-md-refactor`, `chrome-cdp`, `doc-coauthoring`, `documentation-writer`, `marimo-notebook`, `merge-worktree`, `modern-python`, `project-formal-verification`, `project-verification`, `workflow-from-chats` | Mapped source content is unchanged; no pin bump for unrelated repository movement. |
| `deslop`, `domain-modeling`, `effective-agent-skills`, `excalidraw`, `handoff`, `humanizer`, `improve-skill`, `marimo-pair`, `orchestrate-implementation`, `prototype-question`, `review-codebase-architecture`, `shape-design`, `systematic-debugging`, `terminal-session-control`, `verification-before-completion`, `write-implementation-plan` | Retained local adaptations and historical relationships. Relevant changes include formatting/wording, glossary filename changes, invocation metadata, fixed models and expanded delegation/PR rituals; these do not supersede catalog workflow ownership or approval gates. Marimo's cell-boundary guidance and secret redaction in debugging are already present. |
| `capture-project-vision`, `pi-custom-model` | Current original paths are absent. Retained retrievable historical pins; no unrelated replacement. |
| `archify`, `last30days` | Runtime upgrades remain open, not synchronized; see below. |
| `agent-guardrails`, `document-extract`, `document-to-markdown`, `docx`, `land-changes`, `make-release`, `pdf`, `planning-contract`, `pptx`, `second-brain`, `xlsx` | Local owners without imported-file mappings; no upstream package to replace. This pass does not certify every external documentation claim. |

Draw.io adopts dotted/default-install CLI resolution (including Windows), structured validator findings, moved/rerouted diff classification, source provenance in code importers, SVG image embedding, icon URL validation, UTF-8 redirected explanations, file-handle fixes, SVG-text guidance and constrained style-preset paths. The narrow extractor/layout pipeline stays in place. New Diagram IR, `diagramctl`/MCP, importers and CI capabilities are intentionally not imported; the toolbox names only bundled tools. License remains MIT, with the existing notice retained. Changed files keep local adaptations; exact equality applies only to relationships marked `vendored`.

Open coordinated upgrades:

- **Archify:** head `11b0d6031853bdae89eed57e7979aabbf0034097` packages Archify 3.2.0, adds diagram types, moves tests/viewer build machinery outside the distributable subtree, and changes the package license from MIT to Apache-2.0 with MIT-covered portions/notices. A file-only merge would retain obsolete tests and miss package/build/license dependencies. The current coherent MIT snapshot is unchanged; no claim that its engine is current.
- **last30days:** head `de9bf7232b37a18df034b1165a45a41daadef7e2` is 3.32.0, changes 75 mapped files and removes `reddit_rss.py`. Its engine and the local setup/discovery/plan/output references must be upgraded together; merging only conflict-free scripts would break that contract. The existing coherent package is unchanged.

Verification for this selective refresh: the new local validator JSON regression failed before the update and passed afterward; 42 focused upstream tests passed against the actual local scripts (resolver, validator/geometry, icon host checks, importers, diff classification, redirected UTF-8 and SVG image embedding). The local Python importer → existing Graphviz autolayout → refreshed validator chain also passed with the expected dependency/provenance and zero structural errors. The catalog check validated 44 skills, and the source checker validated all 509 pinned paths and vendored hashes; retained branch drift remains informational. These are offline CLI/fixture checks, not desktop rendering, live provider research or agent-routing evaluations. No installation, dependency change, publication or catalog version bump is included.

## Safety and licensing decisions

- Runtime CLI help is authoritative for BB, Herdr, cmux, and Pi.
- `terminal-session-control` interacts only with explicitly identified existing targets in the caller's Herdr session or cmux workspace and never launches agents or uses permission-bypass flags.
- The canonical cmux repository is GPL-3.0-or-later. It is cited as factual authority only; no cmux source text is copied.
- All copied or materially adapted MIT content has an in-skill source block, a `sources.json` relationship, and a notice in `THIRD_PARTY_NOTICES.md`.
