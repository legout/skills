---
name: improve-skill
description: Improve or create Agent Skills from coding-agent session transcripts. Use when session history is the evidence.
---

> Eval-style pre-change/post-change comparison and recurring-correction enforcement are adapted from Cursor's [`poteto-mode`](https://github.com/cursor/plugins/tree/93b00b89ef425a9c1bac0d0b317dfc49c930ac99/pstack/skills/poteto-mode) at commit `93b00b89ef425a9c1bac0d0b317dfc49c930ac99` (MIT, Copyright (c) 2026 Cursor).

# Improve Skill

This skill helps analyze coding agent sessions to improve or create skills. It works with Claude Code, Pi, and Codex session files. Resolve `SKILL_DIR` to this file's parent directory before running its script.

## Quick Start

Extract the current session and generate an improvement prompt:

```bash
# Auto-detect agent and extract current session
node "$SKILL_DIR/scripts/extract-session.js"
```

## Session Extraction

The `extract-session.js` script finds and parses session files from any of the three agents:

```bash
# Auto-detect (uses most recent session for current working directory)
node "$SKILL_DIR/scripts/extract-session.js"

# Specify agent type
node "$SKILL_DIR/scripts/extract-session.js" --agent claude
node "$SKILL_DIR/scripts/extract-session.js" --agent pi
node "$SKILL_DIR/scripts/extract-session.js" --agent codex

# Specify a different working directory
node "$SKILL_DIR/scripts/extract-session.js" --cwd /path/to/project

# Use a specific session file
node "$SKILL_DIR/scripts/extract-session.js" /path/to/session.jsonl
```

**Session file locations:**

- **Claude Code**: `~/.claude/projects/<encoded-cwd>/*.jsonl`
- **Pi**: `~/.pi/agent/sessions/<encoded-cwd>/*.jsonl`
- **Codex**: `~/.codex/sessions/YYYY/MM/DD/*.jsonl`

## Analyze and improve

1. Extract the relevant session.
2. Read the current skill when improving one.
3. Find retries, confusion, missing examples, failed commands, workarounds, and successful patterns.
4. Change only guidance supported by the trace; shorten anything the model already knows.
5. Test description routing separately from workflow execution.
6. Compare pre-change and post-change behavior before promoting a skill change; a change without an observed behavioral difference is a guess.

A correction that recurs across sessions is a candidate for executable enforcement — a lint rule, schema, test, or script — rather than another paragraph of prose. Keep one-off preferences and judgment calls as prose, or out of the skill entirely.

For a self-contained fresh-session prompt, use [prompt templates](references/prompt-templates.md).

## Why a Separate Session?

The improvement prompt is meant to be copied into a **fresh agent session** because:

1. **Token efficiency** - The current session already has a lot of context; starting fresh means only the transcript and skill are loaded
2. **Clean analysis** - The new session can focus purely on improvement without being influenced by the current task
3. **Reproducibility** - The prompt is self-contained and can be shared or reused

## Tips for Good Skill Improvements

When analyzing a transcript, look for:

- **Confusion patterns** - Where did the agent retry or change approach?
- **Missing examples** - What specific commands or code patterns were discovered?
- **Workarounds** - What did the agent have to figure out that wasn't documented?
- **Errors** - What failed and how was it resolved?
- **Successful patterns** - What worked well and should be highlighted?

Keep skills concise - focus on the most important information and examples.
