"""Unit tests for run_arm_a.py (Amendment AA, Arm A activation-steering cells).

CPU-only, synthetic fixtures — no model downloads, no GPU. The cell loop is
exercised with a stub hook + fake generate callables. Covers:
  - hook active ONLY in the correct pass for each position (anchor vs end)
  - the alpha=0 control is always included (alpha* single-alpha mode)
  - proportional alpha via score_fn + calibration
  - revision-discrimination computation end-to-end
  - degenerate-output flagging
  - summary structure (per-alpha metrics + paired bootstrap vs alpha=0)
  - cell-JSON schema
  - --dry-run CLI (loads direction + pool, no model)
"""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from run_arm_a import main, run_arm_a_cell, summarize_arm_a
from steering_common import GenerationHookController, base_cell_payload, write_cell_json


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------

def make_stub_controller():
    """Real GenerationHookController around a stub hook (no torch needed for
    the cell loop — the hook callable itself is never invoked here)."""
    hook = SimpleNamespace(alpha=0.0, position="anchor",
                           anchor_token_idx=None, anchor_start=None)
    return GenerationHookController(hook)


def make_items(n: int = 4, source: str = "selfaware_unknown", aliases: bool = False):
    return [{
        "row_key": f"item::{i:03d}",
        "question": f"Question {i}?",
        "source": source,
        "aliases_norm": ([f"answer{i}"] if aliases else []),
    } for i in range(n)]


class RecordingGen:
    """Fake generate_fn that logs the controller state AT CALL TIME."""

    def __init__(self, controller, initial_text="An initial guess.",
                 final_text="A final answer."):
        self.controller = controller
        self.initial_text = initial_text
        self.final_text = final_text
        self.calls: list[dict] = []

    def __call__(self, item, initial_answer, pass_name):
        self.calls.append({
            "row_key": item["row_key"],
            "pass": pass_name,
            "mode": self.controller.mode,
            "alpha": self.controller.hook.alpha,
            "got_initial": initial_answer,
        })
        return self.initial_text if pass_name == "initial" else self.final_text


# ---------------------------------------------------------------------------
# Pass gating: hook active only in the correct pass for each position
# ---------------------------------------------------------------------------

class TestPassGating:
    def test_anchor_steers_initial_pass_only(self):
        controller = make_stub_controller()
        gen = RecordingGen(controller)
        items = make_items(3)
        run_arm_a_cell(items, [0.0, 2.0], "anchor", controller, gen)

        for c in gen.calls:
            if c["alpha"] == 2.0:
                assert c["pass"] == "initial" and c["mode"] == "anchor"
            else:
                assert c["mode"] == "off" and c["alpha"] == 0.0
        steered = [c for c in gen.calls if c["mode"] == "anchor"]
        assert len(steered) == 3  # one steered initial pass per item at alpha=2

    def test_end_steers_revision_pass_only(self):
        controller = make_stub_controller()
        gen = RecordingGen(controller)
        items = make_items(3)
        run_arm_a_cell(items, [0.0, 2.0], "end", controller, gen)

        for c in gen.calls:
            if c["alpha"] == 2.0:
                assert c["pass"] == "revision" and c["mode"] == "gen_stream"
            else:
                assert c["mode"] == "off" and c["alpha"] == 0.0
        steered = [c for c in gen.calls if c["mode"] == "gen_stream"]
        assert len(steered) == 3

    def test_revision_pass_receives_initial_answer(self):
        controller = make_stub_controller()
        gen = RecordingGen(controller, initial_text="THE-INITIAL")
        run_arm_a_cell(make_items(2), [0.0], "anchor", controller, gen)
        revisions = [c for c in gen.calls if c["pass"] == "revision"]
        assert all(c["got_initial"] == "THE-INITIAL" for c in revisions)

    def test_invalid_position_raises(self):
        with pytest.raises(ValueError, match="position"):
            run_arm_a_cell(make_items(1), [0.0], "sideways",
                           make_stub_controller(), lambda *a: "x")


# ---------------------------------------------------------------------------
# Alpha handling
# ---------------------------------------------------------------------------

