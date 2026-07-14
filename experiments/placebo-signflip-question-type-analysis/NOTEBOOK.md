# Placebo sign-flip: question-type stratification of the family-specific random-direction response notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

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
