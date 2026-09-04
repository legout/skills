---
name: doc-coauthoring
description: Guide users through a structured workflow for co-authoring documentation, proposals, technical specifications, decision records, and similar documents. Use when a substantial document needs context gathering, iterative refinement, or reader testing.
---

# Document co-authoring

Own the collaborative context-gathering, drafting, and reader-testing process for substantial documents. Consume the document type and quality constraints from `documentation-writer`; do not create a competing classification workflow. Keep the user in control of scope and decisions while turning unstructured context into a document that works for an independent reader.

## Operating mode

Offer the structured workflow first. If the user prefers to work freeform, skip the staged process and help directly. Do not impose a long interview on a small edit.

The workflow has three stages:

1. Context gathering
2. Refinement and drafting
3. Reader testing

## Stage 1: Context gathering

Establish:

- document kind and intended audience;
- outcome the reader should achieve;
- required format or template;
- scope, constraints, and non-goals;
- source material, repository paths, and relevant decisions.

Ask focused questions, then invite an unstructured context dump. Read supplied files and links when authorized. Track unresolved gaps and do not fill them with guesses.

For technical documentation, inspect the implementation, tests, schemas, and existing documentation that own the facts. For Python projects, identify the Zensical configuration and docs layout before proposing changes.

## Stage 2: Refinement and drafting

1. Propose an outline suited to the document kind and audience.
2. Confirm the structure or record the user's requested changes.
3. Create a minimal scaffold only when the document is substantial enough to benefit from one.
4. Work section by section. For each section, clarify gaps, identify useful content, draft it, and apply focused revisions.
5. Keep facts, decisions, assumptions, and open questions distinguishable.
6. Re-read the whole document for flow, redundancy, contradictions, and unsupported claims before moving to reader testing.

Leave summaries until the supporting content is stable when the document's conclusion depends on the details.

## Stage 3: Reader testing

Test whether an independent reader can use the document:

1. Predict realistic questions a reader would ask.
2. Answer them using only the document and its linked references.
3. Check for ambiguity, missing prerequisites, contradictions, and unexplained terms.
4. Fix the smallest section that caused each problem.
5. Repeat until the document answers the important questions reliably.

When subagents are available, use a fresh context containing only the document, references, and reader question. Do not leak the author's working context into the test.

## Project integration

- Compose with `documentation-writer` to select the Diátaxis document type and maintain documentation quality.
- When the repository uses Zensical, use `uv run zensical serve` to preview and `uv run zensical build` to validate publishability.
- For library and API documentation, verify examples and reference entries against the code, public exports, schemas, serializers, and tests.

## Upstream basis

This local adaptation is based on the three-stage workflow described by Anthropic's [`doc-coauthoring`](https://github.com/anthropics/skills/blob/41bbe19d1a1a7eaab5e7bb9050a417e5c6cffc8f/skills/doc-coauthoring/SKILL.md) skill, pinned to commit `41bbe19d1a1a7eaab5e7bb9050a417e5c6cffc8f`. The upstream repository does not state a license for this skill; this repository contains an independent adaptation rather than a verbatim copy.
