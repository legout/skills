# Lightweight OCR: simple scans and images

Use RapidOCR for plain single-column text when layout relationships and form states
are not required. For tables, forms, multiple columns or receipts, prefer Docling
or MinerU; for remaining semantic failures, use approved vision. Do not run this
leg merely because the PDF has no text layer.

```sh
uv run <skill-dir>/scripts/ocr_pdf.py input.pdf candidate.md german
```

The existing script renders at 300 DPI and runs PP-OCR through ONNX Runtime. It
sorts recognized boxes top-to-bottom then left-to-right, writes one detection per
line, and appends recognition scores below 0.85. It does not reconstruct table
cells, independent columns or checkbox states, and its Markdown drops box geometry.

## Interpret confidence correctly

The script flags empty pages and mean recognition scores below 0.75. These are
useful recognition warnings, **not the only escalation triggers**. High-confidence
words may still have incorrect ordering or field associations. A document can
need structural parsing or vision without a LOW-QUALITY comment.

Use the configured language supported by the installed RapidOCR version; inspect
the CLI/library docs rather than assume one recognizer covers every script. Model
availability/download behavior depends on the pinned package and selected language;
do not promise air-gapped operation before the needed models are cached.

Keep this output as a candidate. Inspect content and coverage against the source;
preserve the PDF and source-page images for checking. The existing positional
`input output [lang]` invocation remains supported. It can replace its chosen output
path, so select a fresh candidate path, not an existing user-authored final file.

For complex scans read [structured parsers](structured-pdf.md). For the final
fallback read [vision](vision.md), including native-agent vision authorization and
the existing internal-endpoint helper.
