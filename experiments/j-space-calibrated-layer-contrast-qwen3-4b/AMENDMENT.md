# j-space-calibrated-layer-contrast-qwen3-4b

Status: resolved (exploratory pass; local RTX 3090 run completed 2026-07-08).

Keep this document the prose home for the experiment. The machine state lives in
`experiment.yaml` and is never duplicated here.

## Motivation and posture

This experiment is the held-out causal contrast made possible by the resolved
J-space dose calibration. The read-only J-lens characterization localized
Qwen3-4B's workspace-like band to hs23-29 with peak hs26, while the inherited
L34 write site maps to hs34 just after the band. The first causal layer sweep
could not answer the layer-site question because fixed absolute dose 200
collapsed hs23 and hs26 at G0. The FIT-only calibration then recovered
non-collapsing setpoints before any held-out contrast: hs23=25, hs26=75,
hs29=125, and hs34=175.

Posture: exploratory Tier-2 held-out layer-site contrast, local RTX 3090,
raw-base `unsloth/Qwen3-4B` bf16 only. It is not a headline claim and is not
pooled with the cross-family confirmatory line. It does not touch old
trained-checkpoint cells, GRPO-v2, or AI-TRUE.

## Design

Substrate: raw-base `unsloth/Qwen3-4B`, bf16, no adapter, no 4-bit quantization.

Inputs:

- Per-layer fitted directions, frozen gates, build manifest, and source
  provenance from `j-space-midband-write-sweep-qwen3-4b/analysis-committed/`.
- FIT-selected dose summary from
  `j-space-midband-dose-calibration-qwen3-4b/analysis-committed/dose_calibration_summary.json`.
- Local gitignored held-out row text and aliases from the source experiment's
  `analysis/rows_with_text.jsonl`.

No question text, aliases, raw generations, or row-level outputs are committed.
The public output is aggregate JSON only.

Arms:

- hs23 gated snap at absolute setpoint 25.
- hs26 gated snap at absolute setpoint 75.
- hs29 gated snap at absolute setpoint 125.
- hs34 gated snap reference at absolute setpoint 175.

For each layer, the run uses that layer's FIT-frozen doubt gate and `c_hat`
write direction from the stopped sweep. Generation and scoring mirror the
predecessor: EOS-enabled greedy JSON generation, `min_new_tokens=1`,
`max_new_tokens=200`, `enable_thinking=False`; clean_tighten requires a
natural-stop single-object JSON refusal; known-correct cost is
`not_well_formed_correct`.

Run shape: first run smoke on 8 held-out rows to verify calibrated readback and
zero collapse at every layer. If G0 passes, run the full held-out contrast over
all held-out confab and known-correct rows.

Instrument files pinned at sign: `cell.yaml`, `gates.yaml`, `run_contrast.py`.

## Prediction

With layer-specific setpoints fixed before held-out evaluation, the best
mid-band layer (hs23/hs26/hs29, most likely hs26 or hs29) will improve
held-out confab clean_tighten over hs34 by at least 10 percentage points without
increasing known-correct false-refusal cost by more than 2 percentage points;
hs34 will remain a viable predecessor reference.

## Falsifier

If the best mid-band layer improves confab clean_tighten by less than 10
percentage points over hs34, or increases known-correct false-refusal cost by
more than 2 percentage points, the calibrated J-space layer-site hypothesis is
not supported on this raw-base Qwen3-4B surface. If hs34 fails the predecessor
viability floor, the run is a reference replication failure rather than
interpretable evidence about mid-band superiority.

## Gates

- **G0 (instrument validity; stop, not outcome)**: selected doses exactly match
  the resolved FIT calibration (hs23=25, hs26=75, hs29=125, hs34=175); local row
  text exists only under gitignored `analysis/`; smoke readback is within
  5%+0.5 absolute of each layer's calibrated dose for every dosed smoke row;
  smoke collapse on dosed rows is 0 for every layer.
- **G1 (mid-band tighten improvement)**: best mid-band confab clean_tighten rate
  minus hs34 confab clean_tighten rate >= 10 percentage points.
- **G2 (no selectivity regression)**: best mid-band known-correct false-refusal
  cost minus hs34 cost <= 2 percentage points.
- **G3 (predecessor reference viable)**: hs34 confab clean_tighten >=60% and
  Wilson lower CI >50%, matching the predecessor viability floor. If G3 fails,
  do not read G1/G2 as evidence about J-space.

## Predictions scoreboard

| Predictor | Call |
|-----------|------|
| orchestrator | Calibrated mid-band wins; hs26 or hs29 is most likely best, hs34 remains viable but not optimal. |
| user | |

## Outcome

Resolved as an exploratory pass on 2026-07-08. The smoke G0 passed first, then
the full held-out run completed over 443 rows (185 confab, 258 known-correct).
All selected doses matched the FIT calibration, every layer had readback within
tolerance, and dosed-row collapse was 0 for every layer.

Gate results:

- **G1 passed**: best mid-band layer was hs23. It improved held-out confab
  clean_tighten over hs34 by 22.7 percentage points: hs23 165/185 = 89.2%
  (Wilson 95% CI [83.9%, 92.9%]) vs hs34 123/185 = 66.5% (Wilson 95% CI
  [59.4%, 72.9%]).
- **G2 passed**: known-correct false-refusal cost for the best mid-band layer
  increased by only 0.78 percentage points over hs34: hs23 9/258 = 3.5% vs
  hs34 7/258 = 2.7%.
- **G3 passed**: hs34 remained a viable predecessor reference: 66.5%
  clean_tighten with Wilson lower bound 59.4%, above the 60% rate and 50%
  lower-bound floors.

Descriptive layer ordering: hs23 was best on the registered contrast, followed
closely by hs29 (163/185 = 88.1% clean_tighten, 10/258 = 3.9% cost), then hs26
(150/185 = 81.1%, 8/258 = 3.1%), then hs34 (123/185 = 66.5%, 7/258 = 2.7%).

Interpretation: on this raw-base Qwen3-4B bf16 surface, calibrated mid-band
J-space writes beat the late hs34 reference on held-out confab tightening
without a meaningful known-correct cost regression. This supports the layer-site
part of the J-space actuation-bridge hypothesis for this surface. It remains
exploratory Tier-2 evidence, not a headline confirmatory claim or cross-family
result.

Run limitation: this bespoke runner was not row-checkpointed. It wrote the
public aggregate only at completion; future dose/contrast cells should use the
generic tuner checkpoint/resume path where feasible.

Public aggregate: `analysis-committed/full_summary.json`.
