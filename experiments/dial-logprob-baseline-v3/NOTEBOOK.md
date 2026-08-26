# Dial token-logprob baseline v3: fresh self-consistent generation, no reproduction bet notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

### 2026-08-13 -- harness build: dry-run + smoke results

`--dry-run` (CPU-only, no model): resolves the pool-loader module
(`amendment_s_correctness_probe_extract.build_pool`), the scorer module
(`archive/experiment/phase1/eval/scorers.py`), the dial-refit module
(`amendment_s_correctness_probe_score.py`), and both arms' checkpoint paths
(S hub id `unsloth/Qwen3-4B-bnb-4bit`; T local merged-16bit dir + LoRA adapter
dir, both confirmed present on disk). Prints resolved-input counts/fingerprints
only, no row content. Exit 0.

`test_lp_v3_smoke.py` (CPU/tiny-CPU-model, pytest): exercises
`run_arm_generation` (via a `_StubVLLMEngine` wrapping a real tiny HF model so
token_ids/logprobs are internally consistent and realistic without needing
real vLLM), `assert_capture_integrity` (LP3-G0a, both pass and induced-fail
cases), `select_attempted` (target-count replay logic), the teacher-forced
extraction pass (tiny HF model, `output_hidden_states=True`), and
`score_arm_v3` (LP3-G0 b/c/d + LP3-G1 gate evaluation, both a full-pass path
and each induced-failure path). All fabricated `fx`-token content per the
public-repo containment rule. Result: all tests pass (see build report for
exact counts).

### 2026-08-13 -- vLLM capability check (build verification, before harness code)

**Version pinned:** vllm==0.27.1 (latest stable on PyPI at pin time, per
`pip index versions vllm`), installed into an isolated venv
`/home/profsynapse/.venvs/vllm` (NOT the shared base conda env other sessions'
work depends on -- vLLM pulls its own torch build, and installing it into the
shared base env would have silently upgraded torch under every other running
agent). Full pinned stack recorded, resolved by `pip install vllm==0.27.1`
into a clean venv:

- vllm 0.27.1
- torch 2.13.0+cu130 (vLLM's own pin; distinct from the base conda env's
  torch 2.9.0+cu128 used elsewhere in this repo -- the two never mix)
