---
aliases:
- caution direction reads everywhere, actuates only on Qwen lineage
- cross-family read-actuate dissociation at the late write site
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:caution-encoding-read-actuate-dissociation-across-families
  type: mechanism
  status: canonical
cause: "In doubt-snap-cross-family-confirmatory's lead-verified c_hat validity audit (CPU, over existing captures across the four launched cells: qwen35_4b, qwen35_9b, llama32_3b_instruct, mistral7b_instruct_v03), the registered c_hat caution direction and a raw mass-mean refused-vs-answered direction are read out and scored for refused-vs-confab separability, then contrasted against the same cells' registered late write site (round(0.94*(num_hidden_layers-1))) actuation outcomes from the FIT dose sweep."
effect: "The caution encoding reads well in every family (c_hat AUROC 0.84-0.99, raw mass-mean refused-vs-answered AUROC 0.997-1.000, in all four cells), yet the same late-site write moves behavior strongly only on Qwen3-lineage (qwen35_4b, qwen35_9b), weakly on llama32_3b_instruct (peak clean_tighten 0.184), and not at all on mistral7b_instruct_v03 (0/874 fired confabs). Linear readability of the caution direction at the late site does not predict whether writing it there will actuate refusal outside Qwen. On llama/mistral, cross-population contrasts at this anchor also carry a norm/position confound (a fixed random direction reads 0.77-0.83 on refused-vs-known), which the audit records as not affecting the within-cell read-vs-actuate comparison the interpretation rests on."
polarity: prevents
related:
- '[[doubt-snap-cross-family-confirmatory]]'
- '[[qwen35-4b-midband-doubt-snap]]'
- '[[qwen35-4b-midband-write-decouples-refusal-from-format-collapse]]'
- '[[j-space-mediated-actuation-fragility]]'
- '[[workspace-band-peak-location-is-family-relative]]'
- '[[refused-vs-known-contrast-carries-norm-position-confound]]'
- '[[auroc]]'
- '[[refusal-axis-readable-but-not-ablatable-at-midband]]'
relationships:
- type: supported_by
  target: '[[doubt-snap-cross-family-confirmatory]]'
  target_id: experiment:doubt-snap-cross-family-confirmatory
  confidence: medium
  evidence:
  - experiments/doubt-snap-cross-family-confirmatory/AMENDMENT.md#outcome (c_hat validity audit)
- type: related_to
  target: '[[qwen35-4b-midband-doubt-snap]]'
  target_id: experiment:qwen35-4b-midband-doubt-snap
  confidence: high
  evidence:
  - experiments/doubt-snap-cross-family-confirmatory/AMENDMENT.md#outcome
- type: related_to
  target: '[[qwen35-4b-midband-write-decouples-refusal-from-format-collapse]]'
  target_id: mechanism:qwen35-4b-midband-write-decouples-refusal-from-format-collapse
  confidence: high
  evidence:
  - experiments/doubt-snap-cross-family-confirmatory/AMENDMENT.md#outcome
- type: related_to
  target: '[[j-space-mediated-actuation-fragility]]'
  target_id: mechanism:j-space-mediated-actuation-fragility
  confidence: medium
- type: related_to
  target: '[[workspace-band-peak-location-is-family-relative]]'
  target_id: mechanism:workspace-band-peak-location-is-family-relative
  confidence: medium
  evidence:
  - experiments/doubt-snap-cross-family-confirmatory/AMENDMENT.md#outcome
- type: related_to
  target: '[[refused-vs-known-contrast-carries-norm-position-confound]]'
  target_id: mechanism:refused-vs-known-contrast-carries-norm-position-confound
  confidence: medium
  evidence:
  - experiments/doubt-snap-cross-family-confirmatory/AMENDMENT.md#outcome
- type: related_to
  target: '[[auroc]]'
  target_id: metric:auroc
  confidence: high
- type: related_to
  target: '[[refusal-axis-readable-but-not-ablatable-at-midband]]'
  target_id: mechanism:refusal-axis-readable-but-not-ablatable-at-midband
  confidence: medium
  evidence:
  - experiments/jlens-trained-checkpoint-midband-ablation/AMENDMENT.md#outcome
---

*Legacy naming note (2026-08-16): this note's title/slug predates the program's vocabulary rename; see `papers/common/terminology.md` for current running-prose terms (known-unknown direction, KU readout gate, refusal axis, KU-readout coupling, IDK switch). The slug stays verbatim under usage rule 1.*

`doubt-snap-cross-family-confirmatory`'s registered cross-family panel stopped
every launched cell at the pre-outcome FIT dose-viability gate, before any
held-out scoring. On its own that result is ambiguous between two stories:
the doubt-gated caution snap does not transfer to non-Qwen families at all,
or the caution encoding is present everywhere but the ported late write site
is the wrong place to apply it. A post-hoc audit of the cells' own committed
captures adjudicates between these: the caution direction is linearly
readable at high AUROC in every family, so the encoding transfers; the late
write site's actuation strength does not, falling off sharply from Qwen
lineage to llama to mistral.

This read-actuate dissociation is the cross-family generalization of the
same-substrate Qwen3.5-4B finding
([[qwen35-4b-midband-write-decouples-refusal-from-format-collapse]]): moving
the write off the late site to a mid-band layer recovers a coherent decoupling
window on Qwen3.5-4B specifically, which is direct evidence that a write-site
fix, not a family-level mechanism absence, is the right diagnosis for at
least one of the families in this dissociation. The registered
`round(0.94*(num_hidden_layers-1))` layer rule, ported unmodified from
Qwen3-4B across every family in the panel, is the design element this
dissociation indicts: `jspace-family-atlas`'s independent per-family layer
atlas found that readable interior structure sits at family-relative depths
(llama layers 15-23, mistral layers 7-27) rather than at one universal depth
fraction ([[workspace-band-peak-location-is-family-relative]]), which is
consistent with a wrong-site rather than absent-mechanism explanation for
the llama and mistral nulls.
