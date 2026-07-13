# Amendment Z — Cross-FAMILY confirmatory of the training-free two-signal readout notebook

Historical migration notebook.

## Entries

- 2026-07-10T21:30:00Z: ERRATUM (wording only, no number or verdict changes). The
  "Locked gates" section of AMENDMENT.md describes Z-G3 as "confident-hallucination
  veto AUROC (known-answered vs unknown-hallucination, dial trusts the former over
  the latter)". The pinned scorer (`experiments/common/readouts/amendment_x_cross_model_score.py`,
  X-G3 block) computes the veto as correct answers (scored out-of-fold) vs
  hallucinations (scored cold); the known-answered vs hallucination contrast is the
  within-SelfAware CONTROL, reported separately. All recorded results, the verdict,
  and the Results narrative in AMENDMENT.md itself match the scorer's contrast; only
  the gate-definition prose is inconsistent. The gate as computed is what was locked
  by the pinned instrument, so the doc text is not being edited post-outcome; this
  entry records the discrepancy. Found by the paper-4 manuscript review
  (docs/review/paper4-two-signal-readout-review-2026-07-10.md, section 3).

- 2026-07-08T17:40:52Z: migrated legacy amendment `experiments/cross-family-confirmatory/AMENDMENT.md` into `experiments/cross-family-confirmatory/`.
