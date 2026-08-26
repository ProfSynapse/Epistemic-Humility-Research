#!/usr/bin/env python3
"""Thin uploader for a verified exhaust dataset dir. Dry-run by default.

Naming convention: `professorsynapse/eh-<experiment-slug>` for the aggregate
shape, `professorsynapse/eh-<experiment-slug>-rows` for the row-level shape.
Derived automatically from the dataset dir's PROVENANCE.json unless --repo-id
is given explicitly.

This wraps huggingface_hub.HfApi().create_repo + upload_folder -- the same
calls already used by experiments/common/cloud/upload_folder.py -- and adds
nothing else. It does not run verify_exhaust.py for you; run that first and
only point this script at a dataset dir that already passed it.

HF_TOKEN comes from the environment only and is never printed. Without
--live, this script only prints the plan and touches no network.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


def load_provenance(dataset_dir: Path) -> dict:
    path = dataset_dir / "PROVENANCE.json"
    if not path.is_file():
        raise SystemExit(f"missing {path}; run build_exhaust_dataset.py first")
    return json.loads(path.read_text(encoding="utf-8"))


def default_repo_id(provenance: dict) -> str:
    slug = provenance.get("experiment_slug")
    shape = provenance.get("shape")
    if not slug or shape not in ("aggregate", "rows"):
        raise SystemExit(f"PROVENANCE.json missing experiment_slug or a valid shape: {provenance}")
    suffix = "-rows" if shape == "rows" else ""
    return f"professorsynapse/eh-{slug}{suffix}"


def list_files(dataset_dir: Path) -> list[tuple[str, int]]:
    out = []
    for path in sorted(dataset_dir.rglob("*")):
        if path.is_file():
            out.append((str(path.relative_to(dataset_dir)), path.stat().st_size))
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dataset-dir", required=True, help="verified dataset dir (from build_exhaust_dataset.py)")
    parser.add_argument("--repo-id", default=None, help="override the derived professorsynapse/eh-<slug>[-rows] repo id")
    parser.add_argument("--private", action="store_true", help="create/update the repo as private")
    parser.add_argument("--live", action="store_true", help="actually call the Hub API; without this flag the plan is printed and nothing is uploaded")
    args = parser.parse_args(argv)

    dataset_dir = Path(args.dataset_dir).resolve()
    if not dataset_dir.is_dir():
        print(f"[upload-exhaust] FATAL: {dataset_dir} is not a directory", file=sys.stderr)
        return 2

    provenance = load_provenance(dataset_dir)
    repo_id = args.repo_id or default_repo_id(provenance)
    files = list_files(dataset_dir)
    total_bytes = sum(size for _, size in files)

    print("[upload-exhaust] plan")
    print(f"  repo_id:      {repo_id}")
    print(f"  repo_type:    dataset")
    print(f"  private:      {args.private}")
    print(f"  source dir:   {dataset_dir}")
    print(f"  experiment:   {provenance.get('experiment_slug')} (shape={provenance.get('shape')})")
    print(f"  commit sha:   {provenance.get('repo_commit_sha')}")
    print(f"  files:        {len(files)} ({total_bytes} bytes total)")
    for rel, size in files[:20]:
        print(f"    - {rel} ({size} bytes)")
    if len(files) > 20:
        print(f"    ... and {len(files) - 20} more")

    if not args.live:
        print("[upload-exhaust] DRY RUN -- no network calls made. Pass --live to actually upload.")
        return 0

    from huggingface_hub import HfApi

    api = HfApi()
    # Auth: HF_TOKEN env if present, else huggingface_hub's stored login
    # (huggingface-cli login). The library resolves the credential internally;
    # this script never reads, prints, or logs the token value either way.
    if not os.environ.get("HF_TOKEN"):
        try:
            api.whoami()
        except Exception:
            print(
                "[upload-exhaust] FATAL: no HF_TOKEN in environment and no "
                "usable stored login (huggingface-cli login)",
                file=sys.stderr,
            )
            return 2
    api.create_repo(repo_id, repo_type="dataset", exist_ok=True, private=args.private)
    commit_info = api.upload_folder(
        folder_path=str(dataset_dir),
        path_in_repo="",
        repo_id=repo_id,
        repo_type="dataset",
    )
    revision = getattr(commit_info, "oid", None)
    if revision:
        print(f"[upload-exhaust] uploaded {dataset_dir} -> {repo_id}")
        print(f"[upload-exhaust] HF revision sha: {revision}")
        print("[upload-exhaust] record this revision in the experiment NOTEBOOK.md and docs/public-artifacts.md")
    else:
        print(f"[upload-exhaust] uploaded {dataset_dir} -> {repo_id}, but could not read a commit oid from the response:")
        print(f"  {commit_info!r}")
        print("[upload-exhaust] check the repo's commit history on the Hub directly to record the revision.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
