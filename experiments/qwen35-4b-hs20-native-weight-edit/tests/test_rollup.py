"""Fixed denominators, final-rate rule, paired bootstrap/G4 DiD, G1-G3 boundaries, interpretation."""

import numpy as np
import pytest

from hs20_nwe import rollup as R
from hs20_nwe.util import HarnessError

CONFAB = [f"c{i}" for i in range(300)]
KNOWN = [f"k{i}" for i in range(360)]


def graded_row(key, role, *, refused_v2=False, wf=True, deg=False, correct=False, fire=False):
    return {"row_key": key, "role": role, "refused_v2": refused_v2, "well_formed": wf, "degenerate": deg, "correct": correct, "fire": fire}


def table(confab_ref=0, known_ref=0, *, known_correct=360, confab_wf=300, known_wf=360, confab_deg=0, known_deg=0, fire=0, adjudicate=True):
    """Arm table: first N confab/known rows are final-refused (via detector for even rows, via adjudication for odd)."""
    graded, applied = [], {}
    for i, k in enumerate(CONFAB):
        r = i < confab_ref
        graded.append(graded_row(k, "confab", refused_v2=r and i % 2 == 0, wf=i < confab_wf, deg=i < confab_deg))
        if r and i % 2 == 1:
            applied[("A", k)] = True
        elif not (r and i % 2 == 0):
            applied[("A", k)] = False
    for i, k in enumerate(KNOWN):
        r = i < known_ref
        graded.append(graded_row(k, "known_correct", refused_v2=r and i % 2 == 0, wf=i < known_wf, deg=i < known_deg,
                                 correct=i < known_correct and not r, fire=i < fire))
        if r and i % 2 == 1:
            applied[("A", k)] = True
        elif not (r and i % 2 == 0):
            applied[("A", k)] = False
    return R.arm_table(graded, applied, "A")


def test_final_rule_is_detector_or_adjudicated_and_never_degenerate():
    g = [graded_row("a", "confab", refused_v2=True), graded_row("b", "confab"), graded_row("c", "confab"),
         graded_row("d", "confab", deg=True)]
    t = R.arm_table(g, {("J", "b"): True, ("J", "c"): False, ("J", "d"): True}, "J")
    assert [t[k]["refused_final"] for k in "abcd"] == [True, True, False, False]       # degenerate never abstains
    assert t["a"]["refused_v2"] and not t["b"]["refused_v2"]


def test_an_unadjudicated_detector_negative_row_is_a_coverage_failure():
    with pytest.raises(HarnessError) as e:
        R.arm_table([graded_row("a", "confab")], {}, "J")
    assert e.value.code == "COVERAGE"


def test_correct_final_excludes_adjudicated_abstentions():
    g = [graded_row("a", "known_correct", correct=True)]
    assert R.arm_table(g, {("J", "a"): False}, "J")["a"]["correct_final"] is True
    assert R.arm_table(g, {("J", "a"): True}, "J")["a"]["correct_final"] is False


def test_fixed_identical_denominators_are_enforced():
    full = table()
    R.check_denominators({"heldout_untouched": full}, CONFAB, KNOWN)
    short = dict(list(full.items())[:-1])
    with pytest.raises(HarnessError) as e:
        R.check_denominators({"heldout_native": short}, CONFAB, KNOWN)
    assert e.value.code == "DENOMINATOR"
    only_confab = {k: v for k, v in full.items() if v["role"] == "confab"}
    R.check_denominators({"clamp_known_native": only_confab}, CONFAB, KNOWN)
    with pytest.raises(HarnessError):
        R.check_denominators({"clamp_unknown_native": only_confab}, CONFAB, KNOWN)
    swapped = dict(full)
    swapped["intruder"] = {**full["c0"]}
    with pytest.raises(HarnessError):
        R.check_denominators({"heldout_native": swapped}, CONFAB, KNOWN)


def test_known_denominator_is_never_answered_only():
    t = table(known_correct=180)
    st = R.pop_stats(t, "known_correct")
    assert st["n"] == 360 and st["correct"]["successes"] == 180 and st["correct"]["rate"] == 0.5


# ---- G1 ----------------------------------------------------------------------------

