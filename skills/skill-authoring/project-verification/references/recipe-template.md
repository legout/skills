# Generated recipe template

Fill this skeleton for `.agents/skills/verify-<project>/SKILL.md` and replace every `PLACEHOLDER`. Delete sections that do not apply to the project; do not keep unused scaffolding. The generated recipe is a cold-start operating guide, not a test policy or evidence ledger.

```markdown
---
name: verify-PROJECT
description: Launch PROJECT and prove its real user surface with independently derived expectations. Use when a task in this repository needs verified evidence about PROJECT's startup, UI, CLI, or persistence behavior, or when a completion claim names PROJECT's runtime behavior.
---

# Verify PROJECT

## Target identity
- PLACEHOLDER: repository, launch path, and how to confirm the correct installed or built artifact (version command, build hash, package identity).

## Prerequisites and permissions
- PLACEHOLDER: required tools, environment, credentials, fixtures, and authorized actions. Name isolated ports/data/profile ownership; stop if isolation is unavailable rather than adopting a user instance. Name forbidden production, browser, or shared-service actions.

## Launch
- PLACEHOLDER: exact commands and prerequisites to reach a usable state. Include migrations/seeds from empty state when that is the claim; name setup supplied by a stand-in and still unverified on the real target. Stop only what you started.

## Readiness check (read-only)
- PLACEHOLDER: commands confirming health, artifact identity, and ownership before driving and after surprising behavior. Missing journey prerequisites block the journey, not permission to relax it.

## Journey: PLACEHOLDER (one important user-facing scenario)
- Steps: PLACEHOLDER: concrete commands or selectors on the real user surface.
- Expected: PLACEHOLDER: the independently derived expectation and its source (requirement, approved example, trusted reference). Never copied from current output.
- Evidence: PLACEHOLDER: capture the action and outcome, command/output/exit code or selector observation, and side effects. For dry-run/test mode, observe which relevant effects occur or are prevented rather than trusting the label.
- Read-back: PLACEHOLDER: the persisted-state check that proves the outcome survived (reopen, re-query, restart when the claim includes restart survival).

## Cleanup
- PLACEHOLDER: stop only owned resources, including failed-attempt residue; remove scratch state and verify the named evidence artifacts still exist outside it.

## Feature menu
- PLACEHOLDER: one-line index of further journeys, each naming its entry point and observable end state. Promote a journey to `features/<name>.md` only when it outgrows this section.
```
