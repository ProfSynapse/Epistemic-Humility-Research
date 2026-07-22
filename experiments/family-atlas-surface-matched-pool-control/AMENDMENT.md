# Family Atlas Surface-Matched Pool Control

Status: null-result 2026-07-22. Gemma Stage A completed and hard-stopped at
G1. Qwen Stage A and both Stage B captures were not run.

Signed 2026-07-21. Revision 1 before any model launch corrects the official
UMWP unanswerable-pair field spelling from `relevant_id` to `relevant_ids` in
the source adapter and fixture. The failed private materialization produced no
model artifact. No prediction, gate, threshold, or analysis rule changed.

## Motivation and posture

The resolved family-atlas cells report an early-exterior `eff_dim_frac` peak
followed by a later interior band where the known-unknown (KU, answerability),
caution, and raw-refusal axes are linearly readable. The analysis-only
`family-atlas-surface-diversity-control` registered a surface-control test on
existing Gemma and Qwen captures, but its matching-support gate failed before
any controlled peak was computed. It therefore returned an indeterminate
result and pre-stated a fresh surface-matched pool as the next test.

This experiment implements that Shape B escalation. It asks whether the peak
location remains early-exterior after prompt surface is balanced by
construction. Peak height and peak margin are descriptive. The location is the
decision invariant.

Instrument tier is selected first. This is Tier 2 under
`.skills/experiment-runner/reference/amendment-vs-lab-notebook.md`: it creates
a new pool, performs new model generations and captures, and will be reported
as separate exploratory evidence. It does not revise a prior atlas verdict or
enter a confirmatory headline matrix. It tests Gemma-4-E4B-it and Qwen3-4B
only; it does not by itself establish a four-family result.

## Design

### Source and feasibility

The source is the official UMWP `StandardDataset.jsonl`, licensed
CC-BY-SA-4.0 and pinned in `cell.yaml` by upstream raw sha256
`e8840e8383357238a08e9c5028e4758ceceb369e1db31c64678b0f851c9c9e73`.
The pre-sign source audit found 5,200 rows: 2,600 answerable and 2,600
unanswerable, split by native source as ASDiv 100/100, GSM8K 1,700/1,700,
MultiArith 300/300, and SVAMP 500/500. All answerable rows have a nonempty
answer. Every unanswerable row has exactly one same-source answerable
`relevant_ids` value. Two unanswerable rows, IDs 2613 and 4258, contain non-null
bookkeeping answers; the instrument must never consume an answer from an
unanswerable row. The aggregate audit is recorded in `NOTEBOOK.md`; no row
text was copied into the experiment.

### Models, rendering, and roles

Two model-specific pools are built independently:

- `google/gemma-4-E4B-it` at revision
  `fee6332c1abaafb77f6f9624236c63aa2f1d0187`, 42 decoder layers and 43
  hidden-state indices;
- `unsloth/Qwen3-4B` at revision
  `64033659d5caf1b8ed7f929b29de705e93a4d468`, 36 decoder layers and 37
  hidden-state indices.

Each model uses its resolved family-atlas prompt renderer and final-prompt-token
anchor contract, identified exactly in `cell.yaml`. Baseline generation is
greedy and deterministic, with batch size 1, one minimum new token, and a
200-token maximum. A local pinned copy of the program-standard
degeneracy, refusal, and alias-correctness grader will assign roles. UMWP's
numeric answer arrays are converted to canonical string aliases only for
answerable rows. Before signing, grader fixtures must cover integer, negative,
decimal, refusal, malformed, degenerate, and wrong-answer cases, including a
numeric-token boundary case such as 1 versus 10. The registered role rubric is:

- `known_correct_answered`: an answerable row with a clean, correct answer;
- `confab`: an unanswerable row on which the model gives a substantive answer
  instead of refusing;
- `unknown_refused`: an unanswerable row on which the model cleanly refuses.

Answerable rows that are incorrect, nonresponsive, or refused and
unanswerable rows that do not meet either behavior rubric are excluded. Only
answerable reference answers may enter correctness grading. UMWP category is
not a prompt-surface covariate and never enters matching or a surface-role
classifier. It is used only to balance and report the aggregate category
composition of `confab` versus `unknown_refused`.

