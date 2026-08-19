# Wide-instrument re-score of the gated-controller and layer-contrast controls (Qwen3-4B) notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

- 2026-08-18: Signed. All four scoreboard calls recorded before sign
  (orchestrator: G0 passes, G1 holds, G2 survives, G3 holds; user: G0 "it
  works", G1 holds, G2 survives, G3 holds). Launch pre-confirmed by the user
  earlier the same day ("a pre confirm launch go"), sequence per RUNBOOK:
  offline prep (materialize_rows + anchor extraction), Stage 0 regeneration
  on the local 3090, WG-G0 parity stop-check, Stage 1 blinded pool build,
  lead commits the adjudication pool manifest before any grading agent is
  dispatched.
- 2026-08-18 (launch attempt 1): runner stopped pre-GPU on unmet offline
  prerequisites — the two phase-1 probe pool files
  (ah_main/gen_A0/rows.jsonl, ak_stage1/ak_stage1_pool.jsonl) were absent
  from this checkout's archive path. Lead certified byte-identical copies in
  other cells' gitignored staging against the committed sha256 records in
  j-space-localization-qwen3-4b analysis-committed (h1_full.json ah_a0_rows
  2771091c…, ak_stage1_pool 48654798…) and restored them (user executed the
  copies; destination covered by .gitignore line 24). Mechanical RUNBOOK
  corrections, no design change: stale status-draft note replaced with the
  sign date; offline-prep order corrected to extract-before-materialize
  (materialize_rows.py reads the extract manifest, and the extractors'
  docstrings say step 1/3); PYTHONPATH instruction added for the archived
  extractors' amendment_ah_stage0_extract import gap, in preference to
  editing the archived scripts. Note: bin/exp sign regenerated
  instrument.pins from configs+modules, dropping the RUNBOOK and the two
  cross-cell wide-stack pins from experiment.yaml; the wide-stack shas
  remain recorded in the signed AMENDMENT text, which stays the pin of
  record for those two files.
- 2026-08-18 (launch attempt 2): runner stopped pre-GPU again — the July
  archive relocation (commit 0723c329, pure R100 renames) moved
  amendment_s_correctness_probe_extract.py into
  probe/legacy-wrapper-tree/, breaking the archived extractors' bare-name
  import. Lead ruling: environment-only fix, PYTHONPATH extended to
  amendments + legacy-wrapper-tree + repo root. Verification chain: the
  relocated file is a compatibility wrapper delegating to the promoted
  experiments/common/readouts implementation; the untracked probe-root
  backends.py the runner flagged as unrelated cruft is in fact
  byte-identical (sha edb42095) to experiments/common/knowledge_probe/
  backends.py, which defines the render_probe_prompt the chain needs, so
  it was left in place; full import chain proven on CPU
  (load_baseline_system_prompt importable) before relaunch. No archived
  script edited; WG-G0 parity remains the arbiter of regeneration
  fidelity against the committed rows.
- 2026-08-19 (launch attempt 3): third pre-GPU stop, same class — the
  archived helper hardcodes the pre-rename AC config path (d55b7d26
  dropped the phase3_ prefix; R078, not a pure rename). Lead verified the
  helper's sole read, prompt.system, is byte-identical (463 chars) across
  the rename with no other AC_CONFIG consumer, and ruled for the
  h9-propensity-reading-gate precedent: an untracked verbatim shim of the
  tracked yaml at the old expected path, placed by the user. Two sibling
  experiments hit and fixed this same break independently — the archived
  phase-1 launch surface has now cost three stops in one cell; flagged
  for a durable note in the experiments skill after this cell resolves.
