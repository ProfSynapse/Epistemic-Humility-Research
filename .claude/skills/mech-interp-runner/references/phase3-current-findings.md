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

## Next Research Direction

Prioritize the calibrated-expression question over refusal-axis steering:

1. Explore multi-layer or constrained subspace controls; simple single-axis and
   simple two-hook KTO steering are active but behaviorally unsafe.
2. Scan layer windows for directions that separate damaged behavior from paired
   desired behavior without collapsing into a generic refusal axis.
3. Gate candidates with generated-answer replay, not only logit slices.
4. Prefer directions that preserve known correctness while reducing both
   over-refusal and hallucinated unknown answers.
