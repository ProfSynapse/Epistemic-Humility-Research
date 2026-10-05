# Decision-model calibrated choice notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

### 2026-10-04 (late): checklist 7 closed. `count_wrong` policy implemented; label timing complete

- **PI decision** (via coordinator, before any PopQA labeling or outcome): a
  generation containing a thinking marker is scored wrong and the run
  continues (`count_wrong`).
- **Shared EH instrument change** (opt-in; default unchanged):
  - `experiments/common/knowledge_probe/backends.py` adds
    `GENERATED_THINKING_POLICIES` (`abort` | `count_wrong`),
    `resolve_generated_thinking_policy(config)` (key
    `scoring.generated_thinking_policy`; absent = `abort`; other values raise),
    and `has_generated_thinking()`, which is the same `THINK_TAG_MARKERS`
    substring test as the abort path.
  - `VLLMBackend` takes `generated_thinking_policy` and skips its own assert
    only under `count_wrong`.
  - `probe.py` scores a marker-bearing sample or greedy decode as incorrect
    under `count_wrong`. Rows gain `generated_thinking_policy`,
    `n_sampled_thinking_marker` and `greedy_thinking_marker` (only under the
    opt-in, so default-policy rows keep their historical schema), and the
    manifest gains a `generated_thinking` run summary.
  - Other users of the shared files: dial-logprob-baseline-v2/-v3 and
    dial-logprob-t-deployed-confirmatory list `backends.py` as an unpinned
    repository input. Their render path is untouched, and no signed experiment
    pins these files (`exp validate` OK).
- **Tests.**
  - New `tests/test_generated_thinking_policy.py` (12 tests): default aborts;
    `count_wrong` scores marked samples wrong and continues; a marked greedy
    decode blocks "known"; manifest counts; default row schema and manifest
    unchanged; `probe_config_sha` unchanged unless the key is set; VLLMBackend
    aborts by default and passes text through under `count_wrong`; invalid
    policies raise.
  - Windows python: the policy tests plus `test_probe_smoke.py` give 52 passed.
  - Full knowledge-probe suite in the runner image: before the change 12
    failed / 436 passed; after it 12 failed / 448 passed. The failure set is
    identical and pre-existing (hidden-state extraction and docker-config
    tests unrelated to probe.py). Lists are in `analysis/presign/kp_tests_{baseline,after}.txt`.
- **Cell wiring.**
  - `probe.yaml` sets `scoring.generated_thinking_policy: count_wrong`.
  - `gates.yaml g0_label_marker_bound.max_marked_rate: 0.05`.
  - The harness `label` stage writes the run-level marker summary and the flag
    to `label_run.json`. `convert` refuses while the flag is set until a PI
    acknowledgement is recorded.
  - `convert` reports label counts with marker-affected questions dropped.
  - `score` adds the drop-affected sensitivity for H-A, H-B, H-C and H-D1.
- **Label timing under `count_wrong`** (`presign/drill_resume.py --timing 200 0
  --only label --sandbox timing_label_cw`, exclusive GPU, 200 synthetic
  non-PopQA prompts, nothing scored against gold).
  - rc 0, wall 740.8 s. Engine init 376 s, including 325 s of compile.
  - 200 questions in about 306 s after init, or 1.53 s per question including
    per-row scoring and append+flush on the host mount.
  - Estimate for 14,267 questions: about 6 to 6.5 h.
  - Marker rate: 120 of 6,600 generations (1.82%; sampled 1.88%, greedy 0),
    touching 58 of 200 questions (29%). Below the 5% bound; flag false.
  - The rate is higher than the abort run's first impression (about 1 in 130).
    The AMENDMENT states the measured value and keeps the conservative
    rationale: no false knowns are possible.

### 2026-10-04 (evening): exclusive-GPU pre-sign checks and letter-logit provenance

