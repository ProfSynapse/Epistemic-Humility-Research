#!/usr/bin/env python3
"""Incremental full-depth final-prompt-token capture for one approved model stage."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

from instrument_common import (
    ANALYSIS, COMMITTED, ROOT, atomic_json, atomic_jsonl, instrument_fingerprint,
    load_jsonl, load_yaml, require_pinned_container, sha256_file,
)
from source_and_generate import render_prompt


def tensor_sha256(array: np.ndarray) -> str:
    value = np.ascontiguousarray(array)
    h = hashlib.sha256()
    h.update(str(value.dtype).encode())
    h.update(json.dumps(list(value.shape)).encode())
    h.update(value.tobytes(order="C"))
    return h.hexdigest()


def shard_name(row_key: str) -> str:
    return hashlib.sha256(row_key.encode()).hexdigest() + ".safetensors"


def capture_content_digest(
    row_key: str, token_ids_sha256: str, anchor_index: int, model: str,
    model_revision: str, tensor_hashes: list[str],
) -> str:
    payload = {
        "row_key": row_key, "token_ids_sha256": token_ids_sha256,
        "anchor_index": anchor_index, "model": model, "model_revision": model_revision,
        "tensor_hashes": tensor_hashes,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def validate_activation_row(
    root: Path,
    row_key: str,
    records: list[dict[str, Any]],
    expected_states: int,
    expected_model: str | None = None,
    expected_revision: str | None = None,
    expected_fingerprint: str | None = None,
) -> list[str]:
    from safetensors.numpy import load_file
    errors: list[str] = []
    required = {
        "row_key", "hs_index", "shard_key", "dtype", "shape",
        "token_ids_sha256", "anchor_index", "model", "model_revision",
        "tensor_sha256", "instrument_fingerprint", "capture_content_digest",
    }
    for i, rec in enumerate(records):
        missing = sorted(required - set(rec))
        if missing:
            errors.append(f"{row_key}: index record {i} missing {missing}")
    if errors:
        return errors
    if any(rec.get("row_key") != row_key for rec in records):
        errors.append(f"{row_key}: row-key binding mismatch")
    indices = [int(rec.get("hs_index", -1)) for rec in records]
    if len(indices) != expected_states or len(indices) != len(set(indices)) or set(indices) != set(range(expected_states)):
        errors.append(f"{row_key}: hidden-state index set is incomplete or non-unique")
    bound_fields = ("token_ids_sha256", "anchor_index", "model", "model_revision", "instrument_fingerprint")
    for field in bound_fields:
        if len({rec.get(field) for rec in records}) != 1:
            errors.append(f"{row_key}: inconsistent {field}")
    if expected_model and any(rec.get("model") != expected_model for rec in records):
        errors.append(f"{row_key}: model binding mismatch")
    if expected_revision and any(rec.get("model_revision") != expected_revision for rec in records):
        errors.append(f"{row_key}: revision binding mismatch")
    if expected_fingerprint and any(rec.get("instrument_fingerprint") != expected_fingerprint for rec in records):
        errors.append(f"{row_key}: instrument fingerprint mismatch")
    shard_paths = {rec.get("shard_key") for rec in records}
    if len(shard_paths) != 1 or None in shard_paths:
        return errors + [f"{row_key}: multiple or missing shard paths"]
    path = root / next(iter(shard_paths))
    if not path.is_file():
        return errors + [f"{row_key}: missing shard"]
    try:
        tensors = load_file(str(path))
    except Exception as exc:
        return errors + [f"{row_key}: unreadable shard: {type(exc).__name__}"]
    for rec in records:
        key = f"hs_{int(rec['hs_index']):03d}"
        if key not in tensors:
            errors.append(f"{row_key}: missing tensor {key}")
            continue
        array = np.asarray(tensors[key])
        if list(array.shape) != rec["shape"] or str(array.dtype) != rec["dtype"]:
            errors.append(f"{row_key}/{key}: dtype or shape mismatch")
        if tensor_sha256(array) != rec["tensor_sha256"]:
            errors.append(f"{row_key}/{key}: tensor digest mismatch")
    ordered = sorted(records, key=lambda x: x["hs_index"])
    if ordered:
        content = capture_content_digest(
            row_key, ordered[0].get("token_ids_sha256", ""), int(ordered[0].get("anchor_index", -1)),
            str(ordered[0].get("model", "")), str(ordered[0].get("model_revision", "")),
            [r["tensor_sha256"] for r in ordered],
        )
        if any(r.get("capture_content_digest") != content for r in records):
            errors.append(f"{row_key}: capture content digest mismatch")
    return errors


def validate_activation_bundle(
    root: Path,
    expected_states: int | None = None,
    expected_model: str | None = None,
    expected_revision: str | None = None,
    expected_fingerprint: str | None = None,
    input_log_path: Path | None = None,
    expected_row_keys: set[str] | None = None,
) -> dict[str, Any]:
    records = load_jsonl(root / "activation_index.jsonl")
    errors: list[str] = []
    by_row: dict[str, list[dict[str, Any]]] = {}
    for rec in records:
        by_row.setdefault(rec.get("row_key", "<missing>"), []).append(rec)
    if expected_states is None:
        expected_states = max((int(r.get("hs_index", -1)) for r in records), default=-1) + 1
    for row_key, row_records in by_row.items():
        errors.extend(validate_activation_row(root, row_key, row_records, expected_states, expected_model, expected_revision, expected_fingerprint))
    if expected_row_keys is not None and set(by_row) != expected_row_keys:
        errors.append("activation index row set does not exactly match current matched pool")
    if input_log_path is not None:
        input_rows = load_jsonl(input_log_path)
        input_by_key = {row.get("row_key"): row for row in input_rows}
        if len(input_by_key) != len(input_rows):
            errors.append("private capture input log has duplicate row keys")
        required_keys = expected_row_keys if expected_row_keys is not None else set(by_row)
        if set(input_by_key) != required_keys:
            errors.append("private capture input row set does not exactly match current matched pool")
        for row_key in sorted(set(by_row) & set(input_by_key)):
            item = input_by_key[row_key]
            token_ids = item.get("token_ids")
            if not isinstance(token_ids, list) or not token_ids:
                errors.append(f"{row_key}: private token evidence is missing")
                continue
            digest = hashlib.sha256(json.dumps(token_ids, separators=(",", ":")).encode()).hexdigest()
            records_for_row = by_row[row_key]
            if (
                item.get("token_ids_sha256") != digest
                or item.get("anchor_index") != len(token_ids) - 1
                or (expected_model is not None and item.get("model") != expected_model)
                or (expected_revision is not None and item.get("model_revision") != expected_revision)
                or (expected_fingerprint is not None and item.get("instrument_fingerprint") != expected_fingerprint)
                or any(rec.get("token_ids_sha256") != digest for rec in records_for_row)
                or any(rec.get("anchor_index") != len(token_ids) - 1 for rec in records_for_row)
            ):
                errors.append(f"{row_key}: private capture input provenance does not reconstruct")
    digest_records = sorted(
        records,
        key=lambda rec: (str(rec.get("row_key", "")), int(rec.get("hs_index", -1))),
    )
    bundle_digest = hashlib.sha256(
        "".join(str(rec.get("tensor_sha256", "<missing>")) for rec in digest_records).encode()
    ).hexdigest()
    return {"status": "pass" if not errors else "fail", "errors": errors, "n_rows": len(by_row), "n_tensors": len(records), "bundle_digest": bundle_digest}


def repair_invalid_rows(
    root: Path, n_states: int, model: str, revision: str, fingerprint: str,
    input_records: dict[str, dict[str, Any]] | None = None,
    expected_row_keys: set[str] | None = None,
) -> tuple[list[dict[str, Any]], set[str]]:
    index_path = root / "activation_index.jsonl"
    index = load_jsonl(index_path)
    by_row: dict[str, list[dict[str, Any]]] = {}
    for rec in index:
        by_row.setdefault(str(rec.get("row_key", "<missing>")), []).append(rec)
    valid: set[str] = set()
    kept: list[dict[str, Any]] = []
    for row_key, records in by_row.items():
        errors = validate_activation_row(root, row_key, records, n_states, model, revision, fingerprint)
        if expected_row_keys is not None and row_key not in expected_row_keys:
            errors.append(f"{row_key}: row is not in current matched pool")
        item = (input_records or {}).get(row_key)
        if input_records is not None:
            token_ids = item.get("token_ids") if item else None
            digest = hashlib.sha256(json.dumps(token_ids, separators=(",", ":")).encode()).hexdigest() if isinstance(token_ids, list) and token_ids else None
            anchor = len(token_ids) - 1 if isinstance(token_ids, list) and token_ids else None
            if (
                not item
                or item.get("token_ids_sha256") != digest
                or item.get("anchor_index") != anchor
                or item.get("model") != model
                or item.get("model_revision") != revision
                or item.get("instrument_fingerprint") != fingerprint
                or any(r.get("token_ids_sha256") != digest for r in records)
                or any(r.get("anchor_index") != anchor for r in records)
            ):
                errors.append(f"{row_key}: private token evidence mismatch")
        if not errors:
            valid.add(row_key)
            kept.extend(records)
            continue
        for shard in {r.get("shard_key") for r in records if r.get("shard_key")}:
            (root / shard).unlink(missing_ok=True)
    atomic_jsonl(
        index_path,
        sorted(kept, key=lambda rec: (str(rec.get("row_key", "")), int(rec.get("hs_index", -1)))),
    )
    return kept, valid


def run_capture(model_id: str) -> dict[str, Any]:
    import torch
    from safetensors.numpy import save_file
    from transformers import AutoModelForCausalLM, AutoTokenizer

    g0g2_path = COMMITTED / model_id / "g0_g2_summary.json"
    if not g0g2_path.is_file() or json.loads(g0g2_path.read_text())["decision_state"] != "ready_for_capture":
        raise RuntimeError("capture hard-stopped: G0-G2 have not passed")
    cfg = load_yaml(ROOT / "cell.yaml")
    require_pinned_container(cfg["containers"]["capture"]["image_digest"])
    model_cfg = cfg["models"][model_id]
    rows = load_jsonl(ANALYSIS / model_id / "matched_rows_private.jsonl")
    if not rows:
        raise RuntimeError("matched private row pool is absent")
    out = ANALYSIS / "exhaust" / "activations" / model_id
    shards = out / "shards"
    shards.mkdir(parents=True, exist_ok=True)
    index_path = out / "activation_index.jsonl"
    fingerprint = instrument_fingerprint()
    inputs_log = ANALYSIS / model_id / "capture_inputs_private.jsonl"
    input_rows = load_jsonl(inputs_log)
    input_records = {r["row_key"]: r for r in input_rows}
    if len(input_records) != len(input_rows):
        raise RuntimeError("private capture input log has duplicate row keys")
    expected_keys = {r["row_key"] for r in rows}
    input_records = {key: value for key, value in input_records.items() if key in expected_keys}
    atomic_jsonl(inputs_log, [input_records[key] for key in sorted(input_records)])
    index, completed = repair_invalid_rows(
        out, model_cfg["n_hidden_states"], model_cfg["repo"], model_cfg["revision"],
        fingerprint, input_records, expected_keys,
    )
    tokenizer = AutoTokenizer.from_pretrained(model_cfg["repo"], revision=model_cfg["revision"], token=None, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(model_cfg["repo"], revision=model_cfg["revision"], torch_dtype=torch.bfloat16, trust_remote_code=True).to("cuda:0").eval()
    actual_layers = int(getattr(model.config, "num_hidden_layers", getattr(getattr(model.config, "text_config", None), "num_hidden_layers", -1)))
    if actual_layers != model_cfg["num_hidden_layers"]:
        raise RuntimeError(f"model shape mismatch: {actual_layers} decoder layers")
    for row in rows:
        row_key = row["row_key"]
        if row_key in completed:
            continue
        prompt = render_prompt(model_id, tokenizer, row)
        encoded = tokenizer(prompt, return_tensors="pt", add_special_tokens=True)
        token_ids = encoded["input_ids"][0].tolist()
        token_ids_digest = hashlib.sha256(json.dumps(token_ids, separators=(",", ":")).encode()).hexdigest()
        anchor = len(token_ids) - 1
        input_records[row_key] = {
            "row_key": row_key,
            "token_ids": token_ids,
            "token_ids_sha256": token_ids_digest,
            "anchor_index": anchor,
            "model": model_cfg["repo"],
            "model_revision": model_cfg["revision"],
            "instrument_fingerprint": fingerprint,
        }
        atomic_jsonl(inputs_log, [input_records[key] for key in sorted(input_records)])
        encoded = {k: v.to("cuda:0") for k, v in encoded.items()}
        with torch.inference_mode():
            output = model(**encoded, output_hidden_states=True, use_cache=False, return_dict=True)
        hidden = output.hidden_states
        if hidden is None or len(hidden) != model_cfg["n_hidden_states"]:
            raise RuntimeError(f"hidden-state count mismatch for {row_key}")
        tensors = {f"hs_{i:03d}": hs[0, anchor].detach().float().cpu().numpy() for i, hs in enumerate(hidden)}
        if any(list(v.shape) != [model_cfg["hidden_size"]] for v in tensors.values()):
            raise RuntimeError(f"hidden-size mismatch for {row_key}")
        shard_rel = f"shards/{shard_name(row_key)}"
        shard_path = out / shard_rel
        tmp = shard_path.with_suffix(".tmp.safetensors")
        save_file(tensors, str(tmp), metadata={"row_key": row_key, "instrument_fingerprint": fingerprint})
        tmp.replace(shard_path)
        hashes = [tensor_sha256(tensors[f"hs_{i:03d}"]) for i in range(len(hidden))]
        content_digest = capture_content_digest(
            row_key, token_ids_digest, anchor, model_cfg["repo"], model_cfg["revision"], hashes
        )
        row_index = [{
            "row_key": row_key, "hs_index": i, "shard_key": shard_rel,
            "dtype": str(tensors[f"hs_{i:03d}"].dtype), "shape": list(tensors[f"hs_{i:03d}"].shape),
            "anchor_index": anchor, "token_ids_sha256": token_ids_digest,
            "model": model_cfg["repo"], "model_revision": model_cfg["revision"],
            "tensor_sha256": hashes[i],
            "instrument_fingerprint": fingerprint, "capture_content_digest": content_digest,
        } for i in range(len(hidden))]
        index = [rec for rec in index if rec["row_key"] != row_key] + row_index
        atomic_jsonl(index_path, sorted(index, key=lambda r: (r["row_key"], r["hs_index"])))
        completed.add(row_key)
    validation = validate_activation_bundle(
        out, model_cfg["n_hidden_states"], model_cfg["repo"], model_cfg["revision"],
        fingerprint, inputs_log, expected_keys,
    )
    expected = {r["row_key"] for r in rows}
    indexed = {r["row_key"] for r in load_jsonl(index_path)}
    coverage = len(expected & indexed) / len(expected)
    summary = {
        "schema_version": 1, "model_id": model_id, "model": model_cfg["repo"],
        "revision": model_cfg["revision"], "n_hidden_states": model_cfg["n_hidden_states"],
        "hidden_size": model_cfg["hidden_size"], "n_rows_expected": len(expected),
        "n_rows_captured": len(expected & indexed), "coverage": coverage,
        "activation_index_sha256": sha256_file(index_path), "bundle_validation": validation,
        "instrument_fingerprint": fingerprint,
    }
    atomic_json(out / "capture_summary_private.json", summary)
    atomic_json(COMMITTED / model_id / "capture_manifest.json", summary)
    if coverage != 1.0 or validation["status"] != "pass":
        raise RuntimeError("capture bundle failed integrity validation")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    cap = sub.add_parser("capture")
    cap.add_argument("--model-id", choices=["gemma4_e4b_it", "qwen3_4b_raw_base"], required=True)
    val = sub.add_parser("validate")
    val.add_argument("--root", type=Path, required=True)
    val.add_argument("--expected-states", type=int)
    args = parser.parse_args()
    if args.command == "capture":
        print(json.dumps(run_capture(args.model_id), indent=2))
    else:
        result = validate_activation_bundle(args.root, args.expected_states)
        print(json.dumps(result, indent=2))
        if result["status"] != "pass":
            raise SystemExit(1)


if __name__ == "__main__":
    main()
