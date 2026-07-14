# RR3: mistral gated-actuation confirm under corrected placebo + placebo-sign-map rider notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

- 2026-07-14 (drafter). Scaffolded and drafted design only (no run, no GPU, no
  sign). AMENDMENT.md, cell.yaml, gates.yaml, experiment.yaml written on branch
  exp/rr3-corrected-placebo. Core = mistral direction-specificity under the
  corrected effect-ratio placebo gate (RG1 >= 3x, rule-dictated); benefit/cost
  floors carried governed from RR2. Rider = mistral + llama random-direction dose
  ladders to complete the family x placebo-sign map (descriptive, no gate).
  Instrument = wide (detector v2 byte-identical to calibration pins + blinded
  context-free adjudication), with the two calibration successor fixes (held-back
  clear-negative decoy pool; larger + pooled clear-positive CG1 floor). Scoreboard
  bands, secondary tolerance width, K-seed denominator, per-shard decoy count, and
  predictor calls left as TODO-for-lead. instrument.configs left empty for the lead
  (sign requires it non-empty; detector_v2_patterns.yaml is created at harness
  build). Open questions Q1-Q5 in AMENDMENT.md. Not signed, not pushed, no PR.
