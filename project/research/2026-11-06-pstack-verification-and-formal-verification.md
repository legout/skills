# pstack-Verifikation: Abgleich und Empfehlungen für den Skills-Katalog

**Status:** Recherche und Vorschlag vom 2026-11-06, keine Umsetzungsfreigabe. In diesem Auftrag keine Skills geändert, installiert oder ausgeführt. Planning-contract v1. Ausgangs-HEAD `93509c96f9de2a31a945aa9d1e8b5af24908c237` mit bereits vorhandenen lokalen Landing-Änderungen. Während der Recherche wurden diese in `ff4d666` sowie neue Verifikationsregeln in `55f04e9cb46cdb2bbe3e328b92a1b10507ddf010` eingecheckt. Die relevanten Deltas wurden vor Abschluss erneut gelesen und unten berücksichtigt; beide Commits stammen nicht aus diesem Auftrag.

## Kurzurteil

**Den bestehenden `project-verification` gezielt vervollständigen; für formale Verifikation höchstens einen neuen, explizit aufgerufenen Generator/Maintainer `project-formal-verification` vorsehen.** Die Workflow-Skills erhalten wenige bedingte Verweise, keine zusätzliche obligatorische Verifikationsphase. Zuerst sollte ein konkreter Bereich mit einer wertvollen Invariante als Pilot ausgewählt werden.

Der normale pstack-Creator wurde bereits am 16. Oktober untersucht und in `skills/skill-authoring/project-verification` adaptiert. Der Creator, sein Maintainer und alle drei Feature-Map-Dateien sind zwischen unserem damaligen Pin und dem jetzt untersuchten Upstream-Stand **bytegleich**. Es gibt dort keinen neuen Upstream-Delta, der einen zweiten Skill oder einen bloßen Pin-Bump rechtfertigt. Die wirkliche neue Fähigkeit wäre eine gepflegte Verbindung zwischen formaler Eigenschaft, Modell beziehungsweise Code-Verifier und aktuellem Produktcode. [U1–U5, L1–L3]

**Aktualisierung zum Abschlussstand `55f04e9`:** Planung und Orchestrierung verweisen inzwischen bereits auf `project-verification` beziehungsweise installierte `verify-<project>`-Rezepte. Sie bündeln gründliche empirische Verifikation in einem abschließenden Task und behandeln Reviews als benannte Ausnahme. Diese Integration nicht erneut bauen. Noch fehlen die konkrete formale Recipe-Variante und die Unterscheidung zwischen Modellbeweis, Codebeweis, statischem Check und empirischer Beobachtung. Der Vorschlag ergänzt den bestehenden Abschluss-Task, er führt keinen zweiten ein.

## Quellenstand und Untersuchungsumfang

Upstream: `cursor/plugins@2776ddd2355d6d6c8747d3964600f28daf62f049`, Commit-Zeit `2026-11-05T11:14:58Z`. GitHub-Baum vollständig abgefragt; heruntergeladene Markdown-Dateien gegen ihre Git-Blob-Hashes geprüft.

Vollständig gelesen:

- `create-verification-skill/SKILL.md` und dessen gesamte Begleitdateien: Feature-Map-Index, `create-note.md`, `search.md`;
- `create-formal-verification-skill/SKILL.md` — dieser Ordner enthält am untersuchten Stand keine weiteren Dateien;
- die beiden referenzierten Maintainer;
- `statechart/SKILL.md`, dessen Render-Referenz und die pstack-Lizenz;
- alle 13 derzeit vorhandenen `skills/workflow/*/SKILL.md`, die einschlägigen Orchestrierungs-Briefs/Review-Regeln und die Logic-Prototyp-Referenz;
- `project-verification` einschließlich Vorlage, `agent-guardrails`, Autorenkonventionen, README, vorhandene Adoptionserklärung und die Katalog-Strukturtests.

Die Implementierung und Tests des separaten `statechart`-Pakets wurden **nicht** vollständig auditiert. Daraus wird keine Empfehlung zur Installation oder unveränderten Übernahme abgeleitet.

Die Vault-Abfrage lieferte eine einschlägige Seite (`references/grok-bot-hermes-pstack.md`, ein Kandidat gelesen, keiner verworfen). Für diesen Katalog ist die detailliertere lokale Recherche vom 16. Oktober maßgeblich. Der optionale QMD-Lookup lief ins Timeout und startete dabei unerwartet einen Modell-Download; er wurde nicht als Beleg verwendet. Danach war kein QMD-Prozess mehr vorhanden. Kein Embedding-/Index-Rebuild wurde veranlasst. Die dauerhafte Recherche bleibt gemäß Projekt-Artefaktvertrag hier, ohne duplizierte Wiki-Seiten.

## 1. Was `create-verification-skill` genau liefert

### Zweck und Aufruf

Der Skill ist ein **Generator für Projekt-Bedienwissen**, nicht selbst der Verifier einer beliebigen Anwendung. Das Ergebnis soll ein neuer Agent ohne Gesprächskontext benutzen können. Upstream setzt `disable-model-invocation: true` und schreibt nach `.cursor/skills/verify-<app>/`. Die Fähigkeit ist sprach- und frameworkübergreifend. [U1]

