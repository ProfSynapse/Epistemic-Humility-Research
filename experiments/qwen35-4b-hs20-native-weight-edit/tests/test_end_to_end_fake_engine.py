"""Whole-flow CPU test: every stage runs for real against a fake engine CLI (harness logic only)."""

from pathlib import Path

import pytest

from fakecli import make_flow
from hs20_nwe import adjudication as A
from hs20_nwe import stages
from hs20_nwe.util import HarnessError, read_json, read_jsonl, write_json, write_jsonl


@pytest.fixture(scope="module")
def flow(tmp_path_factory):
    """One shared project (module scope: the fake flow is deterministic and slow-ish)."""
    return make_flow(tmp_path_factory.mktemp("e2e") / "proj")


def test_01_doctor_and_materialize(flow):
    rep = stages.doctor(flow.ctx)
    assert rep["law_layer_explicit"] == 19 and rep["directions"]["c_hat"]["json_layer"] == 19
    assert rep["controller_strength"] == pytest.approx(8.0) and rep["clamp_setpoints"]["known"] > 0 > rep["clamp_setpoints"]["unknown"]
    out = stages.materialize(flow.ctx, flow.ctx.layout.local("inputs", shared=True))
    assert out["counts"]["heldout"]["confab"] == 300


def test_02_static_extract_inspect_localize_propose(flow):
    ctx = flow.ctx
    stages.emit_static(ctx)
    stages.extract(ctx, "fit_l")
    stages.inspect_stage(ctx)
    loc = stages.localize_stage(ctx)
    assert loc["eligible_blocks"] == [20, 21, 22]
    prop = stages.propose_stage(ctx)
    assert prop["n_proposals"] == 6 and prop["n_valid"] == 6
    reg = read_json(ctx.layout.local("patches/candidates.json", shared=True))
    assert [c["cand_id"] for c in reg["candidates"]] == ["b20_s4", "b20_s16", "b21_s4", "b21_s16", "b22_s4", "b22_s16"]
    ranking = read_json(ctx.layout.local("localization/ranking.json"))
    assert all(len(r["columns"]) == 32 for r in ranking["rankings"].values())


def test_03_engine_calls_use_the_registered_commands(flow):
    verbs = [c[0] for c in flow.cli.calls]
    assert verbs.count("extract") == 1 and verbs.count("weights-inspect") == 4 and verbs.count("weights-patch") == 6
    extract = next(c for c in flow.cli.calls if c[0] == "extract")
    assert extract[extract.index("--model") + 1] == str(flow.ctx.layout.local("base_model", shared=True))
    assert extract[extract.index("--model-revision") + 1] == flow.ctx.cell.revision and extract[-1] == "--i-know-this-runs-on-gpu"
    assert not any("--yes" in c for c in flow.cli.calls)


def test_04_baseline_generation_decoys_screen_and_selection(flow):
    ctx = flow.ctx
    out = stages.gen_static(ctx)
    assert out["baseline_gate"]["passed"] and out["decoys"]["positive"] >= 25 and out["decoys"]["negative"] >= 25
    stages.gen_screen_candidates(ctx)
    sel = stages.select_stage(ctx)
    assert sel["status"] == "selected" and sel["winner"] == "b21_s16"
    doc = read_json(ctx.layout.local("selection/selection.json"))
    eligible = {e["candidate"] for e in doc["evaluations"] if e["eligible"]}
    assert "b22_s16" not in eligible and "b20_s4" not in eligible and "b21_s16" in eligible
    assert doc["ranking"][0] == "b21_s16"


def test_05_budget_counts_every_generated_row(flow):
    summary = flow.ctx.ledger.summary()
    assert summary["generated_rows"] == 64 + 192 + 6 * 192 + 16 and summary["stopped"] is None


