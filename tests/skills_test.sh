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

assert_not_contains() {
    ! grep -Fqi -- "$2" "$1" || fail "contradictory text in $1: $2"
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
    "skill-authoring": {"agent-md-refactor", "effective-agent-skills", "improve-skill", "workflow-from-chats"},
    "tools-and-research": {"chrome-cdp", "handoff", "last30days", "marimo-notebook", "marimo-pair", "pi-custom-model", "research", "terminal-session-control"},
    "visualization": {"archify", "drawio-skill", "excalidraw"},
    "workflow": {"capture-project-vision", "domain-modeling", "grilling", "make-release", "merge-worktree", "orchestrate-implementation", "planning-contract", "prototype-question", "review-codebase-architecture", "shape-design", "verification-before-completion", "write-implementation-plan"},
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
if len(skill_files) != 34:
    errors.append(f"expected 34 skills, found {len(skill_files)}")
for removed in ("unslop", "improve-codebase-architecture"):
    if any(path.parent.name == removed for path in (root / "skills").rglob("SKILL.md")):
        errors.append(f"removed skill remains: {removed}")

routing = json.loads((root / "tests/routing_prompts.json").read_text())
if set(routing) != names:
    errors.append("routing prompts must cover every skill exactly once")
for name, cases in routing.items():
    if len(cases.get("positive", [])) < 3 or len(cases.get("negative", [])) < 2:
        errors.append(f"{name}: routing prompts require at least 3 positive and 2 negative cases")

handoffs = json.loads((root / "tests/fixtures/orchestrator-skill-handoffs.json").read_text())
required_handoffs = {
    "prototype_choice_without_production_request",
    "explicit_production_request_after_design",
    "multi_context_without_map",
    "multi_context_with_map",
    "conflicting_single_multi_evidence",
    "unconfigured_single_context",
    "configured_single_context",
}
if set(handoffs) != required_handoffs:
    errors.append(f"orchestrator handoff fixture mismatch: expected {required_handoffs!r}, got {set(handoffs)!r}")
for name in ("multi_context_without_map", "configured_single_context", "unconfigured_single_context"):
    if name in handoffs and "files" not in handoffs[name]:
        errors.append(f"handoff fixture {name} must declare its repository file state")

# The lifecycle acceptance eval must be an executable native fixture, not prose
# that forbids the very skill and tools it claims to accept.
evals_path = root / "skills/workflow/orchestrate-implementation/evals/evals.json"
evals = json.loads(evals_path.read_text())
by_id = {item.get("id"): item for item in evals.get("evals", [])}
if sorted(by_id) != [1, 2, 3, 4]:
    errors.append(f"orchestrate evals must remain ids 1..4, got {sorted(by_id)!r}")
else:
    acceptance = by_id[4]
    joined = " ".join([acceptance.get("prompt", ""), acceptance.get("expected_output", "")]).lower()
    if "use an orchestration skill" in joined or "do not modify files" in joined:
        errors.append("eval id4 must not forbid the orchestration skill or file changes; it is an executable acceptance fixture")
    for token in ("disposable", "orchestrate-implementation", "subagent", "finalization", "digest", "candidate", "blocked", "pending", "fallback", "autonomous", "awaiting approval", "ownership"):
        if token not in joined:
            errors.append(f"eval id4 must declare the bounded native acceptance contract (missing {token!r})")
    fixture = (root / "skills/workflow/orchestrate-implementation/evals/fixtures/managed-lifecycle.md").read_text().lower()
    for token in ("pending", "blocked", "disposable", "digest", "evidence", "finalization", "autonomous", "awaiting approval", "configured locations", "before commit"):
        if token not in fixture:
            errors.append(f"managed-lifecycle fixture must declare the executable acceptance contract (missing {token!r})")
    for stale in ("all commits, refs, worktrees, and patches stay inside", "corrupt artifact must each abort before mutation", "init -q 2>/dev/null ||"):
        if stale in fixture:
            errors.append(f"managed-lifecycle fixture retains an incompatible boundary: {stale!r}")

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
    skills/workflow/orchestrate-implementation/evals/fixtures/managed-lifecycle.md \
    tests/orchestrator_handoff_test.sh \
    tests/fixtures/orchestrator-skill-handoffs.json \
    skills/workflow/review-codebase-architecture/references/html-report.md \
    skills/workflow/review-codebase-architecture/agents/openai.yaml \
    skills/skill-authoring/improve-skill/scripts/extract-session.js \
    skills/writing/humanizer/references/pattern-catalog.md; do
    test -f "$ROOT/$file" || fail "missing required asset: $file"
done

# Static contract assertions only; they are not behavioral skill-execution evidence.
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
assert_contains "$ROOT/skills/workflow/orchestrate-implementation/SKILL.md" "Durable handoff and recovery boundary"
assert_contains "$ROOT/skills/workflow/orchestrate-implementation/SKILL.md" "pinned named base"
assert_contains "$ROOT/skills/workflow/orchestrate-implementation/SKILL.md" "complete binary-capable patch"
assert_contains "$ROOT/skills/workflow/orchestrate-implementation/SKILL.md" "replacement patch supersedes"
assert_contains "$ROOT/skills/workflow/orchestrate-implementation/SKILL.md" "registered candidate worktree"
assert_not_contains "$ROOT/skills/workflow/orchestrate-implementation/SKILL.md" "review the worker path"
assert_not_contains "$ROOT/skills/workflow/orchestrate-implementation/SKILL.md" "cherry-pick worker commits only"
assert_contains "$ROOT/skills/workflow/orchestrate-implementation/references/pi-dispatch.md" 'pi-subagents` 0.66.0'
assert_contains "$ROOT/skills/workflow/orchestrate-implementation/references/pi-dispatch.md" 'set -euo pipefail'
assert_contains "$ROOT/skills/workflow/orchestrate-implementation/references/pi-dispatch.md" 'stop() {'
assert_contains "$ROOT/skills/workflow/orchestrate-implementation/references/pi-dispatch.md" 'approved lane base'
assert_contains "$ROOT/skills/workflow/orchestrate-implementation/references/pi-dispatch.md" 'never fall back to the parent'
# The old recipe called an undefined "stop", had no fail-fast, and overwrote existing pins.
assert_not_contains "$ROOT/skills/workflow/orchestrate-implementation/references/pi-dispatch.md" '&& stop'
assert_not_contains "$ROOT/skills/workflow/orchestrate-implementation/references/pi-dispatch.md" 'git update-ref "refs/heads/orchestrator/$run/base/$lane" "$base_sha"'
assert_not_contains "$ROOT/skills/workflow/orchestrate-implementation/references/pi-dispatch.md" 'cherry-picks only accepted commits'
assert_contains "$ROOT/skills/workflow/orchestrate-implementation/references/review-and-recovery.md" "git apply --check"
# Worker-path-only validation/review wording is contradicted by reconstruction.
assert_not_contains "$ROOT/skills/workflow/orchestrate-implementation/references/review-and-recovery.md" 'range in its managed worktree; never use'
assert_not_contains "$ROOT/skills/workflow/orchestrate-implementation/references/review-and-recovery.md" 'validation in each worker worktree matching'
assert_contains "$ROOT/skills/workflow/orchestrate-implementation/references/review-and-recovery.md" 'reconstructed tree'
# The blanket manual-worktree prohibition must be amended only for owned review/candidate checkouts.
assert_not_contains "$ROOT/skills/workflow/orchestrate-implementation/SKILL.md" 'never create nested or manually registered worktrees when managed child worktrees are available'
assert_contains "$ROOT/skills/workflow/orchestrate-implementation/SKILL.md" 'Registered parent-owned review and candidate checkouts'
assert_contains "$ROOT/skills/workflow/merge-worktree/SKILL.md" "parent-owned candidate worktree"
assert_contains "$ROOT/skills/workflow/prototype-question/references/ui.md" "shape-design"
assert_not_contains "$ROOT/skills/workflow/prototype-question/references/ui.md" "implement the selected variant in production"
assert_contains "$ROOT/skills/workflow/domain-modeling/SKILL.md" "docs/agents/domain.md"
assert_contains "$ROOT/skills/workflow/domain-modeling/SKILL.md" "Do not create a root"
# Root glossary creation is not restricted to unconfigured repos: a configured
# single-context repo also creates its first real glossary lazily.
assert_not_contains "$ROOT/skills/workflow/domain-modeling/SKILL.md" 'only for an unconfigured single-context project'
assert_contains "$ROOT/skills/workflow/domain-modeling/SKILL.md" 'configured single-context'
assert_contains "$ROOT/skills/workflow/domain-modeling/references/context-format.md" "CONTEXT-MAP.md"
assert_contains "$ROOT/skills/workflow/domain-modeling/references/context-format.md" "docs/agents/domain.md"
# The old reference fallback recreated a root glossary for configured multi-context projects.
assert_not_contains "$ROOT/skills/workflow/domain-modeling/references/context-format.md" 'If neither exists, create a root `CONTEXT.md` lazily when the first term is resolved'
assert_contains "$ROOT/skills/workflow/domain-modeling/references/context-format.md" 'do not create a root `CONTEXT.md` just because the map is absent'
assert_contains "$ROOT/tests/orchestrator_handoff_test.sh" "GIT binary patch"
assert_contains "$ROOT/tests/orchestrator_handoff_test.sh" "candidate missing from worktree registry"
assert_contains "$ROOT/skills/skill-authoring/effective-agent-skills/SKILL.md" "executable enforcement"
assert_contains "$ROOT/skills/skill-authoring/effective-agent-skills/SKILL.md" "routing"
assert_contains "$ROOT/skills/skill-authoring/improve-skill/SKILL.md" "pre-change"
assert_contains "$ROOT/skills/tools-and-research/marimo-pair/SKILL.md" "active runtime is the source of truth"
assert_contains "$ROOT/skills/tools-and-research/pi-custom-model/SKILL.md" "Never print"
assert_contains "$ROOT/skills/workflow/merge-worktree/SKILL.md" "Opening a PR never authorizes merging"
assert_contains "$ROOT/skills/workflow/orchestrate-implementation/SKILL.md" "test obligation"
assert_contains "$ROOT/skills/workflow/verification-before-completion/SKILL.md" "NO COMPLETION CLAIMS"
assert_contains "$ROOT/skills/writing/humanizer/SKILL.md" "pattern catalog"

# T1: the canonical, locally authored planning contract must exist, stay
# normative, and remain discoverable; consumers reference it in T2.
CONTRACT="$ROOT/skills/workflow/planning-contract/SKILL.md"
test -f "$CONTRACT" || fail "missing required skill: skills/workflow/planning-contract/SKILL.md"
assert_contains "$CONTRACT" "Contract version: 1"
assert_contains "$CONTRACT" "docs/research/"
assert_contains "$CONTRACT" "docs/adr/"
assert_contains "$CONTRACT" "docs/specs/"
assert_contains "$CONTRACT" "docs/plans/"
assert_contains "$CONTRACT" "docs/tickets/"
assert_contains "$CONTRACT" "docs/agents/artifacts.md"
assert_contains "$CONTRACT" "CONTEXT.md"
assert_contains "$CONTRACT" "declarative documentation"
assert_contains "$CONTRACT" "never an executable configuration file"
assert_contains "$CONTRACT" "Directory membership never grants approval"
assert_contains "$CONTRACT" "Scoped authority"
assert_contains "$CONTRACT" "Glossaries own terminology"
assert_contains "$CONTRACT" "capture checkpoint"
assert_contains "$CONTRACT" "Research is evidence"
assert_contains "$CONTRACT" "Execution readiness"
assert_contains "$CONTRACT" "compact plan"
assert_contains "$CONTRACT" "Tickets own the canonical task bodies"
assert_contains "$CONTRACT" "satisfied dependencies, stable consumed interfaces, and non-conflicting ownership"
assert_contains "$CONTRACT" "detect its absence"
assert_contains "$CONTRACT" "request installation"
assert_contains "$CONTRACT" "does not resolve skill-to-skill dependencies"
assert_contains "$CONTRACT" "unknown"
# The contract is locally authored; it must not claim a fake upstream origin.
assert_not_contains "$CONTRACT" "Adapted from"
assert_contains "$ROOT/README.md" "planning-contract"

bash -n "$ROOT/scripts/check-skill-sources.sh"
printf 'all skills valid\n'
