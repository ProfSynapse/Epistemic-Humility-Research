# <slug>

Status: draft (not signed; do not launch as confirmatory evidence).

Keep this document the prose home for the experiment. The machine state lives in
`experiment.yaml` and is never duplicated here.

This skeleton fills in `bin/exp new`'s generic `probe-fit` AMENDMENT
placeholder with the family-atlas instrument's own structure. Delete this
paragraph and every `<PLACEHOLDER>` before signing.

## Motivation and posture

Why this family/model/size needs its own atlas: what actuation amendment is
waiting on this layer map, or what substrate change (new revision, new
checkpoint) invalidated a prior one. State plainly that this is a READ-ONLY
mapping experiment: no steering, no interventions, no behavioral outcomes.
Posture: exploratory instrument-building evidence, never pooled with a
confirmatory headline matrix.

## Design

Substrate: `<hf_org/hf_repo>` at pinned revision `<sha>`, `<N>` layers,
hidden size `<D>`.

Row pool: name the source experiment whose row pool, baseline gradings, and
role/split assignments you are reusing verbatim (no re-mining, no
re-generation), or state that this cell mines a fresh pool per the program's
standard roles (confab / known_correct_answered / unknown_refused) and name
the mining script.

Signal, per cell (the standard family-atlas procedure; adjust only with a
stated reason):

1. Full-depth anchor capture: hidden states at every decoder layer (0
   through n_layers) at the final-prompt-token anchor, for every row in the
   cell's split manifest. FIT/held-out labels carried through unchanged.
2. Workspace profile: per-layer effective-dimension fraction (eff_dim_frac),
   the participation-ratio formula applied to the FIT-row anchor
   hidden-state matrix at each layer. State explicitly that this is a
   representation-variance PR, not comparable to a JVP-based profile from a
   different instrument; comparable across this atlas's own cells only.
3. Per-layer read panel with bootstrap CIs, for doubt / caution /
   raw_refusal, plus the standard random-direction control (see SKILL.md).
   If the source pool's `unknown_refused` role is `fit_only` (no held-out
   partition at all), state the deterministic refused-pool subdivision
   (seed, method) here so every reported panel number is two-sided
   held-out.
4. Committed outputs (aggregates and fitted metadata only, never row text):
   per-layer profile table, per-layer read AUROCs with CIs, the
   random-direction control, direction-fit manifests with seeds and
   sha256s, and the atlas summary JSON.

Execution: name the lane (local GPU or Modal), the estimated spend, and the
instrument files pinned at sign (`cell.yaml`, `gates.yaml`, the capture
runner, the profile/scoring script, the render module copy, any cloud
wrapper).

## Prediction

`<PLACEHOLDER>` -- default family-atlas prediction, restate in your own
words: this family shows an interior workspace band (a contiguous set of
layers strictly inside (20%, 85%) depth) where eff_dim_frac peaks AND all
three read axes (doubt, caution, raw refusal) hold held-out AUROC >= 0.80,
with the peak layer differing from any previously ported layer.

## Falsifier

`<PLACEHOLDER>` -- write this so it explicitly covers EVERY shape the
profile could take, not just the ones you expect. jspace-family-atlas's
first run found the profile peaks EARLY (0.09-0.14 depth) in both mapped
families -- a shape its own prediction and falsifier both failed to name,
leaving the result stuck between "not met" and "not falsified" at resolve.
Do not repeat that gap: state outcomes for an interior peak (prediction
met), a monotone profile (falsifier met), an early-exterior peak, a
late-exterior peak, AND a profile where no layer clears the AUROC floor on
all three axes, so every possible shape maps to an explicit verdict before
you launch.

## Gates

Copy from `gates.yaml` once filled. See `templates/gates.yaml` for the AG0
(integrity) / AG1 (profile) / AG2 (read panel) structure.

## Predictions scoreboard

| Predictor | Call |
|-----------|------|
| orchestrator | |
| user | |

## Outcome

Filled at resolve. Record the verdict, the gate results (AG0/AG1/AG2), and
the one-sentence summary that also goes into `verdict:` in the manifest.
Append this cell's row to `docs/atlas/family-layer-map.md` once resolved --
never add a registry row before the governed doc it cites is signed and
resolved.
