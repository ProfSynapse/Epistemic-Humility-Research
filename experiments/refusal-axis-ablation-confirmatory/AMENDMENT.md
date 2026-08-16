# Refusal-axis ablation fresh-seed confirmatory

Status: FALSIFIED (resolved 2026-08-16, PI approval in-conversation). Machine state in `experiment.yaml`.

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

Resolved 2026-08-16, PI approval in-conversation. All numbers recomputed by
the lead from raw rows (analysis/intervention/.../rows.jsonl, 2148 rows =
537 x 4 arms; exact agreement with the runner summary).

RC-G0 (integrity): PASS. Per-seed lineage verified on disk pre-launch (seed-2
merged base 20260731_232307, seed-2 GRPO-v2 adapter 20260804_131151);
extraction 1233 rows exactly matching the frozen SelfAware manifest, manifest
status ok with adapter tag clean_sft_grpo_v2_seed2; behavior cells
known_refused n=161 / known_correct_answered n=376 (join exit 0, counts
carried exactly into the direction fit); binding fit metadata exact (schema
mechinterp-residual-caution-direction/v1, layer 35 / block 34, source h_lora,
pos/neg cells as registered, construction AUROC 0.869); full coverage (537
rows in every arm); baseline known-item over-refusal 1.0000 >= 0.97.

RC-G1 (call): FALSIFIER FIRED. Post-ablation known-item over-refusal 0.5528
>= 0.30. Per the gates fixed at signing: the seed-1 full refusal-axis
collapse (0.994 -> 0.0298) is seed-1-specific; NO promotion of the collapse
to paper 3 section 6 or paper 5 section 6.6. The registered prediction
(0.03-0.08) and the orchestrator scoreboard call were wrong.

Arm table (known_refused refusal/correct; known_correct_answered
refusal/correct): baseline 1.0000/0.0000; 0.0027/0.9973. ablate
0.5528/0.2919; 0.0133/0.9255. shift_minus2 0.5590/0.3106; 0.0000/0.9628.
shift_plus2 1.0000/0.0000; 0.3617/0.6303.

Descriptive observations (recorded, not claims): the refusal axis remains
causally load-bearing at seed 2 (ablation releases 45.7pp of known-item
refusals and lifts formerly refused knowns from 0 to 29.2 percent correct,
with induced refusal on known-correct items 1.3 percent and a known-correct
drop of 7.2pp). The seed-2 full-axis ablate value (0.5528) sits near seed-1's
KU-orthogonalized component result (0.5238), and shift_minus2 (0.5590) is
nearly identical to the ablate arm; whether the axis decomposes differently
across seeds is a candidate follow-up question for a future registered cell,
not a claim of this one.

Verdict: Falsifier fired: with a valid instrument (RC-G0 pass, baseline
1.000), full refusal-axis ablation on clean_sft_grpo_v2_seed2's own lineage
leaves known-item over-refusal at 0.553, far above both the 0.10 confirmation
bound and the 0.30 falsifier line, so the seed-1 0.994-to-0.030 collapse is
seed-1-specific and no promotion to the papers occurs, while the axis itself
remains causally load-bearing at seed 2.
