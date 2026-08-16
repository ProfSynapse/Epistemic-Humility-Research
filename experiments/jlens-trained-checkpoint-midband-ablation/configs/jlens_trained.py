#!/usr/bin/env python3
"""J-lens (Jacobian lens) for a TRAINED Qwen3-4B checkpoint -- READ-ONLY
interpretability characterization, adapted from
experiments/j-space-localization-qwen3-4b/jlens.py (the pinned raw-base
original, which hardcodes unsloth/Qwen3-4B and has no --model/--adapter
flags) via the precedent
experiments/qwen35-4b-midband-doubt-snap/jlens_qwen35.py (adapted-copy
pattern for a different substrate). The pinned original is untouched by
this file.

What changed vs the pinned original (everything else -- eager attention,
the JVP double-backward machinery, verbalize()/layer_profile(), the smoke
correctness check, the profile grid CLI, seed handling, corpus
build/fetch, and the output JSON schema shape -- is a byte-for-byte port):

1. Model loading (load_model): the original hardcodes MODEL_BF16 =
   "unsloth/Qwen3-4B" with no arguments. This file instead takes
   --model (the merged SFT base, a plain bf16 checkpoint dir or hub id)
   and --adapter (the GRPO-v2 LoRA adapter dir, optional) as CLI flags,
   loads the base via AutoModelForCausalLM.from_pretrained(...,
   attn_implementation="eager") exactly as the original does, then if
   --adapter is given wraps it with peft.PeftModel.from_pretrained(base,
   adapter) and calls .merge_and_unload() to fold the LoRA delta into the
   base weights and return a PLAIN bf16 Qwen3ForCausalLM graph (not a
   PeftModel wrapper) -- required because the JVP double-backward trick
   (_jvp_double_backward) needs a clean second-order autograd path through
   eager attention, and this project's other GPU runners that keep a
   PeftModel wrapper (residual_intervention_runner.py etc.) only ever
   register forward hooks on it, never differentiate through it twice.
   merge_and_unload() does not change attn_implementation or device
   placement, so the rest of the module (unembed(), which reaches
   model.model.norm / model.lm_head directly, and model.config.*) needs no
   further changes.
2. CLI: every subcommand that loads a model (smoke, profile, h1) gains
   --model (required) and --adapter (optional; omit for a raw-base-only
   run). build-corpus is untouched (CPU-only, no model load).
3. Corpus default path: DEFAULT_CORPUS_PATH now resolves under THIS
   experiment cell's own gitignored analysis/ (cell root, not this
   configs/ subdirectory the script lives in) instead of the j-space
   cell's analysis/ -- worktrees/clones do not share gitignored files
   across experiment directories, and this cell owns its own corpus copy.
4. Output JSON: each subcommand's output dict now also records
   "adapter" alongside the existing "model" key (the original's "model"
   field held the hardcoded MODEL_BF16 constant; here it holds the actual
   --model value passed, extended with --adapter for full provenance).

Corpus, staging repo, sampling method, and everything else about *why*
this design looks the way it does is documented in the original module's
own docstring (experiments/j-space-localization-qwen3-4b/jlens.py) and is
not repeated here.
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

# Private HF dataset repo the AH/AK Stage-1 question pool is staged to --
# identical source/pattern to the pinned original (see that module's
# docstring for full provenance/license notes). No question text is ever
# committed to this public repo.
STAGING_REPO = "professorsynapse/eh-al-prep-staging"
POOL_IN_REPO = "pools/ak_stage1_pool.jsonl"

# This file lives in this experiment cell's configs/ subdirectory; the
# cell's own gitignored analysis/ sits one level up, at the cell root (see
# that directory's .gitignore: `analysis/`). Corpus/results/directions
# artifacts this script writes by default all resolve under there, never
# under configs/ and never under any OTHER experiment's analysis/ tree.
CELL_DIR = Path(__file__).resolve().parents[1]
DEFAULT_CORPUS_PATH = CELL_DIR / "analysis" / "corpus_pool.jsonl"


# --------------------------------------------------------------------------
# Model loading / prompt rendering
# --------------------------------------------------------------------------

def load_model(model_path: str, adapter_path: str | None = None,
                device: str = "cuda"):
    """Load the base bf16 checkpoint + tokenizer, eager attention (double-
    backward JVP needs a second derivative through attention; fused SDPA
    kernels have no second-order backward -- same rationale as the pinned
    original). If adapter_path is given, wraps the base with the LoRA
    adapter via peft.PeftModel.from_pretrained then merges it back down to
    a plain bf16 graph via merge_and_unload() -- the JVP machinery below
    needs a clean (non-PeftModel-wrapped) forward graph. Read-only: eval
    mode, gradient tracking left ON (required for JVPs) -- no
    optimizer.step() or .grad write ever occurs."""
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(model_path)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    base = AutoModelForCausalLM.from_pretrained(
        model_path, torch_dtype=torch.bfloat16, device_map=device,
        attn_implementation="eager",
    )
    if adapter_path:
        from peft import PeftModel

        model = PeftModel.from_pretrained(base, adapter_path)
        model = model.merge_and_unload()
        # PEFT freezes base weights (requires_grad=False) and merge_and_unload
        # returns them still frozen; with every parameter frozen the forward
        # builds no autograd graph and the JVP double-backward cannot run.
        # Restore the pinned original's loaded state (all params grad-enabled;
        # still read-only -- no optimizer step or .grad write ever occurs).
        for _p in model.parameters():
            _p.requires_grad_(True)
    else:
        model = base
    model.eval()
    return model, tokenizer


def render_prompt(tokenizer, question: str) -> str:
    """Plain user-turn chat-template render, no system prompt (this module is
    a generic interpretability characterization, deliberately decoupled from
    any experiment-specific abstention/system-prompt surface) -- unchanged
    from the pinned original."""
    messages = [{"role": "user", "content": question}]
    return tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True,
        enable_thinking=False,
    )


def direction_layer_field_to_hs_index(layer_field: int) -> int:
    """Fitted-direction JSON files carry a 0-indexed decoder-block index in
    their `layer` field (== `census_block_index`). hs_index (this module's
    hidden_states-tuple index) is block_index + 1. Unchanged from the
    pinned original."""
    return int(layer_field) + 1


# --------------------------------------------------------------------------
# Core JVP machinery (byte-for-byte port of j-space-localization-qwen3-4b/jlens.py)
# --------------------------------------------------------------------------

def _jvp_double_backward(output: torch.Tensor, input_tensor: torch.Tensor,
                          tangent: torch.Tensor,
                          retain_graph: bool = True) -> torch.Tensor:
    """Jacobian-vector product output_J . tangent, computed via the standard
    forward-over-reverse double-backward trick (two VJPs). See the pinned
    original's docstring for the full derivation."""
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
    """One prompt's contribution to the corpus-averaged JVP at layer
    hs_index for a FIXED external direction, broadcast to every source
    position and averaged over positions (divide by seq_len). Returns a
    1-D float32 CPU tensor of length vocab_size."""
    out, seq_len = _forward_with_hidden_states(model, tokenizer, prompt_text, device)
    h_l = out.hidden_states[hs_index]  # (1, seq, d_model)
    final_logits = out.logits[:, -1, :]  # (1, vocab)
    tangent = direction.to(h_l.dtype).to(h_l.device).view(1, 1, -1).expand_as(h_l)
    push = _jvp_double_backward(final_logits, h_l, tangent, retain_graph=False)
    push = push.squeeze(0).detach().float().cpu() / float(seq_len)
    return push