Authorized by the PI via the coordinator. The GPU was exclusive: 13 MiB
used at start, no local-run containers. Inputs were the 20 smoke questions
plus deterministic synthetic arithmetic and unit-conversion prompts
(`presign/smoke_questions.py synthetic(seed=20261004)`); nothing was scored.
Chains were launched detached (Windows `Start-Process wsl.exe ...
run_exclusive{,2,3}.sh`), with a per-step UTC log in
`analysis/presign/excl/status.log`. Run record:
`analysis-committed/run_records/dmcc-presign-exclusive-20261004.json`.

- **(a) vLLM repeat/reorder smoke** (`presign/check_vllm.py --gpu-mem 0.90`,
  `VLLM_BATCH_INVARIANT=0`).
  - Attempt 1 failed in the engine compile with `PermissionError: 'nvcc'`.
    The detached WSL session inherits the Windows PATH, which includes a
    Windows CUDA toolkit `bin`. Fix: a Linux-only PATH, now also in
    `cell.yaml labeler.env`.
  - Attempt 2 completed. Engine load took 802 s, including a 364 s
    torch.compile that is now cached.
  - Attempt 3 (with the detail fields) loaded in 506 s.
  - Engine `prompt_token_ids` equal the runner render on 20 of 20 rows.
  - Single-request greedy (the probe.py regime) repeats on 20 of 20.
  - Batched greedy vs single greedy differ on rows 15 and 16; batched vs
    reversed differ on row 16; batched greedy across two engine processes
    differs on row 16.
  - Seeded sampled n = 8 repeats on 158 of 160 completions; rows 0 and 17
    each have one differing completion.
  - Verdict: PASS for the label regime, with non-bit-reproducible sampling
    disclosed (AMENDMENT checklist 3).
- **(b) Label kill-resume drill** (`presign/drill_resume.py --only label
  --sandbox drill_label2`, real `dmcc_harness label` -> EH `probe.py`).
  - Attempt 1 failed in the harness's `git rev-parse` under WSL: the
    worktree `.git` points to `F:/...`. Fix: a pure-Python HEAD resolver
    fallback, which resolves both the worktree (`6d686ca6`) and the
    submodule (`29f7af0c`).
  - Attempt 2 PASSED: killed after 568.5 s with 1 row written; resume rc 0
    in 606.7 s; 6 rows, 6 unique keys; the pre-kill row byte-identical.
- **(c) Stage 0 500-row timing shard** (`presign/drill_resume.py --timing 200
  500 --sandbox timing`, real `dmcc_harness stage0-extract`, runner image
  `sha256:b4166dbd...`).
  - 500 of 500 rows answered and captured, anchor and answer_end, 25 states x
    2048.
  - Wall time 912.2 s; first-to-last tensor 824 s, or 1.65 s per row; 200 MB
    on disk.
  - Real FIT rows were not used: they do not exist before labeling, and using
    them would be exposure.
- **Label throughput** (`--timing 200 0 --only label --sandbox timing_label`).
  - ABORTED at synthetic question 4 of 200. EH probe.py raised
    `RuntimeError: Qwen3 generated sampled[16] output containing thinking
    marker '</think>'` ("do not reuse this partial run").
  - Before the abort: greedy about 0.02 s and sampled n = 32 about 0.12 to
    0.42 s per question after load.
  - This blocks the registered label stage (AMENDMENT checklist 7, PI
    decision).
- **Estimates** (synthetic prompts):
  - Stage 0: at most about 8,560 rows x 1.65 s plus shard loads, about 4 to
    4.5 h and 3.4 GB.
  - Labeling, once checklist 7 is resolved: about 1.5 to 2.5 h for 14,267
    questions.
