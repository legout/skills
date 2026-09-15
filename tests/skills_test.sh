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

recovery = (workflow / "references/review-and-recovery.md").read_text()
for rule in ("Disposition before repair", "One fix pass, one delta recheck", "No third round",
             "priorReviewSha..replacementReviewSha", "integration effects", "accept / fix / hand back / ask"):
    if rule not in recovery:
        errors.append(f"review-and-recovery.md: missing {rule!r}")

if errors:
    raise SystemExit("\n".join(errors))
print(f"validated {len(names)} skills")
PY
