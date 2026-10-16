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
- PLACEHOLDER: required tools, environment, credentials, and data fixtures, and the authorizations a run needs. Name what is NOT authorized (production data, user browsers, shared-service restarts).

## Launch
- PLACEHOLDER: exact commands to reach a usable state, how to recognize readiness (not merely a running process), and teardown. Stop only what you started.

## Readiness check (read-only)
- PLACEHOLDER: commands confirming instance health, version, and ownership before driving.

## Journey: PLACEHOLDER (one important user-facing scenario)
- Steps: PLACEHOLDER: concrete commands or selectors on the real user surface.
- Expected: PLACEHOLDER: the independently derived expectation and its source (requirement, approved example, trusted reference). Never copied from current output.
- Evidence: PLACEHOLDER: what to capture (command, output, exit code, selector observation), including side effects.
- Read-back: PLACEHOLDER: the persisted-state check that proves the outcome survived (reopen, re-query, restart when the claim includes restart survival).

## Cleanup
- PLACEHOLDER: owned resources to stop, scratch state to remove, and evidence artifacts to retain.

## Feature menu
- PLACEHOLDER: one-line index of further journeys, each naming its entry point and observable end state. Promote a journey to `features/<name>.md` only when it outgrows this section.
```
