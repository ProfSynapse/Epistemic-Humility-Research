#!/usr/bin/env python3
"""BB phase 1 (CPU, no GPU, NO MODEL LOADING): smoke tests for the phase-1
build. Host constraint (binding): this test file must never load model
weights, CPU or GPU -- the local 3090 is busy with a governed ladder run and
the WSL2 VM will OOM. Every test here either exercises pure-Python/CPU
plumbing on synthetic data or rehearses the Modal container's import setup
block, which touches no model and no torch device.

Run: pytest test_bb_phase1_smoke.py -v
     (or python3 -m pytest test_bb_phase1_smoke.py -v; rtk-proxied `pytest
     <dir>` can falsely report "No tests collected" -- always target this
     file explicitly, per the project's known rtk gotcha.)
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
import yaml

EXP_DIR = Path(__file__).resolve().parent
CANONICAL_ROOT = Path("/home/profsynapse/code/Epistemic-Humility-Research")

sys.path.insert(0, str(EXP_DIR))
import build_fit_id_manifest as bfim  # noqa: E402
import build_fit_pool as bfp  # noqa: E402
import freeze_scorer_base as fsb  # noqa: E402
import near_dup_sweep_bb as ndsb  # noqa: E402
import score_bb_holdout as sbh  # noqa: E402


def _load_jsonl(p: Path):
    return [json.loads(l) for l in p.open() if l.strip()]


# --- 1. schema / manifest round-trip ----------------------------------------
def test_fit_id_manifest_schema_roundtrip(tmp_path):
    cell = yaml.safe_load((EXP_DIR / "cell.yaml").read_text())
    report = bfim.build(cell, CANONICAL_ROOT, EXP_DIR, smoke=True)
    assert report["n_rows"] == cell["phase1"]["fit_surface"]["n_rows"] == 1662

    manifest_path = EXP_DIR / "analysis/fit_surface_smoke/fit_ids.jsonl"
    rows = _load_jsonl(manifest_path)
    assert len(rows) == 1662
    for r in rows[:20]:
        assert set(r.keys()) == {"row_key", "source", "gold_label", "qhash"}
        assert r["gold_label"] in ("answerable", "unanswerable")
        assert len(r["qhash"]) == 64
        assert "question" not in r and "aliases" not in r  # containment: no text


# --- 2. quota / disjointness assertions -------------------------------------
def test_fit_read_disjointness_independent_check():
    """Re-derives the disjointness check independently of build_fit_id_manifest's
    own internal assertion, reading both COMMITTED manifests directly."""
    cell = yaml.safe_load((EXP_DIR / "cell.yaml").read_text())
    fit_ids = _load_jsonl(EXP_DIR / "analysis-committed/fit_surface/fit_ids.jsonl")
    read_ids = _load_jsonl(EXP_DIR / cell["read_surface"]["id_manifest"])
    assert len(fit_ids) == 1662
    assert len(read_ids) == 750
    fit_keys = {r["row_key"] for r in fit_ids}
    read_keys = {r["row_key"] for r in read_ids}
    overlap = fit_keys & read_keys
    assert len(overlap) == 0, f"fit/read surfaces overlap on {sorted(overlap)[:5]}"


def test_fit_pool_qhash_verified_against_manifest():
    cell = yaml.safe_load((EXP_DIR / "cell.yaml").read_text())
    report = bfp.build(cell, CANONICAL_ROOT, EXP_DIR, smoke=True)
    assert report["n_rows"] == 1662
    assert report["all_qhash_verified"] is True

    pool_rows = _load_jsonl(EXP_DIR / "analysis/fit_pool_smoke/fit_pool.jsonl")
    manifest = {r["row_key"]: r["qhash"]
                for r in _load_jsonl(EXP_DIR / "analysis/fit_surface_smoke/fit_ids.jsonl")}
    import hashlib
    for r in pool_rows[:50]:
        recomputed = hashlib.sha256(
            (r["row_key"] + "\x00" + r["question"]).encode("utf-8")).hexdigest()
        assert recomputed == manifest[r["row_key"]] == r["qhash"]
        assert r["label"] in ("known", "unknown")


def test_fit_pool_wrong_text_is_rejected(tmp_path, monkeypatch):
    """A right-key/wrong-text pool must be REJECTED, not silently accepted
    (the C3 guarantee build_fit_pool.py inherits from H9's build_holdout_pool.py)."""
    cell = yaml.safe_load((EXP_DIR / "cell.yaml").read_text())
    fs = dict(cell["phase1"]["fit_surface"])
    # point al_source_graded at a corrupted copy with one question text swapped
    src_rows = _load_jsonl(CANONICAL_ROOT / fs["al_source_graded"])
    src_rows[0]["question"] = "THIS IS DELIBERATELY WRONG TEXT FOR THE TEST"
    corrupt_dir = tmp_path / "corrupt_al"
    corrupt_dir.mkdir()
    corrupt_path = corrupt_dir / "rows_graded.jsonl"
    with corrupt_path.open("w") as fh:
        for r in src_rows:
            fh.write(json.dumps(r) + "\n")
    fs["al_source_graded"] = str(corrupt_path.relative_to(tmp_path))
    cell2 = dict(cell)
    cell2["phase1"] = dict(cell["phase1"])
    cell2["phase1"]["fit_surface"] = fs
    with pytest.raises(AssertionError, match="qhash mismatch"):
        bfp.build(cell2, tmp_path, EXP_DIR, smoke=True)


# --- 3. fake-activation fit+score path --------------------------------------
def test_freeze_scorer_fake_activation_fit_path():
    cell = yaml.safe_load((EXP_DIR / "cell.yaml").read_text())
    gates = yaml.safe_load((EXP_DIR / "gates.yaml").read_text())
    X24, X35, rows = fsb._synthetic_smoke_inputs(seed=42, n=300)
    report = fsb.build_and_verify(cell, gates, X24, X35, rows, EXP_DIR, smoke=True)
    assert report["fidelity_pass"] is True
    assert report["BB-FID-1_determinism"]["cosine"] >= 0.999999
    assert report["BB-FID-2_recipe_parity"]["knobs_match_AL_3_2"] is True
    frozen_out = Path(report["frozen_out"])
    for f in ("pca24.joblib", "pca35.joblib", "scaler24.joblib", "scaler35.joblib",
              "caution_logistic.joblib", "caution_residualizer.joblib",
              "d_confab_full.npy", "d_raw_rederived.npy", "prop_zscale.json",
              "scorer_manifest.json", "fidelity_report.json"):
        assert (frozen_out / f).exists(), f"missing frozen object {f}"


def test_score_holdout_selftest_gate_logic():
    gates = yaml.safe_load((EXP_DIR / "gates.yaml").read_text())
    res = sbh.selftest(gates)
    assert res["BB-P1-G1"]["verdict"] in (
        "PASS", "FAIL", "INCONCLUSIVE",
        "NOT-ADJUDICATED (caution floor failed; pipeline failure)")
    assert isinstance(res["BB-P1-G2"]["pass"], bool)


def test_score_rows_matches_fit_frozen_scorer_pipeline():
    """The frozen deployment path (score_bb_holdout.score_rows) must reproduce
    the SAME propensity/caution readouts the fit-time frozen objects encode,
    on the fit surface's own rows (sanity: fit rows scored through the frozen
    deployment path should closely track the fit-time full-sample readout)."""
    cell = yaml.safe_load((EXP_DIR / "cell.yaml").read_text())
    gates = yaml.safe_load((EXP_DIR / "gates.yaml").read_text())
    X24, X35, rows = fsb._synthetic_smoke_inputs(seed=7, n=300)
    report = fsb.build_and_verify(cell, gates, X24, X35, rows, EXP_DIR, smoke=True)
    fz = sbh.load_frozen(Path(report["frozen_out"]))
    prop_z, caution_z = sbh.score_rows(fz, X24, X35)
    assert prop_z.shape == (300,)
    assert caution_z.shape == (300,)
    assert np.isfinite(prop_z).all() and np.isfinite(caution_z).all()


def test_classify_reading_inconclusive_on_straddling_ci():
    gates = yaml.safe_load((EXP_DIR / "gates.yaml").read_text())
    rg = gates["reading_gate"]
    # point estimate clears the pass line but CI lower does not clear
    # pass_ci_lower_min -> not a clean PASS; and it doesn't fail either.
    verdict = sbh.classify_reading(0.63, 0.50, 0.75, rg)
    assert verdict == "INCONCLUSIVE"


def test_near_dup_sweep_smoke_runs_and_matches_h9_population():
    cell = yaml.safe_load((EXP_DIR / "cell.yaml").read_text())
    report = ndsb.sweep(cell, CANONICAL_ROOT, EXP_DIR, smoke=True)
    # BB reuses H9's exact KUQ populations, so this MUST reproduce H9's own
    # registered sweep result (0 flagged, max overlap 0.75) rather than
    # merely "some result" -- AMENDMENT.md section 8.
    assert report["n_flagged"] == 0
    assert report["max_overlap_observed"] == pytest.approx(0.75, abs=1e-6)
    assert report["n_held_kuq"] > 0 and report["n_fit_kuq"] > 0


# --- 4. import-preflight rehearsal against a clean scratch clone ------------
def test_import_preflight_rehearsal_clean_clone(tmp_path):
    """Rehearses the EXACT setup block from cloud/modal_bb_phase1.py (and,
    identically, modal_bb_phase0.py / H9's modal_h9_holdout.py) in a scratch
    clone that, like a fresh `git clone` inside the Modal container, LACKS the
    untracked experiment/phase1/probe legacy tree. No model is loaded, no GPU
    is touched, no torch device is used -- this only proves the import chain
    and the system-prompt resolver work before any model download would be
    attempted.
    """
    scratch = tmp_path / "ehr_scratch_clone"
    subprocess.run(
        ["git", "clone", "--local", "--no-hardlinks", str(CANONICAL_ROOT), str(scratch)],
        check=True, capture_output=True, text=True)

    legacy_probe = scratch / "experiment" / "phase1" / "probe"
    assert not legacy_probe.exists(), (
        "scratch clone unexpectedly already has experiment/phase1/probe -- "
        "the rehearsal assumption (fresh clone lacks the untracked legacy "
        "tree) does not hold; the local canonical checkout has this directory "
        "only because of an untracked local install, and git clone must not "
        "carry it over.")

    # step 1b: install the legacy-wrapper-tree + AC shim, exactly as the
    # Modal script does.
    legacy_probe.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(
        scratch / "archive" / "experiment" / "phase1" / "probe" / "legacy-wrapper-tree",
        legacy_probe)
    ac_shim = (scratch / "archive" / "experiments" / "doubt-regulated-caution"
               / "phase3_ac_doubt_coupled_intervention.yaml")
    ac_shim.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(
        scratch / "experiments" / "doubt-regulated-caution"
        / "ac_doubt_coupled_intervention.yaml", ac_shim)

    extract_gen = scratch / "archive/experiment/phase1/probe/amendments/amendment_ai_verdict_extract_gen.py"
    assert extract_gen.exists()

    env = dict(os.environ)
    env["PYTHONPATH"] = f"{scratch}:{legacy_probe}"
    result = subprocess.run(
        [sys.executable, "-c",
         "import sys; sys.path.insert(0, "
         f"{str(extract_gen.parent)!r}); "
         "import path_compat; "
         "from amendment_s_correctness_probe_extract import MODEL_TAG; "
         "from amendment_ah_stage0_extract import load_baseline_system_prompt; "
         "sp = load_baseline_system_prompt(); "
         "assert sp.startswith('Answer the user'), 'unexpected system prompt'; "
         "print('preflight imports OK, model_tag=' + MODEL_TAG)"],
        env=env, capture_output=True, text=True)
    assert result.returncode == 0, (
        f"preflight rehearsal FAILED in the clean scratch clone.\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}")
    assert "preflight imports OK" in result.stdout
