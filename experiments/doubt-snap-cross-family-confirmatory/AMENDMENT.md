# doubt-snap-cross-family-confirmatory

Status: resolved (2026-07-12; confirmatory claim NOT promoted; Outcome below).

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
cross-family confirmatory surface: Llama, Mistral/Ministral, Qwen3.5, and Gemma, plus
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
`mistralai/Mistral-7B-Instruct-v0.3`, `Qwen/Qwen3.5-4B`, and
`google/gemma-4-E4B-it`. The mid tier is
`unsloth/Llama-3.1-8B-Instruct`,
`mistralai/Ministral-8B-Instruct-2410`, `Qwen/Qwen3.5-9B`, and
`google/gemma-3-12b-it`. The Gemma-12B cell requires gated HF access before
launch; if access is absent, that cell is ineligible before outcome scoring and
is not replaced after seeing results.

Pre-outcome loader-eligibility note: the initially drafted Mistral-family
Ministral-3 cells expose `Mistral3ForConditionalGeneration`, not a causal-LM
substrate for the registered raw-text activation write path. They were replaced
before any Mistral-family behavioral outcome was observed with the pinned
causal-LM Mistral/Ministral cells listed in `model_matrix.yaml`.

Pre-outcome access note: the initially drafted
`meta-llama/Llama-3.1-8B-Instruct` cell remained gated for the launch HF token
with the access request awaiting review. It was replaced before any Llama-8B
behavioral outcome was observed with the accessible pinned
`unsloth/Llama-3.1-8B-Instruct` causal-LM mirror.

Post-launch pre-outcome harness-portability fix: the grader's dependency on
the legacy Phase-1 eval scorer module was removed after the first Llama-3B
dose-sweep attempt failed inside Modal at import time. The cross-family grader
now carries the small refusal and alias-match primitives it needs locally. No
held-out intervention outcome was scored before this fix.

Before relaunching the full fleet from this fix, run the Modal two-row harness
smoke in `smoke_tuner_path.py` on the quickest eligible model. The smoke uses
synthetic rows and a synthetic readout, not evaluation rows, and must reach
real `mechinterp steer` output plus smoke readback before any full cell
relaunch.

Pre-outcome dose-recalibration note (2026-07-09): the Qwen3.5-4B and
Qwen3.5-9B cells failed the registered FIT dose-viability rule with zero
qualifying doses. An audit of the committed FIT artifacts showed both failures
are overdose collapse of the registered candidate grid on these substrates,
not family nulls: Qwen3.5-4B fits `sigma_c = 2.80`, about 4.7x smaller than
the exploratory Qwen3-4B reference, so the lowest registered dose (100)
already commands a roughly 38-sigma write and all 854 fired FIT confabs
produced degenerate repetition; Qwen3.5-9B shows dose-graded collapse across
100/150/200 (refusal content rises 18 -> 363 -> 886 while well-formedness
falls 886 -> 503 -> 2), placing any coherent operating window below or between
the registered 50-unit grid steps. Readback confirms the write itself realized
the commanded projection exactly on both cells. Because dose selection is
registered as FIT-only and neither cell has seen held-out scoring, the
candidate grid for these two cells only is recalibrated pre-outcome:
Qwen3.5-4B `{10,20,30,40,50,60,75}` and Qwen3.5-9B `{60,80,100,120,140}`,
recorded in `cell.yaml` under per-cell targets. The selection rule and
thresholds (lowest dose with FIT gated clean_tighten >= 0.60 and FIT
known-correct false-refusal <= 0.10) and every other gate are unchanged. All
other cells keep the original grid, and no cell's grid changes after its
held-out outcome is known. If no dose in the recalibrated grid qualifies, the
cell fails G0 dose viability and is recorded as such without further grid
changes.

Pre-outcome dose-recalibration extension (2026-07-11, user-approved): the
llama32_3b_instruct and mistral7b_instruct_v03 probe cells hit the identical
overdose-collapse signature on the unrecalibrated default grid, superseding
the "all other cells keep the original grid" sentence above for these two
cells only. llama32_3b fits `sigma_c = 2.092`, so the default grid 100-250
commands 48.7-120.4 sigma writes (versus the 38 sigma that collapsed
Qwen3.5-4B); a committed-artifact diagnostic confirmed the write realized the
commanded strength exactly (per-arm strengths 47.79-119.48, outputs 94-99.9
percent pairwise identical across doses, not 100 percent) while 100 percent
of fired FIT rows were degenerate at every dose. mistral7b fits
`sigma_c = 0.939`, realizing 106.7-266.5 sigma on the default grid; its sweep
was stopped mid-run before producing a predetermined null (baseline, grading,
capture, and direction fits are volume-backed and reused on resume). Neither
cell has seen held-out scoring, so recalibration remains FIT-only and
pre-outcome. New grids map Qwen3.5-4B's working recalibrated z-ladder
(6.2-29.4 sigma, the grid that produced a real dose-response with peak 0.326)
onto each cell's own `build_manifest.json` `mu_c`/`sigma_c`:
llama32_3b_instruct `{11,19,26,34,41,48,60}` and mistral7b_instruct_v03
`{6,9,12,16,19,22,27}`, recorded in `cell.yaml` per-cell targets. The
selection rule, thresholds, arms, scoring, and every gate are unchanged. As
above: if no dose in the recalibrated grid qualifies, the cell fails G0 dose
viability and is recorded as such without further grid changes, and no cell's
grid ever changes after its held-out outcome is known.