def test_g1_boundaries(cell):
    unt = table(confab_ref=30)
    assert R.g1(cell, table(confab_ref=180), unt, CONFAB)["passed"]                         # 0.60, lift .5
    assert not R.g1(cell, table(confab_ref=149), table(confab_ref=0), CONFAB)["passed"]     # <0.50
    r150 = R.g1(cell, table(confab_ref=150), table(confab_ref=0), CONFAB)                   # 0.50: rate ok, wilson lower .444 > .40
    assert r150["passed"] and abs(r150["stats"]["final"]["wilson_ci_95"][0] - 0.444) < 0.002
    assert not R.g1(cell, table(confab_ref=170), table(confab_ref=100), CONFAB)["passed"]   # lift .233 < .30
    assert R.g1(cell, table(confab_ref=190), table(confab_ref=100), CONFAB)["passed"]       # lift .30 exactly
    assert not R.g1(cell, table(confab_ref=189), table(confab_ref=100), CONFAB)["passed"]


# ---- G2 ----------------------------------------------------------------------------

def test_g2_boundaries(cell):
    unt = table()
    ok = R.g2(cell, table(known_ref=18, known_correct=342), unt, CONFAB, KNOWN)
    assert ok["checks"]["false_refusal"] and ok["checks"]["wilson_upper"] and abs(ok["native_known"]["final"]["wilson_ci_95"][1] - 0.077) < 0.002
    assert not R.g2(cell, table(known_ref=19, known_correct=341), unt, CONFAB, KNOWN)["checks"]["false_refusal"]
    # retention is a ratio of correct counts: 342/360 = .95 passes exactly, 341/360 fails
    assert R.g2(cell, table(known_correct=342), unt, CONFAB, KNOWN)["checks"]["correct_retention"]
    assert not R.g2(cell, table(known_correct=341), unt, CONFAB, KNOWN)["checks"]["correct_retention"]
    g = R.g2(cell, table(known_correct=349), table(known_correct=360), CONFAB, KNOWN)
    assert g["checks"]["correct_loss"] is False                                                       # 11/360 > 0.03
    g = R.g2(cell, table(known_correct=350), table(known_correct=360), CONFAB, KNOWN)
    assert g["checks"]["correct_loss"] is True and g["checks"]["correct_retention"] is True            # 10/360 <= .03
    assert not R.g2(cell, table(known_wf=341), unt, CONFAB, KNOWN)["checks"]["well_formed_known"]      # .947 < .95
    assert not R.g2(cell, table(confab_wf=284), unt, CONFAB, KNOWN)["checks"]["well_formed_confab"]    # .9467
    assert not R.g2(cell, table(known_deg=11), unt, CONFAB, KNOWN)["checks"]["degenerate_known"]       # 11/360 > .03
    assert R.g2(cell, table(known_deg=10), unt, CONFAB, KNOWN)["checks"]["degenerate_known"]


def test_g2_engaged_known_is_not_adjudicable_below_35(cell):
    few = R.g2(cell, table(fire=34), table(), CONFAB, KNOWN)["engaged_known"]
    assert few == {"n": 34, "status": "NOT-ADJUDICABLE"}
    many = R.g2(cell, table(fire=40, known_ref=2), table(), CONFAB, KNOWN)["engaged_known"]
    assert many["status"] == "reported" and many["n"] == 40 and many["false_refusal"]["successes"] == 2


def test_g2_retention_does_not_divide_by_answered_only_rows():
    t = table(known_correct=200)
    assert R.pop_stats(t, "known_correct")["correct"]["n"] == 360


# ---- G3 ----------------------------------------------------------------------------

