"""Unit tests for run_arm_b.py (Amendment AA, Arm B CoT-injection cells).

CPU-only, synthetic fixtures — no model downloads, no GPU. The cell loop is
exercised with fake probe-score and generate callables. Covers:
  - note in the correct pass for each position (early = initial, late = revision)
  - shared plain initial pass for 'late' (one initial per item, reused by both
    variants); per-variant initials for 'early'
  - paired real/placebo runs over the same items
  - placebo score shuffling determinism under --seed (within-batch permutation)
  - note rendering via cot_inject (score formatting)
  - summary structure (real vs placebo paired bootstrap)
  - cell-JSON schema
  - --dry-run CLI (loads direction + pool, no model)
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from run_arm_b import (
    main,
    make_note,
    permute_scores,
    run_arm_b_cell,
    summarize_arm_b,
)
from steering_common import base_cell_payload, write_cell_json


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------

def make_items(n: int = 4, source: str = "selfaware_unknown", aliases: bool = False):
    return [{
        "row_key": f"item::{i:03d}",
        "question": f"Question {i}?",
        "source": source,
        "aliases_norm": ([f"answer{i}"] if aliases else []),
    } for i in range(n)]


def fake_score_fn(item, initial_answer):
    """Distinct deterministic per-item scores; shifts when the initial answer
    is provided (so tests can see the post-answer read path)."""
    i = int(item["row_key"].split("::")[1])
    base = (i + 1) / 10.0
    return base + (0.05 if initial_answer is not None else 0.0)


class RecordingGen:
    """Fake generate_fn logging (item, pass, variant, note) per call."""

    def __init__(self, initial_text="An initial guess.",
                 final_text="A final answer."):
        self.initial_text = initial_text
        self.final_text = final_text
        self.calls: list[dict] = []

    def __call__(self, item, initial_answer, pass_name, variant, note):
        self.calls.append({
            "row_key": item["row_key"],
            "pass": pass_name,
            "variant": variant,
            "note": note,
            "got_initial": initial_answer,
        })
        return self.initial_text if pass_name == "initial" else self.final_text


# ---------------------------------------------------------------------------
# Note rendering (via cot_inject)
# ---------------------------------------------------------------------------

class TestMakeNote:
    def test_gate_note_format(self):
        note = make_note("gate", 0.23, "early")
        assert note == "[internal: gate 0.23 — likely unknown — consider abstaining]"

    def test_dial_note_format(self):
        note = make_note("dial", 0.78, "late")
        assert note == "[internal: dial 0.78 — probably correct]"

    def test_bad_signal_raises(self):
        with pytest.raises(ValueError):
            make_note("vibes", 0.5, "early")


# ---------------------------------------------------------------------------
# Placebo permutation determinism
# ---------------------------------------------------------------------------

class TestPermuteScores:
    def test_is_permutation(self):
        scores = [0.1, 0.2, 0.3, 0.4, 0.5]
        placebo = permute_scores(scores, seed=7)
        assert sorted(placebo) == sorted(scores)

    def test_deterministic_under_seed(self):
        scores = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
        assert permute_scores(scores, seed=7) == permute_scores(scores, seed=7)

    def test_different_seed_differs(self):
        scores = [round(0.05 * i, 2) for i in range(1, 17)]
        assert permute_scores(scores, seed=7) != permute_scores(scores, seed=8)

    def test_input_not_mutated(self):
        scores = [0.9, 0.1, 0.5]
        _ = permute_scores(scores, seed=1)
        assert scores == [0.9, 0.1, 0.5]


# ---------------------------------------------------------------------------
# Cell loop: injection position + pairing
# ---------------------------------------------------------------------------

class TestEarlyInjection:
    def _run(self, n=4):
        gen = RecordingGen()
        items = make_items(n)
        results = run_arm_b_cell(items, "gate", "early", fake_score_fn, gen, seed=7)
        return items, gen, results

    def test_note_in_initial_pass_only(self):
        _, gen, _ = self._run()
        for c in gen.calls:
            if c["pass"] == "initial":
                assert c["note"] is not None, "early: initial pass must carry the note"
            else:
                assert c["note"] is None, "early: revision pass must be plain"

    def test_each_variant_runs_its_own_two_passes(self):
        items, gen, _ = self._run(n=3)
        # per item: real initial + real revision + placebo initial + placebo revision
        assert len(gen.calls) == 3 * 4
        for variant in ("real", "placebo"):
            initials = [c for c in gen.calls
                        if c["variant"] == variant and c["pass"] == "initial"]
            assert len(initials) == 3

    def test_real_notes_carry_real_scores(self):
        items, gen, results = self._run()
        for rec in results["real"]:
            assert f"{rec['real_score']:.2f}" in rec["injection_note"]
            assert rec["injected_score"] == rec["real_score"]

    def test_placebo_notes_carry_permuted_scores(self):
        items, gen, results = self._run()
        real = [r["real_score"] for r in results["real"]]
        placebo = [r["injected_score"] for r in results["placebo"]]
        assert sorted(placebo) == sorted(real)  # within-batch permutation
        for rec in results["placebo"]:
            assert f"{rec['placebo_score']:.2f}" in rec["injection_note"]

    def test_pre_answer_score_read(self):
        # early: probe_score_fn is called WITHOUT an initial answer
        items = make_items(2)
        seen = []

        def score_fn(item, initial_answer):
            seen.append(initial_answer)
            return 0.4

        run_arm_b_cell(items, "gate", "early", score_fn, RecordingGen(), seed=1)
        assert seen == [None, None]


class TestLateInjection:
    def _run(self, n=4):
        gen = RecordingGen()
        items = make_items(n, source="answerable", aliases=True)
        results = run_arm_b_cell(items, "dial", "late", fake_score_fn, gen, seed=7)
        return items, gen, results

    def test_note_in_revision_pass_only(self):
        _, gen, _ = self._run()
        for c in gen.calls:
            if c["pass"] == "initial":
                assert c["note"] is None, "late: initial pass must be plain"
            else:
                assert c["note"] is not None, "late: revision pass must carry the note"

    def test_shared_initial_generated_once_per_item(self):
        items, gen, results = self._run(n=3)
        initials = [c for c in gen.calls if c["pass"] == "initial"]
        assert len(initials) == 3
        assert all(c["variant"] == "shared" for c in initials)
        # per item: 1 shared initial + real revision + placebo revision
        assert len(gen.calls) == 3 * 3
        for real_rec, placebo_rec in zip(results["real"], results["placebo"]):
            assert real_rec["initial_hash"] == placebo_rec["initial_hash"]
            assert real_rec["shared_initial"] is True

    def test_post_answer_score_read(self):
        # late: probe_score_fn is called WITH the shared initial answer
        items = make_items(2, source="answerable", aliases=True)
        seen = []

        def score_fn(item, initial_answer):
            seen.append(initial_answer)
            return 0.4

        gen = RecordingGen(initial_text="THE-INITIAL")
        run_arm_b_cell(items, "dial", "late", score_fn, gen, seed=1)
        assert seen == ["THE-INITIAL", "THE-INITIAL"]


class TestPairing:
    def test_real_and_placebo_aligned_over_same_items(self):
        gen = RecordingGen()
        items = make_items(5)
        results = run_arm_b_cell(items, "gate", "early", fake_score_fn, gen, seed=3)
        assert set(results) == {"real", "placebo"}
        keys_real = [r["row_key"] for r in results["real"]]
        keys_placebo = [r["row_key"] for r in results["placebo"]]
        assert keys_real == keys_placebo == [it["row_key"] for it in items]

    def test_cell_determinism_under_seed(self):
        items = make_items(6)
        r1 = run_arm_b_cell(items, "gate", "early", fake_score_fn,
                            RecordingGen(), seed=11)
        r2 = run_arm_b_cell(items, "gate", "early", fake_score_fn,
                            RecordingGen(), seed=11)
        assert ([x["injected_score"] for x in r1["placebo"]]
                == [x["injected_score"] for x in r2["placebo"]])

    def test_invalid_args_raise(self):
        with pytest.raises(ValueError, match="signal"):
            run_arm_b_cell(make_items(1), "vibes", "early",
                           fake_score_fn, RecordingGen(), seed=1)
        with pytest.raises(ValueError, match="position"):
            run_arm_b_cell(make_items(1), "gate", "middle",
                           fake_score_fn, RecordingGen(), seed=1)


# ---------------------------------------------------------------------------
# Grading, summary, schema
# ---------------------------------------------------------------------------

class TestSummaryAndSchema:
    def _abstain_when_real(self):
        """Fake model: abstains in the final pass only when the injected note
        carries a LOW score (the real scores here are low; placebo permutes)."""
        items = make_items(6)

        def score_fn(item, initial_answer):
            return 0.1  # uniformly low -> placebo permutation is identical

        def gen(item, initial_answer, pass_name, variant, note):
            if pass_name == "initial":
                return "An initial guess."
            if variant == "real":
                return "I don't know the answer."
            return "A confident final answer."

        return run_arm_b_cell(items, "gate", "early", score_fn, gen, seed=5)

    def test_summary_structure(self):
        results = self._abstain_when_real()
        summary = summarize_arm_b(results, n_boot=100, seed=2)
        assert set(summary) == {"real", "placebo", "real_vs_placebo", "adequacy"}
        assert summary["real"]["abstention_unknown"] == pytest.approx(1.0)
        assert summary["placebo"]["abstention_unknown"] == pytest.approx(0.0)
        contrast = summary["real_vs_placebo"]["abstention_unknown"]
        assert contrast["delta"] == pytest.approx(1.0)
        assert {"delta", "ci_lo", "ci_hi", "n_boot", "ci_excludes_zero"} == set(contrast)

    def test_summarize_requires_both_variants(self):
        results = self._abstain_when_real()
        del results["placebo"]
        with pytest.raises(ValueError, match="placebo"):
            summarize_arm_b(results, n_boot=10, seed=1)

    def test_degenerate_outputs_flagged(self):
        items = make_items(3)

        def gen(item, initial_answer, pass_name, variant, note):
            if variant == "real" and pass_name == "revision" \
                    and item["row_key"].endswith("000"):
                return "the the the the the the"
            return "A fine answer."

        results = run_arm_b_cell(items, "gate", "early",
                                 lambda it, ia: 0.5, gen, seed=1)
        assert sum(r["degenerate"] for r in results["real"]) == 1
        assert sum(r["degenerate"] for r in results["placebo"]) == 0

    def test_cell_json_schema(self, tmp_path):
        results = self._abstain_when_real()
        summary = summarize_arm_b(results, n_boot=50, seed=2)
        payload = base_cell_payload(
            arm="B", cell="AA-5", signal="gate", position="early",
            model="synthetic/tiny", direction_meta={"signal": "gate",
                                                    "best_layer": 2},
            eval_pool="gate", seed=5, n_items=6,
            config_extra={"placebo": "internal paired permutation"})
        payload["items"] = results
        payload["summary"] = summary
        out = write_cell_json(tmp_path / "cell.json", payload)
        loaded = json.loads(out.read_text(encoding="utf-8"))
        assert loaded["arm"] == "B"
        assert set(loaded["items"]) == {"real", "placebo"}
        rec = loaded["items"]["real"][0]
        for key in ("row_key", "source", "variant", "injected_score",
                    "real_score", "placebo_score", "injection_note",
                    "initial_text", "initial_hash", "final_text", "final_hash",
                    "initial_grade", "final_grade", "revised", "degenerate"):
            assert key in rec, f"item record missing {key}"
        assert "real_vs_placebo" in loaded["summary"]


# ---------------------------------------------------------------------------
# CLI --dry-run (CPU-only: direction + pool, no model)
# ---------------------------------------------------------------------------

class TestDryRunCli:
    def test_dry_run_early(self, tiny_direction_dir, synthetic_gate_pool_file,
                           tmp_path, capsys):
        rc = main([
            "--model", "synthetic/tiny",
            "--direction", str(tiny_direction_dir / "direction_gate.json"),
            "--signal", "gate",
            "--position", "early",
            "--eval-pool", "gate",
            "--n-unknown", "6", "--n-known", "6",
            "--pool-file", str(synthetic_gate_pool_file),
            "--out", str(tmp_path / "out.json"),
            "--dry-run",
        ])
        assert rc == 0
        assert not (tmp_path / "out.json").exists()
        out = capsys.readouterr().out
        plan = json.loads(out.split("cell plan:\n", 1)[1].rsplit("[run_arm_b]", 1)[0])
        assert plan["arm"] == "B" and plan["position"] == "early"
        assert plan["n_items"] == 12
        assert plan["n_generations"] == 12 * 4  # early: 2 variants x 2 passes

    def test_dry_run_late_dial(self, tiny_direction_dir, synthetic_dial_pool_file,
                               tmp_path, capsys):
        rc = main([
            "--model", "synthetic/tiny",
            "--direction", str(tiny_direction_dir / "direction_dial.json"),
            "--signal", "dial",
            "--position", "late",
            "--eval-pool", "dial",
            "--n-answerable", "10",
            "--pool-file", str(synthetic_dial_pool_file),
            "--out", str(tmp_path / "out.json"),
            "--dry-run",
        ])
        assert rc == 0
        out = capsys.readouterr().out
        plan = json.loads(out.split("cell plan:\n", 1)[1].rsplit("[run_arm_b]", 1)[0])
        assert plan["n_generations"] == 10 * 3  # late: shared initial + 2 revisions
        assert plan["direction_signal"] == "dial"


# ---------------------------------------------------------------------------
# Final (think-end) injection — Amendment AB Revision 1
# ---------------------------------------------------------------------------

class RecordingGenFinal:
    """Fake generate_fn for position='final' (accepts think_draft kwarg)."""

    def __init__(self, initial_text="An initial guess.",
                 think_text="<think>\nMY-REASONING\n</think>\nAn answer.",
                 final_text="A final answer."):
        self.initial_text = initial_text
        self.think_text = think_text
        self.final_text = final_text
        self.calls: list[dict] = []

    def __call__(self, item, initial_answer, pass_name, variant, note,
                 think_draft=None):
        self.calls.append({
            "row_key": item["row_key"],
            "pass": pass_name,
            "variant": variant,
            "note": note,
            "got_initial": initial_answer,
            "think_draft": think_draft,
        })
        if pass_name == "initial":
            return self.initial_text
        if pass_name == "revision_think":
            return self.think_text
        return self.final_text


class TestFinalInjection:
    def _run(self, n=4):
        gen = RecordingGenFinal()
        items = make_items(n, source="answerable", aliases=True)
        results = run_arm_b_cell(items, "dial", "final", fake_score_fn, gen, seed=7)
        return items, gen, results

    def test_pass_sequence_per_item(self):
        items, gen, _ = self._run(n=3)
        # per item: 1 shared initial + 1 shared revision_think + 2 revision_final
        assert len(gen.calls) == 3 * 4
        for pass_name, variant, count in (
                ("initial", "shared", 3),
                ("revision_think", "shared", 3),
                ("revision_final", "real", 3),
                ("revision_final", "placebo", 3)):
            got = [c for c in gen.calls
                   if c["pass"] == pass_name and c["variant"] == variant]
            assert len(got) == count, (pass_name, variant, len(got))

    def test_shared_think_pass_is_plain(self):
        _, gen, _ = self._run()
        for c in gen.calls:
            if c["pass"] == "revision_think":
                assert c["note"] is None, "shared reasoning pass must be plain"

    def test_final_pass_carries_note_and_shared_draft(self):
        _, gen, _ = self._run()
        finals = [c for c in gen.calls if c["pass"] == "revision_final"]
        assert finals, "no revision_final calls recorded"
        for c in finals:
            assert c["note"] is not None
            assert c["think_draft"] == "MY-REASONING", \
                "draft must be the extracted think content, shared verbatim"

    def test_real_placebo_share_identical_draft(self):
        _, gen, _ = self._run(n=2)
        by_item: dict[str, set] = {}
        for c in gen.calls:
            if c["pass"] == "revision_final":
                by_item.setdefault(c["row_key"], set()).add(c["think_draft"])
        for row_key, drafts in by_item.items():
            assert len(drafts) == 1, \
                f"{row_key}: real and placebo must share one draft, got {drafts}"

    def test_post_answer_score_read(self):
        items = make_items(2, source="answerable", aliases=True)
        seen = []

        def score_fn(item, initial_answer):
            seen.append(initial_answer)
            return 0.4

        gen = RecordingGenFinal(initial_text="THE-INITIAL")
        run_arm_b_cell(items, "dial", "final", score_fn, gen, seed=1)
        assert seen == ["THE-INITIAL", "THE-INITIAL"]

    def test_record_flags(self):
        _, _, results = self._run(n=2)
        for rec in results["real"] + results["placebo"]:
            assert rec["shared_initial"] is True
            assert rec["shared_think_draft"] is True

    def test_placebo_scores_still_permuted(self):
        _, _, results = self._run()
        real = [r["real_score"] for r in results["real"]]
        placebo = [r["injected_score"] for r in results["placebo"]]
        assert sorted(placebo) == sorted(real)


class TestDryRunFinal:
    def test_dry_run_final_dial(self, tiny_direction_dir, synthetic_dial_pool_file,
                                tmp_path, capsys):
        rc = main([
            "--model", "synthetic/tiny",
            "--direction", str(tiny_direction_dir / "direction_dial.json"),
            "--signal", "dial",
            "--position", "final",
            "--eval-pool", "dial",
            "--n-answerable", "10",
            "--pool-file", str(synthetic_dial_pool_file),
            "--out", str(tmp_path / "out.json"),
            "--dry-run",
        ])
        assert rc == 0
        out = capsys.readouterr().out
        plan = json.loads(out.split("cell plan:\n", 1)[1].rsplit("[run_arm_b]", 1)[0])
        assert plan["position"] == "final"
        # final: shared initial + shared revision_think + 2 forced answers
        assert plan["n_generations"] == 10 * 4


class TestNoteVariantThreading:
    def test_default_is_v0(self):
        gen = RecordingGen()
        results = run_arm_b_cell(make_items(2), "gate", "early",
                                 fake_score_fn, gen, seed=7)
        for rec in results["real"]:
            assert rec["note_variant"] == "v0"
            assert rec["injection_note"].startswith("[internal:")

    def test_v1_notes_rendered_and_recorded(self):
        gen = RecordingGen()
        results = run_arm_b_cell(make_items(3), "gate", "early",
                                 fake_score_fn, gen, seed=7, note_variant="v1")
        for rec in results["real"] + results["placebo"]:
            assert rec["note_variant"] == "v1"
            assert rec["injection_note"].startswith("Let me first check")
            assert f"{int(round(rec['injected_score'] * 100))}%" \
                in rec["injection_note"]
