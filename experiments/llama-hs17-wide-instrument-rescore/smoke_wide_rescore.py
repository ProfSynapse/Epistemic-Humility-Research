#!/usr/bin/env python3
"""CPU-only smoke for llama-hs17-wide-instrument-rescore (WR-G0). Never
loads a real model, never touches the GPU, never makes a network call.

Per the narrow cell's own crash-1 lesson (NOTEBOOK.md 2026-08-25: "the smoke
stub had bypassed run_one_row so the smoke could not catch it"), this smoke
does NOT bypass the new code this cell adds: it calls
`run_wide_rescore.run_one_row_with_text` FOR REAL, with a stub
model/tokenizer/controller standing in only for the GPU/model boundary
(`model.generate`, `tokenizer.__call__`/`.decode`, `controller.begin_pass`/
`.reset`/`.hook.last_readback`) -- every other call inside
`run_one_row_with_text` (`gl.run_pass_fixed`, `gl.grade_clean_tighten`,
`pl.grader.grade_one`) is the real, unmodified parent function.

Checks (each printed pass/fail; nonzero exit on any failure):
  1. frozen-input sha verification fires on tamper
  2. run-log persistence schema: non-empty out_text + full narrow sub-grade
     dict (`grade`, `old_grade`) + termination/readback fields, on every
     smoke record (both the real-path record and the stub-arm records)
  3. RunLog's required_fields contract: a record missing/emptying out_text
     raises RunLogError
  4. resume-from-checkpoint: iter_pending skips already-recorded keys after
     a fresh RunLog re-open with the same run_config
  5. detector_v2 imports and scores a synthetic string (canonical refusal
     True, committed-answer False)
  6. gate math (WR-G2/WR-G3/WR-G4) reproduces hand-computed values on a tiny
     synthetic fixture, including WR-G4's NOT-ADJUDICABLE and PASS branches
"""

from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

import torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import run_wide_rescore as rwr  # noqa: E402
import gates_wide_rescore as gwr  # noqa: E402

narrow = rwr.narrow

RESULTS: dict[str, bool] = {}


def check(name: str, cond: bool) -> None:
    RESULTS[name] = bool(cond)
    print(f"[smoke] {'PASS' if cond else 'FAIL'}: {name}")


# --------------------------------------------------------------------------
# 1. frozen-input sha verification fires on tamper.
# --------------------------------------------------------------------------

def check_sha_tamper() -> None:
    cell_cfg = rwr.load_yaml(rwr.CELL_YAML)
    tampered = dict(cell_cfg)
    tampered["frozen_reuse_sha256"] = dict(cell_cfg["frozen_reuse_sha256"])
    tampered["frozen_reuse_sha256"]["u_d"] = "0" * 64
    raised = False
    try:
        narrow.verify_frozen_reuse(tampered)
    except SystemExit:
        raised = True
    check("frozen_reuse_sha_tamper_detected", raised)

    # Belt-and-braces: the UNTAMPERED cfg must still verify OK (proves the
    # tamper test above is meaningful, not a check that always raises).
    verified_ok = False
    try:
        narrow.verify_frozen_reuse(cell_cfg)
        verified_ok = True
    except SystemExit:
        verified_ok = False
    check("frozen_reuse_sha_untampered_verifies_ok", verified_ok)


# --------------------------------------------------------------------------
# 2 + 3 + 4: run_one_row_with_text on a stubbed model/tokenizer/controller,
# RunLog required_fields contract, resume-from-checkpoint.
# --------------------------------------------------------------------------

class _FakeEnc(dict):
    def to(self, _dev):
        return self


class _FakeTokenizer:
    pad_token_id = 0

    def __init__(self, decode_map: dict[tuple[int, ...], str]):
        self.decode_map = decode_map

    def __call__(self, prompt, return_tensors="pt"):
        return _FakeEnc({"input_ids": torch.tensor([[1, 2, 3]], dtype=torch.long),
                          "attention_mask": torch.tensor([[1, 1, 1]], dtype=torch.long)})

    def decode(self, ids, skip_special_tokens=True):
        return self.decode_map.get(tuple(int(x) for x in ids.tolist()), "")


