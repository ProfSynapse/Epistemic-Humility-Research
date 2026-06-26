# Phase 3 Current Findings Reference

Load this only when interpreting or reporting current Phase 3 mechanistic
interpretability findings. For full provenance, inspect the referenced session
note and run artifacts.

## Source Of Truth

- Active session note:
  `docs/sessions/0011 - phase3-behavior-conditioned-sae-features.md`
- Sycophancy/helpfulness side route:
  `docs/sessions/0012 - sycophancy-helpfulness-probe.md`
- Key output roots:
  - `experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/`
  - `experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/`

## Current Interpretation

The strongest current evidence is not a clean epistemic-humility feature.
It points to distributed behavior-control subspaces. Some directions steer
refusal or answer-start probability, but generated-answer replay shows that
loosening refusal can produce wrong answers.

This is now named and connected to the literature. The recurring
`separability != coherence != steerability` pattern is the
**generation-discrimination gap** (`term:generation-discrimination-gap`; coined by
Saunders et al., operationalized by ITI `paper:2306.03341`). The Phase 3
model-variation sweep shows the gap is **regimen-robust**: across five regimens
(SFT-DPO-GRPO, SFT-KTO-GRPO, GRPO v2, GRPO-DPO, KTO) the final-adapter delta is
highly separable (pairwise AUC `~0.98-0.99`, final-stage-determined) yet does not
steer generated behavior safely (best four-cell macro recall `0.695`). That is
direct evidence on `gap:4-probe-transfer`: humility fine-tuning moves the
representation, but the moved signal reads like the *performance* of humility, not
a controllable calibration surface. Caution: probes may read knowledge-recall, not
calibration (`paper:2510.09033`), so high separability must not be over-read.

Working target: find coherent layer windows where the model expresses calibrated
knowledge state:

- answer known items correctly,
- refuse unknown items,
- avoid known-item over-refusal,
- avoid unknown-item hallucination,
- preserve or improve stated confidence when available.

## Main Findings

### SAE Features

Behavior-conditioned SAE features correlate with refusal, low confidence, and
over-refusal, but they are not clean monosemantic knobs.

- DPO seed1 strongest unknown-refusal / low-confidence feature: `f49`.
- KTO seed1 strongest unknown-refusal features: `f27`, `f12`.
- KTO `f16` is a known-overrefusal / damage-axis lead.
- Geometry shows behavior features are mostly near-orthogonal to each other and
  weakly aligned with broad known/unknown directions.

Interpret SAE outputs as screening evidence only.

### Layerwise Behavior Axes

Broad unknown-refused vs known-correct directions separate strongly across many
layers. Subtler within-unknown refusal and confidence contrasts peak later but
are not single-layer-local.

Current banded read:

- KTO within-unknown axes are strongest around layers 24-25 under subtraction.
- SFT known-overrefusal is strongest around layer 24 and remains strong through
  layers 24-26.
- Wrong-layer and nearby-layer controls are often competitive, supporting a
  distributed layer-window interpretation.

The calibrated-expression scan separates behavior cells more directly than the
older refusal-axis scan. Best current cell-level windows:

- KTO `unknown_answered_wrong` vs `unknown_refused`: delta layer 25
  (`d ~= 1.424`, AUC `~0.838`), h_lora/base layer 24 (`d ~= 1.42`).
- DPO `unknown_answered_wrong` vs `unknown_refused`: delta layer 28
  (`d ~= 1.262`, AUC `~0.812`).
- KTO `known_refused` vs `known_correct_answered`: h_lora/base layer 27
  (`d ~= 2.8`), delta layer 22 (`d ~= 2.5`).

These are better aligned to the research target than broad unknown-vs-known
axes, but broad axes remain much stronger and should be treated as confounds or
controls.

KTO h_lora layers 24-27 currently look like the best coherent calibrated
expression band. In that band:

- unknown-wrong-vs-refused axes are stable across adjacent layers
  (`cos ~= 0.86-0.93`);
- known-overrefusal axes are stable across adjacent layers (`cos ~= 0.90-0.96`);
- same-layer unknown-wrong damage and known-overrefusal damage axes are
  consistently anti-aligned (`cos ~= -0.49` to `-0.53`).

Interpretation: this is probably a multi-axis control surface, not a single
humility knob. Any live test should evaluate both failure modes together.

The reusable calibrated-expression plane run projected 4,932 KTO h_lora
layer-window rows across layers 24-27. It reproduces the same pattern in cell
space: known-correct answered and unknown-refused occupy opposite regions,
known-refused sits close to unknown-refused, and unknown-answered-wrong is
intermediate and more answer-side than refused unknowns. Treat this as
policy-state alignment evidence, not a one-dimensional refusal or humility
axis.

Cross-regimen geometry currently looks asymmetric. SFT and KTO known-overrefusal
axes align strongly at matched layers (`cos ~= 0.88-0.91`), suggesting a shared
over-refusal direction survives the KTO adapter. DPO has no known-refused rows
in this panel, and its unknown-wrong-vs-refused delta axis is nearly orthogonal
to the KTO h_lora unknown-wrong-vs-refused window (`abs(cos) < 0.04`). Compare
regimens by matched behavior cells and available failure modes, not by assuming
one shared refusal/humility axis.

The KTO calibrated-expression logit sweep confirms that these axes are active
but blunt. Known-overrefusal-axis subtraction strongly reduces refusal-openers
on known-refused rows, but it also reduces refusal-openers on unknown-refused
rows, which is undesirable. The unknown-wrong-vs-refused axis has the opposite
sign: subtraction raises refusal-openers, including on unknown-answered-wrong
rows. Wrong-layer controls remain close to source-layer effects, so treat this
as layer-window steering evidence, not a localized mechanism.

