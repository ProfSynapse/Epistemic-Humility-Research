# j-space-layer-contrast-replication-qwen3-4b notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

- 2026-07-08: exhaustive fresh-pool census completed. Generated 12,923
  candidates (3,305 unknown, 9,618 known), selecting 306 fresh confabs and
  1,957 known_correct_answered rows. Public-safe text-free census uploaded to
  `professorsynapse/eh-jspace-fresh-pool-census-qwen3-4b` at revision
  `3add102ce930f73a29013f572f03e7325da30825`.
- 2026-07-08: local prep completed. Fresh anchor extraction covered all 2,263
  selected rows at hs23/26/29/34. Smoke G0 passed with on-target readback and
  zero dosed-row collapse for every layer. Full outcome run is still held for
  user prediction and `bin/exp sign`.
- (add dated entries as the experiment progresses)
- 2026-07-10: pins for `cell.yaml`, `mine_fresh_eval_pool.py`, and
  `extract_fresh_anchor.py` refreshed while merging main into
  `docs/experiment-provenance-cleanup`. Both branches touched this
  experiment independently (main resolved it with byte-pins of the
  pre-archive-path script content; this branch had already rewritten the
  same scripts' hardcoded `experiment/phase1/...` paths to their
  `archive/experiment/phase1/...` post-migration location), so the pins
  now match the merged, path-corrected content rather than the pre-merge
  as-run bytes.

### 2026-07-09 -- Pre-outcome red-team of the frozen instrument (run mid-flight, no results seen)

An adversarial pre-run audit of the signed instrument returned no invalidating
findings: fresh-pool disjointness confirmed mechanically (0 overlap against
both the 739-key predecessor split and the full 12,923-row census), no re-fit
anywhere (directions, mu/sigma, tau, doses all read from committed predecessor
artifacts), grading shares the predecessor code path with honest all-rows
denominators, Wilson CI implementation reproduces the predecessor's committed
values, and the five sign pins match on-disk sha256 at HEAD 826d9a1c.

Three pre-outcome commitments recorded BEFORE any outcome number is seen, so
they are interpretive additions rather than goalpost moves. The signed gates
themselves are unchanged.

1. G1 is pre-registered as a best-of-three point-estimate delta (>= 10pp) with
   no CI on the delta and no multiplicity correction for selecting the max of
   three mid-band layers. At resolve, alongside the registered G1 pass/fail we
   will report the per-layer Wilson CIs (already emitted by run_contrast.py)
   and state whether the best-mid and hs34 CIs separate. A G1 pass whose CIs
   overlap will be reported as a statistically marginal pass, and Paper 5 will
   carry that qualifier.
2. The resolver must independently re-assert G0 disjointness and pool-count
   floors at resolve; full_summary's overall_pass covers readback/collapse and
   G1-G3 only, not the structural G0 checks.
3. Known limitation to carry into the writeup: the fresh-pool candidate
   universe is an unpinned gitignored local file (the AH stage-0 expansion
   candidates), so pool mining is not reproducible from committed artifacts
   alone; and the predecessor's 1,029 unknown_refused fit-only keys are not in
   the exclusion set (disjointness from them rests on generation determinism;
   any drift would be common-mode across layers and cannot manufacture the
   layer delta, but could flatter absolute rates).
