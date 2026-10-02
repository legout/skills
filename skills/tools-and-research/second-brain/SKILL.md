---
name: second-brain
description: Maintain a source-grounded Second Brain wiki and memory. Use for recall, durable findings, source ingestion, compiling captured notes, or wiki maintenance. Keeps capture history separate from maintained knowledge pages.
---

# Second Brain

Maintain a source-grounded [OKF v0.2](https://github.com/GoogleCloudPlatform/open-knowledge-format) wiki, following [Karpathy's LLM Wiki proposal](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f). The agent owns synthesis; the stdlib-only Python 3.10+ CLI handles file, history and index operations. Markdown is authoritative; `index.db` is rebuildable FTS5.

## Scope first

- Explicit user scope wins. Project knowledge belongs in the project's initialized `knowledge/`; personal and cross-project knowledge belongs in `SECOND_BRAIN_DIR` or `~/second-brain/`. If a requested project bundle is missing, offer `init`; never silently write globally.
- Run from the project root. **Every** project command puts `--vault knowledge` before the subcommand. Keep follow-up commands and bundle-relative `--related` / `--supersedes` paths in the same bundle.
- Read `schema.md`, the root index and relevant folder indexes. Preserve owner rules, existing paths and human-curated text outside generated index blocks. Initialization does not authorize reorganizing existing files.
- Resolve bundled paths from this skill's directory. Use `uv run <skill-dir>/scripts/sb.py --help` and subcommand help when arguments are unclear.

## Recall

Search project knowledge first unless the owner chose global only; search global if no relevant result. Use `rg` when an index or match is unavailable. Read the best 1–3 matches and follow their evidence, preferring relevant maintained pages over an event trail.

```bash
uv run <skill-dir>/scripts/sb.py --vault knowledge search "<terms>" -n 5
uv run <skill-dir>/scripts/sb.py search "<terms>" -n 5
```

Respect `draft`, `deprecated` and expired `stale_after`; source captures have no lifecycle `status`. `verified` is separate trust metadata and does not change status. Prefer human-verified claims, cite underlying evidence, distinguish general knowledge from vault findings, and state gaps rather than guessing.

## Capture and compile

**Capture is not integration.** Normal persistence ends with supported reusable outcomes integrated into maintained pages, or explicitly deferred with a reason and intended target. Honor narrower capture-only, one-note, open-question and read-only requests.

1. Search existing pages and route findings by role. `add` and `idea` always write to `notes/`; `page` selects the maintained folder. Folder roles and OKF types are separate.
2. Read supplied sources in place. Existing project files—including files under `data/`—stay in place and are referenced from `sources/`, not duplicated in `_raw/`. `--archive-original` explicitly preserves an eligible new asset that needs a managed home; `--original` alone only hashes/references it.
3. At a completed topic block or session, compare evidence and integrate supported findings into relevant maintained pages. Preserve capture history, uncertainty and disagreements; do not merely copy or move notes.
4. For page revisions, submit the complete page body and complete current source/related set with the current `--expect-sha256` and a `--reason`. Correct atomic claims with `--supersedes`, not silent rewrites.
5. Inspect meaning, sources and writing quality; run `index` after authorized manual edits and `lint` for structure.

New notes and source captures use `notes/YYYY-MM-DD/slug.md` and `sources/YYYY-MM-DD/slug.md`; captures keep the exact timestamp in `generated.at`. Existing flat notes and captures remain readable at their current paths; do not migrate them automatically. `_raw/` is only for newly acquired attachments/downloads needing a permanent home; legacy `raw/` remains supported.

For project-origin knowledge, record a known stable project ID with repeatable `--origin-project`; origin means where knowledge arose, not where it applies, and never changes vault routing. Read [workflow examples](references/workflows.md) when saving a session, remembering findings, ingesting sources or compiling existing captures. Read [capture and revision details](references/capture-and-revisions.md) before source capture or page/claim revision. Read [writing guidance](references/writing-quality.md) when authoring wiki prose, source summaries or reading views. For initialization, structural checks or retrieval evaluation, read [maintenance and retrieval](references/maintenance-and-retrieval.md).

## Completion contract

- Normal persistence: each supported reusable outcome is reflected in an appropriate maintained page, or explicitly deferred with its reason and intended target. A successful `add`, `capture`, `index` or clean `lint` is not proof of integration.
- Capture-only or open-question work: honor that boundary and name what remains uncompiled. Read-only maintenance never authorizes writes or synthesis.
- Preserve provenance and disagreements. Never store secrets, silently rewrite factual history, or promote uncertain claims merely because they were compiled.
- Report **captures**, **compiled pages**, and **deferrals/open questions** separately, including paths and meaningful source links. Do not create a separate session report as another layer of notes.
