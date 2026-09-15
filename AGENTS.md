# Agent guidance

## Implementation and review ground rules

- Priority: agreed feature, then correctness, then proven risk. Written conventions are binding; violations are must-fix, unwritten taste never blocks. Name the applicable rule. This catalog's conventions are in `skills/skill-authoring/effective-agent-skills/SKILL.md`, `tests/skills_test.sh`, and `README.md`; preserve source attribution and approval/publication gates.
- Findings require a named requirement or written rule, a problem this change caused or worsened, reachability through real callers/inputs/environment, material impact, and a proportionate response.
- Security review requires a touched boundary (untrusted/external input, credentials, auth, dependency changes), a named asset, realistic attacker, and actual attack path. Stories needing stolen secrets, broken TLS, malicious admins, or generic hardening are not findings. No boundary touched: `security: n/a`; missing security facts: `unverified`, never invent a threat model. Local authored skill text and user-owned files are trusted; external content consumed by a skill may cross a boundary. Written safety contracts still bind.
- Test requests are findings: name the real scenario or drop them; coverage percentage is not a reason. Use existing focused checks when sufficient; for `new-test`, one behavior and one failing test first. Dependencies and abstractions need a job today.
- Disposition before repair: parent rejects failed gates in one line, authorizes small in-scope fixes, or hands large/out-of-scope fixes to the human. Reviewer output never overrides approved intent; reviewers do not start fixes or re-reviews.
- Paste the full gates with criteria, conventions, and real-use context into every fresh reviewer prompt; links alone are insufficient. Done means criteria, real risks, and written rules covered: `pass` or `fix-first`, then stop. One fix pass, one delta recheck, then ask the human; no third round or reopening settled findings at candidate review.
- After each task: restate it, compare the result, choose `accept / fix / hand back / ask`. Extra ideas get one line, not code. Use existing reports, not new evidence ledgers, lifecycles, or sign-off artifacts.

## Completion-boundary cleanup

Before committing, opening a pull request, or handing off substantive code, offer one `simplify-code` pass on the changed code. Run it only after a user request or that completion-boundary offer is accepted. Do not run it on every edit, docs-only work, generated artifacts, or mechanical changes.

Suggest `deslop` only when `simplify-code` findings reveal broader systemic scope, and widen to it only after the user accepts. Otherwise use `deslop` only for an explicit broad codebase cleanup request or a deliberately offered deep cleanup pass. It is not an alias for `simplify-code`, and the two cleanup skills are never chained by default.
