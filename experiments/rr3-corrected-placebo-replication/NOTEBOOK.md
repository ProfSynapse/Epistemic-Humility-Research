# RR3: mistral gated-actuation confirm under corrected placebo + placebo-sign-map rider notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

- 2026-07-14 (drafter, revision). Applied bounded lead decisions to the draft,
  still not signed, no run, no GPU, no push. Resolved: Q1 (regeneration kept,
  as drafted), Q2 (RG1 primary-gate denominator is max-over-K of the absolute
  random-arm lift across the K >= 3 fresh seeds), Q4 (llama rider dose ladder
  sweeps the full grid, as drafted), Q5 (Predictions scoreboard now carries
  registered slots for the llama placebo sign, the mistral RG1 pass/fail call,
  and whether the mistral fresh-seed random lifts land inside/outside the
  descriptive envelope; calls themselves stay TODO-for-PI-and-lead). Filled
  numeric slots: secondary descriptive tolerance fixed at +/- 8 points around
  each family's calibration-certified wide baseline (mistral 0.280, llama
  0.164); per-shard clear-positive decoy floor fixed at >= 25. Q3 (verdict
  framing: corrected-criterion re-adjudication of RR2's claim vs fresh
  confirmatory replication) stays OPEN, lifted to the PI; both framings are now
  stated neutrally, with no recommendation, in the "Determinism scope" section.
  New binding design requirement (from the lead's sign-flip feasibility
  scoping): both rider dose ladders (mistral hs16, llama hs20) now dose the
  known_correct_answered (answerable) population with the random direction at
  every rung, not confab alone, and rider results are reported stratified by
  question type via each row's `source` field (triviaqa/popqa = answerable,
  kuq = unanswerable), not by role, because role conflates question type with
  the model's own undosed baseline behavior. The mistral core cell is
  untouched. `gates.yaml`, `cell.yaml`, `AMENDMENT.md`, and `experiment.yaml`
  updated to match; still no `instrument.configs`, no sign, no PR.

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
