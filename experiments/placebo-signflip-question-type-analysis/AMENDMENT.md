# Placebo sign-flip: question-type stratification of the family-specific random-direction response

Status: RESOLVED (signed, run, red-teamed, and resolved 2026-07-14; see the
Outcome section and `experiment.yaml` for the terminal state). Header correction
note: this line originally read "draft (not signed)" from scaffold time and was
not updated at sign/resolve; corrected at resolve. CPU-only retrospective
re-read of generation text, grades, and pre-generation anchor hidden states
that already exist on disk under gitignored `analysis/` trees. No model is
loaded, no GPU is used, no new generation or grading is produced.

Keep this document the prose home for the experiment. The machine state lives in
`experiment.yaml` and is never duplicated here.

## Motivation and posture

The wide-instrument calibration
(`abstention-wide-instrument-calibration`, resolved 2026-07-14, measurements
certified by adversarial red-team review) established that the
matched-magnitude random-direction placebo response is family-specific in
SIGN: at the qwen promoted operating point the random write SUPPRESSES hedging
by -5.13 points (paired wide, n = 1,286), while at the mistral RR2 operating
point it RECRUITS hedging by +7.39 points (paired wide, n = 1,312). The
calibration Outcome reads these as genuinely family-graded and closes with a
design rule (register placebo tolerances against per-family wide baselines);
it does not explain WHY the sign differs across families.

The program's two-signal work
(`base-model-training-free-mechanism`, section 7) established that
answerability is a near-saturated pre-generation activation axis: on the raw
Qwen base with no adapter, the known-vs-unknown gate reads off the
pre-generation anchor at 0.997 AUROC. If question type (answerable vs
unanswerable) places a prompt at a near-deterministic position on a pre-generation
caution/doubt axis before any write, then question type is a candidate
explanation for, or modulator of, the family-specific placebo sign: a random
displacement lands differently depending on where the prompt already sits on
that axis, and the two families' pools may differ in question-type composition
or in how question type maps to the axis.

This experiment tests that candidate on existing artifacts only. Posture:
exploratory lab-diagnostic tier. It produces measurements and a mechanistic
reading; it CANNOT alter, upgrade, or caveat any locked verdict. The
qwen35-4b-midband-heldout shape-A promotion, the RR2 falsified verdict, the RR
cross-family shape-F verdicts, and the calibration resolution all stand exactly
as registered regardless of what this re-read finds. Its outputs bind only
future registrations and paper reporting language, where they appear as clearly
labeled exploratory re-analysis, never pooled with locked numbers.

The answerable-side coverage gap this document repeatedly flags is closed
prospectively by RR3's rider (`rr3-corrected-placebo-replication`, signed and
running on `exp/rr3-corrected-placebo`), which doses answerable rows with the
random direction under power. This amendment does NOT wait for or depend on RR3
data; it analyzes only what is already persisted, and states explicitly where
its answerable-leg reads are limited to what exists (qwen n = 17 dosed, mistral
n = 0 dosed) and must be superseded by RR3's powered version later.

## Design

### Stratification axis: question type from the source field, not role

The stratification axis is QUESTION TYPE, read from each row's data source:
`triviaqa` and `popqa` rows are answerable (a correct answer exists), `kuq`
(Known-Unknown Questions) rows are unanswerable. Source is read from the
`row_key` prefix, which the on-disk runlogs and anchor manifests carry
verbatim (`kuq_unknowns_all:*`, `popqa:*`, `triviaqa:*`).

Question type is deliberately NOT taken from the `role` label
(`confab` / `known_correct_answered` / `unknown_refused`). Role conflates
question type with the model's own undosed baseline BEHAVIOR: a `kuq` row is
labeled `confab` only when the undosed baseline attempted an answer and
`unknown_refused` when it abstained, so role is a post-hoc behavioral split of
a single question type and cannot serve as an exogenous stratifier of the
mechanism. Source is exogenous to the write and to the model's behavior, so it
is the correct axis. Where role and source happen to be collinear in a given
pool (see the structural finding below), the analysis states the collinearity
rather than hiding behind the role label.

