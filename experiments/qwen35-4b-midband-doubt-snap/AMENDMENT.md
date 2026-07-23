# qwen35-4b-midband-doubt-snap

Status: resolved (signed 2026-07-10, Stage C completed 2026-07-12, Outcome below).
Note: this header previously read "draft (not signed)" as a stale leftover from
before the 2026-07-10 sign commit (see NOTEBOOK.md SIGNED entry); corrected at
resolve with no change to any registered content.

Keep this document the prose home for the experiment. The machine state lives in
`experiment.yaml` and is never duplicated here.

## Motivation and posture

`doubt-snap-cross-family-confirmatory` registered a cross-family replication of
the resolved Qwen3-4B `doubt-gated-caution-tighten` mechanism: a doubt-fired
gate plus a caution-direction erase-write snap, at the model-local depth
fraction `round(0.94 * (num_hidden_layers - 1))` (matching Qwen3-4B's L34 write
site). On `Qwen/Qwen3.5-4B` (bf16, revision `851bf6e8...`, 32 layers, hidden
2560) that late-site cell registered a well-characterized **G0 dose-viability
fail**, not a held-out G1/G2/G3 result (see
`doubt-snap-cross-family-confirmatory/AMENDMENT.md` and its NOTEBOOK.md
2026-07-09/07-10 entries, worktree `/home/profsynapse/code/ehr-worktrees/doubt-snap-cross-family`):
the FIT-only dose sweep on the registered grid `{100,150,200,250}` produced
0% confab clean_tighten at every dose (all fired confabs degenerated); a
pre-outcome recalibration to `{10,20,30,40,50,60,75}` found a narrow coherent
window that peaks at **~33% clean_tighten at dose 40** and then collapses
(well-formedness 90% -> 55% -> 3% across doses 40/50/60), well below the
registered 60% bar. `hs30`'s fitted gate is otherwise excellent in isolation
(FIT AUC 0.996) and `sigma_c = 2.80`, about 4.7x smaller than the Qwen3-4B
exploratory reference, so the registered dose grid was already a ~38-sigma
write at its lowest rung -- refusal induction and JSON well-formedness are
entangled at every coherent dose this late site admits on this substrate.

This is a genuine null for the late 0.94-depth site on Qwen3.5-4B, but it does
not by itself distinguish two different failure stories: (a) the mechanism
(doubt-gated caution snap) does not transfer to this model family at all, or
(b) the mechanism transfers, but the LATE write site is the wrong place to
apply it on THIS substrate -- exactly the lesson
`j-space-midband-write-sweep-qwen3-4b` and its calibration/replication chain
established on Qwen3-4B (workspace-like band at hs23-29/peak hs26, distinct
from the late L34/hs34 write site; mid-band beat late-site by +19.0pp to
+22.7pp on two independent held-out pools once dose was calibrated per layer,
see `experiments/j-space-layer-contrast-rep2-multisource/AMENDMENT.md`,
resolved FULL PASS 2026-07-09, worktree
`/home/profsynapse/code/ehr-worktrees/jspace-rep2`).

This amendment asks the Qwen3.5-4B-local version of that same question: does
writing the doubt-snap at a J-space workspace-band (mid-band) layer decouple
refusal induction from output corruption, where the late site provably could
not? It is exploratory Tier-2 evidence, local RTX 3090, FIT-side
characterization only (no held-out touched), and is never pooled with the
cross-family confirmatory headline or with the Qwen3-4B same-model chain.

**Loader/architecture note (pre-registered design premise, verified before
writing any script).** `Qwen/Qwen3.5-4B`'s config is `Qwen3_5Config` with a
NESTED `text_config` (`Qwen3_5TextConfig`: `num_hidden_layers=32`,
`hidden_size=2560`) and architecture `Qwen3_5ForConditionalGeneration`.
`AutoModelForCausalLM.from_config(...)` fails on this nested shape, but
`AutoModelForCausalLM.from_pretrained(...)` resolves correctly on a
transformers version that natively maps `qwen3_5`
(confirmed transformers 5.5.0; the pinned local `unsloth_env`
at transformers 4.57.1 does NOT recognize this model type at all -- a hard
KeyError, not a config/threshold issue -- so this experiment's GPU scripts run
under `/home/profsynapse/miniconda3/bin/python3`, base conda, not the
project's usual `unsloth_env` pin; recorded here as a deviation with cause,
not a silent substitution).

