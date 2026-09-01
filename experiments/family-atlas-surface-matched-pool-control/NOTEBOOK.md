# Family Atlas Surface-Matched Pool Control notebook

Running log for this experiment. Newest entry first. This is a lab notebook,
not a claims surface; the signed prose lives in `AMENDMENT.md` and the machine
state in `experiment.yaml`.

## Entries

### 2026-07-22: Gemma G1 hard stop and PI-adjudicated closure

- Gemma Stage A launch 2 completed all 5,200 eligible generation rows and
  exited 0. The CPU watcher completed G0-G2 processing and exited 0.
- G0 passed exact generation coverage, source and pair provenance, regrade
  parity, prior-atlas exclusion, and containment.
- G1 retained 74 matched triads per role: 36 FIT and 38 held out, below the
  registered 64-per-partition floor. G1 therefore failed. G2-G5 were not run.
- No Stage B capture ran. Qwen Stage A remained unauthorized and was not run.
  Because the prediction required both models, the PI closed the experiment
  as an indeterminate null result. No peak location was computed.
- The signed terminal combiner recorded an indeterminate aggregate and passed
  its final artifact allowlist and private-text containment scan with no
  errors. The committed sha256 values are
  `8cb5b3f6bdab1448ff6edd5a24d3807cb26a3884ad4cc8a24940b3a6bcd5b3e1`
  for `aggregate_results.json`,
  `64d912154ae478ebbd1763e60722649a3b67845ea7ea2b87a39dd0e0931b3169`
  for `containment_report.json`, and
  `f2df954670b893556a587bb85bf6156b26a84caf5ccd453bf0c137a22054dad7`
  for Gemma's `g0_g2_summary.json`.
- The complete row-level generation exhaust remains private under
  `analysis/`. Public row packaging remains blocked pending the registered
  UMWP license audit and an approved dry-run card.

### 2026-07-21: signed and Gemma Stage A launched

- PI authorized signing and Gemma Stage A baseline generation. `bin/exp sign`
  pinned 11 instrument files. After the prelaunch `relevant_ids` repair,
  `bin/exp repin` updated only `source_and_generate.py` and
  `test_instrument.py` with the materialization failure recorded as its reason.
  The signed fingerprint then verified and all 31 focused tests passed.
- Full private UMWP materialization passed: 5,200 rows, 2,600 answerable,
  2,600 unanswerable, exact four-source counts, exact same-source pair mapping,
  and source sha256
  `e8840e8383357238a08e9c5028e4758ceceb369e1db31c64678b0f851c9c9e73`.
- Gemma Stage A launch 1 exited before model loading because the signed
  prior-atlas artifact path was not mounted into the container. Its log and
  exit code 1 remain under `analysis/gemma4_e4b_it/stage_a_generation.log*`.
  It produced no generation rows.
- Gemma Stage A launch 2 uses `launch_detached.sh`, the exact signed
  `mechinterp-runner` image digest, UID/GID 1000, the Gemma prior pool mounted
  read-only at its signed absolute path, and the host HF cache. Its log begins
  with exact digest, CUDA, torch, transformers, Python, and image-revision
  provenance at `analysis/gemma4_e4b_it/stage_a_generation_run2.log`.
- After the first 16 durable generation rows passed schema checks, armed a
  second `launch_detached.sh` exit-code watcher. It runs CPU-only Gemma G0-G2
  after a clean Stage A exit and otherwise records the generation failure. It
  always hard-stops before Stage B. Watch log:
  `analysis/gemma4_e4b_it/stage_a_postprocess.log`.
- Qwen Stage A and both Stage B captures remain unauthorized.

### 2026-07-21: prelaunch source-field repair

- The first private UMWP materialization stopped on unanswerable row 2501
  before any model load or GPU launch. The official file uses `relevant_ids`
  on all 2,600 unanswerable rows; the signed adapter and synthetic fixture used
  the nonexistent singular spelling.
- Revision 1 changes only that field spelling in `source_and_generate.py` and
  `test_instrument.py`. No prediction, gate, threshold, matching rule, or
  analysis rule changed. The two files require an audited prelaunch repin.

### 2026-07-21: prediction scoreboard completed

- Before signing or launch, the PI agreed with the orchestrator prediction
  that the early-exterior peak location survives the fresh surface-matched
  pool on both models. The verbatim response was "i agree"; no separate PI
  confidence was stated. The orchestrator confidence is 65%.
- No result had been observed and no source, model, GPU, Docker, signing,
  commit, or upload action occurred before recording the calls.