### The structural finding that reframes the question (verified on disk)

Every placebo (random-direction) generation that exists on disk, in every
family and every cell, was produced on an UNANSWERABLE (`kuq`) row. The
answerable side of the axis was dosed with the random direction only in the
qwen heldout known population (n = 17) and never in mistral or in the qwen
ladder. Verified counts (row_key-prefix tally over the staged runlogs):

| Cell | Family | Arm | Unanswerable (kuq) dosed | Answerable (popqa+triviaqa) dosed |
|------|--------|-----|--------------------------|-----------------------------------|
| QH | qwen35-4b | random_direction | 1,286 confab | 17 known (15 popqa + 2 triviaqa) |
| QL | qwen35-4b | random_direction | 7,000 confab (28 layer x dose cells) | 0 |
| MC (RR2) | mistral7b-v03 | random_direction | 1,303 confab (+9 non-fired baseline-fill = 1,312) | 0 |

Consequence: the certified family-specific placebo SIGN (qwen -5.13, mistral
+7.39) is measured ENTIRELY on the unanswerable stratum in both families.
Question type is therefore held CONSTANT (unanswerable) across the two signs
that define the phenomenon. This is itself the first-order answer to the PI's
question at the behavioral level: question type cannot be the explanation for
the cross-family sign difference in the existing placebo data, because it does
not vary across the rows that produced that difference. The within-family
answerable-vs-unanswerable behavioral contrast is unpowered (qwen) or absent
(mistral, QL) on existing artifacts and is deferred to RR3.

Two axes of analysis survive this and are the substance of the design:

1. A BEHAVIORAL leg on what exists: report the placebo delta on the
   unanswerable stratum straight (it is the certified number), report the qwen
   answerable leg at its true power (n = 17, uninformative), register the
   mistral/QL answerable legs as coverage gaps, and add a finer WITHIN-unanswerable
   descriptive breakdown by `kuq` subcategory, which is powered and is the only
   question-type-like resolution available on the dosed rows.
2. A MECHANISM leg where question type IS powered: the pre-generation ANCHOR
   hidden states were extracted for BOTH answerable and unanswerable prompts
   (they are read before any write and do not depend on dosing), so the
   projection of answerable vs unanswerable prompts onto each family's
   doubt/caution direction is fully powered on existing artifacts. This is
   where the "does question type place a prompt differently on the caution
   axis" question is actually testable.

### Cells (behavioral leg, CPU re-read of existing grades)

All rates use the frozen wide instrument exactly as the calibration harness
applied it (detector-v2-refused OR blinded-adjudicated-abstention, per row);
this analysis re-slices grades already committed under the calibration's blind
protocol and adds no new grading pass. The per-row wide grade is read from the
calibration harness's persisted row-level log
(`row_level_scored.jsonl`, field `sub_grade.refused_final`), which is the same
per-row grade that produced the certified aggregates; the re-slice reproduces
the certified confab delta bit-for-bit as a coverage check (see gate BG0).

**Cell A (QH, qwen heldout placebo delta by question type).** Source: the
`qwen35-4b-midband-heldout` runlogs `baseline.jsonl` and `random_direction.jsonl`
joined to the calibration `row_level_scored.jsonl` wide grade by
(row_key, arm). Paired wide abstention delta (random minus baseline over rows
present in both arms), computed separately for:
- unanswerable (`kuq`, role confab): n = 1,286 paired. This IS the certified
  -5.13-point delta (baseline 139/1,286 = 0.108, random 73/1,286 = 0.057).
- answerable (`popqa`+`triviaqa`, role known): n = 17 dosed, 1 paired with a
  wide grade in both arms; wide abstention is 0 in both arms. Reported at its
  true power and labeled uninformative; RR3 supplies the powered version.

