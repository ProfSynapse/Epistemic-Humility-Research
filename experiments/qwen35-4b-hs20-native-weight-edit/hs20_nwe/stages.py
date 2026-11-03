"""Stage runners: each is idempotent, writes a completion marker, and says what it persists.

GPU-bearing stages call the engine only through ``Engine`` (host ``EngineCLI``)
after budget reservation.  CPU stages that need the engine (weights-inspect /
weights-patch) also go through it.  No stage prints row text.
"""

from __future__ import annotations

import os
import time
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import yaml

from . import adjudication, capture, grading, inputs, jobs as J, localize, selection, sensor, weights
from .budget import Ledger, planned_new_rows
from .config import EXPERIMENT_DIR, Cell, Layout, find_project_root
from .engine import Engine
from .util import (HarnessError, read_json, read_jsonl, sha256_file, write_json, write_jsonl)


@dataclass
class Ctx:
    project_root: Path
    cell: Cell
    layout: Layout
    gpu_ack: bool = False
    engine_override: Engine | None = None

    @classmethod
    def create(cls, project_root: Path | None = None, *, tag: str | None = None, gpu_ack: bool = False,
               experiment_dir: Path | None = None) -> "Ctx":
        root = find_project_root(project_root) if project_root is None else Path(project_root).resolve()
        cell = Cell.load(experiment_dir)
        return cls(root, cell, Layout(root, cell.slug, tag=tag), gpu_ack)

    @property
    def ledger(self) -> Ledger:
        return Ledger(self.cell, self.layout)

    @property
    def engine(self) -> Engine:
        if self.engine_override is not None:
            return self.engine_override
        # The frozen render finds its tokenizer from this variable (a plain local path); engine children inherit it.
        os.environ.setdefault("HS20NWE_RENDER_MODEL", J.model_path(self.layout))
        try:
            return Engine(self.project_root, [EXPERIMENT_DIR], self.ledger)
        except ValueError as exc:                       # the host boundary refused (pin, plug-in root, shadowing)
            raise HarnessError("ENGINE_BOUNDARY", str(exc)) from exc

    def done(self, name: str, payload: dict) -> dict:
        record = {"stage": name, "ts": time.time(), **self.cell.stamp(), **payload}
        write_json(self.layout.local(f"stages/{name}.done.json"), record)
        return record

    def is_done(self, name: str) -> bool:
        return self.layout.local(f"stages/{name}.done.json").exists()

    def direction(self, name: str) -> tuple[Path, str]:
        path = self.layout.project_local(J.direction_ref(self.cell, name))
        return path, sha256_file(path)

    def c_hat_u_d(self) -> tuple[np.ndarray, np.ndarray]:
        dim = int(self.cell.cell["model"]["hidden_dim"])
        return (sensor.load_direction_vector(self.direction("c_hat")[0], hidden_dim=dim),
                sensor.load_direction_vector(self.direction("u_d")[0], hidden_dim=dim))


# ----------------------------------------------------------------------------------------
# preflight / doctor (CPU)
# ----------------------------------------------------------------------------------------

def doctor(ctx: Ctx) -> dict:
    """Promoted-direction bytes, layer convention, sensor constants and frozen-port pins."""
    root = ctx.project_root
    prov = read_json(ctx.layout.project_local(f"{ctx.cell.cell['writer']['direction_root']}/provenance.json"))
    build = read_json(ctx.layout.project_local(f"{ctx.cell.cell['writer']['direction_root']}/build_manifest.json"))
    report = {"directions": {}, "constants": {}}
    for name in ("c_hat", "u_d"):
        path, digest = ctx.direction(name)
        if digest != prov["directions"][name]["sha256"]:
            raise HarnessError("DIRECTION_HASH", f"{name} bytes differ from the promoted provenance hash")
        src = root / prov["directions"][name]["source"]
        if src.exists() and sha256_file(src) != digest:
            raise HarnessError("DIRECTION_SOURCE", f"{name} differs from its committed source")
        report["directions"][name] = {"sha256": digest, **sensor.direction_layer_report(path)}
        vec = sensor.load_direction_vector(path, hidden_dim=int(ctx.cell.cell["model"]["hidden_dim"]))
        report["directions"][name]["norm"] = float(np.linalg.norm(vec))
    layer = build["layers"]["hs20"]
    s, w = ctx.cell.cell["sensor"], ctx.cell.cell["writer"]
    pairs = {"mu_d": (s["mu_d"], layer["mu_d"]), "sigma_d": (s["sigma_d"], layer["sigma_d"]),
             "tau": (s["tau"], layer["tau_frozen"]), "mu_c": (w["mu_c"], layer["mu_c"]),
             "sigma_c": (w["sigma_c"], layer["sigma_c"])}
    for k, (a, b) in pairs.items():
        report["constants"][k] = {"cell": a, "build_manifest": b, "abs_diff": abs(float(a) - float(b))}
        if abs(float(a) - float(b)) > 1e-12:
            raise HarnessError("CONSTANT_DRIFT", f"cell.yaml {k} differs from the promoted build manifest")
    if int(s["decoder_block"]) != int(s["hidden_state"]) - 1:
        raise HarnessError("INDEX_CONVENTION", "decoder block must be hidden_state - 1")
    if report["directions"]["c_hat"]["json_layer"] != int(s["decoder_block"]):
        raise HarnessError("INDEX_CONVENTION", "c_hat JSON layer is expected to be the decoder block index")
    report["law_layer_explicit"] = int(s["decoder_block"])
    report["controller_strength"] = ctx.cell.controller_strength
    report["clamp_setpoints"] = {"known": ctx.cell.clamp_setpoint("known"), "unknown": ctx.cell.clamp_setpoint("unknown")}
    return report


