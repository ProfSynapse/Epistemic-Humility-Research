---
aliases:
- stable probe F1 does not imply a stable probe subspace
- task subspaces keep shifting after performance converges
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:subspace-identity-rotates-across-seeds-and-checkpoints-despite-stable-probe-performance
  type: mechanism
  status: canonical
cause: "Fitting linear information-theoretic probes for nine linguistic tasks (POS, dependency, semantic tags, NER, coreference, topic, sentiment, QA, NLI) on MultiBERTs checkpoints spanning 2M pretraining steps and five random seeds, then comparing the resulting task subspaces with Principal Subspace Angles (SSA) both across checkpoints of the same training run and across different random seeds at the same training step, independently of probing F1."
effect: "SSA between checkpoints of the same run and seed shifts at a steady ~45 degrees during the 1k-10k step critical learning phase (when F1 is climbing steeply) and only narrows to 5-20 degrees by the end of the 2M-step run, so the fitted subspace keeps rotating substantially well after F1 has plateaued. Separately, SSA between models at the same checkpoint but different random seeds consistently measures above 80 degrees (near-orthogonal, high dissimilarity), even though probing F1 differs only slightly across those same seeds. Probe performance (F1, codelength) is therefore stable much earlier and much more tightly than the probe's own subspace identity."
polarity: complicates
related:
- '[[2310.16484--subspace-chronicles-how-linguistic-information-emerges-shifts]]'
- '[[principal-subspace-angles]]'
- '[[correctness-direction-weakly-identified-defeats-cosine-rotation-probe]]'
relationships:
- type: supported_by
  target: '[[2310.16484--subspace-chronicles-how-linguistic-information-emerges-shifts]]'
  target_id: paper:2310.16484
  confidence: high
  evidence:
  - Figure 4 (step-wise SSA across training time, Sec. 5.2); Figure 13, Appendix
    C.1 (cross-seed SSA >80 degrees at matched timesteps, Sec. 4.1/5.2); Figure
    2 (F1 convergence by 10k steps for comparison, Sec. 5.1)
- type: related_to
  target: '[[principal-subspace-angles]]'
  target_id: method:principal-subspace-angles
  confidence: high
- type: related_to
  target: '[[correctness-direction-weakly-identified-defeats-cosine-rotation-probe]]'
  target_id: mechanism:correctness-direction-weakly-identified-defeats-cosine-rotation-probe
  confidence: high
  evidence:
  - Independent confirmation, at LM-pretraining scale with a different subspace-comparison
    instrument (SSA on information-theoretic probes vs. cosine on logistic-regression
    directions), of the same dissociation between stable readout accuracy and
    unstable direction identity
---

Two linear-probe subspaces can report the same task performance while sitting at very different angles to each other. Subspace Chronicles finds this twice over: across pretraining checkpoints, where subspaces keep rotating at 45 degrees per step during the critical learning phase and only settle to 5-20 degrees near the end of training, well after F1 has converged; and across random seeds at a fixed checkpoint, where subspaces sit above 80 degrees apart despite near-identical F1.

**Why it matters here:** this is an independent confirmation, on a different model class and with a different subspace-comparison instrument (SSA on information-theoretic probes, not cosine on logistic-regression directions), of the same caution the correctness-direction-rotation cell ran into: a probe's accuracy converging says nothing about whether its fitted direction (or subspace) has also converged, so any cross-checkpoint or cross-seed subspace-overlap comparison needs to budget for this rotation as a baseline, not treat a stable AUROC/F1 as evidence the underlying subspace is fixed.

**Lineage:** uses [[principal-subspace-angles]] as the comparison instrument; directly parallels [[correctness-direction-weakly-identified-defeats-cosine-rotation-probe]], which reached the same qualitative conclusion (readout strength and direction identity dissociate) via split-half cosine reliability on a much smaller, fine-tuning-scale probe.
