# Verifikationsrezepte: konkreter Änderungsentwurf

**Status:** approved · **Revision:** 1 · **Datum:** 2026-11-06

**Auftrag:** Zunächst Änderungsentwurf; anschließend „Go ahead with the plan.“ in diesem Thread am 2026-11-06.

**Freigabe:** Revision 1, Katalogänderungen aus §§3–7 und deren bestehende Struktur-/Vertragsprüfungen. Produktpilot, Tool-Installation, Delegation, Commit und Veröffentlichung sind nicht enthalten; die praktische Qualifikation bleibt offen.

**Basis:** Katalog `55f04e9cb46cdb2bbe3e328b92a1b10507ddf010`; [Quellenanalyse](../research/2026-11-06-pstack-verification-and-formal-verification.md). Planning-contract v1; installierte Katalog-Provenienz `unknown`.

Die englischen Blöcke unten sind die freigegebenen Zieltexte im Sprachstil des Katalogs. Diese Spezifikation beschreibt Verhalten und Abnahme; die operative Fassung liegt nach Umsetzung in den benannten Skill-Dateien. Parallel entstandene Änderungen an AGENTS.md, README, Changelog und Cleanup-Skills sind nicht Teil dieses Auftrags und dürfen bei späterer Umsetzung nicht überschrieben werden.

## 1. Entscheidungsvorschlag

Ein neuer `project-formal-verification` unter `skills/skill-authoring/`, mit Create- und Update-Modus. Er erzeugt projektlokale Rezepte und pflegt ihre Codebindung. Der bestehende `project-verification` bleibt für empirische Benutzerwege zuständig. Planung und Orchestrierung konsumieren konkrete Projekt-Rezepte; sie rufen Generatoren nicht als automatische Verifikationsphase auf.

Alternativen:

- **Nur vorhandene Skills:** kleinster Umfang, lässt aber Modell-Code-Synchronisierung und formale Recipe-Pflege ohne zuständigen Skill.
- **Alles in `project-verification`:** kein neuer Name, aber formale Modellpflege würde jeden gewöhnlichen UI-/CLI-Rezeptauftrag mitladen und die Trigger verwischen.
- **Separater Generator — empfohlen:** zwei klar getrennte Rezeptfamilien; gemeinsame Policy bleibt in `agent-guardrails`, Abschlussaussagen in `verification-before-completion`.

### Im Umfang

- Bestehenden empirischen Generator und dessen Vorlage gezielt ergänzen.
- Einen formalen Generator plus eine direkt verlinkte Vorlage entwerfen.
- Vier Workflow-Skills punktuell präzisieren; bei Orchestrierung auch den vorhandenen Worker-Brief.
- Katalogeintrag, Abgrenzung, Adoption, Provenienz, Notice und Changelog mitführen.

### Nicht im Umfang

Keine Änderungen an `agent-guardrails`, `planning-contract`, `prototype-question`, Host-Adaptern oder Review-Verträgen. Keine neuen Runner, Modellchecker-Wrapper, Skripte, Scheduler, MCPs, automatischen Installationen, Verifier-Swarms, globalen Konfigurationsdateien oder obligatorischen neuen CI-Gates. Kein `statechart`-Import. Keine Migration bestehender Projekt-Rezepte. Keine neue Definition von Review-Häufigkeit oder Verifikations-Timing: `55f04e9` bleibt dafür maßgeblich.

## 2. Betroffene Dateien

