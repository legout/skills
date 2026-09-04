# Excalidraw design and layout

## Design Principles

### Default style

- `roughness: 0` — clean, modern look for all technical diagrams (use `1` only when user requests hand-drawn/casual style)
- `fontFamily: 2` (Helvetica) — professional look; use `1` (Virgil) only for casual/sketch style, `3` (Cascadia) for code snippets
- `fillStyle: "solid"` — default fill

### Containers: prefer typography over boxes

A box around every label makes a diagram look like a wireframe. The cleanest Excalidraw diagrams use **free-floating text and lines** for structure and reserve filled boxes for things that are genuinely *components*.

- **Default to no container** — use a standalone `text` element unless the box earns its place.
- **Add a box only when** the element is a real system component, an arrow binds to it, the shape itself carries meaning (decision diamond, start/end ellipse), or it groups a zone.
- Aim for **under ~30% of text elements inside boxes.**
- For timelines, trees, and hierarchies, use a **line/connector + free-floating labels**, not a stack of rectangles. Size, weight, and color create hierarchy without boxes.

### Font size hierarchy

| Level | Size | Use for |
|-------|------|---------|
| Title | 28px | Diagram title |
| Header | 24px | Section/group headers |
| Label | 20px | Primary element labels |
| Description | 16px | Secondary text, descriptions |
| Note | 14px | Annotations, fine print |

### Color palette

Follow the **60-30-10 rule**: 60% whitespace/neutral, 30% primary accent, 10% highlight.

**Semantic fill colors** (use with `strokeColor` one shade darker):

| Category | Fill | Stroke | Use for |
|----------|------|--------|---------|
| Primary / Input | `#dbeafe` | `#1e40af` | Entry points, APIs, user-facing |
| Success / Data | `#dcfce7` | `#166534` | Data stores, success states |
| Warning / Decision | `#fef9c3` | `#854d0e` | Decision points, conditions |
| Error / Critical | `#fee2e2` | `#991b1b` | Errors, alerts, critical paths |
| External / Storage | `#f3e8ff` | `#6b21a8` | External services, databases, AI/ML |
| Process / Default | `#e0f2fe` | `#0369a1` | Standard process steps |
| Trigger / Start | `#fed7aa` | `#c2410c` | Start nodes, triggers, events |
| Neutral / Container | `#f1f5f9` | `#475569` | Groups, swimlanes, backgrounds |

**Text colors:**

| Level | Color |
|-------|-------|
| Title | `#1e293b` |
| Label | `#334155` |
| Description | `#64748b` |

**Rule: Do not invent new colors.** Pick from this palette.

### Arrow semantics

| Style | Meaning |
|-------|---------|
| Solid (`strokeStyle: "solid"`) | Primary flow, main path |
| Dashed (`"dashed"`) | Response, async, callback |
| Dotted (`"dotted"`) | Optional, reference, weak dependency |

## Excalidraw JSON Structure

### File skeleton

```json
{
  "type": "excalidraw",
  "version": 2,
  "source": "claude-code",
  "elements": [],
  "appState": { "viewBackgroundColor": "#ffffff" }
}
```

### Element types

| type      | use for                          |
|-----------|----------------------------------|
| rectangle | boxes, components, modules       |
| ellipse   | start/end nodes, databases       |
| diamond   | decision points                  |
| arrow     | directed connections             |
| line      | undirected connections           |
| text      | standalone labels                |

`image`, `frame`, and `embeddable` are **not covered** by this skill: `image` needs a separate `files` map plus a `fileId`, and frames/embeds render inconsistently through the export path. Stick to the six types above — and for ready-made icons built *from* these primitives, see **Community shape & icon libraries** below.

### Community shape & icon libraries

