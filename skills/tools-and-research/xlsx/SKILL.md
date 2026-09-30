---
name: xlsx
description: Create, edit and verify Excel XLSX/XLSM workbooks and XLTX templates, including formulas, native charts and financial-model conventions. Use when a spreadsheet file is the deliverable; use DuckDB for analysis and document-to-markdown for read-only conversion.
---

# Excel workbooks

Use `openpyxl`: `uv run --no-project --with openpyxl script.py`. Bundled scripts declare their own dependencies; resolve their paths relative to this skill. CSV/TSV inputs may be analyzed with DuckDB/Polars and exported to the requested workbook rather than duplicating a data-analysis skill.

## Workflow

1. Inspect sheets, formulas, cached values, merged cells, input conventions, charts and external workbook links before editing. Load formula strings with `data_only=False`; use a separate `data_only=True` load for inspecting cached values. Never save the cached-value load over the formula-bearing workbook.
2. Keep the original and use a new output. Preserve formulas/styles in existing files; follow the user's exact sheet names, headers, units and calculation rules. Read [workbook features](references/workbook-features.md) for charts, templates and macro limitations; read [financial models](references/financial-models.md) for financial outputs.
3. Write formulas, not precomputed constants, when inputs must remain editable. Verify representative formulas against independently calculated expectations. `openpyxl` does not calculate formulas.
4. For compatible XLSX files, run the recalculation helper. It invokes LibreOffice with an isolated profile, checks cached results for errors/missing values and checks formulas were not lost. It publishes a **new output only on success**. Read [formula verification](references/formula-verification.md) for engine differences and refusal cases.
5. Reopen the final workbook to verify sheet names, key inputs, formulas and calculated results. Validate structure and render/inspect relevant print pages; separately check charts and sheets in Excel when print layout does not show them.

```sh
uv run --no-project <skill>/scripts/recalc.py draft.xlsx calculated.xlsx
uv run --no-project <skill>/scripts/office.py validate calculated.xlsx
uv run --no-project <skill>/scripts/office.py render calculated.xlsx workbook-preview
```

## Output contract

Helpers emit JSON. Recalculation returns `status: ok`, formula count, `errors: []` and output path; formula errors return `status: errors` with cell locations and exit 1. Missing LibreOffice, external workbook links, macros or engine-sensitive formulas return `status: error` and exit 2. A clean exit establishes evaluation checks, **not** financial correctness.

Rendering creates `document.pdf`, page PNGs and a contact sheet. LibreOffice is required; default installation paths on macOS/Windows and PATH are searched. If unavailable, verify in Excel; report checks not performed explicitly. ZIP/XML/relationship validation is structural, not full schema validation. Do not present unchecked formula caches or uninspected previews as verified.

Keep VBA with `keep_vba=True` for `.xlsm`; the recalculation helper refuses macro files rather than claiming their preservation. Complex external-link models, dynamic arrays and unsupported Excel features need Excel-native checks. Editing invalidates document signatures. Deliver the path, changed sheets, evaluated examples and any remaining limitations.

Sources: [openpyxl](https://openpyxl.readthedocs.io/en/stable/) · [LibreOffice CLI](https://help.libreoffice.org/latest/en-US/text/shared/guide/start_parameters.html). Instructions and helpers are independently authored.
