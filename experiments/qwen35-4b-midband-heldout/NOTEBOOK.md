# Qwen3.5-4B mid-band doubt-snap held-out confirmation (hs20 frozen operating point) notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

### 2026-08-11 -- Bookkeeping: Outcome section backfilled from the recorded verdict

**Bookkeeping only, no goalpost implications.** The trailing `## Outcome`
section of `AMENDMENT.md` still held the unfilled "Filled at resolve"
placeholder despite `experiment.yaml` reading `status: resolved` with a verdict
on record, and despite the `### Outcome` subsection under the Falsifier already
recording the resolution. Backfilled in a PI-approved governed pass at the level
of detail the placeholder demanded (shape, G0/G1/G3(i)/G3(ii) with Wilson
intervals on every rate, fired held-out counts, row-level decoupling count,
placebo readings, one-sentence summary) from the recorded verdict line, the
2026-07-13 "RESOLVED shape A" entry, and
`analysis-committed/heldout_summary.json`; every number in the new prose was
re-read from that artifact and agrees with the existing `### Outcome`. One item
is recorded as "not recorded" rather than resolved: the measured realized
projection behind the G0 smoke readback check is in no committed artifact,
which carries only the commanded dose. The existing `### Outcome` subsection was
left untouched. This cell's header carried no "Outcome placeholder still
unfilled" flag to update. NO ADJUDICATION WAS PERFORMED: no verdict, gate,
threshold, prediction, falsifier or status was changed, and no number was
recomputed. (Note for future readers: this file's preamble says newest first,
but the pre-existing entries below run oldest first; this entry follows the
stated convention.)

- 2026-07-13 (draft): scaffolded and drafted the held-out confirmation stage
  reserved by qwen35-4b-midband-doubt-snap scope statement 2. Frozen operating
  point (hs20 direction set, tau_frozen, mu/sigma, sigma_c, dose 8 x sigma_c)
  is consumed verbatim from the ladder's committed artifacts; nothing is refit.
  Population is the untouched 1,332 confab + 360 known held-out pool. Four arms
  (baseline / gated / random_direction / permuted_gate), one dose. Gates:
  G0 instrument-validity stop, G1 primary (refused >= 0.60 AND well-formed
  >= 0.80, cost <= 0.10 over full 360 knowns), G3(i)/G3(ii) placebo. Prediction
  and falsifier enumerate outcome shapes A through E so nothing lands between
  them (fleet wording-gap lesson). NOT signed; harness not written (separate
  assignment). See AMENDMENT.md.

## 2026-07-13 - Sign preparation: provenance pins filled, tolerance adjudication recorded (lead)

Frozen operating-point hashes filled from the resolved
qwen35-4b-midband-doubt-snap ladder's committed artifacts (build_manifest
f0a8ea7a..., hs20 u_d 18e78f25..., c_hat 937d1bff..., random_direction
db8b930d...; full values in frozen_operating_point_hashes.json).
verify_frozen_operating_point_hashes() now has real targets and pipeline.py
refuses to run on any mismatch. All 12 instrument files (9 modules + cell.yaml
+ gates.yaml + the frozen-hash file) hand-pinned in experiment.yaml.

Tolerance adjudication (binding, recorded at sign as required by the G0
hardening acceptance): gates.yaml's "readback within tolerance" is read as the
shared synaptic-tuner MechInterp SmokeConfig contract via
evaluate_smoke_readback (write_rel_tol 0.05, write_abs_floor 0.5,
offtarget_tol 1e-3), applied in smoke mode to the gated and random arms. This
defers to the one shared readback-tolerance definition in the codebase rather
than minting a local variant; any future change to SmokeConfig would surface
as a pin-visible diff in the shared module, not silently here.

Full suite green post-rebase. Scoreboard: orchestrator call recorded in
AMENDMENT.md; awaiting the PI call, then bin/exp sign and the GPU sequence
(materialize -> capture_anchors ~18-19 min -> pipeline smoke -> full run).

## 2026-07-13 - Lab notebook: smoke/full runlog-path collision at first full launch (lead)

The first full-run launch exited at the baseline pass: pipeline smoke and
pipeline run share analysis/runlog/ paths, so the full run tried to open the
smoke's baseline.jsonl and RunLog correctly refused on a run_config
fingerprint mismatch (n_rows 8 vs 1692). This is the RunLog resume guard
working as designed, not a grading or delivery defect; no pinned module was
changed. Operational fix: smoke run logs archived to
analysis/runlog-smoke-20260713/, the refusing attempt's log preserved as
run_full_attempt1_fingerprint_refusal.log, full run relaunched clean.
Materialize and capture_anchors artifacts were untouched and reused. Note
for future harnesses: smoke should namespace its run logs away from the
confirmatory paths so the guard never has to fire.

## 2026-07-13 - RESOLVED shape A: hs20 window promoted to held-out claim (lead)

Full run completed cleanly after the runlog relaunch. All gates pass:
fired-confab refused 872/1286 = 0.678 (Wilson [0.652, 0.703]) vs 0.60,
well-formed 0.977 vs 0.80, gated-arm known false refusal 14/360 = 0.039 vs
0.10, random_direction no-op (+0.008 confab, 0.000 known), permuted_gate
strictly worse on cost (0.056 vs 0.039). Lead independently recomputed every
gated rate from analysis/runlog/ row logs; exact match on all legs.
Per-row text and full sub-grade dicts persisted per the data-exhaust rule.
Both scoreboard calls (shape A) correct; observed refused sits mid-band in
the orchestrator's recorded 0.62-0.70. Result is in-prediction and the
instrument was hardened and adversarially reviewed pre-sign, so lead
verification (not a fresh red-team) is the certification tier applied.
Resolved via bin/exp resolve; PR to follow; KG ingest after merge.

## 2026-08-27 — Exhaust published to HF (aggregate shape)

Data-exhaust release, PI-approved in-conversation (explicit permission
2026-08-27, batch 1 of the exhaust backfill, task-56c61a). Built with the
data-exhaust skill (aggregate-only copy-everything mirror of
analysis-committed/: no question text, generation text, or hidden states;
verify_exhaust.py PASS including the --experiment-dir completeness check;
zero exclusions). 4 files / ~0.36 MB, built at repo commit b642b7c6.

- HF repo: `professorsynapse/eh-qwen35-4b-midband-heldout` (dataset)
- HF revision: `ba7249a84be319827b33241563599188ce8c9673`
