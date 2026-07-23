# Family Atlas Surface-Matched vLLM Control

Status: signed 2026-07-22. Pre-sign model smokes completed under staged PI
approval. Stage A generation and Stage B capture remain unlaunched and require
separate PI approval.

## Instrument tier

This is a Tier 2 amendment and a new evidence surface. The resolved
`family-atlas-surface-matched-pool-control` amendment stopped after Gemma Stage A:
G0 passed, but the strict generation and matching path produced 36 FIT and 38
held-out triads, below the registered 64/64 G1 floor. Qwen Stage A and both
full-depth captures were not run. No controlled peak profile was produced.

Replacing batch-1 Hugging Face generation with schema-constrained,
batch-invariant vLLM generation changes the evidence-producing instrument. It
therefore cannot be treated as an authorized knob change or a notebook rerun.
All scientific pool, matching, capture, estimator, and decision rules below are
carried forward unchanged. The backend change is preregistered explicitly.

This experiment remains exploratory robustness evidence. It is not pooled with
the family-atlas headline rows.

## Question

Does the early-exterior family-atlas `eff_dim_frac` peak persist in fresh,
cross-original, surface-matched KU-role pools for both Gemma-4-E4B-it and
Qwen3-4B when the response interface is enforced by a pinned, batch-invariant
vLLM generator?

## Motivation

The surface-diversity alternative says that the early peak may be induced by
prompt length, lexical overlap, native dataset, formatting, or related surface
structure that covaries with KU role. The fresh surface-matched pool is the
direct control. The predecessor did not answer the scientific question because
its resulting role yield did not reach G1. A suspected instrument failure mode
for the successor to test is that an unconstrained generator may emit a valid
first JSON object and then continue, causing the registered strict whole-output
grader to reject the full completion. This is a pre-run instrument hypothesis,
not a reinterpretation of the predecessor verdict.

JSON syntax is incidental to the model behavior of interest. The successor
therefore constrains syntax only. It does not constrain the answer content,
refusal language, correctness, or confidence value beyond the registered type
and range. The scientific invariant remains peak location, not peak margin.

## Fixed inputs

### Pool

- Source: official UMWP `StandardDataset.jsonl`.
- Source SHA-256:
  `e8840e8383357238a08e9c5028e4758ceceb369e1db31c64678b0f851c9c9e73`.
- Expected rows: 5,200, with 2,600 answerable and 2,600 unanswerable.
- Native-source blocks: ASDiv 100/100, GSM8K 1,700/1,700,
  MultiArith 300/300, and SVAMP 500/500 answerable/unanswerable.
- Unanswerable bookkeeping answer fields are never consumed as reference
  answers. Same-source relevant-row links are used only for the registered
  cross-original matching exclusion.
- Rows overlapping each model's prior atlas pool under the registered Unicode,
  casefold, and whitespace normalization are excluded before role assignment.

Question text, answers, aliases, generation text, token IDs, normalized text
hashes, surface vectors, and row-level grades remain under gitignored
`analysis/`. Only ID-only manifests and aggregates may enter
`analysis-committed/`.

### Models

| Key | Repository | Revision | Hidden-state indices |
|---|---|---|---:|
| `gemma4_e4b_it` | `google/gemma-4-E4B-it` | `fee6332c1abaafb77f6f9624236c63aa2f1d0187` | 0-42 |
| `qwen3_4b_raw_base` | `unsloth/Qwen3-4B` | `64033659d5caf1b8ed7f929b29de705e93a4d468` | 0-36 |

The experiment-owned renderers, chat templates, `add_special_tokens` behavior,
and final-prompt-token anchor are frozen in `cell.yaml` and the pinned modules.
Prompt bytes and prompt token sequences must match those renderers exactly.

## Evidence-surface change

Stage A generation uses the generic Synaptic Tuner `batch-generate --engine
vllm` verb inside a dedicated digest-pinned runner. The exact image digest,
vLLM version, CUDA, PyTorch, Transformers, tokenizer revision, hardware class,
compute dtype, vLLM GPU model-runner implementation, tensor parallel size,
maximum model length, multimodal limits,
GPU-memory utilization, remote-code policy, `max_num_seqs`,
`max_num_batched_tokens`, seed, decode settings, stop settings, and schema hash
must be recorded in `cell.yaml` and run provenance before the pre-sign smoke.
There are no `latest` or tag-only runtime dependencies.