| Datei | Vorgesehene Änderung |
| --- | --- |
| `skills/skill-authoring/project-formal-verification/SKILL.md` | Neu: ein expliziter Generator/Maintainer, Zieltext in §3. |
| `skills/skill-authoring/project-formal-verification/references/recipe-template.md` | Neu: konkrete Ausgabeform, §4. |
| `skills/skill-authoring/project-verification/SKILL.md` | Beschreibung abgrenzen; redundante Bestätigung entfernen; Demonstrationsabschluss präzisieren, §5. |
| `skills/skill-authoring/project-verification/references/recipe-template.md` | Isolation, Ersatzumgebung, Dry-run, Readiness und Beleg-Erhalt in vorhandenen Abschnitten, §5. |
| `skills/workflow/shape-design/SKILL.md` | Ein bedingter Verweis in `Design quality`, §6.1. |
| `skills/workflow/write-implementation-plan/SKILL.md` | Vorhandene Rezeptwahl und Evidenzkategorien präzisieren, §6.2. |
| `skills/workflow/orchestrate-implementation/SKILL.md` | Bestehenden Delivery-Abschnitt um zugewiesene formale Checks erweitern, §6.3. |
| `skills/workflow/orchestrate-implementation/references/manifest-and-briefs.md` | Bestehenden Worker-Brief Punkt 4 ergänzen, §6.3. |
| `skills/workflow/verification-before-completion/SKILL.md` | Beweisarten und Codebindung im bestehenden Evidenzabsatz, §6.4. |
| `README.md` | Neuer Generator; Zuständigkeiten und bedingte Nutzung, §7. |
| `UPSTREAM_ADOPTION.md` | Neue Formal-Adoption mit bewusst ausgeschlossenen Defaults, §7. |
| `sources.json` | File-level-Quellenbeziehungen, §7. |
| `THIRD_PARTY_NOTICES.md` | Formal-Adaption dem bestehenden pstack/MIT-Notice zuordnen, §7. |
| `CHANGELOG.md` | Eintrag unter Unreleased; keine Versionsänderung, §7. |

Das sind zwei neue Skill-Dateien, sieben anzupassende Skill-/Referenzdateien und fünf Katalog-Metadateien. Bestehende Absätze werden ersetzt oder knapp erweitert, nicht durch parallele Regelblöcke dupliziert. Kein zusätzlicher Implementierungsplan oder Ticket-Satz wird mit diesem Entwurf angelegt.

## 3. Neuer Skill: vorgeschlagener vollständiger Body

Ziel: `skills/skill-authoring/project-formal-verification/SKILL.md`.