### Repository-Interview

Fünf Fragen werden zunächst aus dem Repository beantwortet:

1. **Surface:** tatsächliche Oberfläche — UI, CLI/TUI, Desktop, API, Mobile oder Library; bei mehreren eine primäre auswählen und die anderen benennen.
2. **Run:** dokumentierter Startbefehl, Ports, Umgebungsvariablen, Authentisierung, Seed-Daten.
3. **Drive:** zuerst vorhandene Playwright-/Cypress-/PTY-/HTTP-/Debug-Harnesses; erst dann generische Browser-, Terminal- oder HTTP-Rezepte.
4. **Observe:** Screenshots, Transkripte, Antworten, Logs, Exitcodes und Datenbankzustand.
5. **Isolate:** getrennte Ports, Profile und Datenverzeichnisse; andernfalls keine geteilte Benutzerinstanz doppelt steuern.

Upstream fordert, einen kaputten Start zunächst zu reparieren **oder präzise zu melden**. Irrelevante fehlende Assets dürfen als gekennzeichnetes und später entferntes Verifikations-Scaffolding erzeugt werden. Lokal darf daraus keine pauschale Reparatur-, Installations- oder Datenzugriffsberechtigung entstehen. [U1, L1, L4]

### Generiertes Rezept

- **Launch:** nutzbarer Zustand auch aus leerem Datenverzeichnis, Migrationen/Seeds berücksichtigt; Healthcheck allein reicht nicht. Bei kurzlebigen CLIs/TUIs getrennte Sitzungen statt künstlich dauerhaft laufendem Server.
- **Doctor:** ein read-only Check für Instanzgesundheit, Version/Build, Port-Eigentümerschaft und gültige Authentisierung, insbesondere nach überraschendem Verhalten.
- **Drive:** echte Befehle/Selektoren; stabile Rollen, Namen und Routen statt Koordinaten oder Tab-Reihenfolge.
- **Evidence:** Aktion **und** Folgezustand, echte Benutzerwege statt interner Setter; zusätzlich Dateien, Zeilen, Nachrichten oder andere Seiteneffekte. Mocks nur an bereits vorhandenen externen Produktionsgrenzen. Die Nebenwirkungsfreiheit eines Dry-runs wird beobachtet, nicht aus seinem Namen abgeleitet.
- **Cleanup:** nur selbst gestartete Ressourcen beenden, nie nach Prozessnamen; Scratch entfernen, Belege behalten.
- **Helpers:** vorhandene Hilfsskripte ausführbar machen und ihren konkreten Aufruf dokumentieren. Der Creator liefert selbst keine fertigen Harness-Skripte. [U1]

### Feature-Map und Demonstration

Upstream erzeugt ein README und zunächst ungefähr drei bis fünf Feature-Dateien. Die feste Form lautet: `Sub-features`, `How to get to it (user POV)`, `Driving it with <harness>`, `Gotchas`. Jede Datei beschreibt Benutzerwege, Voraussetzungen und beobachtbare Endzustände. Fehlende Seeds sind ein Blocker, keine Erlaubnis zur Abschwächung der Erwartung. Ein anderer Einstieg beweist nicht den übersprungenen Einstieg. [U1, U2]

Die Beispiele zeigen Browser- und CLI-Erstellung, Abbruch, Suche nach Titel/Inhalt, Tastatur-Einstiege, leere Suche und Zurücksetzen. Wertvoll sind insbesondere Read-back nach dem Speichern, Fokusbedingungen für Hotkeys, Debounce-Warten statt festem Sleep und die Bindung jedes Belegs an Feature/Einstieg. [U3, U4]

**Nicht blind kopieren:** In `search.md` wird die UI-Suche geleert; nach anschließenden CLI-Schritten soll ein Screenshot wieder eine gefüllte Suche zeigen, ohne diese UI erneut herzustellen. Das ist eine aus der beschriebenen Reihenfolge abgeleitete Beispiel-Lücke, kein live reproduzierter Produktfehler. Die Beispiele sind Formvorlagen, keine bereits validierten Rezepte für unsere Projekte. [U4]

Der Creator demonstriert ausdrücklich nur **ein** gemapptes Feature end-to-end. Nach Cleanup muss der Beleg noch existieren. Fehlversuche sollen keine Prozesse/Ports hinterlassen. Nicht ausgeführt bedeutet Entwurf. Ersatzumgebungen müssen offenlegen, welche Einrichtungsschritte sie vorweggenommen haben und was am echten Ziel ungeprüft bleibt. Zum Schluss wird der Maintainer angeboten; einen Zeitplan soll der Creator nur auf Nachfrage vorschlagen. [U1]

### Der Maintainer ist deutlich breiter

`maintain-verification-skill` prüft Indexhygiene, startet einen Source-Reader je Feature, lässt den Koordinator alle Features live bedienen und unterscheidet Dokumentationsdrift, Harness-Lücke und Produktregression. Er bietet `clean`, `changed`, `blocked`; bei Änderungen sieht er einen PR vor. Wiederholte Readiness-Prüfung nach Fehlern und Beleg-Erhalt sind Teil seiner Regeln. [U5]

