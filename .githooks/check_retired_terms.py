#!/usr/bin/env python3
"""Commit-time lint: retired terminology must not enter papers/ or docs/ prose.

The program terminology SSOT is papers/common/terminology.md. When a ruling
retires a term, add it to RETIRED_TERMS here. The lint scans only STAGED
markdown files under papers/ and docs/ (never experiments/ or archive/, where
signed and historical text is frozen and legitimately carries old working
labels). Matches inside backticks are allowed: governed identifiers (slugs,
filenames, config keys) stay verbatim and are cited in code spans.

A line can be explicitly exempted with the marker `terminology-ok` in an HTML
comment on that line, for the rare case of prose ABOUT a retired term (for
example the terminology table itself).

Exit 1 with a per-line report on any hit; exit 0 otherwise.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

# term -> ruling note shown in the failure message
RETIRED_TERMS = {
    "caution gate": "retired 2026-08-10; renders as 'refusal axis' (paper 3 construct) or operational description",
    "caution axis": "retired 2026-08-10; renders as 'refusal axis' (paper 3 construct) or operational description",
    "caution install": "retired 2026-08-10; renders as 'abstention install'",
    "caution snap": "retired 2026-08-10; renders as 'answerability-gated abstention snap'",
}

SCAN_PREFIXES = ("papers/", "docs/")
EXEMPT_MARKER = "terminology-ok"

_BACKTICK_SPAN = re.compile(r"`[^`]*`")


def staged_markdown_files() -> list[str]:
    out = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return [
        f
        for f in out.splitlines()
        if f.endswith(".md") and f.startswith(SCAN_PREFIXES)
    ]


def main() -> int:
    patterns = {
        term: re.compile(r"\b" + re.escape(term).replace(r"\ ", r"[\s-]+") + r"\b", re.IGNORECASE)
        for term in RETIRED_TERMS
    }
    problems: list[str] = []
    for rel in staged_markdown_files():
        path = Path(rel)
        if not path.exists():
            continue
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if EXEMPT_MARKER in line:
                continue
            stripped = _BACKTICK_SPAN.sub("", line)
            for term, pat in patterns.items():
                if pat.search(stripped):
                    problems.append(
                        f"{rel}:{lineno}: retired term '{term}' ({RETIRED_TERMS[term]})"
                    )
    if problems:
        print("check_retired_terms: FAILED", file=sys.stderr)
        for p in problems:
            print(f"  {p}", file=sys.stderr)
        print(
            "  Retired terms stay verbatim only inside backticked governed "
            "identifiers or on lines carrying the terminology-ok marker. "
            "SSOT: papers/common/terminology.md",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
