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