Das ist **nicht** der lokale Default. Unsere bewusste Anpassung ist bereits: eine Feature-Map als Auswahlmenü, Pflege nur betroffener Rezepte, keine Swarms, täglichen Vollprüfungen oder impliziten PRs. Diese Entscheidungen bleiben gültig. [L1–L4]

## 2. Was `create-formal-verification-skill` hinzufügt

### Zielwahl und Werkzeugwahl

Ausgangspunkt ist ein konkretes Versprechen, dessen Verletzung Nutzern schadet und dessen Fehlerfälle normale Tests schwer erreichen. Ein vom Nutzer benannter Bereich geht vor; sonst sucht Upstream den wertvollsten, nicht den bequemsten Kandidaten. Lokal begrenzen wir diese Suche auf den freigegebenen Bereich, statt einen repo-weiten Audit daraus zu machen. [U6]

Das Werkzeug folgt der Frage:

- **Reihenfolgen, Concurrency, Retry-/Recovery-Protokolle:** kleines Modell, etwa TLA+/TLC.
- **Speichersicherheit, Overflow, Parser-/Datenstruktur-Eigenschaften:** wenn möglich ein Verifier, der tatsächlichen Code analysiert.
- **Eigenschaft über alle Größen ohne ausreichende endliche Grenze:** gegebenenfalls ein deduktiver Beweis.
- **Kein passender Code-Verifier:** generierte Eingaben gegen den echten Code, ausdrücklich nicht eine handkopierte Modellfunktion als Ersatz. [U6]

Wichtig für unsere Ergebnisbezeichnungen: Property-based Testing ist kein formaler Beweis. Ein vollständiger endlicher Modellcheck ist ein Beweis für dieses Modell unter seinen Annahmen; ein begrenzter Codecheck deckt seine Bounds ab. Keines davon allein ist ein Beweis für das komplette Produkt oder dessen Deployment.

### Die sieben Qualitätsanforderungen

1. **Codebindung:** jeder Modell-/Proof-Teil verweist auf echte Funktionen; eine atomare Modellaktion muss einer tatsächlich unteilbaren Codeaktion entsprechen.
2. **Negative Kontrolle:** jede gewählte Eigenschaft soll einen gezielten Defekt erkennen, beispielsweise eine entfernte Prüfung oder umgeordnete Operation.
3. **Befund bleibt Befund:** eine aktuelle Verletzung mit Gegenbeispiel melden, nicht Eigenschaft/Modell passend biegen; keine Produktreparatur ohne Auftrag.
4. **Geltungsbereich:** Bounds, Annahmen und Ausschlüsse nennen.
5. **Verständlichkeit:** Eigenschaft, Schaden und Gegenbeispiel in Projektsprache erklären.
6. **Reproduzierbarkeit:** ein konkreter Befehl, reproduzierbare Tool-Version, vertretbare Laufzeit.
7. **Synchronität:** erfasste Dateien/Funktionen und den Commit der zuletzt bestätigten Modell-Code-Übereinstimmung dokumentieren. [U6]

Der Generator schreibt einen projektlokalen Skill mit Frontmatter, echten Befehlen, Code-Abdeckung und Sync-Commit. Anders als der normale Creator schreibt dieser Text keinen festen `.cursor/...`-Zielpfad vor. Der nächste Agent soll relevante Änderungen erkennen, den Check ausführen, Modellfehler von Produktfehlern unterscheiden und eine beabsichtigte Vertragsänderung korrekt pflegen können. Ein zweiter Zielbereich wird nur angeboten, wenn ein nahe liegender wertvoller Kandidat gefunden wurde. [U6]

### Demonstration und wichtige Einschränkung

Upstream verlangt eine Scratch-Änderung am echten Code, die die Eigenschaft bricht. Danach soll der generierte Skill den Bruch entdecken; nach Entfernen des Defekts soll der ursprüngliche Zustand wiederhergestellt sein — entweder grün oder nur mit den bereits gemeldeten Ausgangsverletzungen. Ein nie ausgeführter Skill bleibt Entwurf. [U6]

**Die entscheidende Anpassung:** Ein handgeschriebenes TLA+-Modell liest den Produktcode normalerweise nicht. Eine isolierte Code-Mutation verändert dessen TLC-Ergebnis daher nicht automatisch. Für Modellchecks müssen wir zwei getrennte Fähigkeiten demonstrieren:

- Die Property erkennt den Defekt im entsprechend geänderten Modell.
- Der generierte Arbeitsablauf erkennt die relevante Codeänderung und verlangt eine erneute Prüfung/Anpassung der Modell-Code-Zuordnung.

Ein grünes unverändertes Modell nach einer Code-Mutation ist kein Nachweis, dass diese Mutation abgesichert ist. Für einen echten Code-Verifier kann dieselbe Scratch-Änderung unmittelbar den Check scheitern lassen. Ein Modelldefekt ist zudem erst dann ein bestätigter Codefehler, wenn die Schritte mit realen Callern, Atomarität und Umgebungsbedingungen im Code möglich sind; ein Repro erhöht die Evidenz, ist aber keine magische Voraussetzung für jeden logisch belegbaren Fehler.

