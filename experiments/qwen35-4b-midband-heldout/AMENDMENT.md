# qwen35-4b-midband-heldout

Status: resolved (signed 2026-07-13; resolved 2026-07-13, shape A, falsifier does not fire, hs20 window PROMOTED to a held-out claim)

Keep this document the prose home for the experiment. The machine state lives in
`experiment.yaml` and is never duplicated here.

## Motivation and posture

`experiments/qwen35-4b-midband-doubt-snap` (resolved 2026-07-12, G1 PASS)
established, in-sample on the FIT split of `Qwen/Qwen3.5-4B`, that a
doubt-gated caution snap written at mid-band layer hs20 at dose 8 x sigma_c
decouples refusal induction from output corruption: fired FIT confabs refused
at 0.684 with well-formed 0.980 while FIT known-correct false-refusal held at
10/240 = 0.042, where the late 0.94-depth site (hs30) could not clear the
refusal floor at any well-formed dose. That resolved amendment states plainly,
in its binding scope statement 2, that this is in-sample FIT characterization
only: `c_hat` is fit on FIT confab-vs-refused labels and evaluated on those
same FIT confabs, the held-out pool was never touched by design, and
"Promotion to a claim requires a registered held-out stage." This amendment is
exactly that registered held-out stage, and nothing else.

Nothing is refit here. The point of the experiment is to consume the ladder's
frozen operating point verbatim (the hs20 direction set, the frozen gate
threshold, the FIT-fit standardization scalars, and the single dose
8 x sigma_c) and score it, for the first time, on the qwen35_4b held-out pool
that was reserved for this purpose. The held-out pool is the untouched
1,332 held-out confab + 360 held-out known-correct-answered rows defined and
provenanced by `experiments/doubt-snap-cross-family-confirmatory`'s qwen35_4b
cell and recorded ID-only in the ladder's own
`analysis-committed/reused_rows_manifest.json` (`counts.confab_held_out`
= 1332, `counts.known_correct_answered_held_out` = 360). Held-out was never
scored by the fleet (all its cells stopped at the pre-outcome G0 FIT
dose-viability rule) and never scored by the ladder (FIT-side only), so this
run is the first time these rows meet any intervention.

Posture: exploratory Tier-2 held-out confirmation on one substrate. A pass
promotes the hs20 mid-band window from an in-sample existence result to a
held-out claim about Qwen3.5-4B specifically. It is never pooled with the
locked Phase 1 headline matrix and never pooled with the
`doubt-snap-cross-family-confirmatory` fleet (which is resolved not-promoted);
those surfaces used different gate definitions and are governed separately.

**Falsifier-coverage discipline (a lesson taken straight from the fleet).**
`doubt-snap-cross-family-confirmatory` resolved with its registered falsifier
unable to fire: the falsifier was defined only over held-out G1/G2/G3 fails,
every cell stopped at G0 before held-out, and the result "landed between its
prediction and its falsifier, in territory neither anticipated." The
family-atlas skeleton records the same failure mode from a different run and
directs that a falsifier "explicitly cover EVERY shape the profile could take,
not just the ones you expect." This amendment therefore enumerates every
outcome shape below in an explicit table and maps each to a verdict before
launch, so that no result can fall between the prediction and the falsifier
regardless of which surface (refusal transfer, well-formedness, cost, or
placebo) is the one that moves.

## Design

Substrate: `Qwen/Qwen3.5-4B`, bf16, pinned revision
`851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`, no adapter, no quantization.
Identical to the ladder's substrate and to the fleet's qwen35_4b cell.

### Frozen operating point (NOTHING refit)

Every quantity below is loaded verbatim from the resolved ladder's committed
artifacts. This experiment writes no new direction, fits no new gate, and
recomputes no standardization scalar. Loading these bytes and scoring them on
held-out is the entire experiment.