In this pool role and source are perfectly collinear (every dosed `kuq` row is
role confab, every dosed answerable row is role known), so the source-stratified
delta coincides with the role-stratified delta; the amendment states this
collinearity explicitly and uses source as the named axis for cross-family
consistency.

**Cell B (MC / RR2, mistral placebo delta by question type).** Source: the
`rr2-mistral-adjudicated-refusal-confirm` runlogs `heldout__baseline.jsonl` and
`heldout__random_direction.jsonl`, with the wide grade taken from RR2's
committed `final_report.json` (transcribed, not re-graded, identical to the
calibration MC treatment). Unanswerable (`kuq`, confab): n = 1,312, delta +7.39
points (baseline 368/1,312 = 0.280, random 465/1,312 = 0.354). Registered
caveat: the random arm on disk has 1,303 rows because the gate did not fire on
9 confabs; those 9 non-fired rows inherit baseline text (no write applied), so
they are filled from `heldout__baseline.jsonl` by row_key to reach the full
paired n = 1,312, exactly as RR2's RG3 leg computed it. Answerable: n = 0 dosed;
this is a registered coverage gap, not a null; RR3 supplies it.

**Cell C (QL, qwen ladder narrow-only dose-response by question type and layer).**
Source: the `qwen35-4b-midband-doubt-snap` random-direction ladder as staged in
the calibration `row_level_scored.jsonl` (QL cell: 4 layers hs20/23/26/30 x 7
doses 2/4/6/8/12/16/20 x 250 rows = 7,000), against the QL baseline confab
reference. Wide rates are VOIDED for QL: the calibration Outcome terminally
voided the QL wide lane under the registered grader-calibration rule
(CG1 clear-positive floor failed twice on QL_shard_07), so only the
detector-v2 (narrow) rate is admissible. Every dosed QL row is unanswerable
(`kuq`); there is no answerable stratum in QL. The cell therefore reports the
narrow random-refusal rate as a function of (layer, dose) on the unanswerable
stratum only, and states that the answerable-by-dose surface does not exist on
disk. This reproduces and re-slices the calibration Outcome's narrow
dose-response (flat-to-falling in dose on every layer), now with the explicit
question-type label attached.

**Secondary within-unanswerable descriptive breakdown (Cells A and C).** The
`kuq` pool carries a `category_canon` subtype per row (controversial/debatable,
counterfactual, question-with-false-assumption, unsolved-problem/mystery,
future-unknown, underspecified). As the only powered question-type-like
resolution available on the dosed rows, report the QH paired wide placebo delta,
the mistral RR2 paired wide placebo delta (lead decision at sign: extended to
mistral so the recruitment pole gets the same within-type resolution as the
suppression pole), and the QL narrow dose-response, each broken down by these
six subcategories (roughly 150-300 QH rows each). This is descriptive and
exploratory: it asks whether the qwen suppression and the mistral recruitment
concentrate in particular unanswerable subtypes rather than being uniform
across them. No gate rides on it; it is reported with per-cell counts and
Wilson CIs and flagged as hypothesis-generating only.

### Mechanism probe (pre-generation projection, CPU re-read of anchors)

This is the leg where question type is powered on existing data, because the
pre-generation anchor hidden states exist for answerable AND unanswerable
prompts regardless of whether the row was dosed. Anchor coverage verified on
disk:

| Family | Anchor artifact | Layer(s) | Unanswerable (kuq) | Answerable (popqa+triviaqa) |
|--------|-----------------|----------|--------------------|-----------------------------|
| qwen35-4b | `qwen35-4b-midband-heldout/analysis/anchor_extract_heldout.safetensors` (2560-dim, last prompt token) | hs20 | 1,332 | 360 (133 popqa + 227 triviaqa) |
| mistral7b-v03 | `rr2-.../analysis/anchors_at_candidate_layers.json` | 16 | 2,400 | 637 (144 popqa + 493 triviaqa) |
| llama32-3b | `rr-cross-family-raw-refusal/analysis/llama/anchors_at_candidate_layers.json` | 20, 22, 23 | 2,400 | 556 (90 popqa + 466 triviaqa) |

