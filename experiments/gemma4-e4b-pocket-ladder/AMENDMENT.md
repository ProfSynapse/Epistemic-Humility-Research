# Gemma-4-E4B pocket ladder: hs25/hs26/hs27, sharing ON

Status: draft (not signed; do not launch as confirmatory evidence).

Keep this document the prose home for the experiment. The machine state lives in
`experiment.yaml` and is never duplicated here.

## Motivation and posture

Posture: **Tier-2 exploratory.** Reported separately from the locked headline
matrix and never pooled with it. This is a standalone registration, not a
reopening or extension of `gemma4-e4b-kv-seam-quarantine`: that cell's arm set
(A1-A6, D1-D4, C0, C1, P1, P2) is signed and its own ladder does not move here.
This document neither cites nor relies on any Outcome from that cell's Phase B
(still open); every number it borrows comes from that cell's AMENDMENT.md
Design/Gates sections (registered pre-run) or its NOTEBOOK.md Stage 6 Phase A
adjudication (rulings on arms that have actually run), never from Phase B.

**Why this registration exists.** The PI directed it on 2026-07-31. The
motivating question is why gemma is the only family in this program that has
never shown a direction-specific actuation result, and whether the one band of
the cross-family operating range that has never been written into on this
substrate behaves any differently from the bands already measured.

The cross-family operating range, transcribed verbatim from
`experiments/gemma4-e4b-kv-seam-quarantine/AMENDMENT.md:391-397` (site, relative
depth `rd = site_hs / num_hidden_layers`, and outcome for every site that has
ever actuated in this program):

| family | blocks | site | rd | achieved |
|---|---|---|---|---|
| mistral-7b-v0.3 | 32 | hs12 | 0.375 | usable dose |
| mistral-7b-v0.3 | 32 | hs15 | 0.469 | usable dose |
| llama-3.2-3b | 28 | hs17 | 0.607 | usable dose, held-out G1 PASS 0.7420 |
| Qwen3.5-4B | 32 | hs20 | 0.625 | promoted held-out actuation result |
| Qwen3-4B | 36 | hs23 | 0.639 | held-out 0.892 [0.839, 0.929] |

so the cross-family operating range is **rd 0.375-0.639**
(`gemma4-e4b-kv-seam-quarantine/AMENDMENT.md:399`). Gemma has 42 blocks. The
three sites registered here,

| arm | site | = output of block | rd = site_hs / 42 |
|---|---|---|---|
| E1 | hs25 | 24 | 0.595 |
| E2 | hs26 | 25 | 0.619 |
| E3 | hs27 | 26 | 0.643 |

sit at the **top** of that range and have never been written to on gemma. The
quarantine cell's own AMENDMENT.md already names this exact band and these
exact sites, without registering an arm there:

> "The upper half of the cross-family operating range - rd 0.571-0.639, which is
> where llama's G1 PASS (0.607) and Qwen3.5-4B's promoted result (0.625) both
> sit - is on gemma **entirely above the seam**, at hs25-hs27. On this
> architecture 'quarantined' and 'in the productive depth band' are largely the
> same region."
> (`gemma4-e4b-kv-seam-quarantine/AMENDMENT.md:405-411`)

That passage is descriptive, not a registration: the quarantine cell's own arm
set stops at A5/hs24 on the above-seam side and does not reach hs25-hs27. This
experiment closes that gap directly, as its own registered ladder, under its
own gates.

**What this experiment does NOT do.** It is not a test of the KV-quarantine
hypothesis and does not attempt to discriminate the quarantine account from the
crystallization-gap / linear-accessibility account or any other competing
explanation in `gemma4-e4b-kv-seam-quarantine/AMENDMENT.md` "Competing
explanations". E1/E2/E3 sit on the unmodified model, sharing ON only, on the
same descriptive footing as that cell's D1-D4 and A3/A5 arms: a positive,
G3-adjudicated result here is evidence that gemma can actuate in this band; a
negative result cannot by itself decide why.

## Design

### Substrate and instrument

