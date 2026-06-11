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
    # Phase 1 probe/train pool (WS-0). Disjoint from the Cheng test set, which
    # is sourced from the validation split above; the WS-2 builder enforces
    # normalized-question disjointness with a leakage guard. Train rows carry
    # answer.normalized_aliases, so the probe needs no separate gold build.
    ("mandarjoshi/trivia_qa", "rc.nocontext", "train",
     "triviaqa-rc-nocontext", "train.jsonl"),
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

# OpenMOSS "Say I Don't Know" (Cheng et al. 2401.13275) Idk TRAINING data.
# This is a special, user-authorized VENDOR case, not an HF pull:
#   - source data ships only as a Google Drive zip (no HF mirror, no stable host);
#   - the repo has NO license (GitHub license: null), so the data is USE-only and
#     MUST NOT be redistributed: the zip and all regenerated files stay gitignored.
# Only the fetcher code, the pinned ID/SHA, the .gitignore, and dataset.md are
# committed. See fetch_say_i_dont_know_training() and the dataset.md stanza.
OPENMOSS_REPO = "https://github.com/OpenMOSS/Say-I-Dont-Know.git"
OPENMOSS_PIN_SHA = "a4768458638fa78a9a43252d319514db425dcaf3"
OPENMOSS_DRIVE_FILE_ID = "1xN-xtx12eHL-1-pIsS5-vERXrgzfMnw9"
# sha256 of the downloaded data.zip (the zip has no stable host, so the SHA is
# our determinism anchor). Pinned from the authorized fetch on 2026-06-10; later
# runs verify against it. To re-pin after an upstream change, clear this, fetch,
# and copy the observed SHA the fetcher prints (also written to data.zip.sha256).
OPENMOSS_DRIVE_ZIP_SHA256 = "1dfe742ca2ffd4b0a283f972e6bbda68e6131e13648f418c9dfd9b99d91bab86"
OPENMOSS_OUT_DIR = "say-i-dont-know-training"
OPENMOSS_MODEL = "llama-2-7b-chat"


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


def _sha256(path):
    import hashlib

    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _safe_extract_all(zf, dest_dir):
    """Extract every member of zf under dest_dir, rejecting path-traversal.

    A defense against zip-slip that holds INDEPENDENT of the sha pin: even a
    zip whose bytes match the pin is extracted member-by-member, and any member
    that would escape dest_dir (a "../" path, an absolute path, or a symlink) is
    a hard stop. The pin guards which zip we trust; this guards how we open it.

    Validation per member:
      - reject absolute member names (the resolved target must stay inside);
      - resolve the target against dest_dir and require it to be inside (covers
        "../" traversal regardless of how the name is spelled);
      - reject symlink members (external_attr high bits), which could redirect
        a later write outside the tree.
    """
    import stat
    import zipfile

    dest_root = dest_dir.resolve()
    for info in zf.infolist():
        name = info.filename
        # A symlink member carries S_IFLNK in the upper 16 bits of external_attr.
        mode = info.external_attr >> 16
        if stat.S_ISLNK(mode):
            raise RuntimeError(
                f"refusing to extract symlink member from zip: {name!r} "
                f"(zip-slip guard, independent of sha pin)."
            )
        target = (dest_root / name).resolve()
        if not _is_within(target, dest_root):
            raise RuntimeError(
                f"refusing to extract member escaping dest dir: {name!r} -> "
                f"{target} (zip-slip guard, independent of sha pin)."
            )
        if info.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        with zf.open(info) as src, open(target, "wb") as dst:
            import shutil
            shutil.copyfileobj(src, dst)


def _is_within(target, root):
    """True if the resolved target path is inside (or equal to) root."""
    try:
        target.relative_to(root)
        return True
    except ValueError:
        return False


