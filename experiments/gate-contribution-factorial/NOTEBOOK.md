# Gate-contribution factorial notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

### 2026-07-15 (lead) - knobs resolved, scoreboard registered, signed

All seventeen sign-time knobs resolved (AMENDMENT.md Decision record): PI decided
the qwen operating point (Qwen3.5-4B hs20, dose_abs 12.608, the census point) and
confirmed the Sel_abs metric, the 0.20 Gap_Sel(c_hat) floor, the directional-only
random-condition leg, and the 0.10 cost-protection floor; remaining knobs adopt
the drafter proposals, lead-confirmed. Mistral substrate revision pinned at sign
from RR2 (c170c708c41dac9275d15a8fff4eca08d52bab71); mistral permuted-gate seed
pinned 20260715. Predictions scoreboard registered pre-run by both predictors;
the differentiating slot is the mistral gate axis (orchestrator PASS, PI FAIL).
Signed via bin/exp sign; harness build dispatched against the locked spec on the
free local 3090 lane.
