# Persistence and compilation workflows

Use these patterns for normal persistence and when maintaining host-specific shortcuts. The CLI does not synthesize prose or install slash commands; `page` writes the complete body authored by the agent. An explicitly narrower user or command contract still wins.

## Choose the operation

- **Remember a finding:** search first. Update the relevant maintained page when the finding changes reusable knowledge. Add a dated note only when a distinct decision, event or original observation deserves its own history. A confirmation of unchanged knowledge needs neither a duplicate note nor a cosmetic page revision.
- **Save a session:** extract at most 3–5 durable outcomes, not a turn-by-turn diary. Reuse existing captures. Compile related outcomes into the affected pages; several notes may support one page. Leave genuine open questions as `idea` drafts.
- **Ingest a source:** read it with the appropriate document/web tool, preserve a labeled capture and original when applicable, compare against the wiki, then compile supported findings. One source does not automatically require a new topic or a page in every folder.
- **Compile existing captures:** read current and superseded versions as evidence/history, identify the current supported claims and update their owning pages. Cite original evidence; do not treat another agent's synthesis as independent corroboration.
- **Explore connections:** propose evidence-grounded links, possible topics or gaps. Ask for approval where the exploration contract requires it; do not equate a proposed connection with confirmed knowledge.
- **Capture only / one research draft:** write only the requested capture and state the integration deferral. Open questions are not established facts. **Read-only lint** stays read-only and performs no synthesis.

For host shortcuts such as `/sb-remember`, `/sb-session` and `/sb-ingest`, document both capture and compilation when their scope is normal persistence. If a shortcut explicitly authorizes only one note or asks to propose changes before writing, preserve that boundary. A separate compile shortcut may implement the compile-existing-captures pattern, but this repository does not install it or modify existing host configuration.

## Routing examples

- A field mapping or accepted schema belongs in `references/data-schema.md`; an original decision note may remain its evidence.
- A reusable distinction belongs in `concepts/`, a concrete tracked device in `entities/`, an analysis procedure in `playbooks/`, and the cross-source project picture in `topics/`.
- A bounded investigation or unresolved question stays in `notes/`. Do not create an entity for every inventory row or copy a whole session into a topic.

Folder roles are separate from OKF `type`. `add -t reference` creates a dated note, not a maintained reference page. Use `page reference`, `page concept`, `page entity`, `page topic` or `page playbook` for maintained knowledge. Do not invent `syntheses/` or another `skills/` folder inside the wiki.

`add` and `idea` create `notes/YYYY-MM-DD/slug.md`, using the local creation day. A same-day title collision or a reserved filename (`index.md`, `log.md`, `schema.md`) gets a numbered suffix without overwriting earlier captures or navigation. The title itself is unchanged. Existing `notes/YYYY-MM-DD-slug.md` files remain supported and are not moved; migration requires explicit authorization.

## Capture only when it adds evidence

Commands below target project knowledge. Omit `--vault knowledge` for global knowledge. Paths supplied to `--related` must already exist inside the selected bundle; examples are placeholders, not files to manufacture.

```bash
uv run <skill-dir>/scripts/sb.py --vault knowledge add "Accepted decision" -t decision \
  --body-file /path/to/decision.md --related sources/existing-evidence.md
uv run <skill-dir>/scripts/sb.py --vault knowledge idea "Which ownership mapping is still unknown?"
```

The first command preserves an event; it does not complete ordinary wiki integration. The second deliberately preserves an unresolved `draft insight`.

## Compile a complete supported page

Choose its owner, preserve valid claims and citations, and submit the complete current body. `--related` records graph edges but is not a substitute for citations beside material claims.

```bash
uv run <skill-dir>/scripts/sb.py --vault knowledge page reference "Data schema" \
  --body-file /path/to/complete-schema.md --related notes/YYYY-MM-DD/existing-decision.md
```

For an existing page, read it and calculate its current hash first:

```bash
shasum -a 256 knowledge/references/data-schema.md
uv run <skill-dir>/scripts/sb.py --vault knowledge page reference "Data schema" \
  --body-file /path/to/complete-schema.md --related notes/YYYY-MM-DD/existing-decision.md \
  --expect-sha256 <current-hash> --reason "Confirmed field mapping"
```

Retain the full existing source/related set alongside new evidence. Keep uncertainty and disagreements visible; `page` defaults to `draft`. Compilation is not verification or automatic promotion to `stable`.

## Finish at a meaningful boundary

Compile after an accepted topic block or session rather than after every tool call. Keep historical notes in place; only superseded claims become deprecated. Curate the hot index toward the current maintained pages and check meaning, links and sources.

The final response separates:

- **Captures:** new or reused evidence and notes, with paths.
- **Compiled pages:** created or revised maintained pages and their scope.
- **Deferrals/open questions:** what was deliberately not compiled, why, and its intended owner when known.

Legitimate deferrals include explicit capture-only scope, insufficient evidence or an unresolved contradiction. Routine lack of a `page` call is not successful integration. Do not add a synthetic session-report note merely to document that the other notes were written.