The generic dependency has host-side provenance at merged Synaptic Tuner PR 145,
commit `b1ea38298a478a7d40fbab1cb4ad492194b833e7`. The generation container does
not depend on a Git checkout. Before tokenizer or model loading it computes the
registered canonical path, byte digest, and file-size fingerprint over the
complete tracked batch-generation import surface. The required source
fingerprint is
`5a693532465c771ec7c7afe7bcbb6e55c08a508e6d3a1d321bcb8fdb32140576`;
the exact file allowlist and algorithm are pinned in `cell.yaml`. Git commit
identity remains host-side provenance and is not substituted for runtime byte
verification.

`VLLM_BATCH_INVARIANT=1` must be set before vLLM engine construction. The
vLLM 0.23.0 GPU model runner is pinned to V1. This avoids V2's UVA requirement
on the registered WSL2 lane and prevents model-dependent auto-selection from
silently changing the runtime implementation. The
registered generation settings remain greedy, `do_sample=false`,
`min_new_tokens=1`, and `max_new_tokens=200`.

The generation runtime is vLLM 0.23.0, whose batch-invariance path supports the
RTX 3090's compute capability 8.6. Earlier vLLM 0.18 releases required compute
capability 9.0 and are not eligible for this lane. Runtime G0 must verify compute
capability at least 8.0 rather than merely observing that the environment flag
was set.

The candidate capacity pins are `batch_size=16`, `max_model_len=2048`,
`gpu_memory_utilization=0.90`, `max_num_seqs=32`, and
`max_num_batched_tokens=8192`, with remote model code disabled. Gemma text-only
generation sets image, audio, and video limits to zero so vLLM does not profile
unused multimodal encoders. The
pre-sign smoke must verify every prompt plus the 200-token generation allowance
fits the context pin and that the candidate scheduler fits the RTX 3090. Any
capacity-only adjustment occurs before signing and is recorded; no scientific
row may be generated first.

The response is constrained by this semantic JSON Schema:

```json
{
  "type": "object",
  "properties": {
    "answer": {"type": "string"},
    "response_confidence": {"type": "number", "minimum": 0, "maximum": 1}
  },
  "required": ["answer", "response_confidence"],
  "additionalProperties": false
}
```

The schema constrains form only. The xgrammar engine also disables optional JSON
whitespace so a completed object cannot consume the remaining token allowance
as trailing whitespace. The strict whole-output grader remains the scientific
grader. First-object salvage is forbidden for role assignment.
Malformed rows, ambiguous grades, degenerate outputs, and rows outside the
registered role definitions remain excluded.

Stage B retains the predecessor's pinned Hugging Face full-depth capture path.
The selected prompt rows, not generation completions, are captured at the
final-prompt-token anchor. vLLM hidden-state extraction is outside this
experiment, so no hidden-state backend bridge is required.

## Roles and matching

The three registered KU roles are unchanged:

- `known_correct_answered`: answerable row, non-refusal, non-degenerate, and
  correct under the pinned alias-aware grader.
- `confab`: unanswerable row with a substantive non-refusal answer.
- `unknown_refused`: unanswerable row with a valid refusal under the pinned
  refusal grader.

Matching is deterministic 1:1:1 without replacement. Pass 1 matches `confab`
to `unknown_refused` within native source and UMWP category. Pass 2 matches the
mean surface vector of each unknown pair to `known_correct_answered` within
native source. An answerable row and its linked unanswerable original may not
share a triad. Ties use lexicographic role-ordered UMWP IDs.

The frozen surface basis includes rendered prompt token count; question
character, word, and line counts; digit, punctuation, newline, and uppercase
counts and fractions; word 1-2 gram TF-IDF hashed features reduced to 64 fixed
SVD coordinates; and character 3-5 gram TF-IDF hashed features reduced to 64
fixed SVD coordinates. Role, answers, aliases, UMWP category, completions,
grades, activations, and completion length are forbidden matching features.

Intact triads are split by native source with seed `20260721`. Each model must
produce at least 64 FIT and 64 held-out triads. Gemma and Qwen Stage A are run
and gated independently. Failure by one model does not discard the other
model's private exhaust, but the joint scientific prediction passes only when
both models satisfy G5.

## Surface and atlas analyses

For FIT and held-out partitions separately, every pairwise scalar absolute SMD
must be at most 0.10. A five-fold logistic surface-only classifier, grouped by
intact triad, must have maximum pairwise best-orientation held-out AUROC at
most 0.60.

For each eligible model, Stage B captures every hidden-state index at the final
prompt token in float32 with no steering hooks. `eff_dim_frac` is the
participation ratio divided by row count. Depth is
`hs_index / (n_hidden_states - 1)`. The primary population is the matched FIT
pool. A fixed-seed 50% intact-triad subsample stratified by native source is the
registered robustness profile.

