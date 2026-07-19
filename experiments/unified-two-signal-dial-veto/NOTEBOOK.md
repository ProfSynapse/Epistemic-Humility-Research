# Amendment U — Unified Single-Stream Two-Signal Mechanism (Dial-Veto on Unknowns) notebook

Historical migration notebook.

## Entries

- 2026-07-08T17:40:52Z: migrated legacy amendment `experiments/unified-two-signal-dial-veto/AMENDMENT.md` into `experiments/unified-two-signal-dial-veto/`.
- 2026-07-18: CORRIGENDUM arc. (1) PI-funded lab-notebook diagnostic (task #31)
  re-graded the original stage2 generations with both refusal instruments:
  90.1% (109/121) of the hallucination labels are explicit refusals missed by
  the narrow detector's contraction blind spot ("i am not sure..." in the
  marker list, "i'm not sure..." emitted by the trained checkpoint).
  Adversarially confirmed by independent re-derivation (0 row diffs); census
  of all 109 flips found zero hedge-plus-guess rows. Sibling lineages S/W/X
  re-graded: flip rates 0.05% / 2.36% / 1.75-3.82%, so the artifact is
  specific to this cell's trained checkpoint. (2) PI approved the governed
  corrigendum path (ruling 2026-07-18). (3) Re-score with integrity gate:
  the signed pipeline reproduced U-G3 0.9802 bit-for-bit before any corrected
  computation; corrected sets A (n=12) and B (n=8, one both-detector-miss
  template removed, 4 rows) scored 0.9067 [0.8133, 0.9705] and 0.8639
  [0.7384, 0.9498], both under the pre-stated >=50 adequacy floor, so U-G3 is
  reclassified UNPOWERED per section 4's own data-stage stop. Aggregate
  promoted to analysis-committed/ug3_corrected_rescore.json. (4) Corrigendum
  section appended to AMENDMENT.md; frontmatter outcome, Status line, and
  experiment.yaml verdict corrected with the original text retained verbatim.
- 2026-07-18: RED-TEAM of the corrigendum (pre-PR). Verdict: sign-off with
  fixes. The reviewer independently reproduced every corrected number (Set A
  0.9067, Set B 0.8639, rates, flip 90.1% CI [84.3%, 95.0%], reverse-flip
  125 all one template, U-G1 0.9991, sibling S/W/X rates), confirmed the
  retained section 7 byte-identical to origin/main, section 4 untouched (no
  goalpost moved), the reclassification faithful to the pre-stated
  data-stage stop, and the Set B template identification exact (12/12
  keep-remove match; one mild borderline row, 7-vs-8 immaterial to
  UNPOWERED). One MAJOR completeness gap: the within-SelfAware control
  AUROC 0.93 shares the contaminated hallucination side and had no
  corrected value. FIXED: the lead extended analysis/ug3_corrected_rescore.py
  with a control_rescore block and independently reproduced the reviewer's
  values before insertion (section 7's 0.93 reproduces at 0.9300 on the
  contaminated side; corrected 0.8140 vs Set A / 0.7369 vs Set B / 0.7500
  fully corrected), added them to the corrigendum U-G2 area, flagged
  section 7's 0.93 as superseded, and added the 0.93 to the downstream
  correction list (paper 4 manuscript lines 415-416, 465, 947). Minor
  fixes also applied: U-G1 "no refusal detector" phrasing tightened (the
  narrow detector enters row selection, not label or feature); amendment S
  sibling rate given its no-unknown-population parenthetical; known-answered
  control contamination acknowledged (6/276 wide-detector flips, group mean
  0.679 to 0.690, immaterial).
