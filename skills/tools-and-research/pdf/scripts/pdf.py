# /// script
# dependencies = ["pypdf[crypto]>=6.19", "reportlab", "defusedxml", "pypdfium2", "pillow"]
# ///
"""Local PDF operations, AcroForm inspection/filling and bounded text overlays.

No overwrites. Passwords come from a local file, never the command line.
Existing signatures block modification. Render output still needs visual QA.
"""
import argparse
import json
import math
import shutil
import sys
import tempfile
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from office import new_output, render_pdf


def read(source, password_file=None):
    reader = PdfReader(source)
    if reader.is_encrypted:
        if password_file is None or not reader.decrypt(password_file.read_text(encoding="utf-8").rstrip("\r\n")):
            raise ValueError("Valid --password-file required; use only with the owner's authorization")
    return reader


def widgets(reader):
    result = []
    for index, page in enumerate(reader.pages, 1):
        for reference in page.get("/Annots", []):
            widget = reference.get_object()
            if widget.get("/Subtype") != "/Widget":
                continue
            ancestors, current, seen = [], widget, set()
            while current is not None:
                marker = id(current)
                if marker in seen:
                    raise ValueError("Cyclic PDF field parents")
                seen.add(marker)
                ancestors.append(current)
                current = current.get("/Parent")
                current = current.get_object() if current is not None else None
            name = ".".join(str(item["/T"]) for item in reversed(ancestors) if "/T" in item)
            field_type = next((item.get("/FT") for item in ancestors if "/FT" in item), None)
            states = widget.get("/AP", {}).get("/N")
            states = states.get_object() if states is not None else {}
            inherited = lambda key, default: next((item[key] for item in ancestors if key in item), default)
            options = inherited("/Opt", [])
            result.append({"name": name, "page": index, "type": str(field_type), "rect": [float(n) for n in widget.get("/Rect", [])], "states": list(states.keys()) if isinstance(states, dict) else [], "flags": int(inherited("/Ff", 0)), "max_length": int(inherited("/MaxLen", 0)), "options": [list(map(str, option)) if isinstance(option, list) else str(option) for option in options]})
    return result


def form_report(reader):
    fields = reader.get_fields() or {}
    return {"status": "ok", "fields": {str(name): {"type": str(value.get("/FT")), "value": str(value.get("/V", "")), "options": [str(item) for item in value.get("/Opt", [])]} for name, value in fields.items()}, "widgets": widgets(reader), "coordinate_system": "PDF points, bottom-left, before page rotation"}


def writable(reader):
    if any(field.get("/FT") == "/Sig" and field.get("/V") for field in (reader.get_fields() or {}).values()):
        raise ValueError("Signed PDF: modification invalidates signatures; obtain an unsigned working copy")
    root = reader.trailer["/Root"]
    if "/Perms" in root:
        raise ValueError("Certified/permission-controlled PDF: obtain an authorized unsigned working copy")
    writer = PdfWriter(clone_from=reader)
    return writer


def fill(reader, writer, values):
    fields = reader.get_fields() or {}
    acroform = reader.trailer["/Root"].get("/AcroForm")
    if acroform is not None and "/XFA" in acroform.get_object():
        raise ValueError("XFA forms need their native form software")
    if not isinstance(values, dict) or not values:
        raise ValueError("Values file must be a nonempty JSON object keyed by field name")
    unknown = set(values) - set(fields)
    if unknown:
        raise ValueError(f"Unknown fields: {sorted(unknown)}")
    widgets_by_name = {}
    for item in widgets(reader):
        widgets_by_name.setdefault(item["name"], []).append(item)
    for name, value in values.items():
        if not isinstance(value, str):
            raise ValueError(f"{name}: value must be text; checkbox value is an exact export state such as /Yes")
        field = fields[name]
        kind = field.get("/FT")
        matched = widgets_by_name.get(name, [])
        if not matched:
            raise ValueError(f"{name}: no visible widget found")
        flags = 0
        for item in matched:
            flags |= item["flags"]
        if flags & 1:
            raise ValueError(f"{name}: read-only field")
        if kind == "/Btn":
            if flags & (1 << 16):
                raise ValueError(f"{name}: push buttons are actions, not fillable values")
            states = {state for item in matched for state in item["states"]}
            if value not in states:
                raise ValueError(f"{name}: choose one of {sorted(states)}")
        elif kind == "/Ch":
            if flags & (1 << 21):
                raise ValueError(f"{name}: multiselect fields need task-specific handling")
            options = [str(option[0] if isinstance(option, list) else option) for option in matched[0]["options"]]
            if value not in options:
                raise ValueError(f"{name}: choose one of {options}")
        elif kind != "/Tx":
            raise ValueError(f"{name}: unsupported field type {kind}")
        limits = [item["max_length"] for item in matched if item["max_length"] > 0]
        maximum = min(limits) if limits else 0
        if maximum and len(value) > maximum:
            raise ValueError(f"{name}: text exceeds MaxLen {maximum}")
        for widget in matched:
            rect = widget["rect"]
            box = reader.pages[widget["page"] - 1].cropbox
            if len(rect) != 4 or not all(math.isfinite(n) for n in rect) or not (float(box.left) <= rect[0] < rect[2] <= float(box.right) and float(box.bottom) <= rect[1] < rect[3] <= float(box.top)):
                raise ValueError(f"{name}: widget rectangle outside page crop; inspect form before filling")
    for page in writer.pages:
        if "/Annots" in page:
            writer.update_page_form_field_values(page, values, auto_regenerate=False)
    check = writer.get_fields() or {}
    for name, value in values.items():
        if str(check.get(name, {}).get("/V", "")) != value:
            raise ValueError(f"{name}: written value failed verification")


