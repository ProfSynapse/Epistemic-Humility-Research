# Evidence-responsiveness on world-known QA: the M4 rebase (M4-WK) notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

- (add dated entries as the experiment progresses)

## 2026-07-17 DRAFT assembled (pre-sign; no sign, no run, no GPU, no commit)

DRAFT of the world-known M4 rebase, assembled per the PI's locked decisions from
the design derivation
(`/tmp/.../scratchpad/m4wk_design_report.md`). No `bin/exp sign`, no resolve, no
model/GPU, no git commit. `bin/exp validate` + `bin/exp regen` run from the
worktree to confirm structural validity at draft status.

### Pre-sign feasibility probe (MANDATORY - the check M4 skipped)

Every field the design injects or consumes, verified non-empty on the actual
PopQA source rows (`datasets/popqa/test.jsonl`, 14,267 rows) this session:

| Field | Source | Coverage | Verdict |
|---|---|---|---|
| gold answer (single) | PopQA `obj` | 14,267 / 14,267 (100%) | PASS |
| gold aliases | PopQA `possible_answers` (JSON-string list) | 14,267 / 14,267 (100%) | PASS |
| question text | PopQA `question` | 14,267 / 14,267 (100%) | PASS |
| category for distractor | PopQA `prop` | 14,267 / 14,267; 16 categories, min bucket 34 (`color`), none < 5 | PASS |
| correctness label | `detector_v2.grade_one_v2` / `grader._is_correct` over aliases | grader exists (M1 stack); aliases present (above) | PASS (derived post-generation, not a source field) |
| abstention label | `detector_v2.is_refused_v2` | reused verbatim (M1 stack) | PASS (derived post-generation) |
| per-row tipping dose | - | NOT present; KUQ doses do not transfer | must be REBUILT (channel-2 ladder), a build cost, not a source gap |

No infeasibility. Category buckets confirmed this session: director 1999,
screenwriter 1999, genre 1619, producer 1520, author 1514, composer 978, …,
religion 338, mother 187, color 34. Every `prop` bucket has ≥ 34 rows, so the
category-matched donor rule always has candidates.

### Seeds assigned (new, distinct, continuing the registered lineage past M4)

Lineage: M1 …714–16, M2 …717–18, M1b …719–20, M4 …721–23. M4-WK does NOT reuse
721–723; new distinct values:

| Seed | Use |
|---|---|
| 48260724 | bootstrap (channel-1 shifts, channel-2 survival, all CIs) |
| 48260725 | category-matched false-answer distractor permutation |
| 48260726 | blinded calibration slice(s) - correctness + abstention |
| 48260727 | native-fit / test split permutation (disjointness) |

### Build-time assertions (for the harness)

- **Native sign guard (MINOR m2).** Before pinning the native direction's
  negative-z sign, the build MUST assert in code that on the native FIT split
  `mean_raw_proj(confab) < mean_raw_proj(refused)` (raw, pre-negation projection).
  This guards a fit-inversion bug that would silently flip the confab-positive
  orientation for the freshly-fit native direction. The TRANSFER sign is
  empirically known from M2 and needs no such assertion. Pinned in
  `cell.yaml readout.native_sign_assertion`.

### Governance note

The current `experiments/margin-evidence-responsiveness` (M4) is to be resolved
by the LEAD as **void-by-design / superseded** by this slug
(`margin-evidence-responsiveness-worldknown`), citing the missing-gold-answer
feasibility gap (KUQ confab rows have no gold field, so the true_answer /
false_answer arms had nothing to inject). Do NOT delete M4 - keep it for
provenance and the red-team/design-derivation lineage it carries. This resolve is
the lead's action, not part of this draft.

### Open forks / decisions NOT covered by the PI decisions (flag for lead)

1. **Native reference-dose recipe.** The PI locked that native gets its own
   re-derived reference dose, but the exact recipe for a *freshly-fit* direction
   is not spelled out in a prior governed doc. Drafted as: same standardization
   the KUQ reference dose used (mu_c/sigma_c of the native fit manifest). The lead
   should confirm the recipe (or point to the doubt-snap dose-calibration step
   that set 12.608 for KUQ) before the native channel-2 stage. Marked RE_DERIVED
   in `cell.yaml directions.native.reference_dose_abs`.
2. **Native S1 AUROC tolerance = 0.05.** The task said "reproduces the native-fit
   AUROC within a stated tolerance"; I stated 0.05 AUROC (out-of-sample vs
   in-sample fit AUROC). Judgment, not derived - confirm.
3. **Correct-control ladder inclusion in channel 2.** The derivation's cost figure
   ladders both confab (400) and correct (360) rows. M4 gave knowns projection-
   only (no channel-2 margin test). I kept the correct-control ladder to anchor
   the channel-2 S1 separation-reproduction check (median confab margin < median
   correct margin), which doubles the ladder's per-direction control cost. If the
   lead wants M4's leaner posture (confab-only ladder, no separation S1), drop the
   360 correct rows from `channel2_margin.ladder_rebuild.rows` (saves ~3,600
   generations per direction).