```markdown
---
name: project-formal-verification
description: Create or update a project-local verification recipe for a named invariant, model check, or code-level proof. Use when explicitly asked to generate or maintain such a skill, or reconcile its model with changed code; not for ordinary runtime verification or a whole-repo audit.
---

# Project Formal Verification Recipes

> Adapted from Cursor pstack's [create-formal-verification-skill](https://github.com/cursor/plugins/blob/2776ddd2355d6d6c8747d3964600f28daf62f049/pstack/skills/create-formal-verification-skill/SKILL.md) and [maintain-formal-verification-skill](https://github.com/cursor/plugins/blob/2776ddd2355d6d6c8747d3964600f28daf62f049/pstack/skills/maintain-formal-verification-skill/SKILL.md) (MIT, Copyright (c) 2026 Lauren Tan). Automatic tool installation, mandatory statechart rendering, and ceremonial reruns are not adopted.

This explicitly requested generator/maintainer owns verification artifacts, not product repairs. Load `agent-guardrails` for scope, evidence, and correction limits; if unavailable, stop and request it without installing anything. `verification-before-completion` owns completion claims. Skill creation grants no dependency installation, production access, service restart, product-code repair, or publication authority. Temporary fault injection needs authorization covering the isolated scratch work.

## Select the property and method

Start with the named area, or resolve one bounded area from the request; do not scan the whole repo for a harder problem. Identify one promise, its independent source, and a reachable harmful violation. Ask only about missing intent or authority. If the promise conflicts with approved requirements, return to `shape-design` rather than choosing a new contract.

Prefer an existing check and tool. Use a small model for ordering or protocol questions, a code-level verifier for properties of actual code, and a deductive proof when finite bounds cannot establish the required claim. Explain the cheapest suitable choice. Generated-input tests against real code are an empirical alternative, not a formal proof; do not silently substitute them or a hand-copied function model for the requested claim. A missing tool blocks execution, not permission to install one.

## Create mode

1. Inspect the relevant callers, state writers, failure paths, and atomic or transactional boundaries. Map each modeled action to actual code; do not make several interruptible operations atomic to obtain a pass.
2. Generate `.agents/skills/verify-<project>-<area>/SKILL.md` using [the recipe template](references/recipe-template.md). Respect existing names and verification directories. Without an established location, keep owned model/harness files with the recipe; ask before adopting another layout. Reuse existing helpers; add no generic runner.
3. Fill actual paths, property source, method, assumptions, bounds, tool version/configuration, command, result interpretation, code correspondence, and change triggers. Keep unknowns explicit. An unexecuted recipe is a draft, never proof of the property.
4. Within the authorized budget, follow the generated recipe as a cold-start user once. Include one targeted negative control for the selected property and restore the starting state afterward; retain evidence outside disposable scratch. Without execution or fault-injection authority, report the exact unproved part instead of performing it.

## Negative control and code correspondence

For a code-level verifier, a relevant defect in isolated code must trigger the intended property failure, not a parse error, crash, or timeout. For a separate model, demonstrate both that the corresponding modeled defect violates the property and that the recipe identifies the source change requiring correspondence review. An unchanged model cannot detect an arbitrary code edit by itself. Label these two observations separately; never present model mutation as automatic code-regression coverage.

If the current property already fails, preserve that baseline finding. A new negative control must be distinguishable from it; otherwise report the control as unverified. Restoration returns to the original result, not necessarily to green. No mutation campaign or repeat-until-green loop.

## Update mode

Read the affected diff before deciding to rerun: since the last confirmed correspondence, include relevant working-tree changes, moved functions, and new writers of guarded state. A missing sync commit means correspondence is unknown; the last edit to a model is not evidence of alignment. Ignore proven no-effect changes and reuse still-applicable results.

Update models and harnesses from the code, not from the desired result. Change a property or narrow its scope only against approved changed requirements or an explicit owner decision; tests, comments, and commit messages alone do not grant that authority. Report old and new meaning or bounds. Run only the affected check; repeat the negative control when its detection path changed, not after every edit.

Confirm correspondence before advancing its recorded commit. A relevant dirty diff remains explicitly unsynced; do not label HEAD as the checked dirty artifact. Alignment may be confirmed even when a property fails: synchronization and a passing result are different facts. A blocked alignment check does not advance the marker. Keep this metadata in the recipe, not in a new lifecycle or evidence ledger.

## Interpret and hand off

Report what is in sync or updated, any counterexample or confirmed code bug, and any blocked or unverified part. A trace becomes a code finding only after checking its steps against real callers, inputs, atomicity, and environment; otherwise report the modeling mismatch or unknown. Never weaken the property to hide a violation or repair product code under maintenance authority.

State the property, method, command, scope/assumptions, correspondence, result, evidence location, and exclusions in plain language. Preserve failed, unknown, and incomplete outcomes. A successful recipe demonstration does not imply that the product satisfies its property. Use an optional diagram only when it clarifies the trace; do not require or install `statechart` or a renderer.

For runtime journeys, use `project-verification`. For an existing recipe, follow it rather than recreating it. Offer another property only when a concrete nearby need justifies it.
```

Nur portable `name`-/`description`-Metadaten im ersten Entwurf. Die explizite Aufrufgrenze ist ein Verhaltensvertrag, keine behauptete technische Sandbox. Client-spezifische Invocation-Policies werden nicht ungeprüft eingeführt; deren tatsächliche Wirksamkeit müsste bei einer späteren Runtime-Qualifikation geprüft werden.

## 4. Neue Vorlage: vorgeschlagene Ausgabeform

Ziel: `skills/skill-authoring/project-formal-verification/references/recipe-template.md`.

Die Vorlage enthält nur projektabhängige Betriebsdaten und die Schritte zum Benutzen des Rezeptes. Die Methodenlehre bleibt im Generator. Beim Generieren müssen die Platzhalter durch echte Fakten ersetzt oder konkrete Unbekannte mit Entwurfsstatus benannt werden. Kein scheinbar ausführbares Beispielkommando erfinden.

````markdown
# Generated formal recipe template

