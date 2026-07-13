# H9 held-out reading gate — adversarial pre-sign review

Date: 2026-07-11. Reviewer posture: assume the instrument is an artifact and try
to prove it. Target: `experiments/h9-propensity-reading-gate/` on branch
`exp/h9-propensity-reading-gate` (worktree
`/home/profsynapse/code/ehr-worktrees/h9-propensity-gate`). Read in full:
`AMENDMENT.md`, `cell.yaml`, `gates.yaml`, `NOTEBOOK.md`, `freeze_scorer.py`,
`draw_holdout.py`, `score_holdout.py`, `cloud/modal_h9_holdout.py`,
`experiment.yaml`, `.gitignore`, and the reused GPU harness
`archive/experiment/phase1/probe/amendments/amendment_ai_verdict_extract_gen.py`.
Governed cross-refs read: `experiments/radial-anti-propensity-steering/AMENDMENT.md`
(Amendment AL), `docs/review/h9-propensity-reading-gate-feasibility-2026-07-10.md`,
`docs/review/h9-holdout-candidate-inventory-2026-07-10.md`. Ran the CPU
frozen-scorer smoke against the canonical AL artifacts to verify the fidelity
numbers empirically.

Verdict: **NOT SIGN-READY. Two blockers.** Neither is a science/oracle defect —
the scorer is provably AL's scorer and there is no label leak — both are
sign-hygiene defects that pin a self-inconsistent instrument. The first is the
important one: as pinned, the fidelity gate FAILS and the launch is blocked,
which flatly contradicts the AMENDMENT prose that says it passes.

---

## BLOCKERS (must fix before sign)

### B1. The FID-2 respec is written in the prose but NOT wired into the gating code; as pinned, the fidelity gate fails and blocks the launch.

The AMENDMENT was respec'd pre-sign so that FID-2 is an **OOF-reproduction**
check (`AMENDMENT.md:108-120`): "the re-derived pipeline, executed in AL's exact
5-fold out-of-fold construction … reproduces the on-disk OOF `prop_z.npy` at
Pearson r >= 0.98 AND lands its in-cell OOF AUROC … within 0.02 of 0.6802." The
prose lists this as passing (r = 1.0, AUROC 0.68016).

The code does not compute that. `freeze_scorer.py:206-207` sets `fid2_pass` from
`prop_full` — the **full-sample, in-sample** readout:

```python
pearson = float(np.corrcoef(prop_full, prop_z_disk)[0, 1])          # :200 (full-sample)
incell_auroc = ... prop_full[confab_idx], prop_full[un_ref_idx] ... # :201-203 (in-sample)
fid2_pass = (pearson >= 0.98 and auroc_delta <= 0.02)               # :206-207
```

The OOF reproduction that the respec now calls FID-2 is computed at
`freeze_scorer.py:217-222` but stored only under `diagnostic_oof_reproduction`
and **never feeds `fid2_pass`**. `gates.yaml:15` still carries the old
definition in its comment ("frozen full-sample prop_z vs on-disk OOF
prop_z.npy"). So the pinned gate and the AMENDMENT prose disagree about what
FID-2 even is.

Empirically confirmed by running the smoke against the canonical AL fit
artifacts (`freeze_scorer.py --smoke --data-root <canonical>`):

```
FID-2: pearson_prop_z 0.9184  incell_auroc 0.8664  delta_vs_0.6802 0.1862  pass=false
diagnostic_oof_reproduction: r=1.0  auroc=0.68016
fidelity_pass=false   EXIT=1
```

`AMENDMENT.md:122-123` and precondition `§7.2` make a FID pass a hard launch
gate ("FID failure blocks the launch"). So the instrument, run exactly as
pinned, returns exit 1 and blocks its own launch — while the signed prose claims
FID-2 passes. Signing this pins that contradiction.

The respec itself is legitimate (see the CLEAN section: FID-1 pins the direction
bit-for-bit, the OOF reproduction pins the pipeline, and the respec was made
before any held-out result existed to peek at). The defect is purely that it was
absorbed into prose and NOT implemented. Fix before sign: make `fid2_pass` read
the OOF-reproduction operands (`oof_repro_pearson`, `oof_repro_incell_auroc`),
and update the `gates.yaml:15` comment and, ideally, the key names so the machine
gate and the prose name the same thing. The NOTEBOOK (2026-07-11) correctly
flagged this as a "locked-spec adjudication, NOT changed here" and punted it to
the lead — this review confirms it is a genuine blocker, not a cosmetic one.

### B2. `modal_h9_holdout.py:278` references an undefined name; the launcher crashes on the launch path.

```python
print(f"[modal-h9] repo@{repo_commit[:12]} staging={STAGING_REPO}")   # :278
```

`STAGING_REPO` does not exist — the module defines `STAGING_MODEL_REPO` and
`STAGING_POOL_REPO` (`:56-57`). This line is in `local_entrypoint main()` after
all launch guards pass and immediately before `run_h9_holdout.spawn()` (`:279`),
so it raises `NameError` and aborts. It fails safe (no `.spawn()`, no GPU spend),
but the pinned launcher cannot run as written. Because signing pins this file,
fix before sign (or the harness-builder/lead's post-sign GPU validation will
hit it). One-line fix: reference `STAGING_MODEL_REPO`/`STAGING_POOL_REPO`.

---

## CONCERNS (sign-safe but record; several are pre-registration integrity)

### C1. The H9-G0 enlargement remedy is not pre-stated tightly enough — it is a goalpost lever.

`AMENDMENT.md:190-194` says if G0 is unmet "the draw is enlarged (a pre-stated
remedy, not a goalpost move)," but nothing states *how*: `cell.yaml` fixes one
`seed: 20260711` and `draw_size: 500` with no enlarged size, no fresh-seed rule,
and no "read G1 once on the enlarged draw" rule. As written, an experimenter
could enlarge repeatedly and re-read G1. Trigger probability is low (expected
~35 confabs vs the floor of 20, from 403 unanswerable rows), but a remedy that is
invoked *only when the result is inconvenient* must be seed-fixed and read-once to
stay non-leverable. Recommend pinning in `cell.yaml`: the exact enlarged
`draw_size` (or increment), a distinct deterministic seed (or an explicit
continuation of the same RNG stream), and a one-read rule.

