# Batched Generation And Extraction

Standing backend-selection discipline for generation and hidden-state capture.
Use it before registering a GPU cell. The default for new, unsteered work is
vLLM, but comparability and intervention requirements override that default.

## Decision table

| Cell shape | Backend policy |
|------------|----------------|
| Parity-locked surface that extends or regenerates an existing cell | Reuse the exact registered engine, version, batch regime, dtype, and decoding contract. If the reference used HF batch 1, stay HF batch 1. |
| New unsteered generation surface | Prefer pinned vLLM with batch invariance enabled. Register the engine and decoding contract before the run. |
| New structured-output surface where formatting is incidental | Prefer vLLM JSON-schema structured output. Pin the schema. |
| Surface where free-form behavior or format compliance is measured | Use unconstrained decoding and preserve raw output. Do not hide the measured behavior behind structured decoding. |
| New capture-only or read-atlas surface | Prefer vLLM native hidden-state extraction only after the model-specific bridge below passes. Otherwise use the pinned HF batched reference path. |
| Generation followed by capture on a selected subset | Use two stages: vLLM generation, then vLLM extraction on selected rows after its bridge passes. Do not persist full-depth states for every generated row unless the design needs them. |
| Per-row hooks, activation writing, or mixed intervention arms | Use the tuner mechinterp path that implements the intervention correctly. Do not choose vLLM merely for throughput. |
| Base-versus-adapter hidden-state contrast | Use HF + PEFT unless the exact vLLM adapter-load and contrast semantics have their own bridge. |

If the generic tuner lacks the required vLLM verb, record a capability gap and
use the registered HF fallback. Do not bury a one-off vLLM engine inside an
experiment directory. Generic engine work belongs in Synaptic Tuner on its own
branch and PR.

## Why greedy can still vary

Greedy decoding is not probabilistic sampling, but batch composition can change
floating-point reduction order and flip a near-tied argmax. Modern vLLM offers
batch-invariant execution. For research runs:

- set `VLLM_BATCH_INVARIANT=1` before engine construction;
- verify the current batch-invariance hardware requirement; the feature
  currently requires NVIDIA compute capability 8.0 or later;
- pin the exact vLLM version, container digest, hardware class, dtype, tensor
  parallel size, model revision, and tokenizer revision;
- pin scheduler limits such as `max_num_seqs` and `max_num_batched_tokens`;
- keep the same sampling, seed, stopping, and chat-template configuration;
- treat batch invariance as a beta capability that still requires the smoke
  below, not as a substitute for validation.

Reproducibility is only claimed on the same hardware class and exact vLLM
version. A backend or version change creates a new bridge obligation.

## Structured outputs

For current vLLM, prefer JSON-schema structured outputs through
`response_format: {type: json_schema, ...}` or
`StructuredOutputsParams(json=<schema>)`. Do not add new uses of deprecated
`guided_json` fields.

Use schema enforcement only when serialization is an interface requirement,
not an outcome:

- Pin the schema bytes or sha256 in the signed instrument.
- Set `additionalProperties: false` and explicit required keys where supported.
- Constrain numeric ranges and types in the schema instead of only describing
  them in the prompt.
- Preserve generation text, token counts, finish evidence, parsed values, and
  the full grader dictionary in the private resumable row log.
- If format compliance is itself measured, keep decoding unconstrained. A
  constrained comparator may be added only as a separately registered arm.

## vLLM generation smoke

Run before signing the first use of a model, vLLM version, or decoding mode.
Use a fixed private set of about 20 rows spanning short and long prompts,
answer/refusal behavior, and every special renderer path.

1. Render once and require exact prompt bytes and token IDs against the
   experiment-owned renderer.
2. Run the rows twice in one order and twice in a different order under the
   proposed concurrent scheduler configuration.
3. Require identical completion token IDs, finish reasons, and parsed outputs
   for every repeated request.
4. For JSON-schema mode, require every row to validate against the pinned
   schema without salvage parsing.
