# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "mineru==4.0.10",
#     "truststore>=0.10.4",
# ]
# ///


"""Local MinerU candidate; explicit local VLM only for Standard/Advanced."""

import argparse
import time
from pathlib import Path

from artifact_utils import prepare_output, require_pdf, write_paged, write_run


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument(
        "--tier", choices=("basic", "standard", "advanced"), default="standard"
    )
    args = parser.parse_args()
    source = require_pdf(parser, args.pdf)
    output = prepare_output(args.output_dir)

    import truststore

    truststore.inject_into_ssl()

    from mineru.config import VlmConfig
    from mineru.parser import ParseResult, parse
    from mineru.parser.writer import FileBasedDataWriter

    # Explicitly override persisted remote endpoint settings, even for Basic.
    vlm = VlmConfig(engine="llama-cpp", server_url="", max_concurrency=1)
    start = time.perf_counter()
    result = parse(source, tier=args.tier, ocr_mode="ocr", vlm_config=vlm)
    elapsed = time.perf_counter() - start
    result.save(FileBasedDataWriter(str(output)))
    saved = ParseResult.from_json(
        (output / "middle_json.json").read_text(encoding="utf-8")
    )
    pages = []
    for page in saved.pages:
        one_page = saved.middle_json.model_copy(update={"pages": [page]})
        markdown = ParseResult(middle_json=one_page).markdown(add_markers=True)
        pages.append((page.page_idx + 1, markdown))
    write_paged(output, pages)
    write_run(
        output,
        source,
        "mineru",
        len(saved.pages),
        elapsed,
        {
            "tier": args.tier,
            "ocr_mode": "ocr",
            "vlm_enabled": args.tier != "basic",
            "vlm_engine": vlm.engine if args.tier != "basic" else None,
        },
        ("mineru",),
    )
    print(
        f"MinerU {args.tier} candidate: {len(saved.pages)} pages, {elapsed:.1f}s -> {output}"
    )


if __name__ == "__main__":
    main()
