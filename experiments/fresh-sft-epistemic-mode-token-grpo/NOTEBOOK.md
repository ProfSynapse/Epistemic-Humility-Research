# Fresh-SFT Epistemic Mode Tokens (Stage S): notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and machine state in
`experiment.yaml`.

## Entries

### 2026-07-23: corrected dev qualification stage-s-dev-20260723-rerun-f6f1229 VALID; falsifier fired; experiment resolved falsified

- Re-ran the full 3,010-generation dev qualification on the repaired tuner
  (`f6f1229`), fresh run id `stage-s-dev-20260723-rerun-f6f1229`, same
  hash-bound arguments, pinned runtime, seed 20260722, batch 8, local
  RTX 3090. Held-out sealed both runs (`heldout_rows_accessed: 0`).
- LANE DEVIATION recorded: §8 pins the verdict-bearing qualification to the
  Modal A10G lane; the user explicitly directed and accepted local execution
  as verdict-bearing (2026-07-23). Identical runner/scorer/hashes/gates; only
  the compute lane differed.
- Instrument now clean: every format gate at 1.0 (native configured first
  token 602/602, JSON, fields, confidence parse, forced posture 1806/1806,
  stripping). Confirms the first run's zeros were entirely the loader defect.
- Behavioral result, straight: ABSTAIN recall 0.77 (Wilson lower 0.707) PASS,
  ANSWER 0.792 (0.731) PASS, QUALIFY 0/200 FAIL; predicted mode counts
  ABSTAIN 290 / ANSWER 312 / QUALIFY 0; answer-quality noninferiority FAIL
  (−0.239, CI [−0.281, −0.196], floor −0.10); confidence SD 0.4845 PASS;
  max-single-mode 312/602 PASS.
- Lead adjudication: falsifier fired on the QUALIFY-recall and
  answer-quality limbs; checkpoint does not qualify for downstream GRPO.
  Full adjudication prose in AMENDMENT.md §10. Resolved with
  `--status falsified`. Successor design (class-balanced retrain with a
  QUALIFY separability pre-gate) to be drafted as a NEW experiment.
- Bookkeeping correction (lead): the earlier entry below records editing
  `qualification.yaml`'s tuner pin to `f6f1229`. That edit was reverted —
  the signed file keeps its signed bytes (`exp repin` is scoped to
  signed-but-unlaunched instruments; a mid-run repin is intentionally not
  representable, and the pin-drift validator correctly rejected the edited
  file at commit). The repaired-tuner execution is instead recorded as a
  deviation in AMENDMENT.md §10, with the executed commit captured in the
  re-run's `run_manifest.json`. The re-run itself verified the tuner
  worktree at `f6f1229` clean at launch time.

### 2026-07-23: dev qualification run stage-s-dev-20260723-local-prep INVALIDATED as an instrument failure; tuner engine repaired at f6f1229

- The local RTX 3090 dev qualification run `stage-s-dev-20260723-local-prep`
  (prepare -> generate -> score against `qualification.yaml`) completed and
  produced a `summary.json` with every gate failing:
  `configured_first_token_rate=0.0`, all 602 native rows scored mode `None`,
  `forced_posture_compliance=0.3328`, and
  `answer_quality_noninferiority` point difference `-0.573`
  (CI `[-0.613, -0.533]`). Adjudicating this run's numeric result against the
  gates in `qualification.yaml` was withheld pending diagnosis, per the
  read-before-you-cite / no-goalpost-tuning discipline.
