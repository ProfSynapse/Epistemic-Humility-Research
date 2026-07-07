#!/usr/bin/env python3
"""J-lens (Jacobian lens) for Qwen3-4B -- READ-ONLY interpretability
characterization. No writes/injections to activations anywhere in this file;
every function here only READS the model's forward computation graph to take
directional derivatives. This is generic interpretability code, deliberately
kept out of synaptic-tuner so it can be promoted there later via its own PR.

Definition (from the source paper, library/notes/tc-2026-workspace--
verbalizable-representations-global-workspace.md, and this repo's own
docs/ideas/j-space-global-workspace-actuation-bridge.md), OPERATIONALIZED per
the task's simplified formula (final-token logits only, not the paper's full
multi-downstream-position average):

    J_l = E_{t, prompt} [ d(final_token_logits) / d(h_{l,t}) ]

lens(h_l) = softmax(W_U * norm(J_l * h_l))   (paper's full lens; see unembed())

verbalize(layer, direction) computes the corpus-averaged JVP (Jacobian-vector
product) of the final-token logits with respect to h_l, applied to a FIXED
external direction, broadcast identically to every source position within
each prompt and averaged over positions and over the prompt corpus. This
never materializes J_l as an explicit (vocab_size x hidden_dim) matrix -- by
linearity, mean_i(J_i . v) == (mean_i J_i) . v, so summing per-prompt local
Jacobian-vector products IS the corpus average, at the cost of one JVP
(one forward + a double-backward trick, see _jvp_double_backward) per prompt
per layer, never a full Jacobian.

layer_profile() locates the workspace across depth using the SAME per-prompt
JVP machinery applied to a small FIXED battery of random probe directions
(not to each prompt's own activation -- see the module docstring section
"Why layer_profile uses random probes, not self-JVP" below for the reason).

Layer-index convention: this module always indexes layers via `hs_index`,
the index into HF's `output_hidden_states` tuple: hs_index=0 is the embedding
output (pre-block-0), hs_index=i is the output of transformer block i
(1-indexed blocks), so hs_index in [1, num_hidden_layers] and hs_index ==
num_hidden_layers is the LAST block's output (pre-final-norm) -- the
"final layer" the correctness smoke checks against the logit lens. This
matches this project's own "L34" direction-file naming convention exactly:
the fitted directions under analysis-committed/source_directions/ carry a
JSON field `"layer": 33` (0-indexed decoder-block index, i.e.
`census_block_index: 33` in their own provenance block) for what they name
"L34"; census/file convention is 1-indexed hs_index = block_index + 1 = 34.
Use direction_layer_field_to_hs_index() to make this conversion explicit
everywhere in this file rather than repeating "+1" inline.

Why layer_profile uses random probes, not self-JVP:
    A tempting cheap design for "does this layer's OWN activation verbalize
    something coherent" is a self-referential JVP: base point = h_l (from an
    actual forward pass) and tangent = h_l itself (or its unit-normalized
    version). This is degenerate at (and increasingly near) the FINAL layer:
    RMSNorm is scale-invariant (norm(k*x) == norm(x) for any k>0), i.e.
    degree-0 homogeneous, so by Euler's homogeneous-function theorem its
    directional derivative in the direction of its OWN input is exactly
    zero: J_norm(x) . x == 0. Since the final layer's "rest of network" is
    just norm + lm_head, a self-referential JVP there is identically zero --
    a pure math artifact, not a workspace signal. layer_profile() therefore
    reads out each layer with a small FIXED set of random unit directions
    (never aligned with any specific instance's activation), corpus-averaged
    exactly like verbalize(), and aggregates kurtosis / sparsity / effective-
    dimensionality of the resulting per-prompt push vectors. This is a
    faithful, cheap proxy for "is this layer's J-lens operator peaky /
    concentrated (workspace-like) or flat / noisy", without the degeneracy.

Cross-quantization substrate caveat (read before interpreting H1 results):
our fitted directions (u_d, pos_ctrl, neg_ctrl, c_hat) were computed on
bnb-4bit activations (unsloth/Qwen3-4B-bnb-4bit); this module runs the J-lens
on the UNQUANTIZED bf16 sibling (unsloth/Qwen3-4B) because autograd/JVPs do
not work cleanly through bnb-4bit quantized weights. Passing a bnb-4bit-
fitted direction through a bf16 J-lens is an approximate cross-quantization
check, not an exact same-substrate readout. Report it as such.
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

MODEL_BF16 = "unsloth/Qwen3-4B"  # bf16 sibling of the bnb-4bit raw-base
MODEL_BNB4BIT_RAW_BASE = "unsloth/Qwen3-4B-bnb-4bit"  # for provenance notes only

THIS_DIR = Path(__file__).resolve().parent
# Local, gitignored (analysis/) copy this experiment builds for itself via
# the `build-corpus` subcommand -- decouples smoke/profile/h1 runs from
# needing to know about any OTHER experiment's on-disk analysis/ tree
# (worktrees do not share gitignored files with each other or with a fresh
# Modal clone). See build-corpus / NOTEBOOK.md for the source pool choice.
DEFAULT_CORPUS_PATH = THIS_DIR / "analysis" / "corpus_pool.jsonl"
# Fallback source pool on the CANONICAL checkout (not this worktree, and not
# present in a fresh git clone -- analysis/ is gitignored repo-wide). Used
# only as build-corpus's own default --source.
DEFAULT_SOURCE_POOL = (
    "/home/profsynapse/code/Epistemic-Humility-Research/"
    "experiment/phase1/probe/analysis/ak_stage1/ak_stage1_pool.jsonl"
)


# --------------------------------------------------------------------------
# Model loading / prompt rendering
# --------------------------------------------------------------------------

def load_model(model_name: str = MODEL_BF16, device: str = "cuda"):
    """Load the bf16 model + tokenizer. Read-only: eval mode, but gradient
    tracking is left ON (required for JVPs) -- we simply never call
    optimizer.step() or touch any parameter's .grad, so no write occurs."""
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    # attn_implementation="eager": the double-backward JVP trick
    # (_jvp_double_backward) needs a second derivative through attention for
    # any layer that isn't the very last block. PyTorch's fused
    # scaled_dot_product_attention backward kernels (flash / memory-
    # efficient) have NO second-order derivative implemented
    # (RuntimeError: derivative for
    # aten::_scaled_dot_product_flash_attention_backward is not implemented,
    # confirmed empirically on this stack: torch 2.9.1+cu128, transformers
    # 4.57.1). Eager attention (plain matmul+softmax) supports double
    # backward via standard autograd, at a real but affordable speed/memory
    # cost for a 4B model's short prompts.
    model = AutoModelForCausalLM.from_pretrained(
        model_name, torch_dtype=torch.bfloat16, device_map=device,
        attn_implementation="eager",
    )
    model.eval()
    return model, tokenizer


