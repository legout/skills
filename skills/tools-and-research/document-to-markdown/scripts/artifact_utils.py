"""Small shared artifact/provenance helpers; no parsing or semantic certification."""

import hashlib
import json
from datetime import UTC, datetime
from importlib.metadata import version


def require_pdf(parser, path):
    if not path.is_file() or path.suffix.lower() != ".pdf":
        parser.error("input must be an existing local .pdf file")
    return path.resolve()


def prepare_output(path):
    if path.exists() and (not path.is_dir() or any(path.iterdir())):
        raise SystemExit(
            f"Output is not an empty directory: {path}; choose a fresh path."
        )
    path.mkdir(parents=True, exist_ok=True)
    return path.resolve()


def source_hash(source):
    with source.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def write_run(output, source, engine, pages, seconds, settings, packages):
    metadata = {
        "source": str(source),
        "source_sha256": source_hash(source),
        "recorded_at": datetime.now(UTC).isoformat(),
        "engine": engine,
        "page_count": pages,
        "elapsed_seconds": round(seconds, 3),
        "settings": settings,
        "versions": {name: version(name) for name in packages},
        "remote_inference": False,
        "semantic_verification": "requires_source_review",
        "note": "Candidate extraction, not a verified transcription. Initialization/downloads are included in elapsed time.",
    }
    (output / "run.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def write_paged(output, pages):
    parts = []
    for page_no, markdown in pages:
        part = f"<!-- source page {page_no} -->\n\n{markdown}"
        (output / f"page-{page_no:03d}.md").write_text(part, encoding="utf-8")
        parts.append(part)
    (output / "document-paged.md").write_text(
        "\n\n---\n\n".join(parts), encoding="utf-8"
    )
