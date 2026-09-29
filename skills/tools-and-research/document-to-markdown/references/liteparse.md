# liteparse — PDF escalation leg (mixed text/scan, per-page control)

LlamaIndex's local PDF parser (Rust core, PDFium, bundled Tesseract OCR). PDF only — never use it for Office formats (it routes those through LibreOffice; anydoc owns them). Fully local.

## Decision rule

| Situation | Action |
| --- | --- |
| anydoc exit 0 | done — do not call liteparse |
| anydoc exit 3, `lit is-complex` flags **some** pages | `lit parse --format markdown` — text pages stay native, only flagged pages get OCR |
| anydoc exit 3, **all** pages flagged | stay on the RapidOCR/VLM leg ([ocr.md](ocr.md)) |
| need page ranges, per-page verdicts, screenshots, bounding boxes | call liteparse directly |
| anydoc PDF output mangled (e.g. reading order) | one retry with liteparse markdown |

## Commands

```bash
# Per-page needs-OCR verdict — text-layer only, cheap. Exits non-zero if any page is flagged.
uvx --from liteparse lit is-complex report.pdf

# Mixed-vs-fully-scanned split in one line:
uvx --from liteparse lit is-complex report.pdf --compact \
  | jq '{total: length, ocr: ([.[] | select(.needs_ocr)] | length)}'

# Parse with selective OCR to Markdown
uvx --from liteparse lit parse report.pdf --format markdown --ocr-language deu -o report.md

# Page range only
uvx --from liteparse lit parse report.pdf --format markdown --target-pages "1-5,10" -o report.md
```

## Rules

- Local only: bundled Tesseract (the default). Never `--ocr-server-url` at a public endpoint.
- `--ocr-language deu` for German. `.traineddata` downloads on first use (package/model installs are fine); air-gapped: `TESSDATA_PREFIX` → local tessdata dir.
- Markdown reconstruction is heuristic: dense/multi-level tables and heavy multi-column layouts can render imperfectly. Complex scan pages belong to the VLM tier ([ocr.md](ocr.md)); tables as data belong to camelot ([tables.md](tables.md)).
- Encrypted PDFs: `--password` exists, but the qpdf rule stands — decrypt once, then route normally.
