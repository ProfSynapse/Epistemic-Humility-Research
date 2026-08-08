#!/usr/bin/env python3
"""Clean-subset (decontaminated) sensitivity for paper 4's deployed-checkpoint
quantities whose contrast touches the SelfAware known/answerable side.

CONTEXT: `experiments/grpo-three-seed-confirmatory/NOTEBOOK.md` (2026-08-07
"RED-TEAM PASS COMPLETE" + 2026-08-07 "POST-RESOLUTION ADDENDUM") found 128
distinct SelfAware known (answerable) eval questions leaking into the
response-confidence training pipeline for the `clean_sft_grpo_v2` lineage: 117
appear verbatim as user-turn training prompts across SFT/DPO/KTO/GRPO train
files (gradient exposure), plus 11 additional questions that leak only into
`grpo_dev.jsonl` (checkpoint-selection exposure). ALL 128 are label=known,
ZERO are label=unknown.

Amendment U (`experiments/unified-two-signal-dial-veto/AMENDMENT.md`) probes
the qwen3-4b clean-SFT-merged + GRPO-v2-LoRA checkpoint -- confirmed here to
be the IDENTICAL checkpoint as the grpo-three-seed-confirmatory block's seed-1
`clean_sft_grpo_v2` arm (manifest `aligned_run_record_id` /
`adapter_path` both point at
`schema_clean_sft_grpo_v2_seed1_full/20260624_095831/final_model`), trained on
the SAME dataset files the contamination set above was derived from. So the
same 128-question exclusion set applies directly to Amendment U's SelfAware
pool.

This script recomputes, on the FULL population (must reproduce the pinned
values) and on the CLEAN (decontaminated) subset:

  1. U-G1 gate-confirm AUROC (within-SelfAware known-vs-unknown, U pre-gen
     anchor, best layer) -- AMENDMENT.md section 7 reports 0.999 (L33). Its
     397-row population (276 known-answered + 121 hallucination) is only the
     ANSWERED rows (the extraction stores pre-gen anchors for answered rows
     only); contamination can only touch the known-answered side (121
     hallucination rows are all label=unknown, structurally immune, per the
     same logic as the grpo-three-seed block's G1).

  2. The within-SelfAware control AUROC(known-answered vs hallucination),
     dial score, T-fit L22 dial applied cold -- manuscript section 4.3 /
     Limitation 5 cites three values from
     `experiments/unified-two-signal-dial-veto/analysis-committed/ug3_corrected_rescore.json`:
       - reported pre-correction, vs the FULL 121-row hallucination set: 0.93
       - vs Set A (12, both-detector-answered): 0.8140
       - vs Set B (8, census-corrected: Set A minus 4 rows of one refusal
         template BOTH detectors miss): 0.7369
       - "fully corrected" (Set B hallucination side AND 270 known-answered,
         i.e. also dropping 6 known-answered rows the WIDE detector re-grades
         as refusals): 0.7500
     Set A is independently reproducible from the pinned row-level audit
     `experiments/unified-two-signal-dial-veto/analysis/detector_flip_rate_rows.jsonl`
     (deterministic: unknown-label rows the narrow detector calls answered
     AND the wide detector also calls answered). The 6 wide-flipped
     known-answered rows are likewise reproducible from that same file.
     Set B's additional 4-row exclusion is NOT reproducible here: it came
     from a manual census (AMENDMENT.md corrigendum, "found zero
     hedge-plus-guess rows ... one verbatim trained refusal template") whose
     row identities are not recorded in any pinned, checked-in script or
     artifact on this disk (`ug3_corrected_rescore.py` is gitignored and
     absent). This script computes the reproducible combinations (full
     121-row halluc set, and Set A) and reports Set B / fully-corrected as
     NOT INDEPENDENTLY RECOMPUTABLE, citing the manuscript's own numbers only
     for those two rows.

Row text (questions, prompts, answers) is READ locally to compute
contamination membership and row-group identity, but this script prints and
returns aggregates ONLY -- counts, metric names, layer indices, AUROCs, CIs,
paths. No question text, prompt text, or answer text is ever printed or
written. The repo is public; keep it that way.

Usage:
    python3 papers/paper-4-two-signal-readout/analysis/clean_subset_sensitivity_p4.py
Run from the canonical checkout (/home/profsynapse/code/Epistemic-Humility-Research).
CPU only. No GPU, no generation -- reads existing extracted tensors and refits
CPU logistic-regression probes exactly as the pinned amendment scripts do.
"""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