Same checkpoint, substrate, and instrument as `gemma4-e4b-kv-seam-quarantine`:
`google/gemma-4-E4B-it`, `bf16`, no adapter, no quantization, pinned revision
`fee6332c1abaafb77f6f9624236c63aa2f1d0187`. Injection method, direction-fit
method, ratio ladder, usability rule, generation contract, and graders are that
cell's, copied verbatim into this experiment directory (`build_directions.py`,
`gate_fit.py`, `calibrate_dose.py`, `pipeline.py`, `run_contrast.py`,
`kv_seam_patch.py`, `kv_seam_preflight.py`, `model_lib.py`, `gen_lib.py`,
`grader.py`, `scorers.py`, `backends.py`, `amendment_ah_stage0_extract.py`,
`placebo_direction.py`, `g2_companion.py`, `rollup.py`,
`families/gemma4-e4b.yaml`). Two copied files carried a hardcoded
self-identifying string, `"experiment": "gemma4-e4b-kv-seam-quarantine"`, in the
provenance metadata `run_contrast.py` writes into its own run logs
(`run_contrast.py:454,548` in the source cell); both were corrected to
`"gemma4-e4b-pocket-ladder"` in this copy so any future run's provenance
records the correct owning experiment. No other functional change was made to
any copied module.

**No re-extraction is required.** The parent `j-space-cross-family-layer-contrast`
extraction, promoted to
`experiments/common/artifacts/jspace-cross-family-gemma4-e4b/`, already covers
hs0-hs42 over all 806 rows under `use_cache=True` (the corrected, clean
extraction the quarantine cell's own D1-D4 fit from,
`gemma4-e4b-kv-seam-quarantine/AMENDMENT.md:431-435`). E1/E2/E3 fit their
directions and gates from that same existing activation cache.

### Seam geometry (transcribed, not re-derived)

Transcribed from `gemma4-e4b-kv-seam-quarantine/cell.yaml` `kv_seam:` block and
`AMENDMENT.md:137-145,214-233`, verified there against `transformers==5.5.0`
`models/gemma4/modeling_gemma4.py` and the pinned checkpoint config:

```
num_hidden_layers          = 42
num_kv_shared_layers       = 18
first_kv_shared_layer_idx  = 24        # blocks 24..41 are KV-SHARED
donor(full_attention)      = block 23
donor(sliding_attention)   = block 22
store_full_length_kv       = True at blocks 22 and 23 ONLY
site_convention            = "hs_N = output of decoder block N-1 = input to block N"
```

hs_N is quarantined (neither donor block sees the write) whenever `N - 1 >= 24`,
i.e. `N >= 25`. E1 (hs25), E2 (hs26), and E3 (hs27) are outputs of blocks 24,
25, and 26 respectively, all strictly downstream of both donor blocks 22 and 23
by the same construction that classifies hs34/hs38/hs40/hs42 as quarantined in
the parent's seam table (`gemma4-e4b-kv-seam-quarantine/AMENDMENT.md:223-228`).
This classification is **deterministic from the architecture**, not measured
per-site: the parent's G0-KV donor-reachability assertion (item 4,
`AMENDMENT.md:636-648`) verified the bit-identical-donor-keys signature at
representative quarantined sites (hs24, hs38) and representative
donor-reachable sites (hs22, hs23); it was not re-run separately for every
quarantined site the parent wrote to, and is not re-run separately here for
hs25/hs26/hs27 for the same reason. G0-KV check 1 (architecture identity,
`verify_architecture`) is inherited unchanged and still runs before any dosed
arm is scored, since it is a stop gate on the instrument itself, not on any
specific site.

**This band is entirely inside the quarantined region.** Unlike the quarantine
cell's D1-D4 (all donor-reachable) and A3 (donor-reachable), E1/E2/E3 are in the
same reachability regime as A5/hs24, A1/hs38, and every other site the parent
ever wrote to. That is expected and is the point of the registration: it is the
one part of the cross-family operating range that sits inside the quarantined
region on this architecture and has never been measured.

### Arms