### C2. The registered near-duplicate sensitivity check has no committed implementation and silently reads "clean."

`AMENDMENT.md:296-309` and `gates.yaml:42-46` register a KUQ near-duplicate
sweep. But `score_holdout.py:186-188` only *reads* a `near_dup_flagged.json`
sidecar; no script in the experiment *produces* it. `draw_holdout.py` never
touches sensitivity, so `gates.yaml:44`'s claim that the metric is "finalized by
the draw script at sign time" is false. With no producer, the sidecar is absent,
`flagged` defaults to the empty set, and the sensitivity block reports
`n_flagged: 0, verdict_flip: false` regardless of actual near-duplicates — a
false "clean." This is non-gating and low severity (exact-text collisions are
already zero per the inventory memo §4), so it WEAKENS the sensitivity claim, not
the gate verdict. Fix: wire the sweep (token-overlap/cosine between held-out KUQ
and fit-surface KUQ questions, CPU, needs the gitignored question text) as a
committed step, or downgrade the AMENDMENT's "registered" language to "attempted
if a flagged sidecar is supplied."

### C3. The staged question-text pool is assembled by an unscripted manual step, and the row_key check does not verify the text↔key binding.

The Modal harness fetches `holdout_pool.jsonl` (question text keyed by row_key)
from a private HF dataset repo the user uploads by hand (`modal:52-60, 176-177`).
No committed script builds that pool from the committed ID-manifest + the
gitignored source JSONLs. The equality guard (`modal:185-190`) compares row_key
**sets** only; it catches a wrong row *population* but not a pool that maps the
right row_keys to the *wrong question text* (a join/shuffle bug in the manual
build), which would silently feed wrong prompts into extraction and generation.
This is the main "could someone re-run from committed files alone?" gap: no.
Recommend a committed pool-builder (reads `analysis-committed/holdout_draw/
holdout_ids.jsonl` + source JSONLs via `--data-root`, emits `holdout_pool.jsonl`
deterministically) so the text↔key binding is reproducible, plus a per-row hash
or count assertion beyond set equality.

### C4. The pool label schema is coupled across three consumers with incompatible field semantics; a mismatch collapses the gate.

`draw_holdout.py:96` writes the committed manifest's `gold_label` already mapped
to `{answerable, unanswerable}`. But `extract_gen.load_pool` (`:117-120`) expects
`label`/`gold_label` in `{known, unknown}`, and the Modal gold-join
(`modal:216`) does `l2g.get(r.get("label"), r.get("gold_class"))` also expecting
`{known, unknown}`. The staged pool must therefore carry `label` in
`{known, unknown}` (as the source JSONLs do), NOT the committed manifest's
already-mapped `gold_label`. If whoever builds the pool copies the committed
`gold_label` field instead, every row's `gold_class` becomes `None`, `is_confab`
is all-False (`score_holdout.py:175`), and G0 collapses to
`INCONCLUSIVE-BY-POWER`. This fails safe (toward inconclusive, never a false
pass), but it is a real latent footgun. Fix: pin the staged-pool schema and
assert it in the pool-builder (C3) and/or at the top of the Modal join.

---

## NITS (hygiene)

- **N1.** `score_holdout.py:116-120` `classify_reading`: the PASS predicate
  (`auroc>=0.62 and ci_lo>0.55`) and the FAIL predicate
  (`auroc<=0.55 or ci_hi<0.60`) are not provably disjoint; the code resolves any
  overlap by evaluation order (PASS wins). The overlap region requires the point
  estimate to fall above the bootstrap CI upper bound, which a percentile CI
  makes rare, so this is practically unreachable — but the AMENDMENT's "a CI that
  straddles the boundaries → inconclusive" is not literally enforced. Consider an
  explicit precedence note or a runtime disjointness assertion.
