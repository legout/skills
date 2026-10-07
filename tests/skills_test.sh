#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)

python3 - "$ROOT" <<'PY'
import re
import sys
import urllib.parse
from pathlib import Path

root = Path(sys.argv[1]).resolve()
skills_root = root / "skills"
errors = []

source_check = (root / "scripts/check-skill-sources.sh").read_text()
for rule in (
    "--strict-upstream",
    "SKILL_SOURCE_CHECK_STRICT_UPSTREAM",
    "pinned-source integrity passed; branch drift is informational",
):
    if rule not in source_check:
        errors.append(f"check-skill-sources.sh: missing drift policy {rule!r}")
names = set()

# Catch malformed catalog versions and missing release notes before publishing.
try:
    version = (root / "VERSION").read_text()
    if not re.fullmatch(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\n?", version):
        errors.append("VERSION: expected one stable MAJOR.MINOR.PATCH version without a v prefix")
    changelog = (root / "CHANGELOG.md").read_text()
    if "## Unreleased" not in changelog.splitlines():
        errors.append("CHANGELOG.md: missing Unreleased section")
except OSError as exc:
    errors.append(f"catalog versioning: {exc}")

for path in sorted(skills_root.rglob("SKILL.md")):
    relative = path.relative_to(skills_root)
    if len(relative.parts) != 3:
        errors.append(f"{relative}: expected skills/<category>/<name>/SKILL.md")
        continue

    lines = path.read_text().splitlines()
    if not lines or lines[0] != "---":
        errors.append(f"{relative}: frontmatter must start on line 1")
        continue
    try:
        end = lines.index("---", 1)
    except ValueError:
        errors.append(f"{relative}: frontmatter is not closed")
        continue

    fields = {}
    for line in lines[1:end]:
        if not line.strip():
            continue
        match = re.fullmatch(r"([a-z][a-z0-9-]*):\s*(.+)", line)
        if not match:
            errors.append(f"{relative}: invalid single-line frontmatter: {line!r}")
            continue
        key, value = match.groups()
        fields[key] = value.strip().strip("\"'")

    leaf = relative.parts[-2]
    name = fields.get("name")
    if name != leaf:
        errors.append(f"{relative}: name {name!r} must match {leaf!r}")
    if not fields.get("description"):
        errors.append(f"{relative}: description must be non-empty")
    if name in names:
        errors.append(f"duplicate skill name: {name}")
    names.add(name)

if not names:
    errors.append("no skills found")

link_pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
markdown = [root / "README.md", *skills_root.rglob("*.md")]
for path in sorted(markdown):
    in_fence = False
    for line_no, line in enumerate(path.read_text().splitlines(), 1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        for raw_target in link_pattern.findall(line):
            target = raw_target.strip().split()[0].strip("<>")
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            target = urllib.parse.unquote(target.split("#", 1)[0].split("?", 1)[0])
            if target and not (path.parent / target).exists():
                errors.append(f"{path.relative_to(root)}:{line_no}: missing {target}")

# Fresh-context prompts must carry the gates, not merely link to a rules file.
# These pin delivery and loop scope; model behavior is exercised by the eval fixture.
workflow = skills_root / "workflow/orchestrate-implementation"
for relative in (
    "workflow/orchestrate-implementation/references/pi-dispatch.md",
    "engineering/simplify-code/SKILL.md",
):
    text = (skills_root / relative).read_text()
    start = text.find("<!-- reviewer-contract:start -->")
    end = text.find("<!-- reviewer-contract:end -->", start)
    if start < 0 or end < 0:
        errors.append(f"{relative}: missing inline reviewer contract")
        continue
    contract = text[start:end]
    for rule in (
        "named requirement or written rule", "caused or worsened",
        "real callers, inputs, and environment", "proportionate response",
        "written conventions are binding", "taste never blocks",
        "untrusted or external input", "credentials", "auth", "dependency changes",
        "named asset", "realistic attacker", "attack path",
        "stolen secrets, broken TLS, malicious admins", "security: n/a", "unverified",
        "Test requests are findings", "Coverage percentage", "pass or fix-first",
        "Do not fix", "one line", "Then stop",
    ):
        if rule not in contract:
            errors.append(f"{relative}: reviewer prompt missing {rule!r}")

for name in ("SKILL.md", "references/pi-dispatch.md", "references/review-and-recovery.md"):
    text = (workflow / name).read_text()
    if "re-review the complete replacement range" in text or "review the complete replacement range" in text:
        errors.append(f"{name}: reconstruction still forces a full re-review")

# Verified checks may be reused only on an equivalent acceptance surface.
text = (workflow / "SKILL.md").read_text()
for rule in ("Reuse verified focused-check evidence", "exact tree and relevant environment match"):
    if rule not in text:
        errors.append(f"SKILL.md: missing validation reuse gate {rule!r}")

# A pane launch must not mistake an existing session for a fresh worker, and
# CLI-only Paseo launches must not wait for unavailable parent callbacks.
backend_contracts = {
    "references/herdr-dispatch.md": ("action: \"list-cwd\"", "focus: false", "openedProjectPane", "returned paneId", "fresh roster", "before sending the mutation brief"),
    "references/paseo-dispatch.md": ("projectPath", "branchName", "Agent-scoped MCP", "CLI/top-level", "paseo wait"),
    "references/manifest-and-briefs.md": ("outside every disposable worker worktree", "git diff --no-ext-diff --no-textconv --binary --full-index", "Before parent-requested cleanup", "Native finalization may precede parent reconstruction"),
    "references/pi-dispatch.md": ("workflow: true",),
}
for name, rules in backend_contracts.items():
    text = (workflow / name).read_text()
    for rule in rules:
        if rule not in text:
            errors.append(f"{name}: missing backend contract {rule!r}")
if "`workflowScript`" in (workflow / "references/pi-dispatch.md").read_text():
    errors.append("pi-dispatch.md: removed workflowScript parameter")

# Ordinary persistence must not regress to capture-only while narrower scopes survive.
second_brain = skills_root / "tools-and-research/second-brain"
second_brain_text = (second_brain / "SKILL.md").read_text()
for rule in (
    "Capture is not integration", "## Completion contract", "explicitly deferred",
    "capture-only", "Read-only maintenance never authorizes writes or synthesis",
    "`add` and `idea` always write to `notes/`", "`page` selects the maintained folder",
    "sources/YYYY-MM-DD/slug.md", "generated.at", "Existing flat notes and captures",
    "Existing project files—including files under `data/`—stay in place",
    "source captures have no lifecycle `status`", "`verified` is separate trust metadata",
    "`--archive-original` explicitly preserves an eligible new asset",
    "complete page body", "--expect-sha256", "--supersedes",
):
    if rule not in second_brain_text:
        errors.append(f"second-brain: missing persistence contract {rule!r}")

recovery = (workflow / "references/review-and-recovery.md").read_text()
for rule in ("Disposition before repair", "One fix pass, one delta recheck", "No third round",
             "priorReviewSha..replacementReviewSha", "integration effects", "accept / fix / hand back / ask"):
    if rule not in recovery:
        errors.append(f"review-and-recovery.md: missing {rule!r}")

if errors:
    raise SystemExit("\n".join(errors))
print(f"validated {len(names)} skills")
PY

python3 "$ROOT/skills/tools-and-research/second-brain/scripts/sb.py" selftest
