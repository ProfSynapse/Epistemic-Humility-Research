#!/usr/bin/env python3
"""Stage the pre-sign engine checks (lab-notebook tier) for one decision model.

Writes, under the tuner's gitignored scratch/eh_staging/dmio-presign-<model>/:
  final_model/                     the pinned checkpoint (tree digest verified)
  decision_rows_primary.jsonl      dmcc no-IDK rows (render reference only)
  p<k>/decision_rows_idk.jsonl     this cell's IDK rows at position k (render + --dry-run only)
  p<k>/analysis_idk_<model>.yaml   the stage-engine materialization of the pinned
                                   template for position k, with only the staging
                                   prefix moved to this sandbox
  synth/ex_p<k>.jsonl              one synthetic (non-PopQA) row per position (printed render)
  timing/decision_rows_idk.jsonl   throwaway synthetic arithmetic rows (not PopQA) for the timing pass
  timing/analysis_idk_<model>.yaml the position-0 materialization, rows -> timing set,
                                   checkpoint -> ../final_model; every other key as pinned
  check_engine_render.py           copy of presign/check_engine_render.py
  timed_analyze.py                 copy of presign/timed_analyze.py (phase timers around the engine CLI)
and a local-run recipe at analysis/presign/engine/dmio-presign-<model>.yaml: the
pinned template recipe (same image, pip set, copy set) with name, copy dir,
command and artifact path moved to the sandbox. No PopQA row is ever forwarded
through a model: PopQA rows are only tokenised (render) and split (--dry-run).
"""

from __future__ import annotations

import argparse
import json
import random
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CELL = HERE.parent
sys.path.insert(0, str(CELL))

import yaml  # noqa: E402

import idk_harness as H  # noqa: E402


