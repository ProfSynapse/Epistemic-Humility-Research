# Base-model confab-propensity fit and held-out reading gate on untrained Qwen3-4B notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

### 2026-07-11 -- scaffold + DRAFT design (agent, on branch exp/bb-base-propensity-loop)

Scaffolded `bb-base-propensity-fit-read` (type probe-fit) and drafted the full
design as the before-training bookend to H9. Nothing signed, nothing launched,
no HF touched, no spend. Committed artifacts so far: AMENDMENT.md, cell.yaml,
gates.yaml, experiment.yaml, cloud/modal_bb_phase0.py, the vendored H9 read-surface
ID-manifest + its PROVENANCE.md, this notebook.

**Governed docs read this session (with the lines the design leans on):**
- `experiments/h9-propensity-reading-gate/AMENDMENT.md` (H9 branch), full: outcome
  INCONCLUSIVE-BY-POWER (:338-351); 4 confabs / 605 unanswerable, 99.3% refusal on
  AI-TRUE (:360-364); G0 floors 20/20 (:190-203); read gate lines (:168-181);
  caution control 0.90 (:182-189); prompt provenance (:57-59); disjoint complement
  draw (:127-131); FID-1/FID-2 (:100-120); enlargement-does-not-fix-a-rate (:344-347).
- `experiments/h9-propensity-reading-gate/cell.yaml` + `gates.yaml` + `experiment.yaml`
  (H9 branch): staged pool `professorsynapse/eh-h9-holdout-pool`/`holdout_pool_enlarged.jsonl`,
  ID-manifest schema (row_key/source/gold_label/qhash), repin audit trail.
- `experiments/radial-anti-propensity-steering/AMENDMENT.md` (AL): fit surface 1,662
  rows and its AI-TRUE grades (:116-118); fit recipe L24 PCA-128 seed 20260705,
  standardize, caution-residualize, mean-diff confab-vs-unanswerable-refused (:122-142);
  refit-per-checkpoint, cosine-0.17 transfer, single-seed caveat (:208-214).
- `docs/review/paper3-direction-provenance-2026-07-10.md` section 3: the
  propensity direction has NO base/instruct reading validation; only ever fit on
  AI-TRUE; checkpoint-specific.
- `archive/experiment/phase1/probe/amendments/amendment_ai_verdict_extract_gen.py`:
  confirmed `--adapter-repo` defaults None and `--base-model` accepts a hub id or
  local path, so base-only generation is valid; the generate stage emits
  refused/answered/schema_valid/degenerate and grades with the byte-identical AL
  A0 scorer (`import scorers`).
- `TODO.md` rows H9 and BB (the PI directive).

**Key design decisions:**
1. Reuse H9's EXACT 750-row read draw (vendored ID-manifest, byte-identical,
   sha256 86e2dc00...) and AL's EXACT 1,662-row fit surface. BB and H9 then differ
   ONLY in the model under test, which is what makes them a clean before/after-
   training bookend, and the fit/read surfaces stay disjoint by construction
   (H9's holdout is the complement of AL's fit surface).
2. Vendored the H9 manifest into BB's `analysis-committed/` because the H9
   experiment dir is NOT on main (only its review docs are); BB clones off main,
   so it must carry its own copy. Containment-safe: IDs + qhash, no text.
