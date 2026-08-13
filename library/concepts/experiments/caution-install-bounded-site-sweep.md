---
title: caution-install-bounded-site-sweep
aliases:
- Bounded caution-install site sweep on the trained Qwen3-4B lineage
- item-27 caution-install bounded site sweep
tags:
- kg/experiment
- experiment
- doubt-snap
- j-space
kg:
  id: experiment:caution-install-bounded-site-sweep
  type: experiment
  status: canonical
related:
- '[[doubt-gated-caution-tighten]]'
- '[[j-space-layer-contrast-rep2-multisource]]'
- '[[j-space-midband-dose-calibration-qwen3-4b]]'
- '[[ungated-vs-gated-dose-matched]]'
- '[[internal-ac-doubt-regulated-caution--coupled-write]]'
- '[[internal-paper3--knows-but-doesnt-say]]'
- '[[caution-residual-ablation-relaxes-overrefusal-asymmetrically]]'
- '[[caution-install-actuates-but-specificity-unresolved-on-trained-qwen3-4b]]'
relationships:
- type: builds_on
  target: '[[doubt-gated-caution-tighten]]'
  target_id: experiment:doubt-gated-caution-tighten
  confidence: high
  evidence:
  - experiments/caution-install-bounded-site-sweep/AMENDMENT.md (Design,
    Mechanism held fixed across all arms; reuses the answerability-gated
    caution snap verbatim, the one mechanism in the program with a governed
    raw-base installation success)
- type: builds_on
  target: '[[j-space-layer-contrast-rep2-multisource]]'
  target_id: experiment:j-space-layer-contrast-rep2-multisource
  confidence: high
  evidence:
  - experiments/caution-install-bounded-site-sweep/AMENDMENT.md#outcome (G4
    substrate anchor; the registered paired-replication comparison is
    defined at rep2's anchor_onward operating point, rep2 AMENDMENT.md line
    177)
- type: related_to
  target: '[[j-space-midband-dose-calibration-qwen3-4b]]'
  target_id: experiment:j-space-midband-dose-calibration-qwen3-4b
  confidence: medium
  evidence:
  - experiments/caution-install-bounded-site-sweep/AMENDMENT.md (Design,
    Axis 3 dose; absolute setpoints are forbidden per the collapse this
    predecessor's dose-calibration stage recovered from)
- type: related_to
  target: '[[ungated-vs-gated-dose-matched]]'
  target_id: experiment:ungated-vs-gated-dose-matched
  confidence: medium
  evidence:
  - experiments/caution-install-bounded-site-sweep/experiment.yaml (inputs)
- type: related_to
  target: '[[internal-ac-doubt-regulated-caution--coupled-write]]'
  target_id: paper:internal-ac-doubt-regulated-caution
  confidence: medium
  evidence:
  - experiments/caution-install-bounded-site-sweep/AMENDMENT.md (Prediction,
    Basis; the only other governed cell on this trained lineage, which
    resolved positive on coupling information rather than on installation)
- type: related_to
  target: '[[internal-paper3--knows-but-doesnt-say]]'
  target_id: paper:internal-paper3
  confidence: high
  evidence:
  - experiments/caution-install-bounded-site-sweep/AMENDMENT.md (Falsifier;
    tests paper 3 section 6's one-way-leverage statement and, on a silent
    falsifier, replaces the section 9 single-site/few-layer caveat with a
    statement naming the searched space)
- type: related_to
  target: '[[caution-residual-ablation-relaxes-overrefusal-asymmetrically]]'
  target_id: mechanism:caution-residual-ablation-relaxes-overrefusal-asymmetrically
  confidence: high
  evidence:
  - experiments/caution-install-bounded-site-sweep/AMENDMENT.md#outcome
    (falsifier does not fire; the raw-base relaxable-not-installable
    asymmetry survives the bounded search on the trained lineage)
- type: supports
  target: '[[caution-install-actuates-but-specificity-unresolved-on-trained-qwen3-4b]]'
  target_id: mechanism:caution-install-actuates-but-specificity-unresolved-on-trained-qwen3-4b
  confidence: high
  evidence:
  - experiments/caution-install-bounded-site-sweep/AMENDMENT.md#outcome
    (Gate results; G1/G2/G3/G4 dispositions and the falsifier conjunction)
---

Tier 2, exploratory bounded search testing whether the answerability-gated
caution snap of [[doubt-gated-caution-tighten]], the one mechanism in the
program with a governed raw-base installation success, transfers to the
trained clean-SFT-to-GRPO-v2 Qwen3-4B lineage, and if not, whether a
pre-registered bounded search over seven write sites (hs13 through hs35),
two write positions (anchor, anchor_onward), an eight-rung
ratio-normalized dose ladder per site, and three magnitude-matched two-site
combinations finds a site where appropriate abstention can be written into
genuine unknowns. Gated by G0 integrity, per-site dose viability, G1
actuation, G2 selectivity (mandatory three-way disposition), G3 direction
specificity against a random-direction placebo, and a G4 raw-base
interpretability anchor.

Resolved 2026-08-13, PI-approved. The falsifier does not fire and paper 3's
bounded-search statement stands, but the registered prediction's G1 clause
was wrong. Dose viability cleared at only five of fourteen trained cells,
all at the anchor_onward position (hs19, hs23, hs29, hs34, hs35); no
anchor-position cell was dose-viable. G1 actuation passed at all five
selected cells, held-out confab clean_tighten 0.870-0.955 (n=154, Wilson
lower 0.808-0.909). G3 specificity passed at hs35:anchor_onward only (gated
lift 0.870 vs a max random-draw lift of 0.071, ratio 12.18x against the
3.0x floor) and failed at hs19, hs23 (1.50x), hs29 (1.52x), and hs34. G2
selectivity was NOT-ADJUDICABLE (vacuous) at all five cells: the gate fired
on only 4-20 known-correct rows per cell, below the registered floor of 35,
so no cell can be cited as evidence of harmlessness. G4 held at the
replicated anchor_onward operating point (raw-base hs23 0.8824 and hs29
0.9140 both inside their rep2-derived Wilson intervals), so the instrument
is valid and the trained-lineage result is not instrument-void. Because the
falsifier requires G1 pass, adjudicable G2, and G3 pass together at one
registered cell, and no cell satisfies the conjunction, it does not fire:
paper 3's statement that no intervention tried installs appropriate
abstention on genuine unknowns stands, replaced per its own registered rule
by a statement naming the searched space rather than a proof of
impossibility. Source of truth:
`experiments/caution-install-bounded-site-sweep/AMENDMENT.md`.
