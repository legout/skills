#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
MANIFEST=${1:-"$ROOT/sources.json"}

python3 - "$ROOT" "$MANIFEST" <<'PY'
import json
import subprocess
import sys
from pathlib import Path

root = Path(sys.argv[1])
manifest_path = Path(sys.argv[2])
manifest = json.loads(manifest_path.read_text())
updates = 0
errors = 0

for item in manifest.get("sources", []):
    local = root / item["local"]
    pinned = item["commit"]
    branch = item.get("branch", "main")
    repository = item["repository"].rstrip("/")
    compare_base = repository.removesuffix(".git")

    if not local.is_file():
        print(f"ERROR {item['local']}: local file is missing")
        errors += 1
        continue

    try:
        result = subprocess.run(
            ["git", "ls-remote", repository, f"refs/heads/{branch}"],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        print(f"ERROR {item['local']}: cannot run git ls-remote: {exc}")
        errors += 1
        continue

    if result.returncode != 0 or not result.stdout.strip():
        detail = result.stderr.strip() or "no matching branch"
        print(f"ERROR {item['local']}: {detail}")
        errors += 1
        continue

    latest = result.stdout.split()[0]
    if latest == pinned:
        print(f"OK     {item['local']} @ {pinned[:12]}")
        continue

    updates += 1
    print(f"UPDATE {item['local']}: {pinned[:12]} -> {latest[:12]}")
    print(f"       {compare_base}/compare/{pinned}...{latest}")

if errors or updates:
    print(f"\n{errors} error(s), {updates} source update(s) available")
    sys.exit(1)

print(f"\nAll {len(manifest.get('sources', []))} pinned sources are current")
PY
