#!/usr/bin/env python3
"""Upload small cell result artifacts to a results dataset repo.

Runs inside an HF Job at the end of hf_jobs_cell.sh. Uploads only the files
named on the command line (result JSON + manifest — a few KB); never the
extraction dir. Auth comes from HF_TOKEN in the environment (job secret).
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", required=True,
                    help="results dataset repo id, e.g. user/epistemic-humility-cloud-results")
    ap.add_argument("--path-prefix", required=True,
                    help="folder inside the repo (the cell's run tag)")
    ap.add_argument("--file", action="append", required=True, dest="files",
                    help="file to upload (repeatable)")
    args = ap.parse_args()

    if not os.environ.get("HF_TOKEN"):
        print("[upload-result] FATAL: HF_TOKEN not in environment", file=sys.stderr)
        return 2

    from huggingface_hub import HfApi

    api = HfApi()
    api.create_repo(args.repo, repo_type="dataset", exist_ok=True)
    for f in args.files:
        p = Path(f)
        if not p.is_file():
            print(f"[upload-result] FATAL: missing {p}", file=sys.stderr)
            return 2
        dest = f"{args.path_prefix}/{p.name}"
        api.upload_file(path_or_fileobj=str(p), path_in_repo=dest,
                        repo_id=args.repo, repo_type="dataset")
        print(f"[upload-result] uploaded {p} -> {args.repo}:{dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
