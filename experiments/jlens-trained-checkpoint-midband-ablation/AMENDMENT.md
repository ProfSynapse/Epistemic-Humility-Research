# J-lens on a trained checkpoint plus rule-selected mid-band refusal-axis ablation

Status: SIGNED (2026-08-16, PI approval in-conversation). Machine state in `experiment.yaml`. Queued to launch after the seed-2 confirmatory frees the GPU.

Keep this document the prose home for the experiment. The machine state lives in
`experiment.yaml` and is never duplicated here.

## Motivation and posture

Exploratory, PI-approved in-conversation 2026-08-16. Every J-lens
(Jacobian-lens) result in the program to date is raw-base Qwen3-4B only: the
localization cell found a workspace-like band at hs23-29 (peak hs26), the
calibrated layer contrast showed mid-band hs23 beats the inherited late write
site hs34 by 22.7 points, and paper 5 sections 6.3-6.4 explicitly flag
trained-checkpoint J-lens and the trained-vs-raw-base site comparison as
untested. Separately, the governed full refusal-axis ablation on
clean_sft_grpo_v2_seed1 (0.994 -> 0.0298,
`experiments/caution-ablation-rederivation/AMENDMENT.md` Outcome) sits at the
probe-chosen late site L35, selected before the J-lens or the read/actuate
depth-dissociation doctrine existed.

This cell answers two questions at once on the SAME trained checkpoint that
carries the governed collapse: (1) does training preserve, move, or flatten the
J-lens interior band, and (2) does a rule-selected mid-band ablation of the
refusal axis reproduce the collapse away from the late site. It is exploratory
evidence only: no promotion claim, and the governed paper-3 numbers are not
movable by this cell regardless of outcome (pre-stated).

## Design

Substrate: clean_sft_grpo_v2_seed1 on its own lineage (merged SFT base
`scratch/schema_response_confidence/runs/sft_schema_clean_seed1_full/20260623_123624/Qwen3-4B-bnb-4bit/merged-16bit`
plus GRPO-v2 adapter
`scratch/schema_response_confidence/runs/schema_clean_sft_grpo_v2_seed1_full/20260624_095831/final_model`,
loaded merged-and-unloaded in memory to a plain bf16 graph for the J-lens).

Stages:

1. Corpus build (CPU): rebuild the J-lens prompt corpus deterministically from
   the committed manifest (same corpus, seed 20260707, 1000 prompts as the
   raw-base profile). No prompt text is ever committed.
2. J-lens smoke (GPU, ~15 min): final-layer J-lens vs direct unembed on the
   trained substrate; instrument go/no-go (raw-base reference cosine 0.9811,
   top-10 overlap 0.82). Fail = stop; no ablation arms run.
3. J-lens profile (GPU, ~2.5 h): identical settings to the raw-base profile
   for comparability - same corpus manifest, same seed, 5 random directions,
   same 13-point grid hs [2,5,8,11,14,17,20,23,26,29,32,35,36], same plain
   user-turn render with no system prompt and enable_thinking False. The
   J-lens driver is an adapted per-cell copy of the pinned
   `experiments/j-space-localization-qwen3-4b/jlens.py` (which hardcodes the
   raw-base model and has no --model flag) extended with --model/--adapter
   arguments; precedent `experiments/qwen35-4b-midband-doubt-snap/jlens_qwen35.py`.
   The pinned original is untouched.
4. Direction fits (CPU, minutes): mass-mean refusal-axis fits via
   `experiments/common/mechinterp/residual_caution_direction.py` from the
   ARCHIVED seed-1 all-layer extraction
   (`archive/experiment/phase1-data/probe/qwen3-4b-clean-sft-grpo-v2-seed1-selfaware/hidden_states_selfaware_clean_sft_grpo_v2_full/extraction__55254a04aa1f/`,
   1233 rows x 37 layers, fp32, manifest verified) and the archived behavior
   rows (`archive/experiment/phase1-data/probe/analysis/current_selfaware_behavior_rows/clean_sft_grpo_v2/rows.jsonl`,
   known_refused n=168, known_correct_answered n=373). Binding fit at the
   rule-selected site; descriptive fits at all interior grid points are a
   reported AUROC-by-depth profile only and never feed site selection. No new
   extraction is run.
5. Four-arm intervention (GPU, ~50 min): [baseline, ablate, shift_minus2,
   shift_plus2] at the rule-selected site, same rows filter, same
   response-confidence rendering, same parity-locked legacy HF greedy
   intervention stack as the governed rederivation
   (`experiments/common/mechinterp/residual_intervention_runner.py`). The
   baseline arm re-checks the 0.994 integrity floor.