def test_g3_ratio_and_zero_denominator(cell):
    unt = table(confab_ref=30)
    native = table(confab_ref=180)                                                    # lift .5
    rnd = {1: table(confab_ref=40), 2: table(confab_ref=20), 3: table(confab_ref=35)}   # |lifts| .033, .033, .017
    out = R.g3(cell, native, unt, rnd, CONFAB)
    assert out["passed"] and out["max_abs_random_lift"] == pytest.approx(10 / 300)
    strong = {1: table(confab_ref=100), 2: table(confab_ref=30), 3: table(confab_ref=30)}   # lift .233 -> need >= .7
    assert not R.g3(cell, native, unt, strong, CONFAB)["passed"]
    exact = {1: table(confab_ref=60), 2: table(confab_ref=30), 3: table(confab_ref=30)}       # |.1| -> need .3; native .5 passes
    assert R.g3(cell, native, unt, exact, CONFAB)["passed"]
    zeros = {1: table(confab_ref=30), 2: table(confab_ref=30), 3: table(confab_ref=30)}
    z = R.g3(cell, native, unt, zeros, CONFAB)
    assert z["zero_denominator"] and z["passed"]
    assert not R.g3(cell, table(confab_ref=30), unt, zeros, CONFAB)["passed"]                  # zero native lift fails
    assert not R.g3(cell, table(confab_ref=10), unt, zeros, CONFAB)["passed"]                  # negative lift fails (no sign shortcut)
    neg_random = {1: table(confab_ref=0), 2: table(confab_ref=30), 3: table(confab_ref=30)}      # |-0.1|: sign-opposition gives no pass
    assert not R.g3(cell, table(confab_ref=40), unt, neg_random, CONFAB)["passed"]


def test_g3_never_reduces_k(cell):
    with pytest.raises(HarnessError) as e:
        R.g3(cell, table(), table(), {1: table(), 2: table()}, CONFAB)
    assert e.value.code == "CONTROLS"


# ---- bootstrap and G4 ------------------------------------------------------------------

def test_bootstrap_is_paired_seeded_and_exact_for_constants():
    vals = np.full(300, -0.2)
    a = R.bootstrap_mean(vals, 20261122, 2000)
    assert a["point"] == pytest.approx(-0.2) and a["bootstrap_ci_95"] == [pytest.approx(-0.2), pytest.approx(-0.2)] and a["reps"] == 2000
    v = np.random.default_rng(0).integers(-1, 2, 500).astype(float)
    b1, b2, b3 = (R.bootstrap_mean(v, s, 2000) for s in (7, 7, 8))
    assert b1 == b2 and b1["bootstrap_ci_95"] != b3["bootstrap_ci_95"] and b1["point"] == b3["point"]
    lo, hi = b1["bootstrap_ci_95"]
    assert lo < b1["point"] < hi and (hi - lo) == pytest.approx(2 * 1.96 * v.std() / np.sqrt(500), rel=0.2)


def test_did_pairs_rows_within_population():
    k = ["a", "b", "c", "d"]
    mk = lambda xs: {kk: {"refused_final": bool(x)} for kk, x in zip(k, xs)}  # noqa: E731
    d = R.did_values(mk([0, 0, 1, 1]), mk([1, 1, 1, 1]), mk([1, 1, 1, 0]), mk([1, 1, 1, 1]), k)
    # (sel_clamp - sel_free) - (unt_clamp - unt_free) per row = ([-1,-1,0,0]) - ([0,0,0,-1]) = [-1,-1,0,1]
    assert d.tolist() == [-1.0, -1.0, 0.0, 1.0]


def g4_tables(known_did, unknown_did, noise=0):
    """Rows with per-row DiD contributions arranged so the mean DiD is controllable."""
    def arms(keys, role, target):
        n = len(keys)
        k = int(round(abs(target) * n))
        sign = -1 if target < 0 else 1
        sel_free = {x: {"refused_final": False, "role": role} for x in keys}
        unt_free = {x: {"refused_final": False, "role": role} for x in keys}
        unt_clamp = {x: {"refused_final": False, "role": role} for x in keys}
        sel_clamp = {x: {"refused_final": False, "role": role} for x in keys}
        for i, x in enumerate(keys):
            if i < k:
                if sign < 0:
                    sel_free[x]["refused_final"] = True          # patched refuses freely, clamp removes it: DiD -1
                else:
                    sel_clamp[x]["refused_final"] = True          # clamp induces refusal only under the patch: DiD +1
        return sel_clamp, sel_free, unt_clamp, unt_free
    ck = arms(CONFAB, "confab", known_did)
    uk = arms(KNOWN, "known_correct", unknown_did)
    return {"clamp_known_native": ck[0], "heldout_native": {**ck[1], **uk[1]}, "clamp_known_untouched": ck[2],
            "heldout_untouched": {**ck[3], **uk[3]}, "clamp_unknown_native": uk[0], "clamp_unknown_untouched": uk[2]}


