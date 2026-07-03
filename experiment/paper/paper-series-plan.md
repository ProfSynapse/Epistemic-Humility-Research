# Paper Series Plan: Epistemic Humility -> Two-Signal Trust Readout

Status: planning (2026-06-30). This is our internal roadmap, not a draft. It maps
the program onto a three-paper series that builds toward a flagship, records which
internal evidence backs each claim, and lists the concrete work to do before any
of it is submittable.

## Conventions for the papers themselves

1. **Papers state confirmed claims cleanly.** They do not narrate amendments,
   gate IDs, or our governance machinery. The amendment / lab-notebook trail is
   *our* record of how the findings evolved; in the papers it becomes plain-language
   "how we found it / robustness," or moves to a supplement, never "Amendment S
   showed...".
2. **Headline claims rest on pre-registered confirmatory evidence.** An exploratory
   finding (any single-family amendment) earns a flat assertion in a paper only
   after a pre-registered replication predicts it under untouched conditions (fresh
   seeds / bigger model / held-out dataset / new model family) and it lands. The
   exploratory work motivates; the confirmatory run is what the claim stands on.
   See "Confirmatory backbone" below.
3. **Provenance distinction is preserved.** Where a number comes from the locked
   pre-registered matrix vs an exploratory cell, the paper says so in plain terms
   ("a pre-registered three-way comparison" vs "an exploratory extension").

## The spine

Three papers, each the previous one's unanswered question, all pointing at #3.

Title format is `[catchy title]: [subtitle]`.

| # | Title (candidate) | One-line thesis |
|---|-------------------|-----------------|
| 1 | **The Abstention Tax: Calibration Costs of Abstention Training Across SFT, DPO, KTO, and GRPO** | Teaching a small model to say "I don't know" buys the behavior but degrades the calibration of what it does say; shown across all four objectives. |
| 2 | **It Knows, It Won't Say: A Training-Resistant Gap Between Internal Knowledge and Stated Confidence** | The model represents what it doesn't know internally with near-perfect separability, but the stated channel is decoupled, and no training intervention we apply installs the missing link: a channel bottleneck, not a data problem. |
| 3 | **Confidence Is a Readout, Not a Lesson: A Training-Free, Two-Signal Trust Signal for Small Language Models** | You do not need to train trust in. Two orthogonal, linearly decodable axes (an answerability gate and a per-answer correctness dial that vetoes confident confabulation) compose into a deployable, calibrated, thresholdable trust signal that reads off the model with no task training and generalizes across model size and family. |

Build-on logic: *training for abstention trades calibration* (1) -> *because the
model already knows internally but cannot say it, and training cannot install the
link* (2) -> *so stop trying to train it in and read it out instead* (3).

Subtitle alternates if a punchier catchy half is preferred for #3: *Trust on Tap*,
*Two Signals*. The catchy halves above are my leans; subtitles are negotiable.

---

## Paper 1 — The Abstention Tax

**Thesis.** Across the four dominant alignment objectives, training a small model
to abstain reliably trades against the calibration of its non-abstained answers.
The lit review (formerly our standalone meta-analysis) motivates this by showing
the field rarely measures the two together on one run.

**Contributions.**
- A lit review establishing the measurement gap (no head-to-head SFT/DPO/KTO/GRPO
  on the abstention<->calibration tension; recall / over-refusal decomposition
  rarely reported).
- A four-way training comparison (SFT / DPO / KTO / GRPO) on one model, one data
  recipe, decomposing abstention behavior and calibration on the same run.
- The headline tension result.

**Evidence & provenance (internal record; not cited as amendments in-paper).**
- Headline confirmatory surface: the **pre-registered three-way** (SFT/DPO/KTO,
  3 seeds @ 4B) from the locked PROTOCOL matrix. These are the only numbers stated
  as pre-registered.
- GRPO (v1/v2/v3) was added exploratorily after the lock. **Action:** the paper
  presents the four-way, but GRPO is framed as an extension unless a confirmatory
  GRPO replication is registered. Do NOT silently pool it into the pre-registered
  headline.

**Gaps / do before submit.**
- Decide GRPO framing: report-as-extension (cheap, honest) vs register a
  confirmatory GRPO arm (stronger, costs a run).
- Confirm the calibration metric reported (ECE + reliability) is consistent with
  Paper 3's calibrated dial story.

---

## Paper 2 — It Knows. It Won't Say.

**Thesis.** The decoupling in Paper 1 is not a data or objective problem. The model
linearly represents its own knowledge boundary internally with near-ceiling
separability, while its stated-confidence channel is near-chance-correlated with
that internal state; and the gap survives every training and steering intervention
we apply. The bottleneck is the emission channel.

**Contributions.**
- The internal-vs-stated gap: internal answerability axis (AUROC ~0.997) vs stated
  confidence (~0.52-0.56).
- Training-resistance panel: the gap persists through DPO / KTO / GRPO x3 /
  contrastive SFT, and through a joint aux-head co-training attempt that
  specifically tried to open the channel and failed.