Composite KTO-plane tests were informative but not a steering win. An equal
known-overrefusal/unknown-wrong repair blend mostly cancels the unknown-wrong
repair. A 1:1.25 blend at L24 gives the best current logit-cell tradeoff:
known-refused refusal-openers decrease while unknown-wrong refusal-openers
increase, with known-correct roughly preserved. The effect is weak and
wrong-layer controls are comparable. Across L24-L27, L24 is cleanest, L25/L26
are weaker, and L27 moves the unknown cells the wrong way. Treat this as a
narrow L24-L26 behavior-control window, not a clean knob.

A reusable sign-score pass now ranks this tradeoff explicitly. Across the
current SelfAware KTO single-axis and composite summaries, the best source arm
is still the L24 1:1.25 composite source addition (`score ~= 0.0849`, all four
sign goals passed), but the sign-matched wrong-layer control scores higher
(`score ~= 0.1034`). This confirms the L24 composite as the best logit
triage candidate while weakening any source-layer-local interpretation.

The first constrained-subspace test supports the entangled-window hypothesis
but does not yield a steering win. Orthogonalizing same-layer KTO h_lora
known-overrefusal and unknown-wrong axes against each other removes a
substantial component across L24-L26 (`~0.49-0.53` of unit-scaled vector norm).
The six-candidate logit sweep completed, but the best sign score was only
`0.0317` and passed `2/4` goals. The top L24 unknown-repair arm increased
refusal on unknown-wrong rows, but also increased refusal on known-refused and
known-correct rows, failing both known-question protections. Treat
orthogonalization as useful geometry evidence, not as a calibrated-expression
intervention.

The first gold-backed KTO behavior panel gives a cleaner target surface than
the SelfAware labels. On 256 TriviaQA/Cheng rows for SFT->KTO baseline
generation: known answer correctness was `81.25%`, known over-refusal was
`5.47%`, unknown refusal was `84.38%`, and exact truthfulness was `82.81%`.
The behavior cells were: `known_refused=7`, `known_correct_answered=104`,
`known_answered_wrong=17`, `unknown_refused=108`,
`unknown_answered_wrong=16`, and `unknown_answered_correct=4`.

Gold-backed layerwise scans found separable mistake axes, but not a tidy
control knob. Known over-refusal vs known-correct peaks late (`h_lora` L36
`d ~= 5.02`, AUC `~0.997`; L32 also strong). Unknown-wrong vs unknown-refused
peaks around the high-20s for `h_lora` (L27 `d ~= 2.57`, AUC `~0.947`) while
tiny-norm `delta` peaks appear early and should be treated cautiously.
Known-wrong vs known-correct is strongest late (`h_lora` L34 `d ~= 4.54`,
AUC `~1.0`). This reinforces the multi-axis, distributed-window reading.

The first gold-backed KTO logit diagnostic is negative for simple steering.
The known-overrefusal L36 axis can reduce refusal probability on known-refused
rows under addition, but it also lowers refusal on unknown-refused rows. The
unknown-wrong L27 axis can raise refusal on unknown-wrong rows under
subtraction, but it also raises refusal on known-correct rows. Wrong-layer
controls are competitive or stronger, especially for the unknown-wrong axis.
Answer-alias probability movement is tiny compared with refusal movement.
Interpretation: the behavior cells are separable, but current single-axis
interventions are too blunt for calibrated expression.

The first gold-backed same-layer composite grid was also negative. Six
same-layer composites used `known_refused_vs_correct - alpha *
unknown_wrong_vs_refused` at layers 27, 28, and 36 with alpha `0.25` and `0.5`.
No source-addition arm improved both damaged cells while preserving both
desired cells. L27/L28 composites increased refusal on unknown-wrong rows, but
also increased refusal on known-refused and known-correct rows. L36 composites
reduced known-refused refusal, but lowered desired unknown-refused refusal and
did not repair unknown-wrong rows.

A follow-up same-layer single-axis sign map explains the failure. At L27/L28,
known-overrefusal axes under subtraction reduce known-refused refusal, but also
lower refusal on unknown-refused and unknown-wrong rows. Unknown-wrong axes
under subtraction raise refusal on unknown-wrong rows, but also raise refusal on
known-correct rows. The opposite signs flip the damage pattern rather than
solving it. L36 unknown-wrong is weaker and still trades off unknown-refused.
Current implication: calibrated expression may require multi-layer or
constrained subspace intervention, not a single same-layer linear combination.

The first dedicated multi-layer intervention also did not solve the behavior
tradeoff. It paired known-overrefusal repair at KTO `h_lora` L36 with
unknown-wrong repair at L28, using L28 weights `-0.10`, `-0.25`, and `-0.50`
under source addition on the 28-row gold four-cell panel. Increasing the L28
repair weight raised refusal on unknown-wrong rows (`-0.007`, `+0.011`,
`+0.062`), but also increased refusal on known-correct rows (`+0.009`,
`+0.019`, `+0.041`) and still lowered refusal on unknown-refused rows
(`-0.097`, `-0.086`, `-0.081`). Answer-alias movement stayed tiny. This
supports the multi-component/distributed reading but falsifies this simple
two-hook recipe as a calibrated steering intervention.

The first gold-backed multicell readout supports a low-dimensional
control-surface hypothesis, but it is not yet a steering source. A balanced
four-cell ridge readout over KTO seed1 gold behavior cells improved from weak
rank-1 macro recall (`~0.46`) to low-rank macro recall around `0.57-0.58`.
Best current readouts include `h_lora` L21 rank 4 (`macro_recall ~= 0.582`),
`delta` L27 rank 8 (`~0.575`), `delta` L25 rank 4 (`~0.575`), and `h_base`
L22 rank 4 (`~0.569`). The panel is heavily imbalanced
(`known_refused=7`, `unknown_answered_wrong=16`, `known_correct=104`,
`unknown_refused=108`), so treat this as localization/screening evidence. The
next useful step is a larger targeted gold behavior panel that oversamples rare
damage cells before exporting readout-derived directions.

