# PR #119 Review — generic `aux_head` Phase B (joint co-training over unfrozen base)

- **PR**: ProfSynapse/Synaptic-Tuner #119 — `feat(sft): aux_head Phase B — joint co-training over unfrozen base`
- **Branch**: `feature/aux-head-phase-b` → `main` (submodule PR only; root-repo submodule-pointer bump is a separate later commit — tracked task #30)
- **Commits**: `ff4f0bf` (feature, 11 files) · `b77db8d` (integration tests, 2 files)
- **Spec**: `docs/sessions/0028 - phase-b-joint-aux-head-engine-build-handoff.md` (self-contained PREPARE + approved ARCHITECT)
- **Reviewers**: architect (#48, design coherence — independent/authoritative) · test-engineer (#50, coverage — advisory self-review) · backend-coder (#52, implementation — ff4f0bf self-review advisory + b77db8d full-weight peer review)
- **Date**: 2026-06-29

## Verdict

**APPROVE — no blocking findings from any reviewer.** architect: APPROVE; test-engineer: 🟢 GREEN (advisory); backend-coder: NO BLOCKERS. The implementation faithfully realizes handoff-0028 §2 (all five build items) + §3 config + §4 acceptance tests (which map 1:1 onto the six criteria). The Phase-A path is structurally byte-identical by config-gate placement; the generic-engine vocabulary boundary is clean on added lines.

All findings are hardening / doc / coverage follow-ups. One cheap config-coherence guard (B-M1) is the only candidate for pre-merge remediation — it prevents a silent-wrong train mode that would corrupt downstream faithfulness science. Everything else routes to existing follow-ups #16/#29 or is logged future.

## Cross-reviewer convergence

| Topic | architect | test-engineer | backend-coder | Resolution |
|---|---|---|---|---|
| **`enable_input_require_grads` belt keying (CODE YELLOW#1)** | CONCUR ACCEPT-AS-IS (independent reasoning) | ACCEPT-AS-IS (originating disposition) | angle_3 CLEAN | **RESOLVED — unconditional belt (keyed on `freeze_base=false`) is robustly correct.** GC-detection gating would be MORE fragile: Unsloth's `use_gradient_checkpointing='unsloth'` is a SEPARATE mechanism from `TrainingArguments.gradient_checkpointing`; a gate would have to read all paths and a miss silently breaks LoRA grad flow. Belt is idempotent + provably harmless GC-off. |
| **Criterion-3 id-set-equality RED-sensitivity** | (noted sound) | EMPIRICALLY proven (scratch: 1-param real vs 30-param widened → RED) | EMPIRICALLY re-proven (runtime: same 30-vs-1, frozen `down_proj` correctly excluded) | **DOUBLE-confirmed non-tautological** by two independent falsifications. |
| **Cross-dtype `input_norm` reload (lead's deciding question)** | (input_norm portability confirmed clean) | VERIFIED not-a-bug (cast precedes layernorm @ aux_head.py:124-127; `load_aux_head:344` moves whole head atomically) | angle_4 CLEAN (cast-before-norm, autocast-blocklisted fp32, submodule moves with `.to()`) | **NOT a correctness risk.** Only effect is the standard fp32→bf16 precision reduction the plain linear head also incurs. MINOR → #29 roundtrip test. |
| **Belt LOAD-BEARING-ness (CODE YELLOW#2)** | — | CPU-unverifiable; real failure mode is Unsloth custom-offload GC + LoRA | — | **Deferred to live-GPU Unsloth smoke** (documented platform-runtime handback caveat). Belt *harmlessness* is sound; belt *load-bearing* verification is GPU-only. |

## Blocking

None.

## Minor (hardening / doc / coverage — route to follow-ups; B-M1 is the one pre-merge candidate)

| ID | Source | Finding | Recommended action |
|---|---|---|---|
| **B-M1** | architect (highest-value design finding) | **`(freeze_base, lm_loss_weight)` are gated ORTHOGONALLY with no cross-field coherence check** — two silent-misconfig corners. (a) `freeze_base=false` + `lm_loss_weight=0` → base co-trains on HEAD LOSS ALONE with no LM anchor → silent representation collapse that would **invalidate** an Amendment-R faithfulness run. **Proven reachable**: `test_gradient_flows_into_base_from_head_alone_under_checkpointing` (integration:301) updates a base param in exactly this config. (b) `freeze_base=true` + `lm_loss_weight>0` → LM term added to loss value but frozen base gives it ZERO gradient → wasted compute + misleading loss logs. Shipped example config is correct `(false, 1.0)` so neither is default → MINOR. | **Pre-merge candidate (recommended).** Config-load coherence guard in `config_loader.py load_aux_head_config` (~:305-317) that warns/errors unless the two knobs describe the same phase (`true⇔0` or `false⇔>0`). Cheap; prevents silent scientific corruption. **Shares the config-validation surface with FOLLOW-UP #16** — fold both into one config-coherence remediation. |
| **B-M2 (i)** | architect | **Resume-guard message/docstring are Phase-A-framed but the guard fires (and matters more) in Phase B** (`aux_head_trainer.py:90-113`). In Phase B a lost sidecar head pairs a co-adapted base with a fresh-random head — worse than Phase A. | Doc-accuracy: drop the "Phase A" framing; it's a blanket aux_head guard. Trivial. |
| **TE-M1** | test-engineer | **`head_lr` param-group branch still uncovered** (`create_optimizer:178-182`) — `_make_trainer` never sets `head_lr`, so every integration test runs only the `None` branch. Same gap as Phase-A #21-M3; survived remediation 3ddde6c. | Unit test: `create_optimizer` with `cfg.head_lr=X` yields `param_groups[0]['lr']==X` while base group inherits trainer LR. **Route to #29.** |
| **TE-M2** | test-engineer | **Cross-dtype `input_norm` reload uncovered** (not a bug — see convergence table). `test_save_load_roundtrip_preserves_input_norm` reloads same-dtype (fp32), so the bf16 downcast path is untested. | Roundtrip test calling `load_aux_head` against a bf16 base, asserting finite + in-[0,1] within bf16 tol. **Route to #29.** |
| **TE-M3** | test-engineer | **GC-off belt test docstring over-claims** — `test_unfrozen_base_belt_is_harmless_without_checkpointing` is a path-regression guard, not belt-isolating (on an unfrozen base `enable_input_require_grads` is a structural no-op). | Cosmetic: reword the docstring guarantee to "path trains cleanly". **Route to #29 / trivial doc.** |
| **BC angle_2** | backend-coder | **`prompt_end_indices` reads the FIRST completion boundary on interleaved multi-turn masks**, not the final user turn. Always a real boundary token, never garbage; correct for the documented single-turn-completion training-row shape. | **Single-boundary contract is INTENTIONALLY FINAL for Phase B** (lead ruling). Multi-turn generalization → FUTURE, not a defect. |

## Future

| ID | Source | Finding |
|---|---|---|
| B-F1 | architect / backend-coder angle_5 partial | `create_optimizer` doesn't split decay/no-decay param groups. Inconsequential for LoRA base params (no biases); with `input_norm=layernorm` the head now has norm affine params — fold into **FOLLOW-UP #29 M7** (head-bias no-decay). |
| BC angle_5 | backend-coder | **Single-GC-knob example footgun** — `aux_head_phase_b_example.yaml` documents the single-GC-knob choice inline (`lora.use_gradient_checkpointing:'unsloth'` ON, `training.gradient_checkpointing:false`); a user flipping HF GC back on re-introduces double-wrapping, with no loader-side validation warn. **Config hygiene, not correctness** (lead ruling: route to follow-up, fold with B-M1 config-coherence). |
| TE-F1 | test-engineer | `compute_loss` `end_of_prompt` + `labels=None` raise (`:228-232`) untested — defensive guard on a real misconfig. Cheap `pytest.raises`. |
| TE-F2 | test-engineer | `prompt_end_indices` boundary=0 (single prompt token) untested — bottom-of-range off-by-one frontier. |
| TE-F3 | test-engineer | `mlp` head + `input_norm=layernorm` combination untested (norm applies before `self.net` regardless of head_type → low risk). |

## Confirmed clean (load-bearing clearances)

- **Joint-loss seam live & coherent**: `compute_loss` gates on `lm_loss_weight>0` → `loss = outputs.loss + lm_loss_weight*head_loss`; `==0` → `loss = head_loss` (Phase-A byte-identical else branch). `aux_target` popped BEFORE the model forward in both branches. The `>0` vs `>=0` boundary IS pinned by the λ=0 differential (`loss==head_loss` test rejects the `>=0` mutation's `outputs.loss`). (test-engineer retracted her own #44 false-alarm hedge here.)
- **Byte-identical Phase-A guarantee holds STRUCTURALLY** (architect's least-confident item, resolved): every Phase-B branch traces to a config gate — `freeze_base=true` / `lm_loss_weight==0` / `input_norm=='none'` all take the same constructions as Phase A. The `param_group→head_group` rename is cosmetic.
- **Second param-group correct & runtime-confirmed** (backend-coder instantiated the trainer, not source-read): base group = `[p for p in model.parameters() if p.requires_grad]` (PEFT-left-trainable LoRA), no explicit lr → inherits trainer LR (`param_groups[1]['lr']==1e-4`); `head_lr` isolates to group 0; Phase A = exactly 1 group. Scheduler step-count safety carries from the Phase-A clearance (`num_training_steps` is dataloader-derived, independent of param groups).
- **`end_of_prompt` coherent**: `prompt_end_indices` recovers the boundary from `labels` (-100 mask) with a single `first_completion==0` guard unifying empty-completion AND completion-first to `last_real`; clean inference fallback to `"last"` when `prompt_end_idx is None`. Device-safe.
- **`input_norm` portability complete**: `'none'` adds no submodule (byte-identical); `'layernorm'` applied after dtype-cast, before net; persisted in `save_aux_head` and reconstructed in `load_aux_head` with `resolved.get('input_norm','none')` (legacy sidecars default off).
- **Generic-engine boundary CLEAN on ADDED lines**: zero confidence/abstention/epistemic/calibration/answerability vocab across added `Trainers/**` + `tests/**`; new test names generic (`end_of_prompt`/`input_norm`/`joint_loss`/`belt`).
- **Stale-seam test retargeting correct, not a coverage weakening**: the Phase-A test asserting the stubbed seam comment was replaced by `test_aux_head_trainer_source_wires_live_joint_loss_seam` asserting the live combination — verified not a silent removal by all three reviewers.
- **b77db8d peer-reviewed at full weight** (backend-coder, fresh eyes — the test-engineer authored it): both integration tests + the source-test retarget PASS; criterion-3 RED-sensitivity independently re-proven. One FUTURE-minor: criterion-3 is coupled to param-group ORDER (assumes `[0]=head, [1]=base`); a reorder still goes RED but with a confusing message — acceptable (RED-on-drift).

## Recommendation

Merge is design-approved with **zero blockers** from all three reviewers. The one pre-merge candidate is **B-M1** — a cheap config-load coherence guard preventing a silent-wrong train mode `(freeze_base=false, lm_loss_weight=0)` that would invalidate the downstream Amendment-R faithfulness science. This mirrors the Phase-A pattern where the two cheap silent-footgun guards (M1/M2) were remediated before merge. Folding B-M1 with FOLLOW-UP #16 (same config-validation surface) is the natural scope. The remainder route to follow-ups: **#29** absorbs TE-M1 (head_lr), TE-M2 (cross-dtype roundtrip), TE-M3 (docstring), B-F1/M7 (no-decay split); the single-GC-knob loader warn folds with B-M1/#16; multi-turn boundary generalization + TE-F1/F2/F3 are logged future. CODE-phase YELLOW#1 (belt keying) is RESOLVED in favor of the unconditional belt; YELLOW#2 (belt load-bearing) stays a documented live-GPU Unsloth smoke caveat.
