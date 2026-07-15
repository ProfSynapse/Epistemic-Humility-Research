"""CPU smoke for report.py's build_report/build_family_report on synthetic
fixtures -- proves the report-assembly code path (runlog+adjudication merge ->
paired_delta -> criterion -> per-family verdict -> committed aggregate JSON)
runs end-to-end without any real generation/grading data, and that the
registered final rate rule (refused_final = detector_v2_refused OR
adjudicated_abstention, per row; cell.yaml write_law.final_rate_rule) is
implemented: detector-refused rows enter the paired join as refused_final True
instead of being dropped as missing. Run via
`python3 -m pytest test_report_smoke.py -v` (explicit file path)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import config  # noqa: E402
import report  # noqa: E402


def _write_runlog(analysis_dir: Path, family: str, arm: str, seed, rows: list[dict]) -> None:
    runlog = analysis_dir / "runlog"
    runlog.mkdir(parents=True, exist_ok=True)
    if arm == "baseline":
        path = runlog / f"{family}__baseline_reused.jsonl"
    else:
        path = runlog / f"{family}__random_direction__seed{seed}.jsonl"
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


def _synthetic_family(analysis_dir: Path, family: str, s_row_keys: list[str], seeds: list[int],
                      dosed_bias: float, detector_refused_every: int = 0) -> list[dict]:
    """Baseline: fixed low refusal rate. Dosed: refusal rate shifted by
    dosed_bias so every seed shares the same sign. When detector_refused_every
    is n > 0, every n-th dosed row is detector-refused in the runlog and
    OMITTED from the applied rows (as build_pool.py does in production); the
    merge rule must count those rows refused_final True, not drop them."""
    applied = []
    base_runlog = []
    for i, rk in enumerate(s_row_keys):
        base_runlog.append({"row_key": rk, "refused_v2": False})
        applied.append({"cell": family, "arm": "baseline", "row_key": rk, "seed": None,
                        "refused_final": (i % 10 == 0)})
    _write_runlog(analysis_dir, family, "baseline", None, base_runlog)
    for seed in seeds:
        dosed_runlog = []
        for i, rk in enumerate(s_row_keys):
            det_refused = detector_refused_every > 0 and (i % detector_refused_every == 1)
            dosed_runlog.append({"row_key": rk, "refused_v2": det_refused})
            if det_refused:
                continue  # production: refused rows never enter the grading pool
            base_refused = i % 10 == 0
            flip_frac = abs(dosed_bias)
            flip = (i % 100) < int(flip_frac * 100)
            refused = (not base_refused) if (flip and dosed_bias > 0) else base_refused
            if dosed_bias < 0:
                refused = False if flip else base_refused
            applied.append({"cell": family, "arm": "random_direction", "row_key": rk,
                            "seed": seed, "refused_final": refused})
        _write_runlog(analysis_dir, family, "random_direction", seed, dosed_runlog)
    return applied


def _manifests(s_row_keys: dict[str, list[str]], seeds_by_family: dict[str, list[int]]):
    subsample_manifest = {
        "seed": config.SUBSAMPLE_PERMUTATION_SEED,
        "families": {fam: {"row_keys": s_row_keys.get(fam, [])} for fam in config.FAMILIES},
    }
    ledger_summary = {
        "families": {fam: {"accepted_seeds": seeds_by_family.get(fam, [])} for fam in config.FAMILIES},
    }
    return subsample_manifest, ledger_summary


def test_build_report_end_to_end_on_synthetic_fixtures(tmp_path):
    s_row_keys = {fam: [f"{fam}_row{i}" for i in range(40)] for fam in config.FAMILIES}
    seeds = {fam: list(config.SEED_BLOCKS[fam]) for fam in config.FAMILIES}
    subsample_manifest, ledger_summary = _manifests(s_row_keys, seeds)

    applied_rows = []
    applied_rows += _synthetic_family(tmp_path, "qwen35_4b", s_row_keys["qwen35_4b"], seeds["qwen35_4b"], dosed_bias=-0.5)
    applied_rows += _synthetic_family(tmp_path, "mistral7b_v03", s_row_keys["mistral7b_v03"], seeds["mistral7b_v03"], dosed_bias=0.5)
    applied_rows += _synthetic_family(tmp_path, "llama32_3b", s_row_keys["llama32_3b"], seeds["llama32_3b"], dosed_bias=0.0)

    out = report.build_report(applied_rows, subsample_manifest, ledger_summary, tmp_path)

    assert set(out["families"].keys()) == set(config.FAMILIES)
    for fam in config.FAMILIES:
        fr = out["families"][fam]
        assert fr["complete"] is True
        assert fr["n_seeds_present"] == config.K_SEEDS_PER_FAMILY
        assert fr["criterion"]["verdict"] in (
            "SURVIVES", "RETIRED", "INDETERMINATE",
            "NEAR_ZERO_NULL_HOLDS", "NEWLY_DISCOVERED_POSITIVE_SIGN", "NEWLY_DISCOVERED_NEGATIVE_SIGN",
            "INDETERMINATE_NULL_CONTROL",
        )
    assert out["families"]["llama32_3b"]["criterion"]["committed_sign"] == "none"
    assert out["families"]["qwen35_4b"]["criterion"]["committed_sign"] == "negative"
    assert out["families"]["mistral7b_v03"]["criterion"]["committed_sign"] == "positive"


def test_detector_refused_rows_count_as_refused_final_true(tmp_path):
    """The registered rule verbatim: refused_final = detector_v2_refused OR
    adjudicated_abstention. Dosed rows detector-refused in the runlog (and
    therefore absent from the applied adjudication output) must enter the
    paired join as refused_final True -- NOT be dropped as missing."""
    fam = "qwen35_4b"
    s_row_keys = {fam: [f"{fam}_row{i}" for i in range(40)]}
    seeds = {fam: list(config.SEED_BLOCKS[fam])}
    subsample_manifest, ledger_summary = _manifests(s_row_keys, seeds)

    # every 4th dosed row (i % 4 == 1 -> 10 of 40) detector-refused
    applied_rows = _synthetic_family(tmp_path, fam, s_row_keys[fam], seeds[fam],
                                     dosed_bias=0.0, detector_refused_every=4)
    out = report.build_report(applied_rows, subsample_manifest, ledger_summary, tmp_path)
    fr = out["families"][fam]
    for ps in fr["per_seed"]:
        # nothing missing: refused rows joined with value True
        assert ps["n_missing"] == 0
        assert ps["n_paired"] == 40
        assert ps["n_detector_refused_dosed"] == 10
        # baseline rate 4/40 = 10%; dosed = 10 detector-refused + the 4
        # baseline-pattern graded refusals (i%10==0 never collides with i%4==1)
        assert ps["dosed_rate"]["successes"] == 14
        assert ps["baseline_rate"]["successes"] == 4


def test_non_refused_ungraded_rows_stay_missing(tmp_path):
    """A detector-non-refused row with no adjudication value has no
    refused_final under the rule; it must be reported missing, never
    defaulted to either value."""
    fam = "qwen35_4b"
    keys = [f"{fam}_row{i}" for i in range(10)]
    seeds = {fam: list(config.SEED_BLOCKS[fam])[:1]}
    subsample_manifest, ledger_summary = _manifests({fam: keys}, seeds)
    seed = seeds[fam][0]

    _write_runlog(tmp_path, fam, "baseline", None, [{"row_key": rk, "refused_v2": False} for rk in keys])
    _write_runlog(tmp_path, fam, "random_direction", seed, [{"row_key": rk, "refused_v2": False} for rk in keys])
    # adjudication output covers all baseline rows but only 7 dosed rows
    applied_rows = [{"cell": fam, "arm": "baseline", "row_key": rk, "seed": None, "refused_final": False} for rk in keys]
    applied_rows += [{"cell": fam, "arm": "random_direction", "row_key": rk, "seed": seed, "refused_final": False} for rk in keys[:7]]

    out = report.build_report(applied_rows, subsample_manifest, ledger_summary, tmp_path)
    ps = out["families"][fam]["per_seed"][0]
    assert ps["n_paired"] == 7
    assert ps["n_missing"] == 3


def test_build_report_marks_incomplete_when_fewer_than_k_seeds_present(tmp_path):
    fam = "qwen35_4b"
    s_row_keys = {fam: [f"{fam}_row{i}" for i in range(20)]}
    partial_seeds = {fam: list(config.SEED_BLOCKS[fam])[:3]}
    subsample_manifest, ledger_summary = _manifests(s_row_keys, partial_seeds)
    applied_rows = _synthetic_family(tmp_path, fam, s_row_keys[fam], partial_seeds[fam], dosed_bias=-0.5)
    out = report.build_report(applied_rows, subsample_manifest, ledger_summary, tmp_path)
    fr = out["families"][fam]
    assert fr["n_seeds_present"] == 3
    assert fr["complete"] is False


def test_report_writes_no_row_level_text_only_aggregates(tmp_path):
    s_row_keys = {fam: [f"{fam}_row{i}" for i in range(20)] for fam in config.FAMILIES}
    seeds = {fam: list(config.SEED_BLOCKS[fam])[:2] for fam in config.FAMILIES}
    subsample_manifest, ledger_summary = _manifests(s_row_keys, seeds)
    applied_rows = []
    for fam in config.FAMILIES:
        applied_rows += _synthetic_family(tmp_path, fam, s_row_keys[fam], seeds[fam], dosed_bias=0.3)
    out = report.build_report(applied_rows, subsample_manifest, ledger_summary, tmp_path)

    blob = json.dumps(out)
    # containment: aggregate-only report must never carry answer/question text
    assert "answer_text" not in blob
    assert "question" not in blob