The targeted KTO gold panel confirms the sampling bottleneck and improves the
readout surface. A deterministic 448-row probe-pool slice excluded the original
256-row panel and oversampled likely known-overrefusal and unknown-wrong
candidates. Actual SFT->KTO baseline generation yielded:
`known_refused=37`, `known_correct_answered=164`, `known_answered_wrong=23`,
`unknown_refused=187`, `unknown_answered_wrong=31`, and
`unknown_answered_correct=6`. The four-cell readout used 419 labeled rows. Best
current low-rank results improved to `h_lora` L27 rank 16
(`macro_recall ~= 0.613`, rare-cell recall `known_refused ~= 0.43`,
`unknown_answered_wrong ~= 0.55`) and `delta` L34 rank 16
(`macro_recall ~= 0.595`). This strengthens the multi-dimensional
mid/late-layer control-surface hypothesis, but it remains readout/localization
evidence only. Next causal tests should use the enriched behavior-cell row-key
files and preserve paired desired cells.

The first causal follow-up on the targeted panel is negative for simple axes.
Four behavior-axis candidates tested the enriched readout regions:
`h_lora` L27 known-overrefusal, `h_lora` L27 unknown-wrong, `delta` L34
known-overrefusal, and `delta` L34 unknown-wrong. Offline separation remained
strong (`h_lora` L27 AUC `~0.985` for known-overrefusal and `~0.962` for
unknown-wrong), but live logit diagnostics again split the goals. The top
source arm was `h_lora` L27 known-overrefusal subtraction at coefficient `50`
(`sign_score ~= 0.091`, `2/4` goals): it lowered refusal-openers on
known-refused rows and preserved known-correct rows, but also lowered refusal
on unknown-wrong and unknown-refused rows. The complementary unknown-wrong
axis raised refusal on unknown-wrong rows but also raised refusal on
known-correct and known-refused rows. No candidate passed all four goals, and
answer-alias probability deltas stayed small. Do not run generated replay for
these simple axes; the next mech-interp step would need a real constrained
subspace/readout-derived intervention, otherwise pivot to training.

### Gold-Backed Answer-Start Diagnostics

Tiny changed-row KTO evidence initially looked promising, but scale and replay
changed the interpretation.

- 16-row scaled pass weakened the tiny KTO answer-alias lift.
- 64-row pass gave weak KTO support on unknown rows: source subtraction lowered
  refusal and raised answer-start probability, but random controls were close.
- Fixed 32-unknown-row coefficient sweep made KTO a better lead than DPO:
  KTO source subtraction and wrong-layer moved in opposite directions, while DPO
  source and wrong-layer tracked closely.
- Five-seed random matched-norm KTO panel strengthened KTO as a next-token
  source-specific answer-start candidate.

Do not report this as answer recovery.

### Generated-Answer Replay

KTO generated-answer replay is the behavioral gate and currently negative for
answer recovery.

On fixed 32 unknown rows:

- Baseline unknown refusal rate: `81.25%`.
- KTO subtraction unknown refusal rate: `78.125%`.
- Baseline answer-on-unknown rate: `18.75%`.
- KTO subtraction answer-on-unknown rate: `21.875%`.
- Exact correctness stayed flat at `3.125%`.
- The refusal-to-answer flip was wrong: first Miss World country changed from
  refusal to `England`, while gold answer was `Sweden`.

Interpretation: KTO source subtraction can loosen refusal and move answer-start
logits, but it has not supplied missing knowledge. This can worsen truthfulness.

On the SelfAware 64-row calibrated-expression replay, the best current L24
1:1.25 KTO composite also failed the behavioral gate:

- Baseline unknown refusal rate: `84.38%`.
- Composite source-addition unknown refusal rate: `81.25%`.
- Baseline answer-on-unknown rate: `15.62%`.
- Composite source-addition answer-on-unknown rate: `18.75%`.
- Known over-refusal stayed flat at `53.12%`.
- Refusal state changed on only three rows: one unknown wrong-answer row
  switched to refusal, but two rows worsened by switching from refusal to
  non-refusal. Additional rows changed refusal wording without changing the
  behavior classification.

Interpretation: linear blends can tune next-token refusal tradeoffs, but this
blend still loosens refusal behavior more than it repairs calibrated humility.

### Sycophancy / Helpfulness Side Route

Answer-sycophancy is now wired as an exploratory OOD eval path using the local
`datasets/sycophancy-eval/answer.jsonl` file. The first seed-1 4B panel covers
16 base questions across four prompt conditions. Neutral correctness remains
low (`31.25%` base/SFT, `37.5%` DPO/KTO), so this is still a small exploratory
slice. Wrong-hint pressure is measurable after correctness/refusal-aware
matching: base matched the wrong hint on `56.25%` of wrong-hint rows, KTO
`50.0%`, DPO `43.75%`, and SFT `37.5%`. SFT
differs mostly by refusing: `50%` neutral refusal and `37.5%` wrong-hint
refusal, versus `0%` refusal for base/DPO/KTO. Base/DPO/KTO often remain highly
confident despite wrong answers or wrong-hint following; SFT confidence is much
lower where it refuses.

Use this route to test whether helpfulness/user-pleasing pressure changes across
training regimens, but do not treat it as direct epistemic-humility evidence
until a stable behavioral contrast exists.

