# PREPARE — Build-Surface Confirmation: Generic `aux_head` (Phase A, frozen base)

**Phase:** PACT Prepare (focused, READ-ONLY build-surface confirmation — NOT a design
re-derivation). The approved design is `docs/sessions/0027 - aux-scalar-head-build-handoff.md`;
this doc confirms that design against the **actual base branch** and de-risks CODE/TEST.

**Workspace verified at prep time:**
- Submodule `synaptic-tuner/` on branch **`feature/aux-scalar-head` @ `8a4e5ac`** (`git rev-parse HEAD` == `git rev-parse origin/main`, i.e. our base **is** origin/main, a clean root).
- Root repo: `/mnt/f/Code/Epistemic-Humility-Research/`.
- Cross-branch precedent branch `feature/sft-subspan-loss-mask @ 278ddba` (= main+2) is present locally for `git show`.

> **Anchor-drift cause:** the handoff §3 `file:line` table was written against
> `feature/sft-subspan-loss-mask @ 278ddba` (main **plus** the two subspan commits).
> Our base is plain `main`/`8a4e5ac`, which does **not** carry those commits, so the
> SFT-trainer line numbers sit **~5 lines earlier** than the doc. All anchors below
> are re-confirmed against `8a4e5ac` and anchored on **symbol names**, not the doc's numbers.

---

## 0. Executive summary (read this first)

1. **§3 anchors re-confirmed** against `8a4e5ac`. Drift is small and uniform: SFT-trainer
   anchors are **−1 to −5 lines** (the subspan commits are absent on our base);
   `config_loader.py` and the embedding `frozen_head` anchors are **exact (0 drift)**.
   Full table in §1.

2. **CRUX — validation oracle data: PRESENT and RUNNABLE this session.** The cached
   `h_base`/`h_lora` hidden-state extractions that `probe_as_oracle_ceiling.py` and
   `probe_xdataset_transfer.py` read **exist on disk** in this workspace, are CPU-readable
   safetensors with the L35 key the scripts need, and the Amendment O result JSON
   (`probe_appropriateness_auroc = 0.9966`) is on disk as proof of a prior clean run. The
   TEST-phase validation bar (head AUROC vs probe oracle ≈ 0.98–0.997) is **runnable offline,
   no GPU**. **Caveat:** the data is **gitignored** (`*/hidden_states*/`) — it is a local,
   reproducible run product, so a fresh clone / CI / cloud lane would **not** have it. See §4.

3. **CRITICAL BUILD-SURFACE CORRECTION (highest-value finding).** The handoff §2.4 says
   "extend `collate_prepared_sft_batch` to carry `aux_target`." That is **necessary but
   not sufficient.** `prepare_sft_dataset._materialize` returns only
   `{input_ids, attention_mask, labels}` and calls
   `dataset.map(..., remove_columns=dataset.column_names)` — which **drops the
   `target_field` column at preprocessing time, before the collator ever runs.** The
   subspan precedent the doc cites does **not** touch the collator at all; it reads its
   per-row directive *inside `_materialize`* and bakes it into `labels`. So the real
   `aux_target` plumbing is a **two-hop** change: (a) read `target_field` inside
   `_materialize` and thread it into the returned row dict (mirroring how subspan reads
   `loss_mask_text`), THEN (b) stack it in the collator. See §2.4 + §3.

4. **SFT path uses a stock `transformers.Trainer` with NO `compute_loss` override today** —
   confirmed. `output_hidden_states` is enabled nowhere; the `AuxHeadTrainer.compute_loss`
   override is the place to enable it. See §3.

5. **`frozen_head` "separate save" is a partial precedent.** The embedding `frozen_head`
   head is persisted **with** the SentenceTransformer model via `add_module` + native ST
   serialization — it is **not** saved as a separate sidecar. The transferable part is the
   **freeze-all-but-appended-head `requires_grad` mechanics**; the separate
   `aux_head.safetensors` sidecar the design needs is **genuinely net-new** on the
   causal-LM `Trainer.save_model` path. See §2.5.

6. **hidden_size = 2560** for the first-use base (Qwen3-4B), empirically confirmed from the
   L35 shard shape `(2560,)`. Not read anywhere in the SFT path today → builder reads
   `model.config.hidden_size` (PEFT/Unsloth-wrap caution in §5). **"last non-pad token"** is
   computed nowhere today; the SFT collator **right-pads**, so the index is
   `attention_mask.sum(dim=1) - 1`. See §5.