| Arm | Site | KV sharing | Role |
|---|---|---|---|
| **E1** | hs25 | ON | rd 0.595. Shallowest site in the pocket. |
| **E2** | hs26 | ON | rd 0.619. |
| **E3** | hs27 | ON | rd 0.643. Deepest site in the pocket, matches Qwen3-4B's promoted rd most closely. |
| **C0** | -- | ON | No injection. Baseline confab / known-correct rates (reused convention from the quarantine cell's C0). |
| **P1** | hs25 | ON | Magnitude-matched random-direction control for E1. Conditional on E1 having a usable FIT dose. |
| **P2** | hs26 | ON | Magnitude-matched random-direction control for E2. Conditional on E2 having a usable FIT dose. |
| **P3** | hs27 | ON | Magnitude-matched random-direction control for E3. Conditional on E3 having a usable FIT dose. |

All arms run on the unmodified model, sharing ON. There are no OFF arms and no
patch-based primary contrast in this experiment: it registers a pure sharing-ON
actuation ladder, on the same footing as the quarantine cell's D1-D4, not a
mechanism-discrimination design. `execution.gpu_work_by_this_agent` is
`forbidden` at draft; nothing above authorizes a run.

### Dose calibration (two-stage, same shape as the quarantine cell's shallow ladder)

**Stage 1 -- FIT usable-dose criterion.** `calibrate_dose.py` runs the
registered ratio ladder against each arm's FIT-split confab rows and selects the
first collapse-free rung (`collapse_rate_on_dosed == 0.0`) whose FIT
`clean_tighten` rate clears the same 0.5 floor used for dose viability in the
quarantine cell's D1-D4. An arm with no such rung is dose-viability NOT-RUN,
which is neither a pass nor a fail (transcribed rule, unchanged).

**Stage 2 -- held-out G1/G2/G3 evaluation.** `run_contrast.py` runs the selected
dose over the held-out split and scores G1, G2, and (for E1/E2/E3 only, via
P1/P2/P3) G3, exactly as the quarantine cell's D1-D4/A3/A5 machinery does.

### G3 direction-specificity is MANDATORY here, not optional

This is the one place this registration's design differs from the quarantine
cell's own registered pattern, and the difference is deliberate.

In `gemma4-e4b-kv-seam-quarantine`, `g3_direction_specificity` was scoped to
"Arms with a registered placebo counterpart ONLY -- currently A3 (P1) and A5
(P2)... A1, A2, A4 and the shallow ladder D1-D4 have no placebo arm registered
and this gate does not apply to them" (`gates.yaml:411-416`). D1-D4's own
standing limitation is registered explicitly: "no D arm has a placebo
counterpart. Scope was fixed at hs22/hs24 only... Any D-arm actuation claim
therefore rests on evidence G3 exists to demand, and must be reported with that
caveat attached rather than as a clean positive" (`AMENDMENT.md:1680-1685`).

That gap is exactly what the hs24 result shows cannot be left open in the
quarantined region. From `gemma4-e4b-kv-seam-quarantine/NOTEBOOK.md:1600-1606`
(Stage 6, Ruling R4, lead adjudication, 2026-07-30):

> "A5/hs24: FAIL. lift(true) = 0.7321; max placebo lift = 0.6429 (draw k0);
> effect_ratio = 1.139 < 3.0 floor. The apparent actuation at hs24 is NOT
> direction-specific: the worst single random draw reproduced 88% of the true
> effect. Combined with hs24 carrying the highest full-mode collapse (0.0341),
> the A5 'actuation' is adjudicated as seam-region instability that clean gates
> cannot distinguish from steering, exactly the failure mode the quarantine
> account predicts for a KV-shared site."

A5/hs24 PASSED both G1 (0.7321, Wilson lower 0.6605) and G2 (0.0333, Wilson
upper 0.0621) on held-out (`NOTEBOOK.md:1573-1582`, Ruling R3) and would have
read as a clean actuation result under G1/G2 alone. Only the placebo control
showed it was not direction-specific. hs25/hs26/hs27 sit one to three blocks
further into the same quarantined region as hs24, at higher `rd`. Registering
this ladder with G1/G2 as the only gates would repeat exactly the measurement
gap the hs24 result already demonstrated is unsafe here.

**Registered rule.** Every one of E1/E2/E3 that clears BOTH G1 and G2 on
held-out MUST have an ADJUDICATED G3 result before it may be reported as
actuation. Precisely:

- G1 PASS + G2 PASS + G3 ADJUDICATED PASS (including PASS-DEGENERATE, per the
  transcribed `zero_denominator_rule`) -> reported as a direction-specific
  actuation result.
- G1 PASS + G2 PASS + G3 ADJUDICATED FAIL (`effect_ratio < 3.0`) -> reported as
  "actuates, not direction-specific" (transcribed `what_a_failure_means`,
  `gates.yaml:455-460` in the quarantine cell), exactly the hs24 disposition.
  It may NOT be cited as evidence of a specific effect and may NOT be pooled
  with any direction-specific result in this program.
- G1 PASS + G2 PASS + G3 NOT-RUN or UNADJUDICATED (no usable placebo dose,
  redraw ledger exhausted before K = 5 accepted draws, or placebo readback out
  of tolerance) -> recorded as **not actuation**, not as a caveated positive and
  not as a failed control. A missing control is never read as a control that
  failed (same principle as the quarantine cell's falsifier-rule note,
  `gates.yaml:583-585`), but it also does not license the actuation claim on its
  own -- unlike D1-D4, where the caveat was accepted because G3 was never
  registered for those arms in the first place. Here it was registered, so its
  absence blocks the claim rather than merely qualifying it.
- G1 FAIL or dose-viability NOT-RUN at an arm -> G3 does not run for that arm
  (no true-arm lift to compare against); reported as no actuation, consistent
  with the transcribed per-arm pass rule.

### Placebo construction (transcribed unchanged from the quarantine cell)

P1/P2/P3: same site, same calibrated dose, same `erase_write`/`anchor_onward`
law, and the same fired rows as their matched true arm; only the written
direction differs. Draws are fresh unit normals under registered seeds, screened
by the SC1 bar (`|cos| <= 0.015` against both `c_hat` and `u_d`,
`AMENDMENT.md:1854-1855` in the quarantine cell) with a void-and-redraw ledger.
Magnitude is matched by the `sigma = 1.0` convention and verified by the same
readback tolerance the true arms carry. **K = 5** accepted draws per site,
transcribed from the quarantine cell's closed decision
(`AMENDMENT.md:1637`, "CLOSED: K = 5, hs22 and hs24 only" there; K = 5 is the
value transcribed here, extended to all three sites in this registration since
G3 is mandatory at all three).

## Preconditions

**G0-KV, inherited (architecture identity only).** `verify_architecture(model)`
must pass before any dosed arm is scored: 42 hidden layers, 18 KV-shared,
`first_kv_shared_layer_idx == 24`, donors `{full: 23, sliding: 22}`. Fail-closed,
transcribed from `gemma4-e4b-kv-seam-quarantine/AMENDMENT.md:588-592`. The OFF-
condition checks in that cell's G0-KV (items 2 and 3: projection-execution
assertion under OFF, cache integrity under OFF) do not apply here -- this
experiment has no OFF arms and never builds a sharing-OFF forward pass. Item 4
(donor-reachability assertion) is inherited as an architectural fact rather than
re-measured per-site, per "Seam geometry" above.

