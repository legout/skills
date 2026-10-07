# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "pillow>=12.3.0",
# ]
# ///


"""Save a lossless PNG crop; coordinates are left/top/right/bottom source pixels."""

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--box",
        nargs=4,
        type=int,
        required=True,
        metavar=("LEFT", "TOP", "RIGHT", "BOTTOM"),
    )
    args = parser.parse_args()
    if not args.image.is_file():
        parser.error("image must be an existing local file")
    if args.output.suffix.lower() != ".png":
        parser.error("output must be a .png file")
    if args.output.exists():
        parser.error("output already exists; choose a new path")

    from PIL import Image

    with Image.open(args.image) as image:
        left, top, right, bottom = args.box
        if not (0 <= left < right <= image.width and 0 <= top < bottom <= image.height):
            parser.error(
                f"box must be inside the {image.width} x {image.height} source"
            )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with image.crop((left, top, right, bottom)) as crop:
            crop.save(args.output, format="PNG")
        print(f"Saved source crop {args.box} -> {args.output}")


if __name__ == "__main__":
    main()
