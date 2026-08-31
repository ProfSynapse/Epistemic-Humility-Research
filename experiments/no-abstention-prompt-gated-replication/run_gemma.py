#!/usr/bin/env python3
"""gemma-4-e4b arm: no-abstention-prompt gated replication.

Standalone (not folded into run_cross_family.py) because gemma4-e4b-kv-seam-
quarantine ships its OWN copies of model_lib.py/gen_lib.py/grader.py/
gate_fit.py/family_config.py under the SAME module names as
j-space-cross-family-layer-contrast's copies used by run_cross_family.py.
Importing both in one process would collide via sys.modules caching (the
second `import model_lib` would silently reuse whichever copy loaded first).
Two scripts avoids that; nothing is reimplemented that already exists.

Reused unmodified via direct import (no edits to any parent file):
  - experiments/gemma4-e4b-kv-seam-quarantine/model_lib.py
    (load_model_and_tokenizer, resolve_eos_ids, setup_hook_from_vector,
    decoder_layer_module, wilson_ci) -- byte-identical API to the cross-
    family copy (its own docstring: "Ported from
    j-space-midband-write-sweep-qwen3-4b/model_lib.py").
  - experiments/gemma4-e4b-kv-seam-quarantine/gen_lib.py (run_pass_fixed,
    grade_clean_tighten) -- called WITHOUT its optional `cache_factory` arg
    (see "KV-seam" note below).
  - experiments/gemma4-e4b-kv-seam-quarantine/grader.py (grade_one).
  - experiments/gemma4-e4b-kv-seam-quarantine/gate_fit.py (youden_tau,
    roc_auc) -- same threshold-refit method as every other family in this
    cell (mu_d/sigma_d frozen from the pinned build_manifest, only tau
    refit on fresh no-abstention-prompt FIT-split extraction).
  - experiments/gemma4-e4b-kv-seam-quarantine/kv_seam_patch.verify_architecture
    -- a cheap fail-closed check that the pinned KV-sharing geometry (42
    layers, donor blocks 22/23) still holds. Read in full before writing
    this script.
  - THIS cell's own pinned render.py (no-abstention prompt, all families).

KV-seam note (read gemma4-e4b-kv-seam-quarantine/kv_seam_patch.py and
NOTEBOOK.md in full before writing this): the documented IndexError/
corruption risk is specific to the withdrawn kv_sharing(enabled=False)
ablation, which forces every block in 24-41 to call k_proj/v_proj and
.update() at its own layer index against a cache truncated to 24 entries.
This cell never disables KV sharing -- it runs gemma under its normal,
default "sharing ON" condition with an unrelated erase-write hook at hs15
(output of block 14, far upstream of the donor blocks 22/23 and the shared
region 24-41). Under sharing ON, shared blocks never call `.update()` on
their own index (they only READ `shared_layers[donor]`, written by the
non-shared donor blocks within the model's own auto-built cache), so no
crash and no seam interaction. `build_full_length_cache`'s own docstring
confirms this: "Under enabled=True it is not needed to avoid a crash." So
`gen_lib.run_pass_fixed` is called with `cache_factory=None` (its default),
which "preserves the pre-existing behaviour exactly ... correct for every
non-KV-sharing family" per that function's own docstring -- and is also
correct here since this cell's own condition never touches the seam.
Likewise extraction uses `output_hidden_states=True, use_cache=True`
(matching this family's own established "clean extract" convention;
NOTEBOOK.md F2/F3: the withdrawn `use_cache=False` extraction corrupted
activations at hs25+ and was never the registered method at any depth),
not the `use_cache=False` single-row pattern the other four families in
this cell use (none of which have this architecture's KV-sharing).

cell.yaml's gemma-4-e4b artifacts are all sourced from THIS quarantine
experiment's "shallow_ladder" build (build_manifest_layers.shallow_ladder.json,
dose_calibration_summary.shallow_ladder.json, split_manifest.json,
eval_pool_manifest.json) -- the corrected, sharing-ON, clean-activation
operating point (NOTEBOOK.md "Stage 5a -- shallow_ladder ON dose
calibration, COMPLETE, 2026-07-30"; hs15 selected_dose 173.65765096701432
matches cell.yaml's dose_abs exactly).

Row source: eval_rows.jsonl does NOT carry `split` per row (unlike the
cross-family families' own eval_rows.jsonl) -- FIT/held_out membership is a
separate join against split_manifest.json's `rows` array (row_key -> split),
which is also the pinned heldout_pool manifest cell.yaml's counts are
checked against at preflight.

Arms: no_op, gated only (cell.yaml arms list; no random_direction for
gemma, same posture as mistral).
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
GEMMA_DIR = REPO_ROOT / "experiments" / "gemma4-e4b-kv-seam-quarantine"
FAMILY_DIRNAME = "gemma4-e4b"  # this quarantine experiment's own family key (load_family, model_lib)
CELL_KEY = "gemma-4-e4b"  # cell.yaml's own key (with dash)

sys.path.insert(0, str(GEMMA_DIR))
sys.path.insert(0, str(HERE))

import model_lib as ml  # noqa: E402  (gemma4-e4b-kv-seam-quarantine's own copy)
import gen_lib as gl  # noqa: E402
import grader  # noqa: E402
import gate_fit  # noqa: E402  (reuse youden_tau/roc_auc only)
import kv_seam_patch as kv  # noqa: E402  (verify_architecture only; no cache patch needed, see module docstring)

CELL = yaml.safe_load((HERE / "cell.yaml").read_text())
FAM = CELL["families"][CELL_KEY]

TUNER_DIR = REPO_ROOT / "synaptic-tuner"
sys.path.insert(0, str(TUNER_DIR))
from shared.utilities.run_log import RunLog  # noqa: E402

ANALYSIS = HERE / "analysis" / CELL_KEY
ANALYSIS.mkdir(parents=True, exist_ok=True)
RUNLOG_DIR = ANALYSIS / "runlog"
RUNLOG_DIR.mkdir(parents=True, exist_ok=True)

HS_INDEX = int(FAM["site"].replace("hs", ""))
DECODER_BLOCK_INDEX = int(FAM["decoder_block_index"])
DOSE_ABS = float(FAM["dose_abs"])
ARMS = ["no_op", "gated"]

EVAL_ROWS_PATH = GEMMA_DIR / "analysis" / FAMILY_DIRNAME / "eval_rows.jsonl"
SPLIT_MANIFEST_PATH = REPO_ROOT / FAM["heldout_pool"]["path"]

BUILD_MANIFEST = json.loads((REPO_ROOT / FAM["build_manifest"]["path"]).read_text())
HIDDEN_DIM = BUILD_MANIFEST["hidden_dim"]
BUILD_LAYER = BUILD_MANIFEST["layers"][FAM["site"]]
MU_D, SIGMA_D = BUILD_LAYER["mu_d"], BUILD_LAYER["sigma_d"]

os.environ["DOUBT_SNAP_RENDER_MODEL"] = FAM["model"]
import render as cell_render  # noqa: E402


def _sanitize_key(row_key: str) -> str:
    return row_key.replace(":", "_")


def load_jsonl(p: Path) -> list[dict]:
    return [json.loads(ln) for ln in p.open(encoding="utf-8") if ln.strip()]


def all_rows() -> list[dict]:
    """eval_rows.jsonl joined against split_manifest.json's row_key->split
    map (eval_rows.jsonl itself carries no `split` field for this family)."""
    rows = load_jsonl(EVAL_ROWS_PATH)
    split_manifest = json.loads(SPLIT_MANIFEST_PATH.read_text())
    split_by_key = {r["row_key"]: r["split"] for r in split_manifest["rows"]}
    out = []
    for r in rows:
        if r["role"] not in ("confab", "known_correct_answered"):
            continue
        split = split_by_key.get(r["row_key"])
        if split is None:
            continue  # not in the registered fit/held_out split (e.g. unknown_refused has none)
        out.append({**r, "split": split})
    return out


def rows_for(split: str) -> list[dict]:
    return [r for r in all_rows() if r["split"] == split]


def load_direction_vector(rel_path: str) -> tuple[np.ndarray, float, int]:
    data = json.loads((REPO_ROOT / rel_path).read_text())
    return np.asarray(data["vector"], dtype=np.float64), float(data.get("sigma", 1.0)), int(data["layer"])


def cmd_extract() -> int:
    rows = all_rows()
    print(f"[extract] {len(rows)} rows")
    model, tokenizer, hidden_size, num_hidden_layers = ml.load_model_and_tokenizer(FAMILY_DIRNAME)
    kv.verify_architecture(model)  # fail closed if the pinned KV-seam geometry moved
    device = next(model.parameters()).device

    run_log = RunLog(
        RUNLOG_DIR / "extract.jsonl",
        run_config={"family": CELL_KEY, "stage": "extract", "model": FAM["model"], "site": FAM["site"],
                    "prompt": cell_render.NO_ABSTENTION_SYSTEM_PROMPT},
        key_field="row_key",
    )
    pending = list(run_log.iter_pending(rows, key_fn=lambda r: r["row_key"]))
    print(f"[extract] {len(pending)} pending ({len(rows) - len(pending)} done)")
    t0 = time.time()
    for i, row in enumerate(pending):
        prompt = cell_render.render(row)
        enc = tokenizer(prompt, return_tensors="pt").to(device)
        prompt_len = int(enc["input_ids"].shape[1])
        with torch.no_grad():
            # use_cache=True: this family's own established "clean extract"
            # convention (NOTEBOOK.md F2/F3), not use_cache=False -- see
            # module docstring's KV-seam note.
            out = model(**enc, output_hidden_states=True, use_cache=True)
        vec = out.hidden_states[HS_INDEX][0, prompt_len - 1, :].float().cpu().numpy().tolist()
        run_log.record(row["row_key"], {"role": row["role"], "split": row["split"], "vector": vec})
        if (i + 1) % 50 == 0 or (i + 1) == len(pending):
            print(f"[extract] {i + 1}/{len(pending)} ({time.time() - t0:.0f}s)", flush=True)
    run_log.finalize({"n_rows": len(rows)})
    run_log.close()

    del model
    gc.collect()
    torch.cuda.empty_cache()

    all_records = load_jsonl(RUNLOG_DIR / "extract.jsonl")
    by_key = {r["row_key"]: r for r in all_records}
    missing = [r["row_key"] for r in rows if r["row_key"] not in by_key]
    if missing:
        print(f"[extract] FAILED: {len(missing)} rows missing: {missing[:5]}")
        return 1
    np.savez_compressed(ANALYSIS / "extract_vectors.npz",
                         **{_sanitize_key(k): np.asarray(v["vector"], dtype=np.float64) for k, v in by_key.items()})
    (ANALYSIS / "extract_manifest.json").write_text(json.dumps({
        "n_rows": len(rows), "hs_index": HS_INDEX, "model": FAM["model"],
        "rows": [{"row_key": k, "role": v["role"], "split": v["split"]} for k, v in by_key.items()],
    }, indent=2))
    print(f"[extract] DONE: {len(by_key)} vectors")
    return 0


def _load_vectors() -> dict[str, np.ndarray]:
    npz = np.load(ANALYSIS / "extract_vectors.npz")
    return {k: npz[k] for k in npz.files}


def cmd_refit() -> int:
    manifest = json.loads((ANALYSIS / "extract_manifest.json").read_text())
    vecs = _load_vectors()
    role_by_key = {r["row_key"]: r["role"] for r in manifest["rows"]}
    split_by_key = {r["row_key"]: r["split"] for r in manifest["rows"]}
    u_d, _sig, _layer = load_direction_vector(FAM["detector_direction"]["path"])

    confab_fit = [rk for rk, role in role_by_key.items() if role == "confab" and split_by_key[rk] == "fit"]
    known_fit = [rk for rk, role in role_by_key.items() if role == "known_correct_answered" and split_by_key[rk] == "fit"]

    def z_d_for(keys: list[str]) -> np.ndarray:
        h = np.stack([vecs[_sanitize_key(rk)] for rk in keys])
        proj = h @ u_d
        return np.clip((proj - MU_D) / SIGMA_D, -2.0, 2.0)

    z_d = np.concatenate([z_d_for(confab_fit), z_d_for(known_fit)])
    labels = np.concatenate([np.ones(len(confab_fit)), np.zeros(len(known_fit))]).astype(int)
    score = -z_d
    tau, stats = gate_fit.youden_tau(score, labels)
    auc = gate_fit.roc_auc(score, labels)
    report = {
        "family": CELL_KEY, "hs_index": HS_INDEX,
        "n_confab_fit": len(confab_fit), "n_known_fit": len(known_fit),
        "mu_d_frozen": MU_D, "sigma_d_frozen": SIGMA_D,
        "auc_neg_z_d_on_fit_fresh_extraction": auc, "tau_frozen_refit": tau, "youden_stats": stats,
    }
    (ANALYSIS / "refit.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    return 0


def _fire_decisions(rows: list[dict]) -> dict[str, bool]:
    refit = json.loads((ANALYSIS / "refit.json").read_text())
    tau = refit["tau_frozen_refit"]
    vecs = _load_vectors()
    u_d, _sig, _layer = load_direction_vector(FAM["detector_direction"]["path"])
    fire = {}
    for row in rows:
        h = vecs[_sanitize_key(row["row_key"])]
        proj_d = float(h @ u_d)
        z_d = float(np.clip((proj_d - MU_D) / SIGMA_D, -2.0, 2.0))
        fire[row["row_key"]] = bool(-z_d >= tau)
    return fire


def cmd_generate(arm: str) -> int:
    assert arm in ARMS, f"{arm} not a registered arm for {CELL_KEY} ({ARMS})"
    held_out = rows_for("held_out")
    print(f"[generate:{arm}] {len(held_out)} held-out rows")

    fire = _fire_decisions(held_out) if arm != "no_op" else {r["row_key"]: False for r in held_out}
    print(f"[generate:{arm}] n_fire={sum(fire.values())}/{len(held_out)}")

    model, tokenizer, hidden_size, num_hidden_layers = ml.load_model_and_tokenizer(FAMILY_DIRNAME)
    kv.verify_architecture(model)
    device = next(model.parameters()).device
    eos_ids = ml.resolve_eos_ids(FAMILY_DIRNAME, tokenizer)

    c_hat, sigma_c, layer_idx = load_direction_vector(FAM["write_direction"]["path"])
    strength = DOSE_ABS / sigma_c
    _hook, controller, layer_idx2, _sigma2 = ml.setup_hook_from_vector(c_hat, sigma_c, layer_idx)
    layer_module = ml.decoder_layer_module(model, layer_idx2)
    handle = layer_module.register_forward_hook(controller)

    run_log = RunLog(
        RUNLOG_DIR / f"{arm}.jsonl",
        run_config={"family": CELL_KEY, "stage": "generate", "arm": arm, "model": FAM["model"],
                    "site": FAM["site"], "dose_abs": DOSE_ABS,
                    "prompt": cell_render.NO_ABSTENTION_SYSTEM_PROMPT},
        key_field="row_key",
        required_fields=("out_text",),
    )
    pending = list(run_log.iter_pending(held_out, key_fn=lambda r: r["row_key"]))
    print(f"[generate:{arm}] {len(pending)} pending ({len(held_out) - len(pending)} done)")
    try:
        t0 = time.time()
        for i, row in enumerate(pending):
            prompt = cell_render.render(row)
            enc = tokenizer(prompt, return_tensors="pt").to(device)
            row_fire = fire[row["row_key"]]

            # cache_factory=None (default): correct here -- see module
            # docstring's KV-seam note (sharing stays ON; no seam interaction).
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
                print(f"[generate:{arm}] {i + 1}/{len(pending)} ({time.time() - t0:.0f}s)", flush=True)
    finally:
        handle.remove()
        controller.reset()
        run_log.close()

    del model
    gc.collect()
    torch.cuda.empty_cache()
    print(f"[generate:{arm}] DONE")
    return 0


def _import_detector_v2():
    """See run_qwen3_4b.py's identical helper for the full rationale: this
    script already cached gemma4-e4b-kv-seam-quarantine/grader.py in
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


