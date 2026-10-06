#!/usr/bin/env python3
"""Pre-sign kill-resume drill + recognition timing (lab-notebook tier) for
idk_harness.py `recognize`, on the REAL harness code path, in a throwaway sandbox.

The harness's module-level `cfg()` is replaced by a copy of cell.yaml whose
analysis root, committed root and run-records dir point at a sandbox under the
gitignored analysis/presign/; no other harness code is changed. The items are
deterministic synthetic arithmetic multiple-choice questions (not PopQA),
rendered by the harness's own `build_mc_prompt` + `rotations` (the registered
5-shot surface, 4 cyclic orderings). Nothing is scored for any gate.

Drill: launch `recognize` in a child process; once the append-log has
>= --kill-after lines, SIGKILL the child's process group (the docker client
dies; the container is left running as an orphan, as after a crashed
launcher); snapshot the log; rerun `recognize` to completion (its `docker rm -f`
of the fixed container name must remove the orphan before relaunch); require
rc 0, every key exactly once, full coverage, and the snapshot a byte-identical
prefix of the final log.

Run from WSL (python3 with yaml), like the real `recognize` stage:
  python3 experiments/decision-model-idk-option/presign/drill_recognize_resume.py \
      --n-questions 150 --kill-after 40
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import signal
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
CELL = HERE.parent
REPO = CELL.parents[1]
sys.path.insert(0, str(CELL))

import idk_harness as H  # noqa: E402

SANDBOX = CELL / "analysis" / "presign" / "drill_recognize"


def rel(p: Path) -> str:
    return p.relative_to(REPO).as_posix()


def patched_cfg() -> dict:
    c = copy.deepcopy(H._yaml_load(CELL / "cell.yaml"))
    c["paths"]["analysis_root"] = rel(SANDBOX / "analysis")
    c["paths"]["committed_root"] = rel(SANDBOX / "committed")
    c["paths"]["run_records"] = rel(SANDBOX / "committed" / "run_records")
    return c


def synthetic_items(c: dict, n: int, seed: int) -> list[dict]:
    """Arithmetic 4-way MC items (not PopQA), 4 cyclic orderings each."""
    rc = c["recognition"]
    rng = random.Random(seed)
    items = []
    for i in range(n):
        a, b = rng.randint(11, 89), rng.randint(11, 89)
        gold = a + b
        opts = {gold}
        while len(opts) < 4:
            opts.add(gold + rng.choice([-20, -11, -10, -2, -1, 1, 2, 10, 11, 20]))
        opts = [str(x) for x in rng.sample(sorted(opts), 4)]
        g = opts.index(str(gold))
        for k, (opts_k, gold_k) in enumerate(H.rotations(opts, g, int(rc["n_orderings"]))):
            items.append({"qid": f"drill-{i}", "ordering": k, "gold_letter_index": gold_k,
                          "prompt": H.build_mc_prompt(f"What is {a} plus {b}?", opts_k, rc)})
    return items


def lines(p: Path) -> list[str]:
    return p.read_text(encoding="utf-8").splitlines(keepends=True) if p.exists() else []


def child() -> int:
    H.cfg = patched_cfg
    try:
        H.stage_recognize(H.cfg(), None)
    except H.StageError as exc:
        print(f"recognize: REFUSED: {exc}", file=sys.stderr)
        return 1
    return 0


def spawn(log: Path) -> subprocess.Popen:
    fh = open(log, "a", encoding="utf-8")
    return subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "--child"], cwd=str(REPO),
                            stdout=fh, stderr=subprocess.STDOUT, start_new_session=True)


def container_running(c: dict) -> bool:
    rt = c["recognition"]["runtime"]
    out = subprocess.run(list(rt["docker_cli"]) + ["ps", "-q", "--filter", f"name=^{rt['container_name']}$"],
                         capture_output=True, text=True).stdout.strip()
    return bool(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--child", action="store_true")
    ap.add_argument("--n-questions", type=int, default=150)
    ap.add_argument("--kill-after", type=int, default=40)
    ap.add_argument("--seed", type=int, default=20261006)
    args = ap.parse_args()
    if args.child:
        return child()

    c = patched_cfg()
    if container_running(c):
        raise SystemExit("a dmio-recognize container is already running; refusing")
    P = H.paths(c)
    if SANDBOX.exists() and any(SANDBOX.rglob("*.jsonl")):
        raise SystemExit(f"sandbox {SANDBOX} not empty; move it aside")
    items = synthetic_items(c, args.n_questions, args.seed)
    items_sha = H.write_jsonl_atomic(P["rec_items"], items)
    log_path = P["rec_log"]

    t0 = time.monotonic()
    p = spawn(SANDBOX / "drill_kill.log")
    while len(lines(log_path)) < args.kill_after:
        if p.poll() is not None:
            raise SystemExit(f"recognize exited rc {p.returncode} before the kill point")
        time.sleep(0.2)
    os.killpg(p.pid, signal.SIGKILL)
    p.wait()
    killed_after = time.monotonic() - t0
    orphan = container_running(c)
    time.sleep(1.0)
    snap = "".join(lines(log_path))
    snap_lines = len(lines(log_path))

    t1 = time.monotonic()
    p2 = spawn(SANDBOX / "drill_resume.log")
    rc = p2.wait()
    resume_wall = time.monotonic() - t1
    final = "".join(lines(log_path))
    recs = [json.loads(x) for x in final.splitlines() if x.strip()]
    keys = [(r["qid"], int(r["ordering"])) for r in recs]
    need = {(it["qid"], int(it["ordering"])) for it in items}
    secs = [r["seconds"] for r in recs[snap_lines:]]
    secs_steady = sorted(secs[1:]) if len(secs) > 1 else secs
    res = {
        "check": "recognize_kill_resume_drill", "n_items": len(items), "items_sha256": items_sha,
        "kill_signal": "SIGKILL to the launcher process group (docker client); container left as orphan",
        "killed_after_s": round(killed_after, 1), "lines_at_kill_snapshot": snap_lines,
        "orphan_container_running_after_kill": orphan,
        "resume_rc": rc, "resume_wall_s": round(resume_wall, 1), "lines_after": len(recs),
        "unique_keys": len(set(keys)), "coverage_complete": set(keys) == need,
        "prekill_prefix_byte_identical": final.startswith(snap),
        "orphan_container_running_after_resume": container_running(c),
        "resume_first_prompt_s": secs[0] if secs else None,
        "resume_steady_s_per_prompt_median": secs_steady[len(secs_steady) // 2] if secs_steady else None,
        "resume_steady_s_per_prompt_mean": (sum(secs_steady) / len(secs_steady)) if secs_steady else None,
        "resume_prompts": len(secs),
        "top1_in_letters": sum(r["top1_in_letters"] for r in recs), "argmax_ties": sum(r["argmax_tie"] for r in recs),
        "gold_picks": sum(r["pred_letter_index"] == r["gold_letter_index"] for r in recs),
        "n_prompt_tokens_range": [min(r["n_prompt_tokens"] for r in recs), max(r["n_prompt_tokens"] for r in recs)],
    }
    res["pass"] = bool(rc == 0 and res["unique_keys"] == len(need) == len(recs) and res["coverage_complete"]
                       and res["prekill_prefix_byte_identical"] and not res["orphan_container_running_after_resume"])
    H.write_json_atomic(SANDBOX / "drill_summary.json", res)
    print(json.dumps(res, indent=2))
    return 0 if res["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
