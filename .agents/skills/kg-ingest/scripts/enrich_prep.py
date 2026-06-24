#!/usr/bin/env python3
"""Prepare clean fulltext for an enrichment cluster.

For each arXiv id: ensure library/fulltext/<id>.html and library/pdfs/<id>.pdf
exist (fetch what is missing), then write a lean plain-text/markdown render to
<out-dir>/<id>.md for the Sonnet agents to read. Prefers the arXiv HTML render
(pandoc + ltx-noise strip); falls back to pdftotext when there is no usable HTML
(older papers). The library/fulltext and library/pdfs files are gitignored data.

Requires: pandoc, pdftotext, curl. Run from the repo root (or pass --root).

Usage: enrich_prep.py --out <dir> <arxiv-id> [<arxiv-id> ...]
"""
import argparse, os, re, subprocess, sys

UA = "Mozilla/5.0"


def fetch(url, dest):
    subprocess.run(["curl", "-sL", "-A", UA, "-o", dest, url], check=False)


def clean_pandoc_md(text):
    text = re.sub(r'\{[^{}\n]*\}', '', text)                       # drop {.ltx_...} attrs
    text = re.sub(r'\]\(https?://arxiv\.org/html/[^)]*\)', ']', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]+\n', '\n', text)
    return text


def html_is_real(path):
    if not os.path.exists(path) or os.path.getsize(path) < 20000:
        return False
    with open(path, errors="ignore") as fh:
        return "<html" in fh.read(4000).lower()


def prep_one(arxiv, root, out_dir):
    html = os.path.join(root, "library/fulltext", f"{arxiv}.html")
    pdf = os.path.join(root, "library/pdfs", f"{arxiv}.pdf")
    out = os.path.join(out_dir, f"{arxiv}.md")
    if not html_is_real(html):
        fetch(f"https://arxiv.org/html/{arxiv}", html)
    if not os.path.exists(pdf) or os.path.getsize(pdf) < 10000:
        fetch(f"https://arxiv.org/pdf/{arxiv}", pdf)

    if html_is_real(html):
        raw = subprocess.run(["pandoc", "-f", "html", "-t", "markdown", "--wrap=none", html],
                             capture_output=True, text=True)
        open(out, "w").write(clean_pandoc_md(raw.stdout))
        src = "html"
    else:
        if os.path.exists(html):
            os.remove(html)
        subprocess.run(["pdftotext", pdf, out], check=False)
        src = "pdf"
    size = os.path.getsize(out) if os.path.exists(out) else 0
    return f"{arxiv}: {src}, {size // 4000}k tok -> {out}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="output dir for clean <id>.md")
    ap.add_argument("--root", default=os.environ.get("REPO_ROOT") or os.getcwd())
    ap.add_argument("ids", nargs="+")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    for arxiv in a.ids:
        print(prep_one(arxiv, a.root, a.out))


if __name__ == "__main__":
    main()
