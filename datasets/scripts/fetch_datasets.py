#!/usr/bin/env python3
"""Fetch the HF-hosted eval datasets for the epistemic-humility program.

Downloads the splits the meta-analysis + experiment need into
docs/epistemic-humility/datasets/<name>/, as JSONL, subsetting nothing
except by split/config (per HANDOFF.md: large corpora are restricted to
the slices we actually evaluate on, e.g. TriviaQA rc.nocontext validation).

Each dataset directory gets a hand-written dataset.md with provenance
frontmatter; this script only writes the data files and prints row counts.

Idempotent: existing output files are skipped unless --force.

Network note: needs huggingface.co + cdn-lfs.huggingface.co. On macOS
python.org builds, run with SSL_CERT_FILE=$(python3 -m certifi).
"""

import argparse
import json
from pathlib import Path

DATASETS_DIR = Path(__file__).resolve().parent.parent

# (hf_repo, config, split, output_dir, output_file)
SPECS = [
    ("mandarjoshi/trivia_qa", "rc.nocontext", "validation",
     "triviaqa-rc-nocontext", "validation.jsonl"),
    ("cais/mmlu", "all", "test", "mmlu", "test.jsonl"),
    ("cais/mmlu", "all", "validation", "mmlu", "validation.jsonl"),
    ("akariasai/PopQA", None, "test", "popqa", "test.jsonl"),
    ("allenai/coconot", "original", "test", "coconot", "original_test.jsonl"),
    ("allenai/coconot", "original", "train", "coconot", "original_train.jsonl"),
    ("allenai/coconot", "contrast", "test", "coconot", "contrast_test.jsonl"),
]

# Raw files fetched directly (source JSONL has inconsistent columns,
# which breaks the datasets builder): (hf_repo, filename, output_dir)
RAW_SPECS = [
    ("amayuelas/KUQ", "knowns_unknowns.jsonl", "kuq"),
    ("amayuelas/KUQ", "unknowns_all.jsonl", "kuq"),
]

# Repos that are loading-script compositions: snapshot the repo files instead.
SNAPSHOT_SPECS = [
    ("facebook/AbstentionBench", "abstentionbench-repo"),
]


def fetch_split(repo, config, split, out_dir, out_file, force):
    from datasets import load_dataset

    out_path = DATASETS_DIR / out_dir / out_file
    if out_path.exists() and not force:
        print(f"skipped {out_path.relative_to(DATASETS_DIR)} (exists)")
        return
    out_path.parent.mkdir(parents=True, exist_ok=True)
    ds = load_dataset(repo, config, split=split)
    with out_path.open("w") as fh:
        for row in ds:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"wrote {out_path.relative_to(DATASETS_DIR)}: {len(ds)} rows")


def fetch_raw(repo, filename, out_dir, force):
    import shutil

    from huggingface_hub import hf_hub_download

    out_path = DATASETS_DIR / out_dir / filename
    if out_path.exists() and not force:
        print(f"skipped {out_path.relative_to(DATASETS_DIR)} (exists)")
        return
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cached = hf_hub_download(repo, filename, repo_type="dataset")
    shutil.copyfile(cached, out_path)
    n = sum(1 for _ in out_path.open())
    print(f"wrote {out_path.relative_to(DATASETS_DIR)}: {n} rows")


def snapshot(repo, out_dir, force):
    from huggingface_hub import snapshot_download

    target = DATASETS_DIR / out_dir
    if target.exists() and any(target.iterdir()) and not force:
        print(f"skipped {out_dir} (exists)")
        return
    snapshot_download(repo, repo_type="dataset", local_dir=target)
    print(f"snapshotted {repo} -> {out_dir}")


def build_cheng_gold(force):
    """Gold aliases for Cheng et al. (2401.13275) method outputs.

    Their 11,313-question 'test' set is exactly TriviaQA
    unfiltered.nocontext/validation (verified 2026-06-10: 100% match on
    normalized question text; their integer question_ids are a re-index).
    Matching is by normalized question because of that re-indexing.
    """
    import re

    from datasets import load_dataset

    out_path = DATASETS_DIR / "triviaqa-rc-nocontext" / "cheng_test_gold.jsonl"
    if out_path.exists() and not force:
        print(f"skipped {out_path.relative_to(DATASETS_DIR)} (exists)")
        return
    norm = lambda s: re.sub(r"\s+", " ", s.strip().lower())
    cheng = json.loads(
        (DATASETS_DIR / "say-i-dont-know-outputs" / "triviaqa_test_llama2_7b_chat_idk_sft.json").read_text()
    )
    need = {norm(r["question"]) for r in cheng}
    ds = load_dataset("mandarjoshi/trivia_qa", "unfiltered.nocontext", split="validation")
    found = {}
    for r in ds:
        q = norm(r["question"])
        if q in need and q not in found:
            found[q] = r
    missing = need - set(found)
    if missing:
        raise RuntimeError(f"{len(missing)} Cheng questions unmatched; first: {sorted(missing)[:3]}")
    with out_path.open("w") as fh:
        for q, r in found.items():
            a = r["answer"]
            fh.write(json.dumps({
                "question_norm": q,
                "tqa_question_id": r["question_id"],
                "source_split": "unfiltered.nocontext/validation",
                "answer_value": a["value"],
                "aliases": a["aliases"],
                "normalized_aliases": a["normalized_aliases"],
            }, ensure_ascii=False) + "\n")
    print(f"wrote {out_path.relative_to(DATASETS_DIR)}: {len(found)} rows")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="re-download even if present")
    parser.add_argument("--only", help="comma-separated output_dir names to restrict to")
    args = parser.parse_args()

    wanted = set(args.only.split(",")) if args.only else None
    for repo, config, split, out_dir, out_file in SPECS:
        if wanted and out_dir not in wanted:
            continue
        fetch_split(repo, config, split, out_dir, out_file, args.force)
    for repo, filename, out_dir in RAW_SPECS:
        if wanted and out_dir not in wanted:
            continue
        fetch_raw(repo, filename, out_dir, args.force)
    for repo, out_dir in SNAPSHOT_SPECS:
        if wanted and out_dir not in wanted:
            continue
        snapshot(repo, out_dir, args.force)
    if not wanted or "triviaqa-rc-nocontext" in wanted:
        build_cheng_gold(args.force)


if __name__ == "__main__":
    main()
