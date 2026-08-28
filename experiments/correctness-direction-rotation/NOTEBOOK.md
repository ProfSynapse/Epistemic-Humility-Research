# Correctness-direction rotation across training stages notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

- 2026-07-20 (RUN, RED-TEAM, RESOLVE null-result): all three GPU stages ran on
  the local 3090 (raw 1823 answered 500/1323, cleansft 1250 answered 750/500,
  partrue 1217 answered 500/717; grpov2 reused Amendment T stage2 tensors
  1488 rows 988/500), every stage clearing CD-G0. Two idle gaps occurred when
  the harness's log-pattern monitors missed clean stage exits (raw->cleansft
  and cleansft->partrue boundaries); the lead detected both from the DONE
  lines and re-drove the pipeline, and the final stages ran synchronously.
  CPU pass produced analysis-committed/cd_rotation_timeline.{json,md}; the
  lead re-derived all five L19-L24 summary means from the per-layer table
  before adjudication (exact match). Adversarial red-team review: 8 findings,
  no blockers, sign-off conditional on wording fixes F1 (gate result stated
  first, instrument-limited reading labeled post-hoc), F2 (CD-G1 fail rests
  on the later-transition limb, split-half floor is a half-sample lower bound
  whose near-tie with raw->cleansft carries no weight), F6 ("not
  identifiable" rather than "unstable"), all applied to the Outcome. Resolved
  null-result; orchestrator scoreboard call recorded WRONG on both counts.
  A6 exhaust staged and count-verified to
  /home/profsynapse/code/ehr-exhaust/correctness-direction-rotation/ (gen_raw
  1825, gen_cleansft 1252, gen_partrue 1219, cache 5, logs 3) before any
  teardown.

- 2026-07-19 (HARNESS BUILD, A3 STAGING PINS): resolved the two
  `PINNED_AT_STAGING` placeholders in `cell.yaml` (stages `raw` and `partrue`)
  against the answerability diagnostic's own committed provenance, per gate
  CD-G0's first criterion.

  **raw-base identity.** The diagnostic's committed RunPod wrapper
  (`experiments/diag-item9-caution-assembly-timeline/cloud/runpod_diag_caution_timeline.sh:13`)
  states the raw stage checkpoint verbatim: `unsloth/Qwen3-4B-bnb-4bit (no
  adapter)`. This matches `docs/checkpoint-staging.md:14` ("Base model for
  every adapter is unsloth/Qwen3-4B-bnb-4bit") and is the same HF repo id
  Amendment S extracted on as the Instruct base
  (`experiments/common/readouts/amendment_s_correctness_probe_extract.py:73`,
  `MODEL_NAME = "unsloth/Qwen3-4B-bnb-4bit"`) — the same checkpoint the CD
  controls section's CPU-only bracket already cites as
  `archive/experiment/phase1-data/probe/qwen3-4b-instruct/amendment_s/stage2/`.
  Present on disk pre-generation: local HF cache
  `~/.cache/huggingface/hub/models--unsloth--Qwen3-4B-bnb-4bit` (no network
  fetch needed). Pinned in `cell.yaml` as `unsloth/Qwen3-4B-bnb-4bit` (HF repo
  id, no adapter).

  **GRPO-par-true checkpoint timestamp.** The same wrapper's header (line 16)
  names the par-true stage `...-clean-sft-seed1-merged-16bit +
  clean-sft-grpo-par-true-seed1-lora`, i.e. Amendment AI's PAR TRUE arm,
  seed 1. Only one completed full run of that arm exists on disk: of the four
  `amendment_ai_grpo_true_seed1/<timestamp>` directories, three
  (20260703_232457, 20260703_233256, 20260703_234149) are aborted
  launch-verification/killed restarts (checkpoint-16 only, or none), and
  `20260703_234933` is the live full run that reached checkpoint-2934 with a
  complete `final_model/` (adapter_config.json + adapter_model.safetensors
  present) — confirmed against the session record
  (`docs/sessions/20260704T031355Z-ah-close-out-to-amendment-ai-sensor-refit-v1-v2-4-bit-serving-catch-pool-v2-1-arms-launch.md:331-333`:
  "the live full TRUE run is runs/amendment_ai_grpo_true_seed1/20260703_234933
  ... 2,934 scheduled steps"). This exact path is independently cross-cited as
  THE Amendment AI PAR-true checkpoint by three unrelated downstream
  consumers: `docs/checkpoint-staging.md:28` (HF private mirror
  `professorsynapse/eh-qwen3-4b-clean-sft-grpo-par-true-seed1-lora` @ revision
  `7e31d3cf62395275d4ba3d1d9ec8f95287188805`, staged 2026-07-05),
  `experiments/h9-propensity-reading-gate/AMENDMENT.md:50` ("identical to the
  one AL's A0 surface was extracted on"), and
  `experiments/registry.json:1696`. Present on disk pre-generation at
  `scratch/schema_response_confidence/runs/amendment_ai_grpo_true_seed1/20260703_234933/final_model`
  (adapter_config.json + adapter_model.safetensors verified). Pinned in
  `cell.yaml` as that local scratch path, base = the same clean-SFT
  merged-16bit already pinned for the `cleansft`/`grpov2` stages.

  Both raw and par-true checkpoint files verified present on disk before any
  generation (CD-G0 criterion 1 cleared). `bin/exp repin
  correctness-direction-rotation cell.yaml --reason "A3 placeholder
  resolution: raw-base + GRPO-par-true identities pinned to the answerability
  diagnostic's own committed provenance, no design content changed"` run to
  update the pin (placeholder resolution only, mirrors the
  rr-cross-family-raw-refusal revision-repin precedent). No changes to
  gates.yaml; no threshold/arm/gate content touched.

- 2026-07-19 (HARNESS BUILD): wrote two new modules, adapting existing
  precedent rather than reinventing it:
  - `cd_stage_extract_gen.py` (GPU): the per-stage forced-best-guess
    generation + post-gen extraction pass for raw/cleansft/partrue. Reuses
    Amendment S/T's pure helpers verbatim (`build_pool`, `_content_end_index`,
    `render_probe_prompt`, `scorers.is_correct`/`is_stated_confidence_refusal`)
    via `experiments/common/readouts/`; the SYSTEM_PROMPT string is Amendment
    T's forced-best-guess prompt applied to ALL THREE stages per
    AMENDMENT.md's Populations-and-generation section (not S's neutral
    prompt, which only cell 1 of the two precedents would have covered).
  - `cd_rotation_analysis.py` (CPU): the four-stage rotation-cosine analysis,
    method-identical to `diag_item9_caution_timeline.py` (PCA-128 fit once on
    raw reused for all stages, saga logistic in PCA space, 5-fold pooled OOF
    AUROC, consecutive + vs-grpov2 cosines), plus the two AMENDMENT-mandated
    controls (grpov2 split-half noise floor in the SAME raw-fit basis;
    CPU-only Instruct(S)->grpov2(T) bracket in its OWN PCA basis fit on S).
    Deliberately OMITS item9's cross-family Qwen3.5-4B canonical-gate cosine
    (out of scope for this cell's gates/AMENDMENT — CD tracks the
    correctness direction against itself, not against an unrelated
    cross-family answerability axis).

  Build-time adjudications (none change design content):
  1. **Post-generation only, no pre-gen capture.** cell.yaml pins
     `position: post_generation` as primary and marks pre-gen
     "optional-descriptive." The harness computes and persists ONLY the
     post-gen (last-answer-content-token) hidden state, saving one
     `save_file` call and half the tensor volume per answered row across
     three large-attempt-budget stages. Nothing in cell.yaml or gates.yaml
     requires the optional secondary, so this is a resource-cost
     adjudication, not a design change.
  2. **No cross-family canonical-gate cosine.** diag_item9 additionally
     cosines each stage's direction against a checked-in Qwen3.5-4B
     answerability axis as a heuristic cross-family sanity check. CD's own
     gates.yaml/AMENDMENT.md never mention this comparison (CD's questions is
     self-referential rotation, not cross-family alignment), so it is
     dropped rather than blindly ported.
  3. **Attempt-budget sizing (empirical, timed before the full launch).**
     Timed 150-attempt batches on the actual checkpoints: cleansft
     ~0.456 s/attempt, 13/150 wrong (~8.7%/attempt, ~75% refused); partrue
     ~1.0 s/attempt, 32/150 wrong (~21%/attempt, ~60% refused); raw
     (5-attempt smoke) 0% refused. Both abstention-trained stages clear the
     150-wrong floor far faster than Amendment T's 8550-attempts-for-500
     precedent (T's checkpoint, GRPO-v2, refused ~82%; these two stages
     refuse less). Targets set to 500 correct / 500 wrong (T/S parity, well
     above the 150 floor) with max-attempts safety margins: raw 4000
     (S's default; raw showed ~0% refusal), cleansft 10000 (~1.3x the
     ~5766-attempt projection at the observed wrong-rate), partrue 8000
     (~1.7x the ~2347-attempt projection). All three project to finish in
     minutes-to-an-hour each, well inside the AMENDMENT's ~1.5-4 GPU-hr
     per-stage estimates.
  4. **Module registration.** `cd_stage_extract_gen.py` and
     `cd_rotation_analysis.py` added to `experiment.yaml`
     `instrument.modules`/`instrument.pins` by hand (sha256sum), mirroring
     the `qwen35-4b-midband-doubt-snap`/`gate-contribution-factorial`
     precedent for post-sign module registration: nothing had run and no
     outcome existed at the time of the addition. `bin/exp validate`: OK
     (84 experiments). No changes to cell.yaml/gates.yaml gate or threshold
     content.

  GPU smoke (mandatory, pre-full-launch) passed for all three model-loading
  shapes: raw (HF repo, bnb-4bit, no adapter), cleansft (local merged-16bit,
  no adapter), partrue (local merged-16bit + local PEFT LoRA adapter) — each
  loaded, generated, extracted, and wrote well-formed rows.jsonl +
  `__post.safetensors` + manifest.json. CPU smoke of `cd_rotation_analysis.py`
  passed end-to-end on synthetic 200-row/stage data (37 layers, PCA-128,
  cosines, split-half, bracket, ID-manifests all produced without error).

- 2026-07-20 (GPU RUNS + CPU ANALYSIS COMPLETE): all three GPU stages
  finished at the sized budgets, each clearing CD-G0 (>=150/150) by a large
  margin, seed 20260719 throughout:
  - raw: 1823 attempts, 1823 answered (0 refused), 500 correct / 1323 wrong.
  - cleansft: 5359 attempts, 1250 answered (4109 refused, ~76.7%), 750
    correct / 500 wrong.
  - partrue: 2691 attempts, 1217 answered (1474 refused, ~54.8%), 500
    correct / 717 wrong.
  - grpov2 (reused, unchanged): 1488 rows, 988 correct / 500 wrong (Amendment
    T stage2, matches its manifest exactly).
  - s bracket input (reused, unchanged): 1836 rows, 500 correct / 1336 wrong
    (Amendment S stage2).

  CPU analysis (`cd_rotation_analysis.py`) ran clean over all L0..L36,
  ~4m12s wall (26m38s user / 16m23s sys — PCA/logistic fits parallelized
  across cores). All four stages clear CD-G2 (best-layer OOF AUROC well
  above 0.60: raw 0.860@L24, cleansft 0.809@L33, grpov2 0.811@L21, partrue
  0.817@L24) — every cosine is admissible per CD-G2. Numbers reported
  straight in the outcome report to the lead; no gate/falsifier adjudication
  performed here (CD-G1/falsifier read is the lead's).

  Committed: `analysis-committed/cd_rotation_timeline.json` + `.md`
  (diag_item9 shape) and four `id_manifest_<stage>.json` files (row_key +
  label only, no question/answer/alias text, no token ids, no hidden
  states — spot-checked). Exhaust staged to
  `/home/profsynapse/code/ehr-exhaust/correctness-direction-rotation/`
  (gen_raw/, gen_cleansft/, gen_partrue/ tensors+rows+manifests, cache/
  .npz activation caches, logs/) BEFORE any worktree teardown, per A6.

## 2026-08-27 — Exhaust published to HF (aggregate shape)

Data-exhaust release, PI-approved in-conversation (explicit permission
2026-08-27, batch 3 of the exhaust backfill, task-56c61a). Built with the
data-exhaust skill (aggregate-only copy-everything mirror of
analysis-committed/: no question text, generation text, or hidden states;
verify_exhaust.py PASS including the --experiment-dir completeness check;
zero exclusions). 8 files / ~474 KB, built at repo commit 37eaa399.

- HF repo: `professorsynapse/eh-correctness-direction-rotation` (dataset)
- HF revision: `68f9caf284c75e37bec38fd8e8bb08bcaf7ae03a`
