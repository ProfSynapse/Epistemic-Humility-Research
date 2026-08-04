# PR #118 Review — generic `aux_head` Phase A (frozen-base scalar readout head)

- **PR**: ProfSynapse/Synaptic-Tuner #118 — `feat(sft): generic auxiliary scalar readout head (aux_head) — Phase A`
- **Branch**: `feature/aux-scalar-head` → `main` (submodule PR only; root-repo submodule-pointer bump is a separate later commit)
- **Commits**: `873f720` (feature, 14 files, +1339) · `691b8f9` (integration tests, +203)
- **Spec**: `docs/sessions/0027 - aux-scalar-head-build-handoff.md` (PREPARE + approved ARCHITECT)
- **Reviewers**: architect (#19, design coherence) · test-engineer (#21, coverage/testability) · backend-coder (#23, implementation)
- **Date**: 2026-06-29

## Verdict

**APPROVE — no blocking findings from any reviewer.** architect: APPROVE; test-engineer: GREEN; backend-coder: NO BLOCKERS. The implementation faithfully realizes handoff-0027; the feature-off path is structurally byte-identical by gate placement; the highest-risk seam (`create_optimizer` head-only override) is confirmed SAFE on the installed transformers 5.5.0.

All findings are hardening / observability / coverage follow-ups. Two cheap safety guards are recommended to land before merge (see Minor M1/M2); everything else is a tracked or new follow-up.

## Cross-reviewer convergence

| Finding | architect | test-engineer | backend-coder | Disposition |
|---|---|---|---|---|
| `identity` + `brier` silently trains MSE-on-logits (non-proper score) | M3 | M5 | MINOR-1 | **Triple-confirmed → existing follow-up #16** (test-eng: #16 must ship its guard *with* a rejection test) |
| Full LM loss/logits computed then discarded (memory waste at scale) | F1 (future) | — | MINOR-2 | Deliberate MVP choice (spec §2.3) → **FUTURE** optimization |
| `gradient_checkpointing: true` on a fully frozen base = no benefit | F3 | — | FUTURE-1 | **FUTURE** — trim example config |

## Blocking

None.

## Minor (hardening / coverage — close before Phase B or before relying on non-default knobs)

| ID | Source | Finding | Recommended action |
|---|---|---|---|
| **M1** | architect M1 | **Checkpoint/resume silently loses the head.** HF per-step checkpoints (`save_steps=50`, `save_total_limit=3` in example config) serialize `self.model` + `optimizer.pt` + `scheduler.pt` but NOT the separately-held `aux_head` module. On `resume_from_checkpoint` the base/adapter and the head-param optimizer state reload, but the head module is reconstructed **fresh (random)** in `run()` — silently restarting head weights while reapplying stale optimizer momentum. On-path + silent. Zero resume coverage. | **(recommended fix now)** Raise loudly if `resume_from_checkpoint` is set with `aux_head` enabled (cheapest guard; converts silent-wrong → loud-fail). Fuller options: hook the head into `AuxHeadTrainer._save_checkpoint`/`_load_from_checkpoint`, or document resume-unsupported for Phase A. |
| **M2** | architect M2 | **Silent load-bearing dependency on `remove_unused_columns=False`** (`train_sft.py:925`, pre-existing). `aux_target` survives to the collator only because HF doesn't strip it; nothing in the new code asserts/documents this. Flipping the flag would silently strip `aux_target` and surface as an opaque `compute_loss` error far from the real toggle. Fail-loud, not silent-wrong. | **(recommended fix now)** `AuxHeadTrainer.__init__` guard: `assert self.args.remove_unused_columns is False` when aux_head enabled (bundles with M1 — same file). |
| **M4** | test-engineer M4 | **`_resolve_hidden_size` (`train_sft.py:230`) has ZERO executed coverage** — all three fallback branches are source-grep-asserted only, because `train_sft.py` imports `unsloth` at module load and can't be imported in tests. It is the one piece of real branching logic with no executed coverage AND it sizes the head `input_dim` (wrong value → silently mis-shaped head, fails only at first forward). | **(recommended follow-up)** Testability refactor: extract `_resolve_hidden_size` into the unsloth-free `aux_head.py`; unit-test all three fallbacks with `SimpleNamespace` models. |
| **M3** | architect M3 / test-eng M5 / backend MINOR-1 | `identity` + `brier` silent-MSE footgun (see convergence table). | **Already tracked #16.** test-eng: do NOT pin current silent behavior; require #16 to land its rejection guard *with* a test asserting the combo raises. |
| **M5** | test-engineer M1/M2/M3 | Non-default trainer knobs never driven through the real `compute_loss`/`create_optimizer`: `token_position` ∈ {mean, int} (M1), `head_type='mlp'` (M2), `head_lr` param-group lr (M3). All are unit-covered in isolation; the trainer-time wiring is the gap. Harness already parametrized — near-zero cost. | **(recommended follow-up)** Add parametrized integration variants. Bundle with M4 as a test-hardening follow-up. |
| **M6** | test-engineer M6 | `out_activation='sigmoid'` (the safe default keeping output in [0,1]) is NOT asserted in `test_absent_block_yields_disabled_default`. | One-line assert. |
| **M7** | backend MINOR-3 | Weight-decay applied to the head bias param in `create_optimizer` (no no-decay split for bias/norm). | Minor; consider a no-decay group for bias. Defer with M5. |

## Future

| ID | Source | Finding |
|---|---|---|
| F1 | architect F1 / backend MINOR-2 | Phase A computes + discards full LM loss/logits; a hidden-states-only forward (pop labels) saves the `lm_head` projection + `[batch, seq, vocab]` tensor. Deliberate MVP path now. |
| F2 | architect F2 | Multi-device/DDP: head moved to device in `__init__` before `accelerate.prepare`; not part of `accelerator.prepare(model)` → no DDP all-reduce for head params, possible device mismatch under sharding. Phase A is single-GPU (RTX 3090) → fine. Flag for any future multi-GPU use. |
| F3 | architect F3 / backend FUTURE-1 | `aux_head_example.yaml` sets `gradient_checkpointing: true` (no benefit on frozen base) + `completion_only_loss`/`assistant_only_loss` (no effect when LM loss discarded). Trim from example to avoid implying they matter. |
| F4 | test-engineer F4 | No COMMITTED AUROC discrimination guard — the 0.98-vs-oracle bar lives only in the gitignored-data scratchpad (correctly local-only; no CI lane has cached `h_base` shards). Recommend a docstring/skill note so a future maintainer knows it's intentionally local-only, not missing. |
| F5 | test-engineer F1 | `test_feature_off_is_byte_identical...` asserts the column-NAME set (no `aux_target` leak), not VALUE identity of `input_ids`/`labels`. "byte-identical" is mildly overclaimed by the test name — but the off-path is a literal skip, and the architect's structural proof (no statement reordered, no RNG/state touched) establishes byte-identity independently. Stronger guard: compare off-path materialized rows against the feature-absent baseline. |
| F6 | test-engineer F2 | `reduce_hidden_states` negative-int index branch (`idx = seq_len + token_position`) uncovered. |
| F7 | test-engineer F3 | `_log_trainable_param_accounting` WARN branch practically unreachable from a unit test; accept as defensive-only. |
| F8 | test-engineer F5 | `freeze_base=false` branch + `StopIteration` except branches — Phase B / defensive scope. |
| F9 | backend FUTURE-2 | Out-of-range `layer` index produces an unclear message; add a bounds check with a layer-count hint. |

## Confirmed clean (load-bearing clearances)

- **`create_optimizer` override SAFE on transformers 5.5.0**: `create_optimizer_and_scheduler` calls `create_optimizer()` then `create_scheduler(num_training_steps=...)` separately; `num_training_steps` derives from the dataloader/epochs, NOT the optimizer — so the head-only param group cannot desync the scheduler step count. Override signature `create_optimizer(self, model=None)` matches HF 5.5 exactly. (architect — the lead-flagged highest-value clearance.)
- **Feature-off byte-identical is STRUCTURAL**: every enabled branch is gated (`aux_target_field is not None`; `'aux_target' in features[0]`; `aux_head_enabled`/`aux_head_module is not None`). No statement reordered, no RNG touched, no state mutated on the off-path. The byte-identical test is corroboration, not the proof. (architect; cross-checked by backend-coder.)
- **`AuxHeadConfig` is a REAL dataclass field** with a dedicated `load_aux_head_config` — the §2.2 `dict_to_dataclass` silent-drop gotcha is correctly avoided. Enabled-without-`layer` fails loud.
- **Two-hop `aux_target` plumbing coherent**: `_read_aux_target` reads + validates (`math.isfinite`, loud on missing/NaN/non-numeric) in `_materialize` BEFORE `remove_columns`; collator stacks float `aux_target`; `compute_loss` pops it before the model forward. `remove_unused_columns=False` (`:925`) is the load-bearing setting that lets it survive (see M2).
- **Save/load round-trip complete**: `aux_head.safetensors` + `aux_head_config.json` sidecar; `load_aux_head` reconstructs standalone; `target_field` correctly NOT persisted; `infer_aux_scalar` bakes in no threshold/decision policy (spec §2.6 honored).
- **Frozen-base gradient path correct**: base/LoRA `requires_grad=False` → autograd graph only through the head; `bce` computed in fp32 with autocast disabled (`F.binary_cross_entropy` is autocast-blocklisted).
- **Generic-engine boundary CLEAN on ADDED lines**: zero confidence/abstention/epistemic/calibration/answerability vocab across added `Trainers/**` + `tests/**`; generic test filenames; example config uses placeholders + generic `target_field`.
- **Phase B genuinely a config-flag away**: `freeze_base`/`lm_loss_weight` are real fields fixed to Phase-A values; the Phase-B loss seam is a one-line marked comment; no Phase-A lock-in.
- **Coverage GREEN on the default/headline path** (linear + last + bce + sigmoid, frozen base): covered end-to-end through a real `Trainer.train()` CPU smoke; loud-fail paths + save/load roundtrip + feature-off column guard covered.

## Recommendation

Merge is design-approved with no blockers. Recommended remediation before merge: the two cheap `AuxHeadTrainer.__init__`/checkpoint guards **M1** (resume-guard) and **M2** (`remove_unused_columns` assert) — both close silent/opaque footguns in one file at low cost. The remainder route to follow-ups: **#16** absorbs M3 (with test-eng's rejection-test requirement); a new test-hardening follow-up absorbs **M4** (resolver refactor) + **M5** (non-default-knob integration coverage) + **M6**/**M7**; F1–F9 are logged future work.
