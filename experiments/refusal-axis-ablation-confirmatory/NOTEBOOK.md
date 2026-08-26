# Refusal-axis ablation fresh-seed confirmatory notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

- (add dated entries as the experiment progresses)

## 2026-08-16 — lead adjudication of prep flags; cell.yaml/gates.yaml filled

The prep builder's four flags, adjudicated before signing:

1. Stage order: ACCEPTED. The behavior-rows join consumes the extraction's
   rows.jsonl, so extraction runs first; the AMENDMENT's numbered list is a
   component list, not a dependency order. Also ACCEPTED: reuse of the
   governed seed-2 response-confidence eval from the resolved
   grpo-three-seed-confirmatory cell as the stage-1 generation input
   (3,369 scored rows on disk) — provenance-positive, saves a redundant
   GPU generation pass, and satisfies the AMENDMENT's response-confidence
   contract requirement for the behavior labels.
2. Schema-string drift: VERIFIED harmless. git diff of the June original
   (phase3_residual_caution_direction.py @ 1d31ed5b, the script that
   produced the seed-1 direction file) against the live
   residual_caution_direction.py shows 19 changed lines, all
   docstring/import/sys.path/schema-string renames from the July-10
   migration; the mass-mean computation is line-identical. The live
   schema string mechinterp-residual-caution-direction/v1 is the renamed
   successor of phase3-residual-caution-direction/v1 and satisfies
   RC-G0's schema-v1 requirement (pinned as such in gates.yaml).
3. Extraction prompt: ACCEPTED as registered recipe fidelity. The archived
   seed-1 extraction config carries no prompt block (generic assistant
   default); the seed-2 config mirrors that byte-for-byte. The AMENDMENT's
   response-confidence language binds the behavior-row generation (stage
   1), not the extraction pass, exactly as at seed 1.
4. adapter_name relabel to clean_sft_grpo_v2_seed2: ACCEPTED — internal
   generation tag preventing seed-1/seed-2 artifact collision, not a path.

Intervention config lead-reviewed against the archived seed-1 original:
prompt block, arms, rows_filter, and sweep byte-identical; only
model/adapter/direction/rows/output paths and the adapter tag differ.
Extraction and behavior-rows outputs verified contained in this cell's
gitignored analysis/. cell.yaml and gates.yaml written; signing next.

## 2026-08-16 — lead recompute and RC-G1 adjudication (stage 4 complete)

Recomputed from raw rows (analysis/intervention/.../rows.jsonl, 2148 rows =
537 x 4 arms; exact agreement with summary.json):

| arm | known_refused refusal / correct | known_correct_answered refusal / correct |
|---|---|---|
| baseline | 1.0000 / 0.0000 | 0.0027 / 0.9973 |
| ablate | 0.5528 / 0.2919 | 0.0133 / 0.9255 |
| shift_minus2 | 0.5590 / 0.3106 | 0.0000 / 0.9628 |
| shift_plus2 | 1.0000 / 0.0000 | 0.3617 / 0.6303 |

RC-G0: PASS. Per-seed lineage verified pre-launch; direction fit metadata
verified (schema v1, L35/block 34, h_lora, known_refused n=161 /
known_correct_answered n=376, counts exact-match stage 1); full coverage
(537 rows in every arm); baseline known-item over-refusal 1.0000 >= 0.97.

RC-G1: FALSIFIER FIRED. Post-ablation known-item over-refusal 0.5528 >=
0.30. Per the gates fixed at signing: the seed-1 full-axis collapse
(0.994 -> 0.0298) is seed-1-specific; NO promotion to paper 3 section 6 or
paper 5 section 6.6. The registered prediction (0.03-0.08) and the
orchestrator scoreboard call were both wrong; reported straight.

Secondary observations (descriptive, no goalpost movement): the axis is
still causally load-bearing at seed 2 (45.7pp release, 0 -> 29.2% correct
on formerly refused knowns; induced refusal on knowns 1.3%; known-correct
drop 7.2pp). Numerically the seed-2 full-axis ablate (0.5528) sits near
seed-1's KU-orthogonalized component result (0.5238), and shift_minus2
(0.5590) is nearly identical to ablate — a pattern the Outcome section
should note as a candidate follow-up question, not a claim.

Awaiting runner's final report for corroboration; Outcome + resolve
pending PI approval.

## 2026-08-16 — RESOLVED (falsified), PI approval in-conversation

PI approved resolve ("we can resolve the cell as well"). Outcome written to
AMENDMENT.md; verdict recorded in experiment.yaml via bin/exp resolve with
terminal status falsified. Promotion does not occur; the 0.030 figure stays
exploratory seed-1-only and every citing surface must note the registered
failed confirmatory.

## 2026-08-17 — Exhaust published to HF (aggregate shape)

Data-exhaust release, PI-approved in-conversation (explicit permission
2026-08-17). Built with the data-exhaust skill (aggregate-only: no question
text, generation text, or hidden states; verify_exhaust.py PASS including
the --experiment-dir completeness check). Contents: intervention_summary_seed2.json
plus README + PROVENANCE (3 files, ~10 KB), built at repo commit 7e3ded78.

- HF repo: `professorsynapse/eh-refusal-axis-ablation-confirmatory` (dataset)
- HF revision: `f929fa472c521e7233a4c65033a0ef89469747ef`

Card states the cell's terminal status (falsified confirmatory, RC-G1
falsifier fired) straight. Recorded in docs/public-artifacts.md.
