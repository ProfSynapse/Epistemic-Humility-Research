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
cause: "HYPOTHESIS, UNTESTED: IF the network's early high-effective-dimensionality region (where each family's eff_dim_frac profile peaks, early-exterior in the outer ~15 percent of depth in all four families measured) is a high-dimensional deliberation and lexical-processing regime, and the known-unknown (KU), caution, and raw-refusal axes are not workspace-resident variables carried through that broadcast region but are instead late, low-dimensional summary statistics that crystallize only after the representation has compressed past its early peak."
effect: "THEN this would explain [[eff-dim-peak-decoupled-from-readable-band]] directly: the early eff_dim_frac peak marks the deliberation/lexical regime, and the three-axis read panel becomes linearly readable only in the mid-band that follows because that is where the low-dimensional epistemic summary has already formed, not where a high-dimensional workspace broadcast is still in flight. No resolved experiment gate has adjudicated this account; it remains one candidate reading among several left open by the atlas gates, which tested only the profile-peak-location and read-panel-AUROC limbs, not this interpretive question. Of the two originally named deflationary alternatives, the anisotropy or outlier-dimension estimator-artifact alternative has since been TESTED AND SURVIVED on gemma-4-e4b (experiments/gemma-4-e4b-family-atlas/NOTEBOOK.md, 2026-07-20 entry \"anisotropy-artifact control reanalysis\"): the layer-4 peak's LOCATION persists under whitening, top-1/2/4/8 covariance-eigendirection removal, 0.5 percent winsorizing, a rank-based spectral-entropy estimator, and a 50 percent row-subsample guard, though its PROMINENCE (margin over the best interior candidate) compresses from 1.53x baseline to 1.12x under the strongest correction, and the control has not yet been re-run on llama, mistral, or qwen3-4b. The pool surface-diversity alternative, where the eff_dim_frac estimator responds to token-level lexical variety that is naturally higher early in generation rather than to any workspace property, remains untested. A small-N-coincidence reading (three families was not yet a large sample) was under test via a qwen3-4b-family-atlas cell in preparation; that cell resolved 2026-07-21 and replicated the same early-exterior-peak-plus-healthy-mid-band shape as a fourth family, narrowing but not eliminating the small-N-coincidence reading. That cell adjudicated only the profile-peak-location and read-panel-AUROC limbs (the same atlas gates as the other three); it does not itself test the deliberation-then-summary interpretation named here, which remains unadjudicated."
polarity: explains
related:
- '[[eff-dim-peak-decoupled-from-readable-band]]'
- '[[j-space-mediated-actuation-fragility]]'
- '[[workspace-band-peak-location-is-family-relative]]'
- '[[global-workspace]]'
- '[[jspace-family-atlas]]'
- '[[gemma-4-e4b-family-atlas]]'
- '[[qwen3-4b-family-atlas]]'
- '[[propensity-direction-reads-but-does-not-actuate-fabrication]]'
- '[[setpoint-write-on-caution-perp-does-not-actuate-fabrication]]'
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
- type: related_to
  target: '[[qwen3-4b-family-atlas]]'
  target_id: experiment:qwen3-4b-family-atlas
  confidence: low
  note: "Fourth motivating observation (resolved 2026-07-21), not a test of this specific interpretation; the atlas gates adjudicated profile-peak location and read-panel AUROC only, and this hypothesis node's status stays untested."
- type: related_to
  target: '[[propensity-direction-reads-but-does-not-actuate-fabrication]]'
  target_id: mechanism:propensity-direction-reads-but-does-not-actuate-fabrication
  confidence: low
  status: proposed
  note: "Theoretical conjecture, not an identity claim: this use-the-signal null concerns the confabulation-propensity direction, a DIFFERENT fitted signal than the family-atlas read panel. The link asserts only that the same post-decision-summary account would explain both a readout that reads but does not actuate."
- type: related_to
  target: '[[setpoint-write-on-caution-perp-does-not-actuate-fabrication]]'
  target_id: mechanism:setpoint-write-on-caution-perp-does-not-actuate-fabrication
  confidence: low
  status: proposed
  note: "Theoretical conjecture, not an identity claim: this use-the-signal null concerns an unvalidated caution_perp setpoint write, a DIFFERENT fitted signal than the family-atlas read panel. The link asserts only explanatory scope, not that the two phenomena are the same."
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

This account is explicitly weighed against deflationary alternatives named in
`docs/atlas/family-layer-map.md`'s Cross-family pattern section. One of
these, the anisotropy or outlier-dimension estimator-artifact reading, was
tested directly on gemma-4-e4b on 2026-07-20
(`experiments/gemma-4-e4b-family-atlas/NOTEBOOK.md`, "anisotropy-artifact
control reanalysis") and survived: the layer-4 peak's location held under
eight separate correction variants (whitening, dropping the top-1/2/4/8
covariance eigendirections, winsorizing, a rank-based spectral-entropy
estimator, and a subsample guard), even though its prominence over the best
interior candidate compressed under the strongest correction. That control
has not yet been re-run on llama, mistral, or qwen3-4b. The pool
surface-diversity artifact (the `eff_dim_frac` estimator tracking lexical
variety rather than any workspace property) remains untested. The
small-N-coincidence reading was under test via a qwen3-4b-family-atlas cell
in preparation; that cell resolved 2026-07-21 as a fourth family
replicating the same early-exterior-peak-plus-healthy-mid-band shape
([[eff-dim-peak-decoupled-from-readable-band]]), narrowing but not
eliminating the small-N-coincidence reading. That resolution bears on the
decoupling's cross-family replication count only; it is not itself a test
of the deliberation-then-summary interpretation proposed here, which
remains unadjudicated and untested.

This node also links, as a low-confidence proposed conjecture rather than an
evidentiary claim, to two existing write-side "use the signal" null
mechanisms: [[propensity-direction-reads-but-does-not-actuate-fabrication]]
and [[setpoint-write-on-caution-perp-does-not-actuate-fabrication]] (from
`experiments/radial-anti-propensity-steering` and
`experiments/selected-setpoint-regulator`). Both concern a DIFFERENT fitted
signal, the confabulation-propensity direction and an unvalidated
caution_perp setpoint write, not the family-atlas read panel this hypothesis
was raised to explain. The link does not claim these are the same
phenomenon as the eff-dim/readable-band decoupling; it asserts only
explanatory scope, that IF the late-compression-summary account is correct,
a signal that reads cleanly but does not actuate is exactly the shape it
predicts, and these two nulls are additional, weaker, cross-signal instances
of that shape worth weighing against it, not confirmation of it.

Testing this hypothesis further would still need an experiment designed to
separate lexical-diversity confounds from a genuine deliberation-then-summary
staging account (the pool surface-diversity alternative). The
small-N-coincidence reading now has a fourth family
(qwen3-4b-family-atlas, resolved 2026-07-21) weighing against it, but this
node's own interpretive claim (deliberation-then-summary staging, not
workspace broadcast) is still unregistered and untested by any resolved
gate.
