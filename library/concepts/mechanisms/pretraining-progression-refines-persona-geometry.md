---
aliases:
- Pretraining Progression Refines Persona Geometry
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:pretraining-progression-refines-persona-geometry
  type: mechanism
  status: canonical
cause: "Continued pretraining beyond the initial emergence of [[persona-vectors|persona directions]], progressively refining the representation through more gradient updates on diverse text"
effect: "Cosine similarity of persona vectors to the final-checkpoint pretraining direction rises from approximately 0.3 at the earliest extractable checkpoint toward 1.0; adjacent-checkpoint cosine similarity remains high throughout"
polarity: increases
related:
- '[[2605.13329--tracing-persona-vectors-through-llm-pretraining]]'
- '[[persona-vectors]]'
- '[[pretraining-checkpoint-tracing]]'
relationships:
- type: supported_by
  target: '[[2605.13329--tracing-persona-vectors-through-llm-pretraining]]'
  target_id: paper:2605.13329
  confidence: high
- type: related_to
  target: '[[persona-vectors]]'
  target_id: method:persona-vectors
- type: related_to
  target: '[[pretraining-checkpoint-tracing]]'
  target_id: method:pretraining-checkpoint-tracing
---

Once persona directions emerge early in pretraining, continued training does not replace them but rather rotates them toward a stable final geometry. Tracking the cosine similarity of persona vectors extracted at successive checkpoints to the final checkpoint vector reveals a monotonic increase from approximately 0.3 at emergence to near 1.0, while adjacent-checkpoint similarity stays high, indicating slow directional drift rather than discontinuous jumps (arXiv:2605.13329). This smooth convergence suggests that pretraining progressively sharpens the alignment of persona directions with the semantic structure of the full training corpus rather than discovering qualitatively new directions.