First hidden-state sycophancy pass is now wired and live-verified for SFT seed1
and KTO seed1 on a 32-row paired answer-sycophancy panel. The same-condition
controls are more meaningful than neutral-vs-wrong-hint prompt contrasts:

- KTO wrong-hint-followed vs wrong-hint-not-followed, 8/8 rows: best current
  deltas include L17 (`d ~= 5.98`, AUC `1.0`) and L24 (`d ~= 5.11`); late
  h_base/h_lora layers also separate strongly. Treat this as a candidate
  behavior-separation surface, not a causal sycophancy knob.
- SFT wrong-hint-followed vs wrong-hint-refused, 6/6 rows: strongest late
  h_base/h_lora/delta layers around L34-L36, with delta L36 (`d ~= 6.68`, AUC
  `1.0`). This is likely a refusal-vs-answering-under-pressure axis.
- Neutral-vs-wrong-hint contrasts are much larger but confounded by literal
  prompt text. Use them as prompt-framing diagnostics only.

The first sycophancy same-condition logit diagnostic is useful but not a clean
content-control win. KTO delta L17 is causally active on next-token starts, but
wrong-layer controls are comparable or stronger. Source subtraction at
coefficient `25` changed top-1 on `62.5%` of rows, while wrong-layer
subtraction at offset `-1` changed top-1 on `78.12%`. Row inspection shows
flips among generic answer/refusal starts such as `You`, `No`, `I`, and `The`;
the explicit wrong-hint-answer probability stayed effectively zero. SFT delta
L36 is weaker: source subtraction changed one row (`3.12%`) from an `I`
refusal-start toward `The`, while source addition changed none. Interpretation:
offline behavior labels are separable, but this is not yet a sycophancy-content
knob. Treat it as pressure/refusal-start control evidence and expand the panel
or target rows where baseline actually follows the wrong hint before generated
replay.

The targeted KTO wrong-hint generation replay is negative. On eight KTO rows
where the original wrong-hint answer followed the user's bad hint, no-vector
baseline matched the wrong hint on `5/8` rows. KTO L17 source subtraction
matched the wrong hint on `7/8` rows at both coefficients `10` and `25`, while
repairing only the Concorde row to Bristol. Manual review shows several outputs
becoming more explicitly agreeable (`Yes, you are correct...`) while preserving
the wrong answer. This fails the generated-answer gate and reinforces the
current rule: separable behavior axes are not safe steering claims without row
level replay.

### Current Clean Model-Variation Known-Overrefusal Slice

The first current JSON-output model-variation Phase 3 slice has verified
hidden-state extractions for clean SFT, clean SFT->GRPO v2, and clean
SFT->GRPO v2->DPO on the 1,233-row SelfAware panel. Behavior-axis scans found
usable known-overrefusal delta separators, but broad unknown-refusal-vs-known
separators are much stronger and easier; unknown-wrong rows remain too rare in
this slice for a stable under-refusal axis.

Normalized known-overrefusal logit diagnostics showed no clean single
"humility knob." SFT subtraction was comparatively safe for unknown-refusal
preservation but weak and not source-layer-specific. GRPO v2 had the clearest
answer-alias first-token nudge, but also slightly suppressed unknown-refusal
probability in the logit slice. GRPO-DPO at coefficient `10` reduced known
refusal while preserving or raising unknown-refusal probability, but its
answer-alias movement was weak.

Generated replay is more encouraging but still tiny. On a fixed 24-row panel,
coefficient-`10` source subtraction preserved all `8/8` unknown refusals for
both tested candidates. GRPO v2 L25 repaired `3` known rows from refusal to
correct answer, improving known correctness/retention from `25.0%` to
`43.75%` and lowering known over-refusal from `75.0%` to `56.25%`. GRPO-DPO L12
repaired `1` known row, improving known correctness/retention from `37.5%` to
`43.75%`. Addition moved in the opposite/worse direction. Treat GRPO v2 L25
subtraction as the leading behavioral steering candidate, not yet a localized
mechanism claim.

Caveats: the replay panel is small; baseline behavior under the runner prompt
differs from prior eval labels; answer-alias logit evidence requires explicit
alias loading from current row overlays; and same-arm nearby/wrong-layer
generation controls are still needed before source-layer claims.

Scaling the GRPO v2 L25 replay to a deterministic 96-row panel strengthened
the signal. The panel used 32 current `known_refused`, 32 current
`known_correct_answered`, and 32 current `unknown_refused` rows. Coefficient
`10` source subtraction repaired `9` known refusals to truthful answers,
introduced `1` new known wrong answer, worsened `0` previously truthful known
rows, and introduced `0` new unknown non-refusals relative to baseline. Known
answer correctness rose from `25.0%` to `39.06%`; known over-refusal fell from
`75.0%` to `59.38%`; unknown refusal stayed at `96.88%`.

On the same 96-row panel, coefficient sensitivity produced:

- `5`: `6` truthful known repairs, `0` new known wrong answers, `1` new unknown
  non-refusal row swap, known correctness `34.38%`.
- `10`: `9` truthful known repairs, `1` new known wrong answer, `0` new
  unknown non-refusals, known correctness `39.06%`.
- `15`: `11` truthful known repairs, `1` new known wrong answer, `0` new
  unknown non-refusals, known correctness `42.19%`.

Interpretation: coefficient `15` is currently the best behavioral tradeoff in
this fixed panel. This remains Tier 2 exploratory steering evidence. The next
mechanism gate is not another same-axis success metric; it is a source-specific
control, such as nearby-layer generated replay or an equivalent shifted-vector
generation control, because earlier logit controls showed wrong-layer effects
can be nontrivial.

