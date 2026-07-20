# Correctness-direction-rotation + subspace-overlap integration changelog (2026-07-20)

Governed revision executed on branch `paper/cd-so-integration`, PI-approved per
the session's fold-in directive. Rationale: §4.2 carried an explicit `SWAP`
marker ("pending correctness-direction rotation tracking") noting that the
dial's 0.679 cold-transfer discussion applied the answerability rotation
account to correctness by inference, not measurement. Two exploratory Tier-2
cells since resolved that gap directly:
`experiments/correctness-direction-rotation/AMENDMENT.md` (resolved
2026-07-20, null-result) and `experiments/correctness-subspace-overlap/AMENDMENT.md`
(resolved 2026-07-20, null-result, instrument-limited). This changelog records
what changed and the doc:line citations backing each number; both AMENDMENT.md
Outcome sections were read in full before writing (per the repo's
READ-BEFORE-YOU-CITE rule) and are the sole source for every figure below.

## What changed

### §4.2, replaced the SWAP paragraph

Removed the `<!-- SWAP: pending correctness-direction rotation tracking -->`
marker and its two-sentence placeholder. Replaced with two paragraphs:

1. States the first follow-up's null on the single-rotation-at-SFT story
   (raw-to-cleanSFT cosine 0.19 vs later transitions 0.45 and 0.33, neither
   reaching the 0.85 stability floor the answerability account predicts) and
   the reliability control that explains why (split-half cosine 0.17 while
   AUROC stays flat near 0.80).
   - Citations: `correctness-direction-rotation/AMENDMENT.md` lines 174-176
     (predicted-vs-observed cosines), 195-210 (gate results, CD-G1 fail), 216
     (split-half floor 0.174), 202-203 (best-layer AUROC range 0.809-0.860,
     rounded to "~0.80" in prose).
2. States the second follow-up's null on the shared-subspace question, and its
   two positive, label-clean findings: exactly one shared direction above the
   permutation null (k=1), nothing above null at k=4 through k=32 (k=2 only
   marginal), and a diffuse within-checkpoint discriminative geometry (an
   arbitrary 8-dim slice of S's span recovers AUROC ~0.70 vs S's own top-8
   discriminative directions at ~0.74). Also states, in one clause, why
   neither Reading A nor Reading B was adopted (the reliability instrument
   saturates below its gate threshold for any signal, including a planted
   one).
   - Citations: `correctness-subspace-overlap/AMENDMENT.md` lines 552-559
     (SO-G1 fail, all three limbs), 599-610 ("what the run does establish": k=1
     overlap 0.00896 vs null 95th pct 0.00472, k=2 marginal, k=4-32 inside
     null; recovery 0.742 vs floor 0.701 at L20), 576-597 (adopted middle
     ground; the planted-signal simulation showing the reliability limb is
     estimator-structurally unreachable, not a sample-size problem).

No internal instrument names (amendment letters, slugs, codenames) appear in
the body prose, per `papers/common/VOICE.md`'s self-containment rule; both are
described in plain language ("a follow-up measured...", "a second
follow-up asked..."). Repository pointers live only in the Appendix A table
addition below.

### Appendix A, added two provenance rows

Two new rows under "Correctness dial, deployed checkpoint (§4.2)", pointing at
each AMENDMENT.md's Outcome section (repo-root paths, not under the probe
result-JSON directory, since these are prose-governed docs rather than
tracked result JSONs).

## What did not change

- No numbers in §4.2's existing paragraphs (the answerability rotation
  timeline, the dial's own base/deployed AUROCs, the 0.679 cold-transfer
  figure, the ECE caveat) were touched; only the SWAP placeholder was
  replaced.
- §5's restatement of the cold-transfer caveat ("the correctness direction
  drifts under training (cold transfer 0.679, §4.2)") was left as-is; it is
  still accurate and now points at a §4.2 that explains the mechanism more
  fully rather than flagging it as untracked.
- No claim here is pooled with the locked Phase 1 headline matrix or the S/T
  headline readings; both source cells are exploratory Tier-2 and are stated
  as such in the new prose.

## Contradiction check

No existing paper-4 sentence asserted that the correctness direction's own
rotation *had* been measured, or asserted a specific rotation-explains-0.679
mechanism as fact; the SWAP marker existed precisely because that measurement
was pending. No contradiction was found; this is a fill-in, not a
correction.