---

## 1. §3 architecture-map anchors — re-confirmed against `feature/aux-scalar-head @ 8a4e5ac`

All paths relative to `synaptic-tuner/`. "Doc" = the §3 value (vs `278ddba`). "Now" = current line on `8a4e5ac`.

| What | Symbol | Doc (`278ddba`) | **Now (`8a4e5ac`)** | Drift |
|---|---|---|---|---|
| Model load (Unsloth `from_pretrained`) | `FastLanguageModel.from_pretrained(` | `model_loader.py:65` | `Trainers/sft/src/model_loader.py:65` | 0 |
| LoRA wrap | `FastLanguageModel.get_peft_model(` | `model_loader.py:172` | `model_loader.py:172` | 0 |
| Trainable-param accounting (mirror for head logging) | `trainable_params = sum(...)` | `model_loader.py:178` | `model_loader.py:178` | 0 |
| **SFT Trainer construction** (subclass here) | `trainer = Trainer(**trainer_kwargs)` | `train_sft.py:1000` | `Trainers/sft/train_sft.py:995` | **−5** |
| Data collator def (extend for `aux_target`) | `def collate_prepared_sft_batch` | `train_sft.py:231` | `train_sft.py:230` | **−1** |
| `data_collator` wired into trainer kwargs | `"data_collator": lambda features:` | `train_sft.py:998` | `train_sft.py:993` | **−5** |
| `trainer.train()` | `trainer.train(resume_from_checkpoint=...)` | `train_sft.py:1053` | `train_sft.py:1048` | **−5** |
| `trainer.save_model(...)` (does NOT save the head) | `trainer.save_model(` | `train_sft.py:1094` | `train_sft.py:1089` | **−5** |
| SFT config dataclasses / `Config` | `class Config:` | `config_loader.py:149` | `Trainers/sft/configs/config_loader.py:150` | **+1** |
| `EvolutionaryConfig` (template for `AuxHeadConfig`) | `class EvolutionaryConfig:` | `config_loader.py:135` | `config_loader.py:135` | 0 |
| `load_evolutionary_config` (loader template) | `def load_evolutionary_config` | `config_loader.py:225` | `config_loader.py:225` | 0 |
| `dict_to_dataclass` **silently drops unknown keys** | `if k not in fieldtypes: continue` | `config_loader.py:202-203` | `config_loader.py:202-203` (def at `:191`) | 0 |
| `load_config` | `def load_config` | `config_loader.py:265` | `config_loader.py:265` | 0 |
| SFT per-trainer CLI `parse_args` | `def parse_args` | `train_sft.py:357` | `train_sft.py:356` | **−1** |
| CLI override **application** precedent (evo flags) | `if args.evolutionary_*: config... = ...` | `train_sft.py:651-688` | `train_sft.py:646-690` | **~−5** |
| `--evolutionary-*` `add_argument` precedent (add flags here) | `parser.add_argument("--evolutionary-...` | (in `parse_args`) | `train_sft.py:408-418+` | — |
| **Trainable-head precedent** (`frozen_head` dispatch) | `if adapter_mode == "frozen_head":` | `embedding/model_loader.py:52,64,386,401` | `Trainers/embedding/src/model_loader.py:52,64,386,401` | **0 (exact)** |
| `frozen_head` append+freeze body | `def _apply_frozen_head` | (cited via :52/:64) | `Trainers/embedding/src/model_loader.py:224-270` | — |
| Subspan label-mask precedent (per-row directive) | `example.get("loss_mask_text")` etc. | `preprocessing.py:88`; `shared/sft_preprocessing.py:241-270` | **CROSS-BRANCH ONLY** — see §2.4 | N/A |

> **Subspan note:** `loss_mask_text` / `subspan` / `loss_mask_spans` are **absent on our base
> branch** (grep returns nothing). The precedent lives only on `feature/sft-subspan-loss-mask`.
> Read it with `git show feature/sft-subspan-loss-mask:<path>`. Its on-base analogue is the
> generic `prepare_sft_dataset` at `Trainers/sft/src/preprocessing.py:71-100` and
> `materialize_sft_features` in `shared/sft_preprocessing.py`.

---

## 2. The three named precedents to mirror

