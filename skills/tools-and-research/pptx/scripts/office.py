# /// script
# dependencies = ["defusedxml", "pypdfium2", "pillow"]
# ///
"""Portable Office package checks and isolated LibreOffice-to-PNG rendering.

Identical copies ship in DOCX/PPTX/XLSX so each skill installs independently.
Checks are structural, not complete ISO schema validation or visual approval.
"""
import argparse
import json
import os
import posixpath
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from urllib.parse import unquote

from defusedxml import ElementTree as ET

REL = "http://schemas.openxmlformats.org/package/2006/relationships"
ATTR_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
CT = "http://schemas.openxmlformats.org/package/2006/content-types"


def new_output(source, output):
    source, output = Path(source).resolve(), Path(output).resolve()
    if source == output or output.exists():
        raise ValueError("Output must be a new path; original and existing files are never overwritten")
    if not output.parent.is_dir():
        raise ValueError("Output parent directory must exist")
    return source, output


def soffice_path():
    found = shutil.which("soffice") or shutil.which("libreoffice")
    candidates = [Path("/Applications/LibreOffice.app/Contents/MacOS/soffice")]
    for variable in ("PROGRAMFILES", "PROGRAMFILES(X86)"):
        if os.environ.get(variable):
            candidates.append(Path(os.environ[variable]) / "LibreOffice/program/soffice.exe")
    found = found or next((str(p) for p in candidates if p.is_file()), None)
    if not found:
        raise RuntimeError("LibreOffice not found; install it or verify/render in Microsoft Office")
    return found


def convert(source, directory, extension, timeout=120):
    """Convert a copy with a fresh profile, never a user's open LibreOffice session."""
    source, directory = Path(source).resolve(), Path(directory).resolve()
    with tempfile.TemporaryDirectory(prefix="office-profile-") as profile:
        result = subprocess.run([
            soffice_path(), f"-env:UserInstallation={Path(profile).as_uri()}",
            "--headless", "--convert-to", extension, "--outdir", str(directory), str(source),
        ], capture_output=True, text=True, timeout=timeout)
    expected = directory / f"{source.stem}.{extension.split(':', 1)[0]}"
    if result.returncode or not expected.is_file():
        raise RuntimeError(f"LibreOffice conversion failed: {result.stdout} {result.stderr}")
    return expected


def validate(source):
    issues = []
    with zipfile.ZipFile(source) as package:
        names = package.namelist()
        files = set(names)
        if len(names) != len(files):
            issues.append("Duplicate ZIP entries")
        if any(n.startswith("/") or ".." in n.split("/") or "\\" in n for n in names):
            issues.append("Unsafe ZIP member path")
        trees = {}
        for name in names:
            if name.endswith((".xml", ".rels")):
                try:
                    trees[name] = ET.fromstring(package.read(name))
                except Exception as exc:
                    issues.append(f"{name}: invalid or unsafe XML ({exc})")
        types = trees.get("[Content_Types].xml")
        if types is None:
            issues.append("Missing [Content_Types].xml")
        else:
            defaults = {e.get("Extension") for e in types.findall(f"{{{CT}}}Default")}
            overrides = {unquote(e.get("PartName", "")).lstrip("/") for e in types.findall(f"{{{CT}}}Override")}
            for name in overrides - files:
                issues.append(f"Content type references missing part: {name}")
            for name in files:
                if name.endswith("/") or name == "[Content_Types].xml":
                    continue
                if name not in overrides and name.rsplit(".", 1)[-1] not in defaults:
                    issues.append(f"No content type: {name}")
        maps = {}
        root_office = []
        for name, tree in trees.items():
            if not name.endswith(".rels"):
                continue
            if name == "_rels/.rels":
                owner = ""
            else:
                folder, leaf = posixpath.split(name)
                if posixpath.basename(folder) != "_rels":
                    issues.append(f"Unexpected relationships path: {name}")
                    continue
                owner = posixpath.join(posixpath.dirname(folder), leaf[:-5])
                if owner not in files:
                    issues.append(f"Relationships without owning part: {name}")
            ids = set()
            for rel in tree.findall(f"{{{REL}}}Relationship"):
                rid = rel.get("Id")
                if not rid or rid in ids:
                    issues.append(f"{name}: missing or duplicate relationship Id {rid}")
                ids.add(rid)
                if rel.get("TargetMode") == "External":
                    continue  # never fetch external relationships
                target = unquote(rel.get("Target", "").split("#", 1)[0])
                resolved = posixpath.normpath(target.lstrip("/") if target.startswith("/") else posixpath.join(posixpath.dirname(owner), target))
                if not target or resolved not in files:
                    issues.append(f"{name}: missing target {target}")
                if not owner and rel.get("Type", "").endswith("/officeDocument"):
                    root_office.append(resolved)
            maps[owner] = ids
        if len(root_office) != 1:
            issues.append("Expected exactly one root officeDocument relationship")
        for name, tree in trees.items():
            if name.endswith(".rels"):
                continue
            for element in tree.iter():
                for attr, value in element.attrib.items():
                    if attr.startswith(f"{{{ATTR_REL}}}") and value not in maps.get(name, set()):
                        issues.append(f"{name}: unresolved relationship {value}")
            if "/charts/" in name:
                chart_ns = "http://schemas.openxmlformats.org/drawingml/2006/chart"
                declared = {e.find(f"{{{chart_ns}}}axId").get("val") for e in tree.iter() if e.tag in {f"{{{chart_ns}}}{kind}" for kind in ("catAx", "valAx", "dateAx", "serAx")} and e.find(f"{{{chart_ns}}}axId") is not None}
                referenced = {e.get("val") for e in tree.iter(f"{{{chart_ns}}}axId")}
                if referenced - declared:
                    issues.append(f"{name}: undeclared chart axes {sorted(referenced - declared)}")
    return {"status": "errors" if issues else "ok", "checks": "ZIP, safe XML, content types, relationships, chart axis references", "errors": issues}


