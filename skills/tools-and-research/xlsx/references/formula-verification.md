# Formula verification

## Recalculation helper

`uv run --no-project <skill>/scripts/recalc.py draft.xlsx calculated.xlsx --timeout 120`

The helper copies the input to a temporary directory, converts with an isolated LibreOffice profile and validates the result. It checks all error-valued cells and the original formula coordinates for lost formulas/missing caches. It does not replace the original. If verification fails, the requested output is not published and JSON names the error; exit 1 means formula errors, exit 2 means conversion/precondition failure.

An empty-string formula result may read as `None` in openpyxl; the helper recognizes explicitly cached empty text rather than treating it as a missing numeric value. It does not silently accept an absent numeric cache.

## Engine compatibility

Excel and LibreOffice differ. Prefer established functions such as `SUM`, `SUMIFS`, `IF`, `IFERROR`, `INDEX` and `MATCH` when portability is required, but follow the user's intended calculation rather than arbitrarily substituting a different business rule. Newer Excel functions can require `_xlfn.` metadata; openpyxl does not translate formulas.

The helper refuses array/spill objects and formulas using FILTER, SORT, SORTBY, UNIQUE, SEQUENCE, RANDARRAY, XLOOKUP or XMATCH. Some are supported in some LibreOffice releases; this conservative gate avoids claiming Excel-equivalent results from an unverified engine/spill representation. Use Excel to verify those workbooks. Other functions can still differ; error scanning is not a universal compatibility certificate.

External workbook links are rejected before conversion because missing files and rewritten caches can damage a linked model. Do not strip those links or use old cached values as if they were recalculated. Open Excel with the authorized linked files available. XLSM/XLTM and signatures also need native application handling.

## Result checks

Before building a large formula grid, verify representative formulas against independent calculations, including zero/blank inputs where meaningful. After recalculation, separately load formulas and cached values. Compare expected values with an appropriate tolerance and units; verify copied formulas reference the correct periods. Keep the original so any inherited error can be demonstrated, not merely asserted.

If LibreOffice is missing or crashes/times out, report the workbook as generated but **not recalculated**. Ask the user to open/recalculate/save in Excel and supply the result for checking. A successful structural validation or process exit cannot substitute for result verification.
