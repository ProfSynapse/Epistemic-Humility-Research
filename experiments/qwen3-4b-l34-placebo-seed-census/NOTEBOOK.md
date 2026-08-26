# Raw-base Qwen3-4B L34 random-direction seed census notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

### 2026-08-26 — aggregate exhaust published

`professorsynapse/eh-qwen3-4b-l34-placebo-seed-census`, HF revision
`9dccf16109b92d3ea79169e4cd3ab12659062402` (7 files: PROVENANCE, README,
wide-gates report, adjudication pool/graded/applied manifests, generation
manifest; provenance commit 1063f5d3). Built and verified through the
data-exhaust skill (verify PASS, completeness check exact); user-approved
2026-08-26. Row-level shape deferred: `analysis/rows/` carries generation
text but no per-row `source` field, so a row-level build needs a staging
pass that joins each row to its source for the license gate, and the pool's
FalseQA lineage is a no-license source (excluded-entirely disposition).

### 2026-08-26 — full run, blinded adjudication, gates adjudicated, resolved

Generation: 15 seeds x 185 rows on the local RTX 3090 (started immediately
after the llama specificity cell released the card; submodule working tree
at the Synaptic-Tuner readback-device fix 3a21774d). No crashes. Builder
launched, went idle per the usual pattern; lead's Monitor owned the watch
end to end and verified liveness on disk when a ps false-negative suggested
otherwise (GPU utilization + growing log were decisive).

Adjudication lane (per `.skills/experiment-runner/reference/abstention-grading.md`,
RR3 conventions): pool built by the builder (3 shards, 2392 core, 179+179
decoys, seed 20260825, fresh salt); builder's decoy audit confirmed zero
WICR45DECOY leakage into the scored population. Three context-free opus
graders dispatched in parallel, one per shard, each with a private working
directory and unique output path (RR3 isolation rule); rubric verbatim +
edge conventions in every prompt; pattern-classifier use forbidden and
audited (working-directory scan: judgment chunks present, no matcher
scripts; one grader's helpers were a dump/append pair with judgments passed
as agent-authored flags — compliant). Lead verified every graded file
before hash-commit: line count, per-line positional opaque_id match,
boolean-only values, exactly two keys. Hashes committed per shard BEFORE
any unblinding; apply verified hashes, then CG1: 3/3 shards PASS attempt 1,
clear-negative 1.0, clear-positive 1.0 per shard (60/60/59 decoys, all
>=25 floor), pooled 179/179. Graders went idle without final reports (the
recurring glitch); the artifact-level verification above stands as the
record.

Gates: QG-G1 PASS (4.83), QG-G2 FAIL (6/15 negative). Lead re-derived both
gates and all 15 per-seed rates independently from `analysis/rows/` +
`analysis/adjudication_applied.jsonl` with the pinned detector — exact
match with `analysis/wide_gates_report.json`. Verdict and table in
`AMENDMENT.md` Outcome.

Provenance note: the generation manifest records 7 unpinned load-bearing
scripts under `doubt-gated-caution-tighten/` (its own offline-prep scripts,
e.g. `pipeline.py`, `build_directions.py`) — their OUTPUTS were reused
frozen and sha-verified via `frozen_reuse_sha256`; the scripts themselves
carry no pin in dgct's manifest. Recorded transparently via
`provenance.record_unpinned`, ruled acceptable for this cell (a parent
manifest gap, not a reuse-integrity gap); no goalpost or instrument change.

### 2026-08-25 — pre-sign feasibility probe (required before sign)

Every arm confirmed constructible from committed data (verified by direct
artifact read in the primary checkout, lead session):

- Frozen directions/gate exist in `doubt-gated-caution-tighten/analysis-committed/`:
  `u_d_L34.json`, `c_hat_L34.json`, `gate_fit.json`, `build_manifest.json`.
- Historical draw verified: `random_direction_L34.json` — recorded recipe
  `np.random.RandomState(seed).normal(size=hidden_dim), unit-normalized`,
  seed 20260707, layer index 33, hidden_dim 2560, normalized true. The 15
  fresh seeds (920001..920015, `gates.yaml`) are disjoint from it.
- Dose verified: `doubt-gated-caution-tighten/cell.yaml` dose_target 200.0.
- Frozen arm results verified in
  `wide-instrument-control-rescore/analysis-committed/results/wide_gates_report.json`:
  baseline 21/185 = 0.1135, gated 137/185 = 0.7405, lift 0.6270,
  historical random 13/185 = 0.0703 (signed lift −0.0432), ratio 14.5, and
  the report's own note that the ratio is "RR3's formula specialized to K=1"
  — the limitation this cell closes.
- Adjudication tooling present: census `apply_adjudication.py` plus wicr's
  committed shard manifests (pool manifest: 4 shards, decoy counts recorded).
- Self-blinding intact: no new result computed; existence/coverage only.

- (add dated entries as the experiment progresses)
