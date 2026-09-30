# /// script
# dependencies = ["python-docx>=1.2", "defusedxml"]
# ///
"""Add an anchored comment, tracked plain-text replacement, or accept inline revisions.

Replacement/comment targets must occur exactly once in body/table paragraphs.
Unsupported structural revisions are rejected rather than silently discarded.
"""
import argparse
import copy
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph
from office import new_output, validate


def paragraphs(document):
    return [Paragraph(element, document._body) for element in document.element.body.iter(qn("w:p")) if element.getparent().tag in {qn("w:body"), qn("w:tc")}]


def save(document, output):
    # Validate before publishing; output stays new and original stays untouched.
    import tempfile
    with tempfile.TemporaryDirectory() as temporary:
        staged = Path(temporary) / "result.docx"
        document.save(staged)
        report = validate(staged)
        if report["errors"]:
            raise ValueError(report["errors"])
        with output.open("xb") as stream:
            stream.write(staged.read_bytes())


def find_target(document, text):
    if not text:
        raise ValueError("Target text must not be empty")
    matches = []
    count = 0
    for paragraph in paragraphs(document):
        content = paragraph.text
        occurrences = content.count(text)
        if occurrences:
            matches.append((paragraph, content.index(text)))
            count += occurrences
    if count != 1:
        raise ValueError(f"Target must occur exactly once in body/table text; found {count}")
    paragraph, start = matches[0]
    if any(child.tag not in {qn("w:pPr"), qn("w:r")} for child in paragraph._p):
        raise ValueError("Target paragraph contains hyperlinks, bookmarks or revisions; use a task-specific OOXML edit")
    if any(child.tag not in {qn("w:rPr"), qn("w:t")} for run in paragraph._p.findall(qn("w:r")) for child in run):
        raise ValueError("Target paragraph contains fields, images, tabs or breaks; use a task-specific OOXML edit")
    return paragraph, start


def fragment(run, text, deleted=False):
    result = copy.deepcopy(run)
    for element in list(result):
        if element.tag != qn("w:rPr"):
            result.remove(element)
    node = OxmlElement("w:delText" if deleted else "w:t")
    node.set(qn("xml:space"), "preserve")
    node.text = text
    result.append(node)
    return result


def replace(document, target, replacement, author):
    paragraph, start = find_target(document, target)
    end = start + len(target)
    before, deleted, after = [], [], []
    offset = 0
    for run in paragraph.runs:
        text = run.text
        stop = offset + len(text)
        if stop <= start:
            before.append(copy.deepcopy(run._r))
        elif offset >= end:
            after.append(copy.deepcopy(run._r))
        else:
            left, right = max(0, start - offset), min(len(text), end - offset)
            if left:
                before.append(fragment(run._r, text[:left]))
            deleted.append(fragment(run._r, text[left:right], deleted=True))
            if right < len(text):
                after.append(fragment(run._r, text[right:]))
        offset = stop
    ids = [int(e.get(qn("w:id"))) for e in document.element.iter() if e.get(qn("w:id"), "").isdigit()]
    next_id = max(ids, default=0) + 1
    deletion = OxmlElement("w:del")
    insertion = OxmlElement("w:ins")
    for index, wrapper in enumerate((deletion, insertion)):
        wrapper.set(qn("w:id"), str(next_id + index))
        wrapper.set(qn("w:author"), author)
        wrapper.set(qn("w:date"), datetime.now(timezone.utc).isoformat(timespec="seconds"))
    deletion.extend(deleted)
    if replacement:
        insertion.append(fragment(deleted[0], replacement))
    for child in list(paragraph._p):
        if child.tag != qn("w:pPr"):
            paragraph._p.remove(child)
    paragraph._p.extend(before + [deletion] + ([insertion] if replacement else []) + after)


def comment(document, target, text, author):
    paragraph, start = find_target(document, target)
    end = start + len(target)
    selected = []
    offset = 0
    # Split only boundary runs so comments anchor to exactly the requested text.
    for run in list(paragraph.runs):
        stop = offset + len(run.text)
        if stop > start and offset < end:
            left, right = max(0, start - offset), min(len(run.text), end - offset)
            parent = run._r.getparent()
            index = parent.index(run._r)
            pieces = []
            if left:
                pieces.append(fragment(run._r, run.text[:left]))
            anchor = fragment(run._r, run.text[left:right])
            pieces.append(anchor)
            if right < len(run.text):
                pieces.append(fragment(run._r, run.text[right:]))
            parent.remove(run._r)
            for piece in pieces:
                parent.insert(index, piece)
                index += 1
            from docx.text.run import Run
            selected.append(Run(anchor, paragraph))
        offset = stop
    document.add_comment(selected, text=text, author=author, initials="".join(word[0] for word in author.split()))