class TestAlphaHandling:
    def test_control_added_in_single_alpha_mode(self):
        controller = make_stub_controller()
        gen = RecordingGen(controller)
        results = run_arm_a_cell(make_items(2), [2.0], "anchor", controller, gen)
        assert set(results) == {0.0, 2.0}
        assert all(len(v) == 2 for v in results.values())

    def test_records_aligned_across_alphas(self):
        controller = make_stub_controller()
        gen = RecordingGen(controller)
        results = run_arm_a_cell(make_items(4), [0.0, -1.0, 1.0], "anchor",
                                 controller, gen)
        keys0 = [r["row_key"] for r in results[0.0]]
        for alpha in (-1.0, 1.0):
            assert [r["row_key"] for r in results[alpha]] == keys0

    def test_proportional_alpha_recorded(self):
        from confidence_steer import compute_proportional_alpha
        controller = make_stub_controller()
        gen = RecordingGen(controller)
        cal = {"positive_mean": 0.8, "negative_mean": 0.2}
        results = run_arm_a_cell(
            make_items(2), [0.0, 2.0], "anchor", controller, gen,
            score_fn=lambda item: 0.5, calibration=cal)
        expected = compute_proportional_alpha(2.0, 0.5, cal)  # == 1.0
        for r in results[2.0]:
            assert r["probe_score"] == 0.5
            assert r["alpha_effective"] == pytest.approx(expected)
        for r in results[0.0]:
            assert r["probe_score"] is None
            assert r["alpha_effective"] == 0.0

    def test_effective_alpha_reaches_hook(self):
        controller = make_stub_controller()
        gen = RecordingGen(controller)
        cal = {"positive_mean": 0.8, "negative_mean": 0.2}
        run_arm_a_cell(make_items(1), [0.0, 4.0], "anchor", controller, gen,
                       score_fn=lambda item: 0.5, calibration=cal)
        steered = [c for c in gen.calls if c["mode"] == "anchor"]
        assert steered and steered[0]["alpha"] == pytest.approx(2.0)  # 4.0 * 0.5


# ---------------------------------------------------------------------------
# Grading through the cell loop
# ---------------------------------------------------------------------------

class TestGradingThroughCell:
    def test_revision_discrimination_end_to_end(self):
        """Fake model: wrong initials on items 0-1, correct on 2-3; at alpha=2
        the wrong ones get revised, at alpha=0 nothing is revised."""
        controller = make_stub_controller()
        items = make_items(4, source="answerable", aliases=True)

        def gen(item, initial_answer, pass_name):
            i = int(item["row_key"].split("::")[1])
            wrong = i < 2
            if pass_name == "initial":
                return "It is blorp." if wrong else f"It is answer{i}."
            # revision: only revise wrong initials, only when steered
            if wrong and controller.hook.alpha != 0.0:
                return f"On reflection, it is answer{i}."
            return initial_answer

        results = run_arm_a_cell(items, [0.0, 2.0], "end", controller, gen)
        summary = summarize_arm_a(results, n_boot=100, seed=1)
        assert summary["per_alpha"]["2.0"]["revision_discrimination"] == pytest.approx(1.0)
        assert summary["per_alpha"]["0.0"]["revision_discrimination"] == pytest.approx(0.0)
        contrast = summary["vs_control"]["2.0"]["revision_discrimination"]
        assert contrast["delta"] == pytest.approx(1.0)

    def test_degenerate_outputs_flagged(self):
        controller = make_stub_controller()
        items = make_items(3)

        def gen(item, initial_answer, pass_name):
            if pass_name == "revision" and item["row_key"].endswith("000"):
                return ""  # degenerate final output
            return "A plausible text."

        results = run_arm_a_cell(items, [0.0], "anchor", controller, gen)
        flags = [r["degenerate"] for r in results[0.0]]
        assert flags.count(True) == 1
        summary = summarize_arm_a(results, n_boot=50, seed=1)
        # summaries round to 4 decimals
        assert summary["per_alpha"]["0.0"]["degenerate_rate"] == pytest.approx(1 / 3, abs=1e-4)


# ---------------------------------------------------------------------------
# Summary + JSON schema
# ---------------------------------------------------------------------------

