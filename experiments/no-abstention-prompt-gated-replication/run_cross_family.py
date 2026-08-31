#!/usr/bin/env python3
"""llama-3.2-3b and mistral-7b-v0.3 arms: no-abstention-prompt gated
replication. Both reuse the SAME parent lineage (j-space-cross-family-
layer-contrast), so one parametrized script covers both --family values.

Reused unmodified via direct import (no edits to any parent file):
  - experiments/j-space-cross-family-layer-contrast/model_lib.py
    (load_model_and_tokenizer, resolve_eos_ids, setup_hook_from_vector)
  - experiments/j-space-cross-family-layer-contrast/gen_lib.py
    (run_pass_fixed [family-aware eos_ids], grade_clean_tighten)
  - experiments/j-space-cross-family-layer-contrast/grader.py (grade_one)
  - experiments/j-space-cross-family-layer-contrast/gate_fit.py
    (youden_tau, roc_auc) -- same threshold-refit method as qwen3-4b's
    (mu_d/sigma_d frozen from the pinned build_manifest, only tau refit on
    fresh no-abstention-prompt FIT-split extraction).
  - THIS cell's own pinned render.py (no-abstention prompt, all families).

Row source: experiments/j-space-cross-family-layer-contrast/analysis/
<family>/eval_rows.jsonl (row_key, question, aliases, role, split) --
the SAME frozen parity-locked pool cell.yaml's heldout_pool cites (counts
verified against cell.yaml at preflight).

Anchor: forward pass over the rendered prompt alone, output_hidden_states,
use_cache=False, hidden_states[hs_index][0, prompt_len-1, :]. Same
definition as the parent's anchor_extract_manifest.json ("prompt_len-1").

Arms: llama runs no_op, gated, random_direction (matched-dose, generated at
run time via the LOCKED recipe from llama-hs17-direction-specificity/
run_specificity.py: np.random.RandomState(seed).normal(size=hidden_dim),
unit-normalized, seed=910016 -- pinned in cell.yaml as the next value in
that census's seed series). Mistral runs no_op, gated only (cell.yaml
arms list; mistral has no established direction-specificity per
rr3-corrected-placebo-replication, and this cell does not relitigate that).
"""

from __future__ import annotations

import argparse
import gc
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import torch
import yaml

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
CROSS_DIR = REPO_ROOT / "experiments" / "j-space-cross-family-layer-contrast"
sys.path.insert(0, str(CROSS_DIR))
sys.path.insert(0, str(HERE))

import model_lib as ml  # noqa: E402  (cross-family, reused unmodified)
import gen_lib as gl  # noqa: E402
import grader  # noqa: E402
import gate_fit  # noqa: E402  (reuse youden_tau/roc_auc only)

CELL = yaml.safe_load((HERE / "cell.yaml").read_text())

TUNER_DIR = REPO_ROOT / "synaptic-tuner"
sys.path.insert(0, str(TUNER_DIR))
from shared.utilities.run_log import RunLog  # noqa: E402

FAMILY_KEY = {"llama-3.2-3b": "llama-3.2-3b", "mistral-7b-v03": "mistral-7b-v0.3"}
RANDOM_DIRECTION_SEED = {"llama-3.2-3b": 910016}  # llama only; mistral has no random_direction arm


def _sanitize_key(row_key: str) -> str:
    return row_key.replace(":", "_").replace("::", "_")


def load_jsonl(p: Path) -> list[dict]:
    return [json.loads(ln) for ln in p.open(encoding="utf-8") if ln.strip()]