- A bounded, read-only GPU diagnostic (no re-scoring, no gate/scorer/config
  edits, at most a handful of forward passes) traced the null result to an
  **instrument defect in the Synaptic-Tuner generation engine**, not a
  behavioral failure of the trained SFT checkpoint:
  - Transformers' own load report, emitted every time the qualification
    runner loaded the local Stage-S adapter directory (visible in
    `stage_s_qualify_run.log` lines 168 and 337, for the `stage_s_native` and
    `stage_s_forced` invocations respectively), flagged
    `model.embed_tokens.token_adapter.trainable_tokens_delta` as
    `UNEXPECTED` and the corresponding `.default`-suffixed keys as `MISSING`.
  - `tuner/batch/engines/hf_batched.py`'s `_ModelBundle` loaded the local
    adapter directory via a bare `AutoModelForCausalLM.from_pretrained()`
    instead of `peft.PeftModel.from_pretrained(base, adapter_dir)`. The
    ~500 standard LoRA `lora_A`/`lora_B` matrices merged fine through that
    generic state-dict load; the adapter's `trainable_token_indices`
    embedding-delta component (the sole mechanism differentiating
    `<ANSWER>`/`<QUALIFY>`/`<ABSTAIN>`) did not, and was silently dropped
    rather than raising.
  - Direct comparison: loading the checkpoint the way the qualification
    runner actually does (PATH A) left the embedding rows for token ids
    151670-151672 bit-identical (norm 0.364954-0.364955) to an untouched
    reserved vocabulary row, with those three tokens sitting at logit rank
    ~57,000-78,000 out of ~152,000 at the generation position. Loading the
    same checkpoint via explicit `peft.PeftModel.from_pretrained` (PATH B)
    shifted those rows measurably (norm 0.411-0.418) and put the three
    configured tokens in the top-3 logit slots by a wide margin (24.4-30.25
    vs ~15-17 for the next-best ordinary token) on every probe prompt tried.
  - The forced-lane data corroborates the same defect: all three forced
    tokens (`<ANSWER>`, `<QUALIFY>`, `<ABSTAIN>`) produced byte-identical
    completions for 100% of the 602 forced rows in every lane
    (`{"answer":"I don't know reliably.","answer_confidence":0.0151...}`,
    an exactly memorized Jeffreys-mean-`(0+0.5)/33` ABSTAIN training target),
    consistent with the model being unable to distinguish those three token
    ids from any other unused vocabulary slot. `forced_posture_compliance`
    landing at exactly 1/3 (0.3328) reflects only that ABSTAIN's target
    happens to equal this universal fallback string, not partial per-mode
    differentiation.
  - Training's own recorded final loss (`0.1282158998`, all 2,275 steps
    completed, per the entry below) is consistent with PATH B's clean,
    strongly-separated signal and not with PATH A's null signal, i.e. the
    SFT itself is not implicated by this evidence.
- Repair: tuner commit `f6f1229065b846b9bae2fa1d375d112d4a0850a1` on
  `feature/configurable-special-tokens` (parent
  `ef4e45e611e0eef0b935b60eb42ce73d3b5268b1`) adds generic local-adapter-dir
  detection (`adapter_config.json` present) to `_ModelBundle` and routes
  that case through `peft.AutoPeftModelForCausalLM.from_pretrained`, which
  resolves the base model from the adapter's own config and applies every
  adapter component (LoRA deltas and the trainable-tokens embedding delta)
  through PEFT's own loader. Plain hub ids and non-adapter local paths are
  unaffected. No Epistemic-specific logic: detection and repair are generic,
  with no token-id knowledge added to the tuner. Verified: the tuner's own
  focused suite (`tests/batch/test_engines_and_runner.py`, 14/14 including
  two new regression tests; `tests/trainers/sft/test_special_tokens.py`,
  74/74, untouched by the change) and an engine-path re-run of the
  PATH-A/PATH-B diagnostic against the real Stage-S checkpoint, which
  reproduced PATH B's numbers exactly through the fixed `_ModelBundle` code.
- Disposition: `stage-s-dev-20260723-local-prep`'s recorded gate failures are
  an **instrument-failure invalidation**, not a Stage-S falsifier result.
  `qualification.yaml`'s `tuner.expected_commit` is updated to
  `f6f1229065b846b9bae2fa1d375d112d4a0850a1` for the corrected re-run. No
  gate, scorer, threshold, posture contract, or dataset row was touched by
  this diagnosis or repair; held-out remained sealed throughout (all
  diagnostic and repair work read only from the dev split and the already-
  produced qualification artifacts). This adjudication is recorded here at
  the lead's direction; the corrected re-run under the repaired tuner
  commit is the qualifying result for the Stage-S falsifier in
  `AMENDMENT.md` section 7.

### 2026-07-23: full Stage-S training completed and adapter harvested

- Modal app `ap-kvsfvqaI0ZmXmpEPiNkcL0` completed normally at
  `2026-07-22T22:07:13Z`. The trainer reached 2,275/2,275 steps in 4,336.5
  seconds at 0.525 steps/second and recorded descriptive final train loss
  `0.1282158998`.
