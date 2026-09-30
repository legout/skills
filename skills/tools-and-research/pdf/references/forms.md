# PDF forms and bounded overlays

## AcroForm workflow

1. Run `scripts/pdf.py fields input.pdf`. Inspect field types/names, widget pages, rectangles and checkbox export states. Coordinates are PDF points from the bottom-left, before page rotation. A visible blank rectangle is not necessarily a real field.
2. Prepare a UTF-8 JSON object using exact field names, for example `{"full_name":"Ada Lovelace","approved":"/Yes"}`. Checkbox values must match the reported appearance state; `/Yes` is not universal. Use `/Off` only if that state is reported.
3. Run `pdf.py fill input.pdf filled.pdf --values values.json`. The helper rejects unknown/read-only fields, unsupported types, invalid checkbox/choice values, overlong text and widget rectangles outside the crop. It writes appearances and verifies the stored values before publishing.
4. Run `pdf.py fields filled.pdf`, then `pdf.py render filled.pdf form-preview`. Inspect every filled field/checkbox on full-resolution images and in the target viewer. Longer text can still overflow or be shrunk by the form font settings; stored-value checks do not prove legibility. Unicode coverage depends on the form's fonts; do not deliver tofu/missing glyphs.

The helper supports ordinary text, choice fields, checkboxes and radio groups with explicit appearance states (e.g. `/high`). It rejects XFA, push-button actions and multiselect fields rather than guessing. Filled fields remain editable. If the recipient needs fixed appearances, run `pdf.py flatten filled.pdf flattened.pdf`; it embeds current appearances into page content and removes widgets/AcroForm data. Keep the editable source and render the flattened result to verify every field remains visible. For complex scripted/dynamic forms use approved native form software instead.

## Static/scanned forms

A form with no fields needs coordinates, not invented field names. Render the blank page, identify the printed labels and specify one overlay entry per requested line:

```json
[{"page":1,"x":80,"y":650,"text":"Ada Lovelace","size":11}]
```

Run `pdf.py stamp input.pdf filled-static.pdf --annotations annotations.json`. Page numbers are one-based; x/y are points from bottom-left at the text baseline. The helper rejects text outside the crop or rotated pages. For non-ASCII text pass `--font path/to/approved-unicode-font.ttf`; verify actual glyphs, not just whether the font file loads. To tick a static box, use an ASCII `X` overlay at the verified coordinates or create a task-specific ReportLab drawing.

Pixel-to-PDF conversion for an unrotated cropped page: `x = crop.left + pixel_x * 72 / dpi`, `y = crop.top - pixel_y * 72 / dpi`, then account for text baseline height. Do not copy pixel coordinates directly. Normalize rotated pages in a new copy using `page.transfer_rotation_to_content()` and inspect again before stamping; do not silently place text using the wrong frame.

Render the stamped output and check every filled region against the blank form. An overlay is not an editable AcroForm field, OCR, redaction or a signature. Never fabricate approval or a handwritten signature.
