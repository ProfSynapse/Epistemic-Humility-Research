#!/usr/bin/env python3
"""Pre-sign kill-resume drill (lab-notebook tier) for dmcc_harness.py's
incremental stages, on the REAL harness code paths, in a throwaway sandbox.

  label           EH probe.py via dmcc_harness `label` (vLLM), 6 non-PopQA
                  smoke questions; SIGKILL the process group after the first
                  append-log row, rerun, require 6 unique rows, no duplicates,
                  and the pre-kill rows byte-identical.
  stage0-extract  `mechinterp extract` via dmcc_harness `stage0-extract` in the
                  runner image, 2 shards x 3 smoke rows; SIGKILL after shard 0's
                  marker, rerun, require shard 0 skipped (marker untouched),
                  shard 1 completed, both families captured for all 6 rows,
                  and no orphan container left.

The harness's module-level `cfg()` is replaced by a patched copy of cell.yaml
whose analysis root, probe config and extract recipe point at the sandbox; no
other harness code is changed. Questions are not from PopQA and nothing is
scored. Run from WSL with the vLLM venv python (needs yaml).
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
CELL = HERE.parent
REPO = CELL.parents[1]
sys.path.insert(0, str(CELL))
sys.path.insert(0, str(HERE))

import yaml  # noqa: E402

import dmcc_harness as H  # noqa: E402
from smoke_questions import QUESTIONS  # noqa: E402

SANDBOX = CELL / "analysis" / "presign" / "drill"


def rel(p: Path) -> str:
    return p.relative_to(REPO).as_posix()


def patched_cfg(snapshot: str, gpu_mem: float) -> dict:
    c = copy.deepcopy(H._yaml_load(CELL / "cell.yaml"))
    c["paths"]["analysis_root"] = rel(SANDBOX)
    # label: throwaway probe config (probe.yaml verbatim except pool/output/tag
    # and the check-only GPU cap), already "materialized" to the snapshot.
    pc = H._yaml_load(CELL / "probe.yaml")
    pc["model"]["model_tag"] = "drill"
    pc["probe_pool"]["train_jsonl"] = rel(SANDBOX / "popqa" / "probe_pool.jsonl")
    pc["output"]["root"] = rel(SANDBOX / "knowledge_probe")
    pc["runtime"]["vllm"]["gpu_memory_utilization"] = gpu_mem
    H._yaml_dump(pc, SANDBOX / "drill_probe.yaml")
    c["labeler"]["probe_config"] = rel(SANDBOX / "drill_probe.yaml")
    pm = copy.deepcopy(pc)
    pm["model"]["model_name"] = snapshot
    H._yaml_dump(pm, SANDBOX / "knowledge_probe" / "probe.materialized.yaml")
    # stage0: throwaway extract recipe -> sandbox output dir
    er = H._yaml_load(CELL / "stage0_extract.yaml")
    er["output_dir"] = rel(SANDBOX / "stage0" / "extraction")
    H._yaml_dump(er, SANDBOX / "drill_extract.yaml")
    c["stage0"]["extract_recipe"] = rel(SANDBOX / "drill_extract.yaml")
    return c


def write_inputs(c: dict) -> None:
    pool = [{"question": QUESTIONS[i], "question_id": f"smoke-{i}",
             "answer": {"normalized_aliases": ["zzzz"], "value": "zzzz"}} for i in range(6)]
    H.write_jsonl_atomic(SANDBOX / "popqa" / "probe_pool.jsonl", pool)
    st = SANDBOX / "stage0"
    rows = [{"row_key": f"smoke-{i}", "question": QUESTIONS[i], "label": i % 2, "split": "fit"} for i in range(6)]
    template = H._yaml_load(H.rp(c["stage0"]["extract_recipe"]))
    for k in range(2):
        rp_ = st / "shards" / f"rows_{k:03d}.jsonl"
        H.write_jsonl_atomic(rp_, rows[3 * k:3 * k + 3])
        sc = dict(template)
        sc["rows_path"] = rel(rp_)
        H._yaml_dump(sc, st / "shards" / f"extract_{k:03d}.yaml")
    H.write_json_atomic(st / "stage0_rows_manifest.json", {"counts": {}, "n_shards": 2, "s0_floors_met": False})


def child(stage: str, c: dict) -> int:
    H.cfg = lambda: c  # the only patch
    return H.main([stage, "--i-know-this-runs-on-gpu"])


def run_and_kill(stage: str, ready, log: Path, timeout: float = 3600) -> float:
    with open(log, "w", encoding="utf-8") as fh:
        p = subprocess.Popen([sys.executable, __file__, "--child", stage] + sys.argv[1:], cwd=str(REPO),
                             stdout=fh, stderr=subprocess.STDOUT, start_new_session=True)
        t0 = time.time()
        while time.time() - t0 < timeout:
            if ready():
                os.killpg(p.pid, signal.SIGKILL)
                p.wait()
                return time.time() - t0
            if p.poll() is not None:
                raise SystemExit(f"{stage}: child exited {p.returncode} before the kill point; see {log}")
            time.sleep(0.5)
    raise SystemExit(f"{stage}: kill point not reached in {timeout}s")


def run_to_end(stage: str, log: Path) -> tuple[int, float]:
    t0 = time.time()
    with open(log, "w", encoding="utf-8") as fh:
        rc = subprocess.run([sys.executable, __file__, "--child", stage] + sys.argv[1:], cwd=str(REPO),
                            stdout=fh, stderr=subprocess.STDOUT).returncode
    return rc, time.time() - t0


def lines(p: Path) -> list[str]:
    return [x for x in p.read_text(encoding="utf-8").splitlines() if x.strip()] if p.exists() else []


def drill_label(c: dict) -> dict:
    res_path = H.probe_results_path(c)
    killed_after = run_and_kill("label", lambda: len(lines(res_path)) >= 1, SANDBOX / "label_kill.log")
    before = lines(res_path)
    rc, wall = run_to_end("label", SANDBOX / "label_resume.log")
    after = lines(res_path)
    keys = [json.loads(x)["probe_pool_row_key"] for x in after]
    return {"stage": "label", "killed_after_s": round(killed_after, 1), "rows_before_kill": len(before),
            "resume_rc": rc, "resume_wall_s": round(wall, 1), "rows_after": len(after),
            "unique_keys": len(set(keys)), "prekill_rows_unchanged": after[:len(before)] == before,
            "pass": rc == 0 and len(after) == 6 and len(set(keys)) == 6 and after[:len(before)] == before}


def drill_extract(c: dict) -> dict:
    ext = H.rp(H._yaml_load(H.rp(c["stage0"]["extract_recipe"]))["output_dir"])
    m0 = ext / "manifest_shard_000.json"
    killed_after = run_and_kill("stage0-extract", m0.exists, SANDBOX / "extract_kill.log")
    time.sleep(2)
    m0_sha = H.sha256_file(m0)
    orphan = subprocess.run(list(c["stage0"]["runtime"]["docker_cli"]) + ["ps", "-q", "--filter",
                            f"name={H.shard_container(c, 1)}"], capture_output=True, text=True).stdout.strip()
    rc, wall = run_to_end("stage0-extract", SANDBOX / "extract_resume.log")
    resume_log = (SANDBOX / "extract_resume.log").read_text(encoding="utf-8", errors="replace")
    files = {f"smoke-{i}": sorted(p.name.split("__")[1].split(".")[0] for p in ext.glob(f"smoke-{i}__*.safetensors"))
             for i in range(6)}
    leftover = subprocess.run(list(c["stage0"]["runtime"]["docker_cli"]) + ["ps", "-aq", "--filter",
                              "name=dmcc-stage0-"], capture_output=True, text=True).stdout.strip()
    ok = (rc == 0 and "shard 000 done, skipping" in resume_log and H.sha256_file(m0) == m0_sha
          and (ext / "manifest_shard_001.json").exists()
          and all("anchor" in v for v in files.values()) and not leftover)
    return {"stage": "stage0-extract", "killed_after_s": round(killed_after, 1),
            "orphan_container_running_after_kill": bool(orphan), "resume_rc": rc, "resume_wall_s": round(wall, 1),
            "shard0_skipped": "shard 000 done, skipping" in resume_log, "shard0_marker_unchanged": H.sha256_file(m0) == m0_sha,
            "families_per_row": files, "leftover_containers": leftover, "pass": ok}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--child", default=None)
    ap.add_argument("--snapshot", required=True)
    ap.add_argument("--gpu-mem", type=float, default=0.30)
    ap.add_argument("--only", choices=["label", "stage0-extract"], default=None)
    args = ap.parse_args()
    c = patched_cfg(args.snapshot, args.gpu_mem)
    if args.child:
        return child(args.child, c)
    write_inputs(c)
    out = {"drill": "kill_resume", "sandbox": rel(SANDBOX), "results": []}
    if args.only in (None, "label"):
        out["results"].append(drill_label(c))
    if args.only in (None, "stage0-extract"):
        out["results"].append(drill_extract(c))
    H.write_json_atomic(SANDBOX / f"drill_{args.only or 'all'}.json", out)
    print(json.dumps(out, indent=1))
    return 0 if all(r["pass"] for r in out["results"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
