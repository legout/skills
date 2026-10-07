# Local structural PDF parsers

Use these for tables, forms, columns and receipts. Do not install/run both merely
to satisfy a ladder. Choose by the named semantic need, available tools and user
resource/privacy constraints; inspect the candidate before escalating.

The bundled converters process the supplied PDF. For selective page routing, use
an extracted page/range PDF (the existing pdf skill can create it) or the engine's
supported page-range API. Record its mapping back to the original PDF hash and
page numbers. Helper markers refer to the supplied PDF: page 1 of an extracted
subset must not become page 1 of the original final document. For targeted visual
regions, retain the original page identity and crop box when assembling the result.

## Docling: default for printed structure

```sh
uv run <skill-dir>/scripts/convert_docling.py input.pdf candidate-docling
```

The bundled helper pins the tested Docling/RapidOCR/ONNX versions, uses full-page
German-capable OCR by default, accurate table recognition and CPU inference.
`--language iso:en` selects another supported recognition language; `--native-text`
retains the hybrid native-text path instead of forcing OCR on digital pages.

It writes raw Markdown, per-page exports, `document-paged.md`, structured JSON,
referenced picture assets and `run.json`. Page markers are provenance aids, not
proof that Docling did not merge/reorder content across a page boundary. Verify
attendee cells, receipt value associations and checkbox state against the source.

Docling supports Windows/macOS/Linux. The default RapidOCR/ONNX backend is portable;
Apple Vision is a separate macOS-only OCR option, not a Windows fallback. A GPU is
optional; the helper defaults to CPU. PyTorch/layout/table models make the complete
pipeline substantially heavier than standalone RapidOCR. First use downloads
weights; separate download/startup time from document inference when comparing.

## MinerU: Basic versus Standard

```sh
uv run <skill-dir>/scripts/convert_mineru.py input.pdf candidate-mineru --tier standard
uv run <skill-dir>/scripts/convert_mineru.py input.pdf candidate-basic --tier basic
```

The helper pins MinerU 4.0.10 and uses its local SDK with an explicit empty remote
URL; it does not start a document-library service or use hosted conversion.
Standard/Advanced select local llama.cpp and small models. Basic uses the small
layout/OCR/table models without a VLM. Advanced uses the Standard model set with
more inference computation; it is not a different download or an automatic retry.

Outputs include `markdown.md`, materialized JSON, available image/model assets,
`document-paged.md`, per-page exports and `run.json`. Page exports are rendered
from saved materialized JSON so images stay local files rather than base64 payloads.

Basic can preserve printed tables and blank cells but may flatten receipt items,
lose selection marks and misread handwriting. Standard can improve receipts but
can omit VAT rows or introduce unsupported text. Neither result is exempt from
the semantic acceptance gate. Do not claim a universal tool ranking from one sample.

Windows base deployments use ONNX small models and llama.cpp; Apple Silicon also
installs Torch and can accelerate small models with MPS. Start with Python 3.12
for new Windows environments; optional accelerator packages have separate wheel
and driver constraints. A CPU-only Windows run may differ from a Mac MPS run.
For Standard/Advanced plan roughly 16 GB RAM or more, according to workload and
concurrency; no GPU/VRAM minimum guarantees every document fits. Basic is an option
when resources are constrained, not a promise of equal quality or exact peak RAM.
Selecting Basic does not uninstall existing dependencies or cached VLM weights.

## Downloads and verification

Packages and public weights may be downloaded; document content stays local.
Helpers use `truststore` so HTTPS verification can honor the OS trust store, e.g.
corporate CAs on Windows/macOS. They never disable certificate verification.
If downloads or local inference cannot run, report the blocker; never substitute a
public remote endpoint. Consult installed `--help` and upstream model licensing
before deploying a different version/backend or broad commercial use.

Sources: [Docling](https://github.com/docling-project/docling),
[MinerU tiers/runtimes](https://opendatalab.github.io/MinerU/usage/tiers/),
[MinerU installation](https://opendatalab.github.io/MinerU/quick_start/).