The held-out three-axis read panel measures KU/answerability (`doubt` artifact
key), caution, and raw refusal. G4 requires at least one common strict-interior
layer, depth in `(0.20, 0.85)`, where all three held-out AUROCs are at least
0.80. Bootstrap and random-direction seeds remain `20260707` with 2,000
bootstrap resamples.

## Pre-sign reachability validation

Signing is forbidden until the generic vLLM capability and digest-pinned image
are merged and the following smokes pass with separate PI approval for each
model load:

1. Select exactly 20 private rows per model deterministically, spanning every
   native-source and answerability stratum plus short and long rendered prompts.
2. Assert byte-identical rendered prompts and equality of prompt token count
   plus SHA-256 of the unpadded prompt token sequence against the experiment
   renderer.
3. Run the fixed set twice in registered order and twice in a fixed permutation
   at the registered concurrency.
4. Require identical completion token IDs, finish reasons, and parsed objects
   across all four runs.
5. Require 100% whole-output JSON Schema validity without salvage parsing.
6. Interrupt immediately after the first durable 16-row batch, require a
   partial checkpoint, resume the exact input, and require a row log identical
   to an uninterrupted run after canonical ordering.
7. Feed an ID-only planted-role manifest with adequate role support through the
   real matcher and require at least 64 FIT and 64 held-out triads. This tests
   that G1 is structurally reachable without observing or estimating the real
   outcome.

Committed smoke output is limited to versions, hashes, counts, and ID-only
manifests. Completion text and token IDs remain private.

## Planted-signal controls

The surface-classifier positive control appends a three-column one-hot role
tag. Every pairwise held-out AUROC must be at least 0.90. This proves the
classifier and grouped folds can detect strong residual role information.

The geometric positive control injects centered high-rank Gaussian row-space
noise only at the registered midpoint hidden-state index: Gemma index 21 and
Qwen index 18. It searches the frozen RMS scale grid
`[0.25, 0.5, 1, 2, 4, 8, 16]`. A valid control requires a unique peak at the
planted index and a peak-to-runner-up ratio of at least 1.05. This proves the
pipeline can move peak location when the data contain such a signal.

## Prediction

For both Gemma-4-E4B-it and Qwen3-4B, the surface-matched FIT profile and its
fixed-seed 50% intact-triad subsample retain a unique early-exterior
`eff_dim_frac` peak at depth at most 0.20.

## Falsifier

After G0-G4 pass for a model, any valid primary full or registered subsample
profile whose `eff_dim_frac` peak is beyond depth 0.20 falsifies the
surface-robustness prediction. A prerequisite failure or nonunique real peak is
indeterminate and never a pass. Raw peak margins are descriptive only.

## Gates

- **G0, engine, provenance, containment, and coverage:** exact source and model
  pins; exact renderer and anchor; zero prior-atlas overlap; exact row coverage;
  digest-pinned runtime; expected vLLM version; batch-invariance flag set before
  construction; scheduler, tokenizer, schema, and stop pins recorded; 100%
  strict schema validity without salvage; complete prompt/completion token and
  finish evidence in private exhaust; kill/resume equivalence; ID-only committed
  artifacts. Failure is indeterminate.
- **G1, yield and role quality:** per model, valid pinned grading and at least 64
  FIT plus 64 held-out intact 1:1:1 triads. Failure is an indeterminate hard stop
  before capture for that model.
- **G2, surface support:** per model and partition, every pairwise scalar
  absolute SMD at most 0.10 and maximum grouped pairwise best-orientation
  held-out AUROC at most 0.60. Failure is an indeterminate hard stop before
  capture for that model.
- **G3, positive-control reachability:** every pairwise one-hot-tag AUROC at
  least 0.90; midpoint planted-location control has a unique planted peak with
  runner-up ratio at least 1.05. Failure is indeterminate.
- **G4, capture integrity and atlas applicability:** complete exact-join
  full-depth capture; digest-complete shards; registered half-FIT surface
  support recheck passes; at least one common strict-interior layer has all
  three held-out read AUROCs at least 0.80. Failure is indeterminate.
- **G5, peak location:** after G0-G4 pass, both the full FIT and registered
  half-FIT profiles have unique peaks at depth at most 0.20. Both models must
  satisfy both checks for the joint prediction to pass. Any valid peak beyond
  0.20 falsifies the prediction.

### Joint outcome precedence

The joint verdict is derived in this fixed order:

1. **FALSIFIED** if either model has any valid registered unique full or
   half-FIT peak beyond depth 0.20, even when the other model is indeterminate.