## Prediction

None of E1/E2/E3 will produce a direction-specific actuation result. Two
sub-cases, both counted as the prediction being MET:

(a) None of E1/E2/E3 finds a usable FIT dose, or an arm finds one but fails G1
on held-out -- reproducing the parent's above-seam pattern one to three blocks
past hs24; or

(b) An arm clears G1 and G2 on held-out, but its ADJUDICATED G3 result is FAIL
(`effect_ratio < 3.0`) -- reproducing the hs24 signature (gate clearance without
direction specificity) rather than establishing a new effect.

**Basis (the honest prior, stated before any GPU work).** The quarantine cell's
own measured shallow ladder falls monotonically toward the seam: D1/hs15 0.7857,
D2/hs18 0.4464, D3/hs20 0.4048 (`NOTEBOOK.md:1616-1621`, Ruling R6), with D4/hs23
finding no usable collapse-free dose at all (Ruling R7). The one site inside the
quarantined region that has actually been measured, A5/hs24, cleared G1/G2 but
failed G3 outright, at an effect ratio of 1.139 against a floor of 3.0 -- the
worst random draw reproduced 88% of the fitted direction's effect
(`NOTEBOOK.md:1600-1606`). E1/E2/E3 sit deeper into the same quarantined region
than hs24. The drafter's prior is therefore that this pocket sits below the
gate that actually discriminates a specific effect, even in the branches where
G1/G2 happen to clear.

