---
aliases:
- UaIT-style response-confidence target shaping
- contrastive response-confidence target shaping
- response-confidence target shaping
- confidence target distribution shaping
tags:
- kg/method
- concept
- method
kg:
  id: method:contrastive-response-confidence-target-shaping
  type: method
  status: draft
area: calibration
related:
- '[[2024.emnlp-main.1205--llms-learn-uncertainty-uait]]'
- '[[uncertainty-aware-instruction-tuning]]'
- '[[verbalized-confidence]]'
- '[[confidence-elicitation]]'
- '[[supervised-finetuning]]'
- '[[calibration]]'
relationships:
- type: inspired_by
  target: '[[2024.emnlp-main.1205--llms-learn-uncertainty-uait]]'
  target_id: paper:2024.emnlp-main.1205
  confidence: high
  evidence:
  - '[[2024.emnlp-main.1205--llms-learn-uncertainty-uait]]'
- type: derived_from
  target: '[[uncertainty-aware-instruction-tuning]]'
  target_id: method:uncertainty-aware-instruction-tuning
  confidence: high
- type: variation_of
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
  confidence: medium
- type: related_to
  target: '[[verbalized-confidence]]'
  target_id: method:verbalized-confidence
  confidence: high
- type: related_to
  target: '[[confidence-elicitation]]'
  target_id: method:confidence-elicitation
  confidence: high
- type: used_for
  target: '[[calibration]]'
  target_id: term:calibration
  confidence: high
---

Contrastive response-confidence target shaping is a proposed dataset-construction
method for schema-trained confidence expression. It extends [[uncertainty-aware-instruction-tuning]]
to the Epistemic Humility response-confidence setting: train the model to output
both an answer and a scalar probability that the response is appropriate, while
ensuring the supervised targets contain meaningful high, middle, and low
contrast.

The motivating failure mode is modal scalar collapse. In Amendment D, SFT
learned the JSON envelope but emitted a constant `response_confidence: 0.8`.
In Amendment E v1, probe-scaled targets were non-constant, but the dominant
target `0.8765` still represented 81.79% of SFT rows; the resulting model
again emitted one scalar everywhere. This suggests that unique target count is
insufficient: the target distribution must prevent a single modal scalar from
being the easy loss-minimizing answer.

The UaIT precedent is to generate answers, estimate the model's uncertainty
for those answers with a probabilistic/multi-sampling teacher signal, and
distill examples where answer correctness and confidence agree: correct/high
confidence and incorrect/low confidence. The important point for this project
is that low-confidence incorrect answers are part of the supervised signal,
not merely preference or reward negatives after SFT.

For the local response-confidence track, the preferred revision is therefore
not row deletion alone. It is a full-size contrastive target projection:

- appropriate known answers receive high response-confidence targets
- appropriate unknown abstentions receive high response-confidence targets,
  because confidently saying "I don't know" is the correct response when the
  model is outside its knowledge boundary
- wrong answers on known or unknown questions receive low targets
- over-refusals on known questions receive low targets
- ambiguous model-specific rows should generally remain answerable rather than
  forced into abstention, but the answer should carry low-to-middle confidence
  to express uncertainty
- exact 0.0 and 1.0 endpoints are avoided
- mathematically shaped targets should avoid one value dominating the SFT loss

Candidate shaping functions include deterministic quantile mapping, monotonic
band spreading, or stable row-hash spreading within each confidence band. These
preserve rows while widening the scalar support. Random jitter is less
desirable because it obscures provenance; deterministic transforms are easier
to audit, regenerate, and compare across runs.

**Open design question:** whether SFT alone can learn this contrastive scalar
when wrong-answer/over-refusal low-confidence rows are included, or whether the
scalar still requires a downstream preference/RL stage after the output
contract is learned.

**Local evidence:** `docs/sessions/20260623T093654Z-probe-scaled-response-confidence-retrain.md`
records the Amendment E v1 collapse and the subsequent v2 dataset revision.
The v2 local contrastive SFT projection generated 29,338 rows: 14,395
appropriate/high targets, 14,395 inappropriate/low targets, and 548
ambiguous-answer/middle targets. The resulting target distribution had 4,986
unique scalar values, range `[0.10, 0.90]`, mean `0.512539`, and a largest exact
target count of 20 rows. This dataset is intended to test whether supervised
contrast alone can prevent response-confidence scalar collapse before starting
downstream schema DPO/KTO/GRPO.
