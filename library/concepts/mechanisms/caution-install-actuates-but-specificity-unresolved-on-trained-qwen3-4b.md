---
aliases:
- Trained-lineage caution install actuates broadly but specificity and selectivity are unresolved
- G1 actuation clears at every dose-viable site on the trained Qwen3-4B lineage, G3 at one, G2 vacuous everywhere
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:caution-install-actuates-but-specificity-unresolved-on-trained-qwen3-4b
  type: mechanism
  status: canonical
cause: "In the caution-install-bounded-site-sweep experiment (Tier 2, exploratory), the answerability-gated caution snap mechanism from doubt-gated-caution-tighten (an erase-write along c_hat gated on the u_d answerability readout, tau chosen by Youden's J) was applied to the trained clean-SFT-to-GRPO-v2 Qwen3-4B lineage (LoRA revision 8914081dfcec4f1f025f2dbe4195d4f7aa8d210e) across a pre-registered bounded search: seven write sites (hs13 through hs35), two write positions (anchor, anchor_onward), an eight-rung ratio-normalized dose ladder per site and position, and three magnitude-matched two-site combinations, gated by per-site dose viability, G1 actuation, G2 selectivity, G3 direction specificity, and a G4 raw-base substrate anchor."
effect: "Dose viability cleared at only five of fourteen trained cells, all at the anchor_onward position (hs19, hs23, hs29, hs34, hs35); no anchor-position cell was dose-viable. G1 actuation passed at all five selected cells, held-out confab clean_tighten 0.870-0.955 (n=154, Wilson lower 0.808-0.909), contradicting the registered prediction that no registered site and position would clear G1 on the trained lineage. G3 direction specificity passed at hs35:anchor_onward only (gated lift 0.870 against a max random-draw lift of 0.071, ratio 12.18x over the 3.0x floor) and failed at hs19, hs23 (1.50x), hs29 (1.52x), and hs34. G2 selectivity was NOT-ADJUDICABLE (vacuous) at all five cells: the gate fired on only 4-20 known-correct rows per cell, below the registered adjudication floor of 35, so no cell may be cited as evidence the write is harmless. G4 held at the replicated anchor_onward operating point (raw-base hs23 0.8824 and hs29 0.9140 both inside their rep2-derived Wilson intervals), so the null is not an instrument artifact. Because the falsifier requires G1 pass, adjudicable G2, and G3 pass together at one registered cell, and the only G3-passing cell (hs35) has G2 not-adjudicable, the falsifier does not fire: paper 3's statement that no intervention installs appropriate abstention on genuine unknowns survives on the trained lineage, but as an exploratory lead requiring confirmatory replication, since raw actuation is not the bottleneck the prediction expected it to be."
polarity: complicates
related:
- '[[caution-install-bounded-site-sweep]]'
- '[[caution-residual-ablation-relaxes-overrefusal-asymmetrically]]'
- '[[doubt-gated-caution-tighten]]'
- '[[j-space-layer-contrast-rep2-multisource]]'
- '[[internal-paper3--knows-but-doesnt-say]]'
- '[[activation-steering]]'
- '[[abstention]]'
relationships:
- type: supported_by
  target: '[[caution-install-bounded-site-sweep]]'
  target_id: experiment:caution-install-bounded-site-sweep
  confidence: high
  evidence:
  - experiments/caution-install-bounded-site-sweep/AMENDMENT.md#outcome
    (Gate results, resolved 2026-08-13)
- type: related_to
  target: '[[caution-residual-ablation-relaxes-overrefusal-asymmetrically]]'
  target_id: mechanism:caution-residual-ablation-relaxes-overrefusal-asymmetrically
  confidence: high
  evidence:
  - experiments/caution-install-bounded-site-sweep/AMENDMENT.md (Falsifier;
    the mirrored raw-base relaxable-not-installable asymmetry this cell
    directly tests on the trained lineage)
- type: related_to
  target: '[[doubt-gated-caution-tighten]]'
  target_id: experiment:doubt-gated-caution-tighten
  confidence: high
  evidence:
  - experiments/caution-install-bounded-site-sweep/AMENDMENT.md (Design,
    Mechanism held fixed across all arms)
- type: related_to
  target: '[[j-space-layer-contrast-rep2-multisource]]'
  target_id: experiment:j-space-layer-contrast-rep2-multisource
  confidence: medium
  evidence:
  - experiments/caution-install-bounded-site-sweep/AMENDMENT.md#outcome (G4
    substrate anchor, replicated anchor_onward operating point)
- type: related_to
  target: '[[internal-paper3--knows-but-doesnt-say]]'
  target_id: paper:internal-paper3
  confidence: high
  evidence:
  - experiments/caution-install-bounded-site-sweep/AMENDMENT.md (Falsifier;
    section 6 and section 9 text this outcome governs)
- type: related_to
  target: '[[activation-steering]]'
  target_id: method:activation-steering
  confidence: medium
- type: related_to
  target: '[[abstention]]'
  target_id: term:abstention
  confidence: medium
---

The bounded site sweep complicates, rather than settles, the picture behind
[[caution-residual-ablation-relaxes-overrefusal-asymmetrically]]: on the
trained clean-SFT-to-GRPO-v2 Qwen3-4B lineage, bare actuation (G1, held-out
confab converted to a well-formed refusal) is not the bottleneck the
registered prediction expected. Every dose-viable anchor_onward cell cleared
G1 at 0.870-0.955, five sites out of five. What remains unresolved is
whether that actuation is a specific, controller-grade installation rather
than a broad refusal-inducing write: G3 direction specificity passed at only
one of those five sites, and G2 selectivity could not be adjudicated at any
of them because too few known-correct rows fired to satisfy the registered
N=35 floor, so none of the five cells can be cited as evidence the write is
harmless.

**Why it matters here:** because the falsifier is a strict three-gate
conjunction (G1 pass and adjudicable G2 and G3 pass, together, at one
registered cell) and no cell clears it, paper 3's bounded-search statement
survives formally. But the finding is not a clean reproduction of the
raw-base relaxable-not-installable story either: raw actuation clears
almost everywhere viable, and the open question is squarely about
specificity and collateral cost, not about whether a write can move
refusal behavior on genuine unknowns at all. This is registered Tier 2,
exploratory evidence; it is a lead, not a claim, and requires a
confirmatory replication registered before running it.

**Lineage:** resolution of [[caution-install-bounded-site-sweep]], reusing
the frozen answerability-gated caution snap from
[[doubt-gated-caution-tighten]] and the G4 anchor rates from
[[j-space-layer-contrast-rep2-multisource]]. Source of truth:
`experiments/caution-install-bounded-site-sweep/AMENDMENT.md`, Outcome
section, resolved 2026-08-13.
