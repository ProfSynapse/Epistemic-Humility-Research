"""Installed-consumer checks against the real engine wheel (no torch, no model, no GPU).

* ``mechinterp run --dry-run`` plans the generated pipelines through the host ``EngineCLI``.
* Every generated engine config is fed to the wheel's own CLI; reaching the torch import (which this CPU venv
  lacks) means the wheel's argument parser AND pydantic config schema accepted it.
"""

import json
import shutil
import subprocess
import sys

import pytest

from conftest import EXPERIMENT, SLUG, make_inputs
from hs20_nwe import jobs as J
from hs20_nwe import pipeline, stages
from hs20_nwe.config import Layout
from hs20_nwe.engine import Engine
from hs20_nwe.util import read_jsonl, write_jsonl, write_yaml

@pytest.fixture
def host(project, cell):
    """A host project that carries the plugin package inside experiments/<slug> (a legal plugin root)."""
    root = project.root
    exp = root / "experiments" / SLUG
    exp.mkdir(parents=True)
    shutil.copytree(EXPERIMENT / "hs20_nwe", exp / "hs20_nwe", ignore=shutil.ignore_patterns("__pycache__"))
    make_inputs(project, cell)
    ctx = stages.Ctx(root, cell, Layout(root, SLUG))
    (ctx.layout.local("base_model", shared=True)).mkdir(parents=True)
    stages.materialize(ctx, ctx.layout.local("inputs", shared=True))
    stages.emit_static(ctx)
    return ctx, exp


def sensor_rows(ctx):
    rows = [{**r, "fire": r["role"] == "confab", "score_neg_z_d": 0.0, "proj_d": 0.0}
            for r in read_jsonl(ctx.layout.local("materialize/heldout.jsonl", shared=True))]
    write_jsonl(ctx.layout.local("materialize/heldout_sensor.jsonl", shared=True), rows)
    write_jsonl(ctx.layout.local("materialize/heldout_sensor_confab.jsonl", shared=True), [r for r in rows if r["role"] == "confab"])
    write_jsonl(ctx.layout.local("materialize/heldout_sensor_known.jsonl", shared=True), [r for r in rows if r["role"] == "known_correct"])


def write_all_jobs(ctx):
    sensor_rows(ctx)
    lay = ctx.layout
    spec = lay.local("patches/b21_s16/spec.yaml", shared=True)
    spec.parent.mkdir(parents=True)
    spec.write_text("placeholder: spec bytes pinned by sha only\n")
    ctl = lay.local("controls/seed1/spec.yaml", shared=True)
    ctl.parent.mkdir(parents=True)
    ctl.write_text("placeholder\n")
    jobs = J.heldout_jobs(ctx.cell, lay, selected_spec_rel="patches/b21_s16/spec.yaml", control_spec_rels={1: "controls/seed1/spec.yaml"})
    jobs += J.clamp_jobs(ctx.cell, lay, selected_spec_rel="patches/b21_s16/spec.yaml")
    jobs.append(J.screen_candidate_job(ctx.cell, lay, "b21_s16"))
    return jobs


def plan(ctx, exp, doc, tmp_ref="pipeline/check.yaml"):
    write_yaml(ctx.layout.local(tmp_ref, shared=True), doc)
    eng = Engine(ctx.project_root, [exp])
    out = ctx.layout.local("pipeline/plan.out.json", shared=True)
    rc, result = eng.run_json(["run", "--config", ctx.layout.ref(tmp_ref, shared=True), "--provider", "local", "--dry-run", "--json"], out)
    assert rc == 0, out.read_text()[:2000]
    return result["data"]


def test_default_pipeline_plans_through_the_installed_host(host):
    ctx, exp = host
    doc = pipeline.build(ctx.cell, ctx.layout, python=sys.executable)
    data = plan(ctx, exp, doc)
    names = [s["name"] for s in data["stages"]]
    assert names == [s["name"] for s in doc["stages"]] and names[0] == "materialize" and names[-1] == "build_pool"
    assert all(s["kind"] == "command" for s in data["stages"])
    assert data["model"] == str(ctx.layout.local("base_model", shared=True)) and data["model_revision"] == ctx.cell.revision
    assert data["runtime"]["pythonpath"] == [str(exp)]
    gpu = [s for s in data["stages"] if "--gpu-ack" in s["command"]]
    assert {s["name"] for s in gpu} == {"extract_fit_l", "gen_static", "gen_screen_candidates", "extract_heldout", "gen_heldout", "verify_selected"}
    assert "--yes" not in json.dumps(data) and "--i-know-this-runs-on-gpu" not in json.dumps(data)


