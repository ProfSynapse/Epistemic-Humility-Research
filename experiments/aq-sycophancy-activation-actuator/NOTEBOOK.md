# aq-sycophancy-activation-actuator notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

### 2026-07-07 - r2 scale-up planned

- User requested a larger AQ pool, closer to 500 source rows rather than the
  64-row pilot. Updated the next eval pass to `limit: 512`, which corresponds
  to about 128 complete neutral/incorrect-hint pairs under the SycophancyEval
  answer-row ordering.
- Modal staging tags were moved to `aq-sycophancy-actuator-smoke-r2` and
  `aq-sycophancy-readout-r2` so scaled artifacts do not overwrite or restore
  from the r1 pilot.
- Expected effect: if the pilot's 9/7 class rate roughly holds, the scaled pool
  should clear AQ-G0 with substantial margin. The actual 20/20 gate must still
  be evaluated from the r2 scored rows before any actuator launch.

### 2026-07-07 - Modal row-pool smoke and readout pilot

- Modal row-pool smoke completed on A10G against official `Qwen/Qwen3-4B` at
  revision `1cfa9a7208912126459214e8b04321603b3df60c` using commit
  `3a0a7e097` plus wrapper recovery/fix commits through `d5f26f4cb`.
- Smoke artifacts were uploaded to private HF staging at
  `professorsynapse/eh-al-prep-staging:aq-sycophancy-actuator-smoke-r1/artifacts/`.
  The smoke produced 64 scored rows, 32 row-pool rows, and 16 probe labels:
  9 positive `wrong_hint_followed` and 7 negative
  `wrong_hint_not_followed_or_refused`.
- The readout/probe run completed as Modal app `ap-JqoCvvgwbGHSKqkCux9CcM`
  with call `fc-01KWYMPM3A5P5QFPZD29AGXS9M`, run tag
  `aq-sycophancy-readout-r1`, and DONE marker
  `repo_commit=d5f26f4cb`. Artifacts were uploaded to
  `professorsynapse/eh-al-prep-staging:aq-sycophancy-readout-r1/artifacts/`.
- Extraction captured 32/32 answered rows at layers 12, 16, 17, 20, and 24
  for `anchor` and `answer_end` positions. The frozen probe direction selected
  layer 20, hidden dim 2560, with AUROC by layer: 12=0.70, 16=0.80, 17=0.90,
  20=1.00, 24=0.90. Direction calibration: positive mean 2.93, negative mean
  -2.72, separation 5.65, sigma 2.92.
- Governance caveat: this is a pilot/smoke readout, not a gate pass or actuator
  verdict. Pre-stated AQ-G0 requires at least 20 positive and 20 negative
  incorrect-hint rows; this run produced 9/7, so the registered AQ gate is
  underpowered/void and steering should not launch from this row pool without a
  revised/scaled row-pool plan.
