#!/usr/bin/env python3
"""Acquire a paper for kg-ingest (Move 0): metadata + fulltext + note stub.

Given an arXiv id or URL, this:
  1. pulls title / authors / year / abstract from the arXiv API (no scraping),
  2. downloads the HTML render -> library/fulltext/<id>.html (extraction source),
  3. downloads the PDF        -> library/pdfs/<id>.pdf       (provenance),
  4. writes the note stub     -> library/notes/<id>--<slug>.md (skip-if-exists),
  5. prints `<id> | <noteStem> | <src>` for the next moves.

Idempotent: existing files are kept unless --force. The note stub is NEVER
overwritten (so a patched note survives a re-run). fulltext/ and pdfs/ are
gitignored data: this script writes them but you must not commit them.

Usage (run from repo root):
    python3 .agents/skills/kg-ingest/scripts/fetch_paper.py 2606.24790
    python3 .agents/skills/kg-ingest/scripts/fetch_paper.py https://arxiv.org/abs/2606.24790 --area verification
    python3 .agents/skills/kg-ingest/scripts/fetch_paper.py 2606.24790 --slug grad-detect-gradient-hallucination-detection

Options:
    --slug SLUG   override the auto-generated title slug
    --area AREA   note `area` + tag (default: verification)
    --force       re-download HTML/PDF even if present
    --no-pdf      skip the PDF download
    --print-cmd   also emit the Move 2 entity-scan one-liner for this paper
"""
import argparse
import glob
import os
import re
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

ARXIV_API = "https://export.arxiv.org/api/query?id_list={id}"
ABS_URL = "https://arxiv.org/abs/{id}"
HTML_URL = "https://arxiv.org/html/{id}"
PDF_URL = "https://arxiv.org/pdf/{id}"
UA = "Mozilla/5.0 (kg-ingest fetch_paper)"
ATOM = "{http://www.w3.org/2005/Atom}"

STOP = {"the", "a", "an", "of", "for", "in", "on", "and", "to", "with", "via",
        "is", "are", "from", "by", "at"}


def die(msg):
    sys.exit(f"fetch_paper: {msg}")


def normalize_id(raw):
    """Accept a bare id, an abs/pdf/html URL, or an id with a version suffix."""
    raw = raw.strip()
    m = re.search(r"(\d{4}\.\d{4,5})", raw)
    if m:
        return m.group(1)
    # old-style id, e.g. hep-th/9901001
    m = re.search(r"([a-z\-]+(?:\.[A-Z]{2})?/\d{7})", raw)
    if m:
        return m.group(1)
    die(f"could not parse an arXiv id from {raw!r}")


def get(url, binary=False, timeout=60):
    # Shell out to curl: it uses the system cert store, sidestepping the macOS
    # Python.framework "CERTIFICATE_VERIFY_FAILED" issue, and follows redirects.
    if not shutil.which("curl"):
        die("curl not found on PATH (required for downloads)")
    proc = subprocess.run(
        ["curl", "-sSL", "--fail", "--max-time", str(timeout), "-A", UA, url],
        capture_output=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.decode("utf-8", "replace").strip()
                           or f"curl exit {proc.returncode}")
    return proc.stdout if binary else proc.stdout.decode("utf-8", "replace")


def _meta_from_api(arxiv_id):
    """Metadata via the arXiv Atom API. Raises RuntimeError on transport failure
    (incl. HTTP 429) so the caller can back off or fall back."""
    xml = get(ARXIV_API.format(id=arxiv_id))
    root = ET.fromstring(xml)
    entry = root.find(f"{ATOM}entry")
    if entry is None or entry.find(f"{ATOM}title") is None:
        raise RuntimeError(f"arXiv API returned no entry for {arxiv_id}")
    # an error/empty entry has a title but no published date
    published = entry.find(f"{ATOM}published")
    if published is None:
        raise RuntimeError(f"arXiv API returned no metadata for {arxiv_id}")
    title = re.sub(r"\s+", " ", entry.find(f"{ATOM}title").text).strip()
    summary = re.sub(r"\s+", " ", entry.find(f"{ATOM}summary").text).strip()
    year = published.text[:4]
    authors = [re.sub(r"\s+", " ", a.find(f"{ATOM}name").text).strip()
               for a in entry.findall(f"{ATOM}author")]
    return {"title": title, "summary": summary, "year": year, "authors": authors}