The source-specific generated replay gate is partially positive but not a tidy
single-layer mechanism. Applying the same GRPO v2 L25 vector at layers `23-27`
on the same 96-row panel with coefficient `15` produced the following truthful
known repairs while preserving all `32/32` unknown refusals in every arm:
`L23=8`, `L24=10`, `L25=11`, `L26=9`, `L27=7`. Each layer introduced `1` new
known wrong answer and worsened `0` previously truthful known rows. Baseline
answers were identical across all five jobs, so the comparison is not explained
by baseline generation drift. Interpretation: L25 is the best point in this
local window, but adjacent L24 is close enough that the current evidence points
to a late-layer repair region or subspace, not a sharply localized feature.

Native same-layer directions sharpen that reading. Exporting independent GRPO
v2 known-overrefusal vectors at layers `23-27`, all rescaled to the same norm
as the original L25 vector, produced coherent adjacent geometry
(`cos L24-L25 ~= 0.85`, `L25-L26 ~= 0.85`, `L26-L27 ~= 0.92`) and stronger
behavior at L26 than the shifted L25-vector control. On the same 96-row panel,
coefficient-`15` native source subtraction repaired:
`L23=8`, `L24=9`, `L25=11`, `L26=12`, `L27=10` truthful known refusals, with
`0/32` unknown non-refusal leaks at every layer and no worsened previously
truthful known rows. Native L26 is now the best single-layer behavioral
candidate in this window: `12` truthful repairs, `1` new known wrong answer,
known correctness `43.75%`, and known over-refusal `54.69%`. Baselines were
identical across native and shifted sweeps. Interpretation: the effect is a
coherent late-layer direction band, not an L25-only artifact. Next tests should
either sweep L26 coefficients or test a constrained/multi-layer blend centered
on L25-L27.

The native L26 coefficient frontier keeps coefficient `15` as the current best
single-layer operating point. On the same 96-row panel, L26 source subtraction
yielded: coeff `5` = `7` truthful repairs / `0` new known wrong; coeff `10` =
`9` / `1`; coeff `15` = `12` / `1`; coeff `20` = `11` / `2`; coeff `25` =
`11` / `2`. All five settings preserved `32/32` unknown refusals and had no
unknown non-refusal leaks. Interpretation: more coefficient is not better
beyond `15`; it begins trading repair quality for extra wrong known answers.
Use L26 coeff `15` as the single-layer baseline for any multi-layer comparison.

The first normalized multi-layer band comparison did not beat L26 alone. Four
L25-L27 blends used negative component weights under activation addition, with
absolute weights summing to `1.0` so total intervention strength matched the
single-layer baseline. The best blends (`L25/L26 half`, `L26/L27 half`, and
`L25/L26/L27 centered`) repaired `11` truthful known refusals, one fewer than
native L26 coeff `15`; the equal three-layer blend repaired `10`. All preserved
`32/32` unknown refusals and introduced `1` new known wrong answer. Current
conclusion: simple distributed averaging smooths the effect but does not
improve it. Keep native L26 coeff `15` as the best current behavioral steering
candidate on this panel.

Manual inspection of native L26 coeff-`15` key flips found the `12` truthful
known repairs spread across crude question types (`7` entity/fact, `2` person,
`1` date/time, `2` other), not one obvious micro-domain. The single new known
wrong answer is a semantic-direction error on a higher/lower parental-support
question. Report L26 as a broad repair candidate with small observed wrong-answer
risk, not as error-free steering.

A held-out 96-row panel B partially replicated native L26 coeff-`15`, but less
cleanly than panel A. Panel B excluded all original replay rows and used another
`32` current `known_refused`, `32` current `known_correct_answered`, and `32`
current `unknown_refused` rows. Against the replay's own no-vector baseline,
L26 source subtraction improved known answer correctness from `23/64` to
`31/64` (`+8` truthful known repairs), reduced known refusals from `41/64` to
`32/64`, introduced `1` new known wrong answer, and worsened `0` baseline
truthful known rows. Unlike panel A, it also produced `1` unknown non-refusal,
lowering unknown refusal from `32/32` to `31/32`. Current interpretation: the
L26 direction generalizes as a real over-refusal repair pressure, but it is not
yet a safe calibrated-expression intervention because unknown-leak risk appears
on the held-out panel. Manual inspection confirms the leak is substantive: an
unknown cosmology question received an extended expansion/dark-energy answer
before hedging, not merely a parser artifact.

A panel-B coefficient sweep makes the repair/leak tradeoff explicit. Against
the same replay baseline (`23/64` known-correct, `41/64` known-refused,
`32/32` unknown-refused), L26 coeff `5` repaired `3` known refusals with
`0` new known wrong answers and `0` unknown leaks. Coeff `10` repaired `7`
but introduced `1` known wrong answer and `1` unknown leak; coeff `12.5`
repaired `7` with `1` known wrong and `2` unknown leaks; coeff `15` repaired
`8` with `1` known wrong and `1` unknown leak. Current implication: lower
coefficient can be safe but too weak; stronger coefficients recover more known
answers by loosening refusal broadly enough to create unknown-answer risk.
Simple scalar tuning is therefore not enough for calibrated expression.

A same-layer constrained transform is the first stronger positive result. The
native L26 known-overrefusal vector and a broad L26
`unknown_refused_vs_known_correct_answered` protection vector overlap strongly
(`cos ~= 0.707`); orthogonalizing known repair against the protection vector
removed `~70.7%` of the original component before rescaling. On held-out panel
B, the orthogonalized repair at coeff `10` matched the native coeff-10 repair
count (`+7` truthful known repairs) while improving safety: `0` new known wrong
answers and `0` unknown leaks, versus native coeff-10's `1` known wrong and
`1` unknown leak. On panel A, the same constrained coeff `10` matched native
coeff-10: `+9` truthful known repairs, `1` known wrong answer, and `0` unknown
leaks. Current interpretation: removing the broad unknown-refusal component
meaningfully reduces held-out unknown-leak risk while preserving useful repair
pressure, but it does not eliminate known-answer semantic errors. This is the
best current constrained steering candidate, not yet a complete calibrated
expression solution.

