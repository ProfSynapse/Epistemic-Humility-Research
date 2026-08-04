# Prepare: aux_head prompt/completion render seam (0029 token-faithfulness fix)

> **Scope.** RESEARCH ONLY (Task #64). Pin the exact preprocessing seam so CODE can
> wire the 0029 prompt/completion render mode with zero guesswork. No implementation,
> no code change. Verified against submodule main `e95dbde` (PR #119 merge) on branch
> `feature/aux-head-prompt-completion-render`. Spec: `docs/sessions/0029 - phase-b-token-faithfulness-fix-handoff.md`.
>
> The submodule is a **domain-agnostic engine**: every config/code/test NAME proposed
> below uses only generic vocabulary (`aux_head`, `prompt_render`, `prompt_completion`,
> `full_conversation`, `completion_ids`). The aux_head token code
> (`prompt_end_indices`, `reduce_hidden_states`) is CORRECT and is NOT touched.

## Executive summary

The render seam is a **single function**: `materialize_sft_example` in
`shared/sft_preprocessing.py:161-224`. Today it builds `input_ids` from a
**full-conversation** render (`apply_chat_template(messages, add_generation_prompt=False)`,
line 187-192) and then renders the prompt **with `add_generation_prompt=True`** (line
201-206) only to derive the `-100` prefix mask via a prefix-match that **breaks at the
first divergence** (line 209-213). That break is exactly the 0029 §0 root cause: the
two renders diverge around the assistant scaffold (Qwen3: one fewer newline), so the
masked boundary is not the generation anchor and the token the head reads is wrong
(cos 0.544).

**Q2 answer — no reusable prompt/completion render exists.** A `prompt_completion`
*input format* is recognized (`normalize_sft_messages`, `:127-158`), but it is
collapsed into one `messages` list and rendered full-conversation like everything
else — it is NOT a render that builds `input_ids` from `add_generation_prompt=True ++
completion`. So CODE must add a **new render branch**, but it can **reuse the existing
`add_generation_prompt=True` prompt render already present at `:201-206`** as the
prompt half (the building block is already there; only its role changes — from
mask-derivation to `input_ids` construction).

The new branch is small, local, and orthogonal to `aux_target` threading (which lives
one layer up and is untouched). Default (`full_conversation`) must stay byte-identical.

## Q2 — does a canonical prompt/completion tokenization path already exist?

| Candidate | Location | Renders prompt with `add_generation_prompt=True`? | Reusable as the render? |
|---|---|---|---|
| `normalize_sft_messages` `prompt_completion` format | `shared/sft_preprocessing.py:127-158` (returns `example_format="prompt_completion"` at `:158`) | No — converts `prompt`+`completion` into one `messages` list, then `materialize_sft_example` renders it full-conversation | **No** — this is an *input-shape* tag, not a render mode |
| `materialize_sft_example` mask-derivation render | `shared/sft_preprocessing.py:201-206` | **Yes** — `apply_chat_template(messages[:-1], add_generation_prompt=True, **template_kwargs)` | **Partially** — exactly the prompt half the new branch needs; currently used only to compute `mask_len` (`:207-213`) |
| `data_loader.py` `apply_chat_template` text path | `Trainers/sft/src/data_loader.py:98-112` (`add_generation_prompt=False`, `:112`) | No | No — full-conversation `text` materialization |
| `render_chat_text` | `Trainers/sft/src/preprocessing.py:35-46` (`add_generation_prompt=False`, `:45`) | No | No — debug/decode helper |

**Conclusion:** reuse is NOT available as a turnkey path (handoff §2.1's preferred
route does not exist), but the *prompt-render call itself* (`:201-206`) is already
written and should be reused inside the new branch. Recommend: **build a new
render-mode branch in `materialize_sft_example`** (decision deferred to ARCHITECT per
the dispatch; both the reuse-search result and the new-branch insertion point are
pinned here).

## Q3 — exact insertion points

### (a) The render-mode branch — `shared/sft_preprocessing.py:161-224`

The single seam. `materialize_sft_example` currently:
- `:187-192` `full_str = apply_chat_template(messages, add_generation_prompt=False, **template_kwargs)`
- `:193-197` encode → `input_ids`, `attention_mask=[1]*len`, `labels=list(input_ids)`
- `:200-214` if `assistant_only_loss` and last role == assistant: render prompt
  `add_generation_prompt=True` (`:201-206`), encode, mask the matching **prefix** to
  `-100` (`:209-213`, breaks on first mismatch), set `loss_mask_mode="assistant_only"`

**New `prompt_completion` branch** (per 0029 §1) — gate at the top of the
`assistant_only` path (or as a sibling render mode), building:
- `prompt_ids   = encode( apply_chat_template(messages[:-1], add_generation_prompt=True, **template_kwargs) )` — reuse `:201-206`
- `completion_ids = encode(real completion text) + [terminal]` — real completion is
  `messages[-1]` (assistant content); terminal token per Q5
- `input_ids = prompt_ids ++ completion_ids`
- `labels = [-100]*len(prompt_ids) ++ completion_ids`
- `attention_mask = [1]*len(input_ids)`; apply the same `max_seq_length` truncation
  contract as `:194-195`

This makes `prompt_end_indices` (`Trainers/sft/src/aux_head.py:157-184`, boundary =
`(labels != -100).argmax - 1`) return `len(prompt_ids)-1` exactly — **no aux_head
change** (confirmed: `aux_head.py:183-184`). The `**template_kwargs`
(`enable_thinking`, etc.) MUST be forwarded in both renders to stay faithful.

`materialize_sft_example` needs a new param (e.g. `prompt_render: str =
"full_conversation"`); default preserves the current path byte-identically.

### (b) The config flag — `Trainers/sft/configs/config_loader.py`

- `AuxHeadConfig` dataclass: `:150`; current last field `input_norm` at `:169`. Add a
  new field here (e.g. `prompt_render: str = "full_conversation"`).
- `load_aux_head_config`: `:289`; field reads at `:347-356` (e.g. `input_norm` read at
  `:356`). Add `prompt_render=aux_data.get('prompt_render', 'full_conversation')`
  alongside. **Critical gotcha (carried from Phase A/B):** `dict_to_dataclass` silently
  drops unknown keys — a new field MUST be added to the dataclass or it is ignored.
- **Placement decision for ARCHITECT:** the handoff allows `aux_head.prompt_render`
  OR a top-level preprocessing option. Note `completion_only_loss` already lives on
  the **training** config (`config_loader.py:67`, `TrainingConfig`), and the render
  mode changes `input_ids`/`labels` for the whole row (it is preprocessing-wide, not
  aux_head-internal). Recommendation: `aux_head.prompt_render` matches the handoff
  example and keeps the faithfulness knob with the feature that needs it, but the
  flag must then thread from `aux_head_cfg` down into the shared preprocessing (Q3
  thread below). ARCHITECT picks; both anchors are pinned.

### (c) `aux_target` threading — ORTHOGONAL, must stay

`aux_target` is read at the **`prepare_sft_dataset._materialize`** level
(`Trainers/sft/src/preprocessing.py:104-105`, via `_read_aux_target` `:115-137`),
NOT inside `materialize_sft_example`. The render branch lives strictly inside
`materialize_sft_example`, so the `aux_target` read is **undisturbed** — no change
needed, but CODE must not relocate the render in a way that bypasses
`prepare_sft_dataset` (`:72-112`), which is what carries `aux_target` past the
`remove_columns` drop (`:108-112`).

### (d) The §2.5 joint-grad test to extend — `tests/trainers/sft/test_aux_head_integration.py`

The head-path-isolation test ALREADY exists (built in Phase B per the 0028 §2.5
ruling): `test_gradient_flows_into_base_from_head_alone_under_checkpointing` at
**`:301-333`** — `freeze_base=False`, `lm_loss_weight=0`, gradient checkpointing
FORCED ON (`:312`), asserts a pre-read base param grad is non-zero (`:328`) and the
head param grad is non-zero (`:332-333`). The joint-loss-sum test is at `:240-258`
and the param-group/update test at `:287+`. The harness is `_make_trainer`
(`:102-136`) + the local collator (`:90-99`).

**Extension (acceptance §3.4):** add a `prompt_render` param to `_make_trainer`
(`:102-111`) and a `prompt_completion` variant of the joint step that builds rows
through the new render, asserting (i) `prompt_end_indices == len(prompt)-1` on the
rendered labels, (ii) head + LoRA grads non-zero under the new mode (reuse the
forced-GC isolation shape at `:301-333`). Rows are hand-built tensors in this file
(no unsloth import), so the render fixture can call `materialize_sft_example`
directly.

## Q4 — existing full-conversation tests that must stay byte-identical (default flag)

These exercise the current render/contract and must pass unchanged under
`prompt_render="full_conversation"` (the default):

- `tests/trainers/sft/test_preprocessing_contract.py` — the canonical
  `materialize_sft_example` / `prepare_sft_dataset` contract (highest-value guard).
- `tests/trainers/sft/test_aux_head_preprocessing.py` — aux_head two-hop
  `aux_target` threading + `-100` masking on full-conversation rows.
- `tests/trainers/sft/test_chat_template_kwargs_passthrough.py` — `**template_kwargs`
  forwarding through the render (the new branch must keep this green by forwarding
  `template_kwargs` in BOTH the prompt and completion encodes).
- `tests/trainers/sft/test_data_loader.py` — the `add_generation_prompt=False` text
  path (unaffected; confirms the render-mode change is scoped to aux_head preprocessing).

## Q5 — terminal-token convention (im_end vs eos)

The existing preprocessing appends **no explicit terminal token** — the assistant
turn's closing token is emitted by `apply_chat_template` itself (no `im_end`/`eos`
literal anywhere in `shared/sft_preprocessing.py` or `Trainers/sft/src/preprocessing.py`).
The only `eos` reference in the SFT path is the collator **pad** fallback
(`Trainers/sft/train_sft.py:236`, `pad_token_id = getattr(tokenizer, "eos_token_id", 0)`),
which is padding, not the completion terminal.

For this **Qwen3 lineage** the assistant-turn terminal is **`<|im_end|>`** — confirmed
by the research-side prototype (`experiment/phase1/probe/amendment_r_phase_b_promptcompletion_proto.py`,
`build_prompt_completion_rows`: `im_end = tok.convert_tokens_to_ids("<|im_end|>")`,
`comp_ids = tok.encode(text, add_special_tokens=False) + [im_end]`), and 0029 §1
(`completion_ids = encode(completion_text) + [eos/im_end]`).

**Recommendation (generic-engine):** do not hardcode `<|im_end|>`. Derive the terminal
the model's template uses — preferably by rendering the assistant turn via the chat
template (so `completion_ids` terminate exactly as the full-conversation render would),
or fall back to `tokenizer.eos_token_id`. This keeps the engine model-agnostic while
matching this lineage's `<|im_end|>`. ARCHITECT/CODE choose the exact mechanism; the
constraint is that every completion token **including** the terminal carries a real
label (acceptance §3.3).

## The full threading map (config flag → render branch)

If the flag lives on `AuxHeadConfig`, it threads:

1. `Trainers/sft/configs/config_loader.py` — field on `AuxHeadConfig` (`:150`/`:169`) +
   read in `load_aux_head_config` (`:347-356`).
2. `Trainers/sft/train_sft.py` — `aux_head_cfg` read at `:826-828`; the dataset-prep
   call `load_and_prepare_sft_dataset(...)` at `:836-844` (passes `loss_mask_mode`
   `:842`, `chat_template_kwargs` `:843`, `aux_target_field` `:844`). Add
   `prompt_render=aux_head_cfg.prompt_render` here (default `full_conversation` when
   aux_head disabled).
3. `Trainers/sft/src/preprocessing.py` — `load_and_prepare_sft_dataset` (`:140-160`)
   → `prepare_sft_dataset` (`:72-112`) → `materialize_sft_features` (`:49-69`) — add a
   `prompt_render` param threaded through each (default `full_conversation`).
4. `shared/sft_preprocessing.py` — `materialize_sft_example` (`:161-224`) consumes it
   and selects the render branch (Q3a).

Every hop defaults to `full_conversation` so all non-aux and Phase-A/B callers are
byte-identical.

## Risk register

| Risk | Prob. | Impact | Mitigation |
|---|---|---|---|
| New branch changes default-path tokenization (breaks byte-identical) | Low | High | Gate strictly behind `prompt_render != "full_conversation"`; Q4 contract tests guard it |
| Completion terminal hardcoded to `<|im_end|>` → non-Qwen models mis-terminate | Med | Med | Derive terminal from template/`eos_token_id` (Q5), don't hardcode |
| `template_kwargs` (`enable_thinking`) not forwarded in the new encodes → render drifts from full-conv terminal | Med | Med | Forward `**template_kwargs` in BOTH prompt and completion encodes; `test_chat_template_kwargs_passthrough.py` guards |
| Flag placed on aux_head but render is preprocessing-wide → layering confusion | Low | Low | ARCHITECT decision; thread map pins both options |
| Truncation (`max_seq_length`) applied inconsistently between branches | Low | Med | Mirror `:194-195` truncation contract in the new branch; add a truncation assertion |

## Sources / provenance

- Submodule main `e95dbde` (PR #119), branch `feature/aux-head-prompt-completion-render`.
  Files read directly: `shared/sft_preprocessing.py`, `Trainers/sft/src/preprocessing.py`,
  `Trainers/sft/src/data_loader.py`, `Trainers/sft/configs/config_loader.py`,
  `Trainers/sft/train_sft.py`, `Trainers/sft/src/aux_head.py`,
  `tests/trainers/sft/test_aux_head_integration.py`.
- KG-search-first (`bin/search`, project rule) surfaced the research-side prototype
  `experiment/phase1/probe/amendment_r_phase_b_promptcompletion_proto.py`
  (`build_prompt_completion_rows`) — authoritative for the `<|im_end|>` terminal and
  the reference render; then scoped `rg` over the submodule SFT path.
- Spec: `docs/sessions/0029 - phase-b-token-faithfulness-fix-handoff.md` (root cause §0,
  verified fix §1, build items §2, acceptance §3). Anchors cross-checked against
  `docs/sessions/0028 - phase-b-joint-aux-head-engine-build-handoff.md` §1.

## Caveats

- Line numbers are at `e95dbde`; CODE should re-confirm after any rebase.
- This note pins seams and recommends; it makes no build/no-build call and signs off
  no protocol. ARCHITECT owns the placement decision (flag home, terminal mechanism);
  CODE owns the edits and the live faithfulness re-check (the 0029 prototype already
  verified faithfulness at cos 0.9998, n=400).
