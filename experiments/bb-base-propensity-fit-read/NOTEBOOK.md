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

### 2026-07-11 -- phase-1 build (agent, on branch exp/bb-base-propensity-loop, BUILD ONLY -- no launch)

Built the phase-1 harness per AMENDMENT.md sections 5 and 7, following phase 0's
authorization (all three floors passed). No Modal run, no git commit/push
performed by this build; the lead reviews and launches separately.

**New files:** `build_fit_id_manifest.py`, `build_fit_pool.py`,
`cloud/modal_bb_phase1.py`, `freeze_scorer_base.py`, `score_bb_holdout.py`,
`near_dup_sweep_bb.py`, `test_bb_phase1_smoke.py`. None of the pinned files
(`cell.yaml`, `gates.yaml`, `cloud/modal_bb_phase0.py`) were touched.

**Fit-surface ID-manifest (`analysis-committed/fit_surface/fit_ids.jsonl`,
committed):** reconstructed AL's exact 1,662-row A0 surface from two
independent AL artifacts (`al_source_graded` rows_graded.jsonl,
`al_fit_pool_v21` pool_v21.jsonl), cross-checked row_key sets and gold_class
identical between them, and asserted 0 row_key overlap against the vendored
750-row read surface (AMENDMENT.md section 2.3's disjointness claim,
independently verified rather than assumed).

**Fit pool staged:** `fit_pool.jsonl` (1,662 rows, all qhash-verified against
the committed manifest) uploaded to a newly created PRIVATE HF dataset repo
`professorsynapse/eh-bb-fit-pool` (created by this build; did not exist
before), verified by round-trip download (1,662 rows).

