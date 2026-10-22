# Document extraction and Markdown routing — bounded implementation plan

**Status:** Revision 1 implemented and accepted within the synthetic scope on 2026-10-22. Owner execution approval: “Go ahead with the plan.” Changes remain uncommitted and uninstalled; no push or release.
**Date:** 2026-10-22
**Goal:** Add schema-driven document extraction while reusing the existing local parsing tools and simplifying, not weakening, Markdown conversion.

## Authority and capture checkpoint

- **Behavioral source:** the bounded design in this conversation: two task-oriented skills, shared existing parsing helpers, JSON/CSV extraction and an xlsx handoff; no new parsing framework. The owner accepted the direction with “Plan sounds good” and requested: “Write the bounded implementation plan. Use synthetic fixtures initially; retain the current privacy boundary.”
- The original request authorized planning only; the subsequent “Go ahead with the plan” approved revision 1 for implementation. No separate specification is needed for this bounded change.
- **Vocabulary:** no project glossary exists and no new domain vocabulary requires one. Here, a *recipe* specifies requested fields and record grain; *evidence* identifies the source supporting a reading. These definitions belong in the new skill's output reference.
- **Decisions:** no ADR warranted: skill composition and helper reuse are bounded, reversible choices. No runtime service or storage architecture is being introduced.
- **Uncertainty:** representative private documents are deliberately deferred. Synthetic acceptance cannot establish production extraction quality. No unresolved architecture decision blocks planning.
- **Planning contract:** version 1; installed revision/provenance unknown. Source checkout inspected at `a28a37a2de7b969a507f0ec138efe2cc653c0b8e`.
- **Artifact location:** existing legacy `docs/plans/`; sequence 0003 follows existing 0001 and 0002. Do not migrate or edit unrelated plans/research notes.

## Scope and acceptance criteria

- **A1 — Separate purposes:** `document-extract` owns requested fields and repeating records from PDFs and single-page PNG/JPEG document images. `document-to-markdown` retains faithful reading/transcription, including its existing non-PDF formats. Markdown is not a mandatory extraction intermediate.
- **A2 — Reuse with explicit prerequisites:** existing parsing/render/crop helpers remain owned by `document-to-markdown`. Discover the installed skill directory; never assume repository-relative paths exist after a selective install. Missing prerequisites produce a clear install request, not an automatic installation or copied parser implementation.
- **A3 — Grounded records:** recipes define grain, fields, types, relationships, locale/normalization and missing-value handling. Results preserve raw and normalized values, evidence and unresolved states; requested coverage is explicit. No guessing, silent reconciliation or automatic semantic certification.
- **A4 — Useful exports:** canonical JSON retains evidence; flat CSVs retain record/parent identifiers and link back to that JSON. Excel delivery uses the existing xlsx skill, not a second workbook implementation.
- **A5 — Simpler routing, preserved behavior:** present native extraction, structural parsing and targeted approved vision as the ordinary choices. Retain specialist engines and supported Office/legacy helper invocations. Fix stale table handoffs and carry forward the installed financial-context safeguard.
- **A6 — Same privacy and preservation boundary:** local parsing; public package/model downloads only; no public document uploads, automatic network fallback, endpoint-policy changes or TLS bypass. Native vision requires an authorized session; the existing internal endpoint remains subject to its current allowlist. Preserve originals and existing outputs, and treat document instructions as data.
- **A7 — Bounded evidence:** synthetic document-to-data journey, targeted routing evaluation and existing mandatory catalog checks. Report structural checks separately from observed semantic accuracy and model authorization.

**Non-goals:** Azure/Mendix/API integration; databases or queues; bulk ingestion service; general-purpose schema engine; a third parsing skill; parser/version upgrades; automatic backend benchmarking; standalone CSV/JSON skills; broader Office extraction; multi-frame image formats; private-document processing; installation, commits, push, tickets or release.

## Current implementation and constraints