### 2.1 `frozen_head` save/load precedent — `Trainers/embedding/src/model_loader.py`

- **`:52`** `VALID_ADAPTER_MODES = frozenset({"full", "lora", "frozen_head"})` — the adapter-mode axis.
- **`:64`** `_FROZEN_HEAD_MODULE_NAME = "frozen_head_dense"` — the stable module name under which the head is registered.
- **`:386` / `:401`** — the two dispatch sites (`_apply_adapter_mode_fast` / `_apply_adapter_mode_fallback`) that route `frozen_head` → `_apply_frozen_head(model, spec)`.
- **`:224-270`** `_apply_frozen_head(model, spec)` — the body to mirror:
  1. `for param in model.parameters(): param.requires_grad = False` (freeze everything).
  2. Append a head **iff absent** (idempotent on the module name), then `model.add_module(_FROZEN_HEAD_MODULE_NAME, head)`.
  3. Unfreeze only the appended head's params.
  4. Note ST-specific subtlety (`activation_function=nn.Identity()` to keep it linear) — **not** transferable verbatim; the aux_head is a plain `nn.Linear`, not an ST `Dense`.

> **Transferable vs NOT:** the **freeze-all-then-unfreeze-only-the-head `requires_grad`
> pattern** (steps 1+3) is exactly what `AuxHeadTrainer` must do for `freeze_base=true`.
> **NOT transferable:** the *persistence*. The embedding head rides the SentenceTransformer
> container's native `model.save()` (because it was `add_module`'d into the ST `Sequential`).
> There is **no separate `state_dict` save anywhere in `Trainers/embedding/`** (grep
> confirms). The causal-LM `trainer.save_model()` (`train_sft.py:1089`) will **NOT** serialize
> an attached aux head → the `aux_head.safetensors` + `aux_head_config.json` sidecar (design
> §2.5) is **net-new code with no existing in-tree precedent for the separate-sidecar half.**

### 2.2 Subspan-mask per-row plumbing — `feature/sft-subspan-loss-mask` (cross-branch)

Read via `git show feature/sft-subspan-loss-mask:<path>`:

- **`Trainers/sft/src/preprocessing.py:~85-100`** — inside `prepare_sft_dataset._materialize`:
  ```python
  loss_mask_spans = example.get("loss_mask_text")          # per-row directive READ HERE
  if loss_mask_spans is not None and not isinstance(loss_mask_spans, list):
      loss_mask_spans = [loss_mask_spans]
  prepared = materialize_sft_features(..., loss_mask_spans=loss_mask_spans)
  ```
- **`shared/sft_preprocessing.py:241-270`** — `materialize_sft_features` consumes the spans and
  sets `labels[idx] = -100` for overlapping tokens (raises `ValueError` if a span is not found —
  **loud-fail discipline, mirror this for a missing/NaN target**).
- **`Trainers/sft/train_sft.py` collator on that branch** — `collate_prepared_sft_batch` is
  **byte-identical to `main`.** The subspan feature **never touches the collator.**

> **The lesson for `aux_head` (corrects handoff §2.4):** the subspan precedent proves the
> per-row directive is **read inside `_materialize`**, not in the collator. Subspan can stop
> there because it folds into `labels`. `aux_target` is a *separate supervising float* and
> **cannot** fold into `labels`, so it needs BOTH hops:
> 1. **Preprocessing hop (the part the doc omits):** extend `_materialize` (base:
>    `preprocessing.py:82-95`) to read `example.get(target_field)` and include it in the
>    returned dict, so it survives `remove_columns=dataset.column_names` (base:
>    `preprocessing.py:99`). Without this, the column is destroyed before batching.
> 2. **Collation hop (the part the doc names):** extend `collate_prepared_sft_batch` (base:
>    `train_sft.py:230`) to stack the per-row float into an `aux_target` tensor (and an
>    `aux_target_mask` if missing values are allowed).

### 2.3 `EvolutionaryConfig` dataclass + loader — `Trainers/sft/configs/config_loader.py`

