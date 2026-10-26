"""Tells /update whether upstream changes touch the person's own me/ folder. Stdlib only.

CLI: py -3 -X utf8 tools/update_check.py   (reads `git diff --name-only HEAD..upstream/main`)
Exit 0 if upstream leaves me/ alone, 1 if it touches me/, 2 if the diff could not be read.
"""
from __future__ import annotations

import subprocess
import sys


def touches_me(paths: list[str]) -> bool:
    for raw in paths:
        p = raw.strip().replace("\\", "/")
        while p.startswith("./"):
            p = p[2:]
        if p == "me" or p.startswith("me/"):
            return True
    return False


def main() -> int:
    result = subprocess.run(
        ["git", "diff", "--name-only", "HEAD..upstream/main"],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode != 0:
        print(f"could not read upstream diff: {result.stderr.strip()}", file=sys.stderr)
        return 2
    paths = [line for line in result.stdout.splitlines() if line.strip()]
    if touches_me(paths):
        for p in paths:
            if touches_me([p]):
                print(f"upstream touches personal data: {p}")
        return 1
    print("upstream does not touch me/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
