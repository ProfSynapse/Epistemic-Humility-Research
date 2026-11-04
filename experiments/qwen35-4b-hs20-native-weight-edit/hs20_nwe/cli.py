"""Command line entry: ``python -m hs20_nwe <command>``.

Nothing here launches a GPU run unless ``--gpu-ack`` is given, and nothing
reads or prints row text.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import adjudication, integrity, qualification, stages
from .pipeline import build as build_pipeline
from .util import HarnessError, read_jsonl, write_yaml

STAGES = {
    "bind-runtime": lambda c, a: integrity.bind(c.cell, c.layout),
    "check-binding": lambda c, a: integrity.verify(c.cell, c.layout, full_model=True),
    "emit-static": lambda c, a: stages.emit_static(c),
    "extract-fit-l": lambda c, a: stages.extract(c, "fit_l"),
    "extract-heldout": lambda c, a: stages.extract(c, "heldout"),
    "inspect": lambda c, a: stages.inspect_stage(c),
    "localize": lambda c, a: stages.localize_stage(c),
    "propose": lambda c, a: stages.propose_stage(c),
    "check-decoys": lambda c, a: stages.check_decoys(c),
    "gen-static": lambda c, a: stages.gen_static(c),
    "gen-screen-candidates": lambda c, a: stages.gen_screen_candidates(c),
    "select": lambda c, a: stages.select_stage(c),
    "controls": lambda c, a: stages.controls_stage(c),
    "export": lambda c, a: stages.export_stage(c),
    "gen-heldout": lambda c, a: stages.gen_heldout(c),
    "build-pool": lambda c, a: stages.pool_stage(c),
    "parity-prepare": lambda c, a: stages.parity_prepare(c, a.parity_rows, include_selected=a.include_selected),
    "parity-compare": lambda c, a: stages.parity_compare(c),
    "preflight-parity": lambda c, a: stages.preflight_parity(c),
    "verify-selected": lambda c, a: stages.verify_selected(c),
}


def _say(obj) -> None:
    print(json.dumps(obj, indent=2, sort_keys=True, default=str))


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="hs20_nwe", description=__doc__)
    p.add_argument("--project-root", type=Path, default=None)
    p.add_argument("--smoke-tag", default=None, help="isolated output tree for short smokes")
    p.add_argument("--gpu-ack", action="store_true", help="authorize launching GPU engine verbs")
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("doctor")
    m = sub.add_parser("materialize")
    m.add_argument("--inputs-dir", default=None, help="default: artifact://<slug>/inputs")
    sp = sub.add_parser("stage")
    sp.add_argument("name", choices=sorted(STAGES))
    sp.add_argument("--parity-rows", type=int, default=8)
    sp.add_argument("--include-selected", action="store_true")
    sm = sub.add_parser("smoke-prepare", help="truncated private row copies for a --smoke-tag tree")
    sm.add_argument("--limit-rows", type=int, required=True)
    pp = sub.add_parser("plan-pipeline")
    pp.add_argument("--out", default=None, help="artifact path ref; default artifact://<slug>/pipeline/pipeline.yaml")
    pp.add_argument("--python", default="python")
    pp.add_argument("--native-static", action="store_true")
    drill = sub.add_parser("drill")
    drill.add_argument("module", choices=["extract", "generation", "localize"])
    worker = sub.add_parser("drill-worker")
    worker.add_argument("module", choices=["generation", "localize"])
    sub.add_parser("budget")
    sub.add_parser("rollup")

    pool = sub.add_parser("pool")
    ps = pool.add_subparsers(dest="pool_command", required=True)
    ps.add_parser("commit")
    ch = ps.add_parser("commit-hash")
    ch.add_argument("--shard-id", required=True)
    ch.add_argument("--graded-file", required=True)
    rg = ps.add_parser("regrade")
    rg.add_argument("--shard-id", required=True)
    rg.add_argument("--graded-file", required=True)
    sc = ps.add_parser("spot-pack")
    sc.add_argument("--grading-manifest", required=True)
    sr = ps.add_parser("spot-record")
    sr.add_argument("--decisions", required=True)
    sr.add_argument("--accepted", action="store_const", const=True, default=None,
                    help="Compatibility assertion only; acceptance is computed from registered agreement.")
    sr.add_argument("--note", default="")
    ap = ps.add_parser("apply")
    ap.add_argument("--grading-manifest", required=True, help='JSON {shard_id: graded_file_path} (operator authored)')

    args = p.parse_args(argv)
    ctx = stages.Ctx.create(args.project_root, tag=args.smoke_tag, gpu_ack=args.gpu_ack)
    try:
        if args.command == "doctor":
            _say(stages.doctor(ctx))
        elif args.command == "materialize":
            inputs_dir = Path(args.inputs_dir) if args.inputs_dir else ctx.layout.local("inputs", shared=True)
            _say(stages.materialize(ctx, inputs_dir))
        elif args.command == "stage":
            _say(STAGES[args.name](ctx, args))
        elif args.command == "smoke-prepare":
            if not args.smoke_tag:
                raise HarnessError("SMOKE", "smoke-prepare requires --smoke-tag")
            real = stages.Ctx.create(args.project_root)
            _say(stages.smoke_prepare(real, ctx, ["fit_l", "fit_screen", "decoy", "heldout"], args.limit_rows))
        elif args.command == "plan-pipeline":
            doc = build_pipeline(ctx.cell, ctx.layout, python=args.python, native_static=args.native_static)
            ref = args.out or ctx.layout.ref("pipeline/pipeline.yaml", shared=True)
            write_yaml(ctx.layout.to_local(ref), doc)
            _say({"pipeline": ref, "stages": [s["name"] for s in doc["stages"]]})
        elif args.command == "drill":
            _say(qualification.drill(ctx, args.module))
        elif args.command == "drill-worker":
            _say(qualification.localize_worker(ctx) if args.module == "localize" else qualification.generation_worker(ctx))
        elif args.command == "budget":
            _say(ctx.ledger.summary())
        elif args.command == "rollup":
            _say(stages.rollup(ctx))
        elif args.command == "pool":
            if args.pool_command == "commit":
                _say(adjudication.commit_pool(ctx.layout))
            elif args.pool_command == "commit-hash":
                _say(adjudication.commit_hash(ctx.layout, args.shard_id, Path(args.graded_file)))
            elif args.pool_command == "regrade":
                _say(adjudication.build_regrade(ctx.cell, ctx.layout, args.shard_id, Path(args.graded_file)))
            elif args.pool_command == "spot-pack":
                files = json.loads(Path(args.grading_manifest).read_text())
                rows = adjudication.spot_check_pack(ctx.cell, ctx.layout, {k: Path(v) for k, v in files.items()})
                _say({"n": len(rows), "path": str(adjudication.Pool(ctx.layout).root / "spot_pack.blind.jsonl")})
            elif args.pool_command == "spot-record":
                _say(adjudication.record_spot_check(ctx.cell, ctx.layout, read_jsonl(args.decisions),
                                                    accepted=args.accepted, note=args.note))
            elif args.pool_command == "apply":
                files = json.loads(Path(args.grading_manifest).read_text())
                _say(adjudication.apply(ctx.cell, ctx.layout, files))
    except HarnessError as exc:
        print(json.dumps({"error": exc.code, "message": exc.message}), file=sys.stderr)
        return 2
    return 0
