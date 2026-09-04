# Skills

Reusable [Agent Skills](https://agentskills.io/) published by [legout](https://github.com/legout).

## Install

Install one skill:

```bash
npx skills add legout/skills --skill systematic-debugging --global --agent pi --yes --copy
```

Install the complete catalog:

```bash
npx skills add legout/skills --skill '*' --global --agent pi --yes --copy
```

The catalog uses nested categories; skill names and `/skill:<name>` commands remain unchanged.

## Catalog

### Engineering

- **`deslop`** — broad evidence-driven codebase cleanup.
- **`modern-python`** — uv, Ruff, and ty setup or migration.
- **`simplify-code`** — behavior-preserving cleanup of settled changed code.
- **`systematic-debugging`** — reproducible root-cause diagnosis.

### Skill authoring

- **`agent-md-refactor`** — concise agent instructions with scoped references.
- **`effective-agent-skills`** — Agent Skill authoring, review, and debugging.
- **`improve-skill`** — skill changes derived from agent-session evidence.

### Tools and research

- **`chrome-cdp`** — approved control of an existing local Chrome session.
- **`handoff`** — redacted handoff for a fresh agent session.
- **`last30days`** — recent social, community, video, GitHub, and web research.
- **`marimo-notebook`** — file-based marimo notebooks.
- **`marimo-pair`** — live marimo-kernel collaboration.
- **`pi-custom-model`** — explicit custom Pi model registration.
- **`terminal-session-control`** — explicit Herdr or cmux target interaction.

### Visualization

- **`archify`** — standalone interactive HTML diagrams.
- **`drawio-skill`** — precise editable draw.io diagrams.
- **`excalidraw`** — sketch-like editable Excalidraw diagrams.

### Workflow

- **`capture-project-vision`** — project vision and durable decisions.
- **`make-release`** — semver GitHub and optional PyPI releases.
- **`merge-worktree`** — worktree integration and cleanup.
- **`orchestrate-implementation`** — coordinated multi-task implementation.
- **`prototype-question`** — disposable code for one design question.
- **`review-codebase-architecture`** — read-only module and seam review.
- **`shape-design`** — approved bounded design before implementation.
- **`verification-before-completion`** — fresh evidence before success claims.
- **`write-implementation-plan`** — executable plans from approved requirements.

### Writing

- **`doc-coauthoring`** — collaborative document discovery and drafting.
- **`documentation-writer`** — Diátaxis software documentation.
- **`humanizer`** — fact-preserving natural-language rewrites.

## Boundaries

- `deslop` owns broad cleanup; `simplify-code` owns settled changed-code cleanup.
- `documentation-writer` owns document type and quality; `doc-coauthoring` owns collaborative drafting.
- `marimo-notebook` edits files; `marimo-pair` works through a live kernel.
- `effective-agent-skills` covers general authoring; `improve-skill` requires session evidence.
- `review-codebase-architecture` identifies candidates; `shape-design` settles one.
- `archify` produces interactive HTML, `drawio-skill` produces precise editable diagrams, and `excalidraw` produces sketch-like canvases.

## Workflow

```text
review architecture ─┐
capture vision ──────┴─> shape design -> write plan -> orchestrate -> merge
                           |     ^
                           v     |
                     prototype spike

unexpected failure -> systematic-debugging
completion claim   -> verification-before-completion
```

`orchestrate-implementation` expects `pi-subagents` and may use configured `pi-intercom` peers. `merge-worktree` PR mode expects an authenticated `gh` CLI. `make-release` composes with release, changelog, GitHub, commit, and uv tooling when available.

## Provenance

[`UPSTREAM_ADOPTION.md`](UPSTREAM_ADOPTION.md) records adoption decisions. [`sources.json`](sources.json) records pinned file-level provenance, and [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) carries applicable notices.

```bash
bash scripts/check-skill-sources.sh
```

## Development

```bash
bash -n tests/skills_test.sh scripts/check-skill-sources.sh
bash tests/skills_test.sh
bash scripts/check-skill-sources.sh
git diff --check
```

## License

Original material is [MIT](LICENSE). Adopted material remains under the licenses listed in [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).
