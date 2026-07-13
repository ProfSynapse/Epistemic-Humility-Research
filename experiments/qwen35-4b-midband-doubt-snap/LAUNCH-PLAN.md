# qwen35-4b-midband-doubt-snap -- launch plan

Draft-only. This document lists stage costs/ETAs actually observed during
pre-sign prep, and the decision points reserved for the lead/user at sign
time (dose grid values, gate floors). It does not authorize Stage C.

## Stage costs observed (this session, local RTX 3090)

| Stage | What | Wall time | GPU mem |
|---|---|---:|---:|
| Data reuse | download + sha256-verify 3 Modal files, build FIT working file | < 1 min | n/a (CPU) |
| Stage A (J-lens profile) | 14 hs_index points x 3 random dirs x 12 prompts, double-backward JVP | 2554.0s (~42.6 min) | ~9.8 GiB |
| Stage B extract (anchor capture) | 1,308 FIT rows x 4 layers (hs20/23/26/30), single forward pass per row (no grad) | 853.9s (~14.2 min) | ~8.3 GiB peak (observed) |
| Stage B fit (direction + gate fit) | CPU-only, numpy/sklearn, 4 layers x 2 (reproducibility refit) | < 5s | n/a (CPU) |
| Stage C (dose ladder) | NOT RUN. Harness script not yet written. | n/a | n/a |

Both prep stages ran on the local RTX 3090, GPU-idle-checked before launch
(0% util, 1 MiB used both times). Actual per-layer numbers are in
`analysis-committed/profile_summary.json` (Stage A) and
`analysis-committed/build_manifest.json` (Stage B).

## Why Stage A is cheap relative to the Qwen3-4B reference in prompt count but not in wall time

Qwen3.5-4B's hybrid linear-attention (`chunk_gated_delta_rule`) blocks run
the slow, un-accelerated PyTorch fallback (no `flash-linear-attention`
installed). Per-eval JVP cost measured at hs_index=2 (worst case, full-depth
backprop) is roughly 50x the Qwen3-4B jlens.py reference's own full-profile
cost per eval. Stage A therefore uses 12 prompts x 3 random directions
instead of that reference's 1000 x 5 -- a screening tool for band location,
not a statistically hardened characterization. The actual gates (AUC >= 0.90,
effect size) live in Stage B/C, which use ordinary forward passes (no JVP,
no double-backward) and are NOT subject to this slowdown.

## Proposed per-layer dose grids for Stage C (draft -- decision point for sign)

Rationale: the late site (hs30) proved that ABSOLUTE dose setpoints do not
transfer even within one model once `sigma_c` differs meaningfully across
layers (its own `sigma_c=2.80` was ~4.7x smaller than the Qwen3-4B
exploratory reference, so a dose that was coherent there was a ~38-sigma
write here). The Qwen3-4B same-model chain independently found the same
lesson (`j-space-midband-write-sweep-qwen3-4b`'s dose-200 collapse at
mid-band layers hs23/hs26, recovered by per-layer calibration in
`j-space-midband-dose-calibration-qwen3-4b` to hs23=25/hs26=75/hs29=125,
each layer settling at a DIFFERENT multiple of its own `sigma_c`). This
amendment therefore proposes grids anchored to each candidate layer's OWN
fitted `sigma_c` (from `analysis-committed/build_manifest.json`), not a
shared absolute grid:

- Grid shape: `{2, 4, 6, 8, 12, 16, 20} x sigma_c` for each candidate
  mid-band layer, i.e. seven multiples of that layer's own fitted
  `sigma_c`, spanning from a small write (2-sigma) up through a write in
  the same relative range that produced the late site's own peak (recall
  the late site's registered grid started at "already ~38-sigma" and
  found its coherent peak far below that, at dose 40 against `sigma_c=2.80`
  -> ~14.3-sigma; this grid's upper end (20-sigma) deliberately brackets
  that observed late-site peak rather than assuming it transfers).
