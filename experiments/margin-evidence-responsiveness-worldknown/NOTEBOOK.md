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
