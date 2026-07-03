#!/usr/bin/env python3
"""Regenerate the amendment-status index inside TODO.md.

Scans experiment/protocol/*.md, reads each doc's own ``Status:`` line and any
``## 8. Result`` / ``## Result`` / ``VERDICT:`` verdict, classifies the status
into a small fixed vocabulary, and rewrites the fenced GENERATED block in
TODO.md. Everything outside the fence (the hand-curated prioritized backlog and
any prose) is preserved verbatim, so the file is safe to regenerate.

Stdlib only, deterministic, idempotent. See docs/backlog/PLAN.md for design.

Usage:
    python3 bin/build_backlog_index.py --write   # rewrite TODO.md in place
    python3 bin/build_backlog_index.py --check    # exit 1 if TODO.md is stale
    python3 bin/build_backlog_index.py            # print the block to stdout
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PROTOCOL_DIR = REPO_ROOT / "experiment" / "protocol"
TODO_PATH = REPO_ROOT / "TODO.md"

BEGIN_MARKER = "<!-- BEGIN GENERATED: amendment-index (do not edit by hand) -->"
END_MARKER = "<!-- END GENERATED: amendment-index -->"

# Status-line prefix -> normalized bucket. Ordered: first match wins, so more
# specific prefixes ("NOT SIGNED") must precede looser ones ("SIGNED").
STATUS_RULES: list[tuple[str, str]] = [
    ("RESOLVED", "RESOLVED"),
    ("COMPLETE", "RESOLVED"),
    ("SHELVED", "SHELVED"),
    ("DEPRECATED", "SHELVED"),
    ("NOT SIGNED", "DRAFT"),
    ("DRAFT", "DRAFT"),
    ("READY FOR", "SIGNED"),
    ("PRE-REGISTERED", "SIGNED"),
    ("SIGNED", "SIGNED"),
]

# Verdict tokens we surface (searched in the Status line, and in the first few
# lines of a Result/Verdict section). Order = reporting priority.
VERDICT_TOKENS = [
    "FALSIFIED",
    "SUCCESS",
    "POSITIVE",
    "NEGATIVE",
    "PASS",
    "FAIL",
    "AMBIGUOUS",
]

# Sort order for the buckets in the rendered table.
BUCKET_ORDER = {"SIGNED": 0, "DRAFT": 1, "RESOLVED": 2, "SHELVED": 3}


def _amendment_sort_key(letter: str) -> tuple[int, str]:
    """Single letters (A..Z) before double letters (AA, AB, ...), then alpha."""
    return (len(letter), letter)


def parse_status_line(text: str) -> str:
    """Return the raw text following the first ``Status:`` marker, or ''."""
    m = re.search(r"^\*{0,2}Status:?\*{0,2}\s*(.+)$", text, re.MULTILINE)
    return m.group(1).strip() if m else ""


def classify_status(status_line: str) -> str:
    # Only the leading status keyword region is authoritative; the trailing
    # rationale often quotes user text ("...draft amendment...") that would leak
    # keywords into the classifier. Cut at the first date, em-dash, or paren.
    head = re.split(r"\s+—|\s+\(|\s+\d{4}-\d{2}-\d{2}|\.\s", status_line, maxsplit=1)[0]
    upper = head.upper()
    for prefix, bucket in STATUS_RULES:
        if prefix in upper:
            return bucket
    return "UNKNOWN"


def _token_in(haystack: str) -> str:
    """Return the first VERDICT_TOKENS match in ``haystack`` (already upper)."""
    # "FALSIFIED", or a numbered kill-condition that FIRED ("FALSIFIER-1"), reads
    # as FALSIFIED — but "falsifier dead / did not fire" is the opposite and must
    # not match, so guard against those phrasings first.
    if "FALSIFIED" in haystack or re.search(r"FALSIFIER[-\s]?\d", haystack):
        if not re.search(r"FALSIFIER\s+(?:DEAD|DID NOT|DIDN'T|NOT? FIRE|NEVER)", haystack):
            return "FALSIFIED"
    for token in VERDICT_TOKENS:
        if token in haystack:
            return token if token != "AMBIGUOUS" else "ambiguous"
    return ""


def extract_verdict(text: str, status_line: str) -> str:
    """Find a verdict token declared by *this* doc.

    Only lines that DECLARE a verdict count: a ``## Result`` / ``### Verdict``
    section header, or a line whose verdict marker sits at the start ("VERDICT:",
    "**...verdict...:**", "Stage-N verdict ...:"). The token must appear AFTER
    the marker's colon, on the same line — this excludes cross-references to
    another amendment's result (e.g. "The AB verdict is ...-negative" in the AD
    doc) and prose that merely names a token.
    """
    # 1) The Status line itself may carry the verdict (e.g. "RESOLVED — SUCCESS").
    hit = _token_in(status_line.upper())
    if hit:
        return hit

    for line in text.splitlines():
        stripped = line.strip()
        # Section headers: "## 8. Result ...", "### Verdict (date): TOKEN".
        m = re.match(r"#{1,6}\s*(?:8\.?\s*)?(?:Result|Verdict)\b(.*)$", stripped, re.I)
        if m:
            hit = _token_in(m.group(1).upper())
            if hit:
                return hit
            continue
        # Line-leading verdict declarations only (marker within the first ~40
        # chars), so "The AB verdict is ..." (a cross-ref) does not qualify.
        m = re.match(
            r"[\*_\s]*(?:stage-\d+\s+)?verdict\b[^:]{0,60}:(.*)$", stripped, re.I
        )
        if m:
            hit = _token_in(m.group(1).upper())
            if hit:
                return hit
    return ""


def extract_title(text: str, fallback: str) -> str:
    m = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    if not m:
        return fallback
    title = m.group(1).strip()
    # Strip the leading "Amendment X — " / "Protocol Amendment X: " prefix; the
    # letter is already its own column.
    title = re.sub(
        r"^(?:Protocol\s+)?Amendment\s+[A-Z]{1,2}\s*[—:\-]\s*",
        "",
        title,
    )
    return title


def amendment_letter(filename: str) -> str | None:
    m = re.match(r"AMENDMENT-([A-Z]{1,2})-", filename)
    return m.group(1) if m else None


def collect() -> list[dict]:
    rows = []
    for path in sorted(PROTOCOL_DIR.glob("AMENDMENT-*.md")):
        letter = amendment_letter(path.name)
        if letter is None:
            continue
        text = path.read_text(encoding="utf-8")
        status_line = parse_status_line(text)
        rows.append(
            {
                "letter": letter,
                "title": extract_title(text, path.stem),
                "bucket": classify_status(status_line),
                "verdict": extract_verdict(text, status_line),
                "path": path.relative_to(REPO_ROOT).as_posix(),
            }
        )
    rows.sort(
        key=lambda r: (
            BUCKET_ORDER.get(r["bucket"], 99),
            _amendment_sort_key(r["letter"]),
        )
    )
    return rows


def render_block(rows: list[dict]) -> str:
    counts: dict[str, int] = {}
    for r in rows:
        counts[r["bucket"]] = counts.get(r["bucket"], 0) + 1
    count_line = " · ".join(
        f"{b}: {counts[b]}" for b in ["SIGNED", "DRAFT", "RESOLVED", "SHELVED"]
        if b in counts
    )
    if any(r["bucket"] == "UNKNOWN" for r in rows):
        count_line += f" · UNKNOWN: {counts.get('UNKNOWN', 0)}"

    lines = [
        BEGIN_MARKER,
        "",
        "## Amendment status index",
        "",
        "_Generated by `bin/build_backlog_index.py` from the `Status:` line of "
        "each `experiment/protocol/AMENDMENT-*.md`. Do not edit inside this "
        "block by hand — re-run the script instead._",
        "",
        f"Totals: {len(rows)} amendment docs — {count_line}.",
        "",
        "| Amd | Status | Verdict | Title | Doc |",
        "|-----|--------|---------|-------|-----|",
    ]
    for r in rows:
        verdict = r["verdict"] or "—"
        lines.append(
            f"| {r['letter']} | {r['bucket']} | {verdict} | {r['title']} "
            f"| [{r['path'].split('/')[-1]}]({r['path']}) |"
        )
    lines += ["", END_MARKER]
    return "\n".join(lines)


def splice(existing: str, block: str) -> str:
    """Replace the fenced block in ``existing``; if absent, prepend it."""
    if BEGIN_MARKER in existing and END_MARKER in existing:
        pre = existing.split(BEGIN_MARKER)[0]
        post = existing.split(END_MARKER, 1)[1]
        return f"{pre}{block}{post}"
    # No fence yet: put the generated block first, then the old content under a
    # curated heading so nothing is lost.
    return f"{block}\n\n{existing.lstrip()}"


def selftest() -> int:
    """Exercise the parsing edge cases that bit us during authoring."""
    cases_status = [
        ('SIGNED — user-authorized ("draft amendment/session/")', "SIGNED"),
        ("DRAFT / NOT SIGNED", "DRAFT"),
        ("RESOLVED — SUCCESS (2026-06-30)", "RESOLVED"),
        ("COMPLETE (2026-06-30) — gates LOCKED", "RESOLVED"),
        ("SHELVED (2026-06-30) — signed but DEFERRED", "SHELVED"),
        ("PRE-REGISTERED (2026-07-01), training-free", "SIGNED"),
    ]
    for line, want in cases_status:
        got = classify_status(line)
        assert got == want, f"classify_status({line!r}) = {got!r}, want {want!r}"

    cases_verdict = [
        # (body, status_line, expected)
        ("### Verdict (2026-06-30): FALSIFIED", "DRAFT (NOT signed)", "FALSIFIED"),
        ("**Stage-1 verdict (registered roll-up, 2026-07-02): FALSIFIER-1 — the "
         "channel stays shut**", "SIGNED", "FALSIFIED"),
        ("**VERDICT: SUCCESS — ceiling demonstrated. Falsifier dead; all 7**",
         "SIGNED", "SUCCESS"),
        # cross-reference to another amendment's verdict must NOT be picked up:
        ("rule (AB V1). The AB verdict is ambiguous-leaning-negative:", "SIGNED", ""),
        ("**Status:** RESOLVED — SUCCESS", "RESOLVED — SUCCESS", "SUCCESS"),
    ]
    for body, status_line, want in cases_verdict:
        got = extract_verdict(body, status_line)
        assert got == want, f"extract_verdict({body!r}) = {got!r}, want {want!r}"

    # Idempotent splice.
    block = "X"
    fenced = f"before\n{BEGIN_MARKER}\nold\n{END_MARKER}\nafter\n"
    new_block = f"{BEGIN_MARKER}\nnew\n{END_MARKER}"
    once = splice(fenced, new_block)
    assert splice(once, new_block) == once, "splice not idempotent"
    assert "before" in once and "after" in once, "splice dropped surrounding text"

    print("selftest: all cases pass")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--write", action="store_true", help="rewrite TODO.md in place")
    g.add_argument(
        "--check",
        action="store_true",
        help="exit 1 if TODO.md's generated block is stale",
    )
    g.add_argument(
        "--selftest",
        action="store_true",
        help="run built-in parsing/splice unit checks and exit",
    )
    args = ap.parse_args()

    if args.selftest:
        return selftest()

    rows = collect()
    block = render_block(rows)

    if not args.write and not args.check:
        print(block)
        return 0

    existing = TODO_PATH.read_text(encoding="utf-8") if TODO_PATH.exists() else ""
    updated = splice(existing, block)

    if args.check:
        if updated != existing:
            sys.stderr.write(
                "TODO.md amendment index is stale. Run "
                "`python3 bin/build_backlog_index.py --write`.\n"
            )
            return 1
        print("TODO.md amendment index is up to date.")
        return 0

    if updated != existing:
        TODO_PATH.write_text(updated, encoding="utf-8")
        print(f"Wrote {TODO_PATH.relative_to(REPO_ROOT)} ({len(rows)} amendments).")
    else:
        print("TODO.md already up to date; no change.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