| Quantity | Frozen value | Source (ladder artifact) |
|---|---|---|
| Write layer | hs20 (decoder block 19) | `build_manifest.json` `layers.hs20.hs_index` |
| Doubt sensor `u_d` | frozen unit vector, dim 2560 | `directions/hs20/u_d.json` |
| Snap direction `c_hat` | frozen unit vector, dim 2560 | `directions/hs20/c_hat.json` |
| Placebo `random_direction` | frozen unit vector, dim 2560 | `directions/hs20/random_direction.json` |
| Doubt standardization | mu_d -0.290345686796538, sigma_d 1.669221862861343 | `build_manifest.json` `layers.hs20` |
| Snap standardization | mu_c -4.031343053353048, sigma_c 1.576023489724997 | `build_manifest.json` `layers.hs20` |
| Gate threshold | tau_frozen -0.589747307635842 (Youden-J on FIT) | `build_manifest.json` `layers.hs20.tau_frozen` |
| Gate fire rule | fire iff neg_z_d >= tau_frozen, neg_z_d = -(proj_u_d - mu_d)/sigma_d, clipped to [-2, 2] | ladder `cell.yaml` `gate` + fit recipe |
| Dose | dose_mult 8, dose_abs = 8 x sigma_c = 12.6082 | ladder Outcome (G1 cell), scope statement 4 realized-projection target 12.608 |
| Snap law / position | erase_write, anchor_onward | ladder `cell.yaml` `snap` |
| Render / anchor | `doubt-snap-cross-family-confirmatory` `render.py` BASELINE_SYSTEM_PROMPT + chat template, enable_thinking=False, anchor at prompt_len - 1 | ladder Stage B convention |
| Generation | greedy, min_new_tokens 1, max_new_tokens 200, EOS incl. im_end | ladder `cell.yaml` `generation` |

The dose is a single point, not a ladder: this is a confirmation of one
operating point, not a search. The realized-projection readback target on the
gated and random-direction arms is 12.608 (the ladder observed gated 12.627 /
random 12.625 against this target at this cell).

### Population (containment-safe materialization, same recipe as the ladder)

The held-out rows are materialized the same way the ladder materialized its
FIT rows: a read-only, sha256-verified pull of the source file from the Modal
volume `eh-doubt-snap-cross-family`
(`doubt-snap-cross-family-r1/qwen35_4b/analysis/heldout_rows_for_steer.jsonl`)
into this experiment's own gitignored `analysis/` directory, with an ID-only
public manifest committed under `analysis-committed/` (row_key + role + split
+ source + category_canon; never question text, aliases, or answer text).
The committed counts must equal the ladder's reused_rows_manifest.json
held-out counts and the fleet's registered qwen35_4b held-out counts exactly:
1,332 confab + 360 known_correct_answered = 1,692 rows. The FIT rows are not
consumed by this experiment at all; only the held-out partition is scored.

Because absolute row provenance is anchored to a manifest the ladder already
committed on main, the held-out ID set is auditable against a
previously-committed artifact before any generation runs.

### Arms (one dose, four arms)

- `baseline`: no hook, generated once over the full 1,692-row held-out pool.
  Establishes the undosed refusal and well-formed rates (expected refusal near
  0 on both roles, as the ladder observed exactly 0 baseline refusal on both
  FIT roles) and is the reference for the G3(i) placebo comparison.
- `gated`: the real instrument. The frozen doubt gate fires per row on the
  held-out anchor readout; fired rows receive the erase-write `c_hat` snap at
  dose_abs 12.6082, anchor_onward; non-fired rows receive no write and inherit
  their baseline generation.
- `random_direction`: the same fired rows as `gated`, writing the frozen
  placebo direction at a magnitude matched to the gated arm's realized
  projection (readback target 12.608). Isolates direction specificity.
- `permuted_gate`: the same total fire count as `gated`, but the fired rows are
  chosen uniformly at random over the combined held-out pool (confab + known)
  under a fresh seed (20260713, distinct from the ladder's 20260707 and
  recorded in `cell.yaml`), then written with the real `c_hat` snap at the same
  dose. Isolates whether the gate's row selection, rather than raw dose count,
  is what limits known-correct false-refusal.

All rates are reported with Wilson 95% confidence intervals. Row-level
decoupling (rows simultaneously refused AND well-formed) is reported alongside
the marginal rates, mirroring the ladder's row-level evidence (593/869 fired
FIT confabs simultaneously refused and well-formed at the G1 cell).

### Lane and cost

Lane: local RTX 3090, batch_size=8 (batch-parity precedent: the ladder's
Stage C ran and was adjudicated at batch_size=8; single-row parity was not
verified there and is not claimed here either). GPU scripts run under base
conda `/home/profsynapse/miniconda3/bin/python3` because the model_type
`qwen3_5` loader requires transformers >= 5.x and the project's pinned
`unsloth_env` (transformers 4.57.1) does not recognize this architecture. This
is the ladder's documented deviation-with-cause, reused, not a silent
substitution.

