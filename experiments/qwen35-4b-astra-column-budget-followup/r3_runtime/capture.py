"""Manifest-only, hash-checked reading of ``mechinterp-capture/v2`` output.

Only files named by the completed manifest are ever opened, each after its
sha256 is verified; stray files in the directory are ignored. Portable
filenames come from ``capture_files`` / ``site_captures`` (unsafe row keys are
hash-encoded by the engine), never from the row key.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from .util import HarnessError, sha256_file

MANIFEST_SCHEMA = "mechinterp-capture/v2"


def site_key(block: int, module: str, tensor: str) -> str:
    return f"L{block}.{module}.{tensor}"


def load_manifest(directory: Path) -> dict:
    path = Path(directory) / "manifest.json"
    if not path.is_file():
        raise HarnessError("CAPTURE_INCOMPLETE", f"no completed manifest in {directory}")
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != MANIFEST_SCHEMA:
        raise HarnessError("CAPTURE_SCHEMA", "capture manifest is not mechinterp-capture/v2")
    if manifest.get("complete") is not True:
        raise HarnessError("CAPTURE_INCOMPLETE", "capture manifest is not marked complete")
    keys = [r["row_key"] for r in manifest["rows"]]
    if len(set(keys)) != len(keys):
        raise HarnessError("CAPTURE_DUP", "duplicate row keys in capture manifest")
    return manifest


def verified_path(directory: Path, info: dict) -> Path:
    name = info["file"]
    if not isinstance(name, str) or Path(name).name != name or "/" in name or "\\" in name:
        raise HarnessError("CAPTURE_UNSAFE", "capture manifest names an unsafe file")
    path = Path(directory) / name
    if path.is_symlink() or not path.is_file():
        raise HarnessError("CAPTURE_MISSING", f"committed capture file missing: {name}")
    if sha256_file(path) != info["sha256"]:
        raise HarnessError("CAPTURE_HASH", f"capture file hash mismatch: {name}")
    return path


def _load(path: Path, key: str) -> np.ndarray:
    from safetensors.numpy import load_file

    tensors = load_file(str(path))
    if key not in tensors:
        raise HarnessError("CAPTURE_KEY", f"{path.name} lacks tensor {key}")
    return np.asarray(tensors[key], dtype=np.float64)


def read_row(directory: Path, record: dict, *, hidden_state: int, sites: list[tuple[int, str, str]],
             family: str = "anchor") -> dict:
    """Return {'residual': (d,), 'sites': {key: (n,)}} for one manifest row."""
    if not record.get("answered"):
        raise HarnessError("CAPTURE_UNANSWERED", f"row {record['row_key']!r} has no capture")
    residual_info = record.get("capture_files", {}).get(family)
    if residual_info is None:
        raise HarnessError("CAPTURE_FAMILY", f"row {record['row_key']!r} lacks the {family} residual file")
    residual = _load(verified_path(directory, residual_info), f"L{hidden_state}")
    if residual.shape[0] != 1:
        raise HarnessError("CAPTURE_SHAPE", "anchor residual must hold exactly one position")
    out = {"residual": residual[0], "sites": {}}
    if sites:
        site_info = record.get("site_captures", {}).get(family)
        if site_info is None:
            raise HarnessError("CAPTURE_SITES", f"row {record['row_key']!r} lacks site captures")
        path = verified_path(directory, site_info)
        for block, module, tensor in sites:
            key = site_key(block, module, tensor)
            arr = _load(path, key)
            if arr.shape[0] != 1:
                raise HarnessError("CAPTURE_SHAPE", "anchor site must hold exactly one position")
            out["sites"][key] = arr[0]
    return out


def check_rows_covered(manifest: dict, expected_keys: list[str]) -> None:
    got = [r["row_key"] for r in manifest["rows"]]
    if sorted(got) != sorted(expected_keys):
        raise HarnessError("CAPTURE_ROWS", "capture manifest rows differ from the registered population")
    unanswered = [r["row_key"] for r in manifest["rows"] if not r.get("answered")]
    if unanswered:
        raise HarnessError("CAPTURE_ROWS", f"{len(unanswered)} captured rows are unanswered")