**Modal phase-1 script (`cloud/modal_bb_phase1.py`, NOT run):** generates+grades
the 1,662-row fit pool on base (own behavior labels, not AL's AI-TRUE grades)
and extracts pre-generation L0-L36 states for both the fit surface and the
750-row read surface (read-surface behavior labels reused from phase 0,
not regenerated). GPU-stage-only; no local fit or scoring happens in this
script. New volume `eh-bb-phase1-logs`, run_tag `bb-phase1-r1`, 3-hour timeout.
Cost estimate built at gate-open (not in the original AMENDMENT, which only
priced phase 0): ~65-100 min wall time, ~$1.40-$2.50, well within a $15 cap,
but the lead must set an explicit `MODAL_COST_CAP_USD` for phase 1 rather than
assuming phase 0's number.

**Local CPU fit/score scripts:** `freeze_scorer_base.py` implements AL's
recipe (PCA-128 seed 20260705, standardize, caution-residualize, mean-diff,
z-scale) with core fit-math functions copied verbatim from H9's
`freeze_scorer.py`; BB-FID-1 (determinism, refit twice, compare d_raw) and
BB-FID-2 (recipe-parity knob assertion) both pass on synthetic data.
`score_bb_holdout.py` scores the frozen base direction on the read surface and
adjudicates BB-P1-G0/G1/G2 exactly per gates.yaml. `near_dup_sweep_bb.py` was
actually RUN (not just smoke-tested; all its inputs are local, no GPU needed)
and reproduced H9's own sweep result over the same KUQ population: 0 flagged,
max overlap 0.75, committed to `analysis-committed/phase1/near_dup_flagged.json`.

**STOP-and-report item (not resolved unilaterally, flagged for the lead):**
gates.yaml's BB-FID-2 literal wording is "freeze_scorer.py sha256 == H9 pinned
scorer." A whole-FILE hash match against H9's experiment.yaml pin
(`1b64ddd5d24477aa779db58f181e3f50e24c1258bd7df18c731896fcf2d7da8d`, read on
the h9-propensity-gate branch) is not achievable: `freeze_scorer_base.py`
necessarily differs from H9's file in I/O (BB's own base extraction/grades,
not AL's al_run_dir/al_extract_dir/al_graded) and in fidelity-reporting logic
(no on-disk prior array to cross-reference, AMENDMENT.md section 5.4). This
build implements BB-FID-2 as function-level verbatim-copy parity (the actual
PCA/residualization/mean-diff math, copied unchanged) plus a mechanical knob
assertion against AL's section-3.2 constants, and records both sha256 values
in the fidelity report for the lead to adjudicate at a future repin if
desired.

**Smoke tests:** 10/10 passed (`pytest test_bb_phase1_smoke.py -v`), covering
ID-manifest schema round-trip, an independent fit/read disjointness check, a
negative test (wrong-text pool rejected via qhash mismatch), the fake-activation
fit+score path end to end, the score_bb_holdout selftest gate logic, the
straddling-CI inconclusive-resolution rule, the near-dup sweep (real inputs,
not synthetic), and an import-preflight rehearsal of the Modal setup block in
a fresh `git clone --local` scratch clone (confirmed it lacks the untracked
experiment/phase1/probe legacy tree, then rehearsed the exact copy+PYTHONPATH+
import block from modal_bb_phase1.py). No model weights were loaded anywhere
in this build (host constraint: local 3090 busy, WSL2 VM would OOM).

**Not done in this build (deferred to the lead):** the Modal launch itself,
any git commit/push, and the actual GPU-produced extraction/generation this
harness is built to consume -- so freeze_scorer_base.py and score_bb_holdout.py
remain validated only on synthetic data pending the phase-1 GPU run.

- 2026-07-11 (lead adjudication of the builder's STOP-and-report item):
  BB-FID-2's signed wording demanded whole-file sha256 equality between
  freeze_scorer_base.py and H9's pinned freeze_scorer.py. That equality is
  unachievable by construction (different I/O surfaces, different fidelity
  reporting), so the line was an instrument-authoring error caught before
  launch. Repinned gates.yaml via bin/exp repin (3f23b51f -> 33fe08ad) to the
  fidelity intent: fit-math functions verbatim-identical to the H9 pinned
  scorer, AL 3.2 knobs asserted from cell.yaml, both file sha256 values
  recorded in the fidelity report. No outcome gate (BB-P1-G0/G1/G2) was
  touched; this is a fidelity-check definition repair, not a goalpost move.
  Next: full red-team pass over the phase-1 harness, then launch.

- 2026-07-11 (red-team verdict + lead adjudications, pre-launch): full
  red-team pass over the phase-1 harness returned 1 invalidating finding,
  4 non-blocking, and confirmed the BB-FID-2 repin preserves the fidelity
  intent (outcome gates byte-identical to signed values; fit-math functions
  verified verbatim-identical to H9's pinned scorer). Invalidating finding
  F1: the CPU fit and score scripts built the confab / unanswerable-refused
  cells without the degenerate/schema_valid guard that AMENDMENT section 4.1
  and the phase-0 counter both apply, so schema-broken generations (up to 15
  degenerate unanswerables vs only 32 confab positives on the read surface)
  could contaminate the certified positive class. Remediation dispatched
  before launch; the GPU stages are unaffected. Lead adjudications recorded
  BEFORE the run: (1) the gradeable guard (not degenerate and schema_valid)
  applies to both cells in both fit and score paths, including the BB-P1-G0
  evaluability counts and the honest-prior OOF; (2) the BB-P1-G2 caution
  control population is gradeable rows only, with an all-750-rows variant
  reported in the same gate report as a non-gating sensitivity line; the
  0.80 floor applies to the gradeable-only primary. These are pre-read
  interpretations of the signed instrument, not post-hoc choices.

- 2026-07-11 (remediation applied and verified, pre-launch): all four
  red-team fixes landed. F1: shared gradeable guard (not degenerate AND
  schema_valid) now gates both cells in both the fit path
  (freeze_scorer_base.build_gradeable_cells) and the score path
  (score_bb_holdout.build_gradeable_cells), including the BB-P1-G0 counts
  and honest-prior OOF; G2 primary population is gradeable-only with the
  all-rows variant reported non-gating. F2: dated correction note appended
  to AMENDMENT section 5.4 referencing the gates.yaml repin; no signed prose
  rewritten. F3: BB-FID-2 now machine-verifies normalized-source parity of
  the copied fit-math function bodies against H9's pinned scorer, in
  addition to the knob assertion; pass requires both. F4: post-join assert
  in modal_bb_phase1.py fails loud if any of the 1,662 fit rows misses
  gold_class. Smoke suite extended 10 -> 14 (schema-invalid answered row
  excluded from confab in both paths; degenerate row excluded; mutated
  fit-math body fails FID-2); 14/14 pass, re-run by the lead. Pinned files
  untouched (verified via git status). Launch authorized by the user under
  the standing BB cap; proceeding.

- 2026-07-11 (phase 1 run, fit, and READ-ONCE gate adjudication): the phase-1
  Modal run completed clean in 3,447 s on one A10 (first launch aborted inside
  a minute after the HF token was sourced empty from a nonexistent worktree
  .env; relaunched with the token verified non-empty from the canonical
  checkout). Artifacts pulled via the modal Python SDK (the CLI `volume get`
  fails with Errno 21 on directory trees in client 1.5.1; the SDK loop with
  skip-existing resume handled a transient upstream-storage error). Fit ran on
  CPU: BB-FID-1 determinism PASS, BB-FID-2 PASS (knobs plus function-body
  parity, h9 pin verified), G0 evaluability 205 confabs / 1,020 refusals on
  the guarded fit surface. Read-once gate on the 750-row vendored surface:
  BB-P1-G2 caution 0.9820 gradeable-primary (n=732) PASS; BB-P1-G1 PASS at
  AUROC 0.8179, CI [0.7190, 0.9042]. Near-dup sensitivity 0 flagged. Full
  verdict written to AMENDMENT section 12. Gate report committed at
  analysis-committed/phase1/gate_report.json; row-level pulls remain
  gitignored under analysis/.

## 2026-08-27 — Exhaust published to HF (aggregate shape)

Data-exhaust release, PI-approved in-conversation (explicit permission
2026-08-27, batch 3 of the exhaust backfill, task-56c61a). Built with the
data-exhaust skill (aggregate-only copy-everything mirror of
analysis-committed/: no question text, generation text, or hidden states;
verify_exhaust.py PASS including the --experiment-dir completeness check;
zero exclusions). 9 files / ~442 KB, built at repo commit 37eaa399.

- HF repo: `professorsynapse/eh-bb-base-propensity-fit-read` (dataset)
- HF revision: `e215b2021fcbc79662642abe2b0b0ae5bc90fa42`
