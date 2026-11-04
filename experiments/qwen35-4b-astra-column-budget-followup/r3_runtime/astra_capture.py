"""Check the registered capture against the engine's existing resume fingerprint.

The host writes the expected request before capture. The engine independently
fingerprints its actual inputs; preparation checks that fingerprint and files.
This is ordinary job provenance, not an isolation or authenticity boundary.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import numpy as np

from . import astra_render, capture
from .util import HarnessError, canonical_sha256, sha256_file

SCHEMA = "ehr-astra-capture-request/v1"


def fingerprint(identity: dict) -> str:
    # Format-identical to the installed engine RunLog; no engine internals imported.
    payload = {"schema_version": 1, "run_config": identity, "required_fields": []}
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(raw).hexdigest()


def make_request(proposal, model_dir: Path, rows: list[dict]) -> dict:
    """CPU/tokenizer-only, run inside the same container paths as extraction."""
    model_dir = Path(model_dir).resolve()
    files = {str(p.relative_to(model_dir)): sha256_file(p)
             for p in sorted(model_dir.rglob("*")) if p.is_file()}
    expected = proposal.raw["model"]["files_sha256"]
    if any(files.get(k) != v for k, v in expected.items()):
        raise HarnessError("CAPTURE_BASE", "capture model shards do not match the proposal")
    saved = {k: os.environ.get(k) for k in ("HS20NWE_RENDER_MODEL", "HS20NWE_RENDER_REVISION")}
    try:
        os.environ["HS20NWE_RENDER_MODEL"] = str(model_dir)
        os.environ["HS20NWE_RENDER_REVISION"] = proposal.raw["model"]["revision"]
        inputs = [{"row_key": r["row_key"],
                   "prompt_sha256": hashlib.sha256(astra_render.render_pstruct(r).encode()).hexdigest()}
                  for r in rows]
    finally:
        for k, value in saved.items():
            if value is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = value
    spec = proposal.raw["development"]["capture"]
    identity = {"schema_version": "mechinterp-capture-journal/v1",
                "run": {"model": {"path": str(model_dir), "files": files},
                        "revision": proposal.raw["model"]["revision"], "adapter": None,
                        "render": {"callable": "r3_runtime.astra_render:render_pstruct",
                                   "source_sha256": sha256_file(Path(astra_render.__file__))},
                        "content_end": None},
                "inputs": inputs, "families": ["anchor"], "layers": [int(spec["hidden_state"])],
                "every_k": int(spec["every_k"]), "max_new_tokens": int(spec["max_new_tokens"]),
                "use_cache": bool(spec["use_cache"]), "forward_only": True, "save_tensors": True,
                "sites": [{"layer": int(proposal.patch["decoder_block"]), "module": "mlp.down_proj", "tensor": t}
                          for t in ("input", "output")], "manifest_extra": None}
    return {"schema_version": SCHEMA, "proposal_sha256": proposal.sha256, "identity": identity,
            "fingerprint": fingerprint(identity)}


def verify_request(proposal, directory: Path, request_path: Path, keys: list[str]) -> dict:
    request = json.loads(Path(request_path).read_text())
    identity = request.get("identity", {})
    if (request.get("schema_version") != SCHEMA or request.get("proposal_sha256") != proposal.sha256
            or request.get("fingerprint") != fingerprint(identity)):
        raise HarnessError("CAPTURE_BINDING", "capture request is not bound to this proposal")
    run = identity.get("run") or {}
    renderer = run.get("render") or {}
    spec = proposal.raw["development"]["capture"]
    expected_sites = [{"layer": int(proposal.patch["decoder_block"]), "module": "mlp.down_proj", "tensor": t}
                      for t in ("input", "output")]
    model = run.get("model") or {}
    if (run.get("revision") != proposal.raw["model"]["revision"] or run.get("adapter") is not None
            or renderer != {"callable": "r3_runtime.astra_render:render_pstruct",
                            "source_sha256": sha256_file(Path(astra_render.__file__))}
            or run.get("content_end") is not None or identity.get("manifest_extra") is not None
            or any(model.get("files", {}).get(k) != v for k, v in proposal.raw["model"]["files_sha256"].items())
            or identity.get("families") != ["anchor"] or identity.get("layers") != [int(spec["hidden_state"])]
            or identity.get("sites") != expected_sites or identity.get("forward_only") is not True
            or identity.get("save_tensors") is not True or identity.get("use_cache") != spec["use_cache"]
            or identity.get("every_k") != spec["every_k"] or identity.get("max_new_tokens") != spec["max_new_tokens"]
            or [r.get("row_key") for r in identity.get("inputs", [])] != keys):
        raise HarnessError("CAPTURE_BINDING", "capture request differs from the registered base, prompt, sites or rows")
    directory = Path(directory)
    meta_path = directory / "capture.runlog.jsonl.meta.json"
    meta = json.loads(meta_path.read_text())
    if meta.get("complete") is not True or meta.get("fingerprint") != request["fingerprint"]:
        raise HarnessError("CAPTURE_BINDING", "engine capture fingerprint differs from the expected request")
    manifest = capture.load_manifest(directory)
    journal_path = directory / "capture.runlog.jsonl"
    journal = [json.loads(line) for line in journal_path.read_text().splitlines() if line.strip()]
    if journal != manifest["rows"] or manifest.get("weight_patch") is not None:
        raise HarnessError("CAPTURE_BINDING", "capture manifest is patched or differs from the completed journal")
    for row in manifest["rows"]:
        if (row.get("seq_total") != row.get("prompt_len") or row.get("content_end") != row["prompt_len"] - 1
                or row.get("site_captures", {}).get("anchor", {}).get("positions") != [row["prompt_len"] - 1]):
            raise HarnessError("CAPTURE_POSITION", "capture is not exactly the last prompt token")
    return {"request_sha256": sha256_file(request_path), "journal_sha256": sha256_file(journal_path),
            "meta_sha256": sha256_file(meta_path), "fingerprint": request["fingerprint"]}


def linear_consistency(U: np.ndarray, K: np.ndarray, outputs: np.ndarray, W: np.ndarray, proposal) -> dict:
    expected = np.concatenate([U, K]) @ np.asarray(W, dtype=np.float64).T
    outputs = np.asarray(outputs, dtype=np.float64)
    if outputs.shape != expected.shape or not np.isfinite(outputs).all():
        raise HarnessError("CAPTURE_LINEAR", "down-projection output has the wrong shape or nonfinite values")
    limits = proposal.raw["validation"]
    errors = np.linalg.norm(outputs - expected, axis=1)
    bounds = float(limits["linear_absolute_l2_floor"]) + float(limits["linear_relative_l2_max"]) * np.linalg.norm(expected, axis=1)
    if np.any(errors > bounds):
        raise HarnessError("CAPTURE_LINEAR", "captured down-projection output does not agree with the pinned W @ input")
    return {"max_error_to_bound_ratio": float(np.max(errors / bounds)), "rows": len(expected),
            "limits": limits, "output_digest": canonical_sha256(outputs.tolist())}