- **Letter-logit provenance** (secondary arm; pending provenance replaced).
  - Run dir `...\decision\decision-qwen35-2b-letter-logits\20261004_152616\final_model`;
    recipe `Trainers/recipes/decision_qwen35_2b_letter_logits.yaml` at tuner
    `29f7af0c` (training code unchanged since `31962293`); registry run id
    `55307ef8-ec80-414e-967d-c55ba6d7d1d6`; 3,045 steps, 2 h 15 m.
  - Hashes: adapter_model.safetensors `3ab902d84d2a937b74e1181a7018df9f558de5ee89310d66ea564d19b46b4180`;
    tree sha256 (bin/exp algorithm) `3aef07e292b2892d7e2812d2935ed054c01d3422dc330e52c486805e13f9dd96`.
    There is no readout head.
  - The pointer arm was re-hashed and is unchanged: tree `e0cc616d...`,
    adapter `7d66a8a9...`, head `d7d97981...`; 3,045 steps, 2 h 40 m.
  - Both tree digests are pinned in cell.yaml and gates.yaml G0. The harness
    G0 checkpoint check is now per-arm.
  - Disclosure added to prior-exposure item 4: the letter-logit model's
    strands-holdout training eval (accuracy 0.654, calibrated ECE 0.015,
    answer-change 0.097) has been observed.

### 2026-10-04: pre-sign infrastructure checks (lab-notebook tier; no outcomes)

Authorization: the PI's decision, relayed by the coordinator, to run pre-sign
infrastructure checks only: no labeling, no Stage 0 extraction and no
decision-model analysis. The PI also decided to keep all 14,267 PopQA rows,
which leaves the sample and power text unchanged. Every check used the 20
fixed non-PopQA smoke questions in `presign/smoke_questions.py`; nothing was
scored. Row-level outputs are in gitignored `analysis/presign/`. The
committed run record is
`analysis-committed/run_records/dmcc-presign-infra-20261004.json`. The GPU was
shared with the running training container
`local-run-decision-qwen35-2b-letter-logits-*`, which was not touched.

- **Engine repin.** `synaptic-tuner` moved to `29f7af0c` (per-row export, TEST
  state export, external frozen directions). Both analysis configs now carry
  `export.per_row: true`, `export.states: false`, and `directions:` for
  `base_gate` / `base_gate_permuted` / `base_dial`, each at its frozen layer.
  The cell's configs load under the engine's own `load_analysis_config`. The
  harness stages the frozen JSONs and checks them byte-for-byte against the
  freeze marker; H-D1 reads `directions.base_gate` plus per-row
  `direction_scores`.
- **Weights.** `Qwen/Qwen3.5-2B-Base` @ `b1485b2f` downloaded to the WSL HF
  cache (4.24 GiB safetensors).
- **Check 1, Stage 0 image: PASS.** `docker build --build-arg
  TRANSFORMERS_VERSION=5.17.0 --build-arg MECHINTERP_RUNNER_GIT_REVISION=29f7af0c...
  -t mechinterp-runner:dmcc-tf5.17.0 synaptic-tuner/docker/mechinterp-runner`
  produced Image ID `sha256:b4166dbd15d0c7d9cad8a07c46be1301dc5941eb4b4d629ae754dc27cb03eb9c`
  (the same ID from Windows and from WSL `--context default`). Provenance line:
  torch 2.9.1+cu128, transformers 5.17.0, python 3.10.12, image_git_revision
  29f7af0c. Pinned as `instrument.runtime_image_digest`.
- **Check 2, model load and layer index: PASS.** `presign/check_layer_index.py`
  in the Stage 1 image (unsloth digest; transformers 5.17.0, peft 0.21.2, torch
  2.11.0+cu128, with flash-linear-attention installed as the recipe does). It
  loaded the pointer checkpoint with `DecisionModel.load`, disabled the
  adapter, and ran the drill's exact prompt ids through `model._decoder()`
  (the `capture()` call). The runner's `mechinterp extract` saved 25 anchor
  states per row; the decoder returned 25 (`num_hidden_layers` 24). For every
  index i, extraction[i] matches decoder[i] at max relative L2 0.023, while
  the nearest neighbouring index is at least 0.30 away. Convention: 0 =
  embeddings, i = block i, 24 = after the final norm. The MechInterp
  `AutoModelForCausalLM` load is therefore the same text tower as the
  decision loader (a wrong or partial load would not match at 2%).
  Descriptive only, not a population result: with the adapter ENABLED the same
  states move by mean relative L2 0.10 (index 1) rising to 0.50 (index 23) and
  0.97 (index 24). This is noted in the H-D1 text.
