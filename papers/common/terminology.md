# Terminology: the margin-theory vocabulary rename

Status: draft, 2026-07-18; extended 2026-08-10 (IDK switch scope, caution-gate retirement). Single source of truth for the program's vocabulary
rename, adopted in `docs/research/margin-theory-framework.md` section 3 after
the gate-contribution factorial. All five papers (and the planned paper 6)
cite this file instead of each running an independent rename pass.

This file changes running prose only. Governed doc filenames, artifact
names, config keys, and experiment slugs keep their existing names verbatim
wherever they appear, in this file and in every paper.

## 1. Mapping table

| Old term | New term | Reason | Evidence |
|---|---|---|---|
| doubt direction (synonyms in prior prose: doubt axis, doubt readout) | known-unknown direction (KU direction; symbol c_hat unchanged); for the probe reading specifically, known-unknown (answerability) readout | Names how it was fit (separating known from unknown items), not a claim about the model's mental state. | `docs/research/margin-theory-framework.md` section 3 (table row 1); falsification context in `experiments/gate-contribution-factorial/AMENDMENT.md`, Outcome. |
| doubt gate | KU readout gate | It is a classifier threshold used for deployment targeting; calling it "doubt" implied it detected doubt rather than thresholded a readout. | `docs/research/margin-theory-framework.md` section 3 (table row 2); `experiments/gate-contribution-factorial/AMENDMENT.md`, Outcome (gate axis falsified on both families: Gap_Sel(c_hat) 0.148 qwen, CI [0.119, 0.177], and 0.129 mistral, CI [0.103, 0.156], against a registered 0.20 floor). |
| caution write | IDK switch, for the validated actuator only (the frozen Qwen3.5-4B hs20 operating point); boundary push (dosed write) for any other dosed write | The actuator name was earned by a registered confirmatory naming cell (discrete flip to explicit IDK at the endpoint, no graded intermediate at mid-dose, direction-specific), so it applies exactly where it was validated. Generic or historical dosed writes at other sites keep the descriptive boundary-push name, which claims only displacement, not an installed disposition. | `experiments/idk-switch-naming-confirmatory/AMENDMENT.md`, Outcome (all three name-earning gates PASS, resolved 2026-07-31); `docs/research/margin-theory-framework.md` section 3 (table row 3); `experiments/ungated-vs-gated-dose-matched/AMENDMENT.md`, Outcome (H4-G1/H4-G2). PI scope ruling 2026-08-10 (see below). |
| caution gate (paper 3 working label; interim "caution axis" also superseded) | refusal axis | "Gate" asserts conditional switching control no registered cell earned, and "caution" attributes a mental disposition no experiment measured. The operational facts are: the direction is fit as a refuse-versus-answer contrast among known items, it is separable from the known-unknown axis, and ablating it collapses over-refusal with one-way leverage. "Refusal axis" names exactly that fit and that causal handle, and claims nothing more. The earned switch name belongs to the write actuator (row above) and does not extend to the read-side mechanism. | Paper 3 sections 5 and 6 (separability and one-way ablation evidence); naming discipline per `experiments/idk-switch-naming-confirmatory/AMENDMENT.md` (names are earned by registered gates). PI rulings 2026-08-10 (see below). |
| confab propensity | split into two constructs: baseline confab rate (behavior without intervention) and commitment margin (fragility under intervention) | One name was carrying two different quantities: what the model does unprompted, and how easily an intervention flips it. | `docs/research/margin-theory-framework.md` section 2 (Claim 1) and section 3 (table row 4); commitment margin operationalized per row in `experiments/margin-mapping/AMENDMENT.md`, Outcome (resolved 2026-07-17, qwen35_4b only; mistral void by instrument loss). |
| (unnamed) | boundary anisotropy | Names a measured family-level property: whether short margins are direction-specific (qwen) or generic (mistral). | `docs/research/margin-theory-framework.md` section 2 (Claim 4); `experiments/gate-contribution-factorial/AMENDMENT.md`, Outcome (S1 direction-specificity ratio 7.27 qwen, sign-opposed, passes; 2.03 mistral, fails). |
| doubt-coupling | KU-readout coupling (first mention may expand: known-unknown readout coupling) | The mechanism makes the gate a live function of the readout; the coupling is to a readout, not to a mental state. | Construct defined in `experiments/doubt-regulated-caution/AMENDMENT.md`; naming follows the KU-readout-gate row above. Lead adjudication 2026-07-18 (see below). |

