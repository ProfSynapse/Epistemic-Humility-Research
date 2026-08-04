#!/usr/bin/env python3
"""Cross-family held-out J-space outcome run.

PRIMARY (gating): the best MID-BAND site's held-out confab clean_tighten (G1
floor) and known-correct not_well_formed_correct cost (G2 cap), scored on the
REUSED doubt-snap held-out split. SECONDARY (descriptive, non-gating): the
frozen late-reference arm -- doubt-snap's own late-site direction/gate reused
verbatim -- and the best-mid-band-minus-late deltas, reported for contrast with
doubt-snap's resolved late-site null.

REFRAMED 2026-07-23 (sign-time revision): the old relative G1/G2/G3 contrast
(best mid-band beats late by >=10pp, etc.) is replaced by absolute mid-band
gates read from each family's `primary_gate` block. The late arm gates NOTHING;
its scalar dose is calibrated FRESH here with the same calibrate_dose.py ladder
as the mid-band arm (option B, RESOLVED 2026-07-23; the frozen late-site
direction/gate stay reused verbatim). If no usable late dose is found -- expected
per doubt-snap's late-site null -- the late arm is SKIPPED and the primary is
unaffected.

Ported from `j-space-layer-contrast-replication-qwen3-4b/run_contrast.py` and
`j-space-midband-write-sweep-qwen3-4b/pipeline.py`, generalized to `--family`.

ARM KINDS (added 2026-07-25, pre-signature). `--arm-kind` defaults to `true`,
which preserves every existing code path byte-for-byte -- nothing below
changes the `true`-arm behavior that has been registered since sign-time.
Two additive arm kinds implement `cell.yaml placebo_direction_control` (the
P1/P2 direction-specificity control gates.yaml scores as
`g3_direction_specificity`):

  `placebo` -- writes a random, SC1-screened direction at EXACTLY the rows
    and dose the matched TRUE arm fired at (read from that arm's own
    `--mode full` run log, never re-gated: cell.yaml fired_row_matching).
    Only registered for the site set(s) listed in cell.yaml
    `registered_control_site_sets` (resolved at call time, not hardcoded --
    see `registered_control_site_sets()` below; this experiment's cell.yaml
    lists `["pocket"]`, an INSTRUMENT DELTA from the seam-quarantine
    original this file was copied from, which hardcoded `"seam_pair"`. See
    AMENDMENT.md "Instrument deltas from the quarantine cell").
  `undosed` -- the arm's own undosed pass (no injection anywhere), the hard
    input G2's `undosed_floor` companion and G3's lift baseline both require
    (cell.yaml placebo_direction_control.undosed_baseline_required).

`--dry-run` resolves rows, doses, and (for `placebo`) the SC1 draw/screen
ledger entirely on CPU and prints the plan without loading the model --
proves the new flags compose with the existing `--kv-sharing` flag before
any GPU spend.
"""

from __future__ import annotations

import argparse
import gc
import json
import random as pyrandom
import sys
from pathlib import Path

import torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import family_config  # noqa: E402
from family_config import (  # noqa: E402
    FAMILY_SLUGS, SITE_SETS, layer_dir_name, load_family,
    resolve_site_set, site_set_artifact,
    late_reference_hs as family_late_reference_hs,
)
import kv_seam_patch as kv  # noqa: E402
import model_lib as ml  # noqa: E402
import pipeline as pl  # noqa: E402
import placebo_direction  # noqa: E402


def pool_counts(family: str) -> dict:
    return {
        "confab_held_out": len(pl.load_rows(family, "confab", "held_out")),
        "known_correct_answered_held_out": len(
            pl.load_rows(family, "known_correct_answered", "held_out")
        ),
    }


def selected_rows(family: str, n_rows: int | None) -> list[dict]:
    confab = pl.load_rows(family, "confab", "held_out")
    known = pl.load_rows(family, "known_correct_answered", "held_out")
    if n_rows is None:
        return confab + known
    n_confab = n_rows // 2
    n_known = n_rows - n_confab
    return pl.stratified_subset(confab, n_confab) + pl.stratified_subset(known, n_known)