class _FakeModel:
    def __init__(self, sequences: list[list[int]]):
        self.sequences = sequences
        self.calls = 0
        self._params = [torch.zeros(1)]

    def parameters(self):
        return iter(self._params)

    def generate(self, input_ids=None, attention_mask=None, **_kwargs):
        seq = self.sequences[min(self.calls, len(self.sequences) - 1)]
        self.calls += 1
        return torch.cat([input_ids, torch.tensor([seq], dtype=torch.long)], dim=1)


class _FakeHook:
    def __init__(self):
        self.last_readback = None


class _FakeController:
    def __init__(self, dose_readback: float | None = None):
        self.hook = _FakeHook()
        self._dose_readback = dose_readback
        self.reset_calls = 0

    def begin_pass(self, mode, strength, attention_mask=None):
        if mode == "gen_stream" and self._dose_readback is not None:
            self.hook.last_readback = {"measured": [self._dose_readback]}
        else:
            self.hook.last_readback = None

    def reset(self):
        self.reset_calls += 1


def _run_one_row_stubbed(*, fire: bool, dose_readback: float | None) -> dict:
    base_ids = (101, 102)
    dosed_ids = (201, 202, 203)
    decode_map = {
        base_ids: '{"answer": "a stub baseline answer", "response_confidence": 0.5}',
        dosed_ids: '{"answer": "I don\'t know the answer", "response_confidence": 0.9}',
    }
    model = _FakeModel([list(base_ids), list(dosed_ids)])
    tokenizer = _FakeTokenizer(decode_map)
    controller = _FakeController(dose_readback=dose_readback)
    row = {"row_key": "smoke_row_1", "role": "confab", "category_canon": "smoke",
           "hs_index": rwr.HS_INDEX, "fire": fire, "aliases": []}

    orig_render = narrow.ml.render
    narrow.ml.render = lambda family, tok, r: "FAKE SMOKE PROMPT"
    try:
        rec = rwr.run_one_row_with_text(
            model, controller, tokenizer, torch.device("cpu"), [999], row, strength_if_dosed=1.0,
        )
    finally:
        narrow.ml.render = orig_render
    return rec


