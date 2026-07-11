# H9 held-out reading gate for the confab-propensity direction on AI-TRUE notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

- 2026-07-11 (remediation, smoke tier, CPU-only, no GPU): addressed the pre-sign
  red-team (docs/review/h9-presign-redteam-2026-07-11.md), both blockers and all
  four concerns, per lead adjudication. No gate threshold changed.
  - B1 (FID-2 unwired): freeze_scorer.py now gates fid2_pass on the OOF-repro
    operands (oof_repro_pearson >= 0.98, |oof_repro_incell_auroc - 0.6802| <= 0.02);
    the full-sample in-sample readout is recorded non-gating. gates.yaml keys
    renamed FID-2_oof_pearson_min / FID-2_oof_incell_auroc_tol with an updated
    comment. Re-run: FID-1 cosine 1.0 / maxdiff 3.57e-9 PASS; FID-2 OOF-repro
    Pearson 1.0, AUROC 0.68016 (delta 4.0e-5) PASS; fidelity_pass=true, EXIT 0.
  - B2 (NameError): modal_h9_holdout.py launcher now prints STAGING_MODEL_REPO /
    STAGING_POOL_REPO; module compiles.
  - C1 (G0 lever): AMENDMENT section 5 + cell.yaml holdout.enlargement pin ONE
    enlargement of +250 rows by continuing the SAME default_rng(seed) stream, G1
    read once on the 750-row enlarged draw, max_enlargements 1, no re-draws.
  - C2 (near-dup unimplemented): added near_dup_sweep.py (committed producer;
    token-overlap Jaccard between held-out KUQ and fit-surface KUQ text via
    --data-root; emits row_keys-only near_dup_flagged.json). score_holdout
    --sensitivity now FAILS LOUDLY (FileNotFoundError) if the sidecar is absent,
    no default-clean. Smoke on the real 500-row draw: 363 held-out KUQ rows,
    n_flagged 0 at threshold 0.90 (max overlap observed 0.75).
  - C3 (unscripted pool / weak binding): added build_holdout_pool.py (deterministic,
    reads committed manifest + source JSONLs via --data-root, emits gitignored
    holdout_pool.jsonl). draw_holdout now writes per-row qhash = sha256(row_key
    \x00 question_text) into the committed manifest (hash committed, text NOT).
    Modal join verifies each staged row's qhash, not just row_key set equality.
    Pool-builder smoke: 500 rows, all qhash verified.
  - C4 (label schema footgun): pool-builder emits + asserts label in the source
    domain {known, unknown}; the Modal gold-join now crashes on any other value
    instead of defaulting gold_class to None. Pool-builder smoke label split
    known 97 / unknown 403.
  - NITS: N1 classify_reading resolves a PASS/FAIL straddle to INCONCLUSIVE
    explicitly (enforces the AMENDMENT straddle rule, not evaluation order). N2
    amendment_ai_verdict_extract_gen.py added to experiment.yaml inputs; two new
    scripts added to instrument.modules. N3 draw iterates sources in sorted order
    so the RNG stream is independent of YAML key order. N4 score_holdout records
    held-out prop_z/caution_z mean+std as a non-gating L24 z-scale sanity line.
    N5 score_holdout asserts manifest size in {500, 750} and that every row_key
    has a graded row before scoring.
  All CPU smokes pass; nothing signed, no GPU, no Modal, no HF upload.
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

- 2026-07-11 (instrument repair, build environment only, pre-run): first Modal
  launch failed at IMAGE BUILD (no GPU spend, no container ran): the harness
  installed transformers from git HEAD (5.14.0.dev0), which now requires
  huggingface_hub>=1.5.0 and conflicts with the pinned huggingface_hub<1.0.
  Re-pinned to transformers==4.57.1, the pair the j-space-localization Modal
  harness proved on this same model class and task shape (extraction +
  generation, Qwen3-4B). No gate, contrast, prompt, grader, or draw change; the
  registered draw and all committed manifests are untouched. Re-signed to
  update the pinned SHA of cloud/modal_h9_holdout.py (old 2db96e1d5613...,
  new a17a68cbc7c5...). Process note: the exp CLI has no repin verb for a
  signed experiment, so the status field was flipped signed->draft by hand
  for one CLI re-sign and back; deviation authorized by the lead because no
  run had consumed the instrument (the failed image build spent no GPU and
  ran no container). Tooling gap filed in TODO.md (exp repin verb).