def flatten(reader, writer):
    form = reader.trailer["/Root"].get("/AcroForm")
    if form is not None and "/XFA" in form.get_object():
        raise ValueError("XFA forms require native form software")
    fields = reader.get_fields() or {}
    if not fields:
        raise ValueError("No AcroForm fields to flatten")
    if any(field.get("/FT") not in {"/Tx", "/Ch", "/Btn"} for field in fields.values()):
        raise ValueError("Flattening supports text, choice and button fields only")
    values = {name: field.get("/V", field.get("/DV", "/Off" if field.get("/FT") == "/Btn" else "")) for name, field in fields.items()}
    number = 0
    for page in writer.pages:
        if "/Annots" not in page:
            continue
        writer.update_page_form_field_values(page, values, auto_regenerate=False)
        for reference in page["/Annots"]:
            widget = reference.get_object()
            if widget.get("/Subtype") != "/Widget":
                continue
            appearance = widget.get("/AP", {}).get("/N")
            appearance = appearance.get_object() if appearance is not None else None
            if appearance is not None and not hasattr(appearance, "get_data"):
                appearance = appearance.get(widget.get("/AS", "/Off"))
                appearance = appearance.get_object() if appearance is not None else None
            if appearance is None:
                raise ValueError("Widget has no normal appearance; refusing to discard an invisible/unverified field")
            number += 1
            rect = widget["/Rect"]
            # Per-widget names avoid pypdf's same-field resource collision for radio groups.
            # This isolated private API is exercised by the real-file/raster regression.
            writer._add_apstream_object(page, appearance, f"flattened_widget_{number}", rect[0], rect[1])
    writer.remove_annotations("/Widget")
    writer._root_object.pop("/AcroForm", None)


