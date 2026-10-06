#!/usr/bin/env python3
"""Harness for decision-model-idk-option (pinned at `bin/exp sign`).

Location: experiments/decision-model-idk-option/idk_harness.py
Config:   experiments/decision-model-idk-option/cell.yaml (every knob)
Gates:    experiments/decision-model-idk-option/gates.yaml
Adapted from: experiments/decision-model-calibrated-choice/dmcc_harness.py
              (utilities, engine staging, split port and statistics are ports
              of that file; its labeling and Stage 0 stages are not used).

Stages, in the only order the harness allows (each refuses if its inputs are
missing; GPU stages also require --i-know-this-runs-on-gpu):

  import-dmcc         CPU  copy dmcc's sha-pinned artifacts (rows, splits, PopQA
                           meta, dmcc TEST outputs) into analysis/dmcc_inputs/
  build-recognition   CPU  every dmcc primary row x 4 cyclic option rotations ->
                           Amendment-Y-style 5-shot multiple-choice prompts;
                           applies the exemplar-option collision rule
  recognize-smoke     GPU  pre-sign smoke of the recognition worker on the
                           non-PopQA cell.yaml smoke_items (never gated)
  recognize           GPU  base model (no adapter) next-token letter logits per
                           prompt, inside the pinned runner image; resumable
                           append-log (one JSON line per prompt, no text)
  recognition-labels  CPU  c = gold picks of 4 -> recognition groups; R0
                           validity (V1, V2); writes the RECOGNITION FREEZE
                           MARKER (labels sha256 + aggregate counts)
  build-idk-rows      CPU  dmcc rows x 5 IDK positions: one file per position,
                           "I don't know" inserted at canonical index k, the
                           real options in dmcc order; split identity checked
  stage-engine        CPU  per run key (idk_p<k>_<model>, noidk_<model>):
                           materialize the pinned template analysis config and
                           recipe for that run_id, stage rows + checkpoint into
                           the tuner's gitignored scratch/eh_staging/<run_id>/;
                           refuses without the recognition freeze marker;
                           writes the run record BEFORE any launch
  analyze             GPU  `py.exe -3.11 tuner.py local-run --job-config <materialized recipe> --yes`
  collect             CPU  copy engine outputs (test_rows + cal_rows) into
                           analysis/engine/<run_id>/
  score               CPU  gates.yaml adjudication for one model, question
                           level (5 IDK runs + the no-IDK run) -> verdict JSON
                           + committed summary

`plan` prints every stage's resolved inputs/outputs and the exact GPU argv
without computing anything (the registered real-mode dry run).

Containment: question text, prompts, option text and row-level outputs stay
under the gitignored analysis/. Only aggregates, the freeze marker and run
records are written under analysis-committed/.

No-pollution: the tuner is reached only through `tuner.py local-run` and
materialized YAML; the only tuner-tree write is ephemeral staging under its
gitignored scratch/eh_staging/. The recognition worker imports transformers
and torch inside the pinned runner image, never tuner code.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import re
import shutil
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
CELL_CONFIG = HERE / "cell.yaml"
TUNER_DIR = REPO_ROOT / "synaptic-tuner"

GPU_STAGES = {"recognize", "recognize-smoke", "recognize-worker", "analyze"}


# --------------------------------------------------------------------------
# small utilities (stdlib only at import time: the runner container imports
# this module for the recognition worker)
# --------------------------------------------------------------------------


class StageError(RuntimeError):
    pass


def _yaml_load(path: Path) -> dict:
    import yaml

    return yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}


def rp(rel: str | Path) -> Path:
    p = Path(rel)
    return p if p.is_absolute() else REPO_ROOT / p


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def tree_sha256(path: Path) -> str:
    """Same algorithm as bin/exp `_path_sha256` (file digest, or ordered tree digest)."""
    if path.is_file():
        return sha256_file(path)
    digest = hashlib.sha256()
    for child in sorted(path.rglob("*"), key=lambda p: p.relative_to(path).as_posix()):
        rel = child.relative_to(path).as_posix().encode("utf-8")
        if child.is_symlink():
            digest.update(b"L\0" + rel + b"\0" + str(child.readlink()).encode("utf-8") + b"\0")
        elif child.is_file():
            digest.update(b"F\0" + rel + b"\0" + sha256_file(child).encode("ascii") + b"\0")
    return digest.hexdigest()


def read_jsonl(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def write_jsonl_atomic(path: Path, rows: list[dict]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    os.replace(tmp, path)
    return sha256_file(path)


def write_json_atomic(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _host_path(p: str, base: Path) -> Path:
    """'F:/x' -> '/mnt/f/x' under WSL; relative gitdir pointers resolve against base."""
    if len(p) > 2 and p[1] == ":" and p[2] in "/\\" and os.name != "nt":
        return Path("/mnt/" + p[0].lower() + "/" + p[3:].replace("\\", "/"))
    q = Path(p)
    return q if q.is_absolute() else (base / q)


def _read_head(path: Path) -> str:
    """Resolve HEAD without the git CLI (WSL cannot follow a `gitdir: F:/...` pointer)."""
    dotgit = path / ".git"
    gitdir = dotgit
    if dotgit.is_file():
        gitdir = _host_path(dotgit.read_text(encoding="utf-8").split(":", 1)[1].strip(), path)
    head = (gitdir / "HEAD").read_text(encoding="utf-8").strip()
    if not head.startswith("ref:"):
        return head
    ref = head.split(":", 1)[1].strip()
    commondir = gitdir
    if (gitdir / "commondir").exists():
        commondir = _host_path((gitdir / "commondir").read_text(encoding="utf-8").strip(), gitdir)
    for base in (gitdir, commondir):
        f = base / ref
        if f.exists():
            return f.read_text(encoding="utf-8").strip()
    for line in (commondir / "packed-refs").read_text(encoding="utf-8").splitlines():
        if line.endswith(" " + ref):
            return line.split()[0]
    raise StageError(f"cannot resolve HEAD ref {ref} for {path}")


def git_head(path: Path) -> str:
    if not (path / ".git").exists():
        # An uninitialized submodule has no .git; `git -C` would silently
        # resolve the PARENT repo's HEAD instead.
        raise StageError(f"{path} is not a git checkout (submodule not initialized?)")
    out = subprocess.run(["git", "-C", str(path), "rev-parse", "HEAD"], capture_output=True, text=True)
    if out.returncode == 0 and out.stdout.strip():
        return out.stdout.strip()
    return _read_head(path)


def to_windows_path(p: Path) -> str:
    """/mnt/f/x -> F:\\x for py.exe launched from WSL; other paths unchanged."""
    s = str(p)
    if s.startswith("/mnt/") and len(s) > 6 and s[6] == "/":
        return f"{s[5].upper()}:\\" + s[7:].replace("/", "\\")
    return s


def host_abs(p: str) -> Path:
    """An absolute path from cell.yaml ('F:/...') as this host sees it."""
    return _host_path(p, REPO_ROOT)


def cfg() -> dict:
    return _yaml_load(CELL_CONFIG)


def paths(c: dict) -> dict[str, Path]:
    a = rp(c["paths"]["analysis_root"])
    return {
        "analysis": a,
        "committed": rp(c["paths"]["committed_root"]),
        "run_records": rp(c["paths"]["run_records"]),
        "dmcc": a / "dmcc_inputs",
        "rec": a / "recognition",
        "rec_items": a / "recognition" / "items.jsonl",
        "rec_log": a / "recognition" / "recognition_log.jsonl",
        "rec_labels": a / "recognition" / "labels.jsonl",
        "rec_freeze": rp(c["paths"]["committed_root"]) / "recognition_freeze.json",
        "presign": a / "presign",
        "idk_dir": a / "decision_rows_idk",
        "idk_manifest": a / "decision_rows_idk" / "idk_rows_manifest.json",
        "engine": a / "engine",
        "engine_recipes": a / "engine_recipes",
        "score": a / "score",
    }


def require(path: Path, what: str) -> Path:
    if not path.exists():
        raise StageError(f"missing {what}: {path} (run the earlier stage first)")
    return path


def normalize_answer(text: str) -> str:
    """EH scorer's alias normalizer (experiments/common/knowledge_probe/scoring.py),
    restated so the runner container needs no EH import; a test pins equality."""
    return " ".join(re.findall(r"[a-z0-9]+", str(text).lower()))


def dmcc_file(c: dict, key: str) -> Path:
    """Local copy of a predecessor artifact: analysis/dmcc_inputs/<key><suffix>
    (keyed, so the two arms' test_rows.jsonl cannot collide)."""
    return paths(c)["dmcc"] / f"{key}{Path(c['predecessor']['files'][key]['path']).suffix}"


# --------------------------------------------------------------------------
# recognition: prompt, rotations, group rule (pure; tested)
# --------------------------------------------------------------------------


def option_lines(options: list[str], letters: list[str], line_template: str) -> str:
    return "\n".join(line_template.format(letter=L, text=t) for L, t in zip(letters, options))


def build_mc_prompt(question: str, options: list[str], rc: dict) -> str:
    """Amendment-Y base-mode 5-shot block in multiple-choice form: five frozen
    exemplars "Q: ...\\n<A. ..>\\nA: <letter>\\n\\n", then the target ending at
    the answer cue "A:". The scored next token is " <letter>"."""
    pr, letters = rc["prompt"], rc["letters"]
    if len(options) != len(letters):
        raise ValueError(f"expected {len(letters)} options, got {len(options)}")
    block = ""
    for ex in pr["exemplars"]:
        gold = letters[list(ex["options"]).index(ex["gold"])]
        block += pr["exemplar_template"].format(
            question=ex["question"], option_lines=option_lines(ex["options"], letters, pr["option_line_template"]),
            letter=gold)
    return block + pr["target_template"].format(
        question=question, option_lines=option_lines(options, letters, pr["option_line_template"]))


def rotations(options: list[str], gold_index: int, n: int) -> list[tuple[list[str], int]]:
    """Cyclic rotations of the canonical option order: ordering k shows
    canonical[k:] + canonical[:k]; returns (options_k, gold letter index).
    Across the n orderings the gold option sits at every letter exactly once."""
    if n != len(options):
        raise ValueError("cyclic rotations need n == number of options")
    out = []
    for k in range(n):
        opts = list(options[k:]) + list(options[:k])
        out.append((opts, (gold_index - k) % n))
    return out


def letter_argmax(logits: list[float]) -> tuple[int, bool]:
    """Argmax over the letter logits; exact ties go to the lowest index (returned flag)."""
    best = max(logits)
    idx = [i for i, v in enumerate(logits) if v == best]
    return idx[0], len(idx) > 1


def recognition_group(c: int, n: int, rule: dict) -> str:
    if not 0 <= c <= n:
        raise ValueError(f"c={c} outside 0..{n}")
    if c >= int(rule["known_recognized_min"]):
        return "known_recognized"
    if c <= int(rule["unknown_true_max"]):
        return "unknown_true"
    return "recognition_ambiguous"


def exemplar_option_collision_qids(rows: list[dict], meta_by_qid: dict[str, dict], rc: dict) -> list[str]:
    """Pre-registered exclusion: a row collides iff any normalized exemplar
    option text equals a normalized gold alias (aliases + obj) or a normalized
    option text of that row. Deterministic, in row order."""
    ex = {normalize_answer(t) for e in rc["prompt"]["exemplars"] for t in e["options"]}
    ex.discard("")
    out = []
    for r in rows:
        q = r["meta"]["qid"]
        m = meta_by_qid[q]
        texts = {normalize_answer(a) for a in m["aliases"]} | {normalize_answer(m["obj"])} | \
            {normalize_answer(o[0]) for o in r["options"]}
        if texts & ex:
            out.append(q)
    return out


# --------------------------------------------------------------------------
# IDK option insertion (pure; tested)
# --------------------------------------------------------------------------


def insert_idk(row: dict, slot: int, text: str, description: str) -> dict:
    """Copy of a decision-row/v1 row with the IDK option inserted at canonical
    index `slot`. The original options keep their relative order; the gold
    label shifts by one when slot <= label. Everything else is unchanged."""
    n = len(row["options"])
    if not 0 <= slot <= n:
        raise ValueError(f"slot {slot} outside 0..{n}")
    if any(normalize_answer(o[0]) == normalize_answer(text) for o in row["options"]):
        raise ValueError(f"row {row['meta'].get('qid')} already has an option equal to the IDK text")
    new = json.loads(json.dumps(row))
    new["options"] = row["options"][:slot] + [[text, description]] + row["options"][slot:]
    new["label"] = row["label"] + (1 if slot <= row["label"] else 0)
    new["meta"]["idk_slot"] = slot
    new["meta"]["idk_text"] = text
    return new


# --------------------------------------------------------------------------
# engine split port (verbatim port from dmcc_harness, = synaptic-tuner
# decision_core split_fit_cal_test @ 29f7af0c; verified against the engine
# output by G0, never trusted on its own)
# --------------------------------------------------------------------------


def _split_by_task(rows: list[dict], val_fraction: float, seed: int) -> tuple[list[dict], list[dict]]:
    if not 0.0 <= val_fraction < 1.0:
        raise ValueError("val_fraction must be in [0, 1)")
    rng = random.Random(seed)
    by_task: dict[str, list[dict]] = {}
    for ex in rows:
        by_task.setdefault(ex["task"], []).append(ex)
    train: list[dict] = []
    val: list[dict] = []
    for task in sorted(by_task):
        items = list(by_task[task])
        rng.shuffle(items)
        n_val = int(round(len(items) * val_fraction)) if len(items) > 1 else 0
        val.extend(items[:n_val])
        train.extend(items[n_val:])
    rng.shuffle(train)
    rng.shuffle(val)
    return train, val


def engine_split(rows: list[dict], fit: float, cal: float, seed: int):
    rest, fit_rows = _split_by_task(rows, fit, seed)
    test_rows, cal_rows = _split_by_task(rest, cal / (1.0 - fit), seed + 1)
    return fit_rows, cal_rows, test_rows


def split_qids(rows: list[dict], acfg: dict) -> dict[str, list[str]]:
    f, c_, t = engine_split(rows, acfg["fit_fraction"], acfg["cal_fraction"], acfg["seed"])
    return {"fit": [r["meta"]["qid"] for r in f], "cal": [r["meta"]["qid"] for r in c_],
            "test": [r["meta"]["qid"] for r in t]}


# --------------------------------------------------------------------------
# statistics (numpy only; ported from dmcc_harness)
# --------------------------------------------------------------------------


def wilson(k: int, n: int, z: float = 1.959963984540054) -> list[float]:
    if n == 0:
        return [float("nan"), float("nan")]
    p = k / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / den
    return [max(0.0, centre - half), min(1.0, centre + half)]


def three_way(ci: list[float], threshold: float, direction: str) -> str:
    lo, hi = ci
    if direction == "at_most":
        return "PASS" if hi <= threshold else ("FAIL" if lo > threshold else "INCONCLUSIVE")
    return "PASS" if lo >= threshold else ("FAIL" if hi < threshold else "INCONCLUSIVE")


def auroc(y, s) -> float:
    import numpy as np

    y = np.asarray(y, dtype=int)
    s = np.asarray(s, dtype=np.float64)
    n1, n0 = int(y.sum()), int((1 - y).sum())
    if n1 == 0 or n0 == 0:
        return float("nan")
    order = np.argsort(s, kind="mergesort")
    ranks = np.empty(len(s), dtype=np.float64)
    sorted_s = s[order]
    i = 0
    while i < len(s):
        j = i
        while j + 1 < len(s) and sorted_s[j + 1] == sorted_s[i]:
            j += 1
        ranks[order[i:j + 1]] = (i + j) / 2.0 + 1.0
        i = j + 1
    return float((ranks[y == 1].sum() - n1 * (n1 + 1) / 2.0) / (n1 * n0))


def bootstrap_auroc_ci(y, s, reps: int, seed: int) -> list[float]:
    import numpy as np

    y = np.asarray(y, dtype=int)
    s = np.asarray(s, dtype=np.float64)
    rng = np.random.default_rng(seed)
    pos, neg = np.flatnonzero(y == 1), np.flatnonzero(y == 0)
    vals = []
    for _ in range(reps):
        idx = np.concatenate([rng.choice(pos, pos.size), rng.choice(neg, neg.size)])
        vals.append(auroc(y[idx], s[idx]))
    lo, hi = np.quantile(vals, [0.025, 0.975])
    return [float(lo), float(hi)]


def paired_rate_diff_ci(a, b, reps: int, seed: int) -> dict:
    """mean(a) - mean(b) over the same rows; paired row bootstrap, percentile 95%."""
    import numpy as np

    a, b = np.asarray(a, dtype=np.float64), np.asarray(b, dtype=np.float64)
    if a.size == 0:
        return {"diff": float("nan"), "ci95": [float("nan"), float("nan")], "n": 0}
    rng = np.random.default_rng(seed)
    diffs = []
    for _ in range(reps):
        idx = rng.integers(0, a.size, a.size)
        diffs.append(a[idx].mean() - b[idx].mean())
    lo, hi = np.quantile(diffs, [0.025, 0.975])
    return {"diff": float(a.mean() - b.mean()), "ci95": [float(lo), float(hi)], "n": int(a.size)}


def ece_binary(p, y, bins: int) -> float:
    import numpy as np

    p, y = np.asarray(p, dtype=np.float64), np.asarray(y, dtype=np.float64)
    edges = np.linspace(0, 1, bins + 1)
    tot = 0.0
    for i in range(bins):
        m = (p >= edges[i]) & ((p < edges[i + 1]) if i < bins - 1 else (p <= edges[i + 1]))
        if m.any():
            tot += m.mean() * abs(p[m].mean() - y[m].mean())
    return float(tot)


def tau_from_cal(cal_known_conf: list[float], r_cal: float) -> tuple[float, int]:
    """Registered cutoff rule (gates.yaml h3 cutoff): sort the no-IDK arm's CAL
    known R1 ascending; k = round(r_cal * n); tau = s_(k+1), +inf if k == n.
    Abstain iff R1 < tau, so exactly k CAL known rows abstain absent ties."""
    s = sorted(float(x) for x in cal_known_conf)
    n = len(s)
    if n == 0:
        raise ValueError("no CAL known rows")
    k = int(round(r_cal * n))
    k = min(max(k, 0), n)
    return (float("inf") if k == n else s[k]), k


def rate(k: int, n: int) -> dict:
    return {"k": int(k), "n": int(n), "rate": (k / n) if n else float("nan"), "wilson95": wilson(int(k), int(n))}


# --------------------------------------------------------------------------
# import-dmcc
# --------------------------------------------------------------------------


def stage_import_dmcc(c: dict, args) -> None:
    pre = c["predecessor"]
    root = host_abs(pre["root"])
    P = paths(c)
    P["dmcc"].mkdir(parents=True, exist_ok=True)
    got = {}
    for key, spec in pre["files"].items():
        src = root / spec["path"]
        if not src.exists():
            raise StageError(f"dmcc artifact {key} missing at {src}")
        sha = sha256_file(src)
        if sha != spec["sha256"]:
            raise StageError(f"dmcc artifact {key}: sha256 {sha} != pinned {spec['sha256']}")
        dst = dmcc_file(c, key)
        if dst.exists() and sha256_file(dst) == sha:
            got[key] = sha
            continue
        shutil.copy2(src, dst)
        if sha256_file(dst) != sha:
            raise StageError(f"copy of {key} changed bytes")
        got[key] = sha
    lsc = json.loads(dmcc_file(c, "label_and_split_counts").read_text(encoding="utf-8"))
    if lsc["rows_sha256"] != pre["files"]["decision_rows_primary"]["sha256"]:
        raise StageError("dmcc committed rows_sha256 disagrees with the pinned rows file")
    rows = read_jsonl(dmcc_file(c, "decision_rows_primary"))
    split = json.loads(dmcc_file(c, "splits").read_text(encoding="utf-8"))
    exp = pre["expected"]
    if len(rows) != exp["n_rows_primary"]:
        raise StageError(f"dmcc rows {len(rows)} != expected {exp['n_rows_primary']}")
    know = {r["meta"]["qid"]: r["meta"]["knowledge"] for r in rows}
    by = {k: dict(Counter(know[q] for q in v)) for k, v in split["qids"].items()}
    if by != exp["knowledge_by_split"]:
        raise StageError(f"dmcc knowledge_by_split {by} != expected {exp['knowledge_by_split']}")
    write_json_atomic(P["dmcc"] / "import_manifest.json", {
        "imported_at": now_utc(), "predecessor": pre["slug"], "signed_commit": pre["signed_commit"],
        "root": pre["root"], "sha256": got, "knowledge_by_split": by})
    print(f"import-dmcc: {len(got)} artifacts verified and copied to {P['dmcc']}")


def _dmcc_rows(c: dict) -> list[dict]:
    require(paths(c)["dmcc"] / "import_manifest.json", "dmcc import (run import-dmcc)")
    return read_jsonl(dmcc_file(c, "decision_rows_primary"))


# --------------------------------------------------------------------------
# build-recognition / recognize / recognition-labels
# --------------------------------------------------------------------------


def stage_build_recognition(c: dict, args) -> None:
    rc = c["recognition"]
    P = paths(c)
    rows = _dmcc_rows(c)
    meta = {m["qid"]: m for m in read_jsonl(dmcc_file(c, "popqa_meta"))}
    excl = exemplar_option_collision_qids(rows, meta, rc) if rc.get("exclude_exemplar_option_collisions") else []
    expected = _yaml_load(rp(c["scoring"]["gates"]))["g0_exemplar_option_collision_exclusion"]["expected_count"]
    if len(excl) != int(expected):
        raise StageError(f"exemplar-option collision rule matched {len(excl)} rows, pre-registered {expected}; "
                         "stop and consult the PI")
    excl_set = set(excl)
    items = []
    for r in rows:
        q = r["meta"]["qid"]
        if q in excl_set:
            continue
        opts = [o[0] for o in r["options"]]
        for k, (opts_k, gold_k) in enumerate(rotations(opts, int(r["label"]), int(rc["n_orderings"]))):
            items.append({"qid": q, "ordering": k, "gold_letter_index": gold_k,
                          "prompt": build_mc_prompt(r["state"], opts_k, rc)})
    sha = write_jsonl_atomic(P["rec_items"], items)
    write_json_atomic(P["rec"] / "items_manifest.json", {
        "built_at": now_utc(), "n_rows": len(rows) - len(excl), "n_items": len(items),
        "excluded_collisions": excl, "items_sha256": sha})
    print(f"build-recognition: {len(items):,} prompts over {len(rows) - len(excl):,} rows -> {P['rec_items']}")


def _runner_image_id(c: dict) -> str:
    rt = c["recognition"]["runtime"]
    out = subprocess.run(list(rt["docker_cli"]) + ["image", "inspect", rt["image_tag"], "--format", "{{.Id}}"],
                         capture_output=True, text=True)
    if out.returncode != 0:
        raise StageError(f"runner image {rt['image_tag']} not found")
    return out.stdout.strip()


def _check_image(c: dict) -> str:
    image_id = _runner_image_id(c)
    pinned = (_yaml_load(HERE / "experiment.yaml").get("instrument") or {}).get("runtime_image_digest")
    if not pinned:
        raise StageError("experiment.yaml instrument.runtime_image_digest is unset; pin it pre-sign")
    if image_id != pinned:
        raise StageError(f"runner image {image_id} != pinned runtime_image_digest {pinned}")
    return image_id


def runner_argv(c: dict, inner: list[str], image_id: str) -> list[str]:
    rt = c["recognition"]["runtime"]
    return list(rt["docker"]) + [
        "--name", rt["container_name"], "-v", os.path.expandvars(rt["hf_cache_mount"]),
        "-v", f"{REPO_ROOT}:{rt['workdir_in_container']}", "-w", rt["workdir_in_container"],
        "--env", f"IMAGE_DIGEST={image_id}", "--env", f"PYTHONPATH={rt['pythonpath']}", "--env", "HF_TOKEN",
        rt["image_tag"]] + inner


def worker_inner(items: Path, out: Path) -> list[str]:
    rel = lambda p: p.relative_to(REPO_ROOT).as_posix()  # noqa: E731
    return ["python", rel(HERE / "idk_harness.py"), "recognize-worker", "--items", rel(items), "--out", rel(out),
            "--i-know-this-runs-on-gpu"]


def _run_worker(c: dict, items: Path, out: Path, log: Path) -> None:
    image_id = _check_image(c)
    rt = c["recognition"]["runtime"]
    subprocess.run(list(rt["docker_cli"]) + ["rm", "-f", rt["container_name"]], capture_output=True)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(log, "a", encoding="utf-8") as fh:
        fh.write(f"\n=== {now_utc()} launch image {image_id}\n")
        fh.flush()
        rc = subprocess.run(runner_argv(c, worker_inner(items, out), image_id), cwd=str(REPO_ROOT),
                            stdout=fh, stderr=subprocess.STDOUT).returncode
    if rc != 0:
        raise StageError(f"recognition worker exited {rc}; see {log} (rerun resumes from the append-log)")


def stage_recognize(c: dict, args) -> None:
    P = paths(c)
    require(P["rec_items"], "recognition items (run build-recognition)")
    rec = P["run_records"] / "dmio-recognize.json"
    write_json_atomic(rec, {"run_id": "dmio-recognize", "stage": "recognize", "launched_at": now_utc(),
                            "items_sha256": sha256_file(P["rec_items"]),
                            "image": c["recognition"]["runtime"]["image_tag"],
                            "research_repo_commit": git_head(REPO_ROOT),
                            "argv": runner_argv(c, worker_inner(P["rec_items"], P["rec_log"]), "<pinned image id>"),
                            "outcome": {"status": "launched", "verified": False}})
    _run_worker(c, P["rec_items"], P["rec_log"], P["rec"] / "recognize.log")
    r = json.loads(rec.read_text(encoding="utf-8"))
    r["outcome"] = {"status": "completed", "finished_at": now_utc(), "log_sha256": sha256_file(P["rec_log"]),
                    "verified": False}
    write_json_atomic(rec, r)
    print(f"recognize: complete -> {P['rec_log']}")


def stage_recognize_smoke(c: dict, args) -> None:
    """Pre-sign smoke on non-PopQA items; run twice to check repeat identity."""
    rc = c["recognition"]
    P = paths(c)
    items = []
    for i, it in enumerate(rc["smoke_items"]):
        for k, (opts_k, gold_k) in enumerate(rotations(list(it["options"]), list(it["options"]).index(it["gold"]),
                                                       int(rc["n_orderings"]))):
            items.append({"qid": f"smoke-{i}", "ordering": k, "gold_letter_index": gold_k,
                          "prompt": build_mc_prompt(it["question"], opts_k, rc)})
    sp = P["presign"] / "smoke_items.jsonl"
    write_jsonl_atomic(sp, items)
    outs = []
    for rep in (1, 2):
        out = P["presign"] / f"smoke_log_rep{rep}.jsonl"
        if out.exists():
            out.unlink()
        _run_worker(c, sp, out, P["presign"] / "smoke.log")
        outs.append(read_jsonl(out))
    a = {(r["qid"], r["ordering"]): r for r in outs[0]}
    b = {(r["qid"], r["ordering"]): r for r in outs[1]}
    summary = {"smoked_at": now_utc(), "n_prompts": len(items),
               "repeat_identical_logits": sum(a[k]["letter_logits"] == b[k]["letter_logits"] for k in a),
               "top1_in_letters": sum(r["top1_in_letters"] for r in outs[0]),
               "gold_picks": sum(r["pred_letter_index"] == r["gold_letter_index"] for r in outs[0]),
               "seconds_per_prompt": [r.get("seconds") for r in outs[0]][:3]}
    write_json_atomic(P["presign"] / "recognize_smoke_summary.json", summary)
    print(json.dumps(summary, indent=2))


def stage_recognize_worker(c: dict, args) -> None:
    """Runs INSIDE the pinned runner image. Base model, no adapter, one prompt
    per forward; appends one JSON line per (qid, ordering), flushed per line,
    skipping keys already present (kill-resume)."""
    import time

    import torch
    import transformers

    rc = c["recognition"]
    items = read_jsonl(rp(args.items))
    out = rp(args.out)
    done = set()
    if out.exists():
        for r in read_jsonl(out):
            done.add((r["qid"], int(r["ordering"])))
    tok = transformers.AutoTokenizer.from_pretrained(rc["hf_id"], revision=rc["revision"])
    letter_ids = []
    for L in rc["letters"]:
        ids = tok.encode(rc["letter_token_prefix"] + L, add_special_tokens=False)
        if len(ids) != 1:
            raise StageError(f"letter {L!r} encodes to {ids}, not one token")
        letter_ids.append(int(ids[0]))
    cls = getattr(transformers, rc["causal_lm_class"])
    model = cls.from_pretrained(rc["hf_id"], revision=rc["revision"],
                                torch_dtype=getattr(torch, rc["torch_dtype"])).to("cuda").eval()
    print(json.dumps({"recognize_worker_provenance": {
        "image_digest": os.environ.get("IMAGE_DIGEST"), "transformers": transformers.__version__,
        "torch": torch.__version__, "hf_id": rc["hf_id"], "revision": rc["revision"],
        "letter_ids": letter_ids, "n_items": len(items), "n_done": len(done)}}), flush=True)
    with open(out, "a", encoding="utf-8") as fh, torch.no_grad():
        for it in items:
            key = (it["qid"], int(it["ordering"]))
            if key in done:
                continue
            t0 = time.perf_counter()  # monotonic: the container wall clock can step backwards
            enc = tok(it["prompt"], return_tensors="pt", add_special_tokens=False).to("cuda")
            logits = model(**enc, use_cache=False).logits[0, -1].float()
            ll = [float(logits[i]) for i in letter_ids]
            pred, tie = letter_argmax(ll)
            top1 = int(torch.argmax(logits))
            fh.write(json.dumps({"qid": it["qid"], "ordering": int(it["ordering"]),
                                 "gold_letter_index": int(it["gold_letter_index"]), "letter_logits": ll,
                                 "pred_letter_index": pred, "argmax_tie": tie, "top1_token_id": top1,
                                 "top1_in_letters": top1 in letter_ids, "n_prompt_tokens": int(enc["input_ids"].shape[1]),
                                 "seconds": round(time.perf_counter() - t0, 4)}) + "\n")
            fh.flush()
    print("recognize-worker: done", flush=True)


def stage_recognition_labels(c: dict, args) -> None:
    rc = c["recognition"]
    P = paths(c)
    gates = _yaml_load(rp(c["scoring"]["gates"]))
    rows = _dmcc_rows(c)
    split = json.loads(dmcc_file(c, "splits").read_text(encoding="utf-8"))
    split_of = {q: s for s, qs in split["qids"].items() for q in qs}
    items = read_jsonl(require(P["rec_items"], "recognition items"))
    log = {(r["qid"], int(r["ordering"])): r for r in read_jsonl(require(P["rec_log"], "recognition log"))}
    need = {(it["qid"], int(it["ordering"])) for it in items}
    if need - set(log):
        raise StageError(f"recognition log covers {len(need & set(log))} of {len(need)} prompts; finish `recognize`")
    n = int(rc["n_orderings"])
    labels, cdist = [], Counter()
    for r in rows:
        q = r["meta"]["qid"]
        if (q, 0) not in need:
            labels.append({"qid": q, "dmcc_knowledge": r["meta"]["knowledge"], "c": None,
                           "group": "recognition_excluded", "split": split_of[q]})
            continue
        recs = [log[(q, k)] for k in range(n)]
        c_ = sum(int(x["pred_letter_index"] == x["gold_letter_index"]) for x in recs)
        know = r["meta"]["knowledge"]
        group = "known" if know == "known" else recognition_group(c_, n, rc["group_rule"])
        labels.append({"qid": q, "dmcc_knowledge": know, "c": c_, "group": group, "split": split_of[q]})
        cdist[(know, c_)] += 1
    lab_sha = write_jsonl_atomic(P["rec_labels"], labels)
    allrec = list(log.values())
    known_c = [l_["c"] for l_ in labels if l_["dmcc_knowledge"] == "known" and l_["c"] is not None]
    v1k = sum(1 for x in known_c if x >= int(rc["group_rule"]["known_recognized_min"]))
    v1 = rate(v1k, len(known_c))
    g1 = gates["r0_v1_positive_control"]
    v1_ok = v1["wilson95"][0] >= float(g1["threshold"])
    fmt = sum(1 for x in allrec if x["top1_in_letters"]) / max(1, len(allrec))
    v2_ok = fmt >= float(gates["r0_v2_format_adherence"]["threshold"])
    counts = {s: dict(Counter(l_["group"] for l_ in labels if l_["split"] == s)) for s in ("fit", "cal", "test")}
    freeze = {
        "frozen_at": now_utc(), "labels_sha256": lab_sha, "recognition_log_sha256": sha256_file(P["rec_log"]),
        "items_sha256": sha256_file(P["rec_items"]),
        "r0": {"v1_positive_control": {**v1, "threshold": g1["threshold"], "pass": bool(v1_ok)},
               "v2_format_adherence": {"rate": fmt, "n": len(allrec),
                                       "threshold": gates["r0_v2_format_adherence"]["threshold"],
                                       "pass": bool(v2_ok)},
               "valid": bool(v1_ok and v2_ok)},
        "groups_by_split": counts,
        "c_distribution": {f"{k}|c={c_}": v for (k, c_), v in sorted(cdist.items())},
        "argmax_ties": sum(1 for x in allrec if x["argmax_tie"]),
        "pred_letter_shares": {rc["letters"][i]: v / max(1, len(allrec)) for i, v in
                               sorted(Counter(x["pred_letter_index"] for x in allrec).items())},
        "chance_reference": gates["r0_chance_reference"],
    }
    write_json_atomic(P["rec_freeze"], freeze)  # aggregates only, no text
    print(f"recognition-labels: R0 valid={freeze['r0']['valid']} (V1 {v1['rate']:.4f} {v1['wilson95']}, "
          f"V2 {fmt:.4f}); TEST groups {counts['test']}; freeze marker {P['rec_freeze']}")


def require_freeze(c: dict) -> dict:
    P = paths(c)
    marker = require(P["rec_freeze"], "recognition freeze marker (run recognition-labels)")
    fz = json.loads(marker.read_text(encoding="utf-8"))
    if sha256_file(P["rec_labels"]) != fz["labels_sha256"]:
        raise StageError("recognition labels differ from the frozen digest")
    return fz


# --------------------------------------------------------------------------
# build-idk-rows (one file per IDK position)
# --------------------------------------------------------------------------


def idk_rows_path(c: dict, position: int) -> Path:
    return paths(c)["idk_dir"] / f"decision_rows_idk_p{position}.jsonl"


def stage_build_idk_rows(c: dict, args) -> None:
    io = c["idk_option"]
    P = paths(c)
    rows = _dmcc_rows(c)
    acfg = _yaml_load(rp(c["noidk_runs"]["pointer"]["analysis_config"]))["data"]
    split = json.loads(dmcc_file(c, "splits").read_text(encoding="utf-8"))
    if split_qids(rows, acfg) != split["qids"]:
        raise StageError("ported engine split of the dmcc rows differs from dmcc splits.json")
    shas = {}
    for k in io["positions"]:
        new = [insert_idk(r, int(k), io["text"], io["description"]) for r in rows]
        if split_qids(new, acfg) != split["qids"]:
            raise StageError(f"ported engine split of the IDK rows (position {k}) differs from dmcc splits.json")
        shas[int(k)] = write_jsonl_atomic(idk_rows_path(c, int(k)), new)
    write_json_atomic(P["idk_manifest"], {"built_at": now_utc(), "rows_sha256_by_position": shas,
                                          "n_rows_per_position": len(rows),
                                          "source_rows_sha256": sha256_file(dmcc_file(c, "decision_rows_primary")),
                                          "idk_text": io["text"], "positions": list(io["positions"]),
                                          "split_identity_with_dmcc": True})
    print(f"build-idk-rows: {len(rows):,} rows x {len(shas)} IDK positions -> {P['idk_dir']}")


# --------------------------------------------------------------------------
# engine: run specs, template materialization, stage-engine / analyze / collect
# --------------------------------------------------------------------------


def run_keys(c: dict) -> list[str]:
    keys = []
    for model in c["models"]:
        keys += [f"idk_p{k}_{model}" for k in c["idk_option"]["positions"]] + [f"noidk_{model}"]
    return keys


def run_spec(c: dict, key: str) -> dict:
    """Resolve a run key (idk_p<k>_<model> | noidk_<model>) to its run spec."""
    m = re.fullmatch(r"idk_p(\d+)_(\w+)", key)
    if m and m.group(2) in c["idk_runs"] and int(m.group(1)) in [int(x) for x in c["idk_option"]["positions"]]:
        t = c["idk_runs"][m.group(2)]
        k = int(m.group(1))
        return {"key": key, "model": m.group(2), "arm": "idk", "position": k,
                "run_id": t["run_id_template"].format(position=k), "template_run_id": t["template_run_id"],
                "analysis_config": t["analysis_config"], "recipe": t["recipe"],
                "rows_source": idk_rows_path(c, k), "staged_rows_name": c["staged_rows_name"]["idk"]}
    m = re.fullmatch(r"noidk_(\w+)", key)
    if m and m.group(1) in c["noidk_runs"]:
        t = c["noidk_runs"][m.group(1)]
        return {"key": key, "model": m.group(1), "arm": "noidk", "position": None,
                "run_id": t["run_id"], "template_run_id": t["run_id"],
                "analysis_config": t["analysis_config"], "recipe": t["recipe"],
                "rows_source": dmcc_file(c, "decision_rows_primary"),
                "staged_rows_name": c["staged_rows_name"]["noidk"]}
    raise StageError(f"--run must be one of {run_keys(c)}")


def materialize(text: str, template_run_id: str, run_id: str) -> str:
    """A template's text for one run: every occurrence of the template run_id
    replaced by the run's run_id. Identity for the no-IDK runs."""
    if template_run_id not in text:
        raise StageError(f"template does not contain its run_id {template_run_id}")
    return text.replace(template_run_id, run_id)


def _run(c: dict, args) -> tuple[str, dict, dict]:
    if not args.run:
        raise StageError(f"--run must be one of {run_keys(c)}")
    r = run_spec(c, args.run)
    return args.run, r, dict(c["models"][r["model"]])


def staging_dir(c: dict, r: dict) -> Path:
    return TUNER_DIR / c["engine"]["staging_root"] / r["run_id"]


def run_record_path(c: dict, r: dict) -> Path:
    return paths(c)["run_records"] / f"{r['run_id']}.json"


def materialized_recipe_path(c: dict, r: dict) -> Path:
    return paths(c)["engine_recipes"] / f"{r['run_id']}.yaml"


def analyze_argv(c: dict, r: dict) -> list[str]:
    return list(c["engine"]["launcher"]) + [to_windows_path(materialized_recipe_path(c, r)), "--yes"]


def stage_engine(c: dict, args) -> None:
    key, r, m = _run(c, args)
    require_freeze(c)  # no decision-model analysis before the recognition labels are frozen
    src = host_abs(m["source_checkpoint"])
    got = tree_sha256(src)
    if got != m["tree_sha256"]:
        raise StageError(f"checkpoint tree digest {got} != expected {m['tree_sha256']}")
    head = git_head(TUNER_DIR)
    if head != c["engine"]["commit"]:
        raise StageError(f"synaptic-tuner HEAD {head} != pinned engine commit {c['engine']['commit']}")
    rows = require(r["rows_source"], f"{r['arm']} rows")
    sd = staging_dir(c, r)
    if sd.exists() and any(sd.iterdir()):
        raise StageError(f"staging dir {sd} not empty; move it aside (never overwritten)")
    sd.mkdir(parents=True)
    shutil.copytree(src, sd / "final_model")
    shutil.copy2(rows, sd / r["staged_rows_name"])
    acfg_t = rp(r["analysis_config"])
    acfg_text = materialize(acfg_t.read_text(encoding="utf-8"), r["template_run_id"], r["run_id"])
    (sd / acfg_t.name).write_text(acfg_text, encoding="utf-8", newline="\n")
    rec_path = materialized_recipe_path(c, r)
    rec_path.parent.mkdir(parents=True, exist_ok=True)
    rec_path.write_text(materialize(rp(r["recipe"]).read_text(encoding="utf-8"), r["template_run_id"], r["run_id"]),
                        encoding="utf-8", newline="\n")
    if tree_sha256(sd / "final_model") != m["tree_sha256"]:
        raise StageError("staged checkpoint digest mismatch after copy")
    rec = {
        "run_id": r["run_id"], "cell": c["slug"], "run_key": key, "arm": r["arm"], "idk_position": r["position"],
        "model": r["model"], "role": m["role"], "method": "decision", "engine_cli": c["engine"]["cli"],
        "lane": "local", "image": c["engine"]["image"],
        "template_recipe": r["recipe"], "template_recipe_sha256": sha256_file(rp(r["recipe"])),
        "materialized_recipe": rec_path.relative_to(REPO_ROOT).as_posix(),
        "materialized_recipe_sha256": sha256_file(rec_path),
        "template_analysis_config": r["analysis_config"], "template_analysis_config_sha256": sha256_file(acfg_t),
        "materialized_analysis_config_sha256": sha256_file(sd / acfg_t.name),
        "checkpoint": {"source": m["source_checkpoint"], "tree_sha256": got, "tuner_run": m["tuner_run"]},
        "data": {"source_data_file": rows.relative_to(REPO_ROOT).as_posix(),
                 "staged_data_file": (sd / r["staged_rows_name"]).relative_to(TUNER_DIR).as_posix(),
                 "hf_dataset_name": None, "hf_dataset_revision": None},
        "data_sha256": sha256_file(rows), "research_repo_commit": git_head(REPO_ROOT), "submodule_commit": head,
        "recognition_freeze_sha256": sha256_file(paths(c)["rec_freeze"]),
        "tuner_invocation": analyze_argv(c, r), "staged_at": now_utc(),
        "outcome": {"status": "staged", "metrics_path": None, "verified": False}}
    write_json_atomic(run_record_path(c, r), rec)
    print(f"stage-engine: staged {r['run_id']} at {sd}; run record {run_record_path(c, r)}")


def stage_analyze(c: dict, args) -> None:
    key, r, m = _run(c, args)
    require_freeze(c)
    rr = run_record_path(c, r)
    rec = json.loads(require(rr, "run record (run stage-engine)").read_text(encoding="utf-8"))
    sd = staging_dir(c, r)
    if tree_sha256(sd / "final_model") != m["tree_sha256"] or \
            sha256_file(sd / r["staged_rows_name"]) != rec["data_sha256"] or \
            sha256_file(materialized_recipe_path(c, r)) != rec["materialized_recipe_sha256"]:
        raise StageError("staged inputs changed since stage-engine; restage")
    if git_head(TUNER_DIR) != c["engine"]["commit"]:
        raise StageError("synaptic-tuner HEAD moved off the pinned engine commit")
    rec["outcome"] = {"status": "launched", "launched_at": now_utc(), "metrics_path": None, "verified": False}
    write_json_atomic(rr, rec)
    rc = subprocess.run(analyze_argv(c, r), cwd=str(TUNER_DIR)).returncode
    rec["outcome"].update({"status": "completed" if rc == 0 else "failed", "returncode": rc,
                           "finished_at": now_utc()})
    write_json_atomic(rr, rec)
    if rc != 0:
        raise StageError(f"local-run exited {rc}")
    print(f"analyze: {r['run_id']} completed; run `collect --run {key}`")


def stage_collect(c: dict, args) -> None:
    key, r, m = _run(c, args)
    sd = staging_dir(c, r) / "output"
    runs = sorted(p for p in sd.glob("*") if (p / "confidence_report.json").exists())
    if not runs:
        raise StageError(f"no engine output under {sd}")
    src = runs[-1]
    dst = paths(c)["engine"] / r["run_id"] / src.name
    if dst.exists():
        raise StageError(f"{dst} already collected")
    if not (src / c["engine"]["cal_rows_file"]).exists():
        raise StageError(f"{src} has no {c['engine']['cal_rows_file']}; the pinned engine must export CAL "
                         "per-row records (analysis config export.cal_rows: true)")
    shutil.copytree(src, dst)
    rr = run_record_path(c, r)
    rec = json.loads(rr.read_text(encoding="utf-8"))
    rec["outcome"].update({"metrics_path": dst.relative_to(REPO_ROOT).as_posix(),
                           "artifact_sha256": {p.name: sha256_file(p) for p in sorted(dst.iterdir()) if p.is_file()},
                           "collected_at": now_utc()})
    write_json_atomic(rr, rec)
    print(f"collect: {src} -> {dst}")


def _collected(c: dict, run_key: str) -> tuple[dict, Path]:
    r = run_spec(c, run_key)
    rec = json.loads(require(run_record_path(c, r), f"run record {r['run_id']}").read_text(encoding="utf-8"))
    out = rp(rec["outcome"].get("metrics_path") or "__missing__")
    require(out, f"collected engine output for {r['run_id']}")
    return rec, out


# --------------------------------------------------------------------------
# score: question-level aggregation (pure; tested) + adjudication
# --------------------------------------------------------------------------


def pick_idk_flags(rows: list[dict]) -> list[bool]:
    """pick_idk per engine record: the argmax option is the IDK option's
    canonical index (meta.idk_slot = the run's IDK position)."""
    return [int(r["pred"]) == int(r["meta"]["idk_slot"]) for r in rows]


def question_table(runs: dict[int, list[dict]]) -> dict[str, dict]:
    """Per question (qid), over the IDK positions: the IDK rate (mean of the 5
    pick-IDK indicators, in [0, 1]), the 3-way shares (picked IDK / answered
    right / answered wrong; they sum to 1), the per-position indicators, and
    the mean calibrated IDK mass. Every question must appear exactly once in
    every position's run, with that run's position as its IDK slot."""
    positions = sorted(runs)
    by_pos: dict[int, dict[str, dict]] = {}
    for k in positions:
        d = {}
        for r in runs[k]:
            if int(r["meta"]["idk_slot"]) != k:
                raise StageError(f"position-{k} run has a row with idk_slot {r['meta']['idk_slot']}")
            if r["meta"]["qid"] in d:
                raise StageError(f"duplicate qid {r['meta']['qid']} in position-{k} run")
            d[r["meta"]["qid"]] = r
        by_pos[k] = d
    qids = set(by_pos[positions[0]])
    if any(set(by_pos[k]) != qids for k in positions):
        raise StageError("IDK position runs do not cover the same questions")
    out = {}
    n = len(positions)
    for q in sorted(qids):
        recs = [by_pos[k][q] for k in positions]
        idk = [int(r["pred"]) == int(r["meta"]["idk_slot"]) for r in recs]
        right = [(not i) and bool(r["correct"]) for i, r in zip(idk, recs)]
        p_idk = [r["probs_r1"][int(r["meta"]["idk_slot"])] for r in recs if "probs_r1" in r]
        out[q] = {"knowledge": recs[0]["meta"]["knowledge"], "idk_by_position": dict(zip(positions, idk)),
                  "idk_rate": sum(idk) / n, "right_share": sum(right) / n,
                  "wrong_share": (n - sum(idk) - sum(right)) / n,
                  "answered_accuracy": (sum(right) / (n - sum(idk))) if sum(idk) < n else None,
                  "mean_p_idk_r1": (sum(p_idk) / len(p_idk)) if len(p_idk) == n else None,
                  "preds": {k: int(r["pred"]) for k, r in zip(positions, recs)}}
    return out


def cluster_mean_ci(values, reps: int, seed: int) -> dict:
    """Mean of question-level values with a question-level (cluster) bootstrap:
    resample questions with replacement, percentile 95%."""
    import numpy as np

    x = np.asarray([v for v in values if v is not None], dtype=np.float64)
    if x.size == 0:
        return {"mean": float("nan"), "ci95": [float("nan"), float("nan")], "n_questions": 0}
    rng = np.random.default_rng(seed)
    means = [x[rng.integers(0, x.size, x.size)].mean() for _ in range(reps)]
    lo, hi = np.quantile(means, [0.025, 0.975])
    return {"mean": float(x.mean()), "ci95": [float(lo), float(hi)], "n_questions": int(x.size)}


def h3_compare(qt_test: dict[str, dict], qt_cal: dict[str, dict], noidk_test: list[dict], noidk_cal: list[dict],
               group_of: dict[str, str], gates: dict, reps: int, seed: int) -> dict:
    """H3 as registered, on question-level rates: tau from CAL known questions
    only (matched to the IDK arm's CAL question-level over-IDK); matched
    precondition on TEST known; paired question-level delta of recall on TEST
    unknown_true."""
    import numpy as np

    cal_known = [q for q, v in qt_cal.items() if v["knowledge"] == "known"]
    if len(cal_known) < gates["g0_floors"]["min_cal_known"]:
        return {"verdict": "NOT-ADJUDICABLE", "reason": f"CAL known {len(cal_known)} below floor"}
    no_cal = {r["meta"]["qid"]: r for r in noidk_cal}
    no_test = {r["meta"]["qid"]: r for r in noidk_test}
    r_cal = float(np.mean([qt_cal[q]["idk_rate"] for q in cal_known]))
    tau, k = tau_from_cal([no_cal[q]["conf_r1"] for q in cal_known], r_cal)
    known = [q for q, v in qt_test.items() if v["knowledge"] == "known"]
    ut = [q for q in qt_test if group_of.get(q) == "unknown_true"]
    over_idk = [qt_test[q]["idk_rate"] for q in known]
    over_thr = [float(no_test[q]["conf_r1"] < tau) for q in known]
    match = paired_rate_diff_ci(over_thr, over_idk, reps, seed)
    rec_idk = [qt_test[q]["idk_rate"] for q in ut]
    rec_thr = [float(no_test[q]["conf_r1"] < tau) for q in ut]
    delta = paired_rate_diff_ci(rec_idk, rec_thr, reps, seed)
    matched = match["ci95"][0] <= 0.0 <= match["ci95"][1]
    lo, hi = delta["ci95"]
    v = "IDK_BETTER" if lo > 0 else ("THRESHOLD_BETTER" if hi < 0 else "NO_DIFFERENCE_DETECTED")
    out = {"r_cal_question_level_over_idk": r_cal, "tau": tau, "k_cal_abstain": k, "n_cal_known": len(cal_known),
           "test_over_idk": float(np.mean(over_idk)) if known else None,
           "test_over_threshold": float(np.mean(over_thr)) if known else None,
           "matched_check": match, "matched": bool(matched),
           "recall_idk": float(np.mean(rec_idk)) if ut else None,
           "recall_threshold": float(np.mean(rec_thr)) if ut else None,
           "delta": delta, "verdict_if_matched": v}
    out["verdict"] = v if matched else "NOT-ADJUDICABLE"
    if not matched:
        out["reason"] = "operating points not matched on TEST known (paired CI excludes 0)"
    return out


def test_matched_descriptive(qt_test: dict[str, dict], noidk_test: list[dict], group_of: dict[str, str],
                             reps: int, seed: int) -> dict:
    """Descriptive only: tau chosen on TEST known questions to equal the IDK arm's TEST over-IDK."""
    import numpy as np

    no_test = {r["meta"]["qid"]: r for r in noidk_test}
    known = [q for q, v in qt_test.items() if v["knowledge"] == "known"]
    ut = [q for q in qt_test if group_of.get(q) == "unknown_true"]
    r_t = float(np.mean([qt_test[q]["idk_rate"] for q in known]))
    tau, _ = tau_from_cal([no_test[q]["conf_r1"] for q in known], r_t)
    return {"tau_test_matched": tau,
            "delta": paired_rate_diff_ci([qt_test[q]["idk_rate"] for q in ut],
                                         [float(no_test[q]["conf_r1"] < tau) for q in ut], reps, seed)}


def position_table(qt: dict[str, dict], groups: dict[str, list[str]], positions: list[int],
                   strong_range: float) -> dict:
    """Descriptive position bias: pick-IDK rate at each IDK position (one copy
    per question per position, so Wilson over questions), pooled and per group;
    range = max - min over positions; flagged when range >= strong_range."""
    out = {}
    for g, qs in groups.items():
        per = {}
        for k in positions:
            hits = sum(int(qt[q]["idk_by_position"][k]) for q in qs)
            per[k + 1] = rate(hits, len(qs))  # reported as positions 1..5
        vals = [v["rate"] for v in per.values() if v["n"]]
        rng_ = (max(vals) - min(vals)) if vals else None
        out[g] = {"by_position": per, "range": rng_,
                  "strong_position_effect": bool(rng_ is not None and rng_ >= strong_range)}
    return out


def stage_score(c: dict, args) -> None:
    import numpy as np

    model = args.model
    P = paths(c)
    gates = _yaml_load(rp(c["scoring"]["gates"]))
    reps, seed = c["scoring"]["bootstrap_reps"], c["scoring"]["bootstrap_seed"]
    fz = require_freeze(c)
    labels = {l_["qid"]: l_ for l_ in read_jsonl(P["rec_labels"])}
    group_of = {q: l_["group"] for q, l_ in labels.items()}
    e = c["engine"]
    positions = [int(k) for k in c["idk_option"]["positions"]]
    split = json.loads(dmcc_file(c, "splits").read_text(encoding="utf-8"))
    m = c["models"][model]
    na = "NOT-ADJUDICABLE"
    res: dict = {"model": model, "role": m["role"], "scored_at": now_utc(), "unit": "question",
                 "positions": positions, "g0": {}, "r0": fz["r0"], "gates": {}}

    # ---- load: 5 IDK runs + 1 no-IDK run, TEST and CAL per-row records
    recs, test_runs, cal_runs = {}, {}, {}
    for k in positions:
        rec, out = _collected(c, f"idk_p{k}_{model}")
        recs[f"idk_p{k}"] = (rec, out)
        test_runs[k] = read_jsonl(out / e["test_rows_file"])
        cal_runs[k] = read_jsonl(out / e["cal_rows_file"]) if (out / e["cal_rows_file"]).exists() else []
    rec_n, out_n = _collected(c, f"noidk_{model}")
    recs["noidk"] = (rec_n, out_n)
    no_test = read_jsonl(out_n / e["test_rows_file"])
    no_cal = read_jsonl(out_n / e["cal_rows_file"]) if (out_n / e["cal_rows_file"]).exists() else []

    # ---- G0 integrity
    g0 = gates["g0_integrity"]
    want_n = {k: len(v) for k, v in split["qids"].items()}
    test_sets = list(test_runs.values()) + [no_test]
    cal_sets = list(cal_runs.values()) + [no_cal]
    split_ok = all(sorted(r["meta"]["qid"] for r in t) == sorted(split["qids"]["test"]) for t in test_sets)
    cal_ok = all(sorted(r["meta"]["qid"] for r in t) == sorted(split["qids"]["cal"])
                 and all(r.get("split") == "cal" for r in t) for t in cal_sets)
    counts_ok = all(json.loads((out / "confidence_report.json").read_text(encoding="utf-8"))["n_rows"] == want_n
                    for _rec, out in recs.values())
    commit_ok = all(rec["submodule_commit"] == c["engine"]["commit"] for rec, _o in recs.values())
    ckpt_ok = all(rec["checkpoint"]["tree_sha256"] == g0[f"{model}_checkpoint_tree_sha256"]
                  for rec, _o in recs.values())
    shape_ok = all(r["n_options"] == 5 and int(r["meta"]["idk_slot"]) == k
                   for k in positions for r in test_runs[k] + cal_runs[k]) and \
        all(r["n_options"] == 4 for r in no_test + no_cal)
    fz_sha = sha256_file(P["rec_freeze"])
    fz_ok = all(rec.get("recognition_freeze_sha256") == fz_sha for rec, _o in recs.values())
    res["g0"]["integrity"] = {"split_identity": split_ok and counts_ok, "cal_rows_split_identity": cal_ok,
                              "engine_commit": commit_ok, "checkpoint_digest": ckpt_ok,
                              "idk_rows_shape_and_positions": shape_ok,
                              "recognition_frozen_before_analysis": fz_ok}
    integrity_ok = split_ok and counts_ok and cal_ok and commit_ok and ckpt_ok and shape_ok and fz_ok
    if not integrity_ok:
        res["g0"]["adjudicable"] = False
        write_json_atomic(P["committed"] / f"dmio-{model}_gate_summary.json", res)
        raise StageError(f"G0 integrity failed: {res['g0']['integrity']}")
    qt = question_table(test_runs)
    qt_cal = question_table(cal_runs)
    groups = {"known": [q for q, v in qt.items() if v["knowledge"] == "known"]}
    for g in ("unknown_true", "known_recognized", "recognition_ambiguous"):
        groups[g] = [q for q in qt if group_of.get(q) == g]
    groups["dmcc_unknown_all"] = [q for q, v in qt.items() if v["knowledge"] == "unknown"]
    fl = gates["g0_floors"]
    known_floor = len(groups["known"]) >= fl["min_test_known"]
    ut_floor = len(groups["unknown_true"]) >= fl["min_test_unknown_true"]
    res["g0"]["floors"] = {"test_known_questions": len(groups["known"]),
                           "test_unknown_true_questions": len(groups["unknown_true"]),
                           "known_met": known_floor, "unknown_true_met": ut_floor}
    res["g0"]["adjudicable"] = True
    r0_ok = bool(fz["r0"]["valid"])
    ge3 = int(gates["h1_idk_recall"]["secondary_majority_positions"])

    def qblock(g: str) -> dict:
        qs = groups[g]
        return {"idk_rate": cluster_mean_ci([qt[q]["idk_rate"] for q in qs], reps, seed),
                f"share_idk_in_ge{ge3}_positions": rate(sum(sum(qt[q]["idk_by_position"].values()) >= ge3
                                                            for q in qs), len(qs))}

    # ---- H1 / H2 (question-level, cluster bootstrap)
    g1, g2 = gates["h1_idk_recall"], gates["h2_over_idk"]
    b1, b2 = qblock("unknown_true"), qblock("known")
    v1 = three_way(b1["idk_rate"]["ci95"], g1["threshold"], "at_least") if (r0_ok and ut_floor) else na
    v2 = three_way(b2["idk_rate"]["ci95"], g2["threshold"], "at_most") if known_floor else na
    res["gates"]["h1"] = {"verdict": v1, "threshold": g1["threshold"], **b1}
    res["gates"]["h2"] = {"verdict": v2, "threshold": g2["threshold"], **b2}
    im = gates["interpretation_matrix"]
    cell = {("PASS", "PASS"): im["h1_pass_and_h2_pass"], ("PASS", "FAIL"): im["h1_pass_and_h2_fail"],
            ("FAIL", "PASS"): im["h1_fail_and_h2_pass"], ("FAIL", "FAIL"): im["h1_fail_and_h2_fail"]}.get(
        (v1, v2), f"unresolved (H1 {v1}, H2 {v2})")
    res["interpretation"] = cell
    # ---- H3
    if not (r0_ok and ut_floor and known_floor):
        res["gates"]["h3"] = {"verdict": na, "reason": "R0 / floors"}
    else:
        res["gates"]["h3"] = h3_compare(qt, qt_cal, no_test, no_cal, group_of, gates, reps, seed)
    # ---- H4 (descriptive, question-level)
    h4 = {}
    for g in ("known_recognized", "recognition_ambiguous"):
        qs = groups[g]
        h4[g] = {**qblock(g),
                 "answered_accuracy": cluster_mean_ci([qt[q]["answered_accuracy"] for q in qs], reps, seed)}
    res["gates"]["h4"] = {"verdict": "DESCRIPTIVE" if r0_ok else na, **h4}

    # ---- secondary (descriptive)
    sec: dict = {"per_group": {}}
    for g, qs in groups.items():
        sec["per_group"][g] = {
            "n_questions": len(qs), **qblock(g),
            "picked_idk": cluster_mean_ci([qt[q]["idk_rate"] for q in qs], reps, seed),
            "answered_right": cluster_mean_ci([qt[q]["right_share"] for q in qs], reps, seed),
            "answered_wrong": cluster_mean_ci([qt[q]["wrong_share"] for q in qs], reps, seed),
            "answered_accuracy": cluster_mean_ci([qt[q]["answered_accuracy"] for q in qs], reps, seed),
            "mean_p_idk_r1": cluster_mean_ci([qt[q]["mean_p_idk_r1"] for q in qs], reps, seed)}
    sec["unknown_true_breakdown"] = {k: sec["per_group"]["unknown_true"][k]
                                     for k in ("picked_idk", "answered_right", "answered_wrong")}
    known, ut = groups["known"], groups["unknown_true"]
    if known and ut and qt[known[0]]["mean_p_idk_r1"] is not None:
        y = [0] * len(known) + [1] * len(ut)
        s = [qt[q]["mean_p_idk_r1"] for q in known + ut]
        sec["idk_distribution_calibration"] = {"auroc_p_idk_unknown_true_vs_known": auroc(y, s),
                                               "ci95": bootstrap_auroc_ci(y, s, reps, seed),
                                               "ece_binary_15": ece_binary(s, y, 15)}
    strong = float(gates["secondary_descriptive"]["position_bias"]["strong_range"])
    pos_groups = {"pooled": list(qt), **{g: groups[g] for g in ("known", "unknown_true", "known_recognized",
                                                                  "recognition_ambiguous")}}
    sec["position_bias"] = position_table(qt, pos_groups, positions, strong)
    sec["position_bias_caveat_h1_h2"] = [g for g in ("pooled", "known", "unknown_true")
                                        if sec["position_bias"][g]["strong_position_effect"]]
    no_by = {r["meta"]["qid"]: r for r in no_test}
    sec["answer_change_vs_noidk"] = {}
    for g, qs in groups.items():
        changed = answered = 0
        for q in qs:
            for k, pred in qt[q]["preds"].items():
                if pred == k:
                    continue
                answered += 1
                changed += int((pred - (1 if pred > k else 0)) != int(no_by[q]["pred"]))
        sec["answer_change_vs_noidk"][g] = rate(changed, answered)
    known_conf = sorted(no_by[q]["conf_r1"] for q in known)
    curve = []
    if known_conf and ut:
        for qd in np.linspace(0.1, 0.9, 9):
            tau = float(np.quantile(known_conf, qd))
            curve.append({"tau": tau, "over_abstention_known": float(np.mean([x < tau for x in known_conf])),
                          "recall_unknown_true": float(np.mean([no_by[q]["conf_r1"] < tau for q in ut]))})
        sec["test_matched_comparison"] = test_matched_descriptive(qt, no_test, group_of, reps, seed)
    sec["threshold_curve"] = curve
    dm = {r["meta"]["qid"]: r for r in read_jsonl(dmcc_file(c, m["dmcc_test_rows"]))}
    both = [q for q in no_by if q in dm]
    sec["reproduction_vs_dmcc"] = {
        "n_shared": len(both),
        "pred_agreement": float(np.mean([no_by[q]["pred"] == dm[q]["pred"] for q in both])) if both else None,
        "max_abs_conf_r1_diff": float(max(abs(no_by[q]["conf_r1"] - dm[q]["conf_r1"]) for q in both)) if both else None}
    res["secondary"] = sec
    write_json_atomic(P["score"] / f"dmio-{model}_verdicts.json", res)
    write_json_atomic(P["committed"] / f"dmio-{model}_gate_summary.json", res)  # aggregates only, no text
    print(json.dumps({k: v.get("verdict") for k, v in res["gates"].items()}, indent=2))
    print(f"interpretation: {cell}")
    if sec["position_bias_caveat_h1_h2"]:
        print(f"position-bias caveat (range >= {strong}): {sec['position_bias_caveat_h1_h2']}")


# --------------------------------------------------------------------------
# plan (registered real-mode dry run) + CLI
# --------------------------------------------------------------------------


def stage_plan(c: dict, args) -> None:
    P = paths(c)
    print(f"repo root: {REPO_ROOT}")
    try:
        print(f"engine HEAD: {git_head(TUNER_DIR)} (pinned {c['engine']['commit']})")
    except Exception as exc:  # noqa: BLE001 - plan only reports
        print(f"engine HEAD: unresolved ({exc})")
    root = host_abs(c["predecessor"]["root"])
    for key, spec in c["predecessor"]["files"].items():
        src = root / spec["path"]
        print(f"[import-dmcc] {key}: {src} ({'present' if src.exists() else 'ABSENT'}) -> {dmcc_file(c, key)}")
    outs_idk = [idk_rows_path(c, int(k)) for k in c["idk_option"]["positions"]]
    for name, outs in (("build-recognition", [P["rec_items"]]), ("recognize", [P["rec_log"]]),
                       ("recognition-labels", [P["rec_labels"], P["rec_freeze"]]),
                       ("build-idk-rows", outs_idk)):
        print(f"[{name}] " + "; ".join(f"{o.relative_to(REPO_ROOT)}: {'present' if o.exists() else 'absent'}"
                                       for o in outs))
    print("[recognize] argv:", " ".join(runner_argv(c, worker_inner(P["rec_items"], P["rec_log"]), "<image id>")))
    for key in run_keys(c):
        r = run_spec(c, key)
        print(f"[stage-engine/analyze/collect --run {key}] staging {staging_dir(c, r)}; "
              f"analyze argv: {' '.join(analyze_argv(c, r))}")
    print(f"[engine runs] {len(run_keys(c))} total")
    print("[score] --model pointer (PRIMARY) | --model letter_logits (SECONDARY)")
    print("plan: nothing computed")


STAGES = {
    "plan": stage_plan, "import-dmcc": stage_import_dmcc, "build-recognition": stage_build_recognition,
    "recognize-smoke": stage_recognize_smoke, "recognize": stage_recognize,
    "recognize-worker": stage_recognize_worker, "recognition-labels": stage_recognition_labels,
    "build-idk-rows": stage_build_idk_rows, "stage-engine": stage_engine, "analyze": stage_analyze,
    "collect": stage_collect, "score": stage_score,
}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("stage", choices=list(STAGES))
    ap.add_argument("--run", default=None,
                    help="engine run key idk_p<k>_<model> or noidk_<model> (stage-engine/analyze/collect)")
    ap.add_argument("--model", default="pointer", choices=["pointer", "letter_logits"], help="score")
    ap.add_argument("--items", default=None, help="recognize-worker only")
    ap.add_argument("--out", default=None, help="recognize-worker only")
    ap.add_argument("--i-know-this-runs-on-gpu", action="store_true")
    args = ap.parse_args(argv)
    if args.stage in GPU_STAGES and not args.i_know_this_runs_on_gpu:
        print(f"{args.stage} uses a GPU; pass --i-know-this-runs-on-gpu after launch approval")
        return 2
    try:
        STAGES[args.stage](cfg(), args)
    except StageError as exc:
        print(f"{args.stage}: REFUSED: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
