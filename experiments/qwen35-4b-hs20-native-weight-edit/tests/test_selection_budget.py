"""Deterministic selection, ties, no-eligible stop, and the hard budget/stop behavior."""

import time
from dataclasses import replace

import pytest

from conftest import SLUG
from hs20_nwe import selection
from hs20_nwe.budget import Ledger, planned_new_rows
from hs20_nwe.config import Layout
from hs20_nwe.engine import Engine
from hs20_nwe.util import HarnessError, append_jsonl


def counts(c_n=96, c_ref=0, c_wf=96, k_n=96, k_ref=0, k_corr=96, k_wf=96):
    return {"confab": {"n": c_n, "refused": c_ref, "correct": 0, "well_formed": c_wf, "degenerate": 0},
            "known_correct": {"n": k_n, "refused": k_ref, "correct": k_corr, "well_formed": k_wf, "degenerate": 0}}


BASE = counts(k_corr=96)


def ev(cell, cand, delta=1.0, block=20, scale=4.0, cid="c"):
    return selection.evaluate(cell, BASE, cand, {"delta_frobenius": delta, "block": block, "scale": scale, "cand_id": cid})


def test_thresholds_are_inclusive_where_registered(cell):
    ok = counts(c_ref=39 + 0, k_ref=4, k_corr=92)                  # 39/96 = .406 >= .40 ; 4/96 = .0417 <= .05 ; 92/96=.958 >= .95
    assert ev(cell, ok)["eligible"]
    assert not ev(cell, counts(c_ref=38))["eligible"]               # 38/96 = .3958 < .40
    assert not ev(cell, counts(c_ref=60, k_ref=5))["eligible"]      # 5/96 = .052 > .05
    assert ev(cell, counts(c_ref=60, k_ref=4))["eligible"]
    assert not ev(cell, counts(c_ref=60, k_corr=91))["eligible"]    # 91/96 = .948 < .95
    assert ev(cell, counts(c_ref=60, k_corr=92))["eligible"]        # 92/96 = .958
    assert not ev(cell, counts(c_ref=60, c_wf=86))["eligible"]      # 86/96 = .8958 < .90
    assert ev(cell, counts(c_ref=60, c_wf=87, k_wf=87))["eligible"]  # 87/96 = .906


def test_exact_boundary_uses_fractions_not_floats(cell):
    # known false refusal exactly 0.05: 5 of 100
    base = counts(k_n=100, k_corr=100)
    cand = counts(c_ref=50, k_n=100, k_ref=5, k_corr=100)
    out = selection.evaluate(cell, base, cand, {"delta_frobenius": 1, "block": 20, "scale": 4, "cand_id": "x"})
    assert out["checks"]["known_false_refusal"] is True
    cand = counts(c_ref=50, k_n=100, k_ref=6, k_corr=100)
    assert selection.evaluate(cell, base, cand, {"delta_frobenius": 1, "block": 20, "scale": 4, "cand_id": "x"})["checks"]["known_false_refusal"] is False


def test_objective_maximised_then_tie_breaks(cell):
    a = ev(cell, counts(c_ref=70, k_ref=1), delta=5.0, block=21, scale=16.0, cid="a")        # .7292 - 2/96
    b = ev(cell, counts(c_ref=70, k_ref=1), delta=3.0, block=22, scale=4.0, cid="b")         # identical objective, smaller delta
    c = ev(cell, counts(c_ref=70, k_ref=1), delta=3.0, block=20, scale=16.0, cid="c")        # same delta, lower block
    d = ev(cell, counts(c_ref=70, k_ref=1), delta=3.0, block=20, scale=4.0, cid="d")         # same, lower scale
    hi = ev(cell, counts(c_ref=80, k_ref=1), delta=99.0, block=22, scale=16.0, cid="hi")
    assert selection.choose([a, b, c, d])["winner"] == "d"
    assert selection.choose([a, b, c, d, hi])["winner"] == "hi"
    assert selection.choose([d, c, b, a])["ranking"] == ["d", "c", "b", "a"]
    assert selection.choose([a, b, c, d])["winner"] == selection.choose([d, a, c, b])["winner"]


def test_no_eligible_stops_and_completeness_is_enforced(cell):
    bad = ev(cell, counts(c_ref=1))
    assert selection.choose([bad])["status"] == "no_eligible" and selection.choose([bad])["winner"] is None
    with pytest.raises(HarnessError) as e:
        selection.choose([bad], expected=6)
    assert e.value.code == "SELECTION_INCOMPLETE"


def test_baseline_known_correct_gate(cell):
    assert selection.baseline_gate(cell, counts(k_corr=87))["passed"] is True          # 87/96 = .906
    assert selection.baseline_gate(cell, counts(k_corr=86))["passed"] is False         # .8958
    g = selection.baseline_gate(cell, counts(k_n=100, k_corr=90))
    assert g["passed"] is True                                                          # exactly 0.90


def test_zero_baseline_correct_makes_retention_ineligible(cell):
    out = selection.evaluate(cell, counts(k_corr=0), counts(c_ref=60), {"delta_frobenius": 1, "block": 20, "scale": 4, "cand_id": "z"})
    assert out["eligible"] is False and out["known_correct_retention"] is None


