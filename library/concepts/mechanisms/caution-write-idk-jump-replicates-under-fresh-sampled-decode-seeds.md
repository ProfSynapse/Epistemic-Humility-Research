---
aliases:
- fresh-seed sampled-decode replication confirms the IDK mode switch
- endpoint IDK jump +0.6125, CI lower bound 0.5650 vs a 0.15 floor
- placebo direction-specificity confirmed within a 0.05 band
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:caution-write-idk-jump-replicates-under-fresh-sampled-decode-seeds
  type: mechanism
  status: canonical
cause: "Dosing the frozen Qwen3.5-4B hs20 c_hat write direction to 1.0x over the naming battery's registered 400-row P_CONFAB population, regenerated under a FRESH sampling seed (generation_sampling_seed 20260802) and sampled decode (temperature 0.7, top_p 0.9, do_sample true) rather than the naming battery's original greedy Arm A generations, graded by the same validated blinded judge lane and the deterministic F4 (explicit IDK) / F5 (degenerate) screens."
effect: "The F4 explicit-IDK rate jumps from 0.0375 (15/400) at baseline to 0.6500 (260/400) at 1.0x dose, a difference of +0.6125 whose paired-bootstrap 95% CI [0.5650, 0.6600] clears a pre-registered 0.15 floor by 3.8x, replicating the naming battery's exploratory +0.6275 endpoint jump under fresh seeds and sampled decode. Over the same ladder the judged F2+F3 hedged share among non-degenerate rows falls monotonically (baseline 0.4150, 0.5x dose 0.2600, 1.0x dose 0.1629) rather than rising, so no graded hedging intermediate appears at either c_hat-dosed arm. A random-direction placebo arm's F4 rate (0.0150) stays within a pre-registered 0.05 band of baseline (diff 0.0225), so the jump is specific to the c_hat direction rather than an artifact of dosing per se. All three pre-registered name-earning gates (endpoint jump, no graded intermediate, direction specificity) pass together, which is what promotes the working label 'IDK switch' to an earned actuator name at this operating point rather than merely re-observing the exploratory mode switch."
polarity: enables
related:
- '[[idk-switch-naming-confirmatory]]'
- '[[caution-write-mode-switches-prose-to-explicit-idk]]'
- '[[idk-switch]]'
- '[[write-direction-naming-battery]]'
relationships:
- type: supported_by
  target: '[[idk-switch-naming-confirmatory]]'
  target_id: experiment:idk-switch-naming-confirmatory
  confidence: high
  evidence:
  - experiments/idk-switch-naming-confirmatory/AMENDMENT.md#outcome (N1 PASS
    +0.6125 CI [0.5650, 0.6600]; N2 PASS falling hedged share at both dosed
    arms; N3 PASS placebo diff 0.0225 within the 0.05 band)
- type: related_to
  target: '[[caution-write-mode-switches-prose-to-explicit-idk]]'
  target_id: mechanism:caution-write-mode-switches-prose-to-explicit-idk
  confidence: high
  evidence:
  - experiments/idk-switch-naming-confirmatory/AMENDMENT.md (Motivation and
    posture; confirmatory fresh-seed sampled-decode replication of this
    exploratory mode-switch finding, established on the naming battery's
    frozen Arm A greedy generations)
- type: related_to
  target: '[[idk-switch]]'
  target_id: term:idk-switch
  confidence: high
  evidence:
  - experiments/idk-switch-naming-confirmatory/AMENDMENT.md#outcome (the name
    IDK switch is EARNED for this actuator at the pinned Qwen3.5-4B hs20
    operating point)
- type: related_to
  target: '[[write-direction-naming-battery]]'
  target_id: experiment:write-direction-naming-battery
  confidence: medium
  evidence:
  - experiments/idk-switch-naming-confirmatory/AMENDMENT.md (Motivation and
    posture; regenerates that cell's registered P_CONFAB population at its
    frozen operating point)
---

*Legacy naming note (2026-08-16): this note's title/slug predates the program's vocabulary rename; see `papers/common/terminology.md` for current running-prose terms (known-unknown direction, KU readout gate, refusal axis, KU-readout coupling, IDK switch). The slug stays verbatim under usage rule 1.*

Confirmatory replication, under fresh sampling seeds and sampled (not greedy)
decode, of the exploratory mode-switch finding first read on the naming
battery's frozen Arm A generations
([[caution-write-mode-switches-prose-to-explicit-idk]]). That mechanism
resolved the graded-vs-binary axis-G question alone (does intermediate
dosing produce graded hedging or a binary IDK switch); this replication adds
two further pre-registered legs on fresh generations: the endpoint magnitude
of the IDK jump (with a paired-bootstrap CI clearing a pre-set floor by
3.8x) and direction specificity (a random-direction placebo staying within a
pre-set band of baseline). All three legs passing together under a different
sampling seed and a different decode mode is what promotes the actuator's
working label from a descriptive lowercase name to an earned name
([[idk-switch]]), rather than re-observing the same exploratory number a
second time.

**Why it matters here:** this is the specific replication evidence the
program's confirmatory-promotion rule requires before an exploratory naming
result can become a claim; it is reported separately from
`caution-write-mode-switches-prose-to-explicit-idk` because it carries
statistics (the endpoint CI, the placebo band) that mechanism's own
axis-G-only resolution never computed.