Die Upstream-Formulierung „a check that you have never seen fail proves nothing“ ist als praktische Nicht-Vakuositätsprüfung sinnvoll, aber keine allgemeine Definition mathematischer Beweiskraft. Wir übernehmen **eine gezielte negative Kontrolle für die ausgewählte Eigenschaft**, keine allgemeine Mutationstest-Kampagne. Ein Abbruch, Parsefehler oder Tool-Crash darf nicht als erfolgreich erkannter Invariantenbruch zählen.

### Pflege: eigentliche Stärke, aber nicht unverändert übernehmen

`maintain-formal-verification-skill` sammelt Property, Code-Abdeckung, Bounds, Annahmen, Befehl und Sync-Commit. Fehlt dieser, benutzt Upstream ersatzweise den letzten Commit der Verifikationsdateien und legt das offen. Danach: alten Check ausführen, Änderungen inklusive verschobener Funktionen und neuer Schreiber auf geschützten Zustand lesen, Modell anpassen, erneut prüfen, negative Kontrolle, Sync aktualisieren und den Skill noch einmal befolgen. [U7]

Die Klassifikation ist nützlich:

- keine semantische Auswirkung;
- Modell/Harness beschreibt den Code nicht mehr;
- Versprechen wurde absichtlich geändert;
- Versprechen könnte verletzt sein.

Mögliche Ergebnisse sind `in sync`, `updated`, `bug`, `blocked`, wobei `updated` und `bug` gemeinsam möglich sind. Ein zuvor grünes, nach Aktualisierung rotes Modell kann gerade einen alten falschen Sicherheitsnachweis aufdecken. [U7]

Lokal brauchen wir vier Änderungen daran:

1. **Diff zuerst, nicht Ritual-Reruns.** Gültige Evidenz behalten; nur relevante Code-/Modell-/Property-/Tool-/Annahmenänderungen rechtfertigen erneute Ausführung. Der letzte Datei-Commit ist höchstens ein Suchstart, niemals eine behauptete bestätigte Synchronisierung.
2. **Absicht braucht autorisierten Vertrag.** Geänderte Tests, Kommentare oder Commit-Nachrichten sind Hinweise, aber allein keine Freigabe zur Abschwächung einer akzeptierten Invariante. Maßgeblich bleiben freigegebene Kriterien oder eine dokumentierte Owner-Entscheidung.
3. **Nicht nur HEAD vergleichen.** Relevante uncommitted Änderungen sowie neue Mutatoren desselben Zustands berücksichtigen. Ein Sync-Commit ist keine Garantie für den aktuellen Dirty Tree; lokale Abweichungen müssen als ungesynct erkennbar bleiben.
4. **Gebundener Reparaturumfang.** Nur Verifikationsartefakte pflegen, Produktdefekte melden; ein Fix-Pass und ein Delta-Recheck gemäß Guardrails, keine Schleife bis grün. Reine Formatänderungen erzwingen keinen neuen Solverlauf. [L4–L7]

### `statechart` ist kein kostenloser Pflichtbaustein

Der Creator verlangt bei TLA+ den Skill `/statechart` per Namen; er soll keine veränderlichen CLI-Pfade oder Optionen in generierte Skills kopieren. Der separate Skill stellt Zustandsdiagramme und Gegenbeispielpfade dar. [U6, U8]

Seine Laufzeitregeln sind relevant: erster Lauf installiert TLC und Java über mise mit Netzwerkzugriff; die Render-Referenz verlangt Pele. Es gibt mehrere TLC-Läufe zur getrennten Untersuchung verletzter Regeln, eine Grenze von 100.000 Zuständen für Folgeläufe nach dem ersten Bruch und ein Diagrammbudget von 500 Zuständen. Nicht geprüfte Regeln bleiben offen. Große fehlerfreie Modelle können ohne Diagramm enden. Abstraktion, Symmetrie, Constraints und ausgeblendete Pfeile beeinflussen die Darstellung und müssen erklärt werden. [U8, U9]

**Empfehlung:** weder dieses Paket noch seine Installationen automatisch übernehmen. Ein verständlicher Gegenbeispiel-Trace ist Pflicht; eine Grafik ist optional und mit vorhandener Darstellung möglich. Ein Renderer ersetzt keinen Checker. Ein späterer `statechart`-Import wäre eine eigenständige Tool-/Lizenz-/Laufzeitprüfung, nicht Nebenarbeit dieses Vorhabens.

## 3. Abgleich mit allen Workflow-Skills