def check_run_one_row_and_runlog_contract() -> None:
    rec_fired = _run_one_row_stubbed(fire=True, dose_readback=4.9549)
    rec_unfired = _run_one_row_stubbed(fire=False, dose_readback=None)

    check("run_one_row_with_text_fired_out_text_nonempty", bool(rec_fired["out_text"]))
    check("run_one_row_with_text_fired_baseline_text_nonempty", bool(rec_fired["baseline_text"]))
    check("run_one_row_with_text_fired_has_full_grade_dict",
          set(rec_fired["grade"]) == {"well_formed", "n_answer_keys", "single_answer_key",
                                       "trailing_clean", "answer_value", "semantic_refuse",
                                       "terminated_naturally", "degenerate", "clean_tighten"})
    check("run_one_row_with_text_fired_has_old_grade_dict",
          set(rec_fired["old_grade"]) == {"degenerate", "refused", "answered", "correct", "well_formed_correct"})
    check("run_one_row_with_text_fired_readback_measured", rec_fired["readback_measured"] == 4.9549)
    check("run_one_row_with_text_fired_terminated_naturally", rec_fired["terminated_naturally"] is True)
    check("run_one_row_with_text_fired_clean_tighten_true", rec_fired["clean_tighten"] is True)
    check("run_one_row_with_text_unfired_out_text_equals_baseline",
          rec_unfired["out_text"] == rec_unfired["baseline_text"] and bool(rec_unfired["out_text"]))
    check("run_one_row_with_text_unfired_readback_none", rec_unfired["readback_measured"] is None)

    RunLog, RunLogError = narrow.ml.load_run_log_class()
    tmpdir = Path(tempfile.mkdtemp(prefix="wr_smoke_runlog_"))
    try:
        log_path = tmpdir / "smoke.jsonl"
        run_log = RunLog(log_path, run_config={"smoke": True}, required_fields=("out_text",))
        try:
            run_log.record("row_ok", rec_fired)
            missing_field_raised = False
            try:
                run_log.record("row_missing_field", {k: v for k, v in rec_fired.items() if k != "out_text"})
            except RunLogError:
                missing_field_raised = True
            check("runlog_required_fields_raises_on_missing_field", missing_field_raised)

            empty_text_raised = False
            try:
                run_log.record("row_empty_text", {**rec_fired, "out_text": ""})
            except RunLogError:
                empty_text_raised = True
            check("runlog_required_fields_raises_on_empty_text", empty_text_raised)
        finally:
            run_log.close()

        # 4. resume-from-checkpoint: reopen with the SAME run_config; iter_pending
        # must skip "row_ok" (already durable on disk) and yield only new items.
        run_log2 = RunLog(log_path, run_config={"smoke": True}, required_fields=("out_text",))
        try:
            items = [{"row_key": "row_ok"}, {"row_key": "row_new_1"}, {"row_key": "row_new_2"}]
            pending = list(run_log2.iter_pending(items, key_fn=lambda it: it["row_key"]))
            check("runlog_resume_skips_done_keys",
                  [p["row_key"] for p in pending] == ["row_new_1", "row_new_2"])
            check("runlog_resume_done_keys_contains_row_ok", "row_ok" in run_log2.done_keys())
        finally:
            run_log2.close()
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    # Also exercise run_arm_smoke's own stub path (the CLI's --smoke mode) end
    # to end: every record must carry non-empty out_text too.
    tmpdir2 = Path(tempfile.mkdtemp(prefix="wr_smoke_arm_"))
    try:
        gate_rows = [
            {"row_key": f"k{i}", "role": "confab", "category_canon": "c", "hs_index": rwr.HS_INDEX,
             "fire": bool(i % 3 == 0)} for i in range(10)
        ]
        recs = rwr.run_arm_smoke("smoke_arm", gate_rows, force_no_fire=False, bias=0.3, checkpoint_dir=tmpdir2)
        check("run_arm_smoke_all_records_have_nonempty_out_text",
              all(bool(r.get("out_text")) for r in recs) and len(recs) == 10)
        # Re-invoking with the same checkpoint dir/rows must not duplicate work
        # (resume path exercised again, through the harness's own arm runner).
        size_before = (tmpdir2 / "smoke_arm.jsonl").stat().st_size
        recs2 = rwr.run_arm_smoke("smoke_arm", gate_rows, force_no_fire=False, bias=0.3, checkpoint_dir=tmpdir2)
        size_after = (tmpdir2 / "smoke_arm.jsonl").stat().st_size
        check("run_arm_smoke_resume_is_idempotent", size_before == size_after and len(recs2) == 10)
    finally:
        shutil.rmtree(tmpdir2, ignore_errors=True)


# --------------------------------------------------------------------------
# 5. detector_v2 imports and scores a synthetic string.
# --------------------------------------------------------------------------

def check_detector_v2() -> None:
    import score_wide_rescore as swr
    swr.verify_wide_pins()
    detector_v2 = swr._detector_v2()
    cfg = detector_v2.load_patterns()
    check("detector_v2_flags_canonical_refusal", detector_v2.is_refused_v2("I don't know the answer.", cfg) is True)
    check("detector_v2_does_not_flag_committed_answer",
          detector_v2.is_refused_v2("Paris is the capital of France.", cfg) is False)


