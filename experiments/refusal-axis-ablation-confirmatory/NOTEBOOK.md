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
