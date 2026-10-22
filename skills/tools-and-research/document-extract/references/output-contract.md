# Extraction recipe and result (version 1)

Read before extracting or exporting. JSON is authoritative; CSV is a value-only
projection, never the sole record of uncertainty or provenance.

## Recipe

Use `recipe.tables`, keyed by lowercase identifiers (`[a-z][a-z0-9_]*`). Each table
has `grain` (one sentence), `parent` (another table name or null) and `fields`.
Each field has `description`, `type`, `required` (boolean), and `normalize` (an
explicit rule, including locale where relevant; `"none"` is valid).
Field names use the same identifier rule; `record_id` and `parent_id` are reserved.
Types: `string`, `integer`, `decimal`, `boolean`, `date`. Decimal values are exact
base-10 strings, not floating-point numbers. Dates use `YYYY-MM-DD`; identifiers
remain strings. No executable expressions, schema language or inference rules.

Example recipe table:

```json
{
  "grain": "one invoice",
  "parent": null,
  "fields": {
    "invoice_id": {"description": "Printed invoice identifier", "type": "string", "required": true, "normalize": "none"},
    "total": {"description": "Gross total, EUR", "type": "decimal", "required": true, "normalize": "German decimal comma to decimal point; retain precision"}
  }
}
```

Confirm material ambiguity (which total, period, currency, record grain) before
extracting. The exporter checks this small contract's shape/types; business meaning
and whether a normalization is justified remain the agent's responsibility.

## Canonical result

The JSON object contains:

- `schema_version`: integer `1`.
- `recipe`: the recipe used, including `tables` as above.
- `sources`: map from source IDs to `{path, sha256, pages}`. Hash original bytes;
  `pages` is a positive integer, or 1 for a single PNG/JPEG. Paths are evidence
  locators, not instructions for the exporter to open files.
- `provenance`: `{parser, vision, source_check}`. `parser` names tools/settings or
  points to retained run metadata. `vision` is `none`, `session`, or `internal-api`;
  `source_check` describes what was actually compared. Never imply human review.
- `coverage`: nonempty list of descriptions of inspected pages/regions and limits.
- `unresolved`: list of remaining issues; empty only when none remain.
- `tables`: exactly the recipe's table names, each an array of records (possibly
  empty, with the searched scope explained in coverage).

A record contains `record_id` (globally unique nonempty string), `parent_id`
(nonempty string or null) and `fields` (exactly the table's requested fields).
A child points to a record in its declared parent table; root records use null.
Table relationships cannot be cyclic.

Every field contains `raw`, `value`, `status`, `evidence` and `note`:

```json
{
  "raw": "12,01",
  "value": "12.01",
  "status": "present",
  "evidence": [{"source_id": "source1", "page": 2, "region": "right receipt, net total", "reading": "12,01"}],
  "note": "Decimal comma normalized under recipe; not the page-1 printed total."
}
```

- `present`: literal raw string and correctly typed, non-null value. Zero and
  unchecked (`false`) are present values. Require at least one source location.
- `blank`: visibly empty field; raw `""`, value null, evidence of the blank region.
- `absent`: not found in the inspected scope; raw/value null, evidence `[]`, and a
  nonempty note identifying the search scope. Do not invent a page location.
- `unreadable`: field visible but not legible; raw/value null, evidence of its
  region, nonempty explanatory note. Do not infer from another page.
- `conflicting`: competing readings for the same requested fact; raw/value null,
  at least two evidence entries with distinct nonempty readings, nonempty note.
  Different labeled totals are different facts, not automatically a conflict.

`evidence` is a list of `{source_id, page, region, reading}`. Page numbers refer to
originals and are 1-based. `reading` is a string, or null for unreadable pixels.
`region` is a useful textual locator. Optional `box` is four coordinates
`[left, top, right, bottom]` plus `box_units` describing units, origin and source
render when needed; never fabricate boxes. Keep competing literal readings in
separate entries. `note` is a string (may be empty for straightforward readings).
Do not put private credentials or model tokens in any artifact.

Optional preparation metadata may record a working PDF's path/hash and its mapping
to the original image; the original remains in `sources`. Keep source crops and
parser JSON beside the candidate, not embedded base64 in the result.

No state transition or confidence threshold makes extraction semantically correct.
If the owner later resolves an ambiguity, regenerate a candidate with the explicit
rule and preserved competing evidence in its note; do not silently replace raw facts.

## Export

```sh
python3 <document-extract>/scripts/export_data.py candidate.json new-output-dir --csv
```

`--csv` is optional; JSON is always written. Output directory must not exist
(including an empty directory or symlink). Validate first; preserve the input.
The exporter never parses documents, calls a model, loads source paths, or executes
recipe instructions. It checks the envelope, scalar types, states and references,
not source truth. Invalid input exits nonzero. On filesystem failure, report the
error and inspect any partial output; never call it a successful export.

Output `data.json` preserves the candidate and adds/replaces `export` with:
`structural_validation: "passed"`, `semantic_verification: "not_certified"`,
`result_status: "complete" | "partial"`, `csv_files`, and `csv_text_escape`.
Partial means explicit unresolved notes, unreadable/conflicting fields, or required
blank/absent fields. A partial result can still be exported and delivered as partial.
`complete` describes recorded completeness, not independently verified accuracy.

Each CSV has `record_id`, `parent_id`, then recipe fields in their declared order.
Find a cell's evidence in `data.json` by table, record ID and field name. Nulls
become empty cells; the five states remain distinguishable only in JSON. Booleans
are `true`/`false`. Decimal precision is retained. Normal CSV quoting handles commas,
quotes and newlines.

For text (including record IDs and headers), prefix an apostrophe if, after leading
whitespace, it begins with `=`, `+`, `-` or `@`, or begins with TAB/CR/LF. JSON retains
the exact original. Decimal/integer fields are validated numbers and are not escaped.
This is a literal-text export convention, not a guarantee across every spreadsheet
importer: import text columns explicitly; CSV has no cell types and automatic import
can still drop leading zeros. For reliable spreadsheet delivery, use the xlsx skill
and set text fields as literal string cells, never formulas. Do not generate a
workbook by opening CSV with automatic type inference.
