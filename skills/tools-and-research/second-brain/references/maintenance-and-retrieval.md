# Setup, maintenance and retrieval evaluation

## Initialize only the intended bundle

```bash
uv run <skill-dir>/scripts/sb.py --vault knowledge init
```

`init` creates missing folders, `schema.md` and indexes and prints a project AGENTS.md hook. It never rewrites an existing schema or migrates documents.

`index.md` is navigation, `log.md` the change log, `.history/` prior page bytes. Search also indexes frontmatter `aliases`; an older database needs one authorized `index` rebuild to pick them up (`lint` reports the drift). Search and `eval` never rebuild implicitly.

## Structural checks are not compilation

```bash
uv run <skill-dir>/scripts/sb.py --vault knowledge lint      # links, wikilinks, types, index/FTS drift, status, staleness
uv run <skill-dir>/scripts/sb.py --vault knowledge orphans   # missing inbound links, not a demand for new ones
uv run <skill-dir>/scripts/sb.py --vault knowledge dedup     # similarity candidates, not permission to delete
uv run <skill-dir>/scripts/sb.py --vault knowledge stats
```

None of these judge readability, source support or integration. A read-only request does not authorize `index`, `lint --fix`, metadata repair or synthesis. `lint --fix` rebuilds only generated indexes/FTS, never links or claims.

Content maintenance: look for unsupported claims, unintegrated sources, disagreements and outdated syntheses; recheck changeable facts (ownership, pricing, APIs) against evidence. Missing evidence does not prove a claim false. Propose before writing when the exploration contract requires approval. `codegraph` is optional, not a default step.

## Evaluate real retrieval questions

Only with owner approval: keep JSONL cases outside the vault, one real question and at least one acceptable bundle-relative path per line, using `search`'s FTS5 terms.

```jsonl
{"q":"research agents","gold":["concepts/research-agents.md"]}
```

```bash
uv run <skill-dir>/scripts/sb.py --vault knowledge eval /path/to/cases.jsonl
```

`eval` is read-only and reports first gold rank, recall@1/3/5/10 and MRR@10 with `search`'s ranking. A miss may lie in the query, gold choice, sources or index. Scores measure retrieval, not claim correctness; `selftest` checks mechanics, not model compliance. Never invent cases, reindex a real vault or claim improvement without approval and measurement.