A second, more consequential architecture finding: Qwen3.5-4B is a **hybrid
linear-attention model** -- most decoder blocks route through a custom
`chunk_gated_delta_rule` recurrence (`linear_attn`), not standard
scaled-dot-product attention; the `flash-linear-attention` fast path is not
installed, so every such block runs the slow PyTorch fallback. This has two
consequences for the J-lens (Jacobian lens) double-backward JVP machinery
this amendment reuses from `j-space-localization-qwen3-4b/jlens.py`:
(1) per-eval cost is roughly 50x the Qwen3-4B reference (a JVP anchored at an
early hidden state, needing backprop through many `linear_attn` blocks, costs
~11s/prompt-direction here versus ~0.2s/prompt-direction there), which is why
this amendment's profile uses far fewer prompts/random directions than the
Qwen3-4B full profile (12 prompts x 3 directions here vs 1000 x 5 there --
a screening tool, not a statistically hardened profile); (2) running the
profile across multiple `hs_index` values with `attn_implementation="eager"`
and gradient tracking in one long-lived process intermittently raised an
async `CUDA error: unknown error` inside `chunk_gated_delta_rule` on a LATER
layer after an EARLIER layer's double-backward had already completed cleanly
-- re-running the identical layer in isolation, or the identical multi-layer
sequence under `CUDA_LAUNCH_BLOCKING=1`, both completed with no error, so this
is treated as an async-kernel-ordering hazard specific to this custom op
under double-backward, not a correctness bug in the JVP math; `jlens_qwen35.py`
and `fit_midband_directions.py extract` are run with `CUDA_LAUNCH_BLOCKING=1`
set as a hard requirement, not a performance knob.

## Design

Substrate: `Qwen/Qwen3.5-4B`, bf16, pinned revision
`851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`, no adapter, no quantization.

### Data reuse (no re-mining)

FIT rows and role assignments are reused VERBATIM from
`doubt-snap-cross-family-confirmatory`'s `qwen35_4b` cell, downloaded
read-only from the Modal volume `eh-doubt-snap-cross-family`
(`doubt-snap-cross-family-r1/qwen35_4b/analysis/{fit_rows_for_dose,
heldout_rows_for_steer,split_rows_private}.jsonl`) via `modal volume get`. See
`materialize_reused_rows.py` for the sha256-verified download-provenance check
and `analysis-committed/reused_rows_manifest.json` for the ID-only (row_key +
role + split + source + category_canon, no question text/aliases/answers)
public manifest. Counts match that cell's registered
`g0_prep_summary.json` exactly: FIT = 887 confab + 240 known_correct_answered
+ 181 unknown_refused (fit_only) = 1,308 rows; held-out = 1,332 confab + 360
known_correct_answered = 1,692 rows, recorded for provenance completeness but
NOT touched by any script in this amendment (FIT-side dose-window
characterization only; held-out is reserved for a future signed held-out
stage, mirroring how the Qwen3-4B same-model chain characterized the late-site
null cheaply on FIT before any held-out spend).

### Stage A: J-lens layer profile (pre-sign prep, free, local; DONE)