- Selection rule (unchanged from the registered late-site/cross-family
  rule): lowest dose with FIT refused_rate >= 0.60 AND well_formed_rate
  >= 0.80 AND known-correct false_refusal <= 0.10. If none qualifies, the
  cell fails G0/G1 dose viability and is recorded as such, exactly as the
  late site was.
- Per-layer sigma_c values and the resulting absolute dose grids, from
  `analysis-committed/build_manifest.json` (Stage B complete). All four
  layers clear the registered min-AUC-0.90 gate comfortably; note that all
  three mid-band candidates have SMALLER sigma_c than the late site
  (hs30=2.8165), so mid-band coherent windows will sit at smaller absolute
  doses than the late site's own dose-40 peak, not larger:

  | hs_index | sigma_c | AUC (FIT) | tau_frozen | dose grid `{2,4,6,8,12,16,20} x sigma_c` |
  |---:|---:|---:|---:|---|
  | 20 | 1.5760 | 0.9929 | -0.5897 | 3.2, 6.3, 9.5, 12.6, 18.9, 25.2, 31.5 |
  | 23 (peak) | 2.1155 | 0.9926 | -0.7017 | 4.2, 8.5, 12.7, 16.9, 25.4, 33.8, 42.3 |
  | 26 | 2.2364 | 0.9941 | -0.7295 | 4.5, 8.9, 13.4, 17.9, 26.8, 35.8, 44.7 |
  | 30 (late comparator, refit this run) | 2.8165 | 0.9960 | -0.5942 | 5.6, 11.3, 16.9, 22.5, 33.8, 45.1, 56.3 |

  Sanity check against the cited late-site history: the recalibrated grid's
  observed peak (dose 40) and collapse onset (doses 50/60) map to
  40/2.8165=14.2σ and 50/2.8165=17.75σ / 60/2.8165=21.3σ -- these fall
  inside the 6x-8x bracket of this same grid shape (16.9σ-22.5σ at hs30),
  confirming the {2,4,6,8,12,16,20}x shape brackets the one empirically
  known coherent-to-collapse transition on this substrate rather than
  missing it. hs30's refit numbers here (sigma_c=2.8165, AUC=0.9960,
  tau=-0.5942) reproduce the cited cross-family-confirmatory build_manifest
  values (sigma_c=2.8006, AUC=0.99599) closely -- small residual difference
  is consistent with this experiment's independent refit under its own
  render path rather than a byte-for-byte replay, and is not itself a
  finding.

**Open item for whoever signs this experiment:** `run_dose_ladder.py` (the
Stage C harness) has not been written. It should mirror
`j-space-midband-write-sweep-qwen3-4b/pipeline.py`'s structure (gated
erase-write, `anchor_onward`, EOS-enabled greedy JSON generation,
`min_new_tokens=1`, `max_new_tokens=200`) but wire the tuner's
`shared/utilities/run_log.py` RunLog per row (available at this worktree's
pinned submodule commit `cd30d482`, unlike the Qwen3-4B same-model
predecessor which ran before RunLog existed and flagged its own missing
per-row persistence as a limitation -- see
`j-space-layer-contrast-rep2-multisource/AMENDMENT.md`'s "Per-row
persistence (RunLog)" section for the exact wiring pattern to copy). Given
1,308 FIT rows x N candidate layers x 3 arms x 7 doses, this is very likely
to exceed 15 minutes and RunLog is not optional.

## Decision points reserved for the lead/user at sign

1. Final mid-band candidate layer set (from Stage A's profile result).
2. Final per-layer dose grid values (the 7-multiple-of-sigma_c grid above is
   a proposal, not a floor; sign can widen/narrow it based on the actual
   `sigma_c` values Stage B produced).
3. G1 floor values (0.60 refused / 0.80 well-formed / 0.10 false-refusal
   are carried over from the cross-family confirmatory's own registered
   bars, not independently re-derived for this substrate).
4. Whether to write and test `run_dose_ladder.py` before or as part of
   signing.