class Family:
    def __init__(self, family_dirname: str):
        self.dirname = family_dirname  # e.g. "llama-3.2-3b" or "mistral-7b-v03" (parent's on-disk dirname)
        self.cell_key = FAMILY_KEY[family_dirname]  # cell.yaml key (mistral uses a dot)
        self.fam_cfg = CELL["families"][self.cell_key]
        self.hs_index = int(self.fam_cfg["site"].replace("hs", ""))
        self.decoder_block_index = int(self.fam_cfg["decoder_block_index"])
        self.dose_abs = float(self.fam_cfg["dose_abs"])
        self.model_repo = self.fam_cfg["model"]
        self.arms = ["no_op", "gated"] + (["random_direction"] if self.dirname in RANDOM_DIRECTION_SEED else [])

        self.analysis = HERE / "analysis" / self.cell_key
        self.analysis.mkdir(parents=True, exist_ok=True)
        self.runlog_dir = self.analysis / "runlog"
        self.runlog_dir.mkdir(parents=True, exist_ok=True)

        self.eval_rows_path = CROSS_DIR / "analysis" / self.dirname / "eval_rows.jsonl"
        build_manifest = json.loads((REPO_ROOT / self.fam_cfg["build_manifest"]["path"]).read_text())
        self.hidden_dim = build_manifest["hidden_dim"]
        layer = build_manifest["layers"][self.fam_cfg["site"]]
        self.mu_d = layer["mu_d"]
        self.sigma_d = layer["sigma_d"]

        os.environ["DOUBT_SNAP_RENDER_MODEL"] = self.model_repo
        global cell_render
        import render as cell_render  # noqa: F811  (re-import to pick up env var; cached module is fine since render() reads env per call via _tokenizer())

    def all_rows(self) -> list[dict]:
        rows = load_jsonl(self.eval_rows_path)
        return [r for r in rows if r["role"] in ("confab", "known_correct_answered")]

    def rows_for(self, split: str) -> list[dict]:
        return [r for r in self.all_rows() if r["split"] == split]

    def load_direction_vector(self, rel_path: str) -> np.ndarray:
        data = json.loads((REPO_ROOT / rel_path).read_text())
        return np.asarray(data["vector"], dtype=np.float64)

    def direction_and_sigma(self, arm: str):
        if arm in ("no_op", "gated"):
            path = self.fam_cfg["write_direction"]["path"]
            data = json.loads((REPO_ROOT / path).read_text())
            return np.asarray(data["vector"], dtype=np.float64), float(data.get("sigma", 1.0)), self.decoder_block_index
        if arm == "random_direction":
            seed = RANDOM_DIRECTION_SEED[self.dirname]
            rng = np.random.RandomState(seed)
            v = rng.normal(size=self.hidden_dim)
            v = v / np.linalg.norm(v)
            out_path = self.analysis / f"random_direction_seed{seed}.json"
            out_path.write_text(json.dumps({
                "schema_version": "mechinterp-direction/v1", "layer": self.decoder_block_index,
                "hidden_dim": self.hidden_dim, "normalized": True, "vector": v.tolist(),
                "sigma": 1.0, "recipe": {"source": "run_specificity.py random_unit_direction, LOCKED recipe", "seed": seed},
            }, indent=2))
            return v, 1.0, self.decoder_block_index
        raise ValueError(arm)


def cmd_extract(fam: Family) -> int:
    rows = fam.all_rows()
    print(f"[{fam.cell_key}:extract] {len(rows)} rows")
    model, tokenizer, hidden_size, num_hidden_layers = ml.load_model_and_tokenizer(fam.dirname)
    device = next(model.parameters()).device

    run_log = RunLog(
        fam.runlog_dir / "extract.jsonl",
        run_config={
            "family": fam.cell_key, "stage": "extract", "model": fam.model_repo,
            "site": fam.fam_cfg["site"], "prompt": cell_render.NO_ABSTENTION_SYSTEM_PROMPT,
        },
        key_field="row_key",
    )
    pending = list(run_log.iter_pending(rows, key_fn=lambda r: r["row_key"]))
    print(f"[{fam.cell_key}:extract] {len(pending)} pending ({len(rows) - len(pending)} done)")
    t0 = time.time()
    for i, row in enumerate(pending):
        prompt = cell_render.render(row)
        enc = tokenizer(prompt, return_tensors="pt").to(device)
        prompt_len = int(enc["input_ids"].shape[1])
        with torch.no_grad():
            out = model(**enc, output_hidden_states=True, use_cache=False)
        vec = out.hidden_states[fam.hs_index][0, prompt_len - 1, :].float().cpu().numpy().tolist()
        run_log.record(row["row_key"], {"role": row["role"], "split": row["split"], "vector": vec})
        if (i + 1) % 50 == 0 or (i + 1) == len(pending):
            print(f"[{fam.cell_key}:extract] {i + 1}/{len(pending)} ({time.time() - t0:.0f}s)", flush=True)
    run_log.finalize({"n_rows": len(rows)})
    run_log.close()

    del model
    gc.collect()
    torch.cuda.empty_cache()

    all_records = load_jsonl(fam.runlog_dir / "extract.jsonl")
    by_key = {r["row_key"]: r for r in all_records}
    missing = [r["row_key"] for r in rows if r["row_key"] not in by_key]
    if missing:
        print(f"[{fam.cell_key}:extract] FAILED: {len(missing)} rows missing: {missing[:5]}")
        return 1
    np.savez_compressed(
        fam.analysis / "extract_vectors.npz",
        **{_sanitize_key(k): np.asarray(v["vector"], dtype=np.float64) for k, v in by_key.items()},
    )
    (fam.analysis / "extract_manifest.json").write_text(json.dumps({
        "n_rows": len(rows), "hs_index": fam.hs_index, "model": fam.model_repo,
        "rows": [{"row_key": k, "role": v["role"], "split": v["split"]} for k, v in by_key.items()],
    }, indent=2))
    print(f"[{fam.cell_key}:extract] DONE: {len(by_key)} vectors")
    return 0