- Steering asymmetry: ablating the caution direction relaxes over-refusal
  (0.994 -> 0.030) but cannot *install* abstention, and the say/act dissociation
  (one intervention shifts what it says, another what it does, never both).

**Evidence & provenance (internal record).**
- Internal axis, stated-channel gap, training-resistance, steering asymmetry: the
  Paper-3 draft R1-R4 and amendments N/M/R. Single model family.

**Gaps / do before submit (the reviewer attacks to pre-empt).**
- **Scope the gate as category-answerability, not competence.** The ~0.997 may
  partly read "is this the *kind* of question that has an answer" (lexical/format)
  rather than "does *this model* know." Add one control: known-vs-unknown *among
  answerable factual questions* (competence within category). The cross-dataset
  transfer result helps but the two datasets share the answerability construct.
- **"Doesn't say" is "doesn't say under this elicitation."** Robustness across
  verbalization formats (explicit probability / verbal hedge / P(True) /
  multi-sample consistency). If only one elicitation was tried, either add a
  second or scope the claim explicitly. This is the most likely reviewer attack.
- **"Training-resistant" = resistant to the runs we did**, single seed per arm.
  Scope honestly; consider one fresh seed on the key arm as cheap insurance.

---

## Paper 3 — Confidence Is a Readout, Not a Lesson (FLAGSHIP)

**Thesis.** A small LM already carries a deployable trust signal; you read it out
rather than train it in. Two orthogonal linear axes compose into a two-stage
pipeline:
- **gate** = answerability, read at the last prompt token; abstain below threshold.
- **dial** = per-answer correctness, read at the post-generation content token,
  surfaced as a calibrated, thresholdable trust number.
- **veto** = the dial assigns confident confabulation the lowest trust.

Everything above reads off the raw model with no task-specific training; task
training only *sharpens* the veto, it does not create the signal. The readout
generalizes across model size and (confirmatory) across model family, and matches
or beats standard confidence baselines at a fraction of their inference cost
(one forward, no sampling).

**Key results & provenance (internal record).**
- Correctness dial reads post-generation and post beats pre: **AUROC 0.834 (L20)**,
  delta +0.065, bootstrap CI [0.040, 0.090] (excludes 0). n = 500 correct /
  1336 wrong (Instruct base). Selective prediction: top-10%-confident answers reach
  **75.5%** accuracy vs a **27.2%** base rate.
- Answerability axis transfers cross-dataset (~0.983).
- Hallucination veto AUROC 0.980, within-dataset control 0.93 (rules out dataset
  shift).
- Orthogonality: fusing the two scalars *hurts* (delta -0.014) -> keep as a
  two-stage pipeline, do not fuse.
- Training-free: full mechanism reads off the raw base (gate 0.997 / dial 0.834 /
  veto 0.754); training sharpens the veto (0.754 -> 0.980), adds ~0 to the gate.
- Size generalization: within-Qwen3 sweep (1.7B / 4B / 8B / 14B), exploratory.

**Gaps / do before submit — these are the flagship's real work.**

1. **Calibrate the dial (the cheapest, highest-value fix).** Today the dial *ranks*
   (AUROC 0.834) but is *not* a calibrated probability: ECE_post = 0.151 (S) /
   0.168 (T), both miss the 0.15 bar, and there is **no Platt/isotonic step in the
   code**. Add a calibration-map stage (fit on a held-out fold), re-report ECE +
   reliability diagram. This converts "ranks well" into "a number you threshold and
   read as a probability," which is the entire deliverable. Expect it to pull ECE
   under 0.15.
2. **Real deployment-distribution evidence (fill option B).** The dial is validated
   where wrong answers exist in quantity (Instruct base: 500/1336; T on a *forced*
   answer surface). The deployed abstention-trained checkpoint almost never emits a
   wrong answer naturally (~94%-right-when-answering; the natural-distribution
   probe was data-starved at ~96% refusal). Get real evidence on a *natural*
   (un-forced) distribution with a healthy wrong rate: the Instruct base's natural
   output distribution, a less-aggressively-abstaining checkpoint, or a harder
   dataset where the model is wrong often enough (>=30 wrong) to validate against.
   So the dial's "trust number on what the model actually emits" claim has
   real, not forced, support.
3. **Full baseline table** (all on the same answered-items population):
   - verbalized confidence (the "doesn't say" channel; expected to lose, that's the
     point);
   - P(True) / self-eval (we partially have it via the post-gen self-eval gain;
     formalize);
   - max-softmax / sequence logprob (the cheap logit baseline);
   - semantic entropy (the strong modern baseline reviewers will demand; needs
     sampling, which is a deliberate added cost against our greedy-everywhere setup).
   Story the table should tell: the readout matches/beats these at one forward, no
   sampling -> the deployment argument.

**Scope-honestly statements (state in the paper, do not hide).**
- "Training-free" means **no task-specific training**; the base is upstream
  instruction-tuned. The base veto (0.754) is genuinely weaker than trained
  (0.980): the honest claim is "present without task training, sharpened by it."
