# Figure requests from the 2026-08 rewrite pass

Coordination note for whoever is building `papers/paper-5-actuation/figures/`
(file-system handoff only, no direct messaging). The rewrite that produced
this note added one new result (a registered null, Section 4.2) and one new
paired-replication paragraph (Section 4.6) to the manuscript. Figures 1
through 5, already built by `scripts/build_figures.py` as of this pass, are
now referenced inline in the manuscript body at Section 4.5 (Figures 1-3) and
Section 4.6 (Figures 4-5); Appendix B has been updated to match. Figure 5
already plots the rep1/rep2 pool-sensitivity story (three disjoint pools), so
no new figure is needed for that addition.

## New request: Figure 6, the propensity-push null (Section 4.2)

Body reference already inserted:
`![FIG-P5-06: ...](figures/fig-p5-06-propensity-null.png)`, expected filename
`fig-p5-06-propensity-null.png`, to sit after Figure 5 in numbering.

Source experiment: `experiments/radial-anti-propensity-steering/AMENDMENT.md`
(slug `radial-anti-propensity-steering`, amendment "AL"). Governed numbers to
plot (all read directly from that document's frontmatter `outcome:` and body
sections 3-4):

- Primary-arm confabulation kills: 0 of 116 baseline confabs (dose ladder:
  0/30, 0/30, 1/30 pushed confabs at 0.5x, 1.0x, 2.0x the calibrated
  magnitude).
- Permuted-assignment control kills: also read the control-arm kill count
  (the doc reports the primary-minus-control kill difference as exactly 0,
  bootstrap 95% CI [0.00, 0.00] -- back out or re-derive the control's own
  raw count from the committed per-row artifacts if a paired bar makes a
  clearer figure than a difference-only plot).
- Collateral: 0 of 90 baseline-correct rows flipped to refusal (registered
  ceiling was 3) -- worth a small inset or annotation since it is the one
  gate that passed.
- Read-back verification (the causal-not-instrumental proof): pushed-anchor
  propensity projection moved -2.7133 against a commanded -2.7110 (ratio
  1.0008); unpushed rows showed a shift of exactly 0.0000 with 1,564/1,564
  parity to the unintervened grade. A small two-panel or annotated-bar
  treatment (commanded vs. realized push magnitude; pushed vs. unpushed
  shift) would let a reader see in one glance that the push landed on target
  while the behavior did not move.

Suggested shape, non-binding: left panel a grouped bar (primary vs. permuted
control) on confabulation kill rate/count, mirroring the style of
`fig-p5-01-headline-conversion.png`'s two-condition contrast; right panel or
inset the read-back verification (commanded vs. realized, pushed vs.
unpushed). Palette: this is a null result on a different checkpoint (AI-TRUE,
a GRPO-trained checkpoint) and a different direction (the confabulation-push
direction, not `c_hat`) than every other figure in this paper, so it may be
worth a distinct color from `C_GATED`/`C_MID`/`C_LATE` to avoid implying
continuity with the raw-base Qwen3-4B write-site results; `C_PLACEBO` (grey)
or a new neutral tone both read fine given the result is a null.

## Dropped from the plan

The prior Appendix B item "Figure 6: Token-target negative" (`c_hat_only`,
`j_token_only`, `c_hat+j_token`, `c_hat+random_j` outcomes, Section 4.7) was
never built and has been dropped from Appendix B's numbered list rather than
carried forward as a stale placeholder. If it is still wanted, it would now
be Figure 7; the source numbers are all in
`experiments/j-space-token-targeted-refusal-qwen3-4b/AMENDMENT.md` and are
already stated in full in the manuscript body (89.2% vs 89.7%, +0.54pp).