### Adjudicated extensions (lead ruling, 2026-07-18)

Two terms in scope for this rename had no explicit replacement in the
framework's section 3 table. Both were flagged during drafting and
adjudicated by the lead on 2026-07-18; the rulings are folded into the table
above and recorded here:

- **doubt axis** and **doubt readout** are ruled synonyms of "doubt
  direction" for the same c_hat construct, based on uniform repository usage
  (for example `docs/atlas/family-layer-map.md`,
  `docs/review/paper3-direction-provenance-2026-07-10.md`, and
  `experiments/doubt-regulated-caution/AMENDMENT.md`). They take the same
  replacement, with "known-unknown (answerability) readout" preferred where
  the prose means the probe reading rather than the vector.
- **doubt-coupling**, the mechanism of making the KU readout gate a live
  function of the readout itself (`h' = h - (h . c_hat) c_hat + g_i *
  sigma_c * c_hat`, defined in
  `experiments/doubt-regulated-caution/AMENDMENT.md` and used in
  `papers/paper-5-actuation/manuscript.md`), is ruled to rename to
  **KU-readout coupling**, following the KU-readout-gate row. The governed
  doc's own name and slug stay verbatim under usage rule 1.

### Adjudicated extensions (PI rulings, 2026-08-10)

- **IDK switch** is adopted as the earned name of the caution-write actuator,
  scoped to exactly what the confirmatory naming cell validated: the frozen
  Qwen3.5-4B hs20 operating point (`experiments/idk-switch-naming-confirmatory/`,
  resolved 2026-07-31, all three name-earning gates PASS). The PI ruled the
  name actuator-only: it does not extend to the read-side refusal-axis mechanism,
  to other write sites, or across families. Dosed writes outside the
  validated actuator keep "boundary push (dosed write)".
- **caution gate** is retired program-wide. The PI's rule: mechanism names
  are earned through experiment, and no registered cell earned gate
  semantics (conditional switching control) for the read-side mechanism.
- **caution axis** was proposed as the replacement and rejected by the PI
  the same day, under the same rule: "caution" is an inferred mental state
  no experiment measured, so it has no more earned standing than "gate".
  Paper 3's construct renames to **refusal axis**, the fully operational
  name: it is fit as a refuse-versus-answer mass-mean contrast among known
  items, is separable from the known-unknown axis (whitened cosine about
  -0.61), and ablation along it collapses over-refusal on knowns (0.994 to
  0.030) with one-way leverage. Every word in the name is a measured fact.
  "Caution" survives in running prose only in its ordinary-English caveat
  sense, never as a construct name.
- **Disambiguation**: the family-atlas read panel's `caution` axis is a
  DIFFERENT contrast (refused-versus-confabulated, per
  `docs/atlas/family-layer-map.md`) that shared the working label. In
  running prose it renders as the **refusal-versus-confabulation
  contrast**, never as "refusal axis", which is reserved for the
  refuse-versus-answer-among-knowns construct. The atlas artifact keys
  (`doubt` / `caution` / `raw_refusal`) stay verbatim as keys.

## 2. Scope: where the old names held, and why generalizing prose needs new ones

The old names were not wrong everywhere. Within the KUQ population where
c_hat was fit, the framework's own earnability criteria (a) through (c) hold
for qwen: the direction (a) tracks actual ignorance, (b) drives abstention
when amplified, and (c) does so direction-specifically (S1 ratio 7.27,
sign-opposed). Mistral fails (c), so mentalistic naming was already retired
for mistral before this rename (`docs/research/margin-theory-framework.md`,
section 3, "Earnability criterion for mentalistic names").

