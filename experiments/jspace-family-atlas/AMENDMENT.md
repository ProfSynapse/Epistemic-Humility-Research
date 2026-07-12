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

Resolved 2026-07-12, same day as launch. Both capture cells completed on
Modal (app ap-q2mU3RZwwrHyaTbr1ehwVm) at signed commit 2524891, well under
the approved cap.

Gates, all PASS:

- AG0: capture coverage 1.00 in both cells (llama 2956/2956 rows, mistral
  3037/3037, every layer); direction refits byte-identical under seed
  20260707 for all three axes; held-out power floors hold (llama known-held
  334 / confab-held 872; mistral 382 / 1312). Lead re-ran the refit and
  power checks locally from the pulled captures.
- AG1: eff_dim_frac computed at every hidden state (llama 29, mistral 33).
  The lead's independent local recompute of the full profile matches the
  cloud-committed values to better than 1e-9 at spot-checked layers. The
  registered 20 percent subsample re-run reproduces the peak layer exactly
  in both cells (llama 4 -> 4, mistral 3 -> 3), within the +/- 1 tolerance.
- AG2: per-layer held-out AUROCs reported with 2000-resample bootstrap CIs
  for all three axes in both cells; committed in atlas_summary.json.

Prediction: NOT MET, both families, both predictors (orchestrator and user
both registered holds-on-both). The read-panel half held, but the profile
half did not: eff_dim_frac does not peak inside (20%, 85%) depth. It peaks
EARLY in both families, llama at layer 4 of 28 (0.14 depth) and mistral at
layer 3 of 32 (0.09 depth), then declines through the midband with a mild
late uptick.

Falsifier: NOT TRIGGERED. The profile is not monotone to the last layer,
and layers inside (20%, 85%) depth do reach held-out AUROC >= 0.80 on all
three axes simultaneously (llama layers 15-23, mistral layers 7-27).
Instrument-wording gap, recorded straight: the falsifier anticipated only
"monotone to the last layer" or "no readable interior band" as failure
shapes, so an early-exterior profile peak falls between the registered
prediction and the registered falsifier. Neither is satisfied; the verdict
below reports the result as prediction-failed without goalpost movement.

The atlas itself (the AG2 numbers) is the deliverable and it is clean:

- Doubt (known vs refused): ~1.00 from the earliest layers onward in both
  families. Caveat from the lead's post-hoc random-direction diagnostic
  (analysis-committed/random_direction_control.json, lab-notebook tier, not
  a registered gate): the refused-vs-known contrast carries a norm/position
  confound at this anchor, with a fixed random direction reading up to 0.97
  best-orientation at some layers, consistent with the fleet audit's
  finding. Doubt AUROCs on this contrast should be read against that
  elevated baseline.
- Caution (refused vs confab): clears 0.80 at llama layers 15-28 (best
  ~0.84) and mistral layers 3-32 (best ~0.91 at layer 17). Random baseline
  on this contrast stays ~0.5-0.75, so these are genuine signal.
- Raw refusal (refused vs all answered): best 0.90 at llama layers 20-25
  and 0.925 at mistral layers 15-17. Reconciliation with the fleet audit's
  0.997-1.000: that figure was refused-vs-known only; this panel pools
  known and confab as the negative class and the confab side is the harder
  contrast. Populations aligned, the two instruments agree.

Layer map handed to any future per-family actuation amendment: llama
~L20-23, mistral ~L15-17 (best simultaneous three-axis read, interior).
The representation-PR profile did not reproduce the Qwen Stage A midband
peak shape, but the estimator input differs (hidden-state variance here,
JVP push vectors there), so no cross-program claim is made either way; the
profile is comparable across atlas cells only, as registered.

Verdict (one sentence, mirrored in experiment.yaml): prediction failed in
both families because the eff_dim_frac profile peaks early (0.09-0.14
depth) rather than interior, while the read panel delivered the intended
per-family layer map with an interior band (llama 15-23, mistral 7-27)
where doubt, caution, and raw refusal all read >= 0.80 held-out.