def _load_vectors(fam: Family) -> dict[str, np.ndarray]:
    npz = np.load(fam.analysis / "extract_vectors.npz")
    return {k: npz[k] for k in npz.files}


def cmd_refit(fam: Family) -> int:
    manifest = json.loads((fam.analysis / "extract_manifest.json").read_text())
    vecs = _load_vectors(fam)
    role_by_key = {r["row_key"]: r["role"] for r in manifest["rows"]}
    split_by_key = {r["row_key"]: r["split"] for r in manifest["rows"]}
    u_d = fam.load_direction_vector(fam.fam_cfg["detector_direction"]["path"])

    confab_fit = [rk for rk, role in role_by_key.items() if role == "confab" and split_by_key[rk] == "fit"]
    known_fit = [rk for rk, role in role_by_key.items() if role == "known_correct_answered" and split_by_key[rk] == "fit"]

    def z_d_for(keys: list[str]) -> np.ndarray:
        h = np.stack([vecs[_sanitize_key(rk)] for rk in keys])
        proj = h @ u_d
        return np.clip((proj - fam.mu_d) / fam.sigma_d, -2.0, 2.0)

    z_d = np.concatenate([z_d_for(confab_fit), z_d_for(known_fit)])
    labels = np.concatenate([np.ones(len(confab_fit)), np.zeros(len(known_fit))]).astype(int)
    score = -z_d
    tau, stats = gate_fit.youden_tau(score, labels)
    auc = gate_fit.roc_auc(score, labels)

    report = {
        "family": fam.cell_key, "hs_index": fam.hs_index,
        "n_confab_fit": len(confab_fit), "n_known_fit": len(known_fit),
        "mu_d_frozen": fam.mu_d, "sigma_d_frozen": fam.sigma_d,
        "auc_neg_z_d_on_fit_fresh_extraction": auc,
        "tau_frozen_refit": tau, "youden_stats": stats,
    }
    (fam.analysis / "refit.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    return 0


def _fire_decisions(fam: Family, held_out_rows: list[dict]) -> dict[str, bool]:
    refit = json.loads((fam.analysis / "refit.json").read_text())
    tau = refit["tau_frozen_refit"]
    vecs = _load_vectors(fam)
    u_d = fam.load_direction_vector(fam.fam_cfg["detector_direction"]["path"])
    fire = {}
    for row in held_out_rows:
        h = vecs[_sanitize_key(row["row_key"])]
        proj_d = float(h @ u_d)
        z_d = float(np.clip((proj_d - fam.mu_d) / fam.sigma_d, -2.0, 2.0))
        fire[row["row_key"]] = bool(-z_d >= tau)
    return fire


def cmd_generate(fam: Family, arm: str) -> int:
    assert arm in fam.arms, f"{arm} not a registered arm for {fam.cell_key} ({fam.arms})"
    held_out = fam.rows_for("held_out")
    print(f"[{fam.cell_key}:generate:{arm}] {len(held_out)} held-out rows")

    fire = _fire_decisions(fam, held_out) if arm != "no_op" else {r["row_key"]: False for r in held_out}
    print(f"[{fam.cell_key}:generate:{arm}] n_fire={sum(fire.values())}/{len(held_out)}")

    model, tokenizer, hidden_size, num_hidden_layers = ml.load_model_and_tokenizer(fam.dirname)
    device = next(model.parameters()).device
    eos_ids = ml.resolve_eos_ids(fam.dirname, tokenizer)

    vector, sigma, layer_idx = fam.direction_and_sigma(arm)
    strength = fam.dose_abs / sigma
    _hook, controller, layer_idx2, _sigma2 = ml.setup_hook_from_vector(vector, sigma, layer_idx)
    layer_module = ml.decoder_layer_module(model, layer_idx2)
    h_ctrl = layer_module.register_forward_hook(controller)

    run_log = RunLog(
        fam.runlog_dir / f"{arm}.jsonl",
        run_config={
            "family": fam.cell_key, "stage": "generate", "arm": arm, "model": fam.model_repo,
            "site": fam.fam_cfg["site"], "dose_abs": fam.dose_abs,
            "prompt": cell_render.NO_ABSTENTION_SYSTEM_PROMPT,
        },
        key_field="row_key",
        required_fields=("out_text",),
    )
    pending = list(run_log.iter_pending(held_out, key_fn=lambda r: r["row_key"]))
    print(f"[{fam.cell_key}:generate:{arm}] {len(pending)} pending ({len(held_out) - len(pending)} done)")
    try:
        t0 = time.time()
        for i, row in enumerate(pending):
            prompt = cell_render.render(row)
            enc = tokenizer(prompt, return_tensors="pt").to(device)
            row_fire = fire[row["row_key"]]

            base_out, _rb, base_terminated, base_new = gl.run_pass_fixed(
                model, controller, enc, "off", 0.0, tokenizer, eos_ids, max_new=gl.MAX_NEW_CAP
            )
            base_text = tokenizer.decode(base_new, skip_special_tokens=True)

            if arm != "no_op" and row_fire:
                dosed_out, readback, terminated_naturally, dosed_new = gl.run_pass_fixed(
                    model, controller, enc, "gen_stream", strength, tokenizer, eos_ids, max_new=gl.MAX_NEW_CAP
                )
                out_text = tokenizer.decode(dosed_new, skip_special_tokens=True)
                n_new = int(dosed_new.shape[0])
            else:
                out_text = base_text
                readback = None
                terminated_naturally = base_terminated
                n_new = int(base_new.shape[0])

            if not out_text:
                out_text = " "

            run_log.record(row["row_key"], {
                "role": row["role"], "fire": row_fire, "out_text": out_text,
                "readback_measured": readback, "n_new_tokens": n_new,
                "terminated_naturally": terminated_naturally, "aliases": row.get("aliases", []),
            })
            if (i + 1) % 25 == 0 or (i + 1) == len(pending):
                print(f"[{fam.cell_key}:generate:{arm}] {i + 1}/{len(pending)} ({time.time() - t0:.0f}s)", flush=True)
    finally:
        h_ctrl.remove()
        controller.reset()
        run_log.close()

    del model
    gc.collect()
    torch.cuda.empty_cache()
    print(f"[{fam.cell_key}:generate:{arm}] DONE")
    return 0


def _import_detector_v2():
    """See run_qwen3_4b.py's identical helper for the full rationale: this
    script already cached j-space-cross-family-layer-contrast/grader.py in
    sys.modules under "grader" (for grade_one, above); detector_v2.py's own
    unqualified `import grader` expects its OWN sibling
    (abstention-wide-instrument-calibration/grader.py, which defines
    _is_stated_confidence_refusal) and would otherwise silently resolve to
    the wrong cached module. Swap the correct module into sys.modules only
    for detector_v2's own import, then restore. detector_v2.py is not
    edited (pinned instrument)."""
    import importlib.util

    calib_dir = REPO_ROOT / "experiments" / "abstention-wide-instrument-calibration"
    calib_grader_path = calib_dir / "grader.py"
    spec = importlib.util.spec_from_file_location("_calib_grader_for_detector_v2", calib_grader_path)
    calib_grader = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(calib_grader)
    if not hasattr(calib_grader, "_is_stated_confidence_refusal"):
        raise RuntimeError(
            f"loaded grader module at {calib_grader_path} lacks "
            "_is_stated_confidence_refusal; detector_v2 cannot run"
        )

    sys.path.insert(0, str(calib_dir))
    prior_grader = sys.modules.get("grader")
    sys.modules["grader"] = calib_grader
    try:
        import detector_v2
    finally:
        if prior_grader is not None:
            sys.modules["grader"] = prior_grader
        else:
            sys.modules.pop("grader", None)
    print(f"[grade] detector_v2 grader module resolved to: {calib_grader_path}", flush=True)
    return detector_v2


def cmd_grade(fam: Family) -> int:
    detector_v2 = _import_detector_v2()

    cfg = detector_v2.load_patterns()
    report = {"family": fam.cell_key, "arms": {}}
    for arm in fam.arms:
        log_path = fam.runlog_dir / f"{arm}.jsonl"
        if not log_path.exists():
            continue
        records = load_jsonl(log_path)
        confab = [r for r in records if r["role"] == "confab"]
        known = [r for r in records if r["role"] == "known_correct_answered"]

        def grade_pop(pop: list[dict]) -> dict:
            n = len(pop)
            gradings = []
            for r in pop:
                ct = gl.grade_clean_tighten(r["out_text"], r["terminated_naturally"])
                og = grader.grade_one(r["out_text"], r.get("aliases"))
                v2_refused = detector_v2.is_refused_v2(r["out_text"], cfg)
                gradings.append({"clean_tighten": ct["clean_tighten"], "well_formed_correct": og["well_formed_correct"], "detector_v2_refused": v2_refused})
            succ_string_confab = sum(1 for g in gradings if g["clean_tighten"])
            succ_v2 = sum(1 for g in gradings if g["detector_v2_refused"])
            succ_wfc = sum(1 for g in gradings if g["well_formed_correct"])
            n_fired = sum(1 for r in pop if r.get("fire"))
            return {
                "n": n, "n_fired": n_fired,
                "clean_tighten": {"successes": succ_string_confab, "rate": succ_string_confab / n if n else 0.0, "wilson_ci_95": list(ml.wilson_ci(succ_string_confab, n)[1:])},
                "detector_v2_refused": {"successes": succ_v2, "rate": succ_v2 / n if n else 0.0, "wilson_ci_95": list(ml.wilson_ci(succ_v2, n)[1:])},
                "well_formed_correct": {"successes": succ_wfc, "rate": succ_wfc / n if n else 0.0, "wilson_ci_95": list(ml.wilson_ci(succ_wfc, n)[1:])},
            }

        report["arms"][arm] = {"confab": grade_pop(confab), "known_correct_answered": grade_pop(known)}
    out_path = fam.analysis / "grade_report.json"
    out_path.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--family", required=True, choices=["llama-3.2-3b", "mistral-7b-v03"])
    ap.add_argument("stage", choices=["extract", "refit", "generate", "grade", "all"])
    ap.add_argument("--arm", choices=["no_op", "gated", "random_direction"])
    args = ap.parse_args()

    fam = Family(args.family)

    if args.stage == "extract":
        return cmd_extract(fam)
    if args.stage == "refit":
        return cmd_refit(fam)
    if args.stage == "generate":
        if not args.arm:
            print("--arm required for generate", file=sys.stderr)
            return 2
        return cmd_generate(fam, args.arm)
    if args.stage == "grade":
        return cmd_grade(fam)
    if args.stage == "all":
        rc = cmd_extract(fam)
        if rc:
            return rc
        rc = cmd_refit(fam)
        if rc:
            return rc
        for arm in fam.arms:
            rc = cmd_generate(fam, arm)
            if rc:
                return rc
        return cmd_grade(fam)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
