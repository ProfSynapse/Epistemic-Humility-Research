#!/usr/bin/env python3
"""H3 seed/sampled-decode replication -- CPU-only smoke (NO GPU, NO real
model load).

Exercises the harness's non-generation logic on synthetic data: the gate's
fire-decision math (shared with H4), the per-row-per-seed majority/any-
vote/mean-fraction scoring, the pooled-vs-per-seed aggregation, all four gate
computations (H3-G0/G1/G2/G3, both pass and fail shapes), the seed-derivation
and placebo-redraw helpers (determinism given a seed, correct fired counts),
the batched-decode termination-detection primitive (`gen_lib._first_eos_position`,
tested directly on synthetic token tensors), the REAL grading functions
(gen_lib.grade_clean_tighten, grader.grade_one -- pure text, no model), and a
RunLog round-trip proving the per-unit resume contract works with the pinned
synaptic-tuner submodule.

This is NOT a substitute for the GPU smoke (`pipeline.py --mode smoke`),
which is the only thing that can prove batched generation, the write hook,
and readback wiring are correct end to end. This script proves everything
ELSE: the arithmetic and control flow this build task can validate without a
multi-gigabyte model load on a CPU-only / no-GPU host.

Run: python smoke_cpu.py
Exit 0 and "ALL CPU SMOKE CHECKS PASSED" on success; raises AssertionError
(nonzero exit) on any failure.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent / "synaptic-tuner"))

import gen_lib as gl  # noqa: E402
import grader  # noqa: E402
import model_lib as ml  # noqa: E402
import pipeline as pl  # noqa: E402
from shared.utilities.run_log import RunLog  # noqa: E402


def check_gate_decision() -> None:
    # tau_frozen = 0.3026445054171378 (real frozen value, cell.yaml/gates.yaml),
    # same math as H4's smoke -- this instrument is shared, not re-derived.
    tau = 0.3026445054171378
    mu_d, sigma_d = -27.0, 16.0

    d = pl.gate_decision(proj_d=-60.0, mu_d=mu_d, sigma_d=sigma_d, tau=tau)
    assert d["fire"] is True, d
    assert -2.0 <= d["z_d"] <= 2.0

    d2 = pl.gate_decision(proj_d=10.0, mu_d=mu_d, sigma_d=sigma_d, tau=tau)
    assert d2["fire"] is False, d2

    d3 = pl.gate_decision(proj_d=-10000.0, mu_d=mu_d, sigma_d=sigma_d, tau=tau)
    assert d3["z_d"] == -2.0, d3
    d4 = pl.gate_decision(proj_d=10000.0, mu_d=mu_d, sigma_d=sigma_d, tau=tau)
    assert d4["z_d"] == 2.0, d4

    d5 = pl.gate_decision(proj_d=mu_d - tau * sigma_d, mu_d=mu_d, sigma_d=sigma_d, tau=tau)
    assert abs(d5["score_neg_z_d"] - tau) < 1e-9
    assert d5["fire"] is True, d5
    print("[smoke_cpu] gate_decision: PASS")


def check_score_row_samples() -> None:
    # 8/8 true -> majority, any, mean=1.0.
    all_true = [{"k": True}] * 8
    s = pl.score_row_samples(all_true, "k")
    assert s == {"n_samples": 8, "count": 8, "majority_vote": True, "any_vote": True, "mean_fraction": 1.0}, s

    # 0/8 true -> nothing fires.
    all_false = [{"k": False}] * 8
    s2 = pl.score_row_samples(all_false, "k")
    assert s2["majority_vote"] is False and s2["any_vote"] is False and s2["mean_fraction"] == 0.0, s2

    # exactly 5/8 -> majority True (threshold is ">=5", not ">5").
    five = [{"k": True}] * 5 + [{"k": False}] * 3
    s3 = pl.score_row_samples(five, "k")
    assert s3["majority_vote"] is True, s3

    # 4-4 tie -> majority False (AMENDMENT.md: "4-4 tie counts as instrument
    # did not act", i.e. not converted / not damaged either way, since the
    # rule is always ">=5 of 8", never a symmetric ">=4").
    tie = [{"k": True}] * 4 + [{"k": False}] * 4
    s4 = pl.score_row_samples(tie, "k")
    assert s4["majority_vote"] is False, s4
    assert s4["any_vote"] is True, s4  # any-vote envelope still fires on 1+
    assert s4["mean_fraction"] == 0.5, s4
    print("[smoke_cpu] score_row_samples (majority/any/mean, tie behavior): PASS")


def check_wilson_ci_overlap() -> None:
    assert ml.wilson_ci_overlap((0.60, 0.80), (0.70, 0.90)) is True
    assert ml.wilson_ci_overlap((0.60, 0.80), (0.667, 0.793)) is True  # resolved H3-G0 CI
    assert ml.wilson_ci_overlap((0.10, 0.20), (0.30, 0.40)) is False
    assert ml.wilson_ci_overlap((0.10, 0.20), (0.20, 0.30)) is True  # touching endpoints overlap
    print("[smoke_cpu] wilson_ci_overlap: PASS")


def check_seed_and_placebo_helpers() -> None:
    # derive_seed: deterministic given (base_seed, row_key); differs across
    # row_key for the same base_seed, and across base_seed for the same row_key.
    a = pl.derive_seed(20260710, "confab::row1")
    b = pl.derive_seed(20260710, "confab::row1")
    c = pl.derive_seed(20260710, "confab::row2")
    d = pl.derive_seed(20260711, "confab::row1")
    assert a == b, (a, b)
    assert a != c, (a, c)
    assert a != d, (a, d)
    assert isinstance(a, int) and 0 <= a < 2 ** 31

    # draw_random_direction: unit norm, deterministic given seed, differs
    # across seeds (this is the H3-G3(i) fresh-direction-per-seed contract).
    v1 = ml.draw_random_direction(20260710, hidden_dim=64)
    v1_again = ml.draw_random_direction(20260710, hidden_dim=64)
    v2 = ml.draw_random_direction(20260711, hidden_dim=64)
    assert abs(float((v1 ** 2).sum()) ** 0.5 - 1.0) < 1e-9
    assert (v1 == v1_again).all()
    assert not (v1 == v2).all()

    # draw_permuted_gate_indices: correct fired count, deterministic given
    # seed, differs across seeds (H3-G3(ii) fresh-assignment-per-seed).
    idx1 = ml.draw_permuted_gate_indices(pool_size=443, n_fired=57, seed=20260710)
    idx1_again = ml.draw_permuted_gate_indices(pool_size=443, n_fired=57, seed=20260710)
    idx2 = ml.draw_permuted_gate_indices(pool_size=443, n_fired=57, seed=20260711)
    assert len(idx1) == 57, len(idx1)
    assert idx1 == idx1_again
    assert idx1 != idx2
    assert all(0 <= i < 443 for i in idx1)
    print("[smoke_cpu] derive_seed / draw_random_direction / draw_permuted_gate_indices: PASS")


def check_batched_termination_detection() -> None:
    # Synthetic per-row token tensors (no model): row 0 emits eos strictly
    # before the last column (terminated naturally); row 1 emits eos only at
    # the very last column (ambiguous -- called not-terminated, conservative);
    # row 2 never emits eos (not terminated, used the full budget).
    eos_ids = {999}
    row_terminated = torch.tensor([1, 2, 999, 0, 0])   # eos at index 2 of 5 -> True
    row_boundary = torch.tensor([1, 2, 3, 4, 999])     # eos only at last index -> False
    row_never = torch.tensor([1, 2, 3, 4, 5])          # no eos -> False

    assert gl._first_eos_position(row_terminated, eos_ids) == 2
    assert gl._first_eos_position(row_boundary, eos_ids) == 4
    assert gl._first_eos_position(row_never, eos_ids) is None
    print("[smoke_cpu] batched termination detection (_first_eos_position): PASS")


def _greedy_rec(row_key: str, role: str, fire: bool, clean_tighten: bool, wfc: bool) -> dict:
    return {
        "row_key": row_key, "role": role, "fire": fire,
        "clean_tighten": clean_tighten, "well_formed_correct": wfc,
        "not_well_formed_correct": not wfc,
    }


def check_compute_h3_g0() -> None:
    # Predicted-shape PASS case: matches the resolved reference within tolerance.
    greedy_confab = [_greedy_rec(f"c{i}", "confab", True, i < 136, False) for i in range(185)]  # 73.51%
    greedy_known = [_greedy_rec(f"k{i}", "known_correct_answered", i < 8, False, i >= 8) for i in range(258)]  # 3.10% damaged
    g0 = pl.compute_h3_g0(greedy_confab, greedy_known)
    assert g0["passed"] is True, g0
    assert g0["checks"]["confab_conversion_reproduces"] is True, g0
    assert g0["checks"]["known_correct_cost_reproduces"] is True, g0

    # Falsifier-shape FAIL case: conversion far off reference (drops to ~40%).
    greedy_confab_fail = [_greedy_rec(f"c{i}", "confab", True, i < 74, False) for i in range(185)]  # 40.0%
    g0_fail = pl.compute_h3_g0(greedy_confab_fail, greedy_known)
    assert g0_fail["passed"] is False, g0_fail
    assert g0_fail["checks"]["confab_conversion_reproduces"] is False, g0_fail
    print("[smoke_cpu] compute_h3_g0 (pass + fail shapes): PASS")


def _sample_unit(row_key: str, role: str, fire: bool, n_true_ct: int, n_true_not_wfc: int) -> dict:
    samples = []
    for i in range(8):
        samples.append({
            "clean_tighten": i < n_true_ct,
            "not_well_formed_correct": i < n_true_not_wfc,
        })
    return {"row_key": row_key, "role": role, "fire": fire, "samples": samples}


def check_compute_h3_g1_g2() -> None:
    seeds = [20260710, 20260711]
    units_by_seed: dict[int, list[dict]] = {}
    for seed in seeds:
        units = []
        # 185 confab rows: ~68% of rows have >=5/8 clean_tighten (0.68 >= 0.635 gate).
        for i in range(185):
            n_true = 6 if i < 126 else 2  # 126/185 = 68.1% majority-converted
            units.append(_sample_unit(f"c{i}", "confab", True, n_true_ct=n_true, n_true_not_wfc=0))
        # 258 known rows: ~4% damaged (well under the 8% ceiling, UCB under 12%).
        for i in range(258):
            n_true = 6 if i < 10 else 0  # 10/258 = 3.9% majority-damaged
            units.append(_sample_unit(f"k{i}", "known_correct_answered", False, n_true_ct=0, n_true_not_wfc=n_true))
        units_by_seed[seed] = units

    g1 = pl.compute_h3_g1(units_by_seed)
    assert g1["passed"] is True, g1
    assert g1["checks"]["pooled_ge_0_635"] is True, g1
    assert all(g1["checks"]["per_seed_ge_0_635"].values()), g1

    g2 = pl.compute_h3_g2(units_by_seed)
    assert g2["passed"] is True, g2
    assert g2["checks"]["pooled_pass"] is True, g2
    assert all(g2["checks"]["per_seed_pass"].values()), g2

    # Falsifier shape: conversion collapses under sampled decode (majority
    # drops to ~30%, well under 0.635) -- G1 must report passed=False.
    units_by_seed_fail: dict[int, list[dict]] = {}
    for seed in seeds:
        units = []
        for i in range(185):
            n_true = 6 if i < 55 else 2  # 55/185 = 29.7% majority-converted
            units.append(_sample_unit(f"c{i}", "confab", True, n_true_ct=n_true, n_true_not_wfc=0))
        units_by_seed_fail[seed] = units
    g1_fail = pl.compute_h3_g1(units_by_seed_fail)
    assert g1_fail["passed"] is False, g1_fail
    assert g1_fail["checks"]["pooled_ge_0_635"] is False, g1_fail
    print("[smoke_cpu] compute_h3_g1 / compute_h3_g2 (pooled + per-seed, pass + fail shapes): PASS")


def check_compute_h3_g3() -> None:
    seeds = [20260710, 20260711]
    # PASS shape: random-direction confab conversion stays low (< 25%) every
    # seed; permuted-gate known-correct damage stays high (> 15%) every seed
    # -- mirrors the resolved single-seed reference (7.0% / 22.9%).
    random_by_seed = {
        seed: [_greedy_rec(f"c{i}", "confab", True, i < 13, False) for i in range(185)]  # 7.0%
        for seed in seeds
    }
    permuted_by_seed = {
        seed: [_greedy_rec(f"k{i}", "known_correct_answered", True, False, i < 59) for i in range(258)]  # 22.9%
        for seed in seeds
    }
    g3 = pl.compute_h3_g3(random_by_seed, permuted_by_seed)
    assert g3["passed"] is True, g3
    assert all(g3["checks"]["random_direction_stays_inert_every_seed"].values()), g3
    assert all(g3["checks"]["permuted_gate_stays_worse_every_seed"].values()), g3

    # FAIL shape: one seed's random direction is NOT inert (converts 40% of
    # confab rows, >= 25% ceiling) -- must flip passed=False for that seed
    # and for the gate overall, exercising the every-seed requirement.
    random_by_seed_fail = dict(random_by_seed)
    random_by_seed_fail[seeds[1]] = [_greedy_rec(f"c{i}", "confab", True, i < 74, False) for i in range(185)]  # 40%
    g3_fail = pl.compute_h3_g3(random_by_seed_fail, permuted_by_seed)
    assert g3_fail["passed"] is False, g3_fail
    assert g3_fail["checks"]["random_direction_stays_inert_every_seed"][seeds[0]] is True, g3_fail
    assert g3_fail["checks"]["random_direction_stays_inert_every_seed"][seeds[1]] is False, g3_fail
    print("[smoke_cpu] compute_h3_g3 (every-seed pass + single-seed fail shapes): PASS")


def check_real_grading_plumbing() -> None:
    # Real gen_lib.grade_clean_tighten and grader.grade_one, pure text
    # processing, no model -- the exact functions AMENDMENT.md requires
    # reusing unchanged from the resolved cell.
    clean_refusal = '{"answer": "I don\'t know the answer", "response_confidence": 0.95}'
    ct = gl.grade_clean_tighten(clean_refusal, terminated_naturally=True)
    assert ct["clean_tighten"] is True, ct

    not_terminated = gl.grade_clean_tighten(clean_refusal, terminated_naturally=False)
    assert not_terminated["clean_tighten"] is False, not_terminated

    correct_answer = '{"answer": "Paris", "response_confidence": 0.9}'
    g = grader.grade_one(correct_answer, aliases=["Paris", "City of Paris"])
    assert g["well_formed_correct"] is True, g

    wrong_answer = '{"answer": "London", "response_confidence": 0.9}'
    g2 = grader.grade_one(wrong_answer, aliases=["Paris", "City of Paris"])
    assert g2["well_formed_correct"] is False, g2
    print("[smoke_cpu] real grading plumbing (gen_lib/grader): PASS")


def check_run_log_resume() -> None:
    with tempfile.TemporaryDirectory() as td:
        log_path = Path(td) / "smoke_run_log.jsonl"
        run_config = {"amendment": "snap-seed-sampled-decode-replication-smoke", "dose_target": 200.0}
        units = [{"unit_key": f"r{i}::20260710"} for i in range(5)]

        log1 = RunLog(log_path, run_config, key_field="unit_key")
        pending1 = list(log1.iter_pending(units, key_fn=lambda u: u["unit_key"]))
        assert len(pending1) == 5
        for u in pending1[:3]:
            log1.record(u["unit_key"], {"unit_key": u["unit_key"], "value": "done"})
        log1.close()

        log2 = RunLog(log_path, run_config, key_field="unit_key")
        pending2 = list(log2.iter_pending(units, key_fn=lambda u: u["unit_key"]))
        assert [u["unit_key"] for u in pending2] == ["r3::20260710", "r4::20260710"], pending2
        for u in pending2:
            log2.record(u["unit_key"], {"unit_key": u["unit_key"], "value": "done"})
        log2.finalize({"n_units": 5})
        log2.close()

        records = pl._load_jsonl_by_key(log_path, "unit_key")
        assert len(records) == 5, records
        assert all(records[f"r{i}::20260710"]["value"] == "done" for i in range(5)), records
    print("[smoke_cpu] RunLog resume round-trip: PASS")


def main() -> int:
    check_gate_decision()
    check_score_row_samples()
    check_wilson_ci_overlap()
    check_seed_and_placebo_helpers()
    check_batched_termination_detection()
    check_compute_h3_g0()
    check_compute_h3_g1_g2()
    check_compute_h3_g3()
    check_real_grading_plumbing()
    check_run_log_resume()
    print("\nALL CPU SMOKE CHECKS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
