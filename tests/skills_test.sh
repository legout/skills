#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)

fail() {
    printf 'FAIL: %s\n' "$*" >&2
    exit 1
}

assert_contains() {
    grep -Fqi -- "$2" "$1" || fail "missing in $1: $2"
}

python3 - "$ROOT" <<'PY'
import hashlib
import json
import re
import sys
import urllib.parse
from pathlib import Path, PurePosixPath

root = Path(sys.argv[1]).resolve()
expected = {
    "engineering": {"deslop", "modern-python", "simplify-code", "systematic-debugging"},
    "skill-authoring": {"agent-md-refactor", "effective-agent-skills", "improve-skill"},
    "tools-and-research": {"chrome-cdp", "handoff", "last30days", "marimo-notebook", "marimo-pair", "pi-custom-model", "terminal-session-control"},
    "visualization": {"archify", "drawio-skill", "excalidraw"},
    "workflow": {"capture-project-vision", "make-release", "merge-worktree", "orchestrate-implementation", "prototype-question", "review-codebase-architecture", "shape-design", "verification-before-completion", "write-implementation-plan"},
    "writing": {"doc-coauthoring", "documentation-writer", "humanizer"},
}

errors = []
skills_root = root / "skills"
skill_files = sorted(skills_root.rglob("SKILL.md"))
actual = {}
names = set()
for path in skill_files:
    relative = path.relative_to(skills_root)
    if len(relative.parts) != 3:
        errors.append(f"{relative}: expected skills/<category>/<name>/SKILL.md")
        continue
    category, leaf = relative.parts[:2]
    actual.setdefault(category, set()).add(leaf)
    lines = path.read_text().splitlines()
    if not lines or lines[0] != "---":
        errors.append(f"{path}: frontmatter must start on line 1")
        continue
    try:
        end = lines.index("---", 1)
    except ValueError:
        errors.append(f"{path}: frontmatter is not closed")
        continue
    fields = {}
    for line in lines[1:end]:
        if not line.strip():
            continue
        match = re.fullmatch(r"([a-z][a-z0-9-]*):\s*(.+)", line)
        if not match:
            errors.append(f"{path}: frontmatter values must be single-line: {line!r}")
            continue
        key, value = match.groups()
        if key in fields:
            errors.append(f"{path}: duplicate frontmatter key {key}")
        fields[key] = value.strip().strip("\"'")
    name = fields.get("name", "")
    description = fields.get("description", "")
    if name != leaf:
        errors.append(f"{path}: name {name!r} must match leaf directory {leaf!r}")
    if name in names:
        errors.append(f"duplicate skill name: {name}")
    names.add(name)
    if not description:
        errors.append(f"{path}: description must be non-empty")

if actual != expected:
    errors.append(f"catalog mismatch: expected {expected!r}, got {actual!r}")
if len(skill_files) != 29:
    errors.append(f"expected 29 skills, found {len(skill_files)}")
for removed in ("unslop", "improve-codebase-architecture"):
    if any(path.parent.name == removed for path in (root / "skills").rglob("SKILL.md")):
        errors.append(f"removed skill remains: {removed}")

routing = json.loads((root / "tests/routing_prompts.json").read_text())
if set(routing) != names:
    errors.append("routing prompts must cover every skill exactly once")
for name, cases in routing.items():
    if len(cases.get("positive", [])) < 3 or len(cases.get("negative", [])) < 2:
        errors.append(f"{name}: routing prompts require at least 3 positive and 2 negative cases")