The fourth criterion, (d), is the one a title or abstract implicitly invokes:
that the readout responds to evidence the way doubt should, so that
supplying the true answer in-context collapses the projection on that row
and lengthens its margin. Two experiments tested (d) directly on an
out-of-population error class (world-known items, where the model's error is
not ignorance but a wrong answer produced with apparent confidence), and both
resolved as null results on 2026-07-18:

- **`experiments/margin-evidence-responsiveness-worldknown/AMENDMENT.md`,
  Outcome.** The primary test was VOID: the named KUQ direction does not fire
  on this population (baseline confab-vs-correct AUROC 0.3018, bootstrap 95%
  CI [0.2647, 0.3396], against a 0.70 floor), and the projection genuinely
  reverses sign between populations. The direction reads closer to
  unanswerability recognition than to self-directed uncertainty. A
  world-known-specific refit direction fires, but criterion (d) is NOT
  EARNED on it either: it passes the specificity leg (paired true-minus-false
  shift 0.1022, CI [0.0527, 0.1524]) but fails the collapse leg (median shift
  0.5921 against a frozen floor of 0.8209), and the behavioral (margin)
  channel is void on its own reproduction gate. The doc's one-sentence
  verdict: criterion (d) "is not licensed for any direction on the
  world-known error class," so "the mentalistic 'doubt' name remains
  unearned."
- **`experiments/evidence-response-direction-search/AMENDMENT.md`,
  Outcome.** A constructive search fit a direction directly to maximize the
  true-vs-false evidence contrast (d_ev). It separates confab from correct at
  baseline (AUROC 0.7252, CI [0.6832, 0.7652], against a 0.70 floor) but is
  indistinguishable from covariance-shaped random directions (empirical p =
  0.191, robust across three null flavors) and decisively weaker than the
  native ignorance-fit direction (paired AUROC difference -0.1381, CI
  [-0.1895, -0.0872]). It orders refused rows above confabulated rows above
  correct rows, the signature of retrieval-family (answer-availability)
  geometry rather than doubt. The doc's verdict: this "upgrades" the
  fragmentation reading and confirms "the mentalistic name 'doubt' remains
  unearned on the world-known error class for every direction tested to
  date."

That is the concrete reason a name earned inside one fit population cannot
be used in prose that generalizes beyond it, such as a paper's title or
abstract. Both null results are reported straight in this file: neither is a
falsification of the direction's usefulness where it does fire, and neither
moves any locked verdict.

## 3. Usage rules

1. Governed doc filenames, artifact names, config keys, and experiment slugs
   keep their existing names verbatim everywhere, including inside a paper
   that otherwise uses the new vocabulary.
2. A paper's first mention of a renamed construct may parenthesize the old
   name once, for continuity: "the known-unknown (answerability) readout,
   previously called the doubt readout." After that first mention, use only
   the new name.
3. Quotations of prior work, including quoted registered predictions or
   quoted verdicts from an AMENDMENT.md, stay verbatim; do not retrofit the
   new vocabulary into a quotation.
4. New manuscript prose uses only the new vocabulary from section 1. This
   applies to new sections and to any rewrite of existing prose; it does not
   retroactively require touching prose that is not otherwise being
   revised.

## 4. Per-paper applicability

- **Paper 1 (taxonomy).** Clean. No occurrences of the retired vocabulary in
  the current manuscript.
- **Paper 2 (training regimen).** Clean. Its one "doubt" occurrence is the
  governed filename `archive/notes/experiments/caution-vs-doubt-knowledge-gate.md`,
  which stays verbatim under usage rule 1.
- **Paper 3 (knows but doesn't say).** About 35 sites use the retired
  vocabulary; this is the paper's naming and hedging pass, tracked
  separately.
- **Paper 4 (two-signal readout).** Two prose sites, both citing paper 5's
  doubt-gated caution-write result rather than arguing it directly (one scope
  disclaimer, one description of the gated-write finding).
- **Paper 5 (actuation).** Pervasive, including the title. PI ruling
  2026-07-18: paper 5's title retires "doubt." Ruling record: the decision
  checkpoint of 2026-07-18 in
  `docs/sessions/20260717T201649Z-margin-cascade-execution-m1-m2-m1b-m4.md`;
  execution spec in `docs/preparation/paper5-rewrite-spec.md`.
