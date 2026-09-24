---
name: second-brain
description: Persistent personal knowledge base ("second brain") as an Open Knowledge Format (OKF v0.2) markdown bundle with a SQLite FTS5 index — recall prior decisions, insights, failures and project facts before starting non-trivial work, and record atomic observations after meaningful results. Supersede (never silently rewrite) outdated claims. Use when starting a new task or project (check memory first), when learning something durable (a fix, a convention, a quirk, a decision), or when the user mentions their second brain, memory, knowledge base, or asks what was done/decided earlier.
---

# Second Brain — OKF v0.2 bundle + SQLite FTS5 index

A local-first knowledge bundle the agent and the human both own:
`~/second-brain/` (override: `SECOND_BRAIN_DIR` or `--vault`). Plain
Markdown + YAML frontmatter, compatible with the
[Open Knowledge Format v0.2](https://github.com/GoogleCloudPlatform/open-knowledge-format).

```text
~/second-brain/            # OKF bundle
├── index.md               # human-curated pointers + generated navigation (OKF reserved name)
├── log.md                 # update history: deprecations etc. (OKF reserved)
├── notes/                 # atomic concepts  YYYY-MM-DD-<slug>.md
├── topics/                # distilled topic pages (via retro)
├── personal/              # handwritten Markdown source notes; never rewrite on ingest
└── index.db               # SQLite FTS5 only; sb index rebuilds it independently of navigation
```

OKF mapping: every note is a *concept* with required `type:`; `status`,
`stale_after`, `generated`, `verified` follow OKF §5 (lifecycle/trust/
provenance). `sb.py` CLI (stdlib-only) in `scripts/`.

The knowledge graph is ordinary Markdown links plus `index.md` at the root
and in each content directory. These and `index.db` are first-class, separate
views: Markdown indexes provide human navigation; `index.db` is used only for
FTS. Never use `[[wikilinks]]`.

## Recall — before any non-trivial task

1. Read the root `index.md` (curated orientation and generated folder map).
   Follow the relevant folder's `index.md` to browse local notes and links.
2. Search the FTS5 index (ranked, snippet, ms at personal scale):

```bash
uv run <skill-dir>/scripts/sb.py search "<terms>" -n 5        # FTS5: "uv AND workspace"
uv run <skill-dir>/scripts/sb.py --vault ./knowledge search x # project bundle (OKF, git-tracked)
```

3. No index / no hit → grep: `rg -il "<terms>" <vault>`
4. Open only the 1–3 best hits. **No match → proceed; don't stall.**

Search hides `status: deprecated` concepts by default (`--all` shows them,
with history via `log.md`) and marks stale ones (`[STALE]` when
`stale_after` has passed). Trust them accordingly: unverified <
`generated` by agent < machine verification < `verified` by `human:*`.
Search surfaces these as `machine-verified` or `human-verified`; record a
review via `sb verify <path> --by human:<id>`.

## Record — one atomic concept per durable fact

```bash
uv run <skill-dir>/scripts/sb.py add "UV workspace gotcha" \
  -t failure -g "python, uv" -r high --body-file /path/to/body.md \
  --related notes/2026-01-01-uv-workspace.md  # replace with an existing search hit
```

Writes OKF frontmatter (`type`, `generated: {by: second-brain/1.0, at: …}`,
an occasional `sb index` (warns about OKF violations).
optional `status: draft`), normalizes Markdown, writes explicit related/source
links, and rebuilds directory indexes plus FTS. `--body` remains supported;
`--body-file -` reads multiline Markdown from stdin. Plain prose is wrapped;
headings, lists, tables, links, and fenced code are preserved. Unclosed code
fences are rejected before the note is written.

Rules: one fact per note; title = noun phrase; keep specifics (paths,
commands, errors); record failures with root cause; never secrets. Search for
related notes first, then pass each real relationship with repeatable
`--related PATH`; do not invent edges or rely on title/tag auto-matching.
Handwritten Markdown belongs in `personal/`, not `notes/`; it needs no `type:`.
Run `sb index` after manual edits. Generated index blocks are marked and
replaced by the CLI; human-written text outside those blocks is preserved.

## Claims carefully — updates are supersessions, not rewrites

Factual knowledge must never be silently mutated. When a claim changes:

```bash
sb add "UV workspace final" -t decision --supersedes notes/2026-01-01-uv-workspace-gotcha.md -b "…"
```

This marks the old concept `status: deprecated` (stays readable for
history/links), links successor ↔ predecessor, appends a `log.md` entry,
and search stops surfacing the outdated claim. For soft edits (typos,
adding sources) edit in place and bump `generated.at`. Set
`stale_after: <ISO-instant>` on time-sensitive claims so recall flags
them as `[STALE]` instead of asserting them. After human review:
`sb verify notes/<new>.md --by human:<id>` (OKF §5.3 trust tier).

## CLI-Übersicht (`scripts/sb.py`, stdlib-only)

```text
init                OKF-Bundle anlegen + AGENTS.md-Hook ausgeben (Projekt-Bootstrap)
index | rebuild     directory index.md files + index.db (FTS only) rebuild
search Q [-n N] [--all]   gerankte Volltextsuche; deprecated versteckt, [STALE] markiert
add "Titel" [-t T] [-g tags] [-r rel] [-b body | --body-file FILE]
                    [--related PATH]... [--supersedes notes/alt.md] [--source URL]...
                    formatted OKF concept + explicit standard Markdown links
idea "Text"         Quick-Capture als draft-insight
verify <pfad> [--by human:ich]  Verifikation vermerken (OKF §5.3 → human-reviewed)
lint [--fix]        broken links, unsupported wikilinks, index/FTS drift + health
                    --fix rebuilds generated directory indexes and FTS only; notes are never rewritten
orphans             concepts without semantic Markdown inbound links (indexes excluded)
dedup [-t 0.75]     Near-Duplicate-Paare (Body-Shingle-Jaccard; Lösung: superseden)
codegraph [--root .]  Symbol-/Import-Karte via ast-grep -> topics/code-graph.md
stats / selftest    Statistik / Round-Trip-Checks
```

`codegraph` nutzt ast-grep (`ast-grep`/`sg`, `npm i -g @ast-grep/cli`), mappt
python + ts/js (defs/classes/imports) und listet projektinterne Imports als
Inline-Pfade (keine Links — Ziele liegen ausserhalb des Bundles) —
erzeugt ein regenerierbares `type: code-graph` Konzept.

## OpenCode-Commands (im Paket: `commands/`)

| Command | Wirkung |
|---|---|
| `/sb [query]` | Recall: Projekt-Bundle zuerst, dann global; zitiert Konzept-Dateien |
| `/remember [fakt]` | atomares Konzept anlegen (Routing project/global, supersede bei Updates) |
| `/session [fokus]` | aktuelle Session sichern: 1–5 dauerhafte Ergebnisse als Konzepte |
| `/ingest [dateien]` | Dokumente (pdf/docx/pptx/xlsx/md) zu Quell-Konzepten destillieren |
| `/research [thema]` | Deep-Web-Recherche -> draft-Konzept mit `--source`-Belegen |
| `/dream` | Health-Report (lint/orphans/dedup/stats) + Vorschläge, nur nach Bestätigung anwenden |

## Workflows (Agent-Protokolle)

- **Ingest:** Only ingest personal notes when the user asks. Read originals in
  `personal/` without moving or editing them; distill each durable fact into a
  `reference` concept with `--source file://personal/<file>.md` (the CLI adds
  a Markdown source link when the file is inside the bundle). Search first and
  add other real relationships with `--related`; avoid duplicating facts.
  For external PDF/DOCX/PPTX/XLSX sources, use the matching document skill,
  preserve the original source reference, and create formatted concepts.
- **Research:** Teilfragen -> multi-Winkel-Recherche -> nur belegte Aussagen,
  Widersprüche explizit -> EIN `reference`-Konzept als draft mit `--source`-URLs.
- **Dream (periodisch):** `lint`/`orphans`/`dedup`/`stats` -> Vorschläge
  (Topics distillieren, Orphans verknüpfen, Duplikate superseden, Drafts
  promovieren, Stale verifizieren) -> nur Genehmigtes anwenden -> `sb idea`-Log.

## Retro — distill, don't accumulate

When 5+ notes cluster around one topic, write `topics/<topic>.md`
(distilled page with standard Markdown links to the notes and current best
practice), deprecate notes it fully replaces. `sb index` updates every
directory catalog; keep any human-curated root pointers outside the generated block.

## Setup — "setup my project second brain"

When asked to set up a project second brain, the agent does exactly this:

```bash
uv run <skill-dir>/scripts/sb.py --vault knowledge init
```

`init` creates the OKF bundle (`notes/`, `topics/`, `personal/`, root and
per-directory `index.md` files, `log.md`, and FTS-only `index.db`), and
**prints the ready-made AGENTS.md hook block** (with the
absolute script path filled in). Append that block to the project's
`AGENTS.md`, commit, done. Optionally record the first concepts right away.

**Global second brain** needs no setup step: `~/second-brain/` is created
automatically by the first `sb add`/`sb index`, and the recall hook lives in
the global `~/.config/opencode/AGENTS.md` (installed by the setup package —
or add the same four lines manually).

**Routing rule** (which brain gets a fact):
- Project-specific (schemas, decisions, quirks of *this* repo) → project bundle `knowledge/`
- Cross-project durable facts (tool habits, recurring failures, preferences) → concepts in `~/second-brain/notes/`
- Handwritten source documents → `personal/` in the relevant bundle (`~/second-brain/personal/` for global notes)
- Distilled concepts from personal documents → `notes/`, only when ingestion is requested
- Unsure → record in the project bundle; promote to global during retro
  (and supersede the project note with a link).

## Hook into a project's AGENTS.md

Per-project knowledge = an OKF bundle inside the repo (git-tracked —
OKF's recommended distribution). Add to the project's `AGENTS.md`:

```markdown
## Second Brain (project knowledge)
- Project knowledge lives in `knowledge/` (OKF v0.2 bundle, git-tracked).
- Before non-trivial tasks: `uv run ~/.agents/skills/second-brain/scripts/sb.py --vault knowledge search "<terms>"` (fallback: rg).
- Record durable facts: `… sb.py --vault knowledge add "Title" -t decision -g tags --related notes/related.md` (never secrets; search for links first).
- Never silently rewrite claims — supersede: `… add "New" --supersedes notes/old.md` (path relative to the bundle); respect status/stale_after on recall.
- Handwritten Markdown belongs in `knowledge/personal/`; ingest it only when asked, preserving the original and linking each distilled reference note to its source.
- `index.md` files are generated navigation with preserved human text outside markers; `index.db` is FTS-only. Run `sb index` after manual edits and `sb lint` to audit links/drift.
```

Personal cross-project memory stays in `~/second-brain/` (hooked via the
global `~/.config/opencode/AGENTS.md`).