- The committed `DONE`, `COMPLETION_READY.json`, manifest, job provenance, and
  training lineage agree on status and exact identity: run
  `stage-s-full-20260722-204622-qwen3-4b`, tuner commit
  `ef4e45e611e0eef0b935b60eb42ce73d3b5268b1`, config SHA-256
  `dbc79b62e77923dfcea04193b1017aa5d05deac2ce96efafdab3478952d9739b`,
  and train SHA-256
  `da473bc05e544cd2cbfc091e9a9f319ed5623fef2ef969ad02a732d307246268`.
- Downloaded the canonical eight-file adapter/tokenizer bundle plus six root
  provenance files into the ignored local path
  `analysis/checkpoints/stage-s-full-20260722-204622-qwen3-4b-ef4e45e6/`.
  No train, dev, or held-out rows were downloaded during this harvest.
- The local adapter SHA-256
  `2dfa92f4d3e8cd332552c70ae84e5bdc6d8883451a575d30e5ef51a4a4861a09`
  and adapter-config SHA-256 match the training lineage. Safetensors exposes
  the expected 505 tensors. The artifact-tree SHA-256 is
  `0a226657eff07cc9aa7a0aa784d871b0eda4864995dfdb129063e3f4bcf7afb5`.
- Low-level offline tokenizer validation confirmed atomic encodings and exact
  configured IDs: `<ANSWER>=151670`, `<QUALIFY>=151671`, and
  `<ABSTAIN>=151672`. The current local `unsloth_env` Transformers version is
  not compatible with the newer saved `extra_special_tokens` config shape, so
  evaluation must use the signed pinned qualification image/dependencies or an
  equivalently compatible runtime. System Python with the signed Transformers
  5.5.0 pin loads the tokenizer successfully. The older-environment failure is
  a local runtime mismatch, not an artifact-integrity failure.
- The signed qualifier's GPU-free `prepare` phase completed as run
  `stage-s-dev-20260723-local-prep` against the local artifact tree and the
  allowed 602-row dev split. It materialized 602 base-native prompts, 602
  Stage-S-native prompts, and 1,806 forced-token prompts, reported
  `heldout_rows_accessed=0`, and left `launch_authorized=false`. No generation,
  scoring, or paid compute occurred.
- Modal CLI 1.5.1 directory-level `volume get` concatenated the remote files
  into one noncanonical file. The correct named files were fetched separately,
  verified, and the duplicate was removed. The canonical Modal source remains
  unchanged and recoverable.
- The experiment remains `running`: training is complete, but the 602-row
  dev-only qualification has only been prepared locally and remains unlaunched.
  No scientific gate or verdict has been adjudicated, and held-out remains
  sealed.

### 2026-07-22: full Stage-S training launched on Modal

- After explicit user authorization to upload the full private training
  payload and launch paid compute, staged exactly 18,197 train rows plus the
  signed direct-SFT YAML under Modal input namespace
  `stage-s-full-20260722-204622-qwen3-4b`. Dev and held-out were not uploaded.
- Submitted the signed Qwen3-4B A10G six-hour stable run through direct remote
  function `run_stable_training`. Launch-spec SHA-256 is
  `709dcd83b421977c670696aea9925559f86368f7b5bb3c69d5b34ca86d066e54`;
  tuner commit is `ef4e45e611e0eef0b935b60eb42ce73d3b5268b1`.
- Modal app `ap-kvsfvqaI0ZmXmpEPiNkcL0` showed one live task. Remote logs confirmed
  exact source materialization and the expected `train_sft.py` invocation with
  the stable run timestamp, Modal Volume output root, and mounted signed config.
- The experiment status moved from `signed` to `running`. Qualification remains
  unlaunched and requires the committed training `DONE` identity first.

### 2026-07-22: Stage S signed

- The user approved the prospective gates and authorized the full Qwen3-4B
  Stage-S run on Modal. `bin/exp sign` pinned all 14 governed config, runner,
  and test files and moved the manifest to `signed` before any full training or
  scored qualification.
- The signed training lane uses Synaptic-Tuner commit
  `ef4e45e611e0eef0b935b60eb42ce73d3b5268b1`, A10G, a six-hour ceiling, and
  the crash-safe stable-run entrypoint. The separately guarded dev
  qualification lane uses A10G and a twelve-hour ceiling for 3,010 generations.
