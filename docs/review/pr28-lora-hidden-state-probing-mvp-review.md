# Peer Review Synthesis — PR #28 (LoRA hidden-state probing MVP)

> Reviewed at commits 73d90c92 (CODE) + ac9443d2 (TEST) on branch `lora-hidden-state-probing-mvp`.
> Reviewers: architect (#29), test-engineer (#30), backend-coder (#31). Suite GREEN: 95 passed / 5 skipped.
> Synthesized by team-lead, 2026-06-14.

## Verdict

Strong, plan-faithful implementation — verbatim signed-render extraction (Decision A, byte-identical, counter-test-by-revert verified), correct SoC across the 4-file split, faithful leakage-by-key discipline, and a clean crash-safe lifecycle in schema. **One Blocking root theme** blocks merge: the D-bis crash-safe/provenance discipline is correctly *built* in `hidden_state_schema.py` but *not wired through* the harness finalize path, so a real `status=ok` run would write `verified=True` over a ~25-field-None provenance manifest. Two independent reviewers converged on this — including the architect who designed Decision D/D-bis (their own assumption "verified flips only after a real check" falsified).

## Findings

| # | Finding | Severity | Reviewer(s) |
|---|---------|----------|-------------|
| B1 | Config provenance key mismatch: yaml declares `provenance:` (line 91), `build_manifest` reads `config.get('manifest_provenance')` (schema.py:348). Keys never match → every config-sourced provenance field silently `None`. | **Blocking** | architect (corroborates backend-coder R1) |
| B2 | D-bis finalize gate is dead code: `validate_manifest(require_populated=True)` never called (only call site uses default `False`). `_assert_populated` never runs; combined with `_verify_emitted` returning True on shard-existence, a real `status=ok` run sets `verified=True` over None provenance. The GPU-free test (line 80) asserts that broken state and passes. | **Blocking** | architect + backend-coder (R1) |
| B3 | Runtime provenance fields (base/adapter hashes, peft/transformers versions, lora rank/alpha/dropout/target_modules, tokenizer_revision) never patched by `TransformersPeftBackend`; `data_sha256` never computed. Substance behind B2 — surfaces once the finalize gate is wired. Breaks the version-diagnostic the README promises for the #1 first-GPU-run risk. | **Blocking** (bundled w/ B2) | architect (MINOR-1) + backend-coder |
| M1 | `extraction.layer_list` advertised in config + manifest but never consumed — always persists ALL layers. Harmless at default `null`; a future `[10,20]` would silently persist all layers under a manifest claiming the subset. | Minor | backend-coder (R2) |
| M2 | `resolve_eval_arm_adapters` mirror-resolution path untested. Prod config sets `eval_arms_source` (yaml:69); every test sets it `None` → the primary by-value adapter-resolution path is green-by-omission. | Minor | test-engineer (MINOR-1) |
| M3 | `persist_delta=False` branch untested (all configs use `True`). | Minor | test-engineer (MINOR-2) |
| M4 | safetensors round-trip is `importorskip`-gated though `requirements-hidden-state.txt` already declares numpy+safetensors mandatory for tests — make them hard test requirements to match the stated contract. | Minor | test-engineer + lead ruling |
| F1 | Deferred GPU-smoke `h_base != h_lora` numeric confound guard (Decision E tier 2) is an empty skipped test body AND absent from the real backend path. Acceptable to defer, but it is the ONLY guard against a silent `h_base==h_lora` confound — promote to a hard first-GPU-run gate, not an indefinite skip. | Future | architect (FUTURE-1) + backend-coder (R3) |
| F2 | Render parity anchor compares `render_probe_prompt()` vs `VLLMBackend._render_prompt()` but both drive the same stub — no independent oracle. Near-zero risk (wrapper-over-helper; counter-test-by-revert confirmed coupling). Note only. | Future | test-engineer (FUTURE-1) |
| F3 | Two defensive branches untested: `_verify_emitted` False path; `_select_keys` n=None early-return-all. Low-value defensive code. | Future | test-engineer (FUTURE-2) |

## Confirmed clean (against the diff, not on trust)

- Signed `backends.py` byte-identical: verbatim `_RENDER_MODES` order, self-check relocation 1-for-1, `enable_thinking=True` skips discovery; locked by 6 render-regression tests.
- Leakage-by-key: `select_matched_slice` aligns by `probe_pool_row_key` only, streams `probe_results.jsonl`, raises on missing key — no loose-text path.
- Persist/dtype: `contiguous().cpu()`, string-only safetensors metadata, explicit fp32 cast (no silent cast, no compression).
- Crash-safe lifecycle: launched-before-forward, failed-on-exception-then-reraise, verified only after shard check.
- GPU-only deferrals SOUND: all 5 skips structurally require a model load; documented as first-run gates.

## Remediation plan

- **Blocking bundle (B1+B2+B3)** — one coherent fix touching `config/hidden_state_probe.yaml`, `hidden_state_probe.py` (finalize wiring + runtime provenance patching), and `hidden_state_schema.py` (if needed). Fixer: backend-coder (owns harness, traced it). Architect validates gate placement. Test-engineer authors the negative finalize-gate test + fixes the line-80 test that encodes the bug.
- **Minors** — pending user decision (recommend bundling all four into the same cycle; M1/M2 substantive, M3/M4 cheap).
- **Futures** — pending user decision (recommend GitHub issue for F1 as a first-GPU-run gate; note/skip F2; skip-or-defer F3).
