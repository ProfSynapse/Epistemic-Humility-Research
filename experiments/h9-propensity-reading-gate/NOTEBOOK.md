# H9 held-out reading gate for the confab-propensity direction on AI-TRUE notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

- 2026-07-11 (draft): scaffolded from the two H9 memos and Amendment AL
  (`experiments/radial-anti-propensity-steering/AMENDMENT.md`, the direction's
  origin). Wrote AMENDMENT.md (gates section 5), cell.yaml, gates.yaml, and
  skeletons for the three CPU scripts (freeze_scorer, draw_holdout, score_holdout)
  plus the Modal harness (cloud/modal_h9_holdout.py). Status stays draft: nothing
  signed, nothing launched. The frozen scorer, held-out draw, GPU extraction, and
  gate scoring are all specified but not wired (TODO(sign) blocks mark where the
  fit/harness code lands). Flagged in the report: the lead's pointer named
  `experiments/selected-setpoint-regulator` (that is Amendment AN, not AL) and
  asked the frozen scorer to reproduce `prop_z.npy` (which is OOF; the hard
  fidelity target is `d_raw.npy`). Both handled per AMENDMENT.md section 8.
