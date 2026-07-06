#!/usr/bin/env python3
"""Diagnostics bundle cell 2 (TODO item 21) — sentence-panel neutral control.

Lab-notebook diagnostic (tier L): no amendment, no gates. Extends the
single-sentence neutral-prepend control (amendment_ag_neutral_control.py,
PR #166) to a PANEL of semantically-neutral sentences so the residual
"sentence-choice variance" on the §9.3 caution shift can be bounded.

WHY
---
The single-sentence control (result amendment_ag_neutral_result.json) showed
the generic any-prepend component is real (neutral Δcaution ~ -0.34z / -0.65z)
while the prime differential vs neutral stayed semantically coherent. The open
residual: those numbers rest on ONE neutral sentence. A panel of ~6 neutral
sentences that vary surface form but not epistemic content lets us report the
neutral Δcaution as a mean ± between-sentence spread, and check the prime-vs-
neutral differential survives the worst-case neutral sentence.

DESIGN (mirrors amendment_ag_neutral_control.py exactly, per sentence)
----------------------------------------------------------------------
- Raw unsloth/Qwen3-4B-bnb-4bit, no adapter (the AF/AG base surface).
- Extraction: for each panel sentence S_j, render all AE pool rows with
  "S_j <space> baseline_system_prompt" and capture the pre-gen anchor at
  prompt_len-1 for all layers (byte-identical tensor contract to af_base_pregen).
  One forward pass per (sentence, row). Output dir per sentence:
    <out_root>/panel/<slug_j>/{rows.jsonl, <safe_key>__pre.safetensors, manifest.json}
- Analysis (CPU): reuse the AG doubt/caution axis fit (L24, 5-fold CV, doubt
  sanity floor 0.98) from the baseline af_base_pregen tensors; project each
  panel sentence's tensors; report per-sentence Δdoubt/Δcaution (z-scored by
  baseline SD, bootstrap CI) AND the between-sentence mean ± spread, side by
  side with the recomputed HIGH/LOW/single-neutral cells.

PANEL (locked; 6 neutral sentences — surface-varied, epistemically inert)
-------------------------------------------------------------------------
  n1 (the PR #166 sentence, kept as the panel anchor for continuity):
      "The following question was selected from a large general collection of
       questions for use in this study."
  n2: "This item is one of many drawn from a broad survey of general topics."
  n3: "Below is a question taken from a standard assortment of survey prompts."
  n4: "The next question comes from a general-purpose set compiled for research."
  n5: "What follows is a routine question sampled from a large mixed pool."
  n6: "Here is a question chosen at random from an ordinary question bank."

RUNTIME NOTE
------------
This cell's ANALYSIS depends on canonical-only tensors (af_base_pregen and the
AG high/low pregen dirs) that are NOT published to HF, so the natural lane is
LOCAL GPU (the AE pool + AF/AG tensors live in the canonical checkout / AG
worktree). The extraction is a small forward-only pass (6 sentences x 600 rows).
Run extraction + analysis together locally; there is no clean pod version
because the analysis inputs cannot leave the workstation.

Do NOT commit outputs. The lead reviews scripts and results before git ops.

Usage (local GPU):
  python amendment_ag_neutral_panel.py --full          # 6 sentences x 600 rows + analysis
  python amendment_ag_neutral_panel.py                 # smoke: 6 rows x panel, no analysis
  python amendment_ag_neutral_panel.py --analysis-only # analysis over an existing panel
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

PROBE_DIR = Path(__file__).resolve().parent
EVAL_DIR = PROBE_DIR.parent / "eval"
for p in (str(PROBE_DIR), str(EVAL_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

# Reuse every analysis primitive from the single-sentence control so the panel
# numbers are computed by identical machinery (only the sentence set changes).
from amendment_ag_neutral_control import (  # noqa: E402
    AF_PREGEN_DIR, AG_HIGH_DIR, AG_LOW_DIR, AE_CENSUS_ROWS,
    DEFAULT_POOL, DOUBT_SANITY_FLOOR, TARGET_LAYER,
    _config_sha, bootstrap_mean_ci, cell_stats, fit_full, fit_logistic_cv,
    load_baseline_system_prompt, load_jsonl, load_layer_matrix, load_pool,
    project, sha256_path,
)

WORKTREE = Path("/home/profsynapse/code/ehr-worktrees/lab-diagnostics-bundle")
DEFAULT_OUT_ROOT = (
    WORKTREE / "experiment/phase1/probe/analysis/ag_neutral_panel_pregen"
)

# Locked neutral panel. n1 is the PR #166 sentence (panel anchor / continuity).
NEUTRAL_PANEL: list[tuple[str, str]] = [
    ("n1", "The following question was selected from a large general collection "
           "of questions for use in this study."),
    ("n2", "This item is one of many drawn from a broad survey of general topics."),
    ("n3", "Below is a question taken from a standard assortment of survey prompts."),
    ("n4", "The next question comes from a general-purpose set compiled for research."),
    ("n5", "What follows is a routine question sampled from a large mixed pool."),
    ("n6", "Here is a question chosen at random from an ordinary question bank."),
]


def _safe_key(row_key: str) -> str:
    return row_key.replace("::", "__").replace("|", "_")


def run_extraction(args) -> dict:
    """GPU extraction: one pre-gen anchor pass per (panel sentence, pool row)."""
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from safetensors.torch import save_file
    from backends import render_probe_prompt

    model_name = args.base_model or "unsloth/Qwen3-4B-bnb-4bit"
    out_root = Path(args.out_dir).resolve()
    (out_root / "panel").mkdir(parents=True, exist_ok=True)

    baseline_system = load_baseline_system_prompt()
    pool = load_pool(Path(args.pool).resolve())
    rows_to_run = pool if args.full else pool[:6]

    print(f"[ag-panel/extract] loading RAW base {model_name} (no adapter) ...",
          flush=True)
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name, torch_dtype=torch.bfloat16, device_map="cuda")
    model.eval()
    device = next(model.parameters()).device
    n_layers = model.config.num_hidden_layers

    panel_manifest = {}
    for slug, sentence in NEUTRAL_PANEL:
        neutral_system = sentence + " " + baseline_system
        sent_dir = out_root / "panel" / slug
        sent_dir.mkdir(parents=True, exist_ok=True)

        config_payload = {
            "amendment": "AG", "section": "neutral_panel", "sentence_slug": slug,
            "stage": "neutral_panel_pregen_extract", "base_model": model_name,
            "adapter": "NONE-raw-instruct-base",
            "baseline_system_prompt": baseline_system, "neutral_sentence": sentence,
            "enable_thinking": False, "anchor_position": "prompt_len-1",
            "persist_dtype": "float32", "generation": "NONE-forward-only",
            "rendering": "neutral", "pool_source": str(args.pool),
        }
        cfg_sha = _config_sha(config_payload)
        sent_tokens = len(tokenizer(sentence)["input_ids"])

        print(f"[ag-panel/extract] sentence {slug} ({sent_tokens} tok): "
              f"{len(rows_to_run)} rows -> {sent_dir}", flush=True)

        rows_path = sent_dir / "rows.jsonl"
        written = 0
        with rows_path.open("w", encoding="utf-8") as rows_fh:
            for item in rows_to_run:
                rendered, _mode = render_probe_prompt(
                    tokenizer, neutral_system, item["question"],
                    enable_thinking=False)
                if written < 3:
                    assert sentence in rendered and baseline_system in rendered
                    assert rendered.index(sentence) < rendered.index(baseline_system)
                enc = tokenizer(rendered, return_tensors="pt").to(device)
                prompt_len = int(enc["input_ids"].shape[1])
                with torch.no_grad():
                    out = model(**enc, output_hidden_states=True, use_cache=False)
                hs = out.hidden_states
                pre = {f"L{li}": hs[li][0, prompt_len - 1, :].float().cpu().contiguous()
                       for li in range(len(hs))}
                sk = _safe_key(item["row_key"])
                save_file(pre, str(sent_dir / f"{sk}__pre.safetensors"))
                rows_fh.write(json.dumps({
                    "row_key": item["row_key"], "label": item["label"],
                    "question": item["question"], "prompt_len": prompt_len,
                    "safe_key": sk, "rendering": "neutral",
                    "sentence_slug": slug, "config_sha": cfg_sha,
                }, ensure_ascii=False) + "\n")
                rows_fh.flush()
                written += 1

        m = {**config_payload, "config_sha": cfg_sha, "n_layers": n_layers,
             "hidden_dim": model.config.hidden_size, "n_written": written,
             "neutral_sentence_tokens": sent_tokens, "out_dir": str(sent_dir),
             "tensor_layer_keys": f"L0..L{n_layers}"}
        (sent_dir / "manifest.json").write_text(json.dumps(m, indent=2),
                                                encoding="utf-8")
        panel_manifest[slug] = m

    root_manifest = {
        "amendment": "AG", "section": "neutral_panel", "base_model": model_name,
        "n_sentences": len(NEUTRAL_PANEL), "n_rows": len(rows_to_run),
        "panel": {slug: s for slug, s in NEUTRAL_PANEL},
        "per_sentence": panel_manifest,
    }
    (out_root / "manifest.json").write_text(json.dumps(root_manifest, indent=2),
                                            encoding="utf-8")
    del model
    torch.cuda.empty_cache()
    if not args.full:
        print("[ag-panel/extract] SMOKE done; re-run with --full for 600 rows "
              "x panel + analysis", flush=True)
    return root_manifest


def run_analysis(out_root: Path) -> dict:
    """Fit doubt/caution at L24 from baseline af tensors, project each panel
    sentence, report per-sentence + between-sentence Δcaution/Δdoubt."""
    af_rows = load_jsonl(AF_PREGEN_DIR / "rows.jsonl")
    ae_by_key = {r["row_key"]: r for r in load_jsonl(AE_CENSUS_ROWS)}

    y_caution = np.array(
        [1 if ae_by_key[r["row_key"]].get("refused", False) else 0
         for r in af_rows], dtype=int)
    y_doubt = np.array(
        [1 if r["label"] == "known" else 0 for r in af_rows], dtype=int)

    X_base = load_layer_matrix(AF_PREGEN_DIR, af_rows, TARGET_LAYER)
    doubt_auroc, _ = fit_logistic_cv(X_base, y_doubt)
    if doubt_auroc < DOUBT_SANITY_FLOOR:
        raise SystemExit(f"STOP: doubt AUROC {doubt_auroc:.4f} < {DOUBT_SANITY_FLOOR}")

    doubt_clf = fit_full(X_base, y_doubt)
    doubt_base = project(doubt_clf, X_base)
    doubt_flip = doubt_base[y_doubt == 1].mean() < doubt_base[y_doubt == 0].mean()
    if doubt_flip:
        doubt_base = -doubt_base
    doubt_sd = float(doubt_base.std())

    caution_clf = fit_full(X_base, y_caution)
    caution_base = project(caution_clf, X_base)
    caution_flip = caution_base[y_caution == 1].mean() < caution_base[y_caution == 0].mean()
    if caution_flip:
        caution_base = -caution_base
    caution_sd = float(caution_base.std())

    known_mask = (y_doubt == 1)
    unknown_mask = (y_doubt == 0)

    def deltas_for(pregen_dir: Path):
        rows = load_jsonl(pregen_dir / "rows.jsonl")
        assert [r["row_key"] for r in rows] == [r["row_key"] for r in af_rows]
        X = load_layer_matrix(pregen_dir, rows, TARGET_LAYER)
        dp = project(doubt_clf, X); dp = -dp if doubt_flip else dp
        cp = project(caution_clf, X); cp = -cp if caution_flip else cp
        return (dp - doubt_base) / doubt_sd, (cp - caution_base) / caution_sd

    per_sentence = {}
    caution_means_known, caution_means_unknown = [], []
    doubt_means_known, doubt_means_unknown = [], []
    for slug, _ in NEUTRAL_PANEL:
        sent_dir = out_root / "panel" / slug
        if not (sent_dir / "rows.jsonl").exists():
            continue
        dz, cz = deltas_for(sent_dir)
        cell = {
            "caution_known": cell_stats(cz, cz, known_mask, f"{slug}×known"),
            "caution_unknown": cell_stats(cz, cz, unknown_mask, f"{slug}×unknown"),
            "doubt_known": cell_stats(dz, dz, known_mask, f"{slug}×known"),
            "doubt_unknown": cell_stats(dz, dz, unknown_mask, f"{slug}×unknown"),
        }
        per_sentence[slug] = cell
        caution_means_known.append(cell["caution_known"]["mean_z"])
        caution_means_unknown.append(cell["caution_unknown"]["mean_z"])
        doubt_means_known.append(cell["doubt_known"]["mean_z"])
        doubt_means_unknown.append(cell["doubt_unknown"]["mean_z"])

    def spread(vals):
        a = np.array(vals, dtype=float)
        return {"n_sentences": int(a.size), "mean": float(a.mean()),
                "sd": float(a.std(ddof=1)) if a.size > 1 else 0.0,
                "min": float(a.min()), "max": float(a.max())}

    result = {
        "amendment": "AG", "section": "neutral_panel_control",
        "target_layer": TARGET_LAYER,
        "doubt_axis": {"cv_auroc_L24": doubt_auroc, "sign_flipped": bool(doubt_flip)},
        "caution_axis_L24": {"sign_flipped": bool(caution_flip)},
        "per_sentence": per_sentence,
        "between_sentence_spread": {
            "caution_known": spread(caution_means_known),
            "caution_unknown": spread(caution_means_unknown),
            "doubt_known": spread(doubt_means_known),
            "doubt_unknown": spread(doubt_means_unknown),
        },
        "panel": {slug: s for slug, s in NEUTRAL_PANEL},
        "artifact_shas": {
            "af_pregen_rows": sha256_path(AF_PREGEN_DIR / "rows.jsonl"),
            "ae_census_rows": sha256_path(AE_CENSUS_ROWS),
        },
        "artifact_paths": {
            "af_pregen_dir": str(AF_PREGEN_DIR), "ag_high_dir": str(AG_HIGH_DIR),
            "ag_low_dir": str(AG_LOW_DIR),
        },
    }
    (out_root / "ag_neutral_panel_result.json").write_text(
        json.dumps(result, indent=2, allow_nan=False), encoding="utf-8")
    print(f"[ag-panel/analysis] written {out_root}/ag_neutral_panel_result.json",
          flush=True)
    sp = result["between_sentence_spread"]["caution_unknown"]
    print(f"[ag-panel/analysis] Δcaution×unknown across panel: mean={sp['mean']:+.3f} "
          f"sd={sp['sd']:.3f} range=[{sp['min']:+.3f},{sp['max']:+.3f}] "
          f"(n={sp['n_sentences']})", flush=True)
    return result


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", default=str(DEFAULT_OUT_ROOT))
    ap.add_argument("--base-model", default=None)
    ap.add_argument("--pool", default=str(DEFAULT_POOL))
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--analysis-only", action="store_true")
    return ap.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    out_root = Path(args.out_dir).resolve()
    if not args.analysis_only:
        run_extraction(args)
        if not args.full:
            return 0
    run_analysis(out_root)
    return 0


if __name__ == "__main__":
    sys.exit(main())
