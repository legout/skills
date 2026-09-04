---
name: capture-project-vision
description: Interview the user to capture a project's vision and confirmed durable decisions using the repository's documentation conventions.
---

# Capture Project Vision

> Adapted from [`davidondrej/skills` brain-to-docs](https://github.com/davidondrej/skills/blob/11dee2ebc2d045806b686ba0b57746f1e3d7e331/skills/thinking-and-docs/brain-to-docs/SKILL.md) at commit `11dee2ebc2d045806b686ba0b57746f1e3d7e331` (MIT). Its fixed documentation layout and write-after-every-answer rule were replaced with repository discovery and explicit approval.

Extract the user's purpose, taste, constraints, principles, and durable decisions into concise project documentation. This is an explicit interview, not an automatic side effect of ordinary development. Do not shape or implement a specific feature here; hand concrete build questions to `shape-design`, which owns feature-level design.

## Discover conventions

Read the current `README.md`, project instructions, documentation index, `CONTEXT.md` or `CONTEXT-MAP.md`, and existing decision records. Infer where this repository keeps vision and decisions. If no convention exists, propose locations before writing; do not silently create a fixed structure.

## Interview loop

1. Ask a small round of independent, high-variety questions about audience, problem, experience, principles, constraints, success, and non-goals.
2. Recommend answers only when repository evidence supports them.
3. Let the user answer whichever questions are useful.
4. Summarize the new facts and propose exact edits.
5. Write only after approval.
6. Re-read the changed docs before the next round so concurrent edits and settled answers become the new baseline.
7. Continue until the user says the vision is sufficiently captured.

Use short, plain language. Do not challenge taste unless asked, but surface contradictions, severe risks, and conflicts with existing decisions.

## Route each answer

- **Vision document or README:** purpose, audience, principles, intended experience, success, and non-goals.
- **Domain glossary:** one canonical project-specific term and its meaning, without implementation detail.
- **Decision record:** only a hard-to-reverse, surprising trade-off chosen from real alternatives.
- **Nowhere:** transient implementation detail, repeated facts already visible in code/config, or speculation the user has not adopted.

Follow existing templates and numbering. Keep each fact in one authoritative place and link rather than duplicate.

## Completion

Finish with:

- files changed;
- vision and decisions captured;
- contradictions or open questions still unresolved; and
- the next highest-value interview area, if the user wants another round.

Never commit or push unless the user separately asks.
