---
schema_version: research-session/v1
session_id: 20260629T000000Z-phase-b-token-faithfulness-fix-handoff
title: "Phase B token-faithfulness fix \u2014 prompt/completion render mode (engine\
  \ handoff)"
status: complete
created_at: '2026-06-29T00:00:00Z'
updated_at: '2026-06-29T00:00:00Z'
phase: phase3
question: 'The Phase B aux_head engine landed (PR #119), but end_of_prompt on full-conversation
  SFT rows does not reproduce the validated answerability axis. What generic preprocessing
  change makes it faithful?'
tags:
- aux_head
- phase-b
- synaptic-tuner
- engine
- preprocessing
- faithfulness
- handoff
run_ids: []
trajectory:
  anchor: docs/research-trajectory.md
  current_position: Phase B engine works, but the head reads the wrong token on full-conversation
    rows. A verified prompt/completion render mode restores faithfulness (cos 0.9998);
    this handoff specs it.
  changed_by_session: false
checkpoints: []
legacy_session:
  id: 0029
  path: docs/sessions/0029 - phase-b-token-faithfulness-fix-handoff.md
---
# Phase B Token-Faithfulness Fix — Engine Handoff (follow-up to 0028)

> **Generic, reusable `synaptic-tuner` engine work. No project vocabulary** in code,
> config, docstrings, or tests. The change is a preprocessing **render mode**; the
> aux_head token-position code (`prompt_end_indices`, `reduce_hidden_states`) is
> already CORRECT and must not change.

## 0. What happened

PR #119 (handoff 0028) shipped Phase B, including `token_position="end_of_prompt"`,
which recovers the prompt/completion boundary from the labels `-100` mask. A
downstream pre-flight smoke then found that on **full-conversation** SFT rows
`end_of_prompt` reads a representation that does **not** match the intended
generation-anchor token:

| read position | reproduces the reference axis? |
|---|---|
| reference (the generation-prompt token) | yes — cos **0.9998** |
| engine `end_of_prompt` on a full-conversation row | **no — cos 0.544** |
| `end_of_prompt +- small offsets` | no — best 0.91, none >= 0.95 |

**Root cause (generic).** The model's chat template renders an assistant turn
differently in the two modes:
- `apply_chat_template(..., add_generation_prompt=True)` ends the prompt with the full
  generation scaffold (for this Qwen3 lineage: `...</think>\n\n`).
- `apply_chat_template(messages_including_assistant, add_generation_prompt=False)` (what
  the current full-conversation preprocessing uses) renders the same scaffold
  differently (`...</think>\n{content}` — one fewer newline) before the completion.

So on a full-conversation row the boundary token is NOT the generation-anchor token,
and because the content tokens diverge structurally, no integer offset recovers it.
This will affect **any** template whose assistant-turn render differs from its
generation-prompt render around the header/scaffold — it is not Qwen-specific.

## 1. The fix (verified)

Tokenize aux_head rows **prompt/completion-style** instead of full-conversation:

```
prompt_ids     = encode( apply_chat_template(prompt_messages, add_generation_prompt=True) )
completion_ids = encode( completion_text ) + [eos/im_end]      # the real target text
input_ids      = prompt_ids ++ completion_ids
labels         = [-100] * len(prompt_ids) ++ completion_ids    # assistant-only
attention_mask = [1] * len(input_ids)
```

The prompt segment now ends exactly at the generation-anchor token, so the engine's
**existing** `prompt_end_indices` returns `len(prompt_ids) - 1` and
`reduce_hidden_states(token_position="end_of_prompt", prompt_end_idx=...)` reads the
faithful token. **No aux_head code change.**

**Empirical confirmation** (research-side prototype
`experiment/phase1/probe/amendment_r_phase_b_promptcompletion_proto.py`, n=400, L35,
merged Qwen3-4B grpo-v2): boundary == last prompt token **400/400 rows**; end_of_prompt
**CV AUROC 0.9380** vs cached 0.9389; **cos 0.9998**, mse 0.04. The full-conversation
render gave cos 0.544 / AUROC 0.85 on the same rows.

## 2. Build items

1. **Prompt/completion render mode in preprocessing.** Add a render path that builds
   `input_ids`/`labels`/`attention_mask` as in §1 (prompt via
   `add_generation_prompt=True`, completion appended, prompt masked to `-100`). Many
   SFT stacks already support a prompt/completion dataset format — prefer wiring the
   canonical preprocessing's existing prompt/completion path over inventing a new one;
   confirm it renders the prompt with `add_generation_prompt=True`.
2. **Config selector.** Gate it behind a generic flag, e.g.
   `aux_head.prompt_render = "full_conversation" (default) | "prompt_completion"`, or a
   top-level preprocessing option if that fits the existing config shape better. Default
   MUST preserve current behavior (Phase A and all existing users unchanged).
3. **Keep aux_head token code untouched.** `prompt_end_indices` and
   `reduce_hidden_states` are correct; this is purely about which tokens/labels the
   preprocessing emits.
4. **Real completion, not a placeholder.** The mode must carry the row's real
   completion text through to `completion_ids` (the LM loss trains on it during joint
   Phase B). The §1 prototype used a fixed completion only to isolate the read position.

## 3. Acceptance criteria (CPU)

1. **Faithful boundary:** for a model whose template diverges between the two render
   modes, prompt/completion tokenization yields `prompt_end_indices == len(prompt)-1`,
   and the reduced `end_of_prompt` vector equals the prompt-only
   `add_generation_prompt=True` last-token vector (cos ~ 1.0 in a tiny forward).
2. **Backward-compat:** `prompt_render="full_conversation"` (default) is byte-identical
   to current preprocessing; all existing aux_head + SFT tests pass unchanged.
3. **Masking:** every prompt token is `-100`; every completion token (incl. the
   terminal `<|im_end|>`/eos) carries a real label; `aux_target` still threads through.
4. **Joint path intact:** a tiny joint step (`freeze_base=false`, `lm_loss_weight>0`)
   under the new render mode runs and produces head + LoRA gradients (extend the §2.5
   test from 0028).

## 4. Handback

A synaptic-tuner PR adding the prompt/completion render mode + the §3 tests. The
research repo then re-runs the pre-flight smoke (faithfulness already verified) plus the
joint-loss-runs + baseline parts, locks the Amendment R falsifier threshold, and seeks
sign-off for the scored A0/A1/A2 run. Consumed by `AMENDMENT-R` §6/§7.
