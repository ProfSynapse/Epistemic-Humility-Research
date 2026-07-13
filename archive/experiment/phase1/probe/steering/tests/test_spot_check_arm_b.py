"""Unit tests for spot_check_arm_b.py (sequential vs tuner-batched aggregate
equivalence comparator).

CPU-only, synthetic cell JSONs built with the REAL run_arm_b cell loop +
payload writer (so the comparator is tested against the true schema). Covers:
  - identical cells + identical emit files -> PASS (exit 0)
  - note mismatch -> gate (a) fails; waivable via --max-note-mismatch-rate
  - deterministic-surface prompt-id mismatch -> gate (b) fails; revision-pass
    mismatches are reported but NOT gated by default (sampled-decode honesty)
    and gated under --gate-revision-prompts
  - metric shift beyond binomial noise -> gate (c) fails; small shift passes
  - config mismatch (different seed/position) -> fatal exit 1
  - item-set mismatch -> ValueError

Run with an explicit file path (rtk pytest directory-glob false negative):
  pytest experiment/phase1/probe/steering/tests/test_spot_check_arm_b.py
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

STEERING_DIR = Path(__file__).resolve().parents[1]
if str(STEERING_DIR) not in sys.path:
    sys.path.insert(0, str(STEERING_DIR))

import spot_check_arm_b as sc
from run_arm_b import run_arm_b_cell, summarize_arm_b
from steering_common import base_cell_payload


# ---------------------------------------------------------------------------
# Synthetic cell builders (real cell loop, deterministic fakes)
# ---------------------------------------------------------------------------

def make_items(n=40):
    return [{
        "row_key": f"item::{i:03d}",
        "question": f"Question {i}?",
        "source": "selfaware_unknown",
        "aliases_norm": [],
    } for i in range(n)]


def det_score_fn(item, initial_answer):
    i = int(item["row_key"].split("::")[1])
    return ((i % 9) + 1) / 10.0


def gen_fn_factory(abstain_rate_real=1.0, n=40):
    """Real-variant revisions abstain for the first `rate` fraction of the n
    items; placebo answers confidently. Deterministic per item."""
    threshold = int(round(abstain_rate_real * n))

    def gen(item, initial_answer, pass_name, variant, note):
        i = int(item["row_key"].split("::")[1])
        if pass_name == "initial":
            return f"An initial guess {i}."
        if variant == "real" and i < threshold:
            return "I don't know the answer."
        return f"A confident final answer {i}."
    return gen


def build_cell(seed=5, abstain_rate_real=1.0, n=40, config=None):
    items = make_items(n)
    results = run_arm_b_cell(items, "gate", "early", det_score_fn,
                             gen_fn_factory(abstain_rate_real, n), seed=seed)
    payload = base_cell_payload(
        arm="B", cell="AA-5", signal="gate", position="early",
        model="synthetic/tiny", direction_meta={"signal": "gate",
                                                "best_layer": 2},
        eval_pool="gate", seed=seed, n_items=n,
        config_extra=(config or {"placebo": "internal paired permutation"}))
    payload["items"] = results
    payload["summary"] = summarize_arm_b(results, n_boot=50, seed=seed)
    return payload


def build_emit_rows(cell):
    """Emit rows consistent with an early-position cell: injected initial +
    plain revision per (item, variant); token ids derived deterministically."""
    rows = []
    for variant in ("real", "placebo"):
        for rec in cell["items"][variant]:
            note = rec["injection_note"]
            rows.append({
                "pass_id": f"{rec['row_key']}::initial::{variant}",
                "row_key": rec["row_key"], "pass_name": "initial",
                "variant": variant, "note": note,
                "prompt_sha": "deadbeef00000000",
                "prompt_token_ids": [1, 2, hash(note) % 1000],
            })
            rows.append({
                "pass_id": f"{rec['row_key']}::revision::{variant}",
                "row_key": rec["row_key"], "pass_name": "revision",
                "variant": variant, "note": None,
                "prompt_sha": "deadbeef00000001",
                "prompt_token_ids": [4, 5, hash(rec["initial_hash"]) % 1000],
            })
    return rows


def write_cells(tmp_path, seq_cell, bat_cell, seq_emit=None, bat_emit=None):
    paths = {}
    (tmp_path / "seq.json").write_text(json.dumps(seq_cell))
    (tmp_path / "bat.json").write_text(json.dumps(bat_cell))
    paths["seq"], paths["bat"] = tmp_path / "seq.json", tmp_path / "bat.json"
    for name, rows in (("seq_emit", seq_emit), ("bat_emit", bat_emit)):
        if rows is not None:
            p = tmp_path / f"{name}.jsonl"
            p.write_text("".join(json.dumps(r) + "\n" for r in rows))
            paths[name] = p
    return paths


def run_spot(paths, *extra):
    argv = ["--sequential", str(paths["seq"]), "--batched", str(paths["bat"])]
    if "seq_emit" in paths:
        argv += ["--emit-sequential", str(paths["seq_emit"]),
                 "--emit-batched", str(paths["bat_emit"])]
    argv += list(extra)
    return sc.main(argv)


# ---------------------------------------------------------------------------
# Verdicts
# ---------------------------------------------------------------------------

class TestVerdicts:
    def test_identical_cells_pass(self, tmp_path, capsys):
        cell = build_cell()
        emit = build_emit_rows(cell)
        paths = write_cells(tmp_path, cell, copy.deepcopy(cell),
                            emit, copy.deepcopy(emit))
        assert run_spot(paths) == 0
        verdict = json.loads(capsys.readouterr().out)
        assert verdict["verdict"] == "PASS"
        assert verdict["gates"] == {
            "a_notes_byte_identical": True,
            "b_prompt_ids_deterministic_surfaces": True,
            "c_metrics_within_binomial_noise": True,
        }

    def test_without_emit_files_gate_b_skipped(self, tmp_path, capsys):
        cell = build_cell()
        paths = write_cells(tmp_path, cell, copy.deepcopy(cell))
        assert run_spot(paths) == 0
        verdict = json.loads(capsys.readouterr().out)
        assert "b_prompt_ids_deterministic_surfaces" not in verdict["gates"]
        assert "SKIPPED" in verdict["prompt_ids"]

    def test_note_mismatch_fails_and_is_waivable(self, tmp_path, capsys):
        seq = build_cell()
        bat = copy.deepcopy(seq)
        bat["items"]["real"][0]["injection_note"] = \
            "[internal: gate 0.11 — likely unknown — consider abstaining]"
        paths = write_cells(tmp_path, seq, bat)
        assert run_spot(paths) == 1
        verdict = json.loads(capsys.readouterr().out)
        assert verdict["gates"]["a_notes_byte_identical"] is False
        assert verdict["notes"]["n_mismatched"] == 1
        # explicit knife-edge waiver
        assert run_spot(paths, "--max-note-mismatch-rate", "0.05") == 0

    def test_initial_prompt_id_mismatch_fails_gate_b(self, tmp_path, capsys):
        cell = build_cell()
        seq_emit = build_emit_rows(cell)
        bat_emit = copy.deepcopy(seq_emit)
        idx = next(i for i, r in enumerate(bat_emit)
                   if r["pass_name"] == "initial")
        bat_emit[idx]["prompt_token_ids"] = [7, 7, 7]
        paths = write_cells(tmp_path, cell, copy.deepcopy(cell),
                            seq_emit, bat_emit)
        assert run_spot(paths) == 1
        verdict = json.loads(capsys.readouterr().out)
        assert verdict["gates"]["b_prompt_ids_deterministic_surfaces"] is False
        assert verdict["prompt_ids"]["gated_mismatches"] == 1

    def test_revision_prompt_mismatch_reported_not_gated(self, tmp_path,
                                                         capsys):
        cell = build_cell()
        seq_emit = build_emit_rows(cell)
        bat_emit = copy.deepcopy(seq_emit)
        idx = next(i for i, r in enumerate(bat_emit)
                   if r["pass_name"] == "revision")
        bat_emit[idx]["prompt_token_ids"] = [7, 7, 7]
        paths = write_cells(tmp_path, cell, copy.deepcopy(cell),
                            seq_emit, bat_emit)
        # sampled-decode honesty: revision prompts embed generated text
        assert run_spot(paths) == 0
        verdict = json.loads(capsys.readouterr().out)
        assert verdict["prompt_ids"]["categories"]["revision"][
            "n_mismatched"] == 1
        # greedy runs may opt in to gating them
        assert run_spot(paths, "--gate-revision-prompts") == 1

    def test_metric_shift_beyond_noise_fails_gate_c(self, tmp_path, capsys):
        seq = build_cell(abstain_rate_real=1.0)
        bat = build_cell(abstain_rate_real=0.75)  # 10/40 flips: z ~ 3.4
        paths = write_cells(tmp_path, seq, bat)
        assert run_spot(paths) == 1
        verdict = json.loads(capsys.readouterr().out)
        assert verdict["gates"]["c_metrics_within_binomial_noise"] is False
        cond = verdict["metrics"]["conditions"]["abstention_unknown[real]"]
        assert cond["within_noise"] is False

    def test_small_metric_shift_within_noise_passes(self, tmp_path, capsys):
        seq = build_cell(abstain_rate_real=1.0)
        bat = build_cell(abstain_rate_real=0.95)  # 2/40 flips
        paths = write_cells(tmp_path, seq, bat)
        assert run_spot(paths) == 0
        verdict = json.loads(capsys.readouterr().out)
        assert verdict["gates"]["c_metrics_within_binomial_noise"] is True

    def test_config_mismatch_is_fatal(self, tmp_path, capsys):
        seq = build_cell(seed=5)
        bat = build_cell(seed=6)
        paths = write_cells(tmp_path, seq, bat)
        assert run_spot(paths) == 1
        assert "FATAL" in capsys.readouterr().out

    def test_item_set_mismatch_raises(self, tmp_path):
        seq = build_cell()
        bat = copy.deepcopy(seq)
        bat["items"]["real"][0]["row_key"] = "item::999"
        paths = write_cells(tmp_path, seq, bat)
        with pytest.raises(ValueError, match="item sets differ"):
            run_spot(paths)

    def test_verdict_out_file_written(self, tmp_path, capsys):
        cell = build_cell()
        paths = write_cells(tmp_path, cell, copy.deepcopy(cell))
        out = tmp_path / "verdict.json"
        assert run_spot(paths, "--out", str(out)) == 0
        assert json.loads(out.read_text())["verdict"] == "PASS"