Before role assignment, each model's candidates are compared with that
model's prior atlas pool after Unicode normalization, case folding, and
whitespace collapse. Any exact normalized-question overlap is excluded. Text
and normalized hashes remain private; only aggregate exclusion counts may be
committed. `cell.yaml` pins each model's private prior-pool artifact, source
experiment, and sha256; generation accepts no alternate pool path.

### Frozen surface basis and matching

The surface basis is fitted without role labels before baseline generation and
then frozen. It contains:

- rendered-prompt token count;
- question character, whitespace-word, line, digit, punctuation, newline,
  and uppercase counts and fractions;
- hashed word 1-2gram and character 3-5gram TF-IDF features, reduced by the
  frozen SVD and scaling pins in `cell.yaml`;
- native source as a blocking variable.

Question text is the only lexical input. Answers, aliases, UMWP category,
model generations, grades, behavior labels, activations, and completion length
are excluded.

Within each model and native source, matching uses two deterministic Hungarian
passes. First, within every unanswerability category, match `confab` to
`unknown_refused` without replacement, retaining the smaller class count in
that source-category block. Second, represent each matched unknown pair by the
mean of its two standardized surface vectors and match those pair centroids to
`known_correct_answered` rows from the same native source. Cost in both passes
is squared Euclidean distance in the frozen standardized scalar and lexical-PC
basis. The result is a 1:1:1 triad containing one row of each role. All three
rows must have distinct UMWP original-problem group IDs, so an answerable row
and its modified unanswerable counterpart cannot appear in the same primary
triad. Rows are used at most once. A forbidden original-ID edge receives
infinite cost. Equal finite costs break lexicographically by the role-ordered
UMWP IDs. Category never enters the cost or the surface classifier.

Intact triads are assigned to FIT and held-out partitions with seed 20260721,
stratified by native source. Each model must retain at least 64 triads in FIT
and 64 triads held out. The surface-support classifier uses the complete
hashed lexical and scalar basis, not only the SVD matching projection. It is
evaluated separately on FIT and held-out as three grouped one-vs-one role
classifiers, with all members of a triad kept in the same fold. The largest
pairwise best-orientation AUROC or scalar SMD across either partition is the
gate quantity. The fixed 50% FIT intact-triad subsample repeats the same
surface-support check before its peak location can enter G5.

The exact-original answerable/unanswerable pairs supplied by UMWP are reserved
for descriptive sensitivities split by the unanswerable row's model behavior.
They cannot pass, falsify, or rescue the cross-original primary analysis.

### Capture and estimators

After pool gates pass, capture every hidden-state index at the
final-prompt-token anchor. The standard family-atlas profiler computes
`eff_dim_frac`, the representation-variance participation ratio divided by
the number of FIT rows, on the matched FIT triads. Depth is
`hs_index / (n_hidden_states - 1)`. A peak at depth at most 0.20 is
early-exterior.

The standard held-out read panel is fit on FIT rows and scored on held-out
rows for the KU axis (`known_correct_answered` versus `unknown_refused`),
caution (`unknown_refused` versus `confab`), and raw refusal
(`unknown_refused` versus both answered roles). Applicability requires one
hidden-state index strictly inside depths 0.20 and 0.85 where all three axes
have held-out AUROC at least 0.80. Every axis reports the standard
2,000-resample stratified bootstrap interval at seed 20260707 and the
standard fixed-seed per-layer random-direction contrasts.

The registered robustness profile is a fixed-seed 50% subsample of intact FIT
triads, stratified by native source. Sampling never separates triad members.
Peak margins, full profiles, surface composition, and the exact-original
sensitivity are descriptive.

For both real G5 profiles, a peak is valid only when exactly one hidden-state
index attains the maximum under `numpy.isclose` with `rtol=1e-12` and
`atol=1e-15`. A tied full or subsample maximum is indeterminate. It cannot be
resolved by choosing the earliest tied index. The planted control retains its
separate unique-peak and 1.05 runner-up-ratio requirements.

### Positive controls

Two positive controls run before the real peak-location decision.

First, append a private three-column one-hot role tag to a copy of the frozen
classifier input. Under the same grouped folds and classifier, every pairwise
held-out best-orientation AUROC must be at least 0.90. This checks that each
pairwise surface-role gate can detect a planted imbalance. The tag and
row-level scores remain private.

