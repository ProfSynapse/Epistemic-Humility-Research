"""G0-C1 precondition control producer (gates.yaml g0_c1_precondition_control,
lines 204-249 at authoring time).

NEW module -- not modifying rollup.py / cell.yaml / gates.yaml. Fills the
instrument gap found while building the Phase B Modal harness
(cloud/PHASE_B_MODAL_PLAN.md "Gap 1"): rollup.py `build_rollup()` unconditionally
reads `analysis-committed/<family>/c1_precondition_summary.json`
(rollup.py ~401-408) and gates.yaml registers the measurement that file must
contain, but no script previously produced it.

SCOPE (gates.yaml g0_c1_precondition_control, "scope"): FIT split, C0 (sharing
ON) vs C1 (sharing OFF), NO injection in either condition, evaluated before
any OFF arm (A2, A4) is scored on held-out.

PASS_IF_ALL -- this script computes the raw rate/NLL blocks; the actual
pass/fail arithmetic is NOT reimplemented here, it is imported verbatim from
`rollup.c1_verdict` (already registered and tested, see test_rollup.py). The
three criteria it transcribes (gates.yaml g0_c1_precondition_control.pass_if_all):

  1. known_correct_preserved (gates.yaml ~212-220): abs(C1 - C0) delta on
     undosed `not_well_formed_correct` over FIT known_correct_answered rows
     <= 0.05 (rollup.C1_KNOWN_CORRECT_ABS_DELTA_CAP), AND the 95% Newcombe
     hybrid-score interval on the C1-minus-C0 difference excludes a
     degradation > 0.10 (rollup.C1_KNOWN_CORRECT_WILSON_DEGRADE_CAP).
  2. off_model_does_not_hedge (gates.yaml ~221-227): C1 undosed confab
     `clean_tighten` rate <= 0.05 (rollup.C1_HEDGE_RATE_CAP).
  3. likelihood_preserved (gates.yaml ~228-243, threshold_frac 0.10,
     resolved_by_lead CLOSED 2026-07-25): teacher-forced mean per-token NLL
     over the FIT rows, C1 vs C0, within 10% relative
     (rollup.C1_NLL_REL_TOLERANCE).

INTERPRETATION FLAG for lead review (not asserted as registered fact):
gates.yaml's likelihood_preserved criterion scores NLL "over the FIT rows'
rendered prompt plus reference completion" without defining "reference
completion" anywhere in AMENDMENT.md / gates.yaml / cell.yaml. Confab rows
have no ground-truth answer by construction (that is their premise), so a
single canonical gold completion does not exist for the whole FIT population.
This script teacher-forces each row's OWN model-generated completion from
this run's undosed pass (the same `base_text` used for clean_tighten /
well_formed_correct grading), scored under a SEPARATE single-shot forward
with `labels=`. That checks generate()-vs-forward() consistency under the
KV-seam patch -- exactly what gates.yaml's own justification names ("the
sharpest cheap indicator of an intact forward pass" / "a model can keep its
answer rates while its attention routing is subtly wrong") -- but it is a
reading, not a registered definition, and should be confirmed or corrected
before this module is recorded in the instrument.

CACHE CONTRACT (cell.yaml cache_contract.applies_to: "ALL arms and ALL
conditions (A1-A6, C0, C1; dosed and undosed)"): every forward pass in this
script -- the undosed generation AND the teacher-forced NLL forward -- gets a
FRESH `build_full_length_cache()` Cache via `pl.kv_condition_context`'s
cache_factory, in both kv_sharing conditions. `use_cache=True` on every
forward is a correctness requirement here, not a performance knob (see
extract_anchor.py's inline comment: with use_cache=False the KV-shared blocks
starve and hs25+ go from cos 0.998+ to 0.075).

NO SITE (cell.yaml arms: C0/C1 both register `site_hs: null`): this arm has no
fitted direction of its own. The tuner's `GenerationInterventionController`
hook machinery is still a mechanical requirement of `gen_lib.run_pass_fixed`
even for a pure no-op pass (a hook must be attached to some real decoder
layer). This script builds an INERT hook via `model_lib.setup_hook_from_vector`
at hs22 (block 21, `family_config.hs_to_block(22) == 21`) -- the below-seam
donor site already structurally validated in Phase A (AMENDMENT.md A3
tie-break) -- with sigma=1.0 and mode="off"/strength=0.0 on every single row
(no row ever fires; see `_force_off` below, matching
`run_contrast.py.force_undosed`'s identical semantics). Phase A's Stage 3
undosed baseline already empirically confirmed a hook is inert under these
conditions regardless of the site or direction chosen -- this script never
takes the dosed branch at all, so the vector's content is provably
irrelevant to every measured number.

Reuses (does not reimplement):
  - pl.load_rows(family, role, "fit")        [pipeline.py -- split-parameterized]
  - pl.kv_condition_context(family, model, kv_sharing)  [pipeline.py -- the cache
    CALLER CONTRACT]
  - pl.summarize_layer_records(...)          [pipeline.py -- the LOCKED
    confab_tighten / known_correct_cost_control aggregation]
  - ml.load_model_and_tokenizer / ml.render / ml.resolve_eos_ids /
    ml.setup_hook_from_vector / ml.wilson_ci   [model_lib.py]
  - gl.run_pass_fixed / gl.grade_clean_tighten  [gen_lib.py -- the LOCKED
    generation contract + confab-hedging grader]
  - grader.grade_one                         [grader.py -- the LOCKED
    known-correct well-formedness grader]
  - rollup.c1_verdict + its four named constants  [rollup.py -- the LOCKED
    pass/fail arithmetic, imported not copied]

Writes `analysis-committed/<family>/c1_precondition_summary.json` in exactly
the shape `rollup.build_rollup()` reads (rollup.py ~401-408):
    {"c0": {"known_correct_cost_control": {...}, "confab_tighten": {...},
            "mean_nll": float, ...},
     "c1": {same three keys, ...}}
"""