4. **Refused-class target size** is "as available" (census remainder). If the
   abstention prompt yields very few refused rows, the native-fit refused arm
   (target 180) competes with the test refused control. Confirm the fit split
   takes priority (drafted that way: fit reserved first).
5. **Publish-as-exhaust intent** for PopQA generation text (data-exhaust license
   gate). Left as PENDING PI plus the skill's license gate, not decided in this
   draft. Note that MAJOR M3 already guarantees no generation text is committed
   regardless of this decision: the committed census carries only row_key, role,
   question_sha, and the correctness/abstention bits, while the generation text
   lives in a gitignored `analysis/census/*_gen_text.jsonl` sidecar. Publishing is
   therefore a separate, deliberate act through the `data-exhaust` license gate,
   never a side effect of committing the census.
6. **Repin mechanism for the two re-derived floor numerics** (RESOLVED, fork 6).
   The floor-freeze mechanism is `bin/exp repin`: a code-emitted, hashed,
   append-only repin record written to `instrument.repins` in `experiment.yaml`
   (with `old_sha256`/`new_sha256` and a `--reason`; it refuses a no-op and refuses
   unrelated drift). It is applied the moment the baseline gap (collapse floor) and
   the realized n (D2 floor) are measured, before any effect contrast, one repin
   per direction per floor. This satisfies the no-goalpost rule with an auditable
   hash chain. gates.yaml `rederived_floors.*.numeric_at_repin` and
   `cell.yaml` cite `bin/exp repin` explicitly.

### Confirmations

- No `bin/exp sign`, no `bin/exp resolve`, no git commit.
- No model loaded, no GPU touched, no generation. Only CPU inspection of PopQA
  jsonl for field coverage and category counts, and reads of the governed M1/M2/M4
  docs + the derivation report.
- `experiment.yaml` status left at `draft`.

## 2026-07-17 - Red-team, PI adjudication, and sign (lead)

Pre-sign red-team (adversarial, opus) returned NOT-READY: 1 BLOCKER + 4 MAJOR + 5
minor, all fixable without redesign, and it confirmed the primary (transfer) (d)
verdict survives every confound once the BLOCKER + one MAJOR are fixed. It also
pressure-tested the floor-freeze and cleared it: both floors are deterministic
functions of pre-committed populations and locked formulae, so there is no free
parameter to move after seeing the effect (the repin is defense-in-depth, not the
thing preventing a goalpost move).

Fixes applied and lead-verified:
- B1 (BLOCKER): added a transfer firing-strength floor to S1: baseline
  confab-vs-correct AUROC of the transfer negative-z projection on the test
  subset (400 confab / 360 correct-control) at the no-answer arm must be >= 0.70
  (PI-set at sign). Below it the KUQ direction does not fire on the world-known
  error class and the (d) test is VOIDED and lifted, never scored as
  (d)-not-earned. Falsifier conditioned on "transfer firing at baseline".
- M1: native-circularity caveat added; leg-2 specificity named as the
  anti-tautology control for both directions; transfer noted as additionally
  free of fit-circularity (disjoint KUQ fit), hence primary.
- M2: single-batching-regime attestation extended from the census to the two
  paired-contrast sites (the three channel-1 capture arms; the three channel-2
  survival arms).
- M3: generation_text moved to a gitignored analysis/census/ sidecar; the
  committed census carries only row_key, role/label, question_sha, and
  correctness/abstention bits (no row text in a committed path).
- M4: removed the `directions/` pattern from .gitignore (it shadowed the
  committed native c_hat); verified with git check-ignore (no match).
- minors m1-m5 and forks 1-6 applied as adjudicated (baseline gap on the test
  subset; native sign assertion; correctness slice n>=150 with a Wilson-bounded
  false-wrong rate and a <=0.10 interpretability condition on a null; self-blind
  relabel into sign-time vs run-time barriers; D2 conservative-anchor note;
  native 8x reference-dose multiplier stated with a ladder-bracketing
  requirement; correct-control kept in the channel-2 ladder; repin as the
  floor-freeze mechanism).
- Lead also fixed a pre-existing invalid-YAML construct (a flow-mapping setpoint
  with an unquoted `[direction]`) that would have crashed the harness YAML load,
  and scrubbed pre-existing em dashes and "load-bearing" from the committed
  prose.

PI adjudication (conversation 2026-07-17): PopQA-only; transfer primary + native
secondary; native funded for a full two-channel test; alias + blinded-judge-slice
grader; transfer firing floor 0.70; sign and launch. Scoreboard registered:
orchestrator EARNED/projection, PI EARNED/margin (Slot 2 is the differentiating
value). Publish-as-exhaust deferred (independent of sign; no row text committed).

