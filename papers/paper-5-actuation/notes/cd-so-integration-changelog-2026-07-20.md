# Correctness-direction-rotation + subspace-overlap integration changelog (2026-07-20)

Governed revision executed on branch `paper/cd-so-integration`, PI-approved per
the session's fold-in directive. This paper does not own the correctness-dial
results themselves (paper 4 does; see its own changelog dated 2026-07-20 in
`papers/paper-4-two-signal-readout/notes/`). This paper only adds a
cross-family motivating hypothesis built on those results, per the series
plan's claim-ownership rule ("a finding appears in a second paper only as one
summarizing sentence with a citation to its home paper, never re-argued").
Both source AMENDMENT.md Outcome sections were read in full before writing.

## What changed

### Frontmatter, `evidence_base` and `notes`

Added `experiments/correctness-direction-rotation/AMENDMENT.md` and
`experiments/correctness-subspace-overlap/AMENDMENT.md` to the governed
source-doc list. Appended a sentence to `notes` pointing at the new §6.5
paragraph and stating explicitly that it is cited as motivation, not
evidence, for a cross-family claim.

### §6.5, new paragraph before "Recommended escalation"

Added one paragraph contrasting the answerability axis's cross-family
portability (this paper's own gated write is built on it) against the
correctness axis's within-model instability, now measured from two
independent angles by a sibling paper's follow-up cells:

- Answerability portability: "AUROC 0.997 to 0.998" across four families,
  no per-family refit. Source: `papers/paper-4-two-signal-readout/manuscript.md`
  §4.1 ("near-saturated (0.997-0.998) on every size and every family we
  tested"), itself governed by that paper's Amendment-Z provenance row.
- Correctness cross-checkpoint rotation null: cosines 0.19 / 0.45 / 0.33
  across the three training transitions, split-half reliability floor 0.17,
  AUROC flat near 0.80. Source: `experiments/correctness-direction-rotation/AMENDMENT.md`
  lines 174-176, 195-210, 216.
- Correctness subspace-overlap null: one weak shared direction above a
  label-permutation null at k=1, nothing above null at k=4-32; an arbitrary
  8-dim slice of the base model's span recovers AUROC ~0.70 versus its own
  top-8 discriminative directions at ~0.74. Source:
  `experiments/correctness-subspace-overlap/AMENDMENT.md` lines 599-610.

The paragraph closes by stating explicitly that both source results are
single-model, exploratory Tier-2 findings, that neither is a cross-family
claim, and that the resulting expectation (correctness-based actuation should
be treated as a harder generalization problem than the answerability axis
this paper actually actuates on) is "a hypothesis for the next study to test,
not a result it can yet report." No numbered escalation item was added or
reordered; the existing six-item list is untouched, since the ask was framing
only.

## What did not change

- No claim in this paper's own results (Sections 4.1-4.10) or in the existing
  escalation list (items 1-6) was altered.
- No internal instrument codenames appear in the new prose; both cells are
  described in plain language ("a direct measurement of its cross-checkpoint
  rotation", "a follow-up asking whether a shared subspace... explains the
  correctness readout's partial transfer"). The governed paths live only in
  the frontmatter `evidence_base` list, consistent with how every other
  source doc in that list is cited.

## Contradiction check

No existing paper-5 sentence asserted anything about the correctness dial's
cross-family portability (paper 5's actuation work is built on the
known-unknown/caution axes, not the correctness dial), so no contradiction was
found. This is an added forward-looking hypothesis, not a correction.
