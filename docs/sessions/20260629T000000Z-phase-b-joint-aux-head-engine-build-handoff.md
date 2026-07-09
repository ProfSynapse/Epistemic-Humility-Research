---
schema_version: research-session/v1
session_id: 20260629T000000Z-phase-b-joint-aux-head-engine-build-handoff
title: "Phase B joint aux_head co-training \u2014 engine build handoff"
status: complete
created_at: '2026-06-29T00:00:00Z'
updated_at: '2026-06-29T00:00:00Z'
phase: phase3
question: What generic synaptic-tuner engine features must land so the aux_head can
  be co-trained jointly with the LM loss over an unfrozen base (Phase B), faithfully
  reading the answerability axis Amendment Q validated?
tags:
- aux_head
- phase-b
- joint-training
- synaptic-tuner
- engine
- handoff
run_ids: []
trajectory:
  anchor: docs/research-trajectory.md
  current_position: "O/P/Q proved the answerability signal is latent and readable\
    \ by a bolted-on head (transfer AUROC 0.983). Phase B tests whether co-training\
    \ the head INTO the base changes the model's own behavior \u2014 gated on the\
    \ engine build specced here."
  changed_by_session: false
checkpoints: []
legacy_session:
  id: 0028
  path: docs/sessions/0028 - phase-b-joint-aux-head-engine-build-handoff.md
---
# Phase B Engine Build — Handoff for the Builder

> **You are building generic, reusable `aux_head` engine features in the
> `synaptic-tuner` submodule.** This is a domain-agnostic training engine: use NO
> project-specific vocabulary (no "epistemic", "answerability", "abstention", etc.)
> in code, config, docstrings, or tests. The head reads a hidden layer and is
> supervised by a proper-scoring loss against a per-row target — that is the entire
> abstraction. Everything below is phrased generically on purpose; keep it that way.

## 0. Context (read once, then work from §2 onward)

Phase A (PR #118, merged) shipped the `aux_head`: a small scalar readout head over a
**frozen** base, trained head-only by a proper-scoring loss (`freeze_base=true`,
`lm_loss_weight=0`). It works and is well-tested.

A downstream experiment (Amendment Q) used the Phase-A head and surfaced two facts the
Phase-B build must address, plus confirmed the joint path is unimplemented:

1. The **joint-loss path is stubbed**. `Trainers/sft/src/aux_head_trainer.py:186`
   reads literally `# Phase B seam (do NOT enable here): loss = outputs.loss + cfg.lm_loss_weight * head_loss`.
   The config knobs (`lm_loss_weight`, `freeze_base`) exist and are parsed, but the
   loss combination, the unfrozen-base optimizer, and the unfreezing are not wired.
2. **Token position matters and isn't first-class.** The signal the head should read
   lives at the **final prompt token** (the position right before generation). On a
   prompt+completion training row, `token_position="last"` reads the **last completion
   token** (post-answer) — the wrong representation. Measured gap: reading the correct
   token gives a cosine of 0.9998 to the reference vector; the end-of-user/last token
   gives 0.54. The engine needs an explicit **end-of-prompt** token position.
3. **The raw-input head is LR-sensitive and saturates.** On unnormalized hidden states
   the linear head saturates at the example config's LR band (lr=1e-2 → degenerate;
   default lr=1e-3 likely also too high). It trains cleanly only at ~lr=1e-5 or with
   input standardization. The engine should offer an optional **input normalization**
   so the head trains at a normal LR.

Deliver §2's five items. **Hard constraint:** the existing Phase-A path
(`aux_head` absent/`enabled=false`, or `freeze_base=true`+`lm_loss_weight=0`) must
remain **byte-identical** — all current `aux_head` tests stay green unchanged.

## 1. Files in play (verified anchors @ submodule main, the aux_head feature)

