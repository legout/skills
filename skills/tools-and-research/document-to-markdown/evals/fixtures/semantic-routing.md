# Synthetic semantic-fidelity case

This is invented evaluation data, not an excerpt from a private document.

## Page 1: printed form

| Name | Company | Department |
| --- | --- | --- |
| Ada Example | Example Ltd | Research |
| Bert Sample | | Sample University |

- [x] Lunch
- [ ] Dinner
- [x] External

Printed total: **12,00 EUR**. Purpose is not filled.

## Page 2: two independent receipt regions

Left region: expense type, purpose, location `ABC`, guest count and a simulated
handwritten name. Right region: item/price pairs, net **12,01**, gross **13,21**,
and VAT row `10.00 | 12,01 | 13,21 | 1,20`.

Acceptance is source-based: keep the university under Department, preserve the
blank company cell, verify all three selection states, keep regions separate,
and preserve the different totals rather than make them consistent.
