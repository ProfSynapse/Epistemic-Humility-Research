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

- Eval-set keys are canonical loader IDs, not arbitrary slice labels. The OOD
  loader accepts keys such as `selfaware`, `kuq`, `popqa`, and
  `sycophancy_answer`; a config key like `selfaware_unknown_smoke` fails before
  generation. To smoke both known and unknown SelfAware behavior, either use the
  canonical `selfaware` key with a mixed offset/limit (for example offset 2240,
  limit 192) or run separate config files, not multiple invented SelfAware keys
  in one YAML.

- Response-confidence GRPO evals can pass schema perfectly while still failing
  confidence learning. The 2026-06-22 SFT JSON-bridge -> GRPO full SelfAware
  eval had 100% answer/confidence JSON coverage and zero retries, but both arms
  emitted `confidence: 1.0` on every row. Treat this as degenerate confidence,
  not calibrated confidence; inspect unique confidence values and row-level
  behavior transitions before interpreting stated-confidence metrics.

- Reward refusal detection must cover semantic abstentions, not only the
  canonical Cheng phrase. During the 2026-06-22 schema-SFT->GRPO full launch,
  reward-debug rows showed unknown completions like "I'm really not sure what
  the answer is, so I'd rather not guess" receiving the hallucination penalty
  because the reward only matched narrower forms such as "I don't know" and
  exact "I am not sure what the answer is". A first retry exposed the same
  issue for indirect forms such as "NONE OF US KNOW THE ANSWER", "How can I
  know the answer?", and "I can't answer reliably." Treat reward-debug row
  inspection as an early-run gate for every new reward contract: if natural
  abstentions are penalized on unknown rows or rewarded on known rows, stop and
  fix the reward before spending a full run. Regression tests should score each
  accepted abstention as rewarded on unknown rows and penalized as over-refusal
  on known rows.

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

- Schema-SFT can learn the output envelope while still collapsing the scalar.
  The first Amendment D schema-SFT seed-1 SelfAware smoke had 100% JSON
  coverage and no exact endpoints, but every row emitted
  `response_confidence: 0.8`, matching the dominant desirable SFT target. Always
  inspect unique confidence values and band counts before interpreting
  response-confidence metrics; DPO/KTO/GRPO or additional supervised contrast
  is needed to test whether the scalar can carry calibrated signal.

- Before retraining a schema response-confidence SFT model, inspect the training
  target histogram, not only the eval histogram. The failed Amendment D dataset
  had 14,395 ordinary SFT rows at exactly `response_confidence: 0.8` and only
  548 ambiguous-middle rows in `[0.4, 0.6]`, so a constant-0.8 model was a
  target-construction failure. For probe-scaled reruns, derive targets from the
  original 32-sample probe: estimate factual confidence with smoothed
  `p_correct`, use `1 - factual_p` for abstentions, and map to non-endpoint
  response-confidence bands before launching training.

- A target can be non-constant and still be effectively modal. On 2026-06-23,
  the first probe-scaled schema-SFT dataset had 20 target values, but
  `response_confidence: 0.8765` was 12,222 / 14,943 rows (81.79%). The full SFT
  run completed and the mixed SelfAware smoke had 100% JSON coverage, but every
  eval row emitted `0.8765`. Treat dominant target frequency as a preflight
  gate alongside unique-value count; if one scalar is the easy loss minimum,
  add balanced/bin-capped SFT projection or another contrastive calibration
  stage before spending downstream DPO/KTO/GRPO time.

- Keep the SFT/preference boundary explicit in response-confidence experiments.
  The preferred mainline SFT dataset should teach only appropriate completions
  plus the output schema and broad confidence bands: correct known answers,
  correct unknown abstentions, and ambiguous-answer middle-confidence rows.
  Rejected completions, hallucinated answers, and known-question over-refusals
  belong in DPO/KTO/GRPO unless the run is deliberately labeled as an
  exploratory contrastive-SFT diagnostic. If SFT is built from both chosen and
  rejected DPO rows, record that it is no longer a clean format/style SFT
  control before interpreting downstream results.