Fill this skeleton for the project's existing recipe name or `.agents/skills/verify-<project>-<area>/SKILL.md`. Replace every PLACEHOLDER, remove inapplicable items, and label unresolved facts and unexecuted instructions explicitly. Reuse established verification artifacts; do not copy them into the skill.

```markdown
---
name: verify-PROJECT-AREA
description: Check PROPERTY in PROJECT AREA. Use when COVERED_SYMBOLS, their state writers, or stated assumptions change, or when a task needs evidence for this specific property.
---

# Verify PROJECT AREA

## Property and scope
- Property / harm / independent source: PLACEHOLDER.
- Method and covered artifact: PLACEHOLDER.
- Initial states, bounds, assumptions, exclusions: PLACEHOLDER.

## Code correspondence
- Actions or proof obligations → source files/symbols and real atomic boundaries: PLACEHOLDER.
- Related callers and writers of the same guarded state: PLACEHOLDER.
- Last confirmed correspondence commit, or unknown: PLACEHOLDER.
- Relevant uncommitted differences, if any: PLACEHOLDER.
- Before relying on a result, inspect relevant changes against this mapping, including moved code and new writers. Unresolved correspondence prevents a code-level claim; merely rerunning the checker does not resolve it.

## Prerequisites and permissions
- Exact tool version and configuration, existing invocation, fixture and isolation requirements: PLACEHOLDER.
- Authorized actions, scratch-only fault injection, and forbidden product/remote actions: PLACEHOLDER.
- Missing prerequisites or unexecuted steps: PLACEHOLDER.

## Run and interpret
- Command and bounded runtime/resource budget: PLACEHOLDER.
- Exact successful result, property-failure result, and incomplete/error interpretation: PLACEHOLDER.
- Counterexample-to-code replay procedure: PLACEHOLDER.
- Evidence location outside disposable scratch: PLACEHOLDER.
- Reuse applicable evidence; run only for the assigned claim, a relevant delta, or a specific hypothesis. Report property, method, scope, correspondence, result and exclusions; unknown or incomplete is not a pass.

## Negative control and restoration
- Relevant scratch defect and intended property failure: PLACEHOLDER.
- For a separate model, the source change requiring alignment review and the corresponding modeled defect: PLACEHOLDER.
- Existing failure baseline, distinguishing observation, restoration and owned-resource cleanup: PLACEHOLDER.
- Show the control on creation and when its detection path changes, only with applicable authority. Preserve the original property and baseline findings; a tool error is not successful defect detection.

## Maintenance
- Changes that invalidate correspondence or execution evidence: PLACEHOLDER.
- Relevant drift routes to the update mode of `project-formal-verification`; request maintenance authority if absent. Confirm alignment before advancing its commit; keep code bugs as findings and property changes tied to approved requirements.
```
````

Ein Sync-Commit beschreibt Modell-Code-Zuordnung, nicht den Zeitpunkt des letzten grünen Laufs. Ein letzter erfolgreich geprüfter Zustand darf nicht als aktueller Produktzustand ausgegeben werden. Vorhandene CI-/Run-Artefakte bleiben die Ablage für einzelne Laufbelege.

## 5. Bestehenden empirischen Generator präzisieren

### 5.1 `project-verification/SKILL.md`

**Beschreibung ersetzen** — klare Abgrenzung statt langer Prozessbeschreibung:

```yaml
description: Create or update a project-local recipe for a real UI, CLI, service, or persistence journey. Use when explicitly asked to generate or maintain a verification skill or feature map; not for formal invariants or automatic audits.
```

**Create mode, Punkt 2 ersetzen:**

> Resolve the project name, one important journey, and applicable execution authority from the request and repository. Ask only about unresolved choices or missing permission; do not reconfirm an explicit decision.

**Create mode, Punkt 4 ersetzen:**

> Demonstrate once, end to end, only within applicable execution authority: record command, output, exit code, and read-back, clean up owned resources, then confirm the named evidence remains. Clean up owned residue after a failed attempt too. Otherwise label the recipe as an unproved draft and state exactly what remains unverified; a stand-in environment never proves the setup steps it bypassed.

