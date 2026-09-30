# Document features

Use these recipes for a task-specific `python-docx` generator; preserve the user's existing conventions when editing.

## Page layout, styles, tables and images

```python
from docx import Document
from docx.shared import Cm, Pt

word = Document()
section = word.sections[0]
section.page_width, section.page_height = Cm(21), Cm(29.7)
section.top_margin = section.bottom_margin = Cm(2)
normal = word.styles["Normal"]
normal.font.name, normal.font.size = "Arial", Pt(11)
word.add_heading("Report", level=1)
word.add_paragraph("First item", style="List Bullet")
table = word.add_table(rows=1, cols=2)
table.autofit = False
for column in table.columns:
    column.width = Cm(8)
for cell in table.rows[0].cells:
    cell.width = Cm(8)
word.add_picture("figure.png", width=Cm(14))
word.save("report.docx")
```

Set widths within the section's usable page width; a long unbroken URL can still overflow. Inspect images for readability and provide meaningful captions/alt text in the target application's accessibility tools. Do not replace a whole paragraph to change one word: it discards run-level formatting and may remove fields or links. A replacement image may be referenced from multiple places; inspect drawing relationships before replacing the image part, or create a new part for a single occurrence.

## Header/footer fields and TOC

Use sections' `.header` and `.footer` paragraphs. Different-first-page settings and linked headers need checking when documents contain multiple sections. Fields are OOXML, not literal page numbers:

```python
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

footer = word.sections[0].footer.paragraphs[0]
field = OxmlElement("w:fldSimple")
field.set(qn("w:instr"), "PAGE")
footer._p.append(field)

toc = word.add_paragraph()
field = OxmlElement("w:fldSimple")
field.set(qn("w:instr"), 'TOC \\o "1-3" \\h \\z \\u')
toc._p.append(field)
```

Use real Heading 1–3 styles. Field instructions alone do **not** produce a verified populated TOC. Open in Word, update fields/TOC and verify the final PDF; LibreOffice may update fields differently. Do not say the TOC is finished while it is empty. Add page/section breaks deliberately rather than spacing with empty paragraphs.

## DOTX templates

`python-docx` does not open DOTX directly. Make a new DOCX working copy with `scripts/office.py template input.dotx working.docx`, then edit that copy. If a reusable template is the requested output, save the finished DOCX and convert its package type with `office.py template finished.docx template.dotx`. This changes the main content type as well as the extension; renaming alone is not a template conversion. Validate and test the result in Word. Macro templates (`.dotm`) are outside this helper.

## Reading and conversion

For read-only text, `document-to-markdown` avoids reconstructing an Office file. For legacy DOC, use Office's conversion to a new DOCX; do not rename the extension. For PDF output use `office.py render`, then deliver its `document.pdf` only after inspecting all page images. Rendering is not a sandbox for unknown third-party files; do not auto-open embedded links or objects.