def materialize(ctx: Ctx, inputs_dir: Path) -> dict:
    manifest = inputs.materialize(ctx.project_root, ctx.layout, ctx.cell, inputs_dir)
    return ctx.done("materialize", {"manifest_sha256": sha256_file(ctx.layout.local("materialize/manifest.json", shared=True)),
                                    "counts": manifest["counts"]})


def smoke_prepare(real: Ctx, smoke: Ctx, names: list[str], limit: int) -> dict:
    """Truncated private copies of materialized rows for a smoke tree (balanced across roles)."""
    out = {}
    for name in names:
        rows = read_jsonl(real.layout.local(f"materialize/{name}.jsonl", shared=True))
        by_role: dict[str, list] = {}
        for r in rows:
            by_role.setdefault(r["role"], []).append(r)
        picked = []
        per = max(1, limit // max(1, len(by_role)))
        for role in sorted(by_role):
            picked.extend(by_role[role][:per])
        out[name] = write_jsonl(smoke.layout.local(f"materialize/{name}.jsonl"), picked[:max(limit, len(by_role))])
    return out


# ----------------------------------------------------------------------------------------
# configs, jobs, registry
# ----------------------------------------------------------------------------------------

def _registry_path(ctx: Ctx) -> Path:
    return ctx.layout.local("jobs/registry.json")


def load_registry(ctx: Ctx) -> dict[str, J.Job]:
    p = _registry_path(ctx)
    return {k: J.Job(**v) for k, v in read_json(p).items()} if p.exists() else {}


def _register(ctx: Ctx, new: list[J.Job]) -> None:
    reg = {k: asdict(v) for k, v in load_registry(ctx).items()}
    for job in new:
        reg[job.job_id] = asdict(job)
    write_json(_registry_path(ctx), reg)


def emit_static(ctx: Ctx) -> dict:
    cell, layout = ctx.cell, ctx.layout
    e1 = J.extract_config(cell, layout, rows_rel="materialize/fit_l.jsonl", out_rel="capture/fit_l", with_sites=True)
    e2 = J.extract_config(cell, layout, rows_rel="materialize/heldout.jsonl", out_rel="capture/heldout", with_sites=False)
    from .util import write_yaml

    write_yaml(layout.local("configs/extract_fit_l.yaml"), e1)
    write_yaml(layout.local("configs/extract_heldout.yaml"), e2)
    static = J.static_jobs(cell, layout)
    _register(ctx, static)
    return ctx.done("emit_static", {"jobs": [j.job_id for j in static]})


# ----------------------------------------------------------------------------------------
# GPU: extraction
# ----------------------------------------------------------------------------------------

def require_run_admission(ctx: Ctx) -> None:
    from . import integrity
    integrity.verify(ctx.cell, ctx.layout)
    manifest = yaml.safe_load((ctx.cell.directory / "experiment.yaml").read_text())
    evidence = _evidence(ctx)
    needed = ("zero_patch_token_parity", "batch_1_4_token_parity", "kill_resume_drill")
    if manifest.get("status") not in {"signed", "running"} or not all(evidence.get(name, {}).get("passed") for name in needed):
        raise HarnessError("RUN_ADMISSION", "sign and pass the measured preflight before scored extraction/candidates")


def extract(ctx: Ctx, which: str) -> dict:
    if which == "heldout" and require_selected(ctx, "extract_heldout") is None:
        return {"skipped": True}
    if ctx.layout.tag is None:
        require_run_admission(ctx)
    cfg_name = {"fit_l": "extract_fit_l", "heldout": "extract_heldout"}[which]
    rows_rel = f"materialize/{which}.jsonl"
    out_dir = ctx.layout.local(f"capture/{which}")
    rows = read_jsonl(ctx.layout.local(rows_rel, shared=True))
    complete = False
    if (out_dir / "manifest.json").exists():
        try:
            capture.check_rows_covered(capture.load_manifest(out_dir), [r["row_key"] for r in rows])
            complete = True
        except HarnessError:
            complete = False
    if not complete:
        args = ["extract", "--mi-config", ctx.layout.ref(f"configs/{cfg_name}.yaml"), "--model", J.model_path(ctx.layout),
                "--model-revision", ctx.cell.revision]
        rc = ctx.engine.run_gpu(f"extract_{which}", args, gpu_ack=ctx.gpu_ack, planned_rows=0)
        if rc != 0:
            raise HarnessError("ENGINE_EXIT", f"extract {which} exited {rc}")
    manifest = capture.load_manifest(out_dir)
    capture.check_rows_covered(manifest, [r["row_key"] for r in rows])
    payload = {"which": which, "n_rows": len(rows), "capture_manifest_sha256": sha256_file(out_dir / "manifest.json")}
    if which == "heldout":
        _write_sensor_rows(ctx, rows, out_dir, payload)
    return ctx.done(f"extract_{which}", payload)


def _write_sensor_rows(ctx: Ctx, rows: list[dict], capture_dir: Path, payload: dict) -> None:
    _, u_d = ctx.c_hat_u_d()
    fires = {d["row_key"]: d for d in sensor.fire_decisions(ctx.cell, capture_dir, rows, u_d)}
    enriched = [{**r, "fire": fires[r["row_key"]]["fire"], "score_neg_z_d": fires[r["row_key"]]["score_neg_z_d"],
                 "proj_d": fires[r["row_key"]]["proj_d"]} for r in rows]
    shas = {"all": write_jsonl(ctx.layout.local("materialize/heldout_sensor.jsonl", shared=True), enriched),
            "confab": write_jsonl(ctx.layout.local("materialize/heldout_sensor_confab.jsonl", shared=True),
                                  [r for r in enriched if r["role"] == "confab"]),
            "known": write_jsonl(ctx.layout.local("materialize/heldout_sensor_known.jsonl", shared=True),
                                 [r for r in enriched if r["role"] == "known_correct"])}
    payload["sensor_rows_sha256"] = shas
    payload["fires"] = {role: sum(1 for r in enriched if r["role"] == role and r["fire"])
                        for role in ("confab", "known_correct")}


# ----------------------------------------------------------------------------------------
# CPU engine: weights-inspect, localization, proposals
# ----------------------------------------------------------------------------------------

def _inspect(ctx: Ctx, name: str, request: dict) -> dict:
    cfg = ctx.layout.local(f"inspect/{name}.request.yaml", shared=True)
    from .util import write_yaml

    write_yaml(cfg, request)
    rc, doc = ctx.engine.run_json(["weights-inspect", "--weights-config", ctx.layout.ref(f"inspect/{name}.request.yaml", shared=True),
                                   "--json"], ctx.layout.local(f"inspect/{name}.out.json", shared=True))
    if rc != 0 or doc is None:
        detail = weights.unwrap(doc) if doc and doc.get("success") else (doc or {}).get("error", {})
        raise HarnessError("INSPECT_FAILED", f"weights-inspect {name} exited {rc}: {detail}")
    return weights.unwrap(doc)


def inspect_stage(ctx: Ctx) -> dict:
    listing = _inspect(ctx, "list", weights.list_request(ctx.cell, ctx.layout))
    targets = weights.resolve_targets(ctx.cell, listing)
    binding = weights.listing_binding(listing)
    shard_names = set(binding["files_sha256"])
    if not shard_names:
        raise HarnessError("BINDING", "no weight shards listed")
    _, c_sha = ctx.direction("c_hat")
    dots_sha = {}
    for block, target in targets.items():
        report = _inspect(ctx, f"dots_b{block}", weights.dots_request(ctx.cell, ctx.layout, target, block,
                                                                     J.direction_ref(ctx.cell, "c_hat"), c_sha))
        dots = weights.read_dots(report, block, target)
        np.save(ctx.layout.local(f"inspect/dots_b{block}.npy", shared=True), dots)
        dots_sha[block] = sha256_file(ctx.layout.local(f"inspect/dots_b{block}.npy", shared=True))
    write_json(ctx.layout.local("inspect/targets.json", shared=True),
               {"targets": {str(b): t for b, t in targets.items()}, "binding": binding,
                "revision_evidence": listing.get("revision_evidence")})
    return ctx.done("inspect", {"targets": {str(b): t["sha256"] for b, t in targets.items()}, "dots_sha256": dots_sha,
                                "index_sha256": binding["index_sha256"]})


def localize_stage(ctx: Ctx) -> dict:
    cell, layout = ctx.cell, ctx.layout
    blocks = sorted(int(b) for b in cell.cell["candidates"]["blocks"])
    rows = read_jsonl(layout.local("materialize/fit_l.jsonl", shared=True))
    work = layout.local("localization")
    red = localize.reduce_rows(cell, layout.local("capture/fit_l"), rows, work, blocks=blocks)
    rankings, diag = {}, {}
    cand = cell.cell["candidates"]
    for b in blocks:
        dots = np.load(layout.local(f"inspect/dots_b{b}.npy", shared=True))
        m_conf, m_known = red["means"][("confab", b)], red["means"][("known_correct", b)]
        rankings[b] = localize.rank_columns(m_conf, m_known, dots, int(cand["columns"]))
        m_unk = red["means"][("unknown_refused", b)]
        top = rankings[b]["columns"]
        diag[b] = {"unknown_refused_mean_on_selected": [float(m_unk[j]) for j in top],
                   "confab_mean_on_selected": [float(m_conf[j]) for j in top],
                   "known_mean_on_selected": [float(m_known[j]) for j in top],
                   "note": "diagnostic only; never changes the ranking"}
    write_json(layout.local("localization/ranking.json"),
               {"rankings": {str(b): v for b, v in rankings.items()}, "counts": red["counts"], "diagnostics": {str(b): v for b, v in diag.items()}})
    return ctx.done("localize", {"eligible_blocks": [b for b in blocks if rankings[b]["eligible"]],
                                 "n_positive": {str(b): rankings[b]["n_positive"] for b in blocks},
                                 "recomputed_rows_this_pass": red["recomputed_this_pass"]})


def validate_spec(ctx: Ctx, spec_path: Path, tag: str | None = None) -> weights.Validation:
    """``weights-patch --validate`` through the engine; the output file is named for the spec's directory."""
    tag = tag or spec_path.parent.name
    out = ctx.layout.local(f"validation/{tag}.out.json", shared=True)
    ref = ctx.layout.ref(str(spec_path.relative_to(ctx.layout.artifacts_root / ctx.layout.slug)), shared=True)
    rc, doc = ctx.engine.run_json(["weights-patch", "--weights-config", ref, "--validate", "--json"], out)
    if doc is None:
        write_json(ctx.layout.local("results/instrument_failure.json"), {"stage": "validate", "code": "VALIDATE_NO_OUTPUT", "tag": tag})
        raise HarnessError("VALIDATE_NO_OUTPUT", f"weights-patch --validate produced no JSON for {tag} (exit {rc})")
    try:
        return weights.parse_validation(ctx.cell, doc)
    except HarnessError as exc:
        write_json(ctx.layout.local("results/instrument_failure.json"),
                   {"stage": "validate", "code": exc.code, "tag": tag})
        raise


def propose_stage(ctx: Ctx) -> dict:
    cell, layout = ctx.cell, ctx.layout
    c_hat, _ = ctx.c_hat_u_d()
    meta = read_json(layout.local("inspect/targets.json", shared=True))
    targets = {int(b): t for b, t in meta["targets"].items()}
    dots = {b: np.load(layout.local(f"inspect/dots_b{b}.npy", shared=True)) for b in targets}
    rankings = {int(b): v for b, v in read_json(layout.local("localization/ranking.json"))["rankings"].items()}
    proposals = weights.build_proposal_files(cell, layout, c_hat=c_hat, targets=targets, binding=meta["binding"],
                                             dots=dots, rankings=rankings)
    registry = []
    for p in proposals:
        v = validate_spec(ctx, p.spec_path)
        registry.append({"cand_id": p.cand_id, "block": p.block, "scale": p.scale, "tensor": p.tensor,
                         "columns": p.columns, "spec_sha256": p.spec_sha256, "payload_sha256": p.payload_sha256,
                         "valid": v.valid, "validation": v.to_dict() | {"receipt": None},
                         "spec_rel": f"patches/{p.cand_id}/spec.yaml"})
    write_json(layout.local("patches/candidates.json", shared=True),
               {"n_proposals": len(registry), "max_candidates": cell.cell["candidates"]["max_candidates"],
                "invalid_candidates_are_logged_not_replaced": True, "candidates": registry})
    return ctx.done("propose", {"n_proposals": len(registry), "n_valid": sum(1 for r in registry if r["valid"])})


# ----------------------------------------------------------------------------------------
# GPU: generation jobs
# ----------------------------------------------------------------------------------------

def expected_rows(ctx: Ctx, job: J.Job) -> list[dict]:
    return read_jsonl(ctx.layout.local(job.rows_rel, shared=True))


def _digest_from_validation(ctx: Ctx, job: J.Job) -> str | None:
    if not job.patch_rel:
        return None
    name = Path(job.patch_rel).parent.name
    path = ctx.layout.local(f"validation/{name}.out.json", shared=True)
    if not path.exists():
        return None
    v = weights.parse_validation(ctx.cell, read_json(path))
    return v.patch_digest


def run_job(ctx: Ctx, job: J.Job) -> dict:
    layout = ctx.layout
    cfg = layout.local(job.config_rel)
    if not cfg.exists():
        raise HarnessError("JOB_CONFIG", f"{job.job_id}: config missing")
    rows = expected_rows(ctx, job)
    if len(rows) != job.n_rows:
        raise HarnessError("JOB_ROWS", f"{job.job_id}: rows file changed since registration")
    if job.patch_rel and sha256_file(layout.local(job.patch_rel, shared=True)) != job.patch_sha256:
        raise HarnessError("JOB_PATCH", f"{job.job_id}: patch spec bytes changed since registration")
    out = layout.local(job.output_rel)
    ctx.ledger.record_outputs(job.output_rel, out)        # refresh: the file, not an older ledger line, is the truth
    pending = planned_new_rows(out, job.planned_rows)
    if pending:
        rc = ctx.engine.run_gpu(job.job_id, J.engine_args(job, layout, J.model_path(layout), ctx.cell.revision),
                                gpu_ack=ctx.gpu_ack, planned_rows=pending)
        ctx.ledger.record_outputs(job.output_rel, out)
        if rc != 0:
            raise HarnessError("ENGINE_EXIT", f"{job.job_id} exited {rc}")
    else:
        ctx.ledger.record_outputs(job.output_rel, out)
    digest = _digest_from_validation(ctx, job)
    records = grading.load_job_records(job, out, rows, patch_digest=digest)
    graded = grading.grade_records(records, job.job_id)
    grades_sha = grading.write_grades(layout.local(f"grades/{job.job_id}.jsonl"), graded)
    return {"job": job.job_id, "n": len(records), "grades_sha256": grades_sha}


def generate(ctx: Ctx, job_ids: list[str]) -> dict:
    reg = load_registry(ctx)
    results = []
    for jid in job_ids:
        if jid not in reg:
            raise HarnessError("JOB_UNKNOWN", f"unregistered job {jid}")
        results.append(run_job(ctx, reg[jid]))
    return results


def check_decoys(ctx: Ctx) -> dict:
    # Decoys are held back from scored FIT selection/localization. This is
    # constructibility qualification, not a FIT baseline aggregate.
    generate(ctx, ["decoy_baseline"])
    job = load_registry(ctx)["decoy_baseline"]
    records = grading.load_job_records(job, ctx.layout.local(job.output_rel), expected_rows(ctx, job))
    try:
        pools = adjudication.decoy_pools(ctx.cell, records, read_jsonl(ctx.layout.local("grades/decoy_baseline.jsonl")))
    except HarnessError as exc:
        write_json(ctx.layout.local("results/instrument_failure.json"), {"stage": "decoys", "code": exc.code})
        raise
    return ctx.done("check_decoys", {"positive": len(pools["pos"]), "negative": len(pools["neg"])})


def gen_static(ctx: Ctx) -> dict:
    if ctx.layout.tag is None:
        require_run_admission(ctx)
    res = generate(ctx, ["decoy_baseline", "screen_baseline"])
    reg = load_registry(ctx)
    decoy_records = grading.load_job_records(reg["decoy_baseline"], ctx.layout.local(reg["decoy_baseline"].output_rel),
                                             expected_rows(ctx, reg["decoy_baseline"]))
    graded = read_jsonl(ctx.layout.local("grades/decoy_baseline.jsonl"))
    try:
        pools = adjudication.decoy_pools(ctx.cell, decoy_records, graded)
    except HarnessError as exc:
        write_json(ctx.layout.local("results/instrument_failure.json"), {"stage": "decoys", "code": exc.code})
        raise
    base = selection.screen_counts(read_jsonl(ctx.layout.local("grades/screen_baseline.jsonl")))
    gate = selection.baseline_gate(ctx.cell, base)
    write_json(ctx.layout.local("selection/baseline_gate.json"), {"screen_baseline": base, "gate": gate})
    if not gate["passed"]:
        write_json(ctx.layout.local("results/instrument_failure.json"), {"stage": "fit_baseline", "gate": gate})
        raise HarnessError("BASELINE_GATE", f"unpatched known-correct rate {gate['known_correct_rate']:.3f} is below "
                           f"{gate['floor']}: instrument failure, not evidence about the edit")
    return ctx.done("gen_static", {"jobs": res, "decoys": {"positive": len(pools["pos"]), "negative": len(pools["neg"])},
                                   "baseline_gate": gate})


def candidates_registry(ctx: Ctx) -> dict:
    return read_json(ctx.layout.local("patches/candidates.json", shared=True))


def gen_screen_candidates(ctx: Ctx) -> dict:
    require_run_admission(ctx)
    reg = candidates_registry(ctx)
    valid = [c for c in reg["candidates"] if c["valid"]]
    new = [J.screen_candidate_job(ctx.cell, ctx.layout, c["cand_id"]) for c in valid]
    _register(ctx, new)
    res = generate(ctx, [j.job_id for j in new])
    return ctx.done("gen_screen_candidates", {"jobs": res, "n_valid": len(valid)})


def select_stage(ctx: Ctx) -> dict:
    reg = candidates_registry(ctx)
    base = read_json(ctx.layout.local("selection/baseline_gate.json"))["screen_baseline"]
    evaluations, logged_invalid = [], []
    for c in reg["candidates"]:
        if not c["valid"]:
            logged_invalid.append({"cand_id": c["cand_id"], "code": c["validation"].get("code")})
            continue
        graded_path = ctx.layout.local(f"grades/screen_{c['cand_id']}.jsonl")
        if not graded_path.exists():
            raise HarnessError("SELECTION_INCOMPLETE", f"screen evidence missing for {c['cand_id']}")
        counts = selection.screen_counts(read_jsonl(graded_path))
        evaluations.append(selection.evaluate(ctx.cell, base, counts, {
            "delta_frobenius": c["validation"]["delta_frobenius"], "block": c["block"], "scale": c["scale"],
            "cand_id": c["cand_id"]}) | {"screen_counts": counts})
    verdict = selection.choose(evaluations, expected=sum(1 for c in reg["candidates"] if c["valid"]))
    doc = {"schema_version": "hs20-nwe-selection/v1", **ctx.cell.stamp(), **verdict, "evaluations": evaluations,
           "invalid_logged": logged_invalid, "n_proposals": reg["n_proposals"],
           "statement": "exploratory detector-v2 screen; not an accepted-abstention result"}
    write_json(ctx.layout.local("selection/selection.json"), doc)
    return ctx.done("select", {"status": verdict["status"], "winner": verdict["winner"]})


def selection_doc(ctx: Ctx) -> dict:
    p = ctx.layout.local("selection/selection.json")
    if not p.exists():
        raise HarnessError("SELECTION_MISSING", "run the select stage first")
    return read_json(p)


def require_selected(ctx: Ctx, stage: str) -> dict | None:
    """Held-out stages run only after a selection; no eligible candidate -> recorded skip."""
    doc = selection_doc(ctx)
    if doc["status"] == "no_eligible":
        ctx.done(stage, {"skipped": "no eligible FIT candidate (bounded-search null path)"})
        return None
    return doc


def controls_stage(ctx: Ctx) -> dict:
    doc = require_selected(ctx, "controls")
    if doc is None:
        return {"skipped": True}
    cell, layout = ctx.cell, ctx.layout
    cand = next(c for c in candidates_registry(ctx)["candidates"] if c["cand_id"] == doc["winner"])
    meta = read_json(layout.local("inspect/targets.json", shared=True))
    block = cand["block"]
    tensor, binding = meta["targets"][str(block)], meta["binding"]
    c_hat, u_d = ctx.c_hat_u_d()
    dots = np.load(layout.local(f"inspect/dots_b{block}.npy", shared=True))
    native = weights.Proposal(cand["cand_id"], block, cand["scale"], cand["tensor"], cand["columns"])
    target = cand["validation"]["delta_frobenius"]
    results = []
    for seed in cell.cell["controls"]["random_seeds"]:
        results.append(weights.build_control(
            cell, layout, seed=int(seed), native=native, native_delta=target, c_hat=c_hat, u_d=u_d,
            v=dots[cand["columns"]], tensor=tensor, binding=binding,
            validate=lambda spec_path: validate_spec(ctx, spec_path)))
    ok = len(results) == len(cell.cell["controls"]["random_seeds"]) and all(r["status"] == "matched" for r in results)
    write_json(layout.local("controls/controls.json"), {"K": len(results), "all_matched": ok, "controls": results,
                                                          "native_candidate": cand["cand_id"], "native_delta": target})
    if not ok:
        write_json(layout.local("results/instrument_failure.json"), {"stage": "controls", "code": "CONTROL_CONSTRUCTION"})
        raise HarnessError("CONTROL_CONSTRUCTION", "a norm-matched control failed; recorded, K is not reduced")
    return ctx.done("controls", {"all_matched": ok})


def export_stage(ctx: Ctx) -> dict:
    doc = require_selected(ctx, "export_selected")
    if doc is None:
        return {"skipped": True}
    cand = next(c for c in candidates_registry(ctx)["candidates"] if c["cand_id"] == doc["winner"])
    spec = yaml.safe_load(ctx.layout.local(cand["spec_rel"], shared=True).read_text())
    spec["export"] = {"output_dir": ctx.cell.cell["paths"]["export"]}
    from .util import write_yaml

    write_yaml(ctx.layout.local("patches/selected_export.yaml", shared=True), spec)
    rc, out = ctx.engine.run_json(["weights-patch", "--weights-config", ctx.layout.ref("patches/selected_export.yaml", shared=True),
                                   "--export", "--json"], ctx.layout.local("validation/export.out.json", shared=True))
    if rc != 0 or out is None:
        raise HarnessError("EXPORT_FAILED", f"weights-patch --export exited {rc}")
    data = weights.unwrap(out)
    tensors = [{"name": t["name"], "before_sha256": t["before_sha256"], "after_sha256": t["after_sha256"]}
               for t in data["manifest"]["tensors"]]
    write_json(ctx.layout.local("results/evidence/export_manifest_digest.json", shared=True),
               {"patch_digest": data["patch_digest"], "totals": data["totals"], "tensors": tensors,
                "output_files": data["manifest"]["output"]["weight_files"]})
    return ctx.done("export_selected", {"patch_digest": data["patch_digest"], "totals": data["totals"]})


def gen_heldout(ctx: Ctx) -> dict:
    doc = require_selected(ctx, "gen_heldout")
    if doc is None:
        return {"skipped": True}
    require_export_parity(ctx)
    require_run_admission(ctx)
    cand = next(c for c in candidates_registry(ctx)["candidates"] if c["cand_id"] == doc["winner"])
    controls = read_json(ctx.layout.local("controls/controls.json"))
    if not controls["all_matched"]:
        raise HarnessError("CONTROL_CONSTRUCTION", "controls are not all matched")
    ctl_rel = {int(c["seed"]): f"controls/seed{c['seed']}/spec.yaml" for c in controls["controls"]}
    new = J.heldout_jobs(ctx.cell, ctx.layout, selected_spec_rel=cand["spec_rel"], control_spec_rels=ctl_rel)
    new += J.clamp_jobs(ctx.cell, ctx.layout, selected_spec_rel=cand["spec_rel"])
    _register(ctx, new)
    res = generate(ctx, ["heldout_untouched"])
    counts = selection.screen_counts(read_jsonl(ctx.layout.local("grades/heldout_untouched.jsonl")))
    baseline_gate = selection.baseline_gate(ctx.cell, counts)
    write_json(ctx.layout.local("selection/heldout_baseline_gate.json"), {"gate": baseline_gate})
    if not baseline_gate["passed"]:
        write_json(ctx.layout.local("results/instrument_failure.json"),
                   {"stage": "heldout_baseline", "reason": "known_correct_rate_below_floor", **baseline_gate})
        raise HarnessError("BASELINE_GATE", "held-out untouched known-correct rate is below the registered floor")
    res += generate(ctx, [j.job_id for j in new if j.job_id != "heldout_untouched"])
    return ctx.done("gen_heldout", {"jobs": res})


def require_export_parity(ctx: Ctx) -> None:
    path = ctx.layout.local("results/evidence/readback_and_export_roundtrip.json", shared=True)
    if not path.is_file():
        raise HarnessError("EXPORT_PARITY", "selected export/token parity must pass before held-out generation")
    proof = read_json(path)
    from .integrity import binding_digest
    selected = selection_doc(ctx)
    candidate = next(c for c in candidates_registry(ctx)["candidates"] if c["cand_id"] == selected["winner"])
    if (proof.get("passed") is not True or proof.get("basis") != "generated_token_ids"
            or proof.get("tensor_bytes_equal") is not True
            or proof.get("selected_spec_sha256") != candidate["spec_sha256"]
            or proof.get("run_binding_sha256") != binding_digest(ctx.layout)
            or any(proof.get(k) != value for k, value in ctx.cell.stamp().items())):
        raise HarnessError("EXPORT_PARITY", "selected export proof is failed, stale or from another patch")


def verify_selected(ctx: Ctx) -> dict:
    if require_selected(ctx, "verify_selected") is None:
        return {"skipped": True}
    parity_prepare(ctx, int(ctx.cell.cell["generation"]["preflight_rows"]), include_selected=True)
    generate(ctx, [name for name in load_registry(ctx) if name.startswith("parity_")])
    result = parity_compare(ctx)
    require_export_parity(ctx)
    return ctx.done("verify_selected", result)


def pool_stage(ctx: Ctx) -> dict:
    require = require_selected(ctx, "build_pool")
    if require is None:
        return {"skipped": True}
    reg = load_registry(ctx)
    scored = sorted(j for j, job in reg.items() if j.startswith(("heldout_", "clamp_")))
    records = {j: grading.load_job_records(reg[j], ctx.layout.local(reg[j].output_rel), expected_rows(ctx, reg[j]),
                                           patch_digest=_digest_from_validation(ctx, reg[j])) for j in scored}
    graded = {j: read_jsonl(ctx.layout.local(f"grades/{j}.jsonl")) for j in scored}
    cores = adjudication.core_items(records, graded)
    decoy_job = reg["decoy_baseline"]
    decoy_rec = grading.load_job_records(decoy_job, ctx.layout.local(decoy_job.output_rel), expected_rows(ctx, decoy_job))
    pools = adjudication.decoy_pools(ctx.cell, decoy_rec, read_jsonl(ctx.layout.local("grades/decoy_baseline.jsonl")))
    manifest = adjudication.build_pool(ctx.cell, ctx.layout, cores, pools)
    return ctx.done("build_pool", {"n_shards": len(manifest["shards"]), "n_candidates": manifest["n_candidates"]})


# ----------------------------------------------------------------------------------------
# roll-up (CPU)
# ----------------------------------------------------------------------------------------

def _evidence(ctx: Ctx) -> dict:
    out = {}
    for name in ("zero_patch_token_parity", "batch_1_4_token_parity", "readback_and_export_roundtrip", "kill_resume_drill"):
        p = ctx.layout.local(f"results/evidence/{name}.json", shared=True)
        out[name] = read_json(p) if p.exists() else None
    from .integrity import verify_drill
    drill = out.get("kill_resume_drill")
    out["kill_resume_drill"] = {"passed": verify_drill(ctx.cell, ctx.layout, drill)}
    from .integrity import binding_digest
    for name, proof in out.items():
        if name != "kill_resume_drill" and proof:
            if proof.get("run_binding_sha256") != binding_digest(ctx.layout) or any(proof.get(k) != v for k, v in ctx.cell.stamp().items()) or proof.get("n") != ctx.cell.cell["generation"]["preflight_rows"]:
                out[name] = {"passed": False}
    return out


def rollup(ctx: Ctx) -> dict:
    from . import rollup as R

    cell, layout = ctx.cell, ctx.layout
    from . import integrity
    binding = integrity.report(cell, layout)
    mat_ok = binding["passed"]
    ledger = ctx.ledger
    stop = ledger.stopped()
    gate_p = layout.local("selection/baseline_gate.json")
    baseline = read_json(gate_p)["gate"] if gate_p.exists() else None
    result: dict = {"schema_version": "hs20-nwe-rollup/v1", **cell.stamp(), "budget": ledger.summary(), "binding": binding}
    failure = layout.local("results/instrument_failure.json")
    if not mat_ok:
        result["interpretation"] = {"verdict": "instrument_invalid", "statement": "source/runtime/data binding failed"}
        write_json(layout.local("results/rollup.json", shared=True), result)
        return result
    if failure.exists():
        result["instrument_failure"] = read_json(failure)
        result["interpretation"] = {"verdict": "instrument_invalid", "statement": "an instrument check failed"}
        write_json(layout.local("results/rollup.json", shared=True), result)
        return result
    sel_p = layout.local("selection/selection.json")
    if stop is not None or not sel_p.exists():
        g0 = R.g0(cell, materialize_ok=mat_ok, baseline_gate=baseline, evidence=_evidence(ctx), controls_ok=None,
                  adjudication_ok=None, budget_stop=stop, denominators_ok=None)
        result.update({"G0": g0, "interpretation": {"verdict": "incomplete" if stop is None else "instrument_invalid",
                                                    "statement": "no selection yet" if stop is None else f"budget stop: {stop['reason']}"}})
        write_json(layout.local("results/rollup.json", shared=True), result)
        return result
    sel = read_json(sel_p)
    if sel["status"] == "no_eligible":
        reg = candidates_registry(ctx)
        complete = all(layout.local(f"grades/screen_{c['cand_id']}.jsonl").exists() for c in reg["candidates"] if c["valid"]) \
            and baseline is not None and reg["n_proposals"] <= cell.cell["candidates"]["max_candidates"]
        if not complete:
            result["interpretation"] = {"verdict": "incomplete", "statement": "FIT evidence is not complete"}
        else:
            # FIT-side integrity: held-out/export/controls/adjudication evidence is not required on this path.
            g0 = R.g0(cell, materialize_ok=mat_ok, baseline_gate=baseline, evidence=_evidence(ctx), controls_ok=None,
                      adjudication_ok=None, budget_stop=stop, denominators_ok=None,
                      required=("zero_patch_token_parity", "batch_1_4_token_parity", "kill_resume_drill"))
            result["G0_fit_side"] = g0
            result["interpretation"] = R.interpret(cell, g0_result=g0, gate_results=None, selection_status="no_eligible")
        write_json(layout.local("results/rollup.json", shared=True), result)
        return result
    # selected: full held-out evaluation
    from .adjudication import Pool, load_applied

    report_path = Pool(ctx.layout).report
    if not report_path.exists():
        result["interpretation"] = {"verdict": "incomplete", "statement": "blinded adjudication has not been applied"}
        write_json(layout.local("results/rollup.json", shared=True), result)
        return result
    if not read_json(report_path)["instrument_valid"]:
        g0 = R.g0(cell, materialize_ok=mat_ok, baseline_gate=baseline, evidence=_evidence(ctx), controls_ok=None,
                  adjudication_ok=False, budget_stop=stop, denominators_ok=None)
        result.update({"G0": g0, "interpretation": R.interpret(cell, g0_result=g0, gate_results=None, selection_status="selected")})
        write_json(layout.local("results/rollup.json", shared=True), result)
        return result
    reg = load_registry(ctx)
    applied = load_applied(ctx.layout)
    names = ["heldout_untouched", "heldout_native", "heldout_controller"] + \
        [f"heldout_random_{s}" for s in cell.cell["controls"]["random_seeds"]] + \
        ["clamp_known_untouched", "clamp_known_native", "clamp_unknown_untouched", "clamp_unknown_native"]
    tables = {n: R.arm_table(read_jsonl(layout.local(f"grades/{n}.jsonl")), applied, n) for n in names}
    mat = read_json(layout.local("materialize/manifest.json", shared=True))
    confab_keys = sorted(mat["ids"]["heldout"]["confab"])
    known_keys = sorted(mat["ids"]["heldout"]["known_correct"])
    R.check_denominators(tables, confab_keys, known_keys)
    baseline_known = R.pop_stats(tables["heldout_untouched"], "known_correct", known_keys)
    heldout_baseline_gate = selection.baseline_gate(cell, {"known_correct": {
        "n": len(known_keys), "correct": baseline_known["correct"]["successes"]}})
    baseline = {"passed": bool(baseline and baseline["passed"] and heldout_baseline_gate["passed"]),
                "heldout": heldout_baseline_gate, "fit_screen": baseline}
    controls = read_json(layout.local("controls/controls.json"))
    adj_report = read_json(ctx.layout.local("grading/adjudication_report.json", shared=True))
    g0 = R.g0(cell, materialize_ok=mat_ok, baseline_gate=baseline, evidence=_evidence(ctx),
              controls_ok=controls["all_matched"], adjudication_ok=adj_report["instrument_valid"], budget_stop=stop,
              denominators_ok=True)
    gates = {}
    if g0["passed"]:
        randoms = {s: tables[f"heldout_random_{s}"] for s in cell.cell["controls"]["random_seeds"]}
        gates = {"G1": R.g1(cell, tables["heldout_native"], tables["heldout_untouched"], confab_keys),
                 "G2": R.g2(cell, tables["heldout_native"], tables["heldout_untouched"], confab_keys, known_keys),
                 "G3": R.g3(cell, tables["heldout_native"], tables["heldout_untouched"], randoms, confab_keys),
                 "G4": R.g4(cell, tables, confab_keys, known_keys)}
    arms = {n: {"confab": R.pop_stats(t, "confab") if any(v["role"] == "confab" for v in t.values()) else None,
                "known": R.pop_stats(t, "known_correct") if any(v["role"] == "known_correct" for v in t.values()) else None}
            for n, t in tables.items()}
    result.update({"G0": g0, **gates, "arms": arms, "selected": sel["winner"],
                   "interpretation": R.interpret(cell, g0_result=g0, gate_results=gates or None, selection_status="selected")})
    write_json(layout.local("results/rollup.json", shared=True), result)
    return result


# ----------------------------------------------------------------------------------------
# preflight parity (GPU, tiny) -- counted against the same 7000-row / 12 h caps
# ----------------------------------------------------------------------------------------

def preflight_parity(ctx: Ctx) -> dict:
    parity_prepare(ctx, int(ctx.cell.cell["generation"]["preflight_rows"]))
    generate(ctx, ["parity_untouched_b4", "parity_untouched_b1", "parity_zero_b4"])
    result = parity_compare(ctx)
    if not all(result.get(key) is True for key in ("zero_patch", "batch")):
        write_json(ctx.layout.local("results/instrument_failure.json"),
                   {"stage": "preflight_parity", "reason": "exact_token_parity_failed"})
        raise HarnessError("PARITY_FAILED", "registered token parity failed; no retry-until-pass")
    return result


def parity_prepare(ctx: Ctx, n_rows: int, *, include_selected: bool = False) -> dict:
    """Register the preflight slice, a scale-0 no-op patch (engine must report noop) and parity jobs."""
    from . import parity
    if ctx.layout.tag is not None:
        raise HarnessError("PARITY_SCOPE", "smoke-tag outputs cannot certify the registered parity slice")
    if n_rows != int(ctx.cell.cell["generation"]["preflight_rows"]):
        raise HarnessError("PARITY_SLICE", "parity slice size must match the registered preflight_rows")

    cell, layout = ctx.cell, ctx.layout
    parity.make_slice(layout, n_rows)
    n = len(read_jsonl(layout.local("materialize/parity_slice.jsonl", shared=True)))
    meta = read_json(layout.local("inspect/targets.json", shared=True))
    block = sorted(int(b) for b in meta["targets"])[0]
    columns = list(range(int(cell.cell["candidates"]["columns"])))
    native = weights.Proposal("zero", block, 0.0, meta["targets"][str(block)]["name"], columns)
    spec_path = weights.zero_noop_spec(cell, layout, native=native, tensor=meta["targets"][str(block)], binding=meta["binding"])
    v = validate_spec(ctx, spec_path, "zero_patch")
    if not (v.receipt and v.receipt.get("noop") is True):
        raise HarnessError("ZERO_PATCH", "the scale-0 patch did not validate as a true no-op")
    sel_rel, exported = None, None
    if include_selected:
        doc = selection_doc(ctx)
        if doc["status"] == "selected":
            sel_rel = next(c for c in candidates_registry(ctx)["candidates"] if c["cand_id"] == doc["winner"])["spec_rel"]
            exported = str(layout.to_local(cell.cell["paths"]["export"]))
    jobs = parity.parity_jobs(cell, layout, n_rows=n, zero_spec_rel="parity/zero_patch/spec.yaml",
                              selected_spec_rel=sel_rel, exported_model_path=exported)
    _register(ctx, jobs)
    return ctx.done("parity_prepare", {"jobs": [j.job_id for j in jobs], "slice_rows": n,
                                       "zero_patch_noop": True})


def parity_compare(ctx: Ctx) -> dict:
    from . import parity

    from .integrity import evidence_stamp
    stamp = evidence_stamp(ctx.cell, ctx.layout)
    layout = ctx.layout
    reg = load_registry(ctx)

    def recs(name: str) -> list[dict]:
        job = reg[name]
        return grading.load_job_records(job, layout.local(job.output_rel), expected_rows(ctx, job),
                                        patch_digest=_digest_from_validation(ctx, job))

    ze = parity.zero_patch_evidence(recs("parity_untouched_b4"), recs("parity_zero_b4"), True)
    ba = parity.compare(recs("parity_untouched_b1"), recs("parity_untouched_b4"))
    parity.write_evidence(layout, "zero_patch_token_parity", {**ze, **stamp})
    parity.write_evidence(layout, "batch_1_4_token_parity", {**ba, **stamp})
    out = {"zero_patch": ze["passed"], "batch": ba["passed"]}
    if "parity_exported_b4" in reg and "parity_selected_b4" in reg:
        export_doc = read_json(layout.local("results/evidence/export_manifest_digest.json", shared=True)) \
            if layout.local("results/evidence/export_manifest_digest.json", shared=True).exists() else {}
        name = Path(reg["parity_selected_b4"].patch_rel).parent.name
        receipt = weights.parse_validation(ctx.cell, read_json(layout.local(f"validation/{name}.out.json", shared=True))).receipt
        ex = parity.export_evidence(recs("parity_selected_b4"), recs("parity_exported_b4"), receipt["tensors"],
                                    export_doc.get("tensors"))
        selected = selection_doc(ctx)
        candidate = next(c for c in candidates_registry(ctx)["candidates"] if c["cand_id"] == selected["winner"])
        parity.write_evidence(layout, "readback_and_export_roundtrip",
                              {**ex, **stamp, "selected_spec_sha256": candidate["spec_sha256"]})
        out["export"] = ex["passed"]
    return ctx.done("parity_compare", out)
