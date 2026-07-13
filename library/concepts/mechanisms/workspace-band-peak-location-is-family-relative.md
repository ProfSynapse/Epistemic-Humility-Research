---
aliases:
- workspace band peak is family/size relative, not a portable depth constant
- early-exterior eff_dim_frac peak (jspace-family-atlas)
- per-family layer atlas requirement
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:workspace-band-peak-location-is-family-relative
  type: mechanism
  status: canonical
cause: "On two non-Qwen instruction-tuned families captured full-depth (Llama-3.2-3B-Instruct, Mistral-7B-Instruct-v0.3; jspace-family-atlas), the per-layer eff_dim_frac (representation-variance participation-ratio) profile peaks early-exterior rather than interior: llama at layer 4 of 28 (0.14 depth), mistral at layer 3 of 32 (0.09 depth). The interior three-axis readable band (doubt, caution, and raw-refusal all >= 0.80 held-out AUROC simultaneously) also sits at a different depth per family: llama layers 15-23 (best simultaneous read ~L20-23), mistral layers 7-27 (best ~L15-17)."
effect: "Neither the profile's peak layer nor the readable interior band is described by one ported depth fraction: Qwen's registered 0.94-depth late write site, and Qwen3-4B's own hs23-29 J-lens midband peak from a different JVP-based estimator, both land at different relative depths than either mapped family here. A per-family, per-size atlas run is needed before any future actuation amendment borrows a write or read layer, complicating any plan to port a single depth constant across the doubt-snap fleet's family panel."
polarity: complicates
related:
- '[[jspace-family-atlas]]'
- '[[j-space-mediated-actuation-fragility]]'
- '[[doubt-snap-cross-family-confirmatory]]'
- '[[global-workspace]]'
relationships:
- type: supported_by
  target: '[[jspace-family-atlas]]'
  target_id: experiment:jspace-family-atlas
  confidence: low
  evidence:
  - experiments/jspace-family-atlas/AMENDMENT.md#outcome
  - experiments/jspace-family-atlas/NOTEBOOK.md (2026-07-12 resolve entry)
- type: related_to
  target: '[[j-space-mediated-actuation-fragility]]'
  target_id: mechanism:j-space-mediated-actuation-fragility
  confidence: high
  evidence:
  - experiments/jspace-family-atlas/AMENDMENT.md (Motivation and posture)
- type: related_to
  target: '[[doubt-snap-cross-family-confirmatory]]'
  target_id: experiment:doubt-snap-cross-family-confirmatory
  confidence: medium
  evidence:
  - experiments/jspace-family-atlas/AMENDMENT.md (Motivation and posture, ported-layer critique)
- type: related_to
  target: '[[global-workspace]]'
  target_id: term:global-workspace
  confidence: medium
---

The doubt-snap cross-family fleet
([[doubt-snap-cross-family-confirmatory]]) measured every family's actuation
at a single ported depth fraction (`round(0.94 * (num_hidden_layers - 1))`,
copied from Qwen3-4B's working late layer). `jspace-family-atlas` supplied the
missing per-family map and found that the assumption behind that port does
not hold on either mapped family: the workspace-like `eff_dim_frac` profile
peaks near the front of the network rather than at an interior band, and the
band where the three read axes (doubt, caution, raw refusal) actually clear a
strong held-out threshold together sits at a different relative depth in each
family (llama mid-network, mistral spanning a wider mid-to-late range).

This is exploratory, low-confidence evidence from one experiment across two
families: it complicates rather than confirms
[[j-space-mediated-actuation-fragility]]'s general write/read-site-mismatch
account, by showing that even the mismatch's location is not itself portable
across families. It does not yet establish what, if anything, determines
where the band sits (depth, layer count, training recipe, or something else),
only that it moves. Any future per-family actuation amendment should treat
this atlas's layer map (llama ~L20-23, mistral ~L15-17) as an input to
consume, not a constant to extrapolate to a third family without its own
atlas run.