def corpus_average_push(model, tokenizer, prompts: list[str], hs_index: int,
                         direction: torch.Tensor, device,
                         collect_per_prompt: bool = False,
                         log_every: int = 0) -> dict[str, Any]:
    """Average per_prompt_push() over a prompt corpus. If
    collect_per_prompt, also returns the raw (n_prompts, vocab) matrix
    (float32 CPU) for layer_profile's kurtosis/sparsity/effective-dim
    stats; otherwise only the running mean is kept (O(vocab) memory)."""
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


# --------------------------------------------------------------------------
# Entry point (a): verbalize
# --------------------------------------------------------------------------

def unembed(model, v: torch.Tensor) -> torch.Tensor:
    """Naive logit-lens readout: apply the model's OWN final RMSNorm then
    lm_head directly to v, treating v as if it were the final hidden state.
    No JVP / linearization -- an exact (nonlinear) evaluation. Used only as
    the correctness-smoke comparison point for verbalize() at the final
    layer, where the two should approximately agree. model.model.norm /
    model.lm_head resolve identically whether model came from a plain
    from_pretrained() or from merge_and_unload() (both are a plain
    Qwen3ForCausalLM graph)."""
    device = next(model.parameters()).device
    v = v.to(model.dtype).to(device).view(1, -1)
    with torch.no_grad():
        normed = model.model.norm(v)
        logits = model.lm_head(normed)
    return logits.squeeze(0).detach().float().cpu()


