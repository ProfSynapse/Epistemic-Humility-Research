# qwen35-4b-midband-heldout

Status: draft (not signed; do not launch as confirmatory evidence).

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

## Prediction

The frozen hs20 operating point transfers to held-out: on the 1,332 held-out
confabs, the `gated` arm achieves fired-confab refused rate >= 0.60 AND
well-formed rate >= 0.80 simultaneously, with known-correct false-refusal
<= 0.10 over the full 360 held-out known-correct population; and the placebo
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

### Outcome-shape coverage (every shape maps to a verdict before launch)

| Shape | Held-out condition | Verdict |
|---|---|---|
| A | refused >= 0.60 AND well-formed >= 0.80 AND known false-refusal <= 0.10 AND G3(i) no-op AND G3(ii) strictly worse | PROMOTE: hs20 window is a held-out claim (prediction met) |
| B | refused < 0.60 | NOT promoted: refusal does not transfer (falsifier) |
| C | refused >= 0.60 AND well-formed < 0.80 | NOT promoted: decoupling does not survive held-out (falsifier) |
| D | refused >= 0.60 AND well-formed >= 0.80 AND known false-refusal > 0.10 | NOT promoted: not cost-safe out of sample (falsifier) |
| E | confab + cost thresholds clear BUT G3(i) not a no-op OR G3(ii) not strictly worse | NOT promoted: effect not instrument-specific out of sample (falsifier) |

The G0 checks are a pre-outcome instrument-validity stop and do not appear as a
shape: a G0 failure halts the run before any of A through E is scored and is
recorded as an instrument-validity stop, not as a held-out verdict.

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
  >= 0.60 AND well-formed rate >= 0.80 simultaneously. Cost gate: false-refusal
  rate over the full 360 held-out known-correct population <= 0.10, with the
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
| orchestrator | |
| user | |

## Outcome

Filled at resolve. Record the shape (A through E) that occurred, the gate
results (G0 / G1 / G3(i) / G3(ii)) with Wilson CIs on every rate, the fired
held-out counts, the row-level decoupling count, the placebo readbacks, and
the one-sentence summary that also goes into `verdict:` in the manifest.
