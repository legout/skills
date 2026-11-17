# Sources and adaptations

App/core commands are checked against the installed `herdr-app --help`,
`herdr-app --skill`, `hc --help`, `hc --skill` and the generated
`~/.config/herdr-app/AGENTS.md` (or the selected `HERDR_APP_HOME`).
Installed help is authoritative for current syntax.

Legacy Herdr behavior is based on the canonical Apache-2.0
[`herdr` skill](https://github.com/herdrdev/herdr/blob/5bd900d88c80d95f5b145397e45bbeea398b8165/skills/herdr/SKILL.md).
cmux command vocabulary is fact-checked against the canonical GPL-3.0
[`cmux` skill](https://github.com/manaflow-ai/cmux/blob/4256df053a63339d7e786157a9846a765762b4cf/skills/cmux/SKILL.md)
without copying its text. The narrow existing-target workflow adapts MIT
guidance from David Ondrej's
[`herdr`](https://github.com/davidondrej/skills/blob/11dee2ebc2d045806b686ba0b57746f1e3d7e331/skills/agent-orchestration/herdr/SKILL.md)
and
[`cmux`](https://github.com/davidondrej/skills/blob/11dee2ebc2d045806b686ba0b57746f1e3d7e331/skills/agent-orchestration/cmux/SKILL.md)
skills.
