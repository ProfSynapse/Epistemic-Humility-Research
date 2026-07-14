---
title: doubt-snap-cross-family-confirmatory
aliases:
- doubt-gated caution snap cross-family confirmatory replication
tags:
- kg/experiment
- experiment
- cross-family
- doubt-snap
kg:
  id: experiment:doubt-snap-cross-family-confirmatory
  type: experiment
  status: canonical
related:
- '[[qwen35-late-site-entangles-refusal-and-format-collapse]]'
- '[[steering-dose-windows-are-absolute-not-sigma-transferable]]'
- '[[qwen35-batch-composition-flips-greedy-decode-outcomes]]'
- '[[caution-encoding-read-actuate-dissociation-across-families]]'
- '[[qwen35-4b-midband-doubt-snap]]'
- '[[workspace-band-peak-location-is-family-relative]]'
relationships:
- type: supports
  target: '[[qwen35-late-site-entangles-refusal-and-format-collapse]]'
  target_id: mechanism:qwen35-late-site-entangles-refusal-and-format-collapse
  confidence: high
  evidence:
  - experiments/doubt-snap-cross-family-confirmatory/NOTEBOOK.md (2026-07-09 and 2026-07-10 entries)
  - experiments/doubt-snap-cross-family-confirmatory/AMENDMENT.md#outcome
- type: supports
  target: '[[caution-encoding-read-actuate-dissociation-across-families]]'
  target_id: mechanism:caution-encoding-read-actuate-dissociation-across-families
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
  target: '[[workspace-band-peak-location-is-family-relative]]'
  target_id: mechanism:workspace-band-peak-location-is-family-relative
  confidence: medium
  evidence:
  - experiments/doubt-snap-cross-family-confirmatory/AMENDMENT.md#outcome
- type: supports
  target: '[[steering-dose-windows-are-absolute-not-sigma-transferable]]'
  target_id: mechanism:steering-dose-windows-are-absolute-not-sigma-transferable
  confidence: high
  evidence:
  - experiments/doubt-snap-cross-family-confirmatory/NOTEBOOK.md (2026-07-09 entry)
- type: supports
  target: '[[qwen35-batch-composition-flips-greedy-decode-outcomes]]'
  target_id: mechanism:qwen35-batch-composition-flips-greedy-decode-outcomes
  confidence: high
  evidence:
  - experiments/doubt-snap-cross-family-confirmatory/NOTEBOOK.md (2026-07-08 12:20 and 08:55 entries)
---

Registered cross-family confirmatory replication of the resolved Qwen3-4B
doubt-gated-caution-tighten mechanism (a doubt-threshold gate plus a
caution-direction snap) across a Llama / Mistral-Ministral / Qwen3.5 / Gemma
small-and-mid-tier family panel, with FIT-only direction/tau/dose selection
per model and held-out G1/G2/G3 scoring.

Resolved 2026-07-12. **The confirmatory cross-family claim is NOT promoted.**
No cell reached held-out scoring: every launched cell (qwen35_4b, qwen35_9b,
llama32_3b_instruct, mistral7b_instruct_v03) stopped at the registered
pre-outcome G0 FIT dose-viability rule at the ported 0.94-depth write site
(FIT clean_tighten peaks 0.326/0.058/0.184/0.000 respectively), and the user
then decided in-conversation to launch no further cells because the
registered prediction (at least 3 of 4 small-tier families passing held-out
G1/G2/G3) was already arithmetically unreachable.
`gemma4_e4b` and the remaining mid-tier cells were never launched;
`gemma3_12b` was access-blocked before launch. The registered falsifier, as
written over held-out G1/G2/G3 fails, cannot fire on a fleet that stops at
G0: the result lands between the registered prediction and falsifier, in
territory neither anticipated.

Two pieces of registered-adjacent evidence, both cited in the Outcome as
context rather than pooled with this result, adjudicate between "the
mechanism does not transfer to these families" and "the registered write
site is wrong": a lead-verified c_hat validity audit over the fleet's own
captures found the caution direction reads well (AUROC 0.84-0.99) in all
four launched cells, yet the ported late write site actuates behavior
strongly only on Qwen lineage, weakly on llama, and not at all on mistral
([[caution-encoding-read-actuate-dissociation-across-families]]); and the
same-substrate `qwen35-4b-midband-doubt-snap` (resolved separately) shows
that moving the write to a mid-band layer on Qwen3.5-4B recovers a coherent
decoupling window the late site never reaches. The ported cross-family layer
rule (`round(0.94*(num_hidden_layers-1))`, copied unmodified from Qwen3-4B)
is the design element these results indict: `jspace-family-atlas`
independently found that readable interior structure sits at family-relative
depths (llama layers 15-23, mistral layers 7-27) rather than a universal
depth fraction ([[workspace-band-peak-location-is-family-relative]]). Any
successor cross-family actuation amendment should site writes per family
from a layer atlas and register exterior-shaped outcomes in both prediction
and falsifier so a uniform G0 stop cannot fall between them again. Source of
truth: `experiments/doubt-snap-cross-family-confirmatory/AMENDMENT.md` and
`NOTEBOOK.md`.
