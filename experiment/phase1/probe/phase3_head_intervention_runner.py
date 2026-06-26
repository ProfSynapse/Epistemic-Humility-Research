#!/usr/bin/env python3
"""GPU runner for the Step A.4 per-head during-generation ITI sweep.

Loads the GRPO v2 model (merged base + active adapter), generates the unknown
panel under the per-head intervention (phase3_head_intervention) across an alpha
sweep (both signs), scores behavior cells with the SAME scorer the causal-pilot
generated-replay uses (so cell definitions match), and writes per-row results +
a summary. alpha is in units of the per-head sigma: the hook adds
``alpha * sigma * theta`` to each target head's o_proj input, every generated
token. alpha == 0.0 is the no-hook baseline.

This MUST run behind an explicit GPU gate (Docker/unsloth), like the extraction.
The injection mechanism it calls is unit-tested offline in
tests/test_phase3_head_intervention.py; this runner is the heavyweight wiring.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import yaml

PROBE_DIR = Path(__file__).resolve().parent
REPO_ROOT = PROBE_DIR.parents[2]
EVAL_DIR = REPO_ROOT / "experiment" / "phase1" / "eval"
for _dir in (PROBE_DIR, EVAL_DIR):
    if str(_dir) not in sys.path:
        sys.path.insert(0, str(_dir))

import phase3_head_intervention as intervention  # noqa: E402
import scorers  # noqa: E402,F401  (re-exported via score_generation; import validates availability)
from backends import render_probe_prompt  # noqa: E402
from phase3_causal_pilot_runner import score_generation, summarize_metrics  # noqa: E402


class HeadInterventionRunError(RuntimeError):
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
        raise HeadInterventionRunError(f"{path} did not load to a YAML object")
    return payload


def load_rows(rows_path: Path, *, max_rows: int | None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with rows_path.open(encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            row = json.loads(line)
            rows.append(row)
            if max_rows is not None and len(rows) >= max_rows:
                break
    if not rows:
        raise HeadInterventionRunError(f"no rows in {rows_path}")
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
        if adapter:
            self.model = PeftModel.from_pretrained(
                base, adapter, adapter_name=model_cfg.get("adapter_name", "grpo_v2")
            )
        else:
            self.model = base
        self.model.eval()
        self.device = next(self.model.parameters()).device
        self.system_prompt = config.get("prompt", {}).get(
            "system", "You are a helpful assistant. Answer the question concisely."
        )
        self.enable_thinking = bool(model_cfg.get("enable_thinking", False))
        self.num_hidden_layers = int(self.model.config.num_hidden_layers)
        self._render_mode: str | None = None

    def generate(self, question: str, *, by_block: dict[int, list[dict[str, Any]]],
                 max_new_tokens: int) -> str:
        rendered, mode = render_probe_prompt(
            self.tokenizer, self.system_prompt, question,
            enable_thinking=self.enable_thinking, mode=self._render_mode,
        )
        if mode is not None:
            self._render_mode = mode
        inputs = self.tokenizer(rendered, return_tensors="pt").to(self.device)
        with self.torch.no_grad():
            if by_block:
                with intervention.per_head_intervention(
                    self.model, by_block, torch=self.torch, num_hidden_layers=self.num_hidden_layers
                ):
                    output_ids = self.model.generate(
                        **inputs, do_sample=False, max_new_tokens=max_new_tokens,
                        pad_token_id=self.tokenizer.eos_token_id,
                    )
            else:
                output_ids = self.model.generate(
                    **inputs, do_sample=False, max_new_tokens=max_new_tokens,
                    pad_token_id=self.tokenizer.eos_token_id,
                )
        new_tokens = output_ids[0, inputs["input_ids"].shape[1]:]
        return self.tokenizer.decode(new_tokens, skip_special_tokens=True).strip()


def _config_fingerprint(config: dict[str, Any], *, alphas: list[float], max_new_tokens: int) -> str:
    """Stable short hash of everything that defines a unit of generation work.

    If any of these change, prior rows are not comparable to new ones, so resume
    must refuse rather than silently mix two configs in one rows.jsonl.
    """
    model_cfg = config.get("model", {})
    payload = {
        "model_name": model_cfg.get("model_name"),
        "adapter": model_cfg.get("adapter"),
        "adapter_name": model_cfg.get("adapter_name"),
        "enable_thinking": model_cfg.get("enable_thinking"),
        "system": config.get("prompt", {}).get("system"),
        "steering_directions": config.get("steering_directions"),
        "rows": config.get("rows"),
        "alphas": sorted(alphas),
        "max_new_tokens": max_new_tokens,
        "max_rows": config.get("sweep", {}).get("max_rows"),
    }
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def _load_completed(rows_path: Path) -> tuple[set[tuple[str, str]], list[dict[str, Any]]]:
    """Read an existing rows.jsonl into (completed unit keys, clean records).

    A unit key is ``(arm_id, probe_pool_row_key)``. A truncated final line (from a
    process killed mid-write) or a duplicate is dropped, so the rewritten file is
    clean and the dropped unit is simply regenerated on resume.
    """
    completed: set[tuple[str, str]] = set()
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
            arm_id = rec.get("arm_id")
            row_key = rec.get("probe_pool_row_key")
            if arm_id is None or row_key is None:
                continue
            key = (arm_id, row_key)
            if key in completed:
                continue
            completed.add(key)
            kept.append(rec)
    return completed, kept


def run_config(config_path: Path, *, fresh: bool = False) -> dict[str, Any]:
    config = load_config(config_path)
    sweep = config["sweep"]
    alphas = [float(a) for a in sweep["alphas"]]
    if 0.0 not in alphas:
        raise HeadInterventionRunError("sweep.alphas must include 0.0 (the no-hook baseline)")
    max_new_tokens = int(sweep.get("max_new_tokens", 96))
    max_rows = sweep.get("max_rows")
    max_rows = int(max_rows) if max_rows is not None else None

    artifact = intervention.load_steering_directions(resolve_path(config["steering_directions"]))
    directions = artifact["directions"]
    rows = load_rows(resolve_path(config["rows"]), max_rows=max_rows)

    output_root = resolve_path(config["output"]["root"])
    output_root.mkdir(parents=True, exist_ok=True)
    rows_path = output_root / "rows.jsonl"
    ckpt_path = output_root / "checkpoint.json"

    fingerprint = _config_fingerprint(config, alphas=alphas, max_new_tokens=max_new_tokens)

    # --- Resume vs fresh ------------------------------------------------------
    completed: set[tuple[str, str]] = set()
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
            raise HeadInterventionRunError(
                f"checkpoint fingerprint {prior_fp!r} != current {fingerprint!r}: the config "
                f"changed since the partial run in {output_root}. Re-run with --fresh to discard "
                "the prior rows, or restore the original config to resume."
            )
        completed, scored_rows = _load_completed(rows_path)

    total_units = len(alphas) * len(rows)
    ckpt_path.write_text(
        json.dumps(
            {"fingerprint": fingerprint, "total_units": total_units, "config": str(config_path)},
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    harness: ModelHarness | None = None
    generated = 0
    # Rewrite rows.jsonl from the clean kept records, then append new work. Truncating
    # here drops any malformed tail line; we already captured the clean rows in memory.
    with rows_path.open("w", encoding="utf-8") as out_fh:
        for rec in scored_rows:
            out_fh.write(json.dumps(rec) + "\n")
        out_fh.flush()
        for alpha in alphas:
            is_baseline = alpha == 0.0
            by_block = {} if is_baseline else intervention.build_block_deltas(directions, alpha=alpha)
            arm_id = "no_vector_baseline" if is_baseline else f"per_head_iti_alpha_{alpha:+g}"
            control = "no_vector_baseline" if is_baseline else "per_head_iti"
            for row in rows:
                key = (arm_id, row["probe_pool_row_key"])
                if key in completed:
                    continue
                if harness is None:  # lazy: a fully-resumed run never loads the model
                    harness = ModelHarness(config)
                answer = harness.generate(row["question"], by_block=by_block, max_new_tokens=max_new_tokens)
                cells = score_generation(row, answer)
                record = {
                    "arm_id": arm_id,
                    "control": control,
                    "alpha": alpha,
                    "probe_pool_row_key": row["probe_pool_row_key"],
                    "label": row["label"],
                    "generated_answer": answer,
                    **cells,
                }
                scored_rows.append(record)
                completed.add(key)
                generated += 1
                out_fh.write(json.dumps(record) + "\n")
                out_fh.flush()

    metrics = summarize_metrics(scored_rows)
    summary = {
        "ok": True,
        "analysis_type": "phase3_head_intervention_sweep",
        "notice": "HEAD_INTERVENTION_SWEEP_ONLY",
        "config": str(config_path),
        "fingerprint": fingerprint,
        "steering_directions": config["steering_directions"],
        "rows": config["rows"],
        "alphas": alphas,
        "max_new_tokens": max_new_tokens,
        "row_count": len(rows),
        "num_target_heads": len(directions),
        "units_total": total_units,
        "units_resumed": total_units - generated,
        "units_generated": generated,
        "metrics_by_arm": metrics,
        "outputs": {"rows": str(rows_path), "summary": str(output_root / "summary.json")},
    }
    (output_root / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument(
        "--fresh",
        action="store_true",
        help="Discard any prior rows.jsonl/checkpoint and re-run the whole sweep "
        "(default: resume, skipping units already in rows.jsonl).",
    )
    args = parser.parse_args(argv)
    try:
        summary = run_config(resolve_path(args.config), fresh=args.fresh)
    except (HeadInterventionRunError, intervention.HeadInterventionError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(
        f"units: {summary['units_generated']} generated, "
        f"{summary['units_resumed']} resumed, {summary['units_total']} total",
        file=sys.stderr,
    )
    print(json.dumps(summary["metrics_by_arm"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