### 2026-07-21: verify-only blocker remediation

- The final independent consumer-path re-review returned `ALL_RESOLVED` after
  rerunning 31 focused tests and compiling every experiment module. The
  reviewer made no edits and performed no signing or launch.

- Pinned each model-specific prior-atlas artifact and sha256 and removed the
  arbitrary generation-time pool argument.
- G0 now rechecks every raw/materialized identity and class field, exact
  eligible generation coverage, private finish evidence, complete nested and
  flattened grades, and role parity.
- G1 now records insufficient yield before any surface classifier runs; G2 is
  `not_run` in that state.
- Matching and analysis checkpoints bind every consumed artifact hash, the
  registered seed, and the current verified signed-instrument fingerprint.
- Capture validation reconstructs token digests and anchors from the private
  input log and requires the exact current matched row set.
- Terminal aggregation adds a committed-artifact allowlist and containment
  gate. A tied real G5 peak is indeterminate under the registered tolerance.
- Rechecked the private exhaust contract against `.skills/data-exhaust/`.
  Generation rows preserve raw text, complete subgrades, termination evidence,
  and stable provenance; activation shards preserve row and layer identity for
  later analyses. Public row packaging remains fail-closed until the UMWP
  license audit is recorded.
- Verified the experiment-owned CPU suite with
  `PYTHONPYCACHEPREFIX=/tmp/surface-matched-pycache python3 -m pytest -q -p
  no:cacheprovider
  experiments/family-atlas-surface-matched-pool-control/test_instrument.py`.
  Result: 28 passed in 0.85 seconds. Compiled all nine Python modules
  successfully with `py_compile`.
- Re-ran the canonical data-exhaust builder suite with pytest cache disabled.
  Result: 6 passed in 0.09 seconds.
- Lead-side verification then added EOS-at-cap precedence, exact private
  capture-input model/revision/fingerprint binding, and G0 containment on the
  low-yield hard-stop path. The focused suite remained at 28 passing tests
  and completed in 1.17 seconds; all modules compiled again.
- Final consumer-path remediation stages standard row exhaust before a
  low-yield return and removes either input-log or index-anchor corruption for
  clean recapture. The expanded focused suite passed 31 tests in 0.96 seconds;
  all modules compiled again.
- `bin/exp validate` passed for the 89-experiment registry. Its warnings concern
  missing persistence declarations in other experiments; this draft declares
  persistence for every registered module.
- No source download, model load, GPU work, Docker launch, signing, commit, or
  upload occurred.

### 2026-07-21: consumer-path remediation and verification

- Revalidated the raw source and all 5,200 private materialized rows directly
  before G0, enforced exact model-generation coverage, and required complete
  regrading and role parity before any matching output can be accepted.
- Moved prior-atlas overlap exclusion ahead of prompt rendering, feature-basis
  fitting, and generation. The private exclusion manifest records the compared
  inputs without exposing source text.
- Replaced sibling run-time imports with experiment-owned renderer and grader
  ports, added model chat terminators to generation stopping, and bound
  generation and capture to the same renderer.
- Extended surface-support checks to the FIT pool, heldout pool, and registered
  50% FIT subsample. Added the standard 2,000-resample bootstrap confidence
  intervals and random-direction controls.
- Tightened capture identity to the signed instrument fingerprint, row key,
  token digest, anchor, model revision, hidden-state index, tensor hash, and
  whole-row digest. Invalid indexed shards are removed and recaptured on resume;
  malformed index records fail closed.
- Required every resumable generation record to carry the standard row-exhaust
  model, arm, dose, and flattened grading fields, and verified exact parity
  between those flattened fields and the complete grader dictionary.
- Verified the experiment-owned CPU suite with
  `PYTHONPYCACHEPREFIX=/tmp/surface-matched-pycache python3 -m pytest -q
  experiments/family-atlas-surface-matched-pool-control/test_instrument.py`.
  Result: 23 passed in 0.79 seconds. The only warning was pytest's inability to
  create its cache in the read-only worktree; test and bytecode caches used
  `/tmp`.
- Compiled every experiment Python module successfully with `py_compile`.
  Independently ran the canonical data-exhaust builder/verifier test file;
  all 6 tests passed in 0.12 seconds.
  No source rows were downloaded, no model was loaded, and no GPU or Docker
  command was launched. The experiment remains unsigned.

### 2026-07-21: approved-design implementation

