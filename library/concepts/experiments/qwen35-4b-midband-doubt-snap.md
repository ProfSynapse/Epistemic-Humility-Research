---
title: qwen35-4b-midband-doubt-snap
aliases:
- Qwen3.5-4B mid-band doubt-snap decoupling test
tags:
- kg/experiment
- experiment
- j-space
kg:
  id: experiment:qwen35-4b-midband-doubt-snap
  type: experiment
  status: canonical
related:
- '[[j-space-mediated-actuation-fragility]]'
- '[[qwen35-late-site-entangles-refusal-and-format-collapse]]'
- '[[steering-dose-windows-are-absolute-not-sigma-transferable]]'
- '[[qwen35-batch-composition-flips-greedy-decode-outcomes]]'
- '[[doubt-snap-cross-family-confirmatory]]'
- '[[j-space-layer-contrast-rep2-multisource]]'
- '[[qwen35-4b-midband-write-decouples-refusal-from-format-collapse]]'
- '[[caution-write-selectivity-is-content-dependent-not-gate-created]]'
- '[[idk-switch-naming-confirmatory]]'
- '[[idk-switch]]'
relationships:
- type: built_on_by
  target: '[[idk-switch-naming-confirmatory]]'
  target_id: experiment:idk-switch-naming-confirmatory
  confidence: high
  evidence:
  - experiments/idk-switch-naming-confirmatory/AMENDMENT.md (Design; c_hat and
    random_direction loaded byte-identical from this experiment's committed
    directions/hs20/ tree, no direction refit)
- type: related_to
  target: '[[idk-switch]]'
  target_id: term:idk-switch
  confidence: high
  evidence:
  - experiments/idk-switch-naming-confirmatory/AMENDMENT.md#outcome (the name
    IDK switch is EARNED for the c_hat write/dose law at this experiment's
    hs20 operating point)
- type: tests
  target: '[[j-space-mediated-actuation-fragility]]'
  target_id: mechanism:j-space-mediated-actuation-fragility
  confidence: medium
  evidence:
  - experiments/qwen35-4b-midband-doubt-snap/AMENDMENT.md#outcome
- type: tests
  target: '[[qwen35-late-site-entangles-refusal-and-format-collapse]]'
  target_id: mechanism:qwen35-late-site-entangles-refusal-and-format-collapse
  confidence: high
  evidence:
  - experiments/qwen35-4b-midband-doubt-snap/AMENDMENT.md#outcome
- type: supports
  target: '[[qwen35-4b-midband-write-decouples-refusal-from-format-collapse]]'
  target_id: mechanism:qwen35-4b-midband-write-decouples-refusal-from-format-collapse
  confidence: high
  evidence:
  - experiments/qwen35-4b-midband-doubt-snap/AMENDMENT.md#outcome
- type: supports
  target: '[[caution-write-selectivity-is-content-dependent-not-gate-created]]'
  target_id: mechanism:caution-write-selectivity-is-content-dependent-not-gate-created
  confidence: high
  evidence:
  - experiments/qwen35-4b-midband-doubt-snap/AMENDMENT.md#outcome
- type: builds_on
  target: '[[steering-dose-windows-are-absolute-not-sigma-transferable]]'
  target_id: mechanism:steering-dose-windows-are-absolute-not-sigma-transferable
  confidence: high
  evidence:
  - experiments/qwen35-4b-midband-doubt-snap/AMENDMENT.md (Stage B fit result table)
- type: supports
  target: '[[qwen35-batch-composition-flips-greedy-decode-outcomes]]'
  target_id: mechanism:qwen35-batch-composition-flips-greedy-decode-outcomes
  confidence: high
  evidence:
  - experiments/qwen35-4b-midband-doubt-snap/NOTEBOOK.md (2026-07-10 batch-size probe entry)
- type: builds_on
  target: '[[doubt-snap-cross-family-confirmatory]]'
  target_id: experiment:doubt-snap-cross-family-confirmatory
  confidence: high
  evidence:
  - experiments/qwen35-4b-midband-doubt-snap/AMENDMENT.md (Motivation and posture)
- type: builds_on
  target: '[[j-space-layer-contrast-rep2-multisource]]'
  target_id: experiment:j-space-layer-contrast-rep2-multisource
  confidence: high
  evidence:
  - experiments/qwen35-4b-midband-doubt-snap/AMENDMENT.md (Motivation and posture)
---

Exploratory Tier-2 test of whether writing the doubt-gated caution snap at a
J-space workspace-band (mid-band) layer on Qwen/Qwen3.5-4B (bf16, hybrid
linear-attention architecture) decouples confab refusal induction from
output-format corruption, where the registered late write site (0.94-depth,
hs30) produced a well-characterized G0 dose-viability null in
`doubt-snap-cross-family-confirmatory`. A local J-lens profile localized a
workspace-like effective-dimensionality band at hs20/hs23/hs26 (peak at
hs23), distinct from the late hs30 site, mirroring the Qwen3-4B same-model
mid-band-vs-late-band lesson (`j-space-layer-contrast-rep2-multisource`,
resolved FULL PASS).

Resolved 2026-07-12. **G1 PASSES.** hs20 at dose 8 x sigma_c is the unique
cell in the locked 4-layer x 7-dose grid that clears both primary floors on
fired FIT confabs simultaneously: refused 0.684 (594/869) with well_formed
0.980, against floors of 0.60 and 0.80, with known-correct false-refusal
0.042 (10/240, bar <= 0.10). The in-grid late-site comparator (hs30, re-run
here) never clears both floors at any dose (peak refused about 0.31 with
well-formedness already degrading), reproducing its own entangled collapse;
neither hs23 (the eff-dim profile peak, refused 0.456) nor hs26 (refused
0.276) reaches the refusal floor. The mid-band lesson from Qwen3-4B therefore
transfers to Qwen3.5-4B: the late-site failure was a write-site problem, not
a family problem
([[qwen35-4b-midband-write-decouples-refusal-from-format-collapse]]). A
permuted-gate control isolates the confab/known selectivity to the write
direction's own content dependence rather than the doubt gate
([[caution-write-selectivity-is-content-dependent-not-gate-created]]). This
is in-sample FIT characterization only (c_hat fit and evaluated on the same
FIT confabs, held-out untouched by design); promotion to a claim requires a
registered held-out stage. An adversarial red-team review over seven attack
surfaces returned no invalidating finding. Source of truth:
`experiments/qwen35-4b-midband-doubt-snap/AMENDMENT.md` and `NOTEBOOK.md`.
