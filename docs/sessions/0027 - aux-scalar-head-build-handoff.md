---
schema_version: research-session/v1
session_id: '0027'
title: Aux Scalar Head Build Handoff
status: complete
created_at: '2026-06-29T00:00:00Z'
updated_at: '2026-06-29T00:00:00Z'
phase: phase3
question: How should a fresh builder implement the generic frozen-base aux_head
  readout feature (Phase A) in the synaptic-tuner submodule?
tags:
- aux-head
- synaptic-tuner
- engine-build
run_ids: []
trajectory:
  anchor: experiment/protocol/research-trajectory.md
  current_position: 'Amendments O/P merged (readout ceiling + cold cross-dataset
    transfer); decided to productize the linear readout as a generic aux_head head.'
  changed_by_session: 'Authored the build handoff for the generic aux_head feature
    (Phase A, frozen base); no code written yet.'
checkpoints: []
---

# 0027 — Build Handoff: Generic Auxiliary Scalar Readout Head (`aux_head`) — Phase A (frozen base)

**Audience:** a fresh builder agent (and a human reviewer) implementing this in a
**separate conversation**. This doc is self-contained — you should not need the
originating conversation's context.

**Status:** design approved 2026-06-29. Ready to build. **Phase A only** (frozen
base). Phase B (joint multi-task) is explicitly out of scope here but the design must
keep it a config flag away (see §9).

**Where the work happens:** the `synaptic-tuner` **git submodule** (separate ownership
boundary). All code is **generic engine code** — no Epistemic-Humility / abstention /
confidence-domain vocabulary in the tuner (the tuner currently has zero such strings;
keep it that way). This handoff doc lives in the root research repo because it cites
the research that motivates the feature; the *feature itself* is domain-neutral.

---

## 0. TL;DR

Add a generic, optional, config-driven capability to synaptic-tuner: **train a small
scalar head that reads a chosen hidden-layer activation and is supervised by a
proper-scoring loss against a per-row target value, with the base model frozen, and
save that head as a portable artifact with a documented inference hook.**

- Generic feature name: **`aux_head`** (an *auxiliary scalar readout head*). Do **not**
  name it `confidence_head` or anything domain-specific in the tuner — "confidence" is
  merely the first configured use.
- Phase A = **base frozen, only the head trains.** Loss = `loss_fn(head(h_layer),
  target)` — there is **no** language-model loss term in Phase A.
- It must work for *any* `target_field` (a per-row float in `[0,1]` or a binary label)
  on *any* base — calibration, quality, toxicity, a routing gate, a value estimate.

