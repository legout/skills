# Tier 2 — Transcribe one page image via the company-internal multimodal endpoint.
# Run: uv run scripts/vlm_page.py page.png page.md
# env: OPENAI_BASE_URL + OPENAI_API_KEY (internal gateway), DOC2MD_VLM_MODEL (default gpt-5.6-luna)
# /// script
# requires-python = ">=3.10"
# dependencies = ["openai"]
# ///
import base64
import os
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlparse

from openai import OpenAI  # type: ignore[import]

PROMPT = (
    "Transcribe this page exactly as Markdown. Preserve headings, lists, reading order, "
    "and tables as GFM tables. Mark unreadable text as [illegible]. "
    "Do not correct, translate, or invent content."
)


def main() -> None:
    if len(sys.argv) < 3:
        sys.exit("usage: vlm_page.py page.png page.md")
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    if src.resolve() == dst.resolve():
        sys.exit("vlm_page: input and output must be different files")
    tmp_out = None
    try:
        base_url = os.environ["OPENAI_BASE_URL"]
        parsed = urlparse(base_url)
        host = (parsed.hostname or "").lower()
        if parsed.scheme != "https" or not (host == "siemens.com" or host.endswith(".siemens.com")):
            raise ValueError("OPENAI_BASE_URL must be an HTTPS endpoint below siemens.com")
        client = OpenAI(base_url=base_url, api_key=os.environ["OPENAI_API_KEY"])
        model = os.environ.get("DOC2MD_VLM_MODEL", "gpt-5.6-luna")  # alt: qwen-3.8-27b
        img = base64.b64encode(src.read_bytes()).decode()
        r = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img}"}},
                {"type": "text", "text": PROMPT},
            ]}],
        )
        content = r.choices[0].message.content
        if not isinstance(content, str) or not content.strip():
            raise ValueError("model returned no transcription")
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=dst.parent,
                                         prefix=f".{dst.name}.", delete=False) as out:
            tmp_out = Path(out.name)
            out.write(content)
        tmp_out.replace(dst)
    except Exception as exc:  # CLI-Grenze: klare Meldung statt Traceback
        if tmp_out:
            tmp_out.unlink(missing_ok=True)
        sys.exit(f"vlm_page: {exc}")


if __name__ == "__main__":
    main()
