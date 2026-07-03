"""Unit tests for arm_b_batched.py (Arm B tuner-batched engine) + the run_arm_b
--engine / --emit-prompts wiring.

CPU-only, synthetic fixtures — no model downloads, no GPU, no real tuner. The
tuner subprocess boundary is exercised with a FAKE _run_tuner that writes the
tuner's documented artifact shapes (completions.jsonl / capture.jsonl +
tensors/). Covers:
  - ENGINE PARITY: run_arm_b_cell_batched produces byte-identical results to
    run_arm_b.run_arm_b_cell given the same deterministic callables (early and
    late, gate and dial) — including the placebo permutation (same
    permute_scores(real_scores, seed) over the same item set)
  - render_pass_prompt mirrors the sequential generate_fn's prompt layout
    (plain vs injected think-block prompts, initial vs revision messages)
  - request assembly: pass ids, shared initial for 'late', note placement
  - tuner glue: batch-generate CLI flags (greedy vs sampled, per-stage
    max-new-tokens, global seed), completion strip + id join + missing-id
    error; batch-capture rows (token ids + read positions), direction-layer
    tensor loading, probe-score math
  - --emit-prompts recording (both engines' surface) + JSONL round-trip
  - CLI: sequential dry-run plan has NO engine keys; tuner-batched dry-run
    plan carries engine/batch_size
  - CUDA-gated tiny-model e2e: sequential vs tuner-batched slice + the
    spot_check_arm_b comparator

Run with an explicit file path (rtk pytest directory-glob false negative):
  pytest experiment/phase1/probe/steering/tests/test_arm_b_batched.py
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pytest

STEERING_DIR = Path(__file__).resolve().parents[1]
if str(STEERING_DIR) not in sys.path:
    sys.path.insert(0, str(STEERING_DIR))

import arm_b_batched as ab
from run_arm_b import main as run_arm_b_main
from run_arm_b import run_arm_b_cell
from steering_common import REVISION_INSTRUCTION, SYSTEM_PROMPT

try:
    import torch  # noqa: F401
    _TORCH = True
except ImportError:  # pragma: no cover - torch present in the run env
    _TORCH = False

REPO_ROOT = STEERING_DIR.parents[3]


def _resolve_tuner_dir():
    """Locate a synaptic-tuner checkout with tuner.py (worktree fallback)."""
    local = REPO_ROOT / "synaptic-tuner"
    if (local / "tuner.py").exists():
        return local
    if REPO_ROOT.parent.name == ".worktrees":
        main_co = REPO_ROOT.parents[1] / "synaptic-tuner"
        if (main_co / "tuner.py").exists():
            return main_co
    return local


TUNER_DIR = _resolve_tuner_dir()
_cuda = _TORCH and torch.cuda.is_available()
_tuner_present = (TUNER_DIR / "tuner.py").exists()


# ---------------------------------------------------------------------------
# Deterministic fakes shared by both engines (the parity fixture)
# ---------------------------------------------------------------------------

def make_items(n=4, source="selfaware_unknown", aliases=False):
    return [{
        "row_key": f"item::{i:03d}",
        "question": f"Question {i}?",
        "source": source,
        "aliases_norm": ([f"answer{i}"] if aliases else []),
    } for i in range(n)]


def det_score_fn(item, initial_answer):
    """Per-item deterministic score; shifts when an initial answer is given."""
    i = int(item["row_key"].split("::")[1])
    return (i + 1) / 10.0 + (0.05 if initial_answer is not None else 0.0)


def det_text_fn(item, initial_answer, pass_name, variant, note):
    """Deterministic text keyed on EVERYTHING the request carries, so any
    engine divergence in request construction shows up as a text diff."""
    return (f"{pass_name}|{variant}|{item['row_key']}"
            f"|note={'-' if note is None else note}"
            f"|init={'-' if initial_answer is None else initial_answer[:40]}")


def batch_callables():
    """Batch-level callables that delegate to the SAME per-item fakes."""
    def probe_scores(items, initials):
        return [det_score_fn(it, None if initials is None else initials[i])
                for i, it in enumerate(items)]

    def gen_batch(requests, pass_name):
        assert all(r["pass_name"] == pass_name for r in requests)
        return [det_text_fn(r["item"], r["initial_answer"], r["pass_name"],
                            r["variant"], r["note"]) for r in requests]
    return probe_scores, gen_batch


# ---------------------------------------------------------------------------
# Engine parity: batched == sequential given identical callables
# ---------------------------------------------------------------------------

class TestEngineParity:
    @pytest.mark.parametrize("signal,position,source,aliases", [
        ("gate", "early", "selfaware_unknown", False),
        ("gate", "late", "selfaware_unknown", False),
        ("dial", "early", "answerable", True),
        ("dial", "late", "answerable", True),
    ])
    def test_batched_matches_sequential(self, signal, position, source, aliases):
        items = make_items(6, source=source, aliases=aliases)
        seq = run_arm_b_cell(items, signal, position,
                             det_score_fn, det_text_fn, seed=11)
        probe_scores, gen_batch = batch_callables()
        bat = ab.run_arm_b_cell_batched(items, signal, position,
                                        probe_scores, gen_batch, seed=11)
        assert json.dumps(seq, sort_keys=True) == json.dumps(bat, sort_keys=True)

    def test_placebo_permutation_identical_across_engines(self):
        items = make_items(8)
        seq = run_arm_b_cell(items, "gate", "early",
                             det_score_fn, det_text_fn, seed=7)
        probe_scores, gen_batch = batch_callables()
        bat = ab.run_arm_b_cell_batched(items, "gate", "early",
                                        probe_scores, gen_batch, seed=7)
        assert ([r["injected_score"] for r in seq["placebo"]]
                == [r["injected_score"] for r in bat["placebo"]])

    def test_invalid_args_raise(self):
        probe_scores, gen_batch = batch_callables()
        with pytest.raises(ValueError, match="signal"):
            ab.run_arm_b_cell_batched(make_items(1), "vibes", "early",
                                      probe_scores, gen_batch, seed=1)
        with pytest.raises(ValueError, match="position"):
            ab.run_arm_b_cell_batched(make_items(1), "gate", "middle",
                                      probe_scores, gen_batch, seed=1)


# ---------------------------------------------------------------------------
# Batched request assembly
# ---------------------------------------------------------------------------

class TestRequestAssembly:
    def _capture_requests(self, position, n=3):
        items = make_items(n)
        probe_scores, _ = batch_callables()
        seen: list[tuple[str, list[dict]]] = []

        def recording_gen(requests, pass_name):
            seen.append((pass_name, requests))
            _, gen = batch_callables()
            return gen(requests, pass_name)

        ab.run_arm_b_cell_batched(items, "gate", position,
                                  probe_scores, recording_gen, seed=3)
        return items, seen

    def test_early_two_stages_notes_in_initial_only(self):
        items, seen = self._capture_requests("early")
        assert [s[0] for s in seen] == ["initial", "revision"]
        init_reqs, rev_reqs = seen[0][1], seen[1][1]
        assert len(init_reqs) == len(rev_reqs) == 2 * len(items)
        assert all(r["note"] is not None for r in init_reqs)
        assert all(r["note"] is None for r in rev_reqs)
        # revision initial_answer is the matching initial text
        for ir, rr in zip(init_reqs, rev_reqs):
            assert rr["initial_answer"] == det_text_fn(
                ir["item"], None, "initial", ir["variant"], ir["note"])

    def test_late_shared_initial_then_injected_revisions(self):
        items, seen = self._capture_requests("late")
        assert [s[0] for s in seen] == ["initial", "revision"]
        shared, rev = seen[0][1], seen[1][1]
        assert len(shared) == len(items)
        assert all(r["variant"] == "shared" and r["note"] is None
                   for r in shared)
        assert len(rev) == 2 * len(items)
        assert all(r["note"] is not None for r in rev)

    def test_pass_ids_unique(self):
        for position in ("early", "late"):
            _, seen = self._capture_requests(position)
            ids = [r["pass_id"] for _, reqs in seen for r in reqs]
            assert len(ids) == len(set(ids))


# ---------------------------------------------------------------------------
# render_pass_prompt: mirrors the sequential generate_fn layout
# ---------------------------------------------------------------------------

class FakeRender:
    """Records (messages, enable_thinking); returns a deterministic string."""

    def __init__(self):
        self.calls = []

    def __call__(self, messages, enable_thinking):
        self.calls.append((messages, enable_thinking))
        return f"<render thinking={enable_thinking} last={messages[-1]['content']!r}>"


class TestRenderPassPrompt:
    def test_plain_initial(self):
        r = FakeRender()
        item = make_items(1)[0]
        prompt = ab.render_pass_prompt(r, item, None, "initial", None)
        messages, thinking = r.calls[0]
        assert thinking is False
        assert messages[0] == {"role": "system", "content": SYSTEM_PROMPT}
        assert messages[1] == {"role": "user", "content": item["question"]}
        assert "<think>" not in prompt

    def test_injected_initial_opens_think_block(self):
        r = FakeRender()
        item = make_items(1)[0]
        note = "[internal: gate 0.10 — likely unknown — consider abstaining]"
        prompt = ab.render_pass_prompt(r, item, None, "initial", note)
        _, thinking = r.calls[0]
        assert thinking is True
        assert prompt.endswith("<think>\n" + note + "\n\n")

    def test_revision_messages_carry_initial_and_instruction(self):
        r = FakeRender()
        item = make_items(1)[0]
        ab.render_pass_prompt(r, item, "MY INITIAL", "revision", None)
        messages, thinking = r.calls[0]
        assert thinking is False
        assert messages[2] == {"role": "assistant", "content": "MY INITIAL"}
        assert messages[3] == {"role": "user", "content": REVISION_INSTRUCTION}

    def test_injected_revision(self):
        r = FakeRender()
        item = make_items(1)[0]
        note = "[internal: dial 0.78 — probably correct]"
        prompt = ab.render_pass_prompt(r, item, "MY INITIAL", "revision", note)
        _, thinking = r.calls[0]
        assert thinking is True
        assert prompt.endswith("<think>\n" + note + "\n\n")

    def test_none_initial_answer_becomes_empty_assistant_turn(self):
        r = FakeRender()
        item = make_items(1)[0]
        ab.render_pass_prompt(r, item, None, "revision", None)
        messages, _ = r.calls[0]
        assert messages[2] == {"role": "assistant", "content": ""}


# ---------------------------------------------------------------------------
# Tuner glue: batch-generate (fake subprocess)
# ---------------------------------------------------------------------------

def _mk_args(**over):
    base = dict(model="synthetic/tiny", batch_size=4, seed=99, greedy=False,
                temperature=0.9, top_p=0.95)
    base.update(over)
    return argparse.Namespace(**base)


def _cli_value(cli, flag):
    return cli[cli.index(flag) + 1]


class TestTunerGenerate:
    def _fake_run_tuner(self, transform=lambda p: f"  echo:{p[:24]}  ",
                        drop_ids=()):
        calls = []

        def fake(tuner_dir, verb, cli):
            calls.append((verb, list(cli)))
            prompts_path = Path(_cli_value(cli, "--prompts"))
            out_dir = Path(_cli_value(cli, "--out-dir"))
            out_dir.mkdir(parents=True, exist_ok=True)
            with (out_dir / "completions.jsonl").open("w") as fh:
                for line in prompts_path.read_text().splitlines():
                    row = json.loads(line)
                    if row["id"] in drop_ids:
                        continue
                    fh.write(json.dumps({
                        "id": row["id"],
                        "completion_text": transform(row["prompt"]),
                        "completion_token_ids": [1, 2, 3],
                        "prompt_token_len": 5,
                        "finish_reason": "eos",
                    }) + "\n")
        return fake, calls

    def _requests(self, n=3):
        return [{
            "pass_id": f"item::{i:03d}::initial::real",
            "item": make_items(n)[i], "initial_answer": None,
            "pass_name": "initial", "variant": "real",
            "note": f"[internal: gate 0.{i}0 — note]",
        } for i in range(n)]

    def test_texts_stripped_and_aligned(self, tmp_path, monkeypatch):
        fake, _ = self._fake_run_tuner()
        monkeypatch.setattr(ab, "_run_tuner", fake)
        reqs = self._requests()
        texts = ab.tuner_generate_requests(
            reqs, args=_mk_args(), render=FakeRender(), work_dir=tmp_path,
            stage_tag="00_initial", max_new=128, tuner_dir=tmp_path)
        assert len(texts) == len(reqs)
        # sequential parity: decode(...).strip()
        assert all(t == t.strip() and t.startswith("echo:") for t in texts)

    def test_sampled_cli_flags(self, tmp_path, monkeypatch):
        fake, calls = self._fake_run_tuner()
        monkeypatch.setattr(ab, "_run_tuner", fake)
        ab.tuner_generate_requests(
            self._requests(1), args=_mk_args(greedy=False),
            render=FakeRender(), work_dir=tmp_path,
            stage_tag="00_initial", max_new=128, tuner_dir=tmp_path)
        verb, cli = calls[0]
        assert verb == "batch-generate"
        assert _cli_value(cli, "--engine") == "hf-batched"
        assert _cli_value(cli, "--max-new-tokens") == "128"
        assert _cli_value(cli, "--seed") == "99"
        assert _cli_value(cli, "--batch-size") == "4"
        assert "--do-sample" in cli
        assert _cli_value(cli, "--temperature") == "0.9"
        assert _cli_value(cli, "--top-p") == "0.95"

    def test_greedy_cli_flags(self, tmp_path, monkeypatch):
        fake, calls = self._fake_run_tuner()
        monkeypatch.setattr(ab, "_run_tuner", fake)
        ab.tuner_generate_requests(
            self._requests(1), args=_mk_args(greedy=True),
            render=FakeRender(), work_dir=tmp_path,
            stage_tag="01_revision", max_new=96, tuner_dir=tmp_path)
        _, cli = calls[0]
        assert "--do-sample" not in cli
        assert "--temperature" not in cli
        assert _cli_value(cli, "--max-new-tokens") == "96"

    def test_missing_completion_raises(self, tmp_path, monkeypatch):
        reqs = self._requests(2)
        fake, _ = self._fake_run_tuner(drop_ids={reqs[1]["pass_id"]})
        monkeypatch.setattr(ab, "_run_tuner", fake)
        with pytest.raises(RuntimeError, match="no completion"):
            ab.tuner_generate_requests(
                reqs, args=_mk_args(), render=FakeRender(), work_dir=tmp_path,
                stage_tag="00_initial", max_new=128, tuner_dir=tmp_path)

    def test_emit_rows_recorded(self, tmp_path, monkeypatch):
        fake, _ = self._fake_run_tuner()
        monkeypatch.setattr(ab, "_run_tuner", fake)
        emit = []
        reqs = self._requests(2)
        ab.tuner_generate_requests(
            reqs, args=_mk_args(), render=FakeRender(), work_dir=tmp_path,
            stage_tag="00_initial", max_new=128, tuner_dir=tmp_path,
            emit_rows=emit, tokenizer=None)
        assert [e["pass_id"] for e in emit] == [r["pass_id"] for r in reqs]
        assert all(e["note"] is not None and e["prompt_sha"] for e in emit)


# ---------------------------------------------------------------------------
# Tuner glue: batch-capture rows + probe scores (fake subprocess)
# ---------------------------------------------------------------------------

class StubTokenizer:
    """Whitespace tokenizer: token index i -> id 100+i; '<eos>' -> 9."""

    def __call__(self, text):
        ids = []
        for i, tok in enumerate(text.split()):
            ids.append(9 if tok == "<eos>" else 100 + i)
        return {"input_ids": ids}


class TestCaptureRows:
    def test_early_reads_last_prompt_token(self):
        items = make_items(2)
        render = FakeRender()
        rows = ab.build_capture_rows(items, None, render=render,
                                     tokenizer=StubTokenizer(),
                                     special_ids={9})
        for row, item in zip(rows, items):
            assert row["id"] == item["row_key"]
            assert row["positions"] == {"score": len(row["token_ids"]) - 1}

    def test_late_trims_trailing_specials(self):
        items = make_items(1)

        def render(messages, enable_thinking):
            return "P1 P2 P3"

        rows = ab.build_capture_rows(items, [" ANSWER <eos>"], render=render,
                                     tokenizer=StubTokenizer(),
                                     special_ids={9})
        # tokens: P1 P2 P3 ANSWER <eos> -> content end excludes the special
        assert len(rows[0]["token_ids"]) == 5
        assert rows[0]["positions"] == {"score": 3}

    def test_late_all_special_falls_back_to_last(self):
        items = make_items(1)

        def render(messages, enable_thinking):
            return "<eos> <eos>"

        rows = ab.build_capture_rows(items, [" <eos>"], render=render,
                                     tokenizer=StubTokenizer(),
                                     special_ids={9})
        assert rows[0]["positions"] == {"score": len(rows[0]["token_ids"]) - 1}


@pytest.mark.skipif(not _TORCH, reason="torch required for safetensors fixture")
class TestTunerProbeScores:
    LAYER = 2

    def _fake_capture(self, hidden, drop_ids=()):
        """Fake batch-capture: per-row safetensors keyed score__L<layer> with a
        constant vector `hidden`, plus the capture.jsonl index."""
        calls = []

        def fake(tuner_dir, verb, cli):
            from safetensors.torch import save_file
            calls.append((verb, list(cli)))
            rows_path = Path(_cli_value(cli, "--rows"))
            out_dir = Path(_cli_value(cli, "--out-dir"))
            (out_dir / "tensors").mkdir(parents=True, exist_ok=True)
            layer = int(_cli_value(cli, "--layers"))
            with (out_dir / "capture.jsonl").open("w") as fh:
                for k, line in enumerate(rows_path.read_text().splitlines()):
                    row = json.loads(line)
                    if row["id"] in drop_ids:
                        continue
                    fname = f"tensors/row_{k}.safetensors"
                    save_file({f"score__L{layer}":
                               torch.tensor(hidden, dtype=torch.float32)},
                              str(out_dir / fname))
                    fh.write(json.dumps({
                        "id": row["id"], "file": fname, "n_layers": 1,
                        "hidden_dim": len(hidden),
                        "positions": row["positions"],
                    }) + "\n")
        return fake, calls

    def test_scores_are_logistic_dot(self, tmp_path, monkeypatch):
        import math

        import numpy as np
        hidden = [1.0, -2.0, 0.5]
        d = np.array([0.5, 0.25, 1.0])
        fake, calls = self._fake_capture(hidden)
        monkeypatch.setattr(ab, "_run_tuner", fake)
        items = make_items(3)
        scores = ab.tuner_probe_scores(
            items, None, args=_mk_args(), render=FakeRender(),
            tokenizer=StubTokenizer(), special_ids={9},
            layer_idx=self.LAYER, d_np=d, work_dir=tmp_path,
            stage_tag="00_probe", tuner_dir=tmp_path)
        expect = 1.0 / (1.0 + math.exp(-float(np.dot(hidden, d))))
        assert scores == pytest.approx([expect] * 3)
        verb, cli = calls[0]
        assert verb == "batch-capture"
        assert _cli_value(cli, "--layers") == str(self.LAYER)
        assert _cli_value(cli, "--persist-dtype") == "float32"
        assert _cli_value(cli, "--engine") == "hf-batched"

    def test_missing_capture_raises(self, tmp_path, monkeypatch):
        import numpy as np
        items = make_items(2)
        fake, _ = self._fake_capture([1.0], drop_ids={items[0]["row_key"]})
        monkeypatch.setattr(ab, "_run_tuner", fake)
        with pytest.raises(RuntimeError, match="no tensors"):
            ab.tuner_probe_scores(
                items, None, args=_mk_args(), render=FakeRender(),
                tokenizer=StubTokenizer(), special_ids={9},
                layer_idx=self.LAYER, d_np=np.array([1.0]),
                work_dir=tmp_path, stage_tag="00_probe", tuner_dir=tmp_path)


# ---------------------------------------------------------------------------
# --emit-prompts wrapper (the sequential engine's spot-check surface)
# ---------------------------------------------------------------------------

class TestEmitWrapper:
    def test_wrapper_records_and_delegates(self, tmp_path):
        items = make_items(3)
        inner_calls = []

        def inner(item, initial_answer, pass_name, variant, note):
            inner_calls.append(pass_name)
            return det_text_fn(item, initial_answer, pass_name, variant, note)

        emit: list[dict] = []
        wrapped = ab.wrap_generate_for_emit(inner, FakeRender(), None, emit)
        results = run_arm_b_cell(items, "gate", "early",
                                 det_score_fn, wrapped, seed=5)
        # early: 4 generations/item, all delegated AND all recorded
        assert len(inner_calls) == len(emit) == 4 * len(items)
        assert len({e["pass_id"] for e in emit}) == len(emit)
        # wrapped engine changes nothing about the results
        plain = run_arm_b_cell(items, "gate", "early",
                               det_score_fn, det_text_fn, seed=5)
        assert json.dumps(results, sort_keys=True) == \
            json.dumps(plain, sort_keys=True)
        # injected initial passes carry the note; revisions are plain
        for e in emit:
            if e["pass_name"] == "initial":
                assert e["note"] is not None
            else:
                assert e["note"] is None

    def test_emit_round_trip(self, tmp_path):
        rows = [ab.make_emit_row(StubTokenizer(), {
            "pass_id": "k::initial::real",
            "item": {"row_key": "k"}, "pass_name": "initial",
            "variant": "real", "note": "[internal: gate 0.10 — x]",
        }, "a b c")]
        out = ab.write_emit_prompts(tmp_path / "emit.jsonl", rows)
        loaded = [json.loads(x) for x in out.read_text().splitlines()]
        assert loaded == rows
        assert loaded[0]["prompt_token_ids"] == [100, 101, 102]


# ---------------------------------------------------------------------------
# CLI plan provenance (engine fields ONLY when non-sequential)
# ---------------------------------------------------------------------------

class TestCliPlanProvenance:
    def _dry_run_plan(self, tiny_direction_dir, synthetic_gate_pool_file,
                      tmp_path, capsys, extra):
        rc = run_arm_b_main([
            "--model", "synthetic/tiny",
            "--direction", str(tiny_direction_dir / "direction_gate.json"),
            "--signal", "gate", "--position", "early", "--eval-pool", "gate",
            "--n-unknown", "6", "--n-known", "6",
            "--pool-file", str(synthetic_gate_pool_file),
            "--out", str(tmp_path / "out.json"),
            "--dry-run", *extra,
        ])
        assert rc == 0
        out = capsys.readouterr().out
        return json.loads(
            out.split("cell plan:\n", 1)[1].rsplit("[run_arm_b]", 1)[0])

    def test_sequential_plan_has_no_engine_keys(
            self, tiny_direction_dir, synthetic_gate_pool_file, tmp_path,
            capsys):
        plan = self._dry_run_plan(tiny_direction_dir,
                                  synthetic_gate_pool_file, tmp_path, capsys,
                                  extra=[])
        assert "engine" not in plan
        assert "batch_size" not in plan

    def test_batched_plan_carries_engine_and_batch_size(
            self, tiny_direction_dir, synthetic_gate_pool_file, tmp_path,
            capsys):
        plan = self._dry_run_plan(
            tiny_direction_dir, synthetic_gate_pool_file, tmp_path, capsys,
            extra=["--engine", "tuner-batched", "--batch-size", "16"])
        assert plan["engine"] == "tuner-batched"
        assert plan["batch_size"] == 16


# ---------------------------------------------------------------------------
# CUDA-gated tiny-model e2e: sequential vs tuner-batched + spot check.
# Uses a tiny CHAT-TEMPLATED model (the Arm B surface needs
# apply_chat_template); greedy decode so the deterministic surfaces are
# maximal. The tuner runs as a REAL subprocess (public CLI only).
# ---------------------------------------------------------------------------

TINY_CHAT_MODEL = "trl-internal-testing/tiny-Qwen2ForCausalLM-2.5"


@pytest.mark.skipif(
    not (_cuda and _tuner_present),
    reason="needs CUDA (sequential load is device_map=cuda) + a tuner checkout")
def test_sequential_vs_tuner_batched_e2e_spot_check(tmp_path):
    from transformers import AutoConfig

    from spot_check_arm_b import main as spot_main
    from tests.conftest import (build_synthetic_extraction_dir,
                                build_synthetic_pool_file)

    # Direction fitted to THIS model's geometry (n_layers / hidden_dim).
    cfg = AutoConfig.from_pretrained(TINY_CHAT_MODEL)
    ext = build_synthetic_extraction_dir(
        tmp_path, n_layers=cfg.num_hidden_layers, hidden_dim=cfg.hidden_size)
    from persist_probe_direction import main as ppd_main
    ddir = tmp_path / "directions"
    assert ppd_main(["--x-dir", str(ext), "--out-dir", str(ddir),
                     "--seed", "42"]) == 0
    pool = build_synthetic_pool_file(tmp_path / "pool.jsonl",
                                     n_unknown=4, n_known=4)

    def _run(engine_extra, out_name, emit_name):
        argv = [
            "--model", TINY_CHAT_MODEL,
            "--direction", str(ddir / "direction_gate.json"),
            "--signal", "gate", "--position", "early", "--eval-pool", "gate",
            "--n-unknown", "4", "--n-known", "4",
            "--pool-file", str(pool),
            "--seed", "20260701", "--greedy",
            "--max-new-tokens-initial", "8", "--max-new-tokens-revision", "8",
            "--emit-prompts", str(tmp_path / emit_name),
            "--out", str(tmp_path / out_name),
            *engine_extra,
        ]
        assert run_arm_b_main(argv) == 0
        return json.loads((tmp_path / out_name).read_text())

    seq = _run([], "seq.json", "seq_prompts.jsonl")
    bat = _run(["--engine", "tuner-batched", "--batch-size", "4",
                "--tuner-dir", str(TUNER_DIR)],
               "bat.json", "bat_prompts.jsonl")

    # Same result-JSON schema; engine provenance only in the batched config.
    assert set(seq) == set(bat)
    assert "engine" not in seq["config"]
    assert bat["config"]["engine"] == "tuner-batched"

    rc = spot_main([
        "--sequential", str(tmp_path / "seq.json"),
        "--batched", str(tmp_path / "bat.json"),
        "--emit-sequential", str(tmp_path / "seq_prompts.jsonl"),
        "--emit-batched", str(tmp_path / "bat_prompts.jsonl"),
        "--gate-revision-prompts",
        "--out", str(tmp_path / "verdict.json"),
    ])
    verdict = json.loads((tmp_path / "verdict.json").read_text())
    assert verdict["gates"]["a_notes_byte_identical"], verdict["notes"]
    assert rc == 0, verdict
