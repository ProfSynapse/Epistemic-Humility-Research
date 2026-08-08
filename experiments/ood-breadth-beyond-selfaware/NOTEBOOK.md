# ood-breadth-beyond-selfaware notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

### 2026-08-08 registration drafted, pre-sign feasibility probe run

Governed files filled from the reviewed design draft
(`docs/preparation/amendment-draft-ood-breadth.md`) with the PI-adjudicated
decisions applied. Status stays `draft`; `bin/exp sign` is lead-only and has not
been run. Nothing committed, nothing launched.

**Pre-sign feasibility probe (read-only, membership only, no outcome touched).**
Required by `.skills/experiment-runner/reference/amendment-vs-lab-notebook.md`,
"Pre-sign feasibility probe: every arm must be constructible from real data".
Run against the canonical checkout at `53f0ba3f203f585f4ae5402753f93f15b7117fff`.
The reference explicitly permits and requires this under a self-blinding rule:
confirming an arm can be built is not computing its result.

Measured, all now frozen in `cell.yaml`:

- Training-pool union across the eight lineage files: 15,465 distinct user
  prompts. Per-file counts in `cell.yaml` under `screens.training_pool_union`.
- KUQ: 3437 unknown and 3447 known raw. Known side loses 10 duplicates, **169
  verbatim training-pool hits**, and 197 SelfAware overlaps, retaining 3071.
  Unknown side loses 955 duplicates, **zero training hits**, and 13 SelfAware
  overlaps, retaining 2469. Total retained 5540.
- KUQ known-side source breakdown, which explains the 169: squad 1928,
  triviaqa 854, hotpotqa 665 raw. Paper 3 trains on TriviaQA-RC.
- KUQ against SelfAware: **220 shared questions** (207 known, 13 unknown). The
  ordered screen attributes 197 known plus 13 unknown to the SelfAware step
  because 10 of the 207 were already removed upstream. Both figures recorded.
- AmbigQA validation: 1002 pure-multipleQAs and 830 pure-singleAnswer with
  non-empty gold, zero drops on every screen. 170 mixed-annotation rows excluded
  by rule. Known-side gold alias median 3.
- AmbigQA train (internal-panel top-up source): 4739 unknown and 5286 known
  available after screening, against 501 and 415 needed. One training-pool hit
  exists in the train split and is screened out; the validation split has none.
- BIG-bench known-unknowns: 23 Unknown-gold and 23 knowable, zero drops.
- PAR mining pool (10,759 distinct questions), non-binding for these arms:
  1002/1002 AmbigQA unknown, 23/23 BIG-bench unknown, 627 KUQ unknown and 44 KUQ
  known are present in it. Recorded as the standing disqualification for any
  PAR-trained checkpoint.
- Internal panel constructibility confirmed: 2748 rows (1503 unknown, 1245
  known) as 1832 validation plus a 916-row deterministic train top-up. Top-up
  id-list sha256 `76a8a7384727958cd78098b27fce1ddc0dbd6a5b515ca46a42fcb2b4d4998580`.
  Note for the analyst: the top-up known rows have a gold alias median of 1
  against the validation split's 3. This does not affect the internal panel,
  whose label is dataset answerability rather than correctness, and the top-up
  rows are not part of the behavior or stated-calibration surface.

**Blocking prerequisite found and gated, not worked around.** The
answer-supervised merged base at
`scratch/schema_response_confidence/runs/sft_schema_contrastive_seed1_full/20260627_203232/Qwen3-4B-bnb-4bit/`
is an empty directory; the `merged-16bit/` weights are gone. The LoRA adapter
survives at `.../20260627_203232/final_model/` (adapter_model.safetensors,
252.1 MB, plus adapter_config.json and training_args.bin). Verified by listing
both paths. Arms A2, A6 and A7 depend on it. Registered as gate G1 (re-merge,
then reproduce A2's committed SelfAware metrics within 0.10 pp or void the three
arms).

**Harness gap recorded, not fixed.** `ood.py` lines 20-22 claim `run_eval.py`
asserts training/OOD disjointness as a section 6.5 defensive check. Grepping
`run_eval.py` for `norm_question`, `train_questions`, `overlap` and `contamin`
returns only an unrelated thinking-token message at line 172. The assertion does
not exist. Follow-up F1 in `cell.yaml`; this cell does not depend on it.

**Execution-location constraint.** `datasets/ambigqa/` and
`datasets/bigbench-known-unknowns/` are gitignored in full (`.gitignore` lines 75
and 76), dataset cards included, so neither exists in this worktree. Confirmed by
`git check-ignore -v` and by their absence from the worktree checkout. The screen
and the eval both run from the canonical checkout; the four affected files are
pinned by sha256 in `cell.yaml` and verified by G0 instead of by `bin/exp sign`.

**Open for the lead at sign time.** The eight arm configs,
`screen_ood_surfaces.py`, and the `ood.py` loader diff do not exist yet, so they
are not listed under `experiment.yaml` `instrument.modules`. They must be created
and added to the pin set before stage 0 runs. Signing now would pin `cell.yaml`
and `gates.yaml` only.

Nothing in this entry is a result. No generation has been run and no gate has
been read.
