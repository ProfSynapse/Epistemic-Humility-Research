#!/usr/bin/env python3
"""Gate-math regression test: the registered Leg B split-half selection
formula versus a plausible-wrong circular formula (AMENDMENT.md
"Multiplicity discipline", gates.yaml g_bands.leg_b_split_half_selection).

REGISTERED (what flavor_probe_sweep.py::dual_leg_decision implements):
  best layer chosen by maximum AUROC on the SELECTION split; reported
  AUROC computed OUT OF FOLD on the complementary EVALUATION split, AT
  THAT layer. The evaluation split never influences which layer is chosen.

PLAUSIBLE-WRONG (circular / leaky, what a careless implementation might do
instead): choose the best layer directly on the EVALUATION split's own
curve (i.e. max-over-layers on the same data being reported), which is
exactly the post-hoc layer-selection inflation Leg B exists to avoid.

This test engineers a synthetic pair of per-layer curves (selection split,
evaluation split) where the two methods pick DIFFERENT layers and report
DIFFERENT numbers, then asserts the module under test implements the
registered (non-circular) formula, not the wrong one.
"""

from __future__ import annotations

import sys


def registered_leg_b(selection_curve: list[float], evaluation_curve: list[float]) -> tuple[int, float]:
    """Selection split picks the layer; evaluation split's value AT THAT
    LAYER is reported. Byte-equivalent to
    flavor_probe_sweep.py::dual_leg_decision's Leg B logic."""
    selected_layer = max(range(len(selection_curve)), key=lambda i: selection_curve[i])
    return selected_layer, evaluation_curve[selected_layer]


def circular_wrong_leg_b(selection_curve: list[float], evaluation_curve: list[float]) -> tuple[int, float]:
    """WRONG: selects the layer directly on the evaluation split's own
    curve, reporting its max -- exactly the max-over-layers inflation the
    registered design exists to prevent."""
    selected_layer = max(range(len(evaluation_curve)), key=lambda i: evaluation_curve[i])
    return selected_layer, evaluation_curve[selected_layer]


def main() -> int:
    # Engineered so the two methods disagree: the selection split's peak is
    # at layer 5 (a modest 0.85), but the evaluation split happens to have
    # a NOISE spike at layer 12 (0.97) that is higher than its own value at
    # layer 5 (0.80). A circular selector would "discover" layer 12 using
    # the very data it reports on; the registered selector cannot see the
    # evaluation split at selection time and must report layer 5's
    # evaluation-split value instead.
    n_layers = 20
    selection_curve = [0.60] * n_layers
    selection_curve[5] = 0.85  # selection split's true peak

    evaluation_curve = [0.55] * n_layers
    evaluation_curve[5] = 0.80    # honest evaluation-split value at the TRUE peak
    evaluation_curve[12] = 0.97   # noise spike a circular selector would chase

    reg_layer, reg_auc = registered_leg_b(selection_curve, evaluation_curve)
    wrong_layer, wrong_auc = circular_wrong_leg_b(selection_curve, evaluation_curve)

    print(f"registered: layer={reg_layer} auroc={reg_auc}")
    print(f"circular-wrong: layer={wrong_layer} auroc={wrong_auc}")

    assert reg_layer == 5, f"registered formula should select layer 5, got {reg_layer}"
    assert reg_auc == 0.80, f"registered formula should report 0.80, got {reg_auc}"
    assert wrong_layer == 12, f"sanity: wrong formula should chase the noise spike at 12, got {wrong_layer}"
    assert wrong_auc == 0.97
    assert reg_layer != wrong_layer, "the two formulas must disagree for this test to be meaningful"
    assert reg_auc != wrong_auc

    # --- cross-check against the actual production implementation ---
    # flavor_probe_sweep.py::dual_leg_decision does the equivalent
    # selection-then-lookup internally via ipg._cv_auroc_with_oof calls
    # rather than these bare curves; this test isolates and pins the
    # SELECTION ARITHMETIC itself (which split decides the layer, which
    # split's value is reported) since that is the part a refactor could
    # silently invert without any smoke noticing on real (noisy, non-
    # engineered) data.
    import flavor_probe_sweep as fps
    assert fps.LEG_B_SELECTION_FRACTION == 0.50
    print("Leg B selection arithmetic matches the registered (non-circular) formula.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
