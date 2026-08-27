---
aliases:
- llama's hs17 mid-band write is direction-specific
- llama joins qwen as a family with a verified selective write
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:llama-hs17-write-is-direction-specific
  type: mechanism
  status: canonical
cause: "On raw-base Llama-3.2-3B-Instruct, the frozen KU-gated `c_hat` write at the mid-band site hs17 (relative depth 0.607, dose 4.9549) is replicated under a fresh decode seed on 872 held-out confab rows, then contrasted against fifteen fresh matched-dose random unit directions (seeds 910001-910015) applied through the identical KU gate, dose, and generation contract."
effect: "The gated write replicates the floor-clearing behavior (held-out clean_tighten 635/872 = 0.7282, Wilson 95% [0.6977, 0.7567], vs the 0.50 floor and the parent cell's 0.7420) and clears the direction-specificity floor against the random census: gated lift 0.7190 vs the strongest of fifteen random lifts 0.0872 (seed 910010), effect ratio 8.25 against the registered 3.0 floor. Llama's hs17 mid-band write is direction-specific, not a nonspecific dosing artifact, making llama the second family (after Qwen) with a verified selective write. The companion known-correct cost gate is NOT-ADJUDICABLE: the KU gate fired on 0 of 334 held-out known-correct rows, below the pre-registered 22-row adjudicability floor, so no cost claim is made in either direction."
polarity: enables
related:
- '[[llama-hs17-direction-specificity]]'
- '[[j-space-cross-family-layer-contrast]]'
- '[[caution-encoding-read-actuate-dissociation-across-families]]'
- '[[known-unknown-direction]]'
- '[[llama-hs17-direction-specificity-survives-wide-instrument]]'
relationships:
- type: derived_from
  target: '[[j-space-cross-family-layer-contrast]]'
  target_id: experiment:j-space-cross-family-layer-contrast
  confidence: high
  evidence:
  - experiments/llama-hs17-direction-specificity/AMENDMENT.md (Lineage; the
    write, gate, dose, and directions are frozen artifacts reused verbatim
    from that experiment's resolved INCONCLUSIVE llama arm)
- type: supported_by
  target: '[[llama-hs17-direction-specificity]]'
  target_id: experiment:llama-hs17-direction-specificity
  confidence: high
  evidence:
  - experiments/llama-hs17-direction-specificity/AMENDMENT.md#outcome (LG-G1,
    LG-G2, LG-G3)
- type: related_to
  target: '[[caution-encoding-read-actuate-dissociation-across-families]]'
  target_id: mechanism:caution-encoding-read-actuate-dissociation-across-families
  confidence: high
  evidence:
  - experiments/llama-hs17-direction-specificity/AMENDMENT.md (Motivation and
    posture; this result updates the "no verified selective write outside
    the Qwen lineage" reading that mechanism's late-site null had left
    standing, confirming its own wrong-site-not-absent-mechanism hypothesis
    for llama specifically at the mid-band site)
- type: related_to
  target: '[[known-unknown-direction]]'
  target_id: term:known-unknown-direction
  confidence: medium
- type: related_to
  target: '[[llama-hs17-direction-specificity-survives-wide-instrument]]'
  target_id: mechanism:llama-hs17-direction-specificity-survives-wide-instrument
  confidence: high
  evidence:
  - experiments/llama-hs17-wide-instrument-rescore/AMENDMENT.md#outcome
    (extends this narrow-instrument finding to the wide two-instrument
    stack; resolved 2026-08-26)
---

Llama's hs17 mid-band write, the family's only write ever to clear a
held-out abstention floor, had no direction-specificity control until this
cell. Run against fifteen fresh matched-dose random directions, the gated
write's lift is 8.25 times the strongest random draw's lift, well above the
3.0 specificity floor, while the replication itself holds up under a fresh
decode seed (0.7282, consistent with the parent's 0.7420). Llama joins Qwen
as a family with a verified direction-specific selective write; the write
lives at a mid-band site rather than the family-ported late site that
`caution-encoding-read-actuate-dissociation-across-families` found
non-actuating, which is itself evidence for a wrong-site rather than
absent-mechanism reading of that earlier null.

**Lineage:** the write, gate, dose, and directions are frozen artifacts
reused verbatim from `j-space-cross-family-layer-contrast`'s resolved
(INCONCLUSIVE) llama arm. Source of truth:
`experiments/llama-hs17-direction-specificity/AMENDMENT.md`, Outcome
section, resolved 2026-08-25.
