# Financial-model conventions

The user's model conventions always override these defaults. Ask about missing currency, units, periods, assumptions and rounding rather than inventing them.

- Put assumptions in labeled input cells and reference them from formulas; do not bury growth rates or exchange rates as unexplained constants.
- Cite the user input or actual source next to assumptions, in notes or cell comments. Distinguish actuals, estimates and scenarios.
- Default cue: blue font for editable inputs, black for formulas, green for references to other sheets; flag external workbook links separately. Add a written legend so color is not the only signal.
- Label units in headers (`Revenue, EUR thousand`), show negative amounts consistently (for example parentheses) and zeros consistently (for example a dash). Store `0.15` for 15%, not `15`. Use enough decimal precision to avoid hiding meaningful differences.
- Keep formulas consistent across periods. Use absolute references for fixed assumption cells and deliberate relative references for period values.
- Guard genuinely possible zero denominators with a meaningful result; do not blanket-wrap everything in `IFERROR(...,0)` because it conceals broken links and wrong formulas.
- Include reconciliation totals and representative expected results. An error-free formula referencing the wrong row is still wrong. Verify the sum range's first/last row and independently check a base and edge scenario.
- For a new input template, identify editable cells and include one realistic example row. Do not insert invented rows into an existing financial dataset.

With openpyxl use `Font`, `PatternFill`, cell comments and number formats instead of manually aligning text with spaces. Keep totals visibly distinguishable and panes frozen where useful. A balanced model and a successful LibreOffice recalculation do not establish accounting validity or approval.