3. Phase 0 = generate+grade only on base (no extraction, no fit). Phase 1 (fit +
   held-out reading gate) runs ONLY if phase 0 passes its floors. Actuation is a
   later phase, explicitly out of scope here (matches the lead's framing).
4. Phase-0 decision rule protects BOTH propensity cells AND schema-follow, not
   just the positive cell the PI expects: BB-P0-A schema_valid_frac >= 0.60,
   BB-P0-B confab >= 20, BB-P0-C honest_unanswerable_refusal >= 20. Any miss =>
   registered negative-feasibility record naming the starved condition, no phase 1,
   no goalpost move, NO draw enlargement (a behavior-RATE problem is not fixed by
   more rows -- H9 proved this).
5. Phase 1 re-FITS on base with AL's recipe; it does NOT reuse H9's AI-TRUE frozen
   objects (those answer a transfer question, which AL §7 predicts fails at cosine
   0.17). Fidelity gates redefined as determinism + recipe-parity + recorded SHAs,
   since no prior base direction exists to reproduce.

**The central feasibility insight (why this design earns its keep):** H9 died
because the TRAINED model starved the POSITIVE cell (almost never confabulates).
The untrained base faces the MIRROR risks, and the PI's "base is confab-rich, so
power for free" only covers one of them. The negative cell (honest unanswerable
refusal) can starve if base rarely refuses, and the schema-contract prompt (base
was never SFT'd on that JSON) can starve BOTH cells via degeneracy. Phase 0
measures all three before any fit/gate work.

**Open questions logged for the lead (AMENDMENT section 10):**
- Load precision 4-bit (bookend parity) vs bf16 (cleaner base; bf16 two-signal
  precedent). Draft defaults 4-bit.
- Phase-1 reading-gate anchoring: absolute H9 lines (Choice A, default) vs lines
  derived from base's measured in-cell excess (Choice B).
- BB-P0-A schema floor value 0.60 (no base prior -- most uncertain number here).
- BB-P1-G2 caution floor: absolute 0.80 vs relative to measured base in-cell.
- Base hub REVISION must be pinned at sign (harness reads BB_BASE_REVISION /
  cell.yaml model.revision = PIN_AT_SIGN).
- Confirm the vendored-manifest approach vs depending on H9 merging to main.
- Predictions scoreboard left empty for PI + orchestrator.

**Deviations from H9's shape (deliberate, all flagged in the AMENDMENT):**
- No private model-staging repo (base weights are public; H9 had to stage a local
  checkpoint). Harness pulls base from the hub at a pinned revision.
- Extraction stage dropped from the phase-0 harness (phase 0 needs labels, not
  activations).
- Output is a counts-only density_report.json (H9's headline was an AUROC gate
  report); phase-0's job is feasibility density, not a reading number.
- FID gates are determinism/recipe-parity, not cross-reference reproduction of an
  on-disk array (there is no prior base array).

**Not done in this draft (correctly deferred):** phase-1 `build_fit_pool.py`, the
committed fit ID-manifest, the phase-1 extraction+fit+score harness, and the new
private fit-pool staging repo -- all authored at phase-1 gate-open if phase 0
passes. The phase-0 harness has NOT been run (`modal run` reserved for the lead
after user sign-off + spend approval).

- 2026-07-11 (lead adjudication + sign + phase-0 launch): the six draft open
  questions were adjudicated (4-bit for bookend parity; absolute H9 gate lines,
  Choice A; schema floor 0.60; caution floor absolute 0.80 with the in-cell
  prior recorded non-gating; predictions recorded; vendored manifest confirmed
  byte-identical to H9's enlarged manifest, sha256 prefix 86e2dc00400792ef).
  Hub revision pinned: Qwen/Qwen3-4B @ 1cfa9a7208912126459214e8b04321603b3df60c.
  Predictions at sign: user = all three phase-0 floors pass; orchestrator = all
  pass weakly (~50%), most likely failure BB-P0-C honest-refusal floor. Signed
  (3 pins) and phase 0 launched on Modal A10G with user approval, cap $15,
  expected ~$1-2. The lead reviewed the phase-0 harness diff against the proven
  H9 harness before sign: import-environment block, qhash verification, tree
  checkpoint/resume, and the rows.jsonl join (H9 repair-3 lesson) all verified
  present and correct.

- 2026-07-11 (phase 0 adjudicated: ALL FLOORS PASS, phase 1 unlocked): the
  density probe ran clean on the first attempt (preflight OK, resume machinery
  inherited from H9 unused because nothing failed). Read-once against the
  locked floors: BB-P0-A schema-follow 0.976 vs 0.60 floor PASS (the release
  base holds the JSON contract almost perfectly); BB-P0-B confabs 32 vs 20
  floor PASS; BB-P0-C honest unanswerable refusals 558 vs 20 floor PASS.
  Committed aggregate report at analysis-committed/phase0/density_report.json.
  Prediction adjudication: the user called all three floors passing and was
  RIGHT; the orchestrator's weakly-held all-pass was right in outcome but its
  named most-likely-failure (the refusal floor) was maximally wrong in
  direction: base is heavily refusal-prone under this prompt (92.2% honest
  refusal on unanswerable rows) and even refuses 92/142 answerable rows (64.8%
  known over-refusal, far above AI-TRUE's 30/97). Base confabulates at 5.3%
  on unanswerable rows (32/605), roughly 8x AI-TRUE's 0.66%. Non-gating
  observation for the record: the untrained release model is already strongly
  abstention-biased under the schema contract prompt; the propensity contrast
  has mass on both sides, which is all phase 1 needs.