def render_prompt(tokenizer, question: str) -> str:
    """Plain user-turn chat-template render, no system prompt (this module is
    a generic interpretability characterization, deliberately decoupled from
    any experiment-specific abstention/system-prompt surface)."""
    messages = [{"role": "user", "content": question}]
    return tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True,
        enable_thinking=False,
    )


def direction_layer_field_to_hs_index(layer_field: int) -> int:
    """Fitted-direction JSON files carry a 0-indexed decoder-block index in
    their `layer` field (== `census_block_index`). hs_index (this module's
    hidden_states-tuple index) is block_index + 1."""
    return int(layer_field) + 1


# --------------------------------------------------------------------------
# Core JVP machinery
# --------------------------------------------------------------------------

def _jvp_double_backward(output: torch.Tensor, input_tensor: torch.Tensor,
                          tangent: torch.Tensor,
                          retain_graph: bool = True) -> torch.Tensor:
    """Jacobian-vector product output_J . tangent, computed via the standard
    forward-over-reverse double-backward trick (two VJPs), since PyTorch's
    HF forward pass does not support forward-mode AD cleanly end to end.

    output: tensor depending on input_tensor via autograd (e.g. final-token
        logits). input_tensor: an intermediate, non-leaf activation from the
        SAME forward pass (e.g. a captured hidden_states[l] tensor).
        tangent: same shape as input_tensor -- the direction to differentiate
        along. Returns a tensor the same shape as `output`.

    Trick: let u be a dummy same-shape-as-output tensor with requires_grad.
        vjp = d/d(input_tensor) [ sum(u * output) ]   (= u^T J, linear in u)
        jvp = d/du [ sum(vjp * tangent) ]             (= J . tangent)
    Both steps use create_graph=True on the first grad so the second grad
    can differentiate through it. Purely a read of the existing forward
    graph -- no parameter or activation is ever modified.
    """
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
    layer, where the two should approximately agree (see module docstring)."""
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
    """Hoyer sparsity of |x|: (sqrt(n) - L1/L2) / (sqrt(n) - 1), in [0, 1],
    0 == mass spread evenly over all n entries, 1 == mass on a single
    entry. Deliberately NOT computed via softmax: softmax's entropy
    conflates the push vector's raw MAGNITUDE (which is small and
    incidental -- these are linearized deltas for a unit-norm input
    direction, not calibrated logits) with its SHAPE/concentration, so a
    small-magnitude but genuinely peaked vector would misleadingly read as
    "near-uniform, high entropy" after softmax. Hoyer sparsity on |x|
    directly is scale-invariant (unaffected by multiplying x by any
    positive constant), which is what a workspace-location metric needs. A
    simplified, unnormalized proxy for the paper's own sparse
    (gradient-pursuit, k=25) J-space decomposition -- not a re-
    implementation of that method."""
    x = x.double().abs()
    n = x.numel()
    l1 = x.sum().clamp_min(1e-30)
    l2 = x.norm(p=2).clamp_min(1e-30)
    root_n = math.sqrt(n)
    return float(((root_n - l1 / l2) / (root_n - 1.0)).item())


def _participation_ratio(mat: torch.Tensor) -> float:
    """Effective linear dimensionality of an (n, d) matrix via the
    participation ratio of the eigenvalues of its (small, n x n) Gram
    matrix -- shares nonzero eigenvalues with the (d, d) covariance, so this
    avoids ever forming a (vocab, vocab) matrix. Returns a value in
    [1, n]."""
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
    """Per-layer workspace-location statistics, computed via a fixed battery
    of random probe directions read through the SAME corpus-averaged JVP
    machinery as verbalize() (see module docstring for why NOT self-JVP).
    For each (layer, direction) pair, collects the (n_prompts, vocab)
    per-prompt push matrix and reduces it to kurtosis / sparsity (Hoyer,
    scale-invariant) / effective linear dimensionality, then averages those
    reductions across the random-direction battery. on_layer_done(hs_index,
    per_layer_dict_so_far), if given, is called after EACH layer finishes --
    a progress-visible flush hook for long (Modal-scale) runs, so partial
    results are on disk without waiting for the full depth sweep."""
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
# Corpus loading
# --------------------------------------------------------------------------

def load_corpus(path: Path, n: int, seed: int = 20260707) -> list[str]:
    """Read up to n question strings, in file order, from a local corpus
    JSONL already produced by build_corpus() (a flat {"question": ...} per
    line file that was itself randomly sampled once at build time -- so
    taking a PREFIX here is a deterministic, order-preserving sub-sample,
    letting a small --n-prompts smoke run and a large full run share the
    same leading rows). `seed` is accepted for CLI symmetry with
    build-corpus but unused here (the file's own row order already encodes
    the one random shuffle). Falls back to auto-building the corpus from
    DEFAULT_SOURCE_POOL if `path` does not exist yet (first-run
    convenience; see build-corpus for the documented default pool choice)."""
    if not path.exists():
        print(f"[jlens] corpus {path} not found; building it from "
              f"{DEFAULT_SOURCE_POOL} (n={n}, seed={seed})", flush=True)
        build_corpus(Path(DEFAULT_SOURCE_POOL), path, n=max(n, 1000), seed=seed)
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


def build_corpus(source: Path, out_path: Path, n: int, seed: int = 20260707) -> int:
    """Sample n question strings from a source JSONL pool (any row with a
    `question` field) and write them as a flat local JSONL
    ({"question": ...} per line) this experiment owns (under its own
    gitignored analysis/). Deterministic given (source, n, seed)."""
    rows = []
    with Path(source).open("r", encoding="utf-8") as fh:
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
    model, tokenizer = load_model(device=device)
    n_layers = model.config.num_hidden_layers
    final_hs = n_layers  # last block's output, pre-final-norm
    prompts_q = load_corpus(Path(args.corpus), args.n_prompts, seed=args.seed)
    prompts = [render_prompt(tokenizer, q) for q in prompts_q]
    print(f"[jlens/smoke] model={MODEL_BF16} n_layers={n_layers} "
          f"final_hs_index={final_hs} n_prompts={len(prompts)}", flush=True)

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
        "model": MODEL_BF16, "n_layers": n_layers, "final_hs_index": final_hs,
        "n_prompts": len(prompts), "n_test_dirs": len(test_dirs),
        "mean_cosine_sim": mean_cos, "mean_top10_overlap": mean_overlap10,
        "n_top1_match": n_top1, "per_direction": results,
    }
    Path(args.out).write_text(json.dumps(out, indent=2))
    print(f"[jlens/smoke] mean_cosine_sim={mean_cos:.4f} "
          f"mean_top10_overlap={mean_overlap10:.2f} n_top1_match={n_top1}/{len(results)}",
          flush=True)
    print(f"[jlens/smoke] wrote {args.out}", flush=True)


def _cmd_profile(args):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, tokenizer = load_model(device=device)
    n_layers = model.config.num_hidden_layers
    prompts_q = load_corpus(Path(args.corpus), args.n_prompts, seed=args.seed)
    prompts = [render_prompt(tokenizer, q) for q in prompts_q]
    hs_indices = [int(x) for x in args.layers.split(",")]
    print(f"[jlens/profile] n_layers={n_layers} hs_indices={hs_indices} "
          f"n_prompts={len(prompts)} n_random_dirs={args.n_random_dirs}", flush=True)
    out_path = Path(args.out)

    def _flush(hs_index, per_layer_so_far):
        partial = {"model": MODEL_BF16, "n_layers": n_layers,
                   "hs_indices": hs_indices, "n_random_dirs": args.n_random_dirs,
                   "seed": args.seed, "status": "in_progress",
                   "layers_done": list(per_layer_so_far.keys()),
                   "per_layer": per_layer_so_far}
        out_path.write_text(json.dumps(partial, indent=2))
        print(f"[jlens/profile] flushed partial ({len(per_layer_so_far)}/"
              f"{len(hs_indices)} layers) -> {out_path}", flush=True)

    prof = layer_profile(model, tokenizer, prompts, hs_indices,
                          n_random_dirs=args.n_random_dirs, seed=args.seed,
                          on_layer_done=_flush)
    out = {"model": MODEL_BF16, "n_layers": n_layers, "status": "complete", **prof}
    out_path.write_text(json.dumps(out, indent=2))
    print(f"[jlens/profile] wrote {args.out}", flush=True)


def _cmd_h1(args):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, tokenizer = load_model(device=device)
    prompts_q = load_corpus(Path(args.corpus), args.n_prompts, seed=args.seed)
    prompts = [render_prompt(tokenizer, q) for q in prompts_q]

    # All four fitted directions were flattened into this experiment's own
    # analysis-committed/source_directions/ for self-containment (see
    # NOTEBOOK.md); the sibling two-signal worktree keeps u_d/c_hat at its
    # analysis-committed/ top level and pos_ctrl/neg_ctrl nested one level
    # deeper under its own source_directions/ -- both landed in the SAME
    # flat directory here.
    dir_dir = Path(args.directions_dir) / "source_directions"
    named = {
        "u_d_L34 (doubt)": dir_dir / "u_d_L34.json",
        "pos_ctrl_L34 (caution / answer-vs-refuse)": dir_dir / "pos_ctrl_L34.json",
        "neg_ctrl_L34 (confab-propensity)": dir_dir / "neg_ctrl_L34.json",
        "c_hat_L34 (caution write, orthogonalized)": dir_dir / "c_hat_L34.json",
    }
    offsets = [int(x) for x in args.layer_offsets.split(",")]

    out = {"model": MODEL_BF16, "bnb4bit_source_model": MODEL_BNB4BIT_RAW_BASE,
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
        p.add_argument("--corpus", default=str(DEFAULT_CORPUS_PATH))
        p.add_argument("--n-prompts", type=int, default=20)
        p.add_argument("--seed", type=int, default=20260707)
        p.add_argument("--out", required=True)

    p_build = sub.add_parser("build-corpus", help="sample+write this "
                              "experiment's own local prompt corpus (CPU-only)")
    p_build.add_argument("--source", default=DEFAULT_SOURCE_POOL)
    p_build.add_argument("--out", default=str(DEFAULT_CORPUS_PATH))
    p_build.add_argument("--n", type=int, default=1000)
    p_build.add_argument("--seed", type=int, default=20260707)
    p_build.set_defaults(func=lambda a: print(
        f"[jlens/build-corpus] wrote {build_corpus(Path(a.source), Path(a.out), a.n, a.seed)} "
        f"questions -> {a.out}"))

    p_smoke = sub.add_parser("smoke", help="correctness smoke: final-layer "
                              "J-lens vs logit lens + end-to-end run check")
    _common(p_smoke)
    p_smoke.add_argument("--n-test-dirs", type=int, default=5)
    p_smoke.set_defaults(func=_cmd_smoke)

    p_profile = sub.add_parser("profile", help="layer_profile: locate the "
                                "workspace across depth")
    _common(p_profile)
    p_profile.add_argument("--layers", required=True,
                            help="comma-separated hs_index values, e.g. 4,10,16,22,28,34,36")
    p_profile.add_argument("--n-random-dirs", type=int, default=6)
    p_profile.set_defaults(func=_cmd_profile)

    p_h1 = sub.add_parser("h1", help="H1: verbalize our fitted directions "
                           "at L34 and nearby layers")
    _common(p_h1)
    p_h1.add_argument("--directions-dir", required=True,
                       help="path to analysis-committed/ (this experiment's "
                       "own copy, with source_directions/{u_d,pos_ctrl,"
                       "neg_ctrl,c_hat}_L34.json all flattened into one dir)")
    p_h1.add_argument("--layer-offsets", default="-4,-2,0,2",
                       help="hs_index offsets from each direction's own fit layer")
    p_h1.add_argument("--top-k", type=int, default=15)
    p_h1.set_defaults(func=_cmd_h1)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
