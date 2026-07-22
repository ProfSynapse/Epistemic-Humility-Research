# Family Atlas Surface-Matched JSON-Completion Control

Status: signed 2026-07-22. The PI-approved Gemma and Qwen pre-sign smokes
passed. No Stage A scientific generation or Stage B capture has been launched.
Every later GPU stage requires explicit PI approval.

## Instrument tier

This is a Tier 2 amendment and a new evidence surface. The resolved
`family-atlas-surface-matched-vllm-control` amendment stopped at Gemma G0. Its
full 5,200-row generation contained 5,189 strict-valid JSON objects, five
incomplete objects at the registered 200-token cap, and six incomplete objects
terminated by an alternate stop token after 6-8 completion tokens. Qwen Stage A
and both full-depth captures were not run. No controlled peak profile was
produced.

Suppressing model-specific alternate stop tokens and increasing the completion
cap change the output-affecting generation contract. Those changes are outside
the resolved amendment's authorized knobs, so they cannot be treated as a
notebook rerun. All scientific pool, role, matching, capture, estimator, and
decision rules below are carried forward unchanged. The generation-contract
change is preregistered explicitly.

This experiment remains exploratory robustness evidence. It is not pooled with
the family-atlas headline rows.

## Question

Does the early-exterior family-atlas `eff_dim_frac` peak persist in fresh,
cross-original, surface-matched KU-role pools for both Gemma-4-E4B-it and
Qwen3-4B when a pinned, batch-invariant vLLM generator is required to complete
the registered JSON response interface?

## Motivation

The surface-diversity alternative says that the early peak may be induced by
prompt length, lexical overlap, native dataset, formatting, or related surface
structure that covaries with KU role. The fresh surface-matched pool is the
direct control. The immediate predecessor did not answer the scientific
question because strict whole-output validity failed on 11 Gemma rows before
role assignment or matching.

The predecessor exhaust distinguishes two registered interface failures. Five
rows exhausted the 200-token allowance, while six emitted Gemma alternate stop
token ID 106 before completing the JSON object. Plain `ignore_eos` is not used:
in pinned vLLM 0.23.0 it disables every EOS stop, and xgrammar grammar
completion does not independently guarantee request termination. The successor
instead suppresses only exact model-specific alternate stop tokens, retains the
canonical tokenizer EOS, and raises the allowance to 512 tokens. This targets
the observed interface failure without changing answer semantics.

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
`max_num_batched_tokens`, seed, decode settings, canonical EOS, suppressed
alternate stop strings and IDs, and schema hash must be recorded in `cell.yaml`
and run provenance before the pre-sign smoke. There are no `latest` or tag-only
runtime dependencies.

Signing is forbidden until the generic Synaptic Tuner `--suppress-token`
capability is merged and `cell.yaml` records its exact host commit and runtime
source fingerprint. The generation container does not depend on a Git checkout.
Before tokenizer or model loading it computes the registered canonical path,
byte digest, and file-size fingerprint over the complete tracked
batch-generation import surface. Git commit identity remains host-side
provenance and is not substituted for runtime byte verification.

`VLLM_BATCH_INVARIANT=1` must be set before vLLM engine construction. The
vLLM 0.23.0 GPU model runner is pinned to V1. This avoids V2's UVA requirement
on the registered WSL2 lane and prevents model-dependent auto-selection from
silently changing the runtime implementation. The
registered generation settings remain greedy, `do_sample=false`,
`min_new_tokens=1`, and `max_new_tokens=512`.

The suppressions are exact and model-specific. Gemma suppresses `<turn|>` at
token ID 106 and `<|tool_response>` at token ID 50 while retaining canonical
`<eos>` at token ID 1. Qwen suppresses `<|endoftext|>` at token ID 151643 while
retaining canonical `<|im_end|>` at token ID 151645. The harness must resolve
each registered string with the exact pinned tokenizer, require a one-token
encoding equal to the registered ID, and pass that exact ID through the pinned
vLLM 0.23 `_bad_words_token_ids` field. Raw `bad_words` and leading-space
retokenization are forbidden. The harness verifies that no suppressed ID
appears in completion-token evidence. A mismatch fails before scientific
generation. Canonical EOS remains enabled and `ignore_eos` is false.

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
pre-sign smoke must verify every prompt plus the 512-token generation allowance
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

The predecessor's 5,189 strict-valid Gemma rows form a private targeted-parity
comparator. On those exact IDs, successor completion token IDs, finish reasons,
and parsed objects must match the predecessor exactly. The 11 invalid
predecessor rows are excluded from parity and instead must each produce one
strict-valid object, omit every suppressed token ID, and finish before the
512-token cap. Comparator failure makes successor G0 indeterminate; predecessor
rows are never pooled into successor role assignment, matching, or capture.

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

