"""Conservative tracked-file checks; complements GitHub secret scanning."""

import re
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = [
    re.compile(r"gh[pousr]_" + r"[A-Za-z0-9]{30,}"),
    re.compile(r"github_pat_" + r"[A-Za-z0-9_]{40,}"),
    re.compile(r"AKIA" + r"[A-Z0-9]{16}"),
    re.compile(r"-----BEGIN " + r"(?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
]
PRIVATE = {".env", "config.local.json", "web/data.js"}
PRIVATE_PREFIXES = ("evidence/", "models/", "datasets/", "runtime/", "validation/")


def audit(paths):
    failures = []
    for relative in paths:
        if relative in PRIVATE or relative.startswith(PRIVATE_PREFIXES):
            failures.append(relative + ": private path")
            continue
        path = ROOT / relative
        if not path.is_file():
            continue
        text = path.read_bytes().decode("utf-8", errors="ignore")
        if any(pattern.search(text) for pattern in PATTERNS):
            failures.append(relative + ": potential credential")
    return failures


def main():
    value = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT)
    paths = [p for p in value.decode("utf-8").split("\0") if p]
    failures = audit(paths)
    for failure in failures:
        print(failure)
    print("Public file audit:", len(paths), "tracked paths,", len(failures), "findings")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
