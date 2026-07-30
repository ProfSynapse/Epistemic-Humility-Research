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

C1 NLL INTERPRETATION -- RULED by lead 2026-07-30 (supersedes this module's
original interpretation flag; will be recorded in NOTEBOOK.md when the module
is registered in the instrument). gates.yaml's likelihood_preserved criterion
scores NLL "over the FIT rows' rendered prompt plus reference completion"
without defining "reference completion" in AMENDMENT.md / gates.yaml /
cell.yaml. RULING: "reference completion" is singular -- one text per row --
so it is the row's C0 (sharing ON) greedy completion, teacher-forced under
BOTH conditions (identical text, paired per row, mean over rows, then the
unchanged rollup.c1_verdict 10% relative check). Rationale: scoring each
condition's OWN completion (this module's original design) conflates a text
change with a likelihood change and overlaps criterion 1's job; a FIXED
reference text isolates the seam flip, matching gates.yaml's own
justification ("keep its answer rates while its attention routing is subtly
wrong"). Ordering: C0 runs first and generates the reference; its per-row
completion tokens are threaded into C1's NLL pass (`build_summary` /
`run_condition`'s `reference_completions` parameter). The original
own-completion NLL design is RETAINED per condition as a descriptive,
NON-GATING diagnostic field (`own_completion_mean_nll`) -- a fine
generate()-vs-forward() coherence check, just not the registered criterion;
`c1_verdict` is fed only the paired reference-completion `mean_nll`.

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
            "mean_nll": float,  # paired reference-completion NLL (== C0's
                                 # own-completion NLL, since C0 IS the
                                 # reference), fed to c1_verdict
            "own_completion_mean_nll": float,  # diagnostic only, unused by
                                                 # c1_verdict
            ...},
     "c1": {same keys; "mean_nll" is C0's reference text teacher-forced
            under C1's KV condition (paired per row), "own_completion_mean_nll"
            is C1's own generated completion teacher-forced under C1 --
            descriptive only, ...}}
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


def _validate_reference_completions(kv_sharing: str,
                                    reference_completions: dict | None) -> None:
    """C1 NLL interpretation ruling (lead, 2026-07-30): the registered
    "reference completion" is C0's own greedy completion, teacher-forced
    under BOTH conditions. C0 (kv_sharing == 'on') generates that reference
    itself and must not be handed one (it would be scoring C0 against some
    OTHER condition's text, which is not the ruling). C1 (kv_sharing ==
    'off') cannot compute the paired/gating NLL without it."""
    if kv_sharing == "on":
        if reference_completions is not None:
            raise ValueError(
                "kv_sharing='on' (C0) generates its own reference completion; "
                "reference_completions must be None"
            )
    elif kv_sharing == "off":
        if not reference_completions:
            raise ValueError(
                "kv_sharing='off' (C1) requires reference_completions from "
                "the prior C0 run (lead ruling 2026-07-30: reference "
                "completion = C0's greedy completion, teacher-forced under "
                "both conditions, paired per row) -- run C0 first via "
                "build_summary"
            )
    else:
        raise ValueError(f"unknown kv_sharing {kv_sharing!r}")


def run_condition(family: str, model, tokenizer, rows: list[dict], *,
                  kv_sharing: str, dev, eos_ids: list[int],
                  reference_completions: dict[str, torch.Tensor] | None = None,
                  ) -> tuple[dict, dict[str, torch.Tensor]]:
    """One KV condition's full undosed pass + teacher-forced NLL over `rows`
    (already both roles, FIT split). Returns `(summary, completions)`:
    `summary` is the per-condition block `c1_precondition_summary.json`
    needs (confab_tighten, known_correct_cost_control, mean_nll,
    own_completion_mean_nll, plus provenance); `completions` is this
    condition's own row_key -> greedy-completion-token map, always returned
    so the caller (`build_summary`) can thread C0's completions into the
    following C1 call as `reference_completions`.

    C1 NLL INTERPRETATION (lead ruling 2026-07-30, module docstring
    "C1 NLL INTERPRETATION" has the full rationale): `mean_nll` -- the value
    `verdict_from_summary` feeds to `rollup.c1_verdict` -- is the PAIRED
    reference-completion NLL: C0's own greedy text, teacher-forced under
    EACH condition's own forward pass. For C0 that is a single forward per
    row (C0 IS the reference, so its own-completion NLL and its reference
    NLL are the same number by construction). For C1 it is a SECOND forward
    per row using `reference_completions[row_key]` -- C1 still generates its
    OWN completion first (needed for this condition's own clean_tighten /
    well_formed_correct grading, which must reflect what C1 actually says),
    but that generation's NLL is kept only as the non-gating
    `own_completion_mean_nll` diagnostic.

    Does not call `pl.run_one_row` / `pl.run_layer_with_direction` directly:
    both hide the raw generated tokens behind grade-only return dicts, and
    the NLL criterion needs those tokens. Instead this reproduces
    `run_one_row`'s fire=False branch inline (same two graders, same
    `gl.run_pass_fixed` call) so the tokens stay in hand for
    `_teacher_forced_nll`, then hands the resulting per-row records to
    `pl.summarize_layer_records` -- the SAME LOCKED aggregation
    `run_layer_with_direction` itself calls -- unchanged.
    """
    _validate_reference_completions(kv_sharing, reference_completions)
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
    completions: dict[str, torch.Tensor] = {}
    own_nlls: list[float] = []
    ref_nlls: list[float] = []
    try:
        with kv_ctx:
            for row in rows:
                assert row["fire"] is False, "C0/C1 scope: no injection in either condition"
                if kv_sharing == "off" and row["row_key"] not in reference_completions:
                    raise KeyError(
                        f"reference_completions missing row_key "
                        f"{row['row_key']!r} -- C0 and C1 must run over the "
                        "IDENTICAL row set (same _force_off(confab + known) "
                        "list) for the paired NLL to be well-defined"
                    )
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
                completions[row["row_key"]] = new_tokens
                own_nll = _teacher_forced_nll(model, dev, enc, new_tokens, cache_factory)
                own_nlls.append(own_nll)
                if kv_sharing == "on":
                    # C0 is its own reference: no second forward needed.
                    ref_nlls.append(own_nll)
                else:
                    ref_tokens = reference_completions[row["row_key"]]
                    ref_nlls.append(
                        _teacher_forced_nll(model, dev, enc, ref_tokens, cache_factory))
    finally:
        h_ctrl.remove()
        controller.reset()

    summary = pl.summarize_layer_records(
        records, 0.0, hs_index=INERT_HOOK_HS_INDEX, kv_sharing=kv_sharing)
    summary["mean_nll"] = float(np.mean(ref_nlls)) if ref_nlls else None
    summary["n_nll_rows"] = len(ref_nlls)
    summary["own_completion_mean_nll"] = float(np.mean(own_nlls)) if own_nlls else None
    summary["inert_hook_hs_index"] = INERT_HOOK_HS_INDEX
    return summary, completions


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
    # ORDER MATTERS (lead ruling 2026-07-30): C0 must run first -- it
    # generates the reference completions C1's paired NLL teacher-forces.
    c0_summary, c0_completions = run_condition(
        family, model, tokenizer, rows, kv_sharing="on", dev=dev, eos_ids=eos_ids)
    out["c0"] = c0_summary
    c1_summary, _c1_completions = run_condition(
        family, model, tokenizer, rows, kv_sharing="off", dev=dev, eos_ids=eos_ids,
        reference_completions=c0_completions)
    out["c1"] = c1_summary
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