Need a real AWS / Azure / GCP / network / UML / BPMN icon instead of a plain box? The [Excalidraw community libraries](https://libraries.excalidraw.com) (200+ `.excalidrawlib` files) are built almost entirely from the **same vector primitives** above — so their items **render through Kroki and the local CLI** with no `image` element and no `files` map. Use the helper in `scripts/excalidraw_lib.py`:

```bash
# 1. Find a library (matches name / description / item names)
python scripts/excalidraw_lib.py search aws

# 2. List its items (index, name, element count; flags any image-based item)
python scripts/excalidraw_lib.py items slobodan/aws-serverless.excalidrawlib

# 3. Build your base scene first, then drop an item in at (x, y). IDs are
#    namespaced and coordinates translated, so it merges without collisions:
python scripts/excalidraw_lib.py merge scene.excalidraw \
    slobodan/aws-serverless.excalidrawlib 0 455 257 --scale 0.9 --prefix lambda
```

**Rules:**

- **Vector only.** `merge` refuses any item containing an `image` element (won't render via the export path); `items` flags them up front.
- **Use sparingly.** An icon is just a labeled node — keep the design system's spacing, labels, and arrow semantics. Icons accent a diagram; they don't replace it.
- **Arrows don't bind to library groups** — draw connectors with explicit edge-to-edge `points` (bindings don't affect the static export anyway).
- Libraries are MIT-licensed; a courtesy credit is welcome, not required.
- Still run **Verify the Render** afterward — icon bounding boxes vary, so check alignment and spacing.

### Element sizing

Calculate element width from label text to prevent truncation:

```
Latin text:  width = max(160, charCount * 9)
CJK text:   width = max(160, charCount * 18)
Mixed text:  estimate each character individually, sum up
```

Height: use `60` for single-line labels, add `24` per additional line.

**Standalone `text` does NOT auto-wrap.** For multi-line standalone labels, insert manual `\n` line breaks yourself — aim for ≤ ~30 Latin (≤ ~15 CJK) characters per line at 16px — and add `24` height per line. (Text *bound inside a shape* via `containerId` wraps to the container width automatically, so size the container instead of adding `\n`.)

### Required properties (all elements)

```json
{
  "id": "auth_service",
  "type": "rectangle",
  "x": 100, "y": 100,
  "width": 160, "height": 60,
  "angle": 0,
  "strokeColor": "#1e40af",
  "backgroundColor": "#dbeafe",
  "fillStyle": "solid",
  "strokeWidth": 2,
  "roughness": 0,
  "opacity": 100,
  "seed": 100001,
  "boundElements": [
    { "id": "arrow_to_db", "type": "arrow" },
    { "id": "label_auth", "type": "text" }
  ]
}
```

Use **descriptive string IDs** (e.g., `"api_gateway"`, `"arrow_gw_to_auth"`) instead of random strings.

Give each element a unique `seed` (integer). Namespace by section: 100xxx, 200xxx, 300xxx.

### JSON field rules

- `boundElements`: use `null` when empty, never `[]`
- `updated`: always use `1`, never timestamps
- Do NOT include: `frameId`, `index`, `versionNonce`, `rawText`
- `points` in arrows: always start at `[0, 0]`
- `seed`: must be a positive integer, unique per element

### Property values

Use only these values — all verified to render via Kroki and the local CLI:

| Property | Valid values |
|----------|--------------|
| `fillStyle` | `"solid"`, `"hachure"`, `"cross-hatch"`, `"zigzag"` |
| `strokeStyle` | `"solid"` (or omit), `"dashed"`, `"dotted"` |
| `fontFamily` | `1` (Virgil, hand-drawn), `2` (Helvetica), `3` (Cascadia, code) |
| `textAlign` | `"left"`, `"center"`, `"right"` |
| `verticalAlign` | `"top"`, `"middle"`, `"bottom"` |
| `startArrowhead` / `endArrowhead` | `null`, `"arrow"`, `"triangle"`, `"bar"`, `"dot"`, `"circle"`, `"diamond"`, `"crowfoot_many"` |

Arrows default to `endArrowhead: "arrow"` and `startArrowhead: null` — omit both for a standard one-way arrow. Use `"triangle"` for UML inheritance, `"diamond"` for composition, and `"crowfoot_many"` for ER cardinality.

> **Need copy-paste templates or the full property/arrowhead catalogue?** Read `references/schema-reference.md` — complete element templates (component+label, bound arrow, arrow label, swimlane zone, mind-map connector) and every verified property value.

### Text inside shapes (contained text)

When text belongs inside a shape, bind them bidirectionally:

```json
{
  "id": "label_auth",
  "type": "text",
  "text": "Auth Service",
  "fontSize": 20,
  "fontFamily": 2,
  "textAlign": "center",
  "verticalAlign": "middle",
  "strokeColor": "#1e293b",
  "containerId": "auth_service"
}
```

**CRITICAL: Text `strokeColor` is the text color.** Always set it explicitly to a dark color from the text color palette. Never omit it — omitting `strokeColor` on text can cause invisible text that blends with the shape background.

The parent shape must list the text in its `boundElements`:

```json
"boundElements": [{ "id": "label_auth", "type": "text" }]
```

### Arrow binding (bidirectional)

Arrows must bind to shapes, and shapes must reference bound arrows:

```json
{
  "id": "arrow_gw_to_auth",
  "type": "arrow",
  "points": [[0, 0], [200, 0]],
  "startBinding": { "elementId": "api_gateway", "gap": 5, "focus": 0 },
  "endBinding": { "elementId": "auth_service", "gap": 5, "focus": 0 }
}
```

Both `api_gateway` and `auth_service` must include in their `boundElements`:

```json
"boundElements": [{ "id": "arrow_gw_to_auth", "type": "arrow" }]
```

**Endpoints must reach the shape borders.** `startBinding`/`endBinding` (and their `gap`) only affect interactive editing on excalidraw.com — they do **NOT** clip the line when exporting via Kroki or the local CLI. The exporter draws your `points` literally. So compute endpoints edge-to-edge: set the arrow's `x`/`y` to the source shape's border (the side facing the target) and the last point to the target's border. Center-to-center points draw the line straight *through* both shapes.

### Arrow labels

To label an arrow, bind a `text` element to it exactly like shape text: set the label's `containerId` to the **arrow's** id, and add the label to the arrow's `boundElements`. Excalidraw then centers the label on the arrow and masks the line behind the text, so it stays readable (no strike-through).

```json
{
  "id": "arrow_valid_to_grant",
  "type": "arrow",
  "points": [[0, 0], [0, 120]],
  "boundElements": [{ "id": "lbl_yes", "type": "text" }]
}
```

```json
{
  "id": "lbl_yes",
  "type": "text",
  "text": "Yes",
  "fontSize": 14,
  "width": 36,
  "strokeColor": "#1e293b",
  "containerId": "arrow_valid_to_grant"
}
```

**CRITICAL: the label `width` must fit the text (`charCount * 9`), NOT the arrow length.** Excalidraw masks the line behind the label's full bounding box — a label as wide as the arrow masks the *entire* arrow, so the line disappears and only floating text remains. Keep label widths small.

### Arrow routing

**L-shaped (elbow) arrows** — orthogonal routing with 3+ points:

```json
"points": [[0, 0], [100, 0], [100, 150]]
```

**Elbowed arrows** — automatic right-angle routing:

```json
{
  "type": "arrow",
  "points": [[0, 0], [0, -50], [200, -50], [200, 0]],
  "elbowed": true
}
```

**Curved arrows** — smooth routing with waypoints:

```json
{
  "type": "arrow",
  "points": [[0, 0], [50, -40], [200, 0]],
  "roundness": { "type": 2 }
}
```

### Grouping

Related elements share `groupIds`. Nested groups list IDs innermost-first:

```json
"groupIds": ["inner_group", "outer_group"]
```

## Diagram Patterns

Choose the right visual pattern for each diagram type.

### Relationship-to-layout map

Before locking in a *diagram type*, pick the *visual metaphor* that matches the relationship in the idea — it drives the layout more than the type label does:

| Relationship in the idea | Visual metaphor | Build with |
|---|---|---|
| One → many (broadcast, dispatch) | **Fan-out** | one node, arrows radiating outward |
| Many → one (aggregate, merge) | **Convergence** | several inputs, arrows into one node |
| Parent → children (hierarchy) | **Tree** | trunk + branch *lines*, free-floating text |
| Repeating cycle (loop, feedback) | **Cycle** | nodes in a ring, curved arrows back to start |
| Input → transform → output | **Assembly line** | left-to-right pipeline of steps |
| A vs B (comparison) | **Side-by-side** | two parallel columns on a shared baseline |
| Before / after, phase break | **Gap** | whitespace or a dashed divider between groups |
| Fuzzy / overlapping state | **Cloud** | overlapping ellipses, no hard borders |

### Spacing Reference

| Scenario | Spacing |
|----------|---------|
| Labeled arrow gap (between shapes) | 150–200px |
| Unlabeled arrow gap | 100–120px |
| Column spacing (labeled arrows) | 400px (220px box + 180px gap) |
| Column spacing (unlabeled arrows) | 340px (220px box + 120px gap) |
| Row spacing | 280–350px (150px box + 130–200px gap) |
| Zone/container padding | 50–60px around children |
| Zone/container opacity | 25–40 |
| Minimum gap between any elements | 40px |

### Flowchart (LR or TB)

- Ellipse for start/end, diamond for decisions, rectangle for process
- 200px horizontal spacing, 150px vertical spacing
- Decision branches: "Yes" goes forward, "No" goes down
- 3–10 steps (max 15)

### Architecture / System Diagram

- Column spacing per table above; use labeled arrow spacing when connections have labels
- Group related services in dashed `Neutral` containers (opacity: 30, padding: 50px)
- Gateway/entry at left or top, databases at right or bottom
- 3–8 entities (max 12)

### Sequence Diagram

- 200px between participants (rectangles at top)
- Vertical lifelines as dashed lines
- Horizontal arrows for messages, 60px vertical spacing
- Solid arrow = request, dashed arrow = response

### Mind Map

- Central node: largest (200x100), `Trigger` color
- Level 1: 150x70, `Primary` color, radial around center
- Level 2: 120x50, `Process` color
- Level 3: 90x40, `Neutral` color
- Use lines (not arrows) for connections
- 4–6 branches (max 8), 2–4 sub-topics per branch
- **Place level-1 branches on a circle** of radius `R ≈ 280` around the center `(cx, cy)`: for branch `i` of `n`, `angle = 2π·i/n`, `x = cx + R·cos(angle)`, `y = cy + R·sin(angle)`. Even spacing prevents the crossed-line tangle that ad-hoc placement produces.

### Swimlane

- Large transparent rectangles (`Neutral` fill, `"dashed"` stroke, opacity: 30) as lane boundaries
- Lane label as free-standing text at top-left of lane (not bound to rectangle), 28px font
- Elements flow left-to-right within lanes
- Arrows cross lanes for handoffs

## Section-by-Section Construction

For diagrams with **10+ elements**, do NOT generate the entire JSON at once. Build in sections:

1. **Plan all sections first** — list element IDs, positions, and cross-section bindings
2. **Write section 1** — create the file with initial elements
3. **Append section 2** — read the file, add new elements to the `elements` array
4. **Repeat** — continue until all sections are done
5. **Final pass** — verify all `boundElements` and `startBinding`/`endBinding` references are consistent

Namespace element seeds by section (100xxx, 200xxx, 300xxx) to avoid collisions.
