#!/usr/bin/env python3
"""Pre-sign vLLM invariance, resume, containment, and matcher reachability checks."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import signal
import subprocess
import time
from pathlib import Path
from typing import Any

from instrument_common import (
    ANALYSIS, COMMITTED, ROOT, append_jsonl_fsync, atomic_json, atomic_jsonl,
    load_jsonl, load_yaml, require_pinned_container,
    require_synaptic_tuner_source, sha256_file,
)
from match_and_gate import ROLES, build_triads
from source_and_generate import (
    _generation_config, _load_vllm_completions, _load_vllm_provenance,
    build_exclusion_manifest, build_vllm_command, generation_config_sha256,
    render_prompt, validate_source_materialization, validate_structured_completion,
)


RUN_NAMES = ("original_a", "original_b", "permuted_a", "permuted_b", "resume")


def _stable_rank(seed: int, row_key: str) -> str:
    return hashlib.sha256(f"{seed}:{row_key}".encode()).hexdigest()


def select_smoke_rows(
    candidates: list[dict[str, Any]], *, n_rows: int, seed: int,
) -> list[dict[str, Any]]:
    """Select short and long rows from every native-source/answerability stratum."""
    if n_rows < 16:
        raise ValueError("smoke selection requires at least 16 rows")
    by_stratum: dict[tuple[str, bool], list[dict[str, Any]]] = {}
    for row in candidates:
        by_stratum.setdefault((row["native_source"], bool(row["answerable"])), []).append(row)
    expected = {(source, answerable) for source in ("ASDiv", "GSM8K", "MultiArith", "SVAMP") for answerable in (False, True)}
    if not expected <= set(by_stratum):
        raise ValueError("smoke candidates do not cover every source/answerability stratum")
    selected: dict[str, dict[str, Any]] = {}
    for stratum in sorted(expected):
        rows = sorted(
            by_stratum[stratum],
            key=lambda row: (len(row["prompt_token_ids_expected"]), row["row_key"]),
        )
        for row in (rows[0], rows[-1]):
            selected[row["row_key"]] = row
    remaining = sorted(
        (row for row in candidates if row["row_key"] not in selected),
        key=lambda row: (_stable_rank(seed, row["row_key"]), row["row_key"]),
    )
    for row in remaining[: n_rows - len(selected)]:
        selected[row["row_key"]] = row
    if len(selected) != n_rows:
        raise ValueError(f"smoke selection produced {len(selected)} rows, expected {n_rows}")
    return sorted(selected.values(), key=lambda row: row["row_key"])


def fixed_permutation(rows: list[dict[str, Any]], seed: int) -> list[dict[str, Any]]:
    return sorted(rows, key=lambda row: (_stable_rank(seed, row["row_key"]), row["row_key"]))


def _require_model_smoke_approval(model_id: str) -> None:
    if os.environ.get("EHR_PI_APPROVED_PRESIGN_SMOKE") != model_id:
        raise RuntimeError(
            "model smoke requires EHR_PI_APPROVED_PRESIGN_SMOKE set to the exact model id"
        )


def prepare_private_prompts(model_id: str, rows_path: Path) -> Path:
    """Render and select the private fixed smoke set inside the approved container."""
    cfg = load_yaml(ROOT / "cell.yaml")
    _require_model_smoke_approval(model_id)
    require_pinned_container(cfg["containers"]["generation"]["image_digest"])
    require_synaptic_tuner_source(cfg)
    validate_source_materialization(cfg)
    from transformers import AutoTokenizer

    model_cfg = cfg["models"][model_id]
    gen = _generation_config(cfg, model_id)
    tokenizer = AutoTokenizer.from_pretrained(
        model_cfg["repo"], revision=gen["tokenizer_revision"], token=None,
        trust_remote_code=gen["trust_remote_code"],
    )
    source_rows = load_jsonl(rows_path)
    excluded = build_exclusion_manifest(model_id, source_rows, cfg)
    candidates = []
    for row in source_rows:
        if row["row_key"] in excluded:
            continue
        prompt = render_prompt(model_id, tokenizer, row)
        token_ids = tokenizer(prompt, add_special_tokens=True)["input_ids"]
        candidates.append({
            "id": row["row_key"], "row_key": row["row_key"],
            "native_source": row["native_source"], "answerable": row["answerable"],
            "prompt": prompt, "prompt_token_ids_expected": token_ids,
            "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
            "prompt_token_ids_sha256": hashlib.sha256(
                json.dumps(token_ids, separators=(",", ":")).encode("ascii")
            ).hexdigest(),
        })
    n_rows = int(cfg["presign_reachability"]["private_rows_per_model"])
    selected = select_smoke_rows(candidates, n_rows=n_rows, seed=cfg["seed"])
    max_model_len = gen["max_model_len"]
    if any(len(row["prompt_token_ids_expected"]) + gen["max_new_tokens"] > max_model_len for row in selected):
        raise RuntimeError("smoke prompt plus generation allowance exceeds max_model_len")
    path = ANALYSIS / model_id / "presign_smoke" / "selected_prompts_private.jsonl"
    atomic_jsonl(path, selected)
    return path


def _run_command(command: list[str], env: dict[str, str]) -> None:
    subprocess.run(command, check=True, cwd=ROOT.parents[1], env=env)


def _durable_row_count(out_dir: Path) -> int:
    """Read the atomic checkpoint written only after a batch has been fsynced."""
    checkpoint = out_dir / "checkpoint.json"
    if not checkpoint.is_file():
        return 0
    return int(json.loads(checkpoint.read_text(encoding="utf-8"))["count"])


def _run_kill_resume(
    command: list[str], resume_command: list[str], out_dir: Path,
    env: dict[str, str], first_batch_size: int, total_rows: int,
) -> None:
    process = subprocess.Popen(
        command, cwd=ROOT.parents[1], env=env, start_new_session=True,
    )
    completions = out_dir / "completions.jsonl"
    deadline = time.monotonic() + 1800
    while time.monotonic() < deadline:
        count = _durable_row_count(out_dir)
        if count >= first_batch_size:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=60)
            break
        if process.poll() is not None:
            raise RuntimeError("kill-resume smoke exited before one durable batch")
        time.sleep(0.01)
    else:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait(timeout=60)
        raise TimeoutError("kill-resume smoke did not persist its first batch")
    durable = _durable_row_count(out_dir)
    persisted = len(load_jsonl(completions))
    if durable != first_batch_size or persisted != durable or durable >= total_rows:
        raise RuntimeError(
            "kill-resume boundary was "
            f"checkpoint={durable}, completions={persisted}; expected exactly "
            f"{first_batch_size}"
        )
    _run_command(resume_command, env)


def compare_repeat_rows(rows_by_run: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    """Require exact row-keyed completion, finish, parse, and canonical row parity."""
    if set(rows_by_run) != set(RUN_NAMES):
        raise ValueError("smoke run set is incomplete")
    canonical: dict[str, dict[str, Any]] = {}
    canonical_full: dict[str, str] = {}
    for run_name, rows in rows_by_run.items():
        by_id = {str(row["id"]): row for row in rows}
        if len(by_id) != len(rows):
            raise ValueError(f"{run_name} contains duplicate row ids")
        signatures = {
            row_id: {
                "completion_token_ids": row["completion_token_ids"],
                "finish_reason": row["finish_reason"],
                "parsed_object": validate_structured_completion(row["completion_text"]),
            }
            for row_id, row in by_id.items()
        }
        full = json.dumps(
            [by_id[row_id] for row_id in sorted(by_id)],
            sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        )
        canonical[run_name] = signatures
        canonical_full[run_name] = full
    baseline = canonical["original_a"]
    if any(value != baseline for value in canonical.values()):
        raise ValueError("completion token ids, finish reasons, or parsed objects differ")
    if any(value != canonical_full["original_a"] for value in canonical_full.values()):
        raise ValueError("canonical row logs differ across uninterrupted, permuted, or resumed runs")
    return {"n_rows": len(baseline), "run_count": len(rows_by_run)}


def run_model_smoke(model_id: str, prompts_path: Path) -> dict[str, Any]:
    cfg = load_yaml(ROOT / "cell.yaml")
    _require_model_smoke_approval(model_id)
    require_pinned_container(cfg["containers"]["generation"]["image_digest"])
    tuner_source = require_synaptic_tuner_source(cfg)
    prompts = load_jsonl(prompts_path)
    expected_n = int(cfg["presign_reachability"]["private_rows_per_model"])
    if len(prompts) != expected_n:
        raise ValueError(f"private smoke set has {len(prompts)} rows, expected {expected_n}")
    gen = _generation_config(cfg, model_id)
    root = ANALYSIS / model_id / "presign_smoke"
    schema_path = root / "output_schema.json"
    atomic_json(schema_path, gen["output_schema"])
    original_path = root / "prompts_original_private.jsonl"
    permuted_path = root / "prompts_permuted_private.jsonl"
    atomic_jsonl(original_path, prompts)
    atomic_jsonl(permuted_path, fixed_permutation(prompts, cfg["seed"] + 1))
    env = dict(os.environ)
    env["VLLM_BATCH_INVARIANT"] = "1"
    for run_name, order_path in (
        ("original_a", original_path), ("original_b", original_path),
        ("permuted_a", permuted_path), ("permuted_b", permuted_path),
    ):
        out_dir = root / "runs" / run_name
        command = build_vllm_command(
            cfg, model_id, order_path, out_dir, schema_path, resume=False,
        )
        _run_command(command, env)
    resume_dir = root / "runs" / "resume"
    initial = build_vllm_command(
        cfg, model_id, original_path, resume_dir, schema_path, resume=False,
    )
    resumed = build_vllm_command(
        cfg, model_id, original_path, resume_dir, schema_path, resume=True,
    )
    _run_kill_resume(initial, resumed, resume_dir, env, gen["batch_size"], len(prompts))

    rows_by_run: dict[str, list[dict[str, Any]]] = {}
    provenance = None
    schema_hash = generation_config_sha256(gen["output_schema"])
    for run_name in RUN_NAMES:
        order_path = permuted_path if run_name.startswith("permuted") else original_path
        expected_rows = load_jsonl(order_path)
        run_dir = root / "runs" / run_name
        validated = _load_vllm_completions(run_dir / "completions.jsonl", expected_rows, gen)
        rows_by_run[run_name] = list(validated.values())
        observed_provenance = _load_vllm_provenance(
            run_dir / "provenance.json", gen, schema_hash, sha256_file(order_path),
        )
        if provenance is None:
            provenance = observed_provenance
    comparison = compare_repeat_rows(rows_by_run)
    manifest = [{
        "row_id": row["row_key"], "prompt_sha256": row["prompt_sha256"],
        "prompt_token_sequence_sha256": row["prompt_token_ids_sha256"],
        "prompt_token_count": len(row["prompt_token_ids_expected"]),
    } for row in prompts]
    stratum_counts: dict[str, int] = {}
    for row in prompts:
        key = f"{row['native_source']}:{'answerable' if row['answerable'] else 'unanswerable'}"
        stratum_counts[key] = stratum_counts.get(key, 0) + 1
    committed = COMMITTED / model_id
    atomic_jsonl(committed / "presign_smoke_manifest.jsonl", manifest)
    summary = {
        "schema_version": 1, "status": "pass", "model_id": model_id,
        "n_rows": comparison["n_rows"], "run_count": comparison["run_count"],
        "whole_output_schema_valid_fraction": 1.0,
        "salvage_parsing_used": False,
        "completion_token_ids_identical": True, "finish_reasons_identical": True,
        "parsed_objects_identical": True, "kill_resume_canonical_rowlog_exact": True,
        "row_manifest_sha256": generation_config_sha256(manifest),
        "selection_stratum_counts": dict(sorted(stratum_counts.items())),
        "synaptic_tuner_source_fingerprint": tuner_source["sha256"],
        "vllm_version": provenance["runtime"]["vllm_version"],
        "vllm_model_runner": provenance["runtime"]["vllm_model_runner"],
        "generation_image_digest": cfg["containers"]["generation"]["image_digest"],
        "scheduler": {
            "batch_size": gen["batch_size"], "max_num_seqs": gen["max_num_seqs"],
            "max_num_batched_tokens": gen["max_num_batched_tokens"],
            "max_model_len": gen["max_model_len"],
        },
    }
    atomic_json(committed / "presign_smoke_summary.json", summary)
    return summary


def planted_matcher_reachability(
    private_path: Path = ANALYSIS / "presign_reachability" / "planted_rows_private.jsonl",
    committed_path: Path = COMMITTED / "presign_matcher_reachability.json",
) -> dict[str, Any]:
    """Feed 128 planted ID-only triads through the real matcher and split path."""
    rows = []
    for index in range(128):
        for role_offset, role in enumerate(ROLES):
            rows.append({
                "row_key": f"plant:{role}:{index:03d}", "role": role,
                "native_source": "GSM8K",
                "category_canon": None if role == "known_correct_answered" else "plant",
                "original_pair_id": f"plant-original:{role}:{index:03d}",
                "matching_vector": [float(index), float(role_offset)],
            })
    atomic_jsonl(private_path, rows)
    triads = build_triads(rows, 20260721)
    fit = sum(triad["split"] == "fit" for triad in triads)
    held = sum(triad["split"] == "held_out" for triad in triads)
    if len(triads) != 128 or fit != 64 or held != 64:
        raise RuntimeError(f"planted matcher reachability failed: total={len(triads)} fit={fit} held={held}")
    manifest = [{
        "triad_id": triad["triad_id"], "split": triad["split"],
        "row_ids": {role: triad["rows"][role]["row_key"] for role in ROLES},
    } for triad in triads]
    summary = {
        "schema_version": 1, "status": "pass", "planted_triads": len(triads),
        "fit_triads": fit, "held_out_triads": held,
        "roles_per_triad": list(ROLES),
        "private_manifest_sha256": generation_config_sha256(manifest),
    }
    atomic_json(committed_path, summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    prepare = sub.add_parser("prepare")
    prepare.add_argument("--model-id", choices=["gemma4_e4b_it", "qwen3_4b_raw_base"], required=True)
    prepare.add_argument("--rows", type=Path, default=ANALYSIS / "source" / "rows.jsonl")
    run = sub.add_parser("run")
    run.add_argument("--model-id", choices=["gemma4_e4b_it", "qwen3_4b_raw_base"], required=True)
    run.add_argument("--prompts", type=Path)
    sub.add_parser("matcher-reachability")
    args = parser.parse_args()
    if args.command == "prepare":
        print(prepare_private_prompts(args.model_id, args.rows))
    elif args.command == "run":
        prompts = args.prompts or ANALYSIS / args.model_id / "presign_smoke" / "selected_prompts_private.jsonl"
        print(json.dumps(run_model_smoke(args.model_id, prompts), indent=2))
    else:
        print(json.dumps(planted_matcher_reachability(), indent=2))


if __name__ == "__main__":
    main()
