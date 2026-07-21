---
aliases:
- consolidation/crystallization account of the eff-dim/readable-band decoupling
- epistemic axes as late low-dimensional compression summaries, not workspace variables
- HYPOTHESIS - not yet tested
tags:
- kg/mechanism
- concept
- mechanism
- hypothesis
kg:
  id: mechanism:epistemic-readouts-are-late-compression-summaries
  type: mechanism
  status: canonical
cause: "HYPOTHESIS, UNTESTED: IF the network's early high-effective-dimensionality region (where each family's eff_dim_frac profile peaks, early-exterior in the outer ~15 percent of depth in all three families measured) is a high-dimensional deliberation and lexical-processing regime, and the known-unknown (KU), caution, and raw-refusal axes are not workspace-resident variables carried through that broadcast region but are instead late, low-dimensional summary statistics that crystallize only after the representation has compressed past its early peak."
effect: "THEN this would explain [[eff-dim-peak-decoupled-from-readable-band]] directly: the early eff_dim_frac peak marks the deliberation/lexical regime, and the three-axis read panel becomes linearly readable only in the mid-band that follows because that is where the low-dimensional epistemic summary has already formed, not where a high-dimensional workspace broadcast is still in flight. No resolved experiment gate has adjudicated this account; it is one candidate reading among at least three left open by the atlas gates, which tested only the profile-peak-location and read-panel-AUROC limbs, not this interpretive question. The two named deflationary alternatives, equally untested: (a) a pool surface-diversity artifact, where the eff_dim_frac estimator responds to token-level lexical variety that is naturally higher early in generation, rather than to any workspace property; and (b) an anisotropy or outlier-dimension estimator artifact in the participation-ratio computation itself, a known failure mode of variance-based dimensionality estimators on transformer residual streams. A small-N-coincidence reading (three families is not yet a large sample) is also not ruled out."
polarity: explains
related:
- '[[eff-dim-peak-decoupled-from-readable-band]]'
- '[[j-space-mediated-actuation-fragility]]'
- '[[workspace-band-peak-location-is-family-relative]]'
- '[[global-workspace]]'
- '[[jspace-family-atlas]]'
- '[[gemma-4-e4b-family-atlas]]'
relationships:
- type: explains
  target: '[[eff-dim-peak-decoupled-from-readable-band]]'
  target_id: mechanism:eff-dim-peak-decoupled-from-readable-band
  confidence: low
  status: proposed
  evidence:
  - docs/atlas/family-layer-map.md (Cross-family pattern section, "Interpretation beyond these four observations ... is NOT settled by this table")
- type: related_to
  target: '[[j-space-mediated-actuation-fragility]]'
  target_id: mechanism:j-space-mediated-actuation-fragility
  confidence: low
- type: related_to
  target: '[[workspace-band-peak-location-is-family-relative]]'
  target_id: mechanism:workspace-band-peak-location-is-family-relative
  confidence: low
- type: related_to
  target: '[[global-workspace]]'
  target_id: term:global-workspace
  confidence: low
- type: related_to
  target: '[[jspace-family-atlas]]'
  target_id: experiment:jspace-family-atlas
  confidence: low
  note: "Motivating observation, not a test of this specific interpretation; the atlas gates adjudicated profile-peak location and read-panel AUROC only."
- type: related_to
  target: '[[gemma-4-e4b-family-atlas]]'
  target_id: experiment:gemma-4-e4b-family-atlas
  confidence: low
  note: "Motivating observation, not a test of this specific interpretation; the atlas gates adjudicated profile-peak location and read-panel AUROC only."
---

**Status: hypothesis, untested.** This node records a candidate
interpretation raised after the fact by the cross-family decoupling result,
not a finding adjudicated by any resolved experiment gate. It exists so the
interpretation is not lost, and so it can be tested and either promoted or
retired by a future amendment rather than silently assumed true in later
prose.

The account: the epistemic axes read by the family-atlas panel (the
known-unknown [KU] axis, caution, and raw refusal) are late, low-dimensional
summary variables that emerge only once the representation has compressed
past an early, high-dimensional deliberation regime, rather than being
workspace variables resident IN that high-dimensional region. Under this
reading, [[eff-dim-peak-decoupled-from-readable-band]] is not a coincidence
or an artifact: the early `eff_dim_frac` peak and the later readable band are
different processing stages, surface/lexical deliberation first, epistemic
summarization after, and no family should be expected to show them at the
same depth.

This account is explicitly weighed against two deflationary alternatives
named in `docs/atlas/family-layer-map.md`'s Cross-family pattern section, and
none of the three is currently distinguished: a pool surface-diversity
artifact (the `eff_dim_frac` estimator tracking lexical variety rather than
any workspace property), and an anisotropy or outlier-dimension artifact in
the participation-ratio computation itself. A small-N-coincidence reading is
also live at three families. Testing this hypothesis would need an
experiment designed to separate lexical-diversity confounds and estimator
anisotropy from a genuine deliberation-then-summary staging account, which
has not been registered as of this writing.
