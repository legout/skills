# Changelog

Notable changes to the skills catalog are recorded here. Versions apply to the
whole catalog, not individual skills. A version is published only when its
matching Git tag exists.

## Unreleased

- Moved `document-to-markdown` and `second-brain` into the `tools-and-research` category; skill names and invocations are unchanged.
- Moved default planning-artifact paths from `docs/` to the `project/` namespace (`project/research|adr|specs|plans|tickets/`, `project/agents/`), separating delivery artifacts from product documentation; legacy `docs/` installations are grandfathered and never auto-migrated. `planning-contract` records the namespace rule; consumers reference both.
- Standardized specification and plan filenames as `YYYY-MM-DD-NNNN-slug.md`, with shared work-item numbering for linked artifacts.
- Added catalog-wide semantic versioning, with `0.1.0` prepared as the first version.
- Added support for `VERSION`-based catalogs and first releases in `make-release`.
- Included the existing 34-skill catalog as the initial baseline, including planning, implementation, verification, and review guardrails.
- Added human- and agent-friendly writing rules to `second-brain` and its new-vault schema, preserving source fidelity, capture hashes and each wiki's configured language.
- Made ordinary `second-brain` persistence require maintained-page compilation or a justified deferral, preserving explicit capture-only and read-only scopes. Split advanced workflows, capture/history safeguards and retrieval maintenance into directly linked references; new-vault schemas and project hooks carry the same contract. CLI commands and existing owner schemas are unchanged.
- Standardized `second-brain` script comments, docstrings, CLI help/output and new-bundle guidance in English without changing existing owner schemas, captured content or configured wiki languages.
- Changed new `second-brain` notes created by `add` and `idea` to `notes/YYYY-MM-DD/slug.md`, with numbered same-day collisions. Legacy flat notes stay in place and remain valid search, link and supersession targets; source captures and maintained-page layouts are unchanged. Callers that glob only flat note filenames must adapt to the daily layout.
