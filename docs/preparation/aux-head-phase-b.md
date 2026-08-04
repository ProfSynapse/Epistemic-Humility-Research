# Prepare: aux_head Phase B — anchor re-confirmation + §2.5 gradient-flow de-risk

> **Scope.** RESEARCH ONLY (Task #38). Two deliverables, no implementation, no
> code changes. (1) Re-confirm the `0028` handoff §1 file:line anchors against
> the CURRENT `synaptic-tuner` submodule main after PR #118 merged, reporting
> the actual current line numbers and flagging drift. (2) De-risk the §2.5
> gradient-flow gotcha against the INSTALLED stack and recommend the concrete
> CODE fix + the assertion the §2.5 test should check.
>
> The submodule is a **domain-agnostic training engine**: this note describes the
> engine in generic terms (a head reads a hidden layer, supervised by a
> proper-scoring loss against a per-row target). No project vocabulary is used for
> the engine surfaces below.

## Executive summary

1. **Anchors: only one material drift.** Verified at submodule main `9dee8b5`
   (the PR #118 merge commit) with `transformers 5.5.0 / peft 0.18.1 /
   torch 2.9.0+cu128`. All `aux_head.py`, `aux_head_trainer.py`, and
   `train_sft.py` anchors in the `0028` §1 table are **exact or within the
   documented span**. The single material drift is `AuxHeadConfig`: the handoff
   says `:160-168`, the dataclass is actually at **`config_loader.py:150`**
   (header), fields running to ~`:169`. The `train_sft.py` "aux config read"
   anchor (`:824-844`) and "trainer swap-in" (`:1011-1032`) are spans whose
   landmark lines (`AuxHeadTrainer(` at **`:1030`**, `save_aux_head(` at
   **`:1138`**, inside the doc's `:1132-1145` span) check out. No anchor is
   stale enough to misdirect the builder; the `AuxHeadConfig` line just needs the
   −10 correction.

2. **§2.5 gradient-flow fear does NOT reproduce on the installed stack (vanilla
   transformers GC).** An empirical CPU probe (tiny `LlamaForCausalLM` + PEFT
   LoRA on the installed versions) shows that backpropagating a function of a
   **mid-layer** `hidden_states[k]` tensor — the head's read path, with **no LM
   loss** — produces **non-zero grad on LoRA params that sit at or before the read
   layer**, and the read tensor **retains `grad_fn`**, under gradient checkpointing
   **both `use_reentrant=False` (the modern default) AND `use_reentrant=True`**,
   **with and without `enable_input_require_grads()`**. In all four GC×eirg
   combinations: `hidden_grad_fn=True`, `backward` succeeds, LoRA non-zero `4/12`.
   So vanilla-transformers checkpointing does **not** detach the hidden state the
   head reads.

3. **Two caveats keep this from being a blanket "no fix needed."** (a) **Production
   uses Unsloth's custom GC** (`use_gradient_checkpointing: "unsloth"`), not the
   vanilla `torch.utils.checkpoint` my probe exercised — Unsloth's offloading
   checkpoint must be confirmed **live on GPU**, my probe does not cover it.
   (b) The §2.5 test as specced (one joint step, `lm_loss_weight>0`, assert
   non-zero grad on a LoRA param) **can pass through the LM-loss path even if the
   head→base path were dead** — in the LM-present probe the LM CE alone lit `6/12`
   LoRA params. The test must **isolate the head's contribution to the base**, not
   just observe that *some* LoRA grad exists.

4. **Recommendation (to apply in CODE, by the builder — flagged, not done here;
   incorporates the team-lead's crux ruling of 2026-06-29, see "Lead ruling" box
   below):** make the §2.5 test target the **worst case** and key the defensive
   fixes on GC being enabled. Concretely: (i) the §2.5 assertion test must **force
   `gradient_checkpointing` ON** regardless of the resolved default (Phase B
   co-trains an *unfrozen* base — the memory-heavy regime where users *will* enable
   GC — so a latent gotcha would bite exactly the intended use case), and assert
   non-zero grad on **both** a head param **and** a LoRA param; (ii) ship
   `model.enable_input_require_grads()` (and, if needed, `use_cache=False`) as
   **CONDITIONAL guards keyed on `gradient_checkpointing` being enabled** on the
   `freeze_base=false` path — **not** unconditional, so the Phase-A byte-identical
   path stays untouched; the guard is a no-op on vanilla GC (probe proves the path
   already works) and the documented remedy if Unsloth's checkpoint needs it;
   (iii) **strengthen** the both-params assertion to also **isolate the head path**
   (the both-params check alone false-greens via the LM-loss path — see §2.5-test
   below). Then let a **live GPU smoke** on the real Unsloth stack be the
   authoritative confirmation; if the isolated-head assertion passes there with GC
   forced on, no further fix is needed.

---

## Deliverable 1 — §1 anchor re-confirmation (submodule main `9dee8b5`)

Stack verified in-process: `transformers 5.5.0 | peft 0.18.1 | torch 2.9.0`.

| `0028` §1 anchor | Handoff says | Actual @ `9dee8b5` | Status |
|---|---|---|---|
| `aux_head.py` `AuxHead.__init__` | `:66-98` | `def __init__` **:66** | ✅ exact |
| `aux_head.py` `AuxHead.forward` | `:105-110` | `def forward` **:105** | ✅ exact |
| `aux_head.py` `reduce_hidden_states` | `:137-181` | **:137** (no `end_of_prompt` branch — confirms §2.3 is net-new) | ✅ exact |
| `aux_head.py` `compute_aux_head_loss` | (impl) | **:185** | ✅ present |
| `aux_head.py` `save_aux_head` | `:209-243` | **:209** | ✅ exact |
| `aux_head.py` `load_aux_head` | `:245-283` | **:245** | ✅ exact |
| `aux_head.py` `infer_aux_scalar` | `:287+` | **:287** | ✅ exact |
| `aux_head_trainer.py` `__init__` freeze call | `:76-77` | `if ... freeze_base: self._freeze_base_keep_head()` **:76-77** | ✅ exact |
| `aux_head_trainer.py` `_freeze_base_keep_head` | `:106-131` | **:106** | ✅ exact |
| `aux_head_trainer.py` `create_optimizer` | `:133-152` | **:133**; head-only group `head_params` **:147** | ✅ exact |
| `aux_head_trainer.py` `compute_loss` | `:154-188` | **:154**; `output_hidden_states=True` **:176** | ✅ exact |
| `aux_head_trainer.py` **the stubbed seam** | `:186` | **:186** verbatim `# Phase B seam (do NOT enable here): loss = outputs.loss + cfg.lm_loss_weight * head_loss`; `loss = head_loss` **:187** | ✅ exact |
| `config_loader.py` `AuxHeadConfig` dataclass | **`:160-168`** | **`:150`** (header); fields to ~`:169` | ⚠️ **−10 DRIFT** (only material one) |
| `config_loader.py` `dict_to_dataclass` silent-drop | (note) | **:214** (still silently drops unknown keys — the §3 warning to add `input_norm` to the dataclass STANDS) | ✅ note holds |
| `config_loader.py` `load_aux_head_config` | (impl) | **:288** | ✅ present |
| `config_loader.py` `Config.aux_head` field | (impl) | `class Config` **:172**; `aux_head: AuxHeadConfig = field(default_factory=...)` **:180** | ✅ present |
| `train_sft.py` aux config read | `:824-844` | span lands on the aux read block | ✅ span ok |
| `train_sft.py` trainer swap-in | `:1011-1032` | `AuxHeadTrainer(` **:1030** (inside span) | ✅ span ok |
| `train_sft.py` sidecar save | `:1132-1145` | `from src.aux_head import save_aux_head` **:1136**; `save_aux_head(` **:1138** (inside span) | ✅ span ok |
| `aux_head_example.yaml` GC knobs | (referenced) | `use_gradient_checkpointing: "unsloth"` **:30**; `gradient_checkpointing: true` **:46** | ✅ both present — see §2.5 |
| `tests/trainers/sft/test_aux_head*.py` (5 files) | "five test files" | `test_aux_head.py`, `_config.py`, `_integration.py`, `_preprocessing.py`, `_trainer_source.py` | ✅ all 5 present (extend, don't regress) |

**Builder action from Deliverable 1:** apply the **−10 correction** to the
`AuxHeadConfig` anchor (`:150-169`, not `:160-168`) when wiring §3 (adding
`input_norm`). Everything else in §1/§2/§3 can be taken at face value. The
`dict_to_dataclass` silent-drop gotcha is real and unchanged — `input_norm` MUST
be added to the dataclass or it is silently dropped.

---

## Deliverable 2 — §2.5 gradient-flow de-risk (installed stack)

### The §2.5 question, restated

`0028` §2.5 warns: `output_hidden_states=True` + gradient checkpointing + LoRA
co-training is fragile — checkpointing "recomputes activations and can detach the
hidden state the head reads," and LoRA "needs grads to reach the adapter." It asks
the builder to **verify, don't assume**, and says the standard fix (if it breaks)
is `model.enable_input_require_grads()` and/or `use_cache=False`.

The crux: **is the head→hidden→base(LoRA) gradient path alive under gradient
checkpointing on the installed stack?**

### GC is ON by default — this is the realistic regime

Two independent checkpointing knobs are wired, and the example config (the seed
for the Phase-B example) turns **both** on:

| Knob | Where set | Example value |
|---|---|---|
| Unsloth model-level GC | `train_sft.py:860` → `model_loader` (Unsloth `FastLanguageModel`/`get_peft_model`) | `aux_head_example.yaml:30` `use_gradient_checkpointing: "unsloth"` |
| HF Trainer-level GC | `train_sft.py:321` & `:888` → `TrainingArguments.gradient_checkpointing` | `aux_head_example.yaml:46` `gradient_checkpointing: true` |

So Phase-B co-training will run with checkpointing active. The §2.5 concern is
therefore on the live path, not hypothetical. (Side note for the builder, not a
§2.5 item: setting **both** knobs is redundant on an Unsloth model — Unsloth's
`get_peft_model` already installs its checkpoint; HF's
`gradient_checkpointing_enable()` on top is at best a no-op and at worst a
double-wrap. PR #118 review F3 already flagged trimming `gradient_checkpointing:
true` from the example as no-benefit-on-frozen-base. Worth resolving which single
knob the Phase-B example should carry — but that is a config-hygiene call, out of
§2.5 scope.)

### Empirical probe on the installed stack

A CPU probe built a tiny `LlamaForCausalLM` (3 layers, hidden 32), froze the base,
attached PEFT LoRA on `q_proj`/`v_proj` (12 trainable LoRA tensors), and
backpropagated a function of a **mid-layer** `hidden_states[2]` (the head's read
path) with **no LM loss** — the exact path §2.5 says can silently die. It also ran
an LM-loss-present cross-check. Probe scripts (scratchpad, not committed):
`gc_gradflow_probe.py`, `reentrant_probe.py`.

**Head-path isolation (loss = f(mid-layer `hidden_states`), NO LM loss):**

| GC | `use_reentrant` | `enable_input_require_grads` | `hidden.grad_fn` | LoRA non-zero grad |
|---|---|---|---|---|
| off | — | no | present | 4/12 |
| on | False (modern default) | no | present | 4/12 |
| on | False | yes | present | 4/12 |
| on | **True** (classic break case) | no | present | 4/12 |
| on | **True** | yes | present | 4/12 |

**Reading:** the head's read tensor keeps its autograd graph and grad reaches every
LoRA param at/before the read layer, in **every** GC configuration — including
reentrant checkpointing without `enable_input_require_grads`, the configuration
that is classically supposed to zero out grads inside checkpointed blocks. On this
transformers version, collecting `hidden_states[k]` exposes a tensor whose backward
recomputes the checkpointed region and the LoRA grads survive. (Only 4/12 light up
because only LoRA tensors **before** the read layer contribute to that hidden
state — expected and correct, not a partial failure.)

**LM-loss-present cross-check (`outputs.loss.backward()`, GC on):** LoRA non-zero
`6/12` — the LM CE alone reaches *more* LoRA params (it flows through all layers).
**This is the test-adequacy trap:** with `lm_loss_weight>0`, LoRA params get grad
from the LM path regardless of whether the head→base path is alive.

### What this means for the §2.5 fix

- On **vanilla transformers GC**, **no fix is required** for the head→base grad
  path — not even `enable_input_require_grads()`. The fear does not reproduce.
- **`use_cache=False`** during training is already the effective state: HF Trainer
  disables the cache when GC is on, and Unsloth manages it internally. There is
  **no** explicit `use_cache=False` in the SFT training path today (only
  `inference.py` sets `use_cache=True`), and that is fine — the framework owns it.
  The builder does **not** need to add a manual `use_cache=False` for correctness;
  if they want belt-and-suspenders they can set `model.config.use_cache = False`
  on the `freeze_base=false` branch, but it is not load-bearing.
- The **only** real unknown is **Unsloth's custom offloading checkpoint**
  (`"unsloth"`), which my CPU probe cannot exercise (no GPU, Unsloth not importable
  offline in this path). It *may* behave differently from vanilla
  `torch.utils.checkpoint`.

> **Lead ruling (team-lead, 2026-06-29) — target the worst case, guard conditionally.**
> The §2.5 assertion test should **force `gradient_checkpointing` ON** regardless of
> the resolved default, because (1) the `0028` handoff explicitly flags GC×LoRA×hidden
> as a fragility to *verify*, and (2) Phase B co-trains an **unfrozen** base — the
> memory-heavy regime where users *will* enable GC — so shipping the gotcha latent
> would bite exactly the intended use case. The `enable_input_require_grads()` /
> `use_cache=False` fixes must be **CONDITIONAL guards keyed on GC being enabled**,
> **not** unconditional, so the Phase-A byte-identical path (frozen base, GC off or
> on but head-only) stays untouched. The installed transformers **is** 5.5.0 (the
> contingency did not fire — research was done against the actually-installed source),
> so no version discrepancy to flag.

**Concrete CODE recommendation (for the builder to apply, flagged not done):**
1. Do **not** add an *unconditional* training-time `use_cache=False` — the framework
   already handles it when GC is on, and an unconditional flip would touch the
   Phase-A path. If a belt is wanted, set `model.config.use_cache = False` **only on
   the `freeze_base=false` branch AND only when `gradient_checkpointing` is enabled**.
2. Add `model.enable_input_require_grads()` as a **CONDITIONAL guard** — gated on
   `freeze_base=false` **AND** `gradient_checkpointing` enabled (per the lead ruling),
   not unconditional. It is a no-op on vanilla GC (probe proves the path already works
   without it) and is exactly the documented remedy should Unsloth's checkpoint need
   an input requiring grad. Keying it on GC keeps the Phase-A byte-identical path
   (and any GC-off run) completely untouched. Net: harmless on the proven path,
   protective on the unproven one, invisible to Phase A.
3. Spec the §2.5 test to **force GC ON** and assert non-zero grad on **both** a head
   param **and** a LoRA param (lead ruling), then **strengthen** it to **isolate the
   head path** (next section) so the LoRA-grad half cannot false-green via the LM
   loss. The truly authoritative confirmation is a **live GPU smoke on the real
   Unsloth stack with GC on** — recommend the builder run one before handback and
   document the result; the CPU probe de-risks but does not replace it.

### What the §2.5 assertion test must check (test-adequacy fix)

The `0028` §2.5 spec ("one joint step, `freeze_base=false`, `lm_loss_weight>0`,
assert non-zero grad on **both** a head param and a LoRA param") is **necessary but
not sufficient**: the LoRA-grad half can pass through the **LM-loss** path even if
the head→base path is dead (probe: LM CE alone lights 6/12 LoRA params). A silently
detached head would still go green. Strengthen the test to isolate the head's
contribution to the base. Any one of these makes it a real guard:

- **Preferred — head-only step with an unfrozen base:** run a step with
  `freeze_base=false` **and `lm_loss_weight=0`** (so `loss = head_loss` only,
  per the §2.1 guard), and assert a LoRA param at/before the read layer gets
  non-zero grad. This proves the head's gradient reaches the base *through the read
  hidden state*, with no LM path to mask a failure. (Keep the existing
  `lm_loss_weight>0` joint-step assertion too, for the combined-loss path.)
- **Or — assert the read tensor is in the graph:** in/around `compute_loss`, assert
  `outputs.hidden_states[cfg.layer].grad_fn is not None` (equivalently
  `.requires_grad`) on the `freeze_base=false` path. A detached/recomputed-away
  read tensor fails this immediately, independent of any LoRA bookkeeping.
- **Belt:** assert the head param's grad is non-zero too (already in the spec) — the
  head path being alive is necessary for the readout to learn at all.

Run the strengthened assertion on the **real Unsloth GC** stack (live GPU) as the
final word; on vanilla GC it already passes per the probe.

---

## Risk register

| Risk | Prob. | Impact | Mitigation |
|---|---|---|---|
| Unsloth offloading GC detaches the head's read tensor (vanilla does not) | Low–Med | High (head learns nothing / base gets no head-grad, silently) | `enable_input_require_grads()` on the `freeze_base=false` branch + the isolated-head assertion run on a **live GPU** Unsloth smoke before handback |
| §2.5 test passes via the LM-loss path while head→base is dead | Med (if test left as-specced) | High (false green) | Add the `lm_loss_weight=0`+`freeze_base=false` head-only assertion and/or the `hidden_states[layer].grad_fn is not None` check |
| Builder uses stale `AuxHeadConfig:160-168` anchor, edits wrong lines | Low | Low (edit lands off-target, caught immediately) | −10 correction in Deliverable 1; the dataclass header is `:150` |
| Double-GC (both knobs on) interacts oddly with the joint backward | Low | Med | Config-hygiene: pick one GC knob for the Phase-B example (Unsloth's, given the Unsloth model); see §2.5 side note + PR #118 F3 |

## Sources / provenance

- Submodule main `9dee8b5` ("feat(sft): generic auxiliary scalar readout head
  (aux_head) — Phase A (#118)") — `aux_head.py`, `aux_head_trainer.py`,
  `config_loader.py`, `train_sft.py`, `aux_head_example.yaml` read directly.
- Installed versions probed in-process: `transformers 5.5.0`, `peft 0.18.1`,
  `torch 2.9.0+cu128`. `transformers` default `use_reentrant` confirmed via
  `PreTrainedModel.gradient_checkpointing_enable` source introspection.
- Empirical grad-flow probes (scratchpad, not committed): `gc_gradflow_probe.py`,
  `reentrant_probe.py` — both run clean on CPU; results tabulated above.
- `docs/sessions/0028 - phase-b-joint-aux-head-engine-build-handoff.md` — the
  Phase-B design under verification.
- `docs/review/pr118-aux-head-phase-a-review.md` — `create_optimizer` override
  cleared SAFE on transformers 5.5.0; F3 (trim no-benefit GC from example).

## Caveats (read before relying on this)

- The grad-flow finding is **authoritative only for vanilla transformers GC**. The
  production path uses **Unsloth's** checkpoint, which is **not** covered here and
  needs a **live GPU** confirmation. Treat the "no fix needed" conclusion as
  *de-risked, not closed* until that smoke runs.
- The probe uses a 3-layer toy model reading layer index 2; the production head
  reads a mid-late layer of a real base. The *mechanism* (mid-layer read retains
  graph through checkpointed blocks) is layer-position-general, but absolute layer
  index and model scale were not exercised.
- This note changes no code and signs off no protocol. It is input to the Phase-B
  builder, who owns the actual edits and the live verification.
