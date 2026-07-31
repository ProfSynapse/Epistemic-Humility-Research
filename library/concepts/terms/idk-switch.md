---
title: IDK switch
aliases:
- IDK switch (earned actuator name)
- caution write (earned name, formerly working label)
- named caution-write actuator at Qwen3.5-4B hs20
tags:
- kg/term
- concept
- term
kg:
  id: term:idk-switch
  type: term
  status: canonical
area: terms
related:
- '[[known-unknown-direction]]'
- '[[caution-write-mode-switches-prose-to-explicit-idk]]'
- '[[caution-write-idk-jump-replicates-under-fresh-sampled-decode-seeds]]'
- '[[idk-switch-naming-confirmatory]]'
- '[[qwen35-4b-midband-doubt-snap]]'
relationships:
- type: derived_from
  target: '[[known-unknown-direction]]'
  target_id: term:known-unknown-direction
  confidence: high
  evidence:
  - experiments/idk-switch-naming-confirmatory/AMENDMENT.md (Design; c_hat and
    random_direction loaded byte-identical from qwen35-4b-midband-doubt-snap's
    committed directions/hs20/ tree -- the same frozen mid-band hs20 direction,
    used here as a write/dosed actuator rather than a read-side projection)
- type: related_to
  target: '[[caution-write-mode-switches-prose-to-explicit-idk]]'
  target_id: mechanism:caution-write-mode-switches-prose-to-explicit-idk
  confidence: high
  evidence:
  - experiments/idk-switch-naming-confirmatory/AMENDMENT.md (Motivation and
    posture; the behavioral mode-switch this name describes, first read
    exploratorily on the naming battery's frozen Arm A generations)
- type: supported_by
  target: '[[caution-write-idk-jump-replicates-under-fresh-sampled-decode-seeds]]'
  target_id: mechanism:caution-write-idk-jump-replicates-under-fresh-sampled-decode-seeds
  confidence: high
  evidence:
  - experiments/idk-switch-naming-confirmatory/AMENDMENT.md#outcome (all three
    name-earning gates PASS on fresh sampling seeds and sampled decode)
- type: supported_by
  target: '[[idk-switch-naming-confirmatory]]'
  target_id: experiment:idk-switch-naming-confirmatory
  confidence: high
  evidence:
  - "experiments/idk-switch-naming-confirmatory/AMENDMENT.md#outcome (verdict:
    the name IDK switch is EARNED at the Qwen3.5-4B hs20 operating point)"
---

IDK switch is the earned name for the frozen Qwen3.5-4B hs20 `c_hat`
write direction and dose law (the same direction underlying
[[known-unknown-direction]], applied here as a causal write actuator rather
than a read-side projection) at the operating point established by
[[qwen35-4b-midband-doubt-snap]]. The PI adopted "IDK switch" as a
descriptive working label on 2026-07-31 after
[[caution-write-mode-switches-prose-to-explicit-idk]] showed the write
converts prose output of every form, committed and hedged alike, wholesale
into explicit IDK rather than producing graded hedging. The label was
promoted from a descriptive lowercase name to an earned actuator name only
after `idk-switch-naming-confirmatory` confirmed the mode switch on FRESH
sampling seeds and sampled (not greedy) decode and additionally cleared two
further pre-registered legs beyond the original mode-switch question: an
endpoint IDK-rate jump whose paired-bootstrap CI clears a pre-set floor by
3.8x, and direction specificity (a random-direction placebo staying within a
pre-set band of baseline)
([[caution-write-idk-jump-replicates-under-fresh-sampled-decode-seeds]]).

**Naming caveat:** the name describes a validated BEHAVIORAL actuator --
dosing this direction converts prose to explicit IDK, direction-specifically,
at this exact operating point (Qwen3.5-4B, hs20, the frozen dose calibration
from `qwen35-4b-midband-doubt-snap`) -- and carries no claim about the
model's internal epistemic state, generalization to other layers, doses, or
model families, or graded control over hedging: axis G's own resolution is
that there is no graded intermediate to control, only a binary switch.