Keine neuen Abschnitte, keine Änderung des vorhandenen Update-Vertrags und kein allgemeiner Audit.

### 5.2 Empirische `references/recipe-template.md`

Die vorhandenen Bulletpoints werden ersetzt/ergänzt; keine zweite Vorlage:

| Bestehender Abschnitt | Vorgeschlagener Zielinhalt |
| --- | --- |
| `Prerequisites and permissions` | `PLACEHOLDER: required tools, environment, credentials, fixtures, and authorized actions. Name isolated ports/data/profile ownership; stop if isolation is unavailable rather than adopting a user instance. Name forbidden production, browser, or shared-service actions.` |
| `Launch` | `PLACEHOLDER: exact commands and prerequisites to reach a usable state. Include migrations/seeds from empty state when that is the claim; name setup supplied by a stand-in and still unverified on the real target. Stop only what you started.` |
| `Readiness check (read-only)` | `PLACEHOLDER: commands confirming health, artifact identity, and ownership before driving and after surprising behavior. Missing journey prerequisites block the journey, not permission to relax it.` |
| Journey / `Evidence` | `PLACEHOLDER: capture the action and outcome, command/output/exit code or selector observation, and side effects. For dry-run/test mode, observe which relevant effects occur or are prevented rather than trusting the label.` |
| `Cleanup` | `PLACEHOLDER: stop only owned resources, including failed-attempt residue; remove scratch state and verify the named evidence artifacts still exist outside it.` |

Unabhängige Erwartungen, Read-back, Feature-Menü und bestehende Autorisierungsgrenzen bleiben erhalten. Das Vorhandensein einer umfangreicheren Vorlage erzeugt keine Pflicht, jede mögliche Journey auszuführen.

## 6. Workflow-Verweise: genaue Einfügepunkte

### 6.1 `shape-design`: Design quality

Den vorhandenen Retry-/Idempotenz-Bullet um einen bedingten Zusatz erweitern, statt einen neuen Pflichtabschnitt anzulegen. Der relative Link im Zieltext bezieht sich auf die spätere Skill-Datei:

```text
When a named ordering or state invariant has a material gap in existing evidence, propose one bounded formal check; use an existing project recipe, or explicitly scope recipe creation through [`project-formal-verification`](../../skill-authoring/project-formal-verification/SKILL.md). A state machine alone is not a reason to add a checker.
```

Shaping benennt und genehmigt die Frage. Es startet dadurch weder Generator noch Tool und bleibt frei von Modellchecker-Tutorials.

### 6.2 `write-implementation-plan`: vorhandene Evidenzkette

Im bestehenden Absatz `Assign each validation unit ...` nach der bisherigen Evidenzkette einfügen:

```text
Name the selected project recipe and the claim it proves. For a formal check, include its property source, code correspondence, bounds/assumptions, tool configuration, and invalidating delta in that same unit. If no suitable recipe exists, propose explicitly scoped creation via `project-verification` or [`project-formal-verification`](../../skill-authoring/project-formal-verification/SKILL.md); selecting a check does not authorize creating or installing its machinery.
```

Im Absatz `Reviews are the exception, not the default` nur den bisherigen Einstieg bis vor `Plan a review only ...` ersetzen:

> **Reviews are the exception, not the default.** Spend the evidence budget on claim-matched verification. Empirical journeys, type/schema checks, bounded model or code checks, and deductive proofs support different claims; choose the smallest sufficient method rather than treating them as interchangeable badges.

Die restlichen Review-Kriterien, das Timing und der vorhandene finale Verifikationstask bleiben unverändert. Ein formaler Check kommt früh, wenn abhängige Tasks die Invariante bereits voraussetzen; sonst in die bestehende abschließende Validierungseinheit. Ein Modellcheck ersetzt keine daneben erforderliche UI-/Persistenz-Evidenz. Noch gültige Belege werden nicht erneut ausgeführt.

### 6.3 `orchestrate-implementation`: Delivery und Brief

