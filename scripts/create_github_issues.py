#!/usr/bin/env python3
"""Create the prioritized GitHub Issues described in docs/issue-backlog.md.

Run this from a terminal where `gh auth status` succeeds:
    python3 scripts/create_github_issues.py --apply
Without --apply, the script only prints the issues it would create.
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKLOG = ROOT / "docs" / "issue-backlog.md"
SECTION_PATTERN = re.compile(r"^## (P[0-3]) — (.+)$", re.MULTILINE)


def parse_issues(markdown: str):
    matches = list(SECTION_PATTERN.finditer(markdown))
    return [
        (match.group(1), match.group(2), markdown[match.end(): matches[index + 1].start() if index + 1 < len(matches) else None].strip())
        for index, match in enumerate(matches)
    ]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="GitHub Issueを実際に作成する")
    args = parser.parse_args()
    issues = parse_issues(BACKLOG.read_text(encoding="utf-8"))

    if not issues:
        raise RuntimeError("Issueバックログを読み取れませんでした")

    for priority, title, body in issues:
        full_title = f"[{priority}] {title}"
        if not args.apply:
            print(full_title)
            continue
        result = subprocess.run(
            ["gh", "issue", "create", "--title", full_title, "--body", body],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        if result.returncode:
            print(result.stderr, file=sys.stderr)
            raise SystemExit(result.returncode)
        print(result.stdout.strip())


if __name__ == "__main__":
    main()