import numpy as np
from safetensors.numpy import load_file
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score

def _find_repo_root() -> Path:
    """This script lives in the paper-4 worktree, but the extraction tensors,
    stage2 rows, and training data it reads are gitignored local artifacts
    that only exist on the canonical checkout. Resolve REPO_ROOT by looking
    for those artifact markers, in order: cwd, this file's own tree, then the
    documented canonical checkout path (see project CLAUDE.md)."""
    marker = Path("archive/experiment/phase1-data/probe/qwen3-4b-clean-sft-grpo-v2/amendment_u/stage2/rows.jsonl")
    candidates = [Path.cwd(), *Path(__file__).resolve().parents,
                  Path("/home/profsynapse/code/Epistemic-Humility-Research")]
    for cand in candidates:
        if (cand / marker).exists():
            return cand
    raise SystemExit(
        "Could not locate a checkout with the gitignored Amendment U/T artifacts on disk. "
        "Run from the canonical checkout (/home/profsynapse/code/Epistemic-Humility-Research)."
    )


REPO_ROOT = _find_repo_root()
OUT_CSV = Path(__file__).resolve().parent / "clean_subset_sensitivity_p4.csv"

SCRATCH_DIR = REPO_ROOT / "scratch" / "schema_response_confidence"
DATASET_FILES: list[tuple[str, Path, str]] = [
    ("sft_clean_train", SCRATCH_DIR / "qwen3-4b-instruct" / "sft_response_confidence_train_clean.jsonl", "messages"),
    ("dpo_train", SCRATCH_DIR / "qwen3-4b-instruct" / "dpo_response_confidence_train.jsonl", "prompt"),
    ("kto_train", SCRATCH_DIR / "qwen3-4b-instruct" / "kto_response_confidence_train.jsonl", "conversations"),
    ("grpo_train", SCRATCH_DIR / "qwen3-4b-instruct-grpo" / "grpo_train.jsonl", "prompt"),
]
GRPO_DEV_FILE = SCRATCH_DIR / "qwen3-4b-instruct-grpo" / "grpo_dev.jsonl"

U_STAGE2_DIR = (REPO_ROOT / "archive" / "experiment" / "phase1-data" / "probe"
                / "qwen3-4b-clean-sft-grpo-v2" / "amendment_u" / "stage2")
T_STAGE2_DIR = (REPO_ROOT / "archive" / "experiment" / "phase1-data" / "probe"
                / "qwen3-4b-clean-sft-grpo-v2" / "amendment_t" / "stage2")
FLIP_ROWS = (REPO_ROOT / "experiments" / "unified-two-signal-dial-veto"
             / "analysis" / "detector_flip_rate_rows.jsonl")
UG3_RESCORE_JSON = (REPO_ROOT / "experiments" / "unified-two-signal-dial-veto"
                     / "analysis-committed" / "ug3_corrected_rescore.json")

DIAL_LAYER = 22          # Amendment T best post layer (locked, AMENDMENT.md / amendment_u_two_signal_score.py default)
GATE_HEADLINE_LAYER = 33  # AMENDMENT.md section 7 reported U-G1 best layer
SCORE_SEED = 20260630     # amendment_u_two_signal_score.py default seed (probe fits)
BOOT_SEED = 20260718      # ug3_corrected_rescore.py seed (bootstrap CIs), reused here for consistency
N_BOOT = 10000


