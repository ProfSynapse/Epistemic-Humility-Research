# Family Atlas Surface-Diversity Control notebook

Running log for this experiment. Newest entry first. This is a lab notebook,
not a claims surface; the registered design lives in `AMENDMENT.md` and the
machine state in `experiment.yaml`.

## 2026-07-21 - Shape A hard stop, PI adjudication pending

The signed CPU command exited 0 and wrote the positive-schema aggregate. G0 and
G1 passed for Gemma and Qwen. G2 matching support failed for both: Gemma had 293
pairs, best-orientation surface-role AUROC 0.6427, and maximum scalar SMD 0.1545;
Qwen had 108 pairs, AUROC 0.6103, and maximum scalar SMD 0.1738. The registered
floors were at least 100 pairs, AUROC at most 0.60, and maximum scalar SMD at
most 0.10. Pair counts passed, but both balance diagnostics failed.

The hard stop correctly prevented G3-G5 and all controlled peak calculations.
The report's downstream `fail` labels mean not reached after G2, as confirmed by
their null summaries and empty profiles; they are not measured failures. The
instrument decision is `indeterminate`, with the pre-stated Shape B escalation.
No verdict has been assigned because PI adjudication is pending.

Committed aggregate: `analysis-committed/aggregate_results.json`, sha256
`df21b826a041c015657832468bf922f119398f483b7dc528b5a27526d742ebb5`.

## 2026-07-21 - detached CPU analysis launch

Launched the exact signed two-substrate command from commit `a88db1a3` through
`experiments/common/launch_detached.sh`. The live detached wrapper PID is
`1727712`; stdout and stderr append to
`analysis/run/real_cpu.log`, and completion writes
`analysis/run/real_cpu.log.exit_code`. Source roots and private-row paths match
the signed preflight. No model or GPU path is involved.

The first one-shot shell invocation returned PID `1725652` but the execution
environment tore down its detached PID namespace immediately. It wrote no log,
checkpoint, aggregate, or exit-code sidecar, so it was not a data run. The
successful launch uses the same required detached script inside a retained shell
session, which keeps that namespace alive until completion.

## 2026-07-21 - PI approval and instrument sign

Joseph Rosenbaum approved the registered Shape A design and directed the team
to proceed. `bin/exp sign family-atlas-surface-diversity-control` pinned
`cell.yaml`, `gates.yaml`, `reanalyze_surface_diversity.py`, and
`test_surface_diversity_control.py` before the real-data CPU launch. No gate,
threshold, population, seed, or implementation changed after approval. The
launch remains CPU-only and must use the detached launcher.

## 2026-07-21 - pre-sign design and source-feasibility review

Aggregate-only preflight completed after the red-team remediation. This was a
schema, checksum, key, join, and coverage pass only. It did not open activation
tensors, compute an `eff_dim_frac` profile, fit a surface model, or adjudicate an
outcome. The safe report remains gitignored at `analysis/preflight_report.json`.

Gemma safe counts: split 2,815; capture index 2,815; capture input 2,815;
private rows 2,815; exact joined rows 2,815; fit rows 1,301; fit role counts
confab 840, known-correct answered 168, unknown-refused 293; 43 hidden states;
hidden width 2,560. Required role, split, question, derived source, derived
category, render ID, and prompt-token-count coverage is 2,815/2,815. Missing
capture-index, capture-input, private-row, tensor-file, question, token-count,
and activation-metadata counts are all zero. Safe source SHA256 values:
capture index `a11ed3a81fe5cf15e70b3d97a2a532f0aef98c63ebd0db39ce21186fac56f1d0`;
capture input `9ff0ea7c1405b4bd701d8a065b294684a076d9b4fe5325bc5d4ef4004ec57d6d`;
private rows `c207b245919932928c5f4b35edf5dd01d8d3bf29336868436d59b71ed05de4cd`;
split manifest `2aace2691d5193fb22f82e91db379de4edd3527eb4d8e5128161a9f0e65f28aa`.
The sorted row-to-file plus file-byte digest covers 2,815 activation files and
is `9c0a89082aa96ac454c54110bcaead51d075e80a6f918080d516846b81f40493`.

Qwen safe counts: split 1,768; capture index 1,768; capture input 1,768;
private rows 1,768; exact joined rows 1,768; fit rows 1,325; fit role counts
confab 124, known-correct answered 172, unknown-refused 1,029; 37 hidden
states; hidden width 2,560. Required role, split, question, inferred source,
fallback category, render ID, and prompt-token-count coverage is 1,768/1,768.
Missing counts for the same seven checks are all zero. Qwen's source and
category fields are null in the private rows; the registered row-key inference
recovers source for every row, while category is the fixed `unknown` level.
This makes Qwen a deliberately asymmetric independent replication, not a second
copy of Gemma's explicit source/category adjustment. Safe source SHA256 values:
capture index `00fc99cf28962991a280c7bf8079406e58ab519469a078287754c012271eb8f8`;
capture input `a79745b454c8854a2600a090a4032641d4be5d8ac99617a642f983edfcdbaa78`;
private rows `d1e7154481c8e5265e9701ada6e7aaffd7d7dba4d589002330a45b12eb56af98`;
split manifest `a41d7f42e74ddc6e41e1f6d2c04007c8bb6a9dcbfe5f664c5ce1050ba55175b5`.
The corresponding digest covers 1,768 activation files and is
`c3d5cd911ee10a60fbf4cd2a5e6561dd2bffba57d8882ce0de1703c2fac43f70`.

