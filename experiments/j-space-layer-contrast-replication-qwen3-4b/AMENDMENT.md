# j-space-layer-contrast-replication-qwen3-4b

Status: resolved null-result (2026-07-09; registered G1 fail on a ceiling-saturated fresh pool; direction replicates with CI separation at hs23/hs29, magnitude pool-dependent; see Outcome).

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

Pre-sign prep result: fresh anchor extraction covered all 2,263 selected rows at
hs23/26/29/34. Smoke G0 passed with readback means hs23=24.9998, hs26=74.9788,
hs29=125.0104, hs34=174.9906, `frac_readback_within_tol=1.0` for every layer,
and dosed-row collapse 0.0 for every layer.

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
| user | Full replication: the mid-band advantage reproduces at near-predecessor size; best mid-band beats hs34 by roughly +18 to +25pp, known-correct cost within +2pp, hs34 viable. |

## Outcome

**Registered verdict: G1 FAIL. The same-model layer-site result does not
replicate at the registered effect size on this pool.** No goalposts moved:
best mid-band (hs29, 305/306 = 99.67%) minus hs34 (288/306 = 94.12%) =
+5.6pp, below the registered 10pp bar. G2 passes (+1.43pp <= 2pp) and G3
passes (hs34 at 94.12%, Wilson LCB 90.89%, far above the 60%/50% floor).
Instrument was flawless: readback exact at all four setpoints
(25.00/74.99/125.01/175.01), frac_readback_within_tol = 1.0 everywhere,
collapse 0.0 everywhere. Both scoreboard predictions (orchestrator +10-18pp,
user +18-25pp) were wrong.

Full numbers (all 306 confab / 1,957 known-correct rows per arm): hs23
304/306 = 99.35% tighten at 0.97% cost; hs26 299/306 = 97.71% at 1.99%;
hs29 305/306 = 99.67% at 2.81%; hs34 288/306 = 94.12% at 1.38%.

Adversarially audited interpretation (post-run red-team; the audit
reproduced every committed number and the gate decisions from the frozen
artifacts before this text was written):

1. **Ceiling effect, structurally caused.** Every layer's rate jumped by
   almost exactly its predecessor headroom (each closed 82-97% of its gap to
   100%; hs34 moved most, +27.6pp, because it had the most room). With hs34
   at 94.12%, the maximum achievable G1 delta was 5.9pp, so the registered
   bar was arithmetically near-unreachable on this pool.
2. **This is a narrower-distribution replication, not a same-distribution
   one.** All 306 fresh confabs come from a single source
   (kuq_ku_unknown_x); the predecessor held-out confabs mixed three sources
   (112 kuq_ku_unknown_x, 44 kuq_ku_unknown, 29 selfaware_unanswerable),
   and the two harder sources are entirely absent from the fresh candidate
   universe (structural: the AH expansion candidates contain only
   kuq_ku_unknown_x unknowns; nothing was cherry-picked). A G1 miss on a
   narrower, easier confab distribution is a weaker refutation of the
   mid-band thesis than a same-distribution miss would be, and downstream
   text must not read this as "failed to replicate on comparable data."
3. **Direction survives, non-uniformly.** hs23 and hs29 Wilson CIs separate
   cleanly from hs34 (hs29 LCB 98.17% > hs34 UCB 96.25%); hs26 does not
   (LCB 95.35% overlaps). Point-estimate ordering is mid > late at all
   three. The hs34 deficit is a write-effectiveness effect, not a
   gate-transfer effect: hs34 fires on 304/306 confabs (same as mid-band)
   but converts fewer fired rows (94.74% vs 99.67% tighten-given-fired).
4. **Selectivity is less flattering than G2 suggests.** The best mid-band
   layer (hs29) has the highest known-correct cost of all four arms (2.81%,
   about 2x hs34's 1.38%); the predecessor traded +22.7pp tighten for
   +0.78pp cost, this pool trades +5.6pp for +1.43pp. G2 passes on the
   looseness of the 2pp bar, not on a good tradeoff.
5. **Known limitation:** per-row intervention outcomes were not persisted
   (aggregates only), so the 16 fired-but-untightened hs34 failures cannot
   be classified by failure text (answered-anyway vs malformed vs
   non-termination) without a GPU re-run. Fired/non-fired classification
   was recoverable: hs34's 18 failures = 2 gate-misses + 16 fired. This is
   the buffered-run lesson already recorded in NOTEBOOK.md; successor runs
   adopt the tuner RunLog before sign.

Consequences carried forward: (a) Paper 5's layer-site claim keeps the
predecessor exploratory result and gains this pool-sensitivity caveat; the
claim "mid-band beats late site" is supported in direction on both pools
but its magnitude is pool-dependent and unidentifiable near ceiling. (b)
The queued cross-family layer-contrast experiment must replace or
supplement its inherited fixed +10pp G1 bar with a ceiling-robust contrast
(CI separation plus a failure-ratio measure) and must mine multi-source
confab pools hard enough to keep the reference arm off the ceiling.
