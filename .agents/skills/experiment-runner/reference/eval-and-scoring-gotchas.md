# Eval And Scoring Gotchas

Read for live eval, prompt/output contracts, scorer drift, and post-eval sanity checks.

- Qwen3 prompt rendering can look thinking-off while generated answers still
  contain `<think>...</think>`. Treat any generated thinking tags in
  `probe_results.jsonl` as contaminated output: stop the container, archive the
  output directory, and retry only after the generated-output guard fails before
  writing rows or the backend suppression path is fixed. Do not strip tags and
  continue.

- For Phase 1 eval generation, prompt rendering with thinking disabled is not
  sufficient by itself. When `generation.enable_thinking: false`, vLLM
  `SamplingParams` receives `<think>` and `</think>` stop strings while
  preserving any configured `generation.stop` values. The generated-thinking
  guard remains a backstop; do not strip contaminated outputs.

- Thinking-on evals are a separate explicit comparison condition, not a
  replacement for the default non-thinking measurement posture. Use derived
  configs with `generation.enable_thinking: true` and a separate `results_dir`;
  the harness then omits the `<think>` stop strings and records
  `enable_thinking: true` on scored rows. Keep confidence coverage as a gate:
  the parser accepts final JSON after an explicit `</think>` suffix, but plain
  malformed prose should remain unparsed. A 2026-06-20 192-row base SelfAware
  smoke returned 100% confidence coverage, no visible think tags in generated
  rows, unchanged low refusal rates versus non-thinking, slightly lower
  truthful/correct-on-known, and higher mean stated confidence.

- Phase 1 local eval now has an opt-in live vLLM path:
  `python experiment/phase1/eval/run_eval.py --config <scoped-config.yaml>
  --live-vllm`. Default fixture behavior is unchanged. The live config must use
  explicit `model_name` for the loadable HF/vLLM repo id and `model_tag` only as
  the reporting label. Use scoped same-model configs first; base/SFT/DPO and
  local KTO seed 1 have completed Qwen3-4B adapters, while bridge arms are a
  different base model.

- The scoped local 4B eval smoke config pins `vllm.max_lora_rank: 32` because
  the completed SFT/DPO adapters are LoRA rank 32. If running that checked-in
  config inside Docker/Linux from this Windows workspace, translate the
  Windows absolute adapter paths to container-visible paths or mount the
  workspace equivalently before launch; the eval loader preserves absolute
  adapter paths as written.

- After every eval, do a quick plausibility pass before accepting the result:
  compare each arm against its nearest controls, prior seeds, and expected
  directional behavior. Large surprises are allowed as hypotheses, but they are
  first treated as an audit trigger. Check lineage, adapter/base paths, merged
  checkpoint health, generation samples, scorer/refusal phrase alignment, and
  config parity before writing the scientific interpretation. This should be
  general: if an arm that should be SFT-warmed suddenly looks base-like, or a
  control moves far outside its peer runs, pause and run a bounded sanity check
  rather than explaining the outlier from the headline metrics alone.

- Amendment B stated-confidence reruns are prompt-contract evals, not plain
  rescoring. The JSON-only instruction belongs in each eval YAML under
  `prompt.system`; do not mutate old result directories or reuse old configs
  unchanged. Keep outputs labeled as Amendment B stated-confidence reruns,
  use the strict answer/confidence parser as the coverage gate, and set
  `generation.stated_confidence_json_retries` deliberately when live generation
  should retry malformed JSON. A retry reduces accidental format loss, but it is
  still measurement-affecting provenance; inspect `stated_confidence` coverage
  and retry counts before treating the metrics as comparable. Also check a small
  base-model slice before full reruns: on 2026-06-17 an over-strong JSON prompt
  achieved 100% coverage with zero retries but induced massive prompt-only base
  over-refusal, so coverage alone is not enough.

- SelfAware is ordered with known rows first and unknown rows later. A simple
  `limit: 64` smoke only tests known-row behavior; it does not exercise
  abstention/refusal recall. For SelfAware smoke coverage, either run full eval
  or pair a known-block smoke with an unknown-block smoke (the 2026-06-22 local
  dataset had the first unknown row at offset 2337). Record the offset in the
  config and session note rather than relying on memory.

