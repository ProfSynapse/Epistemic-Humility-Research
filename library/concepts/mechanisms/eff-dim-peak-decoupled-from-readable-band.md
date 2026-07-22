---
aliases:
- effective-dimensionality peak precedes the readable epistemic band
- early-exterior eff_dim_frac peak is decoupled from the mid-band read panel
- four-of-four cross-family decoupling of workspace-peak and readable-band location
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:eff-dim-peak-decoupled-from-readable-band
  type: mechanism
  status: canonical
cause: "On four families captured full-depth with the same capture-only instrument (jspace-family-atlas: Llama-3.2-3B-Instruct, Mistral-7B-Instruct-v0.3; gemma-4-e4b-family-atlas: Gemma-4-E4B-it; qwen3-4b-family-atlas: raw-base Qwen3-4B), the per-layer eff_dim_frac (representation-variance participation-ratio) profile peaks early-exterior, in the outer ~15 percent of depth, in all four: llama layer 4 of 28 (0.14 depth), mistral layer 3 of 32 (0.09 depth), gemma-4-e4b hs_index 4 of 42 (0.095 depth), qwen3-4b hs_index 5 of 36 (0.139 depth). The profile then declines through the mid-band in every family rather than staying elevated."
effect: "The three-axis read panel (the known-unknown [KU, labeled `doubt` in the read panel] axis, caution, and raw refusal all clearing 0.80 held-out AUROC simultaneously) becomes readable only in a band that opens AFTER the dimensionality profile has already collapsed from its early peak, not at the peak itself: llama layers 15-23, mistral layers 7-27, gemma-4-e4b a contiguous hs_index 13-42 band (hs_index 4-6 also clear it marginally before a dip at hs_index 7-12), qwen3-4b hs_index 22-36 (at the qwen3-4b profile's own peak, hs5, caution and raw_refusal both read below 0.80). No family shows the registered prediction of an interior eff_dim_frac peak coincident with the readable band; readability begins only in the compression regime that follows the peak, not during it. On qwen3-4b this decoupling also confirms the same instrument dissociation directly on the substrate the site-mismatch mechanism ([[j-space-mediated-actuation-fragility]]) was originally built from: the eff_dim_frac peak (hs5) does not reproduce j-space-localization-qwen3-4b's JVP-based J-lens peak (hs23-29) on the same checkpoint, and the readable band (hs22-36) sits on the J-lens band instead. This decoupling has now replicated 4 of 4 times across three atlas experiments, though each atlas remains individually low-confidence exploratory evidence and the falsifier's own wording only anticipated monotone-to-last-layer or no-readable-band failure shapes, not this early-exterior-peak-plus-healthy-mid-band shape."
polarity: decouples
related:
- '[[jspace-family-atlas]]'
- '[[gemma-4-e4b-family-atlas]]'
- '[[qwen3-4b-family-atlas]]'
- '[[workspace-band-peak-location-is-family-relative]]'
- '[[j-space-mediated-actuation-fragility]]'
- '[[global-workspace]]'
- '[[epistemic-readouts-are-late-compression-summaries]]'
relationships:
- type: supported_by
  target: '[[jspace-family-atlas]]'
  target_id: experiment:jspace-family-atlas
  confidence: low
  evidence:
  - experiments/jspace-family-atlas/AMENDMENT.md#outcome
- type: supported_by
  target: '[[gemma-4-e4b-family-atlas]]'
  target_id: experiment:gemma-4-e4b-family-atlas
  confidence: low
  evidence:
  - experiments/gemma-4-e4b-family-atlas/AMENDMENT.md#outcome
  - experiments/gemma-4-e4b-family-atlas/NOTEBOOK.md (2026-07-20 entry, "anisotropy-artifact control reanalysis")
  - experiments/gemma-4-e4b-family-atlas/analysis-committed/gemma4_e4b_it/anisotropy_control/
- type: supported_by
  target: '[[qwen3-4b-family-atlas]]'
  target_id: experiment:qwen3-4b-family-atlas
  confidence: low
  evidence:
  - experiments/qwen3-4b-family-atlas/AMENDMENT.md#outcome