| Bestehender Skill | Bereits vorhanden | Empfehlung |
| --- | --- | --- |
| `shape-design` | Invarianten, Fehler, Retry/Idempotenz, Shared State und genehmigte Spikes | Kleiner bedingter Verweis: Bei einer konkret benannten schwer testbaren Eigenschaft einen formalen Probe-/Verifikationsauftrag vorschlagen. Kein automatischer Solver bei jedem State Machine-Design. |
| `write-implementation-plan` | Failure → unabhängiger Sollwert → kleinster Check oder Evidenzreuse → invalidierendes Delta; seit `55f04e9` explizite Projekt-Rezepte und finaler Verifikationstask | Bestehenden Integrationspunkt um die formale Variante präzisieren: Property, Code-/Modellbindung, Bounds und Tool-Konfiguration in derselben Validierungseinheit. Vorab prüfen, wenn abhängige Arbeit die Invariante voraussetzt; sonst im vorhandenen Abschluss-Task. Keine doppelte Runtime-Verifikation hinzufügen. |
| `orchestrate-implementation` | Validierungsbudget, konkrete Worker-Aufträge, echte Evidenz, keine Doppelreruns; seit `55f04e9` finale Verifikation mit Projekt-Rezept, Reviews nur als benannte Ausnahme | Die bereits vorhandene Verknüpfung für formale Rezepte konkretisieren, insbesondere im Worker-Brief; nur eine begründete Evidenzlücke schließen. Kein zusätzlicher Abschluss-Task, permanenter Formal-Reviewer oder Verifier-Swarm. |
| `verification-before-completion` | Claim-matched Evidence, gleiche Oberfläche, Reuse | Ein kurzer Zusatz zu Beweisarten und Modell-Code-Synchronität. „Formell verifiziert“ nur mit genannter Property, Scope und Annahmen. Kein eigener Ausführungsworkflow. |
| `prototype-question` | Disposabler Logic-/State-Probe mit Freigabe | Optionaler Verweis auf einen begrenzten Modellcheck, wenn Reihenfolgen statt UI-Bedienbarkeit die Frage sind. Die derzeit HTML-zentrierte Logic-Referenz nicht zu einem zweiten Formal-Handbuch ausbauen. |
| `planning-contract` | Specs besitzen Verhalten/Invarianten; Research ist Evidenz; materielle Änderungen brauchen Freigabe | Unverändert. Formale Properties operationalisieren den bestehenden Vertrag, sie werden keine konkurrierende Spezifikation und kein neuer Artefakttyp. |
| `domain-modeling` | Begriffe und ADRs, ausdrücklich nicht Verhaltensvertrag | Unverändert. Projektnamen im Modell übernehmen; Property gehört in die Spec/Verifikation, nicht ins Glossar. |
| `capture-project-vision` | Vision und bestätigte dauerhafte Entscheidungen | Unverändert; keine formale Toolwahl im Vision-Interview erzwingen. |
| `grilling` | Expliziter Stress-Test von Entscheidungen | Unverändert; kann eine offene Invariante sichtbar machen, muss aber keinen automatischen Verifikationsauftrag erzeugen. |
| `review-codebase-architecture` | Report-only über Module und Seams | Unverändert; ein belegter Kandidat kann als Empfehlung an Shaping gehen. Kein zweiter repo-weiter Invarianten-Scanner. |
| `merge-worktree` | Exakter Candidate, Integration und wiederverwendbare Evidenz | Unverändert. Ein semantisch relevanter Konflikt invalidiert ohnehin betroffene Evidenz; identische Integration erzwingt keinen neuen Formal-Lauf. |
| `land-changes` | Sequenziert Integration, Push, Issue-Abschluss und Cleanup | Unverändert; kein Generator/Modellchecker beim Versand. Zu Beginn unversioniert, inzwischen durch `ff4d666` eingecheckt. |
| `make-release` | Projekt-Release-Gates und Artefaktprüfung | Unverändert. Ein bereits verpflichtender Formal-CI-Gate bleibt verpflichtend; der neue Skill macht ihn nicht automatisch für jedes Release erforderlich. |

Damit würden **vier Workflow-Skills kleine Anpassungen erhalten**, ein fünfter (`prototype-question`) höchstens einen bedingten Verweis. Nicht sämtliche Skills müssen über jede Verifikationsmethode Bescheid wissen.

## 4. Bestehenden `project-verification` behalten und nachschärfen

Ort bleibt `skills/skill-authoring/project-verification/`; der Skill erzeugt Skills und gehört deshalb nicht nur wegen seines Namens nach `workflow/`. [L1]

Sein Kern ist bereits gut: portable `.agents/skills`-Ausgabe, unabhängige Erwartungen, eine Journey, Permissions, Target-Identität, Read-back, ausschließlich eigene Ressourcen, Entwurfsstatus ohne Ausführung und die Trennung Drift/Harness/Produktfehler. Er ist stellenweise strenger und für unseren Workflow geeigneter als Upstream.

Sinnvolle kleine Ergänzungen überwiegend **in der vorhandenen Vorlage**, nicht als neue Checkliste:

- nach Cleanup tatsächlich prüfen, dass die genannten Belege erhalten sind;
- bei Ersatzumgebungen die vom echten Ziel nicht übernommenen Setup-Schritte ausweisen;
- bei Dry-run/Test-Modus beobachtete und ausgeschlossene Seiteneffekte benennen;
- bei fehlender Isolation nicht auf eine Benutzerinstanz ausweichen; Voraussetzungen für nutzbaren First-run konkretisieren, soweit die Journey ihn beansprucht;
- Readiness nach überraschendem Verhalten neu prüfen; kaputte Seeds als Blocker melden statt Erwartungen zu ändern.

