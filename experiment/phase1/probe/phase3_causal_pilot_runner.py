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
import re
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
    "wrong_layer",
    "wrong_layer_subtraction",
    "random_matched_norm",
}
LOGIT_TARGET_NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$")
GENERATION_ONLY_UNSUPPORTED_CONTROLS = SUPPORTED_LOGIT_DIAGNOSTIC_CONTROLS - SUPPORTED_CONTROLS


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
    seen_keys: set[Any] = set()
    with probe_results.open(encoding="utf-8") as fh:
        for line_number, line in enumerate(fh, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            key = row.get("probe_pool_row_key")
            if key in seen_keys:
                raise PilotRunnerError(
                    f"Duplicate probe_pool_row_key {key!r} in {probe_results} at line {line_number}"
                )
            seen_keys.add(key)
            if key in keys:
                found[key] = row
    return found


def select_balanced_rows(
    extraction_rows: Path,
    *,
    max_rows: int,
    probe_results: Path | None = None,
    row_keys: list[str] | None = None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen_keys: set[Any] = set()
    with extraction_rows.open(encoding="utf-8") as fh:
        for line_number, line in enumerate(fh, start=1):
            if line.strip():
                row = json.loads(line)
                key = row.get("probe_pool_row_key")
                if key in seen_keys:
                    raise PilotRunnerError(
                        f"Duplicate probe_pool_row_key {key!r} in {extraction_rows} at line {line_number}"
                    )
                seen_keys.add(key)
                rows.append(row)
    if row_keys:
        if len(set(row_keys)) != len(row_keys):
            raise PilotRunnerError("selection.row_keys must not contain duplicates")
        by_key = {row.get("probe_pool_row_key"): row for row in rows}
        missing = [key for key in row_keys if key not in by_key]
        if missing:
            raise PilotRunnerError(f"selection.row_keys missing from extraction rows: {missing}")
        selected = [by_key[key] for key in row_keys]
    elif max_rows <= 0:
        selected = rows
    else:
        per_label = max(1, max_rows // 2)
        selected = []
        counts: dict[str, int] = defaultdict(int)
        for row in rows:
            label = row.get("label")
            if label in {"known", "unknown"} and counts[label] < per_label:
                selected.append(row)
                counts[label] += 1
            if counts["known"] >= per_label and counts["unknown"] >= per_label:
                break
        selected = selected[:max_rows]
    if probe_results is not None:
        by_key = load_probe_rows(probe_results, {r["probe_pool_row_key"] for r in selected})
        for row in selected:
            probe_row = by_key.get(row["probe_pool_row_key"], {})
            row["aliases"] = probe_row.get("normalized_aliases", [])
            row["answer_value"] = probe_row.get("answer_value")
    return selected


def selection_row_keys_for_candidate(config: dict[str, Any], candidate_label: str) -> list[str] | None:
    selection = config.get("selection", {})
    by_candidate = selection.get("row_keys_by_candidate", {})
    if by_candidate:
        if not isinstance(by_candidate, dict):
            raise PilotRunnerError("selection.row_keys_by_candidate must be a mapping")
        raw_keys = by_candidate.get(candidate_label)
        if raw_keys is not None:
            return validate_selection_row_keys(raw_keys, "selection.row_keys_by_candidate")
    raw_keys = selection.get("row_keys")
    if raw_keys is None:
        return None
    return validate_selection_row_keys(raw_keys, "selection.row_keys")


def validate_selection_row_keys(raw_keys: Any, field_name: str) -> list[str]:
    if not isinstance(raw_keys, list) or not raw_keys:
        raise PilotRunnerError(f"{field_name} must be a non-empty list of row keys")
    if not all(isinstance(key, str) and key for key in raw_keys):
        raise PilotRunnerError(f"{field_name} must contain only non-empty strings")
    if len(set(raw_keys)) != len(raw_keys):
        raise PilotRunnerError(f"{field_name} must not contain duplicates")
    return list(raw_keys)


def logit_diagnostic_top_k(config: dict[str, Any]) -> int:
    raw_value = config.get("logit_diagnostic", {}).get("top_k", 5)
    if not isinstance(raw_value, int) or isinstance(raw_value, bool) or raw_value <= 0:
        raise PilotRunnerError("logit_diagnostic.top_k must be a positive integer")
    return raw_value


def runner_control_settings(config: dict[str, Any]) -> dict[str, Any]:
    raw_settings = config.get("control_settings", {})
    if not isinstance(raw_settings, dict):
        raise PilotRunnerError("control_settings must be a mapping")
    return raw_settings


def wrong_layer_offset(control_settings: dict[str, Any]) -> int:
    return wrong_layer_offsets(control_settings)[0]


def wrong_layer_offsets(control_settings: dict[str, Any]) -> list[int]:
    raw_config = control_settings.get("wrong_layer", {})
    if not isinstance(raw_config, dict):
        raise PilotRunnerError("control_settings.wrong_layer must be a mapping")
    if "layer_offsets" in raw_config:
        raw_offsets = raw_config["layer_offsets"]
        if not isinstance(raw_offsets, list) or not raw_offsets:
            raise PilotRunnerError("control_settings.wrong_layer.layer_offsets must be a non-empty list")
        offsets: list[int] = []
        for raw_offset in raw_offsets:
            if not isinstance(raw_offset, int) or isinstance(raw_offset, bool) or raw_offset == 0:
                raise PilotRunnerError(
                    "control_settings.wrong_layer.layer_offsets must contain nonzero integers"
                )
            offsets.append(raw_offset)
        if len(set(offsets)) != len(offsets):
            raise PilotRunnerError("control_settings.wrong_layer.layer_offsets must not contain duplicates")
        return offsets
    raw_offset = raw_config.get("layer_offset", -1)
    if not isinstance(raw_offset, int) or isinstance(raw_offset, bool) or raw_offset == 0:
        raise PilotRunnerError("control_settings.wrong_layer.layer_offset must be a nonzero integer")
    return [raw_offset]


def random_matched_norm_seed(control_settings: dict[str, Any]) -> int:
    raw_config = control_settings.get("random_matched_norm", {})
    if not isinstance(raw_config, dict):
        raise PilotRunnerError("control_settings.random_matched_norm must be a mapping")
    raw_seed = raw_config.get("seed")
    if raw_seed is None:
        raise PilotRunnerError("control_settings.random_matched_norm.seed is required")
    if not isinstance(raw_seed, int) or isinstance(raw_seed, bool) or raw_seed < 0:
        raise PilotRunnerError("control_settings.random_matched_norm.seed must be a non-negative integer")
    return raw_seed


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
    control_settings: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    arms: list[dict[str, Any]] = []
    control_settings = control_settings or {}
    for coefficient in coefficients:
        for control in controls:
            offsets: list[int | None] = (
                wrong_layer_offsets(control_settings)
                if control in {"wrong_layer", "wrong_layer_subtraction"}
                else [None]
            )
            for offset in offsets:
                effective = effective_coefficient_for_control(control, coefficient)
                layer = int(candidate["layer"])
                direction_id = None if control == "no_vector_baseline" else candidate["direction_id"]
                control_provenance: dict[str, Any] = {
                    "control_type": control,
                    "source_direction_id": candidate["direction_id"],
                    "source_layer": int(candidate["layer"]),
                }
                random_seed = None
                arm_suffix = ""
                if offset is not None:
                    layer = int(candidate["layer"]) + offset
                    if layer <= 0:
                        raise PilotRunnerError(
                            f"{control} control produced invalid layer {layer} "
                            f"from source layer {candidate['layer']} offset {offset}"
                        )
                    if layer == int(candidate["layer"]):
                        raise PilotRunnerError(f"{control} control must not use the source layer")
                    control_provenance.update({
                        "wrong_layer_offset": offset,
                        "applied_layer": layer,
                        "uses_source_direction": True,
                    })
                    if len(offsets) > 1:
                        offset_text = str(offset).replace("-", "neg_")
                        arm_suffix = f"__offset_{offset_text}"
                elif control == "random_matched_norm":
                    random_seed = random_matched_norm_seed(control_settings)
                    direction_id = f"random_matched_norm_seed_{random_seed}"
                    control_provenance.update({
                        "random_seed": random_seed,
                        "matched_norm_source_direction_id": candidate["direction_id"],
                        "matched_norm_source_layer": int(candidate["layer"]),
                    })
                arms.append({
                    "arm_id": (
                        f"{candidate['label']}__coef_{str(coefficient).replace('-', 'neg_').replace('.', 'p')}"
                        f"__control_{control}{arm_suffix}"
                    ),
                    "candidate_label": candidate["label"],
                    "coefficient": effective,
                    "grid_coefficient": coefficient,
                    "control": control,
                    "direction_id": direction_id,
                    "layer": layer,
                    "source_layer": int(candidate["layer"]),
                    "role": candidate["role"],
                    "control_provenance": control_provenance,
                    "random_seed": random_seed,
                    "generation_executed": True,
                })
    return arms


def effective_coefficient_for_control(control: str, coefficient: float) -> float:
    if control not in SUPPORTED_CONTROLS | SUPPORTED_LOGIT_DIAGNOSTIC_CONTROLS:
        raise PilotRunnerError(
            f"Unsupported live control {control!r}; supported controls are "
            f"{sorted(SUPPORTED_CONTROLS | SUPPORTED_LOGIT_DIAGNOSTIC_CONTROLS)}"
        )
    magnitude = abs(float(coefficient))
    if control == "no_vector_baseline":
        return 0.0
    if control in {"activation_addition", "wrong_layer", "random_matched_norm"}:
        return magnitude
    if control in {"activation_subtraction", "sign_flip", "wrong_layer_subtraction"}:
        return -magnitude
    raise AssertionError(f"unhandled control: {control}")


def effective_coefficient_for_logit_diagnostic_control(control: str, coefficient: float) -> float:
    if control not in SUPPORTED_LOGIT_DIAGNOSTIC_CONTROLS:
        raise PilotRunnerError(
            f"Unsupported logit diagnostic control {control!r}; supported controls are "
            f"{sorted(SUPPORTED_LOGIT_DIAGNOSTIC_CONTROLS)}"
        )
    return effective_coefficient_for_control(control, coefficient)


def validate_generation_controls(controls: list[str]) -> None:
    for control in controls:
        if control in GENERATION_ONLY_UNSUPPORTED_CONTROLS:
            raise PilotRunnerError(
                f"Control {control!r} is logit-diagnostic-only and is not implemented for generation"
            )
        if control not in SUPPORTED_CONTROLS:
            raise PilotRunnerError(
                f"Unsupported generation control {control!r}; supported controls are "
                f"{sorted(SUPPORTED_CONTROLS)}"
            )


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


def random_matched_norm_direction(direction: Any, *, seed: int) -> Any:
    import torch  # noqa: PLC0415

    source = torch.as_tensor(direction)
    source_float = source.detach().to(device="cpu", dtype=torch.float32)
    source_norm = torch.linalg.vector_norm(source_float)
    if float(source_norm.item()) == 0.0:
        raise PilotRunnerError("random_matched_norm requires a nonzero source direction norm")
    generator = torch.Generator(device="cpu")
    generator.manual_seed(seed)
    random_vector = torch.randn(source_float.shape, generator=generator, dtype=torch.float32)
    random_norm = torch.linalg.vector_norm(random_vector)
    if float(random_norm.item()) == 0.0:
        raise PilotRunnerError("random_matched_norm generated a zero random vector")
    matched = random_vector * (source_norm / random_norm)
    return matched.to(dtype=source.dtype)


def direction_for_arm(direction: Any, arm: dict[str, Any]) -> Any:
    if arm.get("control") == "random_matched_norm":
        seed = arm.get("random_seed")
        if not isinstance(seed, int):
            raise PilotRunnerError("random_matched_norm arm missing integer random_seed")
        return random_matched_norm_direction(direction, seed=seed)
    return direction


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
    logit_targets: list[dict[str, Any]] | None = None,
    top_k: int = 5,
) -> dict[str, Any]:
    import torch  # noqa: PLC0415

    if top_k <= 0:
        raise PilotRunnerError("logit_diagnostic.top_k must be positive")
    baseline = torch.as_tensor(baseline_logits, dtype=torch.float32)
    intervention = torch.as_tensor(intervention_logits, dtype=torch.float32)
    if baseline.shape != intervention.shape:
        raise PilotRunnerError(
            f"Logit shape mismatch: baseline {tuple(baseline.shape)} vs "
            f"intervention {tuple(intervention.shape)}"
        )
    delta = intervention - baseline
    baseline_probs = torch.softmax(baseline, dim=0)
    intervention_probs = torch.softmax(intervention, dim=0)
    baseline_top1_token_id = int(torch.argmax(baseline).item())
    intervention_top1_token_id = int(torch.argmax(intervention).item())
    out = {
        "max_abs_logit_delta": float(delta.abs().max().item()),
        "l2_logit_delta": float(torch.linalg.vector_norm(delta).item()),
        "baseline_top1_token_id": baseline_top1_token_id,
        "baseline_top1_text": decode_single_token(tokenizer, baseline_top1_token_id),
        "intervention_top1_token_id": intervention_top1_token_id,
        "intervention_top1_text": decode_single_token(tokenizer, intervention_top1_token_id),
        "top1_changed": baseline_top1_token_id != intervention_top1_token_id,
        "baseline_top1_logit": float(baseline[baseline_top1_token_id].item()),
        "intervention_top1_logit": float(intervention[intervention_top1_token_id].item()),
        "top_k": min(top_k, int(baseline.numel())),
        "baseline_top_k": top_k_entries(
            values=baseline,
            probabilities=baseline_probs,
            tokenizer=tokenizer,
            top_k=top_k,
        ),
        "intervention_top_k": top_k_entries(
            values=intervention,
            probabilities=intervention_probs,
            tokenizer=tokenizer,
            top_k=top_k,
        ),
    }
    if logit_targets:
        out["logit_target_metrics"] = compute_logit_target_metrics(
            baseline=baseline,
            intervention=intervention,
            baseline_probs=baseline_probs,
            intervention_probs=intervention_probs,
            logit_targets=logit_targets,
        )
    return out


def top_k_entries(
    *,
    values: Any,
    probabilities: Any,
    tokenizer: Any,
    top_k: int,
) -> list[dict[str, Any]]:
    import torch  # noqa: PLC0415

    k = min(top_k, int(values.numel()))
    top_values, top_indices = torch.topk(values, k=k)
    return [
        {
            "rank": index + 1,
            "token_id": int(token_id.item()),
            "token_text": decode_single_token(tokenizer, int(token_id.item())),
            "logit": float(logit.item()),
            "probability": float(probabilities[int(token_id.item())].item()),
        }
        for index, (token_id, logit) in enumerate(zip(top_indices, top_values))
    ]


def compute_logit_target_metrics(
    *,
    baseline: Any,
    intervention: Any,
    baseline_probs: Any,
    intervention_probs: Any,
    logit_targets: list[dict[str, Any]],
) -> dict[str, Any]:
    metrics: dict[str, Any] = {}
    for group in logit_targets:
        token_ids = group["token_ids"]
        baseline_probability_sum = float(baseline_probs[token_ids].sum().item())
        intervention_probability_sum = float(intervention_probs[token_ids].sum().item())
        baseline_logit_sum = float(baseline[token_ids].sum().item())
        intervention_logit_sum = float(intervention[token_ids].sum().item())
        metrics[group["name"]] = {
            "baseline_probability_sum": baseline_probability_sum,
            "intervention_probability_sum": intervention_probability_sum,
            "probability_sum_delta": intervention_probability_sum - baseline_probability_sum,
            "baseline_logit_sum": baseline_logit_sum,
            "intervention_logit_sum": intervention_logit_sum,
            "logit_sum_delta": intervention_logit_sum - baseline_logit_sum,
            "resolved_token_ids": token_ids,
            "resolved_token_texts": group["token_texts"],
            "resolved_targets": group["resolved_targets"],
            "skipped_targets": group.get("skipped_targets", []),
        }
    return metrics


def decode_single_token(tokenizer: Any, token_id: int) -> str:
    return tokenizer.decode([token_id], skip_special_tokens=False)


def resolve_logit_targets(config: dict[str, Any], tokenizer: Any) -> list[dict[str, Any]]:
    raw_targets = config.get("logit_targets")
    if raw_targets is None:
        return []
    if not isinstance(raw_targets, dict):
        raise PilotRunnerError("logit_targets must be a mapping")
    raw_groups = raw_targets.get("groups")
    if not isinstance(raw_groups, list) or not raw_groups:
        raise PilotRunnerError("logit_targets.groups must be a non-empty list")
    resolved: list[dict[str, Any]] = []
    seen_names: set[str] = set()
    for index, raw_group in enumerate(raw_groups):
        if not isinstance(raw_group, dict):
            raise PilotRunnerError(f"logit_targets.groups[{index}] must be a mapping")
        name = raw_group.get("name")
        if not isinstance(name, str) or not LOGIT_TARGET_NAME_RE.fullmatch(name):
            raise PilotRunnerError(
                f"logit_targets.groups[{index}].name must be non-empty snake-ish lowercase"
            )
        if name in seen_names:
            raise PilotRunnerError(f"Duplicate logit target group name {name!r}")
        seen_names.add(name)
        source = raw_group.get("source", "static_strings")
        if source not in {"static_strings", "row_aliases"}:
            raise PilotRunnerError(
                f"logit_targets.groups[{index}].source must be static_strings or row_aliases"
            )
        strings = raw_group.get("strings")
        if source == "static_strings":
            if not isinstance(strings, list) or not strings or not all(
                isinstance(value, str) and value for value in strings
            ):
                raise PilotRunnerError(
                    f"logit_targets.groups[{index}].strings must be a non-empty list of strings"
                )
        elif strings is not None:
            raise PilotRunnerError(
                f"logit_targets.groups[{index}].strings is only supported for static_strings"
            )
        include_variants = raw_group.get("include_leading_space_variants", False)
        if not isinstance(include_variants, bool):
            raise PilotRunnerError(
                f"logit_targets.groups[{index}].include_leading_space_variants must be boolean"
            )
        include_multi_token = raw_group.get(
            "include_multi_token_first_token",
            source == "static_strings",
        )
        if not isinstance(include_multi_token, bool):
            raise PilotRunnerError(
                f"logit_targets.groups[{index}].include_multi_token_first_token must be boolean"
            )
        if source == "row_aliases":
            resolved_group = {
                "name": name,
                "source": source,
                "strings": [],
                "include_leading_space_variants": include_variants,
                "include_multi_token_first_token": include_multi_token,
                "token_ids": [],
                "token_texts": [],
                "resolved_targets": [],
                "skipped_targets": [],
            }
            resolved.append(resolved_group)
            continue
        resolved_group = resolve_logit_target_group(
            name=name,
            strings=strings,
            include_leading_space_variants=include_variants,
            include_multi_token_first_token=include_multi_token,
            tokenizer=tokenizer,
        )
        if not resolved_group["token_ids"]:
            raise PilotRunnerError(f"logit target group {name!r} resolved to no token ids")
        resolved.append(resolved_group)
    return resolved


def resolve_row_logit_targets(
    *,
    row: dict[str, Any],
    logit_targets: list[dict[str, Any]],
    tokenizer: Any,
) -> list[dict[str, Any]]:
    resolved: list[dict[str, Any]] = []
    for group in logit_targets:
        if group.get("source") != "row_aliases":
            resolved.append(group)
            continue
        aliases = [str(alias) for alias in row.get("aliases", []) if str(alias)]
        if row.get("answer_value"):
            aliases.append(str(row["answer_value"]))
        # Unknown rows often have no correct answer alias. Keep the group absent
        # on those rows rather than forcing an empty metric bucket.
        if not aliases:
            continue
        row_group = resolve_logit_target_group(
            name=group["name"],
            strings=sorted(set(aliases)),
            include_leading_space_variants=bool(group.get("include_leading_space_variants", False)),
            include_multi_token_first_token=bool(group.get("include_multi_token_first_token", False)),
            tokenizer=tokenizer,
        )
        if not row_group["token_ids"] and not row_group["skipped_targets"]:
            continue
        row_group["source"] = "row_aliases"
        resolved.append(row_group)
    return resolved


def resolve_logit_target_group(
    *,
    name: str,
    strings: list[str],
    include_leading_space_variants: bool,
    include_multi_token_first_token: bool,
    tokenizer: Any,
) -> dict[str, Any]:
    seen_texts: set[str] = set()
    seen_token_ids: set[int] = set()
    token_ids: list[int] = []
    token_texts: list[str] = []
    resolved_targets: list[dict[str, Any]] = []
    skipped_targets: list[dict[str, Any]] = []
    for source_text in strings:
        for text in _target_string_variants(
            source_text,
            include_leading_space_variants=include_leading_space_variants,
        ):
            if text in seen_texts:
                continue
            seen_texts.add(text)
            encoded = encode_without_special_tokens(tokenizer, text)
            if not encoded:
                raise PilotRunnerError(
                    f"logit target group {name!r} string {text!r} tokenized to no ids"
                )
            if len(encoded) > 1 and not include_multi_token_first_token:
                skipped_targets.append({
                    "source_string": source_text,
                    "resolved_string": text,
                    "token_ids": [int(token_id) for token_id in encoded],
                    "skip_reason": "multi_token_target",
                })
                continue
            first_token_id = int(encoded[0])
            resolved_text = decode_single_token(tokenizer, first_token_id)
            resolved_targets.append({
                "source_string": source_text,
                "resolved_string": text,
                "first_token_id": first_token_id,
                "first_token_text": resolved_text,
                "token_ids": [int(token_id) for token_id in encoded],
                "used_first_token_only": len(encoded) > 1,
            })
            if first_token_id in seen_token_ids:
                continue
            seen_token_ids.add(first_token_id)
            token_ids.append(first_token_id)
            token_texts.append(resolved_text)
    return {
        "name": name,
        "source": "static_strings",
        "strings": strings,
        "include_leading_space_variants": include_leading_space_variants,
        "include_multi_token_first_token": include_multi_token_first_token,
        "token_ids": token_ids,
        "token_texts": token_texts,
        "resolved_targets": resolved_targets,
        "skipped_targets": skipped_targets,
    }


def _target_string_variants(
    text: str,
    *,
    include_leading_space_variants: bool,
) -> list[str]:
    variants = [text]
    if include_leading_space_variants:
        variants.append(text if text.startswith(" ") else f" {text}")
        stripped = text.lstrip()
        if stripped:
            variants.append(stripped)
    return variants


def encode_without_special_tokens(tokenizer: Any, text: str) -> list[int]:
    if hasattr(tokenizer, "encode"):
        return [int(token_id) for token_id in tokenizer.encode(text, add_special_tokens=False)]
    encoded = tokenizer(text, add_special_tokens=False)
    input_ids = encoded.get("input_ids") if isinstance(encoded, dict) else None
    if input_ids is None:
        raise PilotRunnerError("Tokenizer does not expose encode() or input_ids")
    if input_ids and isinstance(input_ids[0], list):
        input_ids = input_ids[0]
    return [int(token_id) for token_id in input_ids]


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
        target_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in arm_rows:
            target_metrics = row.get("logit_target_metrics", {})
            if not isinstance(target_metrics, dict):
                continue
            for group_name, group_metrics in target_metrics.items():
                if isinstance(group_metrics, dict):
                    target_groups[str(group_name)].append(group_metrics)
        for group_name, group_rows in sorted(target_groups.items()):
            prefix = f"{group_name}_"
            out[arm_id].update(
                {
                    f"{prefix}baseline_probability_sum_mean": _mean_float(
                        r.get("baseline_probability_sum", 0.0) for r in group_rows
                    ),
                    f"{prefix}intervention_probability_sum_mean": _mean_float(
                        r.get("intervention_probability_sum", 0.0) for r in group_rows
                    ),
                    f"{prefix}probability_sum_delta_mean": _mean_float(
                        r.get("probability_sum_delta", 0.0) for r in group_rows
                    ),
                    f"{prefix}probability_sum_delta_abs_mean": _mean_float(
                        abs(float(r.get("probability_sum_delta", 0.0)))
                        for r in group_rows
                    ),
                    f"{prefix}logit_sum_delta_mean": _mean_float(
                        r.get("logit_sum_delta", 0.0) for r in group_rows
                    ),
                }
            )
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
    control_settings = runner_control_settings(config)
    if args.mode == "logit_diagnostic":
        validate_logit_diagnostic_controls(controls)
    else:
        validate_generation_controls(controls)
    arms = build_smoke_arms(
        candidate=candidate,
        coefficients=coefficients,
        controls=controls,
        control_settings=control_settings,
    )

    extraction_dir = resolve_path(candidate["extraction_dir"])
    selection_config = config.get("selection", {})
    probe_results = selection_config.get("probe_results")
    row_keys = selection_row_keys_for_candidate(config, args.candidate)
    rows = select_balanced_rows(
        extraction_dir / "rows.jsonl",
        max_rows=args.max_rows,
        probe_results=resolve_path(probe_results) if probe_results else None,
        row_keys=row_keys,
    )
    if not rows:
        raise PilotRunnerError("No rows selected for pilot")

    direction = load_direction_tensor(candidate)
    generator = TransformersActivationGenerator(config, candidate)
    logit_targets = (
        resolve_logit_targets(config, generator.tokenizer)
        if args.mode == "logit_diagnostic"
        else []
    )
    output_root = _run_output_root(config)
    output_root.mkdir(parents=True, exist_ok=False)

    if args.mode == "logit_diagnostic":
        top_k = logit_diagnostic_top_k(config)
        return run_logit_diagnostic(
            config_path=config_path,
            config=config,
            candidate=candidate,
            coefficients=coefficients,
            controls=controls,
            control_settings=control_settings,
            arms=arms,
            rows=rows,
            direction=direction,
            generator=generator,
            logit_targets=logit_targets,
            top_k=top_k,
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
    control_settings: dict[str, Any],
    arms: list[dict[str, Any]],
    rows: list[dict[str, Any]],
    direction: Any,
    generator: TransformersActivationGenerator,
    logit_targets: list[dict[str, Any]],
    top_k: int,
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
            arm_direction = direction_for_arm(direction, arm)
            for row in rows:
                logits = generator.next_token_logits(
                    row["question"],
                    direction=arm_direction,
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
                    logit_targets=resolve_row_logit_targets(
                        row=row,
                        logit_targets=logit_targets,
                        tokenizer=generator.tokenizer,
                    ),
                    top_k=top_k,
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
        "control_settings": control_settings,
        "row_count": len(rows),
        "row_keys": [row["probe_pool_row_key"] for row in rows],
        "arm_count": len(arms),
        "top_k": top_k,
        "logit_targets": logit_targets,
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
