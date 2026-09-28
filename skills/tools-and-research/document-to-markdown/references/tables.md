# Tables — when the deliverable is data, not markdown

Two different asks, two different paths:

| Ask | Path |
| --- | --- |
| "Convert this document to markdown" (tables included) | anydoc — it already emits GFM tables. Done, nothing here. |
| "Extract the tables from this PDF as CSV/DataFrames" | camelot, below — or defer to the **table-extractor** skill for full depth |

## Quick path (camelot via uv)

```python
# run: uv run --with "camelot-py[base]" --with pymupdf python extract.py input.pdf
import camelot

tables = camelot.read_pdf("input.pdf", pages="all", flavor="lattice")  # bordered tables
if not tables:
    tables = camelot.read_pdf("input.pdf", pages="all", flavor="stream")  # borderless

for t in tables:
    if t.accuracy >= 80:
        t.df.to_csv(f"table_p{t.page}_{t.order}.csv", index=False)
        print(f"page {t.page} · accuracy {t.accuracy:.0f}% · {t.df.shape}")
```

- `lattice` = ruled tables, needs ghostscript (`brew install ghostscript`).
- `stream` = borderless, uses text positions.
- Accuracy below ~80 → tune `line_scale`/`row_tol` or hand the job to the **table-extractor** skill (visual debugging, column hints, multi-page merge).
- Scanned tables: camelot needs a text layer — OCR first does not restore the grid. State the ceiling; don't fabricate structure.