Signed via `bin/exp sign margin-evidence-responsiveness-worldknown`. Next: build
(harness-builder, mandatory GPU preflight, single batching regime), then the
per-direction baseline/n repins freeze the two floors, then blinded correctness +
channel-2 calibration, analysis, adjudication, resolve. The void
margin-evidence-responsiveness (M4) is resolved separately as superseded.

## 2026-07-17 - Build-time interpretations (harness-builder), pre-grading

Two build-time decisions, recorded here (not only in the harness docstrings) so
they are auditable as decisions made BEFORE any grading result was seen, per
lead confirmation the same day:

- **Correctness calibration slice: stratification vs. scoring population.**
  gates.yaml SC2 says the n>=150 correctness slice is "stratified across roles
  (and across prop categories within the confab class)". `calibration.py`
  interprets this as: DRAW the slice stratified across all 3 census roles
  (confab / correct / refused), as a broader alias-grader sanity check, but
  SCORE the false-wrong RATE only over the confab-labeled subset of the drawn
  slice at score time -- a false-wrong event (a truly-correct answer the alias
  grader scored wrong, mislabeling the row confab) is only coherent for a row
  the census actually labeled confab. Lead-confirmed 2026-07-17, consistent
  with `build_calibration_pool.py`'s own documented-interpretation precedent.
- **Native mu_c/sigma_c/reference_dose_abs: runtime read, not sign-time
  constant.** cell.yaml marks these RE_DERIVED and "frozen at the
  direction-fit stage repin." `config.py` cannot hardcode them (unknown at
  sign), so the harness reads them at RUNTIME from the produced
  `c_hat_worldknown.json` (its `sigma` field for the write-side sigma_c;
  `fit_native.py` now also writes `calibration: {mu_c, sigma_c}` into that same
  record so the registered readout's z-standardization can read them there
  too), mirroring `dose_ladder.py`'s pre-existing native-sigma runtime-read
  convention. The governance record (cell.yaml's own text, repinned via
  `bin/exp repin` at the native-fit stage) is the audit trail; the produced
  JSON is the harness's actual read path. Lead-confirmed 2026-07-17 (fork A).
- Also fixed before any GPU capture/generation used them: `steer_lib.py`'s
  copy still set M1's `MARGIN_RENDER_MODEL`/`MARGIN_RENDER_REVISION` env vars
  instead of this experiment's own `M4WK_RENDER_MODEL`/`M4WK_RENDER_REVISION`;
  `capture_channel1.py`'s `registered_score()` omitted the `mu_c` term from
  cell.yaml's `snap_standardization` (numerically inert for every gate --
  AUROC is rank-invariant, every shift/gap/rate-difference is a paired
  difference invariant to a global additive constant -- but the registered
  formula, fixed rather than left as a silent deviation).

## 2026-07-18 - Transfer void, native ladder bracketing re-derivation (harness-builder + lead + PI)

- **Channel-1 firing gate**: transfer (primary) baseline confab-vs-correct
  AUROC = 0.3018 (95% CI [0.2647, 0.3396]) on the TEST subset, far below the
  0.70 floor and below chance; fresh baseline gap_z = -0.181, not strictly
  positive. Independently sign-verified (lead-dispatched analyst): the
  transfer direction reproduces AUROC 0.987 on its own KUQ population under
  this harness's exact sign convention, confirming 0.3018 is a REAL
  below-chance population reversal, not a sign bug. Per gates.yaml BLOCKER
  B1, the primary criterion (d) test is VOID and lifted to PI (PI decision,
  not scored as (d)-not-earned). Native (secondary) fires cleanly: baseline
  AUROC 0.8628, gap_z +1.642, fit-split-to-test reproduction within tolerance
  (abs diff 0.0436 <= 0.05). PI chose the full native two-channel secondary
  dissociation reading; transfer is dropped from channel-2.
- **Native collapse_floor_z frozen**: 0.8209213240458088 (= 0.5 x realized
  native baseline gap_z 1.6418426480916175), via `bin/exp repin` on
  gates.yaml, the moment the baseline gap was measured, before any
  true_answer/false_answer shift was computed. Native D1 leg-1 (median true
  vs baseline shift over confab = 0.592, CI [0.536, 0.669]) is BELOW this
  floor -- leg-1 fails. Leg-2 specificity PASSES (paired true-minus-false
  shift = 0.102, CI [0.053, 0.152], excludes zero, true larger).
