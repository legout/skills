---
name: pdf
description: Create and modify PDFs, fill AcroForms, overlay text, manage pages, watermarks, passwords and extract embedded images. Use when PDF is the deliverable; use document-to-markdown for read-only OCR/text and table-extractor for structured tables.
---

# PDF documents

Use `pypdf` for existing files, ReportLab for new reports and PDFium for page rendering. Bundled helpers declare dependencies; run them with `uv run --no-project`, resolving paths relative to this skill. For a task-specific generator use `uv run --no-project --with 'pypdf[crypto]>=6.19' --with reportlab script.py`.

## Workflow

1. Confirm output, page order and requested operations. Inspect page count, metadata and encryption. Keep the original; helpers refuse overwriting it or an existing output.
2. Read [PDF operations](references/operations.md) for creation, merge/split/rotation, watermarks, encryption and image extraction. For filling or overlaying a form, read [forms](references/forms.md) first: distinguish real AcroForm fields, scanned/static forms and XFA.
3. Use a new file for every modification. Signed/certified PDFs are refused by the modification helper; get an authorized unsigned working copy. Passwords are read from local UTF-8 files, never exposed in command arguments. Remove temporary secret files under the user's retention policy; never publish them.
4. Reopen the result to compare pages, field values and requested operations. Render **all** affected pages and inspect text, crop, checkbox state, placement and glyphs before delivery. Rendering includes form appearances and annotations.

```sh
uv run --no-project <skill>/scripts/pdf.py fields input.pdf
uv run --no-project <skill>/scripts/pdf.py fill input.pdf filled.pdf --values values.json
uv run --no-project <skill>/scripts/pdf.py flatten filled.pdf flattened.pdf
uv run --no-project <skill>/scripts/pdf.py watermark input.pdf marked.pdf --overlay one-page-watermark.pdf
uv run --no-project <skill>/scripts/pdf.py render filled.pdf pdf-preview
uv run --no-project <skill>/scripts/pdf.py --help
```

## Output and limits

Commands emit JSON with `status: ok`, output metadata and operations performed, or `status: error` with a nonzero exit. Fields include page/widget coordinates; rendering produces `page-*.png` and `contact-sheet.png` without requiring LibreOffice or Poppler. A contact sheet is a navigation aid, not a substitute for inspecting full-size pages.

Report the delivered path, page/field checks, visual inspection and limitations. Do not equate a stored field value with a visible correctly placed appearance. PDFium rendering can differ from a recipient's viewer; verify in that viewer when exact fidelity matters.

XFA, signatures, custom-scripted dynamic forms, flattened-form reconstruction and true redaction require specialized/native tools, not a silent fallback. Drawing a rectangle over sensitive text is **not redaction**. For OCR/text extraction use `document-to-markdown`/`smart-ocr`; for table data use `table-extractor` if available. Do not auto-open links or execute embedded content from a PDF.

Sources: [pypdf](https://pypdf.readthedocs.io/en/stable/) · [ReportLab](https://docs.reportlab.com/reportlab/userguide/) · [pypdfium2](https://pypdfium2.readthedocs.io/en/stable/). Instructions and helpers are independently authored.