| File | What |
|---|---|
| `Trainers/sft/src/aux_head.py` | `AuxHead` module (`__init__` :66-98, `forward` :105-110), `reduce_hidden_states` :137-181, `save_aux_head` :209-243, `load_aux_head` :245-283, `infer_aux_scalar` :287+ |
| `Trainers/sft/src/aux_head_trainer.py` | `AuxHeadTrainer`: base-freeze `__init__` :76-77 / `_freeze_base_keep_head` :106-131, `create_optimizer` :133-152, `compute_loss` :154-188 (the stubbed seam :186) |
| `Trainers/sft/configs/config_loader.py` | `AuxHeadConfig` dataclass :160-168; `dict_to_dataclass` **silently drops unknown keys** — any new field MUST be added to the dataclass |
| `Trainers/sft/configs/aux_head_example.yaml` | the Phase-A example; add a Phase-B example (see §3) |
| `Trainers/sft/train_sft.py` | wiring: aux config read :824-844, trainer swap-in :1011-1032, sidecar save :1132-1145 (should need no change if the module/trainer APIs stay compatible) |
| `tests/trainers/sft/test_aux_head*.py` | five test files (module/loss/config/preprocessing/integration) — extend, don't regress |

## 2. The build (five items)

### 2.1 Joint loss (`aux_head_trainer.py` `compute_loss` :154-188)
Replace the stub at :186 with a guarded combination:

- The base forward already runs with `output_hidden_states=True` and `inputs` still
  carries `labels`, so `outputs.loss` (the LM CE) is already computed.
- When `cfg.lm_loss_weight > 0`: `loss = outputs.loss + cfg.lm_loss_weight * head_loss`.
- When `cfg.lm_loss_weight == 0`: `loss = head_loss` (unchanged — Phase A byte-identical).
- Keep the `aux_target` pop (it must never enter the LM forward).

### 2.2 Unfrozen-base path (`__init__` :76-77, `_freeze_base_keep_head` :106-131, `create_optimizer` :133-152)
- `__init__`: when `freeze_base=false`, do **not** freeze the base — leave the PEFT
  adapter params' `requires_grad` as PEFT set them (LoRA params trainable). Still
  ensure the head's params are trainable. Keep calling `_freeze_base_keep_head()` only
  when `freeze_base=true`.
- `create_optimizer`: when `freeze_base=false`, add the base's **trainable** params
  (the LoRA params: `[p for p in self.model.parameters() if p.requires_grad]`) as a
  second param group at the trainer LR, alongside the head group (which may keep its
  optional `head_lr`). When `freeze_base=true`, behavior is unchanged (head-only).

### 2.3 End-of-prompt token position (`reduce_hidden_states` :137-181 + `compute_loss`)
Add `token_position="end_of_prompt"`:
- **Training:** the prompt/completion boundary is recoverable from `labels` (the
  preprocessing masks prompt tokens to `-100`, completion tokens carry real ids).
  Per row, the last prompt token index = `(labels != -100).float().argmax(dim=1) - 1`
  (clamp ≥ 0). Compute this in `compute_loss` (it has `inputs["labels"]`) and gather
  `hidden[arange, idx]`. Cleanest: extend `reduce_hidden_states` to accept an optional
  `prompt_end_idx` tensor and add an `"end_of_prompt"` branch that uses it.
- **Inference** (`infer_aux_scalar`): the input is prompt-only (with the generation
  prompt), so end-of-prompt == last real token. When `token_position="end_of_prompt"`
  and no labels/`prompt_end_idx` are available, fall back to the `"last"` reduction.
  Document this equivalence in the docstring.
- Validate independently: with `end_of_prompt`, a row whose completion is empty must
  reduce to the same vector as `"last"`.

### 2.4 Optional input normalization (`AuxHead.__init__` :66-98, `forward` :105-110)
- Add a constructor arg `input_norm: str = "none"` (`"none"` | `"layernorm"`). When
  `"layernorm"`, build `self.input_norm = nn.LayerNorm(input_dim)` and apply it in
  `forward` (after the dtype cast, before `self.net`). `"none"` → identity (Phase A
  byte-identical; default).
