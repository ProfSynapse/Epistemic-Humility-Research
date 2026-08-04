#!/usr/bin/env python3
"""Publish the paper-2 adapter set: upload each model card, then flip to public.

This script performs Hugging Face WRITE operations and is run by the lead only,
after the user has approved a sample card. It is a two-step-per-repo operation:

  1. upload `docs/hf-cards/<repo>/README.md` to the repo as `README.md`
  2. flip the repo's visibility to public via `update_repo_settings`

Both steps are idempotent. Re-uploading an unchanged card is a no-op commit on
the Hub, and flipping an already-public repo is accepted. Each repo is handled
in its own try/except so one failure does not abort the rest; a summary table is
printed at the end.

Dry run is ON by default. Nothing is written until `--execute` is passed.

    # inspect the plan (no writes)
    python3 scripts/release/flip_paper2_adapter_set_public.py

    # do it
    python3 scripts/release/flip_paper2_adapter_set_public.py --execute

    # one repo only
    python3 scripts/release/flip_paper2_adapter_set_public.py \\
        --execute --only eh-qwen3-4b-headline-kto-seed3-lora

Authentication comes from the ambient Hugging Face token (`huggingface-cli
login`, or `HF_TOKEN` in the environment).
"""
from __future__ import annotations

import argparse
import sys
import traceback
from pathlib import Path

ACCOUNT = "professorsynapse"

# The 17 user-approved repos. Revision is the staged SHA recorded in
# docs/checkpoint-staging.md at the time this release was prepared; it is
# printed for confirmation and is NOT used to pin the upload (uploads always
# land on the default branch head).
REPOS: list[tuple[str, str]] = [
    # 9 headline (PROTOCOL v0.3 locked matrix)
    ("eh-qwen3-4b-headline-sft-seed1-lora", "535dfabec0365b80663df618880ac2ad0976eb51"),
    ("eh-qwen3-4b-headline-sft-seed2-lora", "23ae0043bd794be8ede1122effd9ccfecb9d85aa"),
    ("eh-qwen3-4b-headline-sft-seed3-lora", "b3efd6e7aa133c8ad17d35ec569335b6a858d423"),
    ("eh-qwen3-4b-headline-dpo-seed1-lora", "9d503e1937d361c97abae6480ecafaac19a0668f"),
    ("eh-qwen3-4b-headline-dpo-seed2-lora", "21326cbcd8a975ca3b89f8552f053392281af23e"),
    ("eh-qwen3-4b-headline-dpo-seed3-lora", "dc95b05729a9b45e9335d3ac5ed84cc55f84ac81"),
    ("eh-qwen3-4b-headline-kto-seed1-lora", "ebfa75363afe9a92c97b7032acd608359b2026f6"),
    ("eh-qwen3-4b-headline-kto-seed2-lora", "5153f05b96f70314dab796d79b006ee5236680db"),
    ("eh-qwen3-4b-headline-kto-seed3-lora", "ce68f04723cd9cad30ff58d8037a8629a6adb486"),
    # 6 sequential extension
    ("eh-qwen3-4b-seq-sft-dpo-seed1-lora", "45138e73be9d28fcf9537a9d2de49d90ebf8601b"),
    ("eh-qwen3-4b-seq-sft-dpo-seed2-lora", "62c2cf65d93509ee86bdedb257512f9055a4ff1a"),
    ("eh-qwen3-4b-seq-sft-dpo-seed3-lora", "9cdd0d292c1b0309c3ced096c057697c8fc969d9"),
    ("eh-qwen3-4b-seq-sft-kto-seed1-lora", "2ccb2ec3883bf004feb545fb555ea3846e8c39fb"),
    ("eh-qwen3-4b-seq-sft-kto-seed2-lora", "c9b38352ba852f427e0c3ed802d038f94ebf9997"),
    ("eh-qwen3-4b-seq-sft-kto-seed3-lora", "cb6c246e0e566908f7a4e4844a892d811667cf2d"),
    # deployed checkpoint + its merged base
    ("eh-qwen3-4b-clean-sft-grpo-v2-seed1-lora", "8914081dfcec4f1f025f2dbe4195d4f7aa8d210e"),
    ("eh-qwen3-4b-clean-sft-seed1-merged-16bit", "ac361232c001af0ed5b0386b06dafc35d5cd31ea"),
]

