#!/usr/bin/env python3
"""Host-side staging helper for Phase B's two private, gitignored inputs.

`modal_phase_b.py`'s GPU stages read `eval_rows.jsonl` (question/alias text)
and `anchor_extract.safetensors` (ON activation cache) directly off the
`eh-gemma4-e4b-kv-seam-quarantine-phase-b-logs` Modal Volume (VOL_MOUNT in
that file, under `private-inputs/`) rather than from a local bind mount,
because Modal containers cannot read this machine's disk. Both files are
gitignored by experiment-local `.gitignore` (`directions/`, `analysis/`) and
`experiments/common/artifacts/.../PROVENANCE.md` explicitly records that
neither is promoted/committed anywhere -- they must stay private.

Revision 2026-07-30 lead decision (AMENDMENT.md LAUNCH RECORD): private
inputs go DIRECTLY to the Modal Volume via `modal volume put`, not to any HF
dataset repo -- a private HF dataset repo is still a third-party host outside
Modal's own trust boundary for no benefit here, since the volume is already
scoped to this app and already the thing the GPU stages read from.

This script only COMPUTES what would be uploaded (path, size, sha256) unless
`--execute` is passed. Default is `--dry-run` behavior even without the flag,
so `python3 stage_private_inputs.py` with no arguments is always safe to run.
Uploading question/alias text to a cloud service, even a private volume, is a
lead-authorized step at launch time -- the same posture as the GPU launch
itself -- and is deliberately not something this harness runs on its own.

`--execute` shells out to the `modal` CLI's `volume put` / `volume get`
verbs. Neither is in `.claude/hooks/launch_guard.sh`'s blocked-substring list
(`modal run` / `modal deploy` / `modal app run` / `hf jobs run` /
`huggingface-cli jobs run` / `sbatch `) -- uploading a file to a volume does
not spawn a container or spend GPU time, unlike the stages this staging step
feeds. After upload, each file is re-downloaded from the volume to a temp
path and re-hashed locally ("verify hashes in-volume" -- round-trip through
Modal's own storage, not just trusting the upload's exit code) before the
temp copy is deleted.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP_ROOT = HERE.parent
PRIVATE_FILES = {
    "eval_rows.jsonl": EXP_ROOT / "analysis" / "gemma4-e4b" / "eval_rows.jsonl",
    "anchor_extract.safetensors": EXP_ROOT / "analysis" / "gemma4-e4b" / "anchor_extract.safetensors",
}
# Must match modal_phase_b.py's `vol` (modal.Volume.from_name(...)) and
# VOL_MOUNT exactly -- this script and that one address the SAME volume.
VOLUME_NAME = "eh-gemma4-e4b-kv-seam-quarantine-phase-b-logs"
DEST_IN_VOLUME = {
    "eval_rows.jsonl": "private-inputs/eval_rows.jsonl",
    "anchor_extract.safetensors": "private-inputs/anchor_extract.safetensors",
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
    manifest = {"volume": VOLUME_NAME, "files": []}
    for name, path in PRIVATE_FILES.items():
        entry = {"name": name, "local_path": str(path),
                  "dest_in_volume": DEST_IN_VOLUME[name]}
        if not path.is_file():
            entry["status"] = "MISSING"
        else:
            entry["status"] = "present"
            entry["size_bytes"] = path.stat().st_size
            entry["sha256"] = _sha256(path)
        manifest["files"].append(entry)
    return manifest


def _modal_volume_put(local_path: Path, remote_path: str) -> None:
    cmd = ["modal", "volume", "put", "--force", VOLUME_NAME, str(local_path), remote_path]
    print(f"[stage-private-inputs] $ {' '.join(cmd)}", flush=True)
    subprocess.run(cmd, check=True)


def _modal_volume_get(remote_path: str, local_dest: Path) -> None:
    cmd = ["modal", "volume", "get", "--force", VOLUME_NAME, remote_path, str(local_dest)]
    print(f"[stage-private-inputs] $ {' '.join(cmd)}", flush=True)
    subprocess.run(cmd, check=True)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--execute", action="store_true",
                     help="Actually upload to the Modal Volume via "
                          "`modal volume put`, then re-download each file "
                          "and re-hash it to verify the in-volume copy "
                          "matches -- lead authorization required (same "
                          "posture as the GPU launch itself). Absent this "
                          "flag, only the manifest is printed.")
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
              "Pass --execute (with lead authorization) to actually upload.",
              file=sys.stderr)
        return 0

    verify: list[dict] = []
    with tempfile.TemporaryDirectory() as td:
        for f in manifest["files"]:
            local_path = Path(f["local_path"])
            remote_path = f["dest_in_volume"]
            _modal_volume_put(local_path, remote_path)

            roundtrip_path = Path(td) / f["name"]
            _modal_volume_get(remote_path, roundtrip_path)
            roundtrip_sha = _sha256(roundtrip_path)
            match = roundtrip_sha == f["sha256"]
            verify.append({
                "name": f["name"], "dest_in_volume": remote_path,
                "local_sha256": f["sha256"], "roundtrip_sha256": roundtrip_sha,
                "hash_match": match,
            })
            print(f"[stage-private-inputs] {f['name']}: local sha256="
                  f"{f['sha256']} roundtrip sha256={roundtrip_sha} "
                  f"match={match}", flush=True)
            if not match:
                print(f"[stage-private-inputs] FATAL: hash mismatch for "
                      f"{f['name']} after upload -- volume copy does NOT "
                      "match the local file. Stages reading this volume "
                      "would run on corrupted/truncated input.",
                      file=sys.stderr)
                return 3

    print(json.dumps({"upload_complete": True, "verify": verify}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
