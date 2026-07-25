"""Shared per-family gate-decision / dosed-run machinery for the cross-family
J-space layer contrast.

Ported from `j-space-midband-write-sweep-qwen3-4b/pipeline.py`, generalized
to take `family` as an explicit argument everywhere instead of hardcoding
Qwen3-4B paths, and to resolve EOS ids per-family (`model_lib.resolve_eos_ids`)
instead of the predecessor's Qwen-only `<|im_end|>` lookup. `calibrate_dose.py`
and `run_contrast.py` both import from here so the dosed-row generation loop
is defined exactly once per family, matching the predecessor's own
calibrate_dose.py / pipeline.py split.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent

import gen_lib as gl  # noqa: E402
import grader  # noqa: E402
import kv_seam_patch as kv  # noqa: E402
import model_lib as ml  # noqa: E402
from family_config import (  # noqa: E402
    SITE_SETS, layer_dir_name, load_family, site_set_artifact,
    is_late_reference as fc_is_late, reuse_artifact_path as fc_reuse_path,
)
from MechInterp.intervention import get_decoder_layer  # noqa: E402

MAX_NEW = gl.MAX_NEW_CAP


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(ln) for ln in path.open(encoding="utf-8") if ln.strip()]


def load_roll_up_layer(family: str, stem: str, layer_name: str,
                       kv_sharing: str = "on") -> dict:
    """Read one layer's record out of a per-site-set roll-up JSON.

    build_directions/gate_fit/calibrate_dose write one roll-up per site set
    (`<stem>.json` for midband, `<stem>.<site_set>.json` otherwise), so a
    layer's record lives in exactly one of them. Rather than thread `site_set`
    through every function here, resolve BY CONTENT: site sets are disjoint
    layer sets, so at most one roll-up can contain `layer_name` and the lookup
    is unambiguous. Un-suffixed (midband) is tried first, preserving the
    pre-existing single-file path exactly.

    `kv_sharing` is NOT resolved by content -- it scopes the search. Both
    conditions fit the same layers, so an ON and an OFF roll-up both contain
    `layer_name` and content resolution could not tell them apart. Falling back
    across conditions would violate cell.yaml `readouts.refit_policy`, which
    requires sharing-OFF arms to use their OWN refit parameters; a missing OFF
    roll-up is therefore an error, not a reason to read the ON one.
    """
    committed = HERE / "analysis-committed" / family
    tried = []
    for site_set in [None, *sorted(SITE_SETS)]:
        name = stem if site_set is None else site_set_artifact(stem, site_set)
        name = kv.condition_artifact(name, kv_sharing)
        path = committed / name
        if path in tried or not path.is_file():
            continue
        tried.append(path)
        layers = json.loads(path.read_text()).get("layers", {})
        if layer_name in layers:
            return layers[layer_name]
    raise FileNotFoundError(
        f"{family}: no roll-up derived from {stem!r} at kv_sharing={kv_sharing} contains "
        f"layer {layer_name!r}; searched {[p.name for p in tried] or '(none present)'}. "
        f"Run the build/fit stage for the site set that includes this layer, under "
        f"--kv-sharing {kv_sharing}."
    )


def load_direction_vector(path: Path) -> np.ndarray:
    data = json.loads(path.read_text())
    return np.asarray(data["vector"], dtype=np.float64)


def layer_paths(family: str, hs_index: int, kv_sharing: str = "on") -> dict[str, Path]:
    """Per-site fitted direction paths, scoped by KV-sharing condition.

    Both conditions fit the same sites, so the condition has to live in the
    filename (`u_d_hs38.kv_off.json`) or the OFF refit would overwrite the ON
    one. `on` keeps the historical names byte-for-byte.
    """
    layer_name = layer_dir_name(hs_index)
    root = HERE / "analysis-committed" / family / "layers" / layer_name
    return {
        "u_d": root / kv.condition_artifact(f"u_d_{layer_name}.json", kv_sharing),
        "c_hat": root / kv.condition_artifact(f"c_hat_{layer_name}.json", kv_sharing),
    }


def load_rows(family: str, role: str, split: str) -> list[dict]:
    """Join the private materialized eval rows (question/aliases, from
    `mine_eval_pool.py`) against the committed split manifest (row_key ->
    fit|held_out, from `split_fit_heldout.py`) on the fly, so no separate
    "rows_with_split" materialization step is needed per family."""
    rows_path = HERE / "analysis" / family / "eval_rows.jsonl"
    split_path = HERE / "analysis-committed" / family / "split_manifest.json"
    split_by_key = {
        r["row_key"]: r["split"] for r in json.loads(split_path.read_text())["rows"]
    }
    return [
        r for r in load_jsonl(rows_path)
        if r["role"] == role and split_by_key.get(r["row_key"]) == split
    ]


def stratified_subset(rows: list[dict], n: int) -> list[dict]:
    by_cat: dict[str, list[dict]] = {}
    order: list[str] = []
    for r in sorted(rows, key=lambda rec: rec["row_key"]):
        cat = r.get("category_canon")
        if cat not in by_cat:
            by_cat[cat] = []
            order.append(cat)
        by_cat[cat].append(r)
    out: list[dict] = []
    idx = 0
    while len(out) < n:
        added = False
        for cat in order:
            if idx < len(by_cat[cat]):
                out.append(by_cat[cat][idx])
                added = True
                if len(out) >= n:
                    break
        if not added:
            break
        idx += 1
    return out[:n]


def _late_gate_params(cfg: dict) -> dict:
    """Doubt gate params for the LATE reference arm, loaded FROZEN from the
    reused doubt-snap artifacts (u_d vector + mu_d/sigma_d from build_manifest
    + tau_frozen from gate_fit). Nothing here is refit by this experiment."""
    build = json.loads(fc_reuse_path(cfg, "build_manifest").read_text())
    gate = json.loads(fc_reuse_path(cfg, "gate_fit").read_text())
    return {
        "u_d": load_direction_vector(fc_reuse_path(cfg, "u_d")),
        "mu_d": build["mu_d"], "sigma_d": build["sigma_d"],
        "tau": gate["tau_frozen"], "sigma_c": build["sigma_c"],
        "c_hat_path": fc_reuse_path(cfg, "c_hat"),
    }


def compute_gate_decisions(family: str, rows: list[dict], hs_index: int,
                           kv_sharing: str = "on") -> list[dict]:
    """Apply this arm's gate to each row's anchor activation.

    `kv_sharing` scopes BOTH the activations and the gate parameters, per
    cell.yaml `readouts.refit_policy`: "sharing-OFF arms refit their own
    directions, tau, and per-site median anchor L2 norm on the SAME FIT rows --
    the OFF residual stream is a different distribution and ON-fitted
    parameters are not automatically valid under it." So an OFF run reads the
    OFF extract (`extract_anchor.py --kv-sharing off`) AND the OFF u_d /
    mu_d/sigma_d / tau_frozen. Nothing falls back across conditions: a missing
    OFF artifact raises rather than silently gating on ON parameters the arm
    never fit.

    The LATE reference arm is the one exception and is not condition-scoped --
    it reuses doubt-snap's frozen artifacts verbatim (it is a descriptive,
    non-gating inherited arm, and no OFF late arm is registered in cell.yaml).
    """
    cfg = load_family(family)
    extract_tensors = (HERE / "analysis" / family
                       / kv.condition_artifact("anchor_extract.safetensors", kv_sharing))
    if not extract_tensors.exists():
        raise FileNotFoundError(
            f"no anchor extract for kv_sharing={kv_sharing}: {extract_tensors}. "
            f"Run extract_anchor.py --family {family} --kv-sharing {kv_sharing} first."
        )

    tensors = __import__("safetensors.numpy", fromlist=["load_file"]).load_file(str(extract_tensors))
    fresh = {k: np.asarray(v, dtype=np.float64) for k, v in tensors.items()}

    if fc_is_late(cfg, hs_index):
        # LATE reference arm: frozen doubt gate from the reused doubt-snap cell.
        lp = _late_gate_params(cfg)
        u_d, mu_d, sigma_d, tau = lp["u_d"], lp["mu_d"], lp["sigma_d"], lp["tau"]
    else:
        # MID-BAND candidate: gate fit fresh by this experiment on the reused
        # FIT split, under this arm's own KV-sharing condition.
        layer_name = layer_dir_name(hs_index)
        u_d = load_direction_vector(layer_paths(family, hs_index, kv_sharing)["u_d"])
        build = load_roll_up_layer(family, "build_manifest_layers.json", layer_name,
                                   kv_sharing)
        gate = load_roll_up_layer(family, "gate_fit_layers.json", layer_name, kv_sharing)
        mu_d, sigma_d, tau = build["mu_d"], build["sigma_d"], gate["tau_frozen"]

    out = []
    for row in rows:
        h = fresh[f"hs{hs_index}__{row['row_key'].replace(':', '_')}"]
        proj_d = float(h @ u_d)
        z_d = float(np.clip((proj_d - mu_d) / sigma_d, -2.0, 2.0))
        score = -z_d
        rec = dict(row)
        rec.update({"hs_index": hs_index, "proj_d": proj_d, "z_d": z_d,
                    "score_neg_z_d": score, "tau": tau, "fire": bool(score >= tau)})
        out.append(rec)
    return out


def run_one_row(family: str, model, controller, tokenizer, dev, eos_ids: list[int],
                 row: dict, strength_if_dosed: float, cache_factory=None) -> dict:
    prompt = ml.render(family, tokenizer, row)
    enc = tokenizer(prompt, return_tensors="pt").to(dev)

    base_out, _rb, base_terminated, base_new = gl.run_pass_fixed(
        model, controller, enc, "off", 0.0, tokenizer, eos_ids, max_new=MAX_NEW,
        cache_factory=cache_factory,
    )
    base_text = tokenizer.decode(base_new, skip_special_tokens=True)

    if row["fire"]:
        dosed_out, readback, terminated_naturally, dosed_new = gl.run_pass_fixed(
            model, controller, enc, "gen_stream", strength_if_dosed, tokenizer, eos_ids,
            max_new=MAX_NEW, cache_factory=cache_factory,
        )
        out_text = tokenizer.decode(dosed_new, skip_special_tokens=True)
        n_new = int(dosed_new.shape[0])
    else:
        out_text, readback, terminated_naturally, n_new = (
            base_text, None, base_terminated, int(base_new.shape[0])
        )

    ct = gl.grade_clean_tighten(out_text, terminated_naturally)
    old_grade = grader.grade_one(out_text, row.get("aliases"))
    return {
        "row_key": row["row_key"], "role": row["role"], "category_canon": row.get("category_canon"),
        "hs_index": row["hs_index"], "fire": row["fire"], "readback_measured": readback,
        "n_new_tokens": n_new, "terminated_naturally": terminated_naturally,
        "clean_tighten": ct["clean_tighten"], "semantic_refuse": ct["semantic_refuse"],
        "well_formed_correct": old_grade["well_formed_correct"],
        "not_well_formed_correct": not old_grade["well_formed_correct"],
        "grade": ct, "old_grade": old_grade,
    }


def grade_population(records: list[dict], metric: str) -> dict:
    n = len(records)
    successes = sum(1 for r in records if r[metric])
    rate, lo, hi = ml.wilson_ci(successes, n)
    return {"n": n, "successes": successes, "rate": rate, "wilson_ci_95": [lo, hi]}


def kv_condition_context(family: str, model, kv_sharing: str):
    """(context manager, cache_factory) for one KV condition.

    Implements the CALLER CONTRACT from cell.yaml and
    `kv_seam_patch.build_full_length_cache`: on a KV-sharing substrate BOTH
    conditions get a fresh full-length cache per generate() call, so the cache
    object is a CONSTANT across arms and the ON-vs-OFF contrast varies the
    sharing flag and nothing else. Supplying it in only one arm would make the
    primary contrast uninterpretable, and omitting it under OFF raises
    IndexError on the first shared-layer forward.

    Families without KV sharing get (nullcontext, None) -- the stock path,
    unchanged. `kv_sharing='off'` on such a family is refused rather than
    silently ignored: it would be a no-op the caller almost certainly did not
    intend.
    """
    import contextlib

    cfg = load_family(family)
    shares_kv = bool(cfg.get("architecture", {}).get("kv_sharing")) or family == "gemma4-e4b"
    if not shares_kv:
        if kv_sharing != "on":
            raise ValueError(
                f"{family}: --kv-sharing {kv_sharing!r} requested but this family has no "
                "cross-layer KV sharing; the flag would be a silent no-op."
            )
        return contextlib.nullcontext(model), None

    kv.verify_architecture(model)  # fail closed if the geometry moved
    enabled = kv_sharing == "on"
    return kv.kv_sharing(model, enabled=enabled), (lambda: kv.build_full_length_cache(model))


def run_layer(family: str, model, tokenizer, hs_index: int, rows: list[dict],
              dose_target: float, *, run_log=None, kv_sharing: str = "on") -> dict:
    """Run one family+layer's rows through the dosed pass.

    If `run_log` is given (a tuner `RunLog` opened by the caller at a
    per-family/per-layer path), each row's result is appended and fsynced
    as it completes and rows already recorded on a prior, killed run are
    skipped -- see `experiments/common/README-runlog.md` in the root repo.
    With `run_log=None` (the default, used by `calibrate_dose.py`'s
    per-dose ladder where the same rows repeat under different doses and a
    single run log path would collide), the whole-arm-in-memory behavior is
    unchanged.
    """
    cfg = load_family(family)
    if fc_is_late(cfg, hs_index):
        # LATE reference arm: frozen c_hat + sigma_c from the reused doubt-snap
        # cell. setup_hook_from_path reads the write vector, sigma, and decoder
        # block index from doubt-snap's own committed c_hat.json.
        lp = _late_gate_params(cfg)
        sigma_c = lp["sigma_c"]
        c_hat_path = lp["c_hat_path"]
    else:
        layer_name = layer_dir_name(hs_index)
        build = load_roll_up_layer(family, "build_manifest_layers.json", layer_name,
                                   kv_sharing)
        sigma_c = build["sigma_c"]
        c_hat_path = layer_paths(family, hs_index, kv_sharing)["c_hat"]
    strength = dose_target / sigma_c
    hook, controller, layer_idx, _sigma, _rec = ml.setup_hook_from_path(c_hat_path)
    dev = next(model.parameters()).device
    eos_ids = ml.resolve_eos_ids(family, tokenizer)
    layer_module = get_decoder_layer(model, layer_idx)
    h_ctrl = layer_module.register_forward_hook(controller)
    kv_ctx, cache_factory = kv_condition_context(family, model, kv_sharing)
    try:
        with kv_ctx:
            if run_log is not None:
                pending = list(run_log.iter_pending(rows, key_fn=lambda r: r["row_key"]))
                for row in pending:
                    rec = run_one_row(family, model, controller, tokenizer, dev, eos_ids,
                                      row, strength, cache_factory=cache_factory)
                    rec["kv_sharing"] = kv_sharing
                    run_log.record(row["row_key"], rec)
                on_disk = {rec["key"]: rec for rec in load_jsonl(run_log.path)}
                records = [on_disk[row["row_key"]] for row in rows]
            else:
                records = []
                for r in rows:
                    rec = run_one_row(family, model, controller, tokenizer, dev, eos_ids,
                                      r, strength, cache_factory=cache_factory)
                    rec["kv_sharing"] = kv_sharing
                    records.append(rec)
    finally:
        h_ctrl.remove()
        controller.reset()
    confab = [r for r in records if r["role"] == "confab"]
    known = [r for r in records if r["role"] == "known_correct_answered"]
    dosed = [r for r in records if r["fire"]]
    readbacks = [r["readback_measured"] for r in dosed if r["readback_measured"] is not None]
    within = [abs(rb - dose_target) <= 0.05 * dose_target + 0.5 for rb in readbacks]
    return {
        "hs_index": hs_index, "kv_sharing": kv_sharing,
        "n_rows": len(records), "n_fired": len(dosed),
        "readback_mean": float(np.mean(readbacks)) if readbacks else None,
        "frac_readback_within_tol": (sum(within) / len(within)) if within else None,
        "collapse_rate_on_dosed": (
            sum(1 for r in dosed if r["grade"]["degenerate"]) / len(dosed) if dosed else None
        ),
        "confab_tighten": grade_population(confab, "clean_tighten"),
        "known_correct_cost_control": grade_population(known, "not_well_formed_correct"),
    }
