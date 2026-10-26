"""Fails (exit 1) if tracked files contain an email, a phone number, a resume document, or anything under me/."""
import re
import subprocess
import sys

EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)*\.[A-Za-z]{2,}\b")
PHONE = re.compile(r"\(?\b\d{3}\)?[\s.-]?\d{3}[\s.-]\d{4}\b")
SAFE_EMAIL = re.compile(r"@(example\.(com|org|net)|users\.noreply\.github\.com|noreply\.anthropic\.com)$|^noreply@", re.I)
SAFE_PREFIXES = ("tests/",)
RESUME_EXT = (".pdf", ".doc", ".docx", ".rtf")
RESUME_OK_PREFIXES = ("tests/fixtures/", "templates/")
TEXT_EXT = (".md", ".txt", ".json", ".py", ".js", ".css", ".html", ".yml", ".yaml", ".toml", ".bat", ".sh")


def main() -> int:
    files = subprocess.run(["git", "ls-files"], capture_output=True, text=True, check=True).stdout.splitlines()
    bad = []
    for f in files:
        if f.startswith("me/"):
            bad.append(f"{f}: personal data folder is tracked")
            continue
        if f.lower().endswith(RESUME_EXT) and not f.startswith(RESUME_OK_PREFIXES):
            bad.append(f"{f}: document file (resume?) is tracked; keep resumes in me/")
            continue
        if f.startswith(SAFE_PREFIXES) or not f.endswith(TEXT_EXT):
            continue
        try:
            text = open(f, encoding="utf-8").read()
        except (OSError, UnicodeDecodeError):
            continue
        if any(not SAFE_EMAIL.search(m) for m in EMAIL.findall(text)):
            bad.append(f"{f}: contains an email address")
        if PHONE.search(text):
            bad.append(f"{f}: contains a phone number")
    print("\n".join(bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
