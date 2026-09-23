# anydoc — Office and text-PDF leg

Rust binary (via `@firecrawl/anydoc` on npm). Pure local parsing, no ML models, median < 5 ms per document. Every format renders through one GitHub-Flavored Markdown serializer, so escaping, tables, heading anchors, and footnotes behave identically for a `.doc` from 2003 or a `.pptx` from yesterday.

## CLI

```bash
npx -y @firecrawl/anydoc report.docx               # Markdown to stdout
npx -y @firecrawl/anydoc report.docx -o report.md  # write to file
npx -y @firecrawl/anydoc - --format csv < data.csv # stdin
npm install -g @firecrawl/anydoc                   # permanent `anydoc` command
```

## Exit codes

| Code | Meaning | Router action |
| --- | --- | --- |
| 0 | converted | done |
| 1 | could not convert | try markitdown (fallbacks.md), then report failure |
| 2 | usage error | fix invocation |
| 3 | PDF pages need OCR | RapidOCR leg ([ocr.md](ocr.md)) |

Failures print one `anydoc: <message>` line to stderr. The CLI never prompts.

## Supported formats

| Family | Extensions |
| --- | --- |
| Word | `.doc` `.docx` `.docm` |
| PowerPoint | `.ppt` `.pps` `.pot` `.pptx` `.pptm` `.ppsx` `.ppsm` |
| Excel | `.xls` `.xlsx` `.xlsm` `.xlsb` |
| OpenDocument | `.odt` `.ods` `.odp` |
| Other | `.rtf` `.epub` `.csv` `.pdf` (text-based) |

Notes:
- Format is detected from file **content**, not extension — mislabeled files still convert correctly.
- Structure preserved: headings with anchors, bold/italic/strikethrough, code blocks, links, nested/task lists with the source's own numbering, tables with merged cells, blockquotes, footnotes/endnotes, speaker notes (PPTX).
- Equations convert to LaTeX (`$...$` / `$$...$$`).
- Embedded images render as alt text; raw bytes stay available via the library API (`toDocument`).
- Legacy `.xls/.xlsx` values are rendered as stored (raw values, not the formatted display string).

## Library bindings (inside code, prefer over shelling out)

- Node: `import { toMarkdown } from '@firecrawl/anydoc'`
- Python: `import anydoc; anydoc.to_markdown("report.docx")`
- Rust: `cargo add anydoc`

Never use the hosted OCR option (`--ocr hosted` / `ocr: 'hosted'`) — it uploads the document. This skill's OCR leg is local RapidOCR instead.