from __future__ import annotations

import argparse
import gc
import json
import sys
from pathlib import Path

import numpy as np
import torch

HERE = Path(__file__).resolve().parent

import gen_lib as gl  # noqa: E402
import grader  # noqa: E402
import model_lib as ml  # noqa: E402
import pipeline as pl  # noqa: E402
from family_config import hs_to_block  # noqa: E402
from MechInterp.intervention import get_decoder_layer  # noqa: E402
from rollup import (  # noqa: E402
    C1_HEDGE_RATE_CAP,
    C1_KNOWN_CORRECT_ABS_DELTA_CAP,
    C1_KNOWN_CORRECT_WILSON_DEGRADE_CAP,
    C1_NLL_REL_TOLERANCE,
    c1_verdict,
)

# Inert mechanical vehicle for gen_lib.run_pass_fixed's controller/hook
# requirement. C0/C1 register site_hs: null (cell.yaml) -- there is no fitted
# direction to reuse, and none is needed: every row below forces fire=False,
# so `mode="off", strength=0.0` never takes the write branch, and the site
# choice is inert by construction (see module docstring "NO SITE").
INERT_HOOK_HS_INDEX = 22
INERT_HOOK_SIGMA = 1.0


def _force_off(rows: list[dict]) -> list[dict]:
    """Same semantics as run_contrast.py's `force_undosed`: every row gets
    `fire=False` (no injection anywhere), which is this arm's entire
    registered scope (gates.yaml g0_c1_precondition_control.scope: "no
    injection in either condition")."""
    return [{**row, "fire": False} for row in rows]


def _inert_direction_vector(hidden_size: int) -> np.ndarray:
    # Fixed seed -> reproducible artifact across re-runs; content is inert
    # (see module docstring) so any fixed unit vector is equally valid.
    rng = np.random.default_rng(0)
    v = rng.normal(size=hidden_size).astype(np.float32)
    return v / np.linalg.norm(v)


