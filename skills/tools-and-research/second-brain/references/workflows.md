# Persistence and compilation workflows

The CLI does not synthesize prose or install slash commands; `page` writes the complete body the agent authored. A narrower user or command contract wins.

## Choose the operation

- **Remember a finding:** search first. Update the owning maintained page when reusable knowledge changes. Add a dated note only for a distinct decision, event or original observation. Unchanged knowledge needs no duplicate note or cosmetic revision.
- **Record a decision:** `add -t decision` with the decision, *Why*, *Trade-off* and *Revisit when* (the condition that would overturn it). A reversal is a new decision with `--supersedes`, never an edit of the old one.
- **Save a session:** extract at most 3–5 durable outcomes, not a diary. Reuse existing captures and compile related outcomes into the affected pages; several notes may support one page. Leave genuine open questions as `idea` drafts.
- **Ingest a source:** read it with the right document/web tool, compare against the wiki, then compile supported findings. Excerpts or summaries only where useful, not an archive copy per file ([capture details](capture-and-revisions.md)). One source does not require a new topic or a page in every folder.
- **Compile existing captures:** read current and superseded versions as history, identify the current supported claims and update their owning pages. Cite original evidence; another agent's synthesis is not independent corroboration.
- **Explore connections:** propose evidence-grounded links, topics or gaps. Ask for approval where the exploration contract requires it; a proposed connection is not confirmed knowledge.
- **Capture only / one research draft:** write only the requested capture and state the deferral. Open questions are not facts. **Read-only lint** performs no writes or synthesis.

Host shortcuts such as `/sb-remember`, `/sb-session` and `/sb-ingest` document both capture and compilation when their scope is normal persistence, and keep any narrower boundary (one note, propose-before-write). This repository does not install shortcuts or change host configuration.

## Routing

- A field mapping or accepted schema → `references/data-schema.md`; the original decision note may remain its evidence.
- A reusable distinction → `concepts/`; a concrete tracked device → `entities/`; an analysis procedure → `playbooks/`; the cross-source project picture → `topics/`.
- A bounded investigation or unresolved question stays in `notes/`. No entity per inventory row; no session copied into a topic.

`add -t reference` creates a dated note, not a maintained reference page; use `page reference|concept|entity|topic|playbook`. Do not invent `syntheses/` or a `skills/` folder inside the wiki.

## Commands

Examples target project knowledge; omit `--vault knowledge` for global. `--related` paths must already exist in the bundle.

```bash
# preserve an event (does not complete integration) / an open question as draft insight
uv run <skill-dir>/scripts/sb.py --vault knowledge add "Accepted decision" -t decision \
  --body-file /path/to/decision.md --related sources/existing-evidence.md
uv run <skill-dir>/scripts/sb.py --vault knowledge idea "Which ownership mapping is still unknown?"

# create a maintained page; revise it with the hash of the current file
uv run <skill-dir>/scripts/sb.py --vault knowledge page reference "Data schema" \
  --body-file /path/to/complete-schema.md --related notes/YYYY-MM-DD/existing-decision.md
shasum -a 256 knowledge/references/data-schema.md
uv run <skill-dir>/scripts/sb.py --vault knowledge page reference "Data schema" \
  --body-file /path/to/complete-schema.md --related notes/YYYY-MM-DD/existing-decision.md \
  --expect-sha256 <current-hash> --reason "Confirmed field mapping"
```

`--related` records graph edges; it does not replace citations beside material claims. `page` defaults to `draft`; compilation is not verification or promotion to `stable`. Give claims that can change (prices, APIs, versions, ownership) `--stale-after <ISO date>` on `add` or `page`; `lint` lists expired paths for rechecking. A revision with a new `--stale-after` replaces the old date.

## Project origin

`--origin-project` takes a stable lowercase project ID (works on `add`, `idea`, `capture`, `page`; repeatable). Reuse known IDs, never a path or URL; clarify an ambiguous identity instead of guessing from the working directory. Add a project only when its evidence contributes substantive knowledge. `page` revisions keep existing origins. A transferable finding from a project without a bundle goes global with its ID; project-only facts never fall back to global.

```bash
uv run <skill-dir>/scripts/sb.py page concept "Reusable concept" --origin-project featherbi \
  --body-file /path/to/complete-concept.md --related notes/YYYY-MM-DD/existing-evidence.md
```

## Finish at a meaningful boundary

Compile after an accepted topic block or session, not after every tool call. Historical notes stay; only superseded claims become deprecated. Point the hot index at current maintained pages and check meaning, links and sources.

Legitimate deferrals: explicit capture-only scope, insufficient evidence, an unresolved contradiction. Simply not calling `page` is not integration.