- `skills/tools-and-research/document-to-markdown/scripts/convert_docling.py` already emits `document.json`, Markdown, images, per-page exports and `run.json`. Reuse its JSON and original evidence, not only its Markdown. It accepts PDFs; do not claim it accepts images directly.
- The Docling helper defaults to full-page OCR; `--native-text` already selects hybrid native text/OCR. Document correct invocation for digital content without changing the existing CLI default.
- `artifact_utils.py`, `render_pdf.py` and `crop_image.py` already supply hashing, page identities and preservation guards. Keep these files and their lockfiles in place.
- For a structured PNG/JPEG input, use a local, lossless image-to-single-page-PDF preparation with already used PyMuPDF tooling. Keep the original image/hash as authoritative evidence and record the working PDF/hash and page-1 mapping. This is task preparation, not a new parser/helper subsystem. Approved native vision may instead read the original directly when appropriate.
- `references/tables.md` currently treats a Markdown table as finished and drops low-scoring Camelot tables from export; both conflict with the main fidelity gate. `pdf/SKILL.md` and `pdf/references/operations.md` also name the unavailable `table-extractor` handoff.
- The installed `/home/volker/.agents/skills/document-to-markdown/SKILL.md` has a financial-context paragraph absent from the repository: preserve section, currency, period and date meaning; never merge cash receipts, accrual details and annual subtotals. Bring that rule into the repository without replacing the installed copy.
- Python 3.12+ and `uv` match existing helper usage. Existing model environments remain pinned. No new third-party runtime dependency is planned; one small stdlib-only export helper is sufficient.
- Required conventions: root `AGENTS.md`, `README.md`, `skills/skill-authoring/effective-agent-skills/SKILL.md`, and `tests/skills_test.sh`; preserve provenance/notices. New locally authored material does not require invented upstream attribution or pin changes.

## Proposed extraction interface

Document this once in `document-extract/references/output-contract.md`; the skill links directly to it before extraction/export.

**Recipe:** a small agent-readable JSON object with named tables, record grain, parent relationship where needed, and named fields with descriptions, scalar types, requiredness and normalization rules. No arbitrary code or expression execution. Missing material business meaning prompts a question; output-format preferences alone do not create a new skill. Recipe validation is an agent responsibility in v1, not a universal schema compiler.

**Canonical result:** `schema_version: 1`, the recipe used, source identities/hashes and processing provenance, named tables containing records, and coverage/unresolved notes. Each record has a unique `record_id`, optional `parent_id`, and named fields. Each field holds:

- `raw`: literal source reading or null when no single reading is established;
- `value`: normalized scalar or null; identifiers remain strings and exact decimals use decimal strings;
- `status`: `present`, `blank`, `absent`, `unreadable` or `conflicting`;
- `evidence`: source ID, original page (page 1 for a single image), region/box when actually available, and the supporting literal reading; conflicts retain all competing readings;
- a concise note when normalization or uncertainty needs explanation.

`blank` means the source field exists but is empty; `absent` means the requested field was not found in the inspected scope. Zero and unchecked are present values. Unreadable/conflicting values remain null unless an explicit owner rule resolves them, with that derivation disclosed. Evidence can point to an empty field or unreadable region without fabricating text. An absent-field claim records the searched scope instead of an invented location.

Record source-check scope explicitly; never label agent checking as independent human verification. Required-but-unresolved fields make a result partial, not a fabricated success. Different labeled totals remain different fields; disagreement is an inspection signal.

**Export seam:** `python3 <document-extract>/scripts/export_data.py result.json output-dir [--csv]`. Validate the documented result envelope, scalar values, states, record/parent references and source references before writing. This checks structure, not whether a page supports a claim or whether the recipe's business meaning is correct. Refuse existing/nonempty output directories and input/output collisions. Keep canonical `data.json` with evidence; `--csv` additionally emits one file per table with record/parent IDs and requested value columns. Constrain table names to safe filename identifiers. Use stdlib `json` and `csv`, not handcrafted quoting.

CSV nulls are empty cells; canonical JSON remains authoritative for why they are empty. Document that CSV cannot enforce spreadsheet cell types or preserve leading zeros on automatic import. Formula-looking text must not silently become spreadsheet formulas: preserve exact raw text in JSON and use an explicitly documented literal-text escape in CSV for dangerous text prefixes; xlsx delivery sets those cells to text. Do not apply text escaping to typed numeric values. Record this export transformation, not as a source correction.

## Execution order — one sequential owner

