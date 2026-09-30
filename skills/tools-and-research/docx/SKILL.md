---
name: docx
description: Create and edit Word DOCX documents and DOTX templates, including tables, images, comments and tracked text edits. Use when an editable Word file is the deliverable; use document-to-markdown for read-only extraction.
---

# Word documents

Use `python-docx` for new documents and ordinary edits. For a task-specific generator, run `uv run --no-project --with 'python-docx>=1.2' script.py`. Bundled scripts declare their own dependencies; run them with `uv run --no-project`. Resolve paths below relative to this skill, not the user's working directory.

## Workflow

1. Confirm content, audience, page size, output and template. Inspect the original's paragraphs, runs, tables, headers and sections. Save to a new path; the bundled tools refuse overwriting originals **and** existing outputs.
2. Use built-in headings, named styles, real lists and table column widths. For editing, preserve formatting by changing `run.text` or a targeted table cell, not assigning whole `paragraph.text` values. Read [document features](references/document-features.md) for images, fields, TOC, headers/footers and templates.
3. For comments or redlining, read [review edits](references/review-edits.md), then use `scripts/edit.py`. Its tracked replacement handles a unique plain-text phrase even across differently formatted runs; it rejects fields, bookmarks and structural revisions it cannot safely handle.
4. Check content with `Document(output)` and run `scripts/office.py validate`. Render every page and inspect it. Fix truncation, bad pagination, missing images and tables running off the page; re-render changed output into a new directory.

```sh
uv run --no-project <skill>/scripts/edit.py replace input.docx tracked.docx "Old wording" "New wording" --author "Reviewer"
uv run --no-project <skill>/scripts/edit.py comment input.docx annotated.docx "Target phrase" "Please verify this" --author "Reviewer"
uv run --no-project <skill>/scripts/edit.py accept tracked.docx accepted.docx
uv run --no-project <skill>/scripts/office.py validate accepted.docx
uv run --no-project <skill>/scripts/office.py render accepted.docx word-preview
```

## Verification and delivery

The structural validator checks ZIP members, safe XML, content types, relationship targets/references and chart axes. It is **not** a complete OOXML schema validator, automatic repair tool, or proof of Word fidelity. Renderer output includes `document.pdf`, full-resolution `page-*.png` and a navigation contact sheet. Rendering requires LibreOffice; macOS/Windows installation paths and PATH are searched, and a temporary profile avoids disturbing open sessions. Fonts still affect layout; use the user's fonts or report substitutions.

Scripts emit JSON: `status: ok` on success, `errors`/`error` on failure; nonzero means failure. Rendering alone is not visual approval. If LibreOffice is unavailable, use Word's PDF export and inspect it; otherwise explicitly report visual QA as pending, not passed.

Do not claim lossless handling of complex embedded objects, macros, content controls, signatures or arbitrary revisions. Ask before processing signed documents (editing invalidates signatures). `.doc` requires an authorized conversion in Office first. Report the delivered path, operations performed, content/structure/visual checks and any remaining limitation.

Source APIs: [python-docx](https://python-docx.readthedocs.io/en/latest/) · [LibreOffice CLI](https://help.libreoffice.org/latest/en-US/text/shared/guide/start_parameters.html). This skill and its helpers are independently authored; no Anthropic implementation files are included.