def top_k_tokens(tokenizer, scores: torch.Tensor, k: int = 10) -> list[dict]:
    vals, idx = torch.topk(scores, k)
    out = []
    for v, i in zip(vals.tolist(), idx.tolist()):
        out.append({"token_id": i, "token": tokenizer.decode([i]), "score": v})
    return out


def verbalize(model, tokenizer, prompts: list[str], hs_index: int,
              direction: torch.Tensor, device, top_k: int = 15,
              log_every: int = 0) -> dict[str, Any]:
    """verbalize(layer, direction) -> vocab distribution. direction is
    unit-normalized defensively. Returns top-k tokens by raw JVP score (the
    ranking-relevant quantity) plus a softmax-normalized distribution over
    those same top tokens for a human-readable "how peaky" read."""
    d = direction.float()
    d = d / d.norm().clamp_min(1e-8)
    agg = corpus_average_push(model, tokenizer, prompts, hs_index, d, device,
                               log_every=log_every)
    push = agg["mean_push"]
    probs = torch.softmax(push, dim=0)
    top = top_k_tokens(tokenizer, push, k=top_k)
    for t in top:
        t["softmax_prob"] = probs[t["token_id"]].item()
    return {
        "hs_index": hs_index,
        "n_prompts": agg["n_prompts"],
        "elapsed_sec": agg["elapsed_sec"],
        "top_tokens": top,
        "push_norm": push.norm().item(),
        "push_mean": push.mean().item(),
        "push_std": push.std().item(),
    }


# --------------------------------------------------------------------------
# Entry point (b): layer_profile
# --------------------------------------------------------------------------

def _excess_kurtosis(x: torch.Tensor) -> float:
    x = x.double()
    mu = x.mean()
    sd = x.std(unbiased=False).clamp_min(1e-12)
    z = (x - mu) / sd
    return float((z ** 4).mean().item() - 3.0)


def _hoyer_sparsity(x: torch.Tensor) -> float:
    """Hoyer sparsity of |x|, scale-invariant. See the pinned original's
    docstring for why this is used instead of softmax entropy."""
    x = x.double().abs()
    n = x.numel()
    l1 = x.sum().clamp_min(1e-30)
    l2 = x.norm(p=2).clamp_min(1e-30)
    root_n = math.sqrt(n)
    return float(((root_n - l1 / l2) / (root_n - 1.0)).item())


def _participation_ratio(mat: torch.Tensor) -> float:
    """Effective linear dimensionality via the participation ratio of the
    (small, n x n) Gram matrix eigenvalues. Returns a value in [1, n]."""
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
                   n_random_dirs: int = 6, seed: int = 20260707,
                   log_every: int = 0, on_layer_done=None) -> dict[str, Any]:
    """Per-layer workspace-location statistics via a fixed battery of random
    probe directions, read through the SAME corpus-averaged JVP machinery
    as verbalize() (never self-JVP -- see the pinned original's docstring
    for why). on_layer_done(hs_index, per_layer_dict_so_far), if given, is
    called after EACH layer finishes for progress-visible flushing."""
    hidden_dim = model.config.hidden_size
    directions = sample_random_directions(hidden_dim, n_random_dirs, seed)
    per_layer: dict[int, Any] = {}
    for hs_index in hs_indices:
        kurt_vals, sparse_vals, dim_vals = [], [], []
        t0 = time.time()
        for d in directions:
            agg = corpus_average_push(model, tokenizer, prompts, hs_index, d,
                                       device=next(model.parameters()).device,
                                       collect_per_prompt=True)
            mat = agg["per_prompt"]  # (n_prompts, vocab)
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
              f"eff_dim_frac={per_layer[hs_index]['effective_dim_frac_mean']:.4f}",
              flush=True)
        if on_layer_done is not None:
            on_layer_done(hs_index, per_layer)
    return {"hs_indices": hs_indices, "n_random_dirs": n_random_dirs,
            "seed": seed, "per_layer": per_layer}