Pre-sweep grid correction for mistral7b only (2026-07-11, same day, before any
FIT dose selection ran on that cell): the sigma-mapped grid `{6..27}` above was
wrong for mistral7b. The relaunch was refused by the harness gen-stream smoke
itself: the probe write at strength 27, which equals the strongest arm the grid
would have run (27 / sigma_c 0.939 = 28.75), produced byte-identical output on
all 8 probe rows, so the entire mapped grid is below mistral's token-movement
threshold and the registered selection rule was never evaluated on it. The
"without further grid changes" clause above therefore never triggered: it binds
a FIT dose-viability verdict, and no sweep ran. Direct evidence brackets the
real response region instead: the stopped default-grid partial sweep produced
584/584 fired FIT confabs degenerate at dose 100 (realized strength 106.5),
and the morning probe at strength 250 moved tokens. The mistral7b grid is
revised once more, pre-sweep and pre-outcome, to log-span that empirical
bracket: `{30,38,46,56,67,80,92}` (realized strengths 31.9 to 98.0). The
llama32_3b grid is not touched: its sweep is mid-run on the mapped grid and is
producing a real interior dose-response, and changing a grid mid-sweep is
exactly the drift these clauses forbid. This episode also falsifies the
sigma-ladder transfer assumption used in the 2026-07-11 extension above
(mistral is inert at 29 sigma while llama fires at comparable sigma): sigma
mapping is a first guess only, and per-cell empirical bracketing evidence is
required before any future cell's grid is set. Separately, the harness smoke's
`gen_stream_probe_strength` was decoupled from the dose grid (fixed 250.0,
matching `smoke_tuner_path.py`): the probe is a plumbing check, and tying it to
`max(dose_grid)` makes it inert for any legitimately low-dose grid. Selection
rule, thresholds, arms, scoring, and every gate remain unchanged; as above, if
no dose in this bracketed grid qualifies under the registered FIT rule, the
cell fails G0 dose viability and is recorded as such without further grid
changes.

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
  qualifies, the cell fails G0 viability before held-out scoring. The Qwen3.5
  cells carry a pre-outcome per-cell grid recalibration; see the dated
  dose-recalibration note above.
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
commit for this run is `9a97540` on branch
`feature/doubt-snap-batch-mechinterp`, which combines the existing batch verbs,
config-first mechinterp cells, batched steer generation, generation stop
metadata, and model-revision pins for batch and steer loads. Intervention
generation is batched through the tuner steer path with per-row active masks
and strengths; every model writes restartable per-cell configs under
`analysis/<cell_id>/`, so a failed cell or arm can be relaunched without
rerunning the family matrix. Each family loader must pass a sequential-vs-batch
parity smoke before full held-out scoring.

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

Resolved 2026-07-12. **The confirmatory cross-family claim is NOT promoted.**
No cell reached held-out scoring: every launched cell stopped at the
registered pre-outcome G0 FIT dose-viability rule, and the user then decided
in-conversation (2026-07-12, recorded in NOTEBOOK.md) to launch no further
cells because the registered prediction was already arithmetically
unreachable.

Terminal cell states (all pre-outcome FIT-dose-selection stops per the
registered taxonomy, not G1/G2/G3 held-out fails; committed aggregates under
`analysis-committed/<cell>/`):

- `qwen35_4b` (small tier): every other G0 check passed (gate AUC 0.9960,
  held-out power 1332/360, parity clean); on the recalibrated grid the FIT
  gated confab_tighten peaks at 32.6% at dose 40 with cost control at or
  below 3.3% at every dose, never reaching the registered 0.60 floor.
  `selected_dose: null`.
- `llama32_3b_instruct` (small tier): fully characterized selective interior
  dose-response on FIT, peak clean_tighten 0.184 (107/581, Wilson 95%
  [0.155, 0.218]) at dose 19 with known-correct false-refusal 0.009; gate
  AUC 0.9992; collapses to 0.000 at doses 34 and above. Below floor at
  every dose.