def normq(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def iter_jsonl(path: Path):
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


def user_contents(record: dict, field: str) -> list[str]:
    out = []
    for msg in record.get(field, []) or []:
        if isinstance(msg, dict) and msg.get("role") == "user":
            content = msg.get("content")
            if isinstance(content, str):
                out.append(content)
    return out


def build_contamination_sets() -> tuple[set[str], set[str]]:
    """Return (gradient_117, union_128) sets of normalized contaminated known questions.

    Method identical to experiments/grpo-three-seed-confirmatory/analysis/clean_subset_sensitivity.py:
    normalized exact match of eval-question text against user-turn content of
    the training files. We don't have the eval population's own label here
    (that's supplied separately by the U stage2 rows), so this just collects
    the raw normalized user-turn text per file; overlap against U's known
    questions is computed by the caller.
    """
    gradient_norms: set[str] = set()
    for _label, path, field in DATASET_FILES:
        if not path.exists():
            raise SystemExit(f"missing required training file: {path}")
        for rec in iter_jsonl(path):
            for content in user_contents(rec, field):
                gradient_norms.add(normq(content))
    dev_norms: set[str] = set()
    if GRPO_DEV_FILE.exists():
        for rec in iter_jsonl(GRPO_DEV_FILE):
            for content in user_contents(rec, "prompt"):
                dev_norms.add(normq(content))
    else:
        print(f"[warn] grpo_dev file missing at {GRPO_DEV_FILE}; 128-union will equal gradient-only set")
    return gradient_norms, gradient_norms | dev_norms


def load_u_rows() -> list[dict]:
    rows = list(iter_jsonl(U_STAGE2_DIR / "rows.jsonl"))
    assert len(rows) == 1233, f"expected 1233 U stage2 rows, found {len(rows)}"
    return rows


def load_flip_rows() -> dict[str, dict]:
    rows = list(iter_jsonl(FLIP_ROWS))
    assert len(rows) == 1233, f"expected 1233 flip-audit rows, found {len(rows)}"
    return {r["row_key"]: r for r in rows}


def load_position_vectors(ext_dir: Path, row_keys: list[str], position: str) -> dict[int, np.ndarray]:
    """Load stacked [n, d] vectors per layer for exactly the given row_keys, in order."""
    by_layer: dict[int, list[np.ndarray]] = {}
    for rk in row_keys:
        safe = str(rk).replace("::", "__").replace("|", "_")
        shard = ext_dir / f"{safe}__{position}.safetensors"
        if not shard.exists():
            raise SystemExit(f"missing shard for row_key under {ext_dir}: {position}")
        t = load_file(str(shard))
        for name, vec in t.items():
            by_layer.setdefault(int(name[1:]), []).append(np.asarray(vec, dtype=np.float64))
    return {layer: np.vstack(vs) for layer, vs in by_layer.items()}


def oof_probe(X: np.ndarray, y: np.ndarray, seed: int) -> np.ndarray:
    """Verbatim recipe from experiments/common/readouts/amendment_s_correctness_probe_score.py."""
    p = np.full(len(y), np.nan)
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=seed)
    for tr, te in skf.split(X, y):
        sc = StandardScaler().fit(X[tr])
        clf = LogisticRegression(C=1.0, max_iter=2000)
        clf.fit(sc.transform(X[tr]), y[tr])
        p[te] = clf.predict_proba(sc.transform(X[te]))[:, 1]
    assert not np.isnan(p).any()
    return p


def boot_auroc_ci(y: np.ndarray, score: np.ndarray, n_boot: int, seed: int) -> dict:
    rng = np.random.default_rng(seed)
    n = len(y)
    a = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, size=n)
        if len(np.unique(y[idx])) < 2:
            continue
        a.append(roc_auc_score(y[idx], score[idx]))
    a = np.asarray(a)
    return {"auroc": float(roc_auc_score(y, score)), "ci_lo": float(np.percentile(a, 2.5)),
            "ci_hi": float(np.percentile(a, 97.5)), "n_boot": int(len(a))}


def fit_dial(t_rows: list[dict]):
    """Full-fit (not OOF) StandardScaler + LogisticRegression on ALL T post vectors
    at DIAL_LAYER -- identical recipe to amendment_u_two_signal_score.py's `dial()`,
    used for COLD application to U (U items are external to the T fit)."""
    labeled = [r for r in t_rows if r.get("label") in ("correct", "wrong")]
    row_keys = [r["row_key"] for r in labeled]
    y = np.asarray([1 if r["label"] == "correct" else 0 for r in labeled], dtype=int)
    X_by_layer = load_position_vectors(T_STAGE2_DIR, row_keys, "post")
    X = X_by_layer[DIAL_LAYER]
    assert X.shape[0] == 1488 == (988 + 500), f"unexpected T row count {X.shape[0]}"
    scaler = StandardScaler().fit(X)
    clf = LogisticRegression(C=1.0, max_iter=2000)
    clf.fit(scaler.transform(X), y)
    return scaler, clf


