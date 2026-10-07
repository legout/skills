# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "pillow>=12.3.0",
#     "pypdfium2>=5.14.0",
#     "pyyaml>=6.0.3",
#     "reportlab>=4.4",
# ]
# ///
"""Focused artifact checks and synthetic PDF/image preparation; no private fixtures."""

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills/tools-and-research/document-to-markdown/scripts"


def run_script(name, *args):
    return subprocess.run(
        ["uv", "run", "--script", str(SCRIPTS / name), *map(str, args)],
        capture_output=True,
        text=True,
        check=False,
    )


def make_fixture(destination):
    """Synthetic two-page scan: blank table cells, selections and two receipt regions."""
    from PIL import Image
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfgen import canvas

    destination = Path(destination)
    if destination.exists():
        raise SystemExit("Fixture already exists; choose a fresh path")
    destination.parent.mkdir(parents=True, exist_ok=True)
    digital = destination.with_name("synthetic-native.pdf")
    writer = canvas.Canvas(str(digital), pagesize=(595, 842))
    writer.setFont("Helvetica-Bold", 20)
    writer.drawString(50, 790, "Synthetic expense form")
    writer.setFont("Helvetica", 12)
    writer.drawString(50, 755, "Date: 05.10.2026")
    rows = [
        ("Name", "Company", "Department"),
        ("Ada Example", "Example Ltd", "Research"),
        ("Bert Sample", "", "Sample University"),
    ]
    for index, row in enumerate(rows):
        y = 695 - index * 35
        for x, value in zip((55, 230, 400), row, strict=True):
            writer.drawString(x, y, value)
    for y in (720, 685, 650, 615):
        writer.line(50, y, 550, y)
    for x in (50, 220, 390, 550):
        writer.line(x, 615, x, 720)
    for x, label, selected in (
        (50, "Lunch", True),
        (220, "Dinner", False),
        (390, "External", True),
    ):
        writer.rect(x, 540, 15, 15)
        writer.drawString(x + 23, 542, label)
        if selected:
            writer.line(x, 540, x + 15, 555)
            writer.line(x, 555, x + 15, 540)
    writer.drawString(50, 495, "Printed total: 12,00 EUR")
    writer.drawString(50, 455, "Purpose: [blank field]")
    writer.showPage()
    for x, heading in ((50, "Left receipt"), (325, "Right receipt")):
        writer.setFont("Helvetica-Bold", 16)
        writer.drawString(x, 780, heading)
        writer.setFont("Helvetica", 12)
        writer.drawString(x, 735, "Date: 05.10.2026")
    for index, (left, right) in enumerate(
        [
            ("Expense type: External", "Meal                  9,00"),
            ("Purpose: Example workshop", "Water                 3,01"),
            ("Location: ABC", "Net total            12,01"),
            ("Guests: 2", "Gross total          13,21"),
        ]
    ):
        y = 690 - index * 35
        writer.drawString(50, y, left)
        writer.drawString(325, y, right)
    writer.line(295, 300, 295, 800)
    writer.drawString(325, 495, "VAT %   Net    Gross    VAT")
    writer.drawString(325, 465, "10.00   12,01  13,21    1,20")
    writer.setFont("Helvetica-Oblique", 14)
    writer.drawString(50, 455, "Nora Demo")
    writer.save()
    rendered = run_script(
        "render_pdf.py",
        digital,
        "--output-dir",
        destination.parent / "fixture-pages",
        "--dpi",
        150,
    )
    if rendered.returncode:
        raise RuntimeError(rendered.stderr)
    scanned = canvas.Canvas(str(destination), pagesize=(595, 842))
    for number in (1, 2):
        with Image.open(
            destination.parent / "fixture-pages" / f"page-{number:03d}.png"
        ) as image:
            scanned.drawImage(ImageReader(image), 0, 0, width=595, height=842)
        scanned.showPage()
    scanned.save()
    print(destination)