5. Record engine version, image digest, GPU model, environment pins, scheduler
   knobs, and the exact smoke row-key manifest in the experiment notebook.

If the smoke is not invariant, change the unsigned config or fall back to HF.
Never weaken an already signed gate or retry configurations until one happens
to agree.

For parity against an existing HF surface, add a cross-backend pass over the
same rows. Exact prompt token IDs are mandatory. Exact completion token IDs are
mandatory when the new run will be pooled or compared row-for-row with the HF
surface. If they differ, vLLM may still define a new surface, but it is not a
parity-preserving replacement.

## Full-depth hidden-state bridge

vLLM 0.18 and later expose selected intermediate states through the
`extract_hidden_states` speculative method and KV connector. Pin the exact
tested release rather than a lower-bound dependency. The current output is a
safetensors tensor shaped `[num_tokens, num_extracted_layers, hidden_size]`
plus token IDs.

Before vLLM replaces HF for an established capture instrument:

1. **Capability smoke, about 20 rows.** Require exact rendered bytes and token
   IDs, the expected state count, embeddings at index 0 when the instrument
   requires them, block outputs at indices 1 through N, and the exact final
   prompt-token anchor. Check the last-state normalization convention
   explicitly. Layer IDs are model-implementation semantics, not labels to
   trust by name.
2. **Numerical bridge.** Capture the same rows with the signed HF reference and
   vLLM. Pre-state dtype-aware vector agreement thresholds before running and
   report every row/layer, including the worst layer. Do not choose tolerances
   after inspecting the differences.
3. **Estimator bridge, at least 64 fixed rows when the instrument reports a
   geometric profile.** Run the actual downstream estimator on both captures.
   Require the registered location invariant to agree, such as the same
   `eff_dim_frac` peak or the amendment's pre-stated layer tolerance. Compare
   the complete profile and read-panel outputs descriptively as well.
4. **Persistence and resume.** Verify token IDs, row IDs, tensor paths, dtypes,
   layer IDs, and hashes survive a hard-kill resume exactly as the final
   instrument requires.

For native extraction:

- disable chunked prefill, which is incompatible with the current feature;
- prefer prefill-only capture with one generated token when only prompt states
  are needed;
- set `include_output_tokens` only when completion states are part of the
  registered signal;
- write temporary connector files to ext4 or `/dev/shm`, then stage durable
  artifacts to the experiment's registered private exhaust root;
- keep all token IDs, row-level tensors, and text under gitignored analysis.

If embedding-state availability, normalization, anchor identity, or estimator
location does not bridge, retain HF for that instrument. Do not relabel vLLM
layers to make the bridge pass.

## Governance and signing pins

Backend selection is part of the evidence surface. Before signing, record:

- engine and exact version;
- container image digest and GPU hardware class;
- model and tokenizer revisions;
- renderer and structured-output schema hashes;
- dtype, tensor parallelism, batch-invariance setting, and scheduler limits;
- generation, EOS, stopping, and hidden-state layer contracts;
- smoke and bridge outcomes, with row-key-only manifests.

A throughput-only equivalence check is a lab-notebook instrument. A backend
change that changes prompts, outputs, roles, tensors, or a registered estimator
requires the governed experiment to name that new surface before launch. Never
switch a signed run in flight.

## Currency check

Before the first use of a new vLLM release, read the current official pages for
batch invariance, structured outputs, hidden-state extraction, and supported
models. These APIs are evolving. Update this reference after the real bridge if
the observed contract differs from the documentation.

- `https://docs.vllm.ai/en/stable/features/batch_invariance/`
- `https://docs.vllm.ai/en/stable/features/structured_outputs/`
- `https://docs.vllm.ai/en/stable/features/speculative_decoding/extract_hidden_states/`
- `https://docs.vllm.ai/en/stable/models/supported_models/`

After the first live use of a new vLLM version or model family, update this
reference from the recorded smoke: actual layer mapping, numerical bridge,
batch invariance, schema behavior, throughput, and any fallback. Promote only
the reusable lesson; keep run-specific paths and outcomes in the experiment
notebook.