- Held-out remains sealed and unstaged. GRPO remains outside this experiment.
- No full-run upload or paid submission had occurred at the moment of signing.

### 2026-07-22: Stage-S pre-sign qualification and launch surface implemented

- Prospectively locked the dev-only gates before any full training or scored
  qualification: 95% configured-first-token, JSON-parse, exact-field,
  forced-posture, and confidence-range rates; per-mode two-sided 95% Wilson LCB
  above 0.5 (114/200 and 115/202); maximum single-mode count 374/602;
  confidence population SD at least 0.05; and paired StageS-minus-base
  correctness with a deterministic 10,000-resample percentile bootstrap (seed
  20260722) whose two-sided 95% CI lower bound must exceed -0.10.
- Added a dev-only qualification runner over the generic tuner's public
  `batch-generate` verb. It hash-checks the 602-row dev split, reads runtime IDs
  only from the adapter's configured-token lineage, persists base-native,
  Stage-S-native, and three forced-token paths incrementally, supports exact
  resume, and writes complete private generation text/token/sub-grade exhaust.
  It never opens held-out; the held-out path is forbidden by contract.
- Hardened that runner before any scored qualification: forced posture is now
  structural/semantic rather than gold-correctness gated; configured tokens
  must be registered special with exact lineage IDs; native and forced visible
  token stripping is gated at 100%; preparation binds the complete Stage-S
  artifact tree and validates resume before prompt writes; generation requires
  the exact clean tuner commit, exact manifest model paths and prompt hashes;
  and scoring requires complete checkpoint/status/count/output hashes.
- Final pre-sign review tightened posture without using gold correctness:
  ANSWER is substantive and excludes configured ignorance/uncertainty phrases,
  QUALIFY exactly matches the configured nonempty-candidate template, and
  ABSTAIN remains exact. Scoring resume now recomputes and canonically compares
  every persisted row before skipping it.
- The synthetic kill-resume smoke hard-kills the qualification process group
  after durable generation output appears, resumes the public tuner jobs, and
  reproduces one complete scored row per dev fixture row.
- Extended the existing `prepare_stage_s.py` public-tuner Modal plan rather than
  adding another app. The resolved full package is train-only, A10G, 6-hour,
  hash-bound, detached, Volume-backed, exact-commit, and no-merge-retention.
  `launch-full` requires both an invocation-only explicit authorization flag
  and a token bound to the resolved spec hash.
- Added a separate experiment-local Modal qualification lane for the 3,010
  verdict-bearing generations. It stages only dev plus pinned configs, resolves
  an exact pushed experiment commit and exact tuner commit, refuses launch
  until the stable full-training DONE identity and token lineage exist, invokes
  only `qualify_stage_s.py` and public `tuner.py batch-generate`, commits the
  output Volume at most every 120 seconds, and uses its own hash-bound double
  authorization and DONE/post-submit contract.
- The Modal lane now clears the image entrypoint, enforces exact clean tracked
  source on both cold and warm clone paths while tolerating untracked exhaust,
  rehashes its local module before remote activity, and binds the complete
  expected training DONE identity derived from the resolved training manifest.
- This was implementation/preflight work only. At the time of this entry the
  amendment was still draft, `launch_authorized` remained false, and no full
  training, scored qualification, upload, or launch had occurred.

### 2026-07-22: user-requested Stage-S / downstream-GRPO split (draft design decision)

- The user directed that GRPO be governed as a separate experiment. The current
  draft was narrowed to Stage S only: fresh SFT plus qualification on the
  602-row dev split. The 1,201-row held-out split is sealed from Stage-S
  qualification for a separately registered downstream experiment.
- This is a pre-sign design correction, not an outcome-adaptive change. No full
  Stage-S training or scored qualification has run, the amendment remains
  unsigned, and no experiment result existed whose gate or interpretation could
  be moved.
- The Stage-S claim is now limited to imitation and qualification of the frozen
  empirical action policy: native token and JSON validity, a two-sided 95%
  Wilson recall lower bound above 0.5 for every dev mode, deterministic
  forced-token posture, anti-collapse, and answer-quality noninferiority.
- GRPO recipes, rewards, post-SFT capability-bank construction, true/permuted
  controls, treatment differentials, independent-readout analysis, and full
  blinded LLM posture adjudication are outside this amendment.
