#!/usr/bin/env python3
"""Amendment AG §9.4 — Neutral-prepend control (GPU extraction + analysis).

Lab-notebook diagnostic: no amendment, no gates.

PURPOSE
-------
§8 found caution-axis projection moves NEGATIVE under BOTH HIGH and LOW primes.
The red-team audit could not exclude a generic "prepending ANY sentence shifts
the anchor" artifact. This control closes that hypothesis by extracting the
pre-gen anchor under a SEMANTICALLY NEUTRAL prepended sentence and comparing
its Δcaution/Δdoubt against the HIGH and LOW cells.

NEUTRAL sentence (locked):
  "The following question was selected from a large general collection of
   questions for use in this study."
Prepended + single space before the byte-identical baseline system prompt,
exactly as amendment_ag_primed_extract.py does for HIGH/LOW.

PROCEDURE
---------
Part 1 – GPU extraction (mirrors amendment_ag_primed_extract.py exactly):
  - Load raw unsloth/Qwen3-4B-bnb-4bit (no adapter, native torch CUDA).
  - For all 600 AE pool rows, render with NEUTRAL prepended system prompt.
  - Capture hidden state at position prompt_len−1 for ALL layers.
  - Save per-row safetensors: L0..LN, float32, cpu contiguous.
  - Output: analysis/ag_neutral_pregen/neutral/<safe_key>__pre.safetensors
            analysis/ag_neutral_pregen/neutral/rows.jsonl
            analysis/ag_neutral_pregen/neutral/manifest.json
  - Manifests record the neutral sentence and its token count.

Part 2 – Analysis (mirrors amendment_ag_state_analysis.py exactly):
  - Refit doubt axis (AF L24 procedure, 5-fold CV rs=0); STOP if AUROC < 0.98.
  - Fit caution axis (refused-vs-answered on baseline tensors + AE census).
  - Project baseline/neutral tensors; compute Δ := proj(neutral) − proj(baseline)
    per row, z-scored by baseline SD.
  - Report mean Δdoubt and Δcaution for NEUTRAL with bootstrap 95% CIs (10k,
    seed 20260703), broken out by gold label (known/unknown).
  - Side-by-side with recomputed HIGH and LOW cells from existing tensors.

OUTPUTS
-------
  analysis/ag_neutral_pregen/neutral/<safe_key>__pre.safetensors  (600 files)
  analysis/ag_neutral_pregen/neutral/rows.jsonl
  analysis/ag_neutral_pregen/neutral/manifest.json
  analysis/ag_neutral_pregen/manifest.json                        (root)
  analysis/ag_neutral_pregen/ag_neutral_result.json               (final numbers)

Do NOT commit. The lead reviews scripts and results before any git operations.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import yaml

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
from path_compat import phase1_eval_dir, phase1_probe_dir  # noqa: E402

PROBE_DIR = phase1_probe_dir()
EVAL_DIR = phase1_eval_dir()
for p in (str(PROBE_DIR), str(EVAL_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

CANONICAL = Path("/home/profsynapse/code/Epistemic-Humility-Research")
WORKTREE  = Path("/home/profsynapse/code/ehr-worktrees/amendment-ag")

AF_PREGEN_DIR   = CANONICAL / "experiment/phase1/probe/analysis/af_base_pregen"
AG_HIGH_DIR     = WORKTREE  / "experiment/phase1/probe/analysis/ag_primed_pregen/high"
AG_LOW_DIR      = WORKTREE  / "experiment/phase1/probe/analysis/ag_primed_pregen/low"
AE_CENSUS_ROWS  = CANONICAL / "experiment/phase1/probe/analysis/ae_base_behavior_rows/rows.jsonl"
DEFAULT_POOL    = CANONICAL / "experiment/phase1/probe/analysis/ae_base_pool/rows.jsonl"
DEFAULT_OUT_ROOT = WORKTREE / "experiment/phase1/probe/analysis/ag_neutral_pregen"

AC_CONFIG = (
    PROBE_DIR.parents[2]
    / "experiments/doubt-regulated-caution/phase3_ac_doubt_coupled_intervention.yaml"
)

# ---------------------------------------------------------------------------
# Locked constants
# ---------------------------------------------------------------------------
NEUTRAL_SENTENCE = (
    "The following question was selected from a large general collection of "
    "questions for use in this study."
)
DOUBT_SANITY_FLOOR = 0.98
BOOTSTRAP_N = 10_000
BOOTSTRAP_SEED = 20260703
CV_RANDOM_STATE = 0
N_FOLDS = 5
TARGET_LAYER = "L24"

# ---------------------------------------------------------------------------
# Utilities (mirrored from amendment_ag_state_analysis.py)
# ---------------------------------------------------------------------------

def sha256_path(p: Path, nbytes: int = 65536) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        while chunk := fh.read(nbytes):
            h.update(chunk)
    return h.hexdigest()


def _config_sha(payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def load_jsonl(p: Path) -> list[dict]:
    return [json.loads(line) for line in p.open("r", encoding="utf-8") if line.strip()]


def load_layer_matrix(pregen_dir: Path, rows: list[dict], layer_key: str) -> np.ndarray:
    from safetensors.torch import load_file
    vecs = []
    for r in rows:
        safe_path = pregen_dir / f"{r['safe_key']}__pre.safetensors"
        t = load_file(str(safe_path))
        vecs.append(t[layer_key].numpy().astype(np.float64))
    return np.vstack(vecs)


def bootstrap_mean_ci(
    arr: np.ndarray, n: int = BOOTSTRAP_N, seed: int = BOOTSTRAP_SEED
) -> tuple[float, float, float]:
    rng = np.random.default_rng(seed)
    means = np.array([rng.choice(arr, size=len(arr), replace=True).mean()
                      for _ in range(n)])
    return float(arr.mean()), float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def auroc_score(y_true: np.ndarray, y_score: np.ndarray) -> float:
    from sklearn.metrics import roc_auc_score
    return float(roc_auc_score(y_true, y_score))


def fit_logistic_cv(X: np.ndarray, y: np.ndarray) -> tuple[float, np.ndarray]:
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import StratifiedKFold, cross_val_predict
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import roc_auc_score
    skf = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=CV_RANDOM_STATE)
    clf = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000, C=1.0))
    proba = cross_val_predict(clf, X, y, cv=skf, method="predict_proba")[:, 1]
    return float(roc_auc_score(y, proba)), proba


def fit_full(X: np.ndarray, y: np.ndarray):
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    clf = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000, C=1.0))
    clf.fit(X, y)
    return clf


def project(clf, X: np.ndarray) -> np.ndarray:
    return clf.decision_function(X)


def cell_stats(delta: np.ndarray, delta_z: np.ndarray, mask: np.ndarray, label: str) -> dict:
    d  = delta[mask]
    dz = delta_z[mask]
    mean_raw, lo_raw, hi_raw = bootstrap_mean_ci(d)
    mean_z,   lo_z,   hi_z  = bootstrap_mean_ci(dz)
    return {
        "cell": label,
        "n": int(mask.sum()),
        "mean_raw": mean_raw,
        "ci95_raw": [lo_raw, hi_raw],
        "mean_z": mean_z,
        "ci95_z": [lo_z, hi_z],
    }


# ---------------------------------------------------------------------------
# Part 1 — GPU Extraction
# ---------------------------------------------------------------------------

def load_baseline_system_prompt() -> str:
    with AC_CONFIG.open("r", encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    return cfg["prompt"]["system"]


def load_pool(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def run_extraction(args) -> dict:
    """GPU extraction pass. Returns manifest dict."""
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from safetensors.torch import save_file
    from backends import render_probe_prompt

    model_name = args.base_model or "unsloth/Qwen3-4B-bnb-4bit"
    model_tag  = "qwen3-4b-instruct"
    pool_path  = Path(args.pool).resolve()
    out_root   = Path(args.out_dir).resolve()
    out_dir    = out_root / "neutral"
    out_dir.mkdir(parents=True, exist_ok=True)

    baseline_system = load_baseline_system_prompt()
    neutral_system  = NEUTRAL_SENTENCE + " " + baseline_system

    pool = load_pool(pool_path)
    n_known   = sum(1 for r in pool if r["label"] == "known")
    n_unknown = sum(1 for r in pool if r["label"] == "unknown")

    config_payload = {
        "amendment": "AG",
        "section": "neutral_control",
        "stage": "neutral_pregen_extract",
        "base_model": model_name,
        "adapter": "NONE-raw-instruct-base",
        "model_tag": model_tag,
        "baseline_system_prompt": baseline_system,
        "neutral_sentence": NEUTRAL_SENTENCE,
        "pool_source": str(pool_path),
        "enable_thinking": False,
        "anchor_position": "prompt_len-1",
        "persist_dtype": "float32",
        "generation": "NONE-forward-only",
        "rendering": "neutral",
        "rendered_prompt_recipe": (
            "neutral_sentence + single_space + baseline_system_prompt"
        ),
    }
    cfg_sha = _config_sha(config_payload)

    print(f"[ag-neutral/extract] loading RAW base {model_name} (no adapter) ...",
          flush=True)
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name, torch_dtype=torch.bfloat16, device_map="cuda")
    model.eval()
    device = next(model.parameters()).device
    n_layers = model.config.num_hidden_layers

    # --- Token count diagnostic (record neutral vs HIGH vs LOW additions) ---
    # Tokenize a probe rendering with: (a) baseline, (b) neutral-prepended
    sample_q = pool[0]["question"]
    baseline_rendered, _ = render_probe_prompt(
        tokenizer, baseline_system, sample_q, enable_thinking=False)
    neutral_rendered, _  = render_probe_prompt(
        tokenizer, neutral_system,  sample_q, enable_thinking=False)
    baseline_tokens = len(tokenizer(baseline_rendered)["input_ids"])
    neutral_tokens  = len(tokenizer(neutral_rendered)["input_ids"])
    neutral_added   = neutral_tokens - baseline_tokens
    neutral_sentence_tokens = len(tokenizer(NEUTRAL_SENTENCE)["input_ids"])

    print(f"[ag-neutral/extract] neutral sentence: {neutral_sentence_tokens} tokens "
          f"(adds +{neutral_added} to rendered prompt vs baseline; "
          f"HIGH added +18, LOW added +22 per spec)",
          flush=True)

    print(f"[ag-neutral/extract] pool={len(pool)} (known={n_known} "
          f"unknown={n_unknown}) n_layers={n_layers}", flush=True)

    # --- Smoke: 6 rows ---
    if not args.full:
        smoke_rows = pool[:6]
        print(f"[ag-neutral/extract] SMOKE: running 6 rows ...", flush=True)
    else:
        smoke_rows = pool[:6]  # run smoke first, then full

    # --- Verify tensor contract against af_base_pregen ---
    from safetensors.torch import load_file as stl_load
    af_rows_sample = load_jsonl(AF_PREGEN_DIR / "rows.jsonl")[:1]
    af_sample_t = stl_load(str(AF_PREGEN_DIR / f"{af_rows_sample[0]['safe_key']}__pre.safetensors"))
    af_sample_keys = set(af_sample_t.keys())
    expected_keys  = {f"L{i}" for i in range(n_layers + 1)}
    if af_sample_keys != expected_keys:
        print(f"[ag-neutral/extract] CONTRACT MISMATCH: AF has {sorted(af_sample_keys)[:5]}... "
              f"expected {sorted(expected_keys)[:5]}...", flush=True)
        sys.exit(2)
    print(f"[ag-neutral/extract] tensor contract verified: keys L0..L{n_layers} "
          f"(matches af_base_pregen)", flush=True)

    rows_path = out_dir / "rows.jsonl"
    written   = 0
    rows_to_run = pool if args.full else smoke_rows

    with rows_path.open("w", encoding="utf-8") as rows_fh:
        for item in rows_to_run:
            row_key = item["row_key"]
            rendered, _mode = render_probe_prompt(
                tokenizer, neutral_system, item["question"], enable_thinking=False)
            enc = tokenizer(rendered, return_tensors="pt").to(device)
            prompt_len = int(enc["input_ids"].shape[1])

            # Smoke: verify neutral prompt renders as specified
            if written < 6:
                assert NEUTRAL_SENTENCE in rendered, (
                    f"SMOKE FAIL: neutral sentence not found in rendered prompt "
                    f"for row {row_key}")
                assert baseline_system in rendered, (
                    f"SMOKE FAIL: baseline system prompt not found in rendered prompt "
                    f"for row {row_key}")
                # Verify neutral appears BEFORE baseline in the rendered string
                assert rendered.index(NEUTRAL_SENTENCE) < rendered.index(baseline_system), (
                    f"SMOKE FAIL: neutral sentence does not precede baseline system "
                    f"in rendered prompt for row {row_key}")
                print(f"[ag-neutral/extract] SMOKE row {written+1}: "
                      f"prompt_len={prompt_len} OK (neutral before baseline ✓)",
                      flush=True)

            import torch
            with torch.no_grad():
                out = model(**enc, output_hidden_states=True, use_cache=False)
            hs = out.hidden_states
            pre_tensors = {
                f"L{li}": hs[li][0, prompt_len - 1, :].float().cpu().contiguous()
                for li in range(len(hs))
            }

            # Verify output tensor count matches contract
            if written == 0:
                got_keys = set(pre_tensors.keys())
                if got_keys != expected_keys:
                    print(f"[ag-neutral/extract] OUTPUT MISMATCH: got {sorted(got_keys)[:5]}... "
                          f"expected {sorted(expected_keys)[:5]}...", flush=True)
                    sys.exit(2)
                print(f"[ag-neutral/extract] output tensor contract verified: "
                      f"{len(got_keys)} keys", flush=True)

            safe_key = row_key.replace("::", "__").replace("|", "_")
            save_file(pre_tensors, str(out_dir / f"{safe_key}__pre.safetensors"))

            rows_fh.write(json.dumps({
                "row_key":   row_key,
                "label":     item["label"],
                "question":  item["question"],
                "prompt_len": prompt_len,
                "safe_key":  safe_key,
                "rendering": "neutral",
                "config_sha": cfg_sha,
            }, ensure_ascii=False) + "\n")
            rows_fh.flush()
            written += 1
            if written % 50 == 0:
                print(f"[ag-neutral/extract] rows={written}/{len(rows_to_run)}",
                      flush=True)

    manifest = {
        **config_payload,
        "config_sha": cfg_sha,
        "n_layers":   n_layers,
        "hidden_dim": model.config.hidden_size,
        "n_pool":     len(pool),
        "n_known":    n_known,
        "n_unknown":  n_unknown,
        "n_written":  written,
        "out_dir":    str(out_dir),
        "position":   "pre",
        "tensor_layer_keys": f"L0..L{n_layers}",
        "neutral_sentence": NEUTRAL_SENTENCE,
        "neutral_sentence_tokens": neutral_sentence_tokens,
        "neutral_added_tokens_vs_baseline": neutral_added,
        "high_added_tokens_vs_baseline": 18,
        "low_added_tokens_vs_baseline":  22,
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    root_manifest = {
        **config_payload,
        "config_sha": cfg_sha,
        "n_pool":     len(pool),
        "n_known":    n_known,
        "n_unknown":  n_unknown,
        "n_written":  written,
        "out_root":   str(out_root),
        "neutral_sentence_tokens": neutral_sentence_tokens,
        "neutral_added_tokens_vs_baseline": neutral_added,
        "high_added_tokens_vs_baseline": 18,
        "low_added_tokens_vs_baseline":  22,
    }
    (out_root / "manifest.json").write_text(
        json.dumps(root_manifest, indent=2), encoding="utf-8")

    if not args.full:
        print(f"[ag-neutral/extract] SMOKE complete: {written} rows -> {out_dir}",
              flush=True)
        print(f"[ag-neutral/extract] Re-run with --full for 600 rows.", flush=True)
    else:
        print(f"[ag-neutral/extract] DONE: {written} rows -> {out_dir}", flush=True)

    # Free GPU memory before analysis
    del model
    import torch
    torch.cuda.empty_cache()

    return manifest


# ---------------------------------------------------------------------------
# Part 2 — Analysis
# ---------------------------------------------------------------------------

def run_analysis(out_root: Path) -> dict:
    """Refit axes, project neutral/high/low, compute Δ, write result JSON.

    Mirrors amendment_ag_state_analysis.py exactly for the axis-fitting and
    projection logic; extends it with the NEUTRAL column.
    """
    neutral_dir = out_root / "neutral"
    result_path = out_root / "ag_neutral_result.json"

    af_rows  = load_jsonl(AF_PREGEN_DIR / "rows.jsonl")
    manifest = json.loads((AF_PREGEN_DIR / "manifest.json").read_text())
    n_layers = manifest["n_layers"]
    print(f"[ag-neutral/analysis] af_rows={len(af_rows)} n_layers={n_layers}", flush=True)

    ae_rows_list = load_jsonl(AE_CENSUS_ROWS)
    ae_by_key    = {r["row_key"]: r for r in ae_rows_list}

    y_caution = np.zeros(len(af_rows), dtype=int)
    for i, r in enumerate(af_rows):
        ae = ae_by_key.get(r["row_key"])
        if ae is None:
            raise ValueError(f"Row {r['row_key']} not in AE census")
        y_caution[i] = 1 if ae.get("refused", False) else 0

    y_doubt = np.array(
        [1 if r["label"] == "known" else 0 for r in af_rows], dtype=int)

    # ------------------------------------------------------------------
    # STEP 1: Doubt axis — refit L24 (5-fold CV, same as AG state script)
    # ------------------------------------------------------------------
    print(f"[ag-neutral/analysis] Step 1: loading L24 baseline matrix...", flush=True)
    X_base_L24 = load_layer_matrix(AF_PREGEN_DIR, af_rows, TARGET_LAYER)
    print(f"[ag-neutral/analysis] L24 shape: {X_base_L24.shape}", flush=True)

    doubt_cv_auroc, _ = fit_logistic_cv(X_base_L24, y_doubt)
    print(f"[ag-neutral/analysis] Doubt L24 heldout AUROC: {doubt_cv_auroc:.6f}", flush=True)

    if doubt_cv_auroc < DOUBT_SANITY_FLOOR:
        result = {
            "amendment": "AG",
            "section": "neutral_control",
            "status": "STOP",
            "reason": f"Doubt AUROC {doubt_cv_auroc:.6f} < floor {DOUBT_SANITY_FLOOR}",
        }
        result_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print("[ag-neutral/analysis] STOP: doubt sanity floor failed.", flush=True)
        sys.exit(1)

    doubt_clf       = fit_full(X_base_L24, y_doubt)
    doubt_proj_base = project(doubt_clf, X_base_L24)

    mean_known   = float(doubt_proj_base[y_doubt == 1].mean())
    mean_unknown = float(doubt_proj_base[y_doubt == 0].mean())
    doubt_sign_flipped = False
    if mean_known < mean_unknown:
        doubt_proj_base = -doubt_proj_base
        mean_known, mean_unknown = -mean_known, -mean_unknown
        doubt_sign_flipped = True
        print("[ag-neutral/analysis] Doubt axis sign FLIPPED", flush=True)

    doubt_base_sd = float(doubt_proj_base.std())

    # ------------------------------------------------------------------
    # STEP 2: Caution axis — L24 (same as AG state script, no full sweep)
    # ------------------------------------------------------------------
    print(f"[ag-neutral/analysis] Step 2: fitting caution axis at L24...", flush=True)
    caution_clf_L24      = fit_full(X_base_L24, y_caution)
    caution_proj_L24_base = project(caution_clf_L24, X_base_L24)
    caution_cv_auroc, _  = fit_logistic_cv(X_base_L24, y_caution)

    mean_refused  = float(caution_proj_L24_base[y_caution == 1].mean())
    mean_answered = float(caution_proj_L24_base[y_caution == 0].mean())
    caution_sign_flipped_L24 = False
    if mean_refused < mean_answered:
        caution_proj_L24_base = -caution_proj_L24_base
        mean_refused, mean_answered = -mean_refused, -mean_answered
        caution_sign_flipped_L24 = True

    caution_base_sd_L24 = float(caution_proj_L24_base.std())

    # ------------------------------------------------------------------
    # STEP 3: Load NEUTRAL tensors; compute projections at L24
    # ------------------------------------------------------------------
    print(f"[ag-neutral/analysis] Step 3: loading neutral tensors at L24...", flush=True)
    neutral_rows = load_jsonl(neutral_dir / "rows.jsonl")

    assert len(neutral_rows) == len(af_rows), (
        f"Neutral rows count {len(neutral_rows)} != af_rows {len(af_rows)}")
    assert [r["row_key"] for r in neutral_rows] == [r["row_key"] for r in af_rows], \
        "Neutral rows order mismatch vs af_rows"

    X_neutral_L24 = load_layer_matrix(neutral_dir, neutral_rows, TARGET_LAYER)

    doubt_proj_neutral  = project(doubt_clf, X_neutral_L24)
    if doubt_sign_flipped:
        doubt_proj_neutral = -doubt_proj_neutral

    caution_proj_neutral = project(caution_clf_L24, X_neutral_L24)
    if caution_sign_flipped_L24:
        caution_proj_neutral = -caution_proj_neutral

    delta_doubt_neutral   = doubt_proj_neutral   - doubt_proj_base
    delta_caution_neutral = caution_proj_neutral - caution_proj_L24_base

    delta_doubt_neutral_z   = delta_doubt_neutral   / doubt_base_sd
    delta_caution_neutral_z = delta_caution_neutral / caution_base_sd_L24

    # ------------------------------------------------------------------
    # STEP 4: Load HIGH and LOW tensors; compute Δ (recomputed identically
    #         to amendment_ag_state_analysis.py for exact side-by-side)
    # ------------------------------------------------------------------
    print(f"[ag-neutral/analysis] Step 4: loading HIGH/LOW tensors at L24...", flush=True)
    high_rows = load_jsonl(AG_HIGH_DIR / "rows.jsonl")
    low_rows  = load_jsonl(AG_LOW_DIR  / "rows.jsonl")

    assert [r["row_key"] for r in high_rows] == [r["row_key"] for r in af_rows], \
        "HIGH rows order mismatch"
    assert [r["row_key"] for r in low_rows]  == [r["row_key"] for r in af_rows], \
        "LOW rows order mismatch"

    X_high_L24 = load_layer_matrix(AG_HIGH_DIR, high_rows, TARGET_LAYER)
    X_low_L24  = load_layer_matrix(AG_LOW_DIR,  low_rows,  TARGET_LAYER)

    doubt_proj_high = project(doubt_clf, X_high_L24)
    doubt_proj_low  = project(doubt_clf, X_low_L24)
    if doubt_sign_flipped:
        doubt_proj_high = -doubt_proj_high
        doubt_proj_low  = -doubt_proj_low

    caution_proj_L24_high = project(caution_clf_L24, X_high_L24)
    caution_proj_L24_low  = project(caution_clf_L24, X_low_L24)
    if caution_sign_flipped_L24:
        caution_proj_L24_high = -caution_proj_L24_high
        caution_proj_L24_low  = -caution_proj_L24_low

    delta_doubt_high   = doubt_proj_high   - doubt_proj_base
    delta_doubt_low    = doubt_proj_low    - doubt_proj_base
    delta_caution_high = caution_proj_L24_high - caution_proj_L24_base
    delta_caution_low  = caution_proj_L24_low  - caution_proj_L24_base

    delta_doubt_high_z   = delta_doubt_high   / doubt_base_sd
    delta_doubt_low_z    = delta_doubt_low    / doubt_base_sd
    delta_caution_high_z = delta_caution_high / caution_base_sd_L24
    delta_caution_low_z  = delta_caution_low  / caution_base_sd_L24

    # ------------------------------------------------------------------
    # STEP 5: 2×3 tables (gold label × neutral/HIGH/LOW)
    # ------------------------------------------------------------------
    print(f"[ag-neutral/analysis] Step 5: building 2×3 cell tables...", flush=True)

    known_mask   = (y_doubt == 1)
    unknown_mask = (y_doubt == 0)

    def build_table(
        delta_n, delta_n_z, delta_h, delta_h_z, delta_l, delta_l_z
    ) -> dict:
        return {
            "NEUTRAL_on_known":   cell_stats(delta_n, delta_n_z, known_mask,   "NEUTRAL×known"),
            "NEUTRAL_on_unknown": cell_stats(delta_n, delta_n_z, unknown_mask, "NEUTRAL×unknown"),
            "HIGH_on_known":      cell_stats(delta_h, delta_h_z, known_mask,   "HIGH×known"),
            "HIGH_on_unknown":    cell_stats(delta_h, delta_h_z, unknown_mask, "HIGH×unknown"),
            "LOW_on_known":       cell_stats(delta_l, delta_l_z, known_mask,   "LOW×known"),
            "LOW_on_unknown":     cell_stats(delta_l, delta_l_z, unknown_mask, "LOW×unknown"),
        }

    doubt_table   = build_table(
        delta_doubt_neutral,   delta_doubt_neutral_z,
        delta_doubt_high,      delta_doubt_high_z,
        delta_doubt_low,       delta_doubt_low_z,
    )
    caution_table = build_table(
        delta_caution_neutral, delta_caution_neutral_z,
        delta_caution_high,    delta_caution_high_z,
        delta_caution_low,     delta_caution_low_z,
    )

    # ------------------------------------------------------------------
    # Assemble result
    # ------------------------------------------------------------------
    neutral_manifest = json.loads((out_root / "manifest.json").read_text())

    result = {
        "amendment": "AG",
        "section": "neutral_prepend_control",
        "bootstrap_n": BOOTSTRAP_N,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "cv_random_state": CV_RANDOM_STATE,
        "n_folds": N_FOLDS,
        "target_layer": TARGET_LAYER,
        "neutral_sentence": NEUTRAL_SENTENCE,
        "token_counts": {
            "neutral_sentence_tokens": neutral_manifest.get("neutral_sentence_tokens"),
            "neutral_added_tokens_vs_baseline": neutral_manifest.get("neutral_added_tokens_vs_baseline"),
            "high_added_tokens_vs_baseline": 18,
            "low_added_tokens_vs_baseline":  22,
        },
        "doubt_axis": {
            "cv_auroc_L24": doubt_cv_auroc,
            "sanity_floor": DOUBT_SANITY_FLOOR,
            "sanity_check": "PASS",
            "sign_flipped": doubt_sign_flipped,
            "base_proj_sd": doubt_base_sd,
            "mean_proj_known": mean_known,
            "mean_proj_unknown": mean_unknown,
        },
        "caution_axis_L24": {
            "cv_auroc_L24": caution_cv_auroc,
            "sign_flipped": caution_sign_flipped_L24,
            "base_proj_sd": caution_base_sd_L24,
            "mean_proj_refused": mean_refused,
            "mean_proj_answered": mean_answered,
        },
        "delta_doubt_2x3_table": doubt_table,
        "delta_caution_2x3_table": caution_table,
        "artifact_paths": {
            "neutral_dir": str(neutral_dir),
            "af_pregen_dir": str(AF_PREGEN_DIR),
            "ag_high_dir": str(AG_HIGH_DIR),
            "ag_low_dir": str(AG_LOW_DIR),
            "ae_census_rows": str(AE_CENSUS_ROWS),
        },
        "artifact_shas": {
            "af_pregen_rows": sha256_path(AF_PREGEN_DIR / "rows.jsonl"),
            "ae_census_rows": sha256_path(AE_CENSUS_ROWS),
            "neutral_rows": sha256_path(neutral_dir / "rows.jsonl"),
        },
    }

    out_root.mkdir(parents=True, exist_ok=True)
    result_path.write_text(json.dumps(result, indent=2, allow_nan=False),
                           encoding="utf-8")
    print(f"\n[ag-neutral/analysis] Written: {result_path}", flush=True)
    return result


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", default=str(DEFAULT_OUT_ROOT),
                    help="Root output directory (default: worktree ag_neutral_pregen/)")
    ap.add_argument("--base-model", default=None,
                    help="Raw Instruct base (default unsloth/Qwen3-4B-bnb-4bit); NO adapter")
    ap.add_argument("--pool", default=str(DEFAULT_POOL))
    ap.add_argument("--full", action="store_true",
                    help="Run all 600 rows (omit for smoke-only: 6 rows)")
    ap.add_argument("--analysis-only", action="store_true",
                    help="Skip extraction, run analysis on existing neutral tensors")
    return ap.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    out_root = Path(args.out_dir).resolve()

    if not args.analysis_only:
        manifest = run_extraction(args)
        print(f"[ag-neutral] Extraction complete: {manifest['n_written']} rows", flush=True)
        if not args.full:
            print("[ag-neutral] SMOKE PASS — re-run with --full for 600-row pass + analysis",
                  flush=True)
            return 0

    # Analysis requires the full neutral pass to be complete
    neutral_rows_path = out_root / "neutral" / "rows.jsonl"
    if not neutral_rows_path.exists():
        print(f"[ag-neutral] ERROR: neutral rows not found at {neutral_rows_path}; "
              f"run extraction first", flush=True)
        return 1

    n_rows = sum(1 for l in neutral_rows_path.open() if l.strip())
    if n_rows < 600:
        print(f"[ag-neutral] WARNING: only {n_rows}/600 neutral rows present; "
              f"analysis may be partial", flush=True)

    result = run_analysis(out_root)

    # ------------------------------------------------------------------
    # Print plain-numbers report for the lead
    # ------------------------------------------------------------------
    print("\n" + "="*72, flush=True)
    print("AG §9.4 NEUTRAL-PREPEND CONTROL — RESULT SUMMARY", flush=True)
    print("="*72, flush=True)

    tc = result["token_counts"]
    print(f"\nToken counts:", flush=True)
    print(f"  Neutral sentence:          {tc['neutral_sentence_tokens']} tokens", flush=True)
    print(f"  Neutral adds vs baseline:  +{tc['neutral_added_tokens_vs_baseline']}", flush=True)
    print(f"  HIGH adds vs baseline:     +{tc['high_added_tokens_vs_baseline']}", flush=True)
    print(f"  LOW adds vs baseline:      +{tc['low_added_tokens_vs_baseline']}", flush=True)

    da = result["doubt_axis"]
    ca = result["caution_axis_L24"]
    print(f"\nAxis sanity (L24):", flush=True)
    print(f"  Doubt  AUROC: {da['cv_auroc_L24']:.4f} (floor {da['sanity_floor']})", flush=True)
    print(f"  Caution AUROC: {ca['cv_auroc_L24']:.4f}", flush=True)

    def fmt_cell(c: dict) -> str:
        return (f"n={c['n']:3d}  mean_z={c['mean_z']:+.3f}  "
                f"CI=[{c['ci95_z'][0]:+.3f},{c['ci95_z'][1]:+.3f}]")

    print("\nΔcaution 2×3 table (z-scored by baseline SD, L24):", flush=True)
    for key, cell in result["delta_caution_2x3_table"].items():
        print(f"  {key:25s}  {fmt_cell(cell)}", flush=True)

    print("\nΔdoubt 2×3 table (z-scored by baseline SD, L24):", flush=True)
    for key, cell in result["delta_doubt_2x3_table"].items():
        print(f"  {key:25s}  {fmt_cell(cell)}", flush=True)

    print(f"\nResult JSON: {result['artifact_paths']['neutral_dir']}/../ag_neutral_result.json",
          flush=True)
    print("="*72, flush=True)

    return 0


if __name__ == "__main__":
    sys.exit(main())
