"""Tests for the pre-registered exemplar-collision exclusion (PI, 2026-10-05).

Location: experiments/decision-model-calibrated-choice/tests/test_exemplar_collision_exclusion.py
Run:      python -m pytest experiments/decision-model-calibrated-choice/tests -q

Rule (dmcc_harness.exemplar_collision_qids): a PopQA row is excluded from every
primary analysis iff any normalized gold alias (possible_answers plus obj) equals
a normalized base-mode exemplar answer. Synthetic rows only; no PopQA text.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

CELL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CELL))

import dmcc_harness as H  # noqa: E402


def _row(qid, aliases, obj, prop="country"):
    return {"qid": qid, "question": f"In what country is {qid}?", "prop": prop, "subj": qid,
            "obj": obj, "aliases": aliases, "s_pop": 10}


META = [
    _row("q-au", ["Australia", "AU", "Commonwealth of Australia"], "Australia"),
    _row("q-au-dots", ["A.U."], "Somewhere"),            # normalizes to "a u", not "au"
    _row("q-austria", ["Austria", "AT"], "Austria"),
    _row("q-six", ["6"], "Six", prop="genre"),             # obj collides with exemplar "Six"
    _row("q-jupiter", ["Jupiter Records"], "Jupiter Records", prop="producer"),  # superstring only
    _row("q-everest", ["mount everest"], "Nepal"),        # alias collides with "Mount Everest"
    _row("q-fr", ["France", "FR"], "France"),
    _row("q-de", ["Germany", "DE"], "Germany"),
]


def test_exemplar_answer_norms_match_amendment_y():
    assert H.exemplar_answer_norms() == {"jupiter", "six", "au", "1945", "mount everest"}


def test_rule_is_exact_normalized_alias_match():
    assert H.exemplar_collision_qids(META) == ["q-au", "q-six", "q-everest"]


def test_excluded_rows_never_enter_primary_rows_and_split_happens_after():
    probe = {m["qid"]: {"label": "known", "greedy_correct": True, "p_correct": 1.0} for m in META}
    ch = {"n_options": 4, "instructions": "x", "seed": 0, "include_ambiguous_in_primary": False}
    pool = META + [_row(f"pad-{i}", [f"Country{i}"], f"Country{i}") for i in range(4)] + \
        [_row(f"padg-{i}", [f"Genre{i}"], f"Genre{i}", prop="genre") for i in range(4)] + \
        [_row(f"padp-{i}", [f"Label{i}"], f"Label{i}", prop="producer") for i in range(4)]
    probe.update({m["qid"]: {"label": "known", "greedy_correct": True, "p_correct": 1.0} for m in pool})
    excl = set(H.exemplar_collision_qids(pool))
    rows, counts, skipped = H.build_choice_rows(pool, probe, ch, {"known": "known", "unknown": "unknown",
                                                                  "discard": "ambiguous"}, 32, "sha",
                                                exclude_qids=excl)
    kept = {r["meta"]["qid"] for r in rows}
    assert not (kept & excl)
    assert skipped["exemplar_answer_collision"] == len(excl) == 3
    fit, cal, test = H.engine_split(rows, 0.4, 0.2, 0)
    assert not ({r["meta"]["qid"] for r in fit + cal + test} & excl)
    assert len(fit) + len(cal) + len(test) == len(rows)


def test_committed_popqa_list_matches_pinned_count():
    rec = json.loads((CELL / "analysis-committed" / "exemplar_collision_qids.json").read_text(encoding="utf-8"))
    gates = H._yaml_load(CELL / "gates.yaml")
    assert rec["n"] == len(rec["qids"]) == gates["g0_exemplar_collision_exclusion"]["expected_count"] == 27
    assert rec["matched_by"] == {"au": 27}