- **`:135`** `class EvolutionaryConfig:` — the dataclass template for `AuxHeadConfig`.
- **`:150`** `class Config:` — add an optional `aux_head: AuxHeadConfig = field(default_factory=...)` field here (mirror `:157` `evolutionary: EvolutionaryConfig = field(default_factory=EvolutionaryConfig)`).
- **`:191-223`** `def dict_to_dataclass(cls, data)` — **the silent-drop gotcha, confirmed verbatim:**
  ```python
  for k, v in data.items():
      if k not in fieldtypes:      # :202
          continue                 # :203  <-- unknown YAML keys silently dropped
  ```
  → If `AuxHeadConfig` is not added as a real dataclass field on `Config`, the entire
  `aux_head:` YAML block is **silently ignored** and the feature stays off with no error.
- **`:225-263`** `def load_evolutionary_config(evo_data)` — the loader pattern to mirror as
  `load_aux_head_config(...)`: returns a default-constructed config on absent/empty input,
  else builds the dataclass field-by-field.
- **`:265`** `def load_config(...)` — top-level loader; wire `load_aux_head_config` in here.

---

## 3. SFT loss path: stock `Trainer`, no override, where to enable hidden states

**CONFIRMED:** the SFT path constructs a **stock `transformers.Trainer`** at
`train_sft.py:995` (`trainer = Trainer(**trainer_kwargs)`) with **no `compute_loss`
override and no `Trainer` subclass** anywhere in `Trainers/sft/`. Default causal-LM loss is
used. (The only `compute_loss*` hit is `compute_losses_flag` at `train_sft.py:1112` — an
unrelated post-hoc loss-*reporting* flag, NOT a `Trainer.compute_loss` override.)

- **No call passes `output_hidden_states=True` today** (grep: zero hits in the SFT path).
- **Where to enable it:** inside `AuxHeadTrainer.compute_loss`, on the model forward —
  `outputs = model(**inputs, output_hidden_states=True)` — exactly as handoff §2.3 step 2 says.
  This is the single enable point; do not set it globally on the config.
- **Training invocation:** `trainer.train(resume_from_checkpoint=...)` at `train_sft.py:1048`
  (the non-evolutionary branch; the evolutionary branch uses `evo_wrapper.train()` at `:1046`).
  Construct `AuxHeadTrainer` at `:995`, swap it in behind `aux_head.enabled`.
- **`remove_unused_columns: False`** is already set in `trainer_kwargs` (`train_sft.py:889`).
  Good — it means the stock Trainer won't strip extra batch columns. **But** this does NOT
  rescue the `target_field`, because `prepare_sft_dataset` already removed it at
  `preprocessing.py:99` (§2.2). The two are independent; the preprocessing hop is still required.

---

## 4. CRUX — Validation-oracle availability (cached `h_base`/`h_lora`)

**Question:** do the cached hidden-state extractions that the offline probe scripts read
actually exist on disk, and is the readout CPU-runnable offline for the TEST validation bar?

**ANSWER: YES — present, CPU-runnable, offline. The TEST validation bar is runnable this
session.** (With a gitignore caveat — see below.)

### How the scripts read data (verified by reading both scripts)
Both `experiment/phase1/probe/probe_as_oracle_ceiling.py` and `probe_xdataset_transfer.py`
take an **`extraction_dir`** containing:
- `rows.jsonl` — one row per example with `label ∈ {known, unknown}` and `probe_pool_row_key`.
- per-row shards named `{probe_pool_row_key}__h_base.safetensors` (key sanitized: `::`→`__`, `|`→`_`),
  each a safetensors file with **per-layer keys `L0..L36`** (numpy). `probe_xdataset_transfer.py`
  also supports `__h_lora.safetensors` via `--source h_lora`.

> **Layout gotcha (cost me a false-negative first pass):** the real `extraction_dir` is a
> **nested `extraction__<hash>/` subdir**, NOT the parent `hidden_states_*/` dir. The
> `hidden_states_*/` parent holds only the result JSON; `rows.jsonl` + shards live one level deeper.

### Verified on-disk inventory (this workspace, prep time)

| Use | Extraction dir | `rows.jsonl` | `h_base` shards | `h_lora` shards |
|---|---|---|---|---|
| **Amendment O oracle** (clean-SFT SelfAware) | `experiment/phase1/probe/qwen3-4b-clean-sft-seed1-selfaware/hidden_states_selfaware_clean_sft_full/extraction__8dbd3f623393/` | 1233 | 1233 | 1233 |
| **Amendment P TEST** (SelfAware grpo-v2, cold) | `experiment/phase1/probe/qwen3-4b-clean-sft-grpo-v2-seed1-selfaware/hidden_states_selfaware_clean_sft_grpo_v2_full/extraction__55254a04aa1f/` | 1233 | 1233 | — |
| **Amendment P FIT** (KUQ grpo-v2) | `experiment/phase1/probe/qwen3-4b-clean-sft-grpo-v2-seed1-kuq/hidden_states_kuq_clean_sft_grpo_v2_full/extraction__cfdf25500cf3/` | 1000 | 1000 (present) | — |

