# Paper 5 rewrite specification (task #15)

Prepared 2026-07-18 by the lead from the five-reader papers reconciliation
campaign and the PI's decision-packet rulings (recorded in
`docs/sessions/20260717T201649Z-margin-cascade-execution-m1-m2-m1b-m4.md`,
checkpoint of 2026-07-18). This spec is self-contained: it does not depend
on any session scratchpad. Execution is blocked by the terminology block
(`papers/common/terminology.md`, task #30) merging first.

Manuscript under revision: `papers/paper-5-actuation/manuscript.md`.
Line references below were verified 2026-07-18 and may drift; the writer
re-locates each anchor by quoted text, not by line number alone.

## 1. Objective

Rewrite paper 5 around the operating-point-dependent selectivity thesis
(`docs/research/margin-theory-framework.md` section 5): the caution write
(boundary push) is gate-supplied at the overdrive operating point
(L34/dose-200) and write-supplied (self-sorting) at mid-band, where the
gate's role reduces to a modest increment plus cost governance. The current
draft states "the write itself is not selective; the readout gate supplies
selectivity" as a universal claim; `gate-contribution-factorial` falsified
that as a general claim in both families. Simultaneously execute the
2026-07-10 audit's positive reframe (never executed), fold in the
2026-07-13..07-18 evidence cluster, and apply the program vocabulary rename.

No registered number, gate, or verdict moves. The affected text is
interpretation, framing, and coverage.

## 2. Binding rules for the writer

- READ BEFORE YOU CITE: every experimental fact is transcribed from the
  cited `experiments/<slug>/AMENDMENT.md` Outcome section, opened fresh.
  This spec's numbers are navigation aids, not citable sources.
- Terminology: `papers/common/terminology.md` is the SSOT once merged.
  Governed doc filenames, slugs, config keys, and KG node ids stay
  verbatim; first mention in the paper may parenthesize the old name once.
- Committed-prose rules: no em dashes; never the phrase "load-bearing".
- One branch, one PR (`paper/paper5-rewrite` suggested), worktree under
  `/home/profsynapse/code/ehr-worktrees/`. The writer does not commit or
  push; the lead reviews, commits, PRs. Red-team review of the full draft
  before the PR (paper-changing prose rule).
- Registered numbers quoted must match their Outcome docs byte-for-byte
  where given to more than two decimals.

## 3. PI rulings baked in (2026-07-18)

1. TITLE retires "doubt". Writer proposes three candidate titles using the
   known-unknown/answerability vocabulary (keeping "Look Before You Speak"
   as the lead phrase is allowed but not required); PI picks.
2. Mistral stays in the paper as a bounded negative in the actuation map:
   three independent direction-specificity failures (RR2 flat tolerance;
   RR3 effect ratio 1.87 vs 3.0; factorial S1 ratio 2.03 under the K=15
   census denominator), gate contribution sub-floor (Gap_Sel 0.129 vs
   0.20), true behavioral null on the cross-family confirmatory (0/874
   clean_tighten at every dose). Benefit and cost gates still reproduce.
3. Cross-family generality is framed NOW as "readable everywhere, actuable
   only in the Qwen lineage at tested sites"; per-family atlas-sited
   retests are queued work (tasks #7/#8/#35), not blockers.
4. Margin/geometry cells (margin-mapping, margin-separation-fine-ladder,
   susceptibility-as-probe, the M4 arc's geometry findings, J-space atlas)
   belong to the successor margin-theory paper (task #34). Paper 5 carries
   at most one forward-pointer sentence in its limits section.

## 4. Section-by-section change plan

MUST (the falsified-universal cluster; one thesis, six recurrence sites):

- Abstract (near :73-75): reword the selectivity attribution as
  operating-point-dependent. Evidence: `gate-contribution-factorial`
  Outcome (permuted-gate confab abstention 0.550 qwen / 0.600 mistral;
  Gap_Sel 0.148/0.129 vs 0.20 floor) and `ungated-vs-gated-dose-matched`
  Outcome (registered 60.1% known damage ungated vs 3.1% gated at
  L34/dose-200). Add one scope sentence adopting the known-unknown naming.
- Intro rule 2 (near :128-130): "the snap alone is not selective" becomes
  regime-conditional; at mid-band the write self-sorts.
- Section 4.4 (near :336-341): replace the unregistered n=80 dose-200
  diagnostic (36.2%) with the registered 60.1%-vs-3.1% contrast, scoped
  L34/dose-200, not described as a refusal rate. Evidence:
  `ungated-vs-gated-dose-matched` Outcome, binding scope statement 1.
- Section 5 map (near :758-759): split the gate rows into
  overdrive-regime and mid-band-regime rows; rename to KU-gated; mistral
  row reworded per ruling 2.
- Section 6.2 (near :798-804): rewrite two-regime; at mid-band the gate is
  a deployment limiter and cost governor (known false refusal 0.042/0.005
  vs permuted 0.050/0.039 against the registered 0.05 ceiling), not the
  selectivity source.
- Conclusion: same thesis correction wherever restated.

MUST (naming and coverage):

- Section 4.10 (near :722-730): "coupled to the model's own doubt" /
  "certifying doubt-coupling" becomes known-unknown readout-coupling; drop
  the self-directed-state implication. Evidence:
  `margin-evidence-responsiveness-worldknown` Outcome (criterion (d) not
  licensed; population reversal; the direction reads as unanswerability
  recognition).
- Abstract/frontmatter (near :42): scope sentence for "epistemic state";
  title per ruling 1.
- Section 6.4 limits (near :816-843): add the coherence/saturation ceiling:
  only ~13% (51/400) of world-known confabs tippable inside the
  coherence-valid band, doses >= 3x reference drive degenerate text before
  refusal; scoped to the hs20 lineage, the L34 headline untested for it.
  Evidence: `margin-evidence-responsiveness-worldknown` Outcome, saturation
  finding.

SHOULD:

- Sections 4.4/4.5 region: add the mid-band positive arc, which STRENGTHENS
  the controller: held-out transfer (refused 0.678, well-formedness 0.977,
  known cost 0.039; `qwen35-4b-midband-heldout` Outcome) and sampled-decode
  seed robustness (69.5% pooled conversion, all 5 seeds above floor, cost
  4.65%; `snap-seed-sampled-decode-replication` Outcome). This supersedes
  the 2026-07-10 audit's H2/H3 items.
- Section 6.5 (near :854-881): replace "awaited promotion vehicle" framing
  with the resolved not-promoted verdict: all cells stopped at FIT
  dose-viability; caution readable in every family, late-site writes fail
  outside the Qwen lineage. Evidence: `doubt-snap-cross-family-confirmatory`
  Outcome. Frame per ruling 3.
- Section 6.3 (near :807-813): scope the J-space workspace account to one
  model; the cross-family eff_dim prediction failed (peaks early, not
  interior, in both families; readable interior band exists). Evidence:
  `jspace-family-atlas` Outcome.
- Section 4.7 / Appendix A (near :407-423, :932): AQ sycophancy is still an
  unsigned draft; relabel as unsigned interim pilot or drop.
- Rename sweep (~11 sites incl. :209-214, :290-291, :366, :70, :129, :332,
  :343, :349, :759, :766, :801) per the terminology block. Keep the :366
  observation (the direction verbalizes as answer/reply tokens) and promote
  it as prescient corroboration of the M4-WK reading.
- Sections 4.8/4.9 + Section 5 mistral row: note the factorial as the third
  independent mistral direction-axis failure (S1 ratio 2.03).

NICE (execute inside the same rewrite, lowest priority):

- The 2026-07-10 audit's remaining spine items (AL, AN/AO caveat, rep1/rep2
  evidential tiers, prediction/falsifier layer, frontmatter/appendix
  normalization).
- One forward-pointer sentence to the successor margin-theory paper in 6.4
  (ruling 4); no margin-cell numbers in this paper.
- Placebo subtype sentence if 4.10 is revisited (future-unknown carries
  qwen's -24.7pt suppression / mistral's +11.8pt recruitment;
  `placebo-signflip-question-type-analysis` Outcome).
- Voice pass: remove bold run-ins, c_hat symbol prose in body, journey
  narration.

## 5. Evidence docs the writer must open (slug -> what it supplies)

- `gate-contribution-factorial` -> permuted-gate falsification numbers,
  Gap_Sel, S1 ratios, cost-governance numbers.
- `ungated-vs-gated-dose-matched` -> registered 60.1%/3.1% and scope.
- `margin-evidence-responsiveness-worldknown` -> naming retirement,
  population reversal, coherence ceiling.
- `evidence-response-direction-search` -> constructive-search null (cite
  only if the naming discussion needs the "no recoverable axis" point).
- `qwen35-4b-midband-doubt-snap`, `qwen35-4b-midband-heldout`,
  `snap-seed-sampled-decode-replication` -> mid-band positive arc.
- `doubt-snap-cross-family-confirmatory` -> not-promoted verdict.
- `jspace-family-atlas` -> J-space scoping.
- `abstention-wide-instrument-calibration` -> instrument context for
  4.8/4.9 prose if touched.
- `docs/research/margin-theory-framework.md` sections 2, 3, 5 -> the
  two-regime mechanism and vocabulary.

## 6. Verification contract (lead applies before PR)

1. Diff shows no registered number changed anywhere it was already correct.
2. Every new number spot-checked against its Outcome doc.
3. Terminology sweep check: zero remaining prose uses of the retired names
   outside quoted governed-doc names and the one allowed parenthetical.
4. The six thesis recurrence sites all carry the two-regime formulation.
5. Red-team review verdict recorded before the PR opens.
6. Three title candidates surfaced to the PI in the PR description.