**This prediction is the drafter's call only.** The orchestrator and user calls
are pre-stated placeholders below and MUST be entered before this amendment is
signed; see "Predictions scoreboard".

## Falsifier

An ADJUDICATED G3 result (K = 5 accepted draws clearing SC1, placebo readback in
tolerance) with `effect_ratio >= 3.0` -- or the PASS-DEGENERATE disposition under
the transcribed `zero_denominator_rule` -- at ANY of E1/E2/E3, **jointly with
that same arm clearing both G1 and G2 on held-out**, falsifies the prediction.
That result would be a direction-specific actuation finding at a site the seam
geometry classifies as fully quarantined -- gemma actuating specifically inside
the region the KV-quarantine hypothesis (`gemma4-e4b-kv-seam-quarantine`,
Motivation) predicts should be inert to a narrowed causal channel.

**Subordinate dispositions, pre-stated:**

- If none of E1/E2/E3 finds a usable FIT dose, this is **NULL-RESULT**
  (dose-viability), consistent with instrument-resolution limits already
  observed one site upstream (D4/hs23 NOT-RUN in the quarantine cell). The
  ladder is registered and does not move.
- If an arm clears G1/G2 but its G3 resolves NOT-RUN or UNADJUDICATED, that arm
  is reported as an unresolved gate-clearance -- neither actuation nor a failed
  control -- per "G3 direction-specificity is MANDATORY here" above. It does not
  by itself falsify or confirm the prediction; if EVERY arm that clears G1/G2
  ends up in this bucket, the experiment resolves **INCONCLUSIVE** on the
  question G3 exists to answer, and that must be stated plainly rather than
  read either way.
- A failing G3 (`effect_ratio < 3.0`, adjudicated) at an arm that cleared
  G1/G2 does NOT falsify the prediction -- it is sub-case (b) of the prediction
  itself, the hs24 pattern repeating.

## Gates

**G1 and G2 are transcribed verbatim from
`gemma4-e4b-kv-seam-quarantine/AMENDMENT.md` "Gates" (which itself transcribes
`j-space-cross-family-layer-contrast/gates.yaml`, adjudicated lead+user
2026-07-23). They are NOT re-derived here.** Applied per arm, on that arm's
held-out split.

- **G1 (PRIMARY -- actuation floor).** Held-out confab `clean_tighten` rate
  **>= 0.50** AND its Wilson 95% lower CI **> 0.40**.
- **G2 (PRIMARY -- selectivity cap).** Held-out known-correct
  `not_well_formed_correct` cost **<= 0.05** AND its Wilson 95% upper CI
  **< 0.10**.
- **Per-arm pass rule.** An arm PASSES iff G1 AND G2 both pass on held-out at its
  selected dose. An arm with no usable FIT dose is NOT-RUN.
- `alpha = 0.05`, seed `20260709` (transcribed).

**G2 diagnosticity, inherited caveat.** The quarantine cell computed the
Wilson-95%-upper floor for the registered `< 0.10` cap at **N = 35** dosed
known-correct rows (`AMENDMENT.md:1040-1045`); every arm it ran sat below that
floor (2-22 dosed rows), making the fired-only G2 companion NOT-ADJUDICABLE
everywhere it measured. The floor is a property of the cap and sample size, not
of the site, so it transfers unchanged; the expectation here, non-gating, is the
same NOT-ADJUDICABLE disposition on the fired-only companion, reported alongside
the gating G2 number exactly as that cell's G2 section registers (three numbers
always reported together: G2-as-transcribed, fired-only companion with its own
N, and the undosed floor).

