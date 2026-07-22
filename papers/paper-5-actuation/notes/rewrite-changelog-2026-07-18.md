# Paper 5 rewrite changelog (2026-07-18)

Executed against `docs/preparation/paper5-rewrite-spec.md` on branch
`paper/paper5-rewrite`. This log records what changed per section for lead
review; the writer's full completion table and evidence citations are in the
final agent report, not duplicated here.

## Frontmatter / title

- Added an HTML comment block at the top of the manuscript with three title
  candidates (spec section 3 ruling 1) and a rationale for each. Working
  title set to candidate 1, a minimal-diff swap of "Epistemic State" for
  "Known-Unknown State" in the existing title, chosen to preserve the
  cross-references from papers 3 and 4 that link against the current title
  text. If the PI picks a different candidate at PR time, those two
  cross-reference links need a follow-up fix; not done here (out of this
  worktree's scope).
- Added a scope-note paragraph immediately after the H1 heading defining
  "epistemic state" as a readout-level term, not a mental-state claim, and
  stating the known-unknown (KU) vocabulary substitution up front.
- Extended `evidence_base` in the frontmatter to list the ten evidence docs
  this rewrite newly cites.

## Abstract

- Rewrote the selectivity-attribution paragraph as operating-point-dependent:
  kept the registered 73.5%/3.1% headline, added the overdrive-regime
  contrast (60.1% vs 3.1% known-correct damage, `ungated-vs-gated-dose-matched`)
  and the mid-band factorial numbers (permuted-gate confab abstention
  0.550/0.600, Gap_Sel 0.148/0.129 sub-floor, `gate-contribution-factorial`).
  Added a naming sentence adopting KU vocabulary.

## Introduction

- Rule 2 rewritten as regime-conditional: gate essential at overdrive, write
  self-sorts at mid-band with the gate reduced to increment plus cost
  governance.

## Methods (Section 3)

- 3.2 "Readouts and directions": renamed doubt projection / doubt direction
  to known-unknown (KU) projection / direction.

## Results (Section 4)

- 4.2: renamed "doubt axis" to "known-unknown direction".
- 4.4: retitled to flag the regime-dependence; inserted the registered
  60.1%/3.1% overdrive contrast (replacing no unregistered diagnostic was
  present in this section to begin with, but the contrast is now stated
  here explicitly per the spec's Section 4.4 MUST item); renamed doubt gate
  to KU readout gate throughout; added a "Robustness update" paragraph with
  the mid-band held-out transfer (0.678/0.977/0.039) and the sampled-decode
  seed-robustness replication (69.5% pooled, cost 4.65%), noting supersession
  of the 2026-07-10 audit's H2/H3 items.
- 4.5: renamed "doubt direction" to "known-unknown direction" in the
  verbalization finding; added a sentence promoting that observation as
  prescient corroboration of the later naming finding
  (`margin-evidence-responsiveness-worldknown`).
- 4.7: relabeled the AQ sycophancy screen as an unsigned interim pilot
  (its experiment.yaml status is still `draft`), not a governed result.
- 4.8: renamed "doubt-gated caution write" to "KU-gated caution write".
- 4.9: added a sentence in the Interpretation noting the mid-band factorial's
  S1 leg (ratio 2.03) as a third, independent mistral direction-specificity
  failure alongside RR2 and RR3.
- 4.10: renamed "doubt-coupling" to "KU-readout coupling" and reworded the
  "represented doubt" phrase to "represented known-unknown state" in the
  "two routes to abstention" bullet; added a new paragraph on the
  within-kuq subtype breakdown (`placebo-signflip-question-type-analysis`)
  showing the future-unknown subtype carries qwen's entire suppression and
  is also mistral's largest recruitment delta.

## Synthesis map (Section 5)

- Split the "Unconditional caution write" / "Doubt-gated caution snap" rows
  into three rows: an overdrive-regime unconditional-write row, an
  overdrive-regime KU-gated-snap row, and a new mid-band-regime KU-gated-snap
  row (permuted-gate near-parity, sub-floor Gap_Sel and cost-protection).
- Relabeled the J-space write row to flag it is about layer site, not dose
  regime, to avoid overloading "mid-band".
- Reworded the mistral row per PI ruling 2: three independent
  direction-specificity failures (RR2, RR3, factorial S1), the factorial's
  own sub-floor gate contribution, and the cross-family confirmatory's true
  behavioral null (0/874), while keeping the reproduced benefit/cost gates
  and the census placebo-sign resolution.

## Discussion (Section 6)

- 6.2 retitled and rewritten around the same two-regime mechanism, with the
  known false-refusal contrast (0.042/0.005 true gate vs 0.050/0.039
  permuted) against the registered 0.05 ceiling.
- 6.3 retitled and rewritten to scope the J-space account to raw-base
  Qwen3-4B: added `jspace-family-atlas`'s finding that eff_dim_frac peaks
  early (not interior) in both llama and mistral, while the read panel still
  delivers a usable per-family interior band.
- 6.4: added a new limits bullet on the coherence/saturation ceiling (51/400
  world-known confabs tippable, 12.75%; doses >=3x degenerate before refusal;
  scoped to the hs20 lineage, L34 untested for it) and one forward-pointer
  sentence to the successor margin-theory paper, with no margin-cell numbers.
- 6.5 item 3: replaced the closing framing (llama's snap "remains completely
  untested") with a new item 4 reporting the resolved not-promoted verdict
  of `doubt-snap-cross-family-confirmatory`: every cell stopped at FIT
  dose-viability, the caution encoding reads everywhere but the write only
  actuates in the Qwen lineage at tested sites, framed per PI ruling 3
  ("readable everywhere, actuable only in the Qwen lineage at tested
  sites"); queued per-family atlas retests are noted as queued work, not
  blockers.

## Conclusion (Section 7)

- Rewrote to state the two-regime mechanism explicitly instead of a single
  universal "read doubt, fire selectively" sentence; renamed "doubt" to
  "known-unknown state" throughout.

## Appendix A

- Renamed claim-text (not filenames) using KU vocabulary in two existing
  rows.
- Added nine new traceability rows for: `ungated-vs-gated-dose-matched`,
  `qwen35-4b-midband-doubt-snap`, `qwen35-4b-midband-heldout`,
  `snap-seed-sampled-decode-replication`, `gate-contribution-factorial`,
  `jspace-family-atlas`, `doubt-snap-cross-family-confirmatory`,
  `placebo-signflip-question-type-analysis`, and
  `evidence-response-direction-search`.
- Relabeled the AQ sycophancy row's status to "Unsigned interim pilot".

## Not done / deferred (NICE items, lowest priority per spec)

- The 2026-07-10 audit's remaining spine items (AL, AN/AO caveat, rep1/rep2
  evidential tiers, prediction/falsifier layer, frontmatter/appendix
  normalization beyond what is listed above) were not executed: the writer
  did not have the audit document's specific item list in the evidence
  bundle handed to it, and the spec marks this NICE/lowest priority.
- No standalone whole-file voice pass (bold run-ins, c_hat prose in body,
  journey narration) was performed; voice cleanup was applied only within
  paragraphs already being rewritten for MUST/SHOULD content, per the
  spec's explicit instruction not to let a standalone voice pass consume
  budget ahead of MUST/SHOULD items.

## Post-red-team remediation (lead, 2026-07-18)

Red-team verdict: RESOLVE WITH DISCLOSURES (0 blockers, 1 major, 2 minor).
All ~90 numeric claims traced to their Outcome docs and matched; all six
thesis sites verified two-regime; PI rulings verified in place. Fixes:

1. MAJOR: added experiments/placebo-seed-distribution-census/AMENDMENT.md to
   the frontmatter evidence_base (flagship source of 4.10, was omitted).
2. minor: replaced the writer-interpolated "near the 80th percentile" with
   the census doc's own numbers (above the upper quartile; IQR
   [-9.33, -2.00], median -7.67; AMENDMENT.md line 437).
3. minor: abstract mid-band parenthetical now states both families'
   operating points (qwen hs20 dose_abs 12.608; mistral hs16 dose_abs 3.665
   per gate-contribution-factorial AMENDMENT.md line 252).