- Exploratory contrastive SFT can prove the scalar is movable while still being
  behaviorally bad. On 2026-06-23, an interrupted contrastive
  response-confidence SFT checkpoint at step 1500/2934 produced 31 unique
  `response_confidence` values on a 192-row mixed SelfAware smoke
  (`coverage_pct=99.48`, mean confidence 0.4567), but behavior regressed
  (`correct_on_known_pct=17.24`, `over_refusal_pct=40.21`). Treat this pattern
  as evidence against constant-scalar inevitability, not as a green light to
  continue the branch. Move rejected completions back into DPO/KTO/GRPO and use
  a clean SFT base for the mainline.

- A completed GRPO run can move the refusal boundary without solving confidence
  expression. The 2026-06-23 schema-SFT->GRPO seed-1 full SelfAware eval
  preserved 100% JSON coverage and reduced unknown answering, but every row
  still emitted `response_confidence: 0.8` while known-row over-refusal rose.
  Post-GRPO acceptance checks must compare unique confidence values, unknown
  answering, known over-refusal, and row samples against the nearest control;
  do not call a run calibrated because reward training completed cleanly.

- Reward-grid preflight is necessary but not sufficient for confidence-learning
  claims. A reward can have the right offline ordinal ordering and a healthy
  nonzero-variance GRPO run while the trained model still emits high,
  behavior-insensitive confidence. After any confidence-reward GRPO eval,
  report confidence by behavioral cell: known-correct, known-wrong,
  known-over-refusal, unknown-abstention, and unknown-answer. If those means are
  clustered together, treat the scalar as style or policy confidence, not
  calibrated response appropriateness, even when coverage is 100% and unique
  confidence values are nonzero.

- A preference adapter must be evaluated on the same base family it was trained
  from. On 2026-06-23, an initial clean schema-SFT->DPO seed-1 192-row smoke was
  launched with `model_name: unsloth/Qwen3-4B-bnb-4bit` even though the DPO
  adapter lineage showed it was trained from the merged clean-SFT checkpoint.
  The smoke produced a severe confident-abstention pattern, but that result is
  confounded by the base/adapter mismatch and must not be interpreted as DPO
  objective evidence. Before accepting any sequential SFT->DPO/KTO/GRPO eval,
  check `training_lineage.json` and verify that `model_name` equals the trained
  base checkpoint while `adapter` points to the follow-on adapter. Then compare
  against the nearest SFT base on known over-refusal, unknown answering, answer
  text concentration, and confidence concentration.

- Preference tuning can be behaviorally inert while increasing stated
  confidence. After correcting the base mismatch above, the 2026-06-23 full
  clean schema-SFT->DPO seed-1 SelfAware eval was nearly flat against the merged
  clean-SFT baseline (`truthful_pct` 40.58 -> 40.69,
  `answer_on_unknown_pct` 12.98 -> 12.89, `over_refusal_pct` 57.51 -> 56.18)
  but raised mean `response_confidence` from 0.7485 to 0.8121 and worsened
  response-appropriateness Brier score. Treat higher stated confidence as a
  separate outcome, not an improvement. If DPO/KTO/GRPO moves confidence more
  than behavior, report it as confidence amplification or style regularization
  unless calibration metrics improve relative to the nearest SFT baseline.

- KTO reward separation is not behavioral validation. On 2026-06-23, clean
  schema-SFT->KTO seed 1 trained cleanly from the merged SFT base and reached
  strong preference separation near the end of training (`rewards/margins`
  around 16-18), but full SelfAware eval moved the wrong tradeoff: unknown
  answering rose 12.98 -> 18.99, known over-refusal fell 57.51 -> 52.37,
  correct-on-known fell 47.23 -> 44.03, truthful fell 40.58 -> 39.36, and mean
  confidence rose 0.7485 -> 0.8527. Treat this pattern as "less refusal plus
  higher confidence", not better epistemic humility. Always run the corrected
  base eval and inspect unknown answering, known over-refusal, answer text
  concentration, and confidence concentration before calling KTO useful.

- SelfAware `correct_on_known_pct` is conditional on answered known rows, not
  all known rows. A more selective model can raise this metric simply by
  refusing many hard known questions. Always read it with `over_refusal_pct`,
  `answered_known`, `correct_known`, and `truthful_pct`; if answered-known
  accuracy rises while truthful rate is flat or lower, report that as selective
  answering plus over-refusal, not a broad knowledge improvement.

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