Generation-count estimate (arithmetic shown; actual fired counts are computed
at run and reported):

- Held-out pool: 1,332 confab + 360 known = 1,692 rows.
- Anchor readout capture (forward-only, no generation) over 1,692 rows to
  compute neg_z_d and the fired set. Cheap relative to generation.
- Shared `baseline` generation over the full pool: 1,692 generations.
- Projected fired set at hs20 using the ladder's FIT Youden rates as the
  expectation (confab caught 0.9808, known flagged 0.0542): confab fired about
  0.9808 x 1332 = 1,306; known fired about 0.0542 x 360 = 20; total fired about
  1,326.
- `gated`, `random_direction`, `permuted_gate` each generate over about 1,326
  rows: 3 x 1,326 = about 3,978 generations.
- Total: about 1,692 + 3,978 = about 5,670 generations.

Wall-time estimate: the ladder's Stage C produced 74,753 generations between
2026-07-10 11:20 and 2026-07-12 22:35 (59.25 h = 3,555 min), a measured
throughput of 74,753 / 3,555 = 21.0 generations/min at batch_size=8 on this
substrate (the slow PyTorch fallback for the hybrid linear-attention blocks is
why throughput is this low). At 21 generations/min, 5,670 generations is about
5,670 / 21 = 270 min = about 4.5 h of generation. Budget about 5 to 6 h end to
end including anchor capture and load overhead. This confirmation costs about
one thirteenth of the ladder's Stage C generation budget (5,670 vs 74,753),
because it runs one dose and one layer rather than seven doses across four
layers.

### Instrument files pinned at sign (harness written under a separate assignment)

`cell.yaml`, `gates.yaml`, and (once written) the materialization script, the
held-out scoring runner, and the render/grader module copies reused from the
ladder. No harness code is written by this drafting assignment; the harness
build is a separate assignment gated on this draft's review. The synaptic-tuner
submodule pin for the run is set at the harness-build assignment (main
currently pins `86b134c3`; the ladder's RunLog utility was available at the
ladder's own pin `cd30d482`, and the harness assignment resolves the exact pin
that carries `shared/utilities/run_log.py`).

(Gate-template decision, PI, 2026-07-13, pre-sign and pre-launch: the
fleet-style Wilson-bounded thresholds are adopted as the gating rule; the
ladder's point-estimate floors remain as inner floors and are reported for
continuity. The drafter's original ladder-floors-only rule is superseded
before signing; nothing had run.)

## Prediction

The frozen hs20 operating point transfers to held-out: on the 1,332 held-out
confabs, the `gated` arm achieves fired-confab refused rate >= 0.60 with
Wilson 95% lower CI > 0.50, AND well-formed rate >= 0.80, simultaneously,
with known-correct false-refusal <= 0.05 point estimate and Wilson 95% upper
CI < 0.10 over the full 360 held-out known-correct population; and the placebo
arms behave (random_direction is a no-op relative to baseline within 2 points
on both populations, permuted_gate has strictly worse known-correct
false-refusal than gated). This is outcome shape A in the coverage table and
promotes the hs20 mid-band window to a held-out claim about Qwen3.5-4B.

## Falsifier

Promotion is refused if ANY of the following held-out shapes occurs (shapes B
through E in the coverage table), each of which is a distinct, pre-named way
the in-sample operating point can fail to survive held-out:

- **B, refusal does not transfer:** fired held-out confab refused rate < 0.60.
  The FIT operating point does not induce refusal out of sample.
- **C, decoupling does not survive:** refused rate >= 0.60 but well-formed rate
  < 0.80 on fired held-out confabs. Refusal transfers but output corruption
  returns out of sample, so the decoupling that defined the ladder result does
  not hold on held-out.
- **D, cost gate fails out of sample:** refused >= 0.60 and well-formed >= 0.80
  on confabs but known-correct false-refusal > 0.10 over the full 360 held-out
  knowns. The window induces refusal cleanly but is not cost-safe out of
  sample.
- **E, placebo contamination:** the confab and cost thresholds clear but
  random_direction is NOT a no-op (refusal moves > 2 points from baseline on
  either population) OR permuted_gate does NOT have strictly worse
  known-correct false-refusal than gated. Refusal or selectivity out of sample
  is not specific to the caution direction and doubt gate, so the effect is not
  attributable to the instrument.

Any of B, C, D, or E is a non-promotion verdict recorded straight. The
prediction (shape A) and the falsifier (shapes B, C, D, E) are exhaustive over
the coverage table below, so no held-out result can land between them.

