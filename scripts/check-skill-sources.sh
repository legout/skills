#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
MANIFEST=${1:-"$ROOT/sources.json"}

python3 - "$ROOT" "$MANIFEST" <<'PY'
import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path, PurePosixPath

root = Path(sys.argv[1]).resolve()
manifest_path = Path(sys.argv[2])
errors = 0


def fail(message):
    global errors
    print(f"ERROR {message}")
    errors += 1


def relative_path(value, field, index):
    if not isinstance(value, str) or not value:
        fail(f"source[{index}].{field} must be a non-empty string")
        return None
    if "\\" in value:
        fail(f"source[{index}].{field} must use forward slashes: {value!r}")
        return None
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts:
        fail(f"source[{index}].{field} must stay relative: {value!r}")
        return None
    return path


def github_repository(value, index):
    if not isinstance(value, str) or not value:
        fail(f"source[{index}].repository must be a non-empty string")
        return None
    repository = value[:-4] if value.endswith(".git") else value
    parsed = urllib.parse.urlparse(repository)
    parts = [part for part in parsed.path.split("/") if part]
    if (
        parsed.scheme != "https"
        or parsed.netloc != "github.com"
        or len(parts) != 2
        or parsed.query
        or parsed.fragment
    ):
        fail(f"source[{index}].repository must be https://github.com/<owner>/<repo>: {value!r}")
        return None
    github_path = "/".join(parts)
    return f"https://github.com/{github_path}", github_path


try:
    manifest = json.loads(manifest_path.read_text())
except (OSError, UnicodeError, json.JSONDecodeError) as exc:
    fail(f"cannot read {manifest_path}: {exc}")
    sys.exit(1)

if not isinstance(manifest, dict):
    fail("manifest root must be an object")
    sys.exit(1)
if manifest.get("version") != 2:
    fail("sources.json must have version 2")

items = manifest.get("sources")
if not isinstance(items, list) or not items:
    fail("sources must be a non-empty array")
    sys.exit(1)

required = {"local", "source", "repository", "branch", "commit", "license", "copyright", "mode"}
valid = []
seen = set()

for index, item in enumerate(items):
    if not isinstance(item, dict):
        fail(f"source[{index}] must be an object")
        continue

    missing = sorted(required - item.keys())
    if missing:
        fail(f"source[{index}] is missing: {', '.join(missing)}")
        continue

    local = relative_path(item["local"], "local", index)
    source = relative_path(item["source"], "source", index)
    repository = github_repository(item["repository"], index)

    for field in ("branch", "license", "copyright"):
        if not isinstance(item[field], str) or not item[field].strip():
            fail(f"source[{index}].{field} must be a non-empty string")

    branch = item["branch"]
    if isinstance(branch, str) and (
        not re.fullmatch(r"[A-Za-z0-9._/-]+", branch)
        or ".." in branch
        or "//" in branch
        or branch.startswith("/")
        or branch.endswith(("/", ".lock"))
    ):
        fail(f"source[{index}].branch is not a safe branch name: {branch!r}")

    commit = item["commit"]
    if not isinstance(commit, str) or not re.fullmatch(r"[0-9a-f]{40}", commit):
        fail(f"source[{index}].commit must be a lowercase 40-character SHA")

    mode = item["mode"]
    if not isinstance(mode, str) or mode not in {"vendored", "adapted", "referenced"}:
        fail(f"source[{index}].mode is invalid: {mode!r}")

    if mode == "vendored":
        for field in ("upstream_sha256", "local_sha256"):
            value = item.get(field)
            if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
                fail(f"source[{index}].{field} must be a lowercase SHA-256 for vendored content")

    if local is not None:
        local_file = (root / Path(*local.parts)).resolve()
        try:
            local_file.relative_to(root)
        except ValueError:
            fail(f"source[{index}].local escapes the repository: {item['local']!r}")
        else:
            if not local_file.is_file():
                fail(f"source[{index}].local is missing: {item['local']}")

    identity_values = (item["local"], item["repository"], item["commit"], item["source"])
    if all(isinstance(value, str) for value in identity_values):
        identity = identity_values
        if identity in seen:
            fail(f"duplicate relationship: {item['local']} <- {item['source']}")
        seen.add(identity)

    if local is not None and source is not None and repository is not None:
        normalized = dict(item)
        normalized["_local_file"] = local_file
        normalized["_repository"], normalized["_github_path"] = repository
        valid.append(normalized)

if errors:
    sys.exit(1)

for item in valid:
    encoded_source = urllib.parse.quote(item["source"], safe="/")
    url = f"https://raw.githubusercontent.com/{item['_github_path']}/{item['commit']}/{encoded_source}"
    request = urllib.request.Request(url, headers={"User-Agent": "legout-skills-source-check/2"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            upstream = response.read()
    except urllib.error.HTTPError as exc:
        fail(f"{item['local']} <- {item['source']}: pinned source returned HTTP {exc.code}")
        continue
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        fail(f"{item['local']} <- {item['source']}: cannot fetch pinned source: {exc}")
        continue

    if item["mode"] == "vendored":
        upstream_hash = hashlib.sha256(upstream).hexdigest()
        local_hash = hashlib.sha256(item["_local_file"].read_bytes()).hexdigest()
        if upstream_hash != item["upstream_sha256"]:
            fail(f"{item['local']} <- {item['source']}: upstream content hash changed unexpectedly")
        if local_hash != item["local_sha256"]:
            fail(f"{item['local']}: vendored local content differs from sources.json")

if errors:
    sys.exit(1)

head_env = os.environ.copy()
head_env["GIT_TERMINAL_PROMPT"] = "0"
head_env["GIT_ASKPASS"] = "/usr/bin/false"
heads = {}
for repository, branch in sorted({(item["_repository"], item["branch"]) for item in valid}):
    try:
        result = subprocess.run(
            ["git", "ls-remote", repository, f"refs/heads/{branch}"],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
            env=head_env,
        )
    except subprocess.TimeoutExpired:
        fail(f"{repository}#{branch}: git ls-remote timed out after 30 seconds")
        heads[(repository, branch)] = None
        continue
    except OSError as exc:
        fail(f"{repository}#{branch}: cannot run git ls-remote: {exc}")
        heads[(repository, branch)] = None
        continue

    if result.returncode != 0 or not result.stdout.strip():
        fail(f"{repository}#{branch}: {result.stderr.strip() or 'branch not found'}")
        heads[(repository, branch)] = None
    else:
        heads[(repository, branch)] = result.stdout.split()[0]

if errors:
    sys.exit(1)

drift = 0
groups = {}
for item in valid:
    key = (item["_repository"], item["branch"], item["commit"])
    groups.setdefault(key, []).append(item)

for (repository, branch, commit), group in sorted(groups.items()):
    head = heads[(repository, branch)]
    adopted = [item for item in group if item["mode"] != "referenced"]
    if head == commit:
        print(f"OK     {repository}#{branch} @ {commit[:12]} ({len(group)} relationship(s))")
    elif not adopted:
        print(f"PINNED reference {repository} @ {commit[:12]} (branch head {head[:12]})")
    else:
        drift += 1
        print(f"DRIFT  {repository}#{branch}: {commit[:12]} -> {head[:12]} ({len(adopted)} adopted relationship(s))")
        print(f"       {repository}/compare/{commit}...{head}")

if drift:
    print(f"\n{drift} adopted source group(s) moved; review before updating")
    sys.exit(1)

print(f"\nValidated {len(valid)} pinned source path(s) across {len(heads)} repository branch(es)")
PY