- Whole probe tree: **44 `rows.jsonl`, 11,015 `h_base` shards, 11,015 `h_lora` shards** (34,966 `.safetensors` total).
- A sample O-oracle shard verified CPU-readable: **37 layer keys (`L0..L36`), `L35` present, shape `(2560,)` float32**.
- **Proof of a prior clean run:** `.../hidden_states_selfaware_clean_sft_full/amendment_o_probe_as_oracle.json` is on disk with
  `probe_appropriateness_auroc = 0.9966`, `ece = 0.0149`, `action_margin = 95.1pts`,
  `all_gates_pass = true`, `answered_known_correctness_auroc = 0.6402`. (The Amendment P
  result JSON is **not** on disk, but its input extractions ARE — P is re-runnable.)

### Runnability for the TEST bar
- **CPU-only, offline, no GPU, no network** — the scripts use `numpy` + `scikit-learn`
  (`LogisticRegression`, `StratifiedKFold`, `StandardScaler`) on cached tensors.
- Example invocation the TEST phase can mirror for the head-vs-oracle comparison:
  ```bash
  python3 experiment/phase1/probe/probe_as_oracle_ceiling.py \
    experiment/phase1/probe/qwen3-4b-clean-sft-seed1-selfaware/hidden_states_selfaware_clean_sft_full/extraction__8dbd3f623393 \
    --layer 35
  ```
- The trained `aux_head` (layer 35, `last` token, bce) should reproduce the
  **probe_appropriateness_auroc ≈ 0.997** neighborhood on the same rows. A large gap ⇒
  token-position / layer-index / dtype / target-plumbing bug (per handoff §7).

### ⚠️ Caveat (must reach ARCHITECT/CODE/TEST)
The extraction data is **gitignored** (`experiment/phase1/probe/.gitignore: */hidden_states*/`
and the root `.gitignore: experiment/phase1/probe/analysis/**/*.safetensors`). It is a **local,
reproducible run product**, NOT committed. Therefore:
- **This-session local TEST:** ✅ runnable now (data is materialized in this checkout).
- **Fresh clone / CI / HF-Jobs cloud lane / another machine:** ❌ data absent — would require
  re-running the GPU extraction first. **Do not assume the validation bar is portable.** If
  TEST runs anywhere but this workspace, it degrades to **smoke-only** and the AUROC
  validation must be **deferred** (or the extraction re-materialized on a GPU box first).

---

## 5. Head input_dim (hidden_size) + "last non-pad token" mechanics

### hidden_size (head `input_dim`)
- **Not read anywhere in the SFT path today** (only an unrelated `webgpu.py` converter references
  `hidden_size`). The builder must read it from the loaded model: **`model.config.hidden_size`.**
- **First-use value confirmed empirically: 2560** (Qwen3-4B), from the L35 shard shape `(2560,)`.
- **PEFT/Unsloth-wrap caution:** the model returned by `FastLanguageModel.get_peft_model`
  (`model_loader.py:172`) is a PEFT wrapper. `.config` usually proxies to the base, but if
  `model.config.hidden_size` is unavailable on a given wrap, fall back to
  `model.base_model.config.hidden_size` (or `model.get_input_embeddings().embedding_dim`).
  Resolve `input_dim` once at head-construction time (handoff build-plan step 7) and store it
  in the saved `aux_head_config.json` so the inference hook reconstructs the right shape.

### "last non-pad token" from the attention mask
- **Computed nowhere today** — this is net-new for `compute_loss`.
- **Padding side: RIGHT-pad**, verified in `collate_prepared_sft_batch`
  (`train_sft.py:230-259`): each row is padded on the right —
  `attention_mask = mask + [0]*pad_len`, `input_ids = ids + [pad_token_id]*pad_len`,
  `labels = labels + [-100]*pad_len`.