- transformers 5.15.0
- safetensors 0.8.0
- numpy 2.3.5
- bitsandbytes 0.50.0 (installed separately; not a vllm dependency by default;
  required minimum for vllm's bnb quant path is >=0.48.1, satisfied)
- scikit-learn 1.9.0 (installed separately; needed for the CPU dial-refit path
  so scoring can run in the SAME stack as generation, per AMENDMENT.md
  "Environment: ... generation, extraction, and scoring all execute inside
  one run on one stack")
- peft 0.20.0 (installed separately; needed for the teacher-forced-fallback
  HF+PEFT load of the T arm's adapter, in the same stack)

**Capability verdict, checked against vllm 0.27.1's actual installed source
and the current official docs (fetched 2026-08-13), per the standing
anti-stale-knowledge discipline (never rule vLLM capability from memory):**

- **(a) generated token IDs -- CERTAIN, available.**
  `vllm.outputs.CompletionOutput.token_ids` (`vllm/outputs.py`). Standard,
  long-standing field.
- **(b) per-token logprobs for generated tokens -- CERTAIN, available.**
  `SamplingParams.logprobs: int | None` (`vllm/sampling_params.py:267-274`):
  "the API will always return the log probability of the sampled token."
  `logprobs=0` returns exactly the sampled token's own logprob per position
  (OpenAI-API-compatible semantics) -> `CompletionOutput.logprobs`, a
  `list[dict[int, Logprob]]` keyed by token id, one dict per generated
  position. This is what the harness uses for the primary/secondary logprob
  variants (mirrors v2's use of `gen.scores`, just sourced from vLLM instead
  of HF).
- **(c) per-token hidden states at a chosen intermediate layer at generation
  time -- NOT available in the sense the AMENDMENT's design assumed. Build
  verification finding, registered fallback applies.**
  `vllm.outputs.RequestOutput` / `CompletionOutput` expose no `hidden_states`
  field at all (grepped `outputs.py`, zero hits). The only hidden-state
  mechanism present in this vLLM version is `extract_hidden_states`
  (`vllm/model_executor/models/extract_hidden_states.py`,
  `vllm/v1/spec_decode/extract_hidden_states.py`,
  `vllm/transformers_utils/configs/extract_hidden_states.py`,
  `vllm/distributed/kv_transfer/kv_connector/v1/example_hidden_states_connector.py`).
  Read in full: this is a **speculative-decoding draft-proposer method**, not
  a general per-request hidden-state readout. It requires: a
  `speculative_config` with `method="extract_hidden_states"`,
  `num_speculative_tokens` fixed at 1, `disable_padded_drafter_batch=False`;
  a **draft model config** whose `hf_config.eagle_aux_hidden_state_layer_ids`
  names the layers to cache; and a **KV-transfer config** naming a connector
  (the shipped example is `ExampleHiddenStatesConnector`) plus a shared
  storage path (docs recommend `/dev/shm` for online use). Confirmed against
  the official docs
  (`https://docs.vllm.ai/en/stable/features/speculative_decoding/extract_hidden_states/`,
  fetched 2026-08-13): "allows vLLM to save intermediate layer activations
  from a target model during inference. This is useful for training
  EAGLE-style draft models." Retrieval is **not a direct return value**:
  results come back as `output.kv_transfer_params["hidden_states_path"]`, a
  path to a `.safetensors` file the caller loads separately via the
  connector's `load_hidden_states()` helper.

  This does not satisfy "the SAME vLLM call returns per-token hidden states
  at the arm's signed dial layer" in any direct, single-call sense the
  AMENDMENT's design assumed. Standing it up for this cell's actual need (one
  residual-stream vector, at the dial layer in the `hidden_states`-tuple
  indexing the S/T extractors and the dial were fit against, at exactly the
  last-content-token position, per row) would require: (i) reverse-engineering
  how vLLM's `eagle_aux_hidden_state_layer_ids` decoder-layer indexing maps
  onto that tuple indexing -- an unvalidated layer-semantics risk
  (`.skills/experiment-runner/reference/batched-generation.md`: "Layer IDs
  are model-implementation semantics, not labels to trust by name" / "Do not
  relabel vLLM layers to make the bridge pass"); (ii) implementing or adapting
  a KV connector and its shared-storage retrieval path; (iii) running the
  reference doc's full 4-stage bridge validation (capability smoke, numerical
  bridge against the HF reference, estimator bridge, persistence/resume)
  before this could be trusted for an established capture instrument. None of
  that is achievable inside a harness-build task, and it is exactly the kind
  of generic engine capability the reference doc reserves for Synaptic Tuner
  on its own branch/PR, never buried in an experiment directory.

  **Verdict: (c) is not available in the pinned version in the required
  sense. The AMENDMENT's own registered fallback applies**: "a teacher-forced
  transformers forward pass over each row's captured token IDs (prompt +
  generated, verbatim) at the same layer." The harness implements this
  fallback inside the SAME pinned stack/process as the vLLM generation
  (transformers 5.15.0 + peft 0.20.0 + bitsandbytes 0.50.0, all in the same
  venv), consuming vLLM's own reported `prompt_token_ids` + completion
  `token_ids` directly -- never re-tokenized -- satisfying LP3-G0(a)'s per-row
  capture-integrity assertion by construction.

- **bitsandbytes quantization -- CERTAIN, available.**
  `vllm/model_executor/layers/quantization/bitsandbytes.py`, requires
  `bitsandbytes>=0.48.1` (installed 0.50.0). S arm loads via
  `quantization="bitsandbytes"`.
- **LoRA -- CERTAIN, available.** `vllm/lora/request.py` (`LoRARequest`) plus
  the full `vllm/lora/` subpackage. T arm loads the merged-16bit base with
  `enable_lora=True` and a `LoRARequest` naming the pinned adapter dir.

**Live GPU capability smoke (tiny model, seconds intended; NOT any S/T
checkpoint; no arm run):** attempted a live check of (a)/(b) mechanics on the
real RTX 3090 using `sshleifer/tiny-gpt2`. Two WSL2-specific environment
gotchas surfaced and were fixed, both worth pinning into `cell.yaml`'s engine
block for the real run:

1. **UVA unavailable by default under WSL2.** vLLM's new (v2) GPU model
   runner requires pinned/UVA buffers; `vllm.platforms.cuda.CudaPlatform.
   is_pin_memory_available()` hard-disables pinned memory under WSL2 unless
   `VLLM_WSL2_ENABLE_PIN_MEMORY=1` is set (gated on WSL2 kernel
   >=4.19.121; this host qualifies). Without the env var, engine init fails
   with `RuntimeError: UVA is not available`.
2. **After the UVA fix, `sshleifer/tiny-gpt2`'s GPT2 architecture selected
   FLEX_ATTENTION as its only available attention backend** (no
   FlashAttention/FlashInfer backend registered for GPT2 in this vLLM build),
   and the first-call `flex_attention()` kernel JIT-compiled via
   `torch.inductor` for over 5 minutes without completing (confirmed
   *actively* computing throughout -- 100% GPU util, ~95% CPU on the
   EngineCore subprocess, not deadlocked). Killed at 5m25s as a
   disproportionate cost for a capability probe on an unrepresentative toy
   architecture. GPT2's backend selection has no bearing on Qwen3 (a
   mainstream architecture with native FlashAttention/FlashInfer backend
   support in vLLM, which will not hit this JIT-compile path). Because (a)/(b)
   are already unambiguous from source (long-standing, OpenAI-API-compatible
   fields) and (c)'s absence is independently confirmed by both source and
   official docs, this inconclusive live-smoke result on an unrepresentative
   model is **not treated as blocking** the capability verdict above; the
   verdict stands on the source+docs evidence.

**Batch invariance:** `VLLM_BATCH_INVARIANT=1`
(`https://docs.vllm.ai/en/stable/features/batch_invariance/`, fetched
2026-08-13), requires NVIDIA compute capability >=8.0; this host's RTX 3090
reports compute_cap 8.6 (`nvidia-smi --query-gpu=compute_cap`), satisfies. The
docs do not name required scheduler pins alongside batch invariance; the
reference doc still directs pinning `max_num_seqs` / `max_num_batched_tokens`
for reproducibility -- `cell.yaml` records proposed values, **not validated by
this build task** (no arm was run, no vLLM generation smoke over real S/T
prompts was performed; that is registered as a pre-launch step, per
`.skills/experiment-runner/reference/batched-generation.md` "vLLM generation
smoke").

**Environment note (unrelated to this experiment but discovered during
build):** the base conda env (torch 2.9.0+cu128, transformers 5.5.0) is left
untouched; the isolated `/home/profsynapse/.venvs/vllm` venv is new
infrastructure, following the existing `.venvs/modal` / `.venvs/runpod`
convention, reusable by future vLLM-backed cells per the PI's forced-default
ruling.

### 2026-08-13 -- SIGNED; GPU launch (smoke + both arms)

PI approval: "sign and launch then merge" (2026-08-13). Signed via `bin/exp
sign` (first cell through the generation-engine sign gate; pins recorded in
experiment.yaml instrument.sha256: cell.yaml 133c3a80, gates.yaml 4f0f9c7b,
lp_v3_harness.py 1f3c0d47).

Launch plan, recorded before the launch verb per the launch guard:
1. Pre-launch vLLM generation smoke (registered pre-launch step for the
   unvalidated scheduler pins): scratchpad script reusing the harness's own
   `build_vllm_engine`/`build_sampling_params`/`build_lora_request` on 4
   dummy non-evidence prompts per arm, one process per arm. Asserts
   token_ids + aligned per-token logprobs. Evidence rows untouched.
2. s_base_primary: --phase generate, then --phase extract, then --phase
   score, EACH AS A SEPARATE PROCESS (lead adjudication of build flag #2:
   separate-process phases chosen for guaranteed GPU memory release between
   the vLLM engine and the HF teacher-forced extraction model).
3. t_deployed_descriptive: same three-phase sequence.

Env (per cell.yaml engine.env_vars + host gotchas): VLLM_WSL2_ENABLE_PIN_MEMORY=1,
VLLM_BATCH_INVARIANT=1, HF_HUB_OFFLINE=1 (as-cached checkpoint pins; also
avoids the known uid-1001 .locks permission issue). Interpreter:
/home/profsynapse/.venvs/vllm/bin/python (pinned stack). Fail-fast: any
non-zero rc aborts the sequence.

### 2026-08-13 -- Launch attempt 1 aborted at engine init; repair #1 (host env)

First launch invocation aborted during the pre-launch S-arm generation smoke,
before any evidence row: vLLM engine init failed in torch.compile's inductor
profile run with `PermissionError: [Errno 13] Permission denied: 'nvcc'`.
Diagnosis: host PATH resolves nvcc to the Windows-mount CUDA v12.1 toolchain
(`/mnt/c/Program Files/...`), which WSL cannot exec; a working Linux nvcc
exists at /usr/local/cuda/bin (CUDA 12.8). Repair #1: launch wrapper exports
CUDA_HOME=/usr/local/cuda and prepends /usr/local/cuda/bin to PATH. Host
plumbing only -- no pinned file touched (cell.yaml/gates.yaml/harness shas
unchanged). Relaunching the identical sequence.

### 2026-08-13 -- Run complete (attempt 2), both arms; adjudication

Relaunch after repair #1 ran the full registered sequence clean, rc=0
end-to-end (smoke S PASS, smoke T PASS; S generate/extract/score; T
generate/extract/score). Wall time ~12 min total on the 3090 -- the vLLM
generation phases took ~2.5 min per arm vs v2's 43 min HF path.

S arm (primary): LP3-G0 PASS on all four criteria -- (a) capture integrity
0 failures out of all rows (v2's failure class: 282/1836 = 15.4%
round-trip divergences; the single-capture design removed it entirely),
(b) coverage complete, (c) 1820 answered >= 1000 floor, (d) fresh dial OOF
AUROC 0.8301 >= 0.75 sanity bound (signed June value 0.834; NOT a
reproduction target, noted descriptively). LP3-G1: dial minus
primary-logprob margin +0.0118, paired 95% CI [-0.0122, +0.0359], n_boot
2000. Floor +0.05 not met and CI straddles 0 -> registered AMBIGUOUS BAND
disposition ("small/uncertain margin"). Dial-novelty falsifier (margin <= 0
with CI excluding 0 in that direction): NOT fired. LP3-G0 self-integrity
falsifier: NOT fired. Registered prediction for S ("near +0.02, LP3-G1
most likely NOT passing") landed as stated.

T arm (descriptive-only, no gate): LP3-G0 (a) integrity 0 failures and (b)
coverage PASS, but (c) power floor FAILED -- 710 answered < 1000 floor
(June source inventory had 1488). The arm records the registered
data-stage stop; per gates.yaml its descriptive statistics are not
reported. The registered T prediction (+0.15) is therefore untested.
Observation recorded as hypothesis only: the deployed abstention-trained
checkpoint refuses more under fresh greedy vLLM generation
(enable_thinking=False) than in the June cache; the attempt cap (4000,
verbatim source-extractor default) was pinned, so the shortfall is
reported straight, not padded.

Both result JSONs (aggregates only, containment-checked: counts, AUROCs,
CIs, gate booleans; no row text) written to analysis-committed/.
