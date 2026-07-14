#!/usr/bin/env python3
"""J-lens (Jacobian lens) layer profile on Qwen/Qwen3.5-4B -- READ-ONLY
interpretability characterization, adapted from
experiments/j-space-localization-qwen3-4b/jlens.py for this model's
multimodal-wrapper loader. No writes/injections to activations anywhere in
this file; every function only READS the model's forward computation graph
via directional derivatives (JVPs). See that module's docstring for the full
mathematical derivation (verbalize/layer_profile, corpus-averaged JVP,
kurtosis/Hoyer-sparsity/participation-ratio reductions) -- this file only
changes model loading and layer-index range, the core JVP math
(per_prompt_push / corpus_average_push / layer_profile / _excess_kurtosis /
_hoyer_sparsity / _participation_ratio / sample_random_directions) is a
byte-for-byte port.

Loader note (pre-registered design requirement): Qwen/Qwen3.5-4B's config is
`Qwen3_5Config` with a NESTED `text_config` (`Qwen3_5TextConfig`,
num_hidden_layers=32, hidden_size=2560) and its architecture is
`Qwen3_5ForConditionalGeneration`. `AutoModelForCausalLM.from_config(...)`
fails on this nested shape. `AutoModelForCausalLM.from_pretrained(...)`,
however, resolves correctly (this transformers version, 5.5.0, maps
`qwen3_5` in MODEL_FOR_CAUSAL_LM_MAPPING_NAMES) -- confirmed empirically
before writing this file and consistent with
`experiment/phase1/probe/amendment_x_cross_model_extract.py`'s own
Gemma-4/Qwen-3.5 loader note and with `synaptic-tuner/MechInterp/cli.py`'s
plain `AutoModelForCausalLM.from_pretrained` call, which already succeeded
loading this exact model+revision for the (separate, unmerged)
doubt-snap-cross-family-confirmatory cross-family run. So this file loads via
`from_pretrained` directly; no ImageTextToText/Vision2Seq fallback is needed
for THIS specific model (kept as a documented fact, not a defensive branch,
to avoid an untested code path).

Corpus: this experiment's own reused FIT question text
(`analysis/fit_rows_for_anchor.jsonl`, 1,308 rows -- see
materialize_reused_rows.py), NOT a separately-fetched pool. A fixed-seed
subsample keeps the profile affordable; the full FIT set is reserved for
Stage B anchor extraction / direction fitting.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import time
from pathlib import Path
from typing import Any

import torch

MODEL_NAME = "Qwen/Qwen3.5-4B"
MODEL_REVISION = "851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a"

HERE = Path(__file__).resolve().parent
DEFAULT_FIT_ROWS = HERE / "analysis" / "fit_rows_for_anchor.jsonl"
DEFAULT_CORPUS_OUT = HERE / "analysis" / "jlens_corpus_questions.jsonl"

# Late 0.94-depth write site (registered layer rule from
# doubt-snap-cross-family-confirmatory: round(0.94 * (num_hidden_layers - 1))
# as a 0-indexed decoder block -> hs_index = block_index + 1). For Qwen3.5-4B
# (32 layers): round(0.94 * 31) = 29 -> hs_index 30. Included in the profile
# grid as the within-run comparator, per design.
LATE_SITE_BLOCK_INDEX = 29
LATE_SITE_HS_INDEX = LATE_SITE_BLOCK_INDEX + 1  # 30


# --------------------------------------------------------------------------
# Model loading / prompt rendering
# --------------------------------------------------------------------------

def load_model(device: str = "cuda"):
    """Load the bf16 model + tokenizer, eager attention (double-backward JVP
    needs a second derivative through attention; fused SDPA kernels have no
    second-order backward -- same rationale as the Qwen3-4B jlens.py)."""
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_NAME, revision=MODEL_REVISION, trust_remote_code=True,
    )
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME, revision=MODEL_REVISION, torch_dtype=torch.bfloat16,
        device_map=device, attn_implementation="eager",
        trust_remote_code=True,
    )
    model.eval()
    return model, tokenizer


def text_config(model):
    return getattr(model.config, "text_config", model.config)


def render_prompt(tokenizer, question: str) -> str:
    """Plain user-turn chat-template render, no system prompt -- matches the
    Qwen3-4B jlens.py's generic interpretability convention. (Anchor
    extraction in Stage B uses the doubt-snap baseline system prompt instead,
    for comparability with the reused rows' frozen anchor position; the
    layer-LOCATION profile here does not need that specific prompt surface.)"""
    messages = [{"role": "user", "content": question}]
    return tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True,
        enable_thinking=False,
    )


# --------------------------------------------------------------------------
# Core JVP machinery (byte-for-byte port of j-space-localization-qwen3-4b/jlens.py)
# --------------------------------------------------------------------------

def _jvp_double_backward(output: torch.Tensor, input_tensor: torch.Tensor,
                          tangent: torch.Tensor,
                          retain_graph: bool = True) -> torch.Tensor:
    u = torch.zeros_like(output, requires_grad=True)
    (vjp,) = torch.autograd.grad(
        output, input_tensor, grad_outputs=u, create_graph=True,
        retain_graph=True,
    )
    inner = (vjp * tangent).sum()
    (jvp,) = torch.autograd.grad(inner, u, retain_graph=retain_graph)
    return jvp


def _forward_with_hidden_states(model, tokenizer, prompt_text: str, device):
    enc = tokenizer(prompt_text, return_tensors="pt").to(device)
    out = model(**enc, output_hidden_states=True, use_cache=False)
    seq_len = enc["input_ids"].shape[1]
    return out, seq_len


def per_prompt_push(model, tokenizer, prompt_text: str, hs_index: int,
                     direction: torch.Tensor, device) -> torch.Tensor:
    out, seq_len = _forward_with_hidden_states(model, tokenizer, prompt_text, device)
    h_l = out.hidden_states[hs_index]
    final_logits = out.logits[:, -1, :]
    tangent = direction.to(h_l.dtype).to(h_l.device).view(1, 1, -1).expand_as(h_l)
    push = _jvp_double_backward(final_logits, h_l, tangent, retain_graph=False)
    push = push.squeeze(0).detach().float().cpu() / float(seq_len)
    return push


def corpus_average_push(model, tokenizer, prompts: list[str], hs_index: int,
                         direction: torch.Tensor, device,
                         collect_per_prompt: bool = False,
                         log_every: int = 0) -> dict[str, Any]:
    total = None
    per_prompt = [] if collect_per_prompt else None
    t0 = time.time()
    for i, p in enumerate(prompts):
        push = per_prompt_push(model, tokenizer, p, hs_index, direction, device)
        total = push.clone() if total is None else total + push
        if collect_per_prompt:
            per_prompt.append(push)
        if log_every and (i + 1) % log_every == 0:
            print(f"[jlens] corpus_average_push hs_index={hs_index} "
                  f"{i + 1}/{len(prompts)} ({time.time() - t0:.1f}s)", flush=True)
    mean_push = total / float(len(prompts))
    result = {"mean_push": mean_push, "n_prompts": len(prompts),
              "elapsed_sec": time.time() - t0}
    if collect_per_prompt:
        result["per_prompt"] = torch.stack(per_prompt, dim=0)
    return result


def _excess_kurtosis(x: torch.Tensor) -> float:
    x = x.double()
    mu = x.mean()
    sd = x.std(unbiased=False).clamp_min(1e-12)
    z = (x - mu) / sd
    return float((z ** 4).mean().item() - 3.0)


def _hoyer_sparsity(x: torch.Tensor) -> float:
    x = x.double().abs()
    n = x.numel()
    l1 = x.sum().clamp_min(1e-30)
    l2 = x.norm(p=2).clamp_min(1e-30)
    root_n = math.sqrt(n)
    return float(((root_n - l1 / l2) / (root_n - 1.0)).item())


def _participation_ratio(mat: torch.Tensor) -> float:
    x = mat.double()
    x = x - x.mean(dim=0, keepdim=True)
    n = x.shape[0]
    gram = (x @ x.T) / max(n - 1, 1)
    eigvals = torch.linalg.eigvalsh(gram).clamp_min(0.0)
    s1 = eigvals.sum()
    s2 = (eigvals ** 2).sum()
    if s2 <= 1e-30:
        return 1.0
    return float((s1 * s1 / s2).item())


def sample_random_directions(hidden_dim: int, n: int, seed: int) -> list[torch.Tensor]:
    g = torch.Generator().manual_seed(seed)
    dirs = []
    for _ in range(n):
        v = torch.randn(hidden_dim, generator=g)
        v = v / v.norm().clamp_min(1e-8)
        dirs.append(v)
    return dirs


def layer_profile(model, tokenizer, prompts: list[str], hs_indices: list[int],
                   n_random_dirs: int = 5, seed: int = 20260707,
                   log_every: int = 0, on_layer_done=None) -> dict[str, Any]:
    hidden_dim = text_config(model).hidden_size
    directions = sample_random_directions(hidden_dim, n_random_dirs, seed)
    per_layer: dict[int, Any] = {}
    for hs_index in hs_indices:
        kurt_vals, sparse_vals, dim_vals = [], [], []
        t0 = time.time()
        for d in directions:
            agg = corpus_average_push(model, tokenizer, prompts, hs_index, d,
                                       device=next(model.parameters()).device,
                                       collect_per_prompt=True, log_every=log_every)
            mat = agg["per_prompt"]
            kurt_vals.append(sum(_excess_kurtosis(mat[i]) for i in range(mat.shape[0]))
                              / mat.shape[0])
            sparse_vals.append(sum(_hoyer_sparsity(mat[i]) for i in range(mat.shape[0]))
                                / mat.shape[0])
            dim_vals.append(_participation_ratio(mat) / mat.shape[0])

        def _mean(v):
            return sum(v) / len(v)

        def _std(v):
            m = _mean(v)
            return math.sqrt(sum((x - m) ** 2 for x in v) / max(len(v) - 1, 1))

        per_layer[hs_index] = {
            "excess_kurtosis_mean": _mean(kurt_vals),
            "excess_kurtosis_std": _std(kurt_vals),
            "sparsity_mean": _mean(sparse_vals),
            "sparsity_std": _std(sparse_vals),
            "effective_dim_frac_mean": _mean(dim_vals),
            "effective_dim_frac_std": _std(dim_vals),
            "n_random_dirs": n_random_dirs,
            "n_prompts": len(prompts),
            "elapsed_sec": time.time() - t0,
        }
        print(f"[jlens] layer_profile hs_index={hs_index} done "
              f"({time.time() - t0:.1f}s): "
              f"kurt={per_layer[hs_index]['excess_kurtosis_mean']:.3f} "
              f"sparsity={per_layer[hs_index]['sparsity_mean']:.4f} "
              f"eff_dim_frac={per_layer[hs_index]['effective_dim_frac_mean']:.5f}",
              flush=True)
        if on_layer_done is not None:
            on_layer_done(hs_index, per_layer)
    return {"hs_indices": hs_indices, "n_random_dirs": n_random_dirs,
            "seed": seed, "per_layer": per_layer}


# --------------------------------------------------------------------------
# Corpus (this experiment's reused FIT rows, not a separate fetch)
# --------------------------------------------------------------------------

def load_corpus(fit_rows_path: Path, n: int, seed: int) -> list[str]:
    rows = []
    with fit_rows_path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    rng = random.Random(seed)
    rng.shuffle(rows)
    sampled = rows[:n] if n < len(rows) else rows
    return [r["question"] for r in sampled]


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def _cmd_profile(args):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, tokenizer = load_model(device=device)
    n_layers = int(text_config(model).num_hidden_layers)
    questions = load_corpus(Path(args.fit_rows), args.n_prompts, args.seed)
    prompts = [render_prompt(tokenizer, q) for q in questions]
    hs_indices = [int(x) for x in args.layers.split(",")]
    print(f"[jlens/profile] model={MODEL_NAME}@{MODEL_REVISION} n_layers={n_layers} "
          f"hs_indices={hs_indices} n_prompts={len(prompts)} "
          f"n_random_dirs={args.n_random_dirs}", flush=True)
    out_path = Path(args.out)

    def _flush(hs_index, per_layer_so_far):
        partial = {"model": MODEL_NAME, "revision": MODEL_REVISION,
                   "n_layers": n_layers, "hs_indices": hs_indices,
                   "n_random_dirs": args.n_random_dirs, "seed": args.seed,
                   "status": "in_progress",
                   "layers_done": list(per_layer_so_far.keys()),
                   "late_site_hs_index": LATE_SITE_HS_INDEX,
                   "per_layer": per_layer_so_far}
        out_path.write_text(json.dumps(partial, indent=2), encoding="utf-8")
        print(f"[jlens/profile] flushed partial ({len(per_layer_so_far)}/"
              f"{len(hs_indices)} layers) -> {out_path}", flush=True)

    prof = layer_profile(model, tokenizer, prompts, hs_indices,
                          n_random_dirs=args.n_random_dirs, seed=args.seed,
                          log_every=args.log_every, on_layer_done=_flush)
    out = {"model": MODEL_NAME, "revision": MODEL_REVISION, "n_layers": n_layers,
           "late_site_hs_index": LATE_SITE_HS_INDEX, "status": "complete", **prof}
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"[jlens/profile] wrote {args.out}", flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_profile = sub.add_parser("profile", help="layer_profile: locate the "
                                "workspace-like band across depth")
    p_profile.add_argument("--fit-rows", default=str(DEFAULT_FIT_ROWS))
    p_profile.add_argument("--n-prompts", type=int, default=40)
    p_profile.add_argument("--seed", type=int, default=20260707)
    p_profile.add_argument("--layers", required=True,
                            help="comma-separated hs_index values")
    p_profile.add_argument("--n-random-dirs", type=int, default=5)
    p_profile.add_argument("--log-every", type=int, default=0)
    p_profile.add_argument("--out", required=True)
    p_profile.set_defaults(func=_cmd_profile)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