Each family's frozen doubt direction `u_d` and caution direction `c_hat`
(and the placebo `random_direction`) exist at the matching anchor layer:
qwen hs20 in `qwen35-4b-midband-doubt-snap/analysis-committed/directions/hs20/`,
mistral hs16 reconstructed by RR2's `fit_reuse.py` and pinned in RR2's
`hs16_fit_build_manifest.json` (deterministic double-fit, G0-verified), llama
per-layer fits from the RR cross-family cell / the doubt-snap-cross-family
fleet. Each direction JSON is self-contained (unit `vector`, per-feature `mu`
/ `sigma` standardization, `intercept`, `layer`); the scalar-score
standardization (`mu_d`, `sigma_d`, `mu_c`, `sigma_c`, `tau_frozen`) lives in
the layer's `build_manifest.json` block.

**Contrast M1 (pre-generation position by question type).** For each family,
standardize every anchor into the frozen fit frame and project onto `u_d`
(doubt) and onto `c_hat` (caution). Test whether the standardized doubt
projection and the standardized caution projection differ between answerable
and unanswerable prompts (two-sided Mann-Whitney U plus a standardized mean
difference with a bootstrap 95% CI, per family, per direction). Pre-stated
directional expectation from the two-signal answerability finding: unanswerable
prompts sit HIGHER on the doubt/caution axis pre-generation than answerable
prompts, in every family. This is the powered question-type contrast the
behavioral leg cannot supply.

**Contrast M2 (does the sign of the family's placebo response track its
baseline doubt position).** Cross-family, relate each family's pre-generation
unanswerable doubt/caution projection (its central tendency and its spread) to
the certified placebo sign (qwen suppress, mistral recruit). The lead's working
hypothesis to structure, NOT to assert: the family that already sits high and
saturated on the caution axis at baseline (mistral, wide baseline 0.280) has
more room to be pushed UP by a random displacement (recruitment), while the
family that sits low with headroom (qwen, wide baseline 0.104) is pushed toward
its center / DOWN (suppression). Contrast M2 is descriptive across three
families (qwen, mistral, llama-baseline-only) and is explicitly underpowered as
a cross-family regression (n = 2 families with a placebo sign); it is framed as
consistency-or-not with the hypothesis, never as a test of it.

**Contrast M3 (realized displacement onto the caution axis, qwen and mistral
only).** The placebo write is an erase-write-to-magnitude: the realized
projection onto the dosing (random) direction is the target `dose_abs`
(verified: qwen `readback_measured` mean 12.625 vs target 12.608; mistral
target 3.665 = 12 x sigma_c). Because the write is deterministic and the frozen
vectors are on disk, the realized post-write projection onto `c_hat` at the
anchor token is reconstructable ANALYTICALLY without needing the post-write
state persisted:

    proj_c_hat(post) = proj_c_hat(pre)
                     - <anchor_std, r_hat> * <r_hat, c_hat>
                     + dose_abs * <r_hat, c_hat>

where `r_hat` is the unit random direction and all quantities are on disk.
Compute the realized caution-axis displacement (post minus pre) per row and
test whether it differs by question type (it is expected NOT to, since the
row-dependent term `<anchor_std, r_hat>` is small and question-type-independent
by construction; a non-null here would itself be a finding). Report the
displacement distribution and its question-type split for qwen (dose_abs
12.608) and mistral (dose_abs 3.665). DROP M3 for llama: the RR cross-family
llama leg stopped at shape F before any placebo/random arm ran, so no llama
realized displacement exists on disk. This is stated in the design, not
discovered at run time.

Every mechanism contrast requires the two-stage standardized-score-to-projection
chain to be ported EXACTLY from the doubt-snap fit/gate code (per-feature mu/sigma
from the direction JSON, then scalar mu_d/sigma_d/tau_frozen from the layer
build_manifest). A scoping smoke over the qwen anchors confirmed the artifacts
load and project numerically but that a naive single-stage projection does NOT
reproduce the frozen gate's per-row firing decision; gate BG1 below makes exact
reproduction of the firing decision the acceptance test for the frame port, so
the projection frame is validated before any question-type contrast is trusted.