# --------------------------------------------------------------------------
# Corpus loading (byte-for-byte port; only DEFAULT_CORPUS_PATH's target differs)
# --------------------------------------------------------------------------

def fetch_source_pool() -> Path:
    """Fetch the AH/AK Stage-1 question pool from the private HF staging
    repo via hf_hub_download -- identical source to the pinned original.
    Requires HF_TOKEN in the environment; huggingface_hub reads it
    automatically."""
    from huggingface_hub import hf_hub_download

    p = hf_hub_download(repo_id=STAGING_REPO, filename=POOL_IN_REPO,
                         repo_type="dataset")
    return Path(p)


def load_corpus(path: Path, n: int, seed: int = 20260707) -> list[str]:
    """Read up to n question strings, in file order, from a local corpus
    JSONL already produced by build_corpus(). Falls back to auto-building
    the corpus (fetch + deterministic re-sample) if `path` does not exist
    yet. Unchanged from the pinned original."""
    if not path.exists():
        print(f"[jlens] corpus {path} not found; building it from the "
              f"HF-staged source pool {STAGING_REPO}:{POOL_IN_REPO} "
              f"(n={n}, seed={seed})", flush=True)
        build_corpus(path, n=max(n, 1000), seed=seed)
    rows = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            q = d.get("question")
            if q:
                rows.append(q)
            if len(rows) >= n:
                break
    return rows


def build_corpus(out_path: Path, n: int, seed: int = 20260707,
                  source: Path | None = None) -> int:
    """Sample n question strings from the source JSONL pool and write them
    as a flat local JSONL this experiment cell owns (under its own
    gitignored analysis/). Deterministic given (source, n, seed) -- the
    SAME seed/n against the SAME source pool reproduces the identical
    1000-row corpus the raw-base profile used. Unchanged from the pinned
    original."""
    src_path = Path(source) if source is not None else fetch_source_pool()
    rows = []
    with src_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            q = d.get("question")
            if q:
                rows.append(q)
    rng = random.Random(seed)
    rng.shuffle(rows)
    sampled = rows[:n] if n < len(rows) else rows
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as fh:
        for q in sampled:
            fh.write(json.dumps({"question": q}) + "\n")
    return len(sampled)


def load_direction(path: Path) -> dict[str, Any]:
    d = json.loads(Path(path).read_text())
    vec = torch.tensor(d["vector"], dtype=torch.float32)
    return {"vector": vec, "layer_field": d.get("layer"),
            "hidden_dim": d.get("hidden_dim"), "raw": d}


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def _cmd_smoke(args):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, tokenizer = load_model(args.model, args.adapter, device=device)
    n_layers = model.config.num_hidden_layers
    final_hs = n_layers  # last block's output, pre-final-norm
    prompts_q = load_corpus(Path(args.corpus), args.n_prompts, seed=args.seed)
    prompts = [render_prompt(tokenizer, q) for q in prompts_q]
    print(f"[jlens/smoke] model={args.model} adapter={args.adapter} "
          f"n_layers={n_layers} final_hs_index={final_hs} "
          f"n_prompts={len(prompts)}", flush=True)

    hidden_dim = model.config.hidden_size
    test_dirs = sample_random_directions(hidden_dim, args.n_test_dirs, args.seed)

    results = []
    for i, v in enumerate(test_dirs):
        ub = unembed(model, v)
        vb = verbalize(model, tokenizer, prompts, final_hs, v, device, top_k=10)
        # verbalize() only returns summary stats + top-k, not the full push
        # vector, to keep JSON small; recompute once more here for the
        # cosine-similarity smoke report only (cheap, same corpus).
        agg = corpus_average_push(model, tokenizer, prompts, final_hs, v, device)
        push_vec = agg["mean_push"]
        cos = torch.nn.functional.cosine_similarity(
            push_vec.unsqueeze(0), ub.unsqueeze(0)).item()
        ub_top = {t["token_id"] for t in top_k_tokens(tokenizer, ub, k=10)}
        vb_top = {t["token_id"] for t in vb["top_tokens"][:10]}
        overlap10 = len(ub_top & vb_top) / 10.0
        ub_top1 = list(top_k_tokens(tokenizer, ub, k=1))[0]["token_id"]
        vb_top1 = vb["top_tokens"][0]["token_id"]
        results.append({
            "direction_idx": i, "cosine_sim": cos, "top10_overlap": overlap10,
            "top1_match": ub_top1 == vb_top1,
            "unembed_top5": [t["token"] for t in top_k_tokens(tokenizer, ub, k=5)],
            "verbalize_top5": [t["token"] for t in vb["top_tokens"][:5]],
        })
        print(f"[jlens/smoke] dir={i} cos={cos:.4f} top10_overlap={overlap10:.2f} "
              f"top1_match={ub_top1 == vb_top1}", flush=True)

    mean_cos = sum(r["cosine_sim"] for r in results) / len(results)
    mean_overlap10 = sum(r["top10_overlap"] for r in results) / len(results)
    n_top1 = sum(1 for r in results if r["top1_match"])
    out = {
        "model": args.model, "adapter": args.adapter, "n_layers": n_layers,
        "final_hs_index": final_hs, "n_prompts": len(prompts),
        "n_test_dirs": len(test_dirs), "mean_cosine_sim": mean_cos,
        "mean_top10_overlap": mean_overlap10, "n_top1_match": n_top1,
        "per_direction": results,
    }
    Path(args.out).write_text(json.dumps(out, indent=2))
    print(f"[jlens/smoke] mean_cosine_sim={mean_cos:.4f} "
          f"mean_top10_overlap={mean_overlap10:.2f} n_top1_match={n_top1}/{len(results)}",
          flush=True)
    print(f"[jlens/smoke] wrote {args.out}", flush=True)


