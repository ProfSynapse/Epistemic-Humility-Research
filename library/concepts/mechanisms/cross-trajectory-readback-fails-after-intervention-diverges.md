---
aliases:
- on-vs-off readback breaks down once steering flips the argmax token
- post-divergence readback conflates the write with KV-cache drift
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:cross-trajectory-readback-fails-after-intervention-diverges
  type: mechanism
  status: canonical
cause: "In h6-genstream-hook-firing-check (H6), measuring the realized per-step write on the tuner plain-HF register_forward_hook path as the projection of hidden_ON minus hidden_ABSENT onto the unit write direction, at the same decode position index, across two SEPARATELY generated ON and ABSENT trajectories, evaluated at every instrumented decode position on all 25 pinned prompts (375 instrumented positions total)."
effect: "86 of 375 instrumented positions violate the registered 5% readback tolerance, failing the gate as written, but the failures are fully structured rather than a generic instrument fault: they occur only in the 10 of 25 prompts whose ON argmax token diverges from ABSENT at some decode position, every failing position lies at or after that prompt's own first divergence position (zero failures among the 277 pre-divergence positions, which read back 0.996-0.998 of the commanded write), and the worst post-divergence ratio is 1.95. Once the write flips a token, the ON and ABSENT trajectories condition on different KV-cache history from that position onward, so the hidden-state subtraction no longer isolates the per-step write alone; it also carries the accumulated divergence between two different generated prefixes. The hook fires per decode step and delivers the commanded write correctly before divergence; the metric, not the write, is what stops working."
polarity: complicates
related:
- '[[h6-genstream-hook-firing-check]]'
- '[[unsloth-for-inference-decode-bypasses-steering-hook]]'
- '[[activation-steering]]'
relationships:
- type: supported_by
  target: '[[h6-genstream-hook-firing-check]]'
  target_id: experiment:h6-genstream-hook-firing-check
  confidence: high
  evidence:
  - experiments/h6-genstream-hook-firing-check/AMENDMENT.md#outcome
- type: related_to
  target: '[[unsloth-for-inference-decode-bypasses-steering-hook]]'
  target_id: mechanism:unsloth-for-inference-decode-bypasses-steering-hook
  confidence: medium
  evidence:
  - experiments/h6-genstream-hook-firing-check/AMENDMENT.md#outcome
- type: related_to
  target: '[[activation-steering]]'
  target_id: method:activation-steering
  confidence: medium
---

The tuner plain-HF `register_forward_hook` path passed H6's firing gate
(exact one call per decode step, agreeing independent counters, on all 25
prompts) and its no-op gate (hidden and logits identical to the hook-absent
run when the commanded write is zero), but failed the write-fidelity gate as
registered. The failure is not evidence the hook mis-delivers the write: the
277 decode positions before any prompt's first behavioral divergence all
read back 0.996-0.998 of the commanded magnitude, comfortably inside the 5%
band.

The gate's own readback definition is what breaks: it subtracts an ABSENT
trajectory's hidden state from an ON trajectory's hidden state at the same
position INDEX, which silently assumes both trajectories still share the
same token prefix at that position. Once the steering intervention succeeds
at doing its job, flipping the argmax token, that assumption fails; the two
trajectories diverge in the tokens they condition on, and the subtraction
mixes the per-step write with whatever the model's own KV-cache history
contributes to the difference. This is a general lesson for any on-vs-off
readback built the same way
([[unsloth-for-inference-decode-bypasses-steering-hook]] documents the
companion failure mode, a hook that never fires at all): a divergence-robust
successor design needs a readback that isolates the write under a shared
prefix, for example teacher-forcing both the ON and ABSENT passes over the
same tokens, rather than comparing two independently generated trajectories
position-by-position.
