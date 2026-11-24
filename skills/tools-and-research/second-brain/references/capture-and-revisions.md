# Source capture and revision safeguards

## Read and preserve evidence

The CLI neither fetches URLs nor extracts PDF/Office text: read the original with the right tool first. Keep handwritten `personal/` files unchanged and read them only on request. Never store secrets in text, archived originals or metadata. A generated summary is not the original source.

```bash
uv run <skill-dir>/scripts/sb.py --vault knowledge capture "Existing document" \
  --source file:///path/to/project/document.pdf --body-file /path/to/excerpt.md --scope excerpt
```

`file://` sources are hashed and linked, never copied. A path and hash identify the observed version; they do not freeze or recover the bytes. When historical local versions matter, rely on the owner's backup or version control, not an archive duplicate.

## Archive newly acquired originals

`_raw/` is only for an attachment received in this workflow or a download that has no reliable project location. Acquisition comes from the task context, not a path guess. Already preserved bytes are reused, not copied per capture.

```bash
uv run <skill-dir>/scripts/sb.py --vault knowledge capture "Downloaded paper" \
  --source https://example.org/paper.pdf --body-file /path/to/excerpt.md \
  --original /path/to/downloaded.pdf --archive-original --scope excerpt
```

Leave legacy `raw/` assets where they are. Both archives are excluded from indexing.

## Identity and honest scope

- A repeated `capture` with the same source URI, text, scope, original bytes and `origin_projects` returns the existing capture; with `--archive-original`, only if that capture already references a verified preserved original. Any change creates a linked new snapshot; older captures stay unchanged.
- Let `capture` compute `content_sha256` (the supplied UTF-8 text, not the rendered file) and `original_sha256` (known original bytes, empty otherwise). `original_uri` is the location, `preserved_original` the archived copy. None of these prove authenticity, completeness or present availability; `lint` does not check them.
- Do not add the historical fields `original_capture_sha256` or `captured_content_sha256` to new files, and do not remove them from existing ones.
- `excerpt` is the default; use `full` only for complete text. Older unlabeled captures have unknown scope. For an unread URL, write a labeled draft pointer with `add`, never an empty capture.
- Legacy `type: source` captures may carry an old `status`; indexing ignores it, leave them unchanged.
- `sources/` records what one source says; maintained `references/` hold the current source-grounded lookup. Compare supporting, narrowing and contradicting material before compiling, and keep provenance beside each material claim.

## Revise the right surface

- **Atomic history:** `add --supersedes <bundle-relative-path>`; the old claim stays readable as `deprecated`. Compiling a note elsewhere is no reason to deprecate it.
- **Maintained page:** mismatched `--expect-sha256` aborts; previous bytes go to `.history/` and the reason to the log. Owner metadata (`aliases`, `stale_after`, summaries, custom fields) is kept; CLI-owned type/status/generation/source fields are replaced and prior verification is removed.
- **Source capture:** never revised. Supersession and revision reject captures, and all mutations reject `personal/`, `_raw/`, `raw/` and `.history/` targets. `verify` may still record review on a capture.

Use standard relative Markdown links, not `[[wikilinks]]`. A title change must not create a replacement page or break links.

## Status and verification

Uncertain or contested content stays `draft`; promotion to `stable` is an explicit choice. Run `verify <path> --by human:<id>` only after a real human review; it adds `verified` and never changes `status`. Date time-sensitive observations and review them before reuse.
