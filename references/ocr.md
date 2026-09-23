# OCR leg — scanned PDFs and images, two tiers, all cross-platform

Triggered by: anydoc exit code 3 on a PDF, or an image input (`.png .jpg .jpeg .webp .bmp`).

| Tier | Engine | Use when |
| --- | --- | --- |
| 1 — default | **RapidOCR** (PP-OCR models via ONNX Runtime) | Always first. Pure pip wheels, ~15 MB models, runs on Windows/macOS/Linux CPU |
| 2 — fallback | **Multimodal LLM** (company-internal: `gpt-5.6-luna` / `qwen-3.8-27b`) | Page flagged low-quality by tier 1, or content is dense tables / math / handwriting and fidelity matters |

Why RapidOCR and not paddlepaddle: the same PP-OCR model family runs through ONNX, but `rapidocr + onnxruntime` installs as plain wheels (~50–80 MB) instead of the ~1 GB paddlepaddle stack, which is also fragile on Windows.

Both scripts declare their dependencies inline (PEP 723) — `uv run` resolves them on first use, nothing is installed globally.

## Tier 1 — RapidOCR script

```bash
uv run scripts/ocr_pdf.py input.pdf output.md [lang]    # run from the skill directory
```

[scripts/ocr_pdf.py](../scripts/ocr_pdf.py) rasterizes each page at 300 DPI (PyMuPDF), sorts recognized lines top-to-bottom/left-to-right, and appends ` *(conf 0.xx)*` to lines below 0.85 confidence. Pages with no text or mean confidence < 0.75 get a `LOW-QUALITY PAGE n` comment — the Tier-2 trigger.

- Rasterization via PyMuPDF wheels — no poppler, no system deps; temp dir instead of hardcoded `/tmp`.
- Models ship **inside the rapidocr wheel** (PP-OCRv6 det/rec defaults) — fully offline right after install, no runtime downloads.
- Languages: third CLI arg maps to `Rec.lang_type` — `en`, `ch`, `german`, `french`, … full model list in the [RapidOCR docs](https://rapidai.github.io/RapidOCRDocs/main/model_list/).
- `res.to_markdown()` exists as a one-call alternative, but it drops confidence info — the script keeps the quality marks.
- Single image: skip the script, call `RapidOCR()("photo.png")` directly.

## Tier 2 — VLM fallback for very complex pages

```bash
uv run scripts/vlm_page.py page.png page.md              # run from the skill directory
```

Sends one page as an image to the internal multimodal endpoint ([scripts/vlm_page.py](../scripts/vlm_page.py)), OpenAI-compatible, with a strict transcribe-exactly prompt (`[illegible]` instead of guessing).

- Env: `OPENAI_BASE_URL` + `OPENAI_API_KEY` (internal gateway), `DOC2MD_VLM_MODEL` (default `gpt-5.6-luna`). The script rejects non-HTTPS and non-`*.siemens.com` endpoints.
- Render pages at ~150–200 DPI for the VLM (300 wastes tokens): `page.get_pixmap(dpi=180)`.
- Model choice: `gpt-5.6-luna` default for transcription fidelity; `qwen-3.8-27b` as alternate — worth A/B-ing one page on your typical scans and keeping the winner.
- **Boundary:** internal gateway only. Never point this at a public API — that's the skill's hard rule.
- VLMs can hallucinate plausible-looking text (PP-OCRv6's own benchmarks show frontier VLMs failing vs. classic pipelines on hard scripts): keep `[illegible]` discipline and verify critical values against the image.

## When to use which

| Signal | Action |
| --- | --- |
| anydoc exit 3 / image input | Tier 1 |
| Tier 1 output has `LOW-QUALITY PAGE` comments, `�`, or is near-empty | Re-run those pages via Tier 2 |
| Scanned tables / formulas / handwriting and the user needs structure | Go Tier 2 directly |
| Plain typed scan, good confidence | Tier 1, done |

## Caveats to state in output

- OCR text is never exact: keep confidence marks, tell the user which tier produced the output.
- Tier 2 output is model-generated transcription — flag it as such and spot-check critical numbers/names against the source image.