def test_06_controls_export_heldout_generation(flow):
    ctx = flow.ctx
    stages.controls_stage(ctx)
    ctl = read_json(ctx.layout.local("controls/controls.json"))
    assert ctl["K"] == 3 and ctl["all_matched"]
    for c in ctl["controls"]:
        assert c["relative_error"] <= 0.01 and len(c["history"]) <= 4
    stages.export_stage(ctx)
    stages.verify_selected(ctx)
    ex = stages.extract(ctx, "heldout")
    assert set(ex["fires"]) == {"confab", "known_correct"} and ex["fires"]["confab"] > 200
    stages.gen_heldout(ctx)
    summary = ctx.ledger.summary()
    assert summary["generated_rows"] == 64 + 192 + 6 * 192 + 6 * 660 + 2 * (300 + 360) + 40 + 38
    for name in ("heldout_native", "heldout_controller", "heldout_random_20261111", "clamp_known_native"):
        assert (ctx.layout.local(f"grades/{name}.jsonl")).exists()


def test_07_controller_arm_acts_only_on_fresh_sensor_fires(flow):
    ctx = flow.ctx
    recs = read_jsonl(ctx.layout.local("runlog/heldout_controller.jsonl"))
    cfg = __import__("yaml").safe_load(ctx.layout.local("configs/heldout_controller.yaml").read_text())
    assert cfg["arms"] == [{"name": "controller", "strength": pytest.approx(8.0), "flag_field": "fire"}]
    assert cfg["law"] == {"kind": "erase_write", "readout": "c_hat", "layer": 19, "position": "anchor_onward", "generation_mode": "gen_stream"}
    assert any(r["fire"] for r in recs) and len(recs) == 660


def test_08_native_arm_has_patch_and_zero_activation_only(flow):
    import yaml

    cfg = yaml.safe_load(flow.ctx.layout.local("configs/heldout_native.yaml").read_text())
    assert cfg["arms"] == [{"name": "baseline", "strength": 0.0}] and cfg["surface"]["weight_patch"]["path"].endswith("b21_s16/spec.yaml")
    assert "flag_field" not in cfg["arms"][0] and "score_field" not in cfg["arms"][0]
    assert cfg["surface"]["generation"] == {"max_new_tokens": 200, "min_new_tokens": 1, "do_sample": False, "seed": 0,
                                            "extra_eos_tokens": ["<|im_end|>"]}
    assert cfg["execution"]["batch_size"] == 4 and cfg["execution"]["render_fn"] == "hs20_nwe.render:render"
    unt = yaml.safe_load(flow.ctx.layout.local("configs/heldout_untouched.yaml").read_text())
    assert "weight_patch" not in unt["surface"]


def test_09_clamp_configs_use_u_d_setpoints_and_same_law(flow):
    import yaml

    k = yaml.safe_load(flow.ctx.layout.local("configs/clamp_known_native.yaml").read_text())
    u = yaml.safe_load(flow.ctx.layout.local("configs/clamp_unknown_untouched.yaml").read_text())
    cell = flow.ctx.cell
    assert k["calibration"]["doses"] == [pytest.approx(cell.clamp_setpoint("known"))] and k["calibration"]["dose_kind"] == "setpoint"
    assert u["calibration"]["doses"] == [pytest.approx(cell.clamp_setpoint("unknown"))]
    assert k["law"] == u["law"] and k["law"]["readout"] == "u_d" and k["law"]["layer"] == 19 and k["law"]["position"] == "anchor_onward"
    assert k["surface"]["rows_path"].endswith("heldout_sensor_confab.jsonl") and u["surface"]["rows_path"].endswith("heldout_sensor_known.jsonl")


def _grade_all(layout, tmp):
    """Test-only grader: reads the private map; decoys by construction; soft-abstention texts -> True."""
    pool = A.Pool(layout)
    out = {}
    for e in read_json(pool.manifest)["shards"]:
        sid = e["shard_id"]
        rows = {r["opaque_id"]: r["text"] for r in read_jsonl(pool.pool_file(sid))}
        graded = []
        for m in read_jsonl(pool.idmap_file(sid)):
            text = rows[m["opaque_id"]]
            graded.append({"opaque_id": m["opaque_id"], "is_abstention": ("remains unclear" in text) or m["kind"] == "decoy_pos"})
        out[sid] = Path(tmp) / f"{sid}.jsonl"
        write_jsonl(out[sid], graded)
    return out


