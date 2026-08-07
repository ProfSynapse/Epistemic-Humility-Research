# Headline DPO/KTO seed-1 rerun on post-fix dataset build notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

### 2026-08-01 - draft scaffolded, provenance verified from source

Drafted only. Not signed, not launched, nothing committed.

Verified rather than carried over from the commissioning brief:

- All six headline train-build SHAs byte-verified against the files still on disk
  under `synaptic-tuner/scratch/eh_staging/`. The seed-1 DPO and KTO cells consumed
  pre-fix builds; seeds 2 and 3 consumed one corrected build each.
- SFT is genuinely unaffected: all three SFT seeds record train sha
  `714577a8ce6d32ac...` and SFT seed 1 launched 2026-06-14T09:29:14Z, after the fix.
- What the fix did to the data, measured not assumed: the union of train and dev is
  a byte-identical row set across both builds for both arms (DPO pool 15953, KTO
  pool 30946), so the rebuild reassigned the train/dev boundary and changed no
  content. DPO 1457 rows moved train to dev and 1460 dev to train (10.14% of pre-fix
  train rows absent from post-fix); KTO 2836 and 2915 (10.15%).

Three corrections to the commissioning brief, all carried into `AMENDMENT.md`:

1. The container digest is NOT recorded in `experiments/grpo-three-seed-confirmatory`
   (its `cell.yaml:21` pins only the mutable tag `unsloth/unsloth:latest`). The digest
   lives in `.skills/experiment-runner/reference/local-runtime.md:82-86` and the
   correct value is `sha256:f21629b9ae4ed11231768edfaed0f40d41d85d6ea9a71e8096a3d96ea0311772`.
   The value in the brief was missing one character.
2. The backfilled seed-2/3 run records are not on this branch; the records readable
   here still show `"status": "launched"`. Budget figures were therefore taken from
   the seed-1 records, which do carry completion timestamps: DPO 1h11m16s, KTO
   5h47m41s.
3. The seed-1 cells differ from the seeds-2/3 cohort on the TRAINER axis as well as
   the dataset axis (DPO seed 1 at submodule `3a3d7a26`, KTO seed 1 at `04005402`,
   seeds 2 and 3 both at `089fa9b7`). This second confound is unresolved and is
   raised as a design fork in `AMENDMENT.md` section 10 item 4.

Gate-drafting note: the `[min, max]` cohort band the brief proposed is degenerate
here because both arms sit on the abstention floor (`refusal_recall` is exactly 0.00
at seeds 2 and 3 for both). `gates.yaml` proposes a resolution-floored tolerance and
discloses, at pre-registration, that the resulting G1 passes 8 of 8 metric-arm
combinations when applied to the original pre-fix rows. G1 is a low-power
confirmation gate, not a discovery gate.

Tooling note: `scripts/audit_data_provenance.py` reproduces the hand audit and flags
exactly the two seed-1 cells across all 23 phase1 run records. Its first draft used
`str.splitlines()` for JSONL row splitting, which also breaks on U+0085; one row of
the DPO build carries a raw U+0085, so the row counts came out one too high. Fixed to
split on newlines only, and the corrected output now matches the figures above.

## 2026-08-07 — LAUNCH CLEARED (recorded before the launch verb)

