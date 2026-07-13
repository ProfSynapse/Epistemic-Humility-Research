# Commitment-Point gen_stream Hook-Firing Check notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

- 2026-07-13 (HARNESS-PLUMBING FIXES, pre-relaunch): the first launch attempt
  failed on both paths, harness plumbing on both, not model results. Fixed,
  re-pinned (`bin/exp repin`, audit trail in `instrument.repins`), CPU smoke
  re-run (10/10 pytest, up from 7). No change to gates.yaml, AMENDMENT.md
  thresholds, prediction, or falsifier.

  FAILURE 1 (PATH-TUNER, `evaluate_g2`): `RuntimeError` device mismatch on
  `delta @ d64`. Root cause: `direction_unit` comes from
  `load_direction_json`, which never moves the tensor off CPU; `decode_hidden`
  entries are captured inside the forward hook and live on the model's
  device (cuda for the real run). Fixed by moving `d64` once (outside the
  per-position loop) to `on.decode_hidden[0].device`, rather than moving
  every per-position delta to CPU -- one small direction-vector transfer
  instead of many large hidden-state transfers. `evaluate_g3` was checked
  and does not have the same bug: it never touches `direction_unit`, only
  compares hidden/logit tensors that both come from the same forward-hook
  capture path and therefore already share a device.

  FAILURE 2 (PATH-BESPOKE, `assert_recording_hook_observes_poststeer_output`):
  pre-flight `AssertionError` "recording hook observed the PRE-steer output".
  DIAGNOSED before fixing, per the lead's instruction, with a standalone GPU
  probe (not committed) that registered a plain counting hook alongside the
  real ON-condition controller and ran the exact 2-new-token generate() the
  pre-flight uses: `controller._nth_call` reported 1, the independent
  counting hook fired exactly once with `seq_len=19` (the prompt length,
  i.e. the prefill call), and no seq_len==1 (decode-step) call was ever
  observed, despite `n_generated=2` confirming two tokens were genuinely
  produced. This is NOT a harness bug: it is the AK section-8 confound this
  experiment exists to certify -- Unsloth's `for_inference` optimized decode
  path bypasses the hooked module's `forward()` entirely during cached
  decode, so neither the steering hook nor any recording hook registered on
  that module can ever observe a decode step. The old pre-flight code
  compared "whatever was captured last" and treated the resulting pre==post
  equality (both readings coming from the same never-steered prefill call)
  as a construction failure, when the correct read is "there was no decode
  call to observe in the first place."

  Fixed by keying both hooks' captures by `seq_len` (so the prefill capture
  and a genuine decode capture can never be confused with each other) and
  splitting the decision into two outcomes: if no `seq_len==1` capture ever
  occurs, return a recorded, non-raising result
  (`decode_call_observed: False`) and let the run proceed -- H6-G1's own
  exact-equality-of-call-counts gate is what adjudicates this path's
  certification, not this pre-flight check. If a `seq_len==1` capture DOES
  occur but pre and post are identical there, still raise (that remains a
  genuine harness construction failure). Split the decision logic into a
  pure `_diagnose_construction_check(pre_hidden_by_seqlen,
  post_hidden_by_seqlen)` function so both outcomes are unit-testable on CPU
  with synthetic dicts (added 3 new tests: genuine non-firing does not
  raise, decode-fires-but-hooks-tie does raise, decode-fires-and-differs
  passes clean). `evaluate_g1`/`evaluate_g2`/`evaluate_g3` were checked and
  already fail closed correctly when `decode_hidden`/`decode_logits` are
  empty (the `bool(positions)` / `bool(hidden_deltas)` / `bool(logit_checks)`
  guards make an empty-list result FAIL, not a vacuous pass) -- no change
  needed there; this confound will show up as an H6-G1 FAIL for
  PATH-BESPOKE in the real run, exactly as the orchestrator's registered
  prediction expects, not as a harness crash.

  ALSO (unsolicited but confirmed present): `load_bespoke_model` passed
  `load_in_4bit=True` unconditionally and never forwarded `--revision`. The
  launch log showed Unsloth loading `unsloth/qwen3-4b-unsloth-bnb-4bit`
  instead of the pinned `unsloth/Qwen3-4B`. Confirmed via
  `inspect.signature(FastLanguageModel.from_pretrained)` that `revision` is
  a real, passed-through kwarg. `load_in_4bit=True` is what triggers
  Unsloth's silent substitution of its own pre-quantized mirror for a plain
  base-model name; `load_in_4bit=False` avoids the substitution entirely
  (the unquantized 4B model fits the 24GB 3090 easily, so there is no
  memory reason to accept it) and is truer to cell.yaml's bf16 pin than
  trying to force `use_exact_model_name=True` while keeping quantization.
  Fixed: `load_bespoke_model(model_name, revision=None)` now passes
  `revision=revision, load_in_4bit=False`; `main()` forwards `args.revision`.

