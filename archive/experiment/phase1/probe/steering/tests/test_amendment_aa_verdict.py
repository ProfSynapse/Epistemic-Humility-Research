"""Unit tests for amendment_aa_verdict.py (Amendment AA Stage-1 roll-up).

CPU-only, fully synthetic cell JSONs — no model, no GPU, no real results.
Written BEFORE any Stage-1 result existed so the verdict logic is frozen
against the pre-registered gates:
  - effect-gate predicates G1-G4 (thresholds, coherence floor, known-answer
    floor, adequacy preconditions)
  - alpha* selection (smallest |alpha|, ties to larger effect)
  - AA-G5 cross-cell position-asymmetry paired bootstrap
  - verdict routing: SUCCESS / FALSIFIER-1/2/3 / PARTIAL / INCOMPLETE
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import amendment_aa_verdict as aav


# ---------------------------------------------------------------------------
# Synthetic record + cell builders
# ---------------------------------------------------------------------------

def rec(row_key: str, source: str, *, abstained: bool = False,
        init_correct=None, revised: bool = False,
        degenerate: bool = False) -> dict:
    return {
        "row_key": row_key,
        "source": source,
        "degenerate": degenerate,
        "revised": revised,
        "initial_grade": {"degenerate": False, "abstained": False,
                          "answered": True, "correct": init_correct},
        "final_grade": {"degenerate": degenerate, "abstained": abstained,
                        "answered": not abstained, "correct": None},
    }


def gate_records(abstain_frac: float, n_unknown: int = 150,
                 n_known: int = 50) -> list[dict]:
    """Unknown rows abstain for the first abstain_frac; known rows all answer."""
    out = [rec(f"u{i:03d}", "selfaware_unknown",
               abstained=(i < abstain_frac * n_unknown))
           for i in range(n_unknown)]
    out += [rec(f"k{i:03d}", "selfaware_known") for i in range(n_known)]
    return out


def dial_records(disc: float, n_wrong: int = 60, n_correct: int = 60) -> list[dict]:
    """revision_discrimination == disc exactly: wrong rows revise at disc,
    correct rows never revise."""
    out = [rec(f"w{i:03d}", "answerable", init_correct=False,
               revised=(i < disc * n_wrong)) for i in range(n_wrong)]
    out += [rec(f"c{i:03d}", "answerable", init_correct=True, revised=False)
            for i in range(n_correct)]
    return out


def contrast(delta: float, excl: bool = True) -> dict:
    return {"delta": delta, "ci_lo": delta - 0.03 if excl else -0.01,
            "ci_hi": delta + 0.03, "n_boot": 2000, "ci_excludes_zero": excl}


GATE_ADEQ = {"gate_adequate_ge_100_unknown_answered": True,
             "dial_adequate_ge_40_40": False}
DIAL_ADEQ = {"gate_adequate_ge_100_unknown_answered": False,
             "dial_adequate_ge_40_40": True}


def arm_a_cell(kind: str, *, effect: float, wrong_pos_effect: float = 0.0,
               alphas=("-2.0", "2.0"), star: str = "2.0",
               coherent: bool = True, adequate: bool = True,
               ark_delta: float = -0.01) -> dict:
    """Synthetic Arm A cell. `effect` drives BOTH the summary contrast at
    `star` and the per-item records, so gates and G5 agree."""
    metric = "abstention_unknown" if kind == "gate" else "revision_discrimination"
    mk = gate_records if kind == "gate" else dial_records
    per_alpha, vs, items = {}, {}, {"0.0": mk(0.0)}
    for a in alphas:
        eff = effect if a == star else effect * 0.5
        per_alpha[a] = {"coherence_floor_ok": coherent}
        vs[a] = {metric: contrast(eff),
                 "answer_rate_known": contrast(ark_delta, excl=False)}
        items[a] = mk(eff if a == star else eff)
    per_alpha["0.0"] = {"coherence_floor_ok": True}
    adeq = dict(GATE_ADEQ if kind == "gate" else DIAL_ADEQ)
    for k in adeq:
        adeq[k] = adeq[k] and adequate
    return {"items": items,
            "summary": {"per_alpha": per_alpha, "vs_control": vs,
                        "adequacy": adeq},
            "_wrong_pos_effect": wrong_pos_effect}


def arm_a_wrong_cell(kind: str, *, effect: float, alpha: str = "2.0") -> dict:
    """Off-position Arm A cell: single steered alpha + auto control."""
    metric = "abstention_unknown" if kind == "gate" else "revision_discrimination"
    mk = gate_records if kind == "gate" else dial_records
    return {"items": {alpha: mk(effect), "0.0": mk(0.0)},
            "summary": {"per_alpha": {alpha: {"coherence_floor_ok": True},
                                      "0.0": {"coherence_floor_ok": True}},
                        "vs_control": {alpha: {metric: contrast(effect, excl=False)}},
                        "adequacy": dict(GATE_ADEQ if kind == "gate" else DIAL_ADEQ)}}


def arm_b_cell(kind: str, *, effect: float, coherent: bool = True,
               adequate: bool = True) -> dict:
    metric = "abstention_unknown" if kind == "gate" else "revision_discrimination"
    mk = gate_records if kind == "gate" else dial_records
    adeq = dict(GATE_ADEQ if kind == "gate" else DIAL_ADEQ)
    for k in adeq:
        adeq[k] = adeq[k] and adequate
    return {"items": {"real": mk(effect), "placebo": mk(0.0)},
            "summary": {"real": {"coherence_floor_ok": coherent},
                        "placebo": {"coherence_floor_ok": True},
                        "real_vs_placebo": {
                            metric: contrast(effect),
                            "answer_rate_known": contrast(-0.01, excl=False)},
                        "adequacy": adeq}}


def all_cells_success() -> dict:
    """Eight cells where every effect gate passes and every predicted-position
    effect dwarfs its wrong-position twin -> SUCCESS."""
    return {
        "AA-1": arm_a_cell("gate", effect=0.30),
        "AA-2": arm_a_wrong_cell("gate", effect=0.02),
        "AA-3": arm_a_cell("dial", effect=0.40),
        "AA-4": arm_a_wrong_cell("dial", effect=0.05),
        "AA-5": arm_b_cell("gate", effect=0.25),
        "AA-6": arm_b_cell("gate", effect=0.02),
        "AA-7": arm_b_cell("dial", effect=0.35),
        "AA-8": arm_b_cell("dial", effect=0.03),
    }


@pytest.fixture(autouse=True)
def fast_boot(monkeypatch):
    monkeypatch.setattr(aav, "N_BOOT", 200)


# ---------------------------------------------------------------------------
# Effect gates
# ---------------------------------------------------------------------------

class TestGateArmA:
    def test_passes_on_strong_coherent_effect(self):
        g = aav.gate_arm_a(aav_cell := arm_a_cell("gate", effect=0.30),
                           "abstention_unknown", 0.15, known_floor=True)
        assert g["pass"] and g["alpha_star"] == "2.0"

    def test_alpha_star_is_smallest_abs_alpha(self):
        cell = arm_a_cell("gate", effect=0.30, alphas=("-4.0", "-2.0", "2.0", "4.0"))
        # make every alpha pass equally except star (0.30 at 2.0, 0.15 elsewhere)
        g = aav.gate_arm_a(cell, "abstention_unknown", 0.15, known_floor=True)
        assert abs(float(g["alpha_star"])) == 2.0

    def test_incoherent_alpha_cannot_pass(self):
        cell = arm_a_cell("gate", effect=0.30, coherent=False)
        g = aav.gate_arm_a(cell, "abstention_unknown", 0.15, known_floor=True)
        assert not g["pass"] and not g["passing_alphas"]

    def test_known_answer_floor_blocks(self):
        cell = arm_a_cell("gate", effect=0.30, ark_delta=-0.20)
        g = aav.gate_arm_a(cell, "abstention_unknown", 0.15, known_floor=True)
        assert not g["pass"]

    def test_underpowered_effect_is_not_a_pass(self):
        cell = arm_a_cell("gate", effect=0.30, adequate=False)
        g = aav.gate_arm_a(cell, "abstention_unknown", 0.15, known_floor=True)
        assert not g["pass"] and not g["adequate"]
        assert "UNDERPOWERED" in g["note"]

    def test_ci_must_exclude_zero(self):
        cell = arm_a_cell("gate", effect=0.30)
        cell["summary"]["vs_control"]["2.0"]["abstention_unknown"]["ci_excludes_zero"] = False
        cell["summary"]["vs_control"]["-2.0"]["abstention_unknown"]["ci_excludes_zero"] = False
        g = aav.gate_arm_a(cell, "abstention_unknown", 0.15, known_floor=True)
        assert not g["pass"]


class TestGateArmB:
    def test_passes_real_vs_placebo(self):
        g = aav.gate_arm_b(arm_b_cell("gate", effect=0.25),
                           "abstention_unknown", 0.10, known_floor=True)
        assert g["pass"]

    def test_incoherent_variant_blocks(self):
        g = aav.gate_arm_b(arm_b_cell("gate", effect=0.25, coherent=False),
                           "abstention_unknown", 0.10, known_floor=True)
        assert not g["pass"]

    def test_underpowered_blocks(self):
        g = aav.gate_arm_b(arm_b_cell("dial", effect=0.35, adequate=False),
                           "revision_discrimination", 0.10, known_floor=False)
        assert not g["pass"] and "UNDERPOWERED" in g["note"]


# ---------------------------------------------------------------------------
# AA-G5 asymmetry contrast
# ---------------------------------------------------------------------------

class TestAsymmetryContrast:
    def test_positive_asymmetry_passes(self):
        res = aav.asymmetry_contrast(
            gate_records(0.4), gate_records(0.0),
            gate_records(0.05), gate_records(0.0),
            aav.metric_abstention_unknown, n_boot=200)
        assert res["pass"] and res["contrast"] == pytest.approx(0.35, abs=0.02)

    def test_no_asymmetry_fails(self):
        res = aav.asymmetry_contrast(
            gate_records(0.3), gate_records(0.0),
            gate_records(0.3), gate_records(0.0),
            aav.metric_abstention_unknown, n_boot=200)
        assert not res["pass"]

    def test_disjoint_row_keys_return_none(self):
        a = [rec("x1", "selfaware_unknown")]
        b = [rec("y1", "selfaware_unknown")]
        assert aav.asymmetry_contrast(a, b, a, b,
                                      aav.metric_abstention_unknown,
                                      n_boot=10) is None

    def test_deterministic_under_seed(self):
        args = (gate_records(0.4), gate_records(0.0),
                gate_records(0.1), gate_records(0.0))
        r1 = aav.asymmetry_contrast(*args, aav.metric_abstention_unknown, n_boot=100)
        r2 = aav.asymmetry_contrast(*args, aav.metric_abstention_unknown, n_boot=100)
        assert r1 == r2


# ---------------------------------------------------------------------------
# Verdict routing
# ---------------------------------------------------------------------------

class TestVerdict:
    def test_success(self):
        v = aav.compute_verdict(all_cells_success())
        assert v["verdict"] == "SUCCESS"
        g5 = v["AA_G5_position_asymmetry_PRIMARY"]
        assert g5["pass"] and g5["n_pass"] == 4

    def test_missing_cell_is_incomplete(self):
        cells = all_cells_success()
        cells["AA-7"] = None
        v = aav.compute_verdict(cells)
        assert v["verdict"] == "INCOMPLETE" and v["missing_cells"] == ["AA-7"]

    def test_falsifier_1_when_channel_shut(self):
        cells = all_cells_success()
        for name in ("AA-1", "AA-3"):
            for c in cells[name]["summary"]["vs_control"].values():
                for m in c.values():
                    m["delta"] = 0.01
                    m["ci_excludes_zero"] = False
        for name in ("AA-5", "AA-7"):
            for m in cells[name]["summary"]["real_vs_placebo"].values():
                m["delta"] = 0.01
                m["ci_excludes_zero"] = False
        v = aav.compute_verdict(cells)
        assert v["verdict"].startswith("FALSIFIER-1")

    def test_falsifier_2_when_position_does_not_matter(self):
        cells = all_cells_success()
        # wrong-position cells now carry the SAME effect as predicted ones
        cells["AA-2"] = arm_a_wrong_cell("gate", effect=0.30)
        cells["AA-4"] = arm_a_wrong_cell("dial", effect=0.40)
        cells["AA-6"] = arm_b_cell("gate", effect=0.25)
        cells["AA-8"] = arm_b_cell("dial", effect=0.35)
        v = aav.compute_verdict(cells)
        assert v["verdict"].startswith("FALSIFIER-2")

    def test_falsifier_3_when_effects_only_incoherent(self):
        cells = all_cells_success()
        for name in ("AA-1", "AA-3"):
            for a in cells[name]["summary"]["per_alpha"]:
                if float(a) != 0.0:
                    cells[name]["summary"]["per_alpha"][a]["coherence_floor_ok"] = False
        for name in ("AA-5", "AA-7"):
            for m in cells[name]["summary"]["real_vs_placebo"].values():
                m["delta"] = 0.01
                m["ci_excludes_zero"] = False
        v = aav.compute_verdict(cells)
        assert v["verdict"].startswith("FALSIFIER-3")
        assert "AA-1" in v["falsifier3_incoherent_only_effects"]

    def test_partial_when_only_gate_side_passes(self):
        cells = all_cells_success()
        for name in ("AA-3",):
            for c in cells[name]["summary"]["vs_control"].values():
                c["revision_discrimination"]["delta"] = 0.01
                c["revision_discrimination"]["ci_excludes_zero"] = False
        for m in cells["AA-7"]["summary"]["real_vs_placebo"].values():
            m["delta"] = 0.01
            m["ci_excludes_zero"] = False
        v = aav.compute_verdict(cells)
        # dial side dead but gate side alive -> not SUCCESS, not falsifier-1
        assert v["verdict"].startswith("PARTIAL")

    def test_not_applicable_combo_cannot_count_toward_g5(self):
        cells = all_cells_success()
        for c in cells["AA-1"]["summary"]["vs_control"].values():
            c["abstention_unknown"]["ci_excludes_zero"] = False
        v = aav.compute_verdict(cells)
        combo = v["AA_G5_position_asymmetry_PRIMARY"]["combos"]["armA_gate"]
        assert combo["status"] == "NOT_APPLICABLE"
        assert v["AA_G5_position_asymmetry_PRIMARY"]["n_pass"] == 3


# ---------------------------------------------------------------------------
# End-to-end file round trip
# ---------------------------------------------------------------------------

class TestLoadAndRoundTrip:
    def test_load_cells_and_verdict_from_disk(self, tmp_path: Path):
        cells = all_cells_success()
        for name, fname in aav.CELL_FILES.items():
            payload = {k: v for k, v in cells[name].items()
                       if not k.startswith("_")}
            (tmp_path / fname).write_text(json.dumps(payload), encoding="utf-8")
        loaded = aav.load_cells(tmp_path)
        v = aav.compute_verdict(loaded)
        assert v["verdict"] == "SUCCESS"

    def test_missing_files_reported(self, tmp_path: Path):
        loaded = aav.load_cells(tmp_path)
        v = aav.compute_verdict(loaded)
        assert v["verdict"] == "INCOMPLETE"
        assert len(v["missing_cells"]) == 8