COMMIT_MESSAGE = "Add model card for public release (paper 2 adapter set)"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def card_path(repo: str) -> Path:
    return repo_root() / "docs" / "hf-cards" / repo / "README.md"


def describe(api, repo_id: str) -> str:
    """Return a short 'private=... sha=...' description of the repo's state."""
    info = api.model_info(repo_id)
    private = getattr(info, "private", None)
    sha = getattr(info, "sha", None)
    return f"private={private} revision={sha}"


def process(api, repo: str, staged_rev: str, execute: bool) -> tuple[str, str]:
    repo_id = f"{ACCOUNT}/{repo}"
    card = card_path(repo)

    if not card.is_file():
        return "SKIPPED", f"no card at {card.relative_to(repo_root())}"

    print(f"\n=== {repo_id}")
    print(f"    card        : docs/hf-cards/{repo}/README.md ({card.stat().st_size} bytes)")
    print(f"    staged rev  : {staged_rev}")

    before = describe(api, repo_id)
    print(f"    before      : {before}")

    if not execute:
        print("    DRY RUN     : would upload README.md, then set private=False")
        return "DRY-RUN", before

    api.upload_file(
        path_or_fileobj=str(card),
        path_in_repo="README.md",
        repo_id=repo_id,
        repo_type="model",
        commit_message=COMMIT_MESSAGE,
    )
    print(f"    after upload: {describe(api, repo_id)}")

    api.update_repo_settings(repo_id=repo_id, repo_type="model", private=False)
    after = describe(api, repo_id)
    print(f"    after flip  : {after}")
    print(f"    url         : https://huggingface.co/{repo_id}")

    return "OK", after


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--execute", action="store_true",
                        help="perform the writes (default is a dry run)")
    parser.add_argument("--only", action="append", default=None, metavar="REPO",
                        help="restrict to one repo name (repeatable)")
    args = parser.parse_args()

    try:
        from huggingface_hub import HfApi
    except ImportError:
        print("huggingface_hub is not installed: pip install huggingface_hub", file=sys.stderr)
        return 2

    selected = [(r, rev) for r, rev in REPOS if not args.only or r in args.only]
    if args.only:
        unknown = set(args.only) - {r for r, _ in REPOS}
        if unknown:
            print(f"unknown repo name(s): {sorted(unknown)}", file=sys.stderr)
            return 2

    mode = "EXECUTE" if args.execute else "DRY RUN (no writes; pass --execute)"
    print(f"Paper-2 adapter set release: {len(selected)} repos on {ACCOUNT} [{mode}]")

    api = HfApi()
    results: list[tuple[str, str, str]] = []

    for repo, staged_rev in selected:
        try:
            status, detail = process(api, repo, staged_rev, args.execute)
        except Exception as exc:  # one repo failing must not abort the rest
            print(f"    FAILED      : {type(exc).__name__}: {exc}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            status, detail = "FAILED", f"{type(exc).__name__}: {exc}"
        results.append((repo, status, detail))

    print("\n" + "=" * 78)
    print("SUMMARY")
    print("=" * 78)
    for repo, status, detail in results:
        print(f"{status:8} {repo:44} {detail}")

    failed = [r for r, s, _ in results if s == "FAILED"]
    if failed:
        print(f"\n{len(failed)} repo(s) failed: {failed}", file=sys.stderr)
        return 1

    if args.execute:
        print("\nNext: record the release in docs/public-artifacts.md with the "
              "post-upload revision SHAs printed above.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
