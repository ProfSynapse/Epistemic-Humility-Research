# j-space-midband-write-sweep-qwen3-4b

Status: running (local RTX 3090 lane launched 2026-07-07).

Keep this document the prose home for the experiment. The machine state lives in
`experiment.yaml` and is never duplicated here.

## Motivation and posture

This experiment follows directly from the resolved exploratory
`doubt-gated-caution-tighten` amendment on raw-base `unsloth/Qwen3-4B` bf16.
That predecessor established a selective training-free tighten instrument:
use a doubt threshold to decide which rows look like confabulations, then snap
only those fired rows to a fixed caution setpoint. The important mechanism
lesson was that the write itself is not selective. If known-correct rows are
dosed, many refuse; selectivity comes from the doubt gate mostly dosing
low-doubt/confab rows.

Resolved predecessor result: G1 passed with confab clean_tighten 136/185 =
73.5% (Wilson lower bound 66.7%); G2 passed with known-correct false-refusal
8/258 = 3.1% (Wilson upper bound 6.0%); G3 passed because the random direction
did not reproduce the effect and the permuted gate was much worse.

The J-space localization diagnostic then found that Qwen3-4B's workspace-like
band is hs=23-29, peaking at hs=26, while this project's existing L34 write
site maps to hs=34 just after that band. This amendment asks the clean causal
successor: holding the predecessor mechanism class fixed, does refitting and
writing the same doubt-gated caution snap in the J-space band improve over the
existing hs34 write site?

Posture: exploratory Tier-2 causal layer-site test, local RTX 3090, raw-base
only. It is not a headline claim and is not pooled with the cross-family
confirmatory amendment. It does not touch any old trained-checkpoint cells.

## Design

Substrate: raw-base `unsloth/Qwen3-4B`, bf16, no adapter, no 4-bit
quantization. Same held-out surface as `doubt-gated-caution-tighten`, reusing
the promoted ID-only split manifest under
`experiments/common/doubt-gated-caution-tighten-heldout-split/` and the
predecessor's local materialization scheme. No question text, aliases, or
row-level generations are committed.

Candidate layers: hs=23, hs=26, hs=29, and hs=34. The first three are the
J-space mid-band localized by `j-space-localization-qwen3-4b`; hs34 is the
predecessor L34 reference.

For each candidate layer, the instrument refits on FIT only:

- `u_d = unit(mean(H[known_correct_answered FIT]) - mean(H[unknown_refused]))`.
- `pos_ctrl`: mass-mean caution/refuse direction from unknown_refused versus
  FIT confab.
- `neg_ctrl`: deterministic logistic confab-propensity direction, used only
  as the second orthogonalizer for `c_hat`.
- `c_hat = unit(pos_ctrl orthogonalized against {u_d, neg_ctrl})`.
- `tau`: Youden-J threshold on `neg_z_d = -z_d`, FIT confab versus FIT
  known_correct_answered, separately for each layer.

Generation and scoring mirror the predecessor: EOS-enabled greedy JSON
generation, `min_new_tokens=1`, `max_new_tokens=200`,
`enable_thinking=False`, clean_tighten requires a natural-stop single-object
JSON refusal, and known-correct cost is `not_well_formed_correct`.

Run shape: first run the local extraction, direction build, gate fit,
materialization, and smoke. The full held-out run executes the gated snap at
each layer with fixed realized projection target 200, then compares the best
mid-band layer against hs34.

Instrument files pinned at sign: `cell.yaml`, `gates.yaml`, `layers.py`,
`extract_layer_sweep_anchor.py`, `build_directions.py`, `gate_fit.py`,
`build_random_direction.py`, `materialize_rows.py`, `pipeline.py`,
`gen_lib.py`, `grader.py`, and `model_lib.py`.

## Prediction

Best mid-band layer (hs23/26/29, expected hs26) improves held-out confab
clean_tighten over the hs34 predecessor-reference layer by at least 10
percentage points without increasing known-correct false-refusal by more than
2 percentage points; hs34 itself remains viable under the predecessor gates.

## Falsifier

If the best mid-band layer improves confab clean_tighten by less than 10
percentage points over hs34, or increases known-correct false-refusal by more
than 2 percentage points, the J-space layer-site hypothesis is not supported
on this raw-base Qwen3-4B surface. If hs34 fails to reproduce a viable
predecessor reference, the run is a reference replication failure rather than
interpretable evidence about J-space mid-band superiority.

## Gates

- **G0 (instrument validity; stop, not outcome)**: local row text
  materializes with no missing questions or known-correct aliases; extraction
  contains hs23/hs26/hs29/hs34 for every needed row; FIT AUC for `neg_z_d` is
  >=0.90 at every layer; direction refits are byte-identical; smoke write
  readback lands within 5% + 0.5 absolute of dose 200; dosed smoke collapse
  rate is 0.
- **G1 (mid-band tighten improvement)**: best mid-band confab clean_tighten
  rate minus hs34 confab clean_tighten rate >= 10 percentage points.
- **G2 (no selectivity regression)**: best mid-band known-correct
  false-refusal cost minus hs34 cost <= 2 percentage points.
- **G3 (predecessor reference viable)**: hs34 confab clean_tighten >=60% and
  Wilson lower CI >50%, matching the predecessor G1 viability floor. If G3
  fails, do not read G1/G2 as evidence about J-space.

## Predictions scoreboard

| Predictor | Call |
|-----------|------|
| orchestrator | Option 1: mid-band wins cleanly. hs26 is most likely best; hs29 close; hs34 remains viable but not optimal. |
| user | Option 2: mid-band works but is not better than hs34. |

## Outcome

Resolved 2026-07-07 as a pre-outcome G0 stop (`null-result`). Aggregate public
artifacts are committed under `analysis-committed/`; row text, activation
scratch, and run logs remain gitignored under `analysis/`.

Preparation succeeded:

- Extraction captured 1,768 rows across hs23/hs26/hs29/hs34, producing 7,072
  activation vectors.
- Direction refits were byte-identical for all four layers.
- FIT gate AUC exceeded the G0 floor at every layer: hs23 0.9905, hs26
  0.9970, hs29 0.9984, hs34 0.9955.
- Runtime row materialization had missing_question=0 and
  missing_alias_on_known_correct_answered=0.

The signed dose-200 smoke then failed G0. Readback was accurate at every layer,
but collapse was not:

| layer | fired smoke rows | readback mean | readback within tolerance | collapse on dosed rows | confab clean_tighten |
|---|---:|---:|---:|---:|---:|
| hs23 | 3 | 200.018 | 100% | 100% | 0/4 |
| hs26 | 4 | 199.987 | 100% | 100% | 0/4 |
| hs29 | 4 | 200.027 | 100% | 0% | 4/4 |
| hs34 | 3 | 200.112 | 100% | 0% | 3/4 |

Because G0 pre-stated `collapse rate on dosed smoke rows is 0`, the full
held-out layer contrast was stopped and no `analysis/full_summary.json` was
completed. The conclusion is not that mid-band writing fails behaviorally; it
is that the predecessor's absolute dose-200 setpoint is not portable across
layer sites. hs23 and hs26 need their own coherent-window calibration before
the J-space layer-site hypothesis can be tested.
