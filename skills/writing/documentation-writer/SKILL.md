---
name: documentation-writer
description: Diátaxis Documentation Expert. Use when creating high-quality software documentation across tutorials, how-to guides, reference documentation, and explanations.
---

# Diátaxis documentation writer

Own document-type classification and quality constraints using the [Diátaxis framework](https://diataxis.fr/). For a substantial collaborative document, classify it first and then hand the drafting process to `doc-coauthoring`; for a small edit, work directly.

## Document types

Choose the type before drafting:

- **Tutorial:** learning-oriented guidance that teaches through a successful outcome.
- **How-to guide:** problem-oriented steps that solve a specific task.
- **Reference:** information-oriented descriptions of APIs, commands, configuration, and other machinery.
- **Explanation:** understanding-oriented discussion of concepts, design, and trade-offs.

## Workflow

1. **Clarify:** Identify the document type, audience, reader goal, scope, and exclusions. Ask only questions that materially affect the result.
2. **Outline:** Propose a structure with a short purpose for each section. For substantial documents, wait for approval before drafting.
3. **Draft:** Write well-formatted Markdown with clear headings, concrete examples, and consistent terminology.
4. **Verify:** Check claims, examples, links, code, terminology, and the document type. Ground technical details in repository sources or user-provided references.

## Writing principles

- Prefer plain, direct language and short, scannable paragraphs.
- Give each document a specific reader and a specific outcome.
- Keep tutorials, how-to guides, reference material, and explanations distinct instead of mixing their purposes.
- Do not invent behavior, configuration, APIs, or URLs.
- Treat examples as illustrative unless the document explicitly makes them normative.
- Read comparable documents in the target directory first and follow its conventions.
- Extend an existing document when it already owns the topic instead of creating a competing page.

## Repository integration

- Use `doc-coauthoring` for the collaborative context, refinement, and reader-testing process on substantial documents.
- For Python projects using Zensical, preview with `uv run zensical serve` and validate the generated site with `uv run zensical build`.
- For API and library reference pages, verify the public surface against source code, serializers, schemas, and tests before documenting it.

## Source

Adapted under MIT from GitHub's [`documentation-writer`](https://github.com/github/awesome-copilot/blob/7b1ebe6333397841ca918dec904d24d4695fe953/skills/documentation-writer/SKILL.md), pinned to commit `7b1ebe6333397841ca918dec904d24d4695fe953`.
