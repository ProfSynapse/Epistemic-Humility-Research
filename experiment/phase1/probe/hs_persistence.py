#!/usr/bin/env python3
"""Tensor/manifest persistence + resume helpers for the hidden-state harness.

Split out of hidden_state_probe.py (SRP refactor). Owns the safetensors writer,
the filesystem-safe key sanitizer, the resume-state readers (done row keys,
tensor-shape reconstruction), the emitted-tensor verifier, and the JSON writer.
None of these read PROBE_DIR; they take explicit paths from the facade run-loop.
"""

from __future__ import annotations

import json
from pathlib import Path

import hidden_state_schema as schema


def load_done_row_keys(rows_path: Path) -> set[str]:
    """Row keys already written to the append-log (resume; probe.py idiom)."""
    done: set[str] = set()
    if not rows_path.exists():
        return done
    with rows_path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            key = row.get("probe_pool_row_key") or row.get("row_key")
            if key:
                done.add(key)
    return done


def _persist_row_tensors(out_dir, key, cfg_sha, h_base, h_lora, delta, config,
                         tensor_shapes) -> None:
    """Persist per-arm tensors for one row as safetensors (lazy numpy import).

    numpy is imported lazily so the row-record/append path stays importable
    without it; persistence is where the array dependency legitimately enters.
    """
    import numpy as np  # noqa: PLC0415
    from safetensors.numpy import save_file  # noqa: PLC0415

    persist_dtype = config["extraction"]["persist_dtype"]
    np_dtype = getattr(np, persist_dtype)
    # M1: honor extraction.layer_list. null => persist ALL captured layers; a
    # list => persist ONLY those layer ids (the full stack is still captured and
    # shape-validated upstream; this filters what reaches disk). Advertised knob
    # is now live, so the manifest's layer_list matches the persisted tensors.
    layer_list = config["extraction"].get("layer_list")
    keep_layers = set(layer_list) if layer_list is not None else None
    roles = {"h_base": h_base, "h_lora": h_lora}
    if delta is not None:
        roles["delta"] = delta

    safe_key = safe_tensor_key(key)
    for role, layer_vectors in roles.items():
        selected = {
            layer: vec for layer, vec in layer_vectors.items()
            if keep_layers is None or layer in keep_layers
        }
        if not selected:
            raise ValueError(
                f"extraction.layer_list {sorted(keep_layers)} selected no "
                f"captured layers (available 0..{len(layer_vectors) - 1}); "
                "check the configured layer ids"
            )
        tensors = {
            f"L{layer}": np.asarray(vec, dtype=np_dtype)
            for layer, vec in selected.items()
        }
        metadata = schema.safetensors_metadata(cfg_sha, safe_key, role)
        schema.validate_safetensors_metadata(metadata)
        path = out_dir / f"{safe_key}__{role}.safetensors"
        save_file(tensors, str(path), metadata=metadata)
        any_layer = next(iter(layer_vectors.values()))
        tensor_shapes[role] = [len(layer_vectors), len(any_layer)]


def safe_tensor_key(key: str) -> str:
    """Filesystem-safe tensor shard stem while preserving existing pipe behavior."""
    safe = key.replace("|", "_")
    for char in (":", "/", "\\", "<", ">", '"', "?", "*"):
        safe = safe.replace(char, "_")
    return safe


def _reconstruct_tensor_shapes(out_dir: Path, rows_path: Path) -> dict:
    """Rebuild tensor_shapes for a FULLY-resumed run from on-disk artifacts.

    On a resume where every slice row is already in the append-log, _extract_rows
    forwards nothing, so the in-memory tensor_shapes stays empty. The finalize
    gate (Decision D-bis) requires a status=ok manifest to carry non-None
    tensor_shapes, so a resumed run must reconstruct the same shapes a fresh run
    would have stamped — otherwise an idempotent re-run crashes at finalize.

    Faithful to the fresh-run value `[len(layer_vectors), len(any_layer)]`
    (hidden_state_probe.py: _persist_row_tensors): the FULL captured layer count
    (== the per-row record's `layer_count`, which is M1-independent — layer_list
    filters what reaches disk, not what is captured) and the hidden_dim. The
    roles present are derived from the shards actually on disk so persist_delta is
    honored without re-reading the config. Returns {} if nothing is recoverable
    (no rows or no shards), leaving the caller's None-tensor_shapes gate to fire.
    """
    last_record = None
    if rows_path.exists():
        with rows_path.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    last_record = json.loads(line)
    if last_record is None:
        return {}
    layer_count = last_record.get("layer_count")
    hidden_dim = last_record.get("hidden_dim")
    if layer_count is None or hidden_dim is None:
        return {}

    # Roles present on disk (h_base / h_lora / optionally delta), from the shard
    # filenames `<key>__<role>.safetensors`. Using disk-truth keeps delta in iff
    # it was persisted, with no dependence on the config's persist_delta flag.
    roles = {
        shard.stem.rsplit("__", 1)[1]
        for shard in out_dir.glob("*.safetensors")
        if "__" in shard.stem
    }
    return {role: [layer_count, hidden_dim] for role in sorted(roles)}


def _verify_emitted(out_dir: Path, base_arm, active_arm, config) -> bool:
    """Decision D-bis: verified=True ONLY if expected tensor shards exist.

    The numerical h_base != h_lora check is GPU-only (real forward); on CPU the
    structural existence check is the strongest honest verification, so this
    never hand-sets verified on a run that emitted no tensors.
    """
    shards = list(out_dir.glob("*.safetensors"))
    return len(shards) > 0


def _write_json(path: Path, obj: dict) -> None:
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")