### Why this is worth building (the motivating result — generic lesson)
Our research established that a model can carry a **calibrated internal signal that a
simple linear readout extracts almost perfectly, even though the model's own trained
output channels cannot express it.** Concretely, a linear probe on a mid-late residual
stream separated the target at AUROC ≈ 0.98–0.997 in-distribution *and* transferred
cold across datasets at 0.983 — while two different training regimes (RL on the output
token; SFT distillation into the output token) both failed to route that signal into
the model's emitted behavior. The generic takeaway for *any* fine-tuner: **if a signal
is linearly present in the hidden state, the cheapest robust way to expose it is a
trained readout head, not by trying to force it through the token channel.** This
feature ships that capability. (Our specific use: the target is an "is-this-answerable
/ how-confident-should-I-be" score; other users will have their own.)

---

## 1. Scope

**In scope (Phase A):**
1. A generic `AuxHead` `nn.Module` (linear by default; optional small MLP).
2. An optional config block `aux_head: {...}` (backward compatible — absent ⇒ feature off).
3. A training path that **freezes the base**, reads `hidden_states[layer]` at a
   configured token position, and trains the head with a proper-scoring loss against a
   per-row target carried through the data collator.
4. **Separate** save/load of the head artifact (the existing save paths will NOT
   persist it — see §3).
5. A documented **inference hook**: load base + head, produce the scalar per input.
6. A smoke test + a small validation that the head reproduces the offline probe's
   discrimination on real data.
7. Update the canonical `.skills/fine-tuning` skill and add the proper checked-in
   config/CLI surface (per submodule `AGENTS.md` — no throwaway scripts).

**Out of scope (do NOT build here):**
- Phase B joint multi-task (base + head co-trained, `LM_loss + weight·head_loss`).
  Keep it a flag flip (§9), but do not implement.
- GRPO integration. (GRPO reward closures only see decoded text and cannot read hidden
  states — the head belongs on the SFT/`compute_loss` path. A *trained* head's scalar
  could later feed GRPO as a reward term, but that is a separate future task.)
- Any Epistemic-specific data builder. The target column is supplied by the dataset;
  producing it is the *experiment's* job, not the engine's.

---

## 2. Generic feature spec

### 2.1 `AuxHead` module
- New module file under the SFT trainer's `src/` (e.g. `Trainers/sft/src/aux_head.py`)
  or `Trainers/shared/` if you want it cross-trainer. Generic only.
- `AuxHead(nn.Module)`:
  - `__init__(input_dim, head_type="linear", hidden_dims=(), out_activation="sigmoid")`.
  - `linear`: `nn.Linear(input_dim, 1)`. `mlp`: stacked `Linear+GELU` then `Linear(...,1)`.
  - `forward(h) -> scalar in [0,1]` (sigmoid). Keep it tiny and dtype/device-aware
    (cast the pulled hidden state to the head's dtype).
- **Default to `linear`.** The motivating result is that a *linear* readout suffices;
  start there, expose `mlp` for users who need it.

### 2.2 Config block (mirror the `EvolutionaryConfig` precedent)
Add `AuxHeadConfig` dataclass + an optional `aux_head` field on the SFT `Config`.
Generic fields:
```yaml
aux_head:
  enabled: false           # absent/false ⇒ feature fully off (backward compatible)
  layer: 35                # which hidden_states index to read (0=embeddings)
  token_position: last     # "last" (last non-pad token) | "mean" | int index
  target_field: target     # per-row column name in the dataset carrying the target
  loss: bce                # "bce" (binary/soft in [0,1]) | "brier" (MSE on prob)
  head_type: linear        # "linear" | "mlp"
  hidden_dims: []          # for mlp
  freeze_base: true        # Phase A = true. (Phase B flips this — see §9)
  lm_loss_weight: 0.0      # Phase A = 0.0 (no LM term). (Phase B > 0 — see §9)
  head_lr: null            # optional; default to the trainer LR if null
```
- **Critical gotcha:** `dict_to_dataclass` in the SFT config loader **silently drops
  unknown YAML keys**. The `aux_head` block is ignored unless the dataclass field
  exists. Add the dataclass + a dedicated `load_aux_head_config(...)` mirroring
  `load_evolutionary_config`.
- GRPO config is a plain dict (`config.get('aux_head', {})`) — but GRPO is out of scope
  here; do not wire it.

### 2.3 Trainer (subclass the stock `transformers.Trainer`)
The SFT path uses a **stock `transformers.Trainer`** (not TRL/Unsloth SFTTrainer), with
default causal-LM loss and **no** `compute_loss` override and **no** aux-loss hook.
Implement `AuxHeadTrainer(Trainer)`:
- Hold a reference to the `AuxHead` and the `AuxHeadConfig`.
- Override `compute_loss(model, inputs, return_outputs=False)`:
  1. Pop the per-row target tensor from `inputs` (added by the collator, §2.4).
  2. Forward: `outputs = model(**inputs, output_hidden_states=True)`. With
     `freeze_base=true`, base params have `requires_grad=False`, so only the head
     accumulates gradient. (You may wrap the base forward in `torch.no_grad()` and
     re-run only the head for memory, but the simple path — let autograd skip frozen
     params — is fine for an MVP and less error-prone.)
  3. Pull `h = outputs.hidden_states[layer]` and reduce over the sequence per
     `token_position` (`last` = index of last non-pad/attention-masked token per row;
     `mean` = masked mean; `int` = that index). Result shape `[batch, hidden]`.
  4. `pred = aux_head(h)` → `[batch]` in `[0,1]`.
  5. `loss = proper_score(pred, target)` (`bce` = `F.binary_cross_entropy`; `brier` =
     `F.mse_loss` on the probability). **Phase A: this is the entire loss.** (Phase B:
     `loss = outputs.loss + lm_loss_weight * head_loss`.)
  6. Ensure the optimizer is constructed over the **head's** parameters (and, Phase B,
     the LoRA params). With `freeze_base=true`, freeze base + LoRA so only the head
     trains; if `head_lr` is set, use a param group.
- **Freezing:** set `requires_grad=False` on all base/LoRA params when `freeze_base`;
  register the head so it is on the right device/dtype. Confirm the head's params are
  the only ones in the optimizer (log trainable-param count, mirror
  `model_loader.py` accounting).

### 2.4 Per-row target plumbing (mirror the subspan-mask precedent)
The subspan-loss-mask feature proves the **custom collator is the right place to carry
a per-row directive** into the batch. Do the same for the target:
- Read `target_field` per row during preprocessing/collation and stack it into a
  `aux_target` tensor in the batch (float). Keep rows without the field handled
  explicitly (skip in loss via a mask, or error if `enabled` and field missing — your
  call, but be loud, never silently substitute a default).
- The collator to extend is `collate_prepared_sft_batch`. Add `aux_target` (and an
  `aux_target_mask` if you allow missing values) to the returned batch dict; pop it in
  `compute_loss` before the model forward so it isn't passed to the LM.

### 2.5 Save / load (mirror the embedding `frozen_head` precedent)
Neither SFT save path (`trainer.save_model(...)`) persists an extra module. The
embedding trainer's `frozen_head` mode is the **only** existing precedent for appending
and separately saving a trained head — mirror its mechanics:
- After `trainer.train()`, save `aux_head.state_dict()` + the resolved `AuxHeadConfig`
  (layer, head_type, input_dim, token_position, loss, etc.) to a sidecar file in the
  run output dir (e.g. `aux_head.safetensors` + `aux_head_config.json`).
- Provide a `load_aux_head(run_dir, base_model) -> AuxHead` helper that reconstructs
  the module and loads weights. Keep it pure/generic.

### 2.6 Inference hook
Document and provide a minimal, generic way to use the head at inference:
- Given base model + loaded `AuxHead` + an input, run `model(..., output_hidden_states=
  True)`, reduce `hidden_states[layer]` at `token_position`, apply the head → scalar.
- A small helper function (and/or an eval-time integration point) is enough. Do NOT
  bake any decision policy (e.g. "answer iff scalar ≥ τ") into the engine — thresholds
  and how the scalar is *used* are the caller's/config's concern, not the tuner's.

---

## 3. Exact insertion points (architecture map — verified `file:line`)

All paths relative to `synaptic-tuner/` on branch `feature/sft-subspan-loss-mask`
(latest `278ddba`). Confirm anchors before editing — line numbers may drift.

| What | Where |
|---|---|
| Model load (Unsloth `FastLanguageModel.from_pretrained`) | `Trainers/sft/src/model_loader.py:65` |
| LoRA wrap (`get_peft_model`) | `Trainers/sft/src/model_loader.py:172` |
| Trainable-param accounting (mirror for head logging) | `Trainers/sft/src/model_loader.py:178` |
| **SFT Trainer construction** (`trainer = Trainer(**trainer_kwargs)`) — subclass here | `Trainers/sft/train_sft.py:1000` |
| Data collator def (`collate_prepared_sft_batch`) — add `aux_target` | `Trainers/sft/train_sft.py:231` |
| `data_collator` wired into trainer | `Trainers/sft/train_sft.py:998` |
| `trainer.train()` | `Trainers/sft/train_sft.py:1053` |
| `trainer.save_model(...)` (does NOT save the head) | `Trainers/sft/train_sft.py:1094` |
| Subspan label-mask precedent (per-row directive plumbing) | `Trainers/sft/src/preprocessing.py:88`; `shared/sft_preprocessing.py:241-270` |
| SFT config dataclasses / `Config` | `Trainers/sft/configs/config_loader.py:149` |
| `EvolutionaryConfig` + loader (template for `AuxHeadConfig`) | `Trainers/sft/configs/config_loader.py:135`, `:225` |
| `dict_to_dataclass` **silently drops unknown keys** (must add field!) | `Trainers/sft/configs/config_loader.py:202-203` |
| `load_config` | `Trainers/sft/configs/config_loader.py:265` |
| SFT per-trainer CLI `parse_args` (add any flag here, not in tuner/cli/parser.py) | `Trainers/sft/train_sft.py:357` |
| CLI override precedent (evolutionary flags) | `Trainers/sft/train_sft.py:651-688` |
| **Trainable-head precedent to mirror for save/load** (`frozen_head`) | `Trainers/embedding/src/model_loader.py:52,64,386,401` |

**Key facts that shape the design:**
- The model is a plain `nn.Module` (PEFT/Unsloth) — attaching a head is mechanically
  fine, but **persistence is on you** (save paths only serialize the adapter/base).
- No trainer requests `output_hidden_states=True` today; your `compute_loss` override
  is the place to enable it.
- There is **no** existing Brier/proper-scoring/confidence code in the submodule (the
  `amendment-j-grpo-v3-proper-scoring` work is a *root-repo* branch, not here). You are
  writing the first proper-scoring loss in the tuner — keep it generic.

---

## 4. Data contract

- The SFT training rows must carry a per-row target under `aux_head.target_field` (a
  float in `[0,1]`, or a 0/1 label). The engine reads it generically; **producing it is
  the experiment's responsibility.**
- Confirm the target column survives preprocessing into the collator. (`response_
  confidence`-style columns are NOT special-cased in the tuner's generic preprocessing,
  which is correct — treat the target as an arbitrary configured column.)
- Be loud if `enabled` and the column is missing/NaN. Never silently default it.

---

## 5. Submodule discipline (from `synaptic-tuner/AGENTS.md` — non-negotiable)

- **Config-first / format-agnostic.** This new trainer code is justified only because
  it is a *reusable runtime capability not expressible via existing config surfaces* —
  exactly the AGENTS.md exception. Everything tunable (layer, target_field, loss,
  head_type, token_position) lives in **config**, never hardcoded. Do not hardcode any
  dataset/example/field shape into the trainer.
- **Generic vocabulary only.** No `confidence`/`abstention`/`epistemic`/domain strings
  in tuner code, configs, or test names. `aux_head`, `target_field`, `aux_target`.
- **Skills are canonical.** Update `.skills/fine-tuning` with the new capability +
  checked-in config/CLI usage, then run
  `python3 .skills/scripts/sync_skill_trees.py` and verify with `--check`. No
  throwaway scripts — extend the proper CLI/config surface.
- **Don't import tuner internals upward / don't leak experiment orchestration down.**
  The feature is engine-only.

---

## 6. Build plan (ordered)

1. **Branch** the submodule: `git checkout -b feature/aux-scalar-head` (off
   `feature/sft-subspan-loss-mask` or `main` per maintainer preference — confirm).
2. `AuxHead` module (§2.1) + unit test (shapes, dtype, `[0,1]` range, linear & mlp).
3. `AuxHeadConfig` dataclass + loader + `Config` field (§2.2); test that an absent
   block ⇒ feature off and an unknown-key regression doesn't bite.
4. Extend collator to carry `aux_target` (§2.4); test batch shape.
5. `AuxHeadTrainer(Trainer)` with `compute_loss` override, freezing, optimizer over
   head params (§2.3).
6. Save/load sidecar (§2.5) + inference hook (§2.6).
7. Wire into `train_sft.py::run()` behind `aux_head.enabled` (construct head with
   `input_dim = model hidden size`, swap `Trainer` → `AuxHeadTrainer`). Feature off ⇒
   byte-identical to current behavior.
8. Smoke test + validation (§7).
9. Update `.skills/fine-tuning` + sync; add an example config under `configs/`.
10. PR in the submodule (generic title/body). The **root repo** bumps the submodule
    pointer in a *separate* commit only when an experiment recipe adopts the feature —
    keep that out of the submodule PR.

---

## 7. Testing & acceptance criteria

**Smoke (must pass):** tiny base (or a stub), a handful of rows with a `target` column,
`aux_head.enabled=true`, `freeze_base=true`:
- only the head's params are trainable (assert count);
- head loss **decreases** over a few steps;
- head saves, reloads, and the inference hook returns a per-row scalar in `[0,1]`;
- with `aux_head` absent/`enabled=false`, the SFT run is **byte-identical** to current
  behavior (no regression).

**Validation (the real bar):** on a dataset where an offline linear probe is known to
separate the target well, the trained frozen-base `aux_head` should **reproduce that
discrimination** (AUROC of head-scalar vs target close to the offline probe's). For our
first use, the offline reference is the probe-as-oracle readout (AUROC ≈ 0.98–0.997);
the head should land in the same neighborhood. A large gap ⇒ a bug in token-position
selection, layer indexing, dtype, or target plumbing.

**Acceptance:** all of the above green; generic boundary clean (grep for domain
strings = 0); skill updated + synced; example config provided; PR opened.

---

## 8. Reference: the offline readout the head must reproduce

The root repo has the analysis-script version of exactly this readout — use it as the
**oracle/ground-truth** to validate the head:
- `experiment/phase1/probe/probe_as_oracle_ceiling.py` — fits a CV logistic probe on a
  cached hidden-state extraction at a layer and reads out P(target) per row. The
  `aux_head` trained on the same (layer, target) should match its AUROC/ECE.
- `experiment/phase1/probe/probe_xdataset_transfer.py` — the cross-dataset transfer
  version (cold-applied probe). Confirms the readout is portable.
- These are CPU-only and operate on cached `h_base`/`h_lora` safetensors extractions —
  handy for offline validation without a GPU.

(These scripts are the *analysis* form; the `aux_head` is the *productized model
component* form. The point of the feature is to turn the script's readout into a saved,
inference-usable head — which is what makes it reusable for other fine-tuners.)

---

## 9. Phase B forward-compatibility (do NOT build — just don't preclude it)

Design so Phase B (joint multi-task) is a config flip, not a refactor:
- `freeze_base: false` ⇒ unfreeze LoRA; include LoRA params in the optimizer.
- `lm_loss_weight > 0` ⇒ `loss = outputs.loss + lm_loss_weight * head_loss`.
- Everything else (module, config, collator target, save/load, inference) is unchanged.
That's why `freeze_base` and `lm_loss_weight` are in the Phase-A config already, fixed
to the frozen/no-LM-term values. Leave a one-line note in the code where the LM term
would be added.

---

## 10. Open decisions (defaults chosen; builder may revisit with rationale)

| Decision | Default | Note |
|---|---|---|
| Feature name | `aux_head` | generic; confirmed (no domain name) |
| Head type | `linear` | motivating result: a linear readout suffices |
| Loss | `bce` | `brier` (MSE-on-prob) also offered; both proper scores |
| Token position | `last` (last non-pad) | the generation/decision position; expose `mean`/int |
| Layer | config-required (no silent default) | our use = 35; other users differ |
| Save format | `safetensors` + json sidecar | matches repo norms |
| Where module lives | `Trainers/sft/src/` | move to `Trainers/shared/` if cross-trainer reuse is wanted |

---

## 11. Pointers / provenance

- Motivating results (root repo): `experiment/protocol/AMENDMENT-O-probe-as-oracle-readout-ceiling.md`
  (in-distribution readout ceiling, all gates pass) and
  `experiment/protocol/AMENDMENT-P-xdataset-probe-transfer.md` (cold cross-dataset
  transfer at 0.983). These establish *why* a readout head is the right primitive.
- The correctness caveat (root repo memory): the readout targets **answerability**, not
  per-attempt correctness — out of scope for the engine, but worth knowing the target
  semantics are the *caller's* to define.
- Architecture map basis: the §3 anchors come from a full read of the SFT/GRPO/config/
  model-loader/embedding paths on `feature/sft-subspan-loss-mask`.

**First action for the builder:** read §2 + §3, re-confirm the `file:line` anchors,
branch the submodule, and start at build-plan step 2.
