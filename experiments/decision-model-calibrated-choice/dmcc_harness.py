#!/usr/bin/env python3
"""Harness for decision-model-calibrated-choice (pinned at `bin/exp sign`).

Location: experiments/decision-model-calibrated-choice/dmcc_harness.py
Config:   experiments/decision-model-calibrated-choice/cell.yaml (every knob)
Gates:    experiments/decision-model-calibrated-choice/gates.yaml

Stages, in the only order the harness allows (each refuses if its inputs are
missing; GPU stages also require --i-know-this-runs-on-gpu):

  build-pool       CPU  PopQA test.tsv @ pinned revision -> EH probe pool + meta
  stage-model      CPU  stage the labeler snapshot @ pinned revision; write the
                        MATERIALIZED probe config (model_name -> snapshot dir)
  label            GPU  EH instrument, unchanged:
                        experiments/common/knowledge_probe/probe.py --config <materialized>
                        (vLLM venv; resumable append-log)
  convert          CPU  probe results -> 4-way decision `choice` rows (same-relation
                        distractors, meta.knowledge / meta.s_pop), plus the FIT/CAL/TEST
                        split the engine will draw (exact port, verified after the run)
  stage0-rows      CPU  FIT+CAL known/unknown rows -> extraction shards + FIT labels
  stage0-extract   GPU  `tuner.py mechinterp extract` per shard, inside the pinned
                        mechinterp-runner image (shard-level resume)
  stage0-fit       CPU  `tuner.py mechinterp probe-fit` x3 (gate, dial, permuted gate)
  stage0-validate  CPU  CAL AUROC / permuted control / calibration; writes the
                        FREEZE MARKER (sha256 of every frozen direction)
  stage-engine     CPU  copy rows + checkpoint + analysis config into the tuner's
                        gitignored scratch/eh_staging/<run_id>/; verify digests;
                        write the run record BEFORE any launch
  analyze          GPU  `py.exe -3.11 tuner.py local-run --job-config <recipe> --yes`
                        (engine CLI Trainers/decision/analyze_confidence.py);
                        refuses without the Stage 0 freeze marker
  collect          CPU  copy engine outputs into analysis/engine/<run_id>/
  score            CPU  gates.yaml adjudication -> verdict JSON + committed summary

`plan` prints every stage's resolved inputs/outputs and the exact GPU argv
without computing anything (the registered real-mode dry run).

Containment: question text, generations, hidden states and row-level outputs
stay under the gitignored analysis/ and directions/ dirs. Only aggregates and
run records are written under analysis-committed/.

No-pollution: the tuner is reached only through public CLI verbs
(`mechinterp extract`, `mechinterp probe-fit`, `local-run`) and materialized
YAML; the only tuner-tree write is ephemeral staging under its gitignored
scratch/eh_staging/.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import random
import shutil
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
CELL_CONFIG = HERE / "cell.yaml"
KP_DIR = REPO_ROOT / "experiments" / "common" / "knowledge_probe"
TUNER_DIR = REPO_ROOT / "synaptic-tuner"

GPU_STAGES = {"label", "stage0-extract", "analyze"}


# --------------------------------------------------------------------------
# small utilities (stdlib only at import time: the extraction container
# imports this module for render/content_end)
# --------------------------------------------------------------------------


def _yaml_load(path: Path) -> dict:
    import yaml

    return yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}


def _yaml_dump(data: dict, path: Path) -> None:
    import yaml

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")


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
    """A gitdir pointer as this host sees it: 'F:/x' -> '/mnt/f/x' under WSL;
    relative pointers resolve against the directory holding the .git file."""
    if len(p) > 2 and p[1] == ":" and p[2] in "/\\" and os.name != "nt":
        return Path("/mnt/" + p[0].lower() + "/" + p[3:].replace("\\", "/"))
    q = Path(p)
    return q if q.is_absolute() else (base / q)


def _read_head(path: Path) -> str:
    """Resolve HEAD without the git CLI. Needed under WSL, where a worktree created
    from Windows has a .git pointer `gitdir: F:/...` that Linux git cannot follow
    (pre-sign drill 2026-10-04)."""
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


class StageError(RuntimeError):
    pass


def cfg() -> dict:
    return _yaml_load(CELL_CONFIG)


def paths(c: dict) -> dict[str, Path]:
    a = rp(c["paths"]["analysis_root"])
    return {
        "analysis": a,
        "committed": rp(c["paths"]["committed_root"]),
        "run_records": rp(c["paths"]["run_records"]),
        "popqa": a / "popqa",
        "probe_pool": a / "popqa" / "probe_pool.jsonl",
        "popqa_meta": a / "popqa" / "popqa_meta.jsonl",
        "kp": a / "knowledge_probe",
        "probe_materialized": a / "knowledge_probe" / "probe.materialized.yaml",
        "rows_primary": a / "decision_rows" / "decision_rows_primary.jsonl",
        "splits": a / "decision_rows" / "splits.json",
        "stage0": a / "stage0",
        "engine": a / "engine",
        "score": a / "score",
    }


def probe_results_path(c: dict) -> Path:
    pc = _yaml_load(rp(c["labeler"]["probe_config"]))
    return rp(pc["output"]["root"]) / pc["model"]["model_tag"] / pc["output"]["results_filename"]


def require(path: Path, what: str) -> Path:
    if not path.exists():
        raise StageError(f"missing {what}: {path} (run the earlier stage first)")
    return path


# --------------------------------------------------------------------------
# Stage 0 plug-ins: render + content_end (imported by `mechinterp extract`
# inside the runner container via PYTHONPATH; render_fn dmcc_harness:render)
# --------------------------------------------------------------------------

_RENDER_STATE: dict = {}


def _render_state() -> dict:
    """Labeling surface from probe.yaml (prompt.surface), resolved by the SAME
    EH backends functions probe.py's VLLMBackend uses, so labeling and Stage 0
    extraction render byte-identical prompts."""
    if not _RENDER_STATE:
        if str(KP_DIR) not in sys.path:
            sys.path.insert(0, str(KP_DIR))
        import backends

        pc = _yaml_load(HERE / "probe.yaml")
        surface = backends.resolve_prompt_surface(pc)
        _RENDER_STATE.update(backends=backends, surface=surface, pc=pc)
        if surface == "chat":
            from transformers import AutoTokenizer

            _RENDER_STATE["tok"] = AutoTokenizer.from_pretrained(pc["model"]["model_name"],
                                                                 revision=pc["model"]["model_revision"])
    return _RENDER_STATE


def render(row: dict) -> str:
    """Byte-identical to the labeling prompt. Under prompt.surface base_kshot
    (this cell): Amendment Y's 5-shot block via backends.build_base_mode_prompt,
    no chat template, no system prompt. Under chat: render_probe_prompt."""
    st = _render_state()
    question = row.get("question")
    if not question:
        raise KeyError(f"row {row.get('row_key')!r} has no question")
    if st["surface"] == "base_kshot":
        return st["backends"].build_base_mode_prompt(question)
    text, _mode = st["backends"].render_probe_prompt(
        st["tok"], st["pc"]["prompt"]["system"], question,
        enable_thinking=bool(st["pc"]["model"].get("enable_thinking", False)))
    return text


def content_end(full_ids, prompt_len: int, tokenizer) -> int:
    """Index of the last content token of the greedy answer (the dial read).

    base_kshot (this cell): Amendment Y's first-line rule, vendored from
    amendment_x_cross_model_extract._first_line_content_end. Decode the
    continuation token by token (skip_special_tokens) and stop before the first
    token whose incremental decode introduces a newline, then trim trailing
    specials. This is the same answer the labeler scores (the first line).
    chat: the last non-special, non-whitespace token of the whole completion.

    If no content token exists, return prompt_len. extract only captures a row
    when content_end >= prompt_len, so the anchor (gate) capture is kept for
    every row. Such a row's answer_end tensor sits on a non-content token and
    is EXCLUDED from every dial fit and statistic (see _answered_keys).
    """
    ids = full_ids.tolist() if hasattr(full_ids, "tolist") else list(full_ids)
    special = set(getattr(tokenizer, "all_special_ids", []) or [])
    if _render_state()["surface"] == "base_kshot":
        n = len(ids)
        end, prev = n - 1, ""
        for i in range(prompt_len, n):
            cur = tokenizer.decode(ids[prompt_len:i + 1], skip_special_tokens=True)
            if "\n" in cur[len(prev):]:
                end = i - 1
                break
            prev = cur
        while end >= prompt_len and int(ids[end]) in special:
            end -= 1
        return end if end >= prompt_len else int(prompt_len)
    i = len(ids) - 1
    while i >= prompt_len:
        t = int(ids[i])
        if t in special or not tokenizer.decode([t]).strip():
            i -= 1
            continue
        return i
    return int(prompt_len)


# --------------------------------------------------------------------------
# build-pool
# --------------------------------------------------------------------------


def _normalize_answer():
    if str(KP_DIR) not in sys.path:
        sys.path.insert(0, str(KP_DIR))
    from scoring import normalize_answer  # EH scorer's alias normalizer

    return normalize_answer


def stage_build_pool(c: dict, args) -> None:
    from huggingface_hub import hf_hub_download

    d = c["dataset"]
    P = paths(c)
    tsv = Path(hf_hub_download(d["hf_id"], d["filename"], repo_type="dataset", revision=d["revision"]))
    digest = sha256_file(tsv)
    if digest != d["file_sha256"]:
        raise StageError(f"PopQA digest {digest} != pinned {d['file_sha256']}")
    with open(tsv, encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh, delimiter="\t"))
    if len(rows) != d["expected_rows"]:
        raise StageError(f"PopQA rows {len(rows)} != {d['expected_rows']}")
    props = {r["prop"] for r in rows}
    if len(props) != d["expected_relations"]:
        raise StageError(f"PopQA relations {len(props)} != {d['expected_relations']}")
    norm = _normalize_answer()
    pool, meta = [], []
    for r in rows:
        qid = f"{d['question_id_prefix']}{r['id']}"
        aliases = [str(a) for a in json.loads(r["possible_answers"])]
        normed = list(dict.fromkeys(n for n in (norm(a) for a in aliases) if n))
        if not normed:
            raise StageError(f"{qid}: no normalizable alias")
        pool.append({"question": r["question"], "question_id": qid,
                     "answer": {"normalized_aliases": normed, "value": r["obj"]}})
        meta.append({"qid": qid, "question": r["question"], "prop": r["prop"], "subj": r["subj"],
                     "obj": r["obj"], "aliases": aliases, "s_pop": int(r["s_pop"])})
    if len({m["qid"] for m in meta}) != len(meta):
        raise StageError("PopQA ids are not unique")
    pool_sha = write_jsonl_atomic(P["probe_pool"], pool)
    meta_sha = write_jsonl_atomic(P["popqa_meta"], meta)
    write_json_atomic(P["popqa"] / "build_pool_manifest.json", {
        "built_at": now_utc(), "source": f"{d['hf_id']}@{d['revision']}/{d['filename']}",
        "source_sha256": digest, "n_rows": len(pool), "n_relations": len(props),
        "probe_pool_sha256": pool_sha, "popqa_meta_sha256": meta_sha,
        "alias_normalizer": "experiments/common/knowledge_probe/scoring.py:normalize_answer"})
    print(f"build-pool: {len(pool):,} rows over {len(props)} relations -> {P['probe_pool']}")


# --------------------------------------------------------------------------
# stage-model + label (EH knowledge probe, unchanged)
# --------------------------------------------------------------------------


def stage_model(c: dict, args) -> None:
    from huggingface_hub import snapshot_download

    lab = c["labeler"]
    P = paths(c)
    snap = Path(snapshot_download(lab["hf_id"], revision=lab["revision"]))
    if snap.name != lab["revision"]:
        raise StageError(f"snapshot dir {snap.name} is not the pinned revision {lab['revision']}")
    pc = _yaml_load(rp(lab["probe_config"]))
    if pc["model"].get("model_revision") != lab["revision"]:
        raise StageError("probe.yaml model_revision disagrees with cell.yaml labeler.revision")
    pc["model"]["model_name"] = snap.as_posix()
    _yaml_dump(pc, P["probe_materialized"])
    write_json_atomic(P["kp"] / "stage_model_record.json", {
        "staged_at": now_utc(), "hf_id": lab["hf_id"], "revision": lab["revision"],
        "snapshot_dir": snap.as_posix(), "probe_yaml_sha256": sha256_file(rp(lab["probe_config"])),
        "materialized_sha256": sha256_file(P["probe_materialized"])})
    print(f"stage-model: {snap} -> {P['probe_materialized']}")


def label_argv(c: dict) -> tuple[list[str], dict]:
    lab = c["labeler"]
    P = paths(c)
    argv = [lab["python"], str(rp(lab["probe_entrypoint"])), "--config", str(P["probe_materialized"])]
    env = {**os.environ, **{k: str(v) for k, v in (lab.get("env") or {}).items()}}
    return argv, env


def stage_label(c: dict, args) -> None:
    P = paths(c)
    require(P["probe_pool"], "probe pool")
    require(P["probe_materialized"], "materialized probe config")
    argv, env = label_argv(c)
    record = P["kp"] / "label_run.json"
    write_json_atomic(record, {"launched_at": now_utc(), "argv": argv,
                               "env_overrides": c["labeler"].get("env"),
                               "research_repo_commit": git_head(REPO_ROOT), "status": "launched"})
    rc = subprocess.run(argv, cwd=str(REPO_ROOT), env=env).returncode
    results = probe_results_path(c)
    rows = read_jsonl(results) if results.exists() else []
    gen = marker_summary(rows)
    bound = float(_yaml_load(rp(c["scoring"]["gates"]))["g0_label_marker_bound"]["max_marked_rate"])
    flagged = gen["marked_rate"] > bound
    write_json_atomic(record, {**json.loads(record.read_text(encoding="utf-8")), "finished_at": now_utc(),
                               "returncode": rc, "n_results": len(rows),
                               "generated_thinking": gen, "marker_rate_bound": bound,
                               "marker_rate_flag": flagged,
                               "status": "completed" if rc == 0 else "failed"})
    if rc != 0:
        raise StageError(f"probe.py exited {rc}; rerun `label` to resume from the append-log")
    print(f"label: {len(rows):,} probe rows at {results}; thinking-marker rate "
          f"{gen['marked_rate']:.4f} (bound {bound})" + ("  FLAGGED: consult the PI" if flagged else ""))


def marker_summary(rows: list[dict]) -> dict:
    """Run-level count_wrong policy totals over probe rows (same fields as the
    probe manifest's generated_thinking block)."""
    n_samples = sum(int(r.get("n_samples", 0)) for r in rows)
    n_s = sum(int(r.get("n_sampled_thinking_marker", 0)) for r in rows)
    n_g = sum(1 for r in rows if r.get("greedy_thinking_marker"))
    n_gen = n_samples + len(rows)
    return {"n_questions": len(rows),
            "n_questions_affected": sum(1 for r in rows if r.get("n_sampled_thinking_marker", 0)
                                        or r.get("greedy_thinking_marker")),
            "n_sampled_marked": n_s, "n_greedy_marked": n_g, "n_generations": n_gen,
            "marked_rate": (n_s + n_g) / n_gen if n_gen else 0.0}


# --------------------------------------------------------------------------
# convert (port of the tuner-side build_choice_rows) + engine split port
# --------------------------------------------------------------------------


def _split_by_task(rows: list[dict], val_fraction: float, seed: int) -> tuple[list[dict], list[dict]]:
    """Exact port of synaptic-tuner decision_core.examples.split_by_task @ 29f7af0c
    (same RNG calls in the same order). Verified after the engine run by the
    G0 split-identity check; never trusted on its own."""
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
    """Port of confidence_analysis.split_fit_cal_test @ 29f7af0c."""
    rest, fit_rows = _split_by_task(rows, fit, seed)
    test_rows, cal_rows = _split_by_task(rest, cal / (1.0 - fit), seed + 1)
    return fit_rows, cal_rows, test_rows


def build_choice_rows(meta: list[dict], probe: dict[str, dict], ch: dict, label_map: dict,
                      n_samples: int, cfg_sha: str) -> tuple[list[dict], Counter, Counter]:
    """Gold + (n_options-1) same-relation distractors whose normalized text
    matches no gold alias. Port of the tuner-side build_choice_rows; the only
    changes are EH's alias normalizer and EH label names."""
    norm = _normalize_answer()
    by_prop: dict[str, set] = defaultdict(set)
    for m in meta:
        by_prop[m["prop"]].add(m["obj"])
    rng = random.Random(ch["seed"])
    rows: list[dict] = []
    counts: Counter = Counter()
    skipped: Counter = Counter()
    for m in meta:  # PopQA file order
        pr = probe[m["qid"]]
        knowledge = label_map[pr["label"]]
        counts[knowledge] += 1
        if knowledge == "ambiguous" and not ch["include_ambiguous_in_primary"]:
            skipped["ambiguous_excluded"] += 1
            continue
        gold_norm = {norm(a) for a in m["aliases"]} | {norm(m["obj"])}
        candidates = sorted(o for o in by_prop[m["prop"]] if norm(o) not in gold_norm)
        if len(candidates) < ch["n_options"] - 1:
            skipped["too_few_distractors"] += 1
            continue
        options = rng.sample(candidates, ch["n_options"] - 1) + [m["obj"]]
        rng.shuffle(options)
        rows.append({
            "kind": "choice", "state": m["question"], "instructions": ch["instructions"],
            "options": [[o, ""] for o in options], "label": options.index(m["obj"]),
            "task": f"popqa:{m['prop']}", "weight": 1.0, "instruction_variants": [],
            "meta": {"qid": m["qid"], "knowledge": knowledge, "greedy_correct": bool(pr["greedy_correct"]),
                     "p_correct": float(pr["p_correct"]),
                     "n_sampled_correct": int(round(float(pr["p_correct"]) * n_samples)),
                     "n_samples": n_samples, "s_pop": int(m["s_pop"]), "prop": m["prop"],
                     "source": "popqa", "probe_config_sha": cfg_sha,
                     "n_sampled_thinking_marker": int(pr.get("n_sampled_thinking_marker", 0)),
                     "greedy_thinking_marker": bool(pr.get("greedy_thinking_marker", False))},
        })
    return rows, counts, skipped


def stage_convert(c: dict, args) -> None:
    P = paths(c)
    lr = P["kp"] / "label_run.json"
    if lr.exists() and json.loads(lr.read_text(encoding="utf-8")).get("marker_rate_flag"):
        ack = P["committed"] / "pi_marker_rate_ack.json"
        if not ack.exists():
            raise StageError("thinking-marker rate exceeded the registered bound (gates.yaml "
                             "g0_label_marker_bound); the PI must be consulted and the decision "
                             f"recorded in {ack} before Stage 0 or Stage 1 proceed")
    meta = read_jsonl(require(P["popqa_meta"], "PopQA meta"))
    results = read_jsonl(require(probe_results_path(c), "probe results"))
    probe = {r["question_id"]: r for r in results}
    if len(probe) != len(meta) or set(probe) != {m["qid"] for m in meta}:
        raise StageError(f"probe covers {len(probe)} of {len(meta)} PopQA rows; finish `label` first")
    shas = {r["probe_config_sha"] for r in results}
    if len(shas) != 1:
        raise StageError(f"probe rows carry {len(shas)} probe_config_sha values: {sorted(shas)}")
    pc = _yaml_load(rp(c["labeler"]["probe_config"]))
    rows, counts, skipped = build_choice_rows(meta, probe, c["choices"], c["labeler"]["label_map"],
                                              int(pc["sampling"]["n_samples"]), shas.pop())
    rows_sha = write_jsonl_atomic(P["rows_primary"], rows)
    acfg = _yaml_load(rp(c["models"]["pointer"]["analysis_config"]))["data"]
    fit, cal, test = engine_split(rows, acfg["fit_fraction"], acfg["cal_fraction"], acfg["seed"])
    split = {name: [r["meta"]["qid"] for r in part] for name, part in
             (("fit", fit), ("cal", cal), ("test", test))}
    by = {name: dict(Counter(r["meta"]["knowledge"] for r in part)) for name, part in
          (("fit", fit), ("cal", cal), ("test", test))}
    write_json_atomic(P["splits"], {"rows_sha256": rows_sha, "split_port": "synaptic-tuner@29f7af0c "
                                    "decision_core split_fit_cal_test", "fractions": acfg,
                                    "counts": {k: len(v) for k, v in split.items()},
                                    "knowledge_by_split": by, "qids": split})
    summary = {"converted_at": now_utc(), "rows_sha256": rows_sha, "n_rows_primary": len(rows),
               "label_counts_all": dict(counts), "skipped": dict(skipped),
               # Registered sensitivity (count_wrong policy): label counts with every
               # question that had any thinking-marked generation dropped.
               "label_counts_drop_marker_affected": dict(Counter(
                   c["labeler"]["label_map"][probe[q]["label"]] for q in probe
                   if not (probe[q].get("n_sampled_thinking_marker", 0) or probe[q].get("greedy_thinking_marker")))),
               "marker_summary": marker_summary(results),
               # Pre-stated descriptive check (AMENDMENT "Labels"): the Amendment Y
               # exemplar answer "Au" equals the PopQA alias "AU" (Australia) on 27
               # country questions; count first-line answers that are exactly "au"
               # on rows whose aliases include it (a possible exemplar echo scored
               # correct).
               "exemplar_echo_au": {
                   "rows_with_alias_au": sum(1 for r in results if "au" in r["normalized_aliases"]),
                   "greedy_answer_exactly_au": sum(1 for r in results if "au" in r["normalized_aliases"]
                                                   and _normalize_answer()(r["greedy_answer"]) == "au"),
                   "sampled_answers_exactly_au": sum(sum(_normalize_answer()(a) == "au" for a in r["sampled_answers"])
                                                     for r in results if "au" in r["normalized_aliases"])},
               "knowledge_by_split": by,
               "per_relation": {p: dict(Counter(r["meta"]["knowledge"] for r in rows if r["meta"]["prop"] == p))
                                for p in sorted({r["meta"]["prop"] for r in rows})}}
    write_json_atomic(P["analysis"] / "decision_rows" / "convert_manifest.json", summary)
    # Aggregate counts only (no text) are committed.
    write_json_atomic(P["committed"] / "label_and_split_counts.json",
                      {k: v for k, v in summary.items() if k != "rows_sha256"} | {"rows_sha256": rows_sha})
    print(f"convert: {len(rows):,} primary rows; labels {dict(counts)}; splits {by}")


# --------------------------------------------------------------------------
# Stage 0: extraction -> probe-fit -> validate/freeze
# --------------------------------------------------------------------------


def _safe_key(rk: str) -> str:
    return rk.replace("::", "__").replace("|", "_").replace("/", "_")  # = MechInterp extraction naming


def stage0_rows(c: dict, args) -> None:
    P = paths(c)
    s0 = c["stage0"]
    rows = {r["meta"]["qid"]: r for r in read_jsonl(require(P["rows_primary"], "decision rows"))}
    split = json.loads(require(P["splits"], "splits").read_text(encoding="utf-8"))
    out = P["stage0"]
    fitcal, labels_fit, labels_cal = [], [], []
    for name in ("fit", "cal"):
        for qid in split["qids"][name]:
            r = rows[qid]
            lab = 1 if r["meta"]["knowledge"] == "known" else 0
            fitcal.append({"row_key": qid, "question": r["state"], "label": lab, "split": name})
            (labels_fit if name == "fit" else labels_cal).append({"row_key": qid, "label": lab})
    perm = [x["label"] for x in labels_fit]
    random.Random(s0["permutation_seed"]).shuffle(perm)
    labels_perm = [{"row_key": x["row_key"], "label": y} for x, y in zip(labels_fit, perm)]
    write_jsonl_atomic(out / "rows_fitcal.jsonl", fitcal)
    write_jsonl_atomic(out / "labels_fit.jsonl", labels_fit)
    write_jsonl_atomic(out / "labels_cal.jsonl", labels_cal)
    write_jsonl_atomic(out / "labels_fit_permuted.jsonl", labels_perm)
    template = _yaml_load(rp(s0["extract_recipe"]))
    shard_dir = out / "shards"
    size = int(s0["shard_size"])
    n_shards = 0
    for k in range(0, len(fitcal), size):
        idx = k // size
        shard_rows = out / "shards" / f"rows_{idx:03d}.jsonl"
        write_jsonl_atomic(shard_rows, fitcal[k:k + size])
        shard_cfg = dict(template)
        shard_cfg["rows_path"] = shard_rows.relative_to(REPO_ROOT).as_posix()
        _yaml_dump(shard_cfg, shard_dir / f"extract_{idx:03d}.yaml")
        n_shards += 1
    floors = _yaml_load(rp(c["scoring"]["gates"]))["s0_floors"]
    counts = {"fit_known": sum(x["label"] for x in labels_fit), "fit_unknown": sum(1 - x["label"] for x in labels_fit),
              "cal_known": sum(x["label"] for x in labels_cal), "cal_unknown": sum(1 - x["label"] for x in labels_cal)}
    ok = (counts["fit_known"] >= floors["min_fit_known"] and counts["fit_unknown"] >= floors["min_fit_unknown"]
          and counts["cal_known"] >= floors["min_cal_known"] and counts["cal_unknown"] >= floors["min_cal_unknown"])
    write_json_atomic(out / "stage0_rows_manifest.json", {"counts": counts, "n_shards": n_shards,
                                                          "s0_floors_met": ok})
    print(f"stage0-rows: {len(fitcal):,} FIT+CAL rows in {n_shards} shards; {counts}; floors met: {ok}")


def _runner_image_id(c: dict) -> str:
    tag = c["stage0"]["runtime"]["image_tag"]
    out = subprocess.run(list(c["stage0"]["runtime"]["docker_cli"]) + ["image", "inspect", tag, "--format", "{{.Id}}"],
                         capture_output=True, text=True)
    if out.returncode != 0:
        raise StageError(f"runner image {tag} not found; build it per cell.yaml stage0.runtime")
    return out.stdout.strip()


def _pinned_runtime_digest() -> str | None:
    m = _yaml_load(HERE / "experiment.yaml")
    return (m.get("instrument") or {}).get("runtime_image_digest")


def runner_argv(c: dict, inner: list[str], gpu: bool, image_id: str, name: str | None = None) -> list[str]:
    rt = c["stage0"]["runtime"]
    argv = list(rt["docker"]) if gpu else [x for x in rt["docker"] if x not in ("--gpus", "all")]
    if name:
        argv += ["--name", name]
    argv += ["-v", os.path.expandvars(rt["hf_cache_mount"]), "-v", f"{REPO_ROOT}:{rt['workdir_in_container']}",
             "-w", rt["workdir_in_container"], "--env", f"IMAGE_DIGEST={image_id}",
             "--env", f"PYTHONPATH={rt['pythonpath']}", "--env", "HF_TOKEN", rt["image_tag"]]
    return argv + inner


def _check_image(c: dict) -> str:
    image_id = _runner_image_id(c)
    pinned = _pinned_runtime_digest()
    if not pinned:
        raise StageError("experiment.yaml instrument.runtime_image_digest is unset; pin it pre-sign")
    if image_id != pinned:
        raise StageError(f"runner image {image_id} != pinned runtime_image_digest {pinned}")
    return image_id


def stage0_extract_argvs(c: dict, image_id: str) -> list[tuple[int, list[str]]]:
    lab = c["labeler"]
    out = []
    for cfg_path in sorted((paths(c)["stage0"] / "shards").glob("extract_*.yaml")):
        idx = int(cfg_path.stem.split("_")[1])
        inner = ["python", "synaptic-tuner/tuner.py", "mechinterp", "extract",
                 "--mi-config", cfg_path.relative_to(REPO_ROOT).as_posix(),
                 "--model", lab["hf_id"], "--model-revision", lab["revision"],
                 "--i-know-this-runs-on-gpu"]
        out.append((idx, runner_argv(c, inner, gpu=True, image_id=image_id, name=shard_container(c, idx))))
    return out


def shard_container(c: dict, idx: int) -> str:
    """Deterministic container name per shard. A killed harness can leave its
    `docker run` container alive (killing the CLI client does not stop it), so a
    resumed shard first force-removes any container of the same name: no
    orphan may still be writing into the shared output dir."""
    tag = hashlib.sha256(str(rp(_yaml_load(rp(c["stage0"]["extract_recipe"]))["output_dir"])).encode()).hexdigest()[:8]
    return f"dmcc-stage0-{tag}-shard{idx:03d}"


def stage0_extract(c: dict, args) -> None:
    P = paths(c)
    require(P["stage0"] / "stage0_rows_manifest.json", "stage0 rows")
    image_id = _check_image(c)
    ext_dir = rp(_yaml_load(rp(c["stage0"]["extract_recipe"]))["output_dir"])
    logs = P["stage0"] / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    # The harness user must own the output dir: the container runs as root, and
    # a root-created dir on the host mount is not writable for the shard
    # markers (kill-resume drill 2026-10-04).
    ext_dir.mkdir(parents=True, exist_ok=True)
    if not os.access(ext_dir, os.W_OK):
        raise StageError(f"{ext_dir} is not writable by the harness user (created by the container?); "
                         "move it aside and rerun")
    for idx, argv in stage0_extract_argvs(c, image_id):
        marker = ext_dir / f"manifest_shard_{idx:03d}.json"
        if marker.exists():
            print(f"stage0-extract: shard {idx:03d} done, skipping")
            continue
        subprocess.run(list(c["stage0"]["runtime"]["docker_cli"]) + ["rm", "-f", shard_container(c, idx)],
                       capture_output=True)
        log = logs / f"extract_{idx:03d}.log"
        with open(log, "w", encoding="utf-8") as fh:
            rc = subprocess.run(argv, cwd=str(REPO_ROOT), stdout=fh, stderr=subprocess.STDOUT).returncode
        text = log.read_text(encoding="utf-8", errors="replace")
        if rc != 0:
            raise StageError(f"shard {idx:03d} extract exited {rc}; see {log}")
        if "mechinterp_runner_provenance" not in text:
            raise StageError(f"shard {idx:03d}: runner provenance line missing from {log}")
        # Copy, do not rename: the container writes manifest.json as root on the
        # host mount, which the harness user may not rename (kill-resume drill
        # 2026-10-04). The marker is written atomically by the harness user; the
        # next shard's container overwrites manifest.json.
        tmp = marker.with_suffix(".json.tmp")
        tmp.write_bytes((ext_dir / "manifest.json").read_bytes())
        os.replace(tmp, marker)
        print(f"stage0-extract: shard {idx:03d} complete")


def stage0_fit(c: dict, args) -> None:
    P = paths(c)
    require(P["stage0"] / "stage0_rows_manifest.json", "stage0 rows")
    rows = read_jsonl(P["stage0"] / "rows_fitcal.jsonl")
    ext_dir = rp(_yaml_load(rp(c["stage0"]["extract_recipe"]))["output_dir"])
    n_shards = json.loads((P["stage0"] / "stage0_rows_manifest.json").read_text())["n_shards"]
    missing = [k for k in range(n_shards) if not (ext_dir / f"manifest_shard_{k:03d}.json").exists()]
    if missing:
        raise StageError(f"extraction incomplete; shards missing: {missing}")
    image_id = _check_image(c)
    # Dial labels: FIT rows whose greedy answer has content (answer_end is a real token).
    answered = _answered_keys(ext_dir)
    fit_labels = read_jsonl(P["stage0"] / "labels_fit.jsonl")
    write_jsonl_atomic(P["stage0"] / "labels_fit_dial.jsonl", [r for r in fit_labels if r["row_key"] in answered])
    rp(c["stage0"]["directions_dir"]).mkdir(parents=True, exist_ok=True)
    for name, recipe in c["stage0"]["probe_fit_recipes"].items():
        inner = ["python", "synaptic-tuner/tuner.py", "mechinterp", "probe-fit", "--mi-config", recipe]
        log = P["stage0"] / "logs" / f"probe_fit_{name}.log"
        with open(log, "w", encoding="utf-8") as fh:
            rc = subprocess.run(runner_argv(c, inner, gpu=False, image_id=image_id), cwd=str(REPO_ROOT),
                                stdout=fh, stderr=subprocess.STDOUT).returncode
        if rc != 0:
            raise StageError(f"probe-fit {name} exited {rc}; see {log}")
        print(f"stage0-fit: {name} frozen ({len(rows):,} FIT+CAL rows extracted)")


def _answered_keys(ext_dir: Path) -> set[str]:
    """Row keys whose greedy answer is non-empty under the labeling parse (the
    first line under base_kshot, as the labeler scores it; the whole completion
    under chat), across all shard manifests."""
    first_line = _render_state()["surface"] == "base_kshot"
    keys: set[str] = set()
    for mf in sorted(ext_dir.glob("manifest_shard_*.json")):
        for r in json.loads(mf.read_text(encoding="utf-8"))["rows"]:
            text = str(r.get("answer_text", ""))
            if (text.split("\n", 1)[0] if first_line else text).strip():
                keys.add(str(r["row_key"]))
    return keys


def _load_family_layer(ext_dir: Path, row_keys: list[str], family: str, layer: int):
    import numpy as np
    from safetensors.numpy import load_file

    X, keep = [], []
    for rk in row_keys:
        f = ext_dir / f"{_safe_key(rk)}__{family}.safetensors"
        if not f.exists():
            continue
        X.append(load_file(str(f))[f"L{layer}"][0])
        keep.append(rk)
    return (np.stack(X).astype("float64") if X else np.zeros((0, 0))), keep


def stage0_validate(c: dict, args) -> None:
    import numpy as np

    P = paths(c)
    s0, gates = c["stage0"], _yaml_load(rp(c["scoring"]["gates"]))
    sc = c["scoring"]
    ext_dir = rp(_yaml_load(rp(s0["extract_recipe"]))["output_dir"])
    ddir = rp(s0["directions_dir"])
    dirs = {n: json.loads((ddir / f"direction_{n}.json").read_text()) for n in ("gate", "dial", "gate_permuted")}
    fit = read_jsonl(P["stage0"] / "labels_fit.jsonl")
    cal = read_jsonl(P["stage0"] / "labels_cal.jsonl")
    y_of = {r["row_key"]: r["label"] for r in fit + cal}
    answered = _answered_keys(ext_dir)
    rep: dict = {"validated_at": now_utc(), "directions": {}}
    for name, fam in (("gate", "anchor"), ("dial", "answer_end"), ("gate_permuted", "anchor")):
        d = dirs[name]
        v = np.asarray(d["vector"], dtype=np.float64)
        keys = [r["row_key"] for r in cal if fam != "answer_end" or r["row_key"] in answered]
        Xc, kc = _load_family_layer(ext_dir, keys, fam, d["layer"])
        yc = np.array([y_of[k] for k in kc])
        sc_cal = Xc @ v
        auc = auroc(yc, sc_cal)
        lo, hi = bootstrap_auroc_ci(yc, sc_cal, sc["bootstrap_reps"], sc["bootstrap_seed"])
        rep["directions"][name] = {
            "layer": d["layer"], "family": fam, "cal_auroc": auc, "cal_auroc_ci95": [lo, hi],
            "cal_rows_with_capture": len(kc), "cal_rows": len(cal),
            "fit_cv_auroc_at_layer": d["provenance"]["auroc_by_layer"].get(str(d["layer"]),
                                                                          d["provenance"]["auroc_by_layer"].get(d["layer"])),
            "mu_norm": float(np.linalg.norm(np.asarray(d["mu"]))), "sigma": d["sigma"],
            "class_stats": d["calibration"], "sha256": sha256_file(ddir / f"direction_{name}.json")}
    # permuted control at the GATE's frozen layer (CV surface of the permuted fit)
    gl = dirs["gate"]["layer"]
    surf = dirs["gate_permuted"]["provenance"]["auroc_by_layer"]
    perm_cv_at_gate_layer = surf.get(str(gl), surf.get(gl))
    # descriptive calibration of the gate readout (maps fit on FIT, ECE on CAL)
    d = dirs["gate"]
    coef = np.asarray(d["vector"], dtype=np.float64) * float(d["raw_norm"])
    Xf, kf = _load_family_layer(ext_dir, [r["row_key"] for r in fit], "anchor", gl)
    Xc, kc = _load_family_layer(ext_dir, [r["row_key"] for r in cal], "anchor", gl)
    f_fit, f_cal = Xf @ coef + d["intercept"], Xc @ coef + d["intercept"]
    y_fit, y_cal = np.array([y_of[k] for k in kf]), np.array([y_of[k] for k in kc])
    rep["gate_calibration_descriptive"] = calibration_block(f_fit, y_fit, f_cal, y_cal, s0["calibration"]["ece_bins"])
    # gates
    g1, g2, fl = gates["s0_g1_gate_validity"], gates["s0_g2_permuted_control"], gates["s0_floors"]
    cnt = {"cal_known": int(y_cal.sum()), "cal_unknown": int((1 - y_cal).sum()),
           "fit_known": int(y_fit.sum()), "fit_unknown": int((1 - y_fit).sum())}
    floors_ok = (cnt["cal_known"] >= fl["min_cal_known"] and cnt["cal_unknown"] >= fl["min_cal_unknown"]
                 and cnt["fit_known"] >= fl["min_fit_known"] and cnt["fit_unknown"] >= fl["min_fit_unknown"])
    gate_d = rep["directions"]["gate"]
    v1 = three_way(gate_d["cal_auroc_ci95"], g1["threshold"], "at_least") if floors_ok else "NOT-ADJUDICABLE"
    band = g2["pass_band"]
    perm_cal = rep["directions"]["gate_permuted"]["cal_auroc"]
    v2 = "PASS" if (band[0] <= perm_cv_at_gate_layer <= band[1] and band[0] <= perm_cal <= band[1]) else "FAIL"
    anchor_cov = gate_d["cal_rows_with_capture"] / max(1, gate_d["cal_rows"])
    ans_cov = rep["directions"]["dial"]["cal_rows_with_capture"] / max(1, rep["directions"]["dial"]["cal_rows"])
    integ = gates["s0_extraction_integrity"]
    integrity_ok = anchor_cov >= integ["anchor_family_coverage_min"] and ans_cov >= integ["answer_end_family_coverage_min"]
    rep["gates"] = {"s0_floors": {"counts": cnt, "met": floors_ok},
                    "s0_extraction_integrity": {"anchor_cal_coverage": anchor_cov, "answer_end_cal_coverage": ans_cov,
                                                "ok": integrity_ok},
                    "s0_g1_gate_validity": v1 if integrity_ok else "NOT-ADJUDICABLE",
                    "s0_g2_permuted_control": {"verdict": v2, "fit_cv_auroc_at_gate_layer": perm_cv_at_gate_layer,
                                               "cal_auroc": perm_cal}}
    rep["h_d1_adjudicable"] = bool(rep["gates"]["s0_g1_gate_validity"] == "PASS" and v2 == "PASS")
    write_json_atomic(P["stage0"] / "stage0_report.json", rep)
    # Committed aggregates + the FREEZE MARKER (direction digests). Written once.
    marker = rp(s0["freeze_marker"])
    if marker.exists():
        prior = json.loads(marker.read_text(encoding="utf-8"))
        now = {n: rep["directions"][n]["sha256"] for n in rep["directions"]}
        if prior["direction_sha256"] != now:
            raise StageError("frozen directions changed after the freeze marker was written; refusing")
    write_json_atomic(marker, {"frozen_at": now_utc(), "research_repo_commit": git_head(REPO_ROOT),
                               "engine_commit": git_head(TUNER_DIR),
                               "direction_sha256": {n: rep["directions"][n]["sha256"] for n in rep["directions"]},
                               "summary": {n: {k: v for k, v in rep["directions"][n].items() if k != "class_stats"}
                                           for n in rep["directions"]},
                               "gates": rep["gates"], "h_d1_adjudicable": rep["h_d1_adjudicable"],
                               "gate_calibration_descriptive": rep["gate_calibration_descriptive"]})
    print(f"stage0-validate: gate CAL AUROC {gate_d['cal_auroc']:.4f} {gate_d['cal_auroc_ci95']} "
          f"-> S0-G1 {rep['gates']['s0_g1_gate_validity']}; S0-G2 {v2}; freeze marker {marker}")


# --------------------------------------------------------------------------
# Stage 1: stage-engine / analyze / collect
# --------------------------------------------------------------------------


def _model(c: dict, args) -> dict:
    m = dict(c["models"][args.model])
    if args.source_checkpoint:
        m["source_checkpoint"] = args.source_checkpoint
    if args.expect_tree_sha256:
        m["tree_sha256"] = args.expect_tree_sha256
    if not m.get("source_checkpoint") or not m.get("tree_sha256"):
        raise StageError(f"model {args.model}: pass --source-checkpoint and --expect-tree-sha256 "
                         "(recorded in the NOTEBOOK first)")
    return m


def staging_dir(c: dict, m: dict) -> Path:
    return TUNER_DIR / c["engine"]["staging_root"] / m["run_id"]


def run_record_path(c: dict, m: dict) -> Path:
    return paths(c)["run_records"] / f"{m['run_id']}.json"


def analyze_argv(c: dict, m: dict) -> list[str]:
    return list(c["engine"]["launcher"]) + [to_windows_path(rp(m["recipe"])), "--yes"]


def frozen_direction_files(c: dict) -> dict[str, tuple[Path, str]]:
    """{direction_<name>.json: (path, frozen sha256)} for every Stage 0 direction.
    Refuses if the freeze marker is missing or any file differs from it."""
    marker = rp(c["stage0"]["freeze_marker"])
    if not marker.exists():
        raise StageError("Stage 0 freeze marker missing: the base KU directions must be frozen "
                         "before any decision-model analysis (AMENDMENT Stage 0)")
    frozen = json.loads(marker.read_text(encoding="utf-8"))["direction_sha256"]
    out = {}
    for name, sha in frozen.items():
        path = rp(c["stage0"]["directions_dir"]) / f"direction_{name}.json"
        if sha256_file(path) != sha:
            raise StageError(f"{path.name} differs from its frozen digest")
        out[path.name] = (path, sha)
    return out


def check_staged_directions(c: dict, m: dict) -> None:
    """Every `directions:` entry of the analysis config must resolve to a staged
    file whose bytes equal the frozen Stage 0 direction of the same file name,
    with no layer override (the frozen layer is the registered layer)."""
    frozen = frozen_direction_files(c)
    for d in _yaml_load(rp(m["analysis_config"])).get("directions") or []:
        staged = TUNER_DIR / d["path"]
        fname = Path(d["path"]).name
        if fname not in frozen:
            raise StageError(f"analysis direction {d['name']} -> {fname} is not a frozen Stage 0 direction")
        if not staged.exists() or sha256_file(staged) != frozen[fname][1]:
            raise StageError(f"staged {staged} missing or not the frozen bytes")
        if d.get("layer") is not None:
            raise StageError(f"direction {d['name']}: a layer override is not allowed (frozen layer only)")


def stage_engine(c: dict, args) -> None:
    m = _model(c, args)
    P = paths(c)
    src = Path(m["source_checkpoint"])
    got = tree_sha256(src)
    if got != m["tree_sha256"]:
        raise StageError(f"checkpoint tree digest {got} != expected {m['tree_sha256']}")
    head = git_head(TUNER_DIR)
    if head != c["engine"]["commit"]:
        raise StageError(f"synaptic-tuner HEAD {head} != pinned engine commit {c['engine']['commit']}")
    rows = require(P["rows_primary"], "decision rows")
    frozen = frozen_direction_files(c)  # refuses without the Stage 0 freeze marker
    sd = staging_dir(c, m)
    if sd.exists() and any(sd.iterdir()):
        raise StageError(f"staging dir {sd} not empty; move it aside (never overwritten)")
    sd.mkdir(parents=True)
    shutil.copytree(src, sd / "final_model")
    shutil.copy2(rows, sd / "decision_rows_primary.jsonl")
    (sd / "directions").mkdir()
    for fname, (path, _sha) in frozen.items():
        shutil.copy2(path, sd / "directions" / fname)
    check_staged_directions(c, m)
    acfg = rp(m["analysis_config"])
    shutil.copy2(acfg, sd / acfg.name)
    if tree_sha256(sd / "final_model") != m["tree_sha256"]:
        raise StageError("staged checkpoint digest mismatch after copy")
    rec = {
        "run_id": m["run_id"], "cell": "decision-model-calibrated-choice", "role": m["role"],
        "method": "decision", "engine_cli": c["engine"]["cli"], "lane": "local",
        "image": c["engine"]["image"], "source_recipe_in_engine": m["recipe_in_engine"],
        "materialized_recipe": m["recipe"], "materialized_recipe_sha256": sha256_file(rp(m["recipe"])),
        "analysis_config": m["analysis_config"], "analysis_config_sha256": sha256_file(acfg),
        "checkpoint": {"source": src.as_posix(), "tree_sha256": got, "tuner_run": m["tuner_run"]},
        "data": {"source_data_file": rows.relative_to(REPO_ROOT).as_posix(),
                 "staged_data_file": (sd / "decision_rows_primary.jsonl").relative_to(TUNER_DIR).as_posix(),
                 "hf_dataset_name": None, "hf_dataset_revision": None},
        "data_sha256": sha256_file(rows), "research_repo_commit": git_head(REPO_ROOT), "submodule_commit": head,
        "stage0_freeze_marker_sha256": (sha256_file(rp(c["stage0"]["freeze_marker"]))
                                        if rp(c["stage0"]["freeze_marker"]).exists() else None),
        "tuner_invocation": analyze_argv(c, m), "staged_at": now_utc(),
        "outcome": {"status": "staged", "metrics_path": None, "verified": False}}
    write_json_atomic(run_record_path(c, m), rec)
    print(f"stage-engine: staged {m['run_id']} at {sd}; run record {run_record_path(c, m)}")


def stage_analyze(c: dict, args) -> None:
    m = _model(c, args)
    frozen_direction_files(c)
    marker = rp(c["stage0"]["freeze_marker"])
    rr = run_record_path(c, m)
    rec = json.loads(require(rr, "run record (run stage-engine)").read_text(encoding="utf-8"))
    sd = staging_dir(c, m)
    if tree_sha256(sd / "final_model") != m["tree_sha256"] or \
            sha256_file(sd / "decision_rows_primary.jsonl") != rec["data_sha256"]:
        raise StageError("staged inputs changed since stage-engine; restage")
    check_staged_directions(c, m)
    if git_head(TUNER_DIR) != c["engine"]["commit"]:
        raise StageError("synaptic-tuner HEAD moved off the pinned engine commit")
    argv = analyze_argv(c, m)
    rec["outcome"] = {"status": "launched", "launched_at": now_utc(), "metrics_path": None, "verified": False}
    rec["stage0_freeze_marker_sha256"] = sha256_file(marker)
    write_json_atomic(rr, rec)
    rc = subprocess.run(argv, cwd=str(TUNER_DIR)).returncode
    rec["outcome"].update({"status": "completed" if rc == 0 else "failed", "returncode": rc,
                           "finished_at": now_utc()})
    write_json_atomic(rr, rec)
    if rc != 0:
        raise StageError(f"local-run exited {rc}")
    print(f"analyze: {m['run_id']} completed; run `collect`")


def stage_collect(c: dict, args) -> None:
    m = _model(c, args)
    sd = staging_dir(c, m) / "output"
    runs = sorted(p for p in sd.glob("*") if (p / "confidence_report.json").exists())
    if not runs:
        raise StageError(f"no engine output under {sd}")
    src = runs[-1]
    dst = paths(c)["engine"] / m["run_id"] / src.name
    if dst.exists():
        raise StageError(f"{dst} already collected")
    shutil.copytree(src, dst)
    rr = run_record_path(c, m)
    rec = json.loads(rr.read_text(encoding="utf-8"))
    rec["outcome"].update({"metrics_path": dst.relative_to(REPO_ROOT).as_posix(),
                           "artifact_sha256": {p.name: sha256_file(p) for p in sorted(dst.iterdir()) if p.is_file()},
                           "collected_at": now_utc()})
    write_json_atomic(rr, rec)
    print(f"collect: {src} -> {dst}")


# --------------------------------------------------------------------------
# statistics (numpy only)
# --------------------------------------------------------------------------


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
    """Class-stratified row bootstrap, percentile 95%."""
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


def paired_auroc_diff_ci(y, a, b, reps: int, seed: int) -> dict:
    import numpy as np

    y = np.asarray(y, dtype=int)
    a, b = np.asarray(a, dtype=np.float64), np.asarray(b, dtype=np.float64)
    rng = np.random.default_rng(seed)
    pos, neg = np.flatnonzero(y == 1), np.flatnonzero(y == 0)
    diffs = []
    for _ in range(reps):
        idx = np.concatenate([rng.choice(pos, pos.size), rng.choice(neg, neg.size)])
        diffs.append(auroc(y[idx], a[idx]) - auroc(y[idx], b[idx]))
    lo, hi = np.quantile(diffs, [0.025, 0.975])
    return {"diff": auroc(y, a) - auroc(y, b), "ci95": [float(lo), float(hi)]}


def bootstrap_mean_ci(x, reps: int, seed: int) -> list[float]:
    import numpy as np

    x = np.asarray(x, dtype=np.float64)
    rng = np.random.default_rng(seed)
    means = [x[rng.integers(0, x.size, x.size)].mean() for _ in range(reps)]
    lo, hi = np.quantile(means, [0.025, 0.975])
    return [float(lo), float(hi)]


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


def _ece(p, y, bins: int) -> float:
    import numpy as np

    p, y = np.asarray(p, dtype=np.float64), np.asarray(y, dtype=np.float64)
    edges = np.linspace(0, 1, bins + 1)
    tot = 0.0
    for i in range(bins):
        m = (p >= edges[i]) & ((p < edges[i + 1]) if i < bins - 1 else (p <= edges[i + 1]))
        if m.any():
            tot += m.mean() * abs(p[m].mean() - y[m].mean())
    return float(tot)


def calibration_block(f_fit, y_fit, f_cal, y_cal, bins: int) -> dict:
    """Platt (logistic on the probe logit, C=1e6) and isotonic (clip), as in
    experiments/common/mechinterp/fit_calibration.py; fit on FIT, ECE on CAL."""
    import numpy as np
    from sklearn.isotonic import IsotonicRegression
    from sklearn.linear_model import LogisticRegression

    sig = lambda x: 1.0 / (1.0 + np.exp(-x))  # noqa: E731
    platt = LogisticRegression(C=1e6, max_iter=2000).fit(np.asarray(f_fit).reshape(-1, 1), y_fit)
    iso = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0).fit(sig(np.asarray(f_fit)), y_fit)
    p_raw = sig(np.asarray(f_cal))
    return {"ece_bins": bins, "cal_ece_raw_sigmoid": _ece(p_raw, y_cal, bins),
            "cal_ece_platt": _ece(platt.predict_proba(np.asarray(f_cal).reshape(-1, 1))[:, 1], y_cal, bins),
            "cal_ece_isotonic": _ece(iso.predict(p_raw), y_cal, bins),
            "platt": {"a": float(platt.coef_[0, 0]), "b": float(platt.intercept_[0])}}


