# Evidence-responsiveness: the naming test (M4) notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

- (add dated entries as the experiment progresses)

## 2026-07-17 Pre-sign red-team of the DRAFT, then sign (PI conditional authorization)

An adversarial reviewer examined the unsigned draft (AMENDMENT/cell/gates/
experiment.yaml + derivation), specifically hunting the three defect classes
that bit the cascade: M1's one-rung numerator prose, M2's sign-convention
omission, and M1b's byte-identical-reuse-under-bf16 error. Verdict: SIGN-READY
WITH EDITS, no blocker; the (d)-earned verdict survives every confound probed
(D1 leg 2 and D2 are true-minus-false contrasts that cancel format/mechanical/
dose-noise artifacts).

Findings applied before signing (draft-stage, no repin ceremony):
- MAJOR M1 (anchor position): the answer arms appended context AFTER the
  question, moving the len-1 capture anchor off the question's last token (where
  c_hat was validated by M2) and making leg 1 a cross-anchor comparison. Fix:
  inject context BEFORE the question so the anchor is identical across all three
  arms and inside M2's validated regime; leg 1 becomes a clean same-anchor
  paired shift. Does not change the pass bar or the split-vs-earned meaning.
- MAJOR M2 (floor vs fresh baseline): the collapse floor is 0.5 x M2's committed
  gap, but leg 1's minuend is the fresh in-regime recapture. Added S1
  baseline-reproduction gate: fresh confab-projection median must reproduce
  M2's 3.0005 within 0.10 z before leg 1 is read; exceedance halts to PI.
- MINOR m3: replaced the false "tautologically 0%" baseline-survival claim with
  a MEASURED channel-2 baseline arm (308 generations) that doubles as an
  in-regime staleness check on the reused M1 tipping doses (void channel 2 if
  baseline survival > 0.05). Generation count 616 -> 924, total passes -> 3204.
- MINOR m4: relabeled the 0.056 floor from "Wilson" to normal-approx (Wald)
  half-width (true Wilson 0.0555; both round to 0.056).
- MINOR m5: added the distractor collision/length caveat (both bias D2/leg 2
  conservative, so acceptable and reported).
- MINOR m6: LOCKED the collapse floor at 0.5 x gap; the 0.25/0.75/1.0 candidates
  are not retained as fallbacks (no post-hoc selection among four bars).
- Hygiene h7/h8: SC0 must emit the 308-eligibility list and distractor mapping
  deterministically (seed 48260722) before generation, and name the M1/factorial
  source configs for the carried CG1 floors and detector_v2 pins.

Checked clean by the reviewer (independently verified): collapse and survival
sign directions correct; negative-z convention consistent everywhere;
0.5*1.9483770693182394 = 0.9741885346591197 exact; all counts (400-92=308,
924=308*3, 2280=(400+360)*3, 3204 total); all three input hashes match on disk;
no oracle leak (roles behavior-assigned upstream, placebo controls the
injection); self-blinding holds (only committed baseline computed pre-sign);
prose hygiene clean; templates placeholder-only.

PI authorization: conditional sign (2026-07-17, in conversation): "consider
this signed unless red-team finds something that should change my prediction."
The two MAJORs tighten the projection test's validity without changing the pass
bar or the meaning of the PI's SPLIT prediction, so the condition held and the
lead signed on the PI's behalf. Scoreboard registered: orchestrator EARNED /
projection; PI SPLIT / projection.