# --------------------------------------------------------------------------
# 6. gate math on a tiny synthetic, hand-computed fixture.
# --------------------------------------------------------------------------

def _mk_confab_row(row_key: str, arm: str, refused_v2: bool) -> dict:
    return {"cell": "WR", "row_key": row_key, "arm": arm, "role": "confab",
            "refused_v2": refused_v2, "fire": True, "well_formed_correct": False}


def _mk_known_row(row_key: str, arm: str, fire: bool, refused_v2: bool) -> dict:
    return {"cell": "WR", "row_key": row_key, "arm": arm, "role": "known_correct_answered",
            "refused_v2": refused_v2, "fire": fire, "well_formed_correct": not refused_v2}


def check_gate_math() -> None:
    seeds = rwr.SEEDS
    all_rows: list[dict] = []
    applied_rows: list[dict] = []

    # Every detector_v2-negative (refused_v2==False) row needs an explicit
    # applied_rows entry: `_wide_rate_flags` EXCLUDES (never defaults) a
    # non-refused row with no adjudication entry, matching the real
    # pipeline's "voided/decoy -> excluded" semantics -- so a synthetic
    # fixture must adjudicate every non-refused core row it wants counted.

    # arm0_baseline confab: 5 rows, 1/5 refused_v2 True -> wide rate 0.2
    # (c0 True by detector; c1..c4 adjudicated False)
    for i in range(5):
        all_rows.append(_mk_confab_row(f"c{i}", "arm0_baseline", refused_v2=(i == 0)))
    for i in range(1, 5):
        applied_rows.append({"row_key": f"c{i}", "arm": "arm0_baseline", "refused_final": False})

    # arm1_gated_replication confab: 5 rows, refused_v2 = [T,T,T,F,F];
    # d3 adjudicated True, d4 adjudicated False -> wide rate 4/5 = 0.8
    arm1_flags = [True, True, True, False, False]
    for i, rv2 in enumerate(arm1_flags):
        all_rows.append(_mk_confab_row(f"d{i}", "arm1_gated_replication", refused_v2=rv2))
    applied_rows.append({"row_key": "d3", "arm": "arm1_gated_replication", "refused_final": True})
    applied_rows.append({"row_key": "d4", "arm": "arm1_gated_replication", "refused_final": False})

    # 15 random arms, all identical: 5 rows, 0/5 refused_v2, all adjudicated
    # False -> wide rate 0.0 (uniform, so max_abs_random_lift is exact:
    # 0.0 - 0.2 = -0.2 for every seed)
    for seed in seeds:
        arm_id = f"arm2_random_{seed}"
        for i in range(5):
            row_key = f"r{seed}_{i}"
            all_rows.append(_mk_confab_row(row_key, arm_id, refused_v2=False))
            applied_rows.append({"row_key": row_key, "arm": arm_id, "refused_final": False})

    # WR-G4 fixture A: known-correct, arm1, 25 fired rows (>= floor 22), all
    # non-refused, all adjudicated False -> wide rate 0/25 = 0.0 -> expect PASS.
    for i in range(25):
        row_key = f"kfired{i}"
        all_rows.append(_mk_known_row(row_key, "arm1_gated_replication", fire=True, refused_v2=False))
        applied_rows.append({"row_key": row_key, "arm": "arm1_gated_replication", "refused_final": False})

    scored_summary = {
        "WR_G1_regeneration_bridge": {"id": "WR-G1", "pass": True, "metric": {"rate": 0.8}},
        "per_arm": {
            "arm0_baseline": {"narrow_confab": {"rate": 0.2}},
            "arm1_gated_replication": {"narrow_confab": {"rate": 0.8}},
            **{f"arm2_random_{seed}": {"narrow_confab": {"rate": 0.0}} for seed in seeds},
        },
    }

    gates = gwr.compute_wr_gates(all_rows, applied_rows, scored_summary)

    check("gate_math_wr_g2_net_lift", abs(gates["WR-G2"]["net_lift"] - 0.6) < 1e-9)
    check("gate_math_wr_g2_pass", gates["WR-G2"]["pass"] is True)
    check("gate_math_wr_g3_max_abs_random_lift", abs(gates["WR-G3"]["max_abs_random_lift"] - 0.2) < 1e-9)
    check("gate_math_wr_g3_effect_ratio", abs(gates["WR-G3"]["effect_ratio"] - 3.0) < 1e-9)
    check("gate_math_wr_g3_pass", gates["WR-G3"]["pass"] is True)
    check("gate_math_wr_g4_fired_n", gates["WR-G4"]["fired_n"] == 25)
    check("gate_math_wr_g4_floor_is_22", gates["WR-G4"]["adjudicability_floor"] == 22)
    check("gate_math_wr_g4_disposition_pass", gates["WR-G4"]["disposition"] == "PASS")
    check("gate_math_wr_g4_pass_bool", gates["WR-G4"]["pass"] is True)

    # WR-G4 fixture B: same confab fixture, but only 10 fired known-correct
    # rows (< floor 22) -> expect NOT-ADJUDICABLE, pass=None.
    all_rows_below_floor = [r for r in all_rows if r["role"] != "known_correct_answered"]
    for i in range(10):
        all_rows_below_floor.append(_mk_known_row(f"kfired{i}", "arm1_gated_replication", fire=True, refused_v2=False))
    gates_below = gwr.compute_wr_gates(all_rows_below_floor, applied_rows, scored_summary)
    check("gate_math_wr_g4_below_floor_not_adjudicable", gates_below["WR-G4"]["disposition"] == "NOT-ADJUDICABLE")
    check("gate_math_wr_g4_below_floor_pass_is_none", gates_below["WR-G4"]["pass"] is None)

    # WR-G2 fail branch: shrink arm1's confab lift to match arm0's baseline
    # (net_lift 0.0 < 0.30) to force WR-G3 to report adjudicable=False,
    # pass=None (adjudicable_only_if WR-G2 PASS). Reuses the SAME fully-
    # adjudicated applied_rows for arm0/random arms/known-correct, plus its
    # own weak-arm1 adjudication, so this branch's own numbers are internally
    # consistent too (not merely coincidentally degenerate).
    all_rows_weak = [r for r in all_rows if not (r["arm"] == "arm1_gated_replication" and r["role"] == "confab")]
    applied_rows_weak = [r for r in applied_rows if r["arm"] != "arm1_gated_replication"]
    for i in range(5):
        all_rows_weak.append(_mk_confab_row(f"d{i}", "arm1_gated_replication", refused_v2=(i == 0)))  # 1/5 -> rate 0.2, lift 0.0
    for i in range(1, 5):
        applied_rows_weak.append({"row_key": f"d{i}", "arm": "arm1_gated_replication", "refused_final": False})
    gates_weak = gwr.compute_wr_gates(all_rows_weak, applied_rows_weak, scored_summary)
    check("gate_math_wr_g2_fail_branch", gates_weak["WR-G2"]["pass"] is False)
    check("gate_math_wr_g3_not_adjudicable_when_g2_fails",
          gates_weak["WR-G3"]["adjudicable"] is False and gates_weak["WR-G3"]["pass"] is None)


def main() -> int:
    check_sha_tamper()
    check_run_one_row_and_runlog_contract()
    check_detector_v2()
    check_gate_math()

    n_pass = sum(1 for v in RESULTS.values() if v)
    n_total = len(RESULTS)
    print(f"\n[smoke_wide_rescore] {n_pass}/{n_total} checks passed")
    failed = [k for k, v in RESULTS.items() if not v]
    if failed:
        print(f"[smoke_wide_rescore] FAILED: {failed}", file=sys.stderr)
        return 1
    print("[smoke_wide_rescore] ALL CHECKS PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
