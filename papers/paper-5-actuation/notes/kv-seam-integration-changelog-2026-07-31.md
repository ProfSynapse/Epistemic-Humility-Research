# Gemma KV-sharing seam integration changelog (2026-07-31)

Executed in worktree `paper5-seam` (branch `paper5/seam-section`), per the
lead's directive to fold in the gemma4-e4b-kv-seam-quarantine resolution,
which had been ON HOLD pending that experiment's resolution. It resolved and
merged to `main` on 2026-07-31. Both `experiments/gemma4-e4b-kv-seam-quarantine/AMENDMENT.md`
(Outcome section, and Prediction/Falsifier for context) and
`experiments/gemma4-e4b-pocket-ladder/AMENDMENT.md` (on the unmerged branch
`exp/gemma-pocket-ladder`, read via `git show`) were read in full before
writing. The three merged kv-seam mechanism nodes in `library/concepts/mechanisms/`
(`gemma-actuation-localizes-shallow-of-kv-seam.md`,
`kv-sharing-off-ablation-breaks-baseline-substrate.md`,
`seam-adjacent-gate-clearance-is-non-direction-specific.md`) were used to
cross-check the AMENDMENT.md numbers, not as an independent source.

## What changed

### Frontmatter, `evidence_base` and `notes`

Added `experiments/gemma4-e4b-kv-seam-quarantine/AMENDMENT.md` and
`experiments/gemma4-e4b-pocket-ladder/AMENDMENT.md` (marked registered,
unresolved) to `evidence_base`. Appended a sentence to `notes` pointing at the
new Section 4.11 and at this changelog.

### New Section 4.11, inserted before the Section 5 divider

"Gemma's inertness was a depth-coverage artifact, not a family-specific null."
Covers: the below-seam depth ladder (relative depth 0.357 and 0.524 clear both
held-out gates with zero-lift placebo controls; 0.429 and 0.476 fail the
clean-tightening floor); the seam-adjacent site (0.571) clearing the same two
gates but failing direction-specificity (worst placebo draw reproduces 88% of
the effect); the sharing-off precondition control breaking the model's own
baseline before the primary sharing-on/off contrast could run; and the
registered-but-unrun pocket-ladder follow-up, described accurately as
non-discriminating per its own registration (see "Claim from the brief not
used as stated" below).

### Section 5 (Synthesis: The Actuation Map)

Added one table row for the gemma depth-ladder result, in the same
what-worked/what-failed/lesson format as the existing mistral row.

### Section 6.5 (Next study escalation list)

Inserted a new item 5, "Gemma's KV-sharing seam," between the existing items
4 and 5 (old 5 and 6 renumbered to 6 and 7: Dense-token screen, Generic tuner
support).

### Appendix A (Traceability Map)

Added two rows: the kv-seam-quarantine Outcome (status: "Exploratory,
resolved; quarantine hypothesis open") and the pocket-ladder registration
(status: "Registered draft, not yet run"), the latter citing its unmerged
branch explicitly since it is not reachable from `main`.

## Numbers used and their doc lines

All from `experiments/gemma4-e4b-kv-seam-quarantine/AMENDMENT.md` Outcome
section (line 1919 onward) unless noted:

- D1/hs15 (rd 0.357): "G1 PASS 0.7857 [0.7180, 0.8413], G2 PASS 0.011. Best
  site, shallowest tested."
- D2/hs18 (rd 0.429): "G1 FAIL 0.4464." D3/hs20 (rd 0.476): "G1 FAIL 0.4048."
- A3/hs22 (rd 0.524): "G1 PASS 0.5893, G2 PASS, G3 PASS-DEGENERATE (all five
  accepted placebo draws produced zero lift...)." A3's exact known-correct
  cost number is not given in Outcome, so the manuscript says only "cost
  within the registered floor" rather than inventing a figure.
- A5/hs24 (rd 0.571): "G1 PASS 0.7321, G2 PASS 0.0333, G3 FAIL (effect_ratio
  1.139; worst random draw reproduced 88% of the true effect)."
- C1 precondition: "C1 known-correct cost 180/180 = 1.0 vs C0 0/180 (Newcombe
  CI [0.9704, 1.0] against the 0.05 cap); NLL 3.5342 vs 12.3303 (rel delta
  2.4889...)."