Im Generator selbst die pauschale Bestätigung von Projektname/Journey/Execution in Schritt 2 auf **wirklich ungelöste Entscheidungen oder fehlende Autorisierung** beschränken. Ein klarer Nutzerauftrag muss nicht noch einmal identisch bestätigt werden. Die Ausführungsgrenze bleibt bestehen.

Keine zweite `create-verification-skill`-Kopie und kein zusätzlicher allgemeiner Maintainer: Create/Update existieren bereits.

## 5. Vorschlag für genau einen neuen Skill

### Identität und Zuständigkeit

**Name:** `project-formal-verification`.

**Ort:** `skills/skill-authoring/project-formal-verification/SKILL.md`, passend zum existierenden Generator. Keine Umbenennung des normalen Generators.

**Aufgabe:** Auf ausdrücklichen Auftrag einen projektlokalen formalen Verifikations-Skill erzeugen oder eine betroffene bestehende Verifikation aktualisieren. Kein allgemeiner Audit, kein Ersatz für `shape-design`, `systematic-debugging`, Review oder Abschlussprüfung.

Ein generierter Skill könnte beispielsweise `.agents/skills/verify-<project>-<area>/SKILL.md` heißen. Vorhandene Namen respektieren, Kollisionen mit `verify-<project>` vermeiden. Modelle und Harnesses folgen bestehenden Test-/Verification-Verzeichnissen; falls es keine Konvention gibt, im genehmigten Recipe-Bereich halten oder den Zielort klären. Kein globales neues `formal/`-Repositoryschema und kein neuer Artefaktvertrag.

### Minimaler Vertrag

Das generierte Rezept enthält:

- **Property und Sollquelle:** ein verständlicher Satz, Schadensszenario, Link zu freigegebener Anforderung oder unabhängiger Referenz;
- **Methode:** Modellcheck, begrenzter Codecheck, deduktiver Beweis oder ausdrücklich nur generierte Tests;
- **Codebindung:** Dateien, Symbole, andere Schreiber auf denselben Zustand und relevante Atomaritäts-/Transaktionsgrenzen;
- **Scope:** Anfangszustände, Bounds, Ausfälle, Fairness soweit nötig, Annahmen und Ausschlüsse;
- **Ausführung:** vorhandene/geprüfte Tool-Version, konkrete Eingaben/Konfiguration, ein Befehl, Budget und klare Auswertung von Erfolg, Gegenbeispiel und Abbruch/unknown;
- **Synchronität:** zuletzt tatsächlich bestätigter Commit plus Umgang mit relevantem Dirty Diff; der Sync-Marker wird nicht durch bloßes grünes Ausführen erneuert;
- **Negative Kontrolle:** ein gezielter, genehmigter Defekt in isoliertem Scratch und seine erwartete fachliche Fehlermeldung; danach Wiederherstellung;
- **Ergebnis:** Eigenschaft und Scope, Gegenbeispiel in Projektsprache, Modellfehler vs bestätigter Codefehler vs ungeklärte Zuordnung;
- **Grenzen:** keine Produktreparatur, Tool-Installation, Produktionsdaten, Remote-Aktionen oder Veröffentlichungen allein durch die Skill-Erstellung.

Das ist kleine dauerhafte Verifikationsmetadatenpflege, **kein** Lauf-Protokollarchiv oder Evidence-Ledger. Rohoutputs bleiben in bestehenden CI-/Run-Artefakten.

### Create und Update gemeinsam

Create startet mit genau einer wertvollen Eigenschaft. Update liest nur relevante Änderungen, benennt auch neue Schreiber auf geschützten Zustand und aktualisiert nur betroffene Verifikationsartefakte. Wenn eine echte Produktverletzung gefunden wird, kann das Rezept technisch erfolgreich demonstriert sein, während das Produkt ausdrücklich fehlerhaft bleibt. „Generator funktioniert“ und „Property gilt im Produkt“ sind getrennte Aussagen.

Ein nicht installiertes Tool, fehlende Ausführungsfreigabe, Timeout oder ungeklärte Modell-Code-Korrespondenz ergibt `blocked`/`unverified` beziehungsweise einen ausdrücklich unbewiesenen Entwurf — nie einen Pass. Keine silent fallback-„Beweise“ durch einen anderen Checker oder bloß mehr zufällige Tests.

**Vorläufige Namens-/Scope-Empfehlung, noch nicht beschlossen.** Wenn nach dem Pilot nur ein einzelnes Projekt das benötigt, kann zunächst dessen lokaler Verify-Skill genügen; den Katalog-Generator erst behalten, wenn er tatsächlich wiederverwendbaren Ablauf enthält.

## 6. Wann und wo referenzieren?

Die wichtige Trennung lautet: **Workflow konsumiert konkrete Projekt-Rezepte; Generatoren werden nicht bei jeder Änderung neu aufgerufen.**

