---
title: Boundary Anisotropy
aliases:
- boundary anisotropy
- direction-specificity of the abstention boundary
- anisotropy index
tags:
- kg/term
- concept
- term
kg:
  id: term:boundary-anisotropy
  type: term
  status: canonical
area: terms
related:
- '[[gate-contribution-factorial]]'
- '[[placebo-seed-distribution-census]]'
- '[[matched-magnitude-placebo-sign-survives-as-distributional-property]]'
- '[[random-direction-placebo-response-is-family-specific-in-sign]]'
- '[[commitment-margin]]'
relationships:
- type: related_to
  target: '[[gate-contribution-factorial]]'
  target_id: experiment:gate-contribution-factorial
  confidence: high
  evidence:
  - docs/research/margin-theory-framework.md (section 1, anchor result 3; S1 direction-specificity)
- type: related_to
  target: '[[placebo-seed-distribution-census]]'
  target_id: experiment:placebo-seed-distribution-census
  confidence: high
  evidence:
  - docs/research/margin-theory-framework.md (section 4, M3 anisotropy panel; census seed lineage)
- type: related_to
  target: '[[matched-magnitude-placebo-sign-survives-as-distributional-property]]'
  target_id: mechanism:matched-magnitude-placebo-sign-survives-as-distributional-property
  confidence: high
  evidence:
  - docs/research/margin-theory-framework.md (section 2, Claim 4)
- type: related_to
  target: '[[random-direction-placebo-response-is-family-specific-in-sign]]'
  target_id: mechanism:random-direction-placebo-response-is-family-specific-in-sign
  confidence: high
  evidence:
  - docs/research/margin-theory-framework.md (section 2, Claim 4)
- type: related_to
  target: '[[commitment-margin]]'
  target_id: term:commitment-margin
  confidence: medium
---

Boundary anisotropy is a family-level property: whether a substrate's short
confabulation-prone commitment margins are direction-specific or generic.
On qwen, short confab margins are direction-specific: random directions at
matched magnitude produce close to no refusal until they destroy
well-formedness, and the gate-contribution factorial's direction-specificity
check (S1) passes at effect ratio 7.27, sign-opposed to the census's
suppressive null. On mistral, generic matched-magnitude pushes recruit
abstention almost as readily as the fitted direction does; S1 fails at ratio
2.03, same-signed with the census's recruiting null. Substrates therefore
differ in how directionally organized their epistemic geometry is around the
abstention boundary; this is proposed as a measurable property of the family,
not incidental noise in any one direction-specificity check.

**Why it matters here:** boundary anisotropy is the framework's account of
why the same direction-specificity test dissociates cleanly by family across
independent experiments (the gate-contribution factorial's S1, and the
earlier RR2/RR3 direction-axis failure it reproduces under a stricter
denominator). The framework's M3 anisotropy panel proposes measuring margins
along K vetted random directions (the census seed lineage) plus the fitted
known-unknown direction, per family, to turn this into a quantitative
anisotropy index; qwen is predicted high, mistral low, with a llama data
point pending.

**Lineage:** introduced 2026-07-16 in `docs/research/margin-theory-framework.md`
as a working-framework concept, not yet a registered claim; it names a
family-level pattern first surfaced by
[[placebo-seed-distribution-census]]'s per-family placebo-sign distributions
and confirmed as a direction-specificity dissociation by
`gate-contribution-factorial`'s S1 result.
