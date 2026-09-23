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
├── index.md               # hot index: curated pointers (OKF reserved name)
├── log.md                 # update history: deprecations etc. (OKF reserved)
├── notes/                 # atomic concepts  YYYY-MM-DD-<slug>.md
├── topics/                # distilled topic pages (via retro)
└── index.db               # derived FTS5 index — delete anytime, sb index rebuilds
```

OKF mapping: every note is a *concept* with required `type:`; `status`,
`stale_after`, `generated`, `verified` follow OKF §5 (lifecycle/trust/
provenance). `sb.py` CLI (stdlib-only) in `scripts/`.

## Recall — before any non-trivial task

1. Read `index.md` (fast orientation, curated pointers).
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
  -t failure -g "python, uv" -r high -b "Fix: tool.uv.sources setzen."
```

Writes OKF frontmatter (`type`, `generated: {by: second-brain/1.0, at: …}`,
optional `status: draft`) + reindexes. Hand-written notes need `type:` +
an occasional `sb index` (warns about OKF violations).

Rules: one fact per note; title = noun phrase; keep specifics (paths,
commands, errors); record failures with root cause; never secrets;
update `index.md` pointers when a note is genuinely reusable.

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
index | rebuild     FTS5-Index (neu) aufbauen — index.db ist wegwerfbar
search Q [-n N] [--all]   gerankte Volltextsuche; deprecated versteckt, [STALE] markiert
add "Titel" [-t T] [-g tags] [-r rel] [-b body] [--status draft]
                    [--supersedes notes/alt.md] [--source URL]   OKF-Konzept anlegen (Typ frei, §4.1)
idea "Text"         Quick-Capture als draft-insight
verify <pfad> [--by human:ich]  Verifikation vermerken (OKF §5.3 → human-reviewed)
lint [--fix]        kaputte Links + Health-Report (drafts/deprecated/stale/ohne type)
orphans             Konzepte ohne Inbound-Links (Kandidaten für Verknüpfung)
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

- **Ingest:** Dokument mit passendem Skill lesen (pdf/docx/pptx/xlsx) -> pro
  dauerhaftem Fakt ein `reference`-Konzept mit `--source file://…` -> `sb index`.
  Wichtige Quelldokumente optional im Bundle spiegeln unter `references/`
  (OKF §6.3) — schuetzt gegen Pointer-Rot, wenn das Original wandert.
- **Research:** Teilfragen -> multi-Winkel-Recherche -> nur belegte Aussagen,
  Widersprüche explizit -> EIN `reference`-Konzept als draft mit `--source`-URLs.
- **Dream (periodisch):** `lint`/`orphans`/`dedup`/`stats` -> Vorschläge
  (Topics distillieren, Orphans verknüpfen, Duplikate superseden, Drafts
  promovieren, Stale verifizieren) -> nur Genehmigtes anwenden -> `sb idea`-Log.

## Retro — distill, don't accumulate

When 5+ notes cluster around one topic, write `topics/<topic>.md`
(distilled page, links the notes, states current best practice),
deprecate notes it fully replaces, point `index.md` at the topic page.

## Setup — "setup my project second brain"

When asked to set up a project second brain, the agent does exactly this:

```bash
uv run <skill-dir>/scripts/sb.py --vault knowledge init
```

`init` creates the OKF bundle (`notes/`, `topics/`, `index.md`, `log.md`),
indexes it and **prints the ready-made AGENTS.md hook block** (with the
absolute script path filled in). Append that block to the project's
`AGENTS.md`, commit, done. Optionally record the first concepts right away.

**Global second brain** needs no setup step: `~/second-brain/` is created
automatically by the first `sb add`/`sb index`, and the recall hook lives in
the global `~/.config/opencode/AGENTS.md` (installed by the setup package —
or add the same four lines manually).

**Routing rule** (which brain gets a fact):
- Project-specific (schemas, decisions, quirks of *this* repo) → project bundle `knowledge/`
- Cross-project / personal (tool habits, recurring failures, preferences) → `~/second-brain/`
- Unsure → record in the project bundle; promote to global during retro
  (and supersede the project note with a link).

## Hook into a project's AGENTS.md

Per-project knowledge = an OKF bundle inside the repo (git-tracked —
OKF's recommended distribution). Add to the project's `AGENTS.md`:

```markdown
## Second Brain (project knowledge)
- Project knowledge lives in `knowledge/` (OKF v0.2 bundle, git-tracked).
- Before non-trivial tasks: `uv run ~/.agents/skills/second-brain/scripts/sb.py --vault knowledge search "<terms>"` (fallback: rg).
- Record durable facts: `… sb.py --vault knowledge add "Title" -t decision -g tags` (never secrets).
- Never silently rewrite claims — supersede: `… add "New" --supersedes notes/old.md` (path relative to the bundle); respect status/stale_after on recall.
```

Personal cross-project memory stays in `~/second-brain/` (hooked via the
global `~/.config/opencode/AGENTS.md`).