1. Select the predecessor's exact deterministic 20-row stratified set per
   model, spanning every native-source and answerability stratum plus short and
   long rendered prompts. Union it with the 11 predecessor failure IDs, which
   overlap neither 20-row set, for exactly 31 private rows per model.
   The model-specific base sets overlap on 19 rows: `umwp:609` is Gemma-only
   and `umwp:717` is Qwen-only. The complete 31-row sets therefore overlap on
   30 rows. "Same 31-row smoke design" means each exact prior 20-row set plus
   the same 11-row failure set, not identical row membership across models.
2. Assert exact membership of the 11-row failure set in both model smokes,
   byte-identical rendered prompts, and equality of prompt token count
   plus SHA-256 of the unpadded prompt token sequence against the experiment
   renderer.
3. Run the fixed set twice in registered order and twice in a fixed permutation
   at the registered concurrency.
4. Require identical completion token IDs, finish reasons, and parsed objects
   across all four runs.
5. Require 100% whole-output JSON Schema validity without salvage parsing.
6. Require every registered suppressed token string to resolve to its exact
   one-token ID, require no suppressed ID in any completion, and require every
   prior failure ID to terminate before the 512-token cap.
7. Require every rendered prompt plus the 512-token allowance to fit the
   2,048-token context pin.
8. Interrupt immediately after the first durable 16-row batch, require a
   partial checkpoint, resume the exact input, and require a row log identical
   to an uninterrupted run after canonical ordering.
9. Feed an ID-only planted-role manifest with adequate role support through the
   real matcher and require at least 64 FIT and 64 held-out triads. This tests
   that G1 is structurally reachable without observing or estimating the real
   outcome.

Committed smoke output is limited to versions, aggregate hashes, counts, and a
manifest whose only row-level field is `row_id`. Per-row prompt hashes, prompt
token-sequence hashes, prompt token counts, completion text, and completion
token IDs remain under gitignored `analysis/`. Every committed JSONL row in
this experiment is restricted to `row_id`; role, split, and native-source
labels remain private and are represented publicly only through aggregates.

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
  construction; scheduler, tokenizer, schema, canonical EOS, and exact
  alternate-stop suppression pins recorded; `ignore_eos=false`; 100% strict
  schema validity without salvage; no suppressed completion token; complete
  prompt/completion token and finish evidence in private exhaust; exact targeted
  parity on all 5,189 predecessor-valid Gemma rows; strict valid completion
  before the cap on all 11 predecessor-invalid rows; kill/resume equivalence;
  ID-only committed artifacts. Failure is indeterminate.
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
| G0-G4 indeterminacy risk | none expected after both 31-row smokes pass | none expected after both 31-row smokes pass |

## Private predecessor comparator

The resolved `family-atlas-surface-matched-vllm-control` private Gemma
completion log is mounted read-only at SHA-256
`adb53c0b3024ae32c816ba19912d4215605e42c7e1a11d85914622513f7aee8b`.
Its committed ID-only failure summary is promoted as a shared successor input
with exact origin provenance. The comparator supplies only the 5,189
strict-valid parity rows and the 11-row failure set described above. It is never
pooled with successor rows and never enters successor role assignment,
matching, surface analysis, or capture. Comparator outputs are limited to exact
agreement counts, failure-class counts, IDs, and hashes.

No Hugging Face dataset publication or upload is part of this amendment.

## Data exhaust

The private, resumable generation log retains stable row key, source and native
source, original pair ID, category, model and revision, renderer ID, seed,
prompt bytes hash, prompt token-sequence hash and count, completion text,
completion token IDs,
finish reason, parsed object, answer value, natural-termination flag, token
count, full grader dictionary, role, split, triad ID, vLLM/runtime provenance,
schema hash, canonical EOS IDs, configured suppression strings, resolved
suppressed IDs, scheduler pins, checkpoint hash, and resume history. Raw prompt
token IDs are reproducible from the retained private prompt, renderer, and
tokenizer revision, so the run log stores their sequence hash and count rather
than a second raw copy. Private comparator exhaust retains per-ID equality for
completion tokens, finish reasons, and parsed objects; committed output retains
only counts, IDs, and hashes.

Private activation exhaust remains sharded safetensors plus an index containing
row key, hidden-state index, shard key, dtype, shape, anchor index, token hash,
model and revision, tensor hash, instrument fingerprint, and capture content
digest. Private surface scalars and lexical coordinates are retained for future
audits. Public token IDs and raw hashed lexical features are forbidden.

## Approval stages

1. Merge the generic Synaptic Tuner alternate-token suppression capability and
   pin its exact host commit, runtime source fingerprint, and runner image
   digest.
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
| Joseph Rosenbaum | Both models retain an early-exterior peak at depth at most 0.20 in both registered profiles. |

## Outcome

Not run. The PI will fill this section at resolution.