def stamp(writer, annotations, font_file=None):
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfgen import canvas
    font = "Helvetica"
    if font_file:
        font = "UserFont"
        pdfmetrics.registerFont(TTFont(font, str(font_file)))
    if not isinstance(annotations, list) or not annotations:
        raise ValueError("Annotations must be a nonempty list of page/x/y/text/size objects")
    for item in annotations:
        number = item["page"]
        if not isinstance(number, int) or not 1 <= number <= len(writer.pages):
            raise ValueError("Annotation page outside document")
        page = writer.pages[number - 1]
        if page.rotation:
            raise ValueError("Normalize rotated pages before coordinate stamping")
        x, y, size = float(item["x"]), float(item["y"]), float(item.get("size", 11))
        text = item["text"]
        if not isinstance(text, str) or not text or "\n" in text:
            raise ValueError("Stamp text must be a nonempty single line")
        if not font_file and any(ord(char) > 126 for char in text):
            raise ValueError("Non-ASCII overlay text requires --font with a suitable Unicode TTF")
        width = pdfmetrics.stringWidth(text, font, size)
        box = page.cropbox
        if not all(math.isfinite(n) for n in (x, y, size, width)) or size <= 0 or not (float(box.left) <= x and x + width <= float(box.right) and float(box.bottom) + size <= y <= float(box.top) - size):
            raise ValueError("Text overlay extends outside page crop")
        memory = BytesIO()
        layer = canvas.Canvas(memory, pagesize=(float(page.mediabox.right), float(page.mediabox.top)))
        layer.setFont(font, size)
        layer.drawString(x, y, text)
        layer.save()
        page.merge_page(PdfReader(memory).pages[0])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("fields", "metadata", "images", "render", "fill", "flatten", "stamp", "watermark", "encrypt", "decrypt", "select"):
        cmd = sub.add_parser(name)
        cmd.add_argument("input", type=Path)
        cmd.add_argument("--password-file", type=Path)
        if name not in {"fields", "metadata"}:
            cmd.add_argument("output", type=Path)
        if name == "fill":
            cmd.add_argument("--values", required=True, type=Path)
        if name == "stamp":
            cmd.add_argument("--annotations", required=True, type=Path)
            cmd.add_argument("--font", type=Path)
        if name == "watermark":
            cmd.add_argument("--overlay", required=True, type=Path)
        if name == "encrypt":
            cmd.add_argument("--new-password-file", required=True, type=Path)
        if name == "select":
            cmd.add_argument("--pages", required=True, help="one-based page order, e.g. 3,1,2")
    args = parser.parse_args()
    try:
        reader = read(args.input, args.password_file)
        if args.command == "fields":
            report = form_report(reader)
        elif args.command == "metadata":
            report = {"status": "ok", "pages": len(reader.pages), "metadata": {str(k): str(v) for k, v in (reader.metadata or {}).items()}}
        else:
            _, output = new_output(args.input, args.output)
            if args.command == "render":
                # Render the decrypted copy without putting a password on argv.
                with tempfile.TemporaryDirectory() as temporary:
                    plain = Path(temporary) / "render.pdf"
                    PdfWriter(clone_from=reader).write(plain)
                    report = render_pdf(plain, output)
            elif args.command == "images":
                with tempfile.TemporaryDirectory() as temporary:
                    count = 0
                    for number, page in enumerate(reader.pages, 1):
                        for image in page.images:
                            count += 1
                            name = f"page-{number:03d}-image-{count:03d}{Path(image.name).suffix}"
                            (Path(temporary) / name).write_bytes(image.data)
                    shutil.copytree(temporary, output)
                report = {"status": "ok", "images": count, "directory": str(output)}
            else:
                writer = writable(reader)
                if args.command == "fill":
                    fill(reader, writer, json.loads(args.values.read_text(encoding="utf-8")))
                elif args.command == "flatten":
                    flatten(reader, writer)
                elif args.command == "stamp":
                    stamp(writer, json.loads(args.annotations.read_text(encoding="utf-8")), args.font)
                elif args.command == "watermark":
                    overlay = read(args.overlay)
                    if len(overlay.pages) != 1:
                        raise ValueError("Overlay PDF must contain exactly one page")
                    for page in writer.pages:
                        page.merge_page(overlay.pages[0])
                elif args.command == "encrypt":
                    password = args.new_password_file.read_text(encoding="utf-8").rstrip("\r\n")
                    if not password:
                        raise ValueError("New password must not be empty")
                    writer.encrypt(password, algorithm="AES-256")
                elif args.command == "select":
                    order = [int(i) - 1 for i in args.pages.split(",")]
                    if not order or any(i < 0 or i >= len(reader.pages) for i in order):
                        raise ValueError("Page selection outside document")
                    if reader.get_fields():
                        raise ValueError("Page selection on a form needs deliberate field reconciliation")
                    writer = PdfWriter()
                    for number in order:
                        writer.add_page(reader.pages[number])
                with tempfile.TemporaryDirectory() as temporary:
                    staged = Path(temporary) / "output.pdf"
                    writer.write(staged)
                    check = read(staged, args.new_password_file if args.command == "encrypt" else None)
                    if len(check.pages) != len(writer.pages):
                        raise ValueError("Output page-count verification failed")
                    with output.open("xb") as stream, staged.open("rb") as origin:
                        shutil.copyfileobj(origin, stream)
                report = {"status": "ok", "operation": args.command, "pages": len(writer.pages), "output": str(output), "visual_qa": "pending"}
        print(json.dumps(report))
        return 0
    except Exception as exc:
        print(json.dumps({"status": "error", "error": str(exc)}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
