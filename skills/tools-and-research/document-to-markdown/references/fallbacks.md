# Fallbacks — markitdown (offline formats only)

markitdown covers the formats anydoc lacks. All converters below are local libraries — no network.

## Use for

`.html` `.htm` `.ipynb` `.msg` (Outlook) `.zip` (iterates contents) `.json` `.xml`

```bash
uvx --from 'markitdown[all]' markitdown page.html -o page.md
```

## Second opinion

If anydoc's output for a DOCX/PPTX/XLSX/PDF looks mangled (broken tables, lost headings), try markitdown on the same file and keep the better result — different parsers, different failure modes:

```bash
uvx --from 'markitdown[all]' markitdown report.docx -o report.md
```

## Forbidden (network/API — hard rule)

- `--use-plugins` and the `markitdown-ocr` plugin (LLM vision API)
- `llm_client`/`llm_model` image descriptions
- Audio transcription, YouTube URLs, `az-doc-intel`/`az-content-understanding` extras (cloud services)

Local document formats only. OCR belongs to the RapidOCR leg ([ocr.md](ocr.md)), not to markitdown.
