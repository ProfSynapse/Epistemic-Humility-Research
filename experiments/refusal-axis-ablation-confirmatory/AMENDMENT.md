# Refusal-axis ablation fresh-seed confirmatory

Status: SIGNED (2026-08-16, PI approval in-conversation). Machine state in `experiment.yaml`. Run in progress.

Keep this document the prose home for the experiment. The machine state lives
in `experiment.yaml` and is never duplicated here.

## Motivation and posture

`experiments/caution-ablation-rederivation` (resolved 2026-08-16) re-derived
the archived full refusal-axis ablation result on `clean_sft_grpo_v2_seed1`:
known-item over-refusal 0.994 to 0.0298 with specificity intact, giving the
paper-cited 0.030 figure a governed source. Per the program's promotion rule,
an exploratory win becomes a paper claim only through a confirmatory
replication registered before it runs; the PI requested that step
2026-08-16 ("I want confirmatory for the ablation"). This cell is that step:
the same registered recipe executed end-to-end on a FRESH SEED with no
artifact reuse from seed 1.

Vocabulary per `papers/common/terminology.md`: the construct is the
refusal axis (fit as a refuse-versus-answer mass-mean contrast among known
items; legacy artifact name "caution direction"). Legacy config keys and
artifact filenames stay verbatim.

## Design

Substrate: `clean_sft_grpo_v2_seed2` on its own per-seed lineage (Amendment
G section 3 rule): the published seed-2 GRPO-v2 adapter
(`professorsynapse/eh-qwen3-4b-clean-sft-grpo-v2-seed2-lora` @ 2390e893)
on the published seed-2 merged SFT base
(`eh-qwen3-4b-clean-sft-seed2-merged-16bit` @ 4d526fdd), local copies on
disk. Never seed-1 artifacts anywhere in the chain.

Recipe, mirroring the seed-1 chain that the direction file's own metadata
records (`schema phase3-residual-caution-direction/v1`; layer 35, block 34,
`h_lora`; mass-mean `known_refused` minus `known_correct_answered`):

1. Behavior rows: generate the seed-2 checkpoint's own SelfAware behavior
   partition under the response-confidence contract with the archived
   behavior-rows machinery; the `known_refused` and
   `known_correct_answered` cells define the fit populations and the
   intervention row set.
2. Extraction: L35 hidden states for those rows with the archived
   extraction machinery.
3. Fit: raw mass-mean refusal-axis direction at L35 via
   `experiments/common/mechinterp/residual_caution_direction.py`
   (same script lineage as seed 1; output schema v1).
4. Intervention: the four-arm residual intervention (baseline, ablate,
   shift -2 sigma, shift +2 sigma) via
   `experiments/common/mechinterp/residual_intervention_runner.py`, config
   mirroring
   `archive/experiment/phase1/probe/config/grpo-v2-residual-repair/phase3_current_clean_grpo_v2_caution_residual_intervention.yaml`
   with only substrate/direction/row/output paths changed; prompt text
   byte-identical.

Engine exception (generation-bearing, sign-gate):
`instrument.engine_exception: {kind: parity-locked}` — the archived
legacy intervention stack is the instrument whose result is being
confirmed; changing the engine would break comparability with both the
seed-1 rederivation and the archived original.

Outputs land in this cell's gitignored `analysis/`; aggregate metrics only
(no row text) in `analysis-committed/`.

## Prediction

On the fresh seed, ablating its own refusal axis collapses known-item
over-refusal from a near-ceiling baseline to at or below 0.10 (registrant's
modal expectation 0.03-0.08), with specificity intact on
`known_correct_answered` (induced refusal at or below 0.05; correct-rate
drop at or below 0.05).

## Falsifier

Post-ablation known-item over-refusal at or above 0.30 on the fresh seed:
the collapse is seed-1-specific, the 0.030-class figure is NOT promoted,
and the papers keep their current numbers. (Also not promoted, reported
straight: any specificity break, or a result in the (0.10, 0.30) partial
band.)

## Gates

- RC-G0 (integrity, pre-outcome stop): per-seed lineage verified (seed-2
  adapter on seed-2 merged base, revisions matching the published pins);
  fresh direction fit records schema v1 metadata with `pos_cell:
  known_refused`, `neg_cell: known_correct_answered`, layer 35; full
  coverage of the seed-2 behavior-cell row set in every arm; baseline arm
  known-item over-refusal at or above 0.97 (by construction of the
  known_refused cell; seed-1 read 0.994).
- RC-G1 (confirmatory call, fixed here): post-ablation known-item
  over-refusal at or below 0.10 AND specificity intact (induced refusal on
  known_correct_answered at or below 0.05, correct-rate drop at or below
  0.05) = CONFIRMED, promotion licensed: paper 3 Section 6 and paper 5
  section 6.6 may carry the full-ablation collapse with both seeds cited.
  In (0.10, 0.30) or any specificity break = NOT CONFIRMED, no promotion.
  At or above 0.30 = falsifier fired. Thresholds fixed before the run,
  never retuned.

## Predictions scoreboard

| Predictor | Call |
|-----------|------|
| orchestrator | ablate arm lands 0.03-0.08 with specificity intact; confirmatory PASS |
| user | requested the confirmatory 2026-08-16; no directional call recorded |

## Budget

One fresh seed, four stages (behavior-row generation, L35 extraction,
CPU direction fit, four-arm intervention); ~3-4 GPU-hours on the local
RTX 3090, GPU currently idle. Requested by the PI 2026-08-16.

## Outcome

Filled at resolve.
