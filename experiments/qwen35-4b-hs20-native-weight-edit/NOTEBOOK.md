# Qwen3.5-4B hs20 native weight edit notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

- (add dated entries as the experiment progresses)

## 2026-11-03 — pre-sign installed runtime compatibility smoke

This is synthetic infrastructure evidence, not a scientific result. No FIT or
held-out behavior has been generated and this instrument remains unsigned.

- Tuner extension source b11f0604feaabaed8113198ebf0c3dabeeefa8dd; wheel SHA256
  9b47c5a5100b02008e5b69194039f6950d9270ec1bdb690c074725fe6fc25715. PR281.
- Installed EHR host wheel from commit2370db648be8179aefd631ee42251f2fec98996b;
  SHA256 eb00d2f81ae008d7f2a052d51d9e28888076e6d6fd3ff403a1cdb541eeec83af.
  The reusable preflight launcher is from migration commitd17ba650 (PR603).
- Base image sha256:b4166dbd15d0c7d9cad8a07c46be1301dc5941eb4b4d629ae754dc27cb03eb9c.
  Derived image sha256:aaafc29751b932ed6c7532fb34995552202da358e4af2250d74743afb0ccc509.
  Verified that all16base layers precede the two derived layers. The base stack
  remains Torch2.9.1+cu128, Transformers5.17.0 and Pydantic2.12.4; CUDA sees3090.
- Installed-runtime unit checks:285passed,3source-checkout fixtures excluded.
  The first attempt had284passed and4fixture/CWD failures, not arithmetic or
  model failures. Both attempts remain in the private build directory.
- Forward-only actual Qwen3.5-4B smoke:3synthetic prompts, residual hs20 plus
  down_proj inputs at decoder blocks20/21/22, every captured site shape[1,9216].
  use_cache true; per-row capture journal and completed manifest exist.
- Source model shards were materialized and verified on T7 E:. Smoke project:
  /mnt/e/SynapticResearch/preflight/ehr-installed-20261103. Private evidence:
  /mnt/e/SynapticResearch/builds/ehr-runtime-20261103-b11f0604/preflight-evidence.json.
  A text-free copy is in the migration PR's runtime/mechinterp/evidence/.
- Build attempt1 refused a bare local image ID because BuildKit interpreted it
  as a registry name. Attempt2 used a local tag checked against the full base ID;
  layer ancestry verification passed. No model stack upgrade or native-daemon
  workaround occurred.

Pending before sign: complete harness, independent instrument review, actual
native-weight name mapping/readback, zero-patch token parity, batch parity,
export/reload roundtrip, real SIGKILL/resume drill, input/decoy feasibility and
complete persistence declarations. No G0 or behavioral gate is adjudicated yet.


## 2026-11-03 — pre-sign review repairs and guarded runtime

The pre-sign review found an invalid null-classification path. The harness now
makes every non-budget engine refusal an instrument failure. Smoke output keys
are distinct in the shared ledger. Export/token parity gates held-out generation.
Public Git commitments gate grading and unblinding. A frozen 27/30 spot agreement
rule replaces an operator veto. G0 verifies source/runtime/data binding and the
actual kill/resume journals. The instrument remains unsigned; no candidate or
held-out generation has run.

The active runtime is `sha256:35fc50d3e1878710147f5a0251a4d89c39958255263ed71f5d540fc6d88414e9`.
Its base-layer prefix was checked against the pinned b4166dbd image. `pip check`
passes. Engine wheel b884aab4 and host wheel 28511365 are pinned in
`analysis-committed/runtime_manifest.json`. Host CPU tests: 26 passed, including
an owned launcher SIGKILL and inherited writer-lock release. Earlier NOTEBOOK
image/wheel entries describe prior compatibility checks, not this launch.

The review-regression suite checks budget/instrument refusal separation,
smoke accounting, export-order enforcement, real Git commitment checks,
objective spot acceptance, journal validation, and source/model/threshold drift.
Real-model token parity and measured persistence checks are pending.
