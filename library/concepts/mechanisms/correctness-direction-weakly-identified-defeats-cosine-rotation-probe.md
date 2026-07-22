---
aliases:
- Correctness direction is weakly identified, defeating the cosine-rotation instrument
- split-half noise floor 0.174 versus answerability's >= 0.96 cross-stage cosine
- stable AUROC does not imply a stable probe direction
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:correctness-direction-weakly-identified-defeats-cosine-rotation-probe
  type: mechanism
  status: canonical
cause: "Fitting a per-stage logistic-regression correctness (correct-vs-wrong) direction in a shared raw-basis PCA-128 subspace at each of four training stages (raw base, clean-SFT, GRPO-v2, GRPO-par-true), then comparing directions by cosine, with only 500-1500 correct/wrong rows per stage and best-layer OOF AUROC of 0.809-0.860."
effect: "The fitted direction's own identity is not stable within a single stage: a split-half refit of the grpov2 correctness direction against itself returns a noise-floor cosine of only 0.174, close to the observed cross-stage cosines (raw->cleansft 0.192, cleansft->grpov2 0.449, grpov2->partrue 0.330). This holds even though per-stage AUROC stays stable near 0.80-0.86 and the identical raw-basis PCA-128 construction let the answerability (known-vs-unknown) direction reach cross-stage cosines >= 0.96 in the diag-item9 diagnostic. Readout strength and direction identity dissociate for the correctness dial at this sample size: the cosine-rotation instrument cannot discriminate genuine directional rotation across training stages from identifiability noise in the fitted hyperplane normal, so single-rotation-at-SFT-style claims about the correctness direction are not measurable with this instrument, and the mechanism behind the dial's partial (0.679) cross-checkpoint cold transfer stays unresolved."
polarity: complicates
related:
- '[[correctness-direction-rotation]]'
- '[[sft-rotates-boundary-readout-rl-rides-it]]'
- '[[per-answer-correctness-linearly-readable-post-generation]]'
- '[[answerability-and-correctness-are-orthogonal-readout-axes]]'
- '[[known-unknown-direction]]'
- '[[internal--diag-item9-caution-assembly-timeline]]'
relationships:
- type: supported_by
  target: '[[correctness-direction-rotation]]'
  target_id: experiment:correctness-direction-rotation
  confidence: high
  evidence:
  - experiments/correctness-direction-rotation/AMENDMENT.md#outcome (Outcome,
    Post-hoc interpretation and Caveats)
- type: related_to
  target: '[[sft-rotates-boundary-readout-rl-rides-it]]'
  target_id: mechanism:sft-rotates-boundary-readout-rl-rides-it
  confidence: high
  evidence:
  - experiments/correctness-direction-rotation/AMENDMENT.md (Outcome; contrasts
    with the answerability direction's >= 0.96 cross-stage cosine in the same
    raw-basis PCA-128 construction)
- type: related_to
  target: '[[per-answer-correctness-linearly-readable-post-generation]]'
  target_id: mechanism:per-answer-correctness-linearly-readable-post-generation
  confidence: high
  evidence:
  - experiments/correctness-direction-rotation/AMENDMENT.md (Design; the
    probed direction is the same post-generation correctness dial)
- type: related_to
  target: '[[answerability-and-correctness-are-orthogonal-readout-axes]]'
  target_id: mechanism:answerability-and-correctness-are-orthogonal-readout-axes
  confidence: medium
  evidence:
  - experiments/correctness-direction-rotation/AMENDMENT.md (Motivation and
    posture; the correctness and answerability axes are tracked separately
    and behave differently under this instrument)
- type: related_to
  target: '[[known-unknown-direction]]'
  target_id: term:known-unknown-direction
  confidence: medium
  evidence:
  - experiments/correctness-direction-rotation/AMENDMENT.md (Design; shared
    basis lineage)
- type: related_to
  target: '[[internal--diag-item9-caution-assembly-timeline]]'
  target_id: paper:internal-diag-item9
  confidence: high
  evidence:
  - experiments/correctness-direction-rotation/AMENDMENT.md (Design; the
    cross-stage cosine comparison this mechanism contrasts against)
---

The correctness-direction-rotation cell set out to measure whether the dial's
direction rotates across training stages the way the answerability direction
does. Both pre-registered readings (rotation-confirmed, and the falsifier)
came up empty, and the reason is instrumental rather than substantive: a
split-half refit of the same stage's correctness direction against itself
returns a cosine of only 0.174, a noise floor that sits close to every
observed cross-stage cosine in the study. The per-stage readout itself is
fine (AUROC 0.809-0.860 at every stage, in the same basis where the
answerability direction reached >= 0.96 cross-stage cosine), so the
dissociation is specific to direction identity, not to whether correctness
is decodable at all.

**Why it matters here:** it separates two questions that are easy to
conflate when reading a probe's cosine across checkpoints: "does the model
represent this information reliably" (answered yes, by AUROC) and "does the
same linear direction represent it across training stages" (unanswerable
with this instrument at this sample size, because within-stage refits do not
agree with each other either). Any future attempt to explain the correctness
dial's 0.679 cross-checkpoint cold transfer by appeal to rotation needs a
better-identified direction (more rows per stage, a different fitting
procedure, or an explicit reliability correction) before a cosine comparison
can carry the argument.

**Lineage:** contrasts directly with [[sft-rotates-boundary-readout-rl-rides-it]],
the well-identified single-rotation-at-SFT account measured for the
answerability direction in [[internal--diag-item9-caution-assembly-timeline]]
using the identical raw-basis PCA-128 construction. Probes the same
post-generation dial studied in
[[per-answer-correctness-linearly-readable-post-generation]]. Source of
truth: `experiments/correctness-direction-rotation/AMENDMENT.md`, Outcome
section, resolved 2026-07-20.
