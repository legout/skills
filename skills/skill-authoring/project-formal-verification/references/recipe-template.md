# Generated formal recipe template

Fill this skeleton for the project's existing recipe name or `.agents/skills/verify-<project>-<area>/SKILL.md`. Replace every PLACEHOLDER, remove inapplicable items, and label unresolved facts and unexecuted instructions explicitly. Reuse established verification artifacts; do not copy them into the skill.

```markdown
---
name: verify-PROJECT-AREA
description: Check PROPERTY in PROJECT AREA. Use when COVERED_SYMBOLS, their state writers, or stated assumptions change, or when a task needs evidence for this specific property.
---

# Verify PROJECT AREA

## Property and scope
- Property / harm / independent source: PLACEHOLDER.
- Method and covered artifact: PLACEHOLDER.
- Initial states, bounds, assumptions, exclusions: PLACEHOLDER.

## Code correspondence
- Actions or proof obligations → source files/symbols and real atomic boundaries: PLACEHOLDER.
- Related callers and writers of the same guarded state: PLACEHOLDER.
- Last confirmed correspondence commit, or unknown: PLACEHOLDER.
- Relevant uncommitted differences, if any: PLACEHOLDER.
- Before relying on a result, inspect relevant changes against this mapping, including moved code and new writers. Unresolved correspondence prevents a code-level claim; merely rerunning the checker does not resolve it.

## Prerequisites and permissions
- Exact tool version and configuration, existing invocation, fixture and isolation requirements: PLACEHOLDER.
- Authorized actions, scratch-only fault injection, and forbidden product/remote actions: PLACEHOLDER.
- Missing prerequisites or unexecuted steps: PLACEHOLDER.

## Run and interpret
- Command and bounded runtime/resource budget: PLACEHOLDER.
- Exact successful result, property-failure result, and incomplete/error interpretation: PLACEHOLDER.
- Counterexample-to-code replay procedure: PLACEHOLDER.
- Evidence location outside disposable scratch: PLACEHOLDER.
- Reuse applicable evidence; run only for the assigned claim, a relevant delta, or a specific hypothesis. Report property, method, scope, correspondence, result and exclusions; unknown or incomplete is not a pass.

## Negative control and restoration
- Relevant scratch defect and intended property failure: PLACEHOLDER.
- For a separate model, the source change requiring alignment review and the corresponding modeled defect: PLACEHOLDER.
- Existing failure baseline, distinguishing observation, restoration and owned-resource cleanup: PLACEHOLDER.
- Show the control on creation and when its detection path changes, only with applicable authority. Preserve the original property and baseline findings; a tool error is not successful defect detection.

## Maintenance
- Changes that invalidate correspondence or execution evidence: PLACEHOLDER.
- Relevant drift routes to the update mode of `project-formal-verification`; request maintenance authority if absent. Confirm alignment before advancing its commit; keep code bugs as findings and property changes tied to approved requirements.
```