- **Ladder bracketing failure and re-derivation**: the original 10-rung
  native ladder (multipliers 0.0625x-4.0x) left 349/400 (87.25%) confab rows
  right-censored at the top rung; only 51/400 had a genuine non-right-censored
  tipping dose (target ~308). Per cell.yaml's own
  `channel2_margin.ladder_rebuild.bracketing_requirement` text (report, do
  not silently right-censor a resolvable row; re-derivation reserved for
  lead/PI adjudication), this was reported and NOT resolved unilaterally --
  no floor freeze, no commit, no survival run happened before the report.
  PI approved re-derivation: cell.yaml `channel2_margin.ladder_rebuild.multipliers`
  extended with [6.0, 8.0, 12.0, 16.0] (original 10 rungs unchanged), frozen
  via `bin/exp repin` (cell.yaml ca7126f1... -> d43fdc2a...) BEFORE any
  survival contrast was computed. Per-rung generation-health indicators
  (non-empty rate, detector_v2 pattern-match rate, refused/answered/
  unparseable split) are being recorded at each new rung for the PI's own
  adjudication of which rungs are instrument-valid (degeneration guard,
  report-only -- no pass/fail rule is baked into the scripts). d2_absolute_floor
  remains UNFROZEN pending the PI's review of the re-derived bracketing_report
  and the degeneration indicators.
- **Process note**: a `run_in_background` wait watching a manually-disowned
  ladder-generate PID (rather than the harness supervising the actual
  generate command directly) completed without ever delivering its
  completion notification, even though the monitored process finished
  successfully ~2h earlier. Going forward: pass long-running GPU commands
  directly to a single `run_in_background` call (no nohup/disown/poll-wrapper
  indirection), and on any resume, verify on-disk state first rather than
  assuming a wait fired.
- **Second silent kill (extension run, rung_12)**: relaunching the extension
  directly under `run_in_background` (per the process note above) still died
  mid-rung-12, at 68/760 rows, no traceback, no summary.json. Diagnosis: NOT
  host OOM (free -g: 19G total / 17G available at the time; no OOM in
  dmesg) and NOT a code crash (no error in the log). The background task's
  OWN completion notification for that run arrived with status "killed" /
  "was stopped" -- i.e. the harness's background-task supervision itself
  terminated the task, not a host memory or code issue. Resumability
  semantics verified by reading `shared/utilities/run_log.py` and
  `steer_lib.run_rows` directly: `RunLog` is durable append-only and
  `run_rows` filters to `pending = [r for r in rows if row_key not in done]`
  before batching, so a resume APPENDS remaining rows in canonical order (no
  truncation/overwrite). rung_12's 68-row partial was an exact multiple of
  the batch_size (4), so a plain resume would have reproduced the identical
  batch grouping as an uninterrupted pass -- no real integrity risk was
  present. Regenerated rung_12 from scratch anyway (delete + relaunch) per
  the lead's suggested fallback, since it is cheap and removes all doubt;
  no contrast data was involved (pre-floor-freeze instrument calibration).
  Added RUNG_STARTING / RUNG_DONE / ALL_RUNGS_DONE terminal markers to
  `ladder_channel2.py`'s generate log so a future silent kill is visible at a
  glance against the last emitted marker.

## 2026-07-18 - Rung-validity ruling (lead + PI) and n=51 D2 floor freeze

**Rung-validity ruling (lead ruling, PI approval, recorded verbatim below
before the floor freeze):** "RUNG VALIDITY RULING: rungs >= 3.0x are
instrument-INVALID for tip detection (3.0x confab well_formed 0.007 /
degenerate 0.955; 4x-16x 100% degenerate both roles). The instrument-valid
dose band tops out at 2.0x. The 349 censored rows are unresolvable in
principle on this direction (coherence ceiling precedes refusal), so
cell.yaml's no-silent-censor clause is satisfied: the re-derivation was
performed and proved them unresolvable. The 2.0x rung stays valid
(majority-coherent, 0.733 well_formed confab); 19/51 tips sit there, and the
SC2 abstention slice + CG1 decoys are the check on whether those refusals are
real -- some 2.0x-tipped rows must be represented in the abstention
calibration slice."

**PI decision:** run D2 at the realized n_margin_eligible=51 (all 51 tips
occur at <=2.0x, the ruled-valid band). The 349 right-censored rows are
disposed of as instrument-unresolvable-in-principle on this direction, not
silently dropped: cell.yaml `channel2_margin.ladder_rebuild.bracketing_requirement`
is satisfied by the completed re-derivation (10 rungs, then a 4-rung
extension to 16.0x, both showing the identical censoring and a hard
generation-coherence ceiling above 2.0x -- see the two entries above this
one). No further ladder extension is authorized or warranted by this data.

