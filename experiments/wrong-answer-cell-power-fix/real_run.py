#!/usr/bin/env python3
"""wrong-answer-cell-power-fix -- real-data scoring driver (CPU-only).

Loads the completed Arm A extraction (rows.jsonl + persisted h_base/h_lora
safetensors under a given extraction dir), assembles per-checkpoint arrays via
row_join.py, and calls the EXISTING pinned functions in score_gates.py /
readout.py unchanged to compute G0-1, G0-2, G0-4, G0-5, and E1-E5 (A1-A9) at
the primary layer L35 plus the L30-36 descriptive band.

This module does not redefine any estimator, threshold, or metric formula --
every number below is produced by calling row_join.build_join,
readout.fold_wise_refit_oof / frozen_axis_projection_auroc / ece /
ece_reweighted / bootstrap_ci / paired_bootstrap_delta, and
score_gates.compute_g0_4 / compute_g0_5 / compute_emitted_metrics /
compute_internal_metrics / compute_e4_ordering / check_g0_1_render_parity
exactly as those pinned modules define them. THE SPEC IS LOCKED: the six
pinned files (cell.yaml, gates.yaml, row_join.py, readout.py,
arm_a_extract.py, score_gates.py) are sha-verified below and this module
never edits them.

CONTAINMENT (repo is public; extraction dir is gitignored but the output of
THIS script is examined/reported): question text, generated_answer,
answer_text, and aliases are read only transiently (for the G0-1 tokenizer
re-render and the G0-4 re-grade, both of which are pinned score_gates.py /
row_join.py functions that already avoid persisting them) and are NEVER
written into the results JSON, the markdown summary, or printed to stdout by
this module. Only counts, metrics, shas, and row IDs are persisted/reported.

AMBIGUITY FLAGGED FOR THE LEAD (see `E4_AMBIGUITY_NOTE` below and the run
report): cell.yaml/gates.yaml do not pin WHICH axis A9's "internal projection"
per-cell means and E4's cell-ordering check should use for the two cells
(known_refused, unknown_refused) that never enter the A1 fold-wise-refit CV
population. This module computes E4 under BOTH the frozen L35 axis
(doubt_direction_L35.json, cell.yaml's cold_transport_companion, external to
this run) and a full-population axis freshly fit on this cell's own rows
(cell.yaml's literal `internal_readout.construction` formula, no fold
exclusion) and reports both without collapsing to one. It does NOT silently
pick a reading, because E4 is a gated quantity.

USAGE:
  python3 real_run.py --extraction-dir experiments/wrong-answer-cell-power-fix/analysis/hidden_states/wrong-answer-cell-power-fix-arm-a/extraction/extraction__ab37a32e61a9
  python3 real_run.py --extraction-dir <dir> --skip-g0-1   # skip the tokenizer load (e.g. no local weights)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import yaml

EXP_DIR = Path(__file__).resolve().parent
REPO_ROOT = EXP_DIR.parents[1]

READOUTS_DIR = REPO_ROOT / "experiments" / "common" / "readouts"
if str(READOUTS_DIR) not in sys.path:
    sys.path.insert(0, str(READOUTS_DIR))
from path_compat import knowledge_probe_dir  # noqa: E402

PROBE_DIR = knowledge_probe_dir()
if str(PROBE_DIR) not in sys.path:
    sys.path.insert(0, str(PROBE_DIR))
if str(EXP_DIR) not in sys.path:
    sys.path.insert(0, str(EXP_DIR))

import row_join  # noqa: E402  (pinned)
import readout  # noqa: E402  (pinned)
import score_gates  # noqa: E402  (pinned)
from hs_persistence import safe_tensor_key  # noqa: E402  (common infra, unpinned)

# ---------------------------------------------------------------------------
# Integrity: the six pinned files, verified byte-identical to experiment.yaml
# instrument.pins before this module reads/imports anything from them.
# ---------------------------------------------------------------------------

PINNED = {
    "cell.yaml": "5ee37dd3bdb12e64dd526441f34e732d241e11fbd9c6841879d51ae3ed7b6b34",
    "gates.yaml": "01ee0b017009cf6298a77c60fb5e2a82a67324c1bc0a7d4398489ee1bad2cc54",
    "row_join.py": "187ddd53f7d8027fa0b06dbbf92bd5fa50b65180b56d4ea34c304a9d28d6aa85",
    "readout.py": "75f2c17b2eb0c59a88bdc6f8aca6770db9985adfd0c933f0157458cb5384496b",
    "arm_a_extract.py": "0b5f9b25a3cfc7d9b4b6614d57a6fd868880896e093dc380db03121ca4890687",
    "score_gates.py": "cbf8e154b9423f1875b600118e35b5b7de5b0d44e36ab3cdb77bf67caaf2a23a",
}


def assert_pins_intact() -> None:
    for rel, expected in PINNED.items():
        got = row_join.file_sha256(EXP_DIR / rel)
        if got != expected:
            raise RuntimeError(
                f"{rel} sha256 {got} != pinned {expected} (experiment.yaml "
                "instrument.pins); THE SPEC IS LOCKED -- refusing to run "
                "against a modified pinned file"
            )


PRIMARY_LAYER = 35
LAYER_BAND = list(range(30, 37))
REWEIGHT_TARGET = 0.959
N_BOOT = 2000
SEED = 20260808

CHECKPOINT_ROLE = {"grpov2": "h_lora", "cleansft": "h_base"}

E4_AMBIGUITY_NOTE = (
    "cell.yaml pins A1's estimator (fold-wise-refit axis + 1-D logistic) but "
    "that estimator is undefined for known_refused/unknown_refused rows (they "
    "are never part of the answered-known CV population). A9's per-cell means "
    "and E4's ordering check need a projection defined on all four behavior "
    "cells. This module reports E4 under TWO readings without picking one: "
    "(a) the FROZEN L35 axis (doubt_direction_L35.json, external, never "
    "trained on this cell's data), and (b) a FRESH full-population axis "
    "(unit(mean(known_correct_answered) - mean(unknown_refused)), no fold "
    "exclusion, this cell's own data, cell.yaml's literal `construction` "
    "formula). Neither is the pinned A1 estimator; the lead should adjudicate "
    "which (if either) satisfies gates.yaml E4's wording."
)


# ---------------------------------------------------------------------------
# Extraction-dir loaders.
# ---------------------------------------------------------------------------

def load_manifest(extraction_dir: Path) -> dict:
    manifest = json.loads((extraction_dir / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("status") != "ok" or manifest.get("verified") is not True:
        raise RuntimeError(
            f"extraction manifest at {extraction_dir} is not status=ok/verified=True: "
            f"status={manifest.get('status')!r} verified={manifest.get('verified')!r}"
        )
    return manifest


def load_rows_index(extraction_dir: Path) -> dict[str, dict]:
    """row_key -> {label, question (transient), prompt_hash}. Never returned
    onward past this module's G0-1 sampling; callers must not serialize
    `question`.
    """
    index: dict[str, dict] = {}
    with (extraction_dir / "rows.jsonl").open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            index[rec["probe_pool_row_key"]] = {
                "label": rec["label"],
                "question": rec["question"],
                "prompt_hash": rec["prompt_hash"],
            }
    return index


def load_vector(extraction_dir: Path, row_key: str, role: str, layer: int) -> np.ndarray:
    from safetensors.numpy import load_file  # noqa: PLC0415

    safe = safe_tensor_key(row_key)
    shard = extraction_dir / f"{safe}__{role}.safetensors"
    tensors = load_file(str(shard))
    return np.asarray(tensors[f"L{layer}"], dtype=np.float64)


def load_layer_stack(extraction_dir: Path, row_key: str, role: str,
                      layers: list[int]) -> dict[int, np.ndarray]:
    from safetensors.numpy import load_file  # noqa: PLC0415

    safe = safe_tensor_key(row_key)
    shard = extraction_dir / f"{safe}__{role}.safetensors"
    tensors = load_file(str(shard))
    return {layer: np.asarray(tensors[f"L{layer}"], dtype=np.float64) for layer in layers}


# ---------------------------------------------------------------------------
# Assemble per-checkpoint arrays for a given layer.
# ---------------------------------------------------------------------------

def assemble_answered_known(extraction_dir: Path, join: row_join.JoinResult,
                             checkpoint: str, layer: int):
    role = CHECKPOINT_ROLE[checkpoint]
    rows = row_join.answered_known_rows(join, checkpoint)
    h = None
    y = np.empty(len(rows), dtype=int)
    stated = np.empty(len(rows), dtype=np.float64)
    row_ids = []
    for i, jr in enumerate(rows):
        ckpt = getattr(jr, checkpoint)
        vec = load_vector(extraction_dir, jr.row_id, role, layer)
        if h is None:
            h = np.empty((len(rows), vec.shape[0]), dtype=np.float64)
        h[i] = vec
        y[i] = 1 if ckpt.correct else 0
        stated[i] = ckpt.stated_confidence
        row_ids.append(jr.row_id)
    return h, y, stated, row_ids


def assemble_unknown_refused(extraction_dir: Path, join: row_join.JoinResult,
                              checkpoint: str, layer: int):
    role = CHECKPOINT_ROLE[checkpoint]
    rows = row_join.unknown_refused_rows(join, checkpoint)
    h = None
    for i, jr in enumerate(rows):
        vec = load_vector(extraction_dir, jr.row_id, role, layer)
        if h is None:
            h = np.empty((len(rows), vec.shape[0]), dtype=np.float64)
        h[i] = vec
    return h


def assemble_cell_projection(extraction_dir: Path, join: row_join.JoinResult,
                              checkpoint: str, layer: int, axis: np.ndarray) -> dict:
    """Project every row of each of the 4 behavior cells onto `axis` (any
    externally-supplied or freshly-fit direction; this function does not fit
    anything itself).
    """
    role = CHECKPOINT_ROLE[checkpoint]
    by_cell: dict[str, list[float]] = {c: [] for c in
                                        ("known_correct_answered", "known_answered_wrong",
                                         "known_refused", "unknown_refused")}
    for jr in join.rows:
        ckpt = getattr(jr, checkpoint)
        cell = row_join.behavior_cell(ckpt)
        if cell not in by_cell:
            continue
        vec = load_vector(extraction_dir, jr.row_id, role, layer)
        by_cell[cell].append(float(vec @ axis))
    return {cell: np.asarray(vals) for cell, vals in by_cell.items()}


# ---------------------------------------------------------------------------
# G0-1.
# ---------------------------------------------------------------------------

def run_g0_1(cell: dict, extraction_dir: Path, rows_index: dict[str, dict],
             *, n_sample: int = 50, seed: int = SEED) -> dict:
    from transformers import AutoTokenizer  # noqa: PLC0415

    import arm_a_extract as aae  # noqa: PLC0415  (pinned; only for the system prompt loader)

    system_prompt = aae.load_deployment_system_prompt(cell)
    checkpoints = {c["id"]: c for c in cell["arm_a"]["checkpoints"]}
    base_model_path = REPO_ROOT / checkpoints["grpov2"]["base"]

    rng = np.random.default_rng(seed)
    all_keys = sorted(rows_index.keys())
    sample_keys = rng.choice(all_keys, size=n_sample, replace=False)
    sample_rows = [
        {"probe_pool_row_key": k, "question": rows_index[k]["question"]} for k in sample_keys
    ]

    tokenizer = AutoTokenizer.from_pretrained(str(base_model_path))
    result = score_gates.check_g0_1_render_parity(
        tokenizer, system_prompt, sample_rows, extraction_dir / "rows.jsonl")
    return result


# ---------------------------------------------------------------------------
# Orchestration.
# ---------------------------------------------------------------------------

def run(extraction_dir: Path, *, skip_g0_1: bool = False,
        n_boot: int = N_BOOT, seed: int = SEED) -> dict:
    assert_pins_intact()
    cell = yaml.safe_load((EXP_DIR / "cell.yaml").read_text(encoding="utf-8"))

    checkpoints = {c["id"]: c for c in cell["arm_a"]["checkpoints"]}
    manifest = load_manifest(extraction_dir)
    rows_index = load_rows_index(extraction_dir)

    join = row_join.build_join(
        REPO_ROOT / checkpoints["grpov2"]["scored_rows"],
        REPO_ROOT / checkpoints["cleansft"]["scored_rows"],
        expected_grpov2_sha256=checkpoints["grpov2"]["scored_rows_sha256"],
        expected_cleansft_sha256=checkpoints["cleansft"]["scored_rows_sha256"],
    )
    g0_2 = join.g0_2
    g0_5 = score_gates.compute_g0_5(g0_2)
    g0_4_grpov2 = score_gates.compute_g0_4(
        REPO_ROOT / checkpoints["grpov2"]["scored_rows"], n_sample=200, seed=seed)
    g0_4_cleansft = score_gates.compute_g0_4(
        REPO_ROOT / checkpoints["cleansft"]["scored_rows"], n_sample=200, seed=seed)

    if skip_g0_1:
        g0_1 = {"status": "skipped", "reason": "--skip-g0-1"}
    else:
        g0_1 = run_g0_1(cell, extraction_dir, rows_index, n_sample=50, seed=seed)

    frozen = cell["internal_readout"]["cold_transport_companion"]
    frozen_path = REPO_ROOT / frozen["artifact"]
    frozen_got_sha = row_join.file_sha256(frozen_path)
    if frozen_got_sha != frozen["sha256"]:
        raise RuntimeError(
            f"doubt_direction_L35.json sha256 {frozen_got_sha} != pinned {frozen['sha256']}"
        )
    frozen_doc = json.loads(frozen_path.read_text(encoding="utf-8"))
    theta_frozen_L35 = np.asarray(frozen_doc["theta"], dtype=np.float64)

    per_checkpoint = {}
    for checkpoint in ("grpov2", "cleansft"):
        band = {}
        for layer in LAYER_BAND:
            h_answered, y, stated, _ids = assemble_answered_known(
                extraction_dir, join, checkpoint, layer)
            h_unknown_refused = assemble_unknown_refused(extraction_dir, join, checkpoint, layer)

            oof = readout.fold_wise_refit_oof(h_answered, y, h_unknown_refused, seed=seed)
            a1 = readout.metric_auroc(y, oof)
            a1_ci = readout.bootstrap_ci(y, oof, readout.metric_auroc, n_boot, seed)
            a3 = readout.metric_auroc(y, stated)
            a4 = readout.paired_bootstrap_delta(y, oof, stated, readout.metric_auroc, n_boot, seed)
            a5_raw = readout.ece(oof, y)
            a5_rw = readout.ece_reweighted(oof, y, REWEIGHT_TARGET)
            a6_raw = readout.ece(stated, y)
            a6_rw = readout.ece_reweighted(stated, y, REWEIGHT_TARGET)
            metric_ece_raw = readout.make_metric_ece()
            metric_ece_rw = readout.make_metric_ece_reweighted(REWEIGHT_TARGET)
            a7_raw = readout.paired_bootstrap_delta(y, stated, oof, metric_ece_raw, n_boot, seed)
            a7_rw = readout.paired_bootstrap_delta(y, stated, oof, metric_ece_rw, n_boot, seed)

            layer_result = {
                "n_answered_known": len(y), "n_correct": int(y.sum()),
                "n_wrong": int((1 - y).sum()), "n_unknown_refused": h_unknown_refused.shape[0],
                "A1_internal_refit_auroc": a1, "A1_ci": a1_ci,
                "A3_emitted_auroc": a3,
                "A4_gap": a4,
                "A5_internal_ece_raw": a5_raw, "A5_internal_ece_reweighted": a5_rw,
                "A6_emitted_ece_raw": a6_raw, "A6_emitted_ece_reweighted": a6_rw,
                "A7_calibration_gap_raw": a7_raw, "A7_calibration_gap_reweighted": a7_rw,
            }
            if layer == PRIMARY_LAYER:
                a2 = readout.frozen_axis_projection_auroc(h_answered, y, theta_frozen_L35)
                layer_result["A2_frozen_axis_raw_projection_auroc"] = a2
                a8 = {"mean": float(stated.mean()), "std": float(stated.std(ddof=0)), "n": len(stated)}
                layer_result["A8_emitted_mean_std"] = a8
            band[layer] = layer_result

        primary = band[PRIMARY_LAYER]
        e1 = primary["A1_internal_refit_auroc"] >= 0.60 and primary["A1_ci"]["ci_lo"] > 0.55
        e2 = primary["A4_gap"]["point"] >= 0.05 and primary["A4_gap"]["excludes_zero"]
        e3 = (primary["A7_calibration_gap_raw"]["point"] > 0.0
              and primary["A7_calibration_gap_raw"]["excludes_zero"]
              and primary["A7_calibration_gap_reweighted"]["point"] > 0.0
              and primary["A7_calibration_gap_reweighted"]["excludes_zero"])

        # E4 / A9, two readings (see E4_AMBIGUITY_NOTE).
        proj_frozen = assemble_cell_projection(extraction_dir, join, checkpoint,
                                                PRIMARY_LAYER, theta_frozen_L35)
        h_ans_L35, y_L35, _stated_L35, _ids = assemble_answered_known(
            extraction_dir, join, checkpoint, PRIMARY_LAYER)
        h_unk_ref_L35 = assemble_unknown_refused(extraction_dir, join, checkpoint, PRIMARY_LAYER)
        pos_anchor = h_ans_L35[y_L35 == 1].mean(axis=0)
        neg_anchor = h_unk_ref_L35.mean(axis=0)
        fresh_axis = pos_anchor - neg_anchor
        fresh_axis = fresh_axis / np.linalg.norm(fresh_axis)
        proj_fresh = assemble_cell_projection(extraction_dir, join, checkpoint,
                                               PRIMARY_LAYER, fresh_axis)

        e4_frozen = score_gates.compute_e4_ordering(None, {}, seed=seed, primary_layer_proj=proj_frozen)
        e4_fresh = score_gates.compute_e4_ordering(None, {}, seed=seed, primary_layer_proj=proj_fresh)

        emitted_cells = {}
        for cname in row_join.BEHAVIOR_CELLS:
            vals = [getattr(jr, checkpoint).stated_confidence for jr in join.rows
                    if row_join.behavior_cell(getattr(jr, checkpoint)) == cname]
            emitted_cells[cname] = {"n": len(vals), "emitted_mean": float(np.mean(vals)) if vals else None}

        per_checkpoint[checkpoint] = {
            "layer_band": band,
            "primary_layer": PRIMARY_LAYER,
            "E1_internal_discrimination": {"pass": bool(e1), "auroc": primary["A1_internal_refit_auroc"],
                                            "ci_lower": primary["A1_ci"]["ci_lo"],
                                            "threshold": {"auroc": 0.60, "ci_lower": 0.55}},
            "E2_primary_gap": {"pass": bool(e2), "gap": primary["A4_gap"]["point"],
                                "ci_lo": primary["A4_gap"]["ci_lo"], "ci_hi": primary["A4_gap"]["ci_hi"],
                                "threshold": {"gap": 0.05, "ci": "excludes-zero"}},
            "E3_calibration_contrast": {"pass": bool(e3), "raw": primary["A7_calibration_gap_raw"],
                                         "reweighted": primary["A7_calibration_gap_reweighted"]},
            "E4_cell_ordering_frozen_axis": e4_frozen,
            "E4_cell_ordering_fresh_axis": e4_fresh,
            "A9_emitted_per_cell": emitted_cells,
        }

    primary_falsifier = (
        per_checkpoint["grpov2"]["layer_band"][PRIMARY_LAYER]["A1_internal_refit_auroc"] < 0.60
        and per_checkpoint["grpov2"]["layer_band"][PRIMARY_LAYER]["A4_gap"]["point"] <= 0.05
        and not per_checkpoint["grpov2"]["layer_band"][PRIMARY_LAYER]["A4_gap"]["excludes_zero"]
    )
    g0_pass = (g0_2["pass"] and g0_4_grpov2["pass"] and g0_5["pass"]
               and (g0_1.get("pass") if g0_1.get("status") != "skipped" else None))
    e1 = per_checkpoint["grpov2"]["E1_internal_discrimination"]["pass"]
    e2 = per_checkpoint["grpov2"]["E2_primary_gap"]["pass"]
    if g0_pass and e1 and e2:
        verdict = {"label": "SUCCESS", "reason": "G0 all pass, E1 and E2 pass (grpov2, L35)"}
    elif primary_falsifier:
        verdict = {"label": "FAILURE", "reason": "primary falsifier fired (grpov2, L35)"}
    elif e1 and e2:
        verdict = {"label": "PARTIAL", "reason": "E1/E2 pass; G0-1 unresolved or E3/E4 ambiguous"}
    else:
        verdict = {"label": "AMBIGUOUS", "reason": "neither SUCCESS nor the primary falsifier"}

    return {
        "mode": "real_extraction",
        "extraction_dir": str(extraction_dir.relative_to(REPO_ROOT)),
        "manifest_extraction_config_sha": manifest["extraction_config_sha"],
        "manifest_data_sha256": manifest["data_sha256"],
        "primary_layer": PRIMARY_LAYER,
        "layer_band": LAYER_BAND,
        "n_boot": n_boot,
        "seed": seed,
        "G0_1_render_parity": g0_1,
        "G0_2_join_integrity": g0_2,
        "G0_4_grader_parity_grpov2": g0_4_grpov2,
        "G0_4_grader_parity_cleansft": g0_4_cleansft,
        "G0_5_data_adequacy": g0_5,
        "per_checkpoint": per_checkpoint,
        "E4_ambiguity_note": E4_AMBIGUITY_NOTE,
        "E5_convergent_validity": {"status": "not_computed", "reason": "Arm B not built"},
        "verdict": verdict,
    }


# ---------------------------------------------------------------------------
# Markdown summary.
# ---------------------------------------------------------------------------

def render_markdown(result: dict) -> str:
    lines = []
    lines.append(f"# wrong-answer-cell-power-fix -- real-run gate table")
    lines.append("")
    lines.append(f"extraction_dir: `{result['extraction_dir']}`  ")
    lines.append(f"extraction_config_sha: `{result['manifest_extraction_config_sha']}`  ")
    lines.append(f"primary layer: L{result['primary_layer']}, band L{LAYER_BAND[0]}-L{LAYER_BAND[-1]}, "
                  f"n_boot={result['n_boot']}, seed={result['seed']}")
    lines.append("")
    lines.append("## G0 gates")
    lines.append("")
    lines.append("| Gate | Measured | Threshold | Pass |")
    lines.append("|---|---|---|---|")
    g0_1 = result["G0_1_render_parity"]
    if g0_1.get("status") == "skipped":
        lines.append("| G0-1 render parity | skipped | byte-identical 50-row sample, 100% clean | n/a |")
    else:
        lines.append(f"| G0-1 render parity | {g0_1['n_mismatches']}/{g0_1['n_checked']} mismatches "
                      f"| 0 mismatches | {g0_1['pass']} |")
    g0_2 = result["G0_2_join_integrity"]
    lines.append(f"| G0-2 join integrity | {g0_2['n_only_grpov2']}+{g0_2['n_only_cleansft']} unmatched, "
                  f"{g0_2['n_duplicate_ids_grpov2']}+{g0_2['n_duplicate_ids_cleansft']} dup ids | "
                  f"0/0/0/0 | {g0_2['pass']} |")
    g4a = result["G0_4_grader_parity_grpov2"]
    g4b = result["G0_4_grader_parity_cleansft"]
    lines.append(f"| G0-4 grader parity (grpov2) | {g4a['agreement_rate']:.4f} | >= 0.995 | {g4a['pass']} |")
    lines.append(f"| G0-4 grader parity (cleansft) | {g4b['agreement_rate']:.4f} | >= 0.995 | {g4b['pass']} |")
    g0_5 = result["G0_5_data_adequacy"]
    for name in ("grpov2", "cleansft"):
        c = g0_5[name]
        lines.append(f"| G0-5 data adequacy ({name}) | correct={c['correct']} wrong={c['wrong']} | "
                      f">=300/>=300 | {c['pass']} |")
    lines.append("")

    for checkpoint in ("grpov2", "cleansft"):
        pc = result["per_checkpoint"][checkpoint]
        primary = pc["layer_band"][PRIMARY_LAYER]
        gated = " (GATED per gates.yaml)" if checkpoint == "grpov2" else " (descriptive, not gated)"
        lines.append(f"## {checkpoint} -- L{PRIMARY_LAYER} primary{gated}")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("|---|---|")
        lines.append(f"| A1 internal refit AUROC | {primary['A1_internal_refit_auroc']:.4f} "
                      f"(CI {primary['A1_ci']['ci_lo']:.4f}, {primary['A1_ci']['ci_hi']:.4f}) |")
        lines.append(f"| A2 frozen-axis raw projection AUROC (descriptive) | "
                      f"{primary['A2_frozen_axis_raw_projection_auroc']:.4f} |")
        lines.append(f"| A3 emitted AUROC | {primary['A3_emitted_auroc']:.4f} |")
        lines.append(f"| A4 gap (A1-A3) | {primary['A4_gap']['point']:.4f} "
                      f"(CI {primary['A4_gap']['ci_lo']:.4f}, {primary['A4_gap']['ci_hi']:.4f}) |")
        lines.append(f"| A5 internal ECE raw / reweighted | {primary['A5_internal_ece_raw']:.4f} / "
                      f"{primary['A5_internal_ece_reweighted']:.4f} |")
        lines.append(f"| A6 emitted ECE raw / reweighted | {primary['A6_emitted_ece_raw']:.4f} / "
                      f"{primary['A6_emitted_ece_reweighted']:.4f} |")
        lines.append(f"| A7 calibration gap raw (CI) | {primary['A7_calibration_gap_raw']['point']:.4f} "
                      f"({primary['A7_calibration_gap_raw']['ci_lo']:.4f}, "
                      f"{primary['A7_calibration_gap_raw']['ci_hi']:.4f}) |")
        lines.append(f"| A7 calibration gap reweighted (CI) | "
                      f"{primary['A7_calibration_gap_reweighted']['point']:.4f} "
                      f"({primary['A7_calibration_gap_reweighted']['ci_lo']:.4f}, "
                      f"{primary['A7_calibration_gap_reweighted']['ci_hi']:.4f}) |")
        lines.append(f"| A8 emitted mean/std (n) | {primary['A8_emitted_mean_std']['mean']:.4f} / "
                      f"{primary['A8_emitted_mean_std']['std']:.4f} (n={primary['A8_emitted_mean_std']['n']}) |")
        lines.append("")
        lines.append("A9 emitted per-cell means:")
        lines.append("")
        lines.append("| cell | n | emitted mean |")
        lines.append("|---|---|---|")
        for cname, cval in pc["A9_emitted_per_cell"].items():
            m = f"{cval['emitted_mean']:.4f}" if cval["emitted_mean"] is not None else "n/a"
            lines.append(f"| {cname} | {cval['n']} | {m} |")
        lines.append("")
        lines.append("| E gate | Pass | Detail |")
        lines.append("|---|---|---|")
        lines.append(f"| E1 internal discrimination | {pc['E1_internal_discrimination']['pass']} | "
                      f"AUROC={pc['E1_internal_discrimination']['auroc']:.4f}, "
                      f"ci_lower={pc['E1_internal_discrimination']['ci_lower']:.4f} "
                      f"(need >=0.60 and ci_lower>0.55) |")
        lines.append(f"| E2 primary gap | {pc['E2_primary_gap']['pass']} | "
                      f"gap={pc['E2_primary_gap']['gap']:.4f} "
                      f"(need >=0.05, CI excludes 0) |")
        lines.append(f"| E3 calibration contrast | {pc['E3_calibration_contrast']['pass']} | "
                      f"raw+reweighted both >0 with CI excluding 0 |")
        lines.append(f"| E4 ordering (frozen axis) | {pc['E4_cell_ordering_frozen_axis']['pass']} | "
                      f"AMBIGUOUS axis choice, see E4_ambiguity_note |")
        lines.append(f"| E4 ordering (fresh axis) | {pc['E4_cell_ordering_fresh_axis']['pass']} | "
                      f"AMBIGUOUS axis choice, see E4_ambiguity_note |")
        lines.append("")

    lines.append("## E5")
    lines.append("")
    lines.append(f"status: {result['E5_convergent_validity']['status']} "
                 f"-- {result['E5_convergent_validity']['reason']}")
    lines.append("")
    lines.append("## Verdict (raw; lead adjudicates)")
    lines.append("")
    lines.append(f"**{result['verdict']['label']}** -- {result['verdict']['reason']}")
    lines.append("")
    lines.append("## Ambiguity flagged")
    lines.append("")
    lines.append(result["E4_ambiguity_note"])
    lines.append("")
    return "\n".join(lines)


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--extraction-dir", type=Path, required=True)
    ap.add_argument("--skip-g0-1", action="store_true",
                     help="skip the tokenizer-load render-parity re-render")
    ap.add_argument("--n-boot", type=int, default=N_BOOT)
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--out-json", type=Path, default=None)
    ap.add_argument("--out-md", type=Path, default=None)
    return ap.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    extraction_dir = args.extraction_dir
    if not extraction_dir.is_absolute():
        extraction_dir = (REPO_ROOT / extraction_dir).resolve()

    result = run(extraction_dir, skip_g0_1=args.skip_g0_1, n_boot=args.n_boot, seed=args.seed)

    out_json = args.out_json or (EXP_DIR / "analysis" / "real_run_results.json")
    out_md = args.out_md or (EXP_DIR / "analysis" / "real_run_results.md")
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    out_md.write_text(render_markdown(result), encoding="utf-8")

    print(json.dumps(result, indent=2, default=str))
    print(f"\nwrote {out_json}\nwrote {out_md}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