# Relative Markdown links must resolve. Ignore examples inside code fences.
pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
markdown = [root / "README.md", root / "UPSTREAM_ADOPTION.md", root / "THIRD_PARTY_NOTICES.md"]
markdown.extend(
    path for path in (root / "skills").rglob("*.md")
    if "node_modules" not in path.parts
)
for path in sorted(markdown):
    in_fence = False
    for line_no, line in enumerate(path.read_text().splitlines(), 1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        for raw_target in pattern.findall(line):
            target = raw_target.strip().split()[0].strip("<>")
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            target = urllib.parse.unquote(target.split("#", 1)[0].split("?", 1)[0])
            if target and not (path.parent / target).exists():
                errors.append(f"{path.relative_to(root)}:{line_no} -> {raw_target}")

# Validate local provenance and find each owning skill through nested categories.
manifest = json.loads((root / "sources.json").read_text())
if manifest.get("version") != 2 or not isinstance(manifest.get("sources"), list) or not manifest["sources"]:
    errors.append("sources.json must contain a non-empty version 2 sources array")
else:
    seen = set()
    notice = (root / "THIRD_PARTY_NOTICES.md").read_text()
    for item in manifest["sources"]:
        required = {"local", "source", "repository", "branch", "commit", "license", "copyright", "mode"}
        if not required <= item.keys():
            errors.append(f"incomplete provenance item: {item!r}")
            continue
        if item["mode"] not in {"vendored", "adapted", "referenced"}:
            errors.append(f"invalid provenance mode: {item!r}")
        if not re.fullmatch(r"[0-9a-f]{40}", item["commit"]):
            errors.append(f"invalid commit: {item!r}")
        for field in ("local", "source"):
            value = item[field]
            pure = PurePosixPath(value)
            if not value or pure.is_absolute() or ".." in pure.parts or "\\" in value:
                errors.append(f"unsafe provenance {field}: {value!r}")
        local = (root / item["local"]).resolve()
        if not local.is_file():
            errors.append(f"missing provenance local file: {item['local']}")
            continue
        identity = (item["local"], item["repository"], item["commit"], item["source"])
        if identity in seen:
            errors.append(f"duplicate provenance relationship: {identity!r}")
        seen.add(identity)
        owner = next((parent / "SKILL.md" for parent in (local.parent, *local.parents) if (parent / "SKILL.md").is_file()), None)
        if owner is None:
            errors.append(f"no owning SKILL.md for {item['local']}")
        else:
            provenance_text = local.read_text(errors="ignore") + "\n" + owner.read_text(errors="ignore")
            if item["repository"] not in provenance_text or item["commit"] not in provenance_text:
                errors.append(f"owner lacks provenance pin for {item['local']}")
        if item["repository"] not in notice or item["commit"] not in notice:
            errors.append(f"notice lacks provenance pin for {item['repository']}@{item['commit']}")
        if item["mode"] == "vendored":
            for field in ("upstream_sha256", "local_sha256"):
                if not re.fullmatch(r"[0-9a-f]{64}", item.get(field, "")):
                    errors.append(f"invalid {field}: {item!r}")
            if hashlib.sha256(local.read_bytes()).hexdigest() != item.get("local_sha256"):
                errors.append(f"vendored local hash changed: {item['local']}")

if errors:
    raise SystemExit("\n".join(errors))
PY

for file in \
    skills/tools-and-research/chrome-cdp/scripts/cdp.mjs \
    skills/tools-and-research/last30days/scripts/last30days.py \
    skills/tools-and-research/marimo-notebook/references/REACTIVITY.md \
    skills/tools-and-research/marimo-pair/scripts/execute-code.sh \
    skills/visualization/archify/bin/archify.mjs \
    skills/visualization/drawio-skill/scripts/validate.py \
    skills/visualization/excalidraw/scripts/excalidraw_lib.py \
    skills/workflow/orchestrate-implementation/evals/evals.json \
    skills/workflow/review-codebase-architecture/references/html-report.md \
    skills/workflow/review-codebase-architecture/agents/openai.yaml \
    skills/skill-authoring/improve-skill/scripts/extract-session.js \
    skills/writing/humanizer/references/pattern-catalog.md; do
    test -f "$ROOT/$file" || fail "missing required asset: $file"
done

assert_contains "$ROOT/skills/engineering/simplify-code/SKILL.md" "Reuse"
assert_contains "$ROOT/skills/engineering/simplify-code/SKILL.md" "Quality"
assert_contains "$ROOT/skills/engineering/simplify-code/SKILL.md" "Efficiency"
assert_contains "$ROOT/skills/engineering/simplify-code/SKILL.md" "non-obvious why"
assert_contains "$ROOT/skills/engineering/simplify-code/SKILL.md" "reader load"
assert_contains "$ROOT/skills/engineering/simplify-code/SKILL.md" "behavior pin"
assert_contains "$ROOT/skills/engineering/simplify-code/SKILL.md" "subtract"
assert_contains "$ROOT/skills/engineering/deslop/SKILL.md" "behavior pin"
assert_contains "$ROOT/skills/engineering/deslop/SKILL.md" "legacy"
assert_contains "$ROOT/skills/workflow/verification-before-completion/SKILL.md" "same surface"
assert_contains "$ROOT/skills/workflow/verification-before-completion/SKILL.md" "compilation proves"
assert_contains "$ROOT/skills/engineering/systematic-debugging/SKILL.md" "disproven hypothesis"
assert_contains "$ROOT/skills/engineering/systematic-debugging/SKILL.md" "baseline"
assert_contains "$ROOT/skills/workflow/shape-design/SKILL.md" "data shape"
assert_contains "$ROOT/skills/workflow/shape-design/SKILL.md" "boundary"
assert_contains "$ROOT/skills/workflow/shape-design/SKILL.md" "idempotent"
assert_contains "$ROOT/skills/workflow/prototype-question/SKILL.md" "observable uncertainty"
assert_contains "$ROOT/skills/workflow/write-implementation-plan/SKILL.md" "runnable check"
assert_contains "$ROOT/skills/workflow/write-implementation-plan/SKILL.md" "removal condition"
assert_contains "$ROOT/skills/workflow/write-implementation-plan/SKILL.md" "smallest safe decomposition"
assert_contains "$ROOT/skills/workflow/orchestrate-implementation/SKILL.md" "smallest safe decomposition"
assert_contains "$ROOT/skills/workflow/orchestrate-implementation/SKILL.md" "review the diff"
assert_contains "$ROOT/skills/skill-authoring/effective-agent-skills/SKILL.md" "executable enforcement"
assert_contains "$ROOT/skills/skill-authoring/effective-agent-skills/SKILL.md" "routing"
assert_contains "$ROOT/skills/skill-authoring/improve-skill/SKILL.md" "pre-change"
assert_contains "$ROOT/skills/tools-and-research/marimo-pair/SKILL.md" "active runtime is the source of truth"
assert_contains "$ROOT/skills/tools-and-research/pi-custom-model/SKILL.md" "Never print"
assert_contains "$ROOT/skills/workflow/merge-worktree/SKILL.md" "Opening a PR never authorizes merging"
assert_contains "$ROOT/skills/workflow/orchestrate-implementation/SKILL.md" "test obligation"
assert_contains "$ROOT/skills/workflow/verification-before-completion/SKILL.md" "NO COMPLETION CLAIMS"
assert_contains "$ROOT/skills/writing/humanizer/SKILL.md" "pattern catalog"

bash -n "$ROOT/scripts/check-skill-sources.sh"
printf 'all skills valid\n'