# --------------------------------------------------------------------------
# score
# --------------------------------------------------------------------------


def _lac_set(p, qhat: float) -> list[int]:
    import numpy as np

    p = np.asarray(p, dtype=np.float64)
    members = [int(k) for k in np.flatnonzero(1.0 - p <= qhat)]
    best = int(np.argmax(p))
    return sorted(set(members) | {best})


def stage_score(c: dict, args) -> None:
    import numpy as np

    m = _model(c, args)
    P = paths(c)
    gates = _yaml_load(rp(c["scoring"]["gates"]))
    reps, seed = c["scoring"]["bootstrap_reps"], c["scoring"]["bootstrap_seed"]
    rr = json.loads(require(run_record_path(c, m), "run record").read_text(encoding="utf-8"))
    out_dir = rp(require(rp(rr["outcome"]["metrics_path"] or "__missing__"), "collected engine output"))
    report = json.loads((out_dir / "confidence_report.json").read_text(encoding="utf-8"))
    test = read_jsonl(out_dir / "test_rows.jsonl")
    split = json.loads(P["splits"].read_text(encoding="utf-8"))
    res: dict = {"run_id": m["run_id"], "role": m["role"], "scored_at": now_utc(), "g0": {}, "gates": {}}

    # ---- G0 integrity
    g0 = gates["g0_integrity"]
    test_qids = [r["meta"]["qid"] for r in test]
    split_ok = (sorted(test_qids) == sorted(split["qids"]["test"])
                and report["n_rows"] == {k: len(v) for k, v in split["qids"].items()})
    amb_ok = all(r["meta"]["knowledge"] in ("known", "unknown") for r in test)
    commit_ok = rr["submodule_commit"] == g0["engine_commit"]
    ckpt_ok = rr["checkpoint"]["tree_sha256"] == g0[f"{args.model}_checkpoint_tree_sha256"]
    res["g0"]["integrity"] = {"split_identity": split_ok, "ambiguous_excluded": amb_ok,
                              "engine_commit": commit_ok, "checkpoint_digest": ckpt_ok}
    integrity_ok = split_ok and amb_ok and commit_ok and ckpt_ok
    know = np.array([r["meta"]["knowledge"] == "known" for r in test])
    unk = ~know
    conf = np.array([r["conf_r1"] for r in test], dtype=np.float64)
    ok = np.array([r["correct"] for r in test], dtype=int)
    chance = np.array([1.0 / r["n_options"] for r in test])
    fl = gates["g0_floors"]
    floors_ok = know.sum() >= fl["min_test_known"] and unk.sum() >= fl["min_test_unknown"]
    res["g0"]["floors"] = {"test_known": int(know.sum()), "test_unknown": int(unk.sum()), "met": bool(floors_ok)}
    adjudicable = integrity_ok and floors_ok
    na = "NOT-ADJUDICABLE"

    # ---- H-A
    ga = gates["h_a_unknowns_near_chance"]
    gap = conf[unk] - chance[unk]
    a1_ci = bootstrap_mean_ci(gap, reps, seed)
    cw = int(((conf[unk] >= c_thr("confident", c, m)) & (ok[unk] == 0)).sum())
    a2_ci = wilson(cw, int(unk.sum()))
    a1 = three_way(a1_ci, ga["a1_confidence_over_chance"]["threshold"], "at_most")
    a2 = three_way(a2_ci, ga["a2_confident_wrong"]["threshold"], "at_most")
    ha = "PASS" if a1 == a2 == "PASS" else ("FAIL" if "FAIL" in (a1, a2) else "INCONCLUSIVE")
    res["gates"]["h_a"] = {"verdict": ha if adjudicable else na,
                           "a1": {"gap": float(gap.mean()), "ci95": a1_ci, "verdict": a1},
                           "a2": {"rate": cw / max(1, int(unk.sum())), "k": cw, "n": int(unk.sum()),
                                  "wilson95": a2_ci, "verdict": a2},
                           "companions": {"unknown_accuracy": float(ok[unk].mean()),
                                          "unknown_accuracy_wilson95": wilson(int(ok[unk].sum()), int(unk.sum())),
                                          "mean_r1_unknown": float(conf[unk].mean())}}
    # ---- H-B
    gb = gates["h_b_knowns_confident"]
    ucr = int(((conf[know] < c_thr("underconfident", c, m)) & (ok[know] == 1)).sum())
    b_ci = wilson(ucr, int(know.sum()))
    kacc = float(ok[know].mean())
    hb = three_way(b_ci, gb["threshold"], "at_most")
    if kacc < gb["diagnosticity_precondition"]["known_accuracy_point_min"]:
        hb = na
    res["gates"]["h_b"] = {"verdict": hb if adjudicable else na, "rate": ucr / max(1, int(know.sum())),
                           "k": ucr, "n": int(know.sum()), "wilson95": b_ci,
                           "companions": {"known_accuracy": kacc, "mean_r1_known": float(conf[know].mean()),
                                          "underconfident_among_right": ucr / max(1, int(ok[know].sum()))}}
    # ---- H-C
    y_ku = know.astype(int)
    hc_auc = auroc(y_ku, conf)
    hc_ci = bootstrap_auroc_ci(y_ku, conf, reps, seed)
    hc = three_way(hc_ci, gates["h_c_readout_separates"]["threshold"], "at_least")
    res["gates"]["h_c"] = {"verdict": hc if adjudicable else na, "auroc": hc_auc, "ci95": hc_ci,
                           "engine_point": report.get("knowledge", {}).get("readout_auroc_known_vs_unknown")}
    # ---- H-D2 (engine paired bootstrap)
    kb = report.get("knowledge", {})
    gd2 = gates["h_d2_fresh_probe_beats_readout"]
    d2 = kb.get("ku_probe_minus_readout")
    perm = kb.get("ku_probe", {}).get("permuted_label_cv_auroc")
    margin, band = float(gd2["pass_margin"]), gd2["permuted_band"]
    if d2 is None or perm is None or not (band[0] <= perm <= band[1]):
        hd2 = na
    else:
        lo, hi = d2["ci95"]
        hd2 = "PASS" if (d2["diff"] >= margin and lo > 0) else ("FAIL" if hi < margin else "INCONCLUSIVE")
    d2_auc = kb.get("ku_probe", {}).get("test_auroc_known_vs_unknown")
    res["gates"]["h_d2"] = {"verdict": hd2 if adjudicable else na, "engine": d2, "permuted_label_cv_auroc": perm,
                            "ku_probe_test_auroc": d2_auc, "best_layer": kb.get("ku_probe", {}).get("best_layer")}
    if test and test[0].get("ku_probe_score") is not None:
        s2 = np.array([r["ku_probe_score"] for r in test], dtype=np.float64)
        res["gates"]["h_d2"]["in_cell_auroc_ci95"] = bootstrap_auroc_ci(y_ku, s2, reps, seed)
        res["gates"]["h_d2"]["in_cell_minus_readout"] = paired_auroc_diff_ci(y_ku, s2, conf, reps, seed)
    # ---- H-D1 (frozen base gate direction scored by the engine on decision <answer> states)
    gd1 = gates["h_d1_base_axis_transfer"]
    marker = json.loads(rp(c["stage0"]["freeze_marker"]).read_text(encoding="utf-8"))
    dname = gd1["engine_direction"]
    eng = report.get("directions", {}).get(dname)
    frozen_layer = marker["summary"]["gate"]["layer"]
    if not marker.get("h_d1_adjudicable"):
        res["gates"]["h_d1"] = {"verdict": na, "reason": "Stage 0 validity gate (S0-G1/S0-G2) did not pass"}
    elif eng is None or not test or dname not in (test[0].get("direction_scores") or {}):
        res["gates"]["h_d1"] = {"verdict": na, "reason": f"engine report/rows lack direction {dname!r}"}
    elif int(eng["layer"]) != int(frozen_layer):
        res["gates"]["h_d1"] = {"verdict": na, "reason": f"engine scored layer {eng['layer']} != frozen {frozen_layer}"}
    else:
        s1 = np.array([r["direction_scores"][dname] for r in test], dtype=np.float64)
        d1_auc, d1_ci = auroc(y_ku, s1), bootstrap_auroc_ci(y_ku, s1, reps, seed)
        if abs(d1_auc - float(eng["auroc_known_vs_unknown"])) > 1e-6:
            raise StageError(f"in-cell H-D1 AUROC {d1_auc} != engine {eng['auroc_known_vs_unknown']}")
        hd1 = three_way(d1_ci, gd1["threshold"], "at_least")
        perm_eng = report["directions"].get(gd1["control_direction"], {})
        res["gates"]["h_d1"] = {"verdict": hd1 if adjudicable else na, "layer": eng["layer"], "auroc": d1_auc,
                                "ci95": d1_ci,
                                "minus_readout_engine": eng.get("auroc_known_vs_unknown_minus_r1"),
                                "minus_readout_in_cell": paired_auroc_diff_ci(y_ku, s1, conf, reps, seed),
                                "by_knowledge": eng.get("by_knowledge"),
                                "permuted_control_auroc_descriptive": perm_eng.get("auroc_known_vs_unknown")}
    # ---- interpretation matrix (fixed reading; INCONCLUSIVE stays unresolved)
    v_d1, v_c = res["gates"]["h_d1"]["verdict"], res["gates"]["h_c"]["verdict"]
    d2_high = d2_auc is not None and d2_auc >= float(gd2["d2_high_threshold"])
    im = gates["interpretation_matrix"]
    if v_d1 == "PASS" and v_c == "PASS":
        cell = im["d1_pass_and_hc_pass"]
    elif v_d1 == "PASS" and v_c == "FAIL":
        cell = im["d1_pass_and_hc_fail"]
    elif v_d1 == "FAIL":
        cell = im["d1_fail_and_d2_high"] if d2_high else im["d1_fail_and_d2_low"]
    else:
        cell = f"unresolved (H-D1 {v_d1}, H-C {v_c})"
    res["interpretation"] = {"cell": cell, "d2_high_point": bool(d2_high)}
    # ---- secondary (descriptive)
    sec: dict = {"popularity_quartiles": kb.get("by_popularity_quartile"),
                 "recall_vs_recognition": {"unknown_correct_rate": float(ok[unk].mean()),
                                           "wilson95": wilson(int(ok[unk].sum()), int(unk.sum())),
                                           "chance": 0.25},
                 "arms": {k: v for k, v in report.get("arms", {}).items()},
                 "per_relation": {}}
    for prop in sorted({r["meta"]["prop"] for r in test}):
        for lab, mask in (("known", know), ("unknown", unk)):
            sel = np.array([r["meta"]["prop"] == prop for r in test]) & mask
            if sel.any():
                sec["per_relation"].setdefault(prop, {})[lab] = {"n": int(sel.sum()), "accuracy": float(ok[sel].mean()),
                                                                 "mean_r1": float(conf[sel].mean())}
    if test and "probs_r1" in test[0]:
        conf_rep = report.get("conformal", {})
        sec["conformal_by_knowledge"] = {}
        for key, block in conf_rep.items():
            qhat = block["qhat_by_kind"]["choice"]
            for lab, mask in (("known", know), ("unknown", unk)):
                idx = np.flatnonzero(mask)
                sets = [_lac_set(test[i]["probs_r1"], qhat) for i in idx]
                sec["conformal_by_knowledge"].setdefault(key, {})[lab] = {
                    "coverage": float(np.mean([test[i]["gold"] in s for i, s in zip(idx, sets)])),
                    "mean_set_size": float(np.mean([len(s) for s in sets]))}
    else:
        sec["conformal_by_knowledge"] = "NOT-COMPUTED (engine emitted no per-row option probabilities)"
    # Registered sensitivity (count_wrong policy): the readout statistics with
    # every question that had any thinking-marked generation dropped.
    aff = np.array([bool(r["meta"].get("n_sampled_thinking_marker", 0) or r["meta"].get("greedy_thinking_marker"))
                    for r in test])
    keep = ~aff
    kk, uu = know & keep, unk & keep
    sens = {"n_test_affected": int(aff.sum()), "n_known_kept": int(kk.sum()), "n_unknown_kept": int(uu.sum())}
    if kk.any() and uu.any():
        sens.update({
            "h_a_gap": float((conf[uu] - chance[uu]).mean()),
            "h_a_confident_wrong": float(((conf[uu] >= c_thr("confident", c, m)) & (ok[uu] == 0)).mean()),
            "h_b_underconfident_right": float(((conf[kk] < c_thr("underconfident", c, m)) & (ok[kk] == 1)).mean()),
            "h_c_auroc": auroc(know[keep].astype(int), conf[keep]),
        })
        if "s1" in locals():
            sens["h_d1_auroc"] = auroc(know[keep].astype(int), s1[keep])
    sec["thinking_marker_sensitivity"] = sens
    res["secondary"] = sec
    res["g0"]["adjudicable"] = bool(adjudicable)
    write_json_atomic(P["score"] / f"{m['run_id']}_verdicts.json", res)
    write_json_atomic(P["committed"] / f"{m['run_id']}_gate_summary.json", res)  # aggregates only, no text
    print(json.dumps({k: (v.get("verdict") if isinstance(v, dict) else v) for k, v in res["gates"].items()}, indent=2))
    print(f"interpretation: {cell}")