def _cmd_profile(args):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, tokenizer = load_model(args.model, args.adapter, device=device)
    n_layers = model.config.num_hidden_layers
    prompts_q = load_corpus(Path(args.corpus), args.n_prompts, seed=args.seed)
    prompts = [render_prompt(tokenizer, q) for q in prompts_q]
    hs_indices = [int(x) for x in args.layers.split(",")]
    print(f"[jlens/profile] model={args.model} adapter={args.adapter} "
          f"n_layers={n_layers} hs_indices={hs_indices} "
          f"n_prompts={len(prompts)} n_random_dirs={args.n_random_dirs}", flush=True)
    out_path = Path(args.out)

    def _flush(hs_index, per_layer_so_far):
        partial = {"model": args.model, "adapter": args.adapter,
                   "n_layers": n_layers, "hs_indices": hs_indices,
                   "n_random_dirs": args.n_random_dirs, "seed": args.seed,
                   "status": "in_progress",
                   "layers_done": list(per_layer_so_far.keys()),
                   "per_layer": per_layer_so_far}
        out_path.write_text(json.dumps(partial, indent=2))
        print(f"[jlens/profile] flushed partial ({len(per_layer_so_far)}/"
              f"{len(hs_indices)} layers) -> {out_path}", flush=True)

    prof = layer_profile(model, tokenizer, prompts, hs_indices,
                          n_random_dirs=args.n_random_dirs, seed=args.seed,
                          on_layer_done=_flush)
    out = {"model": args.model, "adapter": args.adapter, "n_layers": n_layers,
           "status": "complete", **prof}
    out_path.write_text(json.dumps(out, indent=2))
    print(f"[jlens/profile] wrote {args.out}", flush=True)