def cmd_grade() -> int:
    detector_v2 = _import_detector_v2()

    cfg = detector_v2.load_patterns()
    report = {"family": CELL_KEY, "arms": {}}
    for arm in ARMS:
        log_path = RUNLOG_DIR / f"{arm}.jsonl"
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
                gradings.append({"clean_tighten": ct["clean_tighten"], "well_formed_correct": og["well_formed_correct"],
                                  "refused": og["refused"], "detector_v2_refused": v2_refused})
            succ_ct = sum(1 for g in gradings if g["clean_tighten"])
            succ_v2 = sum(1 for g in gradings if g["detector_v2_refused"])
            succ_wfc = sum(1 for g in gradings if g["well_formed_correct"])
            succ_refused = sum(1 for g in gradings if g["refused"])
            n_fired = sum(1 for r in pop if r.get("fire"))
            return {
                "n": n, "n_fired": n_fired,
                "refused": {"successes": succ_refused, "rate": succ_refused / n if n else 0.0, "wilson_ci_95": list(ml.wilson_ci(succ_refused, n)[1:])},
                "clean_tighten": {"successes": succ_ct, "rate": succ_ct / n if n else 0.0, "wilson_ci_95": list(ml.wilson_ci(succ_ct, n)[1:])},
                "well_formed_correct": {"successes": succ_wfc, "rate": succ_wfc / n if n else 0.0, "wilson_ci_95": list(ml.wilson_ci(succ_wfc, n)[1:])},
                "detector_v2_refused": {"successes": succ_v2, "rate": succ_v2 / n if n else 0.0, "wilson_ci_95": list(ml.wilson_ci(succ_v2, n)[1:])},
            }

        report["arms"][arm] = {"confab": grade_pop(confab), "known_correct_answered": grade_pop(known)}
    (ANALYSIS / "grade_report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["extract", "refit", "generate", "grade", "all"])
    ap.add_argument("--arm", choices=["no_op", "gated"])
    args = ap.parse_args()

    if args.stage == "extract":
        return cmd_extract()
    if args.stage == "refit":
        return cmd_refit()
    if args.stage == "generate":
        if not args.arm:
            print("--arm required", file=sys.stderr)
            return 2
        return cmd_generate(args.arm)
    if args.stage == "grade":
        return cmd_grade()
    if args.stage == "all":
        rc = cmd_extract()
        if rc:
            return rc
        rc = cmd_refit()
        if rc:
            return rc
        for arm in ARMS:
            rc = cmd_generate(arm)
            if rc:
                return rc
        return cmd_grade()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