def accept(document):
    root = document.element.body
    if any(e.tag in {qn("w:moveFrom"), qn("w:moveTo"), qn("w:moveFromRangeStart"), qn("w:moveToRangeStart"), qn("w:cellIns"), qn("w:cellDel"), qn("w:cellMerge")} for e in root.iter()):
        raise ValueError("Move/cell revisions require Word; this helper only accepts inline insertions/deletions and property changes")
    marks = []
    for element in root.iter():
        if element.tag not in {qn("w:ins"), qn("w:del")}:
            continue
        parent = element.getparent()
        if parent.tag == qn("w:p"):
            continue
        if element.tag == qn("w:del") and parent.tag == qn("w:rPr") and parent.getparent().tag == qn("w:pPr"):
            paragraph = parent.getparent().getparent()
            following = paragraph.getnext()
            if following is None or following.tag != qn("w:p"):
                raise ValueError("Deleted paragraph mark without an adjacent paragraph; accept in Word")
            marks.append(paragraph)
        else:
            raise ValueError("Structural or paragraph-insertion revision requires Word")
    for element in list(root.iter(qn("w:del"))):
        element.getparent().remove(element)
    for element in list(root.iter(qn("w:ins"))):
        parent = element.getparent()
        index = parent.index(element)
        for child in list(element):
            parent.insert(index, child)
            index += 1
        parent.remove(element)
    for paragraph in reversed(marks):
        following = paragraph.getnext()
        # Deleting a paragraph mark adopts the following paragraph's formatting.
        previous_properties = paragraph.find(qn("w:pPr"))
        if previous_properties is not None:
            paragraph.remove(previous_properties)
        next_properties = following.find(qn("w:pPr"))
        if next_properties is not None:
            paragraph.insert(0, copy.deepcopy(next_properties))
        for child in list(following):
            if child.tag != qn("w:pPr"):
                paragraph.append(child)
        following.getparent().remove(following)
    for element in list(root.iter()):
        if element.tag.startswith(qn("w:rPr").split("}")[0] + "}") and element.tag.rsplit("}", 1)[-1] in {"rPrChange", "pPrChange", "sectPrChange", "tblPrChange", "trPrChange", "tcPrChange", "tblGridChange"}:
            element.getparent().remove(element)
    # Header/footer revisions are not silently claimed as accepted.
    from lxml import etree
    for part in document.part.package.parts:
        if part.partname != document.part.partname and str(part.partname).endswith(".xml"):
            tree = etree.fromstring(part.blob, etree.XMLParser(resolve_entities=False, no_network=True))
            if any(e.tag in {qn("w:ins"), qn("w:del"), qn("w:moveFrom"), qn("w:moveTo")} for e in tree.iter()):
                raise ValueError("Revisions outside body/tables require Word")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("replace", "comment", "accept"):
        cmd = sub.add_parser(name)
        cmd.add_argument("input", type=Path)
        cmd.add_argument("output", type=Path)
        if name != "accept":
            cmd.add_argument("target")
            cmd.add_argument("text")
            cmd.add_argument("--author", required=True)
    args = parser.parse_args()
    try:
        source, output = new_output(args.input, args.output)
        if source.suffix.lower() != ".docx" or output.suffix.lower() != ".docx":
            raise ValueError("Editing helper supports .docx only")
        report = validate(source)
        if report["errors"]:
            raise ValueError(report["errors"])
        doc = Document(source)
        if args.command == "accept":
            accept(doc)
        elif args.command == "replace":
            replace(doc, args.target, args.text, args.author)
        else:
            comment(doc, args.target, args.text, args.author)
        save(doc, output)
        print(json.dumps({"status": "ok", "operation": args.command, "output": str(output)}))
        return 0
    except Exception as exc:
        print(json.dumps({"status": "error", "error": str(exc)}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
