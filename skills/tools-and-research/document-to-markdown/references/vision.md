# Final vision escalation

Use original source images/crops for unresolved semantic failures. Do not send the
whole document through every model. An obviously hard handwriting region can skip
an unsuitable OCR pass. Vision output is another candidate requiring source checks.

## Native-agent vision

When the current session's provider is authorized to process the document and the
model actually accepts images, inspect rendered pages with the host's image-reading
tool. Transcribe from those images; do not claim native vision when the host only
supplied OCR text. If unavailable or privacy authorization is unclear, stop/ask or
use the configured approved internal endpoint. Do not invoke a public model merely
because it offers vision. Subagents need explicit user or workflow authorization;
discover exact available model IDs rather than hardcoding provider-specific IDs.

For independent comparisons, give a second authorized vision reader only the
source images/crops, not prior transcripts. Distinguish its first output from any
later correction. Do not run a second model routinely or treat agreement as truth.

## Existing internal HTTP helper

```sh
uv run <skill-dir>/scripts/vlm_page.py page.png page-candidate.md
```

Uses `OPENAI_BASE_URL`, `OPENAI_API_KEY`, and optional `DOC2MD_VLM_MODEL` (default
`gpt-5.6-luna`; `qwen-3.8-27b` is an internal alternative when image-capable and
available). The endpoint must be HTTPS under `siemens.com`; the helper rejects
other hosts. This allowlist does not automatically cover other internal domains.
Do not widen it implicitly; use an already authorized native session or request
the required policy/configuration decision. No credentials go into artifacts.

## Resolution and instructions

Start with readable page renders around 150–200 DPI. Use 300-DPI renders and tight
source crops for small print, handwriting and selection marks when needed. Higher
resolution can increase token/cost usage; do not assert that it always helps or
always wastes tokens. Recheck crop edges against the complete source page.

Require literal transcription, page/region identity, table rows/columns including
empty cells, checked/unchecked/unreadable states, and separate reading order for
independent columns. Do not summarize, translate, silently correct source spelling,
normalize identifiers, reconcile amounts, or invent missing fields. Mark doubtful
readings beside their content; retain original image evidence for signatures,
QR codes and cryptographic strings rather than claim exact recovery.

The existing helper produces one page candidate. Assemble multi-page/region outputs
with explicit source-page markers; preserve raw model output separately from the
reviewed final Markdown. Add local image embeds yourself when required—the HTTP
model cannot create trustworthy local files or know their paths. Verify assets and
compare critical values/relationships back to the source before acceptance.

Record actual model/provider, source hash/page/crop, and session-based versus API
inference in the final sidecar. Neither an HTTP success nor a model's own assurance
establishes a verified transcription. If the final vision result remains uncertain,
deliver that uncertainty with evidence and stop; do not loop indefinitely.