- `posture_reviewer_rubric.yaml` remains in the directory only as unreferenced
  downstream draft material. It is not part of the Stage-S instrument and must
  not be read as a pinned or authorized grader.
- The ordered token strings plus pinned upstream tokenizer are the source of
  truth. Realized token IDs are runtime lineage, not governed constants. The
  canonical Stage-S checkpoint is the adapter, tokenizer, configured-token
  lineage, and exact base lineage; merged-model output remains smoke-only.
- The existing slug/path is intentionally retained so the 17 MB private build
  and bounded-smoke provenance remain stable. This entry changes no launch
  authority: `launch_authorized` remains false and the full recipe remains
  no-launch by default.

### 2026-07-22: bounded Modal Stage-S smoke completed (pre-sign; not verdict-bearing)

- Scope was the six-row, two-step Modal pre-sign smoke only. The amendment is
  still unsigned; full Stage-S was not authorized or launched, and this entry
  is not an experiment verdict.
- Attempt 1 used tuner `67d28e25cdb93d2c7d8f51358c95a04fa870f75c`,
  Modal app `ap-cYm0lXakdNZJWJZK03zhe7`, and canonical run id
  `20260722_173803-67d28e25`. The two trainer steps and adapter path completed,
  then the forced four-bit merge check failed. Canonical manifest status is
  `failed: Training script exited with code 1`; the root exception was
  `TypeError: 'BitsAndBytesConfig' object does not support item assignment`
  when `unsloth_zoo` tried to write `llm_int8_skip_modules` through mapping
  syntax. Tuner commit `b0b7c7f83f2c8f21a1b7fc127b81a85bf3baff0a`
  (`Harden forced 4-bit merge compatibility`) fixed that compatibility seam.
- Attempt 2 used tuner `b0b7c7f83f2c8f21a1b7fc127b81a85bf3baff0a`,
  Modal app `ap-SSgsOGdrXZiR0SxjOynOdS`, and canonical run id
  `20260722_180721-b0b7c7f8`. The item-assignment failure was gone and the
  four-bit merge reached native save, but canonical manifest status was again
  `failed: Training script exited with code 1`. Transformers attempted reverse
  weight conversion on already prequantized merged weights and raised
  `NotImplementedError` from `reverse_weight_conversion`. Tuner commit
  `04b8faa463db0640bea5803ef73c3bff40ab3a93`
  (`Save prequantized merge candidates natively`) selected the compatible
  native representation without reverse conversion.
- Attempt 3 used tuner `04b8faa463db0640bea5803ef73c3bff40ab3a93`,
  Modal app `ap-RzuBUu1lyqSAAfcOGF9ubn`, and canonical run id
  `20260722_183208-04b8faa4`. The canonical manifest and job provenance both
  ended `completed` after two trainer steps. The final tokenizer retained
  `<ANSWER>=151670`, `<QUALIFY>=151671`, and `<ABSTAIN>=151672`; the adapter-only
  artifact contained 505 tensors, no full-vocabulary tensors, and passed an
  exact 505-tensor save/reload comparison. The forced merge saved an NF4
  bitsandbytes four-bit model, reloaded it locally on CPU as four-bit, preserved
  live topology and all three configured rows, and produced identical selected
  input/output row SHA-256
  `0ae61a31730c3a82144e65ddf14963ff37c7208258e1061ab5f62090663b49f5`.
  Temporary merged artifacts were removed and nothing was published.
- Durable artifacts are on Modal Volume `toolset-training-artifacts` at
  `/outputs/runs/modal/sft/20260722_183208-04b8faa4/`; the canonical final model,
  manifest, provenance, training lineage, and capacity features remain there.
- This closes the bounded tokenizer/adapter/merge/save/reload smoke blocker
  only. The next gate is user review of the draft, explicit signing, and
  separate authorization for full Stage-S—not an automatic launch.

### 2026-07-22: pre-sign cache recovery and dataset-contract build

- Located the complete local 20,000-row Qwen3-4B probe cache and its manifest;
  verified SHA-256 values `f8b4b893...635c43` and `52f374db...18b4`, probe
  config `893861257973170b`, 32 samples per row, and thinking disabled. This
  supersedes the earlier same-day note that the row cache was absent.
