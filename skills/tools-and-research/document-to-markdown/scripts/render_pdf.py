# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "pillow>=12.3.0",
#     "pypdfium2>=5.14.0",
# ]
# ///


"""Render source pages locally for visual inspection, without OCR or model calls."""

import argparse
import json
from pathlib import Path

from artifact_utils import prepare_output, require_pdf, source_hash


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--dpi", type=int, default=150)
    args = parser.parse_args()
    source = require_pdf(parser, args.pdf)
    if args.dpi <= 0:
        parser.error("dpi must be positive")
    output = prepare_output(args.output_dir)

    import pypdfium2 as pdfium

    with pdfium.PdfDocument(source) as pdf:
        count = len(pdf)
        for index in range(count):
            page = pdf[index]
            bitmap = page.render(scale=args.dpi / 72)
            image = bitmap.to_pil()
            image.save(output / f"page-{index + 1:03d}.png")
            image.close()
            bitmap.close()
            page.close()
    metadata = {
        "source": str(source),
        "source_sha256": source_hash(source),
        "page_count": count,
        "dpi": args.dpi,
    }
    (output / "source.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Rendered {count} source pages at {args.dpi} DPI -> {output}")


if __name__ == "__main__":
    main()
