# jspace-family-atlas

Status: signed 2026-07-12 (instrument pinned, predictions registered pre-launch; user launch approval granted 2026-07-12, two capture cells, $10 operational cap).

Keep this document the prose home for the experiment. The machine state lives in
`experiment.yaml` and is never duplicated here.

## Motivation and posture

The cross-family doubt-snap confirmatory
(`experiments/doubt-snap-cross-family-confirmatory`) stopped 3 of 4 small-tier
families at the registered FIT dose-viability rule, but every one of its
actuation numbers was measured at a single blindly ported depth: the registered
layer rule `round(0.94 * (num_hidden_layers - 1))` copied Qwen3-4B's working
depth fraction to every family "without tuning layers per family." No non-Qwen
family has ever received the j-space workspace profile that, on Qwen3.5-4B,
moved gated clean_tighten from a below-floor 0.326 at the ported late layer to
an interim ~0.68 at its profiled midband layer hs20 (registered comparison
pending in `experiments/qwen35-4b-midband-doubt-snap`, in flight on the local
ladder).

A post-hoc audit of the fleet's committed captures (lead-verified, recorded in
the fleet NOTEBOOK 2026-07-12) further showed that the refusal-vs-answering
axis reads at 0.997-1.000 in every family at the ported layer, while the
registered write direction carries none of that axis by construction. Layer
and direction are therefore separately confounded in the fleet nulls.

This experiment supplies the missing map. It is a READ-ONLY mapping experiment:
no steering, no interventions, no behavioral outcomes. Posture: exploratory
instrument-building evidence. Its committed profile becomes (a) the layer
selection input for any future per-family actuation amendment (the
gated-snap rescue and the raw-refusal-axis design both depend on it), and (b)
a publishable cross-family atlas dataset under the program's data-exhaust
workflow (professorsynapse/eh-jspace-family-atlas).

## Design

Substrates: the two probe families whose fleet cells are terminal and whose
row pools, baseline generations, gradings, and role assignments are already
volume-backed and reusable verbatim (no re-mining, no re-generation):
`unsloth/Llama-3.2-3B-Instruct` and `mistralai/Mistral-7B-Instruct-v0.3`, at
the exact HF revisions pinned in the fleet's `model_matrix.yaml`. Optional
extension cells (same instrument, separate launches, only if the user
authorizes spend): ministral8b_instruct_2410, qwen35_9b.

Signal, per cell:

1. Full-depth anchor capture: hidden states at every decoder layer (0 through
   n_layers) at the final-prompt-token anchor, for every row in the fleet
   cell's split manifest (roles confab, known_correct_answered,
   unknown_refused; FIT/held-out labels carried through unchanged).
2. Workspace profile: per-layer effective-dimension fraction
   (eff_dim_frac): the participation-ratio formula from
   `experiments/qwen35-4b-midband-doubt-snap` Stage A applied to the FIT-row
   anchor hidden-state matrix at each layer (representation-variance PR).
   Estimator-input note, adjudicated pre-sign: Stage A computed the same
   formula over gradient-based JVP push vectors, which a capture-only run
   cannot reproduce within this experiment's registered spend. The atlas
   profile is therefore NOT numerically comparable to Stage A's profile
   values; what the atlas guarantees is comparability ACROSS its own cells,
   which all use the identical computation. Peak-layer locations may differ
   from what a JVP profile would select, and the prediction below is read
   against the representation-PR profile only.
3. Per-layer read panel, with 2000-resample bootstrap CIs. The fleet's
   FIT/held-out labels for confab and known_correct_answered rows are
   carried through unchanged. The fleet assigned every unknown_refused row
   split=fit_only by design, so a two-sided held-out contrast needs one
   addition, adjudicated pre-sign: the refused pool is subdivided
   deterministically (seed 20260707) into refused_fit (direction fitting)
   and refused_eval (scoring) halves. Directions are fit on FIT
   known/confab rows plus refused_fit; AUROCs are scored on held-out
   known/confab rows against refused_eval, making every reported panel
   number two-sided held-out. No behavioral row changes split; the
   subdivision exists only inside this read-only analysis. Axes:
   - doubt u_d (mean known-correct minus mean refused-unknowns),
   - caution (mean refused minus mean confab, the fleet's pre-orthogonalization
     construction),
   - raw refusal (mean refused minus mean answered),
   each reported as held-out AUROC on its defining contrast per layer.
4. Committed outputs (aggregates and fitted metadata only, never row text):
   per-layer profile table, per-layer read AUROCs with CIs, direction-fit
   manifests with seeds and sha256s, and the atlas summary JSON.

Execution: Modal A10G, capture-only (no steering hooks), batch verbs, one
detached function per cell, resume-safe on the existing experiment volume
namespace pattern. Per-cell dose grids do not apply (no writes). Estimated
spend is capture plus CPU scoring only; exact launch requires fresh user
approval with the estimate at staging time.

Instrument files pinned at sign: `cell.yaml`, `gates.yaml`, the capture
runner, the profile/scoring script, and the Modal wrapper.

## Prediction

Each mapped family shows an interior workspace band: a contiguous set of
layers strictly inside (20%, 85%) depth where eff_dim_frac peaks AND all three
read axes (doubt, caution, raw refusal) hold held-out AUROC >= 0.80, with the
band's peak layer differing from the fleet's ported 0.94-depth layer.

## Falsifier

For either mapped family: no interior eff_dim_frac peak exists (the profile is
monotone to the last layer), or no layer inside (20%, 85%) depth reaches
held-out AUROC >= 0.80 on all three axes simultaneously. Either outcome means
the Qwen-derived workspace-band picture does not describe that family and
layer choice cannot be blamed for its fleet null on this evidence.

## Gates

- AG0 (integrity, pre-outcome): capture covers >= 95% of the cell's manifest
  rows at every layer; direction refits are byte-identical under the fixed
  seed; held-out power carried over from the fleet cell (confab >= 150,
  known-correct >= 250) still holds after capture attrition.
- AG1 (profile): eff_dim_frac profile is computed at every layer with the
  registered estimator; reproducibility re-run on a 20% row subsample keeps
  the peak layer within +/- 1 layer.
- AG2 (read panel): per-layer held-out AUROCs reported with CIs for all three
  axes; no threshold gate on the values themselves beyond the
  prediction/falsifier above (the numbers are the atlas).

## Predictions scoreboard

| Predictor | Call |
|-----------|------|
| orchestrator | Holds on both families: each shows an interior workspace band with all three axes >= 0.80 held-out in-band; mistral's caution axis is the riskiest of the six family-axis pairs. Registered 2026-07-12, pre-launch. |
| user | Holds on both families (selected from the registered options 2026-07-12, pre-launch). |

## Outcome

Filled at resolve. Record the verdict, the gate results, and the one-sentence
summary that also goes into `verdict:` in the manifest.
