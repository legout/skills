# PDF operations

## New reports

Use ReportLab Platypus for flowing paragraphs, tables and page breaks rather than manually guessing line positions. Use a registered Unicode TTF containing the requested glyphs; default PDF fonts do not cover all Unicode. Specify page size, margins and heading/body styles. Escape external text before placing it in a `Paragraph`, since its text supports markup.

```python
from html import escape
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table

styles = getSampleStyleSheet()
story = [Paragraph(escape("Report"), styles["Title"]), Spacer(1, 12)]
story.append(Paragraph(escape("Verified summary."), styles["BodyText"]))
story.append(Table([["Item", "Result"], ["Example", "25"]]))
SimpleDocTemplate("report.pdf", pagesize=A4).build(story)
```

For superscripts/subscripts use Paragraph markup with a font supporting the text; do not assume arbitrary Unicode glyphs exist in built-in fonts. Render the result with `pdf.py render` and check page breaks, table splits and symbols. For an elaborate editable source document, use `docx` and an approved PDF conversion instead of building a page-layout engine.

## Page operations

Use a new PdfWriter and `append` for merging compatible unsigned PDFs, then reopen and check total page count and order. For simple non-form page selection use `pdf.py select input.pdf selected.pdf --pages 3,1,2`; repeated numbers duplicate a page, omitted numbers remove pages. Run it once per desired split file. Selection deliberately refuses AcroForms, whose fields must be reconciled rather than orphaned.

For rotating pages, use `page.rotate(90)` on a new working copy; check rotation metadata and render the result. Before page manipulation, check signatures/certification, attachments and forms; raw `add_page` is not a guarantee all document-level metadata/features survive. For production task scripts reuse the modification preconditions in `pdf.py`, or inspect signatures and permissions explicitly.

## Watermarks and text overlays

`pdf.py watermark input.pdf marked.pdf --overlay watermark.pdf` merges a **single-page** overlay onto each input page without automatically resizing it. Match the overlay geometry to the source; mixed page sizes/crops/rotations need separate matching overlays. Create the overlay with ReportLab. Inspect contrast and transparency; a watermark should not obscure important data.

For positioned text/static-form filling use `pdf.py stamp` and the forms reference. Overlays and white rectangles do not remove underlying text, images, metadata or attachments; never call them redaction.

## Passwords

`pdf.py encrypt input.pdf encrypted.pdf --new-password-file password.txt` uses AES-256. `pdf.py decrypt encrypted.pdf plain.pdf --password-file password.txt` requires the authorized password. This encrypts/decrypts a new copy; it does not crack passwords or prove the document's recipient policy. Keep password files and outputs out of repositories/logs. Do not upload confidential files to an external converter.

## Metadata and images

`pdf.py metadata input.pdf` returns page count and metadata. `pdf.py images input.pdf image-directory` extracts embedded images into a new directory using generated page/image filenames. Embedded images are not the same as rendered pages; vector content and annotations require page rendering. A page may reference masks or recompressed images, so compare any extracted figure with the page before using it.

## Extraction and OCR

Use `document-to-markdown` for read-only text/layout conversion, `smart-ocr` for OCR and `table-extractor` for tables when installed. Do not run unrelated document mutation simply to read a file. Scanned pages need OCR; extracted text does not prove the page was made searchable. If searchable-PDF output is explicitly required, use an approved OCR engine's PDF output mode and verify both the text layer and the preserved page appearance. Do not promise that read-only extraction created a searchable PDF.
