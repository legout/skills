# Semantic fidelity, not merely attractive Markdown

A faithful transcription preserves source content and its relationships. It is
not a summary, a corrected invoice, or a normalized dataset. Added navigation or
explanations belong in clearly marked editorial notes, separate from source text.

## Inspect before and after conversion

Determine page identities and materially different layouts before choosing tools.
For each page, account for meaningful text, tables, selections and image regions.
Blank form entries and static placeholders must not become invented user answers.
On difficult pages, compare crops at a resolution where characters and marks are
actually visible. A cropped edge may hide text; recheck the full page before
asserting an omitted or additional character.

Check table *associations*, not just presence. Verify headers, row counts, empty
cells, multiline cells and totals. An organization printed under Department stays
under Department, even if Company seems more plausible. Preserve source wording
and original numbering; Markdown can introduce clearly editorial region headings.

Checked, unchecked and unreadable selections are different states. A label without
a mark provides no selection evidence. If the source has two empty expense boxes
and a filled amount, reproduce that arrangement; do not tick a box to explain it.

## Escalation examples

- High-confidence OCR interleaves two receipts: named ordering failure; use a
  structural parser or independent-region crops, not another whole-page text dump.
- A candidate has a valid table but values shift columns: recheck source cells;
  a structurally valid export is not semantically accepted.
- A printed attendee table is good but checkbox marks are missing: preserve the
  good table, use vision on the selection region, then check the marks yourself.
- A vision candidate adds a plausible fiscal line: compare the source crop;
  remove unsupported generated content and retain raw candidate/provenance.
- Two source pages show different totals: preserve both. Arithmetic can expose a
  reason to inspect, not establish which source value should be rewritten.

## Vision does not eliminate review

Give the model the original image, not only OCR text. If correcting a candidate,
explicitly treat it as untrusted extraction evidence and require every correction
to be grounded in the image. An independent second reading can reduce anchoring;
model agreement still cannot certify a factual value.

Retain image evidence for uncertain names, signatures, tiny identifiers and long
technical strings. `[illegible]` or `[uncertain: …]` is preferable to an inferred
name copied from another page. Do not translate, expand abbreviations, change
decimal separators or fix source typos unless the user separately requests a
normalized derivative. Keep that derivative distinct from faithful transcription.

## Final artifact

Keep candidate Markdown/JSON and a source/settings manifest. The reviewed final
Markdown needs stable page/region references and working image links. Bare paths
inside code spans are not embeds. Use actual Markdown image syntax:

```markdown
![Signature](<images/signature crop.png>)
```

Cryptographic signatures and QR codes may remain as images; do not imply exact
character recovery or decoding from an ordinary visual reading.

The bundled structural checker finds broken local image links, missing canonical
page markers and ragged GFM table rows. It cannot detect wrong values, displaced
but well-shaped cells, hallucinations, or an incorrect checkbox state. Report
`requires_source_review` until the agent has compared the relevant source regions.
After checking, state the actual scope and remaining uncertainty; never promote
self-review to independent human verification.