- User selected a substantive 0.5 capability reference but rejected a bare
  majority as too arbitrary. The unsigned draft now uses exact one-sided 95%
  binomial evidence: `k<=10` ABSTAIN, `k>=22` plus greedy-correct ANSWER, and
  QUALIFY otherwise. Counts are 10,156 / 8,307 / 1,537 for
  ABSTAIN / ANSWER / QUALIFY. Confidence target is `(k+0.5)/33`.
- Added a fail-closed deterministic dataset builder and synthetic tests. It
  reuses the canonical probe normalizers, groups transitive answer/alias and
  normalized-question components, targets 200 dev and 400 held-out rows per
  mode, and writes row-bearing products only beneath ignored `analysis/`.
- Two real builds were byte-identical. Final allocation is 18,197 train, 602
  dev, and 1,201 held-out rows; normalized answer/alias and normalized-question
  overlap across splits are both zero. The largest of 11,092 components has 55
  rows, so the entity-disjoint split is feasible without removing mixed-mode
  groups.
- Created a separate Synaptic-Tuner worktree for generic, config-driven special
  tokens. No experiment semantics or concrete mode strings are embedded in the
  tuner. CPU tests cover current/legacy tokenizer APIs, tied and untied heads,
  selective-row AdamW isolation, Unsloth-style parameter freezing, and
  adapter/tokenizer persistence. No GPU or scored generation was run.
- The amendment remains unsigned and launch authorization remains false.
  Performance thresholds that require an independent pilot remain pending.

### 2026-07-22: lineage and mechanism correction

- User clarified that the intended substrate is a **new SFT from the original
  Qwen3-4B model**, not an existing clean-SFT or GRPO-v3 checkpoint.
- The new SFT jointly teaches the first private action token and its visible
  behavior: `<ANSWER>`, `<QUALIFY>`, or `<ABSTAIN>`.
- Mode labels come from a frozen 32-generation capability audit: reliably
  correct, intermittently correct, or effectively never correct. Exact bucket
  thresholds are not new: the governed Phase-1 rule maps known to `<ANSWER>`,
  discard/ambiguous-middle to `<QUALIFY>`, and unknown to `<ABSTAIN>`. The
  proposed threshold pilot was removed after user review.
- The tracked artifact preserves 8,892 known and 7,103 unknown keys (14,395
  train, 1,600 dev). The original row-level `probe_results.jsonl` containing
  exact per-question `p_correct` and 32 sampled answers is absent locally and
  from the authenticated project HF dataset inventory. This blocks exact scalar
  targets, not categorical modes. Pre-sign choice: recover that cache or use
  fixed non-endpoint confidence bands after reconstructing the deterministic
  20,000-question ambiguous-middle complement.
- The primary action surface is the model's normal LM head restricted to the
  three registered tokens. A separate internal readout is measurement-only and
  tests whether token choice tracks prompt-end knowledge.
- The mode token prefixes a JSON object containing `answer` and
  `answer_confidence`. This preserves the parseable answer-plus-scalar surface,
  but does not silently reuse historical `response_confidence`: that field meant
  response appropriateness and is high for a correct abstention, whereas the new
  scalar estimates factual-answer capability and must be low when knowledge is
  low. Its target is a smoothed transform of correct generations out of 32.
- GRPO, if the SFT gate passes, starts from this newly trained SFT checkpoint.
  GRPO-v3 is motivation/comparison only and is prohibited as an input.
- The prior custom ordinal-router design was removed. A custom head is now a
  successor hypothesis only if native first-token logits fail while the
  independent readout remains valid.
- Drafting and committing this unsigned handoff branch are authorized. Signing,
  launching, and merging are not authorized.
- Response grading now uses the recent two-instrument discipline. The current
  enumerated detector-v2/pattern inventory is retained and reported, followed by
  a blinded multi-class LLM posture review. Unlike RR3's abstention-only lane,
  this experiment sends all held-out rows to review because qualified answers
  intentionally contain detector phrases such as "I'm not sure" and would be
  systematic detector false positives. The lane adopts RR3/Llama's
  manifest-before-review, graded-hash-before-unblinding, held-back decoy,
  private-reviewer-directory, positional-join, and no-rescoring safeguards.

### 2026-07-22: original scaffold (superseded before sign)

- The initial draft proposed a frozen prompt-end ordinal router on the existing
  GRPO-v3 checkpoint. User review rejected that lineage and clarified the fresh
  SFT-to-GRPO hypothesis above. No run was launched and no instrument was signed.