In Abschnitt 6 nur die Erläuterung des finalen Verifikationstasks ändern:

- bisher: `bounded empirical journeys on the real user surface against independently derived expectations, preferring an installed verify-<project> recipe`;
- vorgeschlagen: `the plan's assigned empirical journeys and any justified formal checks, each against its independent source and exact scope, preferring the selected project-local verification recipes`.

Der bestehende Satz über Evidenzreuse bleibt stehen. Es wird kein weiterer Task, Reviewer oder Run-State eingeführt.

Im Worker-Brief, Punkt 4, vor `Carry this scope unchanged ...` ergänzen:

> Include the selected recipe path; for a formal check, pass its property source, code correspondence, bounds/assumptions, and tool configuration rather than only a green result.

Der Brief transportiert Fakten aus der genehmigten Validierungseinheit. Er dupliziert nicht die gesamte Methodik des Generators und erteilt keine zusätzliche Schreib-/Installationsberechtigung.

### 6.4 `verification-before-completion`: Evidenzabsatz

Nach dem Satz über die Glaubwürdigkeit eines Regressionstests im vorhandenen Evidenzabsatz ergänzen:

> A model-check result covers the stated model and bounds; a code-level check or proof covers its stated obligations and assumptions. A code claim based on a separate model also needs confirmed correspondence to the relevant current source, including working-tree changes. Generated-input tests remain empirical, and static checks prove only their declared contracts. Unknown, interrupted, or incomplete results are not passes.

Kein Generatoraufruf an der Abschlussgrenze und kein obligatorischer neuer Check. Die Passage begrenzt die Aussage, nicht die Wahl des bereits ausreichenden Belegs.

## 7. Katalog, Provenienz und Projekt-Hinweise

### Metadateien

- `README.md`, Skill authoring: `project-formal-verification — explicitly requested invariant/model/code-verification recipe creation and maintenance.`
- `README.md`, Boundaries: den bestehenden `project-verification`-Bullet durch die Abgrenzung empirischer vs formaler Rezeptfamilie erweitern; beide erzeugen/pflegen Wissen, Projekt-Rezepte führen zugewiesene Checks an, Guardrails und Completion-Gate behalten ihre Zuständigkeit. Keine generelle neue Workflow-Stufe.
- `UPSTREAM_ADOPTION.md`: ein neuer Abschnitt mit dem neuen Pin, übernommenen Prinzipien und verworfenen Defaults. Alte Normal-Verifikationsentscheidung bleibt gültig.
- `THIRD_PARTY_NOTICES.md`: den vorhandenen Lauren-Tan/pstack-Notice auf die beiden neuen Dateien erweitern; MIT-Notice nicht duplizieren.
- `CHANGELOG.md`, Unreleased: ein Eintrag für formale Rezepte und die gezielten Integrations-/Rezeptpräzisierungen; kein Release, keine `VERSION`-Änderung.

`sources.json` verwendet das vorhandene `mode: adapted`-Schema. Vorgesehene neue Beziehungen:

| Lokale Datei | Upstream-Datei | Pin |
| --- | --- | --- |
| Neuer Formal-`SKILL.md` | `create-formal-verification-skill/SKILL.md` | `2776ddd2355d6d6c8747d3964600f28daf62f049` |
| Neuer Formal-`SKILL.md` | `maintain-formal-verification-skill/SKILL.md` | gleicher neuer Pin |
| Neue Formal-Vorlage | `create-formal-verification-skill/SKILL.md` | gleicher neuer Pin |
| Neue Formal-Vorlage | `maintain-formal-verification-skill/SKILL.md` | gleicher neuer Pin |
| Vorhandene empirische Vorlage | `create-verification-skill/SKILL.md` | bestehender Pin `f713f14203cd6420cec13cd7c55c32d598dbab68` |

Jeweils `repository: https://github.com/cursor/plugins`, `branch: main`, `license: MIT`, `copyright: Copyright (c) 2026 Lauren Tan`. Upstream-Pfade beginnen mit `pstack/skills/`. Die bereits vorhandenen Beziehungen bleiben erhalten. Keine Umpinnung des unveränderten normalen Creators. Die neuen Workflow-Verweise sind lokale Integrationsregeln, keine zusätzlich importierten Upstream-Workflows.

