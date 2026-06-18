#!/usr/bin/env python3
"""Phase 3 activation-addition causal-pilot runner.

This is an explicit Tier 2 exploratory local runner. It does not relax the
readiness-only dry-run contract in `phase3_causal_pilot_dry_run.py`: generation
requires both a generation-enabled config and `--allow-generation`.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from collections import defaultdict
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import yaml

PROBE_DIR = Path(__file__).resolve().parent
REPO_ROOT = PROBE_DIR.parents[2]
EVAL_DIR = REPO_ROOT / "experiment" / "phase1" / "eval"
if str(PROBE_DIR) not in sys.path:
    sys.path.insert(0, str(PROBE_DIR))
if str(EVAL_DIR) not in sys.path:
    sys.path.insert(0, str(EVAL_DIR))

import phase3_causal_pilot_dry_run as dry_run  # noqa: E402
import scorers  # noqa: E402
from backends import render_probe_prompt  # noqa: E402


class PilotRunnerError(RuntimeError):
    pass


SUPPORTED_CONTROLS = {
    "no_vector_baseline",
    "activation_addition",
    "activation_subtraction",
    "sign_flip",
}
SUPPORTED_LOGIT_DIAGNOSTIC_CONTROLS = {
    "no_vector_baseline",
    "activation_addition",
    "activation_subtraction",
}


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        payload = yaml.safe_load(fh)
    if not isinstance(payload, dict):
        raise PilotRunnerError(f"{path} did not load to a YAML mapping")
    return payload


def config_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def resolve_path(value: str | Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return (REPO_ROOT / path).resolve()


def resolve_runtime_path(value: str | Path | None) -> str | None:
    """Map Docker `/workspace/repo/...` paths to this checkout when needed."""
    if value is None:
        return None
    text = str(value)
    docker_prefix = "/workspace/repo/"
    if text.startswith(docker_prefix) and not Path(text).exists():
        return str((REPO_ROOT / text[len(docker_prefix):]).resolve())
    return text


def require_generation_enabled(config: dict[str, Any], *, allow_generation: bool) -> None:
    if not allow_generation:
        raise PilotRunnerError("Refusing to run generation without --allow-generation")
    if config.get("spec", {}).get("status") != "generation_smoke":
        raise PilotRunnerError("Live runner requires spec.status: generation_smoke")
    allowed = (
        config.get("first_smoke", {})
        .get("initial_scope", {})
        .get("generation_allowed_by_this_spec")
    )
    if allowed is not True:
        raise PilotRunnerError(
            "Live runner requires first_smoke.initial_scope.generation_allowed_by_this_spec: true"
        )
    if config.get("output", {}).get("intervention_results_allowed_by_this_spec") is not True:
        raise PilotRunnerError(
            "Live runner requires output.intervention_results_allowed_by_this_spec: true"
        )
    if config.get("model", {}).get("enable_thinking") is not False:
        raise PilotRunnerError("Phase 3 smoke requires model.enable_thinking: false")


def require_logit_diagnostic_enabled(config: dict[str, Any], *, allow_logit_diagnostic: bool) -> None:
    if not allow_logit_diagnostic:
        raise PilotRunnerError("Refusing to run logit diagnostic without --allow-logit-diagnostic")
    require_generation_enabled(config, allow_generation=True)


def block_index_for_hidden_state_layer(layer: int) -> int:
    """Map Transformers hidden_states layer id to decoder block index.

    hidden_states[0] is the embedding output, so intervention layer N maps to
    decoder block N-1. The first causal pilot only supports decoder blocks.
    """
    if layer <= 0:
        raise PilotRunnerError("Activation addition targets decoder layers; layer 0 is embeddings")
    return layer - 1


def find_decoder_layers(model: Any) -> Any:
    """Resolve Qwen decoder blocks across common Transformers/PEFT wrappers."""
    candidates = [
        ("base_model", "model", "model", "layers"),
        ("base_model", "model", "layers"),
        ("model", "model", "layers"),
        ("model", "layers"),
        ("layers",),
    ]
    for path in candidates:
        cur = model
        for attr in path:
            cur = getattr(cur, attr, None)
            if cur is None:
                break
        if cur is not None:
            return cur
    raise PilotRunnerError("Could not locate decoder layers on model/PEFT wrapper")


def _replace_hook_output(output: Any, hidden: Any) -> Any:
    if isinstance(output, tuple):
        return (hidden, *output[1:])
    return hidden


def make_final_prompt_token_addition_hook(direction: Any, coefficient: float):
    """Return a hook that adds `coefficient * direction` once at final prompt token."""
    state = {"applied": False, "applied_count": 0, "delta_abs_sum": 0.0}

    def hook(_module: Any, _inputs: tuple[Any, ...], output: Any) -> Any:
        if state["applied"]:
            return output
        hidden = output[0] if isinstance(output, tuple) else output
        if getattr(hidden, "ndim", None) != 3 or hidden.shape[1] <= 1:
            return output
        steered = hidden.clone()
        vec = direction.to(device=steered.device, dtype=steered.dtype)
        delta = coefficient * vec
        steered[:, -1, :] = steered[:, -1, :] + delta
        state["applied"] = True
        state["applied_count"] += 1
        state["delta_abs_sum"] = float(delta.float().abs().sum().detach().cpu())
        return _replace_hook_output(output, steered)

    hook._phase3_state = state  # type: ignore[attr-defined]
    return hook


@contextmanager
def activation_addition_hook(model: Any, *, layer: int, direction: Any, coefficient: float):
    layers = find_decoder_layers(model)
    block_index = block_index_for_hidden_state_layer(layer)
    if block_index >= len(layers):
        raise PilotRunnerError(
            f"Layer {layer} maps to block {block_index}, but model has only {len(layers)} blocks"
        )
    hook = make_final_prompt_token_addition_hook(direction, coefficient)
    handle = layers[block_index].register_forward_hook(hook)
    try:
        yield hook._phase3_state  # type: ignore[attr-defined]
    finally:
        handle.remove()


def load_probe_rows(probe_results: Path, keys: set[str]) -> dict[str, dict[str, Any]]:
    found: dict[str, dict[str, Any]] = {}
    with probe_results.open(encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            row = json.loads(line)
            key = row.get("probe_pool_row_key")
            if key in keys:
                found[key] = row
    return found


def select_balanced_rows(
    extraction_rows: Path,
    *,
    max_rows: int,
    probe_results: Path | None = None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with extraction_rows.open(encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                rows.append(json.loads(line))
    if max_rows <= 0:
        return rows
    per_label = max(1, max_rows // 2)
    selected: list[dict[str, Any]] = []
    counts: dict[str, int] = defaultdict(int)
    for row in rows:
        label = row.get("label")
        if label in {"known", "unknown"} and counts[label] < per_label:
            selected.append(row)
            counts[label] += 1
        if counts["known"] >= per_label and counts["unknown"] >= per_label:
            break
    if probe_results is not None:
        by_key = load_probe_rows(probe_results, {r["probe_pool_row_key"] for r in selected})
        for row in selected:
            probe_row = by_key.get(row["probe_pool_row_key"], {})
            row["aliases"] = probe_row.get("normalized_aliases", [])
            row["answer_value"] = probe_row.get("answer_value")
    return selected[:max_rows]


def score_generation(row: dict[str, Any], generated_answer: str) -> dict[str, Any]:
    refused = scorers.is_stated_confidence_refusal(generated_answer)
    label = row.get("label")
    aliases = row.get("aliases", [])
    correct = False if refused else scorers.is_correct(generated_answer, aliases)
    truthful = (refused if label == "unknown" else correct)
    return {
        "refused": bool(refused),
        "correct": bool(correct),
        "truthful": bool(truthful),
    }


def summarize_metrics(scored_rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    rows_all = list(scored_rows)
    baseline_by_key = {
        row["probe_pool_row_key"]: row
        for row in rows_all
        if row.get("control") == "no_vector_baseline"
    }
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows_all:
        groups[row["arm_id"]].append(row)
    out: dict[str, Any] = {}
    for arm_id, rows in groups.items():
        known = [r for r in rows if r.get("label") == "known"]
        unknown = [r for r in rows if r.get("label") == "unknown"]
        joined = [
            (row, baseline_by_key[row["probe_pool_row_key"]])
            for row in rows
            if row.get("probe_pool_row_key") in baseline_by_key
        ]
        out[arm_id] = {
            "n": len(rows),
            "n_known": len(known),
            "n_unknown": len(unknown),
            "unknown_refusal_rate": _pct(sum(r["refused"] for r in unknown), len(unknown)),
            "answer_on_unknown_rate": _pct(sum(not r["refused"] for r in unknown), len(unknown)),
            "over_refusal_on_known": _pct(sum(r["refused"] for r in known), len(known)),
            "known_answer_retention": _pct(sum(not r["refused"] for r in known), len(known)),
            "known_answer_correctness": _pct(sum(r["correct"] for r in known), len(known)),
            "truthful_rate": _pct(sum(r["truthful"] for r in rows), len(rows)),
            "thinking_tag_contamination_count": sum(
                _has_thinking_tag(str(r.get("generated_answer", ""))) for r in rows
            ),
            "per_row_delta_vs_no_vector": {
                "n_joined": len(joined),
                "refusal_changed": sum(row["refused"] != base["refused"] for row, base in joined),
                "truthful_changed": sum(row["truthful"] != base["truthful"] for row, base in joined),
                "correct_changed": sum(row["correct"] != base["correct"] for row, base in joined),
            },
        }
    return out


def _pct(num: int, den: int) -> float:
    return round(100.0 * num / den, 2) if den else 0.0


def _has_thinking_tag(text: str) -> bool:
    return "<think>" in text or "</think>" in text or "reasoning_content" in text


def build_smoke_arms(
    *,
    candidate: dict[str, Any],
    coefficients: list[float],
    controls: list[str],
) -> list[dict[str, Any]]:
    arms: list[dict[str, Any]] = []
    for coefficient in coefficients:
        for control in controls:
            effective = effective_coefficient_for_control(control, coefficient)
            arms.append({
                "arm_id": (
                    f"{candidate['label']}__coef_{str(coefficient).replace('-', 'neg_').replace('.', 'p')}"
                    f"__control_{control}"
                ),
                "candidate_label": candidate["label"],
                "coefficient": effective,
                "grid_coefficient": coefficient,
                "control": control,
                "direction_id": None if control == "no_vector_baseline" else candidate["direction_id"],
                "layer": candidate["layer"],
                "role": candidate["role"],
                "generation_executed": True,
            })
    return arms


def effective_coefficient_for_control(control: str, coefficient: float) -> float:
    if control not in SUPPORTED_CONTROLS:
        raise PilotRunnerError(
            f"Unsupported live control {control!r}; supported controls are "
            f"{sorted(SUPPORTED_CONTROLS)}"
        )
    magnitude = abs(float(coefficient))
    if control == "no_vector_baseline":
        return 0.0
    if control == "activation_addition":
        return magnitude
    if control in {"activation_subtraction", "sign_flip"}:
        return -magnitude
    raise AssertionError(f"unhandled control: {control}")


def effective_coefficient_for_logit_diagnostic_control(control: str, coefficient: float) -> float:
    if control not in SUPPORTED_LOGIT_DIAGNOSTIC_CONTROLS:
        raise PilotRunnerError(
            f"Unsupported logit diagnostic control {control!r}; supported controls are "
            f"{sorted(SUPPORTED_LOGIT_DIAGNOSTIC_CONTROLS)}"
        )
    return effective_coefficient_for_control(control, coefficient)


def validate_logit_diagnostic_controls(controls: list[str]) -> None:
    for control in controls:
        effective_coefficient_for_logit_diagnostic_control(control, 1.0)
    if "no_vector_baseline" not in controls:
        raise PilotRunnerError("Logit diagnostic controls must include no_vector_baseline")
    if controls[0] != "no_vector_baseline":
        raise PilotRunnerError(
            "Logit diagnostic requires no_vector_baseline as the first control"
        )


def validate_non_empty_run_grid(coefficients: list[float], controls: list[str]) -> None:
    if not coefficients:
        raise PilotRunnerError("At least one coefficient is required")
    if not controls:
        raise PilotRunnerError("At least one control is required")


def load_direction_tensor(candidate: dict[str, Any]):
    from safetensors.torch import load_file  # noqa: PLC0415

    payload = load_file(str(resolve_path(candidate["direction_file"])))
    tensor_key = candidate.get("tensor_key", "direction")
    if tensor_key not in payload:
        raise PilotRunnerError(f"{candidate['direction_file']} missing tensor key {tensor_key!r}")
    return payload[tensor_key]


class TransformersActivationGenerator:
    def __init__(self, config: dict[str, Any], candidate: dict[str, Any]):
        import torch  # noqa: PLC0415
        from peft import PeftModel  # noqa: PLC0415
        from transformers import AutoModelForCausalLM, AutoTokenizer  # noqa: PLC0415

        self.torch = torch
        extraction_manifest = json.loads(
            resolve_path(candidate["extraction_manifest"]).read_text(encoding="utf-8")
        )
        model_cfg = config.get("runtime_model", {})
        self.model_name = model_cfg.get("model_name") or extraction_manifest["base_model_id"]
        revision = model_cfg.get("revision") or extraction_manifest.get("base_model_revision")
        if isinstance(revision, str) and revision.startswith("local-sha256:"):
            revision = None
        adapter_path = resolve_runtime_path(
            model_cfg.get("adapter_path") or extraction_manifest.get("adapter_path")
        )
        if not adapter_path:
            raise PilotRunnerError("No adapter path available for active SFT smoke")
        dtype_name = model_cfg.get("torch_dtype", extraction_manifest.get("compute_dtype", "bfloat16"))
        dtype = getattr(torch, dtype_name)
        device_map = model_cfg.get("device_map", "cuda")
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name, revision=revision)
        base = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            revision=revision,
            torch_dtype=dtype,
            device_map=device_map,
        )
        self.model = PeftModel.from_pretrained(
            base,
            adapter_path,
            adapter_name=candidate.get("arm") or extraction_manifest.get("active_adapter_name", "sft"),
        )
        self.model.eval()
        self.device = next(self.model.parameters()).device
        self.system_prompt = config.get("prompt", {}).get(
            "system", "You are a helpful assistant. Answer the question concisely."
        )
        self.enable_thinking = config.get("model", {}).get("enable_thinking", False)
        self.last_hook_state: dict[str, Any] = {}

    def generate(self, question: str, *, direction: Any, layer: int, coefficient: float, max_new_tokens: int) -> str:
        rendered, _mode = render_probe_prompt(
            self.tokenizer,
            self.system_prompt,
            question,
            enable_thinking=self.enable_thinking,
        )
        inputs = self.tokenizer(rendered, return_tensors="pt").to(self.device)
        direction = direction.to(self.device)
        with self.torch.no_grad():
            with activation_addition_hook(
                self.model,
                layer=layer,
                direction=direction,
                coefficient=coefficient,
            ) as hook_state:
                output_ids = self.model.generate(
                    **inputs,
                    do_sample=False,
                    max_new_tokens=max_new_tokens,
                    pad_token_id=self.tokenizer.eos_token_id,
                )
            self.last_hook_state = dict(hook_state)
        new_tokens = output_ids[0, inputs["input_ids"].shape[1]:]
        return self.tokenizer.decode(new_tokens, skip_special_tokens=True).strip()

    def next_token_logits(self, question: str, *, direction: Any, layer: int, coefficient: float) -> Any:
        rendered, _mode = render_probe_prompt(
            self.tokenizer,
            self.system_prompt,
            question,
            enable_thinking=self.enable_thinking,
        )
        inputs = self.tokenizer(rendered, return_tensors="pt").to(self.device)
        direction = direction.to(self.device)
        with self.torch.no_grad():
            with activation_addition_hook(
                self.model,
                layer=layer,
                direction=direction,
                coefficient=coefficient,
            ) as hook_state:
                outputs = self.model(**inputs)
            self.last_hook_state = dict(hook_state)
        return outputs.logits[0, -1, :].detach().float().cpu()


def compute_next_token_logit_metrics(
    *,
    baseline_logits: Any,
    intervention_logits: Any,
    tokenizer: Any,
) -> dict[str, Any]:
    import torch  # noqa: PLC0415

    baseline = torch.as_tensor(baseline_logits, dtype=torch.float32)
    intervention = torch.as_tensor(intervention_logits, dtype=torch.float32)
    if baseline.shape != intervention.shape:
        raise PilotRunnerError(
            f"Logit shape mismatch: baseline {tuple(baseline.shape)} vs "
            f"intervention {tuple(intervention.shape)}"
        )
    delta = intervention - baseline
    baseline_top1_token_id = int(torch.argmax(baseline).item())
    intervention_top1_token_id = int(torch.argmax(intervention).item())
    return {
        "max_abs_logit_delta": float(delta.abs().max().item()),
        "l2_logit_delta": float(torch.linalg.vector_norm(delta).item()),
        "baseline_top1_token_id": baseline_top1_token_id,
        "baseline_top1_text": decode_single_token(tokenizer, baseline_top1_token_id),
        "intervention_top1_token_id": intervention_top1_token_id,
        "intervention_top1_text": decode_single_token(tokenizer, intervention_top1_token_id),
        "top1_changed": baseline_top1_token_id != intervention_top1_token_id,
        "baseline_top1_logit": float(baseline[baseline_top1_token_id].item()),
        "intervention_top1_logit": float(intervention[intervention_top1_token_id].item()),
    }


def decode_single_token(tokenizer: Any, token_id: int) -> str:
    return tokenizer.decode([token_id], skip_special_tokens=False)


def summarize_logit_metrics(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[row["arm_id"]].append(row)
    out: dict[str, Any] = {}
    for arm_id, arm_rows in groups.items():
        out[arm_id] = {
            "n": len(arm_rows),
            "top1_changed_count": sum(bool(r["top1_changed"]) for r in arm_rows),
            "top1_changed_rate": _pct(
                sum(bool(r["top1_changed"]) for r in arm_rows),
                len(arm_rows),
            ),
            "max_abs_logit_delta_max": _max_float(r["max_abs_logit_delta"] for r in arm_rows),
            "max_abs_logit_delta_mean": _mean_float(r["max_abs_logit_delta"] for r in arm_rows),
            "l2_logit_delta_mean": _mean_float(r["l2_logit_delta"] for r in arm_rows),
            "intervention_applied_count_total": sum(
                int(r.get("intervention_applied_count", 0)) for r in arm_rows
            ),
            "intervention_delta_abs_sum_mean": _mean_float(
                r.get("intervention_delta_abs_sum", 0.0) for r in arm_rows
            ),
        }
    return out


def _mean_float(values: Iterable[Any]) -> float:
    vals = [float(value) for value in values]
    return round(sum(vals) / len(vals), 6) if vals else 0.0


def _max_float(values: Iterable[Any]) -> float:
    vals = [float(value) for value in values]
    return max(vals) if vals else 0.0


def run(config_path: Path, args: argparse.Namespace) -> dict[str, Any]:
    config = load_yaml(config_path)
    if args.mode == "generation":
        require_generation_enabled(config, allow_generation=args.allow_generation)
    elif args.mode == "logit_diagnostic":
        require_logit_diagnostic_enabled(
            config,
            allow_logit_diagnostic=args.allow_logit_diagnostic,
        )
    else:
        raise PilotRunnerError(f"Unsupported runner mode {args.mode!r}")
    candidate_summaries = []
    for raw_candidate in config.get("candidate_directions", []):
        validated = dry_run.validate_candidate(
            raw_candidate, config.get("readiness_checks", {})
        )
        candidate_summaries.append({**raw_candidate, **validated})
    matches = [c for c in candidate_summaries if c["label"] == args.candidate]
    if len(matches) != 1:
        raise PilotRunnerError(f"Expected exactly one candidate {args.candidate!r}; found {len(matches)}")
    candidate = matches[0]
    coefficients = _parse_csv_floats(args.coefficients)
    controls = _parse_csv_strings(args.controls)
    validate_non_empty_run_grid(coefficients, controls)
    if args.mode == "logit_diagnostic":
        validate_logit_diagnostic_controls(controls)
    arms = build_smoke_arms(candidate=candidate, coefficients=coefficients, controls=controls)

    extraction_dir = resolve_path(candidate["extraction_dir"])
    probe_results = config.get("selection", {}).get("probe_results")
    rows = select_balanced_rows(
        extraction_dir / "rows.jsonl",
        max_rows=args.max_rows,
        probe_results=resolve_path(probe_results) if probe_results else None,
    )
    if not rows:
        raise PilotRunnerError("No rows selected for pilot")

    direction = load_direction_tensor(candidate)
    generator = TransformersActivationGenerator(config, candidate)
    output_root = _run_output_root(config)
    output_root.mkdir(parents=True, exist_ok=False)

    if args.mode == "logit_diagnostic":
        return run_logit_diagnostic(
            config_path=config_path,
            config=config,
            candidate=candidate,
            coefficients=coefficients,
            controls=controls,
            arms=arms,
            rows=rows,
            direction=direction,
            generator=generator,
            output_root=output_root,
        )

    generations_path = output_root / "generations.jsonl"
    scored_path = output_root / "scored_rows.jsonl"
    scored_rows: list[dict[str, Any]] = []
    with generations_path.open("w", encoding="utf-8") as gen_fh, scored_path.open("w", encoding="utf-8") as score_fh:
        for arm in arms:
            for row in rows:
                generated = generator.generate(
                    row["question"],
                    direction=direction,
                    layer=int(arm["layer"]),
                    coefficient=float(arm["coefficient"]),
                    max_new_tokens=args.max_new_tokens,
                )
                generation_row = {
                    **row,
                    **arm,
                    "generated_answer": generated,
                    "intervention_applied_count": generator.last_hook_state.get(
                        "applied_count", 0
                    ),
                    "intervention_delta_abs_sum": generator.last_hook_state.get(
                        "delta_abs_sum", 0.0
                    ),
                }
                gen_fh.write(json.dumps(generation_row, ensure_ascii=False) + "\n")
                scored = {
                    **generation_row,
                    **score_generation(row, generated),
                }
                scored_rows.append(scored)
                score_fh.write(json.dumps(scored, ensure_ascii=False) + "\n")

    metrics = summarize_metrics(scored_rows)
    (output_root / "metrics.json").write_text(
        json.dumps(metrics, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    manifest = {
        "status": "ok",
        "generation_executed": True,
        "evidence_tier": "tier2_exploratory_local",
        "config": str(config_path.resolve()),
        "config_sha": config_sha(config_path),
        "candidate": candidate,
        "coefficients": coefficients,
        "controls": controls,
        "row_count": len(rows),
        "arm_count": len(arms),
        "outputs": {
            "generations": str(generations_path),
            "scored_rows": str(scored_path),
            "metrics": str(output_root / "metrics.json"),
        },
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    (output_root / "run_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {
        "ok": True,
        "generation_executed": True,
        "output_root": str(output_root),
        "arm_count": len(arms),
        "row_count": len(rows),
    }


def run_logit_diagnostic(
    *,
    config_path: Path,
    config: dict[str, Any],
    candidate: dict[str, Any],
    coefficients: list[float],
    controls: list[str],
    arms: list[dict[str, Any]],
    rows: list[dict[str, Any]],
    direction: Any,
    generator: TransformersActivationGenerator,
    output_root: Path,
) -> dict[str, Any]:
    diagnostic_path = output_root / "logit_diagnostics.jsonl"
    metrics_path = output_root / "logit_metrics.json"
    baseline_logits_by_key: dict[tuple[str, float], Any] = {}
    diagnostic_rows: list[dict[str, Any]] = []

    with diagnostic_path.open("w", encoding="utf-8") as fh:
        for arm in arms:
            control = arm["control"]
            effective_coefficient_for_logit_diagnostic_control(
                control,
                float(arm["grid_coefficient"]),
            )
            for row in rows:
                logits = generator.next_token_logits(
                    row["question"],
                    direction=direction,
                    layer=int(arm["layer"]),
                    coefficient=float(arm["coefficient"]),
                )
                row_key = row["probe_pool_row_key"]
                baseline_key = (row_key, float(arm["grid_coefficient"]))
                if control == "no_vector_baseline":
                    baseline_logits_by_key[baseline_key] = logits
                if baseline_key not in baseline_logits_by_key:
                    raise PilotRunnerError(
                        "Logit diagnostic requires no_vector_baseline before interventions "
                        f"for row {row_key!r} coefficient {arm['grid_coefficient']!r}"
                    )
                metrics = compute_next_token_logit_metrics(
                    baseline_logits=baseline_logits_by_key[baseline_key],
                    intervention_logits=logits,
                    tokenizer=generator.tokenizer,
                )
                diagnostic_row = build_logit_diagnostic_row(
                    row=row,
                    arm=arm,
                    metrics=metrics,
                    hook_state=generator.last_hook_state,
                )
                diagnostic_rows.append(diagnostic_row)
                fh.write(json.dumps(diagnostic_row, ensure_ascii=False) + "\n")

    metrics = summarize_logit_metrics(diagnostic_rows)
    metrics_path.write_text(
        json.dumps(metrics, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    manifest = {
        "status": "ok",
        "generation_executed": False,
        "logit_diagnostic_executed": True,
        "evidence_tier": "tier2_exploratory_local",
        "config": str(config_path.resolve()),
        "config_sha": config_sha(config_path),
        "candidate": candidate,
        "coefficients": coefficients,
        "controls": controls,
        "row_count": len(rows),
        "arm_count": len(arms),
        "outputs": {
            "logit_diagnostics": str(diagnostic_path),
            "logit_metrics": str(metrics_path),
        },
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    (output_root / "run_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {
        "ok": True,
        "generation_executed": False,
        "logit_diagnostic_executed": True,
        "output_root": str(output_root),
        "arm_count": len(arms),
        "row_count": len(rows),
    }


def build_logit_diagnostic_row(
    *,
    row: dict[str, Any],
    arm: dict[str, Any],
    metrics: dict[str, Any],
    hook_state: dict[str, Any],
) -> dict[str, Any]:
    return {
        **row,
        **arm,
        **metrics,
        "generation_executed": False,
        "logit_diagnostic_executed": True,
        "intervention_applied_count": hook_state.get("applied_count", 0),
        "intervention_delta_abs_sum": hook_state.get("delta_abs_sum", 0.0),
    }


def _run_output_root(config: dict[str, Any]) -> Path:
    root = resolve_path(config.get("output", {}).get("root", "phase3_activation_smoke"))
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return root / f"run_{stamp}"


def _parse_csv_floats(value: str) -> list[float]:
    return [float(part.strip()) for part in value.split(",") if part.strip()]


def _parse_csv_strings(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=["generation", "logit_diagnostic"],
        default="generation",
    )
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--coefficients", default="0,1,-1")
    parser.add_argument(
        "--controls",
        default="no_vector_baseline,activation_addition,activation_subtraction",
    )
    parser.add_argument("--max-rows", type=int, default=16)
    parser.add_argument("--max-new-tokens", type=int, default=64)
    parser.add_argument("--allow-generation", action="store_true")
    parser.add_argument("--allow-logit-diagnostic", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        result = run(args.config, args)
    except (PilotRunnerError, dry_run.DryRunValidationError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