### Blinding and containment

No new grading pass is planned; every grade is read from the calibration and
RR2 committed blind lanes. If any step were found to require re-grading text, it
would have to use the frozen wide instrument in a context-free blinded lane per
standing PI directive, or be dropped; the design contains no such step. No
question, answer, or generation text enters any committed file: cells key on
`row_key` and `category_canon` (a taxonomy label, not question text) only.
Row-level joins and per-row projections stay under gitignored `analysis/`; only
aggregates (deltas, projection statistics, CIs, dose-response tables) go under
`analysis-committed/`.

### Deliverable

`analysis-committed/signflip_report.json`: per family, per cell, the
question-type-stratified placebo delta (behavioral leg) with Wilson CIs and
paired-n; the within-`kuq`-subcategory breakdown; the QL narrow dose-response by
(layer, dose); and the mechanism-leg projection statistics for M1/M2/M3 with
bootstrap CIs. Plus a short design-note section in the Outcome stating, in one
paragraph, whether question type modulates the placebo response at the
behavioral level (given the coverage constraint), whether it modulates
pre-generation caution position (M1), and whether the two are consistent with
the family-specific sign (M2), with the answerable-side conclusion explicitly
deferred to RR3.

## Prediction

Question type does NOT explain the cross-family placebo sign difference. At the
behavioral level the sign is a family property measured entirely on the
unanswerable stratum, so it cannot be attributed to question-type mixing. At the
mechanism level (M1), unanswerable prompts sit higher than answerable prompts on
the pre-generation doubt/caution axis in every family (consistent with the
near-saturated answerability gate), and within the unanswerable stratum the
family that sits higher and more saturated at baseline (mistral) shows placebo
recruitment while the family with headroom (qwen) shows suppression (M2
consistency). The realized random displacement onto the caution axis (M3) does
not differ by question type within a family.

## Falsifier

The prediction's mechanism reading is falsified if, within each family, the
answerable-vs-unanswerable difference in pre-generation doubt/caution projection
(M1) is statistically indistinguishable (bootstrap 95% CI on the standardized
mean difference spans 0 in every family and both directions). A credible
behavioral falsifier, to the limited extent existing data can speak: if the
within-`kuq`-subcategory QH placebo deltas are themselves statistically
indistinguishable across subcategories (no subtype concentrates the effect),
that is consistent with question type being inert for the placebo response and
strengthens the prediction; if instead one subtype carries the entire qwen
suppression while others are flat, question type (at the subtype resolution) DOES
modulate the placebo response and the "inert" reading is falsified for qwen.
Because the answerable stratum is unpowered (qwen n = 17) or absent
(mistral/QL/llama-placebo) on existing artifacts, NO existing-data result can
confirm or falsify the answerable-vs-unanswerable BEHAVIORAL contrast; that
verdict is reserved for RR3 and this amendment must not claim it either way.

## Gates

Integrity and coverage gates only. This experiment has no promotion gate: its
outputs are measurements and a mechanistic reading, and every prediction outcome
is a reportable result.

- **BG0 (provenance and re-slice fidelity).** Every source runlog, anchor
  artifact, direction JSON, and build_manifest is staged into gitignored
  `analysis/staged_inputs/` with sha256 and row/vector counts recorded in a
  committed ID-manifest (no text). The QH unanswerable re-slice must reproduce
  the calibration-certified confab delta bit-for-bit (baseline 139/1,286,
  random 73/1,286, delta -5.13) before any stratified number is trusted; the
  MC unanswerable number must equal RR2's committed 368/1,312 and 465/1,312.