### Projektlokale `AGENTS.md` — nur später beim konkreten Rezept

Dieser Katalogentwurf ändert weder globale noch fremde Projekt-Agentenhinweise. Bei einer ausdrücklich beauftragten Recipe-Erstellung kann folgender **projektkonkret auszufüllender** Verweis angeboten werden:

> For changes to NAMED_SYMBOLS or other writers of GUARDED_STATE, read `.agents/skills/verify-PROJECT-AREA/SKILL.md` and check its correspondence before relying on prior evidence. Run only the assigned check or a justified delta recheck. Recipe maintenance and tool installation require their own applicable authority.

Der Generator aktualisiert `AGENTS.md` nicht ungefragt. Der Verweis gehört zum lokalen Projekt, nicht in jeden Host-Adapter. Ein fehlender optionaler Skill blockiert keine fachfremde Arbeit; eine erforderliche fehlende Voraussetzung wird genannt, nicht automatisch installiert.

## 8. Abnahmekriterien und gezielte spätere Validierung

**Stand nach Katalogumsetzung, 2026-11-06:** A1–A6 bleiben ohne Routing-Läufe bzw. autorisierten Pilot **unverified**. A7 ist an der Vorlage geprüft, nicht durch eine neue Produkt-Journey. A8 wurde am gezielten Workflow-Diff abgeglichen. Für A9 bestehen `bash tests/skills_test.sh` (45 Skills und enthaltene Selftests), `bash tests/orchestrator_handoff_test.sh`, `git diff --check` sowie `check-skill-sources.sh` mit den acht betroffenen Quellenbeziehungen; der unveränderte alte Pin meldet nur informativen Branch-Drift. Beide neuen Dateien entsprechen den Zieltexten in §§3–4; bestehende Quellenbeziehungen und gesicherte fremde Änderungen bleiben erhalten. Strukturprüfungen allein belegen weder korrektes Routing noch Modell-Code-Synchronisierung.

| ID | Kriterium | Konkreter Nachweis nach Umsetzungsfreigabe |
| --- | --- | --- |
| A1 | Ein normaler UI-/CLI-Rezeptauftrag bleibt beim empirischen Generator; ein expliziter Formal-Rezeptauftrag wählt den neuen Generator. | Tatsächlich geladene `SKILL.md` bei zwei gezielten Routing-Prompts prüfen; keine bloße Agenten-Selbstauskunft. |
| A2 | Ein gewöhnlicher Code-/Review-Auftrag erzeugt weder Verifikations-Skill noch Checker-Installation. | Ein Near-miss-Prompt ohne Generatorauftrag; keine neuen Recipe-/Dependency-Dateien. |
| A3 | Das generierte formale Rezept benennt Property/Sollquelle, Methode, Codebindung, Grenzen, echten Befehl, Tool-Konfiguration und Ergebnisinterpretation. | Ein begrenzter Pilot; erzeugte Dateien plus tatsächliche Laufbelege prüfen. |
| A4 | Eine relevante Codeänderung wird nicht durch ein weiterhin grünes altes Modell abgedeckt behauptet. | Im selben Pilot eine genehmigte Scratch-Änderung an einer modellierten Operation; Rezept muss fehlende Übereinstimmung erkennen. Der entsprechende Modellfehler muss die Property fachlich verletzen. |
| A5 | Echte Property-Verletzung bleibt Befund; Driftpflege schwächt weder Property noch Grenzen ohne Freigabe ab. | Gegenbeispiel aus A4 mit Original-Sollquelle vergleichen. Falls Pfad nicht real erreichbar ist, Modellfehler statt Produktfehler melden. |
| A6 | Fehlende Ausführungs-/Fault-injection-Berechtigung oder fehlendes Tool ergibt Entwurf/blockiert, keinen Pass und keine Installation. | Im selben Pilot zuerst ohne Ausführungsfreigabe beginnen; keine nicht genehmigten Lauf-/Installationsaktionen. Nach Freigabe denselben Entwurf weiterverwenden. |
| A7 | Cleanup betrifft nur eigene Ressourcen und erhält Belege; Ersatzumgebung/Dry-run werden nicht überbehauptet. | Geänderte empirische Vorlage prüfen; eine vorhandene geeignete Journey nur dann erneut ausführen, wenn die konkreten Recipe-Änderungen ihre Evidenz betreffen. Nicht künstlich drei neue Demo-Anwendungen erzeugen. |
| A8 | Planung/Orchestrierung behalten ihren vorhandenen Abschluss-Task und Evidenzreuse; keine neue universelle Formal-Pflicht. | Gezielter Diff-/Konsistenzabgleich der vier Workflow-Skills und des Briefs gegen `55f04e9`. |
| A9 | Namen, Frontmatter, relative Links und Quellenbeziehungen stimmen. | Bestehende Katalog-Struktur-/Linkprüfungen und gezielte Provenienzprüfung; vorhandene verpflichtende Projekt-Gates bleiben bindend. |