Second, at the exact midpoint hidden-state index, hs21 for Gemma and hs18 for
Qwen, add centered seeded high-rank Gaussian row-space noise to the matched FIT
activation matrix. Try the fixed RMS scale grid `[0.25, 0.5, 1, 2, 4, 8, 16]`
and select the smallest scale that makes the planted index the unique
`eff_dim_frac` peak at least 1.05 times the runner-up. This checks that the
location estimator can report a known interior peak. It does not tune or
transform the real profile. Failure of either control is indeterminate.

### Staged execution and containment

Stage A is baseline generation for one named model at a time. It requires
fresh, explicit PI launch approval for that model. CPU pool construction then
runs G0-G2. Stage B is full-depth capture for one named model at a time and
requires G1 and G2 to pass plus fresh, explicit PI launch approval for that
model. Approval for Stage A does not authorize Stage B or the other model.

All model work runs inside the pinned `mechinterp-runner` image
`sha256:d445632098cd2c70c115fe84d5343ff98286ac3f510a2d4c9cb488b550a3d23c`.
On WSL2 each Docker command uses
`DOCKER_HOST=unix:///var/run/docker.sock` as a per-command override. No model
loads on WSL2 CPU. Any process expected to exceed 15 minutes launches through
`experiments/common/launch_detached.sh` with an exit-code watch.

Question, answer, alias, generation, and token-ID fields, row-level features,
grades, and activations stay under gitignored `analysis/`. Only ID-only split
manifests and aggregate diagnostics or profiles may enter
`analysis-committed/`. An output-schema allowlist and prohibited-key/text scan
must pass before promotion.

### Reusable data exhaust

The run must preserve reusable exhaust as it executes. This is an instrument
requirement, not a post hoc packaging task.

Every baseline generation writes incrementally to a resumable private row log.
Each record includes a stable `umwp:<id>` row key, license-gate source
`umwp`, UMWP original-pair ID, native source and category, model and revision,
renderer ID, seed, raw
generation text, parsed answer value, termination metadata, token counts, the
complete grader sub-dictionary, final role, split, and matched-triad ID. A
booleans-only row log is an instrument failure. A CPU smoke must verify this
schema and kill-resume behavior before signing. Question text, reference
answers, generations, and token IDs remain gitignored.

The private log also retains `finish_reason`, the final completion token ID,
and the EOS-ID set. G0 reconstructs `terminated_naturally` from those fields
and the pinned token cap. Completion-token evidence is removed from the
staged public row-exhaust file.

Full-depth captures are written as deterministic, incrementally completed
safetensors shards under `analysis/exhaust/activations/<cell_id>/`. A private
index maps stable row key and hidden-state index to shard key, dtype, shape,
anchor index, token-ID digest, model revision, and tensor sha256. The index
also records the signed instrument fingerprint and capture-content digest.
This makes later profile,
residualization, probe, or alternative-estimator analyses possible without
loading either model again. Row-level scalar surface covariates and frozen
lexical-PC coordinates are retained privately with the same row keys. Raw
hashed lexical features and token IDs are not public-release fields.

After PI adjudication gives the experiment a terminal status, the
`.skills/data-exhaust/` workflow must build and verify two standard datasets:

- aggregate exhaust containing every file under `analysis-committed/`;
- row-level generation exhaust, one cell per model, using the standard
  `generation_text`, `answer_value`, grading, termination, role, split, model,
  revision, and seed schema.

UMWP is not currently present in the data-exhaust license-gate table, so it is
fail-closed as `pending-audit` even though the upstream data README states
CC-BY-SA-4.0. Before any row-level build, audit UMWP and its constituent-source
terms and record the resulting verdict in the canonical license gate. A
full-text verdict must include the required CC-BY-SA-4.0 attribution and
share-alike disclosure; otherwise the standard text-free or excluded
disposition applies. Aggregate exhaust is unaffected by that text-license
gate.

The activation bundle is retained in private staging as a required reusable
artifact. Public activation release requires a separate source-license and
model-license audit plus an explicit PI-approved dry-run card. No live HF
upload occurs before terminal resolution, successful containment verification,
and explicit approval of that exact upload. The terminal NOTEBOOK entry records
dataset revisions, artifact hashes, exclusions, and any text-free disposition.
After all committed aggregates exist, a deterministic artifact allowlist and
private-text scan writes `containment_report.json`; packaging is blocked unless
that final complete-tree scan passes.

