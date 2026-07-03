#!/usr/bin/env python3
"""GPU runner for the B1 causal residual intervention on the caution axis.

For each KNOWN probe-pool row and each configured arm, generates the answer under
greedy decoding while a forward hook on the target decoder block REWRITES the
residual stream per the arm (``baseline`` no-op, ``ablate`` removes the caution
component, ``shift`` adds alpha*sigma*theta). Re-scores realized behavior with the
causal-pilot scorer and writes a resumable per-(row,arm) record so the analysis
can compare refusal rates across arms (does ablating the caution axis reduce
over-refusal on known_refused, while leaving known_correct_answered alone?).

MUST run behind an explicit GPU gate (Docker/unsloth). Hook math + analysis are
unit-tested offline in tests/test_phase3_residual_intervention.py; this runner is
the heavyweight wiring and mirrors phase3_residual_read_trajectory_runner.
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

import phase3_residual_intervention as ri  # noqa: E402
from backends import render_probe_prompt  # noqa: E402
from phase3_causal_pilot_runner import score_generation  # noqa: E402


class ResidualInterventionRunError(RuntimeError):
    pass


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def resolve_path(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else _repo_root() / path


def resolve_model_ref(value: str | None) -> str | None:
    """Repo-relative checkpoint dirs -> absolute paths (from_pretrained
    resolves relative paths against the process CWD, not the repo root);
    HF hub ids and absolute paths pass through untouched."""
    if not value:
        return value
    cand = resolve_path(value)
    return str(cand) if cand.exists() else value


def load_config(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        payload = yaml.safe_load(fh)
    if not isinstance(payload, dict):
        raise ResidualInterventionRunError(f"{path} did not load to a YAML object")
    return payload


def load_direction(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        payload = json.load(fh)
    if not isinstance(payload, dict) or "theta" not in payload:
        raise ResidualInterventionRunError(f"{path} is not a caution-direction JSON")
    return payload


def load_rows(rows_path: Path, *, max_rows: int | None, labels: set[str] | None,
              cells: set[str] | None,
              max_rows_per_cell: int | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    per_cell: dict[str, int] = {}
    with rows_path.open(encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            rec = json.loads(line)
            if labels is not None and rec.get("label") not in labels:
                continue
            if cells is not None and rec.get("behavior_cell") not in cells:
                continue
            if max_rows_per_cell is not None:
                cell = str(rec.get("behavior_cell"))
                if per_cell.get(cell, 0) >= max_rows_per_cell:
                    continue
                per_cell[cell] = per_cell.get(cell, 0) + 1
            rows.append(rec)
            if max_rows is not None and len(rows) >= max_rows:
                break
    if not rows:
        raise ResidualInterventionRunError(f"no rows in {rows_path} after filtering")
    return rows


class ModelHarness:
    def __init__(self, config: dict[str, Any]):
        import torch  # noqa: PLC0415
        from peft import PeftModel  # noqa: PLC0415
        from transformers import AutoModelForCausalLM, AutoTokenizer  # noqa: PLC0415

        self.torch = torch
        model_cfg = config["model"]
        model_name = resolve_model_ref(model_cfg["model_name"])
        adapter = resolve_model_ref(model_cfg.get("adapter"))
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

    def generate(self, question: str, *, spec: dict[str, Any], arm: dict[str, Any],
                 max_new_tokens: int) -> str:
        rendered, mode = render_probe_prompt(
            self.tokenizer, self.system_prompt, question,
            enable_thinking=self.enable_thinking, mode=self._render_mode,
        )
        if mode is not None:
            self._render_mode = mode
        inputs = self.tokenizer(rendered, return_tensors="pt").to(self.device)
        prompt_len = inputs["input_ids"].shape[1]
        with ri.residual_intervention(self.model, spec, arm):
            with self.torch.no_grad():
                output_ids = self.model.generate(
                    **inputs, do_sample=False, max_new_tokens=max_new_tokens,
                    pad_token_id=self.tokenizer.eos_token_id,
                )
        return self.tokenizer.decode(
            output_ids[0, prompt_len:], skip_special_tokens=True
        ).strip()

    def generate_batch(self, questions: list[str], *, spec: dict[str, Any],
                       arm: dict[str, Any], max_new_tokens: int) -> list[str]:
        """One hooked forward over a left-padded batch of prompts.

        For couple arms ``arm["alpha"]`` is a list aligned to ``questions``
        (per-row gains); the write hook broadcasts each row's alpha over its
        positions. Greedy decode, same flags as the sequential path.
        """
        rendered = []
        for q in questions:
            r, mode = render_probe_prompt(
                self.tokenizer, self.system_prompt, q,
                enable_thinking=self.enable_thinking, mode=self._render_mode,
            )
            if mode is not None:
                self._render_mode = mode
            rendered.append(r)
        tok = self.tokenizer
        if tok.pad_token_id is None:
            tok.pad_token = tok.eos_token
        prev_side = tok.padding_side
        tok.padding_side = "left"  # decoder-only: completions stay contiguous
        try:
            inputs = tok(rendered, return_tensors="pt", padding=True).to(self.device)
        finally:
            tok.padding_side = prev_side
        prompt_len = inputs["input_ids"].shape[1]
        with ri.residual_intervention(self.model, spec, arm):
            with self.torch.no_grad():
                output_ids = self.model.generate(
                    **inputs, do_sample=False, max_new_tokens=max_new_tokens,
                    pad_token_id=tok.eos_token_id,
                )
        return [
            self.tokenizer.decode(output_ids[i, prompt_len:],
                                  skip_special_tokens=True).strip()
            for i in range(len(questions))
        ]


def _config_fingerprint(config: dict[str, Any], *, direction: dict[str, Any],
                        arms: list[dict[str, Any]], max_new_tokens: int,
                        batch_size: int = 1) -> str:
    model_cfg = config.get("model", {})
    payload = {
        "model_name": model_cfg.get("model_name"),
        "adapter": model_cfg.get("adapter"),
        "adapter_name": model_cfg.get("adapter_name"),
        "system": config.get("prompt", {}).get("system"),
        "caution_direction": config.get("caution_direction"),
        "direction_layer": direction.get("layer"),
        "direction_sigma": direction.get("sigma"),
        "arms": arms,
        "rows": config.get("rows"),
        "rows_filter": config.get("rows_filter"),
        "max_new_tokens": max_new_tokens,
    }
    if batch_size != 1:
        # sequential (=1) keeps the historical fingerprint; a batched run is a
        # different decode regime and must not resume a sequential partial.
        payload["batch_size"] = batch_size
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def _unit_key(row_key: str, arm_id: str) -> str:
    return f"{arm_id}::{row_key}"


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
                continue
            uk = _unit_key(rec.get("probe_pool_row_key", ""), rec.get("arm_id", ""))
            if uk in completed:
                continue
            completed.add(uk)
            kept.append(rec)
    return completed, kept


def run_config(config_path: Path, *, fresh: bool = False) -> dict[str, Any]:
    config = load_config(config_path)
    sweep = config.get("sweep", {})
    max_new_tokens = int(sweep.get("max_new_tokens", 96))
    max_rows = sweep.get("max_rows")
    max_rows = int(max_rows) if max_rows is not None else None
    batch_size = int(sweep.get("batch_size", 1))
    if batch_size < 1:
        raise ResidualInterventionRunError(f"batch_size must be >= 1, got {batch_size}")

    rf = config.get("rows_filter", {})
    labels = set(rf["labels"]) if rf.get("labels") else None
    cells = set(rf["cells"]) if rf.get("cells") else None
    max_rows_per_cell = rf.get("max_rows_per_cell")
    max_rows_per_cell = int(max_rows_per_cell) if max_rows_per_cell is not None else None

    direction = load_direction(resolve_path(config["caution_direction"]))
    spec = ri.build_intervention_spec(direction)
    arms = ri.parse_arms(config["arms"])
    rows = load_rows(resolve_path(config["rows"]), max_rows=max_rows, labels=labels, cells=cells,
                     max_rows_per_cell=max_rows_per_cell)

    # Amendment AC: couple arms resolve a per-row alpha from a doubt gain map.
    # Load each arm's map once (keyed by arm_id, kept OFF the arm dict so the
    # config fingerprint stays path-independent) and fail fast if any eval row
    # is missing, before spending any GPU time.
    gain_maps: dict[str, dict[str, Any]] = {}
    for arm in arms:
        if arm["mode"] != ri.MODE_COUPLE:
            continue
        with resolve_path(arm["gain_map"]).open(encoding="utf-8") as fh:
            gain_maps[arm["arm_id"]] = json.load(fh)
        for row in rows:
            ri.resolve_couple_alpha(gain_maps[arm["arm_id"]], arm["gain_key"],
                                    row["probe_pool_row_key"])

    output_root = resolve_path(config["output"]["root"])
    output_root.mkdir(parents=True, exist_ok=True)
    rows_path = output_root / "rows.jsonl"
    ckpt_path = output_root / "checkpoint.json"
    fingerprint = _config_fingerprint(config, direction=direction, arms=arms,
                                      max_new_tokens=max_new_tokens, batch_size=batch_size)

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
            raise ResidualInterventionRunError(
                f"checkpoint fingerprint {prior_fp!r} != current {fingerprint!r}: config changed since the "
                f"partial run in {output_root}. Re-run with --fresh to discard prior rows."
            )
        completed, scored_rows = _load_completed(rows_path)

    total_units = len(rows) * len(arms)
    ckpt_path.write_text(
        json.dumps({"fingerprint": fingerprint, "total_units": total_units, "config": str(config_path)},
                   indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    harness: ModelHarness | None = None
    generated = 0
    with rows_path.open("w", encoding="utf-8") as out_fh:
        for rec in scored_rows:
            out_fh.write(json.dumps(rec) + "\n")
        out_fh.flush()
        for arm in arms:
            pending = [row for row in rows
                       if _unit_key(row["probe_pool_row_key"], arm["arm_id"]) not in completed]
            for start in range(0, len(pending), batch_size):
                chunk = pending[start:start + batch_size]
                if harness is None:
                    harness = ModelHarness(config)
                if arm["mode"] == ri.MODE_COUPLE:
                    alphas = [ri.resolve_couple_alpha(
                        gain_maps[arm["arm_id"]], arm["gain_key"],
                        r["probe_pool_row_key"]) for r in chunk]
                    # scalar for a 1-row forward (the sequential contract);
                    # per-row vector otherwise (the hook broadcasts it).
                    effective_arm = {**arm, "alpha": (alphas[0] if len(chunk) == 1
                                                      else alphas)}
                else:
                    alphas = [arm["alpha"]] * len(chunk)
                    effective_arm = arm
                if batch_size == 1:
                    answers = [harness.generate(
                        chunk[0]["question"], spec=spec, arm=effective_arm,
                        max_new_tokens=max_new_tokens)]
                else:
                    answers = harness.generate_batch(
                        [r["question"] for r in chunk], spec=spec,
                        arm=effective_arm, max_new_tokens=max_new_tokens)
                for row, answer, row_alpha in zip(chunk, answers, alphas):
                    key = row["probe_pool_row_key"]
                    cells_scored = score_generation(row, answer)
                    record = {
                        "probe_pool_row_key": key,
                        "arm_id": arm["arm_id"],
                        "arm_mode": arm["mode"],
                        "arm_alpha": float(row_alpha),
                        "label": row["label"],
                        "behavior_cell": row.get("behavior_cell"),
                        "generated_answer": answer,
                        **cells_scored,
                    }
                    scored_rows.append(record)
                    completed.add(_unit_key(key, arm["arm_id"]))
                    generated += 1
                    out_fh.write(json.dumps(record) + "\n")
                out_fh.flush()

    observed_cells = {r.get("behavior_cell") for r in scored_rows}
    groups = tuple(c for c in (ri.KNOWN_REFUSED, ri.KNOWN_ANSWERED, ri.UNKNOWN_REFUSED)
                   if c in observed_cells) or ri.DEFAULT_GROUPS
    analysis = ri.analyze_arms(scored_rows, groups=groups)
    summary = {
        "ok": True,
        "analysis_type": "phase3_residual_intervention_sweep",
        "notice": "RESIDUAL_CAUTION_CAUSAL_INTERVENTION",
        "config": str(config_path),
        "fingerprint": fingerprint,
        "caution_direction": config["caution_direction"],
        "direction_layer": direction.get("layer"),
        "arms": [a["arm_id"] for a in arms],
        "rows": config["rows"],
        "rows_filter": rf,
        "max_new_tokens": max_new_tokens,
        "row_count": len(rows),
        "total_units": total_units,
        "units_generated": generated,
        "units_resumed": total_units - generated,
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
    except (ResidualInterventionRunError, ri.ResidualInterventionError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(
        f"units: {summary['units_generated']} generated, {summary['units_resumed']} resumed, "
        f"{summary['total_units']} total",
        file=sys.stderr,
    )
    print(json.dumps(summary["analysis"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