- Implemented the experiment-owned instrument as four cohesive stages plus
  shared helpers: source and resumable baseline generation, deterministic
  matching and G0-G2, incremental full-depth capture, and CPU-only G3-G5
  analysis. No module imports a mutable sibling experiment at run time.
- Baseline rows are written with raw generation text, parsed answer value,
  natural-stop inputs, the complete grader dictionary, stable source and
  model provenance, and later receive role, split, and triad enrichment.
  The enriched per-model JSONL is directly shaped for the standard
  `data-exhaust` row builder after the UMWP license gate is resolved.
- Full-depth activations persist as one deterministic safetensors shard per
  row. The private index records every row/layer join, dtype, shape, anchor,
  tensor sha256, signed-instrument fingerprint, and row capture digest.
  Validation recomputes tensor hashes and a whole-bundle digest.
- Committed output is limited to the four-field ID-only split manifest and
  aggregate gate/profile/read-panel artifacts. The containment linter checks
  prohibited structured keys and scans against the private source questions
  and generated completions before G0 can pass.
- CPU synthetic suite:
  `PYTHONPYCACHEPREFIX=/tmp/surface-matched-pycache python3 -m pytest -q
  experiments/family-atlas-surface-matched-pool-control/test_instrument.py`.
  Result: 14 passed in 2.83 seconds. The read-only worktree caused only a
  pytest cache warning; bytecode and test execution used `/tmp`.
- The incremental generation drill wrote one complete record, simulated a
  process loss by discarding the writer, reopened the log, skipped the
  completed key, and appended the next row with raw text and full subgrades
  intact. The activation-resume contract is independently tested by indexed
  shard validation and deliberate tensor mutation.
- No source rows were downloaded, no model was loaded, and no GPU or Docker
  command was launched. The experiment remains unsigned.

### 2026-07-21: design-review draft and source feasibility

- Tier selected before design: Tier 2 exploratory amendment, fresh-pool
  `probe-fit` cell.
- Official source: UMWP `StandardDataset.jsonl`, CC-BY-SA-4.0, upstream raw
  sha256 `e8840e8383357238a08e9c5028e4758ceceb369e1db31c64678b0f851c9c9e73`.
- Source audit: 5,200 rows total; 2,600 answerable and 2,600 unanswerable.
  Native-source answerable/unanswerable counts are ASDiv 100/100, GSM8K
  1,700/1,700, MultiArith 300/300, and SVAMP 500/500.
- Field coverage: 2,600 of 2,600 answerable rows have a nonempty answer. Every
  unanswerable row has exactly one same-source answerable `relevant_ids` value.
- Safety exception: unanswerable IDs 2613 and 4258 contain non-null bookkeeping
  answers. The registered instrument forbids consuming answers on every
  unanswerable row, including these two.
- No question, answer, alias, generation, or token-ID text was copied into this
  experiment. This entry records aggregate feasibility only.
- The primary design uses cross-original triads. Exact-original UMWP pairs are
  descriptive sensitivities only.

### Before signing: implementation state

The instrument modules and persistence declarations are present. Signing
still requires PI action through `bin/exp sign`; signing does not authorize
either GPU stage.

### Data-exhaust contract

- Generation modules must persist raw text, parsed answer value, the complete
  grader output, termination inputs, and stable row identity incrementally.
- Capture modules must persist sharded full-depth activations plus a row/layer
  index and tensor hashes, so later analyses do not require another model load.
- Aggregate and row-level HF exhaust are built only after a terminal verdict
  using `.skills/data-exhaust/`; live upload needs its own PI approval.
- UMWP currently has no canonical `license-gates.md` entry and therefore remains
  `pending-audit` for row-level publication. Before packaging rows, audit UMWP
  and its constituent-source terms, then record the resulting full-text,
  text-free, or excluded verdict in the canonical data-exhaust skill. Any
  full-text release must carry the upstream CC-BY-SA-4.0 attribution and
  share-alike disclosure.
- The activation bundle is a required private-staging artifact. A public release
  additionally requires model-license review and a PI-approved dry-run card.

- 2026-09-01: aggregate data exhaust published (batch 4 of the backfill, task-56c61a; PI-approved in-conversation 2026-09-01). Copy-everything mirror of analysis-committed plus README + PROVENANCE; aggregate shape, no row text, zero exclusions. 5 files / ~7 KB, built at repo commit 54e64547.
- HF repo: `professorsynapse/eh-family-atlas-surface-matched-pool-control` (dataset)
- HF revision: `6756754725d1f66a2dfd778043602285d091c39b`