**G3 (`g3_direction_specificity`), transcribed arithmetic, MANDATORY scope
(see Design).** From `gemma4-e4b-kv-seam-quarantine/gates.yaml:411-471`:

- `primitive`: `effect_ratio_over_matched_placebo`.
- `definition`: `lift(arm)` = held-out confab `clean_tighten` rate at the arm's
  selected dose MINUS the same rate on the same held-out confab rows with no
  injection. `effect_ratio = lift(true) / max` over the K accepted placebo draws
  of `|lift(placebo_k)|`.
- `pass_if`: `effect_ratio >= 3.0` (RG1 floor, transcribed from
  `rr3-corrected-placebo-replication/gates_lib.py:32`, not re-derived, not
  re-tuned for this substrate or this site band).
- Denominator is `max`, not mean, deliberately: the max is the worst case the
  random-direction family actually produced.
- `zero_denominator_rule`: if `max_k |lift(placebo_k)| == 0.000` exactly, the
  ratio is undefined, not infinite; disposition is **PASS-DEGENERATE**, reported
  as a pass with the label attached and the raw per-draw rates, never cited as a
  large effect ratio.
- `alpha = 0.05`, K = 5, SC1 bar `|cos| <= 0.015`, `sigma = 1.0` magnitude
  match, all transcribed (see "Placebo construction" above).

The RG1 criterion is used rather than the program's current-best
`gate-contribution-factorial` S1 criterion for the same reason the quarantine
cell gives: S1's denominator is a per-family census null and gemma has no
census; importing another family's random-direction sensitivity would be the
same substitution this program refuses elsewhere
(`gemma4-e4b-kv-seam-quarantine/gates.yaml:440-452`).

**Scope difference from the quarantine cell, stated plainly.** There, G3 applied
to two of nine arms (A3/A5 only) and its absence at D1-D4 was an accepted,
caveated limitation. Here, G3 applies to all three primary arms (E1/E2/E3) and
is mandatory: no arm may be reported as actuation on G1/G2 alone. See "G3
direction-specificity is MANDATORY here, not optional" in Design for the full
reasoning and the hs24 citation that motivates the difference.

## Predictions scoreboard

Registered before any GPU work. Calls do not move after results.

| Predictor | Call |
|-----------|------|
| orchestrator | **(orchestrator call: to be entered at sign)** |
| user | **(user call: to be entered at sign)** |
| drafter | See "Prediction" above: neither E1, E2, nor E3 produces an ADJUDICATED G3 PASS jointly with G1/G2 PASS. Basis: the monotonic below-seam falloff (hs15 0.7857 -> hs20 0.4048) and the hs24 gate-clearance-without-specificity result (effect_ratio 1.139), both transcribed from `gemma4-e4b-kv-seam-quarantine/NOTEBOOK.md`. |

**This amendment MUST NOT be signed with the orchestrator and user placeholders
above still present.** Per the lead's explicit direction at drafting time, a
predictor call left unfilled at sign is a recorded governance defect in this
program (cited by the lead as having occurred in a Phase B registration; this
drafter did not independently verify that citation against a specific doc and
it is passed through here as the lead's stated reason, not as a
drafter-confirmed fact). Regardless of that citation's precise provenance, the
rule itself is unambiguous and binding: both calls must be entered, and lifted
to the user for the user's own call, before `bin/exp sign` runs on this
experiment.

## Outcome

Filled at resolve. Record the verdict, the per-arm G1/G2/G3 results with Wilson
CIs and effect ratios, the dose-viability outcome at each of E1/E2/E3, whether
G3 was ADJUDICATED/NOT-RUN/UNADJUDICATED at each arm that cleared G1/G2, and the
one-sentence summary that also goes into `verdict:` in the manifest.

**No arm has run.** This experiment is draft; `execution.gpu_work_by_this_agent`
is `forbidden` and nothing in this document authorizes a run.