Adding a second same-layer protection constraint for `known_answered_wrong` is
the current best generated-replay result. The rare known-wrong axis is based on
only 15 positive rows, so treat it cautiously, but it meaningfully changes the
frontier. Orthogonalizing the native L26 known-repair vector against both the
broad unknown-refusal protection axis and the L26 known-wrong-vs-known-correct
axis removed `~71.0%` of the original component before rescaling. At coeff
`10`, the double-constrained vector preserved useful repair and eliminated
observed safety failures across three fixed panels: panel A produced `+9`
truthful known repairs, `0` new known wrong answers, and `0` unknown leaks;
panel B produced `+7` truthful repairs with the same zero/zero safety profile;
panel C replicated with another `+7` truthful repairs and zero/zero safety. In
aggregate across 288 replay rows, coeff `10` yielded `+23` truthful known
repairs with no observed new known-wrong answers, no worsened baseline-truthful
known answers, and no unknown non-refusal leaks. Higher coefficients are worse:
panel B coeff `20` reached `+9` repairs but introduced `1` known wrong answer
and `2` unknown leaks. Current interpretation: constrained subspace removal is
a real improvement over scalar tuning, but the safe operating point remains
coefficient-sensitive and is not yet evidence for a single localized humility
feature.

Shifted-layer controls further weaken a source-layer-local interpretation. On
panel C, applying the same double-constrained L26 vector at layers `24-28` with
coeff `10` showed a late-layer safety band rather than L26 specificity. Layers
`26`, `27`, and `28` all produced the same clean outcome: `+7` truthful known
repairs, `0` new known wrong answers, and `0` unknown leaks. Layers `24` and
`25` still repaired known refusals, but introduced known-wrong answers (`2` at
L24, `1` at L25). Current interpretation: the constrained vector is
behaviorally useful in a late-layer region, but should be reported as a
distributed/source-window intervention rather than a localized L26 mechanism.

A larger disjoint panel D falsifies the clean safety reading from A/B/C. Panel D
used the reusable behavior-panel row-key builder to select 64 fresh rows each
from `known_refused`, `known_correct_answered`, and `unknown_refused`, excluding
all A/B/C keys. At L26 coeff `10`, the double-constrained vector still repaired
known refusals (`+5`) but introduced `1` known wrong answer and `1` unknown
non-refusal leak. Shifting the same vector to L27/L28 removed the known-wrong
error but not the unknown leak, and lowering coefficients to `5` or `7.5` across
L26/L27/L28 also failed to remove that same unknown leak while reducing repairs
to `+3` or `+4`. Current interpretation: constrained subspace removal is a real
repair pressure, but it is not robust calibrated-expression control. The
remaining failure appears row-sensitive: the same unknown item, "When does
something become impossible?", flips to a non-refusal answer under every tested
nonzero placement/coefficient.

The current GRPO v2 unknown-answering question requires a full-eval enriched
panel, not the prior extracted overlay. The already extracted 1,233-row current
SelfAware overlay had only `1` `unknown_answered_wrong` row for
`clean_sft_grpo_v2`, which is too sparse for an unknown-wrong axis. The full
3,369-row clean SFT->GRPO v2 SelfAware eval has `68`
`unknown_answered_wrong` rows. A focused extraction-ready manifest now selects a
balanced 256-row panel: `64` `unknown_answered_wrong`, `64`
`unknown_refused`, `64` `known_correct_answered`, and `64` `known_refused`.
Use this panel for the next GRPO v2 unknown-failure hidden-state extraction and
axis scan before any generated-answer replay.

Panel artifacts:

- `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_unknown_failure_selfaware_manifest.yaml`
- `experiment/phase1/probe/manifests/phase3_current_clean_grpo_v2_unknown_failure_selfaware_manifest.json`
- `experiment/phase1/probe/config/hidden_state_selfaware_manifest_clean_sft_grpo_v2_unknown_failure_panel.yaml`
- `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_unknown_failure_behavior_axis_scan.yaml`

Prompt parity matters for this panel. A generic-prompt extraction/replay did
not reproduce the source eval behavior: the no-vector replay refused most rows
that had been selected as `unknown_answered_wrong`. The corrected prompt-matched
extraction used the exact Amendment E JSON response-confidence prompt. Under
that prompt, the unknown-answering separation shifted to mid layers: delta L15
was strongest (`d ~= 2.39`, AUC `~0.985`), nearby delta L14 remained strong,
and h_lora L22 was the strongest h_lora surface (`d ~= 1.88`, AUC `~0.912`).

The prompt-matched simple-axis causal gate is mostly negative. Final-prompt
logit diagnostics under the JSON schema prompt produced near-zero
refusal-opener probability movements because the next token is the JSON object
opener, not the answer text. Generated replay on the 256-row balanced panel
was more informative: baseline replay refused `68/128` unknown rows and
answered `60/128`, so it did contain both sides. The best simple arms repaired
only one or two unknown-answering failures and introduced comparable or worse
unknown-refusal leaks:

- delta L15 addition coeff `10`: `2` unknown answer-to-refusal repairs, `3`
  unknown refusal-to-answer leaks, `+1` known truthful repair.
- delta L15 subtraction coeff `25`: `1` unknown repair, `1` unknown leak.
- h_lora L22 subtraction coeff `10` or `25`: `1` unknown repair, `1` unknown
  leak.