A3–A6 werden nach Möglichkeit durch **einen** zusammenhängenden Pilot abgedeckt, nicht durch je eigene Projekte oder Agenten-Swarms. Kein Werkzeug-/Sprachenvergleich, kein breiter Benchmark und keine Mutationstest-Kampagne. Unterbrochene/unknown Checkergebnisse sind ausdrücklich kein Erfolg. Trigger-Evaluierung benötigt dafür geeignete Ausführungsfreigabe; dieser Entwurf startet keine Agenten.

Die bestehenden Prüfungen entdecken neue Skills automatisch; zunächst keine zusätzlichen generischen Testskripte. Falls die Umsetzung eine konkrete wiederkehrende Vertragsverletzung offenlegt, kann eine kleine passende Assertion in vorhandenen Checks vorgesehen werden — keine Textkopie jeder Regel als Test.

## 9. Offene Entscheidung und Freigabegrenze

**Empfohlener Katalogumfang ist oben vollständig benannt.** Noch offen für die praktische Qualifikation sind **Pilotprojekt, eine konkrete Eigenschaft und das vorhandene passende Werkzeug**. Diese Auswahl ist kein Grund, jetzt irgendeinen Checker zu installieren oder in einem anderen Projekt tätig zu werden.

Der Folgeauftrag „Go ahead with the plan.“ gibt die Katalogumsetzung dieser Revision frei. Er bestimmt kein Pilotprojekt und autorisiert weder fremde Produktänderungen noch Installation, Veröffentlichung oder Delegation. Die ausführende Formal-Fähigkeit bleibt bis zum ausgewählten und autorisierten Pilot ausdrücklich unqualifiziert.

### Capture checkpoint

- **Vokabular:** keine neuen bestätigten Projektdomänenbegriffe; vorhandene Begriffe für Recipe, Property, Evidence und Code werden in ihrem bestehenden Sinn verwendet. Keine künstliche `CONTEXT.md` anlegen.
- **Entscheidung:** der getrennte Generator ist durch die Freigabe von Revision 1 bestätigt. Die Wahl ist reversibel und erfüllt nicht alle ADR-Kriterien; kein ADR nötig.
- **Verhalten:** §§3–7 und A1–A9 beschreiben den freigegebenen Vertrag und die Abnahme. Der Folgeauftrag autorisiert die direkte Katalogumsetzung mit bestehenden Struktur-/Vertragsprüfungen.
- **Unsicherheit:** praktische Qualifikation benötigt einen ausgewählten und autorisierten Pilot; keine uneingeschränkte Laufzeit-Abnahme aus der Katalogumsetzung ableiten.

**Abnahmegrenze:** `accept` ist für die geprüfte Katalogumsetzung möglich; `ask` für Pilotprojekt, Eigenschaft und Werkzeug vor praktischer Qualifikation. Routing- und Ausführungskriterien bleiben ohne entsprechende Läufe unverified.
