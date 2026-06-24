#!/usr/bin/env python3
"""Scan a paper source for named entities the graph cares about (Move 2 helper).

Strips an arXiv HTML render (or pdftotext output) to plain text and counts
mentions of common datasets / models / metrics / baselines so you can quickly
see which atoms a paper touches. This is a HINT to speed extraction, not a
substitute for reading the fulltext: it only knows the terms in DEFAULT_TERMS
plus any you pass with --term.

Usage (run from repo root):
    python3 .agents/skills/kg-ingest/scripts/scan_entities.py library/fulltext/2606.24790.html
    python3 .agents/skills/kg-ingest/scripts/scan_entities.py library/pdfs/2606.24790.pdf
    python3 .agents/skills/kg-ingest/scripts/scan_entities.py <src> --term "Grad Detect" --term SmolLM3
"""
import argparse
import html
import os
import re
import shutil
import subprocess
import sys

DEFAULT_TERMS = [
    # datasets / benchmarks
    "TriviaQA", "TruthfulQA", "PopQA", "SciQ", "MMLU", "Natural Questions",
    "HotpotQA", "GSM8K", "SelfAware", "EntityQuestions", "PararRel", "AbstentionBench",
    # model families
    "Llama", "LLaMA", "Qwen", "Gemma", "Mistral", "Falcon", "Phi", "GPT",
    "OPT", "Pythia", "SmolLM",
    # metrics
    "AUROC", "AUC", "AUPRC", "ECE", "Brier", "accuracy", "F1", "calibration",
    # signals / baselines
    "abstention", "hallucination", "semantic entropy", "perplexity", "P(True)",
    "verbalized", "logit", "probe", "consistency",
]


def to_text(path):
    if not os.path.exists(path):
        sys.exit(f"scan_entities: no such file: {path}")
    if path.lower().endswith((".html", ".htm")):
        raw = open(path, encoding="utf-8", errors="replace").read()
        txt = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", raw, flags=re.S | re.I)
        txt = re.sub(r"<[^>]+>", " ", txt)
        return re.sub(r"\s+", " ", html.unescape(txt))
    if path.lower().endswith(".pdf"):
        if not shutil.which("pdftotext"):
            sys.exit("scan_entities: PDF given but `pdftotext` not installed; "
                     "pass the HTML render instead, or `brew install poppler`.")
        out = subprocess.run(["pdftotext", path, "-"], capture_output=True, text=True)
        return re.sub(r"\s+", " ", out.stdout)
    # treat anything else as plain text
    return re.sub(r"\s+", " ", open(path, encoding="utf-8", errors="replace").read())


def main():
    ap = argparse.ArgumentParser(description="Scan a paper source for known entities.")
    ap.add_argument("src", help="path to HTML/PDF/text source")
    ap.add_argument("--term", action="append", default=[], help="extra term(s) to count")
    a = ap.parse_args()

    txt = to_text(a.src)
    terms = DEFAULT_TERMS + a.term
    hits = []
    for t in terms:
        n = len(re.findall(re.escape(t), txt, flags=re.I))
        if n:
            hits.append((n, t))
    hits.sort(reverse=True)

    if not hits:
        print("no known entities found (read the fulltext directly)")
        return
    print(f"entity mentions in {a.src}:")
    for n, t in hits:
        print(f"  {n:4d}  {t}")
    print("\nReminder: confirm exact dataset/model/metric variants in the text; "
          "reuse existing slugs from /tmp/kg_inventory.json before creating atoms.")


if __name__ == "__main__":
    main()
