# Paper 3 naming + hedging pass (2026-07-18)

Executed against `docs/preparation/papers-reconciliation-2026-07-18.md` (Paper 3
section) and `papers/common/terminology.md`. Scope: vocabulary rename + hedging
prose only. Zero reported numbers changed.

## 1. Rename sweep

35 pre-existing "doubt"-family occurrences (matching the campaign's estimate)
were located by `grep -n -i "doubt" manuscript.md` before editing. Disposition:

- 29 sites renamed: "doubt axis" / "doubt-axis" / "doubt direction" /
  "knowledge/doubt" / "doubt scale" / "doubt-orthogonal(ized)" and the
  descriptive-prose nickname "caution-vs-doubt note" all became
  "known-unknown axis" (or the specific variant in context: "known-unknown
  direction", "known-unknown-axis probe", "known-unknown-axis readout",
  "known-unknown scale", "known-unknown-orthogonal(ized)",
  "caution-vs-known-unknown note").
- 1 site (abstract, first mention) kept the old name as the one allowed
  continuity parenthetical per terminology.md usage rule 2: "previously
  called the doubt axis."
- 5 sites are governed/quoted and stay verbatim per terminology.md usage
  rule 1 (filenames/artifact names) or rule 3 (quotations/citations):
  - `docs/sessions/20260627T093723Z-caution-vs-doubt-knowledge-gate.md`
    (frontmatter `evidence_base` path, and again in the Appendix A table row).
  - `archive/notes/experiments/caution-vs-doubt-knowledge-gate.md` (Appendix A
    table row).
  - "Rewarding Doubt" (Bani-Harouni et al. 2025 paper title), both the
    in-prose mention (§2 related work) and the reference-list entry.

Residual-grep proof after editing (`grep -n -i doubt manuscript.md`): 7 hits
remain, all accounted for above (2 governed-filename lines, repeated once
each; 1 continuity parenthetical; 2 paper-title citations; 1 line in the new
§9 limitations bullet that quotes the retired name in scare-quotes to
describe what was tested; 1 line in the new Appendix A footnote that names
the retired vocabulary family being mapped away from). No unaccounted
"doubt" occurrence remains.

## 2. Title/abstract scope sentence

Added to the abstract, after "The model represents what it does not know; it
does not report it.":

> By "knows" we mean this internal recognition of which questions are
> answerable, not verified self-knowledge that the model's own answer is
> correct.

## 3. Hedge sentences (2)

**After the "monotone across behavior cells" claim (§4, "The internal
readout"):**

> This monotone ordering, like the answerability identity below, is a
> single-model/single-population reading (Qwen3-4B, SelfAware); a
> methodologically parallel evidence-responsiveness test on a different Qwen
> lineage and a different error class (confident wrongness on answerable,
> world-known questions, rather than KUQ ignorance) found the analogous
> KUQ-fit direction's projection reverses in sign instead of ordering
> monotonically there, and a constructive search for a portable
> evidence-responsive axis on that population recovered only generic
> retrieval-family geometry, not a specific evidence axis, so this ordering
> should not be assumed to transfer before it is tested directly
> (`experiments/margin-evidence-responsiveness-worldknown/AMENDMENT.md`,
> Outcome; `experiments/evidence-response-direction-search/AMENDMENT.md`,
> Outcome).

Source: margin-evidence-responsiveness-worldknown/AMENDMENT.md, Outcome ->
"the RAW projections genuinely reverse between populations (KUQ confab
more-negative than correct; world-known confab more-POSITIVE than correct)"
and evidence-response-direction-search/AMENDMENT.md, Outcome -> "d_ev ...
orders refused above confab above correct, so the evidence contrast recovers
retrieval-family geometry rather than a doubt axis."

**Near the "factual confidence P(answer correct)" distillation framing (§8,
"The implied experiment, run and resolved"):**

> This framing treats the known-unknown axis's calibrated appropriateness
> estimate as a stand-in for factual confidence, P(answer correct); that
> identification, like the axis's monotonicity in Section 4, is a
> single-model/single-population reading on Qwen3-4B/SelfAware, and a
> methodologically parallel constructive search for a portable
> evidence-responsive axis on a different model and error-class population
> found only generic retrieval-family geometry rather than a specific
> evidence/correctness axis, so the identification should not be assumed to
> hold outside this population without a direct test
> (`experiments/evidence-response-direction-search/AMENDMENT.md`, Outcome).

Source: evidence-response-direction-search/AMENDMENT.md, Outcome -> "the
mentalistic name 'doubt' remains unearned on the world-known error class for
every direction tested to date" and the construct-tell finding that d_ev
"orders refused above confab above correct, the signature of an
answer-availability / retrieval-success signal."

## 4. New §9 limitations bullet

Added as the last bullet before "## 10. Conclusion":

> Naming caution from a different lineage. A dedicated naming-earnability
> test on a different model and direction lineage (Qwen3.5-4B, hs20, not
> this paper's Qwen3-4B L35 known-unknown axis) found the mentalistic
> "doubt" name not earned on evidence-responsiveness: the transfer test
> voided on population reversal (the KUQ-fit direction reads reversed on a
> world-known confident-wrong error class), and the natively refit direction
> passed specificity but failed the projection-collapse leg, with the margin
> channel instrument-void
> (`experiments/margin-evidence-responsiveness-worldknown/AMENDMENT.md`,
> Outcome). A follow-on constructive search for a direction built to
> maximize the evidence contrast fired at baseline but was indistinguishable
> from covariance-shaped random directions and recovered generic
> retrieval-family geometry rather than a specific evidence axis
> (`experiments/evidence-response-direction-search/AMENDMENT.md`, Outcome).
> Neither result is a direct test of this paper's known-unknown axis; they
> transfer as a naming caution by methodology, not as a falsification of the
> identity or monotonicity claims made here.

Sources (both read fresh from AMENDMENT.md before writing):
- margin-evidence-responsiveness-worldknown/AMENDMENT.md, Outcome -> "criterion
  (d) is not licensed for any direction on the world-known error class: the
  named KUQ direction does not fire there (primary test void, out of domain;
  population reversal), and the native refit shows only a weak
  evidence-specific, sub-floor, behaviorally-inert projection response ((d)
  not earned; margin channel instrument-void)."
- evidence-response-direction-search/AMENDMENT.md, Outcome -> "The
  constructive search fails on specificity: d_ev fires at baseline (0.7252
  >= 0.70, rung (a) pass) but is indistinguishable from covariance-shaped
  random directions (p = 0.191, robust across three null flavors) ...
  d_ev fires at baseline but is indistinguishable from random directions of
  the same covariance ... it orders refused > confab > correct, the
  signature of an answer-availability / retrieval-success signal."

Framing check: every new sentence attributes the caution to "a
methodologically parallel test / search on a different Qwen lineage
(Qwen3.5-4B, hs20)," never claiming M4-WK or M4c directly tested or
falsified this paper's Qwen3-4B L35 known-unknown axis.

## 5. Appendix A footnote

Added after the provenance table, before "Governance notes":

> Vocabulary note: reader-facing prose in this paper follows the
> program-wide rename in `papers/common/terminology.md`, the canonical
> mapping from the prior "doubt"-family names (doubt axis, doubt direction,
> doubt readout) to the known-unknown vocabulary used throughout. Governed
> filenames, artifact names, and internal labels in the table above keep
> their original names verbatim per that file's usage rule 1.

## Verification that zero numbers changed

`git diff` on the manuscript, filtered to added/removed lines containing a
digit: every pair of removed/added lines carrying a number (0.997, 0.866,
0.798, 0.83, 0.001, 0.999, n=3369, 1233, ECE 0.004, AUROC figures, etc.)
shows the identical numeral on both sides of the diff; only surrounding
prose/vocabulary changed. The four new sentences/bullet (scope sentence, two
hedges, limitations bullet, Appendix A footnote) contain no numeric values
copied from the AMENDMENT.md Outcomes — they cite the docs by path and
describe findings qualitatively, so there was nothing to transcribe
incorrectly.

## Unfinished / ambiguous

Nothing unfinished. One judgment call worth flagging for the lead's review:
terminology.md's mapping table literally gives "known-unknown direction (KU
direction) ... for the probe reading specifically, known-unknown
(answerability) readout" — i.e., the "(answerability)" parenthetical is
scoped to the probe-reading term, not to "axis"/"direction" generally. The
campaign record's Paper 3 section explicitly instructs "rename doubt axis ->
known-unknown (answerability) axis," so I used the full parenthetical form
once (abstract, first mention, alongside the old-name continuity note and
the new scope sentence) and used the shorter "known-unknown axis" at the
other ~28 sites for readability, consistent with terminology.md usage rule 2
("after that first mention, use only the new name" — read as: the fully
specified name, which need not repeat its own parenthetical every time). If
the lead wants "(answerability)" repeated at every occurrence instead of
just the first, that is a mechanical follow-up, not a substantive change.
