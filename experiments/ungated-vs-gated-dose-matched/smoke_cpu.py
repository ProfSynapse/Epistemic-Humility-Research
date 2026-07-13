#!/usr/bin/env python3
"""H4 ungated-vs-gated -- CPU-only smoke (NO GPU, NO real model load).

Exercises the harness's non-generation logic on synthetic data: the gate's
fire-decision math, the dual-record -> gated/ungated arm construction, the
paired McNemar computation, the gate-pass/fail wiring (compute_h4_gates), the
REAL grading functions (gen_lib.grade_clean_tighten, grader.grade_one -- pure
text processing, no model), and a RunLog round-trip proving the per-row
resume contract actually works with the pinned synaptic-tuner submodule.

This is NOT a substitute for the GPU smoke (`pipeline.py --mode smoke`),
which is the only thing that can prove generation, the write hook, and
readback wiring are correct. This script proves everything ELSE: the
arithmetic and control flow this build task can validate without a
multi-gigabyte model load on a CPU-only / no-GPU host.

Run: python smoke_cpu.py
Exit 0 and "ALL CPU SMOKE CHECKS PASSED" on success; raises AssertionError
(nonzero exit) on any failure.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent / "synaptic-tuner"))

import gen_lib as gl  # noqa: E402
import grader  # noqa: E402
import model_lib as ml  # noqa: E402
import pipeline as pl  # noqa: E402
from shared.utilities.run_log import RunLog  # noqa: E402


def check_gate_decision() -> None:
    # tau_frozen = 0.3026445054171378 (real frozen value, gates.yaml).
    tau = 0.3026445054171378
    mu_d, sigma_d = -27.0, 16.0

    # A confab-like row: LOW doubt (low proj_d) -> high neg_z_d -> should fire.
    d = pl.gate_decision(proj_d=-60.0, mu_d=mu_d, sigma_d=sigma_d, tau=tau)
    assert d["fire"] is True, d
    assert -2.0 <= d["z_d"] <= 2.0

    # A known-correct-like row: HIGH doubt (high proj_d) -> low/negative
    # neg_z_d -> should NOT fire.
    d2 = pl.gate_decision(proj_d=10.0, mu_d=mu_d, sigma_d=sigma_d, tau=tau)
    assert d2["fire"] is False, d2

    # Clipping: an extreme proj_d must clip z_d to [-2, 2], not silently
    # blow past it (this is the exact standardization convention build_directions.py
    # / gate_fit.py use -- if this drifted, the reproduction gate H4-G0 would
    # be scored against a differently-standardized score than the resolved
    # cell used).
    d3 = pl.gate_decision(proj_d=-10000.0, mu_d=mu_d, sigma_d=sigma_d, tau=tau)
    assert d3["z_d"] == -2.0, d3
    d4 = pl.gate_decision(proj_d=10000.0, mu_d=mu_d, sigma_d=sigma_d, tau=tau)
    assert d4["z_d"] == 2.0, d4

    # Boundary: score exactly at tau must fire (">=", not ">").
    d5 = pl.gate_decision(proj_d=mu_d - tau * sigma_d, mu_d=mu_d, sigma_d=sigma_d, tau=tau)
    assert abs(d5["score_neg_z_d"] - tau) < 1e-9
    assert d5["fire"] is True, d5
    print("[smoke_cpu] gate_decision: PASS")


def _dual(row_key: str, role: str, fire: bool, base_ct: bool, base_wfc: bool,
          dosed_ct: bool, dosed_wfc: bool) -> dict:
    """Synthetic dual (baseline+dosed) record in the exact shape
    run_one_row_dual produces, without ever calling it (no model)."""
    return {
        "row_key": row_key, "role": role, "category_canon": "synthetic", "fire": fire,
        "score_neg_z_d": 0.5 if fire else -0.5, "tau": 0.3026445054171378,
        "readback_measured": 200.1 if fire else None,
        "baseline": {
            "text": "synthetic-baseline", "terminated_naturally": True,
            "clean_tighten": {"clean_tighten": base_ct},
            "well_formed_correct": {"well_formed_correct": base_wfc},
        },
        "dosed": {
            "text": "synthetic-dosed", "terminated_naturally": True,
            "clean_tighten": {"clean_tighten": dosed_ct},
            "well_formed_correct": {"well_formed_correct": dosed_wfc},
        },
    }


def check_build_arm_records() -> None:
    # Fired confab row: gated arm must read the DOSED grade (clean_tighten
    # True), matching the ungated arm's grade exactly (same generation).
    dual_fired = _dual("r1", "confab", fire=True, base_ct=False, base_wfc=False,
                        dosed_ct=True, dosed_wfc=False)
    gated, ungated = pl.build_arm_records(dual_fired)
    assert gated["clean_tighten"] is True and gated["dosed"] is True, gated
    assert ungated["clean_tighten"] is True and ungated["dosed"] is True, ungated
    assert gated == ungated, "fired row: gated and ungated must be identical (same dosed pass)"

    # Non-fired confab row: gated arm must fall back to the BASELINE grade
    # (clean_tighten False here), while ungated still uses the dosed grade.
    dual_nonfired = _dual("r2", "confab", fire=False, base_ct=False, base_wfc=True,
                          dosed_ct=True, dosed_wfc=False)
    gated2, ungated2 = pl.build_arm_records(dual_nonfired)
    assert gated2["dosed"] is False and gated2["clean_tighten"] is False, gated2
    assert ungated2["dosed"] is True and ungated2["clean_tighten"] is True, ungated2

    # Non-fired known-correct row where baseline itself is correct: gated
    # not_well_formed_correct must be False (baseline correct, untouched),
    # ungated not_well_formed_correct must be True (dosed pass damaged it).
    dual_known = _dual("r3", "known_correct_answered", fire=False, base_ct=False, base_wfc=True,
                       dosed_ct=False, dosed_wfc=False)
    gated3, ungated3 = pl.build_arm_records(dual_known)
    assert gated3["not_well_formed_correct"] is False, gated3
    assert ungated3["not_well_formed_correct"] is True, ungated3
    print("[smoke_cpu] build_arm_records: PASS")


def check_mcnemar() -> None:
    # b=c=0: no discordant pairs, null-consistent, p must be exactly 1.0.
    r0 = ml.mcnemar_exact(0, 0)
    assert r0["p_value"] == 1.0 and r0["n_discordant"] == 0, r0

    # Symmetric discordance (b==c): p must be 1.0 regardless of magnitude
    # (perfectly consistent with the null of marginal homogeneity).
    r1 = ml.mcnemar_exact(10, 10)
    assert abs(r1["p_value"] - 1.0) < 1e-9, r1

    # Extreme asymmetry over a decent sample: must be highly significant.
    # b=0 (gated damages nothing extra), c=50 (ungated damages 50 rows gated
    # does not) -- this is the shape H4-G1 is designed to detect.
    r2 = ml.mcnemar_exact(0, 50)
    assert r2["p_value"] < 0.001, r2

    # A known small textbook case: b=1, c=9 (n=10) -- exact two-sided
    # binomial p from Binomial(10, 0.5): P(X<=1)=11/1024, p=2*11/1024.
    r3 = ml.mcnemar_exact(1, 9)
    expected_p = 2 * 11 / 1024
    assert abs(r3["p_value"] - expected_p) < 1e-9, (r3, expected_p)
    print("[smoke_cpu] mcnemar_exact: PASS")


def check_compute_h4_gates_pass_case() -> None:
    # Construct a synthetic dataset shaped like the PREDICTED outcome: gate
    # reproduces the resolved reference, ungated known-correct damage
    # greatly exceeds gated, ungated/gated confab conversion are close.
    gated_confab = [{"clean_tighten": i < 136} for i in range(185)]       # 136/185 = 73.51%
    ungated_confab = [{"clean_tighten": i < 150} for i in range(185)]     # 150/185 = 81.08%

    gated_known = [{"row_key": f"k{i}", "not_well_formed_correct": i < 8} for i in range(258)]  # 8/258=3.10%
    # ungated damages 90/258 = 34.9%, all discordant against gated (b=0 by construction).
    ungated_known = [{"row_key": f"k{i}", "not_well_formed_correct": i < 90} for i in range(258)]

    gates = pl.compute_h4_gates(gated_confab, gated_known, ungated_confab, ungated_known)

    g0 = gates["h4_g0_gate_on_reproduction"]
    assert g0["passed"] is True, g0
    g1 = gates["h4_g1_gate_certifies_selectivity"]
    assert g1["passed"] is True, g1
    assert g1["n_paired"] == 258 and g1["n_unpaired_rows_dropped"] == 0, g1
    g2 = gates["h4_g2_conversion_preserved"]
    assert g2["passed"] is True, g2
    print("[smoke_cpu] compute_h4_gates (predicted-shape PASS case): PASS")


def check_compute_h4_gates_falsifier_case() -> None:
    # Construct the FALSIFIER shape: ungated known-correct damage is about
    # as harmless as gated (gap << 15pp) -- H4-G1 must report passed=False,
    # exercising the failure path, not just the happy path.
    gated_confab = [{"clean_tighten": i < 136} for i in range(185)]
    ungated_confab = [{"clean_tighten": i < 136} for i in range(185)]

    gated_known = [{"row_key": f"k{i}", "not_well_formed_correct": i < 8} for i in range(258)]
    ungated_known = [{"row_key": f"k{i}", "not_well_formed_correct": i < 10} for i in range(258)]

    gates = pl.compute_h4_gates(gated_confab, gated_known, ungated_confab, ungated_known)
    g1 = gates["h4_g1_gate_certifies_selectivity"]
    assert g1["passed"] is False, g1
    assert g1["checks"]["gap_ge_0_15"] is False, g1
    print("[smoke_cpu] compute_h4_gates (falsifier-shape FAIL case): PASS")


def check_unpaired_rows_are_dropped_not_silently_wrong() -> None:
    gated_known = [{"row_key": "a", "not_well_formed_correct": False},
                   {"row_key": "b", "not_well_formed_correct": True}]
    ungated_known = [{"row_key": "b", "not_well_formed_correct": True},
                     {"row_key": "c", "not_well_formed_correct": False}]
    gates = pl.compute_h4_gates([], gated_known, [], ungated_known)
    g1 = gates["h4_g1_gate_certifies_selectivity"]
    assert g1["n_paired"] == 1 and g1["n_unpaired_rows_dropped"] == 2, g1
    print("[smoke_cpu] unpaired-row handling: PASS")


def check_real_grading_plumbing() -> None:
    # Real gen_lib.grade_clean_tighten and grader.grade_one, pure text
    # processing, no model -- these are the exact functions AMENDMENT.md
    # requires reusing unchanged.
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
        run_config = {"amendment": "ungated-vs-gated-dose-matched-smoke", "dose_target": 200.0}
        rows = [{"row_key": f"r{i}"} for i in range(5)]

        log1 = RunLog(log_path, run_config, key_field="row_key")
        pending1 = list(log1.iter_pending(rows, key_fn=lambda r: r["row_key"]))
        assert len(pending1) == 5
        for r in pending1[:3]:
            log1.record(r["row_key"], {"row_key": r["row_key"], "value": "done"})
        log1.close()

        # Simulate a restart: reopen the SAME path, confirm only the
        # remaining 2 rows are pending.
        log2 = RunLog(log_path, run_config, key_field="row_key")
        pending2 = list(log2.iter_pending(rows, key_fn=lambda r: r["row_key"]))
        assert [r["row_key"] for r in pending2] == ["r3", "r4"], pending2
        for r in pending2:
            log2.record(r["row_key"], {"row_key": r["row_key"], "value": "done"})
        log2.finalize({"n_rows": 5})
        log2.close()

        records = pl._load_jsonl_by_key(log_path, "row_key")
        assert len(records) == 5, records
        assert all(records[f"r{i}"]["value"] == "done" for i in range(5)), records
    print("[smoke_cpu] RunLog resume round-trip: PASS")


def main() -> int:
    check_gate_decision()
    check_build_arm_records()
    check_mcnemar()
    check_compute_h4_gates_pass_case()
    check_compute_h4_gates_falsifier_case()
    check_unpaired_rows_are_dropped_not_silently_wrong()
    check_real_grading_plumbing()
    check_run_log_resume()
    print("\nALL CPU SMOKE CHECKS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
