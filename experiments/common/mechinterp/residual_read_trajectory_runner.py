#!/usr/bin/env python3
"""GPU runner for the Tier-2 caution-axis residual read-trajectory (no steering).

For each KNOWN probe-pool row, generates the answer under BASELINE greedy
decoding (no injection) while a READ post-hook on the target decoder block records
the residual projection onto the caution direction theta at the final prompt token
and every generated position. Also decodes the generated tokens to locate where
the refusal lexicon surfaces, so the analysis can split pre- vs post-lexical
windows. Scores realized behavior with the SAME scorer the causal-pilot
generated-replay uses (so groups match the A2 construction), and writes a
resumable per-row trajectory summary.

This MUST run behind an explicit GPU gate (Docker/unsloth), like the extraction
and the A.4 intervention sweep. The read-hook + analysis live in the offline-tested
``phase3_residual_read_trajectory``; this runner is the heavyweight wiring and
mirrors ``phase3_head_read_trajectory_runner.ModelHarness``.
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
PROBE_DIR = REPO_ROOT / "experiment/phase1/probe"
EVAL_DIR = REPO_ROOT / "experiment" / "phase1" / "eval"
for _dir in (PROBE_DIR, EVAL_DIR):
    if str(_dir) not in sys.path:
        sys.path.insert(0, str(_dir))

import residual_read_trajectory as rrt  # noqa: E402
from backends import render_probe_prompt  # noqa: E402
from causal_pilot_runner import score_generation  # noqa: E402


class ResidualReadTrajectoryRunError(RuntimeError):
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
        raise ResidualReadTrajectoryRunError(f"{path} did not load to a YAML object")
    return payload


def load_direction(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        payload = json.load(fh)
    if not isinstance(payload, dict) or "theta" not in payload:
        raise ResidualReadTrajectoryRunError(f"{path} is not a caution-direction JSON")
    return payload


def load_rows(rows_path: Path, *, max_rows: int | None,
              label_filter: str | None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with rows_path.open(encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            rec = json.loads(line)
            if label_filter is not None and rec.get("label") != label_filter:
                continue
            rows.append(rec)
            if max_rows is not None and len(rows) >= max_rows:
                break
    if not rows:
        raise ResidualReadTrajectoryRunError(
            f"no rows in {rows_path} (label_filter={label_filter!r})")
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
        self._render_mode: str | None = None

    def generate_with_read(self, question: str, *, spec: dict[str, Any],
                           max_new_tokens: int) -> tuple[str, dict[str, Any]]:
        rendered, mode = render_probe_prompt(
            self.tokenizer, self.system_prompt, question,
            enable_thinking=self.enable_thinking, mode=self._render_mode,
        )
        if mode is not None:
            self._render_mode = mode
        inputs = self.tokenizer(rendered, return_tensors="pt").to(self.device)
        prompt_len = inputs["input_ids"].shape[1]
        store: list[float] = []
        with rrt.residual_read(self.model, spec, store=store):
            with self.torch.no_grad():
                output_ids = self.model.generate(
                    **inputs, do_sample=False, max_new_tokens=max_new_tokens,
                    pad_token_id=self.tokenizer.eos_token_id,
                )
        gen_ids = output_ids[0, prompt_len:].tolist()
        gen_tokens = [self.tokenizer.decode([tid], skip_special_tokens=True) for tid in gen_ids]
        answer = self.tokenizer.decode(gen_ids, skip_special_tokens=True).strip()
        onset = rrt.find_lexical_onset(gen_tokens)
        summary = rrt.summarize_row_trajectory(store, float(spec["sigma"]), lexical_onset_idx=onset)
        return answer, summary


def _config_fingerprint(config: dict[str, Any], *, direction: dict[str, Any],
                        max_new_tokens: int, max_rows: int | None,
                        label_filter: str | None) -> str:
    model_cfg = config.get("model", {})
    payload = {
        "model_name": model_cfg.get("model_name"),
        "adapter": model_cfg.get("adapter"),
        "adapter_name": model_cfg.get("adapter_name"),
        "enable_thinking": model_cfg.get("enable_thinking"),
        "system": config.get("prompt", {}).get("system"),
        "caution_direction": config.get("caution_direction"),
        "direction_layer": direction.get("layer"),
        "direction_sigma": direction.get("sigma"),
        "rows": config.get("rows"),
        "label_filter": label_filter,
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
    label_filter = config.get("rows_filter", {}).get("label")

    direction = load_direction(resolve_path(config["caution_direction"]))
    spec = rrt.build_residual_read_spec(direction)
    rows = load_rows(resolve_path(config["rows"]), max_rows=max_rows, label_filter=label_filter)

    output_root = resolve_path(config["output"]["root"])
    output_root.mkdir(parents=True, exist_ok=True)
    rows_path = output_root / "rows.jsonl"
    ckpt_path = output_root / "checkpoint.json"
    fingerprint = _config_fingerprint(
        config, direction=direction, max_new_tokens=max_new_tokens,
        max_rows=max_rows, label_filter=label_filter,
    )

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
            raise ResidualReadTrajectoryRunError(
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
                row["question"], spec=spec, max_new_tokens=max_new_tokens
            )
            cells = score_generation(row, answer)
            record = {
                "probe_pool_row_key": key,
                "label": row["label"],
                "behavior_cell": row.get("behavior_cell"),
                "generated_answer": answer,
                **cells,
                **summary,
            }
            scored_rows.append(record)
            completed.add(key)
            generated += 1
            out_fh.write(json.dumps(record) + "\n")
            out_fh.flush()

    analysis = rrt.analyze_trajectories(scored_rows)
    summary = {
        "ok": True,
        "analysis_type": "phase3_residual_read_trajectory_sweep",
        "notice": "RESIDUAL_CAUTION_READ_TRAJECTORY_ONLY",
        "config": str(config_path),
        "fingerprint": fingerprint,
        "caution_direction": config["caution_direction"],
        "direction_layer": direction.get("layer"),
        "direction_prompt_token_auroc": direction.get("prompt_token_auroc"),
        "rows": config["rows"],
        "label_filter": label_filter,
        "max_new_tokens": max_new_tokens,
        "row_count": len(rows),
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
    except (ResidualReadTrajectoryRunError, rrt.ResidualReadTrajectoryError) as exc:
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
