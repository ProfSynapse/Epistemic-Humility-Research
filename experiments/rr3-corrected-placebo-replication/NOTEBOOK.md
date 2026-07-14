# RR3: mistral gated-actuation confirm under corrected placebo + placebo-sign-map rider notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

- 2026-07-14 (lead). STOP item fixed and amendment SIGNED. cell.yaml rider
  block repaired: shared config hoisted to a new top-level `rider_shared` key
  and `rider_cells` restored to a pure list of id-carrying cells, matching the
  runtime loaders' access pattern (`next(r for r in cell["rider_cells"] if
  r.get("id") == ...)`); semantics unchanged, PyYAML parses clean. Llama rider
  revision pinned to 006f5dcd1393c3add266de40994ba96225e9689d after lead
  verification that RR's cell.yaml and the fleet model_matrix.yaml agree on it.
  Core K-seeds [30260714, 30260715, 30260716] confirmed. The strict-xfail
  STOP-item test flipped to a structural assertion (parse + rider ids +
  rider_shared keys). Suite: 78 passed, 0 failed. `bin/exp sign` run with the
  full config/module pin set; `bin/exp validate` OK. Next: launch (local_3090
  lane, free, standing approval, noted to the PI at go).
- 2026-07-14 (harness-builder). Harness built end to end: generation harness
  (materialize_rows.py, fit_reuse.py, heldout_scorer.py, steer_lib.py,
  render.py, gen_lib.py -- family-generalized to `--family {mistral,llama}`
  where RR2's own modules were mistral-only), detector_v2.py +
  detector_v2_patterns.yaml (copied verbatim from RR2/calibration, sha256
  byte-identity confirmed against both), the sharded blinded-adjudication pool
  builder/regrade builder/apply+scorer (build_adjudication_pool.py,
  build_regrade.py, apply_adjudication.py, rr3_scorer.py, gates_lib.py) with
  the two registered successor fixes: (a) clear-negative decoys drawn only
  from a HELD-BACK pool (undosed baseline over each family's FIT-split
  known-correct rows, structurally disjoint from every scored held-out arm,
  never carved out of scored rows), and (b) a per-shard clear-positive floor
  (>= 25) plus a POOLED clear-positive CG1 floor across every shard, with the
  void-once-then-terminal-cell-void ladder. Opaque ids extended to the full
  (cell, arm, row_key, seed, dose_multiplier, regrade_index) tuple from the
  start. `test_rr3_smoke.py` (77 tests) covers, per the build brief: shard
  building with global opaque-id uniqueness including cross-dose and
  cross-seed reuse; positional-join rejection on both line-count and
  line-order misalignment; CG1 floor logic including the pooled floor and the
  void-regrade-once/void-cell-terminal ladder (a per-shard PASS can still be
  voided by a pooled-floor miss, tested end to end via `cmd_apply`);
  held-back clear-negative decoy disjointness from core; and the max-over-K
  RG1 arithmetic (a case constructed to pass under a mean denominator but
  fail under the registered max, to prove the code uses max, not mean/sum).
  `synaptic_tuner_pin` TODO filled with `86b134c32254668893800a453b3c5d8285ae85df`
  (already the submodule commit pinned by this worktree's tracked tree; the
  document's own text deferred this one field to harness-build). `python3 -m
  pytest test_rr3_smoke.py -v` (explicit path, not the rtk-proxied directory
  glob): 77 passed, 1 xfailed, 0 failed. `bin/exp validate`: OK (72
  experiments; validates registry schema/hashes, not deep YAML semantics of
  referenced configs). `experiment.yaml` instrument.configs/modules/pins
  filled for every created file.

  STOP item found during the build, NOT fixed here: `cell.yaml`'s
  `rider_cells:` block does not parse as valid YAML -- the
  dose_ladder/subsample/reporting shared config is written as an unmarked
  block mapping directly under `rider_cells:`, then followed by
  `- id: rider_mistral_placebo_ladder` / `- id: rider_llama_placebo_ladder`
  as block-sequence items under the SAME key (PyYAML ParserError at line
  134). Confirmed present at HEAD (commit b66f9b19, the lead's own "Apply
  lead decisions" commit) and NOT introduced by this build's one authorized
  edit (the synaptic_tuner_pin line only; verified via `git diff`). This
  breaks every function that calls `load_cell_yaml()` regardless of which
  part of the document it actually needs (PyYAML must parse the whole file),
  which is most of this harness's runtime code paths (materialize_rows,
  heldout_scorer, build_adjudication_pool's cell.yaml-touching loaders,
  rr3_scorer's report builders). The smoke suite routes around it with
  monkeypatched synthetic cell dicts and documents the parse failure as a
  single `xfail(strict=True)` test so it stays visible without blocking an
  otherwise-green suite. Not self-repaired: this is a locked-spec content
  question (what the correct nesting should restore), not a mechanical
  typo call for the harness-builder to make unilaterally. See the harness
  report to the lead for the full detail and a proposed minimal fix.

- 2026-07-14 (lead). Q3 resolved by the PI: the core verdict is reported as a
  corrected-criterion re-adjudication of RR2's claim (same test done more
  intelligently, rider as additional data exhaust), not as a fully fresh
  replication. Motivation and Determinism-scope prose aligned to that decision;
  the RR2-verdict-stands point preserved unchanged. Scoreboard calls filled for
  both predictors (PI: llama null / RG1 pass / seeds inside; orchestrator:
  llama weak recruitment / RG1 pass / at least one seed outside on the
  recruitment side), registered pre-launch and checkpointed in the session note
  before entry here. All open questions now resolved. Remaining before launch:
  harness build, instrument.configs pins, sign, PI GPU approval.
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
