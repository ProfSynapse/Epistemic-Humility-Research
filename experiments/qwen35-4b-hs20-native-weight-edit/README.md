# Astra fixed hs20 edit (unsigned)

The active proposal is `astra_r1.yaml`, with runtime settings in
`astra_runtime.yaml`. `AMENDMENT.md` defines the question, evaluation, gates and
stop rules. This is one fixed edit of block-19 down_proj, not the earlier
six-candidate pilot. The old harness remains for provenance and regression tests;
its documentation is under `design-history/`.

No numerical edit or scored evaluation exists. The source has CPU test evidence;
real-model runtime qualification, decoy feasibility, persistence measurements,
the remaining runtime/readback checks and PI sign-off are still required. `astra_run` refuses
capture/evaluation while the experiment is draft.

Run from the EHR project snapshot with the experiment directory on PYTHONPATH.
Use the installed `engine_host` and exact pinned engine wheel. Keep the project,
`.synaptic` artifacts, exports and model cache on T7 E:. Existing public CLI
verbs own model execution; this package imports no Tuner internals.

```bash
python -m hs20_nwe.astra_run plan
python -m hs20_nwe.astra_run materialize --fit FIT --selfaware SELF --ambigqa AMBIG
python -m hs20_nwe.astra_run preflight --model BASE
```

These stages do not perform model inference. Materialization checks source
hashes, excludes evaluation-question matches, writes the exact 64+64 development
roster, strips old responses, and preserves existing benchmark labels/aliases.
Preflight uses only the pinned tokenizer and reports aggregate context lengths.

After the construction contract is signed, capture the development rows:

```bash
python -m hs20_nwe.astra_run capture --model BASE --gpu-ack
```

The engine persists each anchor row and its tensor hashes. It captures both
block-19 down_proj input and output under P-struct. The helper checks the complete
request/journal provenance and compares captured output with W times input.

Use `ehr-engine cli mechinterp weights-inspect --weights-config INSPECT --json`
for the target tensor/index/shard hashes. The inspect document uses schema
`mechinterp-weights-inspect/v1`, the staged base checkpoint, `hash_files: true`,
`hash_tensors: true`, and the exact target tensor. `astra_run read-tensor`
converts that exact tensor to float32 NPY on CPU, checking the expected raw bf16
hash and absence of a bias. It uses safetensors, not pickle or a model load.

```bash
python -m hs20_nwe.astra_run read-tensor --model BASE --expected-sha256 TENSOR_SHA --out BASE_NPY
python -m hs20_nwe.astra_fixed --proposal PROPOSAL prepare \
  --roster ROSTER --capture-dir CAPTURE --capture-binding REQUEST \
  --c-hat DIRECTION --inspect-listing INSPECT_JSON --base-tensor-npy BASE_NPY \
  --checkpoint-ref artifact://SLUG/base_model \
  --payload-ref artifact://SLUG/astra-r1/patch/payload.safetensors \
  --export-ref artifact://SLUG/astra-r1/checkpoints/edited --out-dir PATCH_DIR
```

Preparation is create-only. It emits one spec and payload; no search or rescale
exists. A construction refusal ends the proposal. Validate/export through the
existing `weights-patch --validate` / `--export` CLI. The `--export-ref` argument embeds `export.output_dir` in the original spec;
never edit the emitted spec after preparation. Read back the exported tensor using its after-hash, then run
`astra_fixed audit` with all preparation inputs plus `--edited-tensor-npy`.
Its passed audit is required for the numerical freeze.

```bash
python -m hs20_nwe.astra_run freeze --base-model BASE --edited-model EDITED \
  --audit-ref AUDIT_REF --spec-ref SPEC_REF --payload-ref PAYLOAD_REF --prepare-ref PREPARE_REF
```

The lead commits `analysis-committed/astra_patch_freeze.json` before generating
any evaluation arm. It records exact factors/spec/audit/export hashes and checks
unchanged tokenizer/config sidecars. Both arms use the base tokenizer.

After runtime qualification, sign-off and that Git commitment:

```bash
VLLM_BATCH_INVARIANT=1 python -m hs20_nwe.astra_run eval-cell \
  --surface selfaware --prompt P-struct --arm base \
  --base-model BASE --edited-model EDITED --gpu-ack
```

Repeat for the eight registered surface/prompt/arm cells. Each uses the public
`batch-generate` verb with pinned HF batch-one/XGrammar settings after the
observed vLLM GDN batch-invariance refusal. Raw text, token
IDs and finish reasons persist by batch. Only malformed rows get up to two
format retries. Resume uses the same physical output paths and exact prompt
rosters. No cells may be added in response to a score.

`astra_benchmark` preserves the legacy metrics and separately builds the semantic
acceptance vectors. Every detector-negative final response from all eight cells
must pass through the existing committed/blinded adjudication lane before a
final verdict. A legacy-detector score alone cannot establish success.

Use `python -m hs20_nwe.astra_analysis` for `prepare-decoys`, `pool-build`,
`pool-commit`, `commit-hash`, `spot-pack`, `spot-record`, `regrade`, `apply`, and
`rollup`. These compose the existing adjudication implementation. The grader
input has only opaque IDs and answer text. The lead owns the required public
Git commitments and never commits the private pool, ID maps or raw grades.

The current calibration pool uses 25 historical positives and 25 held-back
historical negatives, with evaluation and construction questions excluded.
Its exact bytes are pinned in `astra_r1.yaml`. `prepare-decoys` verifies both
prior runlogs before selecting that pool; it performs no model inference.


Runtime qualification uses `python -m hs20_nwe.astra_qualification prepare`,
`run`, `verify`, and `verify-capture` in the exact registered image. It uses a
separate named namespace of twenty development questions, never benchmark rows.
Both repeats in both orders and an actual hard-killed/resumed run must retain
identical token IDs and whole-schema-valid outputs. Capture has its own hard-kill
and tensor-byte equality check. A changed source/runtime requires a fresh
qualification namespace; stale checkpoints are preserved, never bypassed.