- **Check 3, vLLM batch invariance: BLOCKED (unsupported).**
  `presign/check_vllm.py` with `VLLM_BATCH_INVARIANT=1` fails at engine init
  with `RuntimeError: VLLM batch_invariant mode is not supported for GDN_ATTN`
  (vLLM 0.27.1; Qwen3.5 gated DeltaNet). cell.yaml now sets it to "0";
  rationale under AMENDMENT "Lane".
- **Check 3b, vLLM repeat smoke without invariance: BLOCKED (shared GPU).
  INCIDENT.** With `VLLM_BATCH_INVARIANT=0` and `gpu_memory_utilization=0.30`,
  vLLM resolved `Qwen3_5ForConditionalGeneration` and profiled the vision
  encoder (budget 114,688 tokens, one video item). A 3.5 GiB allocation
  overran the cap, and the card sat at about 24.2 of 24.6 GB for about 7 minutes
  (16:41-16:48). The drafting agent killed the vLLM processes. The training
  container stayed `Up` and card memory returned to 6.7 GB. I did not inspect
  the container's internals (not permitted), so whether a training step was
  slowed or failed in that window is unverified; the training owner should
  check its log. Not retried. The label-path engine smoke needs an exclusive
  GPU.
- **Check 4, render identity: PASS (tokenizer level).**
  `presign/check_vllm_render.py` (vLLM 0.27.1 `vllm.tokenizers.get_tokenizer`,
  `CachedQwen2Tokenizer`, CPU, render mode `direct`) vs
  `presign/check_runner_render.py` (runner image, `dmcc_harness.render`),
  compared by `presign/compare_render.py`: 20 of 20 rows have identical prompt
  sha256 and identical token ids, and `encode == __call__` on every row.
  Engine-observed `prompt_token_ids` pend the exclusive-GPU smoke.
- **Check 5, kill-resume drill: PARTIAL.** `presign/drill_resume.py --only
  stage0-extract` runs the real `dmcc_harness stage0-extract` path (2 shards x
  3 rows) with only `cfg()` patched to a sandbox. The first two attempts failed
  and exposed harness defects, now fixed:
  1. the shard marker was an `os.replace` of the container's root-owned
     `manifest.json` (EACCES on the host mount); it is now an atomic copy;
  2. the container-created output dir was not writable by the harness user;
     the harness now pre-creates it and refuses if it is unwritable.
  Shard containers are also now named per shard and force-removed on resume,
  so an orphan from a killed client cannot keep writing.
  The third attempt PASSED: SIGKILL at 158.7 s after shard 0's marker, resume
  rc 0 in 215.0 s, shard 0 skipped with its marker byte-identical, shard 1
  completed, anchor and answer_end on all 6 rows, no leftover container. The
  kill landed between shards, so the orphan-cleanup path was not exercised.
  The `label` drill (real vLLM path) is BLOCKED with check 3b. EH probe.py's
  resume is covered by its own tests: `test_probe_smoke.py`, 40 passed,
  including the resumability tests.
- **Extra, Stage 0 -> Stage 1 direction contract: PASS.**
  `presign/check_direction_contract.py`: a throwaway `freeze_direction` on 6
  drill anchors at layer 12, loaded by the engine's `load_direction` and scored
  by `score_directions`. Schema `mechinterp-direction/v1`, 2048-d, layer
  resolved to 12, finite scores; a hidden-size mismatch raises. The direction
  carries no meaning (arbitrary labels) and was discarded.
- **Throughput note.** The runner and Stage 1 stacks both lack `causal_conv1d`,
  so transformers falls back to its reference PyTorch path for the short
  convolutions. That is slower but correct. Full Stage 0 wall-clock is unknown
  until a 500-row shard smoke runs on an exclusive GPU.

