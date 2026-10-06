"""Tests for the analysis-time IDK option: insertion at all five positions,
question-level aggregation, the H3 cutoff, position bias and run materialization.

Location: experiments/decision-model-idk-option/tests/test_idk_insertion.py
Run:      python -m pytest experiments/decision-model-idk-option/tests -q

Synthetic rows only; no PopQA text, no model.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import yaml

CELL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CELL))

import idk_harness as H  # noqa: E402

C = H.cfg()
IO = C["idk_option"]
GATES = H._yaml_load(CELL / "gates.yaml")


def _row(qid, task, label=2, knowledge="unknown"):
    return {"kind": "choice", "state": f"Question {qid}?", "instructions": "Which option?",
            "options": [[f"o{i}-{qid}", ""] for i in range(4)], "label": label, "task": task, "weight": 1.0,
            "instruction_variants": [], "meta": {"qid": qid, "knowledge": knowledge}}


def test_registered_idk_text_and_all_five_positions():
    assert IO["text"] == "I don't know" and IO["text"].isascii() and IO["description"] == ""
    assert IO["positions"] == [0, 1, 2, 3, 4]


@pytest.mark.parametrize("slot,label,new_label", [(0, 2, 3), (2, 2, 3), (3, 2, 2), (4, 2, 2), (1, 0, 0)])
def test_insert_shifts_label_and_keeps_relative_order(slot, label, new_label):
    r = _row("q", "t", label=label)
    n = H.insert_idk(r, slot, IO["text"], IO["description"])
    assert len(n["options"]) == 5 and n["options"][slot] == [IO["text"], ""]
    assert [o for i, o in enumerate(n["options"]) if i != slot] == r["options"]
    assert n["label"] == new_label and n["options"][n["label"]] == r["options"][label]
    assert n["meta"]["idk_slot"] == slot
    for k in ("kind", "state", "instructions", "task", "weight", "instruction_variants"):
        assert n[k] == r[k]
    assert len(r["options"]) == 4  # input untouched


def test_five_positions_cover_every_rendered_slot_once():
    r = _row("q", "t", label=1)
    copies = [H.insert_idk(r, k, IO["text"], "") for k in IO["positions"]]
    assert sorted(cp["options"].index([IO["text"], ""]) for cp in copies) == [0, 1, 2, 3, 4]
    for cp in copies:  # real options always in dmcc relative order; gold is always the same text
        assert [o for o in cp["options"] if o[0] != IO["text"]] == r["options"]
        assert cp["options"][cp["label"]] == r["options"][1]


def test_insert_refuses_duplicate_idk_text():
    r = _row("q", "t")
    r["options"][1] = ["i don't know", ""]
    with pytest.raises(ValueError):
        H.insert_idk(r, 0, IO["text"], "")


@pytest.mark.parametrize("k", [0, 1, 2, 3, 4])
def test_engine_split_unchanged_at_every_position(k):
    rows = [_row(f"q{i}", f"popqa:rel{i % 3}", knowledge="known" if i % 7 == 0 else "unknown") for i in range(300)]
    new = [H.insert_idk(r, k, IO["text"], "") for r in rows]
    acfg = {"fit_fraction": 0.4, "cal_fraction": 0.2, "seed": 0}
    assert H.split_qids(new, acfg) == H.split_qids(rows, acfg)


def test_pick_idk_reads_canonical_slot():
    recs = [{"pred": 3, "meta": {"idk_slot": 3}}, {"pred": 2, "meta": {"idk_slot": 3}}]
    assert H.pick_idk_flags(recs) == [True, False]


def _rec(qid, knowledge, pred, slot, conf=0.5, correct=0, p_idk=None):
    r = {"pred": pred, "conf_r1": conf, "correct": correct,
         "meta": {"qid": qid, "knowledge": knowledge, "idk_slot": slot}}
    if p_idk is not None:
        probs = [0.0] * 5
        probs[slot] = p_idk
        r["probs_r1"] = probs
    return r


def _runs(spec):
    """spec: qid -> (knowledge, [IDK picked at positions 0..4], [correct when answered])."""
    runs = {k: [] for k in range(5)}
    for q, (know, picks, rights) in spec.items():
        for k in range(5):
            pred = k if picks[k] else (k + 1) % 5
            runs[k].append(_rec(q, know, pred, k, correct=int(not picks[k] and rights[k]), p_idk=0.1 * k))
    return runs


def test_question_table_rate_is_mean_of_five_indicators_and_shares_sum_to_one():
    qt = H.question_table(_runs({
        "a": ("unknown", [1, 1, 1, 0, 0], [0, 0, 0, 1, 0]),
        "b": ("known", [0, 0, 0, 0, 0], [1, 1, 1, 1, 0]),
        "c": ("unknown", [1, 1, 1, 1, 1], [0] * 5)}))
    assert qt["a"]["idk_rate"] == pytest.approx(0.6) and qt["a"]["right_share"] == pytest.approx(0.2)
    assert qt["a"]["answered_accuracy"] == pytest.approx(0.5)
    assert qt["b"]["idk_rate"] == 0 and qt["b"]["answered_accuracy"] == pytest.approx(0.8)
    assert qt["c"]["idk_rate"] == 1 and qt["c"]["answered_accuracy"] is None
    for v in qt.values():
        assert v["idk_rate"] + v["right_share"] + v["wrong_share"] == pytest.approx(1.0)
    assert qt["a"]["mean_p_idk_r1"] == pytest.approx(0.2)


def test_question_table_refuses_incomplete_or_mislabeled_positions():
    runs = _runs({"a": ("unknown", [0] * 5, [1] * 5), "b": ("known", [0] * 5, [1] * 5)})
    runs[3] = runs[3][:1]
    with pytest.raises(H.StageError):
        H.question_table(runs)
    runs = _runs({"a": ("unknown", [0] * 5, [1] * 5)})
    runs[2][0]["meta"]["idk_slot"] = 1
    with pytest.raises(H.StageError):
        H.question_table(runs)


def test_cluster_bootstrap_resamples_questions():
    out = H.cluster_mean_ci([0.0, 0.2, 1.0, 0.6, None], 500, 0)
    assert out["n_questions"] == 4 and out["mean"] == pytest.approx(0.45)
    assert 0.0 <= out["ci95"][0] <= 0.45 <= out["ci95"][1] <= 1.0
    flat = H.cluster_mean_ci([0.3] * 50, 200, 0)
    assert flat["ci95"] == [pytest.approx(0.3), pytest.approx(0.3)]


def test_tau_rule_abstains_on_exactly_k_cal_known():
    conf = [0.9, 0.3, 0.5, 0.7, 0.2, 0.6, 0.8, 0.4, 0.95, 0.35]
    tau, k = H.tau_from_cal(conf, 0.2)
    assert k == 2 and sum(x < tau for x in conf) == 2
    tau0, k0 = H.tau_from_cal(conf, 0.0)
    assert k0 == 0 and sum(x < tau0 for x in conf) == 0
    taun, kn = H.tau_from_cal(conf, 1.0)
    assert kn == 10 and taun == float("inf")


def test_h3_question_level_cal_fit_matched_delta():
    gates = json.loads(json.dumps(GATES))
    gates["g0_floors"]["min_cal_known"] = 10
    # CAL: 20 known questions at question-level IDK rate 0.2 -> r_cal 0.2.
    # Unknown CAL questions (IDK everywhere, very low no-IDK R1) must not move tau.
    cal_spec = {f"c{i}": ("known", [1, 0, 0, 0, 0], [1] * 5) for i in range(20)}
    cal_spec.update({f"cu{i}": ("unknown", [1] * 5, [0] * 5) for i in range(30)})
    qt_cal = H.question_table(_runs(cal_spec))
    no_cal = [_rec(f"c{i}", "known", 1, None, conf=(i + 1) / 20) for i in range(20)] + \
        [_rec(f"cu{i}", "unknown", 1, None, conf=0.01) for i in range(30)]
    # TEST: 40 known at IDK rate 0.2; 40 unknown_true at 0.8 (30 of them) or 0.0 (10).
    t_spec = {f"k{i}": ("known", [1, 0, 0, 0, 0], [1] * 5) for i in range(40)}
    t_spec.update({f"u{i}": ("unknown", [1, 1, 1, 1, 0] if i < 30 else [0] * 5, [0] * 5) for i in range(40)})
    qt = H.question_table(_runs(t_spec))
    no_test = [_rec(f"k{i}", "known", 1, None, conf=(i + 1) / 40) for i in range(40)] + \
        [_rec(f"u{i}", "unknown", 1, None, conf=0.2 if i < 10 else 0.9) for i in range(40)]
    group_of = {f"u{i}": "unknown_true" for i in range(40)}
    out = H.h3_compare(qt, qt_cal, no_test, no_cal, group_of, gates, 500, 0)
    assert out["r_cal_question_level_over_idk"] == pytest.approx(0.2) and out["k_cal_abstain"] == 4
    assert out["tau"] == pytest.approx(0.25)
    assert out["test_over_idk"] == pytest.approx(0.2) and out["test_over_threshold"] == pytest.approx(0.225)
    assert out["matched"] is True
    assert out["recall_idk"] == pytest.approx(0.6) and out["recall_threshold"] == pytest.approx(0.25)
    assert out["verdict"] == "IDK_BETTER"


def test_position_table_flags_strong_position_effect():
    qt = H.question_table(_runs({f"q{i}": ("known", [1, 0, 0, 0, 0] if i < 5 else [0] * 5, [1] * 5)
                                 for i in range(20)}))
    tab = H.position_table(qt, {"pooled": list(qt)}, [0, 1, 2, 3, 4], 0.10)
    assert tab["pooled"]["by_position"][1]["rate"] == pytest.approx(0.25)  # reported as positions 1..5
    assert tab["pooled"]["range"] == pytest.approx(0.25) and tab["pooled"]["strong_position_effect"] is True
    flat = H.question_table(_runs({f"q{i}": ("known", [0] * 5, [1] * 5) for i in range(10)}))
    assert H.position_table(flat, {"pooled": list(flat)}, [0, 1, 2, 3, 4], 0.10)["pooled"][
        "strong_position_effect"] is False


def test_run_keys_and_specs_twelve_runs():
    keys = H.run_keys(C)
    assert len(keys) == 12 and "idk_p4_letter_logits" in keys and "noidk_pointer" in keys
    s = H.run_spec(C, "idk_p3_pointer")
    assert s["run_id"] == "dmio-idk-p3-pointer" and s["position"] == 3 and s["arm"] == "idk"
    assert s["rows_source"].name == "decision_rows_idk_p3.jsonl"
    with pytest.raises(H.StageError):
        H.run_spec(C, "idk_p5_pointer")


@pytest.mark.parametrize("model", ["pointer", "letter_logits"])
def test_template_materialization_rewrites_every_run_path(model):
    t = C["idk_runs"][model]
    for kind in ("analysis_config", "recipe"):
        text = H.rp(t[kind]).read_text(encoding="utf-8")
        assert t["template_run_id"] in text
        for k in IO["positions"]:
            rid = t["run_id_template"].format(position=k)
            out = H.materialize(text, t["template_run_id"], rid)
            if k != 0:
                assert t["template_run_id"] not in out
            assert rid in out
            if kind == "analysis_config":
                cfg = yaml.safe_load(out)
                assert cfg["checkpoint"] == f"scratch/eh_staging/{rid}/final_model"
                assert cfg["data"]["files"] == [f"scratch/eh_staging/{rid}/{C['staged_rows_name']['idk']}"]
                assert cfg["output"]["output_root"] == f"scratch/eh_staging/{rid}/output"


@pytest.mark.parametrize("name", ["analysis_idk_pointer.yaml", "analysis_noidk_pointer.yaml",
                                  "analysis_idk_letter_logits.yaml", "analysis_noidk_letter_logits.yaml"])
def test_every_engine_config_exports_cal_rows_for_h3(name):
    cfg = H._yaml_load(CELL / name)
    assert cfg["export"]["cal_rows"] is True and cfg["export"]["per_row"] is True
    assert "directions" not in cfg
    assert cfg["data"] == {"files": cfg["data"]["files"], "max_rows": None, "fit_fraction": 0.4,
                           "cal_fraction": 0.2, "seed": 0}


def test_gates_are_question_level_with_confirmed_thresholds():
    assert GATES["ci"]["unit"] == "question"
    assert GATES["h1_idk_recall"]["threshold"] == 0.50 and GATES["h1_idk_recall"]["ci"].startswith("cluster")
    assert GATES["h2_over_idk"]["threshold"] == 0.10 and GATES["h2_over_idk"]["ci"].startswith("cluster")
    assert GATES["r0_v1_positive_control"]["threshold"] == 0.80
    assert GATES["r0_v2_format_adherence"]["threshold"] == 0.95
    assert GATES["secondary_descriptive"]["position_bias"]["strong_range"] == 0.10