class ArtifactChecks(unittest.TestCase):
    def test_skill_frontmatter_is_valid_yaml(self):
        import yaml

        text = (SCRIPTS.parent / "SKILL.md").read_text(encoding="utf-8")
        metadata = yaml.safe_load(text.split("---", 2)[1])
        self.assertEqual(metadata["name"], "document-to-markdown")
        self.assertIsInstance(metadata["description"], str)
        self.assertTrue(metadata["description"].strip())

    def test_missing_image_is_not_a_successful_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            md = Path(tmp) / "candidate.md"
            md.write_text("<!-- source page 1 -->\n![Signature](missing.png)\n")
            result = run_script("check_markdown.py", md, "--expected-pages", 1)
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertIn("missing local image", result.stdout)

    def test_swapped_source_cells_are_not_certified_by_structural_checks(self):
        with tempfile.TemporaryDirectory() as tmp:
            md = Path(tmp) / "candidate.md"
            # Deliberately plausible but semantically wrong. This script cannot see the PDF.
            md.write_text(
                "<!-- source page 1 -->\n| Name | Company |\n| --- | --- |\n"
                "| Example Ltd | Ada Example |\n- [x] Lunch\n- [ ] Dinner\n"
            )
            result = run_script("check_markdown.py", md, "--expected-pages", 1)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["semantic_verification"], "requires_source_review")
            self.assertEqual(report["checkboxes"], {"selected": 1, "unselected": 1})

    def test_incomplete_page_coverage_and_ragged_tables_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            md = Path(tmp) / "candidate.md"
            md.write_text(
                "<!-- source page 1 -->\n| Item | EUR |\n| --- | --- |\n| Meal |\n"
            )
            result = run_script("check_markdown.py", md, "--expected-pages", 2)
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertIn("page coverage", result.stdout)
            self.assertIn("table column count", result.stdout)

    def test_angle_bracket_image_paths_with_spaces(self):
        from PIL import Image

        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            Image.new("RGB", (10, 10), "white").save(base / "source crop.png")
            md = base / "candidate.md"
            md.write_text("<!-- source page 1 -->\n![Source](<source crop.png>)\n")
            result = run_script("check_markdown.py", md, "--expected-pages", 1)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["local_images"], 1)

    def test_compact_blank_table_cells_are_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            md = Path(tmp) / "candidate.md"
            md.write_text("|Name|Company|\n|---|---|\n|Ada Example||\n")
            result = run_script("check_markdown.py", md)
            self.assertEqual(result.returncode, 0, result.stdout)

    def test_render_and_crop_preserve_source_and_refuse_overwrites(self):
        from PIL import Image
        from reportlab.pdfgen import canvas

        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            pdf = base / "synthetic.pdf"
            writer = canvas.Canvas(str(pdf))
            writer.drawString(50, 750, "Synthetic page one")
            writer.showPage()
            writer.drawString(50, 750, "Synthetic page two")
            writer.save()
            original = pdf.read_bytes()
            pages = base / "pages"
            rendered = run_script(
                "render_pdf.py", pdf, "--output-dir", pages, "--dpi", 72
            )
            self.assertEqual(rendered.returncode, 0, rendered.stderr)
            metadata = json.loads((pages / "source.json").read_text())
            self.assertEqual(metadata["page_count"], 2)
            self.assertEqual(
                metadata["source_sha256"], hashlib.sha256(original).hexdigest()
            )
            crop = base / "crop.png"
            result = run_script(
                "crop_image.py", pages / "page-001.png", crop, "--box", 0, 0, 40, 30
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            with Image.open(crop) as image:
                self.assertEqual(image.size, (40, 30))
            self.assertEqual(pdf.read_bytes(), original)
            again = run_script("render_pdf.py", pdf, "--output-dir", pages)
            self.assertNotEqual(again.returncode, 0)
            again = run_script(
                "crop_image.py", pages / "page-001.png", crop, "--box", 0, 0, 40, 30
            )
            self.assertNotEqual(again.returncode, 0)


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--make-fixture":
        make_fixture(sys.argv[2])
    else:
        unittest.main()