`jlens_qwen35.py`, ported from `j-space-localization-qwen3-4b/jlens.py` (same
corpus-averaged JVP math: `per_prompt_push` / `corpus_average_push` /
`layer_profile` / kurtosis / Hoyer sparsity / participation-ratio effective
dimension, byte-for-byte). Corpus: a fixed-seed (20260707) 12-question
subsample of this experiment's own reused FIT questions (not a separate
fetch). Profiled `hs_index` grid (14 points, depth-proportional to the
Qwen3-4B profile's own 13-point grid, plus the late comparator inserted
explicitly): `2,5,7,10,13,15,18,20,23,26,28,30,31,32`, where `hs_index=30`
(decoder block 29) is the registered late 0.94-depth write site
(`round(0.94*(32-1))=29` -> `hs_index=block+1=30`), included as the
within-run comparator per design. `n_prompts=12`, `n_random_dirs=3` (see
architecture note above for why this is far smaller than the Qwen3-4B
reference's 1000x5).

Band-selection rule (model-specific, not assumed to transfer from Qwen3-4B's
hs23-29/peak-hs26): the workspace-like band is read from the
`effective_dim_frac_mean` curve (rising effective linear dimensionality of
the corpus-averaged random-probe JVP push vectors is this project's
established workspace-location signal, see
`j-space-localization-qwen3-4b/jlens.py` module docstring and
`docs/ideas/j-space-global-workspace-actuation-bridge.md`); the selected band
is the profiled-grid peak plus its immediately adjacent profiled layers.

**Profile result:** see `analysis-committed/profile_summary.json` and
NOTEBOOK.md for the full curve and the selected band with its rationale.
`effective_dim_frac_mean` rises from a shallow hs2 baseline (0.336) through
oscillating mid-depth values (hs5-hs20, 0.39-0.53), peaks at **hs23 (0.558)**,
descends through hs26 (0.525) and hs28 (0.486), falls further at the late-site
region hs30-31 (~0.396-0.399), and collapses at the final layer hs32 (0.083,
RMSNorm degeneracy at the output head). Applying the band-selection rule
(grid peak + immediately adjacent profiled layers) selects **midband_candidates_hs
= {20, 23, 26}**. Total profile wall time: 2554.0s (~42.6 min) across 14
layers -- over the >15-min checkpoint threshold. `jlens_qwen35.py` flushes a
partial `profile_full.json` after each completed layer (per-layer times range
21.1s-403.2s, none individually over 15 min) rather than using the tuner's
`shared/utilities/run_log.py` RunLog; this is a deviation from the letter of
the RunLog requirement, noted here rather than silently passed over. The
per-layer flush gave equivalent progress-visibility (disk-checkable state
after every layer) but is not the same instrument as RunLog and should not
be assumed to satisfy it for any future run of this script with a
longer-than-15-min single unit of work.

### Stage B: FIT anchor extraction + direction/gate fit (pre-sign prep, free, local; DONE)

`fit_midband_directions.py`, mirroring
`doubt-snap-cross-family-confirmatory/prep_tuner_cell.py:fit_directions` /
`fit_byte_identical` exactly (same mass-mean caution direction, same
`LogisticRegression(saga, C=1.0, tol=1e-3, max_iter=5000,
random_state=20260707)` confab-propensity orthogonalizer, same QR erase for
`c_hat`, same `mu_d/sigma_d`/`mu_c/sigma_c` standardization over FIT
projections, same `np.random.default_rng(SEED + hidden_dim + hs_index)`
placebo direction) -- so every mid-band cell is the SAME instrument class as
the cited late-site null, differing only in layer. Anchor position is
`prompt_len - 1` under `doubt-snap-cross-family-confirmatory`'s own
`BASELINE_SYSTEM_PROMPT` + chat template (`enable_thinking=False`), copied
verbatim from that experiment's `render.py`, so anchors are comparable to the
cited late-site instrument's own frozen anchor convention. Gate: Youden-J
`tau_frozen` on `neg_z_d` (FIT confab vs FIT known_correct_answered), same
score definition and clip-to-[-2,2] standardization as the late-site cell and
the Qwen3-4B same-model chain. Every layer's fit is run twice and asserted
byte-identical before any artifact is written (mirrors
`fit_byte_identical`).

**Fit result:** see `analysis-committed/build_manifest.json` and
`analysis-committed/directions/hs{N}/{u_d,c_hat,random_direction}.json` for
per-layer AUC, tau, mu/sigma, and the fitted vectors. All four layers
(the three mid-band candidates plus hs30) were fit under this experiment's own
extraction, each refit twice and confirmed byte-identical before any artifact
was written:

| hs_index | AUC (neg_z_d, FIT) | tau_frozen | sigma_c | mu_c |
|---:|---:|---:|---:|---:|
| 20 | 0.9929 | -0.5897 | 1.5760 | -4.0313 |
| 23 (peak) | 0.9926 | -0.7017 | 2.1155 | -7.7542 |
| 26 | 0.9941 | -0.7295 | 2.2364 | -5.0889 |
| 30 (late comparator, refit here) | 0.9960 | -0.5942 | 2.8165 | -7.3884 |

All four clear the registered min-FIT-AUC-0.90 gate comfortably. All three
mid-band candidates have SMALLER `sigma_c` than the late site, not larger --
so if a coherent window exists at mid-band it will sit at a smaller absolute
dose than the late site's own dose-40 peak, not a larger one; see
`LAUNCH-PLAN.md` for the derived per-layer dose grids. hs30's refit here
(sigma_c=2.8165, AUC=0.9960) closely reproduces `doubt-snap-cross-family
-confirmatory`'s cited baseline (sigma_c=2.8006, AUC=0.99599) -- the small
residual difference is expected from this being an independent refit on
freshly extracted anchors (same render path, not a replay of cached
anchors), not itself a finding.

### Stage C: per-layer dose ladder (SIGNED EVIDENCE RUN -- NOT EXECUTED)

Draft-only. Per selected mid-band layer (plus late-site hs30 cited, not
re-run): gated erase-write, `anchor_onward`, EOS-enabled greedy JSON
generation, `min_new_tokens=1`, `max_new_tokens=200`, RunLog per row
(`shared/utilities/run_log.py`, available at this worktree's pinned
submodule commit `cd30d482`). Proposed per-layer dose grids and their
readback-sigma rationale are in `LAUNCH-PLAN.md`, marked draft-until-sign.
(Stale draft-era sentence corrected at resolve: `run_dose_ladder.py` was in
fact written and smoke-tested pre-sign at 8b26cfa3, pinned into the
instrument at sign, and Stage C ran post-sign 2026-07-10 to 2026-07-12 as the
signed evidence run; see NOTEBOOK.md and the Outcome section.)

### Registered readouts (Stage C, once signed)

Per dose per layer, on fired FIT confabs and the known-correct cost
population: (a) the original strict-conjunction `clean_tighten`, (b) a
format-agnostic stated-confidence refusal rate (`refused`), (c) well-formed
rate, (d) degenerate rate, (e) natural-stop rate, (f) mean new tokens. Late
site comparator numbers are the cited baseline (dose 100: 0% clean_tighten,
854/887 fired all degenerate; recalibrated dose 40: ~33% coherent tighten
peak, well-formedness collapsing to 3% by dose 60 -- see NOTEBOOK.md 2026-07-10
entry in the doubt-snap-cross-family worktree for the exact per-dose curve).

Instrument files pinned at sign (once written/finalized):
`materialize_reused_rows.py`, `jlens_qwen35.py`, `fit_midband_directions.py`,
`cell.yaml`, `gates.yaml`, `run_dose_ladder.py` (with its `grader.py` and
`gen_lib.py` companions, written and smoke-tested pre-sign at 8b26cfa3).

## Prediction

Some mid-band layer, at some dose on the proposed grid, will achieve refusal
rate >= 0.60 AND well-formed rate >= 0.80 on fired FIT confabs with
known-correct false-refusal <= 0.10 -- the coherent operating window the late
site (hs30) provably lacks on this substrate (peak ~33% coherent tighten with
collapsing well-formedness). This would decouple refusal induction from
output corruption at the mid-band site, replicating the Qwen3-4B same-model
lesson (mid-band write site outperforms the late site once dose is
calibrated per layer) on a second, architecturally distinct (hybrid
linear-attention) substrate.

## Falsifier

No mid-band layer/dose achieves the window above, AND every mid-band layer
shows the SAME entanglement pattern as the late site (refusal rate rises only
as well-formed rate falls, with no dose achieving both thresholds
simultaneously). That result would say the doubt-gated caution snap's
overdose-collapse failure mode on Qwen3.5-4B is a property of the WRITE
DIRECTION / MECHANISM on this substrate, not of the late write site
specifically -- i.e., the mid-band lesson from Qwen3-4B does not transfer to
this architecturally different (hybrid linear-attention) family member.

## Gates

Locked at sign (2026-07-10); see `gates.yaml` for the machine-readable form.
The dose grids in `cell.yaml` ({2,4,6,8,12,16,20} x per-layer sigma_c for
hs20/hs23/hs26/hs30) are locked as registered; no grid changes after this
point regardless of outcome.

- **G0 (instrument validity; stop, not outcome)**: loader resolves via
  `AutoModelForCausalLM.from_pretrained` under a transformers version that
  recognizes `qwen3_5`; FIT AUC >= 0.90 at every candidate mid-band layer;
  direction refits byte-identical; anchor extraction covers all 1,308 FIT
  rows at every candidate layer; dosed-smoke readback within tolerance;
  RunLog visibly grows during any run projected > 15 minutes.
- **G1 (primary)**: some mid-band layer + dose achieves fired-FIT-confab
  refusal rate >= 0.60 AND well-formed rate >= 0.80 with known-correct
  false-refusal <= 0.10.
- **Falsifier gate**: every mid-band layer's dose-response shows the same
  refusal-vs-well-formed tradeoff curve as the late site (no dose clears both
  thresholds at once).

Predictions scoreboard filled at sign (2026-07-10), per locked design.

## Predictions scoreboard

| Predictor | Call |
|-----------|------|
| orchestrator | G1 passes: at least one mid-band layer/dose reaches refused >= 0.60 with well_formed >= 0.80 and known false-refusal <= 0.10; most likely at hs23 in the 6-12 sigma_c range, based on the Stage B fits (smaller sigma_c, AUC 0.9926) and the sign-time smoke (clean well-formed flip at 8 sigma_c where the matched random-direction control did not flip). |
| user | G1 passes (decouples): the late-site failure was a write-site problem, not a family problem. |

## Outcome

Resolved 2026-07-12. Stage C ran on the local RTX 3090 at batch_size=8
(launched 2026-07-10 11:20, completed 2026-07-12 22:35; 74,753 generations:
1,127 shared baseline plus 3 arms x 7 doses x per-layer fired counts, hs20
882 / hs23 878 / hs26 881 / hs30 865). Official aggregates:
`analysis-committed/dose_ladder_full_summary.json` (row-text-free, promoted
from the runner's output at resolve). The lead independently recomputed the
headline aggregates from the raw RunLogs before the red-team pass and matched
the runner's values; an adversarial red-team review then ran over seven attack
surfaces (cost-gate denominator, grader circularity, baseline integrity,
placebo magnitude matching, permuted-gate construction, provenance and
determinism, goalpost check) and returned no invalidating finding, with every
recomputed number matching the RunLogs.

**Verdict: G1 PASSES.** hs20 at dose 8 x sigma_c (dose_abs 12.61) is the
unique cell in the locked 4-layer x 7-dose grid that clears both primary
floors simultaneously on fired FIT confabs: refused 0.684 (594/869) with
well_formed 0.980, against floors of 0.60 and 0.80. The decoupling is
row-level real: 593/869 fired confabs are simultaneously refused AND
well-formed, and exactly one refused row is not well-formed. The cost gate
passes on its registered population: false-refusal on FIT
known_correct_answered is 10/240 = 0.042 (bar: <= 0.10), where baseline
refusal on both roles is exactly 0. The dose-response is a coherent ridge,
not a fluke cell: dose 6 misses only the refusal floor (0.595) and dose 12
misses only the well-formed floor (0.786), with the known overdose collapse
arriving at dose 16+ (about 100% degenerate), exactly the entanglement cliff
the late site shows everywhere. The falsifier gate does NOT fire: hs20 shows
a dose window where refusal rises with well-formedness intact, which the
late site (hs30, re-run in-grid here) never achieves at any dose (peak
refused about 0.31 at doses 12-16 with well-formedness already degrading).
The mid-band lesson from Qwen3-4B therefore transfers to Qwen3.5-4B: the
late-site failure was a write-site problem, not a family problem.

Layer ordering: refusal potency at matched relative dose is monotone toward
earlier layers (hs20 > hs23 > hs26 > hs30). hs23 (the eff-dim profile peak)
peaks at refused 0.456 and hs26 at 0.276, neither reaching the 0.60 floor at
any well-formed dose. This echoes the jspace-family-atlas finding on llama
and mistral that functional structure sits earlier than the interior-peak
prior expected.

Binding scope statements (from the red-team review, adopted verbatim as
adjudicated by the lead):

1. **Cost-gate conditional.** System-level false-refusal on known-correct
   items is 0.042 (10/240) at hs20 dose 8; this is low because the doubt
   gate fires on only 13/240 knowns AND the write direction spares most
   knowns; it is NOT because dosing a known is benign: of the 13 knowns the
   gate does fire on, 77% (10/13) are falsely refused. The snap is not safe
   to apply to a known item.
2. **In-sample scope.** This is in-sample FIT characterization only: c_hat
   is fit on FIT confab-vs-refused labels and evaluated on those same FIT
   confabs; the held-out pool was never touched, by design. G1 is existence
   evidence for a decoupling operating window, not a held-out or
   generalization claim. Promotion to a claim requires a registered held-out
   stage.
3. **Selectivity attribution.** The confab/known selectivity belongs to the
   c_hat write direction's content dependence, not to the doubt gate: in the
   permuted-gate control, randomly selected dosed confabs refuse at 0.669 vs
   the gated arm's 0.684, while directly dosed knowns refuse at only 0.056.
   The gate's operational role is limiting how many knowns get dosed (13 vs
   197 at hs20), not creating the refusal selectivity.
4. **Placebo is magnitude-matched and clean.** The random-direction arm
   commands the same realized projection as the gated arm (readback at hs20
   dose 8: gated mean 12.627 vs random 12.625 against target 12.608) and
   produces about 0 refusal at every dose (0.005 at the G1 cell) until it
   destroys well-formedness at high dose. Refusal is direction-specific.
5. **Operating point.** All numbers are at batch_size=8, validated by the
   pre-launch parity probe; single-row parity was not verified. The
   documented about-1-in-240 batch-composition flip rate is small against
   the +0.084 refused and +0.18 well-formed margins.
6. **No optimum claim.** hs20 is the shallowest registered candidate and the
   only layer that clears G1; layers earlier than hs20 were profiled but
   never fit or dosed. This result establishes EXISTENCE of a decoupling
   window at a registered mid-band candidate; the operating optimum may lie
   off-grid earlier and is untested.

Predictions scoreboard adjudication: both predictors called G1 pass and both
were right on the primary call. The user's framing (write-site problem, not
a family problem) is the verdict sentence. The orchestrator's layer call
(hs23 in the 6-12 sigma range) was wrong on layer: the window is at hs20,
dose 8, and hs23 never clears the refusal floor.

One-sentence summary (mirrors `verdict:` in `experiment.yaml`): G1 passed at
hs20 dose 8 x sigma_c, the unique grid cell decoupling refusal induction
(0.684) from output corruption (well-formed 0.980, known false-refusal
10/240 = 0.042, in-sample FIT), while hs23/hs26 never clear the refusal
floor and the in-grid late-site comparator hs30 reproduces its entangled
failure, so the Qwen3-4B mid-band write-site lesson transfers to
Qwen3.5-4B.
