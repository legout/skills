# Setup, maintenance and retrieval evaluation

## Initialize only the intended bundle

```bash
uv run <skill-dir>/scripts/sb.py --vault knowledge init
```

`init` creates missing folders, `schema.md` and indexes, and prints a project AGENTS.md hook. It does not rewrite an existing owner schema or migrate existing documents. Global commands omit `--vault knowledge` to honor `SECOND_BRAIN_DIR` or `~/second-brain/`. Do not silently create global knowledge when a requested project bundle is missing.

New bundles use `_raw/` for explicitly preserved acquired originals; existing local sources are referenced in place, not copied. Legacy `raw/` directories remain unchanged. Both archives, including Markdown assets and their subdirectories, are excluded from knowledge indexes; initialization and rebuilding do not migrate originals or rewrite old archive links.

`index.md` contains navigation, `log.md` records changes and `.history/` preserves prior maintained-page bytes. Keep human-curated text outside generated index blocks; prefer current maintained pages as entry points. `index.db` is generated FTS5 and can be rebuilt from Markdown.

New atomic notes use `notes/YYYY-MM-DD/slug.md`. Indexing creates navigation for day folders and continues to include legacy flat notes. Initialization and rebuilding do not relocate existing notes or change their links.

## Structural checks are not compilation

Run the requested checks in the selected bundle:

```bash
uv run <skill-dir>/scripts/sb.py --vault knowledge lint
uv run <skill-dir>/scripts/sb.py --vault knowledge orphans
uv run <skill-dir>/scripts/sb.py --vault knowledge dedup
uv run <skill-dir>/scripts/sb.py --vault knowledge stats
```

`lint` checks links, unsupported wikilinks, missing types, index/FTS drift, lifecycle status on notes and maintained pages, and stale metadata. It does not establish readability, source support or semantic integration. `orphans` reports missing inbound links, not a verdict that a page needs a new relationship. `dedup` reports similarity candidates, not permission to delete.

A read-only request does not authorize `index`, `lint --fix`, metadata repair or synthesis. When authorized, `lint --fix` repairs only generated indexes/FTS, not broken links or contradictory claims. After authorized manual edits run `index` and then `lint`.

For content maintenance, inspect unsupported claims, unresolved source-to-page integration, disagreements and outdated syntheses. Recheck changeable facts such as ownership, pricing or APIs against evidence. Missing evidence does not prove a claim false. Propose changes before writing when the user's exploration contract requires approval. `codegraph` remains an optional generated `topics/code-graph.md` artifact, not a default maintenance action.

## Evaluate actual retrieval questions

Only with owner approval, keep JSONL cases outside the vault: one real question `q` and at least one acceptable bundle-relative Markdown path in `gold` per line.

```jsonl
{"q":"research agents","gold":["concepts/research-agents.md"]}
```

Use the same FTS5-compatible terms as `search`. Rebuild an index after manual edits only when authorized; then run:

```bash
uv run <skill-dir>/scripts/sb.py --vault knowledge eval /path/to/cases.jsonl
```

`eval` is read-only. It reports each first acceptable gold rank, recall@1/3/5/10 and MRR@10 using `search`'s ranking and deprecated filter. Any acceptable gold page counts. A miss may concern the query, chosen gold pages, sources or index, not necessarily missing knowledge.

Scores measure retrieval of those pages, not claim correctness or integration quality. Temporary `selftest` fixtures verify mechanics, not real-world model compliance. Do not invent cases, reindex a real vault or claim improved retrieval without approval and measured evidence.
