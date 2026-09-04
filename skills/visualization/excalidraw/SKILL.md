---
name: excalidraw
description: Create editable Excalidraw diagrams and export them to SVG or PNG for architecture, workflows, and other visualizations.
---

> Adapted from [`Agents365-ai/365-skills`](https://github.com/Agents365-ai/365-skills/tree/08f4791bbe21f42ef8e4013c7bd15c92347b916f) at commit `08f4791bbe21f42ef8e4013c7bd15c92347b916f` (MIT).

# Excalidraw diagrams

Use this for an editable sketch-like canvas. Use `drawio-skill` for precise UML, ER, BPMN, network, or branded diagrams; use `archify` for a standalone interactive HTML explainer.

## Workflow

1. Confirm scope and output: `.excalidraw` plus SVG by default, or PNG when a local exporter is available.
2. Read [design and layout](references/design-and-layout.md) before composing the scene. Read [schema reference](references/schema-reference.md) only for fields not covered there.
3. Generate valid Excalidraw JSON with unique element IDs and references.
4. Export and follow [rendering and troubleshooting](references/rendering-and-troubleshooting.md).
5. Inspect the render, fix defects, re-export, and show the result for feedback.
6. Apply targeted JSON edits until approved; report every output path.

## Minimal file shape

```json
{"type":"excalidraw","version":2,"source":"https://excalidraw.com","elements":[],"appState":{"viewBackgroundColor":"#ffffff","gridSize":null},"files":{}}
```

Use `scripts/excalidraw_lib.py` for reusable element construction. For SVG, Kroki needs only `curl`; PNG requires the documented local Firefox exporter. Do not claim an export succeeded until the output file exists and renders.
