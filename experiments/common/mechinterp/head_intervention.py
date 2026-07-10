#!/usr/bin/env python3
"""During-generation per-head ITI intervention (Step A.4).

Applies the per-head steering directions built by
``head_steering_directions.py`` to a sparse set of attention heads, on
EVERY generated token, via forward PRE-hooks on each target block's
``self_attn.o_proj``. For each target head the hook adds ``alpha * sigma * theta``
to that head's slice of the o_proj input (columns ``head*head_dim:(head+1)*head_dim``)
at all token positions — the ITI update ``h' = h + alpha * sigma * theta``.

This is deliberately NOT the residual-stream, final-prompt-token intervention in
``mechinterp_causal_pilot_runner.py`` (which the regimen sweep showed is exhausted):
ITI's gains come from a sparse set of *attention heads*, steered *token-by-token
during generation*, which is what this harness does.

The injection mechanism is torch-injected and unit-tested against a tiny model
without a real LLM (see tests/test_mechinterp_head_intervention.py). Actually
generating on the GRPO v2 panel loads a 4B model on GPU and MUST be run behind an
explicit GPU gate (Docker/unsloth), exactly like the extraction step.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any


class HeadInterventionError(RuntimeError):
    pass


# ---------------------------------------------------------------------------
# Steering-direction artifact -> per-block head deltas (pure, torch-free)
# ---------------------------------------------------------------------------

def load_steering_directions(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise HeadInterventionError(f"missing steering-directions artifact: {path}")
    artifact = json.loads(path.read_text(encoding="utf-8"))
    if artifact.get("artifact_type") != "head_steering_directions":
        raise HeadInterventionError(
            f"{path} artifact_type is {artifact.get('artifact_type')!r}, "
            "expected 'head_steering_directions'"
        )
    directions = artifact.get("directions")
    if not isinstance(directions, list) or not directions:
        raise HeadInterventionError(f"{path} has no directions")
    return artifact


def build_block_deltas(directions: list[dict[str, Any]], *, alpha: float) -> dict[int, list[dict[str, Any]]]:
    """Group target heads by block, precomputing each head's delta = alpha*sigma*theta.

    Returns ``{block_id: [{head, lo, hi, delta:[float...]}, ...]}``. ``lo:hi`` are
    the o_proj-input columns for that head. The delta is a plain python list so
    this stays torch-free; the hook converts it to a tensor on the model device.
    """
    by_block: dict[int, list[dict[str, Any]]] = {}
    for entry in directions:
        layer = int(entry["layer"])
        head = int(entry["head"])
        head_dim = int(entry["head_dim"])
        theta = entry["theta"]
        sigma = float(entry["sigma"])
        if len(theta) != head_dim:
            raise HeadInterventionError(
                f"L{layer}H{head}: theta length {len(theta)} != head_dim {head_dim}"
            )
        scale = alpha * sigma
        delta = [scale * float(t) for t in theta]
        lo = head * head_dim
        hi = lo + head_dim
        by_block.setdefault(layer, []).append({"head": head, "lo": lo, "hi": hi, "delta": delta})
    return by_block


# ---------------------------------------------------------------------------
# o_proj discovery + pre-hook injection (torch injected for testability)
# ---------------------------------------------------------------------------

def discover_o_proj_modules(model: Any, *, num_hidden_layers: int) -> dict[int, Any]:
    """block id -> that block's o_proj module (PEFT-safe, name-suffix based).

    Mirrors hs_backends.TransformersPeftBackend._o_proj_modules so the
    intervention hooks the SAME modules the per-head extraction read from.
    """
    modules: dict[int, Any] = {}
    for name, module in model.named_modules():
        if not name.endswith("self_attn.o_proj"):
            continue
        match = re.search(r"layers\.(\d+)\.", name)
        if match is None:
            raise HeadInterventionError(f"o_proj module with no parseable block index: {name!r}")
        modules[int(match.group(1))] = module
    expected = set(range(num_hidden_layers))
    if set(modules) != expected:
        raise HeadInterventionError(
            f"o_proj discovery captured blocks {sorted(modules)}, expected contiguous "
            f"0..{num_hidden_layers - 1}; model attention naming is not the assumed layout"
        )
    return modules


def make_oproj_pre_hook(head_specs: list[dict[str, Any]], *, torch: Any):
    """Forward PRE-hook that adds each head's delta to the o_proj input, all positions.

    A forward_pre_hook receives ``(module, args)`` where ``args[0]`` is the
    o_proj input of shape ``[batch, seq, num_heads*head_dim]``. We add the
    per-head delta to the ``lo:hi`` slice across every batch/position and return
    the modified args so o_proj sees the steered input. The hook records how many
    times it fired (one call per forward; generation calls it once per decode
    step) for provenance.
    """
    state = {"calls": 0}

    def _hook(_module: Any, args: tuple[Any, ...]):
        x = args[0]
        steered = x.clone()
        for spec in head_specs:
            delta = torch.tensor(spec["delta"], device=steered.device, dtype=steered.dtype)
            steered[..., spec["lo"]:spec["hi"]] = steered[..., spec["lo"]:spec["hi"]] + delta
        state["calls"] += 1
        return (steered, *args[1:])

    _hook._mechinterp_state = state  # type: ignore[attr-defined]
    return _hook


@contextmanager
def per_head_intervention(model: Any, by_block: dict[int, list[dict[str, Any]]], *, torch: Any,
                          num_hidden_layers: int):
    """Register o_proj pre-hooks for every target block; remove them in finally.

    Yields the list of hook state dicts (one per hooked block) so callers can
    assert the hooks actually fired. Hooks are always removed so a raising
    generate() cannot leak handles.
    """
    modules = discover_o_proj_modules(model, num_hidden_layers=num_hidden_layers)
    handles = []
    states: list[dict[str, Any]] = []
    try:
        for block_id, head_specs in by_block.items():
            if block_id not in modules:
                raise HeadInterventionError(f"target block {block_id} not found among o_proj modules")
            hook = make_oproj_pre_hook(head_specs, torch=torch)
            handles.append(modules[block_id].register_forward_pre_hook(hook))
            states.append(hook._mechinterp_state)  # type: ignore[attr-defined]
        yield states
    finally:
        for handle in handles:
            handle.remove()


# ---------------------------------------------------------------------------
# GPU generation runner (gated) — loads the real model and sweeps alpha
# ---------------------------------------------------------------------------

def generate_steered(model: Any, tokenizer: Any, prompts: list[str], *, by_block, torch,
                     num_hidden_layers: int, max_new_tokens: int) -> tuple[list[str], list[dict[str, Any]]]:
    """Generate each prompt under the per-head intervention; return texts + hook states."""
    outputs: list[str] = []
    with per_head_intervention(model, by_block, torch=torch, num_hidden_layers=num_hidden_layers) as states:
        for prompt in prompts:
            enc = tokenizer(prompt, return_tensors="pt").to(model.device)
            with torch.no_grad():
                gen = model.generate(**enc, max_new_tokens=max_new_tokens, do_sample=False)
            text = tokenizer.decode(gen[0, enc["input_ids"].shape[1]:], skip_special_tokens=True)
            outputs.append(text)
    return outputs, states


def _load_config(path: Path) -> dict[str, Any]:
    import yaml  # local import: keep the module importable without yaml for unit tests

    with path.open(encoding="utf-8") as fh:
        payload = yaml.safe_load(fh)
    if not isinstance(payload, dict):
        raise HeadInterventionError(f"{path} did not load to a YAML object")
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    args = parser.parse_args(argv)
    # The GPU generation path (model load + sweep) is intentionally gated: this CLI
    # is a placeholder so the run command is discoverable, but the heavyweight
    # backend wiring lands with the explicit GPU gate. Unit tests exercise the
    # injection mechanism directly without this entry point.
    raise HeadInterventionError(
        "mechinterp_head_intervention GPU runner is gated; invoke the injection API "
        "(per_head_intervention / generate_steered) from the gated Docker harness. "
        f"config={args.config}"
    )


if __name__ == "__main__":
    raise SystemExit(main())