def _teacher_forced_nll(model, dev, enc: dict, new_tokens: torch.Tensor,
                        cache_factory) -> float:
    """Mean per-token cross-entropy over the rendered prompt PLUS this row's
    own greedy completion (see module docstring "INTERPRETATION FLAG"). A
    SEPARATE single-shot forward from the generation call above -- the cache
    contract requires a FRESH Cache per forward, not a reused one (a Cache is
    stateful; see extract_anchor.py / kv_seam_patch.build_full_length_cache).
    use_cache=True for the same reason as every other forward in this
    experiment: on gemma4-e4b, False starves the KV-shared blocks."""
    full_ids = torch.cat([enc["input_ids"], new_tokens.unsqueeze(0)], dim=1)
    full_attn = torch.ones_like(full_ids)
    fwd_kwargs = {}
    if cache_factory is not None:
        fwd_kwargs["past_key_values"] = cache_factory()
    with torch.no_grad():
        out = model(input_ids=full_ids, attention_mask=full_attn,
                    use_cache=True, labels=full_ids, **fwd_kwargs)
    return float(out.loss.item())


def run_condition(family: str, model, tokenizer, rows: list[dict], *,
                  kv_sharing: str, dev, eos_ids: list[int]) -> dict:
    """One KV condition's full undosed pass + teacher-forced NLL over `rows`
    (already both roles, FIT split). Returns the per-condition block
    `c1_precondition_summary.json` needs (confab_tighten,
    known_correct_cost_control, mean_nll, plus provenance).

    Does not call `pl.run_one_row` / `pl.run_layer_with_direction` directly:
    both hide the raw generated tokens behind grade-only return dicts, and
    the NLL criterion needs those tokens. Instead this reproduces
    `run_one_row`'s fire=False branch inline (same two graders, same
    `gl.run_pass_fixed` call) so the tokens stay in hand for
    `_teacher_forced_nll`, then hands the resulting per-row records to
    `pl.summarize_layer_records` -- the SAME LOCKED aggregation
    `run_layer_with_direction` itself calls -- unchanged.
    """
    layer_idx = hs_to_block(INERT_HOOK_HS_INDEX)
    vector = _inert_direction_vector(model.config.get_text_config().hidden_size
                                     if hasattr(model.config, "get_text_config")
                                     else model.config.hidden_size)
    hook, controller, _li, _sigma = ml.setup_hook_from_vector(
        vector, INERT_HOOK_SIGMA, layer_idx)
    layer_module = get_decoder_layer(model, layer_idx)
    h_ctrl = layer_module.register_forward_hook(controller)
    kv_ctx, cache_factory = pl.kv_condition_context(family, model, kv_sharing)

    records: list[dict] = []
    nlls: list[float] = []
    try:
        with kv_ctx:
            for row in rows:
                assert row["fire"] is False, "C0/C1 scope: no injection in either condition"
                prompt = ml.render(family, tokenizer, row)
                enc = tokenizer(prompt, return_tensors="pt").to(dev)
                _out, _rb, terminated_naturally, new_tokens = gl.run_pass_fixed(
                    model, controller, enc, "off", 0.0, tokenizer, eos_ids,
                    max_new=pl.MAX_NEW, cache_factory=cache_factory,
                )
                text = tokenizer.decode(new_tokens, skip_special_tokens=True)
                ct = gl.grade_clean_tighten(text, terminated_naturally)
                og = grader.grade_one(text, row.get("aliases"))
                records.append({
                    "row_key": row["row_key"], "role": row["role"],
                    "category_canon": row.get("category_canon"),
                    "fire": False, "readback_measured": None,
                    "n_new_tokens": int(new_tokens.shape[0]),
                    "terminated_naturally": terminated_naturally,
                    "clean_tighten": ct["clean_tighten"],
                    "semantic_refuse": ct["semantic_refuse"],
                    "well_formed_correct": og["well_formed_correct"],
                    "not_well_formed_correct": not og["well_formed_correct"],
                    "grade": ct, "old_grade": og, "kv_sharing": kv_sharing,
                })
                nlls.append(_teacher_forced_nll(model, dev, enc, new_tokens, cache_factory))
    finally:
        h_ctrl.remove()
        controller.reset()

    summary = pl.summarize_layer_records(
        records, 0.0, hs_index=INERT_HOOK_HS_INDEX, kv_sharing=kv_sharing)
    summary["mean_nll"] = float(np.mean(nlls)) if nlls else None
    summary["n_nll_rows"] = len(nlls)
    summary["inert_hook_hs_index"] = INERT_HOOK_HS_INDEX
    return summary