def dial_scores(scaler, clf, row_keys: list[str]) -> np.ndarray:
    if not row_keys:
        return np.array([])
    X_by_layer = load_position_vectors(U_STAGE2_DIR, row_keys, "post")
    X = X_by_layer[DIAL_LAYER]
    return clf.predict_proba(scaler.transform(X))[:, 1]


def gate_auroc_at_layer(row_keys: list[str], y: np.ndarray, layer: int, seed: int) -> tuple[float, np.ndarray]:
    X_by_layer = load_position_vectors(U_STAGE2_DIR, row_keys, "pre")
    p = oof_probe(X_by_layer[layer], y, seed)
    return float(roc_auc_score(y, p)), p


def main() -> None:
    u_rows = load_u_rows()
    flip = load_flip_rows()

    known_answered = [r for r in u_rows if r["label"] == "known" and r.get("outcome") == "answerable_attempt"]
    hallucination = [r for r in u_rows if r["label"] == "unknown" and r.get("outcome") == "hallucination"]
    assert len(known_answered) == 276, len(known_answered)
    assert len(hallucination) == 121, len(hallucination)

    ka_keys_full = [r["row_key"] for r in known_answered]
    halluc_keys_full = [r["row_key"] for r in hallucination]

    # --- contamination set -------------------------------------------------
    gradient_117, union_128 = build_contamination_sets()
    print("=" * 78)
    print("CONTAMINATION SET (reused method: experiments/grpo-three-seed-confirmatory/"
          "analysis/clean_subset_sensitivity.py normq exact match)")
    print("=" * 78)
    print(f"training files: {[str(p.relative_to(REPO_ROOT)) for _, p, _ in DATASET_FILES]}")
    print(f"grpo_dev file: {GRPO_DEV_FILE.relative_to(REPO_ROOT)} (exists={GRPO_DEV_FILE.exists()})")

    ka_norms = {r["row_key"]: normq(r["question"]) for r in known_answered}
    contam_117 = {rk for rk, qn in ka_norms.items() if qn in gradient_117}
    contam_128 = {rk for rk, qn in ka_norms.items() if qn in union_128}
    print(f"known-answered rows (n={len(known_answered)}) contaminated under gradient-117 set: {len(contam_117)}")
    print(f"known-answered rows (n={len(known_answered)}) contaminated under 128-union set: {len(contam_128)}")
    print("hallucination rows (n=121, label=unknown): structurally immune (contamination set is 100% known)")
    print("PRIMARY CONVENTION USED BELOW: 128-union (matches the block's documented convention)")

    ka_keys_clean = [rk for rk in ka_keys_full if rk not in contam_128]
    n_excluded_ka = len(ka_keys_full) - len(ka_keys_clean)

    # --- detector flip-rate audit (Set A, 6 wide-flipped known) -------------
    set_a_keys = [rk for rk in halluc_keys_full if flip[rk]["wide_answered"]]
    assert len(set_a_keys) == 12, len(set_a_keys)
    wide_flipped_known_keys = {rk for rk in ka_keys_full if flip[rk]["wide_refused"]}
    assert len(wide_flipped_known_keys) == 6, len(wide_flipped_known_keys)
    ka_keys_wide270 = [rk for rk in ka_keys_full if rk not in wide_flipped_known_keys]
    ka_keys_clean_wide = [rk for rk in ka_keys_clean if rk not in wide_flipped_known_keys]

    rows_out: list[dict] = []

    # =====================================================================
    # 1. U-G1 gate confirm AUROC (within-SelfAware known-vs-unknown, U pre-gen)
    # =====================================================================
    print()
    print("=" * 78)
    print("U-G1 GATE CONFIRM (within-SelfAware known-vs-unknown, U pre-gen anchor)")
    print("=" * 78)
    y_full = np.concatenate([np.ones(len(ka_keys_full)), np.zeros(len(halluc_keys_full))])
    keys_full_g1 = ka_keys_full + halluc_keys_full
    auroc_full_l33, _ = gate_auroc_at_layer(keys_full_g1, y_full, GATE_HEADLINE_LAYER, SCORE_SEED)
    print(f"FULL population n={len(keys_full_g1)} (known={len(ka_keys_full)}, unknown={len(halluc_keys_full)}), "
          f"L{GATE_HEADLINE_LAYER} AUROC = {auroc_full_l33:.4f}  (manuscript/AMENDMENT.md: 0.999)")
    manuscript_g1 = 0.999
    if round(auroc_full_l33, 3) != manuscript_g1:
        print(f"  *** DISCREPANCY: recomputed {auroc_full_l33:.4f} rounds to "
              f"{round(auroc_full_l33, 3)} != manuscript {manuscript_g1} ***")

    y_clean = np.concatenate([np.ones(len(ka_keys_clean)), np.zeros(len(halluc_keys_full))])
    keys_clean_g1 = ka_keys_clean + halluc_keys_full
    auroc_clean_l33, _ = gate_auroc_at_layer(keys_clean_g1, y_clean, GATE_HEADLINE_LAYER, SCORE_SEED)
    print(f"CLEAN subset n={len(keys_clean_g1)} (known={len(ka_keys_clean)}, unknown={len(halluc_keys_full)}, "
          f"excluded={n_excluded_ka}), L{GATE_HEADLINE_LAYER} AUROC = {auroc_clean_l33:.4f}")
    print(f"delta (clean - full) = {auroc_clean_l33 - auroc_full_l33:+.4f}")

    rows_out.append({
        "name": "U_G1_gate_confirm_auroc_L33",
        "description": "within-SelfAware known-vs-unknown AUROC, U pre-gen anchor, layer 33 (AMENDMENT.md sec.7 headline)",
        "manuscript_value": manuscript_g1,
        "full_recomputed": round(auroc_full_l33, 4),
        "clean_value": round(auroc_clean_l33, 4),
        "n_full": len(keys_full_g1),
        "n_clean": len(keys_clean_g1),
        "n_excluded": n_excluded_ka,
        "delta": round(auroc_clean_l33 - auroc_full_l33, 4),
        "status": "recomputed",
    })

    # =====================================================================
    # 2. Within-SelfAware control (dial-based), full T fit
    # =====================================================================
    print()
    print("=" * 78)
    print("WITHIN-SELFAWARE CONTROL: dial AUROC(known-answered vs hallucination), T-fit L22 cold")
    print("=" * 78)
    t_rows = list(iter_jsonl(T_STAGE2_DIR / "rows.jsonl"))
    scaler, clf = fit_dial(t_rows)

    def control_auroc(ka_keys: list[str], h_keys: list[str], boot: bool = True) -> dict:
        s_ka = dial_scores(scaler, clf, ka_keys)
        s_h = dial_scores(scaler, clf, h_keys)
        y = np.concatenate([np.ones(len(s_ka)), np.zeros(len(s_h))])
        s = np.concatenate([s_ka, s_h])
        if boot:
            r = boot_auroc_ci(y, s, N_BOOT, BOOT_SEED)
        else:
            r = {"auroc": float(roc_auc_score(y, s))}
        r["n_ka"] = len(s_ka)
        r["n_h"] = len(s_h)
        return r

    combos = [
        ("control_known_vs_full_halluc121", "known-answered vs FULL 121-row hallucination set (pre-correction reading)",
         ka_keys_full, ka_keys_clean, halluc_keys_full, 0.93),
        ("control_known_vs_setA12", "known-answered vs Set A (12, both-detector-answered; corrected)",
         ka_keys_full, ka_keys_clean, set_a_keys, 0.8140),
        ("control_wide270_vs_setA12", "known-answered minus 6 wide-flipped (270) vs Set A (12)",
         ka_keys_wide270, ka_keys_clean_wide, set_a_keys, None),
    ]
    for name, desc, full_ka, clean_ka, h_keys, manuscript_val in combos:
        r_full = control_auroc(full_ka, h_keys)
        r_clean = control_auroc(clean_ka, h_keys)
        print(f"\n{name}: {desc}")
        print(f"  FULL:  n_known={r_full['n_ka']} n_halluc={r_full['n_h']}  "
              f"AUROC={r_full['auroc']:.4f}  CI=[{r_full['ci_lo']:.4f},{r_full['ci_hi']:.4f}]")
        if manuscript_val is not None and round(r_full["auroc"], 4) != round(manuscript_val, 4):
            print(f"  *** DISCREPANCY: recomputed {r_full['auroc']:.4f} vs manuscript {manuscript_val} ***")
        n_excl = r_full["n_ka"] - r_clean["n_ka"]
        print(f"  CLEAN: n_known={r_clean['n_ka']} (excluded={n_excl}) n_halluc={r_clean['n_h']}  "
              f"AUROC={r_clean['auroc']:.4f}  CI=[{r_clean['ci_lo']:.4f},{r_clean['ci_hi']:.4f}]")
        print(f"  delta (clean - full) = {r_clean['auroc'] - r_full['auroc']:+.4f}")
        rows_out.append({
            "name": name,
            "description": desc,
            "manuscript_value": manuscript_val,
            "full_recomputed": round(r_full["auroc"], 4),
            "clean_value": round(r_clean["auroc"], 4),
            "n_full": r_full["n_ka"] + r_full["n_h"],
            "n_clean": r_clean["n_ka"] + r_clean["n_h"],
            "n_excluded": n_excl,
            "delta": round(r_clean["auroc"] - r_full["auroc"], 4),
            "status": "recomputed",
        })

    # =====================================================================
    # 3. Set B / fully-corrected: NOT independently recomputable
    # =====================================================================
    print()
    print("=" * 78)
    print("SET B (8) / FULLY-CORRECTED (270 known / 8 halluc): BLOCKED")
    print("=" * 78)
    ug3_manuscript = None
    if UG3_RESCORE_JSON.exists():
        ug3_manuscript = json.loads(UG3_RESCORE_JSON.read_text())
    set_b_full = (ug3_manuscript["control_rescore"]["corrected_kaNarrow276_vs_setB"]["auroc_known_answered_vs_hallucination"]
                  if ug3_manuscript else 0.7369)
    fully_corrected_full = (ug3_manuscript["control_rescore"]["fully_corrected_kaBoth_vs_setB"]["auroc_known_answered_vs_hallucination"]
                             if ug3_manuscript else 0.75)
    print("Set B = Set A (12, reproducible) minus 4 rows identified by a MANUAL census "
          "(AMENDMENT.md corrigendum: 'one verbatim trained refusal template both detectors miss'). "
          "That census's row identities are not recorded in any pinned script or artifact on this "
          "checkout: `analysis/ug3_corrected_rescore.py` is gitignored and ABSENT from disk "
          "(checked: find . -iname ug3_corrected_rescore.py -> no results).")
    print(f"Reporting the pinned manuscript/artifact values only (from "
          f"{UG3_RESCORE_JSON.relative_to(REPO_ROOT) if UG3_RESCORE_JSON.exists() else 'MISSING'}), "
          f"not independently re-derived: Set B full={set_b_full}, fully-corrected full={fully_corrected_full}. "
          "Clean-subset (decontaminated) versions of these two: NOT COMPUTABLE without the missing script.")
    for name, desc, manuscript_val in [
        ("control_known_vs_setB8_BLOCKED", "known-answered vs Set B (8, census-corrected) -- Set B row identity not reproducible", set_b_full),
        ("control_fully_corrected_270vs8_BLOCKED", "270 known-answered vs Set B (8) fully-corrected -- Set B row identity not reproducible", fully_corrected_full),
    ]:
        rows_out.append({
            "name": name,
            "description": desc,
            "manuscript_value": manuscript_val,
            "full_recomputed": None,
            "clean_value": None,
            "n_full": None,
            "n_clean": None,
            "n_excluded": None,
            "delta": None,
            "status": "BLOCKED: Set B row identity requires missing analysis/ug3_corrected_rescore.py (gitignored, absent from disk) or a manual text census not present as a pinned artifact",
        })

    # --- write CSV -----------------------------------------------------
    fieldnames = ["name", "description", "manuscript_value", "full_recomputed", "clean_value",
                  "n_full", "n_clean", "n_excluded", "delta", "status"]
    with OUT_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows_out)
    print()
    print(f"wrote {OUT_CSV}")


if __name__ == "__main__":
    main()