- 2026-07-11 (instrument repair 2, container import environment, pre-data): two
  launch attempts consumed no evidence. Attempt 1 (an undetached launch) never
  executed GPU work: the local entrypoint spawned the function and exited,
  which stopped the app and reaped the container before it started (operator
  error; the harness is designed for a detached launch). Attempt 2 (detached)
  cloned the repo, downloaded base+adapter+pool, passed the pool
  manifest/qhash checks, then crashed at extraction start:
  `ModuleNotFoundError: No module named 'amendment_s_correctness_probe_extract'`.
  Root cause: the archived entry script's flat sibling imports only resolve in
  the LOCAL checkout because an untracked legacy tree sits at
  experiment/phase1/probe/; a fresh clone has no such tree. Two independent
  breaks were found by rehearsing the pinned commit in a clean checkout:
  (1) flat module names need the archive legacy-wrapper-tree installed at its
  designed experiment/phase1/probe/ location plus PYTHONPATH containing the
  workspace root and that directory; (2) load_baseline_system_prompt() resolves
  the AC config at its pre-rename path phase3_ac_doubt_coupled_intervention.yaml,
  renamed at d55b7d26 to
  experiments/doubt-regulated-caution/ac_doubt_coupled_intervention.yaml with
  prompt.system verified byte-identical, so the harness shims the old path with
  the tracked file. The repaired harness performs both installs after clone and
  adds a fail-fast import preflight (mirroring the entry script's import order,
  including its path_compat-first caching) BEFORE any model download. The full
  setup+preflight sequence was rehearsed green in a clean pinned-commit
  checkout. No scorer, pool, draw, contrast, prompt, or gate logic changed; the
  registered draw and committed manifests are untouched. Repinned via the new
  `bin/exp repin` verb (its first production use): cloud/modal_h9_holdout.py
  old a17a68cbc7c5..., new aded92aed142..., reason recorded in
  instrument.repins; `exp validate` OK. GPU spend so far: attempt 2 burned
  roughly 10-15 A10G-minutes (clone + HF downloads + crash), well inside the
  $15 cap.

- 2026-07-11 (instrument repair 3, post-generate join + checkpointing,
  pre-score): attempt 3 was the first COMPLETE GPU pass. Preflight imports OK
  in-container (repair 2 verified), extraction finished all 500 rows with the
  in-run fidelity spot-check passing (max_abs_diff_L24 = 0.0 on n=3), and
  generation+grading finished all 500 rows. The harness then crashed at its
  own step 4b: it read gen/rows_graded.jsonl but the entry script's generate
  stage writes gen/rows.jsonl (fields row_key/refused/answered/schema_valid/
  degenerate/prompt_len/config_sha + answer_text). Because checkpoint_once
  only mirrored TOP-LEVEL files and the stage trees were only mirrored in the
  final step, the completed extraction and generation outputs were lost with
  the container, and Modal's automatic retries would have recomputed
  everything just to crash at the same line; the app was stopped to cut spend.
  Repair (repin 3, old aded92aed142..., new 844f4c7bfbb6...): (1) step 4b
  reads gen/rows.jsonl; (2) checkpoint_once now mirrors the extract/gen trees
  during the run (only-new safetensors, refreshed metadata, atomic); (3) at
  container start the harness restores any checkpointed stage trees into /tmp
  so a retry resumes instead of recomputing -- safe because the entry script's
  own resume logic skips rows already present in its out-dir rows.jsonl and
  hard-fails on config_sha mismatch. Join and mirror/restore semantics
  unit-tested locally (scratchpad test, all pass); no scorer, pool, draw,
  prompt, contrast, or gate change; registered draw and manifests untouched.
  Estimated cumulative spend after three attempts: roughly 1.0-1.5 A10G-hours
  (~$1.5), inside the $15 cap. No evidence consumed: no scored artifact
  exists yet; the gates remain unadjudicated.