6. Paired comparison (CPU): row-level paired comparison of the mid-band ablate
   arm against the existing L35 rederivation rows
   (`experiments/caution-ablation-rederivation/analysis/current_clean_grpo_v2_caution_residual_intervention/rows.jsonl`,
   2164 rows on disk; greedy deterministic, same checkpoint, same rows, same
   instrument). Pre-stated fallback if those gitignored rows are gone at run
   time: re-run the L35 ablate arm (~12 min) under the archived config with
   the sha-pinned direction from the rederivation gates.

### Site-selection rule (fixed at signing; never revised after any result)

Metric: effective_dim_frac_mean per hs index from the trained profile.
Interior window: relative depth hs/36 in [0.35, 0.85], i.e. interior grid
points {14, 17, 20, 23, 26, 29}.

RULE (shallow band edge): the ablation site is the SHALLOWEST interior grid
point whose effective_dim_frac_mean is at least 0.5x the interior maximum.
Tie-break is inherent (shallowest). Rationale: the read/actuate
depth-dissociation doctrine (`.skills/family-atlas/reference/read-actuate-depth.md`)
warns the eff-dim peak is a read criterion, not the actuation optimum, and
shallowest-usable won in all four families. Sanity: applied to the raw-base
profile this rule selects hs23, the site that won the calibrated layer
contrast.

NO-INTERIOR-BAND BRANCH (pre-stated): declare "no interior band" if the
interior maximum is below 1.5x the median effective_dim_frac_mean over the
early points {2, 5, 8, 11}. In that branch the ablation still runs, at fixed
fallback site hs23 (the raw-base rule site), reframed as a band-portability
probe; the profile flattening is itself the primary band-reshaping finding.

VOID GUARD: if the rule ever selects a site within 2 layers of hs35, the
mid-band-vs-late contrast is void and only the profile is reported (cannot
occur under the 0.85 depth cap, which makes hs29 the deepest selectable).

Out of scope by default (noted as caveats, addable later by a new signed
revision): interior grid densification (hs 21/22/24/25/27/28) and a
behavior-matched second profile under the response-confidence system prompt.

Instrument configs pinned at sign: cell.yaml, gates.yaml, RUNBOOK.md, the
adapted J-lens driver, and the mid-band intervention config (exact list in
`experiment.yaml` instrument.configs).

## Prediction

The trained checkpoint keeps a J-lens interior band overlapping hs23-29
(interior max >= 1.5x early median), and full refusal-axis ablation at the
rule-selected mid-band site collapses known-item over-refusal to at most 0.10
with specificity intact (induced refusal on unknowns <= 0.05, known-correct
drop <= 0.05).

## Falsifier

Mid-band ablate known-item over-refusal >= 0.30 (the causal handle is
late-site-specific and J-lens guidance does not transfer to writes on this
trained checkpoint), or a specificity break at the mid-band site (induced
refusal > 0.05 or known-correct drop > 0.05) while the collapse holds
(mid-band is a blunter instrument; the late site stays preferred).

## Gates

JT-G0 (integrity, pre-outcome stop): smoke passes (final-layer J-lens tracks
the direct unembed on the trained substrate at cosine >= 0.95 and top-10
overlap >= 0.7); archived extraction and behavior rows load with verified
manifest and expected counts (1233 rows; 168/373 cells); binding direction fit
carries pos_cell known_refused, neg_cell known_correct_answered, source
h_lora, and the rule-selected layer; intervention baseline arm reproduces
0.994 within 0.02; full coverage of the declared row set in every arm.

JT-G1 (call, per branch):
- Band: interior band present (interior max >= 1.5x early median) vs absent.
- Ablation at the rule site: reproduced (<= 0.10 with specificity intact),
  partial (0.10-0.30 exclusive, or specificity break), not-transferred
  (>= 0.30).
- The paired mid-band-vs-L35 release comparison is reported descriptively
  (releases, specificity, cost per row) and carries no gate: L35 sits at
  0.0298 and a rate-delta bet would have ~3 points of headroom.

Either way the governed paper-3 numbers and the seed-2 confirmatory cell are
untouched by this cell (pre-stated; exploratory tier).

## Predictions scoreboard

| Predictor | Call |
|-----------|------|
| orchestrator | Band persists overlapping hs23-29; rule selects hs20 or hs23; mid-band ablate lands 0.03-0.10 with specificity intact |
| user | |

## Outcome

Filled at resolve. Record the verdict, the gate results, and the one-sentence
summary that also goes into `verdict:` in the manifest.
