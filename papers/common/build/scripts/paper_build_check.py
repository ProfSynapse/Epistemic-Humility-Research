#!/usr/bin/env python3
"""Pre-build checks for Epistemic-Humility paper manuscripts.

Usage: paper_build_check.py <paper-dir>   (dir containing manuscript.md)

Fails (exit 1) on:
  1. Unresolved figure references — a figure file cited in the markdown
     (code-span `fig-*.png` / markdown image) that does not exist on disk.
  2. Markdown link rot within the repo — a relative link target that does
     not exist (checked relative to the paper dir, then the repo root).
  3. Em dashes in manuscript prose (series prose rule; fenced code excluded).
  4. The phrase "load-bearing" (series prose rule; case-insensitive).

Warns (does not fail) on figure files present in figures/ but never cited.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

FIG_EXTS = (".png", ".svg", ".pdf", ".jpg", ".jpeg")
CODE_SPAN = re.compile(r"`([^`]+)`")
MD_IMAGE = re.compile(r"!\[[^\]]*\]\(([^)\s]+)")
MD_LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)\)")
FENCE = re.compile(r"^\s*(```|~~~)")


def repo_root(start: Path) -> Path:
    for p in [start, *start.parents]:
        if (p / ".git").exists():
            return p
    return start


def prose_lines(lines: list[str]):
    """Yield (lineno, line) outside fenced code blocks."""
    in_fence = False
    for n, line in enumerate(lines, 1):
        if FENCE.match(line):
            in_fence = not in_fence
            continue
        if not in_fence:
            yield n, line


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    paper_dir = Path(sys.argv[1]).resolve()
    manuscript = paper_dir / "manuscript.md"
    if not manuscript.exists():
        print(f"FAIL: no manuscript.md in {paper_dir}")
        return 1
    root = repo_root(paper_dir)
    text = manuscript.read_text(encoding="utf-8")
    lines = text.split("\n")
    failures: list[str] = []
    warnings: list[str] = []

    # --- 1. figure references -------------------------------------------
    cited: set[str] = set()
    for n, line in prose_lines(lines):
        candidates = [m.group(1) for m in CODE_SPAN.finditer(line)]
        candidates += [m.group(1) for m in MD_IMAGE.finditer(line)]
        for ref in candidates:
            if not ref.lower().endswith(FIG_EXTS):
                continue
            cited.add(Path(ref).name)
            if "/" in ref:
                ok = (paper_dir / ref).exists() or (root / ref).exists()
            else:
                ok = (paper_dir / "figures" / ref).exists()
            if not ok:
                failures.append(f"line {n}: figure cited but not found: {ref}")

    fig_dir = paper_dir / "figures"
    if fig_dir.is_dir():
        for f in sorted(fig_dir.iterdir()):
            if f.suffix.lower() in FIG_EXTS and f.name not in cited:
                warnings.append(f"figures/{f.name} exists but is never cited")

    # --- 2. relative link rot -------------------------------------------
    for n, line in prose_lines(lines):
        for m in MD_LINK.finditer(line):
            target = m.group(1)
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            path = target.split("#", 1)[0]
            if not path:
                continue
            if not ((paper_dir / path).exists() or (root / path).exists()):
                failures.append(f"line {n}: link target not found: {target}")

    # --- 3. em dashes in prose ------------------------------------------
    for n, line in prose_lines(lines):
        if "—" in line:
            failures.append(f"line {n}: em dash in prose: {line.strip()[:80]}")

    # --- 4. banned phrase -----------------------------------------------
    for n, line in prose_lines(lines):
        if "load-bearing" in line.lower():
            failures.append(f"line {n}: banned phrase 'load-bearing': "
                            f"{line.strip()[:80]}")

    # --- report ----------------------------------------------------------
    for w in warnings:
        print(f"WARN: {w}")
    if failures:
        for f in failures:
            print(f"FAIL: {f}")
        print(f"\ncheck FAILED: {len(failures)} problem(s) in {manuscript}")
        return 1
    print(f"check PASSED: {manuscript} "
          f"({len(cited)} figure refs resolved, {len(warnings)} warning(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
