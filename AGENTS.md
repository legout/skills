# Agent guidance

## Completion-boundary cleanup

Before committing, opening a pull request, or handing off substantive code, offer one `simplify-code` pass on the changed code. Run it only after a user request or that completion-boundary offer is accepted. Do not run it on every edit, docs-only work, generated artifacts, or mechanical changes.

Suggest `deslop` only when `simplify-code` findings reveal broader systemic scope, and widen to it only after the user accepts. Otherwise use `deslop` only for an explicit broad codebase cleanup request or a deliberately offered deep cleanup pass. It is not an alias for `simplify-code`, and the two cleanup skills are never chained by default.
