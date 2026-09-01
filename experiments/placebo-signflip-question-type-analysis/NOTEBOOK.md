# Placebo sign-flip: question-type stratification of the family-specific random-direction response notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

- 2026-07-14 (lead, red-team certification + verdict). Adversarial red-team
  review (opus) completed before any verdict was written. Certification: every
  committed M1/M3/gate number reproduces to full float precision under
  independent recomputation (qwen safetensors + mistral 251MB anchor JSON
  reloaded from scratch; fire-set 1303/1303, symdiff 0); circularity discharged
  (mistral M1 restricted to the 1,694 held-out rows gives z_d SMD -6.05,
  LARGER than the -5.80 full-population value, so fit-row inclusion does not
  manufacture the contrast); subtype n's sum to stratum totals everywhere;
  behavioral BG0 re-slices reproduce. The M1 axis-orientation question that
  was lifted to the red-team resolved from the locked instruments themselves:
  no prose doc pins the orientation, but the frozen gate code (rr2
  direction_fit.py) defines +u_d as the KNOWN pole and the doubt score as
  -z_d, and the manifest field auc_neg_z_d_on_fit names the axis. Adjudication
  therefore split M1 by axis: doubt CONFIRMED in all three families under the
  operational convention (with the stated caveat that it largely re-expresses
  the answerability gate); caution NOT INTERPRETABLE as a question-type
  ordering (c_hat is fit on an unanswerable-only contrast; answerable
  placement on it is emergent geometry). The committed raw-axis
  prediction_consistent booleans were NOT transcribed into the Outcome; the
  mismatch is sign-labeling in the report, not arithmetic. Registered
  mechanism falsifier UNTRIGGERED (sign-agnostic; no CI spans 0). Behavioral
  subtype falsifier arm FIRES for qwen (future-unknown -24.7 vs -2.8 or
  smaller elsewhere): inert reading falsified for qwen at subtype resolution.
  Scoreboard: M1 both correct (doubt axis); subtype slot user CORRECT /
  orchestrator WRONG; M3 both wrong for qwen (null), mistral statistically
  non-null but negligible (1.2e-4 on 0.0426, 0.3%; per-group variances ~2e-8,
  non-degenerate). M2 reported with the RR3 single-seed variance caveat as
  registered in the previous entry. Red-team hygiene notes folded into the
  Outcome: BG1 mistral/llama row-level reproductions live in notebook prose +
  opt-in checks, not committed JSON (BG1 met at its registered bar
  regardless); QH answerable n=17 denominator carries only 1 wide-graded pair.
  Resolved via bin/exp with status resolved; verdict one-liner mirrors the
  Outcome summary.