- type: related_to
  target: '[[workspace-band-peak-location-is-family-relative]]'
  target_id: mechanism:workspace-band-peak-location-is-family-relative
  confidence: high
  evidence:
  - docs/atlas/family-layer-map.md (Cross-family pattern section)
  note: "That node names WHERE each family's peak and band sit (family-relative depth); this node names the standing RELATIONSHIP between the two locations (decoupled, not coincident) as a distinct claim in its own right."
- type: related_to
  target: '[[j-space-mediated-actuation-fragility]]'
  target_id: mechanism:j-space-mediated-actuation-fragility
  confidence: medium
  evidence:
  - experiments/jspace-family-atlas/AMENDMENT.md (Motivation and posture)
- type: related_to
  target: '[[global-workspace]]'
  target_id: term:global-workspace
  confidence: medium
- type: explained_by
  target: '[[epistemic-readouts-are-late-compression-summaries]]'
  target_id: mechanism:epistemic-readouts-are-late-compression-summaries
  confidence: low
  status: proposed
  note: "Candidate interpretation, not yet adjudicated by any resolved gate; see that node's own hypothesis-status marking."
---

Three family-atlas experiments measured the same two quantities, per layer,
on four instruction-tuned or raw-base families: `eff_dim_frac` (a
representation-variance participation-ratio profile) and a held-out
three-axis read panel (the known-unknown axis, caution, and raw refusal).
Each family's registered prediction was that the two would coincide, an
interior band where `eff_dim_frac` peaks and is also where the three axes
read well, consistent with a workspace-like broadcast region. That
prediction failed identically in all four families measured so far.

Instead, the `eff_dim_frac` peak sits early-exterior (llama 0.14 depth,
mistral 0.09 depth, gemma-4-e4b 0.095 depth, qwen3-4b 0.139 depth), and the
profile then declines. The readable band opens later, in the mid-network
compression regime that follows the peak's collapse, not during the peak
itself. The two properties are decoupled rather than coincident: high
effective dimensionality and strong held-out epistemic readability occur at
different depths in every family tried. [[workspace-band-peak-location-is-family-relative]]
establishes that the absolute and relative depth of each location differs
family to family; this node names the separate, replicated claim that
WHEREVER the peak sits for a given family, the readable band does not sit
there too, it sits downstream of it. `qwen3-4b-family-atlas` adds a second
confirmation on the same substrate `j-space-mediated-actuation-fragility` was
built from: its own `eff_dim_frac` peak (hs5) does not land on
`j-space-localization-qwen3-4b`'s JVP-based J-lens peak (hs23-29) on the
identical checkpoint, and the readable band (hs22-36) sits on the J-lens band
instead, so the decoupling is not an artifact of comparing different
substrates.

This is exploratory, low-confidence evidence from four families across three
atlas experiments, with the registered falsifier not cleanly anticipating
this exact failure shape (an instrument-wording gap recorded straight in the
resolved `AMENDMENT.md` docs). A PI-directed deflationary control on
gemma-4-e4b, run 2026-07-20 (`experiments/gemma-4-e4b-family-atlas/NOTEBOOK.md`,
"anisotropy-artifact control reanalysis"), asked whether outlier
eigendirections were manufacturing the layer-4 peak rather than a genuine
early-exterior maximum. The peak's LOCATION survived all eight correction
variants tried: whitening by the correlation matrix, dropping the top-1, -2,
-4, and -8 covariance eigendirections, 0.5 percent winsorizing, a rank-based
spectral-entropy estimator (a different estimator family), and a 50 percent
row-subsample guard. Correcting for anisotropy only compressed the peak's
margin over the best interior candidate, from 1.53x at baseline to 1.12x
under the strongest correction, and never relocated it; the notebook records
the caveat that the peak's PROMINENCE partly rides on early-layer isotropy
even though its LOCATION does not. This is one deflationary alternative
tested and survived, on gemma-4-e4b specifically (not yet re-run on llama,
mistral, or qwen3-4b); the pool surface-diversity alternative remains open.
`qwen3-4b-family-atlas`, resolved 2026-07-21, is the fourth family registered
against the small-N-coincidence reading named below; it replicated the same
shape rather than breaking the pattern, weakening but not eliminating that
alternative (a fourth data point narrows, it does not close, a
small-N-coincidence reading). What, if anything, causally explains the
decoupling itself is still not settled by the atlas gates; see
[[epistemic-readouts-are-late-compression-summaries]] for one untested
candidate account and the remaining deflationary alternatives it is weighed
against.