Shared instructions and routing make parallel writers unnecessary. Each slice leaves usable documentation and runnable validation; no generic prefactor or helper relocation is needed.

### T1 — Extract one synthetic document to evidence-backed JSON/CSV

**Prerequisites:** approval of revision 1; existing helper skill discoverable. **Covers:** A1–A4, A6–A7.

**Create:**
- `skills/tools-and-research/document-extract/SKILL.md`
- `skills/tools-and-research/document-extract/references/output-contract.md`
- `skills/tools-and-research/document-extract/scripts/export_data.py`
- `skills/tools-and-research/document-extract/evals/evals.json`
- `skills/tools-and-research/document-extract/evals/fixtures/extraction.md`
- `tests/document_extract_test.py`

**Consumes:** source files, recipe, existing parser JSON and original images. **Produces:** reviewed extraction candidate plus JSON/CSV artifacts and disclosed unresolved readings.

- [x] Write the new skill's narrow trigger, workflow, data boundary and dependency discovery. Reuse only parsing/evidence portions of document-to-markdown; do not require its full-transcription acceptance loop for an intentionally scoped field extraction.
- [x] Author one synthetic two-page invoice/form scenario and independent expected readings before model execution. Include repeating rows, a blank identifier, zero, a deliberately unreadable region, conflicting unlabeled duplicate readings, different clearly labeled totals, decimal-comma amounts and a text value `=1+1`. Include ordinary document prose that must not be treated as an instruction. Use only invented entities.
- [x] Let `tests/document_extract_test.py --make-fixture DIR` generate the PDF plus a PNG page using the existing ReportLab/rendering approach. Keep expected readings in the authored fixture, not derived from parser/model output. No generated binaries or model caches are committed.
- [x] Add one table-driven export-contract regression at the public CLI seam; first demonstrate failure because the helper is absent, then implement the minimal exporter. It covers valid round-trip records, null/status distinctions, parent/source references, escaping and refusal to overwrite. Invalid examples are mutations of that same small authored result, not a second test matrix.
- [x] Document the image preparation/source mapping, JSON/CSV limitations and conditional xlsx handoff. If the required skills are missing, stop with the named prerequisite; do not silently install them.
- [x] Add `--check-result RESULT_DIR` to the test script for comparison with the independently authored synthetic expectations. This is a scenario-specific oracle, not a reusable extraction engine. Keep the expected-answer fixture out of the extracting agent's input.

**Validation unit V1:** normal risk; `new-test` for the exporter plus one real skill journey in T3. Reachable failures: false zero/null equivalence, displaced line items, lost evidence, altered identifiers, overwritten files and formula-like text interpreted as executable spreadsheet content. The JSON/CSV test proves serialization and guards, not OCR or semantic accuracy.

**Focused command:** `uv run --script tests/document_extract_test.py` (proposed file, created in this task). Expected: independent valid values survive export; invalid envelopes/existing outputs fail before output mutation. Reuse that passing result unless exporter, contract, fixture or relevant environment changes.

**Completion:** the skill can guide the source-to-record workflow and the export seam is checked. Do not claim end-to-end extraction quality until V3.

### T2 — Simplify Markdown routing and replace stale handoffs

**Prerequisite:** T1 defines the new target. **Covers:** A1–A2, A5–A6.

**Modify only:**
- `skills/tools-and-research/document-to-markdown/SKILL.md`
- its `references/tables.md`, `references/structured-pdf.md`, `references/fallbacks.md`
- its `evals/evals.json` and `evals/fixtures/semantic-routing.md`
- `skills/tools-and-research/pdf/SKILL.md` and `references/operations.md`
- `README.md` and `CHANGELOG.md` (Unreleased only)

**Consumes:** the new skill name/contract and unchanged parser interfaces. **Produces:** unambiguous routing without dropping existing formats or helper invocations.