def load_midband_selected_doses(family: str, site_set: str = "midband",
                                kv_sharing: str = "on") -> dict[str, float]:
    """Gating-arm per-layer FIT-calibrated doses (calibrate_dose.py output). The
    late arm's dose is resolved separately (resolve_late_dose): it is
    non-gating and may be null, so it is NOT part of the mid-band dose map. Only
    the mid-band arm gates calibration success.

    `site_set` selects WHICH arm is the gating one and hence which
    calibrate_dose roll-up to read; the JSON key names are unchanged across
    site sets, so only the filename varies. `kv_sharing` scopes it the same
    way: an OFF arm must be dosed from the OFF calibration, because under
    cell.yaml `dose_ladder.dose_rule` the ratio rung is scaled by that
    condition's own median anchor norm."""
    path = HERE / "analysis-committed" / family / kv.condition_artifact(
        site_set_artifact("dose_calibration_summary.json", site_set), kv_sharing)
    data = json.loads(path.read_text())
    midband_names = {layer_dir_name(hs) for hs in resolve_site_set(load_family(family), site_set)}
    src = data.get("midband_selected_doses")
    if src is None:  # pre-option-B schema: filter the flat selected_doses map
        src = {k: v for k, v in data.get("selected_doses", {}).items() if k in midband_names}
    selected = {str(k): float(v) for k, v in src.items()}
    # Partial mid-band coverage is PERMITTED (user-approved 2026-07-24): R2's
    # registered roll-up semantics ("a family 'runs past G0' if its v2
    # calibration finds a usable dose and G0 passes") supersede this loader's
    # original all-midband precondition, which was written under the sign-time
    # assumption (true for Qwen3-4B) that every candidate would be usable.
    # Layers without a calibrated dose are never dosed downstream (see
    # _layer_dose_map); zero usable doses anywhere remains a hard stop -- that
    # family is a G0 dose-viability NOT-RUN and never reaches this script.
    if not selected:
        raise ValueError(
            f"[{family}] calibration summary has no usable mid-band dose at "
            f"any layer -- this family is a dose-viability NOT-RUN and "
            f"run_contrast should not have been invoked"
        )
    extra = set(selected) - midband_names
    if extra:
        raise ValueError(
            f"[{family}] calibration summary contains non-mid-band layers: "
            f"{sorted(extra)} (site set {site_set!r} is {sorted(midband_names)})"
        )
    return selected


def resolve_late_dose(family: str, cli_late_dose: float | None,
                      site_set: str = "midband",
                      kv_sharing: str = "on") -> float | None:
    """Late-arm dose resolution. Option (B) (RESOLVED 2026-07-23, lead+user):
    the late-site scalar dose is calibrated FRESH here with the same
    calibrate_dose.py ladder as the mid-band arm (doubt-snap selected no
    late-site dose for any family, so there is nothing to reuse verbatim; the
    frozen late-site DIRECTION/GATE are still reused verbatim). Priority:
    explicit --late-dose override, else the fresh late dose from this
    experiment's calibrate_dose.py summary
    (`late_reference_selected_dose.selected_dose`), else the family YAML
    `reuse.doubt_snap.late_site.resolved_late_dose` (legacy manual override),
    else None (no usable late dose -> late arm SKIPPED; the primary does not
    depend on it). This function never invents a dose."""
    if cli_late_dose is not None:
        return float(cli_late_dose)
    path = HERE / "analysis-committed" / family / kv.condition_artifact(
        site_set_artifact("dose_calibration_summary.json", site_set), kv_sharing)
    if path.exists():
        data = json.loads(path.read_text())
        block = data.get("late_reference_selected_dose") or {}
        dose = block.get("selected_dose")
        if dose is not None:
            return float(dose)
    ls = (load_family(family).get("reuse", {}).get("doubt_snap", {}) or {}).get("late_site", {}) or {}
    resolved = ls.get("resolved_late_dose")
    return float(resolved) if resolved is not None else None


