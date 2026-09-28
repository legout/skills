# Tier 1 — OCR a scanned PDF to Markdown with RapidOCR (local, CPU).
# Run: uv run scripts/ocr_pdf.py input.pdf output.md [lang]
# lang: en (default), ch, german, french, ... https://rapidai.github.io/RapidOCRDocs/main/model_list/
# /// script
# requires-python = ">=3.10"
# dependencies = ["rapidocr", "onnxruntime", "pymupdf"]
# ///
import sys
import tempfile
from pathlib import Path

import pymupdf  # type: ignore[import]
from rapidocr import RapidOCR  # type: ignore[import]


def main() -> None:
    if len(sys.argv) < 3:
        sys.exit("usage: ocr_pdf.py input.pdf output.md [lang]")
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    if src.resolve() == dst.resolve():
        sys.exit("ocr_pdf: input and output must be different files")
    lang = sys.argv[3] if len(sys.argv) > 3 else "en"
    tmp_out = None
    try:
        engine = RapidOCR(params={"Rec.lang_type": lang})
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=dst.parent,
                                         prefix=f".{dst.name}.", delete=False) as out:
            tmp_out = Path(out.name)
            with tempfile.TemporaryDirectory() as tmp, pymupdf.open(src) as doc:
                pages = len(doc)
                for i, page in enumerate(doc):
                    png = Path(tmp) / f"p{i}.png"
                    page.get_pixmap(dpi=300).save(str(png))
                    res = engine(str(png))
                    out.write(f"\n\n<!-- page {i + 1} -->\n")
                    if res.txts:
                        lines = sorted(
                            (
                                (min(p[1] for p in box), min(p[0] for p in box), txt, conf)
                                for box, txt, conf in zip(res.boxes, res.txts, res.scores, strict=True)
                            ),
                            key=lambda item: (item[0], item[1]),
                        )
                        for _, _, txt, conf in lines:
                            mark = "" if conf >= 0.85 else f" *(conf {conf:.2f})*"
                            out.write(txt + mark + "\n")
                    mean = sum(res.scores) / len(res.scores) if res.scores else 0.0
                    if not res.txts or mean < 0.75:
                        out.write(f"\n<!-- LOW-QUALITY PAGE {i + 1} (mean conf {mean:.2f}) -> rerun via VLM tier -->\n")
        tmp_out.replace(dst)
        print(f"{pages} pages -> {dst}")
    except Exception as exc:  # CLI-Grenze: klare Meldung statt Traceback
        if tmp_out:
            tmp_out.unlink(missing_ok=True)
        sys.exit(f"ocr_pdf: {exc}")


if __name__ == "__main__":
    main()