- [x] Present three ordinary routes: native extraction; Docling for structure/scans; targeted approved vision for unresolved regions. Move specialist MinerU/RapidOCR/liteparse choices behind explicit conditions, not a sequential engine ladder.
- [x] Explain `--native-text` for digital structural PDFs and the scan default without changing helper behavior. Retain language/resource constraints and skip unsuitable stages.
- [x] Replace `table-extractor` references with the new extraction owner. Keep Camelot as an optional targeted technique, but never silently discard low-scoring tables or certify output by its accuracy score.
- [x] Remove the stale fallback suggestion to use lightweight OCR indiscriminately for complex pages. Keep existing Office/other-format coverage and local-only restrictions.
- [x] Preserve all semantic/privacy gates and carry in the installed financial-context safeguard. Narrow trigger wording so schema-driven extraction does not compete with faithful Markdown transcription.
- [x] Update the catalog and Unreleased notes. Document explicit co-installation of document-extract and document-to-markdown; xlsx is needed only for workbook delivery. Do not change any installed directory.

**Validation unit V2:** low-risk documentation/routing; `existing-check`, no new parser tests. Extend existing routing eval data with a paired Markdown-versus-data request and missing-dependency/privacy refusal expectations. Evaluate the existing three scenarios and the new pair once during T3; judge choices against approved boundaries, not model agreement. Do not use fresh subagents without execution authorization.

**Completion:** existing Markdown workflows remain documented; extraction has one owner; searches find no obsolete `table-extractor` handoff in the touched document/PDF instructions. Existing parser/script versions and invocations are unchanged.

### T3 — Prove the bounded journey and hand off the candidate

**Prerequisites:** T1–T2. **Covers:** A1–A7. **Files:** no additional production files; only in-scope corrections if warranted.

- [x] Generate one fixture in a fresh temporary directory with `uv run --script tests/document_extract_test.py --make-fixture DIR`.
- [x] Follow the new skill on that PDF using local parsing and source inspection; request JSON and CSV. The extracting run sees the source and recipe, not the expected answers. Use the PNG page as a bounded input-route check of the same scenario, not another full parser benchmark. If approved vision is unavailable, report that prerequisite and retain unresolved readings; do not broaden the boundary because the data is synthetic.
- [x] Run `uv run --script tests/document_extract_test.py --check-result RESULT_DIR`; inspect original pages/crops for field associations and the declared source-check scope. Confirm the deliberately unreadable case stays unresolved rather than guessed. Stop on a material mismatch; no engine tournament.
- [x] Evaluate V2 routing cases once. Record actual observed behavior; static frontmatter/link checks cannot substitute for routing evidence.
- [x] Run `uv run --script tests/document_to_markdown_test.py` once for existing artifact behavior; do not rerun an applicable earlier pass on unchanged inputs/environment. No Docling/MinerU comparative performance run and no Office runtime suite: those implementations are untouched.
- [x] Carry the mandatory `.github/workflows/test.yml` gates unchanged: shell syntax checks for the two catalog/handoff runners; JSON parsing of existing orchestration evals and `sources.json`; `bash tests/skills_test.sh`; `bash tests/orchestrator_handoff_test.sh`; `git diff --check`. Also parse the new/changed document eval JSON. The scheduled source-freshness workflow is not an extra per-task upstream audit, and no source pins are being changed.
- [x] One candidate review covers the new contract/exporter, routing, privacy boundaries and integration effects. A reviewer must receive the complete agent-guardrails dispatch contract, A1–A7, the written conventions and real inputs inline; links alone are insufficient. The parent owns dispositions and fixes. At most one authorized fix pass and one delta recheck; remaining blockers go to the owner.
- [x] Before substantive-code handoff, offer one `simplify-code` pass under the repository rule; run it only if accepted. Do not chain deslop or repeat green checks for ceremony.
- [x] Report exact verification scope, unresolved limitations and accept/fix/hand-back outcome. No installed-copy update, commit, push, release or cleanup of unrelated work.

**Validation unit V3:** normal risk; one scenario-specific source-to-export journey plus existing catalog checks. Oracle: authored fixture and direct source inspection, not extracted output or a second model's confidence. Changes to extraction instructions, parser settings, fixture, export semantics or relevant environment invalidate only the affected evidence. High-stakes financial correctness on real documents remains unverified.

## Requirement map and handoff