def run_layers(
    family: str,
    rows: list[dict],
    hs_index_to_dose: dict[int, float],
    *,
    mode: str,
    fresh: bool = False,
    kv_sharing: str = "on",
) -> dict[str, dict]:
    """Run each requested layer's dosed pass for one family, checkpointing per
    row. `hs_index_to_dose` maps an hs_index (mid-band candidate or the late
    reference) to its dose; the late arm is included only if a dose was
    resolved for it (see resolve_late_dose)."""
    RunLog, _RunLogError = ml.load_run_log_class()
    model, tokenizer, _hidden_size, _n_layers = ml.load_model_and_tokenizer(family)
    try:
        layer_results: dict[str, dict] = {}
        for hs_index, dose in hs_index_to_dose.items():
            layer_name = layer_dir_name(hs_index)
            print(f"[contrast:{family}] layer={layer_name} dose={dose}", flush=True)
            gate_rows = pl.compute_gate_decisions(family, rows, hs_index,
                                                  kv_sharing=kv_sharing)
            # Run logs are condition-scoped: resuming an ON log under OFF would
            # silently interleave two conditions into one arm's records, and the
            # per-row `kv_sharing` field would be the only trace. `on` keeps the
            # historical path. run_config carries it too, so RunLog's own config
            # check is a second line of defence.
            log_path = (HERE / "analysis" / family / "runlog" / mode
                        / kv.condition_artifact(f"{layer_name}.jsonl", kv_sharing))
            run_log = RunLog(
                log_path,
                run_config={
                    "experiment": "j-space-cross-family-layer-contrast",
                    "family": family, "mode": mode, "layer": layer_name,
                    "hs_index": hs_index, "dose_target": dose,
                    "kv_sharing": kv_sharing,
                },
                fresh=fresh,
            )
            try:
                rec = pl.run_layer(family, model, tokenizer, hs_index, gate_rows, dose,
                                   run_log=run_log, kv_sharing=kv_sharing)
            finally:
                run_log.close()
            rec["dose_target"] = dose
            layer_results[layer_name] = rec
    finally:
        del model
        gc.collect()
        torch.cuda.empty_cache()
    return layer_results


def _passes_floor(rate_block: dict, floor: dict) -> bool:
    return bool(
        rate_block["rate"] >= floor["rate"]
        and rate_block["wilson_ci_95"][0] > floor["wilson_lower_ci"]
    )


def _passes_cap(rate_block: dict, cap: dict) -> bool:
    return bool(
        rate_block["rate"] <= cap["rate"]
        and rate_block["wilson_ci_95"][1] < cap["wilson_upper_ci"]
    )


def evaluate_primary(family: str, layer_results: dict[str, dict]) -> dict:
    """ABSOLUTE mid-band actuation gates (G1/G2) plus the descriptive late arm.

    Best mid-band = highest held-out confab clean_tighten, ties broken by lower
    known-correct cost. G1/G2 thresholds come from the family YAML primary_gate
    block. The late arm (if it ran) is reported descriptively; it gates nothing.
    """
    cfg = load_family(family)
    pg = cfg["primary_gate"]
    g1_floor = pg["g1_midband_clean_tighten_floor"]
    g2_cap = pg["g2_midband_known_correct_cost_cap"]

    late_hs = family_late_reference_hs(cfg)
    late_name = layer_dir_name(late_hs)
    mid_names = [n for n in layer_results if n != late_name]
    if not mid_names:
        raise ValueError(f"[{family}] no mid-band layer results to evaluate primary on")

    best_mid_name = max(
        mid_names,
        key=lambda name: (layer_results[name]["confab_tighten"]["rate"],
                          -layer_results[name]["known_correct_cost_control"]["rate"]),
    )
    best_mid = layer_results[best_mid_name]
    g1_pass = _passes_floor(best_mid["confab_tighten"], g1_floor)
    g2_pass = _passes_cap(best_mid["known_correct_cost_control"], g2_cap)

    out = {
        "family": family,
        "best_mid_layer": best_mid_name,
        "g1_floor_used": g1_floor,
        "g2_cap_used": g2_cap,
        "best_mid_confab_clean_tighten": best_mid["confab_tighten"],
        "best_mid_known_correct_cost": best_mid["known_correct_cost_control"],
        "g1_midband_actuation_floor_pass": g1_pass,
        "g2_midband_selectivity_cap_pass": g2_pass,
        "primary_pass": bool(g1_pass and g2_pass),
        "late_reference_layer": late_name,
    }

    # Secondary descriptive: only if the late arm actually ran.
    if late_name in layer_results:
        late = layer_results[late_name]
        out["secondary_late_reference"] = {
            "gating": "none",
            "late_confab_clean_tighten": late["confab_tighten"],
            "late_known_correct_cost": late["known_correct_cost_control"],
            "best_mid_minus_late_tighten_delta": (
                best_mid["confab_tighten"]["rate"] - late["confab_tighten"]["rate"]
            ),
            "best_mid_minus_late_cost_delta": (
                best_mid["known_correct_cost_control"]["rate"]
                - late["known_correct_cost_control"]["rate"]
            ),
        }
    else:
        out["secondary_late_reference"] = {
            "gating": "none",
            "status": "SKIPPED -- no usable late-arm dose found in fresh "
                      "calibration (expected per doubt-snap's late-site null); "
                      "the primary does not depend on the late arm.",
        }
    return out