- `mistral7b_instruct_v03` (small tier): true behavioral null on a
  correctly bracketed grid. The write visibly moves tokens inside a
  coherent window (dose 30: 11/876 fired answers identical to baseline,
  638/876 well-formed) yet fired-confab clean_tighten is 0/874 at every
  dose and induced refusals are zero. Gate AUC 0.9998, held-out power
  1312/382.
- `qwen35_9b` (mid tier): confab_tighten rises monotonically from 0.43% to
  5.75% across the recalibrated grid with cost control 2.10-2.45%
  throughout; never approaches the floor. Gate AUC 0.9992, held-out power
  1384/428. `selected_dose: null`.
- `gemma4_e4b` (small tier) and the remaining mid-tier cells were never
  launched (fleet abandoned pre-launch); `gemma3_12b` was access-blocked
  before launch. Under the registered eligibility language these are
  unlaunched/ineligible, not fails.

**Prediction: NOT MET.** The registered prediction required at least 3 of 4
small-tier families to pass G1/G2/G3 on held-out; with three small-tier
cells stopped at G0 before held-out, at most one small-tier family could
ever have passed.

**Falsifier: NOT TRIGGERED, by a wording gap recorded straight.** The
registered falsifier is defined over held-out G1/G2/G3 fails ("A cell fails
if G1, G2, G3(i), or G3(ii) fails on held-out"), and no cell reached
held-out, so the falsifier as written can never fire on a fleet that stops
at G0. The honest reading: the experiment landed between its prediction and
its falsifier, in territory neither anticipated (uniform pre-outcome
dose-viability stops). The confirmatory claim is simply not promoted; the
mid-tier claim is underpowered by its own registered language (fewer than 3
eligible mid-tier cells).

What the stops mean (two pieces of registered-adjacent evidence adjudicate
between "mechanism does not transfer to these families" and "the registered
write site is wrong", both recorded in NOTEBOOK.md 2026-07-12 entries):

1. **The c_hat validity audit (lead-verified, CPU, over existing captures)**
   shows a read-actuate dissociation at the registered late site, not a
   failure to locate the encoding: the registered c_hat reads
   refused-vs-confab at 0.84-0.99 AUROC in ALL FOUR families (and a raw
   mass-mean refused-vs-answered direction reads 0.997-1.000 everywhere),
   yet the same write moves behavior strongly only on Qwen3-lineage,
   weakly on llama, and not at all on mistral. The encoding is present and
   linearly readable in every family; pushing it at the late site does not
   actuate refusal outside Qwen. Caveat carried from the audit: on
   llama/mistral, cross-population contrasts at this anchor carry a
   norm/position confound (random direction reads 0.77-0.83
   refused-vs-known), which does not affect the within-cell comparisons
   the interpretation rests on.
2. **The mid-band ladder on the same substrate**
   (`experiments/qwen35-4b-midband-doubt-snap`, exploratory Tier-2,
   resolved 2026-07-12, same instrument class and the same reused FIT
   rows): at hs20 dose 8 x sigma_c the SAME doubt-gated caution snap that
   fails here at the registered late site (hs30, peak 0.326) achieves
   refused 0.684 with well-formed 0.980 and known false-refusal 0.042,
   in-sample FIT. For Qwen3.5-4B specifically, the late-site G0 stop is
   therefore demonstrated to be a write-site problem, not a family
   problem. That result is exploratory and in-sample; it is cited as
   context, never pooled with this experiment.

The registered cross-family layer rule (`round(0.94 *
(num_hidden_layers - 1))`, ported from Qwen3-4B's L34) is the design
element these results indict: the jspace-family-atlas (resolved
2026-07-12) independently found that readable interior structure sits at
family-relative depths (llama band layers 15-23, mistral 7-27), not at a
universal 0.94 depth fraction. Any successor cross-family actuation
amendment should site its writes per family from the atlas layer map and
must register exterior-shaped outcomes in both prediction and falsifier so
a uniform G0 stop cannot fall between them again.

Predictions scoreboard adjudication: both predictors called "estimate
holds" and both were wrong; the fleet never reached the held-out surface
the estimate was about.

One-sentence summary (mirrors `verdict:` in `experiment.yaml`): the
cross-family confirmatory is not promoted because all four launched cells
stopped at the registered pre-outcome FIT dose-viability rule at the 0.94
depth write site (peaks 0.326/0.184/0.000 small tier, 0.058 mid tier),
and the companion c_hat audit plus the qwen35_4b mid-band ladder show the
caution encoding is readable in every family while late-site writes fail
to actuate outside Qwen lineage, indicting the universal-depth write-site
rule rather than establishing a family-level mechanism null.
