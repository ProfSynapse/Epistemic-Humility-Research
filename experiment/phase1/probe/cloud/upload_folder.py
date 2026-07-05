#!/usr/bin/env python3
"""Upload a whole extraction/generation dir to a (private) dataset repo.

The X/Z/Y readout lane uploads only small files (result/manifest/rows) with
cloud/upload_result.py and keeps the hidden-state tensors ephemeral. The
Amendment AI verdict eval is the exception: its TENSORS are the deliverable
(the CPU scorer refits a fresh probe on them), so the extraction dirs must be
uploaded whole. This helper wraps HfApi.upload_folder to a PRIVATE staging repo.

Auth comes from HF_TOKEN in the environment (job secret). The staging repo is
private because the union surface's rows.jsonl derives from NO-LICENSE FalseQA
source (the extractor already strips question text, but the private repo is the
belt-and-suspenders boundary).
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", required=True, help="staging dataset repo id")
    ap.add_argument("--folder", required=True, help="local dir to upload")
    ap.add_argument("--path-in-repo", required=True,
                    help="destination prefix inside the repo")
    ap.add_argument("--private", action="store_true", default=True)
    ap.add_argument("--public", dest="private", action="store_false",
                    help="override: create the repo public (NOT for FalseQA surfaces)")
    args = ap.parse_args()

    if not os.environ.get("HF_TOKEN"):
        print("[upload-folder] FATAL: HF_TOKEN not in environment", file=sys.stderr)
        return 2
    folder = Path(args.folder)
    if not folder.is_dir():
        print(f"[upload-folder] FATAL: not a dir {folder}", file=sys.stderr)
        return 2

    from huggingface_hub import HfApi

    api = HfApi()
    api.create_repo(args.repo, repo_type="dataset", exist_ok=True,
                    private=args.private)
    api.upload_folder(folder_path=str(folder), path_in_repo=args.path_in_repo,
                      repo_id=args.repo, repo_type="dataset")
    print(f"[upload-folder] uploaded {folder} -> {args.repo}:{args.path_in_repo}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