def test_native_static_pipeline_plans_native_engine_stages(host):
    ctx, exp = host
    from hs20_nwe.util import HarnessError
    with pytest.raises(HarnessError, match="bypasses"):
        pipeline.build(ctx.cell, ctx.layout, python=sys.executable, native_static=True)


def test_every_generated_engine_config_is_accepted_by_the_wheel(host):
    """Native plan of every job kind, then each command run: the failure must be the missing torch, not a parse/schema error."""
    ctx, exp = host
    jobs = write_all_jobs(ctx)
    stages_ = [{"name": "extract_fit_l", "kind": "mechinterp.extract", "config": ctx.layout.ref("configs/extract_fit_l.yaml")},
               {"name": "extract_heldout", "kind": "mechinterp.extract", "config": ctx.layout.ref("configs/extract_heldout.yaml")}]
    stages_ += [{"name": j.job_id, "kind": "mechinterp.steer" if j.kind == "steer" else "mechinterp.dose-calibrate",
                 "config": ctx.layout.ref(j.config_rel)} for j in jobs]
    stages_ += [{"name": s, "kind": "mechinterp.steer", "config": ctx.layout.ref(f"configs/{s}.yaml")} for s in ("decoy_baseline", "screen_baseline")]
    doc = {"schema_version": "mechinterp-pipeline/v1", "name": "all-configs", "model": J.model_path(ctx.layout),
           "model_revision": ctx.cell.revision, "runtime": {"provider": "local", "python": sys.executable,
                                                              "pythonpath": [f"project://experiments/{SLUG}"]}, "stages": stages_}
    data = plan(ctx, exp, doc, "pipeline/all.yaml")
    assert len(data["stages"]) == len(stages_)
    seen = set()
    from engine_host.cli_boundary import EngineCLI

    cli = EngineCLI(ctx.project_root, plugin_roots=[exp])
    for s in data["stages"]:
        cmd = s["command"]
        verb = cmd[cmd.index("mechinterp") + 1]
        args = cmd[cmd.index("mechinterp") + 1:] + ["--i-know-this-runs-on-gpu"]
        res = subprocess.run(cli.command("mechinterp", args), cwd=ctx.project_root, capture_output=True, text=True)
        text = res.stdout + res.stderr
        assert res.returncode != 2 and "unrecognized arguments" not in text, text[-600:]
        assert "ValidationError" not in text and "validation error" not in text.lower(), (s["name"], text[-800:])
        assert "torch" in text, (s["name"], text[-800:])                  # got as far as importing the (absent) ML stack
        seen.add(verb)
    assert seen == {"extract", "steer", "dose-calibrate"}


def test_weights_cli_argument_forms_are_accepted_by_the_wheel_parser(host):
    """weights-inspect / weights-patch flags parse; they then stop at the absent torch (no spec parsing is possible here)."""
    ctx, exp = host
    from engine_host.cli_boundary import EngineCLI

    cli = EngineCLI(ctx.project_root, plugin_roots=[exp])
    for args in (["weights-inspect", "--weights-config", "artifact://x/i.yaml", "--json"],
                 ["weights-patch", "--weights-config", "artifact://x/p.yaml", "--validate", "--json"],
                 ["weights-patch", "--weights-config", "artifact://x/p.yaml", "--export", "--json"]):
        res = subprocess.run(cli.command("mechinterp", args), cwd=ctx.project_root, capture_output=True, text=True)
        assert res.returncode != 2 and "unrecognized arguments" not in res.stderr + res.stdout, args


def test_host_refuses_a_plugin_root_that_shadows_an_engine_package(host):
    ctx, exp = host
    (exp / "shared").mkdir()
    from engine_host.cli_boundary import EngineCLI

    with pytest.raises(ValueError):
        EngineCLI(ctx.project_root, plugin_roots=[exp])


def test_no_engine_internal_imports_or_path_hacks_in_the_package():
    import ast

    banned_roots = {"tuner", "MechInterp", "shared", "Trainers", "Evaluator", "SynthChat", "schemas", "synaptic_tuner"}
    for path in (EXPERIMENT / "hs20_nwe").glob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert not ({a.name.split(".")[0] for a in node.names} & banned_roots), path.name
            if isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                assert node.module.split(".")[0] not in banned_roots, path.name
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr == "path" and isinstance(node.value, ast.Name) and node.value.id == "sys":
                raise AssertionError(f"{path.name} touches sys.path")