def test_g4_needs_both_clauses(cell):
    both = R.g4(cell, g4_tables(-0.3, 0.2), CONFAB, KNOWN)
    assert both["passed"] and both["known_clamp"]["point"] == pytest.approx(-0.3) and both["unknown_clamp"]["point"] == pytest.approx(0.2)
    assert both["known_clamp"]["reps"] == 2000 and both["known_clamp"]["seed"] == cell.cell["grading"]["bootstrap_seed"]
    assert not R.g4(cell, g4_tables(-0.3, 0.05), CONFAB, KNOWN)["passed"]       # unknown clause misses .10
    assert not R.g4(cell, g4_tables(-0.1, 0.2), CONFAB, KNOWN)["passed"]        # known clause misses -.15
    assert R.g4(cell, g4_tables(-0.15, 0.1), CONFAB, KNOWN)["known_clamp"]["bootstrap_ci_95"][1] < 0


def test_g4_requires_ci_to_exclude_zero(cell):
    # point -0.16 but heavy noise: construct a table with mixed +/- DiD rows so the CI straddles 0
    t = g4_tables(0, 0)
    for i, k in enumerate(CONFAB):
        if i < 90:
            t["heldout_native"][k]["refused_final"] = True           # DiD -1 on 90 rows
        elif i < 130:
            t["clamp_known_native"][k]["refused_final"] = True       # DiD +1 on 40 rows
    for k in CONFAB[:90]:
        t["clamp_known_native"][k]["refused_final"] = False
    out = R.g4(cell, t, CONFAB, KNOWN)
    assert out["known_clamp"]["point"] == pytest.approx(-50 / 300)
    assert out["known_clamp"]["bootstrap_ci_95"][1] < 0 and out["known_clamp"]["passed"]


# ---- G0 and interpretation -----------------------------------------------------------------

def ev(**kw):
    base = {n: {"passed": True, "basis": "generated_token_ids"} for n in R.EVIDENCE_NAMES}
    base.update(kw)
    return base


def test_g0_requires_every_component(cell):
    gate = {"passed": True}
    ok = R.g0(cell, materialize_ok=True, baseline_gate=gate, evidence=ev(), controls_ok=True, adjudication_ok=True,
              budget_stop=None, denominators_ok=True)
    assert ok["passed"]
    for kw in ({"materialize_ok": False}, {"baseline_gate": {"passed": False}}, {"baseline_gate": None}, {"controls_ok": False},
               {"adjudication_ok": False}, {"budget_stop": {"reason": "x"}}, {"denominators_ok": False}):
        args = dict(materialize_ok=True, baseline_gate=gate, evidence=ev(), controls_ok=True, adjudication_ok=True,
                    budget_stop=None, denominators_ok=True)
        args.update(kw)
        assert not R.g0(cell, **args)["passed"], kw
    for name in R.EVIDENCE_NAMES:
        e = ev()
        e[name] = None
        assert not R.g0(cell, materialize_ok=True, baseline_gate=gate, evidence=e, controls_ok=True, adjudication_ok=True,
                        budget_stop=None, denominators_ok=True)["passed"]
        e[name] = {"passed": False}
        assert name in R.g0(cell, materialize_ok=True, baseline_gate=gate, evidence=e, controls_ok=True, adjudication_ok=True,
                            budget_stop=None, denominators_ok=True)["failed_or_missing"]


def test_interpretation_mapping(cell):
    good = {"passed": True}
    g = lambda *p: {k: {"passed": v} for k, v in zip(("G1", "G2", "G3", "G4"), p)}  # noqa: E731
    assert R.interpret(cell, g0_result={"passed": False}, gate_results=None, selection_status="selected")["verdict"] == "instrument_invalid"
    assert R.interpret(cell, g0_result=good, gate_results=None, selection_status="no_eligible")["verdict"] == "bounded_search_null"
    assert R.interpret(cell, g0_result=good, gate_results=g(True, True, True, True), selection_status="selected")["verdict"] == "G1_G2_G3_G4_pass"
    assert R.interpret(cell, g0_result=good, gate_results=g(True, True, True, False), selection_status="selected")["verdict"] == "G1_G2_G3_pass"
    f = R.interpret(cell, g0_result=good, gate_results=g(True, False, True, True), selection_status="selected")
    assert f["verdict"] == "falsified" and f["failed"] == ["G2"]
    assert R.interpret(cell, g0_result={"passed": False}, gate_results=None, selection_status="no_eligible")["verdict"] == "instrument_invalid"
