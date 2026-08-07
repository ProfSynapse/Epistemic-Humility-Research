---
title: best-stack-replication-scale-gate
aliases:
- 'Protocol Amendment G: Best-Stack Replication And Scale Gate'
- Amendment G
tags:
- kg/experiment
- experiment
- response-confidence
kg:
  id: experiment:best-stack-replication-scale-gate
  type: experiment
  status: canonical
related:
- '[[grpo-centered-stacking]]'
- '[[grpo-three-seed-confirmatory]]'
relationships:
- type: builds_on
  target: '[[grpo-centered-stacking]]'
  target_id: experiment:grpo-centered-stacking
  confidence: high
  evidence:
  - "experiments/best-stack-replication-scale-gate/AMENDMENT.md section 3 (registers seed-2/3 replication of the Amendment F seed-1 winner clean_sft_grpo_dpo)"
- type: built_on_by
  target: '[[grpo-three-seed-confirmatory]]'
  target_id: experiment:grpo-three-seed-confirmatory
  confidence: high
  evidence:
  - "experiments/grpo-three-seed-confirmatory/AMENDMENT.md Relationship to prior registrations, Amendment G (lead disposition at sign, 2026-07-31: superseded-before-signing for its seed-replication half; the 8B/publication half is untouched and survives as a separate downstream registration)"
---

Protocol Amendment G. DRAFT / NOT SIGNED. Registers two things: (1) a
seed-2/3 replication of the single best seed-1 stack from
[[grpo-centered-stacking]], `clean_sft_grpo_dpo`, as arms
`clean_sft_grpo_dpo_seed2` and `clean_sft_grpo_dpo_seed3`; and (2) a
separate, narrower 8B scale gate and Hugging Face publication gate, both
pending explicit launch approval.

Disposition ruled by the lead at sign time (2026-07-31): G's seed-replication
half is **superseded-before-signing** by
[[grpo-three-seed-confirmatory]], which is a strict superset covering the
same two seeds, the same per-seed lineage-rebuild rule, and the same metrics,
but all four stage-3 stacks plus all three stage-2 arms rather than the one
winning stack alone; the two registrations could not both be signed as
written without authorizing the same GPU work twice under different gates.
G's other half, the 8B scale gate and the HF publication gate, is **not**
covered by that disposition and survives as a separate, still-DRAFT,
downstream registration. Source of truth:
`experiments/best-stack-replication-scale-gate/AMENDMENT.md`.