### Outcome

Resolved 2026-07-13, shape A: the falsifier does not fire and the frozen hs20
operating point is PROMOTED to a held-out claim about Qwen3.5-4B. Run: local
RTX 3090, single pass over the untouched held-out pool (1,332 confabs, 360
known-correct; doubt gate fired on 1,286/1,332 confabs and 17/360 knowns).
Gate artifacts: analysis-committed/heldout_summary.json (text-free);
row-level logs gitignored under analysis/runlog/ with per-row text and full
sub-grade dicts per the data-exhaust build-time rule. The lead independently
recomputed every gated rate from the row-level logs; all match exactly.

Gate results:

- G1 refusal transfer PASS: held-out fired-confab refused 872/1286 = 0.678
  (Wilson 95% [0.652, 0.703]) against the 0.60 floor.
- G1 format PASS: fired-confab well-formed 1256/1286 = 0.977 against the
  0.80 floor. Refusal and format decouple from corruption exactly as the
  in-sample window claimed.
- G1 cost PASS: gated-arm known-correct false refusal 14/360 = 0.039
  (fired knowns under the write plus unfired knowns at baseline) against the
  0.10 ceiling.
- G3(i) PASS: random_direction is a no-op (confab refused delta vs baseline
  +0.008, known delta 0.000). Its confab well-formed dips to 0.880, noted
  for completeness; no gate reads that surface.
- G3(ii) PASS: permuted_gate known false refusal 0.056 is strictly worse
  than the gated arm's 0.039, preserving gate-specificity.
- Instrument G0 held throughout: frozen operating-point hashes verified at
  launch (pipeline refuses placeholders and mismatches), single-launch
  run-log integrity, natural-stop rate 0.986 on knowns, degenerate 0.022.

Predictions adjudication: both scoreboard calls were shape A and both are
CORRECT. The observed 0.678 sits inside the orchestrator's recorded
0.62-0.70 band; the user's transfer call is vindicated on every leg.

Operational note (lab-notebook entry, same date): the first full-run launch
was refused by the RunLog fingerprint guard because pipeline smoke and run
share run-log paths; smoke logs were archived and the run relaunched clean.
No pinned module changed; future harnesses should namespace smoke logs.

One-sentence verdict (mirrored in experiment.yaml): the frozen hs20 mid-band
operating point transfers to the untouched Qwen3.5-4B held-out pool with
refused 0.678 / well-formed 0.977 / known cost 0.039 and intact placebo
specificity, promoting the doubt-gated caution-snap window from an in-sample
selection to a held-out claim about this model.

## Gates

Locked at sign; see `gates.yaml` for the machine-readable form. Wilson 95% CIs
(alpha 0.05) are reported on every rate. The primary gate floors mirror the
resolved ladder's own G1 conjunction and its cost-gate handling; the fleet's
stricter Wilson-bounded gate definitions are reported alongside as a
robustness lens but are not the pass/fail rule unless the PI elevates them at
sign (see the adjudication note in the handoff and `gates.yaml`
`fleet_style_reported_lens`).

- **G0 (instrument validity; stop, not outcome).** Loader resolves via
  `AutoModelForCausalLM.from_pretrained` on `Qwen/Qwen3.5-4B@851bf6e8...` under
  a transformers version recognizing `qwen3_5`; held-out source file
  sha256-verified before the local working file is built; held-out counts
  equal 1,332 confab + 360 known exactly; the three frozen hs20 vectors load
  byte-identical to the ladder's committed `directions/hs20/*.json` (sha256
  match, nothing refit) and the standardization scalars and tau_frozen load
  byte-for-byte from the ladder `build_manifest.json` hs20 block; dosed-smoke
  realized-projection readback within tolerance of target 12.608 on the gated
  and random arms; RunLog visibly grows during the run (projected > 15 min);
  no question text, aliases, or answer text appear anywhere under
  `analysis-committed/`.
- **G1 (primary held-out gate).** On fired held-out confabs, refused rate
  >= 0.60 with Wilson 95% lower CI > 0.50, AND well-formed rate >= 0.80,
  simultaneously. Cost gate: false-refusal rate over the full 360 held-out
  known-correct population <= 0.05 point estimate with Wilson 95% upper CI
  < 0.10, with the
  fired-known conditional (false-refusal among only the knowns the gate fires
  on) reported alongside, mirroring the ladder Outcome's cost-gate handling
  (system-level 10/240 = 0.042 with fired-known conditional 10/13 = 0.77).
  Baseline refusal on both roles reported (expected near 0).
