# Workbook features

## Editing and formats

Use `load_workbook(path, data_only=False)` for editing; `data_only=True` reads cached results and removes formula strings from that in-memory workbook. Cached values can be absent or stale. For merged ranges, write only the top-left cell. Quote sheet names in cross-sheet formulas, e.g. `='Inputs 2027'!$B$2`. Store dates as dates, numbers as numbers and percentages as fractions; number formats affect appearance, not the stored value.

Retain the original's designated input cells and formatting. Avoid rewriting an entire workbook for one changed input. Unsupported drawing/extension features may be dropped on save: inspect a representative copy in Excel before processing complex files.

## Editable tables and charts

```python
from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.worksheet.table import Table, TableStyleInfo

book = Workbook()
sheet = book.active
sheet.title = "Revenue"
sheet.append(["Period", "Amount (EUR)"])
sheet.append(["Q1", 1200])
sheet.append(["Q2", 1500])
table = Table(displayName="RevenueData", ref="A1:B3")
table.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
sheet.add_table(table)
chart = BarChart()
chart.title = "Revenue by period"
chart.y_axis.title = "EUR"
chart.add_data(Reference(sheet, min_col=2, min_row=1, max_row=3), titles_from_data=True)
chart.set_categories(Reference(sheet, min_col=1, min_row=2, max_row=3))
sheet.add_chart(chart, "D2")
sheet.freeze_panes = "A2"
sheet.column_dimensions["A"].width = 18
sheet.column_dimensions["B"].width = 20
book.save("revenue.xlsx")
```

Check chart ranges and labels, not just whether the chart exists. Configure print area/orientation deliberately for PDF inspection; otherwise cells or charts can be split across many pages. Workbook UI features and hidden sheets need separate Excel inspection when not present in PDF output. A filled-out template should include an input legend and realistic example row when creating it, not when editing someone else's existing data.

## Templates and VBA

For XLTX set `book.template = True` and save with `.xltx`. For a normal workbook created from XLTX, set `.template = False` and save as a new `.xlsx`. Alternatively `office.py template` switches the package's main content type between XLSX/XLTX. Validate before delivery.

Load XLSM with `keep_vba=True` and save as XLSM. This retains the VBA archive but does not edit, run or prove macro correctness, and cannot guarantee signatures/controls/unsupported extensions survive. Never execute macros from an untrusted attachment. The recalc helper only supports XLSX; verify macro-bearing workbooks in authorized Excel instead.

For CSV/TSV→Excel, inspect encoding and delimiter, preserve identifier strings and prevent formula injection: external strings beginning with `=`, `+`, `-` or `@` must not be promoted to executable formulas unless the user explicitly intends formulas. With openpyxl, explicitly store externally supplied text with `cell.data_type = 's'`; do not change genuine numeric negatives into text.
