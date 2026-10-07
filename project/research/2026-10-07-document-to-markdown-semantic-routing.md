# Document-to-Markdown semantic routing update

## Approved scope

The owner approved the bounded in-chat design with “Implement this. Update the
skill accordingly.” The implementation source is that approved design, not an
assumed universal ranking of PDF parsers. Scope: semantic-fidelity-first routing,
local structural helpers, targeted approved vision, provenance, and synthetic
checks. Existing Office and legacy OCR/internal-HTTP invocations remain supported.
No installed-copy update, commit, publication or release is authorized here.

Planning contract: version 1; installed provenance: unknown. No new domain glossary
is needed; semantic fidelity is the acceptance requirement described in the skill.
No ADR is warranted for these reversible routing defaults. The earlier owner
approval resolves the material behavior/privacy choices for this bounded update.

## Synthetic evidence

The test fixture contains invented attendee names/organizations, a blank company
cell, selected/unselected boxes, different printed totals, and two independent
receipt regions. No private source document, attendance data or original signature
was added to the catalog. `tests/document_to_markdown_test.py --make-fixture PATH`
recreates native and scanned versions locally.

The new Docling and MinerU Basic/Standard helpers produced two-page artifacts with
source hashes, per-page markers, JSON and local image references. Structural checks
passed, while visual inspection still found semantic limitations: Docling recognized
selection states but flattened the synthetic table/receipt associations; Basic
preserved attendee cells but lost selection marks and receipt details. A structural
pass therefore deliberately retains `semantic_verification: requires_source_review`.
These are smoke checks of the helpers, not proof that all source facts are correct.

Fresh read-only old/new-skill agents answered three routing scenarios. The old
policy selected internal vision directly for the printed scanned form; the new
policy selected Docling first and targeted unresolved regions for vision. Both
rejected the explicitly defective candidate and retained the lightweight native
route for clean digital text. No generalized accuracy improvement is inferred from
these small routing-only evaluations. Outputs/review artifacts remain in the local
temporary evaluation workspace, not the distributed skill.

## Verification and remaining limits

Focused checks exercise missing image assets, page coverage, ragged tables, blank
table cells, image paths with spaces, source rendering/cropping and overwrite
refusal. A deliberately swapped but well-shaped table confirms that the structural
checker cannot certify semantics. Catalog link/frontmatter checks and orchestrator
handoff tests cover existing repository contracts. New helpers were exercised on
macOS; Windows portability is documented, not execution-tested. The internal HTTP
vision prompt was strengthened without sending an API transcription request.

The owner-approved simplification pass retained the helper structure and safety
checks. It replaced only the manual streaming hash loop with Python's
`hashlib.file_digest`; an independently calculated expected SHA-256 pins the
source-manifest behavior before and after that change.

Model-download/cache state makes observed runtimes unsuitable for a controlled
performance comparison. Upstream provenance files are unchanged; the optional
network-dependent full upstream check timed out in this environment.