- **G3(i) (placebo: direction specificity).** The random_direction arm's
  refusal rate is within 2 points of baseline on BOTH the held-out confab and
  the held-out known-correct populations.
- **G3(ii) (placebo: gate selectivity).** The permuted_gate arm's
  known-correct false-refusal rate is strictly worse (higher) than the gated
  arm's known-correct false-refusal rate.

## Predictions scoreboard

| Predictor | Call |
|-----------|------|
| orchestrator | Promotes (shape A): held-out fired-confab refused lands 0.62-0.70 with well-formed >= 0.85, known false-refusal 0.04-0.08, placebos behave. The frozen window transfers; the in-sample 0.60+ margin was not row-selection luck. (recorded 2026-07-13, pre-launch) |
| user | Promotes (shape A): the frozen hs20 window transfers to the held-out pool; refusal, format, cost, and placebo legs all clear. (recorded 2026-07-13, pre-launch) |

## Outcome

Resolved 2026-07-13 by the lead (`NOTEBOOK.md`, "RESOLVED shape A" entry;
`bin/exp resolve`). **Outcome shape A** occurred, as recorded in
`analysis-committed/heldout_summary.json` (`outcome_shape: "A"`): the falsifier
does not fire and the frozen hs20 operating point is PROMOTED to a held-out
claim about Qwen3.5-4B. The `### Outcome` subsection under the Falsifier above
records the same resolution; this section is the fuller transcription demanded
by the template and adds no content beyond it.

One-sentence summary (also in `experiment.yaml` `verdict:`): "The frozen hs20
mid-band operating point transfers to the untouched Qwen3.5-4B held-out pool
with refused 0.678, well-formed 0.977, known-correct false refusal 0.039, and
intact placebo specificity, promoting the doubt-gated caution-snap window from
an in-sample selection to a held-out claim about this model."

Every rate below is quoted from `analysis-committed/heldout_summary.json` with
its n, its success count, and its Wilson 95 percent interval, at four decimal
places where the artifact carries them. Nothing was refit: the write layer
(`hs_index` 20), the direction set, the threshold, the standardization scalars
and the dose (`dose_abs` 12.6082 = 8 x sigma_c, `gain_gated` 8.0) were loaded
verbatim from the resolved ladder.

### Fired held-out counts

The frozen gate fired on **1286 of the 1332 held-out confabs** and **17 of the
360 held-out known-correct rows**, 1303 fired rows in total
(`n_fired_confab`, `n_fired_known`, `n_fired_total`). The population was the
untouched held-out pool at its registered size, 1332 + 360 = 1692 rows, meeting
an intervention for the first time. The `permuted_gate` arm reproduced that
same total fire count as 1025 confab plus 278 known rows under the registered
fresh seed 20260713 (`heldout_permute_seed`).

### Gate results

- **G0 instrument validity: held throughout** (stop-gate, not an outcome).
  The frozen operating-point hashes were verified at launch and the pipeline
  refuses placeholders and mismatches; the run passed under single-launch
  run-log integrity. The dosed-smoke realized-projection readback was
  adjudicated under the shared MechInterp `SmokeConfig` contract recorded at
  sign (`write_rel_tol` 0.05, `write_abs_floor` 0.5, `offtarget_tol` 1e-3)
  against the target 12.608; the measured realized projection is **not
  recorded** in any committed artifact, which carries only the commanded
  `dose_abs` / `gain_random` of 12.6082. Degenerate and natural-stop hygiene
  from the summary: the `gated` known-role arm ran at natural stop 1.0000 with
  degenerate 0.0000, and the weakest known-role arm on this surface is
  `permuted_gate` at natural stop 0.9861 (355/360) with degenerate 0.0222
  (8/360).
- **G1 refusal transfer: PASS.** Fired-confab refused **872/1286 = 0.6781**,
  Wilson 95 percent [0.6520, 0.7030], against the 0.60 point floor and the
  requirement that the Wilson lower bound exceed 0.50. Both legs clear.
- **G1 format: PASS.** Fired-confab well-formed **1256/1286 = 0.9767**, Wilson
  [0.9669, 0.9836], against the 0.80 floor. Refusal induction and output
  well-formedness stay decoupled out of sample, which is the property the
  in-sample window claimed.
