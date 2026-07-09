"""Family-aware model/hook/loader machinery for the cross-family J-space
layer contrast.

Ported from `j-space-midband-write-sweep-qwen3-4b/model_lib.py` (the
Qwen3-4B-only predecessor), generalized to read checkpoint/loader/render/EOS
facts from a family config (`family_config.py`) instead of hardcoding
`unsloth/Qwen3-4B` and a Qwen-only `<|im_end|>` lookup. The loader hardening
(model-class fallback chain, `config.text_config` nesting for multimodal
families) is ported from `experiment/phase1/probe/amendment_x_cross_model_extract.py`
`load_model_and_config()`, as pointed to by
`experiment/protocol/AMENDMENT-Z-cross-family-confirmatory.md` "Loader
hardening (this amendment)".

Uses the tuner's own `InterventionHook` / `GenerationInterventionController`
unmodified. Does NOT modify synaptic-tuner.

FIXED absolute-realized-projection dosing: given a target realized readback T
(the SNAP setpoint s*), the commanded gain is strength = T / sigma_c, since
the tuner's erase_write law writes setpoint = gain * sigma exactly
(synaptic-tuner MechInterp/intervention/hooks.py:erase_and_write) and
hook.last_readback confirms the realized value at run time (never assumed).
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Any

import torch

HERE = Path(__file__).resolve().parent  # experiment dir
REPO_ROOT = HERE.parents[1]
TUNER_DIR = REPO_ROOT / "synaptic-tuner"
PROBE_DIR = Path("/home/profsynapse/code/Epistemic-Humility-Research/experiment/phase1/probe")

for p in (str(TUNER_DIR), str(PROBE_DIR), str(HERE)):
    if p not in sys.path:
        sys.path.insert(0, p)

from MechInterp.intervention import (  # noqa: E402
    InterventionHook,
    GenerationInterventionController,
    get_decoder_layer,
)
from MechInterp.probe import load_frozen_direction  # noqa: E402

from family_config import load_family  # noqa: E402


def load_jsonl(p: Path) -> list[dict]:
    import json

    return [json.loads(ln) for ln in p.open(encoding="utf-8") if ln.strip()]


def _resolve_dtype(dtype_name: str):
    return {"bf16": torch.bfloat16, "fp16": torch.float16, "fp32": torch.float32}[dtype_name]


def load_model_and_tokenizer(family: str):
    """Load a family's raw-base checkpoint via the Amendment Z loader
    hardening: try AutoModelForCausalLM first, then fall back to
    AutoModelForImageTextToText / AutoModelForVision2Seq for multimodal
    families named in that family's `loader.model_classes`. Returns
    (model, tokenizer, hidden_size, num_hidden_layers).

    Loading Qwen3.5-4B / Gemma-4-E4B on THIS path is unverified: it is
    ported from Amendment Z's own extraction script, not re-tested here
    (no GPU work in this draft). A load failure on a multimodal family is a
    G0 loader blocker, recorded as INELIGIBLE per Amendment Z's own
    disposition -- not silently worked around.
    """
    cfg = load_family(family)
    repo = cfg["checkpoint"]["repo"]
    dtype = _resolve_dtype(cfg["loader"]["dtype"])

    import transformers as tf
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(repo)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    major = int(tf.__version__.split(".")[0])
    dtype_kw = "dtype" if major >= 5 else "torch_dtype"
    load_kw = {dtype_kw: dtype, "device_map": "auto"}

    model = None
    last_err: Exception | None = None
    tried: list[str] = []
    for cls_name in cfg["loader"]["model_classes"]:
        if not hasattr(tf, cls_name):
            continue
        tried.append(cls_name)
        try:
            cls = getattr(tf, cls_name)
            model = cls.from_pretrained(repo, **load_kw)
            break
        except Exception as exc:  # noqa: BLE001 -- loader fallback chain, logged not swallowed
            last_err = exc
            continue
    if model is None:
        raise RuntimeError(
            f"[{family}] could not load {repo} via any of {tried}: {last_err}"
        )
    model.eval()

    text_cfg = model.config
    if cfg["loader"].get("nested_text_config") and hasattr(model.config, "text_config"):
        text_cfg = model.config.text_config
    hidden_size = getattr(text_cfg, cfg["loader"]["hidden_size_field"])
    num_hidden_layers = getattr(text_cfg, cfg["loader"]["num_layers_field"])

    return model, tokenizer, hidden_size, num_hidden_layers


def render(family: str, tokenizer, row: dict) -> str:
    """Render one row's question via this family's chat template contract.
    `render.fn` in the family config names a `module:callable` pair,
    resolved with `importlib` exactly like the mechinterp-cells skill's
    render-fn convention (see .skills/mechinterp-cells/SKILL.md "Plug-in
    points"). Every family currently points at the same
    `backends:render_probe_prompt` (already model-agnostic via
    tokenizer.apply_chat_template); a family whose template needs a
    different call shape can point at its own module without touching this
    function."""
    cfg = load_family(family)
    module_name, func_name = cfg["render"]["fn"].split(":")
    module = importlib.import_module(module_name)
    render_probe_prompt = getattr(module, func_name)
    from amendment_ah_stage0_extract import load_baseline_system_prompt

    system_prompt = load_baseline_system_prompt()
    rendered, _mode = render_probe_prompt(
        tokenizer, system_prompt, row["question"], enable_thinking=False
    )
    return rendered


def resolve_eos_ids(family: str, tokenizer) -> list[int]:
    """Family-aware EOS resolution. Ported from the predecessor's
    Qwen-only `resolve_eos_ids` (which hardcoded `<|im_end|>`), generalized
    to read each family's own end-of-turn token strings from its config
    (`eos.additional_end_of_turn_tokens`) instead of assuming Qwen's
    convention transfers."""
    cfg = load_family(family)
    ids: set[int] = set()
    if cfg["eos"].get("include_tokenizer_eos", True) and tokenizer.eos_token_id is not None:
        ids.add(int(tokenizer.eos_token_id))
    for tok_str in cfg["eos"].get("additional_end_of_turn_tokens", []):
        tok_id = tokenizer.convert_tokens_to_ids(tok_str)
        if tok_id is not None and tok_id != getattr(tokenizer, "unk_token_id", None):
            ids.add(int(tok_id))
    return sorted(ids)


def setup_hook_from_path(direction_path: Path):
    direction_record = load_frozen_direction(str(direction_path))
    direction = torch.tensor(direction_record["vector_np"], dtype=torch.float32)
    sigma = float(direction_record.get("sigma", 1.0))
    layer_idx = int(direction_record["layer"])
    hook = InterventionHook(
        law="erase_write", direction=direction, sigma=sigma,
        position="anchor_onward", measure_readback=True,
    )
    controller = GenerationInterventionController(hook)
    return hook, controller, layer_idx, sigma, direction_record


def setup_hook_from_vector(vector, sigma: float, layer_idx: int):
    """Same as setup_hook_from_path but takes a raw (possibly random)
    direction vector directly."""
    direction = torch.tensor(vector, dtype=torch.float32)
    hook = InterventionHook(
        law="erase_write", direction=direction, sigma=sigma,
        position="anchor_onward", measure_readback=True,
    )
    controller = GenerationInterventionController(hook)
    return hook, controller, layer_idx, sigma


def decoder_layer_module(model, layer_idx: int):
    return get_decoder_layer(model, layer_idx)


def wilson_ci(successes: int, n: int, z: float = 1.959963984540054) -> tuple[float, float, float]:
    """Wilson score 95% CI for a binomial proportion. Returns (point, lo, hi)."""
    if n == 0:
        return 0.0, 0.0, 0.0
    phat = successes / n
    denom = 1 + z * z / n
    center = (phat + z * z / (2 * n)) / denom
    half = (z * ((phat * (1 - phat) / n + z * z / (4 * n * n)) ** 0.5)) / denom
    return phat, max(0.0, center - half), min(1.0, center + half)
