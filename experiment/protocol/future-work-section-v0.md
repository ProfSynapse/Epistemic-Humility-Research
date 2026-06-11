# Paper 1, Section 8 (v0 text) — parked 2026-06-10

SUPERSEDED 2026-06-11: §8 has been drafted in `meta-analysis/paper/draft-v0.md`
as a four-phase program (method three-way / dose-response and composition /
probe-transfer mechanism / rolling generalization), sourced from
`experiment/protocol/research-trajectory.md`. This file is kept for the record;
the coherent-humility framing and the three-outcome probe-transfer reading
below were carried into the new section.

Removed from `meta-analysis/paper/draft-v0.md` pending the research-trajectory
mapping conversation; will be rewritten once the experimental program is
formally scoped. Original v0 text follows.

---

## 8. Future work: toward coherent humility

The synthesis points at one experiment-shaped question more insistently than any other. The unreconciled tension (Section 6.1), the estimator-fragility problem (Section 6.2), and gaps 1-4 (Section 6.3) are all facets of a single unknown: **when fine-tuning makes a model behave humbly, does anything change beneath the behavior?** The companion research program (experiment/protocol/RESEARCH-DIRECTIONS.md) frames this as *coherent humility*: training a model whose intellectual humility agrees across its tokens, its hidden states, and its stated confidence — and verifying that agreement mechanistically rather than behaviorally. The measurement design follows from this synthesis directly: any future training comparison (the natural arms, given the verified gaps, are SFT, KTO, and a GRPO-style calibration-aware-reward arm) should be evaluated as a three-layer panel — token-level calibration, hidden-state probes of the P(IK) type with base-to-tuned probe-transfer analysis, and stated behavior with the recall/over-refusal decomposition of Section 5.3 — so that the result is a coherence delta rather than another single-metric win. All three possible probe-transfer outcomes are informative: layers moving together (humility internalized), behavior moving over unchanged hidden states (humility performed — the polite liar with better manners), or probes ceasing to transfer (representations moved; localize per layer). We deliberately do not pre-commit a design here; the point of this synthesis is that the field has enough evidence to pick that hypothesis well, and not yet enough to assume its answer.

