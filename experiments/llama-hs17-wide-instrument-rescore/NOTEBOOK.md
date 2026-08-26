# Llama hs17 wide-instrument regeneration and re-score notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

### 2026-08-26 — sign-time feasibility probe (PASS) and sign

Probe performed by direct artifact read in the primary checkout (lead
session), immediately around sign:

- All six frozen-reuse inputs exist and sha256-match the pins carried over
  from `llama-hs17-direction-specificity` `cell.yaml` (u_d, c_hat, gate_fit,
  standardization, dose_source, row_pools — six exact matches).
- Dose verified: `full_summary.json /layers/hs17/dose_target =
  4.954897429720482`.
- Row pools verified by direct read of `reused_rows_manifest.json`:
  confab held_out 872, known_correct_answered held_out 334 (fit splits
  581/222 and fit_only 947 untouched by this cell).
- Wide pins present: `abstention-wide-instrument-calibration/detector_v2.py`
  plus the committed patterns/rubric (hash equality is WR-G0's job at run).
- Adjudication tooling present: census `apply_adjudication.py` lane.
- Random directions reproducible from the registered recipe + seeds
  (910001..910015, identical to the resolved narrow census).
- Self-blinding intact: no result computed; existence/coverage/sha only.

Signed 2026-08-26 (lead + user). Both predictors on record for outcome A
(wide replicates + specific). Engine exception declared (intervention path;
the bridge requires the identical engine as the resolved narrow cell).

- (add dated entries as the experiment progresses)