def test_10_pool_adjudication_parity_and_rollup(flow, tmp_path):
    ctx = flow.ctx
    stages.pool_stage(ctx)
    manifest = read_json(A.Pool(ctx.layout).manifest)
    n_candidates = manifest["n_candidates"]
    assert n_candidates > 3000 and len(manifest["shards"]) == -(-n_candidates // 55)
    # detector-negative rows only: no refused_v2 row from any scored arm is pooled
    files = _grade_all(ctx.layout, tmp_path)
    with pytest.raises(HarnessError):                                    # hash before pool commit
        A.commit_hash(ctx.layout, "shard_000", files["shard_000"])
    A.commit_pool(ctx.layout)
    for sid, f in files.items():
        A.commit_hash(ctx.layout, sid, f)
    pack = A.spot_check_pack(ctx.cell, ctx.layout, files)
    labels = {r["opaque_id"]: r["is_abstention"] for path in files.values() for r in read_jsonl(path)}
    A.record_spot_check(ctx.cell, ctx.layout, [{"opaque_id": r["opaque_id"], "lead_is_abstention": labels[r["opaque_id"]]} for r in pack], accepted=True)
    rep = A.apply(ctx.cell, ctx.layout, {k: str(v) for k, v in files.items()})
    assert rep["instrument_valid"] and rep["n_core_credited"] == n_candidates
    # preflight parity evidence (zero patch, batch 1/4, export round trip), then the pre-sign drill evidence from the parent
    stages.parity_prepare(ctx, 8, include_selected=True)
    reg = stages.load_registry(ctx)
    stages.generate(ctx, [j for j in reg if j.startswith("parity_")])
    stages.parity_compare(ctx)
    write_json(ctx.layout.local("results/evidence/kill_resume_drill.json", shared=True), __import__("conftest").synthetic_drill(ctx.cell, ctx.layout))
    result = stages.rollup(ctx)
    assert result["G0"]["passed"], result["G0"]
    for gate in ("G1", "G2", "G3", "G4"):
        assert gate in result
    assert result["G1"]["passed"] and result["G2"]["passed"]
    assert result["interpretation"]["verdict"] in {"G1_G2_G3_pass", "G1_G2_G3_G4_pass", "falsified"}
    assert result["arms"]["heldout_native"]["confab"]["n"] == 300 and result["arms"]["heldout_native"]["known"]["n"] == 360
    assert result["arms"]["clamp_known_native"]["known"] is None
    assert ctx.ledger.summary()["generated_rows"] <= 7000


def test_11_rollup_is_instrument_invalid_without_pre_sign_evidence(flow):
    ctx = flow.ctx
    p = ctx.layout.local("results/evidence/kill_resume_drill.json", shared=True)
    keep = p.read_text()
    p.unlink()
    try:
        r = stages.rollup(ctx)
        assert r["interpretation"]["verdict"] == "instrument_invalid" and "kill_resume_drill" in r["G0"]["failed_or_missing"]
        assert "G1" not in r                                           # no behavioral verdict without G0
    finally:
        p.write_text(keep)


def test_12_job_resume_after_midrun_failure_is_exact(flow, tmp_path):
    """A partially written output resumes without duplicating rows and without double-counting the budget."""
    ctx = flow.ctx
    job = stages.load_registry(ctx)["heldout_untouched"]
    out = ctx.layout.local(job.output_rel)
    rows = read_jsonl(out)
    write_jsonl(out, rows[:100])                                      # simulate a kill after 100 rows
    before = ctx.ledger.generated_rows()
    stages.run_job(ctx, job)
    assert len(read_jsonl(out)) == 660 and len({r["row_key"] for r in read_jsonl(out)}) == 660
    assert ctx.ledger.generated_rows() == before + 2                  # conservative probe bound; file count is the unit, not the call count