- Response-confidence GRPO evals can pass schema perfectly while still failing
  confidence learning. The 2026-06-22 SFT JSON-bridge -> GRPO full SelfAware
  eval had 100% answer/confidence JSON coverage and zero retries, but both arms
  emitted `confidence: 1.0` on every row. Treat this as degenerate confidence,
  not calibrated confidence; inspect unique confidence values and row-level
  behavior transitions before interpreting stated-confidence metrics.

- Do not seed a calibrated-confidence experiment with a bridge target that
  emits endpoint confidence on every supervised row. The 2026-06-22 SFT JSON
  bridge used `confidence: 1.0` for both known gold answers and unknown
  abstentions; the resulting SFT control and downstream GRPO adapter then
  emitted 1.0 for every SelfAware row, even under higher temperature, a
  stronger scale prompt, and no structured-output grammar. Before scaling a
  confidence-learning run, smoke-test unique confidence values and reward sanity
  cases for both behavior and confidence endpoints. Prefer non-endpoint target
  bands for appropriate responses, low-confidence bands for inappropriate
  responses, and explicit penalties or zero credit for exact 0.0/1.0 endpoints
  when the research question is calibrated expression rather than deterministic
  correctness.

- For schema-trained response-confidence runs, prefer the explicit
  `response_confidence` key over generic `confidence`. The intended scalar is
  "probability that this answer or abstention is the appropriate response": high
  for correct known answers, high for correct unknown abstentions, low for wrong
  answers and over-refusals, and middle for model-specific ambiguous rows. Keep
  historical Amendment B `confidence` outputs parseable, but label new runs so
  answer-confidence and response-confidence are never pooled silently.

- Amendment B can also expose scorer drift in the opposite direction: JSON answer
  text may contain natural abstentions like "I do not know the exact number"
  rather than the Cheng fixed phrase "I do not know the answer." Do not broaden
  the legacy Cheng `is_refusal` path if the bridge regression moves; keep it
  byte-stable and add JSON-aware stated-confidence refusal handling with tests
  that cover both the natural abstention and the Cheng regression.

- Amendment B structured-output schemas still need behavioral smoke tests, not
  only parser coverage. A 2026-06-17 base-only SelfAware smoke with an explicit
  `decision: answer|abstain` enum achieved perfect structure
  (`stated_confidence.coverage_pct=100.0`, no retry exhaustion, all abstentions
  canonicalized to "I don't know") but induced large base over-refusal
  (`over_refusal_pct=37.11` on the 192-row slice where the neutral-concise
  comparator had 0.0). Treat explicit abstain enums as measurement-affecting
  until a base-slice behavioral comparator clears them. This is a general
  instrumentation lesson: making abstention schema-visible can steer the model
  toward over-abstention even when the prompt says to preserve normal behavior.
  Prefer a control that constrains JSON shape without exposing an abstain option
  if behavior must match the plain-answer baseline.

- The follow-up answer/confidence-only structured-output control on the same
  192-row base SelfAware slice preserved the intended behavior much better:
  `stated_confidence.coverage_pct=100.0`, retry exhaustion 0,
  `over_refusal_pct=1.03`, and `refusal_rate_pct=1.04`. Use this as the
  preferred Amendment B measurement posture unless a later base-slice smoke
  falsifies it. The durable rule is: any output contract that names abstention
  as an explicit option is a behavioral intervention until proven otherwise.

- Structural validation of a merged SFT checkpoint is not sufficient after any
  nonzero merge exit, OSError, or memory/flush warning. On 2026-06-16, the
  seed2 merged SFT directory had `config.json`, two readable safetensor shards,
  and a plausible index, but a 192-row SelfAware behavioral sanity eval of the
  merged model alone produced refusal_recall 6.32, over_refusal 4.12, and
  truthful 12.5, while the adapter-on-base SFT seed2 full eval had
  refusal_recall 87.4. Treat such merges as semantically failed until a tiny
  merged-base live eval confirms the expected SFT refusal behavior. Do not use a
  suspect merged SFT checkpoint as the base for sequential `SFT -> DPO` or
  `SFT -> KTO`; rebuild/merge with a lower-memory path first.

- OOD records carry their own `aliases`; scoring now prefers normalized
  non-empty record aliases and falls back to global Cheng gold. Without this,
  OOD known correctness/truthful vectors could be wrongly zero when questions
  are absent from Cheng gold.

- Non-blocking warnings seen in local diagnostics: Triton routing module
  warning, AOT cache save/HF cache metadata permission warnings, and NCCL
  `destroy_process_group` shutdown warning.