- h_lora L22 addition produced no unknown repairs and `3-4` unknown leaks.

Interpretation: the prompt-matched behavior cells are separable, but these
simple unknown-failure axes are not useful calibrated-expression interventions.
The next useful mech-interp move would need a constrained or multicell subspace
that explicitly preserves `unknown_refused` and known-question behavior, not
more scalar tuning of the same single axes.

A multicell readout reconciles the apparent layer shift. The simple pairwise
unknown-wrong-vs-refused contrast peaks earlier/mid (`delta` L15), but the
four-cell prompt-matched control surface is best in a later `delta` band. On
the balanced 256-row panel, the best readout was `delta` L26 full-rank
(`macro_recall ~= 0.695`), followed by nearby delta L24-L30. Per-cell recall at
L26 was balanced but imperfect: `known_refused ~= 0.75`,
`known_correct_answered ~= 0.734`, `unknown_refused ~= 0.656`, and
`unknown_answered_wrong ~= 0.641`. This supports a distributed multicell
surface rather than a single early unknown-failure knob.

The first L26 constrained unknown-repair test did not rescue the behavior. A
same-layer transform orthogonalized the L26 unknown-wrong repair source against
unknown-refusal and known-refusal protection axes, removing `~47%` of the raw
source vector before rescaling. Generated replay showed no unknown
answer-to-refusal repairs. Subtraction coeff `10` was safe but only repaired
one known refusal; subtraction coeff `25` and both addition arms introduced
two unknown-refusal leaks. Current interpretation: the L26 multicell surface is
readable but this protection-constrained unknown repair vector is not a useful
causal control.

The first cross-regimen prompt-matched rare-cell comparison does not make
GRPO-DPO look cleaner than GRPO v2. On a matched 256-row SelfAware panel, the
unknown-answering contrast remains strongest around final-adapter `delta` L15,
but GRPO-DPO is weaker than GRPO v2 (`d=2.280`, AUC `0.939`, balanced accuracy
`0.867` vs GRPO v2 `d=2.388`, AUC `0.985`, balanced accuracy `0.914`). The
known-overrefusal delta axis is also weaker after final DPO (`d=1.956`, AUC
`0.935` vs GRPO v2 `d=3.276`, AUC `0.999`). Four-cell multicell readout stays
readable but not improved: best GRPO-DPO delta readout is L24 full-rank macro
recall `0.664`, below GRPO v2 delta L26 full-rank macro recall `0.695`.
Current interpretation: DPO stacked after GRPO looks like a weaker/broader
version of the same surface, not a qualitatively better control surface.

Clean SFT->KTO behaves differently from GRPO-DPO on the same prompt-matched
rare-cell protocol. KTO has much sharper pairwise final-adapter axes: `delta`
L11 unknown-answering `d=2.998`, AUC `0.994`; known-overrefusal `delta` L11
`d=3.468`, AUC `1.000`; and unknown-refused-vs-known-correct `delta` L11
`d=4.436`, AUC `1.000`. But the four-cell readout is weaker, not stronger:
best KTO `delta` readout is L25 full-rank macro recall `0.566`, and best
overall is `h_base` L33 rank-16 macro recall `0.625`. Current interpretation:
KTO likely creates a sharp pairwise behavior boundary, but this may not be a
coherent calibrated-expression surface. Generated replay is required before
treating KTO L11 as useful.

The GRPO-order pass closes the cross-regimen sweep with two findings. On matched
prompt-matched 256-row rare-cell panels, `clean_sft_dpo_grpo` (SFT->DPO->GRPO)
and `clean_sft_kto_grpo` (SFT->KTO->GRPO) both restore the GRPO-like surface:
dpo_grpo unknown-answering `delta` L14 `d=2.391`, AUC `0.983`; known-overrefusal
`delta` L13 `d=3.205`, AUC `1.000`. kto_grpo unknown-answering `delta` L14
`d=2.269`, AUC `0.987`; known-overrefusal `delta` L12 AUC `1.000`. (1)
FINAL-STAGE DOMINANCE: the final training stage, not the stacking history, sets
the final-adapter delta geometry. All three GRPO-terminal stacks (GRPO v2,
dpo_grpo, kto_grpo) converge on the same sharp mid-layer L14-15 delta axis at
AUC `~0.98-0.99`; the GRPO stage overwrites KTO's distinctive ultra-sharp L11
axis (kto_grpo looks like GRPO, not standalone KTO), while the lone DPO-terminal
stack (GRPO-DPO) is the blurred outlier (AUC `0.939`). (2) SEPARABILITY !=
COHERENCE confirmed across the sweep: best four-cell macro recall ranks
GRPO v2 `0.695` > GRPO-DPO `0.664` > dpo_grpo `0.648` > kto_grpo `0.641` >
KTO `0.625`. Plain single-stage GRPO v2 keeps the best multicell coherence; no
stacking order improves it, and sharp GRPO-terminal pairwise axes do not yield a
cleaner calibrated-expression surface. This independently re-confirms that
hand-built linear surfaces are exhausted for calibrated-expression control. The
clean SFT control was deferred: its h_base is the original Qwen base (fail-closed
adapterless path) plus a 4-bit-base vs 16-bit-merged quantization-parity confound
the other regimens lack.

## Reusable Gotchas

- SelfAware `known` labels do not guarantee gold answer aliases. Confirm
  `aliases`, `normalized_aliases`, or `answer_value` before answer-alias claims.
- First-token answer-start metrics are not exact multi-token correctness.
- Always stratify answer-start diagnostics by known/unknown labels.
- Use fixed row keys for replay claims.
- Use generated-answer replay before claiming behavioral improvement.
- A right-signed logit-cell composite is not enough; check generated row flips.
- Treat `h_base` in DPO/KTO extractions as SFT-merged pre-adapter activations,
  not original Qwen base activations.
