"""CPU smoke for report.py's merge_refused_final / intersect_and_align /
build_family_report on synthetic + (where staged data exists) real-population
fixtures. Proves the registered final-rate rule is implemented correctly:
detector-refused rows enter every rate/gap as refused_final=True instead of
being dropped as missing -- the EXACT bug class census's own report.py hit
once (its first draft joined over the adjudication output alone, silently
dropping every detector-refused row; found post-unblind, corrected). Run via
`python3 -m pytest test_report_smoke.py -v` (explicit file path)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import common  # noqa: E402
import config  # noqa: E402
import report  # noqa: E402
import row_pool  # noqa: E402


# ---------------------------------------------------------------------------
# merge_refused_final -- the census bug class, guarded directly
# ---------------------------------------------------------------------------

def test_merge_refused_final_detector_refused_row_not_dropped():
    """A row with refused_v2=True never enters the grading pool (build_pool.py
    routes it to a decoy or drops it), so it has NO entry in
    `adjudicated_by_key`. The merge must still produce refused_final=True for
    it, not silently omit it."""
    runlog_by_key = {
        "rk_detector_refused": {"row_key": "rk_detector_refused", "refused_v2": True},
        "rk_adjudicated_true": {"row_key": "rk_adjudicated_true", "refused_v2": False},
        "rk_adjudicated_false": {"row_key": "rk_adjudicated_false", "refused_v2": False},
        "rk_pending_adjudication": {"row_key": "rk_pending_adjudication", "refused_v2": False},
    }
    adjudicated_by_key = {
        "rk_adjudicated_true": {"refused_final": True},
        "rk_adjudicated_false": {"refused_final": False},
    }
    merged = report.merge_refused_final(runlog_by_key, adjudicated_by_key)

    assert merged["rk_detector_refused"]["refused_final"] is True
    assert merged["rk_detector_refused"]["detector_refused"] is True
    assert merged["rk_adjudicated_true"]["refused_final"] is True
    assert merged["rk_adjudicated_false"]["refused_final"] is False
    assert "rk_pending_adjudication" not in merged  # missing, not folded into either value


def test_merge_refused_final_all_detector_refused_reproduces_full_rate():
    """If every row in a population is detector-refused, the merged map's
    refused_final rate must be exactly 1.0, entirely from the detector flag,
    with zero dependency on adjudication output."""
    runlog_by_key = {f"rk{i}": {"row_key": f"rk{i}", "refused_v2": True} for i in range(50)}
    merged = report.merge_refused_final(runlog_by_key, {})
    assert len(merged) == 50
    assert all(v["refused_final"] for v in merged.values())


# ---------------------------------------------------------------------------
# rate_over_keys / intersect_and_align -- sc3 paired coverage
# ---------------------------------------------------------------------------

def test_rate_over_keys_reports_missing_separately():
    merged = {"rk1": {"refused_final": True}, "rk2": {"refused_final": False}}
    result = report.rate_over_keys(merged, ["rk1", "rk2", "rk3"])
    assert result["n"] == 2  # rk3 missing, not folded in
    assert result["n_missing"] == 1
    assert result["n_expected"] == 3
    assert result["successes"] == 1
    assert result["rate"] == pytest.approx(0.5)


def test_intersect_and_align_pairs_only_common_keys():
    maps = {
        "a": {"rk1": {"refused_final": True}, "rk2": {"refused_final": False}, "rk3": {"refused_final": True}},
        "b": {"rk1": {"refused_final": False}, "rk2": {"refused_final": True}},  # rk3 missing from b
    }
    arrays, ordered, diag = report.intersect_and_align(maps, ["rk1", "rk2", "rk3"])
    assert ordered == ["rk1", "rk2"]  # rk3 dropped, absent from map "b"
    assert diag["n_paired"] == 2
    # n_dropped_per_map[name] = how many REQUESTED row_keys are absent from
    # THAT map specifically (not the pairing outcome): rk3 is present in "a"
    # itself (0 dropped for "a") but absent from "b" (1 dropped for "b"),
    # which is exactly why the pairing above excludes it.
    assert diag["n_dropped_per_map"]["a"] == 0
    assert diag["n_dropped_per_map"]["b"] == 1
    assert list(arrays["a"]) == [True, False]
    assert list(arrays["b"]) == [False, True]


# ---------------------------------------------------------------------------
# P2/P3 statistic functions -- hand-computable arithmetic
# ---------------------------------------------------------------------------

def test_gap_sel_c_hat_stat_fn_matches_hand_computation():
    confab_baseline = np.array([False] * 70 + [True] * 30, dtype=bool)   # rate 0.30
    confab_true = np.array([False] * 20 + [True] * 80, dtype=bool)       # rate 0.80
    confab_permuted = np.array([False] * 50 + [True] * 50, dtype=bool)   # rate 0.50
    known_baseline = np.array([False] * 98 + [True] * 2, dtype=bool)     # rate 0.02
    known_true = np.array([False] * 99 + [True] * 1, dtype=bool)         # rate 0.01
    known_permuted = np.array([False] * 90 + [True] * 10, dtype=bool)    # rate 0.10

    gap = report.gap_sel_c_hat_stat_fn(confab_baseline, confab_true, confab_permuted,
                                       known_baseline, known_true, known_permuted)
    sel_true = abs(0.80 - 0.30) - abs(0.01 - 0.02)
    sel_permuted = abs(0.50 - 0.30) - abs(0.10 - 0.02)
    assert gap == pytest.approx(sel_true - sel_permuted, abs=1e-9)


def test_cost_protection_stat_fn_matches_hand_computation():
    known_true = np.array([False] * 98 + [True] * 2, dtype=bool)      # 0.02
    known_permuted = np.array([False] * 85 + [True] * 15, dtype=bool)  # 0.15
    cp = report.cost_protection_stat_fn(known_true, known_permuted)
    assert cp == pytest.approx(0.15 - 0.02, abs=1e-9)


# ---------------------------------------------------------------------------
# build_family_report end-to-end on synthetic per-row data over the REAL
# population (real row_pool row_key sets, since staging.py has already run
# for real in this worktree; skips cleanly if it has not).
# ---------------------------------------------------------------------------

def _write_runlog(analysis_dir: Path, tag: str, rows: list[dict]) -> None:
    path = analysis_dir / "runlog" / f"{tag}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


def _synthetic_arm_rows(row_keys: list[str], role: str, refused_rate: float, well_formed_rate: float, seed: int) -> list[dict]:
    rng = np.random.default_rng(seed)
    out = []
    for rk in row_keys:
        refused = bool(rng.random() < refused_rate)
        out.append({
            "row_key": rk, "role": role, "refused_v2": refused,
            "well_formed": bool(rng.random() < well_formed_rate),
        })
    return out


def _applied_rows_for(family: str, arm: str, seed, rows: list[dict]) -> list[dict]:
    """Every non-detector-refused row gets an adjudication_applied entry
    (in production this is the blinded agent's call; here it is a coin flip
    biased toward NOT abstaining, so refused_final for those rows == False
    unless overridden by the detector flag already handled in the runlog)."""
    out = []
    for r in rows:
        if r["refused_v2"]:
            continue  # detector-refused rows never enter the grading pool
        out.append({"cell": family, "arm": arm, "row_key": r["row_key"], "role": r["role"],
                    "seed": seed, "refused_final": False})
    return out


def test_build_family_report_end_to_end_synthetic_qwen(tmp_path):
    family = "qwen35_4b"
    if not (HERE / "analysis" / "staged_inputs" / family).is_dir():
        pytest.skip("staged_inputs not present for qwen35_4b; run staging.py first")

    pools = row_pool.heldout_row_keys_by_role(family)
    confab_full = pools["confab"]
    known_full = pools["known_correct_answered"]
    subsample_row_keys = confab_full[:config.SUBSAMPLE_CONFAB_ROWS_PER_FAMILY]

    analysis_dir = tmp_path / "analysis"
    committed_dir = tmp_path / "analysis-committed"
    committed_dir.mkdir(parents=True)

    all_applied: list[dict] = []

    # baseline: low refusal everywhere
    baseline_confab = _synthetic_arm_rows(confab_full, "confab", refused_rate=0.10, well_formed_rate=0.95, seed=1)
    baseline_known = _synthetic_arm_rows(known_full, "known_correct_answered", refused_rate=0.02, well_formed_rate=0.99, seed=2)
    baseline_rows = baseline_confab + baseline_known
    _write_runlog(analysis_dir, report.runlog_tag(family, "baseline"), baseline_rows)
    all_applied += _applied_rows_for(family, "baseline", None, baseline_rows)

    # true_gate__c_hat: high confab refusal, low known false refusal (P1 benefit/cost shape)
    tg_confab = _synthetic_arm_rows(confab_full, "confab", refused_rate=0.72, well_formed_rate=0.97, seed=3)
    tg_known = _synthetic_arm_rows(known_full, "known_correct_answered", refused_rate=0.03, well_formed_rate=0.99, seed=4)
    tg_rows = tg_confab + tg_known
    _write_runlog(analysis_dir, report.runlog_tag(family, "true_gate_c_hat"), tg_rows)
    all_applied += _applied_rows_for(family, "true_gate_c_hat", None, tg_rows)

    # permuted_gate__c_hat: moderate confab refusal, higher known false refusal (less selective)
    pg_confab = _synthetic_arm_rows(confab_full, "confab", refused_rate=0.45, well_formed_rate=0.95, seed=5)
    pg_known = _synthetic_arm_rows(known_full, "known_correct_answered", refused_rate=0.12, well_formed_rate=0.95, seed=6)
    pg_rows = pg_confab + pg_known
    _write_runlog(analysis_dir, report.runlog_tag(family, "permuted_gate_c_hat"), pg_rows)
    all_applied += _applied_rows_for(family, "permuted_gate_c_hat", None, pg_rows)

    # K=5 random-condition arms, over the subsample + full known. Seeds come
    # from a synthetic accepted-seed ledger written into the tmp committed dir:
    # report.py reads seeds ONLY from the ledger (never the raw pre-void
    # config.RANDOM_SEED_BLOCKS), so the fixture must provide one.
    synthetic_accepted = list(config.RANDOM_SEED_BLOCKS[family])
    common.write_json(committed_dir / "random_seed_ledger.json",
                      {family: {"accepted_seeds": synthetic_accepted,
                                "n_accepted": len(synthetic_accepted), "n_voids": 0}})
    for seed in synthetic_accepted:
        tgr_confab = _synthetic_arm_rows(subsample_row_keys, "confab", refused_rate=0.55, well_formed_rate=0.95, seed=seed)
        tgr_known = _synthetic_arm_rows(known_full, "known_correct_answered", refused_rate=0.04, well_formed_rate=0.98, seed=seed + 1)
        tgr_rows = tgr_confab + tgr_known
        _write_runlog(analysis_dir, report.runlog_tag(family, "true_gate_random", seed), tgr_rows)
        all_applied += _applied_rows_for(family, "true_gate_random", seed, tgr_rows)

        pgr_confab = _synthetic_arm_rows(subsample_row_keys, "confab", refused_rate=0.50, well_formed_rate=0.95, seed=seed + 2)
        pgr_known = _synthetic_arm_rows(known_full, "known_correct_answered", refused_rate=0.06, well_formed_rate=0.95, seed=seed + 3)
        pgr_rows = pgr_confab + pgr_known
        _write_runlog(analysis_dir, report.runlog_tag(family, "permuted_gate_random", seed), pgr_rows)
        all_applied += _applied_rows_for(family, "permuted_gate_random", seed, pgr_rows)

    common.write_jsonl(analysis_dir / "adjudication_applied.jsonl", all_applied)
    common.write_json(committed_dir / "subsample_manifest.json",
                      {"families": {family: {"row_keys": subsample_row_keys}}})

    fr = report.build_family_report(family, analysis_dir, committed_dir, all_applied, subsample_row_keys)

    assert fr["family"] == family
    assert fr["reported_rates"]["true_gate_c_hat"]["confab_abstention"]["rate"] > fr["reported_rates"]["baseline"]["confab_abstention"]["rate"]
    assert set(fr["p1"].keys()) >= {"benefit", "cost", "passed"}
    assert set(fr["p2"].keys()) >= {"c_hat", "random", "passed"}
    assert set(fr["p3"].keys()) >= {"c_hat", "random", "passed"}
    assert set(fr["s1"].keys()) >= {"passed", "cannot_move_gate_axis"}
    assert fr["s1"]["cannot_move_gate_axis"] is True
    # the true gate is designed (by construction of the synthetic rates above)
    # to be MORE selective than the permuted gate on both populations -> Gap_Sel(c_hat) > 0
    assert fr["p2"]["c_hat"]["gap_sel_c_hat"] > 0
    # the true gate's known false-refusal rate (0.03) is designed lower than the
    # permuted gate's (0.12) -> cost_protection_c_hat > 0
    assert fr["p3"]["c_hat"]["cost_protection_c_hat"] > 0


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