def g0_smoke_pass(layer_results: dict[str, dict]) -> bool:
    for rec in layer_results.values():
        if rec["frac_readback_within_tol"] != 1.0:
            return False
        if rec["collapse_rate_on_dosed"] != 0.0:
            return False
    return True


def _layer_dose_map(family: str, late_dose: float | None,
                    site_set: str = "midband",
                    kv_sharing: str = "on") -> dict[int, float]:
    """The selected site set's candidates (always) + the late reference (only
    if a late dose is resolved)."""
    cfg = load_family(family)
    selected = load_midband_selected_doses(family, site_set, kv_sharing)
    dose_map: dict[int, float] = {}
    for hs_index in resolve_site_set(cfg, site_set):
        name = layer_dir_name(hs_index)
        if name in selected:  # only usable-dose (calibrated) sites are dosed
            dose_map[hs_index] = selected[name]
    if late_dose is not None:
        dose_map[family_late_reference_hs(cfg)] = late_dose
    return dose_map


def write_summary(family: str, name: str, summary: dict, commit_public: bool) -> None:
    analysis = HERE / "analysis" / family
    analysis.mkdir(parents=True, exist_ok=True)
    (analysis / name).write_text(json.dumps(summary, indent=2))
    if commit_public:
        committed = HERE / "analysis-committed" / family
        committed.mkdir(parents=True, exist_ok=True)
        (committed / name).write_text(json.dumps(summary, indent=2))


def run_smoke(family: str, n_rows: int, late_dose: float | None, *, fresh: bool = False,
              site_set: str = "midband", kv_sharing: str = "on") -> dict:
    dose_map = _layer_dose_map(family, late_dose, site_set, kv_sharing)
    rows = selected_rows(family, n_rows)
    layer_results = run_layers(family, rows, dose_map, mode="smoke", fresh=fresh,
                               kv_sharing=kv_sharing)
    summary = {
        "family": family, "mode": "smoke", "site_set": site_set, "kv_sharing": kv_sharing,
        "layer_doses": {layer_dir_name(k): v for k, v in dose_map.items()},
        "late_arm_included": late_dose is not None,
        "pool_counts": pool_counts(family), "n_rows": len(rows), "layers": layer_results,
        "g0_smoke_pass": g0_smoke_pass(layer_results),
    }
    write_summary(family,
                  kv.condition_artifact(site_set_artifact("smoke_summary.json", site_set),
                                        kv_sharing),
                  summary, commit_public=False)
    print(json.dumps(summary, indent=2))
    return summary


def run_full(family: str, late_dose: float | None, *, fresh: bool = False,
             site_set: str = "midband", kv_sharing: str = "on") -> dict:
    dose_map = _layer_dose_map(family, late_dose, site_set, kv_sharing)
    rows = selected_rows(family, None)
    rng = pyrandom.Random(20260708)
    rng.shuffle(rows)
    layer_results = run_layers(family, rows, dose_map, mode="full", fresh=fresh,
                               kv_sharing=kv_sharing)
    primary = evaluate_primary(family, layer_results)
    summary = {
        "family": family, "mode": "full", "site_set": site_set, "kv_sharing": kv_sharing,
        "layer_doses": {layer_dir_name(k): v for k, v in dose_map.items()},
        "late_arm_included": late_dose is not None,
        "pool_counts": pool_counts(family), "n_rows": len(rows), "layers": layer_results,
        "primary": primary,
        "primary_pass": bool(g0_smoke_pass(layer_results) and primary["primary_pass"]),
    }
    write_summary(family,
                  kv.condition_artifact(site_set_artifact("full_summary.json", site_set),
                                        kv_sharing),
                  summary, commit_public=True)
    print(json.dumps(summary, indent=2))
    return summary