def render_pdf(source, output, dpi=120):
    import pypdfium2 as pdfium
    from PIL import Image, ImageDraw

    source, output = new_output(source, output)
    if dpi < 36 or dpi > 300:
        raise ValueError("DPI must be between 36 and 300")
    with tempfile.TemporaryDirectory(prefix="office-render-") as temp:
        staged = Path(temp)
        thumbnails = []
        with pdfium.PdfDocument(str(source)) as pdf:
            pdf.init_forms()
            if not len(pdf):
                raise ValueError("PDF has no pages")
            for index in range(len(pdf)):
                page = pdf[index]
                bitmap = page.render(scale=dpi / 72, draw_annots=True)
                image = bitmap.to_pil().convert("RGB")
                image.save(staged / f"page-{index + 1:03d}.png")
                image.thumbnail((240, 320))
                tile = Image.new("RGB", (260, 350), "white")
                tile.paste(image, ((260 - image.width) // 2, 25))
                ImageDraw.Draw(tile).text((10, 5), f"Page {index + 1}", fill="black")
                thumbnails.append(tile)
                bitmap.close()
                page.close()
        # Contact sheets are navigation aids; inspect full-resolution pages for QA.
        columns = min(4, len(thumbnails))
        sheet = Image.new("RGB", (260 * columns, 350 * ((len(thumbnails) + columns - 1) // columns)), "#dddddd")
        for index, tile in enumerate(thumbnails):
            sheet.paste(tile, ((index % columns) * 260, (index // columns) * 350))
        sheet.save(staged / "contact-sheet.png")
        shutil.copytree(staged, output)
    return {"status": "ok", "pages": len(thumbnails), "directory": str(output), "visual_qa": "pending human/agent image inspection"}


def template(source, output):
    """Switch a non-macro document/template main content type in a new package."""
    source, output = new_output(source, output)
    mime = {
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml",
        ".dotx": "application/vnd.openxmlformats-officedocument.wordprocessingml.template.main+xml",
        ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml",
        ".potx": "application/vnd.openxmlformats-officedocument.presentationml.template.main+xml",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml",
        ".xltx": "application/vnd.openxmlformats-officedocument.spreadsheetml.template.main+xml",
    }
    pairs = ({".docx", ".dotx"}, {".pptx", ".potx"}, {".xlsx", ".xltx"})
    old, new = source.suffix.lower(), output.suffix.lower()
    if not any({old, new} == pair for pair in pairs):
        raise ValueError("Choose a matching non-macro document/template pair (.docx/.dotx, .pptx/.potx, .xlsx/.xltx)")
    check = validate(source)
    if check["errors"]:
        raise ValueError(check["errors"])
    with zipfile.ZipFile(source) as archive:
        types = ET.fromstring(archive.read("[Content_Types].xml"))
        matches = [e for e in types if e.get("ContentType") == mime[old]]
        if len(matches) != 1:
            raise ValueError("Input extension/main content type mismatch")
        matches[0].set("ContentType", mime[new])
        with tempfile.TemporaryDirectory() as temporary:
            staged = Path(temporary) / output.name
            with zipfile.ZipFile(staged, "w", zipfile.ZIP_DEFLATED) as package:
                for info in archive.infolist():
                    package.writestr(info, ET.tostring(types, encoding="utf-8", xml_declaration=True) if info.filename == "[Content_Types].xml" else archive.read(info.filename))
            with output.open("xb") as stream, staged.open("rb") as origin:
                shutil.copyfileobj(origin, stream)
    return {"status": "ok", "output": str(output), "note": "Package type changed; fields/layout still need native Office verification"}


def render(source, output, dpi=120):
    source, output = new_output(source, output)
    report = validate(source)
    if report["errors"]:
        raise ValueError(f"Invalid package: {report['errors']}")
    with tempfile.TemporaryDirectory(prefix="office-convert-") as temp:
        export = 'pdf:impress_pdf_Export:{"ExportHiddenSlides":{"type":"boolean","value":"true"}}' if source.suffix.lower() in {".pptx", ".potx"} else "pdf"
        pdf = convert(source, temp, export)
        result = render_pdf(pdf, output, dpi)
        shutil.copy2(pdf, output / "document.pdf")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("validate")
    check.add_argument("input", type=Path)
    draw = sub.add_parser("render")
    draw.add_argument("input", type=Path)
    draw.add_argument("output", type=Path)
    draw.add_argument("--dpi", type=int, default=120)
    kind = sub.add_parser("template")
    kind.add_argument("input", type=Path)
    kind.add_argument("output", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "validate":
            report = validate(args.input)
        elif args.command == "template":
            report = template(args.input, args.output)
        else:
            report = render(args.input, args.output, args.dpi)
        print(json.dumps(report))
        return 1 if report.get("errors") else 0
    except Exception as exc:
        print(json.dumps({"status": "error", "error": str(exc)}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
