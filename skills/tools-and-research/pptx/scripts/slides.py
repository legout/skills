# /// script
# dependencies = ["lxml", "defusedxml"]
# ///
"""Select/reorder/duplicate slides within one PPTX/POTX, cloning mutable parts.

Slide numbers are one-based. Repeated numbers duplicate the selected slide;
omitted numbers delete it. This is not a cross-deck theme/master merger.
"""
import argparse
import copy
import json
import posixpath
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path
from urllib.parse import unquote

from lxml import etree as XML
from office import new_output, validate, REL, CT

P = "http://schemas.openxmlformats.org/presentationml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def relpath(part):
    folder, leaf = posixpath.split(part)
    return posixpath.join(folder, "_rels", leaf + ".rels") if part else "_rels/.rels"


def target_path(owner, target):
    target = unquote(target)
    return posixpath.normpath(target.lstrip("/") if target.startswith("/") else posixpath.join(posixpath.dirname(owner), target))


def select(source, output, order):
    source, output = new_output(source, output)
    if source.suffix.lower() not in {".pptx", ".potx"} or output.suffix.lower() != source.suffix.lower():
        raise ValueError("Use matching .pptx or .potx extensions")
    report = validate(source)
    if report["errors"]:
        raise ValueError(report["errors"])
    with zipfile.ZipFile(source) as archive:
        parts = {name: archive.read(name) for name in archive.namelist() if not name.endswith("/")}
    parse = lambda data: XML.fromstring(data, XML.XMLParser(resolve_entities=False, no_network=True))
    dump = lambda tree: XML.tostring(tree, xml_declaration=True, encoding="UTF-8", standalone=True)
    root = parse(parts["_rels/.rels"])
    presentation_path = next(target_path("", rel.get("Target")) for rel in root if rel.get("Type", "").endswith("/officeDocument"))
    presentation = parse(parts[presentation_path])
    relationships = parse(parts[relpath(presentation_path)])
    listing = presentation.find(f"{{{P}}}sldIdLst")
    if listing is None:
        raise ValueError("Presentation has no slide list")
    originals = list(listing)
    if not order or any(i < 1 or i > len(originals) for i in order):
        raise ValueError(f"Choose slide numbers from 1 to {len(originals)}; output needs at least one slide")
    # Section/custom-show references need deliberate editing, not stale slide IDs.
    if presentation.find(f"{{{P}}}custShowLst") is not None or any(XML.QName(e).localname == "sectionLst" for e in presentation.iter()):
        raise ValueError("Custom shows/sections present; edit their membership in PowerPoint before using this helper")
    lookup = {rel.get("Id"): rel for rel in relationships}
    types = parse(parts["[Content_Types].xml"])
    serial = 0

    def clone(part, mapped):
        nonlocal serial
        if part in mapped:
            return mapped[part]
        serial += 1
        stem, extension = posixpath.splitext(part)
        candidate = f"{stem}_copy{serial}{extension}"
        while candidate in parts:
            serial += 1
            candidate = f"{stem}_copy{serial}{extension}"
        mapped[part] = candidate
        parts[candidate] = parts[part]
        existing_type = next((e for e in types if e.get("PartName") == "/" + part), None)
        if existing_type is not None:
            new_type = copy.deepcopy(existing_type)
            new_type.set("PartName", "/" + candidate)
            types.append(new_type)
        old_rels = relpath(part)
        if old_rels in parts:
            relations = parse(parts[old_rels])
            for rel in relations:
                if rel.get("TargetMode") == "External":
                    continue
                original = target_path(part, rel.get("Target"))
                immutable = rel.get("Type", "").rsplit("/", 1)[-1] in {"slideLayout", "slideMaster", "notesMaster", "handoutMaster", "theme", "image"}
                destination = original if immutable else clone(original, mapped)
                rel.set("Target", posixpath.relpath(destination, posixpath.dirname(candidate)))
            parts[relpath(candidate)] = dump(relations)
        return candidate

    for element in list(listing):
        listing.remove(element)
    for rel in list(relationships):
        if rel.get("Type", "").endswith("/slide"):
            relationships.remove(rel)
    used = {rel.get("Id") for rel in relationships}
    for index, number in enumerate(order, 1):
        old = lookup[originals[number - 1].get(f"{{{R}}}id")]
        source_slide = target_path(presentation_path, old.get("Target"))
        cloned_slide = clone(source_slide, {})
        rid = f"rIdSelected{index}"
        while rid in used:
            rid += "x"
        used.add(rid)
        relation = copy.deepcopy(old)
        relation.set("Id", rid)
        relation.set("Target", posixpath.relpath(cloned_slide, posixpath.dirname(presentation_path)))
        relationships.append(relation)
        entry = copy.deepcopy(originals[number - 1])
        entry.set("id", str(255 + index))
        entry.set(f"{{{R}}}id", rid)
        listing.append(entry)
    parts[presentation_path] = dump(presentation)
    parts[relpath(presentation_path)] = dump(relationships)
    # Remove orphaned slides/media/relationships by walking the actual OPC graph.
    reachable = set()

    def visit(part):
        if part in reachable:
            return
        if part:
            reachable.add(part)
        relations_path = relpath(part)
        if relations_path in reachable or relations_path not in parts:
            return
        reachable.add(relations_path)
        for rel in parse(parts[relations_path]):
            if rel.get("TargetMode") != "External":
                visit(target_path(part, rel.get("Target")))

    visit("")
    for element in list(types):
        if element.tag == f"{{{CT}}}Override" and element.get("PartName", "").lstrip("/") not in reachable:
            types.remove(element)
    parts["[Content_Types].xml"] = dump(types)
    reachable.add("[Content_Types].xml")
    with tempfile.TemporaryDirectory() as temporary:
        staged = Path(temporary) / output.name
        with zipfile.ZipFile(staged, "w", zipfile.ZIP_DEFLATED) as archive:
            for name in sorted(reachable):
                archive.writestr(name, parts[name])
        result = validate(staged)
        if result["errors"]:
            raise ValueError(result["errors"])
        with output.open("xb") as destination, staged.open("rb") as origin:
            shutil.copyfileobj(origin, destination)
    return {"status": "ok", "slides": len(order), "order": order, "output": str(output)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--order", required=True, help="one-based comma-separated slide numbers, e.g. 3,1,1")
    args = parser.parse_args()
    try:
        print(json.dumps(select(args.input, args.output, [int(i) for i in args.order.split(",")])))
        return 0
    except Exception as exc:
        print(json.dumps({"status": "error", "error": str(exc)}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
