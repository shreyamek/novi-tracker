"""Render a local HTML file to PDF with the Chrome or Edge already installed. Stdlib only.

Usage: py -3 -X utf8 tools/render_pdf.py <input.html> <output.pdf>
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


class BrowserNotFound(RuntimeError):
    pass


def _candidates() -> list[str]:
    paths: list[str] = []
    for env in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA"):
        base = os.environ.get(env)
        if base:
            paths += [
                os.path.join(base, "Google", "Chrome", "Application", "chrome.exe"),
                os.path.join(base, "Microsoft", "Edge", "Application", "msedge.exe"),
            ]
    paths += [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    ]
    for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "microsoft-edge"):
        found = shutil.which(name)
        if found:
            paths.append(found)
    return paths


def find_browser() -> str:
    for path in _candidates():
        if os.path.isfile(path):
            return path
    raise BrowserNotFound(
        "No Chrome or Edge found. Install Google Chrome or Microsoft Edge, then run this again. "
        "Searched the standard Windows, Mac and Linux install locations."
    )


def render(html_path: str | Path, pdf_path: str | Path) -> Path:
    html = Path(html_path).resolve()
    pdf = Path(pdf_path).resolve()
    if not html.is_file():
        raise FileNotFoundError(f"HTML file not found: {html}")
    pdf.parent.mkdir(parents=True, exist_ok=True)
    browser = find_browser()
    cmd = [
        browser,
        "--headless",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={pdf}",
        html.as_uri(),
    ]
    subprocess.run(cmd, check=True, capture_output=True, timeout=120)
    if not pdf.is_file() or pdf.stat().st_size == 0:
        raise RuntimeError(f"Browser ran but no PDF was written to {pdf}")
    return pdf


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: render_pdf.py <input.html> <output.pdf>", file=sys.stderr)
        return 2
    try:
        out = render(argv[0], argv[1])
    except (BrowserNotFound, FileNotFoundError, RuntimeError, subprocess.SubprocessError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
