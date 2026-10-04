# Decision-model calibrated choice notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

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
