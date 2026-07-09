# Phase 3 Causal Pilot Readiness

Status: Gate 6 readiness artifact produced
Created: 2026-06-15
Scope: local causal-pilot readiness for Phase 3 exploratory interpretability

## Gate 6 Status

Gate 6 is ready for a first local smoke-run implementation plan, but no
intervention results exist yet. The available directions are Tier 1
correlational hidden-state diagnostics. If a future runner performs activation
addition, subtraction, erasure, or patching, those outputs are Tier 2
exploratory local mechanism diagnostics only.

This artifact does not authorize protocol edits, Phase 1 headline claim
promotion, reward-loop use of probes or directions, SAE or encoder training,
Docker/GPU execution, or model generation.

## Evidence Inputs

- Gate 5 source map: `docs/plans/phase3-mechanism-source-map.md`
- Process gate: `docs/plans/phase3-interpretability-research-process.md`
- Hidden-state summary: `experiment/phase1/probe/README.md`
- Candidate extraction root:
  `experiment/phase1/probe/qwen3-4b-instruct/hidden_states/`

The five comparable 128 known / 128 unknown extractions are reported as
`status=ok`, `verified=true`, 256 rows each, and 222 ok direction vectors each:

| arm | extraction | best h_base | best h_lora | best delta |
| --- | --- | ---: | ---: | ---: |
| `sft` | `extraction__12fb10b1c8c8` | 0.753906 L25 | 0.863281 L36 | 0.855469 L35 |
| `cold_dpo` | `extraction__f3dbd2c1754a` | 0.753906 L25 | 0.773438 L35 | 0.750000 L35 |
| `cold_kto` | `extraction__0810aa2972e8` | 0.753906 L25 | 0.765625 L36 | 0.750000 L26 |
| `sft_dpo` | `extraction__0d58c201ab3e` | 0.843750 L36 | 0.855469 L34 | 0.859375 L35 |
| `sft_kto` | `extraction__e1473df788a5` | 0.843750 L36 | 0.859375 L35 | 0.855469 L36 |

## First Smoke Target

The first smoke should prioritize SFT directions because SFT has the strongest
known/unknown separability and best matches the working assumption that SFT
created the behavior/internal shift. Sequential DPO/KTO over SFT should be
confirmatory after the smoke, not the first intervention target.

Primary candidates:

| priority | arm | extraction | role | layer | direction_id | rationale |
| --- | --- | --- | --- | ---: | --- | --- |
| 1 | `sft` | `extraction__12fb10b1c8c8` | `h_lora` | 36 | `direction__9c8c74f718038292` | strongest SFT h_lora readout; direct active-adapter state |
| 2 | `sft` | `extraction__12fb10b1c8c8` | `delta` | 35 | `direction__8bb10838ed21eebe` | strongest SFT delta readout; isolates LoRA-minus-base shift |

Initial intervention family should be simple activation addition/subtraction on
the final prompt token before any encoder, SAE, or broader tracing work.

## Exclusion Boundaries

- Do not edit `docs/protocols/phase1/PROTOCOL.md`.
- Do not edit `library/`, KG notes, source maps, run records, training queues,
  dashboard code, `synaptic-tuner`, hidden-state artifacts, or model artifacts.
- Do not use Phase 3 outputs to rank Phase 1 arms or update Phase 1 headline
  claims.
- Do not feed probe, direction, SAE, encoder, or intervention outputs back into
  training rewards, data selection, or model selection.
- Do not collapse safety refusal into epistemic abstention. Safety refusal is a
  harmful-request policy behavior; epistemic abstention is a knowledge-boundary
  response on factual QA rows.

## Required Controls

- No-vector baseline for every row and arm.
- Sign flip for each candidate direction.
- Random direction with matched layer, dimensionality, and norm handling.
- Shuffled-label direction derived from the same extraction contract.
- Wrong-layer neighbor control, at minimum adjacent layer around the target.
- Base-only/no-vector control to separate adapter behavior from direction
  intervention effects.
- Prompt-format and thinking-leak checks, including byte-stable rendering and
  fixed `enable_thinking=false`.

Optional later controls, after the smoke: unrelated behavior direction,
sequential-arm transfer, erase/projection-removal, and alternate token
positions.

## Metrics

Predeclare all metrics before interpreting any generated outputs:

- Unknown abstention/refusal rate, with epistemic abstention separated from
  safety refusal.
- Known answer retention and known-answer correctness.
- Over-refusal on known rows.
- Answer-on-unknown rate.
- Invalid output and refusal-template contamination.
- Thinking tag contamination: `<think>`, `</think>`, and `reasoning_content`.
- Per-row deltas against the no-vector baseline for every coefficient and
  control.

Null results are valid outcomes. A direction that classifies known/unknown but
does not move behavior under controls remains a Tier 1 readout, not a causal
handle.

## Artifact Contracts

A future runner should require:

- Extraction manifest path, `status=ok`, and `verified=true`.
- Candidate direction manifest path and direction row with `status=ok`.
- Direction tensor path, tensor key, layer, role, method, contrast, hidden
  dimension, and vector hash.
- Stable row ids shared across extraction rows, intervention inputs, and
  scoring outputs.
- Fixed prompt bytes and renderer identity across baseline and intervention
  arms.
- Fixed `enable_thinking=false` and explicit checks for thinking scaffolding.
- Coefficient grid including zero and sign-flipped values.
- Output manifest that records evidence tier, KG mechanism ids, source map,
  source extraction hashes, no-vector baseline, controls, metrics, and stop
  conditions.

Suggested output root:
`experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_sft_smoke/`

## Stop Conditions

Stop before interpreting results if:

- Any selected extraction manifest is missing, not `status=ok`, or not
  `verified=true`.
- Any selected direction is missing, not `status=ok`, or has a layer/role/hash
  mismatch against the config.
- Row ids cannot be joined exactly across extraction, intervention, and scoring.
- Rendered prompt bytes differ across baseline and intervention arms.
- Thinking scaffolding appears in prompts or outputs.
- The run would consume or block the active Phase 1 training lane.
- The implementation would require protocol, KG/library, run-record,
  hidden-state, model-artifact, dashboard, or `synaptic-tuner` edits.
- A result would be described as Phase 1 headline evidence or Tier 3 mechanism
  evidence without a signed protocol revision.

## Next Implementation Step

Implement a minimal no-generation readiness runner or dry-run validator that
loads `archive/experiment/phase1/probe/config/causal-pilot-core/phase3_causal_pilot_smoke.yaml`, verifies
the extraction and direction contracts, resolves row ids, materializes the
planned arms and controls, and writes a dry-run manifest. Generation and GPU
execution should remain a separate explicit approval step.
