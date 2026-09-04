# Excalidraw rendering and troubleshooting

## Export

### Option A: Kroki API (SVG only — zero install)

```bash
# SVG via Kroki API
curl -s -X POST https://kroki.io/excalidraw/svg \
  -H "Content-Type: text/plain" \
  --data-binary "@diagram.excalidraw" \
  -o diagram.svg

# Via local Kroki Docker (offline)
curl -s -X POST http://localhost:8000/excalidraw/svg \
  -H "Content-Type: text/plain" \
  --data-binary "@diagram.excalidraw" \
  -o diagram.svg
```

### Option B: Local CLI (PNG + SVG)

```bash
# PNG at 2x scale, with background baked in (recommended)
excalidraw-brute-export-cli -i diagram.excalidraw -o diagram.png -f png -s 2 -b true

# PNG at 1x scale
excalidraw-brute-export-cli -i diagram.excalidraw -o diagram.png -f png -s 1 -b true

# SVG
excalidraw-brute-export-cli -i diagram.excalidraw -o diagram.svg -f svg -s 1 -b true
```

**Required flags:** `-f` (format: `png` or `svg`) and `-s` (scale: `1`, `2`, or `3`).

**Optional flags:** `-b true` bakes the `viewBackgroundColor` into the image — **the export is transparent by default**, so omit `-b` (or pass `-b false`) only when you want a transparent background. `-d true` exports dark mode; `-e true` embeds the scene so the PNG/SVG reopens as an editable drawing in excalidraw.com. (Long forms also work: `--background`, `--dark-mode`, `--embed-scene`, `--format`, `--scale`, `--input`, `--output`.)

## Verify the Render

**You cannot judge a diagram from its JSON.** The JSON can look perfect while the image has clipped text, overlapping boxes, or an arrow slicing through a shape. After exporting, *look at the result and fix it* — this is the single highest-leverage step.

1. **Render to PNG** (the image must be viewable — PNG, not SVG, even if the user ultimately wants SVG):

   ```bash
   excalidraw-brute-export-cli -i diagram.excalidraw -o /tmp/check.png -f png -s 2 -b true
   ```

   View `/tmp/check.png` (Claude can read PNGs directly). *Visual audit needs the local CLI; with Kroki-only (SVG), fall back to the structural checks below.*
2. **Audit the image:**

   | Look for | Fix |
   |----------|-----|
   | Text clipped / overflowing its shape | Widen the shape (`max(160, charCount * 9)`, ×2 for CJK) or pre-wrap with `\n` |
   | Boxes or labels overlapping | Re-space using the Spacing Reference (≥40px gap) |
   | Arrow cutting straight through a shape | Move endpoints to the shape borders, not centers |
   | Arrow invisible — only its label shows | Shrink the label `width` to fit the text |
   | Element off-canvas or floating with no connection | Reposition / connect it |
   | **Isomorphism Test:** mentally delete all text — does the structure alone still convey the idea? | If not, the *layout* is wrong, not the labels — restructure |

3. **Fix the JSON and re-export.** Repeat until clean — typically 1–3 passes. Skip only for trivial 2–3 element diagrams.

## Review Loop

Verify-the-render fixes *defects*; the review loop incorporates *the user's* wishes. After the render is clean, show it and collect feedback, then apply the **minimal `.excalidraw` edit** for each request and re-export:

| User request | Edit action |
|---|---|
| Change a label | Edit the `text` (or the bound label element) |
| Change a color | Update `backgroundColor` / `strokeColor` on the element |
| Add / remove an element | Append or delete the element (fix any `boundElements` / binding refs) |
| Move / resize | Update `x` / `y` / `width` / `height` |
| Restructure / re-route | Re-apply the pattern's spacing & routing rules, or regenerate |

- Overwrite the same `diagram.excalidraw` / output file each round — don't create `v1`, `v2`, …
- Re-run **Verify the Render** after each edit (a change can introduce a new clip / overlap).
- **Safety valve:** after 5 rounds, suggest the user fine-tune in [excalidraw.com](https://excalidraw.com) — the output preserves arrow binding, so it opens fully editable.

## Anti-Patterns

**Never put `text` on large background/zone rectangles.** Excalidraw centers text in the middle of the shape, overlapping contained elements. Instead, use a free-standing `text` element positioned at the top of the zone.

**Avoid cross-zone arrows.** Long diagonal arrows create visual spaghetti. Route arrows within zones or along zone edges. If a cross-zone connection is unavoidable, route it along the perimeter.

**Use arrow labels sparingly.** Bind labels to the arrow (see **Arrow labels**) so the line is masked behind the text instead of striking through it — but keep the label `width` to the text, never the arrow length. Keep labels to ≤12 characters and ensure ≥120px clear space between connected shapes. Omit labels when the connection meaning is obvious from context.

**Don't use filled backgrounds on containers that hold other elements.** Use `opacity: 30` (or 25-40 range) for zone/container rectangles so contained elements remain visible.

**Always set explicit `strokeColor` on text elements.** Text `strokeColor` is the rendered text color. If omitted, text may inherit the parent shape's background color and become invisible. Use `#1e293b` (title), `#334155` (label), or `#64748b` (description) from the text color palette.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Kroki returns HTTP 400 | Send `-H "Content-Type: text/plain"` (NOT `application/json`, which Kroki reads as a `{"diagram_source": ...}` wrapper and rejects); ensure valid JSON with `"type": "excalidraw"` and `"elements"` array |
| Kroki only outputs SVG | Use local CLI (`excalidraw-brute-export-cli`) for PNG |
| Export fails with "Missing required flag" | Always pass `-f png` and `-s 2` |
| Export fails with "Executable doesn't exist" | Run `npx playwright install firefox` |
| macOS: timeout waiting for file chooser | Apply the macOS Meta patch above |
| Arrow `points` not relative to origin | `points` always start at `[0,0]` |
| Missing `id` on elements | Use descriptive string IDs per element |
| Overlapping elements | Use spacing reference table; minimum 40px gap |
| Arrows not interactive in excalidraw.com | Add `boundElements` to shapes referencing all bound arrows/text |
| Arrow/line cuts straight through the shapes | Compute endpoints at the shape borders, not centers — bindings don't clip the static export |
| Arrow invisible — only its label shows | Bound label `width` spans the whole arrow and masks the line; set label `width` to fit the text (`charCount * 9`) |
| Exported PNG/SVG has no background | CLI export is transparent by default; pass `-b true` to bake in `viewBackgroundColor` |
| Text not centered in shape | Set `containerId` on text AND add text to shape's `boundElements` |
| All text same size | Use font size hierarchy: 28 → 24 → 20 → 16 → 14 |
| Diagram looks monotone | Apply semantic colors from the palette, follow 60-30-10 rule |
| Text invisible / same color as background | Always set `strokeColor` on text elements to a dark color (`#1e293b`, `#334155`, or `#64748b`) |
| Text overlaps inside zone/container | Don't bind text to zone rectangles; use free-standing text at top |
| Text truncated in shapes | Use width formula: `max(160, charCount * 9)`, double for CJK |
| `boundElements: []` causes issues | Use `null` for empty boundElements, never `[]` |