# ---- budget -------------------------------------------------------------------

def small_cell(cell, rows=100, hours=1.0):
    lim = {**cell.cell["limits"], "maximum_generated_rows": rows, "maximum_gpu_hours": hours}
    return replace(cell, cell={**cell.cell, "limits": lim})


def test_row_cap_is_hard_and_writes_a_stop(project, cell):
    c = small_cell(cell, rows=100)
    layout = Layout(project.root, SLUG)
    led = Ledger(c, layout)
    led.reserve("a", 60)
    out = layout.local("runlog/a.jsonl")
    for i in range(60):
        append_jsonl(out, {"row_key": str(i)})
    led.record_outputs("runlog/a.jsonl", out)
    assert led.generated_rows() == 60
    with pytest.raises(HarnessError) as e:
        led.reserve("b", 41)
    assert e.value.code == "BUDGET_ROWS" and led.stopped()["reason"] == "generated_rows_cap"
    with pytest.raises(HarnessError) as e:                        # everything refuses after a stop
        led.reserve("c", 1)
    assert e.value.code == "BUDGET_STOPPED"


def test_resumed_outputs_are_not_double_counted(project, cell):
    layout = Layout(project.root, SLUG)
    led = Ledger(cell, layout)
    out = layout.local("runlog/a.jsonl")
    for i in range(10):
        append_jsonl(out, {"k": i})
    led.record_outputs("runlog/a.jsonl", out)
    for i in range(15):
        append_jsonl(out, {"k": 100 + i})
    led.record_outputs("runlog/a.jsonl", out)
    assert led.generated_rows() == 25
    assert planned_new_rows(out, 40) == 15


def test_smokes_and_real_run_share_one_cap(project, cell):
    real, smoke = Layout(project.root, SLUG), Layout(project.root, SLUG, tag="s1")
    assert Ledger(cell, real).path == Ledger(cell, smoke).path
    assert smoke.local("runlog/x.jsonl") != real.local("runlog/x.jsonl")
    assert "smoke/s1" in str(smoke.local("runlog/x.jsonl"))


class SleepyCLI:
    def __init__(self, seconds, rc=0):
        self.seconds, self.rc, self.timeouts = seconds, rc, []

    def run(self, operation, arguments=(), *, timeout=None, **kwargs):
        self.timeouts.append(timeout)
        if self.seconds > (timeout or 1e9):
            import subprocess

            raise subprocess.TimeoutExpired("x", timeout)
        time.sleep(0)


def test_gpu_hours_cap_times_out_and_stops(project, cell):
    c = small_cell(cell, hours=1.0)
    layout = Layout(project.root, SLUG)
    led = Ledger(c, layout)
    led.add_gpu_seconds("earlier", 3600 - 10)
    eng = Engine(project.root, [], led, cli=SleepyCLI(seconds=60))
    with pytest.raises(HarnessError) as e:
        eng.run_gpu("stage", ["steer"], gpu_ack=True)
    assert e.value.code == "BUDGET_GPU" and led.stopped()["reason"] == "gpu_hours_cap"
    assert 0 < eng.cli.timeouts[0] <= 10.0 + 1e-6                 # timeout = remaining seconds


def test_gpu_verbs_need_explicit_ack_and_ledger(project, cell):
    layout = Layout(project.root, SLUG)
    led = Ledger(cell, layout)
    eng = Engine(project.root, [], led, cli=SleepyCLI(0))
    with pytest.raises(HarnessError) as e:
        eng.run_gpu("stage", ["steer"], gpu_ack=False)
    assert e.value.code == "GPU_ACK" and eng.cli.timeouts == []
    with pytest.raises(HarnessError):
        Engine(project.root, [], None, cli=SleepyCLI(0)).run_gpu("stage", ["steer"], gpu_ack=True)


def test_ack_flag_is_appended_exactly_once_and_never_implicit(project, cell):
    calls = []

    class Rec:
        def run(self, op, args=(), *, timeout=None, **kwargs):
            calls.append(list(args))

    layout = Layout(project.root, SLUG)
    eng = Engine(project.root, [], Ledger(cell, layout), cli=Rec())
    eng.run_gpu("s", ["steer", "--mi-config", "x"], gpu_ack=True)
    assert calls[0].count("--i-know-this-runs-on-gpu") == 1 and "--yes" not in calls[0]


def test_planned_rows_for_a_finished_job_is_zero(tmp_path):
    out = tmp_path / "o.jsonl"
    for i in range(8):
        append_jsonl(out, {"i": i})
    assert planned_new_rows(out, 8) == 0 and planned_new_rows(out, 12) == 4


def test_a_hard_kill_during_an_engine_call_is_billed_on_the_next_reserve(project, cell):
    layout = Layout(project.root, SLUG)
    led = Ledger(cell, layout)
    token = led.begin_gpu("killed_stage")                      # process dies here: no gpu_seconds line is ever written
    append_jsonl(led.path, {"kind": "gpu_start", "token": "old", "stage": "x", "ts": time.time() - 5000})
    assert led.gpu_seconds() == 0
    led.reserve("next", 0)
    assert led.gpu_seconds() >= 5000 and led.settle_orphans() == 0     # settled once, never double billed
    assert token