- **BG1 (mechanism frame port).** The ported two-stage standardized-projection
  chain must reproduce the frozen doubt gate's per-row fire/no-fire decision on
  the qwen anchors to within a pre-registered mismatch tolerance (<= 1% of rows)
  against the `gated.jsonl` fired set, and the mistral/llama frames must
  reproduce their respective committed gate statistics from `fit_reuse` /
  atlas manifests. A frame that cannot reproduce firing is fixed or the family's
  mechanism leg is dropped and reported straight; no question-type contrast runs
  on an unvalidated frame.
- **BG2 (coverage and honesty).** Every cell reports paired-n and Wilson CIs;
  the paired-population rule is respected in every delta (unpaired rows reported
  separately, never inside a delta); the answerable behavioral legs are reported
  at true power with the coverage gaps named (qwen n = 17, mistral/QL/llama
  n = 0) and no answerable-vs-unanswerable behavioral verdict is asserted from
  existing data; M2 is labeled underpowered (n = 2 families); M3 is dropped for
  llama with the reason stated; QL wide is reported as voided (narrow-only) with
  the calibration void reason cited.

## Predictions scoreboard

Calls registered 2026-07-14, pre-run, before the analysis harness was built;
also checkpointed in the session note
(docs/sessions/20260708T164625Z-paper-5-j-space-hardening.md) before entry
here. No edits after results.

| Predictor | M1: answerable vs unanswerable separate on the pre-generation doubt/caution axis in ALL THREE families? | kuq-subtype breakdown: does the placebo effect concentrate in particular unanswerable subtypes? | M3: does realized caution-axis displacement differ by question type within family? |
|-----------|------|------|------|
| orchestrator | YES, all three | NO, spreads evenly (question type inert at subtype resolution) | YES, differs (fixed-magnitude snap means rows starting higher on the axis receive smaller displacement; coupled to M1) |
| user | YES, all three | YES, concentrated or at least uneven | YES, differs |

The differentiating slot is the subtype breakdown: an even spread supports the
question-type-inert reading (orchestrator); concentration in specific
unanswerable subtypes means question type modulates the placebo response at
subtype resolution (user). M1 and M3 calls agree across predictors.

## Outcome

Resolved 2026-07-14. All gates passed; every committed number was independently
recomputed to full float precision by an adversarial red-team review before this
verdict was written (qwen safetensors and the mistral 251MB anchor JSON reloaded
from scratch; gate fire-set reproduced 1303/1303 with zero symmetric difference;
circularity checked by restricting mistral M1 to the 1,694 held-out rows, where
the separation is larger, not smaller: z_d SMD -6.05 vs -5.80 full-population).

**One-sentence summary (= manifest verdict).** Question type does not explain
the cross-family placebo sign difference (the sign is a family property measured
entirely on the unanswerable stratum, and the registered mechanism falsifier is
untriggered: no M1 SMD CI spans 0 in any family on either axis), but the
subtype-inert reading is falsified for qwen: the future-unknown kuq subtype
carries the entire qwen suppression (-24.7 pts vs -2.8 or smaller elsewhere), is
also mistral's largest recruitment delta (+11.8), and is the pre-generation
projection outlier in both families.

**Gates.** BG0 PASS (QH re-slice reproduced 139/1,286 -> 73/1,286, delta -5.13
bit-for-bit; MC reproduced 368/1,312 -> 465/1,312, delta +7.39). BG1 PASS after
one honest failure cycle: the first real-data run failed at the registered hard
stop because both checks scored populations the pipelines never gate-evaluated
(mistral: all 3,037 anchors instead of the 1,694-row held-out roster; llama: 222
unconditionally-dosed known rows counted as missed fires). Both were adjudicated
check-scope defects, frame math untouched; frame_port.py was corrected to the
gate-evaluated populations and repinned (repins entry in the manifest), and the
rerun passed honestly: qwen 0/1,692 mismatches, mistral 0/1,694, llama 1/581 =
0.0017 at hs20 (inside the registered 1% tolerance) and 0/581 at hs22/hs23 with
the known-presence invariant true at all layers. Provenance note: the mistral
and llama row-level fire-set reproductions are recorded here and in the
notebook and are reproducible via the opt-in checks in the pinned
frame_port.py, but the committed report JSON carries only the qwen fire-set and
the mistral fit-reuse crosscheck; BG1 as registered required exactly that, so
the gate is met at its registered bar. BG2 PASS (paired-n and Wilson CIs
throughout; answerable legs at true power with gaps named; M2 labeled
underpowered; M3 dropped for llama with reason; QL wide voided, narrow-only).