def _cmd_h1(args):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, tokenizer = load_model(args.model, args.adapter, device=device)
    prompts_q = load_corpus(Path(args.corpus), args.n_prompts, seed=args.seed)
    prompts = [render_prompt(tokenizer, q) for q in prompts_q]

    dir_dir = Path(args.directions_dir) / "source_directions"
    named = {
        "u_d_L34 (doubt)": dir_dir / "u_d_L34.json",
        "pos_ctrl_L34 (caution / answer-vs-refuse)": dir_dir / "pos_ctrl_L34.json",
        "neg_ctrl_L34 (confab-propensity)": dir_dir / "neg_ctrl_L34.json",
        "c_hat_L34 (caution write, orthogonalized)": dir_dir / "c_hat_L34.json",
    }
    offsets = [int(x) for x in args.layer_offsets.split(",")]

    out = {"model": args.model, "adapter": args.adapter,
           "n_prompts": len(prompts), "layer_offsets_from_fit_layer": offsets,
           "status": "in_progress", "directions": {}}
    out_path = Path(args.out)
    for name, p in named.items():
        d = load_direction(p)
        fit_hs = direction_layer_field_to_hs_index(d["layer_field"])
        print(f"[jlens/h1] {name}: layer_field={d['layer_field']} "
              f"-> hs_index={fit_hs}", flush=True)
        per_layer = {}
        for off in offsets:
            hs_index = fit_hs + off
            if hs_index < 1 or hs_index > model.config.num_hidden_layers:
                continue
            vb = verbalize(model, tokenizer, prompts, hs_index, d["vector"],
                           device, top_k=args.top_k)
            per_layer[str(hs_index)] = vb
            top5 = [t["token"] for t in vb["top_tokens"][:5]]
            print(f"[jlens/h1]   hs_index={hs_index} (offset {off:+d}) "
                  f"top5={top5}", flush=True)
        out["directions"][name] = {
            "source_file": str(p), "layer_field": d["layer_field"],
            "fit_hs_index": fit_hs, "raw_provenance": d["raw"].get("provenance", {}),
            "per_layer": per_layer,
        }
        # progress-visible flush: a direction can take minutes at full
        # corpus size, so write partial results to disk as each completes
        # rather than only at the very end.
        out_path.write_text(json.dumps(out, indent=2))
        print(f"[jlens/h1] flushed partial ({len(out['directions'])}/{len(named)} "
              f"directions) -> {out_path}", flush=True)
    out["status"] = "complete"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"[jlens/h1] wrote {args.out}", flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def _common(p):
        p.add_argument("--model", required=True,
                        help="merged bf16 base checkpoint dir or hub id")
        p.add_argument("--adapter", default=None,
                        help="LoRA adapter dir to merge onto --model "
                        "(omit for a raw-base-only run)")
        p.add_argument("--corpus", default=str(DEFAULT_CORPUS_PATH))
        p.add_argument("--n-prompts", type=int, default=20)
        p.add_argument("--seed", type=int, default=20260707)
        p.add_argument("--out", required=True)

    p_build = sub.add_parser("build-corpus", help="fetch the source pool "
                              "from the private HF staging repo and sample"
                              "+write this experiment's own local prompt "
                              "corpus (CPU-only, no model load)")
    p_build.add_argument("--source", default=None,
                          help="local override path for the source pool "
                          "(testing only); default fetches "
                          f"{STAGING_REPO}:{POOL_IN_REPO} via hf_hub_download")
    p_build.add_argument("--out", default=str(DEFAULT_CORPUS_PATH))
    p_build.add_argument("--n", type=int, default=1000)
    p_build.add_argument("--seed", type=int, default=20260707)
    p_build.set_defaults(func=lambda a: print(
        f"[jlens/build-corpus] wrote "
        f"{build_corpus(Path(a.out), a.n, a.seed, source=Path(a.source) if a.source else None)} "
        f"questions -> {a.out}"))

    p_smoke = sub.add_parser("smoke", help="correctness smoke: final-layer "
                              "J-lens vs logit lens + end-to-end run check "
                              "on the trained checkpoint")
    _common(p_smoke)
    p_smoke.add_argument("--n-test-dirs", type=int, default=5)
    p_smoke.set_defaults(func=_cmd_smoke)

    p_profile = sub.add_parser("profile", help="layer_profile: locate the "
                                "workspace across depth on the trained "
                                "checkpoint")
    _common(p_profile)
    p_profile.add_argument("--layers", required=True,
                            help="comma-separated hs_index values, e.g. 4,10,16,22,28,34,36")
    p_profile.add_argument("--n-random-dirs", type=int, default=6)
    p_profile.set_defaults(func=_cmd_profile)

    p_h1 = sub.add_parser("h1", help="H1: verbalize fitted directions at "
                           "L34 and nearby layers on the trained checkpoint")
    _common(p_h1)
    p_h1.add_argument("--directions-dir", required=True,
                       help="path to an analysis-committed/-style dir with "
                       "source_directions/{u_d,pos_ctrl,neg_ctrl,c_hat}_L34.json")
    p_h1.add_argument("--layer-offsets", default="-4,-2,0,2",
                       help="hs_index offsets from each direction's own fit layer")
    p_h1.add_argument("--top-k", type=int, default=15)
    p_h1.set_defaults(func=_cmd_h1)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
