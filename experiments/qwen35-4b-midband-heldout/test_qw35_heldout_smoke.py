"""CPU-only pytest smoke for the qwen35-4b-midband-heldout harness.
NO GPU, NO model download.

This is a harness-code-correctness check, not the instrument itself: it
proves the gate arithmetic (predicted-shape PASS and falsifier-shape FAIL,
every outcome-shape branch), the seeded permuted-gate draw, the batched
termination-detection/readback plumbing (mocked model.generate()), the
RunLog resume + data-exhaust persistence schema, the render-env-gap fix
(load_model must set QW35H_RENDER_MODEL/QW35H_RENDER_REVISION -- the exact
gap `rr-cross-family-raw-refusal`'s own CPU smoke shipped without catching,
because that smoke never exercised the render module), and the G0
byte-identical frozen-operating-point load against the REAL committed
ladder files already on disk in this worktree.

Run: python3 -m pytest test_qw35_heldout_smoke.py -v
(bare `python3 test_qw35_heldout_smoke.py` exits 0 silently -- known
repo-wide rtk/pytest gotcha, do not use it.)
"""

from __future__ import annotations

import hashlib
import json
import sys
import tempfile
from pathlib import Path

import numpy as np
import pytest
import torch
import transformers

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
for _p in (str(REPO_ROOT / "synaptic-tuner"), str(HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import gate_lib  # noqa: E402
import gen_lib  # noqa: E402
import grader  # noqa: E402
import materialize_rows as mrows  # noqa: E402
import pipeline  # noqa: E402
import steer_lib  # noqa: E402
from shared.utilities.run_log import RunLog  # noqa: E402


# ---------------------------------------------------------------------------
# render-env gap (the RR lesson): load_model must set the render env vars.
# ---------------------------------------------------------------------------

def test_load_model_sets_render_env_vars(monkeypatch):
    """load_model must set render.py's QW35H_RENDER_MODEL/
    QW35H_RENDER_REVISION to the SAME model/revision it just loaded -- the
    exact render-env gap that shipped in rr-cross-family-raw-refusal because
    its CPU smoke never called render.render() or checked the env vars.
    This test exercises the render module (importing it, reading the env
    vars it depends on) to close that gap here. Mocks transformers'
    from_pretrained classmethods so this stays CPU-only, network-free."""

    class _FakeTok:
        pad_token_id = 1
        eos_token = "<eos>"
        padding_side = None

    class _FakeModel:
        def eval(self):
            return self

        def parameters(self):
            yield torch.zeros(1)

    monkeypatch.setattr(transformers.AutoTokenizer, "from_pretrained", lambda *a, **k: _FakeTok())
    monkeypatch.setattr(transformers.AutoModelForCausalLM, "from_pretrained", lambda *a, **k: _FakeModel())
    monkeypatch.delenv("QW35H_RENDER_MODEL", raising=False)
    monkeypatch.delenv("QW35H_RENDER_REVISION", raising=False)

    steer_lib.load_model("some/model", "somerev")
    assert __import__("os").environ["QW35H_RENDER_MODEL"] == "some/model"
    assert __import__("os").environ["QW35H_RENDER_REVISION"] == "somerev"


def test_render_module_raises_clearly_when_env_unset(monkeypatch):
    """render.render() must fail loudly (not silently use a stale cached
    tokenizer) when the env var is unset -- the actual failure mode the RR
    gap produced in production. Exercising this IS exercising the render
    module, which is the whole point of this test's existence."""
    import render as render_mod

    monkeypatch.delenv("QW35H_RENDER_MODEL", raising=False)
    render_mod._TOKENIZER = None
    render_mod._TOKENIZER_KEY = None
    with pytest.raises(RuntimeError, match="QW35H_RENDER_MODEL"):
        render_mod.render({"row_key": "x", "question": "What is the capital of France?"})


def test_render_no_question_raises_keyerror():
    import render as render_mod

    with pytest.raises(KeyError):
        render_mod.render({"row_key": "x"})


# ---------------------------------------------------------------------------
# grader / gen_lib
# ---------------------------------------------------------------------------

def test_grader_self_check_does_not_raise():
    grader._self_check()


def test_gen_lib_grade_row_refusal_and_answer():
    refusal = '{"answer": "I don\'t know the answer", "response_confidence": 0.9}'
    r = gen_lib.grade_row(refusal, terminated_naturally=True, aliases=[])
    assert r["refused"] is True
    assert r["well_formed"] is True
    assert r["clean_tighten"] is True

    correct_answer = '{"answer": "Paris", "response_confidence": 0.9}'
    a = gen_lib.grade_row(correct_answer, terminated_naturally=True, aliases=["Paris", "City of Paris"])
    assert a["refused"] is False
    assert a["well_formed_correct"] is True
    assert a["clean_tighten"] is False  # not a refusal


# ---------------------------------------------------------------------------
# gate_lib: Wilson CI, rate_summary, every gate, every outcome-shape branch.
# ---------------------------------------------------------------------------

def _recs(n_refused: int, n_well_formed: int, n: int, role: str) -> list[dict]:
    return [
        {"refused": i < n_refused, "well_formed": i < n_well_formed, "clean_tighten": False,
         "degenerate": False, "terminated_naturally": True, "n_new_tokens": 20, "role": role}
        for i in range(n)
    ]


def test_wilson_matches_ladder_reference_numbers():
    # Sanity: the ladder's own resolved fired-confab clean_tighten 136/185 =
    # 73.5% with Wilson [66.7%, 79.3%] -- reusing that number as a
    # cross-check that this Wilson implementation matches the program's.
    w = gate_lib.wilson(136, 185)
    assert abs(w["rate"] - 0.7351351351351352) < 1e-12
    assert abs(w["wilson_ci_95"][0] - 0.6672350299153391) < 1e-9
    assert abs(w["wilson_ci_95"][1] - 0.7934688882989707) < 1e-9


def test_rate_summary_and_row_level_decoupling():
    records = [
        {"refused": True, "well_formed": True, "clean_tighten": True, "degenerate": False,
         "terminated_naturally": True, "n_new_tokens": 10},
        {"refused": True, "well_formed": False, "clean_tighten": False, "degenerate": False,
         "terminated_naturally": True, "n_new_tokens": 20},
        {"refused": False, "well_formed": True, "clean_tighten": False, "degenerate": False,
         "terminated_naturally": False, "n_new_tokens": 30},
    ]
    summary = gate_lib.rate_summary(records)
    assert summary["n"] == 3
    assert summary["refused"]["successes"] == 2
    assert summary["well_formed"]["successes"] == 2
    assert summary["row_level_decoupling"] == 1  # only record 0 is refused AND well_formed
    assert summary["mean_new_tokens"] == 20.0


def test_g1_gates_predicted_shape_pass():
    """Predicted shape A: refused >= 0.60 with LCB > 0.50, well_formed >= 0.80,
    known false-refusal <= 0.05 with UCB < 0.10."""
    fired_confab = _recs(n_refused=140, n_well_formed=160, n=185, role="confab")  # 75.7% / 86.5%
    known_full = _recs(n_refused=15, n_well_formed=0, n=360, role="known_correct_answered")  # 4.17%
    refused = gate_lib.rate_wilson(fired_confab, "refused")
    well_formed = gate_lib.rate_wilson(fired_confab, "well_formed")
    cost = gate_lib.rate_wilson(known_full, "refused")
    assert gate_lib.g1_refused_transfer_pass(refused) is True
    assert gate_lib.g1_well_formed_pass(well_formed) is True
    assert gate_lib.g1_cost_pass(cost) is True


def test_g1_refused_transfer_fails_shape_b():
    # 50% refused, well under the 0.60 floor.
    fired_confab = _recs(n_refused=92, n_well_formed=160, n=185, role="confab")
    refused = gate_lib.rate_wilson(fired_confab, "refused")
    assert gate_lib.g1_refused_transfer_pass(refused) is False


def test_g1_well_formed_fails_shape_c():
    # refused clears (75%) but well_formed only 50% (< 0.80 floor).
    fired_confab = _recs(n_refused=140, n_well_formed=92, n=185, role="confab")
    refused = gate_lib.rate_wilson(fired_confab, "refused")
    well_formed = gate_lib.rate_wilson(fired_confab, "well_formed")
    assert gate_lib.g1_refused_transfer_pass(refused) is True
    assert gate_lib.g1_well_formed_pass(well_formed) is False


def test_g1_cost_fails_shape_d():
    # confab legs clear, but known false-refusal is 15% (> 0.05 point AND UCB >= 0.10).
    known_full = _recs(n_refused=54, n_well_formed=0, n=360, role="known_correct_answered")
    cost = gate_lib.rate_wilson(known_full, "refused")
    assert cost["rate"] > gate_lib.COST_FLOOR
    assert gate_lib.g1_cost_pass(cost) is False


def test_g3i_placebo_pass_and_fail():
    baseline_confab_refused = gate_lib.wilson(2, 185)  # ~1.1%
    baseline_known_refused = gate_lib.wilson(1, 360)   # ~0.3%
    random_confab_refused_ok = gate_lib.wilson(4, 185)  # ~2.2%, delta ~1.1pp <= 2pp
    random_known_refused_ok = gate_lib.wilson(3, 360)   # ~0.8%, delta ~0.5pp <= 2pp
    g3i_pass = gate_lib.g3i_pass(random_confab_refused_ok, baseline_confab_refused, random_known_refused_ok, baseline_known_refused)
    assert g3i_pass["passed"] is True

    random_confab_refused_bad = gate_lib.wilson(30, 185)  # ~16.2%, delta ~15pp > 2pp
    g3i_fail = gate_lib.g3i_pass(random_confab_refused_bad, baseline_confab_refused, random_known_refused_ok, baseline_known_refused)
    assert g3i_fail["passed"] is False


def test_g3ii_placebo_pass_and_fail():
    gated_cost = gate_lib.wilson(15, 360)      # 4.17%
    permuted_worse = gate_lib.wilson(80, 360)  # 22.2%, strictly worse
    permuted_not_worse = gate_lib.wilson(5, 360)  # 1.4%, NOT worse

    assert gate_lib.g3ii_pass(permuted_worse, gated_cost)["passed"] is True
    assert gate_lib.g3ii_pass(permuted_not_worse, gated_cost)["passed"] is False


def test_classify_outcome_shape_priority_chain_covers_a_through_e():
    # A: everything passes.
    assert gate_lib.classify_outcome_shape(
        refused_transfer_pass=True, well_formed_pass=True, cost_pass=True,
        g3i_passed=True, g3ii_passed=True,
    ) == "A"
    # B: refused-transfer fails first, regardless of the other legs.
    assert gate_lib.classify_outcome_shape(
        refused_transfer_pass=False, well_formed_pass=False, cost_pass=False,
        g3i_passed=False, g3ii_passed=False,
    ) == "B"
    # C: refused clears, well_formed fails.
    assert gate_lib.classify_outcome_shape(
        refused_transfer_pass=True, well_formed_pass=False, cost_pass=True,
        g3i_passed=True, g3ii_passed=True,
    ) == "C"
    # D: refused + well_formed clear, cost fails.
    assert gate_lib.classify_outcome_shape(
        refused_transfer_pass=True, well_formed_pass=True, cost_pass=False,
        g3i_passed=True, g3ii_passed=True,
    ) == "D"
    # E: confab + cost clear but EITHER placebo leg fails (both sub-cases).
    assert gate_lib.classify_outcome_shape(
        refused_transfer_pass=True, well_formed_pass=True, cost_pass=True,
        g3i_passed=False, g3ii_passed=True,
    ) == "E"
    assert gate_lib.classify_outcome_shape(
        refused_transfer_pass=True, well_formed_pass=True, cost_pass=True,
        g3i_passed=True, g3ii_passed=False,
    ) == "E"


# ---------------------------------------------------------------------------
# Seeded-draw determinism: permuted-gate row selection.
# ---------------------------------------------------------------------------

def test_draw_permuted_gate_indices_determinism():
    idx1 = pipeline.draw_permuted_gate_indices(pool_size=1692, n_fired=890, seed=20260713)
    idx2 = pipeline.draw_permuted_gate_indices(pool_size=1692, n_fired=890, seed=20260713)
    idx3 = pipeline.draw_permuted_gate_indices(pool_size=1692, n_fired=890, seed=20260714)
    assert idx1 == idx2  # deterministic given the same seed
    assert idx1 != idx3  # differs across seeds
    assert len(idx1) == 890
    assert len(set(idx1)) == 890  # no replacement
    assert all(0 <= i < 1692 for i in idx1)
    assert idx1 == sorted(idx1)


# ---------------------------------------------------------------------------
# Batched generation: eos-position/termination detection + readback, mocked
# model.generate() (no download, no GPU).
# ---------------------------------------------------------------------------

class _MockHook:
    def __init__(self):
        self.last_readback = None


class _MockController:
    def __init__(self, hook):
        self.hook = hook
        self.calls = []

    def begin_pass(self, mode, strength, attention_mask=None, force_active=False):
        self.calls.append(("begin_pass", mode, strength))

    def reset(self):
        self.calls.append(("reset",))


class _MockBatchEncoding(dict):
    def to(self, device):
        return self


class _MockTokenizer:
    eos_token_id = 999
    pad_token_id = 0
    padding_side = "left"

    def __call__(self, prompts, return_tensors=None, padding=None):
        # Fixed prompt_len=3 for every row in this mock (padding is a real
        # tokenizer concern; the mocked model.generate() output below is
        # what actually drives the test, not this encoding).
        n = len(prompts)
        return _MockBatchEncoding({
            "input_ids": torch.ones((n, 3), dtype=torch.long),
            "attention_mask": torch.ones((n, 3), dtype=torch.long),
        })

    def convert_tokens_to_ids(self, tok):
        return None

    def decode(self, ids, skip_special_tokens=True):
        return " ".join(str(int(t)) for t in ids.tolist())


class _MockModel:
    def __init__(self, output_tensor, readback_on_generate=None):
        self.output_tensor = output_tensor
        self.readback_on_generate = readback_on_generate
        self.controller_ref = None

    def generate(self, **kwargs):
        if self.controller_ref is not None and self.readback_on_generate is not None:
            self.controller_ref.hook.last_readback = self.readback_on_generate
        n = kwargs["input_ids"].shape[0]
        return self.output_tensor[:n]


def _batch(rows: list[list[int]]) -> torch.Tensor:
    prompt = [1, 2, 3]
    return torch.tensor([prompt + r for r in rows], dtype=torch.long)


def test_run_batch_fixed_termination_and_readback():
    out = _batch([
        [10, 11, 999, 0, 0],    # eos at index 2 -> terminated True, n_new=3
        [10, 11, 12, 13, 14],   # no eos, n_new=200 cap reached (here max_new=5) -> terminated False
    ])
    hook = _MockHook()
    controller = _MockController(hook)
    model = _MockModel(out, readback_on_generate={"measured": [12.608, 12.608]})
    model.controller_ref = controller
    tokenizer = _MockTokenizer()

    results, raw_rb = steer_lib.run_batch_fixed(model, tokenizer, "cpu", controller, ["p0", "p1"], "gen_stream", 8.0, max_new=5)

    assert results[0]["terminated_naturally"] is True
    assert results[0]["n_new_tokens"] == 3
    assert results[0]["text"] == "10 11 999"
    assert results[0]["readback_measured"] == 12.608
    assert raw_rb == {"measured": [12.608, 12.608]}  # raw hook dict passed through unmodified

    assert results[1]["terminated_naturally"] is False
    assert results[1]["n_new_tokens"] == 5

    assert controller.calls[0] == ("begin_pass", "gen_stream", 8.0)
    assert controller.calls[-1] == ("reset",)


def test_run_batch_fixed_baseline_no_controller():
    out = _batch([[10, 11, 999, 0, 0]])
    tokenizer = _MockTokenizer()
    model = _MockModel(out)
    results, raw_rb = steer_lib.run_batch_fixed(model, tokenizer, "cpu", None, ["p0"], "off", 0.0, max_new=5)
    assert results[0]["readback_measured"] is None
    assert results[0]["terminated_naturally"] is True
    assert raw_rb is None  # no controller -> no readback to report at all


# ---------------------------------------------------------------------------
# RunLog resume + data-exhaust persistence schema (run_rows end to end,
# render mocked to avoid a real tokenizer download).
# ---------------------------------------------------------------------------

def test_run_rows_persistence_schema_and_runlog_resume(monkeypatch):
    monkeypatch.setattr(steer_lib, "render_prompt", lambda row: f"prompt-for-{row['row_key']}")

    clean_refusal = '{"answer": "I don\'t know the answer", "response_confidence": 0.95}'
    out = _batch([[10, 11, 999, 0, 0]] * 3)  # 3 rows, all the same eos pattern

    def _fresh_model():
        model = _MockModel(out)
        return model

    tokenizer = _MockTokenizer()
    tokenizer.decode = lambda ids, skip_special_tokens=True: clean_refusal  # force real, gradeable text

    rows = [
        {"row_key": f"r{i}", "role": "confab", "split": "held_out", "category_canon": "x", "aliases": []}
        for i in range(3)
    ]

    with tempfile.TemporaryDirectory() as td:
        log_path = Path(td) / "baseline.jsonl"
        run_config = {"stage": "test"}

        log1 = RunLog(log_path, run_config=run_config, key_field="row_key")
        model1 = _fresh_model()
        steer_lib.run_rows(model1, tokenizer, "cpu", None, "off", rows[:2], 0.0, 5, 8, log1)
        log1.close()

        # Resume: row r2 still pending, r0/r1 must be skipped.
        log2 = RunLog(log_path, run_config=run_config, key_field="row_key")
        model2 = _fresh_model()
        steer_lib.run_rows(model2, tokenizer, "cpu", None, "off", rows, 0.0, 5, 8, log2)
        log2.finalize({"n_rows": len(rows)})
        log2.close()

        records = {r["row_key"]: r for r in steer_lib.load_jsonl(log_path)}

    assert set(records) == {"r0", "r1", "r2"}
    for rk, rec in records.items():
        # Data-exhaust schema: generation text AND the full sub-grade dict
        # survive the round trip -- not booleans-only.
        assert rec["answer_text"] == clean_refusal
        assert rec["role"] == "confab"
        for field in ("well_formed", "single_answer_key", "trailing_clean", "answer_value",
                      "semantic_refuse", "terminated_naturally", "degenerate", "clean_tighten",
                      "refused", "answered", "correct", "well_formed_correct"):
            assert field in rec, f"missing {field!r} in persisted record for {rk}"
        assert rec["clean_tighten"] is True
        assert rec["refused"] is True


# ---------------------------------------------------------------------------
# G0: frozen operating point loads byte-identical from the REAL committed
# ladder files (no GPU needed -- these are just file reads).
# ---------------------------------------------------------------------------

def test_frozen_operating_point_loads_real_ladder_files():
    ladder_committed = REPO_ROOT / "experiments" / "qwen35-4b-midband-doubt-snap" / "analysis-committed"
    if not (ladder_committed / "build_manifest.json").is_file():
        pytest.skip("ladder analysis-committed artifacts not present in this worktree")

    fop = pipeline.load_frozen_operating_point()
    assert fop["c_hat"].shape == (2560,)
    assert fop["random_direction"].shape == (2560,)
    assert fop["u_d"].shape == (2560,)
    assert abs(np.linalg.norm(fop["c_hat"]) - 1.0) < 1e-6
    assert abs(np.linalg.norm(fop["random_direction"]) - 1.0) < 1e-6
    assert abs(np.linalg.norm(fop["u_d"]) - 1.0) < 1e-6

    # Cross-check against cell.yaml's own registered frozen values --
    # AMENDMENT.md's "NOTHING refit" claim, verified, not assumed.
    cell = json.loads(json.dumps(_load_yaml(HERE / "cell.yaml")))
    fstd = cell["frozen_operating_point"]["standardization"]
    assert abs(fop["sigma_c"] - fstd["sigma_c"]) < 1e-9
    assert abs(fop["mu_d"] - fstd["mu_d"]) < 1e-9
    assert abs(fop["sigma_d"] - fstd["sigma_d"]) < 1e-9
    assert abs(fop["tau_frozen"] - cell["frozen_operating_point"]["gate"]["tau_frozen"]) < 1e-9


def _load_yaml(path: Path) -> dict:
    import yaml

    return yaml.safe_load(path.read_text())


# ---------------------------------------------------------------------------
# materialize_rows: stale-field stripping + no-text-leak check.
# ---------------------------------------------------------------------------

def test_strip_stale_fleet_fields():
    row = {
        "row_key": "x", "role": "confab", "question": "q", "aliases": [],
        "score_neg_z_d": 0.1, "z_d": -0.1, "tau": -0.55, "fire": True,
        "baseline_terminated_naturally": True, "category_canon": "c",
    }
    stripped = mrows.strip_stale_fleet_fields(row)
    assert "score_neg_z_d" not in stripped
    assert "z_d" not in stripped
    assert "tau" not in stripped
    assert "fire" not in stripped
    assert "baseline_terminated_naturally" not in stripped
    assert stripped["row_key"] == "x"
    assert stripped["question"] == "q"


def test_report_no_text_leak_raises_on_leak():
    with tempfile.TemporaryDirectory() as td:
        committed = Path(td) / "analysis-committed"
        committed.mkdir()
        (committed / "leaky.json").write_text(json.dumps({"note": "What is the capital of France?"}))

        pipeline.COMMITTED = committed
        rows = [{"question": "What is the capital of France?"}]
        with pytest.raises(SystemExit, match="leaked"):
            pipeline._report_no_text_leak(rows)


def test_report_no_text_leak_passes_when_clean():
    with tempfile.TemporaryDirectory() as td:
        committed = Path(td) / "analysis-committed"
        committed.mkdir()
        (committed / "clean.json").write_text(json.dumps({"n": 1692, "rate": 0.735}))

        pipeline.COMMITTED = committed
        rows = [{"question": "What is the capital of France?"}]
        pipeline._report_no_text_leak(rows)  # must not raise


# ---------------------------------------------------------------------------
# G0 hardening (PI adjudication, gates.yaml registered text): hash-verified
# directions_byte_identical/scalars_frozen_match, readback_within_tolerance,
# and runlog_growth are raise-on-failure assertions, not eyeballed prose.
# ---------------------------------------------------------------------------

def test_verify_frozen_operating_point_hashes_placeholder_refuses_to_run(monkeypatch, tmp_path):
    """Placeholder entries MUST refuse to run, not silently pass. (Until sign
    the committed file itself carried placeholders and this asserted on it
    directly; the hashes were filled at sign 2026-07-13, so the placeholder
    behavior is asserted via a fixture and the committed file is asserted to
    verify clean below.)"""
    hashes_path = tmp_path / "frozen_operating_point_hashes.json"
    hashes_path.write_text(json.dumps({"placeholder": "FILLED-AT-SIGN",
                                       "files": {"d.json": "FILLED-AT-SIGN"}}))
    monkeypatch.setattr(pipeline, "HERE", tmp_path)
    monkeypatch.setattr(pipeline, "FROZEN_HASHES_PATH", hashes_path)
    with pytest.raises(SystemExit, match="placeholder"):
        pipeline.verify_frozen_operating_point_hashes()


def test_verify_frozen_operating_point_hashes_committed_file_verifies_clean():
    """Post-sign invariant: the committed hash file carries no placeholders
    and matches the resolved ladder's artifacts byte-for-byte."""
    pipeline.verify_frozen_operating_point_hashes()  # must not raise


def test_verify_frozen_operating_point_hashes_passes_on_correct_hash(monkeypatch, tmp_path):
    target = tmp_path / "d.json"
    target.write_text('{"vector": [1, 2, 3]}')
    real_hash = hashlib.sha256(target.read_bytes()).hexdigest()

    hashes_path = tmp_path / "frozen_operating_point_hashes.json"
    hashes_path.write_text(json.dumps({"placeholder": "FILLED-AT-SIGN", "files": {"d.json": real_hash}}))

    monkeypatch.setattr(pipeline, "HERE", tmp_path)
    monkeypatch.setattr(pipeline, "FROZEN_HASHES_PATH", hashes_path)
    pipeline.verify_frozen_operating_point_hashes()  # must not raise


def test_verify_frozen_operating_point_hashes_mismatch_raises(monkeypatch, tmp_path):
    target = tmp_path / "d.json"
    target.write_text('{"vector": [1, 2, 3]}')

    hashes_path = tmp_path / "frozen_operating_point_hashes.json"
    hashes_path.write_text(json.dumps({
        "placeholder": "FILLED-AT-SIGN",
        "files": {"d.json": "0" * 64},  # deliberately wrong
    }))

    monkeypatch.setattr(pipeline, "HERE", tmp_path)
    monkeypatch.setattr(pipeline, "FROZEN_HASHES_PATH", hashes_path)
    with pytest.raises(SystemExit, match="directions_byte_identical"):
        pipeline.verify_frozen_operating_point_hashes()


def test_verify_frozen_operating_point_hashes_missing_file_raises(monkeypatch, tmp_path):
    hashes_path = tmp_path / "frozen_operating_point_hashes.json"
    hashes_path.write_text(json.dumps({
        "placeholder": "FILLED-AT-SIGN",
        "files": {"does_not_exist.json": "0" * 64},
    }))

    monkeypatch.setattr(pipeline, "HERE", tmp_path)
    monkeypatch.setattr(pipeline, "FROZEN_HASHES_PATH", hashes_path)
    with pytest.raises(SystemExit, match="does not exist"):
        pipeline.verify_frozen_operating_point_hashes()


def test_verify_frozen_operating_point_hashes_missing_pin_file_raises(monkeypatch, tmp_path):
    monkeypatch.setattr(pipeline, "FROZEN_HASHES_PATH", tmp_path / "nope.json")
    with pytest.raises(SystemExit, match="missing"):
        pipeline.verify_frozen_operating_point_hashes()


def test_verify_smoke_readback_tolerance_passes_within_tolerance():
    # SmokeConfig defaults: write_rel_tol=0.05, write_abs_floor=0.5 -- 12.62
    # vs commanded 12.608 is well inside both the relative and absolute floor.
    readbacks = [{"commanded": [12.608, 12.608], "measured": [12.62, 12.60], "offtarget_abs_max": 0.0}]
    pipeline.verify_smoke_readback_tolerance(readbacks, "gated")  # must not raise


def test_verify_smoke_readback_tolerance_out_of_tolerance_raises():
    readbacks = [{"commanded": [12.608], "measured": [20.0], "offtarget_abs_max": 0.0}]
    with pytest.raises(SystemExit, match="readback_within_tolerance"):
        pipeline.verify_smoke_readback_tolerance(readbacks, "gated")


def test_verify_smoke_readback_tolerance_offtarget_movement_raises():
    # Write itself lands on target, but an inactive row moved more than
    # SmokeConfig.offtarget_tol (1e-3) -- parity failure, not a write failure.
    readbacks = [{"commanded": [12.608], "measured": [12.608], "offtarget_abs_max": 5.0}]
    with pytest.raises(SystemExit, match="readback_within_tolerance"):
        pipeline.verify_smoke_readback_tolerance(readbacks, "random_direction")


def test_verify_smoke_readback_tolerance_empty_collector_raises():
    with pytest.raises(SystemExit, match="no readback captured"):
        pipeline.verify_smoke_readback_tolerance([], "gated")


def test_assert_runlog_growth_short_count_raises():
    with pytest.raises(SystemExit, match="runlog_growth"):
        pipeline._assert_runlog_growth("gated", {"r0": {}, "r1": {}}, expected_n=3)


def test_assert_runlog_growth_exact_count_passes():
    pipeline._assert_runlog_growth("gated", {"r0": {}, "r1": {}, "r2": {}}, expected_n=3)  # must not raise


def test_run_batch_fixed_exposes_raw_readback_for_tolerance_check():
    """run_batch_fixed's raw_readback return is exactly the dict shape
    verify_smoke_readback_tolerance expects (commanded/measured/
    offtarget_abs_max) -- proves the two are actually wired together, not
    just independently plausible."""
    out = _batch([[10, 11, 999, 0, 0]])
    hook = _MockHook()
    controller = _MockController(hook)
    raw = {"commanded": [12.608], "measured": [12.61], "offtarget_abs_max": 0.0}
    model = _MockModel(out, readback_on_generate=raw)
    model.controller_ref = controller
    tokenizer = _MockTokenizer()

    _, raw_rb = steer_lib.run_batch_fixed(model, tokenizer, "cpu", controller, ["p0"], "gen_stream", 8.0, max_new=5)
    pipeline.verify_smoke_readback_tolerance([raw_rb], "gated")  # must not raise