- Therefore the **last non-pad token index per row** is:
  ```python
  last_idx = attention_mask.long().sum(dim=1) - 1          # [batch], right-padded
  h_last = hidden[torch.arange(hidden.size(0)), last_idx]  # [batch, hidden]
  ```
  For `token_position="mean"`, use a mask-weighted mean over the sequence; for an int index,
  index directly. (Guard `last_idx >= 0`; an all-zero mask row should be impossible given the
  collator always keeps ≥1 real token, but a `clamp_min(0)` is cheap insurance.)
- **Consistency check for TEST:** the offline extraction (`hs_backends.py:251`
  `TransformersPeftBackend.forward_hidden_states`) takes the **final prompt token, all layers,
  batch=1**. If the `aux_head` validation is to match the probe oracle, the head's
  `token_position` must select the **same token** the extraction used. The extraction is
  batch=1 (no padding), so its "final token" == last real token == the head's right-pad
  `sum-1`. This alignment is what makes the AUROC comparison apples-to-apples — flag for TEST.

---

## 6. Risks / open questions for ARCHITECT

| # | Item | Severity | Note / mitigation |
|---|---|---|---|
| R1 | `target_field` dropped by `_materialize` `remove_columns` before collation | **HIGH** | The doc's collator-only plan is insufficient. Two-hop fix (§2.2). Highest-value finding; bake into the ARCHITECT contract. |
| R2 | aux_head sidecar save has **no in-tree precedent** (embedding head rides ST native save) | MED | Separate `aux_head.safetensors` + `aux_head_config.json` is net-new; budget for it (§2.5/§2.1). |
| R3 | Validation oracle data is gitignored / local-only | MED | Runnable this session; **not** portable to cloud/CI. Gate the AUROC bar on "local lane only" or re-extract first (§4 caveat). |
| R4 | `model.config.hidden_size` access through PEFT/Unsloth wrap | LOW | Resolve once at construction; fall back to `base_model.config` (§5). |
| R5 | token-position alignment between trained head and offline extraction | LOW-MED | Both must select the last real token (§5 consistency check) or the AUROC comparison is invalid, masquerading as a bug. |
| R6 | `dict_to_dataclass` silent-drop | LOW | Known gotcha; just add the real `AuxHeadConfig` field on `Config` (§2.3). |

**No algedonic signal warranted.** Scope matches the dispatch (read-only confirmation); no
security/ethics/scope-misunderstanding trigger surfaced. The design is sound and buildable
on our base; the one substantive correction (R1) is a *completeness* fix to the plumbing
plan, not a design contradiction.

---

## 7. Sources (all primary, read at prep time on `8a4e5ac` / cross-branch `278ddba`)

- `synaptic-tuner/Trainers/sft/train_sft.py` (`8a4e5ac`) — collator `:230`, Trainer `:995`, train `:1048`, save `:1089`, parse_args `:356`, evo overrides `:646-690`, `remove_unused_columns:False` `:889`, no `compute_loss` override.
- `synaptic-tuner/Trainers/sft/src/model_loader.py` (`8a4e5ac`) — `:65/:172/:178`.
- `synaptic-tuner/Trainers/sft/src/preprocessing.py` (`8a4e5ac`) — `prepare_sft_dataset` `:71-100`, `remove_columns` `:99`.
- `synaptic-tuner/Trainers/sft/configs/config_loader.py` (`8a4e5ac`) — `:135/:150/:191-223/:202-203/:225/:265`.
- `synaptic-tuner/Trainers/embedding/src/model_loader.py` (`8a4e5ac`) — `:52/:64/:224-270/:386/:401`; no separate head `state_dict` save in `Trainers/embedding/`.
- `git show feature/sft-subspan-loss-mask:Trainers/sft/src/preprocessing.py` + `:shared/sft_preprocessing.py` (`278ddba`) — subspan per-row directive read inside `_materialize`; collator unchanged.
- `experiment/phase1/probe/probe_as_oracle_ceiling.py`, `probe_xdataset_transfer.py` (root) — extraction-dir read contract.
- `experiment/phase1/probe/hs_backends.py:251` (root) — extraction token/layer semantics.
- On-disk verification: 3 extraction dirs (O-oracle / P-TEST / P-FIT), shard counts, L35 `(2560,)` float32, `amendment_o_probe_as_oracle.json` (AUROC 0.9966), `.gitignore` rules.