def synth_rows(n: int, seed: int, positions: list[int], text: str) -> list[dict]:
    rng = random.Random(seed)
    ops = {"synth:add": lambda a, b: (f"What is {a} plus {b}?", a + b),
           "synth:sub": lambda a, b: (f"What is {a + b} minus {b}?", a),
           "synth:mul": lambda a, b: (f"What is {a % 12 + 2} times {b % 12 + 2}?", (a % 12 + 2) * (b % 12 + 2)),
           "synth:max": lambda a, b: (f"Which is larger, {a} or {b + 100}?", b + 100)}
    names = sorted(ops)
    rows = []
    for i in range(n):
        task = names[i % len(names)]
        a, b = rng.randint(11, 89), rng.randint(11, 89)
        q, gold = ops[task](a, b)
        opts = {gold}
        while len(opts) < 4:
            opts.add(gold + rng.choice([-20, -11, -10, -2, -1, 1, 2, 10, 11, 20]))
        opts = [str(x) for x in rng.sample(sorted(opts), 4)]
        row = {"kind": "choice", "state": q,
               "instructions": "Which option correctly answers the question in the state?",
               "options": [[o, ""] for o in opts], "label": opts.index(str(gold)), "task": task, "weight": 1.0,
               "instruction_variants": [],
               "meta": {"qid": f"synth-{i}", "knowledge": "known" if rng.random() < 0.11 else "unknown",
                        "source": "synthetic-presign"}}
        rows.append(H.insert_idk(row, positions[i % len(positions)], text, ""))
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, choices=["pointer", "letter_logits"])
    ap.add_argument("--n-timing-rows", type=int, default=2400)
    ap.add_argument("--seed", type=int, default=20261006)
    args = ap.parse_args()
    c = H.cfg()
    m = c["models"][args.model]
    t = c["idk_runs"][args.model]
    positions = [int(k) for k in c["idk_option"]["positions"]]
    sb_rel = f"{c['engine']['staging_root']}/dmio-presign-{args.model.replace('_', '-')}"
    sb = H.TUNER_DIR / sb_rel
    if sb.exists() and any(sb.iterdir()):
        raise SystemExit(f"{sb} not empty; move it aside")
    sb.mkdir(parents=True)
    src = H.host_abs(m["source_checkpoint"])
    shutil.copytree(src, sb / "final_model")
    if H.tree_sha256(sb / "final_model") != m["tree_sha256"]:
        raise SystemExit("staged checkpoint digest mismatch")
    shutil.copy2(H.dmcc_file(c, "decision_rows_primary"), sb / "decision_rows_primary.jsonl")
    shutil.copy2(HERE / "check_engine_render.py", sb / "check_engine_render.py")
    shutil.copy2(HERE / "timed_analyze.py", sb / "timed_analyze.py")
    tmpl = H.rp(t["analysis_config"]).read_text(encoding="utf-8")
    manifest = {"model": args.model, "sandbox": sb_rel, "configs": {}, "rows": {}}
    for k in positions:
        run_id = t["run_id_template"].format(position=k)
        text = H.materialize(tmpl, t["template_run_id"], run_id)
        text = text.replace(f"{c['engine']['staging_root']}/{run_id}", f"{sb_rel}/p{k}")
        (sb / f"p{k}").mkdir()
        rows_src = H.idk_rows_path(c, k)
        shutil.copy2(rows_src, sb / f"p{k}" / c["staged_rows_name"]["idk"])
        p = sb / f"p{k}" / H.rp(t["analysis_config"]).name
        p.write_text(text, encoding="utf-8", newline="\n")
        manifest["configs"][f"p{k}"] = H.sha256_file(p)
        manifest["rows"][f"p{k}"] = H.sha256_file(rows_src)
        ex = synth_rows(1, args.seed + k, [k], c["idk_option"]["text"])
        H.write_jsonl_atomic(sb / "synth" / f"ex_p{k}.jsonl", ex)
    # timing set: synthetic rows only, IDK position cycling 0..4
    (sb / "timing").mkdir()
    trows = synth_rows(args.n_timing_rows, args.seed, positions, c["idk_option"]["text"])
    manifest["rows"]["timing"] = H.write_jsonl_atomic(sb / "timing" / c["staged_rows_name"]["idk"], trows)
    p0 = t["run_id_template"].format(position=0)
    text = H.materialize(tmpl, t["template_run_id"], p0)
    text = text.replace(f"{c['engine']['staging_root']}/{p0}/final_model", f"{sb_rel}/final_model")
    text = text.replace(f"{c['engine']['staging_root']}/{p0}", f"{sb_rel}/timing")
    tp = sb / "timing" / H.rp(t["analysis_config"]).name
    tp.write_text(text, encoding="utf-8", newline="\n")
    manifest["configs"]["timing"] = H.sha256_file(tp)
    # recipe: pinned template, sandbox paths
    rec = yaml.safe_load(H.rp(t["recipe"]).read_text(encoding="utf-8"))
    name = f"dmio-presign-{args.model.replace('_', '-')}"
    rec["name"] = name
    rec["description"] = f"EH dmio PRE-SIGN engine checks ({args.model}): IDK render + --dry-run + timing on synthetic rows"
    rec["setup"]["copy"] = [x for x in rec["setup"]["copy"] if not x.startswith(c["engine"]["staging_root"])] + [sb_rel]
    cfgname = H.rp(t["analysis_config"]).name
    idk_files = " ".join(f"$S/p{k}/{c['staged_rows_name']['idk']}" for k in positions)
    ex_files = " ".join(f"$S/synth/ex_p{k}.jsonl" for k in positions)
    script = f"""S={sb_rel}; O=$S/output; mkdir -p $O
echo "render_start $(date -u +%FT%TZ)" >> $O/timeline.txt
python $S/check_engine_render.py --checkpoint $S/final_model --noidk-rows $S/decision_rows_primary.jsonl \\
  --idk-rows {idk_files} --positions {' '.join(map(str, positions))} --example-rows {ex_files} \\
  --out $O/render_check.json > $O/render_check.log 2>&1; echo "render_rc $?" >> $O/timeline.txt
echo "dryrun_start $(date -u +%FT%TZ)" >> $O/timeline.txt
for k in {' '.join(map(str, positions))}; do echo "== p$k" >> $O/dry_run.log; python Trainers/decision/analyze_confidence.py --config $S/p$k/{cfgname} --dry-run >> $O/dry_run.log 2>&1; echo "dryrun_p$k rc $?" >> $O/timeline.txt; done
echo "analysis_start $(date -u +%FT%TZ)" >> $O/timeline.txt
python $S/timed_analyze.py --config $S/timing/{cfgname} --output-root $O/timing --run-timestamp timing > $O/timing.log 2>&1; echo "analysis_rc $?" >> $O/timeline.txt
echo "analysis_end $(date -u +%FT%TZ)" >> $O/timeline.txt
cat $O/timeline.txt; tail -5 $O/render_check.log; exit 0"""
    rec["run"]["command"] = ["bash", "-c", script]
    rec["artifacts"]["host_path"] = f"{sb_rel}/output"
    rp_ = CELL / "analysis" / "presign" / "engine" / f"{name}.yaml"
    rp_.parent.mkdir(parents=True, exist_ok=True)
    rp_.write_text(yaml.safe_dump(rec, sort_keys=False, width=200), encoding="utf-8", newline="\n")
    manifest["recipe"] = str(rp_)
    manifest["recipe_sha256"] = H.sha256_file(rp_)
    manifest["checkpoint_tree_sha256"] = m["tree_sha256"]
    H.write_json_atomic(CELL / "analysis" / "presign" / "engine" / f"{name}_manifest.json", manifest)
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
