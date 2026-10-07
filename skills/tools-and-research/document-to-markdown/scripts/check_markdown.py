# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Check structural artifacts only; semantic fidelity requires original-source review."""

import argparse
import json
import re
from pathlib import Path
from urllib.parse import unquote, urlparse


def inspect(path, expected_pages=None):
    text = path.read_text(encoding="utf-8")
    # Code examples/technical strings are not Markdown image or table syntax.
    prose = re.sub(r"(?ms)^```[^\n]*\n.*?^```\s*$", "", text)
    errors = []
    if not text.strip():
        errors.append("empty Markdown candidate")
    pages = [int(n) for n in re.findall(r"<!--\s*source page (\d+)\s*-->", text)]
    if expected_pages is not None and sorted(pages) != list(
        range(1, expected_pages + 1)
    ):
        errors.append(f"page coverage: expected 1..{expected_pages}, found {pages}")
    images = re.findall(r"!\[[^\]]*\]\(\s*(?:<([^>]+)>|([^\s)]+))[^)]*\)", prose)
    local_images = 0
    for angle, plain in images:
        target = angle or plain
        parsed = urlparse(target)
        if parsed.scheme:
            continue
        local_images += 1
        destination = path.parent / unquote(parsed.path)
        if not destination.is_file():
            errors.append(f"missing local image: {target}")
    width = None
    tables = 0
    for line in prose.splitlines():
        if not line.strip().startswith("|"):
            width = None
            continue
        cells = re.split(r"(?<!\\)\|", line.strip())[1:]
        if cells[-1] == "":
            cells = cells[:-1]
        if width is None:
            width = len(cells)
            tables += 1
        elif len(cells) != width:
            errors.append(
                f"table column count: expected {width}, found {len(cells)} in {line}"
            )
    return {
        "structural_checks_passed": not errors,
        "semantic_verification": "requires_source_review",
        "source_page_markers": pages,
        "local_images": local_images,
        "gfm_table_blocks": tables,
        "checkboxes": {
            "selected": len(re.findall(r"(?m)^\s*- \[[xX]\]", prose))
            + prose.count("☒"),
            "unselected": len(re.findall(r"(?m)^\s*- \[ \]", prose)) + prose.count("☐"),
        },
        "warnings": ["unresolved image placeholder"]
        if "<!-- image -->" in text
        else [],
        "errors": errors,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("markdown", type=Path)
    parser.add_argument("--expected-pages", type=int)
    args = parser.parse_args()
    if not args.markdown.is_file():
        parser.error("markdown must be an existing local file")
    if args.expected_pages is not None and args.expected_pages <= 0:
        parser.error("expected-pages must be positive")
    report = inspect(args.markdown, args.expected_pages)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if report["structural_checks_passed"] else 1)


if __name__ == "__main__":
    main()