- 2026-07-13 (LAUNCH-TIME RESOLUTION, pre-launch): the three cell.yaml
  PLACEHOLDERs left open at sign are resolved from the ak-artifact-scout's
  locate report, lead-verified against the artifacts. No gate, threshold,
  prediction, or falsifier text changed; experiment.yaml's cell.yaml pin is
  re-computed to cover the resolution (old
  2880140afb33fbb4fe86292831e8109984ab0137be39aed0c1812936c5591791, new
  2d6bf0e3273d3f223a55b8405401c97ebe1ecb1000fd607df3ade81fc07d76a3).
  (1) revision: unsloth/Qwen3-4B main =
  64033659d5caf1b8ed7f929b29de705e93a4d468, unchanged on the Hub since
  2025-05-13, so this is also the snapshot the AK Stage 2 run drew from.
  Fidelity note recorded in cell.yaml: the AK cloud run actually loaded the
  unsloth/Qwen3-4B-bnb-4bit quantized variant (modal_ak_stage2.py:61); H6
  runs the unquantized base. Hook-firing semantics, not AK's numbers, are
  under test, so this is a scope note for the Outcome, not a gate concern.
  (2) direction: AK Stage 2 commitment-perp direction.json, sha256
  9e0bf40c... (full hash in cell.yaml), lead-recomputed against the file;
  staged gitignored at directions/ak_stage2_direction.json. (3) pool: first
  25 unique row_keys in appearance order of the AK matched-run rows.jsonl
  (deterministic, lead-derived, matches the scout's list); question text
  joined at launch from staging pools/ak_stage1_pool.jsonl (all 25 resolved)
  into gitignored analysis/pool_smoke.jsonl, ID-only manifest at
  analysis/pool_smoke_ids.json for promotion at resolve. Two corrections to
  the scout's report, recorded for provenance hygiene: the staging
  ak-stage2-raw-base-r1/data/rows.jsonl does NOT contain question text (0 of
  4,592 rows; text lives in pools/ak_stage1_pool.jsonl, which is what
  modal_ak_stage2.py actually feeds --pool), and the matched-run rows file
  holds 328 unique row_keys, not 25 (the 25 is the smoke subset). Import
  smoke re-run post-submodule-init in this worktree: h6_hook_check.py
  imports both path classes cleanly under base conda python3 (which carries
  unsloth for PATH-BESPOKE).

- 2026-07-13 (SIGNED, pre-launch): Signed after lead review of the built
  harness (commit 93bda177; CPU smoke re-run by the lead under pytest, 7/7
  both paths; note the smoke is pytest-style and a bare python3 invocation
  exits 0 silently without running anything, so always run it via
  python3 -m pytest). gates.yaml was transcribed from AMENDMENT.md
  thresholds verbatim pre-sign (was a placeholder). Builder adjudications
  reviewed and accepted, recorded here so the Outcome inherits them:
  (1) PATH-BESPOKE's GenerationHookController is source-extracted from the
  archived steering_common.py because that module's import chain broke in
  the paper-reorg migration; the extraction is the exact class source with
  no runtime dependency on the broken imports, and SteeringHook imports
  unmodified. (2) PATH-TUNER's NOOP condition uses force_active=True at
  strength 0.0 so the real clone/add code path is exercised, not the
  inactive-row early-exit. (3) PATH-BESPOKE's NOOP is a structural identity
  with ABSENT by construction (its controller short-circuits at alpha==0
  before touching the hidden state), so add-zero perturbation is untestable
  on that path as written; its G3 pass is legitimate but weaker, and the
  Outcome must say so. (4) H6-G1's decode-call count reads HF cached
  generate() semantics: N new tokens = 1 prefill + N-1 decode-only calls,
  and both controllers' gen_stream mode skips the prefill, so the exact
  expectation is N-1 steered calls. Launch: local RTX 3090 after the H4 run
  frees the card; GPU minutes for both paths.

- 2026-07-13: harness built (`h6_hook_check.py`) implementing the AMENDMENT's
  Design/Measurement/Gates against both real path classes (PATH-BESPOKE:
  `confidence_steer.SteeringHook` + `steering_common.GenerationHookController`
  extracted by source since that module's own import chain is broken against
  the current repo layout, see the harness module docstring; PATH-TUNER:
  synaptic-tuner `MechInterp.intervention.InterventionHook` +
  `GenerationInterventionController`, unmodified). `gates.yaml` filled in
  (was a placeholder) by transcribing AMENDMENT.md's H6-G1..G4 thresholds
  verbatim, no new numbers. CPU smoke (`test_h6_smoke.py`, 7 tests) run
  against a tiny from-scratch plain-HF GPT2 model (no download, no GPU):
  ALL PASS for both paths' harness code, plus the existing tuner regression
  suite `synaptic-tuner/tests/mech_interp/test_gen_stream_firing.py` (6
  tests, pre-existing, not modified) cross-checked green. No GPU load
  performed; PATH-BESPOKE's real confound (Unsloth `for_inference`) is
  untestable on CPU by construction and remains open pending the real-model
  run. See the build report for adjudications made during construction
  (off-by-one in decode-call counting, PATH-BESPOKE's structural NOOP
  short-circuit, prompt-rendering scope for the real-run CLI).