def _meta_from_abs(arxiv_id):
    """Fallback: scrape the /abs/ page's citation_* meta tags.

    export.arxiv.org (the API host) rate-limits aggressively and is sometimes
    unreachable when arxiv.org itself is fine, so a batch ingest that would
    otherwise stall out entirely can still make progress from the abs page.
    """
    html = get(ABS_URL.format(id=arxiv_id))
    def meta(name):
        m = re.search(rf'<meta name="{name}" content="([^"]*)"', html)
        return re.sub(r"\s+", " ", m.group(1)).strip() if m else ""
    title = meta("citation_title")
    if not title:
        raise RuntimeError(f"abs page for {arxiv_id} has no citation_title")
    authors = [re.sub(r"\s+", " ", a).strip() for a in
               re.findall(r'<meta name="citation_author" content="([^"]*)"', html)]
    date = meta("citation_date") or meta("citation_online_date")
    year = re.match(r"(\d{4})", date).group(1) if re.match(r"(\d{4})", date) else "?"
    m = re.search(r'<blockquote class="abstract[^"]*">(.*?)</blockquote>', html, re.S)
    summary = ""
    if m:
        summary = re.sub(r"<[^>]+>", " ", m.group(1))
        summary = re.sub(r"^\s*Abstract:\s*", "", re.sub(r"\s+", " ", summary)).strip()
    return {"title": title, "summary": summary, "year": year, "authors": authors}


def fetch_metadata(arxiv_id, retries=3):
    """API first, with backoff on rate-limiting, then the abs-page fallback.

    NOTE: this endpoint must be https. Over plain http the host returns an empty
    body, which parses as "no entry" and surfaces as a *bad id* error -- i.e. a
    transport failure that looks exactly like a fabricated arXiv id. Do not
    'simplify' the scheme back to http.
    """
    last = None
    for attempt in range(retries):
        try:
            return _meta_from_api(arxiv_id)
        except RuntimeError as e:
            last = e
            if "429" in str(e) and attempt < retries - 1:
                time.sleep(15 * (attempt + 1))
                continue
            break
    try:
        meta = _meta_from_abs(arxiv_id)
        print(f"fetch_paper: API unavailable ({last}); used abs-page metadata "
              f"for {arxiv_id}", file=sys.stderr)
        return meta
    except RuntimeError as e:
        die(f"could not fetch metadata for {arxiv_id}: API said {last}; "
            f"abs fallback said {e}")


def slugify(title, max_words=7):
    words = re.findall(r"[a-z0-9]+", title.lower())
    words = [w for w in words if w not in STOP]
    return "-".join(words[:max_words]) or "paper"


def yaml_quote(s):
    return "'" + s.replace("'", "''") + "'"


def download(url, path, force, label):
    if os.path.exists(path) and not force:
        return f"kept {label} ({os.path.getsize(path)} B)"
    try:
        data = get(url, binary=True)
    except Exception as e:  # noqa: BLE001 - report and continue
        return f"WARN {label} download failed: {e}"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)
    note = ""
    if label == "html" and len(data) < 2000:
        note = " (suspiciously small; older papers may have no HTML render)"
    return f"wrote {label} ({len(data)} B){note}"


def write_stub(note_path, arxiv_id, meta, slug, area):
    if os.path.exists(note_path):
        return "kept note stub (exists)"
    authors_block = "\n".join(f"- {a}" for a in meta["authors"]) or "- Unknown"
    body = f"""---
title: {yaml_quote(meta['title'])}
arxiv: '{arxiv_id}'
year: {meta['year']}
url: https://arxiv.org/abs/{arxiv_id}
area: {area}
status: verified
tags:
- paper
- epistemic-humility
- {area}
authors:
{authors_block}
models: []
metrics: []
pdf: ../pdfs/{arxiv_id}.pdf
---
## Abstract

{meta['summary']}

## Summary

<!-- filled during extraction -->

## Extracted numbers

<!-- rows feeding papers/paper-1-taxonomy-framework/evidence/*.csv; cite table/figure of origin -->

## Relevance to experiment

<!-- how this informs the Synaptic Tuner experiment design -->
"""
    os.makedirs(os.path.dirname(note_path), exist_ok=True)
    with open(note_path, "w", encoding="utf-8") as f:
        f.write(body)
    return "wrote note stub"


