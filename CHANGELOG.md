# Changelog

Notable changes to the skills catalog are recorded here. Versions apply to the
whole catalog, not individual skills. A version is published only when its
matching Git tag exists.

## Unreleased

- Moved default planning-artifact paths from `docs/` to the `project/` namespace (`project/research|adr|specs|plans|tickets/`, `project/agents/`), separating delivery artifacts from product documentation; legacy `docs/` installations are grandfathered and never auto-migrated. `planning-contract` records the namespace rule; consumers reference both.
- Standardized specification and plan filenames as `YYYY-MM-DD-NNNN-slug.md`, with shared work-item numbering for linked artifacts.
- Added catalog-wide semantic versioning, with `0.1.0` prepared as the first version.
- Added support for `VERSION`-based catalogs and first releases in `make-release`.
- Included the existing 34-skill catalog as the initial baseline, including planning, implementation, verification, and review guardrails.
