---
name: skill-distribution-audit
description: Audit a skill catalog's intended releases against its manifests and a specific consumer's discovery results. Use for installer omissions, unexpected skills, duplicate identities, or release distribution drift.
---

# Skill Distribution Audit

> Adapted from [github/awesome-copilot `skill-distribution-audit`](https://github.com/github/awesome-copilot/tree/a06ba06d11f41b996f8c246e2a452e1bf3a17950/skills/skill-distribution-audit) at `a06ba06d11f41b996f8c246e2a452e1bf3a17950` (MIT, Copyright GitHub, Inc.).

Audit only when requested; this is not an automatic release gate. It is read-only unless the user separately authorizes repairs. `effective-agent-skills` owns skill authoring and `project-verification` owns real-use verification recipes.

## Audit

1. Establish the source revision, target consumer and version, intended scope, and distribution contract from the repository's actual policy. Inspect the consumer's documentation or implementation before asserting its discovery rules. Distinguish public skills from fixtures, archives, templates, generated copies and internal material. A manifest alone is not the intended-set oracle.
2. Map intended identities to source paths, preserving duplicates. Parse frontmatter with a YAML parser compatible with the target consumer; distinguish invalid YAML from valid metadata rejected by that consumer. Inspect manifest paths, exclusions and globs where applicable. Use the consumer's actual input: a manifest for another installer may not control discovery.
3. Inspect how the target consumer lists skills before running it; listing may download or write. Only run within existing authorization, preferably on an isolated source snapshot. Record the exact command, source revision, consumer version, exit status, stderr and any pagination or truncation. Existing captured output is historical evidence. If discovery is unavailable or incomplete, report it as unverified rather than a pass. Never execute skill bodies to collect discovery evidence.
4. Compare exact identities, not counts: intended versus manifest and intended versus discovery, plus manifest versus discovery when relevant. Report missing, unexpected and duplicate identities, parse failures, and ambiguous name-to-path mappings separately. Equal counts do not prove matching sets. Reuse existing repository checks or ordinary set comparison rather than adding a helper by default.
5. Report each discrepancy with its identities, evidence paths, observed behavior, likely cause and smallest proposed repair. Include scope, revisions, versions, relevant counts and limitations; allow a clean result. Discovery parity does not prove live skill invocation, helper execution or external-service access. After an authorized repair, recheck only affected evidence.