2. Otherwise **INDETERMINATE** if either model has a G0-G4 failure or any
   required real profile has a nonunique peak.
3. Otherwise **PASS** only when both models have unique early peaks for both
   the full and half-FIT checks.

The derived joint row is not independently scored and cannot double-count a
model-level call.

## Pre-run scoreboard

PI and orchestrator calls are recorded below. These calls were made before any
Stage A scientific generation or controlled capture.

| Model | Direction | PI call | Orchestrator call |
|---|---|---|---|
| Gemma-4-E4B-it | EARLY | selected | selected |
| Gemma-4-E4B-it | LATE | not selected | not selected |
| Qwen3-4B | EARLY | selected | selected |
| Qwen3-4B | LATE | not selected | not selected |
| Joint, derived only | fixed precedence above | both models EARLY | both models EARLY |

An optional gate-risk call is recorded separately and never changes an
EARLY/LATE call:

| Risk surface | PI call | Orchestrator call |
|---|---|---|
| G0-G4 indeterminacy risk | none expected | none expected |

## Private predecessor comparator

The predecessor's private Gemma generation exhaust may be mounted read-only by
an exact locally recorded artifact hash. It is never pooled with successor
rows, never enters matching or capture, and cannot pass, fail, or rescue a
gate. Comparator-only aggregates may report strict schema validity, natural
termination, strict role counts, matched-triad yield, and paired semantic
agreement on rows where a separately pinned diagnostic parser finds one valid
first object in the predecessor completion. That diagnostic parser is never
used for successor role assignment.

No Hugging Face dataset publication or upload is part of this amendment.

## Data exhaust

The private, resumable generation log retains stable row key, source and native
source, original pair ID, category, model and revision, renderer ID, seed,
prompt bytes hash, prompt token-sequence hash and count, completion text,
completion token IDs,
finish reason, parsed object, answer value, natural-termination flag, token
count, full grader dictionary, role, split, triad ID, vLLM/runtime provenance,
schema hash, scheduler pins, checkpoint hash, and resume history. Raw prompt
token IDs are reproducible from the retained private prompt, renderer, and
tokenizer revision, so the run log stores their sequence hash and count rather
than a second raw copy.

Private activation exhaust remains sharded safetensors plus an index containing
row key, hidden-state index, shard key, dtype, shape, anchor index, token hash,
model and revision, tensor hash, instrument fingerprint, and capture content
digest. Private surface scalars and lexical coordinates are retained for future
audits. Public token IDs and raw hashed lexical features are forbidden.

## Approval stages

1. Merge the generic Synaptic Tuner vLLM capability and pin an exact runner
   image digest.
2. Obtain separate PI approval for the Gemma and Qwen pre-sign GPU smokes.
3. Sign only after both required smokes and synthetic G1 reachability pass.
4. Obtain separate PI approval for Gemma Stage A generation.
5. Obtain separate PI approval for Qwen Stage A generation. Stage A runs are
   independent and may proceed even if the other model fails G1 or G2.
6. Run CPU-only G0-G2 scoring for each model.
7. Obtain a separate PI approval for each model that is eligible for Stage B
   full-depth capture.
8. The PI alone adjudicates G5 and the experiment verdict.

All GPU work runs inside the registered digest-pinned runner, with
`DOCKER_HOST=unix:///var/run/docker.sock` set per command. No CPU model loading
is allowed on WSL2. Processes expected to exceed 15 minutes use
`experiments/common/launch_detached.sh` with an exit-code watch.

## Predictions scoreboard

| Predictor | Call |
|---|---|
| orchestrator | Both models retain an early-exterior peak at depth at most 0.20 in both registered profiles. |
| Joseph Rosenbaum | Both models retain an early-exterior peak at depth at most 0.20 in both registered profiles; no G0-G4 indeterminacy is expected. |

## Outcome

PI adjudication: **INDETERMINATE at G0** on 2026-07-22.

Gemma Stage A durably generated all 5,200 registered completions in the pinned
vLLM V1 runtime. Strict whole-output validation accepted 5,189 rows
(0.9978846154). Five rows reached the registered 200-token cap with incomplete
JSON, and six rows emitted a stop token after 6-8 completion tokens before the
JSON object was complete. The registered G0 threshold is 1.0 with no salvage,
so G0 failed and the completion set was not admitted to role grading or
matching.

Qwen Stage A was not launched under the sequential approval. Neither model was
captured, and no controlled geometric profile or peak-location result was
produced. This experiment therefore does not decide the surface-diversity
alternative. The private Gemma generation and surface artifacts remain intact
as diagnostic exhaust. The committed failure summary contains only row IDs,
counts, and provenance hashes.