def c_thr(name: str, c: dict, m: dict) -> float:
    return float(_yaml_load(rp(m["analysis_config"]))["thresholds"][name])


# --------------------------------------------------------------------------
# plan (registered real-mode dry run) + CLI
# --------------------------------------------------------------------------


def stage_plan(c: dict, args) -> None:
    P = paths(c)
    print(f"repo root: {REPO_ROOT}")
    print(f"engine HEAD: {git_head(TUNER_DIR)} (pinned {c['engine']['commit']})")
    items = [("build-pool", [P["probe_pool"], P["popqa_meta"]]),
             ("stage-model", [P["probe_materialized"]]),
             ("label", [probe_results_path(c)]),
             ("convert", [P["rows_primary"], P["splits"]]),
             ("stage0-rows", [P["stage0"] / "stage0_rows_manifest.json"]),
             ("stage0-extract", [rp(_yaml_load(rp(c["stage0"]["extract_recipe"]))["output_dir"])]),
             ("stage0-fit", [rp(c["stage0"]["directions_dir"]) / f"direction_{n}.json"
                             for n in ("gate", "dial", "gate_permuted")]),
             ("stage0-validate", [rp(c["stage0"]["freeze_marker"])])]
    for name, outs in items:
        print(f"[{name}] " + "; ".join(f"{o.relative_to(REPO_ROOT)}: {'present' if o.exists() else 'absent'}"
                                       for o in outs))
    print("[label] argv:", " ".join(label_argv(c)[0]))
    print("[stage0-extract] per-shard argv: docker run ... ", c["stage0"]["runtime"]["image_tag"],
          "python synaptic-tuner/tuner.py mechinterp extract --mi-config <shard> --model",
          c["labeler"]["hf_id"], "--model-revision", c["labeler"]["revision"], "--i-know-this-runs-on-gpu")
    for key, m in c["models"].items():
        print(f"[stage-engine/analyze/collect/score --model {key}] staging "
              f"{staging_dir(c, m)}; analyze argv: {' '.join(analyze_argv(c, m))}")
    print("plan: nothing computed")


STAGES = {
    "plan": stage_plan, "build-pool": stage_build_pool, "stage-model": stage_model, "label": stage_label,
    "convert": stage_convert, "stage0-rows": stage0_rows, "stage0-extract": stage0_extract,
    "stage0-fit": stage0_fit, "stage0-validate": stage0_validate, "stage-engine": stage_engine,
    "analyze": stage_analyze, "collect": stage_collect, "score": stage_score,
}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("stage", choices=list(STAGES))
    ap.add_argument("--model", default="pointer", choices=["pointer", "letter_logits"])
    ap.add_argument("--source-checkpoint", default=None)
    ap.add_argument("--expect-tree-sha256", default=None)
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
