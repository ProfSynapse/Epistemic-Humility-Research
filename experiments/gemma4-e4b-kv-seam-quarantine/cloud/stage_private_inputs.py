#!/usr/bin/env python3
"""Host-side staging helper for Phase B's two private, gitignored inputs.

`modal_phase_b.py`'s GPU stages fetch `eval_rows.jsonl` (question/alias text)
and `anchor_extract.safetensors` (ON activation cache) from a private HF
dataset repo (STAGING_REPO in that file) rather than from a local bind mount,
because Modal containers cannot read this machine's disk. Both files are
gitignored by experiment-local `.gitignore` (`directions/`, `analysis/`) and
`experiments/common/artifacts/.../PROVENANCE.md` explicitly records that
neither is promoted/committed anywhere -- they must stay private.

This script only COMPUTES what would be uploaded (path, size, sha256) unless
`--execute` is passed. Default is `--dry-run` behavior even without the flag,
so `python3 stage_private_inputs.py` with no arguments is always safe to run.
Uploading question/alias text to a cloud service, even a private repo, is a
lead-authorized step at launch time -- the same posture as the GPU launch
itself -- and is deliberately not something this harness runs on its own.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP_ROOT = HERE.parent
PRIVATE_FILES = {
    "eval_rows.jsonl": EXP_ROOT / "analysis" / "gemma4-e4b" / "eval_rows.jsonl",
    "anchor_extract.safetensors": EXP_ROOT / "analysis" / "gemma4-e4b" / "anchor_extract.safetensors",
}
STAGING_REPO = "professorsynapse/eh-gemma4-kvseam-phaseb-staging"
DEST_IN_REPO = {
    "eval_rows.jsonl": "phase-b-r1/eval_rows.jsonl",
    "anchor_extract.safetensors": "phase-b-r1/anchor_extract.safetensors",
}


def _sha256(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        while True:
            b = fh.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def build_manifest() -> dict:
    manifest = {"staging_repo": STAGING_REPO, "files": []}
    for name, path in PRIVATE_FILES.items():
        entry = {"name": name, "local_path": str(path),
                  "dest_in_repo": DEST_IN_REPO[name]}
        if not path.is_file():
            entry["status"] = "MISSING"
        else:
            entry["status"] = "present"
            entry["size_bytes"] = path.stat().st_size
            entry["sha256"] = _sha256(path)
        manifest["files"].append(entry)
    return manifest


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--execute", action="store_true",
                     help="Actually upload to the private staging repo. "
                          "Requires HF_TOKEN in the environment and lead "
                          "authorization -- absent this flag, only the "
                          "manifest is printed.")
    ap.add_argument("--dry-run", action="store_true",
                     help="Explicit no-op flag; identical to omitting "
                          "--execute. Kept for symmetry with modal_phase_b.py.")
    args = ap.parse_args()

    manifest = build_manifest()
    print(json.dumps(manifest, indent=2, sort_keys=True))

    missing = [f for f in manifest["files"] if f["status"] == "MISSING"]
    if missing:
        print(f"[stage-private-inputs] {len(missing)} file(s) missing locally; "
              "cannot stage until they exist.", file=sys.stderr)
        return 1 if args.execute else 0

    if not args.execute:
        print("[stage-private-inputs] DRY RUN (default) -- nothing uploaded. "
              "Pass --execute (with HF_TOKEN set and lead authorization) to "
              "actually upload.", file=sys.stderr)
        return 0

    import os
    if not os.environ.get("HF_TOKEN"):
        print("[stage-private-inputs] FATAL: --execute passed but HF_TOKEN "
              "is not in the environment.", file=sys.stderr)
        return 2

    from huggingface_hub import HfApi
    api = HfApi()
    api.create_repo(STAGING_REPO, repo_type="dataset", exist_ok=True, private=True)
    for f in manifest["files"]:
        print(f"[stage-private-inputs] uploading {f['local_path']} -> "
              f"{STAGING_REPO}:{f['dest_in_repo']} ...", flush=True)
        api.upload_file(path_or_fileobj=f["local_path"],
                         path_in_repo=f["dest_in_repo"],
                         repo_id=STAGING_REPO, repo_type="dataset")
    print("[stage-private-inputs] upload complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