# ---------------------------------------------------------------------------
# ARM KINDS: placebo (P1/P2/P3, cell.yaml placebo_direction_control) and
# undosed (the baseline pass g2's undosed_floor and g3's lift both require).
# Both are registered ONLY for the site set(s) cell.yaml
# `registered_control_site_sets` lists. Neither touches the `true` arm-kind
# code path above, which stays byte-for-byte as originally signed.
#
# INSTRUMENT DELTA from the quarantine cell this file was copied from: the
# original hardcoded a module-level `PLACEBO_REGISTERED_SITE_SET = "seam_pair"`
# constant. This experiment's arms (E1/E2/E3 at hs25/hs26/hs27) live under
# `--site-set pocket`, which the hardcoded constant would refuse outright, so
# both G3 and the undosed baseline would be unexecutable. Resolving the
# registered set from cell.yaml instead keeps the refusal behavior for any
# site set NOT listed there -- this is a generalization of the check, not a
# removal of it. Registered here rather than re-hardcoded to "pocket" so a
# future copy of this file does not have to repeat the same fix.
# ---------------------------------------------------------------------------

def registered_control_site_sets(root: Path = HERE) -> list[str]:
    """The site set(s) `--arm-kind placebo`/`undosed` are registered for,
    read from this experiment's own `cell.yaml registered_control_site_sets`
    key. Raises if the key is missing or empty rather than falling back to
    any default, so an unregistered cell.yaml fails closed the same way an
    unregistered site set does."""
    import yaml
    cell_path = root / "cell.yaml"
    data = yaml.safe_load(cell_path.read_text(encoding="utf-8"))
    values = data.get("registered_control_site_sets")
    if not values:
        raise ValueError(
            f"{cell_path}: registered_control_site_sets not present or empty "
            "-- --arm-kind placebo/undosed have no registered site set to run "
            "against and must not silently default to one."
        )
    return list(values)


def force_undosed(gate_rows: list[dict]) -> list[dict]:
    """Copy of `gate_rows` with every row's `fire` forced False -- the arm's
    own undosed pass (no injection anywhere), used verbatim by both G2's
    `undosed_floor` companion and G3's lift baseline. Does NOT re-gate; the
    original gate decision is simply not acted on."""
    return [{**row, "fire": False} for row in gate_rows]


def true_arm_run_log_path(root: Path, family: str, hs_index: int, mode: str,
                          kv_sharing: str) -> Path:
    layer_name = layer_dir_name(hs_index)
    return (root / "analysis" / family / "runlog" / mode
            / kv.condition_artifact(f"{layer_name}.jsonl", kv_sharing))


def load_true_arm_fire_flags(root: Path, family: str, hs_index: int, mode: str,
                             kv_sharing: str) -> dict[str, bool]:
    """Read the matched TRUE arm's own run log for its per-row fire
    decisions. cell.yaml fired_row_matching: the placebo writes at EXACTLY
    the rows the TRUE gate fired; it is NEVER re-gated and the gate indices
    are NEVER permuted. Fails closed (naming the missing stage) if that
    arm has not been run yet -- a placebo control cannot invent a fire set
    of its own."""
    log_path = true_arm_run_log_path(root, family, hs_index, mode, kv_sharing)
    if not log_path.is_file():
        raise FileNotFoundError(
            f"[placebo] true arm run log not found at {log_path}. The "
            f"placebo control writes at EXACTLY the rows the TRUE gate "
            f"fired (cell.yaml fired_row_matching) and cannot construct its "
            f"own fire set -- run `--arm-kind true --site-set pocket "
            f"--mode {mode} --kv-sharing {kv_sharing}` for hs{hs_index} first."
        )
    records = pl.load_jsonl(log_path)
    return {r["key"]: bool(r["fire"]) for r in records}


