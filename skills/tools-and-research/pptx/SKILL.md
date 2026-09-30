---
name: pptx
description: Create and edit PowerPoint PPTX decks and POTX templates, with editable charts, speaker notes, slide selection and independent slide copies. Use when a PowerPoint file is the deliverable; use document-to-markdown for read-only extraction.
---

# PowerPoint presentations

Use `python-pptx` for generators and targeted edits: `uv run --no-project --with python-pptx script.py`. Bundled scripts declare dependencies; resolve their paths relative to this skill. No Node.js runtime is required.

## Workflow

1. Confirm audience, message, slide count, aspect ratio, editable content and brand/template. Inspect layouts and existing shapes before editing. Preserve the original; all helpers require a new output path.
2. Read [design and native charts](references/design-and-charts.md) before building a new deck. Keep standard charts, tables and text native/editable rather than using whole-slide screenshots. For Siemens branding, compose with `siemens-brandville`/`siemens-color-guidance` if installed.
3. Read [template editing](references/template-editing.md) for existing decks, notes, POTX and structural changes. `scripts/slides.py` selects, reorders, duplicates and removes slides within one deck, clones mutable chart/workbook/note parts, and removes orphaned parts. It refuses custom shows/sections rather than leaving broken memberships.
4. Verify slide count, text and chart values with `Presentation(output)`. Run structural validation, render every slide, then inspect full-resolution images for clipping, overlaps, fonts, contrast and leftover placeholders. Fix and re-render into a new directory.

```sh
# Keep slides 3 then 1 twice; omitted slides are removed.
uv run --no-project <skill>/scripts/slides.py input.pptx selected.pptx --order 3,1,1
uv run --no-project <skill>/scripts/office.py validate selected.pptx
uv run --no-project <skill>/scripts/office.py render selected.pptx deck-preview
```

## Verification and limits

`office.py` checks ZIP members, safe XML, content types, package relationships and chart axis references. This is not complete schema validation or proof PowerPoint will preserve every feature. Rendering uses LibreOffice with a separate temporary profile; it creates `document.pdf`, `page-*.png` and `contact-sheet.png`. Inspect all full-resolution slides, not just the contact sheet. Missing LibreOffice is an explicit failure: use PowerPoint export or report visual QA as pending. Font substitution can alter fit; prefer available fonts or validate in the recipient's environment.

Scripts return JSON with `status`; errors have a nonzero exit. Never equate a successful render with visual approval. Report delivered paths, changes, checks and remaining fidelity risks.

Animations, SmartArt, embedded objects, cross-deck master/theme merging and arbitrary third-party extensions are not guaranteed. Use native PowerPoint for unsupported edits; changing a signed deck invalidates its signature. Legacy `.ppt` needs an authorized conversion first. The slide helper does not import slides from another deck.

Source APIs: [python-pptx](https://python-pptx.readthedocs.io/en/latest/) · [LibreOffice CLI](https://help.libreoffice.org/latest/en-US/text/shared/guide/start_parameters.html). Helpers and instructions are independently authored.