**d2_absolute_floor frozen for native at n=51**, via `bin/exp repin` on
gates.yaml, AFTER this ruling was recorded and BEFORE any survival contrast
is computed (self-blinding order): formula `1.96 * sqrt(0.25 / n_margin_eligible)`,
n_margin_eligible(native) = 51, floor = 0.13722492664818098. transfer's
d2_absolute_floor remains unfrozen (void, BLOCKER B1, no floor is ever frozen
for a voided direction, mirroring collapse_floor_z's disposition).

Next: native channel-2 single-dose survival (3 arms, 51 margin-eligible rows,
one pinned batch composition, live-SC1 readback, S1 baseline-staleness gate
<= 0.05 read first), then D1+D2, then both SC2 blinded-grading shards
(ensuring 2.0x-tipped rows are represented in the abstention slice) handed to
the lead at the grading boundary without self-grading.

## 2026-07-18 - Survival generate bug (gold field), S1 gate FAILS for native channel 2, D1+D2 committed

**Bug, not a supervision kill:** the first native survival `generate` invocation
completed `no_answer_baseline` (51/51 rows, readback OK) then crashed with
`KeyError: 'gold'` at the start of `true_answer`, with a real traceback (not a
silent kill like the two prior ladder incidents). Root cause:
`survival_channel2.load_margin_eligible_rows()` copied question/aliases/category
from `popqa_pool.load_pool()` into each eligible row dict but dropped `gold`,
which `capture_channel1.context_for_arm` requires for the `true_answer` arm
(`row["gold"]`) and, via the distractor donor row, for `false_answer_placebo`.
`no_answer_baseline` never surfaced the gap (its `context_for_arm` branch
returns `None` before touching `row["gold"]`). Fixed by carrying `pr["gold"]`
through (one line); `batch_composition`'s `row_order_sha256` is unaffected
(hashes row_key order only), so the completed `no_answer_baseline` arm and its
composition file remained valid. Re-invoked `generate`; `RunLog` correctly
resumed with zero work for the already-complete baseline arm (same
fingerprint) and generated `true_answer` + `false_answer_placebo` fresh under
the SAME pinned composition (`row_order_sha256=011599327e...`). All 3 arms:
51/51 rows, live-SC1 first-batch and pass-completion readback OK,
`ALL_ARMS_DONE` marker seen.

**S1 gate (channel-2 baseline-staleness check) FAILS for native:**
`no_answer_baseline` survival at each row's own tipping dose = 0.2549
(13/51), ceiling 0.05 (gates.yaml `S1_baseline_reproduction` channel-2
bullet). Per that gate's `on_failure`, channel 2 for native is VOIDED / lifted
to PI here, NOT scored as a D2 (d)-not-earned failure. Raw D2 numbers are
still reported (survival_rates: baseline 0.2549, true_answer 0.9412,
false_answer_placebo 0.9412; paired true-minus-false diff point=0.0, CI
[-0.098, 0.098], excludes_zero=False; d2_absolute_floor_frozen=0.1372) but
their validity is undermined by the S1 failure: at doses meant to be each
row's own tipping point (defined as the smallest ladder rung where that row
first showed non-survival), 3 in 4 rows now "survive" in this separate
generation pass. This is a reproducibility-in-the-survival-regime finding
(same class of concern the S1 gate exists to catch), not resolved or explained
by this notebook entry -- reserved for lead/PI.

**D1 (channel 1, unaffected by the S1 channel-2 gate) reconfirmed via
`analysis.py`:** native leg-1 median shift = 0.5921 (CI [0.5364, 0.6694]) vs
frozen floor 0.8209 -- FAILS. Leg-2 paired specificity: true-minus-false
diff = 0.1022 (CI [0.0527, 0.1524]), excludes zero, true larger -- PASSES.
transfer leg-1 = -0.2172 (CI [-0.2368, -0.1976]; floor null, transfer void, no
substantive read); transfer leg-2 diff = -0.0399 (CI [-0.0545, -0.0253]),
excludes zero but FALSE shift larger, not true -- fails leg-2 specificity in
the direction required (reported for completeness only; transfer is void per
BLOCKER B1, this is not a scored result).

**Construct caveat on `C1_separation_reproduction` (native):** with 349/400
confab AND 354/360 correct-control rows right-censored at the ladder's top
rung (16.0x, itself already ruled instrument-invalid >=3.0x -- see the ruling
above), BOTH group medians collapse to the same censoring ceiling
(135.5093...), so `reproduces_m1_style_separation` reads False as a direct
consequence of the median statistic being degenerate under this much
censoring, not a substantive non-separation finding. Reported as-is (raw
number), flagged here as a caveat on interpretation.

Fixed `analysis.py::compute_D2` to return `None` (not raise) when a
direction's survival score file is absent, mirroring the existing
`load_separation_reproduction`/`frozen_floor` None-safe pattern -- transfer's
channel 2 was correctly never run after its channel-1 void, so the two-
direction loop in `main()` would otherwise hard-crash on `compute_D2("transfer")`.

Committed: `analysis-committed/channel2_survival/{native_survival_score.json,
native_batch_composition.json}` and `analysis-committed/results/m4wk_results.json`
(full raw D1+D2+gate-attestation dump, no verdict language, no row text).

