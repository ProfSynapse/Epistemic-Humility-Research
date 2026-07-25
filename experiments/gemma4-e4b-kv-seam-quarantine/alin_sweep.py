#!/usr/bin/env python3
"""G0-ALIN Part 1 -- linear accessibility (`A_lin`) sweep for below-seam site selection.

Implements `gates.yaml` gate `g0_alin_site_selection` (part 1 of 2) and the
matching AMENDMENT.md section. CPU-ONLY over the parent's already-cached gemma
activations; it loads NO weights to CUDA, which is what makes this a pre-sign
deliverable rather than a run stage.

## Definition (registered, not invented here)

    A_lin(hs_N) = top-1 accuracy of applying the model's final RMSNorm and
    unembedding W_U to the cached hidden state at hs_N, argmax over the KU
    contrast's answer tokens.

Operationally, following the parent's validated harness
(`j-space-cross-family-layer-contrast/analysis/crystallization-ladder/
alin_recompute.py`, whose numbers this gate's blocker note is drawn from):

  * hidden state = the cached anchor activation at `prompt_len - 1`, the last
    prompt token, from `anchor_extract.safetensors`;
  * logits = `softcap(W_U @ final_norm(h))`, the model-native output path;
  * target = the row's own RECORDED GREEDY next token. Because the recorded
    generation is greedy (`do_sample=False`), that token is BY CONSTRUCTION the
    argmax of the true final-layer logits, which is what makes the terminal
    layer a tautology and therefore a harness self-test (see below).

The phrase "argmax over the KU contrast's answer tokens" in the registered
definition is read the way the parent's harness implements it: argmax over the
full vocabulary, scored against the recorded answer token OF each KU-contrast
row. It is NOT a restricted argmax over a hand-built candidate list -- no such
list exists anywhere in this program, and a restricted argmax would make
`A_lin` depend on a list nobody registered. Reading it the other way would also
break the terminal-layer tautology that validates the harness.

## Why this is not just a re-read of the parent's numbers

The parent ran this ladder and its results are quoted in the G0-ALIN blocker,
but they cannot be reused as-is for selection, for two independent reasons:

  1. **hs23 was never computed.** The parent swept
     [15, 18, 20, 22, 24, 28, 34, 38, 40, 42] -- hs23 is absent, and hs23 is one
     of the two candidates the selection rule chooses between.
  2. **It ran on all 806 rows.** The gate registers `split: FIT only`.

## Harness self-validation (all three must pass, or this refuses to report)

  1. **Terminal-layer tautology.** Greedy decoding means the recorded token IS
     the argmax of the true final-layer logits, so `A_lin(hs42)` must be ~1.0
     with median rank 1. A wrong norm/softcap/tying recipe cannot produce that
     -- the corrupt extraction scored 0.000 here. Measured: 0.9975 over all 806
     rows against the parent's GPU 1.0000, every miss a rank-2 near-tie, so the
     threshold is 0.98 with `max_rank` reported alongside (a real failure ranks
     in the thousands and cannot hide behind that tolerance).

     This does NOT double as the postnorm calibration. An earlier revision tried
     to resolve `final_is_postnorm` on CPU by requiring exactly one recipe to be
     tautological; both score ~0.99, because re-normalizing an already-normalized
     vector barely moves the argmax. The fail-closed guard caught that rather
     than picking silently. The recipe is therefore taken from the parent's
     decisive GPU calibration, and it affects hs42 ONLY -- every candidate site
     is normed identically under either recipe, so the selection cannot turn
     on it.
  2. **Distinct-storage / non-vacuity.** Two different depths of the same row
     must be stored as different, non-zero tensors -- catching a silently
     truncated or duplicated extraction.
  3. **Target coverage.** Every FIT row must yield a recorded target token whose
     re-render reproduces the manifest's `prompt_len` exactly. Rows that fail
     are counted and reported, never silently dropped.

## Revision pinning

The tokenizer is loaded at the experiment's PINNED revision. The local HF cache
holds two revisions of this checkpoint and `refs/main` points at the OTHER one,
so a bare load takes an unpinned chat template. Verified 2026-07-25 that both
revisions render all 806 rows to identical `prompt_len` (their differences are
in tool-calling/thinking macros this probe never exercises) and that the
`model.safetensors` blob is byte-identical between them -- but the pin is passed
explicitly anyway, so the ambiguity cannot return.

## What this script does NOT do

It does not select A3 by median rank. The registered statistic is top-1
accuracy; on this model it is expected to sit at the floor for every below-seam
candidate, in which case the registered TIE-BREAK decides (hs22, the site that
reaches both donors). Median rank is reported as an OBSERVATION because it is
informative, but substituting it for the registered statistic would be
goalpost movement and is refused. See `--emit-selection`.

Usage (CPU-only):
    python3 alin_sweep.py                     # sweep + report, no selection written
    python3 alin_sweep.py --emit-selection    # also write the A3/A6 selection record
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

import torch
from safetensors import safe_open

import model_lib as ml  # noqa: E402  (vendored render path; see backends.py)

FAMILY = "gemma4-e4b"
PINNED_REVISION = "fee6332c1abaafb77f6f9624236c63aa2f1d0187"

# Registered in gates.yaml g0_alin_site_selection.recorded_for.
RECORDED_FOR = [15, 18, 20, 22, 23, 24, 34, 38, 42]
CANDIDATES = (22, 23)   # A3 is the higher-A_lin of these; the other becomes A6.
A5_SITE = 24            # Fixed by geometry: the first quarantined block.
TIE_BAND = 0.01         # |delta A_lin| < TIE_BAND -> tie -> break to hs22.
CONFOUND_BAND = 0.10    # |A_lin(A3) - A_lin(A5)| > this -> declare confounded.
TIE_BREAK_SITE = 22

# Resolved by the parent's GPU calibration, which reconstructed the model's own
# `out.logits` from `hidden_states[-1]`: applying the head directly reproduced
# them to max-abs error EXACTLY 0.0, while inserting the final norm first gave
# 17.6875. That is decisive; a CPU-only run cannot reproduce it (see the
# calibration block in main() for why the terminal-layer tautology does not
# discriminate). It affects hs42 only and cannot touch the site selection.
FINAL_IS_POSTNORM = True
FINAL_IS_POSTNORM_PROVENANCE = (
    "j-space-cross-family-layer-contrast/analysis/crystallization-ladder/"
    "alin_recompute.py calibrate_head(), GPU, 2026-07-24: maxabs_recon_postnorm=0.0 "
    "vs maxabs_recon_prenorm=17.6875, vocab=262144, softcap=30.0"
)

# The terminal layer is a tautology under greedy decoding, but only up to
# arithmetic: this runs on CPU in the head's dtype while the parent ran on GPU,
# and rows whose top-2 logits are a near-tie can swap. Measured 2026-07-25: bf16
# head, postnorm -> 0.9975 over all 806 rows (parent, on GPU: 1.0000), with
# max rank 2 -- i.e. every miss is a rank-2 near-tie, never a real failure. The
# threshold is set to catch a BROKEN lens (which scores ~0.000, as the corrupt
# extraction did), not to chase the last two rows of CPU/GPU tie-breaking.
TAUTOLOGY_MIN_TOP1 = 0.98


def _here() -> Path:
    return Path(__file__).resolve().parent


def load_jsonl(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def sanitize_key(row_key: str) -> str:
    """Matches extract_anchor.py / build_directions.py tensor-key convention."""
    return row_key.replace(":", "_")


def tensor_key(hs_index: int, row_key: str) -> str:
    return f"hs{hs_index}__{sanitize_key(row_key)}"


def summarize(ranks: list[int], top1s: list[int]) -> dict:
    if not ranks:
        return {"n": 0, "top1_acc": None, "median_rank": None}
    return {
        "n": len(ranks),
        "top1_acc": round(sum(top1s) / len(top1s), 4),
        "median_rank": int(statistics.median(ranks)),
        "mean_rank": round(sum(ranks) / len(ranks), 1),
        "p90_rank": int(sorted(ranks)[int(0.9 * (len(ranks) - 1))]),
        "min_rank": min(ranks),
        "max_rank": max(ranks),
    }


def load_head_and_norm(snapshot: Path, eps: float, head_dtype: torch.dtype = torch.bfloat16):
    """Load ONLY the final RMSNorm and the tied unembedding, on CPU.

    Deliberately not a full `from_pretrained`: this experiment's loader uses
    `device_map="auto"`, which would place weights on CUDA and break the gate's
    CPU-only scope, and the full Gemma4 graph materializes vision AND audio
    towers (families/gemma4-e4b.yaml notes) that no part of a logit lens needs.
    """
    from transformers.models.gemma4.modeling_gemma4 import Gemma4RMSNorm

    weights_path = snapshot / "model.safetensors"
    with safe_open(str(weights_path), "pt") as f:
        keys = set(f.keys())
        norm_key = "model.language_model.norm.weight"
        embed_key = "model.language_model.embed_tokens.weight"
        for k in (norm_key, embed_key):
            if k not in keys:
                raise RuntimeError(
                    f"[alin_sweep] {k} missing from {weights_path}. The logit "
                    "lens needs the final RMSNorm and the tied unembedding; "
                    "refusing to guess an alternative tensor name."
                )
        norm_w = f.get_tensor(norm_key)
        embed = f.get_tensor(embed_key)

    final_norm = Gemma4RMSNorm(norm_w.shape[0], eps=eps)
    with torch.no_grad():
        final_norm.weight.copy_(norm_w.float())
    final_norm.eval()
    # Tied embeddings: W_U IS the embedding matrix (tie_word_embeddings: true).
    # Default bf16, matching the checkpoint's own dtype and the parent harness's
    # `head.weight.dtype` -- the point is to reproduce the model's real output
    # path, not a more precise one. fp32 is available via --head-dtype and moves
    # the terminal tautology from 0.9966 to 0.9897 on FIT (measured 2026-07-25),
    # i.e. slightly further from the model's actual behaviour, not closer.
    W_U = embed.to(head_dtype)
    return final_norm, W_U


def lens_logits(h: torch.Tensor, final_norm, W_U: torch.Tensor,
                softcap: float, apply_norm: bool) -> torch.Tensor:
    """h: [n, hidden] fp32 -> [n, vocab] fp32, via the model-native output path.

    The cast to `W_U.dtype` mirrors the parent harness's `head(h.to(hd))`: the
    unembedding runs in the head's own dtype, and only the resulting logits are
    promoted to fp32 for ranking.
    """
    x = final_norm(h) if apply_norm else h
    z = (x.to(W_U.dtype) @ W_U.T).float()
    if softcap is not None:
        z = softcap * torch.tanh(z / softcap)
    return z


def score_depth(f, depth: int, row_keys: list[str], targets: dict,
                final_norm, W_U, softcap: float, apply_norm: bool,
                chunk: int = 32) -> tuple[list[int], list[int], int]:
    """Return (ranks, top1s, n_missing_tensor) for one depth."""
    ranks: list[int] = []
    top1s: list[int] = []
    missing = 0
    batch: list[torch.Tensor] = []
    batch_tgt: list[int] = []

    def flush():
        if not batch:
            return
        H = torch.stack(batch).float()
        logits = lens_logits(H, final_norm, W_U, softcap, apply_norm)
        for i, tgt in enumerate(batch_tgt):
            row = logits[i]
            tv = row[tgt]
            ranks.append(int((row > tv).sum().item()) + 1)
            top1s.append(int(int(row.argmax().item()) == tgt))
        batch.clear()
        batch_tgt.clear()

    for rk in row_keys:
        key = tensor_key(depth, rk)
        try:
            h = f.get_tensor(key)
        except Exception:
            missing += 1
            continue
        batch.append(h)
        batch_tgt.append(targets[rk])
        if len(batch) >= chunk:
            flush()
    flush()
    return ranks, top1s, missing


def build_targets(tok, rows: list[dict], rows_meta: dict, gens: dict) -> tuple[dict, dict]:
    """Recorded greedy next token per row, with the prompt_len guard.

    Ported from the parent's `build_gemma_targets`. The `prompt_len` check is
    load-bearing, not defensive: it proves the render used here reproduces the
    one the activations were extracted under, so the anchor index means the
    same thing in both.
    """
    targets: dict[str, int] = {}
    skipped = {"no_generation": 0, "prompt_len_mismatch": 0,
               "not_a_prefix": 0, "empty_answer": 0}
    for row in rows:
        rk = row["row_key"]
        if rk not in rows_meta:
            continue
        if rk not in gens:
            skipped["no_generation"] += 1
            continue
        want_len = rows_meta[rk]["prompt_len"]
        rendered = ml.render(FAMILY, tok, row)
        pids = tok(rendered)["input_ids"]
        if len(pids) != want_len:
            skipped["prompt_len_mismatch"] += 1
            continue
        answer = gens[rk].get("answer_text") or ""
        full = tok(rendered + answer)["input_ids"]
        if full[:len(pids)] != pids:
            skipped["not_a_prefix"] += 1
            continue
        if len(full) <= want_len:
            skipped["empty_answer"] += 1
            continue
        targets[rk] = int(full[want_len])
    return targets, skipped


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--parent-analysis", default=None,
                    help="Directory holding the parent's cached gemma artifacts. "
                         "Defaults to this experiment's analysis/gemma4-e4b/ "
                         "(where they are staged as symlinks).")
    ap.add_argument("--emit-selection", action="store_true",
                    help="Also write the A3/A6 selection record to "
                         "analysis-committed/. Off by default so the sweep can "
                         "be inspected before anything registration-bearing is "
                         "written.")
    ap.add_argument("--chunk", type=int, default=32)
    ap.add_argument("--head-dtype", choices=["bf16", "fp32"], default="bf16",
                    help="dtype of the unembedding matmul. Default bf16 = the "
                         "checkpoint's own dtype and the parent harness's path.")
    args = ap.parse_args(argv)
    head_dtype = {"bf16": torch.bfloat16, "fp32": torch.float32}[args.head_dtype]

    here = _here()
    analysis = Path(args.parent_analysis) if args.parent_analysis else here / "analysis" / FAMILY
    committed = here / "analysis-committed" / FAMILY

    extract_path = analysis / "anchor_extract.safetensors"
    manifest_path = analysis / "anchor_extract_manifest.json"
    split_path = committed / "split_manifest.json"
    if not extract_path.exists():
        raise RuntimeError(f"[alin_sweep] missing cached extraction: {extract_path}")

    manifest = json.loads(manifest_path.read_text())
    if manifest.get("forward_use_cache") is not True:
        raise RuntimeError(
            "[alin_sweep] this extraction was produced with forward_use_cache != "
            "True. Blocks >= hs25 read K/V from donors THROUGH the cache, so a "
            "use_cache=False extraction is corrupt above the seam and A_lin "
            "measured on it is meaningless (parent finding (6) / Defect 3). "
            "Refusing to sweep."
        )
    rows_meta = {r["row_key"]: r for r in manifest["rows"]}

    rows_path = Path(manifest["rows_path"])
    if not rows_path.exists():
        raise RuntimeError(
            f"[alin_sweep] the extraction manifest points at {rows_path}, which "
            "does not exist. The eval rows are restricted data staged from the "
            "parent experiment; pass --parent-analysis or restore the symlink."
        )
    rows = load_jsonl(rows_path)
    gens = {r["row_key"]: r for r in load_jsonl(analysis / "pool_generations.jsonl")}

    split_manifest = json.loads(split_path.read_text())
    split_by_key = {r["row_key"]: r["split"] for r in split_manifest["rows"]}
    fit_keys = {rk for rk, sp in split_by_key.items() if sp == "fit"}
    if not fit_keys:
        raise RuntimeError("[alin_sweep] split_manifest.json yielded no FIT rows.")

    # ---- model-side constants, from the PINNED snapshot ------------------
    from huggingface_hub import snapshot_download
    snapshot = Path(snapshot_download("google/gemma-4-E4B-it", revision=PINNED_REVISION,
                                      allow_patterns=["config.json", "model.safetensors",
                                                      "tokenizer*", "chat_template.jinja"]))
    cfg = json.loads((snapshot / "config.json").read_text())
    tcfg = cfg["text_config"]
    softcap = tcfg.get("final_logit_softcapping")
    eps = tcfg.get("rms_norm_eps", 1e-6)
    n_layers = tcfg["num_hidden_layers"]
    vocab = tcfg["vocab_size"]

    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained("google/gemma-4-E4B-it", revision=PINNED_REVISION)

    print(f"[alin_sweep] CPU-only. n_layers={n_layers} vocab={vocab} softcap={softcap}", flush=True)
    print("[alin_sweep] building targets (recorded greedy next token) ...", flush=True)
    targets, skipped = build_targets(tok, rows, rows_meta, gens)
    fit_rows = [rk for rk in targets if rk in fit_keys]
    fit_rows.sort()
    print(f"[alin_sweep] targets={len(targets)}/{len(rows)}  FIT rows with target={len(fit_rows)}"
          f"  skipped={skipped}", flush=True)
    if not fit_rows:
        raise RuntimeError("[alin_sweep] no FIT row produced a usable target.")
    if skipped["prompt_len_mismatch"]:
        raise RuntimeError(
            f"[alin_sweep] {skipped['prompt_len_mismatch']} rows re-rendered to a "
            "different prompt_len than the extraction recorded. The render has "
            "drifted from the one the activations were produced under, so the "
            "anchor index does not mean the same thing in both. Refusing to sweep."
        )

    print("[alin_sweep] loading final RMSNorm + tied unembedding (CPU) ...", flush=True)
    t0 = time.time()
    final_norm, W_U = load_head_and_norm(snapshot, eps, head_dtype)
    print(f"[alin_sweep] head loaded in {time.time()-t0:.1f}s, W_U={tuple(W_U.shape)}", flush=True)

    report: dict = {
        "gate": "g0_alin_site_selection",
        "part": "1 of 2",
        "generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "family": FAMILY,
        "checkpoint": "google/gemma-4-E4B-it",
        "revision": PINNED_REVISION,
        "device": "cpu",
        "definition": ("A_lin = top-1 accuracy of softcap(W_U @ final_norm(h_anchor)) "
                       "predicting the row's recorded greedy next token, argmax over "
                       "the full vocabulary; median rank reported as an observation"),
        "split": "fit",
        "n_fit_rows_scored": len(fit_rows),
        "n_rows_total": len(rows),
        "target_skips": skipped,
        "softcap": softcap,
        "rms_norm_eps": eps,
    }

    with safe_open(str(extract_path), "pt") as f:
        available = set(f.keys())

        # ---- guard 2: distinct storage / non-vacuity --------------------
        probe_rk = fit_rows[0]
        ka, kb = tensor_key(22, probe_rk), tensor_key(n_layers, probe_rk)
        if ka not in available or kb not in available:
            raise RuntimeError(f"[alin_sweep] vacuity probe tensors missing ({ka}, {kb}).")
        ta, tb = f.get_tensor(ka), f.get_tensor(kb)
        vacuity = {
            "pair": [22, n_layers],
            "hsA_norm": round(ta.norm().item(), 3),
            "hsB_norm": round(tb.norm().item(), 3),
            "distinct": bool(not torch.equal(ta, tb)),
            "both_nonzero": bool(ta.norm() > 0 and tb.norm() > 0),
        }
        report["vacuity_guard"] = vacuity
        if not (vacuity["distinct"] and vacuity["both_nonzero"]):
            raise RuntimeError(f"[alin_sweep] vacuity guard FAILED: {vacuity}")
        print(f"[alin_sweep] vacuity guard OK: {vacuity}", flush=True)

        # ---- guard 1: terminal-layer tautology, both output recipes -------
        # NOTE ON WHAT CPU CAN AND CANNOT ESTABLISH. An earlier revision of this
        # script tried to RESOLVE final_is_postnorm here, by requiring exactly
        # one recipe to hit ~1.0 at the terminal layer. It does not work, and the
        # fail-closed guard caught it rather than letting it pick silently: both
        # recipes score ~0.99 with median rank 1, because re-normalizing an
        # already-normalized vector barely moves the argmax. Discriminating the
        # two needs a live forward to reconstruct `out.logits`, which is GPU work
        # and out of this gate's CPU-only scope. So the recipe is taken from the
        # parent's decisive measurement (see FINAL_IS_POSTNORM) and the tautology
        # is kept as a HEALTH CHECK, not a discriminator. Both variants are
        # reported so the choice stays inspectable.
        #
        # This choice cannot touch the selection: `apply_norm` differs between
        # the recipes ONLY at hs{n_layers}. Every candidate site (hs22, hs23,
        # hs24) is normed identically either way.
        print(f"[alin_sweep] terminal-layer tautology at hs{n_layers}, both recipes ...",
              flush=True)
        calib = {}
        for label, apply_norm in (("postnorm_no_extra_norm", False), ("prenorm_apply_norm", True)):
            r, t, _ = score_depth(f, n_layers, fit_rows, targets, final_norm, W_U,
                                  softcap, apply_norm, args.chunk)
            calib[label] = summarize(r, t)
            print(f"    {label:24s} -> {calib[label]}", flush=True)
        final_is_postnorm = FINAL_IS_POSTNORM
        chosen = calib["postnorm_no_extra_norm" if final_is_postnorm else "prenorm_apply_norm"]
        report["calibration"] = {
            "final_is_postnorm": bool(final_is_postnorm),
            "resolved_by": FINAL_IS_POSTNORM_PROVENANCE,
            "cpu_can_resolve_this": False,
            "why_not": ("both recipes score ~0.99 with median rank 1 at the terminal "
                        "layer -- re-normalizing an already-normalized vector barely "
                        "moves the argmax. Discriminating them needs a live forward to "
                        "reconstruct out.logits, which is GPU work and outside this "
                        "gate's CPU-only scope."),
            "affects_selection": False,
            "affects_selection_why": (f"the two recipes differ only at hs{n_layers}; "
                                      "hs22/hs23/hs24 are normed identically either way"),
            "head_dtype": str(W_U.dtype),
            "candidates": calib,
        }
        print(f"[alin_sweep] final_is_postnorm={final_is_postnorm} "
              f"(from the parent's GPU calibration; CPU cannot discriminate)", flush=True)

        # ---- the sweep ---------------------------------------------------
        by_depth = {}
        for d in RECORDED_FOR:
            apply_norm = not (d == n_layers and final_is_postnorm)
            t0 = time.time()
            r, t, missing = score_depth(f, d, fit_rows, targets, final_norm, W_U,
                                        softcap, apply_norm, args.chunk)
            if missing:
                raise RuntimeError(
                    f"[alin_sweep] hs{d}: {missing} FIT rows had no cached tensor. "
                    "A partial depth would silently change the population A_lin is "
                    "averaged over. Refusing to report."
                )
            s = summarize(r, t)
            by_depth[f"hs{d}"] = s
            print(f"    hs{d:<3d} A_lin={s['top1_acc']:.4f}  median_rank={s['median_rank']:>7d}"
                  f"  n={s['n']}  ({time.time()-t0:.1f}s)", flush=True)
        report["by_depth"] = by_depth

    # ---- terminal tautology, restated as an explicit pass/fail ----------
    term = by_depth[f"hs{n_layers}"]
    report["harness_self_test"] = {
        "terminal_layer_tautology": {
            "site": f"hs{n_layers}",
            "top1_acc": term["top1_acc"],
            "median_rank": term["median_rank"],
            "threshold": TAUTOLOGY_MIN_TOP1,
            "max_rank": term["max_rank"],
            "pass": bool(term["top1_acc"] >= TAUTOLOGY_MIN_TOP1 and term["median_rank"] == 1),
            "why": ("the recorded generation is greedy, so the recorded token IS the "
                    "argmax of the true final-layer logits; a wrong norm/softcap/"
                    "tying recipe cannot reproduce this -- the corrupt extraction "
                    "scored 0.000 here"),
            "tolerance_note": ("threshold is 0.98, not 1.0: this runs on CPU in the "
                               "head's dtype while the parent ran on GPU, so rows whose "
                               "top-2 logits near-tie can swap. max_rank is reported so "
                               "a real failure (rank in the thousands) cannot hide "
                               "behind that tolerance."),
        },
        "vacuity_guard_pass": True,
        "all_fit_rows_present_at_every_depth": True,
    }
    if not report["harness_self_test"]["terminal_layer_tautology"]["pass"]:
        raise RuntimeError(f"[alin_sweep] terminal-layer tautology FAILED: {term}")

    # ---- registered selection rule --------------------------------------
    a22 = by_depth["hs22"]["top1_acc"]
    a23 = by_depth["hs23"]["top1_acc"]
    delta = abs(a22 - a23)
    tied = delta < TIE_BAND
    if tied:
        a3, a6, basis = TIE_BREAK_SITE, (23 if TIE_BREAK_SITE == 22 else 22), "tie_break"
    elif a22 > a23:
        a3, a6, basis = 22, 23, "higher_a_lin"
    else:
        a3, a6, basis = 23, 22, "higher_a_lin"

    a_a3 = by_depth[f"hs{a3}"]["top1_acc"]
    a_a5 = by_depth[f"hs{A5_SITE}"]["top1_acc"]
    confound_delta = abs(a_a3 - a_a5)
    confounded = confound_delta > CONFOUND_BAND

    selection = {
        "rule": ("A3 = whichever of hs22/hs23 has the HIGHER A_lin; ties "
                 f"(|delta| < {TIE_BAND}) break to hs{TIE_BREAK_SITE}, the site that "
                 "reaches BOTH donors. A5 is hs24 regardless (first quarantined block)."),
        "a_lin_hs22": a22,
        "a_lin_hs23": a23,
        "delta_a_lin": round(delta, 6),
        "tie_band": TIE_BAND,
        "tie": bool(tied),
        "selection_basis": basis,
        "A3": f"hs{a3}",
        "A6": f"hs{a6}",
        "A5": f"hs{A5_SITE}",
        "confound_declaration": {
            "rule": (f"|A_lin(A3) - A_lin(A5)| > {CONFOUND_BAND} -> the A3-vs-A5 "
                     "DESCRIPTIVE contrast is declared CONFOUNDED BY LINEAR "
                     "ACCESSIBILITY at registration time"),
            "a_lin_A3": a_a3,
            "a_lin_A5": a_a5,
            "abs_delta": round(confound_delta, 6),
            "band": CONFOUND_BAND,
            "declared_confounded": bool(confounded),
        },
        "statistic_note": (
            "The registered statistic is TOP-1 ACCURACY. Median rank is recorded as "
            "an observation only and takes no part in selection; substituting it "
            "would be goalpost movement on a locked rule."
        ),
    }
    report["selection"] = selection

    # Outputs ALWAYS land in this experiment's own private analysis dir, never
    # in `analysis` -- that may point at the parent experiment (--parent-analysis
    # supplies INPUTS), and writing results into another experiment's tree would
    # scatter this run's provenance across two trees.
    out_dir = here / "analysis" / FAMILY
    out_dir.mkdir(parents=True, exist_ok=True)
    out_private = out_dir / "alin_sweep_part1.json"
    out_private.write_text(json.dumps(report, indent=2))
    print(f"\n[alin_sweep] wrote {out_private}", flush=True)

    print("\n=== G0-ALIN Part 1 ===")
    for d in RECORDED_FOR:
        s = by_depth[f"hs{d}"]
        print(f"  hs{d:<3d} A_lin={s['top1_acc']:.4f}  median_rank={s['median_rank']:>7d}")
    print(f"\n  A_lin(hs22)={a22:.4f}  A_lin(hs23)={a23:.4f}  |delta|={delta:.6f}"
          f"  tie={tied} ({basis})")
    print(f"  -> A3 = hs{a3}   A6 = hs{a6}   A5 = hs{A5_SITE}")
    print(f"  |A_lin(A3) - A_lin(A5)| = {confound_delta:.6f}  "
          f"({'DECLARED CONFOUNDED' if confounded else 'not confounded'}, band {CONFOUND_BAND})")

    if args.emit_selection:
        committed.mkdir(parents=True, exist_ok=True)
        out_committed = committed / "alin_part1_selection.json"
        # Aggregates and the decision ONLY -- no row keys, no prompt text, no
        # per-row data. analysis-committed/ is public; the eval rows are not.
        out_committed.write_text(json.dumps({
            k: report[k] for k in (
                "gate", "part", "generated", "family", "checkpoint", "revision",
                "device", "definition", "split", "n_fit_rows_scored", "softcap",
                "rms_norm_eps", "calibration", "vacuity_guard", "harness_self_test",
                "by_depth", "selection")
        }, indent=2))
        print(f"[alin_sweep] wrote {out_committed}", flush=True)
    else:
        print("\n[alin_sweep] --emit-selection not passed; nothing written to "
              "analysis-committed/.", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
