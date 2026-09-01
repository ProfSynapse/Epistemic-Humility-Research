# H4: Registered Ungated-vs-Gated Dose-Matched Arm for the Caution Snap notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

- 2026-07-13 (RESOLVED): red-team review complete (5 surfaces: exact-reproduction
  plausibility, derived-arm validity, metric decomposition, fire-bit provenance,
  cross-result consistency with the ladder). All gates SURVIVE; no invalidating
  finding. Lead adjudications accepted into the Outcome: (1) metric hygiene:
  60.1% is DAMAGE (not-well-formed-correct), decomposed 55.8pp clean
  false-refusal + 3.9pp answered-wrong + 0.4pp degenerate, and SUPERSEDES the
  unregistered n=80 36.2% diagnostic rather than reproducing it; (2) scope: the
  write-non-selective / gate-supplies-selectivity claim is bound to
  Qwen3-4B / L34 / dose-200 and explicitly reconciled with the qwen3.5 mid-band
  ladder's permuted-gate result as operating-point dependence, not
  contradiction; (3) provenance: sha256 of the held-out anchor tensor and both
  source artifacts recorded in the Outcome so the CPU join survives a source
  worktree wipe. The exact G0 reproduction (identical numerators 136/185 and
  8/258) is expected single-row greedy determinism and doubles as proof the
  anchor reuse did not drift; run freshness verified via live readback on all
  443 rows and 371/443 baseline-vs-dosed text differences. The pre-outcome
  G0-asymmetry adjudication was not exercised (cost landed at 0.031 exactly).
  Both scoreboard calls adjudicated in the Outcome: orchestrator directionally
  right but under-predicted damage magnitude; user falsifier-fires call wrong
  at this operating point.


- 2026-07-13 (SIGNED, pre-launch): Signed after lead review of the built
  harness (CPU smoke 8/8 re-run by the lead; commit 919c3888). Instrument
  modules added to instrument.modules BEFORE sign so the sha256 pins cover
  them. Builder adjudications accepted: informational-only readback block
  (mirrors the resolved cell's own diagnostic, not a new gate); defensive
  McNemar pairing with reported drop count; hard pre-launch row-count
  asserts; reuse of the resolved cell's still-on-disk L34 anchor artifacts
  (anchor is prompt-only, so no fresh extraction needed; escape hatch
  documented in the builder log if that worktree is ever wiped). Pre-outcome
  adjudication recorded BEFORE any GPU spend, on H4-G0's known-cost check:
  the pinned formula abs(rate - 0.031) <= 0.03 is literally asymmetric (a
  0/258 = 0.0% rate would fail by 0.1pp), while the pinned gates.yaml
  comment states the intent as an upper bound ("<= 0.061"). The gate will
  be executed as WRITTEN; if it stops solely because the rate lands BELOW
  0.001 (better than the resolved cost), that stop will be diagnosed with
  the pinned comment's stated intent on record, and any continuation past
  such a stop will be its own documented decision, never a silent pass.
  G0 is a stop-not-outcome gate, so this clarification moves no outcome
  goalpost. Launch: local RTX 3090 (free lane per the amendment's
  PLACEHOLDER resolution; card idle), full mode, 886 generations.

- 2026-07-13 -- HARNESS BUILD (harness-builder agent, CPU-only; GPU launch NOT
  run). Wrote `materialize_rows.py`, `gen_lib.py`/`grader.py`/`model_lib.py`
  (verbatim copies of the resolved doubt-gated-caution-tighten cell's own
  modules, not cross-experiment imports), and `pipeline.py` (dual-pass, both
  arms in one harness pass, RunLog-resumable per row).

  Key build-time finding: the resolved cell's own gitignored extraction
  artifacts (`l34_anchor_extract.safetensors`, `rows_with_text.jsonl`) still
  exist on disk in the worktree where that cell was actually run
  (`/home/profsynapse/code/ehr-worktrees/gate-snap-tighten/experiments/doubt-gated-caution-tighten/analysis/`).
  Since the L34 anchor is a function of the prompt only (prompt_len-1,
  before any generation or write), those same tensors are valid input to
  this experiment's gate-decision math -- no fresh GPU extraction is needed.
  `materialize_rows.py` joins the promoted `split_manifest.json` against
  those artifacts and subsets to the 443 held-out rows (185 confab + 258
  known_correct_answered), entirely CPU/offline. Ran it against the real
  artifacts: 0 missing question, 0 missing alias, 0 missing tensor.

  Ran `load_rows_and_gate_decisions()` against the real frozen instrument
  (`tau_frozen=0.3026445054171378`, FIT-pool mu_d/sigma_d): held-out fire
  counts are confab 168/185 (90.8%) and known_correct_answered 4/258
  (1.55%), consistent with the FIT-split gate_fit.json numbers (96.8%/1.2%).

  CPU smoke (`smoke_cpu.py`): gate-decision math (fire rule, clipping,
  boundary), dual-record -> gated/ungated arm construction (fired vs
  non-fired paths), exact paired McNemar (`model_lib.mcnemar_exact`, textbook
  cross-check), `compute_h4_gates` end-to-end on both a predicted-shape PASS
  case and the falsifier-shape FAIL case, unpaired-row handling, the REAL
  `gen_lib.grade_clean_tighten` / `grader.grade_one` on synthetic text, and a
  RunLog resume round-trip using the pinned synaptic-tuner submodule's
  `shared/utilities/run_log.py`. All 8 checks PASS. No model load, no GPU.

  Did NOT run `pipeline.py --mode smoke` (GPU) or `--mode full` (GPU,
  confirmatory) -- both are gated behind the lead's sign-off and launch
  approval, per this build task's scope.

  synaptic-tuner submodule was uninitialized in this worktree at build start
  (`git submodule update --init synaptic-tuner` was required before any
  import from `MechInterp.*` or `shared.utilities.run_log` would resolve);
  initializing it to the already-pinned commit produced no diff.

- 2026-09-01: aggregate data exhaust published (batch 4 of the backfill, task-56c61a; PI-approved in-conversation 2026-09-01). Copy-everything mirror of analysis-committed plus README + PROVENANCE; aggregate shape, no row text, zero exclusions. 3 files / ~6 KB, built at repo commit 8862f83e.
- HF repo: `professorsynapse/eh-ungated-vs-gated-dose-matched` (dataset)
- HF revision: `d062242ee17f19b275a0699dc04223eb7d73ea2d`