HALTING here per the S1 gate failure and per instruction: reporting to lead,
not proceeding to build the SC2 blinded-grading shards until the void is
adjudicated (their purpose -- validating detector_v2 against a blinded
abstention judgment for D2 -- is moot while D2 itself is void, and building
them is the lead's call, not mine, given the significance of this gate
failure).

## 2026-07-18 - Adjudication: channel-2 void confirmed, no re-derivation; correctness calibration shard built; abstention slice skipped

Lead adjudication on the S1 failure: void confirmed, and because the D2
contrast has now been SEEN (true 0.9412 / false 0.9412 / diff 0.0), no
instrument change, re-derivation, or re-run of channel 2 is permissible for
this cell under the no-goalpost rule. The 0.2549-vs-0.05 ladder-vs-survival
reproducibility gap is reported straight as an instrument finding, not
diagnosed further within this cell (a separate diagnostic or a fresh
pre-registered cell, decided later, if wanted).

**Native D1 is a null-type result** (leg-1 sub-floor: 0.5921 < 0.8209), so per
gates.yaml SC2 its interpretation requires the alias-grader false-wrong
bound (null interpretable only if <= 0.10). Built the correctness
calibration shard accordingly:

- n=150 drawn, seed 48260726, largest-remainder role allocation:
  confab_on_answerable=117, correct_on_answerable=29, refused_on_answerable=4
  (the false-wrong rate is scored ONLY over the confab subset per gates.yaml;
  the other two strata are a broader sanity check on the alias grader).
- Lead-directed addition beyond the pre-existing calibration.py: (a) shard
  rows now also carry `gold_aliases` (needed for the adjudicator to judge
  correctness at all -- previously missing); (b) every drawn
  correct_on_answerable row is tagged `decoy_type: "clear_positive"` in the
  PRIVATE id_map (29 of them, clearing the >=25 CG1 floor) as a sanity check
  on the adjudicator's own accuracy before trusting their false-wrong calls
  on confab; (c) `score_correctness` now also computes a clear-positive
  agreement rate against these decoys once grading returns. NOTE: gates.yaml's
  own CG1 bullet ties the clear_negative/clear_positive AGREEMENT FLOORS
  (0.95 / 0.60) to the abstention slice's refusal-classification task
  specifically; there is no natural clear_negative analog for a correctness
  judgment here (the confab role IS the ambiguous class under test, so it
  cannot supply a ground-truth-WRONG decoy without circularity). Implemented
  exactly what was asked (>=25 clear_positive decoys + their agreement rate),
  not a literal application of the abstention CG1 spec -- flagging this
  distinction for the record rather than silently treating it as identical.
- (d) `id_map_sha256` added to the committed manifest, satisfying "commit the
  blind-index->row_key mapping as a sha256 hash only"; the mapping file
  itself (`analysis/calibration/correctness_calibration_id_map.jsonl`) stays
  gitignored until unblind (confirmed via `git check-ignore`).

Shard schema verified blind: `{opaque_id, question, gold_aliases,
model_answer_text}` only -- no row_key, role, arm, or detector verdict.
id_map (private) verified: 150 rows, decoy_type clear_positive exactly on the
29 correct_on_answerable rows, nowhere else.

Committed (commit-before-grade): `analysis-committed/correctness_calibration_pool_manifest.json`
(shard_sha256, id_map_sha256, n_clear_positive_decoys=29, opaque_id_list,
role_allocation -- no text) and `harness/calibration.py`.

**Channel-2 abstention calibration slice: SKIPPED.** Its sole consumer, D2,
is void per the S1 gate above; building it now would validate detector_v2
against a contrast that cannot be scored. Per lead instruction, not built.

HALTING here per instruction. Handing the lead: shard path
(`analysis/calibration/correctness_calibration_shard.jsonl`, gitignored, for
the blinded adjudicator to read directly) and the committed manifest/hashes
above. Not grading, not touching the shard or id_map further until the lead
delivers a graded-file hash commit.

## 2026-07-18 - Correctness calibration ceremony complete: unblind, score, fold into results

