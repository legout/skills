---
name: agent-md-refactor
description: Refactor bloated AGENTS.md, CLAUDE.md, or similar agent instruction files into a small root contract plus linked, scoped references. Use when an agent instruction file is repetitive, contradictory, or difficult to navigate.
license: MIT
---

# Refactor Agent Instructions

Turn a monolithic instruction file into a navigable instruction graph without changing its meaning.

## Before Editing

1. Identify the target file and every runtime that consumes it.
2. Read the complete target, any nested instruction files, and every document it links to.
3. Check repository conventions for documentation locations and instruction precedence.
4. Record duplicated rules, contradictions, stale guidance, and scopes that apply only to certain tasks or directories.
5. Stop and ask the user when two authoritative rules conflict. Do not silently choose one.

Do not assume one agent's filenames, import syntax, or precedence rules work in another runtime. Consult the installed runtime documentation when discovery behavior is uncertain.

## Classify the Content

Assign each instruction to exactly one destination:

- **Root contract:** universal commands, repository-wide constraints, safety rules, and links to deeper guidance.
- **Scoped reference:** topic- or subsystem-specific procedures needed only for a subset of tasks.
- **Nested instruction file:** rules that truly apply only below a directory and are supported by the consuming runtime.
- **Delete:** duplicated, stale, generic, or self-evident prose that adds no project-specific value.
- **Unresolved:** contradictory guidance that requires a human decision.

Prefer semantic boundaries over arbitrary line-count targets. Keep a coherent workflow together when splitting it would force agents to load several files for one task.

## Design the Instruction Graph

The root file should answer only:

1. What is this repository?
2. Which commands and constraints apply to every task?
3. Where is the authoritative guidance for each specialized workflow?

Choose reference locations that match existing repository conventions. Do not introduce a tool-specific directory merely because an example used one.

Use links relative to the file containing them. Keep the graph shallow when possible, and give every link a descriptive label that tells the agent when to read it.

Example:

```markdown
## Detailed Guidance

- [Testing](docs/agents/testing.md) — commands, fixtures, and coverage expectations
- [Architecture](docs/agents/architecture.md) — module boundaries and dependency rules
- [Releases](docs/agents/releases.md) — versioning and publication workflow
```

Avoid chains of placeholder files that only point elsewhere. Link directly to the authoritative content unless precedence or runtime discovery requires an intermediate file.

## Refactor Safely

Before writing, show the proposed destination for each section and any deletions. After approval:

1. Create only the references needed for real scoped content.
2. Move authoritative guidance rather than copying it.
3. Replace moved root sections with concise links.
4. Preserve exact commands, paths, prohibitions, precedence, and user-defined terminology.
5. Remove duplicate companion summaries unless they serve a distinct human-facing purpose.
6. Do not rewrite policy while reorganizing it; propose behavioral changes separately.

## Verify

Check all of the following before claiming completion:

- Every referenced path exists and resolves from the linking file.
- Every retained instruction has one authoritative home.
- No command, constraint, exception, or prohibition was lost.
- No contradictory duplicate remains.
- Runtime-specific discovery and precedence still work.
- The root file can orient an agent without loading unrelated material.
- `git diff --check` and any repository documentation tests pass.

Report the new structure, deletions, unresolved conflicts, and verification evidence.

## Sources and Adaptations

The inventory-first extraction and organizational-pattern guidance is adapted from Matt Pocock's [`writing-for-agents`](https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/productivity/writing-for-agents/SKILL.md) skill. This local workflow removes fixed directory and size prescriptions so repository conventions and runtime documentation remain authoritative.