def run_undosed_baseline(family: str, hs_index: int, dose_target: float, *,
                         mode: str, n_rows: int, fresh: bool, site_set: str,
                         kv_sharing: str, dry_run: bool, root: Path = HERE) -> dict:
    """The arm's own undosed pass over its (mode-scoped) held-out rows.
    cell.yaml placebo_direction_control.undosed_baseline_required: "Each of
    P1/P2's matched true arms (A3, A5) must also run an UNDOSED pass over
    the same held-out confab rows... a lift cannot be computed without it."
    """
    rows = selected_rows(family, n_rows if mode == "smoke" else None)
    gate_rows = pl.compute_gate_decisions(family, rows, hs_index, kv_sharing=kv_sharing)
    forced_rows = force_undosed(gate_rows)
    layer_name = layer_dir_name(hs_index)

    if dry_run:
        return {
            "family": family, "arm_kind": "undosed", "dry_run": True,
            "hs_index": hs_index, "layer": layer_name, "site_set": site_set,
            "kv_sharing": kv_sharing, "mode": mode, "n_rows": len(forced_rows),
        }

    RunLog, _RunLogError = ml.load_run_log_class()
    model, tokenizer, _hidden_size, _n_layers = ml.load_model_and_tokenizer(family)
    try:
        log_path = (root / "analysis" / family / "runlog" / "undosed" / mode
                    / kv.condition_artifact(f"{layer_name}.jsonl", kv_sharing))
        run_log = RunLog(
            log_path,
            run_config={
                "experiment": "gemma4-e4b-pocket-ladder", "family": family,
                "arm_kind": "undosed", "mode": mode, "layer": layer_name,
                "hs_index": hs_index, "kv_sharing": kv_sharing,
            },
            fresh=fresh,
        )
        try:
            rec = pl.run_layer(family, model, tokenizer, hs_index, forced_rows, dose_target,
                               run_log=run_log, kv_sharing=kv_sharing)
        finally:
            run_log.close()
    finally:
        del model
        gc.collect()
        torch.cuda.empty_cache()

    summary = {
        "family": family, "arm_kind": "undosed", "site_set": site_set,
        "kv_sharing": kv_sharing, "mode": mode, "hs_index": hs_index,
        "dose_target_of_matched_true_arm": dose_target, "layer": rec,
    }
    write_summary(
        family,
        kv.condition_artifact(
            family_config.site_set_artifact(f"undosed_summary.{layer_name}.json", site_set),
            kv_sharing),
        summary, commit_public=True,
    )
    return summary