def fetch_say_i_dont_know_training(force):
    """Vendor + regenerate the OpenMOSS Idk training data (USE, no REDISTRIBUTE).

    Steps, all under datasets/say-i-dont-know-training/ (gitignored):
      1. gdown the pinned Drive file id -> data.zip; record/verify its sha256.
      2. git clone OpenMOSS/Say-I-Dont-Know at the pinned SHA (do not vendor
         their code into our repo; clone is transient, also gitignored).
      3. unzip data.zip and ASSERT the layout the scripts expect; a mismatch is
         a hard stop (raises), not a silent guess.
      4. run their process_sft_data.py to regenerate the Idk-SFT train/valid/test
         sets; locate the Idk-DPO preference-pairs file shipped in the zip.

    Network egress (Google Drive + GitHub) is required and is user-authorized
    for this dataset only. If the Drive link is dead or the zip layout does not
    match, this raises so the caller stops and reports (a new blocker).
    """
    import subprocess

    out_root = DATASETS_DIR / OPENMOSS_OUT_DIR
    out_root.mkdir(parents=True, exist_ok=True)
    zip_path = out_root / "data.zip"
    unzip_dir = out_root / "unzipped"
    clone_dir = out_root / "_openmoss_repo"
    sha_sidecar = out_root / "data.zip.sha256"

    # 1. Download the Drive zip (idempotent: skip if present unless --force).
    if zip_path.exists() and not force:
        print(f"skipped {zip_path.relative_to(DATASETS_DIR)} (exists)")
    else:
        import gdown

        url = f"https://drive.google.com/uc?id={OPENMOSS_DRIVE_FILE_ID}"
        got = gdown.download(url, output=str(zip_path), quiet=False)
        if not got or not zip_path.exists():
            raise RuntimeError(
                "OpenMOSS Drive download failed (link dead or access changed). "
                "This is a blocker: stop and report, do not work around."
            )

    # 2. Verify / record the zip sha256 (determinism anchor; no stable host).
    observed = _sha256(zip_path)
    sha_sidecar.write_text(observed + "\n")
    if OPENMOSS_DRIVE_ZIP_SHA256:
        if observed != OPENMOSS_DRIVE_ZIP_SHA256:
            raise RuntimeError(
                f"OpenMOSS data.zip sha256 mismatch: expected "
                f"{OPENMOSS_DRIVE_ZIP_SHA256}, got {observed}. The Drive file "
                f"changed under a fixed id; stop and report."
            )
        print(f"verified data.zip sha256 == pinned ({observed[:16]}...)")
    else:
        print(f"OBSERVED data.zip sha256: {observed}\n"
              f"  -> pin this into OPENMOSS_DRIVE_ZIP_SHA256 in a follow-up commit")

    # 3. Unzip and assert the layout process_sft_data.py expects.
    import zipfile

    if force and unzip_dir.exists():
        import shutil
        shutil.rmtree(unzip_dir)
    unzip_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as zf:
        _safe_extract_all(zf, unzip_dir)

    # The scripts read sft_data/<model>/triviaqa_{train,dev}_tp1.0_10responses_with_em_labels.json
    needed = [
        "triviaqa_train_tp1.0_10responses_with_em_labels.json",
        "triviaqa_dev_tp1.0_10responses_with_em_labels.json",
    ]
    sft_base = _locate_sft_model_dir(unzip_dir, needed)
    if sft_base is None:
        raise RuntimeError(
            "OpenMOSS zip layout mismatch: could not find "
            f"sft_data/{OPENMOSS_MODEL}/ with {needed}. The zip contents do not "
            f"match the scripts' expectations; stop and report (new blocker)."
        )

    # 4. Clone the repo at the pinned SHA and run their SFT regeneration in place.
    if clone_dir.exists():
        import shutil
        shutil.rmtree(clone_dir)
    subprocess.run(["git", "clone", "--no-checkout", OPENMOSS_REPO, str(clone_dir)],
                   check=True)
    subprocess.run(["git", "-C", str(clone_dir), "checkout", OPENMOSS_PIN_SHA],
                   check=True)

    # process_sft_data.py reads/writes relative to its CWD's sft_data/<model>/,
    # so run it from the unzip dir (which holds sft_data/) with the pinned script.
    sft_script = clone_dir / "Idk_datasets" / "process_sft_data.py"
    subprocess.run(
        ["python3", str(sft_script), "--model_name", OPENMOSS_MODEL, "--threshold", "1.0"],
        cwd=str(sft_base.parents[1]),  # the dir that CONTAINS sft_data/
        check=True,
    )

    # Idk-SFT outputs now exist under sft_data/<model>/; Idk-DPO preference pairs
    # ship in the zip (the repo has no from-scratch pair builder). Locate them.
    dpo_pairs = _locate_file(unzip_dir, "preference", "threshold_1.0", ".json")
    print("Idk-SFT regenerated under "
          f"{sft_base.relative_to(DATASETS_DIR)} "
          "(triviaqa_{train,valid,test}_threshold_1.0_sft_data.json)")
    print("Idk-DPO preference pairs: "
          + (str(dpo_pairs.relative_to(DATASETS_DIR)) if dpo_pairs
             else "NOT FOUND in zip; stop and report (DPO arm needs them)"))
    print("ALL outputs under "
          f"{out_root.relative_to(DATASETS_DIR)} are gitignored (do not commit).")


def _locate_sft_model_dir(root, needed_files):
    """Find the sft_data/<model>/ dir under root that holds the needed files.

    Walks the unzipped tree so the zip's top-level wrapper dir (if any) does
    not matter, and matches the sft_data/<model> path tail explicitly. Returns
    the model dir (the one CONTAINING needed_files), or None on no match.
    """
    for sft_data in root.rglob("sft_data"):
        if not sft_data.is_dir():
            continue
        model_dir = sft_data / OPENMOSS_MODEL
        if model_dir.is_dir() and all((model_dir / f).exists() for f in needed_files):
            return model_dir
    return None


def _locate_file(root, *substrings):
    """Return the first file under root whose name contains all substrings."""
    for path in root.rglob("*"):
        if path.is_file() and all(s in path.name for s in substrings):
            return path
    return None


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
    # OpenMOSS Idk training data is OPT-IN only (network egress to Drive+GitHub,
    # runs their scripts, user-authorized for this dataset). It never runs as
    # part of a bare `python fetch_datasets.py`; request it explicitly:
    #   python datasets/scripts/fetch_datasets.py --only say-i-dont-know-training
    if wanted and OPENMOSS_OUT_DIR in wanted:
        fetch_say_i_dont_know_training(args.force)


if __name__ == "__main__":
    main()