| Stelle | Auslöser | Verweis / Aktion |
| --- | --- | --- |
| `shape-design`, Abschnitt Design quality / Spike | Eine konkrete Reihenfolge-/Invariantenfrage bleibt durch günstige bestehende Tests unbeantwortet | Begrenzten formalen Probe-Auftrag anbieten; für dauerhafte Wiederholung den neuen Generator vorschlagen. Vor Implementierung, nicht erst am Release-Ende. |
| `write-implementation-plan`, Lean verification default / Tasks | Akzeptanzkriterium braucht einen bereits vorhandenen Runtime- oder Formal-Check | Den bereits eingeführten Projekt-Rezeptverweis um die formale Auswahl ergänzen. Genau den Pfad in die vorhandene Validierungseinheit schreiben; kein zweiter Abschluss-Task. |
| Derselbe Plan, falls Rezept fehlt | Wiederholbares Projektwissen fehlt und dessen Erstellung ist genehmigt | Einen eigenen begrenzten Recipe-Task über `project-verification` oder `project-formal-verification` einplanen. |
| `orchestrate-implementation/references/manifest-and-briefs.md`, Worker brief Punkt 4 | Ein delegierter Task benutzt dieses Rezept | Pfad, Property/Journey, Bounds, Sollquelle, Ausführungsbudget und gültige Evidenz mitgeben. Eine allgemeine Skill-Verlinkung ersetzt kein vollständiges Briefing. |
| Projekt-`AGENTS.md` bzw. vorhandene lokale Agentenhinweise | Änderung berührt die im Rezept benannten Dateien, Funktionen oder denselben geschützten Zustand | Projektlokalen `verify-...` lesen und Sync prüfen; nur bei relevantem Delta den zugeordneten Check ausführen. Auf fremde Änderungen am selben Zustand achten. |
| Generierter Verify-Skill | Modell-/Harness-Drift nach relevanter Änderung | Auf Update-Modus des Generators verweisen; Lesezugriff und Driftmeldung sind nicht automatisch Schreibberechtigung. |
| `verification-before-completion` | Erfolgsaussage verwendet „verifiziert“, „bewiesen“ oder benennt die abgesicherte Property | Beweisart, aktuelle Zuordnung und Grenzen prüfen; nie aus einem Modellcheck UI-/Deployment-Erfolg ableiten. |
| `README.md` und `UPSTREAM_ADOPTION.md` | Neuer Generator wird tatsächlich angenommen | Generator vs konsumiertes Rezept und die bewusst ausgeschlossenen Defaults dokumentieren. |

Keine Verweise in jeden Host-Adapter, jeden Reviewer-Prompt oder jeden Release-Schritt kopieren. Ein fehlender optionaler Spezialskill blockiert keine fachfremde Arbeit. Wird er für den genehmigten Task benötigt, Installation separat klären statt Skill-Abhängigkeiten automatisch vorauszusetzen. Manual-only-Metadaten sind clientabhängig; `disable-model-invocation: true` allein ist kein portabler Nachweis der Aufruf- oder Autorisierungsgrenze. [L6, L8]

## 7. Was ausdrücklich nicht übernommen werden sollte

- Tägliche Voll-Audits, ein Agent je Feature, obligatorische neue Shipping-Prüfungen oder frische Solverläufe nach jedem Commit/Merge.
- Produktreparatur, Installationen, Testdatenänderungen, PRs oder Veröffentlichung als Nebenwirkung eines Generators/Maintainers.
- TLA+ für jede Funktion oder generierte Eingaben mit dem Etikett „formal bewiesen“.
- Eigenschaft aus beobachtetem Implementierungsoutput ableiten oder anhand geänderter Tests still abschwächen.
- Sync-Commit als magischen Korrespondenzbeweis; Modelle müssen semantisch zu heutigen Callern, Mutatoren und atomaren Schritten passen.
- Obligates `statechart`/mise/Java/Pele-Paket oder ein neuer generischer Harness ohne aktuellen Bedarf.
- Getrennte Creator-/Maintainer-Skills nur aus Upstream-Symmetrie; ein zusammengehöriger Create-/Update-Auftrag genügt je Rezeptfamilie.

## 8. Umsetzung nach Freigabe und passende Validierung

Kleinster sinnvoller Umfang: normaler Generator plus Vorlage, ein neuer Formal-Generator mit einer direkt verlinkten Vorlage, vier kurze Workflow-Anpassungen, gegebenenfalls ein Prototype-Verweis. In Planung und Orchestrierung die inzwischen vorhandenen Verweise präzisieren, nicht duplizieren. Der neue Planungstext nennt auch Typen, Schemas und statische Checks neben formaler Verifikation: deren konkrete Aussagekraft muss jeweils benannt werden; ein beliebiger statischer Check ist kein allgemeiner Beweis. `agent-guardrails` bleibt der Policy-Owner und muss dafür nicht um ein zweites Formal-Regelwerk wachsen.

Bei Übernahme: `README.md`, `UPSTREAM_ADOPTION.md`, `sources.json`, `THIRD_PARTY_NOTICES.md` und `CHANGELOG.md` mitpflegen. Die normale bereits adaptierte Quelle nicht nur wegen eines neuen Repository-HEADs umpinnen. Neues übernommenes Formal-Material auf den untersuchten Commit pinnen; die pstack-Lizenz nennt **MIT, Copyright (c) 2026 Lauren Tan**. [U10, L2, L8]

