---
name: effective-agent-skills
description: How to write effective agent skills — what to do, what not to do, anatomy, progressive disclosure, design patterns, anti-patterns, testing, security. Read this whenever a skill (Claude Skill, Agent Skill, SKILL.md) is being created, edited, reviewed, or debugged. Use when the user says "create a skill", "new skill", "update this skill", "improve a skill", "why isn't my skill triggering", or anything else involving authoring or editing SKILL.md files.
---

> Adapted from [David Ondrej's `effective-agent-skills`](https://github.com/davidondrej/skills/tree/11dee2ebc2d045806b686ba0b57746f1e3d7e331/skills/skill-authoring/effective-agent-skills) at commit `11dee2ebc2d045806b686ba0b57746f1e3d7e331` (MIT). Recurring-correction enforcement is adapted from Cursor's [`poteto-mode`](https://github.com/cursor/plugins/tree/93b00b89ef425a9c1bac0d0b317dfc49c930ac99/pstack/skills/poteto-mode) at commit `93b00b89ef425a9c1bac0d0b317dfc49c930ac99` (MIT, Copyright (c) 2026 Cursor).

# Effective Agent Skills

## Workflow

1. Define one coherent capability or discipline.
2. Write the description first: what it does, when it should trigger, and the differentiator from nearby skills. Do not summarize the workflow there.
3. Keep the ordinary execution path, safety gates, output contract, and verification loop in `SKILL.md`.
4. Move uncommon detail into directly linked `references/`; put fragile or repetitive logic in tested `scripts/`.
5. Test positive triggers, near-miss negatives, explicit invocation, execution, failure handling, and links.

Read [the authoring guide](references/authoring-guide.md) for anatomy, design patterns, composition, security, and detailed examples.

## Rules

- Use valid YAML frontmatter with `name` and one concise `description` line.
- Match the skill name to its leaf directory and keep names stable.
- Use relative paths and one reference level; tell the agent exactly when to open each file.
- Do not reteach general knowledge, bundle unrelated workflows, or include human-facing README files.
- Preserve approval, publication, credential, destructive-action, and evidence-before-claim gates.
- Prefer installed tools and `--help` over copied command catalogs.
- When the same correction recurs, decide whether it belongs in concise prose, routing metadata, an evaluation, or executable enforcement. Prefer a lint rule, schema, metadata constraint, test, or script when prose repeatedly fails; do not automate subjective preferences that still require judgment.
- Treat skills as code: validate, test, review, and version them.

## Verification

Confirm frontmatter parses strictly, every local link resolves, scripts run, the skill triggers on intended prompts, nearby skills win their own prompts, and the shortest supported workflow still completes. Test description routing separately from workflow execution.
