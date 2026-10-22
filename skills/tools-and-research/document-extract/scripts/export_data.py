"""Validate an extraction candidate and export JSON/CSV; never certify source truth."""

import argparse
import csv
import json
import math
import re
from datetime import date
from pathlib import Path

IDENTIFIER = re.compile(r"[a-z][a-z0-9_]*")
DECIMAL = re.compile(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?")
STATES = {"present", "blank", "absent", "unreadable", "conflicting"}
TYPES = {"string", "integer", "decimal", "boolean", "date"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def text(value):
    return isinstance(value, str) and bool(value.strip())


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def valid_value(value, kind):
    if kind == "integer":
        return type(value) is int
    if kind == "boolean":
        return type(value) is bool
    if not isinstance(value, str):
        return False
    if kind == "decimal":
        return DECIMAL.fullmatch(value) is not None
    if kind == "date":
        try:
            return date.fromisoformat(value).isoformat() == value
        except ValueError:
            return False
    return kind == "string"


def validate(data):
    require(isinstance(data, dict), "Result must be an object")
    require(type(data.get("schema_version")) is int and data["schema_version"] == 1,
            "Expected schema_version 1")
    recipe = data.get("recipe")
    require(isinstance(recipe, dict) and isinstance(recipe.get("tables"), dict), "Missing recipe.tables")
    specs = recipe["tables"]
    tables = data.get("tables")
    require(specs and isinstance(tables, dict) and tables.keys() == specs.keys(), "Table names must match recipe")
    sources = data.get("sources")
    require(isinstance(sources, dict) and sources, "Missing sources")
    for key, source in sources.items():
        require(text(key) and isinstance(source, dict), "Invalid source")
        require(text(source.get("path")) and isinstance(source.get("sha256"), str)
                and re.fullmatch(r"[0-9a-f]{64}", source["sha256"]), "Source needs path and SHA-256")
        require(type(source.get("pages")) is int and source["pages"] > 0, "Invalid source page count")
    provenance = data.get("provenance")
    require(isinstance(provenance, dict) and text(provenance.get("parser"))
            and text(provenance.get("source_check")), "Missing processing/source-check provenance")
    require(provenance.get("vision") in ("none", "session", "internal-api"), "Invalid vision provenance")
    for key in ("coverage", "unresolved"):
        require(isinstance(data.get(key), list) and all(text(v) for v in data[key]), f"Invalid {key}")
    require(data["coverage"], "Coverage must describe inspected scope")
    partial = bool(data["unresolved"])
    records = {}
    parents = []
    for name, spec in specs.items():
        require(IDENTIFIER.fullmatch(name) is not None and isinstance(spec, dict), "Unsafe table name or invalid recipe")
        require(text(spec.get("grain")), f"{name}: missing record grain")
        require("parent" in spec and (spec["parent"] is None or isinstance(spec["parent"], str)
                and spec["parent"] in specs), f"{name}: unknown parent table")
        fields = spec.get("fields")
        if not isinstance(fields, dict) or not fields:
            raise ValueError(f"{name}: missing field definitions")
        for field, definition in fields.items():
            require(IDENTIFIER.fullmatch(field) is not None and field not in ("record_id", "parent_id")
                    and isinstance(definition, dict), f"{name}: invalid/reserved field name")
            require(definition.get("type") in TYPES and type(definition.get("required")) is bool
                    and text(definition.get("description")) and text(definition.get("normalize")),
                    f"{name}.{field}: invalid field definition")
        require(isinstance(tables[name], list), f"{name}: records must be an array")
        for record in tables[name]:
            require(isinstance(record, dict) and text(record.get("record_id")), f"{name}: missing record ID")
            record_id = record["record_id"]
            require(record_id not in records, f"Duplicate record ID: {record_id}")
            records[record_id] = name
            require("parent_id" in record, f"{record_id}: missing parent_id")
            parent = record["parent_id"]
            require(parent is None if spec["parent"] is None else text(parent), f"{record_id}: invalid parent_id")
            if parent is not None:
                parents.append((parent, spec["parent"]))
            values = record.get("fields")
            if not isinstance(values, dict) or values.keys() != fields.keys():
                raise ValueError(f"{record_id}: fields must match recipe")
            for field, cell in values.items():
                location = f"{record_id}.{field}"
                require(isinstance(cell, dict) and {"raw", "value", "status", "evidence", "note"} <= cell.keys(),
                        f"{location}: incomplete field")
                state = cell["status"]
                require(isinstance(state, str) and state in STATES and isinstance(cell["note"], str), f"{location}: invalid state/note")
                if state == "present":
                    require(isinstance(cell["raw"], str) and valid_value(cell["value"], fields[field]["type"]),
                            f"{location}: invalid raw/typed value")
                else:
                    require(cell["value"] is None and (cell["raw"] == "" if state == "blank" else cell["raw"] is None),
                            f"{location}: unresolved/empty states cannot carry a value")
                    if state != "blank":
                        require(text(cell["note"]), f"{location}: explain unresolved reading/search scope")
                    partial |= state in ("unreadable", "conflicting") or fields[field]["required"]
                evidence = cell["evidence"]
                require(isinstance(evidence, list), f"{location}: evidence must be an array")
                require(not evidence if state == "absent" else bool(evidence), f"{location}: missing/invented evidence")
                for item in evidence:
                    require(isinstance(item, dict) and isinstance(item.get("source_id"), str)
                            and item["source_id"] in sources, f"{location}: unknown evidence source")
                    require(type(item.get("page")) is int and 1 <= item["page"] <= sources[item["source_id"]]["pages"],
                            f"{location}: evidence page outside source")
                    require(text(item.get("region")) and "reading" in item
                            and (item["reading"] is None or isinstance(item["reading"], str)), f"{location}: invalid evidence reading/region")
                    if "box" in item:
                        box = item["box"]
                        require(isinstance(box, list) and len(box) == 4 and all(type(v) in (int, float) and math.isfinite(v) for v in box)
                                and box[0] < box[2] and box[1] < box[3] and text(item.get("box_units")), f"{location}: invalid evidence box")
                if state == "conflicting":
                    require(len({e["reading"] for e in evidence if text(e["reading"])}) >= 2, f"{location}: conflict needs competing readings")
    for parent, table in parents:
        require(records.get(parent) == table, "Parent record missing or belongs to wrong table")
    for name in specs:
        visited = set()
        while name is not None:
            require(name not in visited, "Cyclic parent tables")
            visited.add(name)
            name = specs[name]["parent"]
    return partial


def csv_text(value):
    if value is None:
        return ""
    if type(value) is bool:
        return "true" if value else "false"
    if isinstance(value, str) and (value.startswith(("\t", "\r", "\n")) or value.lstrip().startswith(("=", "+", "-", "@"))):
        return "'" + value
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("output_dir", type=Path, help="new directory; existing paths are refused")
    parser.add_argument("--csv", action="store_true", help="also export one value-only CSV per table")
    args = parser.parse_args()
    try:
        data = json.loads(args.candidate.read_text(encoding="utf-8"), object_pairs_hook=unique_object,
                          parse_constant=lambda value: require(False, f"Invalid JSON number: {value}"))
        partial = validate(data)
        output = args.output_dir
        require(not output.exists() and not output.is_symlink(), "Output path already exists; choose a new directory")
        data["export"] = {
            "structural_validation": "passed", "semantic_verification": "not_certified",
            "result_status": "partial" if partial else "complete",
            "csv_files": [f"{name}.csv" for name in data["tables"]] if args.csv else [],
            "csv_text_escape": "apostrophe prefix for formula-like text; raw values preserved in JSON",
        }
        output.mkdir(parents=True, exist_ok=False)
        (output / "data.json").write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        if args.csv:
            for name, records in data["tables"].items():
                definitions = data["recipe"]["tables"][name]["fields"]
                with (output / f"{name}.csv").open("w", encoding="utf-8", newline="") as stream:
                    writer = csv.writer(stream)
                    writer.writerow(["record_id", "parent_id", *definitions])
                    for record in records:
                        values = [record["fields"][field]["value"] if definition["type"] in ("integer", "decimal")
                                  else csv_text(record["fields"][field]["value"])
                                  for field, definition in definitions.items()]
                        writer.writerow([csv_text(record["record_id"]), csv_text(record["parent_id"]), *values])
        print(json.dumps({"output": str(output), **data["export"]}))
    except (OSError, ValueError, TypeError) as exc:
        parser.exit(1, f"export_data: {exc}\n")


if __name__ == "__main__":
    main()
