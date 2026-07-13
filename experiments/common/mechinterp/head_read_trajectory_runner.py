#!/usr/bin/env python3
"""GPU runner for the Tier-2 failure-axis read-trajectory (no steering).

For each probe-pool row, generates the answer under BASELINE greedy decoding
(no injection) while READ pre-hooks on the target o_proj blocks record the
per-head projection onto F at the final prompt token and every generated
position. Scores the realized behavior with the SAME scorer the causal-pilot
generated-replay uses (so groups match F's construction), and writes a resumable
per-row trajectory summary.

This MUST run behind an explicit GPU gate (Docker/unsloth), like the extraction
and the A.4 intervention sweep. The read-hook mechanism it calls is unit-tested
offline in tests/test_mechinterp_head_read_trajectory.py; this runner is the
heavyweight wiring and mirrors mechinterp_head_intervention_runner.ModelHarness.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
PROBE_DIR = REPO_ROOT / "archive/experiment/phase1/probe"
EVAL_DIR = REPO_ROOT / "archive" / "experiment" / "phase1" / "eval"
for _dir in (PROBE_DIR, EVAL_DIR):
    if str(_dir) not in sys.path:
        sys.path.insert(0, str(_dir))

import head_read_trajectory as traj  # noqa: E402
from backends import render_probe_prompt  # noqa: E402
from causal_pilot_runner import score_generation  # noqa: E402
from head_intervention import load_steering_directions  # noqa: E402


class HeadReadTrajectoryRunError(RuntimeError):
    pass


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def resolve_path(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else _repo_root() / path


def load_config(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        payload = yaml.safe_load(fh)
    if not isinstance(payload, dict):
        raise HeadReadTrajectoryRunError(f"{path} did not load to a YAML object")
    return payload


def load_rows(rows_path: Path, *, max_rows: int | None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with rows_path.open(encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            rows.append(json.loads(line))
            if max_rows is not None and len(rows) >= max_rows:
                break
    if not rows:
        raise HeadReadTrajectoryRunError(f"no rows in {rows_path}")
    return rows


class ModelHarness:
    def __init__(self, config: dict[str, Any]):
        import torch  # noqa: PLC0415
        from peft import PeftModel  # noqa: PLC0415
        from transformers import AutoModelForCausalLM, AutoTokenizer  # noqa: PLC0415

        self.torch = torch
        model_cfg = config["model"]
        model_name = model_cfg["model_name"]
        adapter = model_cfg.get("adapter")
        dtype = getattr(torch, model_cfg.get("torch_dtype", "bfloat16"))
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        base = AutoModelForCausalLM.from_pretrained(
            model_name, torch_dtype=dtype, device_map=model_cfg.get("device_map", "cuda")
        )
        self.model = PeftModel.from_pretrained(
            base, adapter, adapter_name=model_cfg.get("adapter_name", "grpo_v2")
        ) if adapter else base
        self.model.eval()
        self.device = next(self.model.parameters()).device
        self.system_prompt = config.get("prompt", {}).get(
            "system", "You are a helpful assistant. Answer the question concisely."
        )
        self.enable_thinking = bool(model_cfg.get("enable_thinking", False))
        self.num_hidden_layers = int(self.model.config.num_hidden_layers)
        self._render_mode: str | None = None

    def generate_with_read(self, question: str, *, by_block: dict[int, list[dict[str, Any]]],
                           sigma_map: dict[tuple[int, int], float], max_new_tokens: int) -> tuple[str, dict[str, Any]]:
        rendered, mode = render_probe_prompt(
            self.tokenizer, self.system_prompt, question,
            enable_thinking=self.enable_thinking, mode=self._render_mode,
        )
        if mode is not None:
            self._render_mode = mode
        inputs = self.tokenizer(rendered, return_tensors="pt").to(self.device)
        store: dict[tuple[int, int], list[float]] = {}
        with traj.per_head_read(self.model, by_block, num_hidden_layers=self.num_hidden_layers, store=store):
            with self.torch.no_grad():
                output_ids = self.model.generate(
                    **inputs, do_sample=False, max_new_tokens=max_new_tokens,
                    pad_token_id=self.tokenizer.eos_token_id,
                )
        answer = self.tokenizer.decode(
            output_ids[0, inputs["input_ids"].shape[1]:], skip_special_tokens=True
        ).strip()
        return answer, traj.summarize_row_trajectory(store, sigma_map)


def _config_fingerprint(config: dict[str, Any], *, max_new_tokens: int, max_rows: int | None) -> str:
    model_cfg = config.get("model", {})
    payload = {
        "model_name": model_cfg.get("model_name"),
        "adapter": model_cfg.get("adapter"),
        "adapter_name": model_cfg.get("adapter_name"),
        "enable_thinking": model_cfg.get("enable_thinking"),
        "system": config.get("prompt", {}).get("system"),
        "steering_directions": config.get("steering_directions"),
        "rows": config.get("rows"),
        "max_new_tokens": max_new_tokens,
        "max_rows": max_rows,
    }
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def _load_completed(rows_path: Path) -> tuple[set[str], list[dict[str, Any]]]:
    completed: set[str] = set()
    kept: list[dict[str, Any]] = []
    if not rows_path.is_file():
        return completed, kept
    with rows_path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue  # truncated tail; that unit re-runs
            key = rec.get("probe_pool_row_key")
            if key is None or key in completed:
                continue
            completed.add(key)
            kept.append(rec)
    return completed, kept


def run_config(config_path: Path, *, fresh: bool = False) -> dict[str, Any]:
    config = load_config(config_path)
    sweep = config.get("sweep", {})
    max_new_tokens = int(sweep.get("max_new_tokens", 96))
    max_rows = sweep.get("max_rows")
    max_rows = int(max_rows) if max_rows is not None else None

    artifact = load_steering_directions(resolve_path(config["steering_directions"]))
    directions = artifact["directions"]
    by_block = traj.build_block_read_specs(directions)
    sigma_map = {(int(d["layer"]), int(d["head"])): float(d["sigma"]) for d in directions}
    rows = load_rows(resolve_path(config["rows"]), max_rows=max_rows)

    output_root = resolve_path(config["output"]["root"])
    output_root.mkdir(parents=True, exist_ok=True)
    rows_path = output_root / "rows.jsonl"
    ckpt_path = output_root / "checkpoint.json"
    fingerprint = _config_fingerprint(config, max_new_tokens=max_new_tokens, max_rows=max_rows)

    completed: set[str] = set()
    scored_rows: list[dict[str, Any]] = []
    if fresh:
        rows_path.unlink(missing_ok=True)
        ckpt_path.unlink(missing_ok=True)
    elif rows_path.is_file():
        prior_fp = None
        if ckpt_path.is_file():
            try:
                prior_fp = json.loads(ckpt_path.read_text(encoding="utf-8")).get("fingerprint")
            except json.JSONDecodeError:
                prior_fp = None
        if prior_fp is not None and prior_fp != fingerprint:
            raise HeadReadTrajectoryRunError(
                f"checkpoint fingerprint {prior_fp!r} != current {fingerprint!r}: config changed since the "
                f"partial run in {output_root}. Re-run with --fresh to discard prior rows."
            )
        completed, scored_rows = _load_completed(rows_path)

    ckpt_path.write_text(
        json.dumps({"fingerprint": fingerprint, "total_units": len(rows), "config": str(config_path)},
                   indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    harness: ModelHarness | None = None
    generated = 0
    with rows_path.open("w", encoding="utf-8") as out_fh:
        for rec in scored_rows:
            out_fh.write(json.dumps(rec) + "\n")
        out_fh.flush()
        for row in rows:
            key = row["probe_pool_row_key"]
            if key in completed:
                continue
            if harness is None:  # lazy: a fully-resumed run never loads the model
                harness = ModelHarness(config)
            answer, summary = harness.generate_with_read(
                row["question"], by_block=by_block, sigma_map=sigma_map, max_new_tokens=max_new_tokens
            )
            cells = score_generation(row, answer)
            record = {
                "probe_pool_row_key": key,
                "label": row["label"],
                "generated_answer": answer,
                **cells,
                **summary,
            }
            scored_rows.append(record)
            completed.add(key)
            generated += 1
            out_fh.write(json.dumps(record) + "\n")
            out_fh.flush()

    analysis = traj.analyze_trajectories(scored_rows)
    summary = {
        "ok": True,
        "analysis_type": "mechinterp_head_read_trajectory_sweep",
        "notice": "HEAD_READ_TRAJECTORY_ONLY",
        "config": str(config_path),
        "fingerprint": fingerprint,
        "steering_directions": config["steering_directions"],
        "rows": config["rows"],
        "max_new_tokens": max_new_tokens,
        "row_count": len(rows),
        "num_target_heads": len(directions),
        "units_generated": generated,
        "units_resumed": len(rows) - generated,
        "analysis": analysis,
        "outputs": {"rows": str(rows_path), "summary": str(output_root / "summary.json")},
    }
    (output_root / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--fresh", action="store_true",
                        help="Discard any prior rows.jsonl/checkpoint and re-run (default: resume).")
    args = parser.parse_args(argv)
    try:
        summary = run_config(resolve_path(args.config), fresh=args.fresh)
    except (HeadReadTrajectoryRunError, traj.HeadReadTrajectoryError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(
        f"units: {summary['units_generated']} generated, {summary['units_resumed']} resumed, "
        f"{summary['row_count']} total",
        file=sys.stderr,
    )
    print(json.dumps(summary["analysis"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
