# PR #120 Review — `aux_head` prompt_completion render mode + CLI coherence guard

- **PR**: ProfSynapse/Synaptic-Tuner #120 — `feat(sft): aux_head prompt_completion render mode + shared coherence guard`
- **Branch**: `feature/aux-head-prompt-completion-render` → `main` (submodule PR only; root-repo submodule-pointer bump is a separate later commit — tracked task #30, now covering PR #119 + this PR)
- **Commit**: `3317667` (15 files, +1063/-23) — bundle of #68 (render mode + CLI flags + runner forwarding + skill doc), #72 (Finding-A remediation: shared `validate_aux_head_coherence`), #74 (debug-print hygiene)
- **Spec**: `docs/sessions/0029 - phase-b-token-faithfulness-fix-handoff.md` (self-contained PREPARE + approved ARCHITECT `docs/architecture/aux-head-prompt-completion-render.md`)
- **Reviewers**: architect (#76, design coherence — independent/authoritative) · test-engineer (#78, coverage — fresh full-PR lens) · backend-coder (#80, implementation — adversarial self-review, runtime-weighted)
- **Date**: 2026-06-29

## Verdict

**APPROVE — no blocking findings from any reviewer.** architect: APPROVE; test-engineer: 🟢 GREEN; backend-coder: PASS. The prompt_completion render branch faithfully realizes the #66 design contract (D1 ownership with the "replaces the assistant_only masking region" rationale; D2 derived-eos terminal, improved with an `_encoder→tokenizer` fallback for Processor wrappers, loud-if-None) and the lead's WARN-vs-ERROR ruling. The default `prompt_render="full_conversation"` path is byte-identical (asserted at full `to_dict()` value identity); the generic-engine vocabulary boundary is clean on all added lines.

One cheap lane-parity guard (**A-M1**) is the single pre-merge remediation candidate — it completes the CLI/YAML parity intent that this PR's own Finding-A remediation (#72) began. Everything else routes to follow-up #29 or is logged future/nit.

## Lead-flagged verification targets (both CLEAN)

| Target | Reviewer | Resolution |
|---|---|---|
| **Call-site staleness** of `validate_aux_head_coherence()` (does it read post-CLI-override config?) | architect (independent grep) + backend-coder (source) | **CLEAN.** Guard reads `{enabled, freeze_base, lm_loss_weight, out_activation, loss}`, all set by the override block at `train_sft.py:681-703`, immediately before the call at `:711-715`. Zero mutation of `config.aux_head.*` / `config.training.prompt_render` after `:703`; later lora/model overrides touch only `config.lora`/`config.model`. |
| **WARN guard location + non-escalation** | architect + backend-coder | **CLEAN.** WARN guard (`:919-935`) is a distinct `print()`-only block reading the truly-final config (`:914`), never raises; the legitimate `end_of_prompt + full_conversation` combo only warns. Distinct from the RAISING `validate_aux_head_coherence`. |

## Cross-reviewer convergence

| Topic | architect | test-engineer | backend-coder | Resolution |
|---|---|---|---|---|
| **`hidden_dims` missing from CLI/runner surface** | A-M2 (Minor, silent-wrong) | (forwarding coverage GREEN; gap not surfaced as defect) | R1 (Minor, NEW, runtime-confirmed via probe 2) | **DOUBLE-confirmed** (architect by design-trace, backend-coder by runtime probe). `head_type='mlp'` recipe on the flag-only lane silently degrades to `hidden_dims=[]`. **No headline impact** (headline path is `head_type='linear'`). → **#29** (non-default-knob hardening, with M5). |
| **CLI handler forwarding has executed (not just structural) coverage** | (forwarding byte-identical-when-absent confirmed by design) | GREEN — `_compile_local_command` drives the REAL `LocalRunHandler._compile` (non-mocked seam); both tri-state directions + falsy-scalar + absent-path asserted | GREEN — probe 2 (11/11) via the real `_build_trainer_command` | **Green-by-omission risk CLOSED** by two independent executed checks. |
| **Fully-truncated-prompt → all-(-100) labels** | A-F2 (future/nit) | covered (truncation assertion at TEST) | R2 (Nit) | **Shared right-trim contract property, NOT a new defect.** Accept as-is; optional future warn. |

## Blocking

None.

## Minor

| ID | Source | Finding | Disposition |
|---|---|---|---|
| **A-M1** | architect (unique) | **Layer-presence lane asymmetry.** `validate_aux_head_coherence()` omits the "enabled requires layer" check (it stayed in `load_aux_head_config`). The local-runner lane builds the trainer command from FLAGS ONLY with no config file (`local_run_handler._build_trainer_command:692`), so `load_aux_head_config` never runs on that lane. A recipe enabling aux_head whose `layer` doesn't reach the flags → `enabled=True, layer=None` passes the shared validator and crashes **late + cryptic** at `hidden_states[None]` → TypeError, where the YAML lane raised **early + descriptive** ValueError. On the PRIMARY runner lane. Severity MINOR (loud, not silent) — but it is the **same CLI/YAML asymmetry class Finding A (#72) set out to close** (which folded 2 of 3 YAML guards into the shared validator and left layer-presence behind). | **PRE-MERGE candidate (lead concurs).** Add a `layer` param to `validate_aux_head_coherence`, check `enabled and layer is None → raise`, pass `config.aux_head.layer` at the `:711` call site; `load_aux_head_config` delegates its layer check too → both lanes raise identically. Completes the Finding-A parity intent. Mirrors Phase A M1/M2 + Phase B B-M1 pre-merge precedent. |
| **A-M2 / R1** | architect + backend-coder | **`hidden_dims` missing from CLI surface** (see convergence table). | → **#29.** Add `--aux-head-hidden-dims` + forward, OR loud-guard `mlp`-without-`hidden_dims`. Bites only non-default `head_type='mlp'`. |

## Coverage gaps (test-engineer, all MINOR → #29)

| ID | Finding | Production behavior |
|---|---|---|
| G1 | empty-completion (`content==''`) untested | graceful: `completion_ids = [] + [eos] = [eos]` |
| G2 | multi-turn `prompt_completion` input untested | clean single-boundary by construction (`messages[:-1]` → masked prompt, final assistant = completion) |
| G3 | non-string-content ValueError loud-fail untested | sibling of the COVERED eos-raise; cheap `pytest.raises` |

Residual (not new, not blocking): `train_sft.run()`'s argparse→override→validate glue is source-asserted only (unsloth blocks in-process import) — but both the shared validator AND the handler forwarding are executed-tested, so only the thin wiring is structural. Same class as PR#118 M4.

## Future / Nit

| ID | Source | Finding |
|---|---|---|
| A-F1 | architect | `prompt_completion` + non-assistant-final row silently renders `full_conversation`. As-DESIGNED (correct for assistant-final SFT rows); note only. |
| A-F2 / R2 | architect / backend-coder | Fully-truncated prompt → all-(-100) labels (zero loss). Shared right-trim property; consistent with full_conversation. Optional future warn. |
| R3 | backend-coder (runtime) | Mid-completion truncation silently drops the derived-eos terminal (`input_ids[-1] != eos` when `max_seq_length = len(prompt)+1`). Judged ACCEPTABLE / by-design: universal SFT right-trim contract (full_conversation drops its trailing eos the same way), NOT silent at the data layer (`truncation_applied=True` surfaces every cut row), and the row still carries real completion LM-loss labels. prompt_completion nuance: the derived terminal is appended LAST → first trimmed, so marginally more prone to terminal-loss than a full render. **No task** — optional doc note (max_seq_length should comfortably exceed max(prompt+completion) for aux_head rows; or warn/drop `truncation_applied` rows) folds into #29 if pursued. |
| A-N1 | architect | `data_loader.py` debug prints rephrased (`Tokenized→Encoded`) for the secret-scanner false positive (#74); function name `load_and_prepare_tokenized_dataset` + `dataset_representation='tokenized'` unchanged → cosmetic terminology mismatch. Harmless. |

## Confirmed clean (load-bearing clearances)

- **D1 ownership**: `prompt_render` on `SFTTrainingConfig` with the exact "REPLACES the assistant_only masking region" field-comment rationale; default `full_conversation`.
- **D2 terminal**: derived `tokenizer.eos_token_id` with `_encoder→tokenizer` fallback (handles Processor wrappers), loud-raise if None; terminal carries a real label — implements AND improves on the contract.
- **Byte-identical default**: render-branch early-return precedes the UNTOUCHED full-conversation path, gated on the non-default flag AND assistant-final turn; `prompt_render` threads at all 5 hops defaulting to `full_conversation`; test asserts full `to_dict()` VALUE identity (strictly stronger than PR#118 F1's column-name-only assertion).
- **template_kwargs / enable_thinking**: forwarded verbatim into the prompt-half render (identical to full-conversation); completion encoded raw — no new divergence axis.
- **Runner byte-identical-when-absent**: aux_head block forwarded only when `isinstance(dict)`; `_append_bool_flag` tri-state (None=omit / True=`--flag` / False=`--no-flag`); `prompt_render` forwarded independently.
- **`validate_aux_head_coherence` extraction**: module-level, disabled→no-op, phase + prob-loss guards preserved verbatim; `load_aux_head_config` delegates (YAML lane byte-identical); both lanes raise on the `(false, 0.0)` corner at runtime.
- **Non-mocked seam coverage**: `_compile_local_command` drives the real `LocalRunHandler._compile`; forwarding tests are executed, not structural.
- **Non-vacuity**: `_DivergingTokenizer` deliberately diverges the two render modes; `test_full_conversation_boundary_is_not_the_generation_anchor` is the explicit contrast guard against template-divergence collapse.
- **Generic-vocab boundary**: CLEAN on all added source/test/skills lines (zero confidence/abstention/epistemic/answerability/calibration/domain vocab).
- **Test cardinality (author-blindness recount)**: 25 net-new test functions; the "7-guard" reconciles exactly to 7 parametrized `validate` cases (2+2+2+1). 78 passed, 1 skipped (RUN_LIVE_HUB live-Qwen3 render assertion, correct on CPU).

## Recommendation

Merge is design-approved with **zero blockers** from all three reviewers. **One pre-merge remediation recommended: A-M1** — a cheap `layer`-presence parameter on `validate_aux_head_coherence` so the flag-only runner lane enforces layer-presence identically to the YAML lane, completing the Finding-A (#72) parity intent this PR began (and matching the Phase A / Phase B pre-merge-guard precedent). A-M2/R1 (`hidden_dims`) + the three futures/nits route to **#29** / logged future. Root-repo submodule-pointer bump remains separate (**#30**).
