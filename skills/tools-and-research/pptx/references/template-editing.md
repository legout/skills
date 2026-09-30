# Templates, structural changes and notes

## Targeted edits

Inspect `Presentation(input).slide_layouts` and slide shapes before choosing layouts. Index 6 is blank only in the default template, not universally. Change `run.text` to preserve a run's font and styling; assigning `text_frame.text` rebuilds the text frame and can discard formatting. Keep bullets and placeholder styles inherited from the layout where possible.

Remove an unused repeated template item as a whole group (image and text), not just its label. Check for leftover example names, TODOs and empty icons. Use existing picture placeholders or `add_picture` for supported images; SVG/EMF may need an approved conversion to PNG, or reuse the original relationship rather than pretending PIL can read it.

Speaker notes: inspect/edit `slide.notes_slide.notes_text_frame`. Keep notes separate from visible slide text and verify them in PowerPoint; PDF slide renders do not show notes. Comments and advanced notes layout need application-level checking.

## Duplicate, reorder and delete

`uv run --no-project <skill>/scripts/slides.py input.pptx output.pptx --order 3,1,1` creates a new deck. Each selected occurrence gets its own slide, chart, embedded workbook and notes graph. Layouts, masters, themes and image parts are shared because editing their definitions is intentionally a deck-wide operation. The helper removes parts no longer reachable from the root relationships.

Do structural selection **before** editing the new slides. Edit the result's separate chart objects with `replace_data`; replacing a shared image binary or editing a master still affects all its users. The helper operates inside one package, not across unrelated decks. It rejects invalid packages, out-of-range numbers, empty output and decks with custom shows/sections. Complex animations/extensions may encode additional identifiers that basic relationship checks do not understand; verify them in PowerPoint or use native duplication.

## POTX

For creating a template from a finished deck, use `scripts/office.py template finished.pptx reusable.potx`. To edit a POTX with python-pptx, make a new PPTX working copy with `office.py template reusable.potx working.pptx`. Merely renaming leaves the wrong main content type. `slides.py` can select directly from POTX when the output extension remains POTX. Macro templates and legacy PPT need native Office.

## Preview and fidelity

`office.py render` uses a fresh LibreOffice profile, not a running user's session. It requests LibreOffice's `ExportHiddenSlides` option so appendix slides are included. Check rendered page count against the deck's total before claiming every slide was inspected; if an older LibreOffice version ignores the option, render an approved temporary copy with hidden flags removed or export all slides in PowerPoint. Exact native PowerPoint features and substituted fonts need final inspection there.