The real CPU pipeline is now wired end to end but remains unrun. It imports the
pinned estimator, reproduces G1 before control, processes substrates and layers
sequentially, checkpoints every outer fold with a config fingerprint, matches
inside source blocks, samples intact matched pairs, runs the planted and
permutation controls, measures the registered R2 treatment-strength gate, and
writes only the positive-schema aggregate. No sign or run approval is implied.

Synthetic checkpoint drill: PASS. The test completed a five-fold synthetic
surface-to-activation fit, rewound the persisted state to a simulated kill after
fold 2 of 5, and resumed folds 3 through 5 under the same source/instrument
fingerprint. Resumed residuals, predictions, and selected alphas matched the
uninterrupted result. The registered planted endpoint also passed synthetically:
hs2 became the unique peak above the 1.05 ratio, the control relocated it, and
the normalized controlled-profile deviation was 0.02473, below 0.05.

Tier selected before design: Tier 3 analysis-only diagnostic under
`.skills/experiment-runner/reference/amendment-vs-lab-notebook.md`, registered
through `bin/exp` only because the PI explicitly requested stronger governance
for the final paper-facing robustness gate. This does not create an atlas cell,
modify a prior verdict, revise a protocol, or authorize a GPU launch.

Shape decision: A, existing-capture reanalysis. Gemma is primary and Qwen3-4B
is an independent replication. Their governed Amendment Outcomes and committed
capture manifests establish complete full-depth captures at the required
final-prompt-token anchor. The source cells also retain, locally and gitignored,
the capture input containing token IDs and the private text row materialization
needed to construct the registered surface covariates. The harness reduces token
IDs immediately to prompt length and never writes token IDs or text to output.

The dataset-origin and role structure is confounded in the full pool. The design
therefore does not rely on a single residualization result. It triangulates a
five-fold cross-fitted full-pool residual analysis with a KUQ-only, 1:1 matched
confab-versus-unknown-refused sensitivity that holds origin fixed and must pass
explicit overlap, scalar-balance, and held-out surface-role predictability
thresholds. If those thresholds cannot be reached on either substrate, the
registered result is indeterminate and the next step is Shape B under separate
PI review.

The Gemma anisotropy reanalysis was read directly. Reused rigor: import the
pinned estimator; reproduce the committed baseline at `<= 1e-6`; treat location,
not peak margin, as decisive; require a seeded subsample guard. This design adds
a planted surface peak at hs2 so failure to relocate the real peak is
interpretable only after the control proves it can remove a reachable
surface-generated peak. It also adds within-origin by role permutations as a
negative control.

Private rows were accessed only for the aggregate-only schema, checksum, join,
and coverage preflight recorded above. No activation tensor was opened and no
surface model, controlled profile, or outcome was computed. No model was loaded.
No GPU process was launched. The draft is not signed and no launch is approved.

Pre-sign items still requiring PI review:

1. Approve Shape A and the two-substrate decision rule.
2. Approve the KUQ overlap thresholds and the rule that overlap failure is
   indeterminate with Shape B escalation.
3. Approve hs2, the planted alpha grid, and the 5% controlled-profile tolerance.
4. Provide the user prediction call before signing if desired.
5. Confirm that the PI accepts the completed synthetic kill-resume and planted-
   endpoint drills as the pre-sign execution evidence.

## Execution note

The real CPU analysis is expected to exceed 15 minutes and must be launched
detached after signing and separate PI run approval, for example:

```bash
experiments/common/launch_detached.sh \
  experiments/family-atlas-surface-diversity-control/analysis/run \
  python experiments/family-atlas-surface-diversity-control/reanalyze_surface_diversity.py \
  run --substrates gemma4_e4b_it qwen3_4b_raw_base
```

The exact launcher interface must be checked at execution time. Do not substitute
a direct foreground long run. No GPU flags, devices, or model-loading entrypoints
exist in this instrument.

- 2026-09-01: aggregate data exhaust published (batch 4 of the backfill, task-56c61a; PI-approved in-conversation 2026-09-01). Copy-everything mirror of analysis-committed plus README + PROVENANCE; aggregate shape, no row text, zero exclusions. 3 files / ~17 KB, built at repo commit 34663f87.
- HF repo: `professorsynapse/eh-family-atlas-surface-diversity-control` (dataset)
- HF revision: `d1cc11908f36ec7ba7a35bc5f700da285e530095`
