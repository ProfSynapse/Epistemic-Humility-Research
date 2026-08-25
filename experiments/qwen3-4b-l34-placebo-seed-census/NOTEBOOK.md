# Raw-base Qwen3-4B L34 random-direction seed census notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

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
