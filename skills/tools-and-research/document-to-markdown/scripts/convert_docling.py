# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "docling==2.134.0",
#     "onnxruntime==1.30.0",
#     "rapidocr==3.9.2",
#     "truststore>=0.10.4",
# ]
# ///


"""Local Docling candidate with OCR/layout/tables and referenced source assets."""

import argparse
import time
from pathlib import Path

from artifact_utils import prepare_output, require_pdf, write_paged, write_run


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--language", default="iso:de", help="RapidOCR language/tag")
    parser.add_argument(
        "--native-text",
        action="store_true",
        help="Hybrid native text/OCR instead of full-page OCR",
    )
    parser.add_argument("--device", choices=("cpu", "mps", "auto"), default="cpu")
    args = parser.parse_args()
    source = require_pdf(parser, args.pdf)
    output = prepare_output(args.output_dir)

    import truststore

    truststore.inject_into_ssl()

    from docling.datamodel.accelerator_options import AcceleratorOptions
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import (
        OcrMode,
        PdfPipelineOptions,
        RapidOcrOptions,
        TableStructureOptions,
    )
    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling_core.types.doc import ImageRefMode

    options = PdfPipelineOptions(
        do_ocr=True,
        do_table_structure=True,
        ocr_options=RapidOcrOptions(
            mode=OcrMode.DEFAULT if args.native_text else OcrMode.FULL_PAGE,
            lang=[args.language],
            scale=300 / 72,
        ),
        table_structure_options=TableStructureOptions(do_cell_matching=True),
        accelerator_options=AcceleratorOptions(device=args.device),
        generate_picture_images=True,
        images_scale=2,
        enable_remote_services=False,
    )
    start = time.perf_counter()
    converter = DocumentConverter(
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=options)}
    )
    result = converter.convert(source)
    elapsed = time.perf_counter() - start
    if result.status.value != "success":
        raise SystemExit(f"Incomplete conversion: {result.status}; {result.errors}")
    doc = result.document
    assets = output / "images"
    doc.save_as_markdown(
        output / "document.md", artifacts_dir=assets, image_mode=ImageRefMode.REFERENCED
    )
    doc.save_as_json(
        output / "document.json",
        artifacts_dir=assets,
        image_mode=ImageRefMode.REFERENCED,
    )
    pages = []
    for page_no in sorted(doc.pages):
        path = output / f"page-{page_no:03d}.md"
        doc.save_as_markdown(
            path,
            artifacts_dir=assets,
            image_mode=ImageRefMode.REFERENCED,
            page_no=page_no,
        )
        pages.append((page_no, path.read_text(encoding="utf-8")))
    write_paged(output, pages)
    write_run(
        output,
        source,
        "docling",
        len(doc.pages),
        elapsed,
        options.model_dump(mode="json"),
        ("docling", "docling-core", "rapidocr", "onnxruntime"),
    )
    print(f"Docling candidate: {len(doc.pages)} pages, {elapsed:.1f}s -> {output}")


if __name__ == "__main__":
    main()
