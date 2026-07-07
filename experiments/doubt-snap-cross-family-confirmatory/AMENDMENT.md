# doubt-snap-cross-family-confirmatory

Status: draft (not signed; do not launch as confirmatory evidence).

Keep this document the prose home for the experiment. The machine state lives in
`experiment.yaml` and is never duplicated here.

## Motivation and posture

This experiment is the headline-promotion test for the merged exploratory
`doubt-gated-caution-tighten` amendment. That amendment found, on bf16 raw-base
`unsloth/Qwen3-4B`, that a doubt-threshold gate plus a caution-direction snap
selectively converted confabulations into clean refusals while preserving most
known-correct answers. Its held-out result was G1 136/185 = 73.5%
clean_tighten with Wilson LCB 66.7%, G2 8/258 = 3.1% known-correct
false-refusal with Wilson UCB 6.0%, and clean G3 placebo behavior.

That is not yet a headline family claim. This amendment asks whether the same
class of training-free instrument survives a fresh, registered cross-family
replication on the family panel used by the prior "Knows but Doesn't Say"
cross-family confirmatory surface: Llama, Ministral, Qwen3.5, and Gemma, plus
8B-ish or nearest mid-size siblings where available.

Posture: confirmatory cross-family promotion. The prior Qwen3-4B exploratory
numbers are navigation and effect-size justification only. They are never pooled
with this run. All cross-family claims come from this amendment's fresh cells,
after each model's FIT-only direction, tau, and dose choices are frozen before
held-out scoring.

## Design

Substrates are listed in `model_matrix.yaml`, with Hugging Face revisions pinned
before launch. The small tier mirrors the prior cross-family panel:
`unsloth/Llama-3.2-3B-Instruct`,
`mistralai/Ministral-3-3B-Instruct-2512`, `Qwen/Qwen3.5-4B`, and
`google/gemma-4-E4B-it`. The mid tier is
`meta-llama/Llama-3.1-8B-Instruct`,
`mistralai/Ministral-3-8B-Instruct-2512`, `Qwen/Qwen3.5-9B`, and
`google/gemma-3-12b-it`. The Llama-8B and Gemma-12B cells require gated HF
access before launch; if access is absent, those cells are ineligible before
outcome scoring and are not replaced after seeing results.

The instrument is the same mechanism class as the merged Qwen amendment:

1. GATE: a doubt readout `z_d`, fired as `neg_z_d = -z_d >= tau` because
   confabulations have low doubt. `tau` is fit with Youden-J on FIT confab vs
   known-correct rows only.
2. SNAP: fired rows get an erase-and-write intervention along the model-local
   caution direction `c_hat`, scoped anchor_onward. Non-fired rows receive no
   write.
3. GEN: EOS-enabled greedy JSON generation, `min_new_tokens=1`,
   `max_new_tokens=200`, `enable_thinking=False` where the model family exposes
   that option.

Cross-family constants:

- Layer rule: use the model-local decoder layer
  `round(0.94 * (num_hidden_layers - 1))`, matching the depth fraction of Qwen
  L34 in the exploratory run without tuning layers per family.
- Direction fit: fit `u_d`, `pos_ctrl`, `neg_ctrl`, `c_hat`, and the random
  placebo direction from FIT only, with deterministic seeds and a byte-identical
  reproducibility check.
- Dose rule: because absolute readback units are not guaranteed comparable
  across model families, choose a model-local dose on FIT only from
  `{100,150,200,250}`. The selected dose is the lowest dose with FIT gated
  clean_tighten >= 60% and FIT known-correct false-refusal <= 10%. If no dose
  qualifies, the cell fails G0 viability before held-out scoring.
- Populations: mine fresh behavior-defined roles per model from checked-in
  public dataset files. Answerable candidates come from TriviaQA and PopQA and
  enter `known_correct_answered` only if that model's undosed baseline answer is
  well-formed and correct. Unanswerable candidates come from KUQ and enter
  `unknown_refused` or `confab` according to that model's undosed baseline
  behavior. Each eligible cell must have held-out confab >=150 and held-out
  known-correct >=250 before outcome scoring. Public commits contain ID-only
  manifests and aggregate summaries, never row text, answer aliases, or
  generation text.

Arms:

- `gated`: real instrument, doubt gate then `c_hat` snap at the frozen dose.
- `random_direction`: same fired rows, random direction at matched realized
  projection.
- `permuted_gate`: same total fire count, uniformly permuted over combined
  held-out confab and known-correct rows.

Execution is Modal-first on A100. Cells run in parallel, one detached Modal
function per model cell. The EHR side owns orchestration and scoring only:
baseline generation and hidden-state capture use the existing Synaptic-Tuner
batch verbs (`batch-generate` / `batch-capture`, or vLLM where the stage is
generation-only and does not need hidden states), and activation writing uses
the generic tuner `mechinterp steer` cell. The pinned Synaptic-Tuner submodule
commit for this run is `be733fe` on branch
`feature/doubt-snap-batch-mechinterp`, which combines the existing batch verbs,
config-first mechinterp cells, batched steer generation, and generation stop
metadata. Intervention generation is batched through the tuner steer path with
per-row active masks and strengths; every model writes restartable per-cell
configs under `analysis/<cell_id>/`, so a failed cell or arm can be relaunched
without rerunning the family matrix. Each family loader must pass a
sequential-vs-batch parity smoke before full held-out scoring.

Instrument files pinned at sign: `model_matrix.yaml`, `cell.yaml`,
`gates.yaml`, the thin Modal wrapper, the tuner-cell materializer, render and
grader adapters, and the pinned Synaptic-Tuner submodule commit.

## Prediction

The doubt-gated caution snap will replicate as a selective, training-free
tighten instrument across model families: at least 3 of 4 small-tier families
and at least 3 eligible mid-tier cells will pass G1/G2/G3, with at least one
passing mid-tier family outside Qwen.

## Falsifier

The headline claim is falsified if at least 2 eligible small-tier families fail,
or at least 2 eligible mid-tier cells fail, or Qwen is the only passing eligible
mid-tier family. A cell fails if G1, G2, G3(i), or G3(ii) fails on held-out.
If fewer than 3 mid-tier cells are eligible before held-out scoring, the
mid-tier claim is underpowered rather than passed. No replacements or threshold
changes after outcomes are known.

## Gates

Per-cell gates are in `gates.yaml`.

G0 is a pre-outcome eligibility and instrument-validity gate: repo access,
held-out power, baseline generation termination, FIT AUC >=0.90, direction
reproducibility, FIT-only dose viability, and batched parity smoke. G0 failure
stops that cell before outcome scoring.

G1: held-out net confab `clean_tighten >= 60%` and Wilson lower CI >50%.

G2: held-out net known-correct false-refusal <=5% and Wilson upper CI <10%.

G3(i): random-direction placebo is a no-op relative to baseline within 2 points
on both populations.

G3(ii): permuted-gate placebo has strictly worse known-correct false-refusal
than the real doubt gate.

## Predictions scoreboard

| Predictor | Call |
|-----------|------|
| orchestrator | Estimate holds |
| user | Estimate holds |

## Outcome

Filled at resolve. Record the verdict, the gate results, and the one-sentence
summary that also goes into `verdict:` in the manifest.
