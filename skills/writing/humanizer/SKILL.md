---
name: humanizer
description: Rewrite AI-sounding prose so it reads naturally without changing its facts or the writer's voice.
---

> Adapted from [`blader/humanizer`](https://github.com/blader/humanizer/tree/e2e92e7b4b8229253ed5c8e81dc65463fdeddda5) and [`cursor/plugins`](https://github.com/cursor/plugins/tree/93b00b89ef425a9c1bac0d0b317dfc49c930ac99) at the pinned commits recorded in `sources.json` (MIT).

# Humanizer

Rewrite prose so it sounds natural while preserving its claims and intended voice.

## Workflow

1. Read the source and any writing sample. Match the sample's register, rhythm, vocabulary, and punctuation.
2. Mark concrete AI-writing patterns. Read [the pattern catalog](references/pattern-catalog.md) when the text is substantial or the user asks for a thorough pass.
3. Rewrite whole sentences or paragraphs rather than swapping watched words mechanically.
4. Check that no fact, name, number, date, quote, citation, ranking, or link target was invented, removed, or changed.
5. Read the result aloud, remove remaining stock phrasing, and return the requested form.

A single watched phrase is not proof of AI writing. Keep quotations, proper names, useful caveats, deliberate repetition, technical terms, and quirks supported by the writer's sample.

## Voice

- Keep formal, technical, legal, and reference text neutral.
- Preserve opinions, uncertainty, humor, asides, and first person when they belong to the writer.
- Prefer concrete subjects, plain verbs, specific facts, and varied sentence length.
- Do not impose blanket bans on dashes, parentheses, first person, or personality. Match the source voice.

## Output

- **Pasted text:** return the rewrite; mention unresolved issues only when useful.
- **Named file:** change prose only. Preserve code blocks, metadata, data, and link targets, then summarize the edit.
- **Embedded use:** return only the rewritten text.
