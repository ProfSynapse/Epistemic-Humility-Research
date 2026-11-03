"""Bounded-search null path (no held-out generation), baseline instrument failure, and CLI wiring."""

import json

import pytest

import fakecli
from fakecli import make_flow
from hs20_nwe import cli, stages
from hs20_nwe.util import HarnessError, read_json, write_json


def run_to_select(flow):
    ctx = flow.ctx
    stages.materialize(ctx, ctx.layout.local("inputs", shared=True))
    stages.emit_static(ctx)
    stages.extract(ctx, "fit_l")
    stages.inspect_stage(ctx)
    stages.localize_stage(ctx)
    stages.propose_stage(ctx)
    stages.gen_static(ctx)
    stages.gen_screen_candidates(ctx)
    return stages.select_stage(ctx)


def preflight_evidence(ctx):
    stages.parity_prepare(ctx, 8)
    stages.generate(ctx, ["parity_untouched_b4", "parity_untouched_b1", "parity_zero_b4"])
    stages.parity_compare(ctx)
    write_json(ctx.layout.local("results/evidence/kill_resume_drill.json", shared=True), __import__("conftest").synthetic_drill(ctx.cell, ctx.layout))


def test_no_eligible_candidate_stops_before_heldout_and_rolls_up_as_bounded_search_null(tmp_path, monkeypatch):
    monkeypatch.setattr(fakecli, "CAND_P", {k: (0.10, 0.0) for k in fakecli.CAND_P})          # nobody reaches 0.40 confab refusal
    flow = make_flow(tmp_path / "proj")
    ctx = flow.ctx
    sel = run_to_select(flow)
    assert sel["status"] == "no_eligible" and sel["winner"] is None
    before = ctx.ledger.generated_rows()
    for fn in (stages.controls_stage, stages.export_stage, stages.gen_heldout, stages.pool_stage):
        assert fn(ctx) == {"skipped": True}
    assert ctx.ledger.generated_rows() == before                                          # no held-out generation
    assert not (ctx.layout.local("runlog/heldout_untouched.jsonl")).exists()
    r = stages.rollup(ctx)
    assert r["interpretation"]["verdict"] == "instrument_invalid"                         # a missing G0 component is instrument-invalid
    preflight_evidence(ctx)
    r = stages.rollup(ctx)
    assert r["interpretation"]["verdict"] == "bounded_search_null"
    assert r["G0_fit_side"]["passed"] and "G1" not in r


def test_null_requires_complete_fit_evidence_and_valid_integrity(tmp_path, monkeypatch):
    monkeypatch.setattr(fakecli, "CAND_P", {k: (0.10, 0.0) for k in fakecli.CAND_P})
    flow = make_flow(tmp_path / "proj")
    ctx = flow.ctx
    run_to_select(flow)
    preflight_evidence(ctx)
    (ctx.layout.local("grades/screen_b21_s16.jsonl")).unlink()                            # FIT evidence gap
    assert stages.rollup(ctx)["interpretation"]["verdict"] == "incomplete"
    flow2 = make_flow(tmp_path / "proj2")
    run_to_select(flow2)
    preflight_evidence(flow2.ctx)
    p = flow2.ctx.layout.local("results/evidence/zero_patch_token_parity.json", shared=True)
    doc = read_json(p)
    doc["passed"] = False
    write_json(p, doc)
    r = stages.rollup(flow2.ctx)
    assert r["interpretation"]["verdict"] == "instrument_invalid"                         # integrity, not a behavioral null


def test_budget_stop_makes_the_rollup_instrument_invalid_not_partial(tmp_path):
    flow = make_flow(tmp_path / "proj")
    ctx = flow.ctx
    run_to_select(flow)
    ctx.ledger.stop("generated_rows_cap", note="test")
    r = stages.rollup(ctx)
    assert r["interpretation"]["verdict"] == "instrument_invalid" and "budget" in r["interpretation"]["statement"]
    with pytest.raises(HarnessError):
        ctx.ledger.reserve("again", 1)


def test_unpatched_baseline_below_floor_is_an_instrument_failure(tmp_path, monkeypatch):
    monkeypatch.setattr(fakecli.FakeCLI, "_text", lambda self, r, refuse: '{"answer": "wrong", "response_confidence": 0.5}')
    flow = make_flow(tmp_path / "proj")
    ctx = flow.ctx
    stages.materialize(ctx, ctx.layout.local("inputs", shared=True))
    stages.emit_static(ctx)
    with pytest.raises(HarnessError) as e:
        stages.gen_static(ctx)
    assert e.value.code in {"BASELINE_GATE", "DECOY_FLOOR"}


def test_cli_refuses_gpu_without_ack_and_plans_a_pipeline(tmp_path, capsys):
    flow = make_flow(tmp_path / "proj")
    base = ["--project-root", str(flow.root)]
    assert cli.main(base + ["materialize"]) == 0
    assert cli.main(base + ["stage", "emit-static"]) == 0
    capsys.readouterr()
    assert cli.main(base + ["stage", "extract-fit-l"]) == 2                                 # no --gpu-ack, and no GPU anyway
    assert "error" in capsys.readouterr().err
    assert cli.main(base + ["plan-pipeline", "--python", "python"]) == 0
    out = json.loads(capsys.readouterr().out.split("\n}\n")[-2] + "\n}")
    assert out["stages"][0] == "materialize" and out["stages"][-1] == "build_pool"
    assert cli.main(base + ["budget"]) == 0


def test_smoke_tree_is_isolated_and_counts_against_the_same_cap(tmp_path):
    flow = make_flow(tmp_path / "proj")
    stages.materialize(flow.ctx, flow.ctx.layout.local("inputs", shared=True))
    smoke = stages.Ctx(flow.root, flow.ctx.cell, type(flow.ctx.layout)(flow.root, flow.ctx.layout.slug, tag="s1"), gpu_ack=True)
    smoke.engine_override = stages.Engine(flow.root, [], smoke.ledger, cli=fakecli.FakeCLI(smoke.layout, flow.root))
    stages.smoke_prepare(flow.ctx, smoke, ["fit_l"], 12)
    stages.emit_static  # smoke uses its own configs/outputs
    from hs20_nwe import jobs as J

    from hs20_nwe.util import read_jsonl, write_yaml

    write_yaml(smoke.layout.local("configs/extract_fit_l.yaml"),
               J.extract_config(smoke.cell, smoke.layout, rows_rel="materialize/fit_l.jsonl", out_rel="capture/fit_l", with_sites=True))
    smoke_rows = read_jsonl(smoke.layout.local("materialize/fit_l.jsonl", shared=True))
    assert 12 <= len(smoke_rows) <= 15 and {r["role"] for r in smoke_rows} == {"confab", "known_correct", "unknown_refused"}
    stages.extract(smoke, "fit_l")
    assert "smoke/s1/capture/fit_l" in str(smoke.layout.local("capture/fit_l"))
    assert (smoke.layout.local("capture/fit_l") / "manifest.json").exists() and not flow.ctx.layout.local("capture/fit_l").exists()