- Manifest one-liner verdict: "C1 FAIL: sharing-OFF substrate broken at
  baseline, A2/A4 INCONCLUSIVE as registered; D-ladder fires the supporting
  leg (D1 0.786 vs A1 no-usable-dose): KV-quarantine SUPPORTED-not-established,
  confounded with depth as registered; hs24 clearance adjudicated
  non-specific."
- "A1 dose-viability NOT-RUN means the parent's above-seam null REPRODUCED"
  (Phase B and C1 paragraph) sources the manuscript's claim that the deep-site
  null was reproduced alongside the new shallow-band result.

Depth fractions (0.357/0.429/0.476/0.524/0.571) are transcribed from the same
document's site-geometry table (donor-reachability table, "The shallow depth
ladder (D1-D4) varies depth at constant donor reachability") and cross-checked
against `.skills/family-atlas/reference/read-actuate-depth.md`'s own gemma
table, which reproduces the same five values and outcomes.

From `experiments/gemma4-e4b-pocket-ladder/AMENDMENT.md` (branch
`exp/gemma-pocket-ladder`): the E1/E2/E3 site table gives hs25 = rd 0.595,
hs26 = rd 0.619, hs27 = rd 0.643. The cross-family operating range 0.375-0.639
and the qwen/llama comparison sites are transcribed verbatim from the same
document's "Motivation and posture" section.

## Claim from the brief not used as stated

The task brief characterized the pocket ladder as "the registered
discriminating follow-up." Its own AMENDMENT.md contradicts that framing
directly: "It is not a test of the KV-quarantine hypothesis and does not
attempt to discriminate the quarantine account from the crystallization-gap /
linear-accessibility account or any other competing explanation... A positive
result is evidence that gemma CAN actuate in this band; it is not, by itself,
evidence about why, and must not be reported or interpreted as resolving the
quarantine hypothesis in either direction." The manuscript instead describes
the pocket ladder as registered but explicitly non-discriminating, and
attributes the "needs a gentler ablation" framing to the
`kv-sharing-off-ablation-breaks-baseline-substrate` mechanism note's closing
sentence, which is the actual sourced next step toward a discriminating test.

## What did not change

- No claim in Sections 4.1-4.10, the existing Section 5 rows, or the existing
  Appendix A rows was altered.
- Section 6.3 (J-space scoping) was left untouched. It already scopes its
  eff-dim-peak account to raw-base Qwen3-4B and separately notes llama/mistral
  eff-dim profiles from `jspace-family-atlas`; extending it to gemma's own
  flat eff-dim profile was outside this brief's binding source-doc list (the
  brief cited only the kv-seam-quarantine and pocket-ladder amendments, the
  two family-atlas/read-actuate reference docs, and the three merged
  mechanism nodes) and was not added.
- The abstract was left untouched, matching the manuscript's existing
  precedent: the abstract does not mention the mistral/llama cross-family
  arc (Sections 4.8-4.10) either, so a fourth family's cross-family result
  follows the same body-only placement.

## Contradiction check

No existing paper-5 sentence asserted gemma does or does not actuate (the
manuscript had zero prior mentions of gemma outside the Section 3.1 block-count
table), so no contradiction was found. This is new content, not a correction.

## Lead review corrections (2026-07-31, before commit)

The drafting agent's section attributed the five-draw zero-lift placebo
result to the relative-depth-0.357 site and called it "a clean pass
rather than a narrow one". Two defects, both corrected by the lead:

1. The Outcome records G3 placebo results only for A3/hs22 (rd 0.524)
   and A5/hs24 (rd 0.571). The depth-ladder arms, including D1/hs15,
   carried G1/G2 only; no placebo control ran at rd 0.357. The section
   now says so explicitly and no longer claims direction-specific
   actuation there.
2. A3/hs22's placebo result is registered as G3 PASS-DEGENERATE with a
   reporting restriction ("reported with the degenerate label, never as
   a large effect ratio", AMENDMENT.md Outcome). "Clean pass" language
   removed; the degenerate label and its restriction are now stated.

Consequential wording change: "Gemma is actuable" softened to "Gemma
clears held-out behavioral gates", matching the family-atlas caveat
that raw gate clearance without an adjudicated G3 is not claimed as
actuation.
