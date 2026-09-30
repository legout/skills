# Research: Human-readable and agent-usable wiki pages

Status: research evidence, not approval to implement. Inspected 2026-09-30.
Planning contract: version 1; installed skill revision/provenance: unknown.

## Question and scope

Compare the writing rules in the four repositories supplied by the owner. Identify a minimal addition to the existing **English-language** second-brain skill that makes authored wiki pages, including source summaries and reading views, useful to both people and agents. The language of the reusable skill is separate from the language of a particular wiki.

This note describes instructions, templates and selected implementation files. It does not establish how reliably models follow them in practice. Repository code was not executed. The existing second-brain skill and CLI were not changed.

## Evidence

### eugeniughelbur/obsidian-second-brain: explicitly agent-first

Snapshot: `b0089f7666d0c1e3db41c9d587b6f3c997665235` (`main`).

The [skill](https://github.com/eugeniughelbur/obsidian-second-brain/blob/b0089f7666d0c1e3db41c9d587b6f3c997665235/SKILL.md) explicitly says: “The vault is designed for **future agent** to read and reason over, not for human review.” Its useful transferable mechanisms are self-contained context, a short relevance preamble, machine-readable metadata, source attribution and freshness qualifiers.

The [portable AI-FIRST rules](https://github.com/eugeniughelbur/obsidian-second-brain/blob/b0089f7666d0c1e3db41c9d587b6f3c997665235/AI-FIRST.md) require a fixed `## For future agent` header and “Two or three plain sentences” explaining the content, why it was saved, and caveats. The [write rules](https://github.com/eugeniughelbur/obsidian-second-brain/blob/b0089f7666d0c1e3db41c9d587b6f3c997665235/references/write-rules.md) also instruct the writer to read existing notes and match their heading structure, tone and list style.

Assessment: useful context and evidence discipline, but its explicit agent-first objective is not the owner's desired equal emphasis on human readability. Do not copy its fixed agent-only preamble wholesale.

### Ar9av/obsidian-wiki: page templates plus a separate writing profile

Snapshot: `972de66b481db44f5e25ce73da0263ee0246c27b` (`main`).

The canonical [LLM Wiki skill](https://github.com/Ar9av/obsidian-wiki/blob/972de66b481db44f5e25ce73da0263ee0246c27b/.skills/llm-wiki/SKILL.md) supplies a page template with frontmatter, a short `summary`, a one-paragraph introduction, Key Ideas, Open Questions and Sources. Its summary is “One or two sentences, ≤200 chars, so a reader (or another skill) can preview this page without opening it.” It distinguishes extracted, inferred and ambiguous claims using inline markers.

Its writing-profile resolution is particularly relevant: preferences apply to newly drafted or rewritten natural-language fields and body text, but “cannot alter YAML syntax, required keys, structure, types, or machine-generated fields.” Structured logs and pass-through content remain unchanged. The optional [WRITING.md profile](https://github.com/Ar9av/obsidian-wiki/blob/972de66b481db44f5e25ce73da0263ee0246c27b/.skills/llm-wiki/references/WRITING.md) has headings for Language, Tone, Structure and Content Density, Evidence and Uncertainty, and other preferences; it does not prescribe values by default.

Citation detail: `.agents/skills/llm-wiki` is a Git symlink to `../../.skills/llm-wiki`. Cite `.skills/...` files: a raw URL that attempts to traverse the symlink returns HTTP 404.

Assessment: adopt the separation of invariant schema/evidence rules from prose preferences. Keep our existing `schema.md` as the owner-editable surface; a new writing-profile subsystem is unnecessary for this bounded task. Do not import Obsidian-specific inference markers or a mandatory new summary field without a separate need.

### nashsu/llm_wiki: explicit output-language instructions

Snapshot: `48fd970e206a02a6d2028d1dbfc41b7a0345bf0b` (`main`).

The [output-language helper](https://github.com/nashsu/llm_wiki/blob/48fd970e206a02a6d2028d1dbfc41b7a0345bf0b/src/lib/output-language.ts) constructs a `MANDATORY OUTPUT LANGUAGE` directive. It states: “All generated prose, including prose titles and section headings, must be in” the selected language. It separately preserves names, identifiers, URLs, filenames, paper titles and citation strings, and explicitly allows evidence to be in another language.

The [schema templates](https://github.com/nashsu/llm_wiki/blob/48fd970e206a02a6d2028d1dbfc41b7a0345bf0b/src/lib/templates.ts) describe page types, metadata and evidence conventions. The language directive is an instruction to the model, not proof of output-language validation or perfect compliance. The full ingestion implementation was not inspected end-to-end.

Assessment: directly applicable distinction between instruction language, wiki prose language and unchanged technical/source content. Do not infer that an English skill requires an English wiki.

### nvk/llm-wiki: self-contained explanatory articles

Snapshot: `1224fbcdf3827f4ba56d225a9e359f5e8a5594e5` (`master`).

The [core principles](https://github.com/nvk/llm-wiki/blob/1224fbcdf3827f4ba56d225a9e359f5e8a5594e5/AGENTS.md) say: “Articles are synthesized, not copied” and “Think textbook, not clipboard.” Raw sources and synthesized wiki articles have distinct roles.

The [compilation guide](https://github.com/nvk/llm-wiki/blob/1224fbcdf3827f4ba56d225a9e359f5e8a5594e5/claude-plugin/skills/wiki-manager/references/compilation.md) starts articles with an abstract explaining what the subject is and why it matters. Its quality rules require articles to be readable without consulting raw sources, accurate without excessive simplification, direct in language and honest about disagreement. The same guide requires machine-usable `sources:` for raw-derived articles and describes structural lint checks.

Assessment: the closest direct model for readable prose. Retain our own relative Markdown links rather than importing its dual wikilink/Markdown syntax. Structural lint is not evidence that prose is understandable or citations prove claims.

## Transfer to our existing skill

Our skill already covers inline evidence, drafts, stale facts, disagreements, source identity, revision history and stable relative links. The missing addition is a concise authoring-quality contract, not another metadata or formatting system.

Suggested English wording, **proposed only**:

> Write authored wiki pages, including source summaries and reading views, for both people and agents.
>
> - Make each page understandable without the original conversation. Start substantive pages with a brief introduction that states their subject, scope and relevant caveats.
> - Use descriptive headings, short paragraphs and lists or tables where they improve scanning. Include only sections with meaningful content; do not fill templates with invented facts or boilerplate.
> - Distinguish source statements, observed results, interpretation, limitations and open questions. Keep material evidence and qualifications beside the claims they support.
> - Preserve factual meaning, numbers, units, ranges, technical names and identifiers. Readability must not weaken precision or hide uncertainty.
> - Follow the wiki's configured prose language while preserving technical identifiers, source quotations and machine-readable structure. The skill's instruction language does not determine the wiki's content language.
> - Keep original assets and verbatim captures unchanged. Clearly label derived summaries, translations and reading views and link them to their evidence; revise maintained views through the existing history safeguards.

Add the contract to `SKILL.md`, refer to it from Compile and Verify, and mirror its essentials in `DEFAULT_SCHEMA` for new bundles. Do not overwrite existing owner schemas. No new formatter, confidence formula, mandatory empty sections, minimum link count or retrieval metadata is needed for this request.

## Limitations and next action

The repository findings combine a delegated primary-source inspection with parent verification of the key quotations, output-language helper, writing profile, canonical paths and commit identities. Not every command, prompt, lint implementation or runtime workflow was inspected. No assertion is made about the absence of additional language/style rules elsewhere.

Original captures and authored source-reading views must not be conflated merely because both may live under a folder named `sources/`. Our append-only capture contract must remain intact when adding prose guidance.

Research supports the proposed small English-language addition. Owner approval of the wording and scope is still needed before implementation; this note does not authorize changing the skill or synchronizing installed copies.