class TestSummaryAndSchema:
    def _run(self):
        controller = make_stub_controller()
        gen = RecordingGen(controller,
                           initial_text="Some guess.",
                           final_text="I don't know the answer.")
        items = make_items(4)
        results = run_arm_a_cell(items, [0.0, 2.0], "anchor", controller, gen)
        return items, results

    def test_summary_structure(self):
        _, results = self._run()
        summary = summarize_arm_a(results, n_boot=100, seed=1)
        assert set(summary) == {"per_alpha", "vs_control", "adequacy"}
        assert set(summary["per_alpha"]) == {"0.0", "2.0"}
        assert set(summary["vs_control"]) == {"2.0"}
        for ci in summary["vs_control"]["2.0"].values():
            assert {"delta", "ci_lo", "ci_hi", "n_boot", "ci_excludes_zero"} == set(ci)

    def test_summarize_requires_control(self):
        _, results = self._run()
        del results[0.0]
        with pytest.raises(ValueError, match="alpha=0"):
            summarize_arm_a(results, n_boot=10, seed=1)

    def test_cell_json_schema(self, tmp_path):
        items, results = self._run()
        summary = summarize_arm_a(results, n_boot=50, seed=1)
        payload = base_cell_payload(
            arm="A", cell="AA-1", signal="gate", position="anchor",
            model="synthetic/tiny", direction_meta={"signal": "gate",
                                                    "best_layer": 2},
            eval_pool="gate", seed=7, n_items=len(items),
            config_extra={"alpha_values": [0.0, 2.0]})
        payload["items"] = {str(a): r for a, r in results.items()}
        payload["summary"] = summary
        out = write_cell_json(tmp_path / "cell.json", payload)
        loaded = json.loads(out.read_text(encoding="utf-8"))
        assert loaded["amendment"] == "AA" and loaded["arm"] == "A"
        assert set(loaded["items"]) == {"0.0", "2.0"}
        rec = loaded["items"]["2.0"][0]
        for key in ("row_key", "source", "alpha", "alpha_effective",
                    "probe_score", "initial_text", "initial_hash",
                    "final_text", "final_hash", "initial_grade",
                    "final_grade", "revised", "degenerate"):
            assert key in rec, f"item record missing {key}"
        assert "per_alpha" in loaded["summary"]


# ---------------------------------------------------------------------------
# CLI --dry-run (CPU-only: direction + pool, no model)
# ---------------------------------------------------------------------------

class TestDryRunCli:
    def test_dry_run_gate_pool(self, tiny_direction_dir, synthetic_gate_pool_file,
                               tmp_path, capsys):
        rc = main([
            "--model", "synthetic/tiny",
            "--direction", str(tiny_direction_dir / "direction_gate.json"),
            "--position", "anchor",
            "--alpha-sweep=-2,0,2",  # '=' form: the value starts with '-'
            "--eval-pool", "gate",
            "--n-unknown", "6", "--n-known", "6",
            "--pool-file", str(synthetic_gate_pool_file),
            "--out", str(tmp_path / "out.json"),
            "--dry-run",
        ])
        assert rc == 0
        assert not (tmp_path / "out.json").exists()  # no results in dry-run
        out = capsys.readouterr().out
        assert "cell plan" in out and "dry-run" in out
        plan = json.loads(out.split("cell plan:\n", 1)[1].rsplit("[run_arm_a]", 1)[0])
        assert plan["n_items"] == 12
        assert plan["alpha_values"] == [-2.0, 0.0, 2.0]
        assert plan["n_generations"] == 12 * 3 * 2

    def test_dry_run_single_alpha_adds_control(self, tiny_direction_dir,
                                               synthetic_dial_pool_file,
                                               tmp_path, capsys):
        rc = main([
            "--model", "synthetic/tiny",
            "--direction", str(tiny_direction_dir / "direction_dial.json"),
            "--position", "anchor",
            "--alpha", "2.0",
            "--eval-pool", "dial",
            "--n-answerable", "8",
            "--pool-file", str(synthetic_dial_pool_file),
            "--out", str(tmp_path / "out.json"),
            "--dry-run",
        ])
        assert rc == 0
        out = capsys.readouterr().out
        plan = json.loads(out.split("cell plan:\n", 1)[1].rsplit("[run_arm_a]", 1)[0])
        assert plan["alpha_values"] == [0.0, 2.0]
        assert plan["signal"] == "dial"