def build_summary(family: str, *, n_rows: int | None, dev, model=None, tokenizer=None,
                  eos_ids=None) -> dict:
    """`n_rows`: None runs the full FIT population; an int takes a
    category-stratified subset per role (matching `run_contrast.py`'s own
    smoke convention) -- used only for the CPU-safe self-test, which stubs
    `model`/`tokenizer`/`eos_ids` in and never actually generates."""
    confab = pl.load_rows(family, "confab", "fit")
    known = pl.load_rows(family, "known_correct_answered", "fit")
    if n_rows is not None:
        confab = pl.stratified_subset(confab, n_rows)
        known = pl.stratified_subset(known, n_rows)
    rows = _force_off(confab + known)

    out = {"family": family, "split": "fit", "n_confab": len(confab),
          "n_known_correct_answered": len(known)}
    for kv_sharing in ("on", "off"):
        cond = run_condition(family, model, tokenizer, rows, kv_sharing=kv_sharing,
                             dev=dev, eos_ids=eos_ids)
        out["c0" if kv_sharing == "on" else "c1"] = cond
    return out


def verdict_from_summary(summary: dict) -> dict:
    return c1_verdict(
        c0_known_correct_cost=summary["c0"]["known_correct_cost_control"],
        c1_known_correct_cost=summary["c1"]["known_correct_cost_control"],
        c1_confab_clean_tighten=summary["c1"]["confab_tighten"],
        c0_mean_nll=summary["c0"]["mean_nll"], c1_mean_nll=summary["c1"]["mean_nll"],
    )


def write_summary(family: str, summary: dict) -> Path:
    committed = HERE / "analysis-committed" / family
    committed.mkdir(parents=True, exist_ok=True)
    out_path = committed / "c1_precondition_summary.json"
    out_path.write_text(json.dumps(summary, indent=2))
    return out_path


def run(family: str, *, smoke_n: int | None, dry_run: bool) -> int:
    confab = pl.load_rows(family, "confab", "fit")
    known = pl.load_rows(family, "known_correct_answered", "fit")
    plan = {
        "family": family, "split": "fit", "smoke_n": smoke_n,
        "n_confab_fit": len(confab), "n_known_correct_answered_fit": len(known),
        "inert_hook_hs_index": INERT_HOOK_HS_INDEX,
        "criteria_transcribed": [
            "gates.yaml g0_c1_precondition_control.pass_if_all.known_correct_preserved",
            "gates.yaml g0_c1_precondition_control.pass_if_all.off_model_does_not_hedge",
            "gates.yaml g0_c1_precondition_control.pass_if_all.likelihood_preserved",
        ],
        "caps": {
            "known_correct_abs_delta_cap": C1_KNOWN_CORRECT_ABS_DELTA_CAP,
            "known_correct_wilson_degrade_cap": C1_KNOWN_CORRECT_WILSON_DEGRADE_CAP,
            "hedge_rate_cap": C1_HEDGE_RATE_CAP,
            "nll_rel_tolerance": C1_NLL_REL_TOLERANCE,
        },
    }
    if dry_run:
        print(json.dumps(plan, indent=2))
        return 0

    model, tokenizer, _hidden_size, _n_layers = ml.load_model_and_tokenizer(family)
    dev = next(model.parameters()).device
    eos_ids = ml.resolve_eos_ids(family, tokenizer)
    try:
        summary = build_summary(family, n_rows=smoke_n, dev=dev, model=model,
                                tokenizer=tokenizer, eos_ids=eos_ids)
    finally:
        del model
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    verdict = verdict_from_summary(summary)
    summary["verdict"] = verdict
    out_path = write_summary(family, summary)
    print(json.dumps({"out_path": str(out_path), "verdict": verdict}, indent=2))
    return 0


def parse_args(argv=None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--family", required=True)
    ap.add_argument("--smoke", type=int, default=None, metavar="N",
                    help="category-stratified subset of N rows per role instead "
                         "of the full FIT population (matches run_contrast.py's "
                         "own smoke convention). Default: full FIT population.")
    ap.add_argument("--dry-run", action="store_true",
                    help="print the row-count plan and registered caps; no "
                         "model load, no GPU, $0.")
    return ap.parse_args(argv)


if __name__ == "__main__":
    args = parse_args()
    raise SystemExit(run(args.family, smoke_n=args.smoke, dry_run=args.dry_run))