**Behavioral leg.** Unanswerable stratum: qwen QH 10.8% -> 5.7% (delta -5.13
pts, n = 1,286 paired); mistral MC 28.0% -> 35.4% (delta +7.39 pts, n = 1,312
paired). Answerable stratum: qwen 0/17 -> 0/17 (unpowered; and only 1 of the 17
carries a wide grade in both arms, so the informative paired denominator is
effectively 1); mistral/QL/llama n = 0. As registered, NO
answerable-vs-unanswerable behavioral verdict is asserted from existing data;
that contrast was deferred to RR3 and is not claimed here. Within-kuq subtype
breakdown (delta pts, random minus baseline): qwen future-unknown -24.7
(n = 190, baseline 0.332) with every other subtype between -2.8 and +0.5;
mistral future-unknown +11.8 (n = 153, baseline 0.536, the highest-hedging
subtype) with the other five between +3.8 and +9.2. The same subtype is the
extreme mover in both families, in opposite directions, and baseline hedging
orders the six subtypes identically in both families. QL narrow dose-response:
baseline 40/887 (4.5%); no layer/dose cell rises above baseline (hs20 span
0.0-2.0%, hs23 3.2-5.6% falling with dose to 0 at 20 sigma-c, hs26 2.4-5.6%,
hs30 1.6-4.8%), consistent with narrow-band suppression and no recruitment
anywhere in the qwen ladder.

**M1 (pre-generation projection contrast), adjudicated axis-by-axis.** The
committed report's `prediction_consistent` booleans are computed on the raw fit
axis and are NOT transcribed here, for a reason the red-team review located in
the locked instruments: no prose doc pins the axis orientation, and the frozen
gate code this amendment ports (rr2 direction_fit.py, validated by BG1) defines
u_d as unit(mean known minus mean unknown), so +u_d points to the KNOWN pole and
the gate's doubt score is -z_d (score = -z_d, fire = score >= tau; the manifest
field auc_neg_z_d_on_fit names the axis). Under that pre-registered operational
convention:

- Doubt axis: CONFIRMED in all three families. Unanswerable sits higher on
  -z_d everywhere; raw-axis SMDs (answerable minus unanswerable on raw z_d,
  equivalently the negated doubt contrast): qwen -3.762 [-3.956, -3.590],
  mistral -5.796 [-5.997, -5.605], llama -6.43/-6.33/-6.3 at hs20/22/23, all
  Mann-Whitney p <= 1e-176. Caveat stated plainly: u_d IS the known-vs-unknown
  contrast direction, so this largely re-expresses the near-saturated
  answerability gate rather than establishing an independent finding.
- Caution axis: NOT INTERPRETABLE as a question-type ordering. Answerable rows
  project higher on +c_hat in all families (raw SMDs qwen -3.004, mistral
  -1.577, llama -0.65 [-0.73, -0.57]), but c_hat is fit only on the
  confab-vs-unknown-refused contrast (both unanswerable) and then
  orthogonalized against u_d and u_p, so where answerable rows land on it is
  emergent geometry with no designed caution semantics. Means are reported; no
  directional reading is claimed.

**Registered falsifier: UNTRIGGERED.** The falsifier asks whether the M1 SMD CI
spans 0 in every family and both directions; it is sign-agnostic, so the axis
labeling question cannot touch it. No CI spans 0 (smallest magnitude: llama z_c
-0.65 [-0.73, -0.57]). The behavioral falsifier arm, however, FIRES for qwen:
one subtype (future-unknown) carries the entire suppression while others are
flat, so question type at subtype resolution DOES modulate the placebo response
and the inert reading is falsified for qwen, exactly as the registered text
provided.

