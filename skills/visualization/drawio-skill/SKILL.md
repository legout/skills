---
name: drawio-skill
description: Create and export draw.io diagrams including architecture, flowchart, ER, UML, BPMN, network, and data visualizations.
---

> Adapted from [`Agents365-ai/365-skills`](https://github.com/Agents365-ai/365-skills/tree/08f4791bbe21f42ef8e4013c7bd15c92347b916f) at commit `08f4791bbe21f42ef8e4013c7bd15c92347b916f` (MIT).

# Draw.io diagrams

Create `.drawio` XML and requested PNG, SVG, PDF, or JPG exports. Use `excalidraw` for a sketch-like canvas and `archify` for a standalone interactive HTML explainer.

## Workflow

1. Clarify only missing essentials: diagram type, fidelity, format, or explicit destination.
2. Resolve an optional style preset from `~/.drawio-skill/styles/` or `styles/built-in/`; read [style presets](references/style-presets.md) when one applies.
3. Resolve the desktop binary with `drawio --version`, then `draw.io --version`, then platform app paths. Record its major version.
4. Choose one authoring path:
   - bundled generator/importer: find it in [the toolbox](references/toolbox.md);
   - Mermaid conversion on draw.io 30+ for standard unstyled diagrams: read [Mermaid authoring](references/mermaid-authoring.md);
   - hand-written XML for precise styling or geometry: read [XML authoring](references/xml-authoring.md);
   - large graphs: read [autolayout](references/autolayout.md).
5. For a named diagram family, read [diagram types](references/diagram-types.md). For stock or vendor symbols, use [shape search](references/shapes.md); do not guess style strings.
6. Run `python3 scripts/validate.py <file.drawio>` before export.
7. Export a preview PNG without `-e`, capped with `--width 2000`. Inspect it for overlaps, clipping, missing connections, off-canvas shapes, and unreadable labels.
8. Apply targeted edits and repeat the preview until approved, at most five user-review rounds.
9. Export final requested formats. For editable PNG use `-e`, a `.drawio.png` suffix, then run `python3 scripts/repair_png.py <file.drawio.png>`.
10. Report source and export paths.

## Export commands

```bash
drawio -x -f png --width 2000 -o diagram.png diagram.drawio
drawio -x -f png -e -s 2 -o diagram.drawio.png diagram.drawio
python3 scripts/repair_png.py diagram.drawio.png
drawio -x -f svg -e -o diagram.svg diagram.drawio
drawio -x -f pdf -e -o diagram.pdf diagram.drawio
```

Substitute the binary resolved in step 3 and resolve scripts from this skill directory. Do not use `-e` for the vision preview. If the CLI crashes or produces no output in a sandbox, stop retrying and follow [troubleshooting](references/troubleshooting.md), use `scripts/encode_drawio_url.py`, or deliver XML only.