- A1: T1 skill boundary + T2 routing; V2/V3.
- A2: T1 dependency discovery + T2 install guidance; V2 missing-prerequisite case.
- A3: T1 output contract; V1 structure and V3 source relationships.
- A4: T1 exporter and xlsx handoff; V1/V3. Workbook generation itself is not newly implemented or certified.
- A5: T2 instructions and installed-rule reconciliation; V2 and existing artifact checks.
- A6: both skills' written boundary and T1 export preservation; V1 refusal/literal-text behavior, V2 refusal routing, candidate review. Asset: source documents and faithful exported data. No new service/auth/credential boundary; actual external-document content must not alter instructions or escape into formula execution. No hypothetical stolen-secret or malicious-admin scenarios.
- A7: T3, with no unrequested broad benchmarks or verification loops.

After approval, use the existing `orchestrate-implementation` handoff contract with this exact revision, bounded behavioral source, capture outcome and planning-contract version/provenance. The original plan-writing request granted no execution authority; the subsequent owner approval permitted implementation and the planned validation/review, not installation or publication. Do not invent a second execution router or publish tracker tickets.

## Execution outcome — 2026-10-22

T1–T3 completed by the parent as the only repository writer; two fresh native Pi
children exercised the synthetic journey/routing and reviewed the stable candidate.
Both children completed; no pending supervisor requests. Independent review found
no issues; no fix/re-review cycle was needed. The optional simplify-code pass was
offered, not requested, and not run. Outcome: **accept** for the approved scope.

Verified evidence lives under `$BB_THREAD_STORAGE/document-extract/` in this thread:

- `export-red.log`: expected initial failure for the absent exporter;
  `export-green.log`: one table-driven public-CLI check passed.
- `markdown-tests.log`: seven existing artifact tests passed; `catalog.log`:
  mandatory catalog/handoff/CI checks passed. Changed frontmatter also parsed as
  strict YAML. LSP: exporter clean; the test file has editor-only ReportLab source
  resolution warnings, while its uv runtime and fixture generation passed.
- `exercise-report.md` and `exercise/result/`: local PyMuPDF native PDF parsing,
  authorized session image inspection, JSON/CSV delivery and PNG-to-working-PDF
  preparation checked. No Docling/MinerU benchmark or remote OCR was performed.
- `journey-oracle.log`: parent-run independent authored oracle passed, including
  values/states, associations, source hashes/page identities and CSV projections.
  Parent inspected both original renders and the canonical result. The correct
  fixture result is partial: unreadable approval and conflicting references remain.
- `exercise/routing-responses.json`: six responses inspected against the existing
  and new expectations; correct ownership, native/structural routing, missing-skill
  handling and privacy refusal. `review-report.md`: independent candidate pass.

Existing parsing helper files/versions and unrelated worktree files were preserved.
No installed-copy update, commit, push or release. Passing checks were not rerun
for this outcome-only plan update. This plan is the durable project capture; no
second wiki copy or evidence ledger was created.

## Owner-approved vision-routing follow-up

The owner subsequently specified ordered providers for GPT-6 Luna, Haiku 5.5 and
Gemini 3.8 Flash, plus native Codex/Claude Code/GitHub Copilot/agy choices. The
canonical policy now lives in document-to-markdown's `references/vision.md`; both
skills point to it. Multi-model selection uses the listed family order, then the
owner's provider order among available, image-capable and document-authorized
routes. Native harnesses do not switch to another installed CLI. Copilot Luna uses
small targeted context; runtime limits and exact IDs are discovered, not assumed.
This is one-child selection, not a model retry ladder, pricing claim or blanket
permission to process documents with another provider.

Outcome: **accept** for this instruction-only follow-up. Added one routing-only
evaluation scenario covering provider precedence, native harnesses, missing pixel
delivery and launch-failure handling. Eval JSON, catalog/link validation and diff
whitespace checks passed (`vision-policy-checks.log` in the existing thread storage).
No live model calls or cross-harness tests were run for this follow-up; earlier
exporter/parser evidence remains applicable because runtime code is unchanged.
No installed-copy, credential, provider configuration or internal HTTP-helper change.

**Residual limits:** synthetic samples cannot establish OCR/handwriting accuracy across real document populations; JSON schema validity cannot establish source truth; CSV loses type information unless imported deliberately; installed copies can drift and require a separately authorized update. Optional model downloads may be resource-heavy: missing runtime/resource prerequisites block the relevant journey rather than authorize a public endpoint or weaker success claim.