- 2026-07-14 (lead, BG1 adjudication + repin). The constrained-executor run of
  the real-data BG1 checks FAILED as built (mistral fire-set mismatch 0.358,
  llama ~0.274 per layer) and stopped at the registered hard stop, correctly.
  Lead-adjudicated diagnosis, independently re-derived (the mistral restricted
  recomputation was re-run by the lead directly; the llama restricted numbers
  were read from the diagnostic run's raw output log): both failures were
  CHECK-SCOPE defects, not frame defects. The mistral check scored all 3037
  anchor rows while RR2's pipeline gate-evaluated only the 1694-row held-out
  roster; restricted to that roster the ported frame reproduces every fire and
  no-fire decision (0/1694 both directions). The llama check treated
  unconditionally-dosed known_correct rows (222, present in the gated runlog
  regardless of any gate decision) as missed fires; restricted to the 581
  gate-evaluated confab FIT rows the frame reproduces hs22 and hs23 exactly
  and hs20 with one extra fire (0.0017, inside the registered 1% tolerance).
  frame_port.py corrected to the populations the pipelines actually
  gate-evaluated (no change to frame math or analysis paths); the llama
  fire-set check now also gates each layer at the same 1% tolerance, a
  strictness increase. Repinned with a repins entry. Smoke suite 31 passed.
  Corrected BG1 rerun over both real-data files: PASS honestly (qwen 0/1692,
  mistral 0/1694, llama 1/581 + 0/581 + 0/581, known-presence invariant true
  at all layers). BG0/BG1/BG2 all green; mechanism leg now authorized.
  Cross-experiment caveat registered for the eventual verdict:
  rr3-corrected-placebo-replication (resolved FALSIFIED, PR #290) shows
  mistral random-direction lifts spanning -7.4 to +21.8 points across three
  fresh seeds at matched magnitude, so the single-seed family-sign premise
  behind this experiment's mistral recruitment pole must be read with
  per-seed variance in mind; the falsifier and M1/M3 predictions are
  unaffected (they concern anchors and question type, not placebo seeds).
- 2026-07-14 (lead, PRE-STATED before the mechanism leg runs). Behavioral leg
  executed post-sign; BG0/BG1/BG2 all PASS; report written (uncommitted until
  the mechanism leg completes). Headline behavioral observation: the qwen
  suppression concentrates in the future-unknown kuq subtype (-24.7 pts,
  n=190, baseline 0.332) with every other subtype at -2.8 or smaller, and
  future-unknown is ALSO mistral's largest positive delta (+11.8); baseline
  hedging orders the six subtypes identically in both families. The PI's
  scoreboard call (concentrated-or-uneven) is currently ahead of the
  orchestrator's (even-spread); no verdict until red-team certification.
  PRE-STATEMENT for the not-yet-run mechanism leg: in addition to the
  registered M1 (answerable vs unanswerable), report a SUBTYPE-RESOLVED
  descriptive breakdown of the pre-generation doubt/caution projection
  (per kuq subtype, per family), specifically whether future-unknown anchors
  sit highest on the caution axis and whether M3 realized displacement is
  largest there. Descriptive, hypothesis-generating only, no gate, no bearing
  on the registered falsifier; stated here BEFORE any anchor tensor for the
  mechanism leg is loaded so it is not a post-hoc read. Mechanism leg remains
  deferred until the RR3 GPU job frees host RAM (PI machine restart pending).
- 2026-07-14 (harness-builder). Analysis harness built, CPU-only, no model/GPU
  touched (RR3's local 3090 job left alone throughout). BG0 stage-in
  (staging.py) symlinks 26 gitignored cross-worktree artifacts + records 9
  committed-local ones into analysis/, sha256+count per entry. BG1's known
  build risk (naive single-stage port only reproduced 421/1303 firings) was
  resolved by reading the gate-firing chain directly out of three independent
  upstream callers (qwen capture_anchors.py, mistral RR2 direction_fit.py, RR
  direction_fit.py): raw dot product onto the unit direction vector, then
  scalar z-score standardize+clip[-2,2], `score = -z_d`, `fire = score >=
  tau_frozen`; the direction JSON's `mu` field is always a zero placeholder
  and `sigma` is display-only, never consulted by the gate. frame_port.py's
  exact port reproduced the qwen ground-truth firing set 0/1692 mismatches
  (1303/1303 fires exact) and the mistral fit_reuse_report.json cross-check
  passed on all 6 stats fields; mistral/llama fire-set checks against the
  full 251MB/493MB anchor JSONs were written but left opt-in (host RAM
  headroom risk noted in the build brief), for the lead to run post-sign.
  behavioral_leg.py's Cells A (QH) and B (MC) reproduced BG0's certified
  numbers bit-for-bit (139/1286, 73/1286, delta -5.13; 368/1312, 465/1312,
  delta 7.39). Cell C (QL) needed one design correction: QL rows in
  row_level_scored.jsonl carry no category_canon field at all, because QL's
  dosed population is the doubt-snap ladder's FIT split, not the QH held-out
  pool; fixed by reading the committed (non-gitignored)
  qwen35-4b-midband-doubt-snap reused_rows_manifest.json for the row_key to
  subtype lookup. mechanism_leg.py (M1/M2/M3) is written and unit-tested on
  synthetic vectors only; its mistral/llama real-data loaders are opt-in and
  were never invoked in this build session, so no M1/M2/M3 numbers exist yet.
  report.py assembles BG0/BG1/BG2 + the behavioral leg into one committed
  JSON; its main() was deliberately not run in this session (writing the real
  deliverable is the lead's call after sign). test_signflip_smoke.py: 31
  synthetic-fixture tests pass, 4 opt-in real-data tests skip by default
  (`SIGNFLIP_RUN_REALDATA=1` to enable). One real bug caught and fixed by the
  suite: mechanism_leg.py's m1_contrast returned `prediction_consistent` as a
  raw numpy.bool_, which write_json's `default=str` fallback would have
  silently serialized as the string "True"/"False" instead of a JSON boolean
  rather than raising; wrapped in `bool()` at the source. experiment.yaml
  instrument.modules/pins filled with all 7 harness modules + configs
  (sha256, no verdict/sign touched). Next: lead runs `bin/exp sign`, then the
  CPU behavioral-only run (`python3 report.py`), then decides on
  mistral/llama real-data BG1 + mechanism-leg execution given host RAM
  headroom.
- 2026-07-14 (lead). Draft reviewed and pre-sign decisions applied. The
  drafter's structural finding (every dosed placebo row in every family is
  unanswerable; the certified sign difference is measured entirely on the
  unanswerable stratum) was independently re-derived by the lead from
  row_level_scored.jsonl before acceptance: unanswerable baseline 139/1332 =
  0.104 vs random 73/1286 = 0.057, answerable 0/77 vs 0/7. Lead decisions:
  within-kuq subtype breakdown EXTENDED to mistral RR2 (recruitment pole gets
  the same resolution as the suppression pole); mistral hs16 direction JSONs
  are provenance-by-regeneration (fit_reuse against RR's committed manifest,
  JSONs never committed, BG0 verifies). Scoreboard calls registered pre-run
  and checkpointed in the session note: M1 both YES all three; subtype
  breakdown user CONCENTRATED-OR-UNEVEN vs orchestrator EVEN-SPREAD (the
  differentiating slot); M3 both YES-differs. Next: analysis harness build
  (BG1 exact frame-port acceptance test is the known build risk), then sign,
  then CPU run.
- 2026-07-14 (drafter). Initial draft: behavioral leg (certified unanswerable
  deltas reported straight, qwen answerable n=17 at true power, mistral/QL
  answerable registered as coverage gaps deferred to RR3, within-kuq subtype
  breakdown) + mechanism leg (M1 powered answerable-vs-unanswerable anchor
  projection, M2 cross-family consistency read, M3 analytic realized
  displacement; M3 dropped for llama, no placebo arm exists). Gates BG0-BG2.

- 2026-09-01: aggregate data exhaust published (batch 4 of the backfill, task-56c61a; PI-approved in-conversation 2026-09-01). Copy-everything mirror of analysis-committed plus README + PROVENANCE; aggregate shape, no row text, zero exclusions. 4 files / ~66 KB, built at repo commit ee61d702.
- HF repo: `professorsynapse/eh-placebo-signflip-question-type-analysis` (dataset)
- HF revision: `3ba76f647a83662339976c3bc4562cec4868bb24`