- **Portability is mandatory:** persist `input_norm` in `save_aux_head`'s resolved
  config dict (:209-243) and reconstruct it in `load_aux_head` (:245-283). A head
  saved with a LayerNorm must reload and infer identically — extend the save/reload
  roundtrip test.

### 2.5 Gradient-flow gotcha (verify, don't assume)
`output_hidden_states=True` + gradient checkpointing + LoRA co-training is fragile:
checkpointing recomputes activations and can detach the hidden state the head reads,
and LoRA needs grads to reach the adapter. After 2.1–2.2, **assert in a test** that a
single joint step (`freeze_base=false`, `lm_loss_weight>0`) produces non-zero grads on
**both** a head param **and** a LoRA param. If checkpointing breaks it, the standard
fix is `model.enable_input_require_grads()` and/or `use_cache=False`; document whatever
is needed.

## 3. Config (`config_loader.py` + example)
- Add `input_norm: str = "none"` to `AuxHeadConfig` (:160-168). (`lm_loss_weight`,
  `freeze_base`, `head_lr`, `token_position` already exist.)
- Add `Trainers/sft/configs/aux_head_phase_b_example.yaml`: a copy of the Phase-A
  example with `freeze_base: false`, `lm_loss_weight: 1.0`, `token_position: end_of_prompt`,
  `input_norm: layernorm`, and a sane base LR (e.g. 1e-4) with `head_lr` optional.
  Keep all placeholders/comments generic (no domain words).

## 4. Acceptance criteria (all must pass; CPU, no real GPU)
1. **Backward-compat:** every existing `aux_head` test passes unchanged; a Phase-A
   config (`enabled=true, freeze_base=true, lm_loss_weight=0, input_norm=none`) yields
   byte-identical loss/behavior to current `main`.
2. **Joint loss:** with `lm_loss_weight>0`, `compute_loss` returns
   `outputs.loss + λ*head_loss` (unit test on a tiny `LlamaForCausalLM`, asserting the
   exact sum).
3. **Unfrozen base:** with `freeze_base=false`, the optimizer's param groups include
   LoRA params, and one joint `Trainer.train()` step updates **both** a LoRA weight and
   a head weight (extend `test_aux_head_integration.py`).
4. **End-of-prompt:** `reduce_hidden_states(..., "end_of_prompt", prompt_end_idx=...)`
   selects the labels-boundary token on a hand-built mask; the empty-completion case
   equals `"last"`; inference falls back to `"last"` cleanly.
5. **Input norm:** `AuxHead(input_norm="layernorm")` has a LayerNorm, does not saturate
   on large-magnitude inputs, and survives a `save_aux_head`→`load_aux_head` roundtrip
   bit-for-bit.
6. **Gradient flow:** the §2.5 assertion test passes.

## 5. Offline validation hook (optional but recommended)
The downstream experiment's faithfulness check lives in the research repo at
`experiment/phase1/probe/amendment_q_faithfulness_smoke.py` (reads a hidden layer at a
token position and checks a linear readout AUROC). It is NOT part of the engine and
must not be imported by engine code, but the builder may use it (or its logic) to
sanity-check that the new `end_of_prompt` reduction reproduces the reference
representation before handing back.

## 6. Out of scope (do NOT build here)
- Any experiment data, targets, recipes, or run orchestration (research-repo side).
- Any domain-specific behavior, metric, or naming.
- Multi-head / multi-target support, schedulers for λ — keep λ a fixed scalar.

## 7. Handback
A PR to `synaptic-tuner` with §2's five items, §3's config, §4's tests green, and a
short note documenting the §2.5 gradient-flow resolution. The research repo will then
bump the submodule pointer, finalize Amendment R's falsifier, and run A0/A1/A2.
