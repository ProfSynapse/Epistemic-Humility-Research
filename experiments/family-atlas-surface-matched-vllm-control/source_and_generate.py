#!/usr/bin/env python3
"""Materialize UMWP and run resumable baseline generation inside the pinned container."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import shutil
import string
import subprocess
import sys
import unicodedata
import urllib.request
from pathlib import Path
from typing import Any, Callable

import numpy as np

from grader_port import grade_generation

from instrument_common import (
    ANALYSIS, ROOT, append_jsonl_fsync, atomic_json, atomic_jsonl, load_jsonl,
    load_yaml, require_pinned_container, require_synaptic_tuner_source, sha256_file,
)

def normalize_question(text: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split())


def _source_name(row: dict[str, Any]) -> str:
    for key in ("source", "dataset", "dataset_name", "original_dataset"):
        if row.get(key):
            return str(row[key])
    raise ValueError(f"UMWP row {row.get('id')} has no native source")


def _original_pair_id(row: dict[str, Any]) -> str:
    value = row.get("id") if bool(row["answerable"]) else row.get("relevant_ids")
    if isinstance(value, list):
        if len(value) != 1:
            raise ValueError(f"row {row.get('id')} must have exactly one relevant_ids value")
        value = value[0]
    if value is None:
        raise ValueError(f"row {row.get('id')} has no original-pair id")
    return str(value)


def canonical_answer_aliases(value: Any) -> list[str]:
    if isinstance(value, list):
        values = value
    else:
        values = [value]
    out: list[str] = []
    for item in values:
        if item is None or isinstance(item, bool):
            continue
        if isinstance(item, (int, float)):
            out.append(format(float(item), ".15g"))
        else:
            candidate = str(item).strip()
            if candidate:
                out.append(candidate)
    return sorted(set(out))


def materialize_source(source_path: Path, out_path: Path, cfg: dict[str, Any]) -> dict[str, Any]:
    source_cfg = cfg["source"]
    if sha256_file(source_path) != source_cfg["raw_sha256"]:
        raise ValueError("UMWP source sha256 does not match cell.yaml")
    rows = load_jsonl(source_path)
    materialized: list[dict[str, Any]] = []
    counts: dict[str, dict[str, int]] = {}
    answerable_ids: dict[str, dict[str, Any]] = {}
    for raw in rows:
        rid = str(raw["id"])
        answerable = bool(raw["answerable"])
        native = _source_name(raw)
        side = "answerable" if answerable else "unanswerable"
        counts.setdefault(native, {"answerable": 0, "unanswerable": 0})[side] += 1
        if answerable:
            aliases = canonical_answer_aliases(raw.get("answer"))
            if not aliases:
                raise ValueError(f"answerable row {rid} has no answer")
            answerable_ids[rid] = raw
        else:
            aliases = []
        materialized.append({
            "row_key": f"umwp:{rid}", "umwp_id": rid, "source": "umwp",
            "native_source": native, "original_pair_id": _original_pair_id(raw),
            "category_canon": None if raw.get("category") is None else str(raw["category"]),
            "answerable": answerable, "question": str(raw["question"]),
            "aliases": aliases,
        })
    by_key = {row["row_key"]: row for row in materialized}
    for row in materialized:
        if row["answerable"]:
            continue
        peer = by_key.get(f"umwp:{row['original_pair_id']}")
        if not peer or not peer["answerable"] or peer["native_source"] != row["native_source"]:
            raise ValueError(f"invalid same-source pair mapping for {row['row_key']}")
    expected_counts = source_cfg["native_source_counts"]
    checks = {
        "rows": len(rows), "answerable": sum(r["answerable"] for r in materialized),
        "unanswerable": sum(not r["answerable"] for r in materialized),
        "native_source_counts": counts,
    }
    if checks["rows"] != source_cfg["expected_rows"] or checks["answerable"] != source_cfg["expected_answerable"] or checks["unanswerable"] != source_cfg["expected_unanswerable"] or counts != expected_counts:
        raise ValueError(f"UMWP source counts differ from cell.yaml: {checks}")
    atomic_jsonl(out_path, materialized)
    audit = {**checks, "source_sha256": sha256_file(source_path), "pair_mapping_exact": True}
    atomic_json(out_path.parent / "source_audit.json", audit)
    return audit


def validate_source_materialization(cfg: dict[str, Any]) -> dict[str, Any]:
    """Revalidate the raw source and private materialization without trusting an audit file."""
    source_path = ANALYSIS / "source" / "StandardDataset.jsonl"
    rows_path = ANALYSIS / "source" / "rows.jsonl"
    source_cfg = cfg["source"]
    if not source_path.is_file() or not rows_path.is_file():
        raise ValueError("raw UMWP source or private materialization is missing")
    if sha256_file(source_path) != source_cfg["raw_sha256"]:
        raise ValueError("raw UMWP sha256 changed")
    raw_rows, rows = load_jsonl(source_path), load_jsonl(rows_path)
    if len(raw_rows) != source_cfg["expected_rows"] or len(rows) != source_cfg["expected_rows"]:
        raise ValueError("UMWP raw/materialized row coverage is not exactly 5200")
    raw_by_id = {str(r["id"]): r for r in raw_rows}
    row_by_key = {r["row_key"]: r for r in rows}
    if len(raw_by_id) != len(raw_rows) or len(row_by_key) != len(rows):
        raise ValueError("UMWP IDs are not unique")
    counts: dict[str, dict[str, int]] = {}
    for rid, raw in raw_by_id.items():
        key = f"umwp:{rid}"
        row = row_by_key.get(key)
        if row is None or row["question"] != str(raw["question"]):
            raise ValueError(f"materialized row mismatch for {key}")
        native = _source_name(raw)
        side = "answerable" if raw["answerable"] else "unanswerable"
        counts.setdefault(native, {"answerable": 0, "unanswerable": 0})[side] += 1
        if row["original_pair_id"] != _original_pair_id(raw) or row["native_source"] != native:
            raise ValueError(f"pair/source mapping mismatch for {key}")
        expected_category = None if raw.get("category") is None else str(raw["category"])
        if (
            row.get("umwp_id") != rid
            or row.get("source") != "umwp"
            or row.get("answerable") is not bool(raw["answerable"])
            or row.get("category_canon") != expected_category
        ):
            raise ValueError(f"materialized identity/class fields mismatch for {key}")
        if raw["answerable"]:
            if row["aliases"] != canonical_answer_aliases(raw.get("answer")):
                raise ValueError(f"answer aliases mismatch for {key}")
        elif row["aliases"] != []:
            raise ValueError(f"unanswerable aliases consumed for {key}")
    if counts != source_cfg["native_source_counts"]:
        raise ValueError("UMWP native-source counts changed")
    return {"source_sha256": source_cfg["raw_sha256"], "rows": len(rows), "native_source_counts": counts, "pair_mapping_exact": True}


def build_exclusion_manifest(model_id: str, rows: list[dict[str, Any]], cfg: dict[str, Any]) -> set[str]:
    prior_cfg = cfg["models"][model_id]["prior_atlas_pool"]
    path = Path(prior_cfg["local_artifact"])
    if not path.is_file() or sha256_file(path) != prior_cfg["sha256"]:
        raise ValueError("pinned model-specific prior-atlas artifact is missing or changed")
    prior: dict[str, list[str]] = {}
    for row in load_jsonl(path):
        if row.get("question"):
            prior.setdefault(normalize_question(str(row["question"])), []).append(prior_cfg["source_experiment"])
    excluded = []
    for row in rows:
        normalized = normalize_question(row["question"])
        if normalized in prior:
            excluded.append({
                "row_key": row["row_key"],
                "normalized_text_hash": __import__("hashlib").sha256(normalized.encode()).hexdigest(),
                "matched_prior_paths": sorted(set(prior[normalized])),
            })
    path = ANALYSIS / model_id / "prior_atlas_exclusions_private.jsonl"
    atomic_jsonl(path, excluded)
    atomic_json(ANALYSIS / model_id / "prior_atlas_exclusion_summary_private.json", {
        "model_id": model_id, "n_source_rows": len(rows), "n_excluded": len(excluded),
        "n_eligible": len(rows) - len(excluded),
        "prior_source_experiment": prior_cfg["source_experiment"],
        "prior_artifact_sha256": prior_cfg["sha256"],
    })
    return {r["row_key"] for r in excluded}


def surface_scalars(question: str, prompt_tokens: int) -> dict[str, float]:
    n = max(len(question), 1)
    return {
        "rendered_prompt_token_count": float(prompt_tokens),
        "question_char_count": float(len(question)),
        "question_word_count": float(len(question.split())),
        "question_line_count": float(question.count("\n") + 1),
        "digit_count": float(sum(c.isdigit() for c in question)),
        "digit_fraction": sum(c.isdigit() for c in question) / n,
        "punctuation_count": float(sum(c in string.punctuation for c in question)),
        "punctuation_fraction": sum(c in string.punctuation for c in question) / n,
        "newline_count": float(question.count("\n")),
        "newline_fraction": question.count("\n") / n,
        "uppercase_count": float(sum(c.isupper() for c in question)),
        "uppercase_fraction": sum(c.isupper() for c in question) / n,
    }


def render_prompt(model_id: str, tokenizer: Any, row: dict[str, Any]) -> str:
    if model_id == "gemma4_e4b_it":
        from render_gemma import render_with_tokenizer
    elif model_id == "qwen3_4b_raw_base":
        from render_qwen import render_with_tokenizer
    else:
        raise ValueError(f"unknown model renderer {model_id!r}")
    return render_with_tokenizer(tokenizer, row)


def resolve_eos_ids(tokenizer: Any) -> list[int]:
    ids: set[int] = set()
    raw = tokenizer.eos_token_id
    if isinstance(raw, (list, tuple, set)):
        ids.update(int(value) for value in raw if value is not None)
    elif raw is not None:
        ids.add(int(raw))
    for token in ("<|im_end|>", "<end_of_turn>"):
        value = tokenizer.convert_tokens_to_ids(token)
        if isinstance(value, int) and value >= 0 and value != tokenizer.unk_token_id:
            ids.add(value)
    if not ids:
        raise RuntimeError("tokenizer provides no valid EOS token id")
    return sorted(ids)


def assign_role(answerable: bool, grade: dict[str, Any]) -> str | None:
    g = grade["full_grader_dict"]
    if answerable:
        return "known_correct_answered" if g["well_formed_correct"] and not g["refused"] else None
    if g["clean_tighten"]:
        return "unknown_refused"
    if g["answered"] and not g["refused"]:
        return "confab"
    return None


class BaselineRunLog:
    STANDARD_GRADE_FIELDS = {
        "well_formed", "n_answer_keys", "single_answer_key", "trailing_clean",
        "answered", "correct", "well_formed_correct", "refused",
        "semantic_refuse", "degenerate", "clean_tighten", "confidence_valid",
        "terminated_naturally",
    }
    REQUIRED = {
        "row_key", "source", "native_source", "original_pair_id", "category_canon",
        "umwp_id", "answerable",
        "model", "model_revision", "renderer_id", "seed", "generation_text",
        "answer_value", "terminated_naturally", "n_new_tokens", "full_grader_dict",
        "role", "split", "triad_id", "cell_id", "layer", "arm",
        "dose_or_strength", "finish_reason", "last_completion_token_id",
        "eos_token_ids", "prompt_token_ids_sha256", "completion_token_ids",
        "prompt_token_count", "schema_valid", "generation_engine",
        "generation_engine_version", "generation_config_sha256",
        "batch_invariant", "structured_output_backend",
        "structured_output_disable_any_whitespace",
        "prompt_bytes_sha256", "parsed_object", "vllm_version",
        "image_digest", "runtime_versions", "schema_sha256",
        "scheduler_pins", "checkpoint_config_sha256", "resume_history",
        "loader_pins", "hardware_pins",
        "synaptic_tuner_source_fingerprint",
    } | STANDARD_GRADE_FIELDS

    def __init__(self, path: Path):
        self.path = path
        rows = load_jsonl(path)
        keys = [r["row_key"] for r in rows]
        if len(keys) != len(set(keys)):
            raise ValueError("run log has duplicate row keys")
        self.completed = set(keys)

    def append(self, row: dict[str, Any]) -> None:
        missing = self.REQUIRED - set(row)
        if missing:
            raise ValueError(f"run-log record missing {sorted(missing)}")
        full = row["full_grader_dict"]
        if not isinstance(full, dict) or not self.STANDARD_GRADE_FIELDS <= set(full):
            raise ValueError("run log requires the complete grader dictionary")
        if any(row[field] != full[field] for field in self.STANDARD_GRADE_FIELDS):
            raise ValueError("run log flattened grader fields differ from full_grader_dict")
        if row["row_key"] in self.completed:
            return
        append_jsonl_fsync(self.path, row)
        self.completed.add(row["row_key"])


def _fit_surface_basis(rows: list[dict[str, Any]], prompts: list[str], token_counts: list[int], model_id: str) -> None:
    from joblib import dump
    from scipy import sparse
    from sklearn.decomposition import TruncatedSVD
    from sklearn.feature_extraction.text import HashingVectorizer, TfidfTransformer
    from sklearn.preprocessing import StandardScaler

    cfg = load_yaml(ROOT / "cell.yaml")["surface_basis"]["lexical"]
    questions = [r["question"] for r in rows]
    word = HashingVectorizer(n_features=cfg["hash_features_word"], alternate_sign=False, ngram_range=tuple(cfg["word_ngram_range"]), norm=None)
    char = HashingVectorizer(analyzer="char", n_features=cfg["hash_features_char"], alternate_sign=False, ngram_range=tuple(cfg["char_ngram_range"]), norm=None)
    word_tf = TfidfTransformer(sublinear_tf=True).fit_transform(word.transform(questions))
    char_tf = TfidfTransformer(sublinear_tf=True).fit_transform(char.transform(questions))
    word_svd = TruncatedSVD(n_components=cfg["svd_components_word"], random_state=cfg["svd_seed"]).fit(word_tf)
    char_svd = TruncatedSVD(n_components=cfg["svd_components_char"], random_state=cfg["svd_seed"]).fit(char_tf)
    scalar_names = list(surface_scalars("x", 1))
    scalars = np.asarray([[surface_scalars(r["question"], n)[k] for k in scalar_names] for r, n in zip(rows, token_counts)], dtype=np.float64)
    projected = np.hstack([scalars, word_svd.transform(word_tf), char_svd.transform(char_tf)])
    scaler = StandardScaler().fit(projected)
    out = ANALYSIS / model_id / "surface"
    out.mkdir(parents=True, exist_ok=True)
    dump({"word": word, "char": char, "word_tfidf": TfidfTransformer(sublinear_tf=True).fit(word.transform(questions)), "char_tfidf": TfidfTransformer(sublinear_tf=True).fit(char.transform(questions)), "word_svd": word_svd, "char_svd": char_svd, "scaler": scaler, "scalar_names": scalar_names}, out / "basis.joblib")
    atomic_jsonl(out / "coordinates.jsonl", [
        {"row_key": r["row_key"], "scalars": dict(zip(scalar_names, scalars[i].tolist())), "matching_vector": scaler.transform(projected[i:i+1])[0].tolist()}
        for i, r in enumerate(rows)
    ])


def derive_finish_evidence(
    n_new_tokens: int, max_new_tokens: int, last_token_id: int | None,
    eos_token_ids: list[int],
) -> tuple[str, bool]:
    if n_new_tokens < 0 or n_new_tokens > max_new_tokens:
        raise ValueError("completion token count is outside the generation cap")
    if last_token_id is not None and last_token_id in eos_token_ids:
        return "eos_token", True
    if n_new_tokens >= max_new_tokens:
        return "length", False
    return "stopping_criteria", True


def validate_structured_completion(text: str) -> dict[str, Any]:
    """Validate the exact registered JSON object without repair or extraction."""
    try:
        value = json.loads(text)
    except (json.JSONDecodeError, TypeError) as exc:
        raise ValueError("vLLM completion is not one complete JSON value") from exc
    if not isinstance(value, dict) or set(value) != {"answer", "response_confidence"}:
        raise ValueError("vLLM completion does not match the registered object keys")
    confidence = value["response_confidence"]
    if not isinstance(value["answer"], str):
        raise ValueError("vLLM completion answer must be a string")
    if (
        isinstance(confidence, bool)
        or not isinstance(confidence, (int, float))
        or not np.isfinite(float(confidence))
        or not 0.0 <= float(confidence) <= 1.0
    ):
        raise ValueError("vLLM response_confidence must be finite and in [0, 1]")
    return value


def _generation_config(cfg: dict[str, Any], model_id: str) -> dict[str, Any]:
    model_cfg = cfg["models"][model_id]
    vllm_cfg = cfg["generation"]["vllm"]
    return {
        "model": model_cfg["repo"],
        "model_revision": model_cfg["revision"],
        "tokenizer_revision": model_cfg["tokenizer_revision"],
        "engine": "vllm",
        "engine_version": vllm_cfg["expected_version"],
        "model_runner": vllm_cfg["model_runner"],
        "compute_dtype": vllm_cfg["compute_dtype"],
        "trust_remote_code": bool(vllm_cfg["trust_remote_code"]),
        "min_new_tokens": int(cfg["generation"]["min_new_tokens"]),
        "max_new_tokens": int(cfg["generation"]["max_new_tokens"]),
        "seed": int(cfg["seed"]),
        "batch_size": int(cfg["generation"]["batch_size"]),
        "tensor_parallel_size": int(vllm_cfg["tensor_parallel_size"]),
        "max_model_len": int(vllm_cfg["max_model_len"]),
        "gpu_memory_utilization": float(vllm_cfg["gpu_memory_utilization"]),
        "max_num_seqs": int(vllm_cfg["max_num_seqs"]),
        "max_num_batched_tokens": int(vllm_cfg["max_num_batched_tokens"]),
        "limit_mm_per_prompt": dict(
            vllm_cfg["per_model"][model_id]["limit_mm_per_prompt"]
        ),
        "batch_invariant": bool(vllm_cfg["batch_invariant"]),
        "structured_output_backend": vllm_cfg["structured_output_backend"],
        "structured_output_disable_any_whitespace": bool(
            vllm_cfg["structured_output_disable_any_whitespace"]
        ),
        "output_schema": vllm_cfg["output_schema"],
        "minimum_compute_capability": str(
            cfg["containers"]["generation"]["minimum_compute_capability"]
        ),
        "registered_compute_capability": str(
            cfg["containers"]["generation"]["registered_compute_capability"]
        ),
        "hardware_class": cfg["containers"]["generation"]["hardware_class"],
        "registered_host_driver": str(
            cfg["containers"]["generation"]["registered_host_driver"]
        ),
        "synaptic_tuner_source_fingerprint": vllm_cfg["synaptic_tuner_source"]["sha256"],
    }


def generation_config_sha256(config: dict[str, Any]) -> str:
    payload = json.dumps(config, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def build_vllm_command(
    cfg: dict[str, Any], model_id: str, prompts_path: Path, out_dir: Path,
    schema_path: Path, *, resume: bool,
) -> list[str]:
    """Build the generic tuner invocation; no shell interpolation is permitted."""
    gen = _generation_config(cfg, model_id)
    command = [
        sys.executable, str(ROOT.parents[1] / "synaptic-tuner" / "tuner.py"),
        "batch-generate", "--engine", "vllm",
        "--prompts", str(prompts_path), "--out-dir", str(out_dir),
        "--model", gen["model"], "--model-revision", gen["model_revision"],
        "--tokenizer-revision", gen["tokenizer_revision"],
        "--compute-dtype", gen["compute_dtype"],
        "--min-new-tokens", str(gen["min_new_tokens"]),
        "--max-new-tokens", str(gen["max_new_tokens"]),
        "--batch-size", str(gen["batch_size"]), "--seed", str(gen["seed"]),
        "--tensor-parallel-size", str(gen["tensor_parallel_size"]),
        "--max-num-seqs", str(gen["max_num_seqs"]),
        "--max-num-batched-tokens", str(gen["max_num_batched_tokens"]),
        "--max-model-len", str(gen["max_model_len"]),
        "--gpu-memory-utilization", str(gen["gpu_memory_utilization"]),
        "--limit-mm-per-prompt", json.dumps(
            gen["limit_mm_per_prompt"], sort_keys=True, separators=(",", ":")
        ),
        "--structured-output-backend", gen["structured_output_backend"],
        "--expected-vllm-version", gen["engine_version"],
        "--vllm-model-runner", gen["model_runner"],
        "--min-compute-capability", gen["minimum_compute_capability"],
        "--json-schema", str(schema_path),
    ]
    if gen["structured_output_disable_any_whitespace"]:
        command.append("--structured-output-disable-any-whitespace")
    if gen["trust_remote_code"]:
        command.append("--trust-remote-code")
    if resume:
        command.append("--resume")
    return command


def _load_vllm_completions(
    path: Path, expected_rows: list[dict[str, Any]], gen: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    completions = load_jsonl(path)
    by_id: dict[str, dict[str, Any]] = {}
    for item in completions:
        row_id = str(item.get("id", ""))
        if not row_id or row_id in by_id:
            raise ValueError("vLLM completion IDs are missing or duplicated")
        by_id[row_id] = item
    expected = {row["row_key"]: row for row in expected_rows}
    if set(by_id) != set(expected):
        raise ValueError("vLLM completion row set does not exactly match eligible prompts")
    for row_id, item in by_id.items():
        validate_structured_completion(item.get("completion_text"))
        prompt_ids = expected[row_id]["prompt_token_ids_expected"]
        completion_ids = item.get("completion_token_ids")
        prompt_ids_hash = hashlib.sha256(
            json.dumps(prompt_ids, separators=(",", ":")).encode("ascii")
        ).hexdigest()
        if item.get("prompt_token_ids_sha256") != prompt_ids_hash:
            raise ValueError(f"{row_id}: vLLM prompt tokens differ from the registered renderer")
        if not isinstance(completion_ids, list) or not all(isinstance(x, int) for x in completion_ids):
            raise ValueError(f"{row_id}: vLLM completion-token evidence is missing")
        if int(item.get("prompt_token_len", -1)) != len(prompt_ids):
            raise ValueError(f"{row_id}: vLLM prompt-token length does not reconstruct")
        prompt_hash = hashlib.sha256(expected[row_id]["prompt"].encode("utf-8")).hexdigest()
        if item.get("prompt_sha256") != prompt_hash:
            raise ValueError(f"{row_id}: vLLM prompt bytes differ from the registered renderer")
        if len(completion_ids) > gen["max_new_tokens"]:
            raise ValueError(f"{row_id}: vLLM completion exceeds the registered token cap")
        if item.get("finish_reason") not in {"stop", "eos_token", "length"}:
            raise ValueError(f"{row_id}: unsupported vLLM finish reason")
    return by_id


def _load_vllm_provenance(
    path: Path, gen: dict[str, Any], schema_sha256: str, prompts_sha256: str,
) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError("vLLM provenance.json is missing")
    value = json.loads(path.read_text(encoding="utf-8"))
    config = value.get("config", {})
    runtime = value.get("runtime", {})
    expected = {
        "model": gen["model"], "model_revision": gen["model_revision"],
        "tokenizer_revision": gen["tokenizer_revision"], "engine": "vllm",
        "prompts_sha256": prompts_sha256,
        "batch_size": gen["batch_size"], "max_new_tokens": gen["max_new_tokens"],
        "min_new_tokens": gen["min_new_tokens"], "seed": gen["seed"],
        "dtype": gen["compute_dtype"], "json_schema_sha256": schema_sha256,
        "trust_remote_code": gen["trust_remote_code"],
        "expected_vllm_version": gen["engine_version"],
        "vllm_model_runner": gen["model_runner"],
        "vllm_batch_invariant": gen["batch_invariant"],
        "structured_output_backend": gen["structured_output_backend"],
        "structured_output_disable_any_whitespace": gen[
            "structured_output_disable_any_whitespace"
        ],
        "tensor_parallel_size": gen["tensor_parallel_size"],
        "max_num_seqs": gen["max_num_seqs"],
        "max_num_batched_tokens": gen["max_num_batched_tokens"],
        "max_model_len": gen["max_model_len"],
        "limit_mm_per_prompt": gen["limit_mm_per_prompt"],
        "gpu_memory_utilization": gen["gpu_memory_utilization"],
        "min_compute_capability": gen["minimum_compute_capability"],
    }
    if any(config.get(key) != expected_value for key, expected_value in expected.items()):
        raise ValueError("vLLM runtime provenance differs from the registered generation config")
    hardware = runtime.get("hardware", {})
    devices = hardware.get("devices")
    hardware_tokens = [
        token.casefold() for token in gen["hardware_class"].split("_")
        if token and not token.casefold().startswith("sm")
    ]
    hardware_names_match = isinstance(devices, list) and all(
        all(
            token in "".join(character for character in str(device.get("name", "")).casefold() if character.isalnum())
            for token in hardware_tokens
        )
        for device in devices
    )
    if (
        runtime.get("vllm_version") != gen["engine_version"]
        or runtime.get("vllm_model_runner") != gen["model_runner"]
        or runtime.get("vllm_batch_invariant") is not gen["batch_invariant"]
        or runtime.get("structured_outputs") is not True
        or runtime.get("structured_output_backend") != gen["structured_output_backend"]
        or runtime.get("structured_output_disable_any_whitespace")
        is not gen["structured_output_disable_any_whitespace"]
        or runtime.get("documented_compute_capability_floor") != gen["minimum_compute_capability"]
        or runtime.get("effective_compute_capability_floor") != gen["minimum_compute_capability"]
        or not isinstance(devices, list)
        or len(devices) != gen["tensor_parallel_size"]
        or any(
            device.get("compute_capability") != gen["registered_compute_capability"]
            for device in devices
        )
        or not hardware_names_match
        or hardware.get("nvidia_driver_versions") != [gen["registered_host_driver"]]
        or not isinstance(hardware.get("cuda_runtime"), str)
        or not hardware.get("cuda_runtime")
        or not isinstance(hardware.get("torch_version"), str)
        or not hardware.get("torch_version")
        or not isinstance(value.get("config_hash"), str)
    ):
        raise ValueError("vLLM runtime provenance is incomplete or inconsistent")
    return value


def _runtime_versions(expected_vllm_version: str) -> dict[str, Any]:
    import torch
    import transformers

    actual_vllm = importlib.metadata.version("vllm")
    if actual_vllm != expected_vllm_version:
        raise RuntimeError(
            f"vLLM version mismatch: expected {expected_vllm_version}, found {actual_vllm}"
        )
    return {
        "vllm": actual_vllm, "torch": torch.__version__,
        "transformers": transformers.__version__, "cuda": torch.version.cuda,
    }


def run_generation(model_id: str, rows_path: Path) -> None:
    cfg = load_yaml(ROOT / "cell.yaml")
    require_pinned_container(cfg["containers"]["generation"]["image_digest"])
    tuner_source = require_synaptic_tuner_source(cfg)
    from transformers import AutoTokenizer

    validate_source_materialization(cfg)
    model_cfg = cfg["models"][model_id]
    source_rows = load_jsonl(rows_path)
    excluded = build_exclusion_manifest(model_id, source_rows, cfg)
    rows = [row for row in source_rows if row["row_key"] not in excluded]
    gen = _generation_config(cfg, model_id)
    tokenizer = AutoTokenizer.from_pretrained(
        model_cfg["repo"], revision=gen["tokenizer_revision"], token=None,
        trust_remote_code=gen["trust_remote_code"],
    )
    prompts = [render_prompt(model_id, tokenizer, row) for row in rows]
    prompt_token_ids = [tokenizer(p, add_special_tokens=True)["input_ids"] for p in prompts]
    token_counts = [len(ids) for ids in prompt_token_ids]
    _fit_surface_basis(rows, prompts, token_counts, model_id)
    vllm_root = ANALYSIS / model_id / "vllm"
    prompts_path = vllm_root / "prompts_private.jsonl"
    schema_path = vllm_root / "output_schema.json"
    prompt_rows = [
        {
            "id": row["row_key"], "row_key": row["row_key"], "prompt": prompt,
            "prompt_token_ids_expected": ids,
        }
        for row, prompt, ids in zip(rows, prompts, prompt_token_ids)
    ]
    atomic_jsonl(prompts_path, prompt_rows)
    atomic_json(schema_path, gen["output_schema"])
    schema_sha256 = generation_config_sha256(gen["output_schema"])
    resume_path = vllm_root / "resume_history.jsonl"
    prior_completed = len(load_jsonl(vllm_root / "completions.jsonl"))
    resume_event = {
        "sequence": len(load_jsonl(resume_path)),
        "resume_requested": (vllm_root / "checkpoint.json").is_file(),
        "prior_completed_rows": prior_completed,
    }
    append_jsonl_fsync(resume_path, resume_event)
    invocation = {
        "generation_config": gen,
        "generation_config_sha256": generation_config_sha256(gen),
        "n_prompts": len(prompt_rows),
        "prompts_sha256": sha256_file(prompts_path),
    }
    atomic_json(vllm_root / "invocation_private.json", invocation)
    command = build_vllm_command(
        cfg, model_id, prompts_path, vllm_root, schema_path,
        resume=(vllm_root / "checkpoint.json").is_file(),
    )
    env = dict(os.environ)
    if gen["batch_invariant"]:
        env["VLLM_BATCH_INVARIANT"] = "1"
    subprocess.run(command, check=True, cwd=ROOT.parents[1], env=env)
    completions = _load_vllm_completions(
        vllm_root / "completions.jsonl", prompt_rows, gen,
    )
    provenance = _load_vllm_provenance(
        vllm_root / "provenance.json", gen, schema_sha256,
        invocation["prompts_sha256"],
    )
    runtime_versions = _runtime_versions(gen["engine_version"])
    resume_history = load_jsonl(resume_path)
    log = BaselineRunLog(ANALYSIS / model_id / "generation_rows.jsonl")
    if log.completed & excluded:
        raise RuntimeError("an excluded prior-atlas row is present in the generation log")
    renderer_id = model_cfg["render_contract"]
    eos_ids = resolve_eos_ids(tokenizer)
    for row in rows:
        if row["row_key"] in log.completed:
            continue
        item = completions[row["row_key"]]
        text = item["completion_text"]
        parsed_object = validate_structured_completion(text)
        new_ids = item["completion_token_ids"]
        last_token_id = int(new_ids[-1]) if new_ids else None
        finish_reason = item["finish_reason"]
        terminated = finish_reason != "length"
        aliases = row["aliases"] if row["answerable"] else None
        graded = grade_generation(text, aliases, terminated)
        role = assign_role(row["answerable"], graded)
        g = graded["full_grader_dict"]
        log.append({
            "row_key": row["row_key"], "source": "umwp", "native_source": row["native_source"],
            "original_pair_id": row["original_pair_id"], "category_canon": row["category_canon"],
            "umwp_id": row["umwp_id"], "answerable": row["answerable"],
            "model": model_cfg["repo"], "model_revision": model_cfg["revision"], "renderer_id": renderer_id,
            "seed": cfg["seed"], "generation_text": text, "answer_value": graded["answer_value"],
            "terminated_naturally": terminated, "n_new_tokens": len(new_ids), "full_grader_dict": g,
            "finish_reason": finish_reason, "last_completion_token_id": last_token_id,
            "eos_token_ids": eos_ids,
            "prompt_token_ids_sha256": item["prompt_token_ids_sha256"],
            "completion_token_ids": new_ids, "prompt_token_count": item["prompt_token_len"],
            "schema_valid": True, "generation_engine": "vllm",
            "generation_engine_version": gen["engine_version"],
            "generation_config_sha256": invocation["generation_config_sha256"],
            "batch_invariant": gen["batch_invariant"],
            "structured_output_backend": gen["structured_output_backend"],
            "structured_output_disable_any_whitespace": gen[
                "structured_output_disable_any_whitespace"
            ],
            "prompt_bytes_sha256": item["prompt_sha256"],
            "parsed_object": parsed_object, "vllm_version": gen["engine_version"],
            "vllm_model_runner": gen["model_runner"],
            "image_digest": cfg["containers"]["generation"]["image_digest"],
            "runtime_versions": runtime_versions, "schema_sha256": schema_sha256,
            "scheduler_pins": {
                "batch_size": gen["batch_size"],
                "tensor_parallel_size": gen["tensor_parallel_size"],
                "max_model_len": gen["max_model_len"],
                "gpu_memory_utilization": gen["gpu_memory_utilization"],
                "max_num_seqs": gen["max_num_seqs"],
                "max_num_batched_tokens": gen["max_num_batched_tokens"],
                "limit_mm_per_prompt": gen["limit_mm_per_prompt"],
            },
            "loader_pins": {"trust_remote_code": gen["trust_remote_code"]},
            "hardware_pins": {
                "minimum_compute_capability": gen["minimum_compute_capability"],
                "registered_compute_capability": gen["registered_compute_capability"],
                "hardware_class": gen["hardware_class"],
                "registered_host_driver": gen["registered_host_driver"],
            },
            "synaptic_tuner_source_fingerprint": tuner_source["sha256"],
            "checkpoint_config_sha256": provenance["config_hash"],
            "resume_history": resume_history,
            "role": role, "split": None, "triad_id": None, "cell_id": model_id,
            "layer": None, "arm": "baseline", "dose_or_strength": 0.0, **g,
        })
    final_keys = {r["row_key"] for r in load_jsonl(log.path)}
    eligible_keys = {r["row_key"] for r in rows}
    if final_keys != eligible_keys:
        raise RuntimeError(
            f"generation coverage mismatch: got {len(final_keys)}, expected {len(eligible_keys)} "
            f"eligible rows from {cfg['source']['expected_rows']} source rows"
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("materialize")
    p.add_argument("--source", type=Path)
    p.add_argument("--download", action="store_true")
    g = sub.add_parser("generate")
    g.add_argument("--model-id", choices=["gemma4_e4b_it", "qwen3_4b_raw_base"], required=True)
    g.add_argument("--rows", type=Path, default=ANALYSIS / "source" / "rows.jsonl")
    args = parser.parse_args()
    if args.command == "materialize":
        cfg = load_yaml(ROOT / "cell.yaml")
        canonical_source = ANALYSIS / "source" / "StandardDataset.jsonl"
        source = args.source or canonical_source
        if args.download:
            source.parent.mkdir(parents=True, exist_ok=True)
            urllib.request.urlretrieve(cfg["source"]["official_url"], source)
        if source.resolve() != canonical_source.resolve():
            if sha256_file(source) != cfg["source"]["raw_sha256"]:
                raise ValueError("UMWP source sha256 does not match cell.yaml")
            canonical_source.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, canonical_source)
        print(json.dumps(materialize_source(canonical_source, ANALYSIS / "source" / "rows.jsonl", cfg), indent=2))
    else:
        run_generation(args.model_id, args.rows)


if __name__ == "__main__":
    main()
