# Matrix expansion — how `matrix.yaml` maps to PROTOCOL v0.3 cells

`config/matrix.yaml` encodes PROTOCOL v0.3 §3.1 / §3.1a as data.
`scripts/run_matrix.py` expands it into cells and ASSERTS the resulting counts
match the pre-registered design. The assertion is the pre-registration guard:
a typo in `matrix.yaml` that changes a count ABORTS the run rather than silently
altering the locked experiment.

## The product

| Block | Expansion | Count |
|-------|-----------|-------|
| Headline 4B | 3 arms (sft, dpo, kto) × 3 seeds [1,2,3] | 9 |
| LR panel 4B | 3 arms × 2 multipliers [3.0, 0.333] @ panel_seed | 6 |
| beta panel 4B | 2 arms (dpo, kto; `has_beta: true`) × 2 betas [0.05, 0.5] @ panel_seed | 4 |
| **4B total** | | **19** |
| Confirm 8B | 3 arms × `confirm_8b_seeds` (3) | 9 |
| **8B total** | | **9** |
| Bridge | 2 recipes × 1 seed | 2 |
| **Bridge total** | | **2** |

`run_matrix.py` holds these as `EXPECTED_COUNT_4B = 19`, `EXPECTED_COUNT_8B = 9`,
`EXPECTED_COUNT_BRIDGE = 2`. `expand_4b` / `expand_8b` / `expand_bridge` each
raise `MatrixError` if their block's count drifts.

## Per-arm-relative LR (structural, not hardcoded)

The LR panel multiplies each arm's OWN default learning rate — read FROM that
arm's recipe at materialization time — by the multiplier. So SFT (default 2e-4),
DPO (5e-6), and KTO (1e-6) each get their own 3× / 0.333× cells. The
per-arm-relative rule is structural because the default is sourced from the
recipe, never hardcoded in the matrix.

## Headline vs panel

Headline cells (9 @ 4B, 9 @ 8B) produce the pre-registered numbers. Panel cells
(LR + beta, 10 @ 4B) are robustness-only and are tagged distinctly in the run-id
coordinate (`cell_type` = `lr_panel` / `beta_panel`) so the eval-side layer-2
aggregation (arch §6.6) isolates them from the headline mean+CI.

## Changing the matrix

Do NOT loosen the count assertions to absorb a `matrix.yaml` edit. The counts
are pre-registered; a change requires a NEW signed PROTOCOL revision FIRST, then
the matching edit to both `matrix.yaml` and the `EXPECTED_COUNT_*` constants.