def note_status(note_path):
    """NEW (no note) | STUB (acquired, not in graph) | INGESTED (kg edges present)."""
    if not note_path or not os.path.exists(note_path):
        return "NEW"
    txt = open(note_path, encoding="utf-8").read()
    # the kg ingest stamps the note with a `kg.id: paper:<id>` block + typed edges
    if "id: paper:" in txt or re.search(r"^relationships:", txt, re.M):
        return "INGESTED"
    return "STUB"


STATUS_HINT = {
    "NEW": "not in the vault yet -> acquire, then run moves 1-4.",
    "STUB": "note exists but NOT in the graph -> run moves 1-4 (skip acquire).",
    "INGESTED": "already in the graph -> nothing to do (re-running is a no-op).",
}


def main():
    ap = argparse.ArgumentParser(description="Acquire a paper for kg-ingest (Move 0).")
    ap.add_argument("paper", help="arXiv id or URL")
    ap.add_argument("--slug", help="override the auto title slug")
    ap.add_argument("--area", default="verification")
    ap.add_argument("--force", action="store_true", help="re-download HTML/PDF")
    ap.add_argument("--no-pdf", action="store_true")
    ap.add_argument("--print-cmd", action="store_true")
    ap.add_argument("--check", action="store_true",
                    help="report existence status only; do not download or write")
    a = ap.parse_args()

    if not os.path.isdir("library/notes"):
        die("run from the repo root (library/notes not found)")

    arxiv_id = normalize_id(a.paper)

    # Existence check FIRST, off the local vault, so you never hand-search. Reuse an
    # existing note for this id REGARDLESS of its slug, so a re-run never creates a
    # second note file; a curated slug on disk wins over --slug and the auto slug.
    existing = sorted(glob.glob(f"library/notes/{arxiv_id}--*.md"))
    note_path = existing[0] if existing else None
    status = note_status(note_path)

    # --check is offline-friendly: only hit the arXiv API for the title when we can.
    meta = None
    if not a.check:
        meta = fetch_metadata(arxiv_id)
    elif not existing:
        try:
            meta = fetch_metadata(arxiv_id)
        except Exception:  # noqa: BLE001 - offline / bad id; status still reported
            pass

    if existing:
        note_stem = os.path.basename(existing[0])[:-3]
        slug = note_stem.split("--", 1)[1]
        if a.slug and a.slug != slug:
            print(f"note: --slug {a.slug!r} ignored; existing note uses {slug!r}",
                  file=sys.stderr)
    else:
        slug = a.slug or (slugify(meta["title"]) if meta else "paper")
        note_stem = f"{arxiv_id}--{slug}"
        note_path = f"library/notes/{note_stem}.md"

    title = meta["title"] if meta else "(arXiv metadata not fetched)"
    print(f"STATUS : {status}  -- {STATUS_HINT[status]}")
    print(f"id     : {arxiv_id}")
    print(f"title  : {title}")
    if existing:
        print(f"note   : {note_path}")
    print(f"slug   : {slug}")

    if a.check:
        html_path = f"library/fulltext/{arxiv_id}.html"
        pdf_path = f"library/pdfs/{arxiv_id}.pdf"
        have = [n for n, p in (("html", html_path), ("pdf", pdf_path)) if os.path.exists(p)]
        print(f"sources: {', '.join(have) if have else 'none on disk'}")
        # exit code encodes status for scripting: 0 INGESTED, 10 STUB, 20 NEW
        sys.exit({"INGESTED": 0, "STUB": 10, "NEW": 20}[status])

    if status == "INGESTED":
        print("\nalready ingested; acquiring source files is still safe (idempotent).")

    html_path = f"library/fulltext/{arxiv_id}.html"
    pdf_path = f"library/pdfs/{arxiv_id}.pdf"
    print()
    print(download(HTML_URL.format(id=arxiv_id), html_path, a.force, "html"))
    if not a.no_pdf:
        print(download(PDF_URL.format(id=arxiv_id), pdf_path, a.force, "pdf"))
    print(write_stub(note_path, arxiv_id, meta, slug, a.area))

    src = html_path if os.path.exists(html_path) and os.path.getsize(html_path) >= 2000 \
        else (pdf_path if os.path.exists(pdf_path) else "none")
    print()
    print(f"{arxiv_id} | {note_stem} | {src}")
    if a.print_cmd:
        print("\n# Move 2 entity scan:")
        print(f"python3 .agents/skills/kg-ingest/scripts/scan_entities.py {src}")


if __name__ == "__main__":
    main()