- The +95pt policy-margin demonstration is partly circular (the action is driven by
  the probe). Lead with the readout AUROCs and the selective-prediction curve, not
  the margin. The non-circular correctness number is the dial AUROC.
- Correctness-ranking on the deployed model is underpowered by design (it answers
  only when ~94% right); this is why the gate carries most of the load there and
  why the dial is validated on a healthier distribution (see fill B).

---

## Confirmatory backbone (what makes #3 a flagship, not a pile of amendments)

All of S/T/U/W/X are exploratory, single-family, discovered iteratively. To assert
the readout flatly, pre-register ONE replication that predicts the result under
conditions we have not touched, then run once:

- **Primary: a pre-registered cross-FAMILY replication.** Before running, register
  the predicted gate / dial / veto AUROC thresholds (with CIs) on new families.
  Run once. If they land, the readout is confirmed and the "single model family"
  weakness dies in one shot. The within-Qwen3 size sweep (Amendment X) stays as
  exploratory robustness, not the confirmatory claim.
- The calibrated dial + the baseline table should be specified in that same
  pre-registration so the headline calibration and comparison numbers are
  confirmatory, not chosen after the fact.

**This requires NO training.** The readout is training-free: each cross-family
model is one forward pass over [prompt+answer] + a CPU linear probe. We do not
fine-tune any new family. Papers 1 and 2 stay Qwen-only by design (those runs
exist); cross-family *training* (to test whether the Paper-2 gap is family-general)
is a larger lift and explicitly future work, not part of this confirmatory claim.

**Model set (size held ~3-4B so size is not a family confound).** Anchor +
three new families:

| Role | Model | Family | Modality for us | Verify before registering |
|------|-------|--------|-----------------|---------------------------|
| anchor / positive control | Qwen3-4B | Qwen | text | already validated |
| new family | Llama 3.2 3B | Meta | text-only (1B/3B are pure text) | 4-bit/unsloth build |
| new family | Ministral 3B | Mistral | text-only | open weights availability (8B-Instruct is open; 3B was API-gated) |
| new family | Gemma 4 E4B | Google | TBD (post-cutoff; verify empirically) | architecture, modality, hidden-state access, chat template all confirmed by the compat smoke, not assumed |
| within-family version control (optional) | newer Qwen (e.g. 3.5) | Qwen | text | tests version, NOT family; label separately |

**On multimodal models.** A small VLM is an LM backbone + a vision adapter; with
text-only input the vision tower never fires and the residual stream at text token
positions is exactly what the probe reads. The only work is plumbing, not concept:
(a) reaching `output_hidden_states` on the VLM wrapper (sometimes via the
`.language_model` submodule); (b) each family's chat template + EOS/turn tokens for
`content_end` detection (the extractor already handles Qwen `<|im_end|>` with a
plain-EOS fallback; each new family needs its own); (c) confirming a 4-bit build or
falling back to HF + bitsandbytes. A multimodal backbone passing the protocol
*strengthens* the paper ("works even text-only on a multimodal model").

**De-risk step before locking the pre-registration:** a one-model extraction-compat
smoke on Gemma 4 E4B (post-cutoff, architecture unknown to us) to confirm text-only
hidden-state extraction + content_end detection work end-to-end. Cheap, and it
prevents registering thresholds for a model we then cannot cleanly extract from.

This is the single most important pre-submit decision for the flagship: it is the
difference between "we observed this on Qwen3" and "this is a property of small
instruction-tuned LMs."

---

## Cross-cutting checklist

Do (build new evidence):
- [ ] Add Platt/isotonic calibration stage to the dial scorer; re-report ECE +
      reliability (Paper 3 #1).
- [ ] Real natural-distribution dial validation, fill option B (Paper 3 #2).
- [ ] Full baseline table: verbalized, P(True), max-softmax, semantic entropy
      (Paper 3 #3).
- [ ] Competence-within-category gate control (Paper 2).
- [ ] Multi-elicitation robustness for "doesn't say" (Paper 2).
- [ ] Pre-register + run the cross-family confirmatory replication (backbone).

Verify (double-check existing):
- [ ] GRPO numbers reproduce and the four-way is internally consistent (Paper 1).
- [ ] Selective-prediction + calibration numbers consistent across S/T after the
      calibration stage lands.

Scope (state honestly, no new runs):
- [ ] "Training-free = no task-specific training" framing everywhere.
- [ ] Demote the +95pt margin to a demonstration; lead with AUROC + selective
      prediction.
- [ ] Gate = category-answerability caveat where the 0.997 is reported.
- [ ] Single-seed-per-arm caveat on the training-resistance panel.

---

## Open decisions for the user

1. Final titles (candidates above).
2. GRPO in Paper 1: report-as-extension vs register a confirmatory GRPO arm.
3. Confirmatory model set (proposed: Qwen3-4B anchor + Llama 3.2 3B + Ministral 3B
   + Gemma 4 E4B; optional newer-Qwen version control). Confirm availability +
   run the Gemma 4 extraction-compat smoke before locking the pre-registration.
4. Author / collaborator outreach timing (user plans to seek collaborators once
   drafts exist; venue follows from that).