PI launch approval received in session 2026-08-07 ("get our next gpu run going"), matching the signed authorization ("Launch authorized once the GPU frees after the GRPO three-seed chain"). The GRPO chain resolved and released the GPU earlier today (grpo-three-seed-confirmatory resolved, PR #397 merged); GPU verified free at dispatch. Preconditions per AMENDMENT §5/§10: container digest pinned (mismatch = hard stop), trainer submodule must sit at pinned commit 089fa9b7 for BOTH cells, data staged by sha256 (post-fix builds only; consuming a pre-fix sha is a G0 stop), beta 0.1 explicit in both cell configs, eval config committed with placeholder adapter paths. Two cells SERIAL: dpo__4b__headline__seed1__postfix (~1.2h) then kto__4b__headline__seed1__postfix (~5.8h), then full SelfAware evals (~40min/arm). Training seed stays 1 in both cells (dataset-version replication, not fresh-seed). Executor dispatched with read-the-docs-first instruction; lead adjudicates all gates from artifacts.

## 2026-08-07 — G0 preflight: executor HARD STOP on trainer pin (correct), lead ruling on submodule state

Executor preflight: data shas MATCH the post-fix pins exactly (DPO 39e2ba8c..., KTO 9cb291ee...) and are not the superseded pre-fix shas; container digest exact match; GPU free; disk 113G. STOP fired on the trainer pin: canonical synaptic-tuner HEAD is 2995494885c9ddebae37efd38e27caa844e7bba8 (unrelated mechinterp-runner image chain, working tree clean), and pinned 089fa9b7 is NOT an ancestor of it (diverged line). Executor correctly did not launch and did not touch submodule state.

LEAD RULING: temporary detached checkout of the pinned commit, recorded and reversible. The pin is the point of the design (AMENDMENT §10 item 4: both cells at the cohort's trainer vintage 089fa9b7); the current submodule HEAD is incidental state from unrelated tooling work with no active consumer this session. Procedure: (1) record restore target 2995494885c9ddebae37efd38e27caa844e7bba8 (this entry is that record); (2) `git -C synaptic-tuner checkout 089fa9b7` (detached) in the CANONICAL checkout, verify HEAD; (3) run BOTH cells at that vintage; (4) after the second cell's closeout, restore the submodule to the recorded commit. The superproject pointer is never committed in either direction; the staged data under synaptic-tuner/scratch/ is gitignored and unaffected by checkout.

## 2026-08-07 ~09:47Z — DPO cell LAUNCHED; recipe-diff adjudicated (beta field = pre-authorized exception)

Submodule at 089fa9b7 (verified full hash, clean tree, nothing committed); data sha re-verified post-checkout and again on the staged copy (39e2ba8c..., row count 14395, staged to its own dir per cell.yaml). Digest re-verified before dry-run and launch. Dry-run clean (banner: batch 2, effective 8, LR 5e-06, beta 0.1, r32/a64/dropout 0.05 — all match cell.yaml).

**G0 `config_identity_vs_original` ADJUDICATED PASS with one recorded nuance.** Materialized recipe (hand-built, no generator exists for off-matrix arms; committed at `archive/experiment/phase1/run_records/materialized_recipes/dpo__4b__headline__seed1__postfix.yaml`) diffs from the original seed-1 recipe in exactly 5 of 40 fields: `name`, `dataset.local_file`, `setup.copy[4]`, `artifacts.output_root` (all dataset-path/run-naming, as G0 requires) plus `training.beta: None -> 0.1`. The beta field is NOT dataset/run-naming, but it is the AMENDMENT §10 item 3 ruled addition, signed before launch: both cells state beta explicitly instead of relying on the trainer's implicit default, with the effective value unchanged (PROTOCOL 3.1a records 0.1; lead verified at 089fa9b7 that beta flows only from config). Adjudicated as a pre-authorized exception, surfaced by the executor rather than silently passed — correct handling.

Launch: container `eh-postfix-seed1-dpo-train-20260807_094728` (started 09:47:28Z), run dir `synaptic-tuner/toolset-training-artifacts/runs/local/4b/dpo__4b__headline__seed1_postfix/20260807_094728`. One aborted attempt with a malformed run-timestamp was self-caught at 14s (before model load), container removed, no output dir created; an EMPTY decoy dir `20260807_094614` (zero files) sits alongside the real run dir — closeout must key off `20260807_094728` only. Steps advancing: 345/1800 at ~11 min, checkpoints writing, GPU profile matches the original seed-1 run. Lead independently verified the live container digest, explicit python3 entrypoint, and submodule commit. Expected completion ~10:58Z.

## 2026-08-07 ~11:00Z — DPO training COMPLETE and verified; eval-config instrument defect repaired via audited repin

Training: exit 0, 1800/1800 steps, 58m07s, lineage matches cell.yaml on every field (base 4-bit foundation, seed 1, r32/a64/0.05, LR 5e-06, beta 0.1, staged dataset 14395 rows). Adapter 264,308,896 bytes.

Executor hard-stopped at eval launch on a real instrument defect (third correct stop this experiment): the pinned eval config's `gold_path` and `eval_sets.selfaware.path` carried three `../` segments, but run_eval.py resolves relative paths from `archive/experiment/phase1/eval/` which needs four; as committed the eval would crash at load, before any GPU cost. Lead verified the resolution both ways and against the known-working GRPO-chain configs, fixed both lines to four levels, and ran `bin/exp repin` (pre-run, audited; third repin in this experiment's trail) with the full reason. The same repin absorbs the amendment-authorized DPO adapter-placeholder fill (§10 item 1). New pin 876842ce... `exp validate` OK. Worktree and canonical copies byte-identical. No prompt, generation, scoring, or bootstrap field changed — the eval surface is untouched.

## 2026-08-07 ~11:45Z — DPO cell: eval complete, G0 PASS, arm INSIDE all four G1 bands

Eval container exited 1; attribution verified by evidence chain (executor) and accepted by lead: run_eval's arm loop fully generated, scored, and wrote arm 0 (dpo, 3369 rows, config_sha 876842ce matches provenance) BEFORE arm 1 (kto) whose adapter is still the amendment's placeholder; the crash is the placeholder failing its first lazy LoRA weight load, after all DPO artifacts were complete. No KTO artifacts exist anywhere; DPO scored_rows exactly 3369 with label counts matching the cohort surface (1032/2337). LESSON for the record: a multi-arm eval config with an unfilled placeholder arm exits nonzero BY CONSTRUCTION after the filled arms complete; the KTO arm eval needs lead-decided scoping at its closeout (do not blind-rerun the whole config: nondeterministic regeneration of the completed dpo arm would be a silent-substitution provenance hole).

G0 ADJUDICATED PASS (all checks): data sha (pre- and post-checkout, twice), config identity (5-field diff, beta pre-authorized), pinned digest at every verb, trainer at 089fa9b7, training clean 1800/1800, eval surface identity (0 think-tag/reasoning matches over 3369 rows, enable_thinking uniformly False, temp 0.0 / seed 20240601, cohort shape 1032/2337).

**G1, DPO arm: INSIDE all four signed bands (lead re-derived from metrics.json):**
| metric | rerun | band | cohort s2/s3 |
|---|---|---|---|
| refusal_recall_pct | 0.00 | [0.00, 0.29] | 0.00 / 0.00 |
| over_refusal_pct | 0.13 | [0.00, 0.30] | 0.04 / 0.17 |
| truthful_pct | 16.62 | [13.48, 18.28] | 16.68 / 15.08 |
| correct_on_known_pct | 23.99 | [19.48, 26.35] | 24.06 / 21.77 |

The rerun sits at the cohort's abstention floor exactly (refusal_recall 0.00, counts 0/1032). Per the signed §10.5 decision rule the pair verdict (PASS/PARTIAL/FAIL) waits for the KTO cell; no verdict is recorded yet. Raw observation, no gate weight: stated_confidence coverage 0.0 (all rows null) — surface-consistent, the cohort CSV carries no confidence columns; this track never measured it. correct_on_known_pct carries the standing filtered-denominator caveat (560/2334 here; near-complete answering makes the filter mild for this arm).

KTO cell CLEARED for launch (second and final cell): cold-start seed 1, post-fix build sha 9cb291ee... (verified twice already), trainer stays at 089fa9b7, ~5.8h expected.

## 2026-08-07 ~12:00Z — KTO recipe-diff ADJUDICATED (15 fields, all accepted with reasons); dry-run/launch cleared

Executor held before dry-run on a structurally larger recipe diff than DPO's (15 of 46 fields vs 5 of 40) — correct hold, fourth of this experiment. Lead adjudication, field group by field group:
1. Dataset-path/run-naming (output_root, dataset.local_file, name, setup.copy[4], run_timestamp literal->placeholder): PASS per G0 text, same category as the DPO cell.
2. `training.beta` absent->0.1: pre-authorized §10.3, same ruling as DPO.
3. `job.keep_container` True->False: container lifecycle plumbing, no training semantics; matches the --rm discipline used for every cell in this rerun and the GRPO chain. ACCEPTED.
4. `run.command` (original: bash -lc string that PATCHES train_kto.py in place to insert `import logging`, then runs it) -> plain trainer invocation: ACCEPTED, two grounds. (a) Lead-verified at the pinned vintage 089fa9b7: `Trainers/kto/train_kto.py:13` has `import logging` at module scope, so the patch is dead code there; notably the import is also present at the original vintage 04005402, so the patch appears to have been redundant even historically (cargo-culted workaround; harmless duplicate-insert then, unnecessary now). (b) Applying the in-place patch under this rerun's bind-mount launch pattern would edit the real checked-out submodule file and dirty the pinned tree the design requires clean. The omission is a direct consequence of the signed §10.4 trainer-vintage ruling.
5. `artifacts.host_path`/`container_path` absent, `run.workdir` representational gap: derived bookkeeping, same gap already present and accepted in the DPO cell.
G0 `config_identity_vs_original` intent check: nothing differs SILENTLY; every divergence is surfaced, reasoned, and outside training semantics. Substantive hyperparameters identical to cell.yaml (batch 2, accum 4, LR 1e-6, seed 1, r32/a64/0.05, 1 epoch, beta 0.1, cold-start 4-bit foundation). Preflight otherwise clean: submodule pinned+clean, data sha verified source and staged copy (9cb291ee...), 28790 rows matching cell.yaml, GPU idle, disk 111G. CLEARED for dry-run and launch.

## 2026-08-07 ~12:05Z — KTO cell LAUNCHED; eval-scoping ruling PRE-STATED for the KTO closeout

Launch: dry-run clean (banner matches cell.yaml, twice-shown values consistent); training container `eh-postfix-seed1-kto-train-20260807_115232` started 11:52:32Z, run dir `.../kto__4b__headline__seed1_postfix/20260807_115232`, total_steps 3599 — exactly the original seed-1 KTO record's step count, as expected for an identical dataset size and batch geometry. Lead independently verified live-container digest, explicit python3 entrypoint, submodule at 089fa9b7 with clean tree. Expected completion ~17:30-17:40Z.

EVAL SCOPING RULING, pre-stated before any KTO eval artifact exists: `run_eval.py` has no arm-selection flag (lead verified: only --config/--live-vllm, run() iterates all cfg arms). Therefore at KTO closeout the pinned eval config receives ONE more pre-run repin that (a) fills arms[kto].adapter with the real final_model path (amendment-authorized placeholder fill, §10.1) and (b) REMOVES the dpo arm from the arms list, so the completed DPO results (config_sha 876842ce, on disk) cannot be nondeterministically regenerated and silently substituted. Prompt/generation/confidence/scoring/bootstrap/eval_sets sections must remain byte-identical, verified by section diff before launch. Each arm's metrics.json carries its own config sha; the repin audit trail ties both shas to this experiment. This ruling is recorded now so the closeout executes a pre-stated procedure rather than improvising one after seeing a result.

## 2026-08-07 ~12:10Z — KTO run STOPPED by PI request (machine restart), at step 115/3599

PI needed a machine restart; lead stopped the training container deliberately at step 115/3599 (~12 min elapsed, ~3%). Cheapest possible stop point; nothing adjudicable was in flight. Run dir `20260807_115232` is now an ABORTED DECOY (no final_model) — the relaunch after reboot starts FROM SCRATCH (not checkpoint resume, consistent with this experiment's provenance design and the GRPO-chain precedent: the original seed-1 cell trained in one clean pass, and a resumed trajectory is not that). All prior evidence unaffected: DPO cell closed (G0 PASS, INSIDE all bands), branch commits pushed on next connect. Post-reboot checklist for the relaunch: docker daemon up, submodule still at 089fa9b7 clean (re-verify; reboot does not change git state but verify anyway), digest re-verify, staged KTO data sha re-verify, fresh dry-run, fresh launch.

## 2026-08-07 — Post-reboot relaunch of the KTO cell (recorded before the verb)

Machine restarted (planned, PI). Lead re-verified the full post-reboot checklist: docker daemon up, pinned digest still resolves exactly, GPU free (0 MiB), submodule at 089fa9b7 with clean tree, staged KTO train file sha unchanged (9cb291ee...), 111G free. Prior executor session did not survive the reboot; a fresh executor is dispatched with the same signed invocation. Run dir 20260807_115232 remains an aborted decoy (stopped at step 115). Relaunch is FROM SCRATCH per the recorded stop ruling. All prior adjudications unaffected.

## 2026-08-07 ~12:35Z — Post-reboot relaunch STOPPED by lead: launch-pattern deviation (G0 instrument stop, no training occurred)

The fresh executor's relaunch container (`eh-postfix-seed1-kto-train-20260807_123133`) passed the digest check but deviated from the experiment's established launch pattern in two ways, caught by the lead's independent inspection within ~2 minutes: (1) entrypoint `["bash"]` wrapping a command that runs `pip install --upgrade trl==0.22.2 git+.../unsloth_zoo.git git+.../unsloth.git` BEFORE the trainer — a runtime upgrade of unpinned GitHub HEADs that mutates the pinned software environment and defeats the digest pin's purpose; (2) a different mount layout (submodule mounted at /workspace/repo rather than the superproject). The DPO cell of this same experiment ran with plain `--entrypoint python3` and a direct trainer command, no pip preamble (lead-verified on that live container at the time), so this would also have made the two cells of the same experiment differ from each other. Container stopped before any training step or file write: run dirs `20260807_123133`, `20260807_122846`, and `20260807_115128` all verified EMPTY (zero files) — decoys only, no contaminated artifacts. GPU free.

Relaunch will be re-dispatched with the launch pattern mandated explicitly (the DPO cell's verified pattern: superproject mount, `-w /workspace/repo/synaptic-tuner/Trainers/kto`, `--entrypoint python3`, direct trainer invocation, no package installation of any kind at runtime). Decoy ledger for this cell now: 115128, 115232 (aborted step-115, has content), 122846, 123133.
