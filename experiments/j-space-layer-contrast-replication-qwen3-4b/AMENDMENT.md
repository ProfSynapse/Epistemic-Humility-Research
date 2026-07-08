# j-space-layer-contrast-replication-qwen3-4b

Status: draft (not signed; do not launch the full layer contrast as evidence).

Keep this document the prose home for the experiment. The machine state lives in
`experiment.yaml` and is never duplicated here.

## Motivation and posture

Paper 5 now has a coherent exploratory actuation thesis: readable epistemic
state is not automatically writable, but gated hidden-state caution writes can
work, and the J-space layer-site result suggests writing near the workspace band
is materially better than writing at the inherited late hs34 site.

The resolved predecessor `j-space-calibrated-layer-contrast-qwen3-4b` found a
large same-model effect on raw-base Qwen3-4B bf16: hs23 reached 165/185 =
89.2% clean_tighten versus hs34 123/185 = 66.5%, a +22.7 percentage-point
mid-band advantage with only +0.78 percentage-point known-correct cost. That is
strong exploratory evidence, but still only one held-out split from one row
surface.

This experiment hardens that result in the narrowest useful way: freeze the
predecessor directions, gates, and calibrated doses, then rerun the same
layer-site contrast on a fresh private evaluation pool whose row keys are
disjoint from the predecessor fit and held-out split. It is still Tier-2
exploratory evidence, not a headline or cross-family claim. It does not touch
GRPO-v2, AI-TRUE, or old trained-checkpoint cells.

## Design

Substrate: raw-base `unsloth/Qwen3-4B`, bf16, no adapter, no 4-bit
quantization.

Frozen predecessor inputs:

- Per-layer `u_d` gate directions and `c_hat` write directions from
  `j-space-midband-write-sweep-qwen3-4b/analysis-committed/layers/`.
- Per-layer frozen gate thresholds from
  `j-space-midband-write-sweep-qwen3-4b/analysis-committed/gate_fit_layers.json`.
- FIT-selected calibrated doses from
  `j-space-midband-dose-calibration-qwen3-4b/analysis-committed/dose_calibration_summary.json`:
  hs23=25, hs26=75, hs29=125, hs34=175.

Fresh pool construction:

1. Read the AH expansion candidate pool from the canonical private analysis
   tree.
2. Exclude every row key in the predecessor split manifest, including both fit
   and held-out rows.
3. Generate on raw-base Qwen3-4B bf16 with the AH-A0 baseline rendering.
4. Select fresh `confab` rows as gold-unanswerable rows where the raw base
   answers rather than refuses.
5. Select fresh `known_correct_answered` rows as gold-answerable rows where the
   raw base answers and grades correct, matching the predecessor's selection
   rule.
6. Require at least 200 fresh confab rows and at least 300 fresh
   known-correct rows before the layer contrast can launch.

The fresh miner orders unknown rows first from `kuq_ku_unknown_x` and orders
known rows PopQA before TriviaQA. That avoids starting in the same
TriviaQA-first region already mined by the predecessor's G2 power fix.

No question text, aliases, baseline generations, or row-level intervention
outputs are committed. The committed pool artifact is ID-only:
`analysis-committed/fresh_eval_pool_manifest.json`.

The fresh-pool miner may be run in `--scan-all-candidates` mode before the full
contrast to create a reusable census over the configured fresh AH expansion
candidate universe. This does not change the evaluation gates: G0 is a minimum
power floor, and all rows selected before the contrast launch are eligible. The
public-facing artifact remains ID/provenance/role metadata only unless and
until each source dataset's redistribution terms are audited; text, aliases,
and model generations stay private under `analysis/`.

Pre-sign census result: exhaustive mining completed over 12,923 fresh
candidates, selecting 306 fresh `confab` rows and 1,957
`known_correct_answered` rows. The text-free public manifest is committed at
`analysis-committed/fresh_eval_pool_manifest.json`; a public-safe HF copy is
published at `professorsynapse/eh-jspace-fresh-pool-census-qwen3-4b` revision
`3add102ce930f73a29013f572f03e7325da30825`.

Layer contrast:

- hs23 gated snap at absolute setpoint 25.
- hs26 gated snap at absolute setpoint 75.
- hs29 gated snap at absolute setpoint 125.
- hs34 gated snap reference at absolute setpoint 175.

For each layer, the fresh prompt-anchor state is projected through that layer's
frozen `u_d`; rows fire iff `score_neg_z_d >= tau_frozen`. Fired rows receive
the frozen `c_hat` erase-write at the calibrated setpoint, anchor_onward. The
generation and scoring contract mirrors the predecessor: EOS-enabled greedy JSON
generation, `min_new_tokens=1`, `max_new_tokens=200`, `enable_thinking=False`;
clean_tighten requires a natural-stop single-object JSON refusal;
known-correct cost is `not_well_formed_correct`.

Instrument files pinned at sign: `cell.yaml`, `gates.yaml`,
`mine_fresh_eval_pool.py`, `extract_fresh_anchor.py`, and `run_contrast.py`.

## Prediction

With predecessor directions, gates, and calibrated doses frozen, the best
mid-band layer will beat hs34 by at least 10 percentage points on fresh confab
clean_tighten without increasing known-correct false-refusal cost by more than
2 percentage points; hs34 will remain viable.

## Falsifier

If the best mid-band layer beats hs34 by less than 10 percentage points on fresh
confab clean_tighten, or increases known-correct false-refusal cost by more than
2 percentage points, the same-model layer-site result does not replicate. If
hs34 fails the predecessor viability floor, the run is a reference replication
failure rather than interpretable evidence about mid-band superiority.

## Gates

- **G0 (instrument validity; stop, not outcome)**: fresh pool row keys have zero
  overlap with the predecessor split; fresh pool has at least 200 confab rows
  and at least 300 known_correct_answered rows; no restricted text/generations
  are committed; selected doses exactly equal hs23=25, hs26=75, hs29=125,
  hs34=175; fresh anchor extraction covers every fresh eval row at
  hs23/26/29/34; smoke readback is within 5%+0.5 absolute of each layer's
  calibrated dose for every dosed smoke row; smoke collapse on dosed rows is 0
  for every layer.
- **G1 (same-model mid-band replication)**: best mid-band confab clean_tighten
  rate minus hs34 confab clean_tighten rate >= 10 percentage points.
- **G2 (no selectivity regression)**: best mid-band known-correct false-refusal
  cost minus hs34 cost <= 2 percentage points.
- **G3 (predecessor reference viable)**: hs34 confab clean_tighten >=60% and
  Wilson lower CI >50%.

## Predictions scoreboard

| Predictor | Call |
|-----------|------|
| orchestrator | Replication holds but shrinks: hs23 or hs29 wins; best mid-band beats hs34 by roughly +10 to +18pp, with known-correct cost still within +2pp. |
| user | Pending before full layer-contrast launch. |

## Outcome

Filled at resolve. Record the verdict, gate results, pool counts, and the
one-sentence summary that also goes into `verdict:` in the manifest.
