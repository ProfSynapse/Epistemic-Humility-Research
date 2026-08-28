# Weights-Level Consultation: Can Training or Architecture Replace the Runtime Thermostat?

_Status: literature scan + design memo, drafted 2026-08-28. Task: task-7eb629.
Scoping input for the successor actuation study (working label "internalized
controller"; numbering TBD against the Paper 6 margin/geometry routing). This
is a navigation document, not an evidence document: every internal claim below
cites its governed doc, and no number here is citable without opening that
doc (CLAUDE.md rule 6)._

---

## 1. The question

Paper 5's positive result is a runtime thermostat: an external probe reads the
pre-generation known-unknown (KU) state, and where it fires, a dosed
hidden-state write converts confabulations into the model's own well-formed
refusals (`papers/paper-5-actuation/manuscript.md` §4.5-4.6). Every route that
asked the policy to consult its own readout failed (§4.1-4.4). The PI's
question for the next study: **is there a training method or architecture that
installs the sensor-to-actuator wiring in the weights**, so the deployed model
consults its internal signal with no runtime harness — for example a dedicated
MoE-style module the forward pass routes through, whose effect on tokens is
conditioned on internal activations?

## 2. What the program already knows (constraints any candidate must clear)

Read each source doc before citing any of this; pointers only.

1. **The signal is there and training does not touch it.** KU readout at
   AUROC ~0.997 on the raw base, unchanged after every training arm
   (`papers/paper-3-knows-but-doesnt-say/manuscript.md`, "The internal signal
   survives training"). So the sensor half is free; the wiring is the unsolved
   half.
2. **Behavioral abstention is installable; consultation is not shown.**
   Paper 3's mechanistic reading: training arms decompose as *policy over a
   fixed epistemic signal* — SFT installs a refusal routine, preference/RL
   moves its threshold, nothing moves the signal. Whether the installed
   routine causally reads the KU axis (vs. surface correlates of the same
   rows) is exactly what the program has never confirmed, and probe-as-reward
   GRPO answered "no" for its arm: TRUE-sensor congruence 59.75% vs permuted
   76.75% (`experiments/probe-as-reward/AMENDMENT.md` §5, NULL).
3. **The stated-confidence channel is a bottleneck, not a knowledge failure.**
   A single scalar trained by next-token prediction collapses onto the
   lowest-entropy correlate whatever the target (Paper 3 §8). Any candidate
   that routes the signal through an emitted token inherits this.
4. **Writes work only at the right operating point.** Site and dose are
   family-specific; mid-band writes self-sort by commitment margin; the gate's
   role is dose-dependent (Paper 5 §6.2-6.3). A weights-level mechanism does
   not escape this geometry — it has to implement it.
5. **DPO is already a steering write in disguise.** D-Steer
   (`library/notes/2512.11838--d-steer-preference-alignment-techniques-learn-behave.md`)
   argues the DPO update is a low-rank, near-static activation shift: adding
   the extracted vector to the base reproduces the aligned behavior. Read
   against constraint 2, this predicts that naive preference-distillation of
   the thermostat installs an *unconditional* push (a permanent dose), not a
   gated one — the exact failure the gate exists to prevent at overdrive.
6. **The crux test is causal, not behavioral.** Per Paper 5 §2.2, use of the
   readout means alignment + specificity + selectivity. For a weights-level
   candidate the decisive instrument is an *intervention-based congruence
   test*: after installation, ablate/flip/clamp the KU direction in the
   student's own hidden state and ask whether the installed refusal follows
   the intervened signal. If behavior does not move with the internal signal,
   the candidate has installed a surface policy, however good its ROC looks.
   (This is the test AI could not pass and AH formalized on the compliance
   side.)

## 3. Candidate space

_Filled from the external literature scan (Section 4) and ranked in Section 5._

## 4. Literature scan

_(three sweeps: architectures with modules routing on internal activations;
training objectives that force causal dependence on internal state;
distillation of runtime control into weights). Citations verified against
abstract pages by the scanning agents; entries marked "verify" had bylines
that could not be confirmed from the proxy-reachable snippets and need a
direct arXiv check before entering any manuscript._

### 4A. Architectures: modules that route on internal activations

**Crux legend:** [WEIGHTS] = genuine weights-level consultation of the
model's own internal state; [RUNTIME] = inference-time intervention in
disguise; [BEHAVIORAL] = objective satisfiable without consultation (the
probe-as-reward failure mode).

**Headline of the sweep: no published system yet (i) reads a validated
epistemic axis from the model's own hidden state and (ii) routes generation
through it at the weights level. The pieces exist separately; the
combination is open territory.**

#### Gated-adapter / hypernetwork actuator scaffolds

- **X-LoRA** (Buehler & Buehler, arXiv:2402.07148; APL ML 2024). Frozen
  base + a set of LoRA experts; a gating network **reads the model's own
  hidden states** and mixes adapters token-wise and layer-wise. This is the
  PI's sketch, implemented and in HF PEFT (`xlora`) — except the gate is
  trained end-to-end on task loss, so nothing constrains it to read the
  epistemic subspace, and nobody has checked what it does read. [WEIGHTS].
  Obvious adaptation: freeze or initialize the gate's input projection at
  the KU probe direction; make one expert a refusal-LoRA. Fits a 3090 at 4B
  (cost: a second forward pass).
- **ReFT / LoReFT** (Wu et al., NeurIPS 2024, arXiv:2404.03592). Learned
  low-rank interventions on hidden states of a frozen model; 15-65x more
  parameter-efficient than LoRA. [WEIGHTS] in form but **unconditional** —
  it is an actuator without a sensor; the gate would have to be added.
- **SelfControl / Prefix Controller** (Cai et al., arXiv:2406.02721).
  Distills suffix-gradient self-assessment steering into a trained prefix
  module. Middle case: supervision is the model's own (text-level)
  self-judgment — the same stated channel Paper 3 found decoupled — and the
  deployed prefix is always-on, not state-contingent.
- **Generative Adapter** (arXiv:2411.05877). Hypernetwork maps the frozen
  LM's hidden states to LoRA-style weight deltas in one forward pass —
  working proof at LLM scale that *hidden states → weight deltas → behavior*
  is trainable. Never aimed at epistemic state.
- **Circuit Breakers / Representation Rerouting** (Zou et al., NeurIPS
  2024, arXiv:2406.04313). LoRA fine-tune whose loss is stated **directly in
  representation space**: states preceding harmful continuations are
  rerouted to orthogonality; benign states held by a retain loss. Works at
  7-8B with minimal capability loss. [WEIGHTS], and the one published
  precedent whose objective *cannot* be satisfied by a parallel behavioral
  boundary that ignores internal state — the structural fix for the
  probe-as-reward failure. Direct adaptation: reroute
  confabulation-trajectory states to refusal-trajectory states, conditioned
  on the KU axis.

#### MoE routing as consultation

- **Router science.** Routers are linear readouts of a distinct residual
  "control channel" orthogonal to content (arXiv:2604.17837, verify);
  refusal can be steered from a **single expert** (Expert-Aware Refusal
  Steering, Marbut et al., arXiv:2606.04160 — existence proof for an
  "abstention expert"); router entropy/expert-disagreement carries
  hallucination signal (InnerExpert, arXiv:2608.17687, verify); but expert
  usage tracks hidden-state geometry, not domain semantics
  (arXiv:2604.09780) — **an answerability-consulting router needs explicit
  supervision, which nobody has published.**
- **SteerMoE** (arXiv:2509.09660, ICLR 2026, verify): behavior-linked
  expert (de)activation at inference. [RUNTIME] — thermostat moved to
  router logits.
- **Bayesian MoE routing** (Li, arXiv:2509.23830, verify): router epistemic
  uncertainty as a first-class forward-pass quantity; used for OOD/
  calibration readout, loop to behavior not closed.
- **Confidence-adaptive MoE-LoRA** (CARE, arXiv:2607.26052; VoI routing
  with certificate-based abstention, arXiv:2608.02528; both verify).
  Closest published thing to "forward pass consults an internal uncertainty
  signal to allocate computation and abstain" — but the consulted signal is
  router-distribution flatness, not a validated epistemic readout.
  MoE-LoRA over a frozen dense 3-9B base is 3090-class.

#### Bottleneck generation

- **CB-LLM** (Sun, Oikarinen et al., ICLR 2025, arXiv:2412.07992). A
  concept-bottleneck layer inside a pretrained LLM for **generation**:
  intervening on a concept neuron moves outputs (~90% vs 60% sentiment
  flip). [WEIGHTS] — generation genuinely routes through the bottleneck —
  but concept values are recomputed from input under supervision, so the
  aux-head risk (a parallel re-representation rather than the native
  readout) applies; congruence must be tested, not assumed.
- **Concept Bottleneck Generative Models** (Ismail et al., ICLR 2024). The
  transferable asset is the **orthogonality/anti-leakage loss** against
  information routing around the bottleneck.

#### Self-monitoring wired into the pass, and cautionary results

- **[IDK]-token training** (Cohen et al., NeurIPS 2024, arXiv:2412.06676).
  Vocabulary token whose mass is trained up where the model's own
  prediction errs. Cleanest weights-level *output pathway* for abstention;
  [BEHAVIORAL] risk — nothing forces the [IDK] logit to be computed from
  the pre-existing KU axis. Cheap cell: IDK-tune, then test whether the
  [IDK] logit became a linear function of the KU readout.
- **CALM early exit** (Schuster et al., NeurIPS 2022, arXiv:2207.07061;
  decoder-only successor LayerSkip arXiv:2404.16710). Canonical existence
  proof that a trained internal confidence readout can causally alter the
  forward pass per token — but the quantity is next-token confidence and
  the action is compute, not content.
- **Uncertainty-aware decoding systematic study** (arXiv:2608.14653,
  verify): uncertainty-triggered rollback **degrades** pass@1 in 5 of 6
  configurations — naive wiring of weak uncertainty signals into control
  usually hurts. Useful contrast: our readout is near-ceiling.
- **LatentRefusal** (arXiv:2601.10398, verify): convergent external work —
  a pre-generation answerability probe gating refusal on Llama-3.1-8B /
  Qwen3-8B (F1 ~88.5). [RUNTIME], same class as our thermostat; it names
  the problem "answerability gating" — check its related work when
  positioning the new paper.
- **Backpack LMs** (Hewitt et al., ACL 2023): designed-for-intervention
  architecture; only ~170M checkpoints exist — conceptual value only.

#### Direct tests of models using their own internal uncertainty

- **Masked by Consensus** (arXiv:2604.12373, verify): correctness probes on
  a model's OWN hidden states show **no self-advantage** over probes on
  peer models' states on standard evals; self-advantage appears only on
  disagreement subsets for factual-knowledge tasks. Design consequence: the
  new study should benchmark the KU probe against a peer-model probe as a
  privileged-access control.
- **Can LLMs Introspect? A Reality Check** (arXiv:2605.26242, verify):
  input-only classifiers match models' "introspective" self-reports;
  behavioral evidence cannot establish introspection. Convergent with
  AA/AB/AH.
- **Metacognitive monitoring/control of activations** (Ji-An et al.,
  arXiv:2505.13763): models can report and control activation along given
  directions in-context, but only within a **low-dimensional metacognitive
  space**. Testable framing: is the KU axis inside that space?
- **Looking Inward** (Binder et al., arXiv:2410.13787): positive-but-narrow
  self-prediction advantage; contested by the above.

### 4B. Training objectives that force causal dependence on internal state

_(pending second sweep)_

### 4C. Distilling the runtime controller into weights

_(pending third sweep)_

## 5. Ranked recommendation

## 6. Design notes for the registered study
