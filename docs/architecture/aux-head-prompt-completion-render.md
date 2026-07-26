# Architecture: aux_head prompt/completion render mode (0029 token-faithfulness fix)

> **Scope.** ARCHITECT phase for the 0029 Phase B token-faithfulness fix. Resolves the
> two layering decisions PREPARE deliberately left open and specifies a zero-ambiguity
> CODE contract. Design/interface level only — **no code edits**. Verified against the
> submodule at `feature/aux-head-prompt-completion-render` HEAD `e95dbde` (PR #119
> merge). Inputs: `docs/sessions/0029 - phase-b-token-faithfulness-fix-handoff.md`
> (spec), `docs/preparation/aux-head-prompt-completion-render.md` (seam doc, #64).
>
> **Generic-engine discipline (NON-NEGOTIABLE).** The submodule is a domain-agnostic
> training engine. Every proposed name uses only generic vocabulary: `prompt_render`,
> `prompt_completion`, `full_conversation`, `completion_ids`, `aux_head`. Zero project
> vocabulary in any code/config/test name.

## Executive summary

The fix is a **preprocessing render mode**: tokenize aux_head rows prompt/completion-style
(`prompt_ids` from `add_generation_prompt=True` ++ `completion_ids` = real completion +
terminal, prompt masked to `-100`) instead of the current full-conversation render whose
prefix-match boundary is the 0029 root cause (cos 0.544 vs the verified 0.9998). The
aux_head token code (`prompt_end_indices`, `reduce_hidden_states`) is **correct and
untouched** — under prompt/completion labels `prompt_end_indices` already returns
`len(prompt_ids) - 1`.

**Two decisions, resolved:**

- **DECISION 1 (flag home) → `prompt_render` on `SFTTrainingConfig`** (`config.training.prompt_render`,
  default `"full_conversation"`). NOT on `AuxHeadConfig`. The render mutates whole-row
  `input_ids`/`labels` — it is a preprocessing-wide masking/render strategy in the same
  *kind* as `completion_only_loss` / `assistant_only_loss` / `chat_template_kwargs` (all
  already on `SFTTrainingConfig`), and it governs the **same code region** (`sft_preprocessing.py:200-214`)
  that `assistant_only_loss` governs. This **overturns my teachback lean** (`aux_head.prompt_render`),
  for the reason teachback is meant to surface — see §D1.

- **DECISION 2 (terminal token) → append a DERIVED `tokenizer.eos_token_id`** (never a
  hardcoded `<|im_end|>` literal), guarded loud if `None`, with the terminal carried as a
  real (non-`-100`) label and a faithfulness-pin test. Re-rendering the assistant turn to
  derive the terminal is **rejected** — it reintroduces the exact full-conversation
  scaffold render that *is* the 0029 root cause. See §D2.

Both decisions plus the `enable_thinking`/`chat_template_kwargs` forwarding invariant
(§ENABLE-THINKING, the real risk the lead flagged, connected to project issue #47) and a
recommended cross-config coherence guard (§GUARD) form the contract in §CONTRACT.

## Root cause (recap, generic)

`materialize_sft_example` (`shared/sft_preprocessing.py:161-224`) builds `input_ids` from a
**full-conversation** render (`apply_chat_template(messages, add_generation_prompt=False)`,
`:187-192`), then renders the prompt with `add_generation_prompt=True` (`:201-206`) only to
derive the `-100` prefix mask via a prefix-match that **breaks at first divergence**
(`:209-213`). The two renders diverge around the assistant scaffold (Qwen3: one fewer
newline, `...</think>\n\n` vs `...</think>\n{content}`), so the masked boundary is not the
generation anchor and the token the head reads is wrong. This afflicts **any** template
whose assistant-turn render differs from its generation-prompt render — not Qwen-specific.

---

## DECISION 1 — flag home: `SFTTrainingConfig.prompt_render`

### Options

| | A: `aux_head.prompt_render` (my teachback lean; handoff example) | B: `training.prompt_render` on `SFTTrainingConfig` (CHOSEN) |
|---|---|---|
| Field home | `AuxHeadConfig` (`config_loader.py:150-169`) | `SFTTrainingConfig` (`config_loader.py:56-87`, beside `assistant_only_loss:68`) |
| Value source (train_sft.py) | `aux_head_cfg.prompt_render if aux_head_enabled else "full_conversation"` | `config.training.prompt_render` |
| Threads through | `load_and_prepare_*` → `materialize_sft_example` | **the same** `load_and_prepare_*` → `materialize_sft_example` |
| Owns a preprocessing-wide row mutation? | No (a feature sub-config owns a whole-row tokenization change) | Yes (preprocessing config owns a preprocessing concern) |
| Co-located with the masking it modifies (`assistant_only_loss`)? | No — split across two configs | Yes — same config |

### Why the "4-hop thread" is NOT the discriminator (correcting my teachback)

My teachback flagged the 4-hop config→`materialize_sft_example` thread as a cost of Option
A. On reading the wiring, **both options thread the identical chain** — the value must
reach `materialize_sft_example` regardless of which dataclass holds it; only the one-line
read at the top of `train_sft.py` differs. The existing chain already carries three
preprocessing knobs the same way: `loss_mask_mode` (from `assistant_only_loss`),
`chat_template_kwargs`, and `aux_target_field` (`train_sft.py:842-844` →
`load_and_prepare_sft_dataset` `preprocessing.py:140-160` → `prepare_sft_dataset:72-112` →
`materialize_sft_features:49-69` → `materialize_sft_example`). So the 4-hop is a **shared
byte-identity risk** (every hop must default `full_conversation`), not a differentiator.
This is exactly the assumption I marked `most_likely_wrong`; it dissolves the thread-length
argument and leaves the decision on layering grounds alone.

### Decision + rationale

**Choose B: `prompt_render: str = "full_conversation"` on `SFTTrainingConfig`.** Three
reasons, in priority order:

1. **Same-kind precedent.** `SFTTrainingConfig` already owns every preprocessing-wide
   render/masking knob: `packing:66`, `completion_only_loss:67`, `assistant_only_loss:68`,
   `chat_template_kwargs:86`. `prompt_render` selects among render/masking *strategies* —
   it is a peer of these, not an aux_head-internal parameter (contrast the genuinely
   internal `layer`, `token_position`, `head_type`, `loss`).
2. **Co-location with the code region it governs.** The `prompt_completion` branch
   *replaces* the `assistant_only_loss` prefix-match masking at `sft_preprocessing.py:200-214`
   with an exact prompt/completion split. Housing `prompt_render` on `AuxHeadConfig` while
   `assistant_only_loss` lives on `SFTTrainingConfig` splits governance of **one masking
   region** across two configs — the real layering smell.
3. **The "decoupling" con is already true and is not location-specific.** The lead's
   concern about Option B (a user enabling `aux_head` + `end_of_prompt` must also set
   `prompt_render=prompt_completion`) is real but (a) *already exists* — aux_head
   `end_of_prompt` already depends on `assistant_only_loss=true` (a `SFTTrainingConfig`
   knob) to produce the `-100` mask `prompt_end_indices` reads; and (b) is **default-driven,
   not location-driven** — the default is `full_conversation` under *either* option, so the
   silent-unfaithful footgun is identical for A and B. It is addressed by the coherence
   guard (§GUARD), not by the field's home.

**Exact field:** `SFTTrainingConfig.prompt_render: str = "full_conversation"` (allowed:
`"full_conversation"` | `"prompt_completion"`). Loader: parsed in `load_config`'s training
block alongside the other `SFTTrainingConfig` fields (default preserves byte-identity for
every existing config; absent key ⇒ `full_conversation`). **No `AuxHeadConfig` change** for
the flag (the `dict_to_dataclass` silent-drop gotcha is therefore not in play for this
field — but CODE must still add it as a real `SFTTrainingConfig` field, not rely on kwargs).

---

## DECISION 2 — terminal-token mechanism: append derived `eos_token_id`

### Options

- **D2-a — re-render the assistant turn** (`apply_chat_template([... , assistant], add_generation_prompt=False)`
  and diff to isolate the completion+terminal). **REJECTED.** Re-rendering the assistant
  turn reproduces the precise `...</think>\n{content}` full-conversation scaffold whose
  divergence from the `add_generation_prompt=True` render is the 0029 root cause. Any
  mechanism that round-trips the completion through `add_generation_prompt=False` risks
  re-importing the cos-0.544 failure. The lead's steer (faithfulness/determinism outranks
  model-agnosticism here) makes this disqualifying.
- **D2-b — encode the raw completion + append a derived terminal id.** **CHOSEN.**
  `completion_ids = encode(completion_text, add_special_tokens=False) + [terminal_id]`,
  where `terminal_id = tokenizer.eos_token_id`. This is what §1/the prototype already do in
  spirit (raw content + explicit terminal); it is fully deterministic (no template
  round-trip, no scaffold divergence) and model-agnostic by deriving — not hardcoding — the
  id.

### Decision + rationale

**Append `tokenizer.eos_token_id` as the terminal**, with these constraints:

1. **Derived, never literal.** Read `tokenizer.eos_token_id`; do NOT hardcode
   `<|im_end|>` or any literal. For this Qwen3 lineage the chat `eos_token` resolves to
   `<|im_end|>`, matching the verified prototype; for other models it resolves to their own
   end-of-turn id. Keeps the engine portable.
2. **Loud guard on `None`.** If `tokenizer.eos_token_id is None`, raise a clear error
   (`prompt_render="prompt_completion" requires the tokenizer to define eos_token_id`) —
   never silently emit a completion with no terminal.
3. **Terminal carries a real label.** `labels = [-100]*len(prompt_ids) + completion_ids`,
   so every `completion_ids` element including the appended `terminal_id` is a real label
   (acceptance §3.3). Pin with an assertion: `labels[len(input_ids)-1] != -100` and (pre-
   truncation) `labels[-1] == terminal_id`.
4. **Faithfulness pin (the safety net for the eos==terminal assumption).** The verified
   number (cos 0.9998) was obtained with `<|im_end|>`. The faithful-boundary test (§TESTS)
   asserts the chosen terminal reproduces the verified read on the real tokenizer: the
   `prompt_completion` `end_of_prompt` vector equals the prompt-only
   `add_generation_prompt=True` last-token vector (cos ~ 1.0). If, for some target model,
   `eos_token_id` is NOT the template's end-of-turn id, this test fails RED and CODE falls
   back to deriving the end-of-turn id from a minimal controlled render (CODE discretion;
   the primary path is `eos_token_id`).

Note: the terminal only affects which token *closes* the completion (and the LM-loss
target on it). The aux_head reads `end_of_prompt` = the **last prompt token**, which is
fixed entirely by the prompt-half render and is independent of the terminal choice — so D2
cannot move the read position; it governs LM-loss correctness on the completion tail.

---

## ENABLE-THINKING — `chat_template_kwargs` forwarding (first-class contract, not a footnote)

This is the real residual risk (my teachback assumption (e); the lead's first-class item;
connected to project issue #47 VLLMGenerator `enable_thinking`).

- **Within the engine:** `chat_template_kwargs` (e.g. `{"enable_thinking": false}`)
  controls the assistant scaffold the prompt-half render emits (whether `</think>` is
  present, and thus the exact boundary token). The `prompt_completion` branch builds its
  prompt half via the **existing** `:201-206` call, which already forwards
  `**template_kwargs`. The branch MUST forward the identical `template_kwargs` there — same
  object the full-conversation render (`:187-192`) receives — so `prompt_render` introduces
  **no new** divergence axis. The completion half is encoded RAW (`encode(completion_text)`,
  no `apply_chat_template`), so `enable_thinking` does not apply to it — correct by
  construction.
- **Contract assertion:** the prompt-half render forwards `**template_kwargs` verbatim;
  `test_chat_template_kwargs_passthrough.py` stays green AND gains a `prompt_completion`
  case asserting the kwargs reach the prompt-half render (§TESTS).
- **Cross-system dependency (cannot be enforced by the engine alone — flag to #47):**
  faithfulness holds only if the SAME `enable_thinking` value is used at (i) training
  preprocessing here and (ii) the inference-time render where the head reads. The engine
  guarantees (i) is internally consistent; matching (ii) is a research-side / generation
  concern tracked by issue #47. The HANDOFF records this as a downstream invariant, not an
  engine deliverable.

---

## GUARD — recommended cross-config coherence check (architect proposal; lead decides scope + severity)

Because `prompt_render` (training) and `token_position` (aux_head) live on different
configs and the default is `full_conversation`, the silent-unfaithful combo —
`aux_head.enabled` AND `token_position=="end_of_prompt"` AND
`training.prompt_render=="full_conversation"` on multi-turn rows — is the exact 0029 bug a
user can re-trip by omission. Consistent with the engine's existing coherence-guard pattern
(`load_aux_head_config` phase/identity guards, #54/B-M1), I recommend a cross-config check
at the wiring site where both are visible (`train_sft.py` ~`:826-828`, where `aux_head_cfg`
is read and `config.training` is in scope):

> when `aux_head_enabled and aux_head_cfg.token_position == "end_of_prompt" and
> config.training.prompt_render == "full_conversation"`: emit a loud signal that
> `end_of_prompt` on full-conversation rows may read a non-anchor token (cite 0029).

**Severity — RESOLVED (lead ruling): `WARN`, LAND NOW (this PR, not deferred).** WARN keeps
the generic engine permissive (`end_of_prompt` + `full_conversation` is legitimate for
prompt-only / single-turn / inference-shaped rows where the divergence may not bite), while
making the footgun observable. ERROR would false-positive on those valid configs. The
WARN-vs-ERROR discriminator is principled and consistent with the prior coherence guards:
**B-M1 was ERROR because its combo `(freeze_base=false, lm_loss_weight=0)` is NEVER
legitimate; this combo is SOMETIMES legitimate, so it WARNs.** Any hard project-side
enforcement belongs in the research-repo recipe layer, not the generic tuner. It lands in
THIS PR on the same config-validation surface as the Phase A M1/M2 and Phase B B-M1 guards
(`train_sft.py` ~`:826-828`).

---

## CONTRACT — `materialize_sft_example` new branch (CODE-precise)

### Signature

Add `prompt_render: str = "full_conversation"` to `materialize_sft_example`
(`shared/sft_preprocessing.py:161`). **Thread it EXACTLY alongside `chat_template_kwargs`**
at every hop that already forwards `chat_template_kwargs` — same functions, same
passthrough shape, default `"full_conversation"`:

1. `SFTTrainingConfig.prompt_render` (`config_loader.py`) → value at `train_sft.py` source
   (beside `chat_template_kwargs=config.training.chat_template_kwargs`, `:843`).
2. `load_and_prepare_tokenized_dataset` (train_sft's dataset-prep wrapper, the `:832` call)
   → `load_and_prepare_sft_dataset` (`preprocessing.py:140-160`) →
   `prepare_sft_dataset` (`:72-112`) → `materialize_sft_features` (`:49-69`) →
   `materialize_sft_example`. Each gains a `prompt_render: str = "full_conversation"` param
   forwarded verbatim, mirroring the existing `chat_template_kwargs` parameter at each hop.

Using `chat_template_kwargs` as the wiring template makes the thread unambiguous and DRY,
and guarantees every hop defaults to `full_conversation` (byte-identity).

### Branch logic (inside `materialize_sft_example`, after `:178` sanitize)

```
if prompt_render == "prompt_completion" and messages[-1].get("role") == "assistant":
    # prompt half: REUSE the existing add_generation_prompt=True render (:201-206)
    prompt_str = tokenizer.apply_chat_template(
        messages[:-1], tokenize=False, add_generation_prompt=True, **template_kwargs)
    prompt_ids = _encoder.encode(prompt_str, add_special_tokens=False)

    # completion half: RAW assistant content + DERIVED terminal (D2)
    completion_text = messages[-1]["content"]            # sanitized assistant text (str)
    terminal_id = tokenizer.eos_token_id                 # loud-guard if None
    completion_ids = _encoder.encode(completion_text, add_special_tokens=False) + [terminal_id]

    full = prompt_ids + completion_ids
    truncation_applied = len(full) > max_seq_length
    input_ids = full[:max_seq_length]
    attention_mask = [1] * len(input_ids)
    labels = ([-100] * len(prompt_ids) + completion_ids)[:max_seq_length]
    loss_mask_mode = "assistant_only"
    return PreparedSFTExample(input_ids, attention_mask, labels,
                              example_format, loss_mask_mode, truncation_applied, source_hash)
else:
    # EXISTING full-conversation path (:187-214) — UNCHANGED, byte-identical
```

### Invariants the contract must hold

- **Byte-identity (default):** `prompt_render == "full_conversation"` takes the existing
  path with zero statement reordering — the new branch is a strict prepend gated on a
  non-default string. No RNG/state touched on the default path.
- **Boundary faithfulness:** under `prompt_completion`, `(labels != -100).argmax == len(prompt_ids)`
  ⇒ `prompt_end_indices == len(prompt_ids) - 1` (acceptance §3.1) — **no aux_head change**.
- **Masking (§3.3):** every `prompt_ids` index is `-100`; every `completion_ids` index
  (incl. terminal) is a real label. `aux_target` threading is **untouched** — it is read one
  layer up in `prepare_sft_dataset._materialize` (`preprocessing.py:104-105`), outside this
  function; CODE must not relocate the render out of `prepare_sft_dataset`.
- **Truncation:** right-trim `input_ids`/`labels` to `max_seq_length`, mirroring `:194-195`.
  Document the existing-behavior edge: a row whose `prompt_ids` alone exceed `max_seq_length`
  loses the boundary (same limitation as today's over-long full-conversation rows). Add a
  truncation assertion in tests.
- **`template_kwargs`:** forwarded verbatim in the prompt-half render (§ENABLE-THINKING).
- **Non-string assistant content:** the branch assumes `messages[-1]["content"]` is the
  sanitized assistant text (string), which `normalize_sft_messages`/`sanitize_*` guarantee
  for the SFT path. If content is non-string after sanitize, CODE raises (no silent
  mis-encode) — scoped, since aux_head SFT rows are text.

---

## Q4 — backward-compat guard tests (must stay byte-identical green under default)

Confirmed present at HEAD; all must pass unchanged under `prompt_render="full_conversation"`:

- `tests/trainers/sft/test_preprocessing_contract.py` — canonical `materialize_sft_example`
  / `prepare_sft_dataset` contract (highest-value byte-identity guard).
- `tests/trainers/sft/test_aux_head_preprocessing.py` — aux_head two-hop `aux_target`
  threading + `-100` masking on full-conversation rows.
- `tests/trainers/sft/test_chat_template_kwargs_passthrough.py` — `**template_kwargs`
  forwarding; the new branch keeps it green by forwarding kwargs in the prompt-half render,
  and gains a `prompt_completion` case (§TESTS).
- `tests/trainers/sft/test_data_loader.py` — the `add_generation_prompt=False` text path
  (unaffected; confirms the change is scoped to the render branch).

The default-path byte-identity is **structural** (new branch is a gated prepend), so these
tests corroborate rather than constitute the proof — but they are the regression tripwire if
a future edit perturbs the default path.

## TESTS — new + extended

1. **§2.5 joint-grad extension** (`test_aux_head_integration.py`): add a `prompt_render`
   param to `_make_trainer` (`:102-111`). Add a `prompt_completion` variant of the
   forced-GC head-path-isolation shape (`:301-333`): build rows via the new render,
   assert (i) `prompt_end_indices == len(prompt)-1` on the rendered labels, (ii) head + a
   base/LoRA param both receive non-zero grad under `freeze_base=false, lm_loss_weight>0`,
   forced GC on. Rows are hand-built tensors (no unsloth), so the fixture may call
   `materialize_sft_example` directly. (Acceptance §3.4.)
2. **New faithful-boundary test** (preprocessing-level; new test or in
   `test_aux_head_preprocessing.py`): on a tokenizer whose chat template **diverges**
   between the two render modes, materialize one row `prompt_completion`, run a tiny forward,
   and assert the reduced `end_of_prompt` vector equals the prompt-only
   `add_generation_prompt=True` last-token vector (cos ~ 1.0). Also assert the terminal label
   `!= -100` and `truncation_applied` correctness. **Fixture recommendation:** a small
   hand-authored chat template reproducing the one-fewer-newline divergence (hermetic, no
   model download), or the real Qwen3 tokenizer if available offline. (Acceptance §3.1/§3.3.)
3. **Default byte-identity** is already covered by the Q4 set; add one explicit assertion
   that `prompt_render="full_conversation"` yields the same `PreparedSFTExample` as omitting
   the param.
4. **`prompt_completion` kwargs passthrough**: extend `test_chat_template_kwargs_passthrough.py`
   with a case asserting `template_kwargs` reach the prompt-half render under
   `prompt_completion`.

## Acceptance-criteria mapping (0029 §3)

| 0029 criterion | Where satisfied |
|---|---|
| §3.1 faithful boundary (cos ~ 1.0) | §CONTRACT boundary invariant + TESTS #2 |
| §3.2 backward-compat byte-identical | §CONTRACT byte-identity invariant + Q4 set + TESTS #3 |
| §3.3 masking (prompt -100, completion+terminal real) | §D2 + §CONTRACT masking invariant + TESTS #2 |
| §3.4 joint path intact (head+LoRA grads) | TESTS #1 |

## Decisions formerly open — RESOLVED (lead rulings, binding on CODE)

1. **GUARD severity + scope** (§GUARD): **RESOLVED — `WARN`, LAND NOW in this PR.** Not
   deferred. ERROR is wrong here because `end_of_prompt` + `full_conversation` is sometimes
   a legitimate config (unlike B-M1's never-legitimate combo, which is why B-M1 was ERROR).
   Lands on the `train_sft.py` ~`:826-828` config-validation surface alongside the prior
   coherence guards.
2. **D2 terminal** (§D2): **RESOLVED — derived `tokenizer.eos_token_id` is the primary
   terminal** (loud-guard if `None`; terminal carries a real label; faithfulness pinned by
   the §TESTS cos~1.0 boundary test). The minimal-render fallback is CODE discretion **only
   if** the boundary pin fails for a specific target model — it is NOT a default path.

## reasoning_chain — how the two decisions connect to the seam

The seam is a single function (`materialize_sft_example`) reached by a thread that already
carries every preprocessing knob (`loss_mask_mode`, `chat_template_kwargs`, `aux_target_field`).
→ Because the value reaches the function identically regardless of field home, D1 cannot be
decided on thread mechanics (this dissolves my teachback's 4-hop argument); it is decided by
*ownership* — and the `prompt_completion` branch replaces the `assistant_only_loss` masking
region, so its selector belongs beside `assistant_only_loss` on `SFTTrainingConfig` (D1=B).
→ The same seam encodes the completion RAW and appends a terminal; deriving that terminal by
re-rendering the assistant turn would re-enter the full-conversation scaffold that is the
0029 root cause, so the terminal must be a derived id (`eos_token_id`), not a re-render and
not a literal (D2=eos-append). → The seam's prompt half is the *existing*
`add_generation_prompt=True` render, which already forwards `template_kwargs`; reusing it
verbatim is what keeps `enable_thinking` from becoming a new divergence axis (ENABLE-THINKING
invariant). → Because D1 places the selector on a different config from `aux_head.token_position`,
the default `full_conversation` leaves a silent-unfaithful corner that is *default-driven, not
location-driven*, so it is closed by a cross-config coherence guard rather than by the field's
home (GUARD). The four threads — single seam, ownership, terminal determinism, kwargs reuse —
are one structure viewed from four sides.
