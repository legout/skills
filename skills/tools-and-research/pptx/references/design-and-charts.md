# Design and native charts

## Layout

Choose slide size before adding content; a template's existing size wins unless the user requests conversion. Lead with an actionable takeaway, one main idea per slide, generous margins and a consistent grid. Match the user's brand and language; avoid arbitrary decorative elements. Prefer readable body text around 20–24 pt and titles around 30–40 pt, then adapt to the real template and screen size. Dense supporting detail belongs on separate appendix slides, not tiny text.

Use contrasting text/backgrounds, aligned shapes and consistent gaps. Do not convey meaning only through color. Give charts clear units, periods and labels; avoid 3D effects and unrelated illustrations. Use fonts installed in the rendering and receiving environments; a LibreOffice fallback can look different from PowerPoint. Verify the rendered result, not just the point-size settings.

## Editable charts

```python
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE
from pptx.util import Inches

slides = Presentation()
slides.slide_width, slides.slide_height = Inches(13.333), Inches(7.5)
page = slides.slides.add_slide(slides.slide_layouts[6])
data = CategoryChartData()
data.categories = ["Actual", "Target"]
data.add_series("Revenue (EUR million)", [12, 15])
chart = page.shapes.add_chart(
    XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(1), Inches(2), Inches(11), Inches(4), data
).chart
chart.has_title = True
chart.chart_title.text_frame.text = "Revenue compared with target"
chart.has_legend = False
chart.plots[0].has_data_labels = True
page.notes_slide.notes_text_frame.text = "Source and assumptions: ..."
slides.save("briefing.pptx")
```

Use `CategoryChartData`, `XyChartData` or `BubbleChartData` according to chart type. For changing data in an existing native chart, use `chart.replace_data(...)`. Check categories, series, axes, legends, units and data labels after rendering. Do not substitute an image just to avoid learning the native API. For unsupported chart types such as network diagrams, an image is acceptable if the user accepts reduced editability; explain it.

## QA

Reopen the deck and compare slide text/count and chart values to the supplied data. Render every slide, including hidden appendix slides, and inspect the actual images for text outside boxes, overlaps, poor contrast, misleading scales and unresolved placeholders. Contact sheets locate slides; they do not prove tiny text is readable. A structural chart-axis check does not validate data correctness or every possible combo-chart constraint. Final application-level checks are in PowerPoint when exact fidelity matters.