- **G1 cost: PASS.** Gated-arm false refusal over the full 360 held-out
  known-correct population **14/360 = 0.0389**, Wilson [0.0233, 0.0642],
  against the 0.05 point ceiling and the Wilson-upper ceiling of 0.10; both
  clear. Reported alongside as registered, the fired-known conditional is
  **14/17 = 0.8235**, Wilson [0.5897, 0.9381] — of the 17 knowns the gate fired
  on, 14 refused, so the system-level cost is low because the gate fires on few
  knowns, not because the write is gentle on the ones it fires on.
- **Baseline reference (registered as expected near zero, and it is).** Refused
  0/1332 = 0.0000, Wilson [0.0000, 0.0029] on confabs and 0/360 = 0.0000,
  Wilson [0.0000, 0.0106] on knowns. Baseline well-formed 1324/1332 = 0.9940 on
  confabs and 360/360 = 1.0000 on knowns.
- **G3(i) placebo, direction specificity: PASS.** The `random_direction` arm
  moved refusal by **+0.0083** on confabs (11/1332 = 0.0083 against a baseline
  0.0000) and by **0.0000** on knowns (0/360, unchanged from baseline), both
  inside the 2-point band on both populations
  (`gates.g3i.confab_delta_random_minus_baseline` 0.008258,
  `known_delta_random_minus_baseline` 0.0). Recorded for completeness and read
  by no gate: the placebo arm's confab well-formed dips to **1172/1332 =
  0.8799**, Wilson [0.8613, 0.8963], with natural stop 0.9354, so the matched-
  magnitude placebo write degrades output without inducing refusal.
- **G3(ii) placebo, gate selectivity: PASS.** The `permuted_gate` arm's
  known-correct false refusal is **20/360 = 0.0556**, Wilson [0.0362, 0.0842],
  strictly worse than the `gated` arm's 0.0389. Choosing the same number of
  rows at random rather than by the frozen gate costs more on the known side,
  so the row selection, not the raw dose count, is what limits false refusal.

### Row-level decoupling

**869 of the 1286 fired held-out confabs were simultaneously refused AND
well-formed** (`gated.fired_confab.row_level_decoupling`). The decoupling is a
property of individual rows on held-out, not only of the two marginal rates.
The corresponding counts on the cost side are 14 on both the fired-known
conditional and the full known population, and 0 on both baseline populations.

### Predictions scoreboard adjudication

Both recorded scoreboard calls were shape A and both are CORRECT. The observed
fired-confab refused rate of 0.6781 sits inside the orchestrator's pre-launch
0.62 to 0.70 band, and the well-formed, cost and placebo legs all landed inside
the calls as recorded.

### Scope limits carried from the signed text

- Tier 2, exploratory, one substrate. This promotes the hs20 mid-band window
  from an in-sample existence result to a held-out claim **about Qwen3.5-4B
  specifically**, and about the one frozen operating point scored here.
- Never pooled with the locked Phase 1 headline matrix, and never pooled with
  the `doubt-snap-cross-family-confirmatory` fleet, which is resolved
  not-promoted and used different gate definitions; those surfaces are governed
  separately.
- One dose and one layer: a confirmation of a single operating point, not a
  search. The FIT rows were not consumed here; only the held-out partition was
  scored.
- Batch parity, not single-row parity: the run used `batch_size` 8, following
  the ladder's Stage C precedent. Single-row parity was not verified there and
  is not claimed here.
- The fleet-style Wilson-bounded thresholds adopted at sign are the pass/fail
  rule; the ladder's point-estimate floors are reported as inner floors for
  continuity.
- Row-level logs with per-row text and full sub-grade dicts stay gitignored
  under `analysis/runlog/` per the data-exhaust rule; `analysis-committed/`
  carries counts, rates and ID-only manifests, no question, alias, or answer
  text.

### Run provenance and verification

The lead independently recomputed every gated rate from the row-level logs and
reports an exact match on all legs; the result is in-prediction and the
instrument was hardened and adversarially reviewed before signing, so lead
verification rather than a fresh red-team pass is the certification tier
applied. One operational event is on record and changed nothing: the first full
launch was refused by the RunLog fingerprint guard because pipeline smoke and
pipeline run share `analysis/runlog/` paths (n_rows 8 against 1692). That is
the resume guard working as designed; the smoke logs were archived, the
refusing attempt's log preserved, and the run relaunched clean. No pinned
module changed, and the materialize and anchor-capture artifacts were untouched
and reused.