- **N2.** `experiment.yaml` `instrument.pins: {}` is empty and the load-bearing
  GPU harness `amendment_ai_verdict_extract_gen.py` is neither in `inputs` nor
  `pins` — it is referenced only as a path string in `modal:67`. It is covered by
  the `EHR_REPO_COMMIT` pin at launch, so provenance is intact, but it is
  invisible in the manifest. Recommend adding it to `inputs`.
- **N3.** `draw_holdout.py:88` consumes the RNG per source in `stratify_targets`
  dict order; reordering the YAML keys silently changes which rows are drawn at
  the same seed. Reproducible-as-committed via the committed ID-manifest + source
  SHAs, so low severity.
- **N4.** G2 (caution control) reads L35 while the propensity read is L24
  (`score_holdout.py:168-172`), so G2 is an *indirect* health control for the
  L24 read: a subtle L24-only corruption could pass G2. Mitigated by FID-1/FID-2
  (which pin the L24 construction) and the extraction determinism spot-check.
  Consider a light held-out L24 z-scale sanity check (mean/std not wildly off the
  frozen fit scale).
- **N5.** `score_holdout.py` has no explicit DONE-marker or n==500 completeness
  assertion; it relies on `load_stack`/the graded-join raising on a missing
  row_key. That fails loudly (not silently), so acceptable, but an explicit
  completeness check would be cleaner.

---

## Checked and CLEAN (no invalidating findings)

- **No oracle/label leak into grading.** `run_generate` grades behavior
  (`refused`/`answered`/`schema_valid`/`degenerate`) purely from the model's own
  emission `answer_text` (`extract_gen:385-394`); it never reads gold answerability
  or aliases. `gold_class` is joined *after* generation from the pool's
  answerability label (`modal:216-231`). No correctness grading occurs anywhere,
  so gold answers/aliases never enter any label. The propensity contrast label =
  gold_class(unanswerable) × behavior(answered vs refused); the behavior half is
  ungraded-against-gold and the gold half is a dataset property, neither reachable
  by the pre-generation-anchor activation the scorer reads.
- **No fit↔held-out circularity.** `freeze_scorer` fits only on AL's 1,662-row
  surface (`:145-146` asserts 1662); the frozen objects are created before any
  held-out extraction exists. The held-out draw is the set-arithmetic complement,
  verified zero exact-text collisions against the fit surface
  (inventory memo §4). The caution residualization is *conservative* — it removes
  the refusal signal that correlates with the negative class, so it cannot inflate
  held-out AUROC.
- **FID-1 exact / scorer identity.** Empirically, the re-derived `d_raw`
  reproduces the on-disk `d_raw.npy` at cosine 1.0, max|diff| 3.57e-9. The
  OOF-reproduction diagnostic reproduces AL's `prop_z.npy` at r=1.0 and in-cell
  AUROC 0.68016 == 0.6802. Together these prove the frozen PCA/scaler/caution/
  residualization pipeline and folds/seeds ARE AL's construction — the full-sample
  scorer differs from AL only in using all rows, which a deployable single-row
  scorer must.
- **FID-2 respec is scientifically sound and clean-before-sign.** Comparing a
  full-sample in-sample readout to an OOF number was genuinely apples-to-oranges;
  the OOF-reproduction definition is the correct like-to-like check. The smoke ran
  only on AL's own 1,662 fit rows — no held-out extraction existed — so no
  held-out result was peeked. (The *implementation* of this respec is B1.)
- **Grading config byte-identical to AL A0.** Same reused harness, greedy
  `max_new_tokens=96` (`extract_gen:85,377`; `cell.yaml:48`), `do_sample=False`,
  matching AL's A0 generation config.
- **Statistics.** Bootstrap resamples at the row unit over the contrast rows,
  fixed seed 20260711, 1000 resamples (`score_holdout.py:99-112,152-153`);
  class-loss skips are negligible (~35 positives in ~403 rows). AUROC tie-handling
  is sklearn's in both the in-cell and held-out paths — identical. The contrast
  (confab vs unanswerable-refused) and denominators match AL's readout_quality
  contrast (`AMENDMENT.md §4.1`).
- **Containment.** `.gitignore` excludes `*.safetensors`, `rows.jsonl`,
  `rows_graded.jsonl`, `*pool*.jsonl` even under `analysis-committed/`; committed
  artifacts are limited to the ID-manifest (row_key + source + gold_label) and the
  aggregate gate report; `analysis-committed/` is currently empty. Modal performs
  no external upload of outputs (Volume-only, pulled with `modal volume get`).
- **Launch guards real.** `local_entrypoint` refuses to spawn unless
  `EHR_LAUNCH_OK==slug`, `MODAL_COST_CAP_USD` set, `EHR_REPO_COMMIT` (>=12 chars)
  set, `HF_TOKEN` present (`modal:258-274`), all before any `.spawn()`. Retries
  capped at 2; checkpoint daemon + DONE marker; a partial run cannot be scored as
  complete because `score_holdout` requires every manifest row_key's extraction
  and graded row and raises on any missing (loud failure, not silent partial).