### 2026-10-04: draft scaffolded, engine pinned, Stage 0 added (drafting agent)

- Scaffolded with `bin/exp new` (type `eval`) in worktree
  `.worktrees/amendment-decision-model-calibrated-choice`, branched from
  `origin/main` at `e1a0bdf84`.
- `synaptic-tuner` gitlink moved from `6b01834b` (no `decision` method) to
  `26cb57c72c68c382cf9299096bce535d4a606929` (branch
  `jev-models-tuner-training-b55d92`, pushed). `31962293` adds the decision
  method, `26cb57c7` the confidence analysis. Verified
  `Trainers/decision/analyze_confidence.py` and
  `Trainers/decision/configs/experiments/confidence_analysis_{pointer,letter_logits}.yaml`
  exist at that commit. Interim pin; see AMENDMENT "Lane, runtime and engine
  pin".
- Stage 0 (base-model KU extraction -> probe-fit -> freeze) added at the PI's
  request through the coordinator. It is kept inside this amendment; the tier
  reasoning is in AMENDMENT "Stage 0".

### 2026-10-04: pre-sign feasibility probe (no model, no labels, no outcome)

Required by amendment-vs-lab-notebook.md ("every arm must be constructible
from real data"). Run on the HF-cached PopQA file only.

- Source: `akariasai/PopQA` @ `098765c79ea10a2cb19c828324e33281b8336ec0`,
  `test.tsv`, sha256 `9a5227f41bff0e4c331d4a774d946b12f95307892b58f860a9606ef356e6089b`.
- Rows: 14,267, ids unique. Fields present: id, subj, prop, obj,
  possible_answers, s_pop, question (plus aliases, URIs and o_pop). No row
  is missing a needed field.
- Every row has at least one alias that survives EH `normalize_answer`.
- Distractor feasibility: all 14,267 rows have >= 3 same-relation objects
  whose normalized text matches no gold alias.
- Relations (rows / distinct objects): director 1999/1521, screenwriter
  1999/1468, genre 1619/283, producer 1520/1133, author 1514/1158, composer
  978/624, country 838/107, capital 645/584, place of birth 584/434, father
  570/524, sport 547/49, occupation 532/84, capital of 363/356, religion
  338/70, mother 187/173, color 34/5.
- Pointer checkpoint
  `decision-qwen35-2b-pointer/20261004_122756/final_model`: tree sha256
  (bin/exp algorithm) `e0cc616de238cfad85a8627aaa47583dba7689ece63c9bedc4c63a6e9a4acbfc`.
  Files: adapter_model.safetensors `7d66a8a9d34f85eb3661b458598ed85e727a6748a4831effec83a820d3770ab6`,
  readout_head.safetensors `d7d979817375367ccec4bf09bfa54e2ffbea07872958b7462e328608c0857989`,
  decision_config.json `7cd67f757c189a44e0f00eecbb4e599519a8dc43ac74d3e57861e30094ad247e`
  (readout pointer, base revision b1485b2f, LoRA r16/alpha 32, max_length 4096).
- Base chat template (`final_model/chat_template.jinja`, copied from the base
  tokenizer): lines 149-152 implement `enable_thinking`. When it is off they
  render an empty `<think>\n\n</think>\n\n` marker, which probe.py's
  `assert_no_think_scaffolding` accepts. Read only; nothing rendered or
  generated.
- Harness split port: on 3,000 synthetic rows (no PopQA content), the
  harness's `engine_split` gave FIT/CAL/TEST lists identical, element for
  element, to the engine's `split_fit_cal_test` at `26cb57c7`. The helpers
  `auroc` / `wilson` / `three_way` returned the expected values on toy inputs
  (Wilson upper at 0/35 is 0.0989 and at 0/73 is 0.04999, matching the
  gates.yaml floor derivation).

### Pending before sign

See AMENDMENT "Pre-sign checklist". The coordinator owns the engine
capability request (per-row TEST states, `probs_r1`, `ku_probe_score`).
