# H9 held-out reading gate for the confab-propensity direction on AI-TRUE notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

- 2026-07-11 (smoke/diagnostic, CPU-only, no GPU, no model load): wired the
  three CPU scripts and the Modal harness to full working state and ran the
  pre-sign smokes. Results below are smoke tier, not the registered run.
  - FID scorer-fidelity smoke (`freeze_scorer.py --smoke`, 1,662 fit rows):
    FID-1 PASS emphatically (cosine 1.0, max abs elementwise diff 3.57e-9 vs the
    on-disk d_raw.npy; exact replication of AL's frozen direction). FID-2 FAIL as
    the gate is currently written: frozen full-sample in-cell AUROC 0.8664
    (delta 0.186 from AL's OOF 0.6802) and Pearson 0.9184 vs prop_z.npy, both
    outside the locked r>=0.98 / tol<=0.02 targets. Root cause is NOT a pipeline
    defect: the non-gating OOF-reproduction diagnostic reproduces AL's OOF prop
    readout exactly (Pearson 1.0 vs prop_z.npy, in-cell AUROC 0.68016 == 0.6802),
    proving the pipeline is faithful. FID-2 fails purely because it compares a
    FULL-SAMPLE direction evaluated IN-SAMPLE on its own fit rows (optimistic) to
    an OUT-OF-FOLD number. The held-out H9-G1 number carries no such optimism, so
    the 0.6802-anchored held-out gate stays honest. FLAGGED to the lead/red-team:
    FID-2's numeric definition is mis-specified against what the frozen scorer
    computes; the fix (compare a matched OOF reproduction, which passes at r=1.0)
    is a locked-spec adjudication, NOT changed here.
  - Held-out draw dry-run (`draw_holdout.py --smoke`, seed 20260711): complement
    16,834 (union 18,496 minus fit 1,662), per-source complement counts match the
    holdout memo exactly, per-source draw hits targets 226/137/40/35/24/23/15
    (500 total), namespace-disjoint (ah:: / ahx::), zero fit-surface orphans.
    Gold-label split 403 unanswerable / 97 answerable (the 403 unanswerable rows
    carry the confab-vs-un_ref contrast, ~35 expected confabs).
  - score_holdout.py: cannot smoke before the GPU lane exists (no held-out
    extraction on disk); validated by `--selftest` (scoring math + bootstrap CI +
    gate classification exercised on synthetic arrays; produced a well-formed
    PASS with CI, confirming the gate logic runs).
  - Wiring deviations flagged (not silently absorbed): (1) the three CPU scripts
    take a `--data-root` (default the canonical checkout) because the AL fit
    artifacts and the draw source JSONLs are gitignored and absent in the
    worktree; paths themselves are unchanged from cell.yaml. (2) freeze_scorer
    now persists the L35 PCA (pca35.joblib) that the draft skeleton omitted;
    without it held-out caution scoring had no transform (FID numbers unchanged).
    (3) the Modal harness REUSES the proven AL/AI extract+generate script
    archive/.../amendment_ai_verdict_extract_gen.py (--stage extract/generate,
    full L0..L36 layer list, staged base+adapter as local paths) rather than a
    fresh gpu_extract_gen.py, giving byte-identical extraction to AL; it also adds
    a second private staging dataset repo for the held-out question pool and a
    hard check that the staged pool row_keys equal the committed ID-manifest. The
    Modal harness is wired but UNTESTED (no GPU / no HF here); GPU validation is
    the harness-builder + lead step after red-team.
- 2026-07-11 (draft): scaffolded from the two H9 memos and Amendment AL
  (`experiments/radial-anti-propensity-steering/AMENDMENT.md`, the direction's
  origin). Wrote AMENDMENT.md (gates section 5), cell.yaml, gates.yaml, and
  skeletons for the three CPU scripts (freeze_scorer, draw_holdout, score_holdout)
  plus the Modal harness (cloud/modal_h9_holdout.py). Status stays draft: nothing
  signed, nothing launched. The frozen scorer, held-out draw, GPU extraction, and
  gate scoring are all specified but not wired (TODO(sign) blocks mark where the
  fit/harness code lands). Flagged in the report: the lead's pointer named
  `experiments/selected-setpoint-regulator` (that is Amendment AN, not AL) and
  asked the frozen scorer to reproduce `prop_z.npy` (which is OOF; the hard
  fidelity target is `d_raw.npy`). Both handled per AMENDMENT.md section 8.