Spätere Prüfung muss die eigentlichen Fehlerrisiken abdecken: korrekte Auswahl zwischen normalem und formalen Rezept; kein automatischer Generator bei gewöhnlichen Änderungen; ein nach Codeänderung veraltetes grünes Modell wird nicht als Produktbeweis akzeptiert; ein echtes Gegenbeispiel bleibt Befund; fehlende Tools/Erlaubnis lösen keine Installation aus. Dazu vorhandene Struktur-/Linktests nutzen. Diese prüfen lediglich die Auslieferung von Anweisungen, nicht deren Befolgung. Ein kleiner genehmigter Pilot mit nachvollziehbarer Property und negativer Kontrolle ist nötig, bevor ein funktionierender Formal-Workflow behauptet wird; keine Benchmark-/Mutationstest-Kampagne als Nebenauftrag.

**Abschluss des Analyseauftrags: accept für die quellenbasierte Untersuchung; ask vor Umsetzung.** Es wurde keine Anwendung gestartet, kein Solver/Browser-Harness ausgeführt und keine Produkt- oder Skilltestsuite gefahren. Die Empfehlungen sind noch keine genehmigte Spezifikation.

## Quellen

### Upstream, immutable

- **U1:** [create-verification-skill](https://github.com/cursor/plugins/blob/2776ddd2355d6d6c8747d3964600f28daf62f049/pstack/skills/create-verification-skill/SKILL.md).
- **U2:** [Feature-Map-Index](https://github.com/cursor/plugins/blob/2776ddd2355d6d6c8747d3964600f28daf62f049/pstack/skills/create-verification-skill/references/feature-map-example/README.md).
- **U3:** [Create-note-Beispiel](https://github.com/cursor/plugins/blob/2776ddd2355d6d6c8747d3964600f28daf62f049/pstack/skills/create-verification-skill/references/feature-map-example/create-note.md).
- **U4:** [Search-Beispiel](https://github.com/cursor/plugins/blob/2776ddd2355d6d6c8747d3964600f28daf62f049/pstack/skills/create-verification-skill/references/feature-map-example/search.md).
- **U5:** [maintain-verification-skill](https://github.com/cursor/plugins/blob/2776ddd2355d6d6c8747d3964600f28daf62f049/pstack/skills/maintain-verification-skill/SKILL.md).
- **U6:** [create-formal-verification-skill](https://github.com/cursor/plugins/blob/2776ddd2355d6d6c8747d3964600f28daf62f049/pstack/skills/create-formal-verification-skill/SKILL.md).
- **U7:** [maintain-formal-verification-skill](https://github.com/cursor/plugins/blob/2776ddd2355d6d6c8747d3964600f28daf62f049/pstack/skills/maintain-formal-verification-skill/SKILL.md).
- **U8:** [statechart](https://github.com/cursor/plugins/blob/2776ddd2355d6d6c8747d3964600f28daf62f049/pstack/skills/statechart/SKILL.md).
- **U9:** [statechart Rendering](https://github.com/cursor/plugins/blob/2776ddd2355d6d6c8747d3964600f28daf62f049/pstack/skills/statechart/references/render.md).
- **U10:** [pstack MIT-Lizenz](https://github.com/cursor/plugins/blob/2776ddd2355d6d6c8747d3964600f28daf62f049/pstack/LICENSE).

### Lokaler Katalog

- **L1:** [project-verification](../../skills/skill-authoring/project-verification/SKILL.md), [Rezeptvorlage](../../skills/skill-authoring/project-verification/references/recipe-template.md).
- **L2:** [Bestehende Adoption](../../UPSTREAM_ADOPTION.md#cursor-pstack-verification-recipe-review), [Recherche 2026-10-16](2026-10-16-project-verification-skills.md).
- **L3:** [README / Boundaries](../../README.md#boundaries).
- **L4:** [agent-guardrails](../../skills/engineering/agent-guardrails/SKILL.md).
- **L5:** [verification-before-completion](../../skills/workflow/verification-before-completion/SKILL.md).
- **L6:** [planning-contract](../../skills/workflow/planning-contract/SKILL.md).
- **L7:** [write-implementation-plan](../../skills/workflow/write-implementation-plan/SKILL.md), [Orchestrierungs-Briefs](../../skills/workflow/orchestrate-implementation/references/manifest-and-briefs.md), [Review/Recovery](../../skills/workflow/orchestrate-implementation/references/review-and-recovery.md).
- **L8:** [Autorenregeln](../../skills/skill-authoring/effective-agent-skills/SKILL.md), [Autorenreferenz](../../skills/skill-authoring/effective-agent-skills/references/authoring-guide.md), [Strukturtests](../../tests/skills_test.sh), [Provenienz](../../sources.json), [Notices](../../THIRD_PARTY_NOTICES.md).
- **L9:** [shape-design](../../skills/workflow/shape-design/SKILL.md), [prototype-question](../../skills/workflow/prototype-question/SKILL.md).
