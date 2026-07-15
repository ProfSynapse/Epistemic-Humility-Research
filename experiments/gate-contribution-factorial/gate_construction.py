"""True-doubt-gate and permuted-gate construction for
gate-contribution-factorial (cell.yaml `gates_construction`).

Pure CPU functions; no model, no GPU. Two gates per family:

  true_doubt_gate    per-row fire iff neg_z_d >= tau_frozen (cell.yaml
                      `families.<family>.gate.fire_rule`). `gate_decision` is
                      ported byte-for-byte (logic) from
                      `qwen35-4b-midband-heldout/capture_anchors.py`'s own
                      `gate_decision` -- the SAME math H3/H4/H6/midband-
                      heldout all share. For qwen, this experiment REUSES the
                      already-computed row-level fire decisions
                      (`fire_decisions_heldout.jsonl`, staged at SC0) rather
                      than recomputing them from raw anchor tensors: the
                      anchor extraction pass is GPU-adjacent (a forward pass
                      over a 1,692-row pool) and midband-heldout already ran
                      it once at this exact frozen operating point;
                      `load_qwen_fire_decisions` is a pure read of that
                      artifact, gated by an independent CPU cross-check
                      (`verify_qwen_fire_counts`) against the row-level
                      `role`x`fire` counts the AMENDMENT itself cites
                      (confab 1286/1332, known 17/360). For mistral, the true
                      gate's fired ROW SET is read directly off RR2's own
                      `heldout__gated.jsonl` (the fired-rows-only runlog RR2
                      persisted; cell.yaml `true_gate_fire_counts`
                      {confab: 1303, known: 0}).

  permuted_gate       fire_count == the true gate's total fire count, rows
                      chosen uniformly at random (without replacement) over
                      the FULL combined deployment pool (confab + known),
                      fixed pre-registered seed (cell.yaml
                      `gates_construction.permuted_gate`; AMENDMENT.md
                      "Permuted gate", item 11). `draw_permuted_gate_indices`
                      is ported byte-for-byte (logic) from
                      `qwen35-4b-midband-heldout/pipeline.py`'s own function
                      of the same name (`np.random.default_rng(seed).choice
                      (pool_size, size=n_fired, replace=False)`, sorted).

BUILD-TIME INTERPRETATION (pool ORDER for the permuted draw; cell.yaml
registers the pool COMPOSITION and the SEED, not an explicit row order):

  qwen      uses the EXACT row order of `heldout_rows_for_steer.jsonl` (the
            same file midband-heldout's own `pipeline.py` iterated over when
            IT drew ITS OWN permuted_gate arm at the SAME seed, 20260713).
            This choice is not incidental: it lets `permuted_gate_row_keys`
            reproduce midband-heldout's already-on-disk `permuted_gate.jsonl`
            row_key set EXACTLY, which `test_factorial_smoke.py` verifies
            against that on-disk artifact as a genuine cross-experiment
            integrity check (not a synthetic fixture).
  mistral   has no prior permuted-gate pass to reproduce (RR2/RR3 never ran
            one). This harness defines the pool order as: confab rows sorted
            by row_key, then known_correct_answered rows sorted by row_key
            -- a clean, fully-specified, deterministic convention, recorded
            here for the lead's review.
"""

from __future__ import annotations

from typing import Any

import numpy as np


def gate_decision(proj_d: float, mu_d: float, sigma_d: float, tau: float) -> dict[str, Any]:
    """Frozen fire rule: fire iff neg_z_d = -z_d >= tau_frozen, z_d
    standardized with the family's own FIT-pool mu_d/sigma_d and clipped to
    [-2, 2]. Identical math to H3/H4/H6/midband-heldout's own gate_decision."""
    z_d = float(np.clip((proj_d - mu_d) / sigma_d, -2.0, 2.0))
    score = -z_d
    fire = bool(score >= tau)
    return {"proj_d": proj_d, "z_d": z_d, "score_neg_z_d": score, "fire": fire, "tau": tau}


def verify_qwen_fire_counts(fire_decisions: list[dict[str, Any]]) -> dict[str, Any]:
    """Cross-checks the staged fire_decisions_heldout.jsonl row-level counts
    against the AMENDMENT's own descriptive figures (confab 1286/1332 fired,
    known 17/360 fired; AMENDMENT.md "Design" table, gates_construction
    comment)."""
    n_confab = sum(1 for r in fire_decisions if r["role"] == "confab")
    n_confab_fired = sum(1 for r in fire_decisions if r["role"] == "confab" and r["fire"])
    n_known = sum(1 for r in fire_decisions if r["role"] == "known_correct_answered")
    n_known_fired = sum(1 for r in fire_decisions if r["role"] == "known_correct_answered" and r["fire"])
    expected = {"n_confab": 1332, "n_confab_fired": 1286, "n_known": 360, "n_known_fired": 17}
    observed = {"n_confab": n_confab, "n_confab_fired": n_confab_fired, "n_known": n_known, "n_known_fired": n_known_fired}
    return {"expected": expected, "observed": observed, "pass": expected == observed}


def qwen_true_gate_fired_row_keys(fire_decisions: list[dict[str, Any]]) -> list[str]:
    return sorted(r["row_key"] for r in fire_decisions if r["fire"])


def draw_permuted_gate_indices(pool_size: int, n_fired: int, seed: int) -> list[int]:
    """n_fired indices chosen uniformly at random (without replacement) over
    range(pool_size). Byte-for-byte port of
    `qwen35-4b-midband-heldout/pipeline.py:draw_permuted_gate_indices`."""
    rng = np.random.default_rng(seed)
    return sorted(rng.choice(pool_size, size=n_fired, replace=False).tolist())


def qwen_permuted_gate_row_keys(pool_row_keys_in_file_order: list[str], n_fired: int, seed: int) -> list[str]:
    """Pool order = the exact `heldout_rows_for_steer.jsonl` file order
    (midband-heldout's own convention; see module docstring)."""
    idx = draw_permuted_gate_indices(len(pool_row_keys_in_file_order), n_fired, seed)
    return sorted(pool_row_keys_in_file_order[i] for i in idx)


def mistral_permuted_gate_row_keys(confab_row_keys: list[str], known_row_keys: list[str], n_fired: int, seed: int) -> list[str]:
    """Pool order = confab rows sorted by row_key, then known rows sorted by
    row_key (this harness's own build-time convention; see module
    docstring -- mistral has no prior permuted-gate pass to reproduce)."""
    pool = sorted(confab_row_keys) + sorted(known_row_keys)
    idx = draw_permuted_gate_indices(len(pool), n_fired, seed)
    return sorted(pool[i] for i in idx)
