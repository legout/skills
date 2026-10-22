# Tables: faithful transcription versus structured records

For Markdown transcription, preserve tables and relationships in the reading view;
a GFM table is only a candidate. Apply the main skill's coverage and semantic gates.
For requested fields, rows or tables as JSON/CSV, discover `document-extract`; it
owns recipes, source evidence, uncertainty and data export. Workbook delivery goes
to `xlsx`. A missing skill is a prerequisite to report, not permission to assume a
sibling path or install it automatically.

## Optional Camelot technique

For a suitable digital PDF with a text layer, Camelot can produce candidate cell
data. Prefer existing tools and consult installed `--help`/API documentation for
backend requirements; do not install or run it merely to add a second parser.

```python
import camelot

tables = camelot.read_pdf("input.pdf", pages="all", flavor="lattice")  # ruled tables
# Use stream instead when text positions, rather than ruling lines, define cells.
for table in tables:
    print(table.page, table.order, table.parsing_report)
    # Inspect table.df against the original page; keep every candidate accounted for.
```

Accuracy scores are inspection signals, not acceptance thresholds. Never silently
drop a table because its score is low; record it as unresolved or reprocess the
named failed region. High scores do not prove column placement, blank cells,
multiline rows or page continuity. Retain source page/table identities and check
associations before exporting through the extraction workflow.

For scanned/complex tables, prefer structural parsing rather than assuming OCR
restores the grid. If the source remains unclear, retain its image and explicit
uncertainty. Neither successful CSV serialization nor arithmetic agreement makes
the candidate source-faithful.