def run_placebo(family: str, hs_index: int, dose_target: float, k: int, *,
                mode: str, n_rows: int, fresh: bool, site_set: str,
                kv_sharing: str, dry_run: bool, root: Path = HERE) -> dict:
    """P1/P2/P3: K SC1-screened random directions written at exactly the TRUE
    arm's fired rows and dose (cell.yaml placebo_direction_control). Raises
    `placebo_direction.PlaceboRedrawExhausted` (caller records NOT-RUN) if
    SC1 screening cannot find K acceptable directions within max_redraws."""
    registered = registered_control_site_sets(root)
    if site_set not in registered:
        raise ValueError(
            f"[placebo] --site-set {site_set!r} is not registered for the "
            f"placebo control (cell.yaml registered_control_site_sets: "
            f"{registered!r})"
        )
    layer_name = layer_dir_name(hs_index)
    fire_by_key = load_true_arm_fire_flags(root, family, hs_index, mode, kv_sharing)
    rows = selected_rows(family, n_rows if mode == "smoke" else None)
    missing = [row["row_key"] for row in rows if row["row_key"] not in fire_by_key]
    if missing:
        raise ValueError(
            f"[placebo] {len(missing)} row(s) in this arm-kind's population have "
            f"no fire decision in the true arm's run log (population drift "
            f"since the true arm ran); first missing key: {missing[0]!r}"
        )
    # hs_index is stamped here because this path deliberately skips
    # compute_gate_decisions (fired-row matching, never re-gated), but
    # run_one_row still requires row["hs_index"] like every other arm-kind.
    gate_rows = [{**row, "hs_index": hs_index, "fire": fire_by_key[row["row_key"]]}
                 for row in rows]

    paths = pl.layer_paths(family, hs_index, kv_sharing)
    c_hat = pl.load_direction_vector(paths["c_hat"])
    u_d = pl.load_direction_vector(paths["u_d"])
    hidden_dim = int(c_hat.shape[0])

    accepted, ledger = placebo_direction.screen_k_accepted_directions(
        hidden_dim, hs_index, c_hat, u_d, k=k)
    ledger_path = (root / "analysis-committed" / family
                   / family_config.site_set_artifact("placebo_draw_ledger.json", site_set))
    placebo_direction.write_ledger(ledger_path, ledger, hs_index=hs_index, hidden_dim=hidden_dim, k=k)

    n_fired = sum(1 for v in fire_by_key.values() if v)
    if dry_run:
        return {
            "family": family, "arm_kind": "placebo", "dry_run": True,
            "hs_index": hs_index, "layer": layer_name, "site_set": site_set,
            "kv_sharing": kv_sharing, "mode": mode, "k": k,
            "n_accepted_directions": len(accepted), "n_ledger_entries": len(ledger),
            "n_fired_rows": n_fired, "n_rows": len(gate_rows),
            "ledger_path": str(ledger_path),
        }

    RunLog, _RunLogError = ml.load_run_log_class()
    model, tokenizer, _hidden_size, _n_layers = ml.load_model_and_tokenizer(family)
    per_draw = []
    try:
        for k_index, direction in enumerate(accepted):
            sigma, gain = placebo_direction.placebo_write_params(dose_target)
            log_path = (root / "analysis" / family / "runlog" / "placebo" / mode
                        / kv.condition_artifact(f"{layer_name}.k{k_index}.jsonl", kv_sharing))
            run_log = RunLog(
                log_path,
                run_config={
                    "experiment": "gemma4-e4b-pocket-ladder", "family": family,
                    "arm_kind": "placebo", "mode": mode, "layer": layer_name,
                    "hs_index": hs_index, "k_index": k_index, "dose_target": dose_target,
                    "sigma": sigma, "kv_sharing": kv_sharing,
                },
                fresh=fresh,
            )
            try:
                rec = pl.run_layer_with_direction(
                    family, model, tokenizer, hs_index, gate_rows, dose_target,
                    direction, sigma=sigma, run_log=run_log, kv_sharing=kv_sharing)
            finally:
                run_log.close()
            rec["k_index"] = k_index
            per_draw.append(rec)
    finally:
        del model
        gc.collect()
        torch.cuda.empty_cache()

    summary = {
        "family": family, "arm_kind": "placebo", "site_set": site_set,
        "kv_sharing": kv_sharing, "mode": mode, "hs_index": hs_index,
        "dose_target": dose_target, "k": k, "n_fired_rows": n_fired,
        "ledger_path": str(ledger_path), "per_draw": per_draw,
    }
    write_summary(
        family,
        kv.condition_artifact(
            family_config.site_set_artifact(f"placebo_summary.{layer_name}.json", site_set),
            kv_sharing),
        summary, commit_public=True,
    )
    return summary


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--family", required=True, choices=FAMILY_SLUGS)
    parser.add_argument("--site-set", default="midband", choices=sorted(SITE_SETS),
                        help="named site set from families/<family>.yaml "
                             "band_selection. Default 'midband' preserves the "
                             "pre-existing behaviour exactly.")
    parser.add_argument(
        "--kv-sharing", default=kv.DEFAULT_KV_SHARING, choices=list(kv.KV_SHARING_CHOICES),
        help="KV-sharing condition for KV-sharing architectures. 'on' (default) "
             "is the native architecture; 'off' is the A2 counterfactual arm, "
             "which severs the donor seam. Both arms pass a FRESH full-length "
             "cache on every generate() call (CALLER CONTRACT, cell.yaml) so the "
             "cache object is constant across arms. Outputs are condition-scoped: "
             "'off' writes <stem>.kv_off.<ext>, never over the 'on' artifacts.",
    )
    parser.add_argument("--mode", choices=["smoke", "full"], required=True)
    parser.add_argument("--n-rows", type=int, default=8, help="smoke mode only")
    parser.add_argument(
        "--late-dose", type=float, default=None,
        help="Override the SECONDARY late-reference arm's dose. If omitted, the "
             "fresh late dose from calibrate_dose.py's summary "
             "(late_reference_selected_dose) is used (option B); if that is null "
             "too, the late arm is SKIPPED and only the primary (mid-band) gates "
             "are evaluated.",
    )
    parser.add_argument(
        "--arm-kind", choices=["true", "placebo", "undosed"], default="true",
        help="'true' (default) is the pre-existing gating/descriptive arm "
             "path, unchanged. 'placebo' runs the P1/P2/P3 direction-"
             "specificity control at the matched true arm's site and dose, "
             "on the SAME fired rows (cell.yaml placebo_direction_control); "
             "only registered for the site set(s) in cell.yaml "
             "registered_control_site_sets. 'undosed' runs the undosed "
             "baseline pass g2's undosed_floor and g3's lift both require.",
    )
    parser.add_argument(
        "--placebo-k", type=int, default=placebo_direction.K,
        help="Number of SC1-screened placebo draws. LOCKED at 5 by the lead "
             "(cell.yaml k_number_of_draws) -- do not override for a "
             "registered run; this flag exists for CPU testing only.",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Resolve rows, doses, and (for --arm-kind placebo) the SC1 "
             "draw/screen ledger entirely on CPU, print the plan, and exit "
             "WITHOUT loading the model. No generation occurs. Composes "
             "with every other flag, including --kv-sharing.",
    )
    parser.add_argument("--i-know-this-is-the-cross-family-run", action="store_true")
    resume_group = parser.add_mutually_exclusive_group()
    resume_group.add_argument(
        "--resume", dest="fresh", action="store_false", default=False,
        help="Resume from each layer's existing run log, skipping already-done rows (default).",
    )
    resume_group.add_argument(
        "--fresh", dest="fresh", action="store_true",
        help="Discard each layer's existing run log for this family/mode and start over.",
    )
    args = parser.parse_args(argv)

    if args.arm_kind != "true":
        registered = registered_control_site_sets()
        if args.site_set not in registered:
            print(
                f"[contrast] --arm-kind {args.arm_kind!r} is only registered "
                f"for --site-set in {registered!r} (cell.yaml "
                "registered_control_site_sets)", file=sys.stderr,
            )
            return 2

    if args.arm_kind in ("placebo", "undosed"):
        cfg = load_family(args.family)
        hs_list = resolve_site_set(cfg, args.site_set)
        dose_map = load_midband_selected_doses(args.family, args.site_set, args.kv_sharing)
        results: dict[str, dict] = {}
        exit_code = 0
        for hs_index in hs_list:
            layer_name = layer_dir_name(hs_index)
            if layer_name not in dose_map:
                print(f"[contrast] {layer_name} has no usable FIT dose; its "
                      f"{args.arm_kind} pass is NOT-RUN (matches the true "
                      "arm's own dose-viability NOT-RUN)", file=sys.stderr)
                results[layer_name] = {"status": "NOT-RUN",
                                       "reason": "true arm has no usable FIT dose"}
                continue
            dose_target = dose_map[layer_name]
            try:
                if args.arm_kind == "undosed":
                    results[layer_name] = run_undosed_baseline(
                        args.family, hs_index, dose_target, mode=args.mode,
                        n_rows=args.n_rows, fresh=args.fresh, site_set=args.site_set,
                        kv_sharing=args.kv_sharing, dry_run=args.dry_run)
                else:
                    results[layer_name] = run_placebo(
                        args.family, hs_index, dose_target, args.placebo_k,
                        mode=args.mode, n_rows=args.n_rows, fresh=args.fresh,
                        site_set=args.site_set, kv_sharing=args.kv_sharing,
                        dry_run=args.dry_run)
            except placebo_direction.PlaceboRedrawExhausted as exc:
                print(f"[contrast] {layer_name} placebo: {exc}", file=sys.stderr)
                results[layer_name] = {"status": "NOT-RUN", "reason": str(exc)}
                exit_code = 4
        print(json.dumps(results, indent=2, default=str))
        return exit_code

    late_dose = resolve_late_dose(args.family, args.late_dose, args.site_set,
                                  args.kv_sharing)

    if args.mode == "smoke":
        smoke = run_smoke(args.family, args.n_rows, late_dose, fresh=args.fresh,
                          site_set=args.site_set, kv_sharing=args.kv_sharing)
        return 0 if smoke["g0_smoke_pass"] else 4

    if not args.i_know_this_is_the_cross_family_run:
        print(
            "[contrast] full mode is the signed cross-family outcome run; refusing "
            "without --i-know-this-is-the-cross-family-run",
            file=sys.stderr,
        )
        return 2
    run_full(args.family, late_dose, fresh=args.fresh, site_set=args.site_set,
             kv_sharing=args.kv_sharing)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