## Prediction

For both Gemma-4-E4B-it and Qwen3-4B, the surface-matched FIT profile and its fixed-seed 50% intact-triad subsample retain an early-exterior `eff_dim_frac` peak at depth at most 0.20.

## Falsifier

After G0-G4 pass for a model, any valid primary full or registered subsample profile whose `eff_dim_frac` peak is beyond depth 0.20 falsifies the surface-robustness prediction; a gate failure is indeterminate and never a pass.

## Gates

- **G0 provenance and containment:** The UMWP source sha256, license, row
  counts, pair mapping, model revisions, render contracts, hidden-state shapes,
  fresh-pool exclusions, private output roots, committed schema, and prohibited
  field scans match `cell.yaml`. Unanswerable answer fields are never read. The
  resumable generation-log smoke preserves raw text, the full grader
  sub-dictionary, termination inputs, and stable row identity.
- **G1 generation yield and role quality:** For each model, role assignment and
  grader-integrity checks pass and the final matched pool contains at least 64
  triads per role in FIT and 64 per role held out. Failure hard-stops before
  capture as indeterminate.
- **G2 surface support:** Within each model and separately on FIT and held-out,
  every pairwise scalar maximum absolute SMD is at most 0.10 and the grouped
  maximum pairwise best-orientation surface-role AUROC is at most 0.60. Failure
  hard-stops before capture as indeterminate.
- **G3 positive-control reachability:** The private one-hot surface tag makes
  every pairwise held-out AUROC at least 0.90 under the registered grouped
  classifier. At the
  predeclared midpoint index, the smallest successful planted-noise scale makes
  that index the unique `eff_dim_frac` peak at least 1.05 times the runner-up.
  Failure is indeterminate.
- **G4 capture and atlas applicability:** Full-depth final-prompt-token coverage,
  model shapes, row joins, activation-shard indices, and tensor digests are
  exact. The registered 50% FIT subsample repeats the G2 surface check. At one
  layer strictly inside depths 0.20 and 0.85, all three standard axes attain
  held-out AUROC at least 0.80. Failure is indeterminate.
- **G5 peak location:** Only after G0-G4 pass, each model's matched FIT profile
  and fixed-seed 50% intact-triad subsample must peak at depth at most 0.20. If
  both models pass, the prediction passes. Any valid unique peak beyond 0.20
  falsifies it. A nonunique real peak is indeterminate. Margins are descriptive
  only.

## Predictions scoreboard

| Predictor | Call |
|-----------|------|
| orchestrator | The early-exterior peak location survives the fresh surface-matched pool on both models (65% confidence). |
| user | The early-exterior peak location survives the fresh surface-matched pool on both models. Verbatim response: "i agree"; no separate confidence stated. |

Resolution: **TIE / TIE**. G1 failed before any controlled profile was
computed, so neither registered peak-location call was evaluated.

## Outcome

PI adjudication on 2026-07-22 closed this experiment as an indeterminate null
result after the registered Gemma Stage A pool gate failed.

Gemma generation completed all 5,200 eligible UMWP rows. G0 passed exact source
and generation coverage, pair mapping, regrade parity, prior-atlas exclusion,
and containment. G1 retained 74 matched triads per role, split into 36 FIT and
38 held-out triads. This was below the registered floor of 64 triads in each
partition, so G1 failed. G2 was not run, and the registered hard stop prevented
G3-G5 and all full-depth capture.

Qwen Stage A was not run because Gemma's gate failure already made the joint
two-model prediction indeterminate. Neither the prediction nor the falsifier
was evaluated: no controlled `eff_dim_frac` profile or peak location was
computed. The result is therefore not evidence for or against the
surface-diversity account.

The complete private Gemma generation exhaust remains under gitignored
`analysis/` for method development and licensed downstream analysis. The
committed surface contains only aggregate gate records. The terminal
allowlist and private-text containment scan passed with no errors. Row-level
publication remains blocked pending the registered UMWP license audit and a
separate PI-approved dry-run card.