- For generated behavior-cell scans, materialize rows from scored baseline
  generations and pass them as `rows_path`; do not assume extraction rows have
  behavior labels.
- Wrong-layer offsets near final layers must be bounded. A source hidden-state
  L36 plus offset `+1` maps past a 36-block decoder and fails live execution.
- On local Windows/WSL, host Python can find `vllm` while compiled extensions
  such as `vllm._C` are missing. Use the Docker vLLM path before chasing host
  package state.
- For answer-sycophancy, do not use raw alias/string matching as capitulation.
  A correct answer that says "not <wrong hint>" can mention the wrong answer
  without following it.
- For Docker hidden-state extraction, mounted repo ownership can make `git`
  reject the repository as unsafe and leave commit provenance null. The helper
  should pass `safe.directory`; do not weaken the manifest finalization gate.
- Do not equate the current hidden-state extraction overlay with the full eval
  corpus. If a rare behavior cell is sparse in the overlay, scan full scored
  eval rows and build a focused SelfAware manifest before concluding the model
  lacks enough cases for an axis.
- Under JSON/schema prompts, final-prompt-token logit diagnostics can probe the
  JSON scaffold instead of the answer/refusal content. Do not interpret
  refusal-opener or answer-alias probability slices from that position as
  behavioral evidence unless an answer-field prefix/position diagnostic exists.

## Next Research Direction

**Step A (chosen, ITI-grounded).** The regimen sweep closed the single-residual-axis
question: that path is exhausted (`separability != steerability`, regimen-robust).
ITI (`paper:2306.03341`) shows the generation-discrimination gap closes by changing
*where* the direction is read/applied, not by a sharper estimator — mass-mean (which
we already use) was ITI's best direction; their gains came from intervening on a
**sparse set of attention heads, token-by-token during generation, at intermediate
strength**. Our `hidden_state_probe.py` currently extracts residual-stream
final-prompt-token vectors only. Step A is therefore: (a) extend extraction to
per-attention-head activations (and generated-token positions), (b) localize the
heads where the cell-probe is most accurate, (c) apply the mass-mean direction
during generation at swept alpha, (d) gate with generated-answer replay. Avoid more
scalar tuning of one residual axis — the literature predicts it will not close the gap.

**Step A.1-A.3 DONE (2026-06-26, GRPO v2).** Per-head extraction is built and run.
Added an additive `attention_head` extraction granularity to `hidden_state_probe.py`
that hooks each block's `self_attn.o_proj` INPUT (concatenated per-head context
vectors, width `num_attention_heads * head_dim`). GRPO v2 prompt-matched run:
manifest `ok/verified`, 32 heads x head_dim 128 = width 4096 across 36 blocks,
256 rows. New offline `phase3_head_localization_scan.py` (config
`phase3_current_clean_grpo_v2_unknown_failure_prompt_matched_head_localization_scan.yaml`)
splits each block vector into its per-head slices and ranks (block, head) axes.
Result (delta role): the refuse-vs-answer IDENTITY axis is richly head-localized
(223/1152 heads >= 0.85 AUC, best L34H17/L32H14 ~0.98) and GRPO pushes it to LATE
heads (L32-35); the FAILURE-discrimination axis we must steer
(`unknown_answered_wrong vs unknown_refused`) is the sparsest and weakest (20/1152
heads >= 0.85, best L21H17 AUC 0.910). Single-head best AUC sits 0.02-0.08 BELOW the
full-block AUC — per-head's value is sparse-intervention localization (ITI), not a
sharper probe. Step A.4 targets (failure axis, delta): L21H17, L35H0, L23H1, L7H30,
L10H11, L22H12. Step A.4 (during-generation intervention + behavior gate) still needs
the generated-token extraction/intervention path, which is not yet built.

**Step A.4 INPUT DONE (2026-06-26, GPU-free).** `phase3_head_steering_directions.py`
(config `..._head_steering_directions.yaml`) emits the per-head ITI triple the
generation hook consumes: `theta` (unit mass-mean direction
`mean(positive)-mean(negative)`), `sigma` (std of the arm's projections onto theta;
ITI scale `h' = h + alpha*sigma*theta`), and provenance. Directions come from the
`h_lora` (adapter-active) arm — the hooked forward pass — not delta. Targets =
union of top-6 `h_lora` + top-6 `delta` failure-axis heads (11 sparse heads). GRPO
v2 artifact: 11 unit directions, 64/64 rows, sigma 0.18-3.0. Sign: positive =
`unknown_answered_wrong` projects higher than `unknown_refused`, so steering toward
SAFE refusal is `alpha<0` (the harness sweeps both signs). Remaining: the GPU
generation-intervention harness.

GQA GOTCHA confirmed live: Qwen3-4B `hidden_size=2560` but o_proj input width is
`num_attention_heads * head_dim = 32 * 128 = 4096`; `2560 // 32 = 80 != 128`. Always
read `head_dim` from `config.head_dim`, never `hidden_size // num_heads`.

Then prioritize the calibrated-expression question over refusal-axis steering:

1. Explore multi-layer or constrained subspace controls; simple single-axis and
   simple two-hook KTO steering are active but behaviorally unsafe.
2. Build a larger targeted gold behavior panel for rare cells before relying on
   readout-derived directions.
3. Scan layer windows for directions that separate damaged behavior from paired
   desired behavior without collapsing into a generic refusal axis.
4. Gate candidates with generated-answer replay, not only logit slices.
5. Prefer directions that preserve known correctness while reducing both
   over-refusal and hallucinated unknown answers.
