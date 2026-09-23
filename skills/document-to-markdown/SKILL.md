---
name: document-to-markdown
description: "Convert or read any local document — PDF (text or scanned), Word, PowerPoint, Excel, OpenDocument, RTF, EPUB, CSV, images, HTML, notebooks — into agent-optimized Markdown by routing to the best engine (anydoc, RapidOCR, camelot, markitdown), with a company-internal multimodal fallback (gpt-5.6-luna / qwen-3.8-27b) for very complex scans. Local-first: no public APIs. Use when asked to 'convert X to markdown', 'read/extract the content of this document/deck/workbook', 'what's in this PDF', to make any document agent-readable, or to OCR an image or scan. Do NOT use for: creating/editing native Office files (docx/pptx/xlsx skills), precise table extraction as data (table-extractor skill), or data analysis of CSV/Excel (read-file)."
---

# Document to Markdown

One router, four engines — local by default, company-internal VLM for the hard pages. Any document in, agent-optimized Markdown out.

## Hard rule: data stays inside the company

Default is fully local inference. The only exception is the OCR **VLM fallback tier** ([references/ocr.md](references/ocr.md)), which sends flagged page images to the company-internal multimodal endpoint (`gpt-5.6-luna` / `qwen-3.8-27b`) — never a public API. Never use:
- `anydoc --ocr hosted` (uploads the document to Firecrawl)
- `markitdown --use-plugins`, `llm_client`, audio transcription, or YouTube URLs (public APIs)
- MinerU or any other hosted conversion API

Package installs (`npx`, `uv`, ONNX model downloads) are fine.

## Prerequisites

| Engine | Needs |
| --- | --- |
| anydoc | Node 20+ (`npx`) |
| RapidOCR | `uv` (rapidocr + onnxruntime — pure wheels, ~50–80 MB total) |
| camelot | `uv` + ghostscript for lattice mode (stream needs nothing) |
| markitdown | `uv` |

Windows colleagues: `winget install astral-sh.uv OpenJS.NodeJS.LTS qpdf` (+ `ArtifexSoftware.GhostScript` only for camelot lattice). Every OCR-leg dependency is a plain wheel — no paddlepaddle, no poppler, nothing that needs a compiler.
Corporate network: `npx`/`uv` package downloads may need `HTTPS_PROXY` or internal registry mirrors.

## Routing

| Input | Engine | Command |
| --- | --- | --- |
| `.docx .doc .pptx .ppt .xlsx .xls .xlsb .odt .ods .odp .rtf .epub .csv` | anydoc | `npx -y @firecrawl/anydoc file -o file.md` |
| `.pdf` (text-based) | anydoc | same — exit 0 means done |
| `.pdf` (scanned) | RapidOCR | anydoc exits **3** → [references/ocr.md](references/ocr.md) |
| `.png .jpg .jpeg .webp .bmp` | RapidOCR | [references/ocr.md](references/ocr.md) |
| Complex scan (tables/math/handwriting) | internal VLM | tier 2 in [references/ocr.md](references/ocr.md): `gpt-5.6-luna` / `qwen-3.8-27b` |
| `.html .ipynb .msg .zip .json .xml` | markitdown | `uvx --from 'markitdown[all]' markitdown file -o file.md` |
| Encrypted PDF | qpdf first | `qpdf --password=PW --decrypt in.pdf out.pdf`, then route normally |
| Deliverable is **tables as data** | camelot | [references/tables.md](references/tables.md) — not the markdown path |

The exit code IS the scanner — no separate detection step:

```text
npx -y @firecrawl/anydoc report.pdf -o report.md
# exit 0 → text PDF, done
# exit 3 → pages need OCR → RapidOCR (references/ocr.md)
# exit 1 → could not convert → try markitdown fallback, then report failure
```

## Output conventions

- Default: write `<stem>.md` next to the input (`-o`), don't stream huge documents into context — read the parts you need.
- Report which engine was used and the page/slide/sheet count.
- OCR output: state that it is OCR and flag low-confidence regions instead of presenting them as exact.
- If a PDF converts to near-empty, repeated, or `�`-filled text, treat it as scanned and take the OCR leg.

## Boundaries (other skills own these)

- Tables as DataFrames/CSV/Excel with accuracy scores → `table-extractor` skill
- Creating/editing native files → `docx` / `pptx` / `xlsx` / `pdf` skills
- Analyzing CSV/Excel data → `read-file` (DuckDB), not markdown conversion
- Excel with live formulas: markdown gives cached values only — formula work belongs to the `xlsx` skill

## Known ceilings

- `# ponytail: scanned tables — tier-1 OCR recovers text, not structure; the VLM tier in ocr.md is the in-house upgrade, Docling if a fully-local one is ever needed`
- `# ponytail: mixed text/scan PDFs — whole document falls to the OCR leg`
- `# ponytail: PP-OCRv6 models ship inside the rapidocr wheel — offline immediately after install`

## References — read on demand

| File | Read when |
| --- | --- |
| [references/anydoc.md](references/anydoc.md) | Office/PDF conversion options, exit codes, format matrix, library bindings |
| [references/ocr.md](references/ocr.md) | A PDF exits 3 or the input is an image — two tiers: RapidOCR script + internal-VLM fallback, languages, caveats |
| [references/tables.md](references/tables.md) | The deliverable is extracted tables, not a markdown file |
| [references/fallbacks.md](references/fallbacks.md) | Input is HTML/ipynb/msg/zip, or anydoc output looks mangled |
| [scripts/](scripts/) | Executable legs — `ocr_pdf.py`, `vlm_page.py` (run via `uv run`, deps are inline) |