**Ceremony order** (git-provable): shard + manifest committed BEFORE grading
(0e4e229a) -> graded-file sha256 committed BEFORE unblind (1c28acde,
`analysis-committed/correctness_grading_receipt.json`, grader "isolated
blinded adjudicator (fresh opus agent, shard-file-only access; saw
opaque_id/question/gold_aliases/model_answer_text only; no
row_key/role/arm/detector fields)") -> unblind authorized by lead -> verified
the graded file's live sha256 (65fe24198813c2e...) against the committed
receipt BEFORE consuming it (matched) -> joined to the private id_map (no
verdict alteration) -> scored -> folded into `m4wk_results.json`.

**Schema fix on the way in**: `calibration.py`'s own `--graded-shard` docstring
had guessed a placeholder field name (`adjudicated_correct`) at build time,
before any real grading existed. The actual graded file uses `{opaque_id,
correct, note}`. Fixed `score_correctness` to read `correct` (the real
grader's field), not the placeholder -- a schema-alignment fix against ground
truth, not a verdict change (the join reads the SAME boolean values either
way; only the key name being read changed).

**Alias-grader false-wrong rate** (confab subset only, n=117): 5/117 =
0.0427, Wilson 95% CI [0.0184, 0.0962]. Null-interpretability bar (gates.yaml
SC2 bullet 1) is <= 0.10 -- **CLEARS the bar** (0.0427 << 0.10), so the native
D1 leg-1 null result (0.5921 < floor 0.8209) IS interpretable per this bound:
the alias grader is not systematically mislabeling confab rows as
false-wrong at a rate that could explain the sub-floor shift.

**Clear-positive decoy agreement** (29 correct_on_answerable rows, CG1
adaptation): 29/29 = 1.0 agreement, floor 0.60, floor_min_decoys 25 (both
cleared). CG1 adaptation ruling (lead-accepted, recorded here per lead
instruction): clear-positive-only decoys were used because gates.yaml's CG1
clear_negative/clear_positive agreement floors are written for the abstention
slice's refusal-classification task; no non-circular clear-negative decoy
exists for a correctness judgment (the confab role IS the class under test).
The adjudicator's perfect agreement on the unambiguous decoys is a strong
sanity check supporting trust in their 5/117 false-wrong calls above.

**Adjudicator-reported caveats** (from the grader's own summary, no row text,
as relayed by lead): 3 broader/equivalent-term acceptances; a
core-referent-right-despite-wrong-detail cluster; 1 gold-mismatch graded
against gold; 1 garbled non-answer marked false; refusals graded false per
rubric (matches this experiment's construct: a refusal is not a correct
assertion).

Promoted + committed (aggregates only, no text): `analysis-committed/correctness_calibration_score.json`
and the updated `analysis-committed/results/m4wk_results.json` (now carries
`alias_grader_false_wrong_bound` populated). `harness/calibration.py` (field-
name fix) also committed.

Reported both numbers to lead. HALTING -- build scope complete per lead
instruction; resolution writing, KG ingest, and the PR are the lead's from
here.

## 2026-07-18 - Red-team remediation: M-1 vacuous-attestation fix, m-6 join-key note

**M-1 (MAJOR, fixed).** Red-team review flagged that
`harness/analysis.py::load_single_regime_attestation` read channel-1 capture
manifests from `CHANNEL1_DIR.parent / "channel1_capture" / <arm> /
capture_manifest.json`, i.e. `analysis-committed/channel1_capture/<arm>/
capture_manifest.json` -- a path that has never existed. The real manifests
live at `analysis/channel1_capture/<arm>/capture_manifest.json`. Because the
function treated a missing file as `None` for every arm, `channel1_shas` was
always the empty set, and `len(empty_set) <= 1` evaluated `True` -- a
*vacuous* single-regime pass, not a verified one. The underlying fact was
never in question (all three arms' real manifests share identical
`row_order_sha256 = e756a17a0c72f3948b65930920750484e0c69922f672d0a959a5e4dd760c318b`,
`batch_size=8`, `n_rows=1001`, `n_batches=126`,
`template_sha256=81a04a99827ade21b9d5bd1832c2012429d196f96e604238a4b927701ca58e3c`),
but the committed record did not actually demonstrate it.

Fix, in `harness/analysis.py`:
1. New `build_channel1_capture_attestation()` reads the real path
   (`ANALYSIS / "channel1_capture" / <arm> / "capture_manifest.json"`) and
   **fails loudly** (`raise SystemExit`) if any arm's manifest is missing --
   channel-1 capture is unconditional for every arm regardless of direction
   void status, so a missing manifest here is a provenance bug, never a
   legitimate absence. This is a deliberately different rule from
   channel-2's None-safety (kept as-is): a direction's channel-2 survival
   file can be legitimately absent (transfer, voided at channel-1 per
   BLOCKER B1), so that arm of the function still returns `None` rather than
   raising.
2. `load_single_regime_attestation()` now delegates to (1) for the
   channel-1 side, so `m4wk_results.json`'s `single_regime_attestation`
   block carries the real shas.
3. `main()` promotes the same attestation to a new committed artifact,
   `analysis-committed/channel1_capture_attestation.json` (per-arm
   `row_order_sha256` / `batch_size` / `n_rows` / `n_batches` /
   `template_sha256` -- hash/count metadata only, no row text), so
   `channel1_single_regime` is re-verifiable from committed files alone,
   without depending on the gitignored `analysis/` capture directory.

Verified the fail-loud path directly (temporarily renamed one arm's manifest
off disk, confirmed `build_channel1_capture_attestation()` raises
`SystemExit` with a clear message, restored the file). Re-ran
`harness/analysis.py` and diffed the regenerated `m4wk_results.json` against
the previously-committed version: the **only** substantive change is
`single_regime_attestation.channel1_{no_answer_baseline,true_answer,
false_answer_placebo}` going from `null`/vacuous-`True` to the real shas /
genuinely-verified `True`. Every D1, D2, `transfer_firing_gate`, and
`alias_grader_false_wrong_bound` number is byte-identical to what was already
committed -- this is a provenance fix, not a re-derivation, and it changed no
number that had already been seen.

**m-6 (minor, documented, artifact NOT rewritten).** `per_row_projections.jsonl`
(and the ladder/survival row dicts feeding it -- `harness/capture_channel1.py`
line 77, `harness/ladder_channel2.py`, `harness/survival_channel2.py`,
`harness/analysis.py`, `harness/stats.py`) all write/read the confab role as
the bare string `"confab"`. The committed census
(`analysis-committed/census/qwen35_4b_worldknown_census.jsonl`, via
`harness/census.py` line 170 and `harness/selection.py`'s `ROLE_ORDER`) uses
`"confab_on_answerable"` (with `ROLE_SHORT` mapping it back to `"confab"` for
internal use). The two vocabularies are consistent within each artifact and
the mapping is deterministic (`ROLE_SHORT["confab_on_answerable"] ==
"confab"`), so this is not a scoring bug -- but a future reuse of
`per_row_projections.jsonl` joined directly against the census by role string
would silently miss all confab rows if it did not know to translate. Flagging
for future harnesses; not rewriting any existing committed artifact.

**m-4 (minor, NOT resolved -- flagging to lead rather than fabricating).**
Red-team asked to commit the KUQ sign-verification reproduction (the "0.987
KUQ AUROC under this harness's convention" cited in the 2026-07-18 "Transfer
void, native ladder bracketing re-derivation" entry above) as a small
aggregate JSON. I could not locate that computation anywhere on disk: the
only committed sign-check script, `analysis-committed/channel1/
verify_transfer_sign.py`, reproduces AUROC from M4-WK's own
`per_row_projections.jsonl` (0.3018 transfer / 0.8628 native) -- a different
check (M4-WK's own captured rows, not a KUQ population). The nearest
KUQ-adjacent number I found is
`experiments/qwen35-4b-midband-doubt-snap/analysis-committed/build_manifest.json`'s
`hs20.auc_neg_z_d_on_fit = 0.9928504321683578` (whose `mu_c`/`sigma_c` do
match this experiment's `TRANSFER_MU_C`/`TRANSFER_SIGMA_C` constants, so that
file is confirmed provenance for the transfer-direction constants) -- but
0.9928 is a fit-time Youden AUC on doubt-snap's own fit split, not an
independent KUQ-population reproduction under M4-WK's sign convention, and it
is not 0.987. I searched scratchpad dirs and the other active worktrees
(`margin-mapping`, `mechinterp-salvage`, `doubt-snap-cross-family`,
`paper5-actuation`, and others) for a leftover script/output from the
originally-dispatched sign-flip analyst computing exactly 0.987 -- found
nothing. Rather than relabel the 0.9928 figure as if it were the cited 0.987,
or spend a fresh GPU capture cycle on a KUQ subset I cannot confirm matches
the original check, I am flagging this gap to the lead directly and holding
on m-4 pending guidance (original artifact / analyst transcript, vs.
authorization to re-derive fresh, vs. accepting the 0.9928 figure as a
documented-but-distinct provenance number).

**m-4 CLOSED.** Lead identified the original artifact: the sign-check
analyst ran in the lead's own session sandbox and left the script at the
lead's scratchpad path (never version-controlled there), which is why the
worktree/scratchpad search above missed it. Re-ran the script verbatim
(CPU-only, read-only, no GPU) against its stated on-disk inputs --
doubt-snap's own committed `c_hat.json` plus its gitignored fit-population
working files (`anchor_extract.safetensors`, `fit_rows_for_anchor.jsonl`) --
and independently confirmed it reproduces exactly: `n_confab=887`,
`n_correct=240`, `n_missing_keys=0`,
`AUROC(confab>correct, READOUT_SIGN=-1) = 0.986650`,
`AUROC with flipped (+1) sign = 0.013350` -- matching the lead-reported
figures (the earlier NOTEBOOK entry's "0.987" was a rounded citation of this
same 0.986650). Copied the script verbatim (provenance header added, no
logic changed) to
`analysis-committed/channel1/kuq_sign_reproduction.py`, and committed the
full result plus the three input files' sha256 (no row text) to
`analysis-committed/channel1/kuq_sign_reproduction.json`. That JSON also
carries forward the m-4-triage note that
`qwen35-4b-midband-doubt-snap/analysis-committed/build_manifest.json`'s
`hs20.auc_neg_z_d_on_fit=0.9928504321683578` is a *different* quantity
(fit-time Youden-threshold AUC on doubt-snap's own fit split) and must never
be conflated with this KUQ-population reproduction number.