**M2 (cross-family consistency, descriptive, n = 2, non-gating).** Directionally
consistent with the prediction: mistral's unanswerable stratum sits higher at
baseline (mean z_c -0.22 vs qwen -0.43; wide baseline hedge rate 0.280 vs 0.104)
and mistral recruits (+7.39) while qwen suppresses (-5.13). Mandatory caveat
carried from rr3-corrected-placebo-replication (resolved FALSIFIED, PR #290):
the +7.39 mistral figure is a SINGLE-SEED draw, and RR3 measured fresh
random-seed lifts at matched magnitude spanning -7.4 to +21.8 points across
three seeds, so the family-sign premise itself has wide per-seed variance and
this consistency read must not be treated as established sign structure. M1 and
M3 are unaffected (they concern anchors, not placebo seeds).

**M3 (realized displacement split).** Qwen: null as the registered prediction
stated (SMD +0.012 [-0.098, +0.124], mean displacement 0.21220 vs 0.21221 at
dose 12.61). Mistral: statistically non-null (SMD -0.851 [-0.944, -0.761]) but
mechanistically negligible: the mean displacement difference is 1.2e-4 against
a displacement magnitude of 0.0426 (0.3%), arising from mild non-orthogonality
of this seed's r_hat to the answerability axis with tiny per-group variances
(~2e-8, finite and non-degenerate per the red-team recomputation). This is the
pre-flagged "a non-null here would itself be a finding" case and is reported as
negligible-in-magnitude, not as question type modulating the write. M3 is flat
across kuq subtypes in both families (qwen subtype-median span 0.0014, mistral
0.00014).

**Subtype-resolved mechanism readout (pre-stated in the notebook before the
mechanism leg ran; descriptive, hypothesis-generating).** Future-unknown is
qwen's doubt-axis outlier (median z_d -0.985 vs -0.21..-0.51 for the other
five), matching the behavioral -24.7 concentration; it is mistral's BOTH-axes
outlier (median z_c +0.844 vs next-highest +0.158; median z_d -1.008 vs
-0.34..-0.57); and it is llama's second-highest caution subtype (z_c +0.326,
behind false-assumption +0.589). Displacement is flat across subtypes, so the
behavioral concentration is not explained by differential dose realization; the
concentration correlates with where the subtype sits pre-generation.

**Predictions scoreboard, adjudicated.**

- M1 slot (both predictors YES, all three): BOTH CORRECT on the doubt axis
  under the operational convention; the caution axis is not interpretable as
  worded, so the slot is scored on doubt.
- Subtype slot (the differentiating slot): USER CORRECT (concentrated or at
  least uneven), ORCHESTRATOR WRONG (even spread). The concentration is
  extreme, one subtype carrying effectively the entire qwen effect, and it is
  echoed mechanistically in both families.
- M3 slot (both predictors YES, differs): BOTH WRONG for qwen (null); for
  mistral the difference is statistically real but negligible in magnitude, so
  at most a technicality. Note the scoreboard calls here contradicted the
  registered Prediction prose ("does not differ"), which the qwen result
  vindicates.

**Design note (required by Analysis outputs).** Question type does not modulate
the placebo response at the answerable-vs-unanswerable level on existing data
(the sign difference lives entirely on the unanswerable stratum, and the
answerable behavioral contrast remains unmeasured, deferred to RR3); it DOES
modulate it within the unanswerable stratum at kuq-subtype resolution (qwen
future-unknown carries the suppression, and the same subtype is mistral's
largest recruitment); M1 confirms answerable/unanswerable separation on the
operational doubt axis in all three families (with the near-tautology caveat);
and the M2 family-sign consistency read is directionally supportive but stands
on a single-seed premise that RR3 showed has -7.4..+21.8 per-seed variance, so
it is reported as unestablished.
