# Family Atlas Surface-Matched JSON-Completion Control notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

- 2026-07-22: Ran a CPU-only, successor-design matching-feasibility diagnostic
  over the complete retained Stage A exhaust: 5,200 generation records per
  model, yielding 435 eligible Gemma triads and 149 eligible Qwen triads. No
  model was loaded, no activation tensor was read, and no scientific endpoint
  or current-experiment gate was recomputed. The diagnostic used the pinned
  mechinterp image with scikit-learn 1.7.2 and three deterministic 120,000-step
  optimization seeds. Private ID-only selection manifests remain under
  `analysis/`; the aggregate contains counts, balance diagnostics, and
  classifier scores only. Its local path is
  `analysis/diagnostics/matching_feasibility_summary.json`, with SHA-256
  `afb1bee60ef771e6d6a46bced0799a5cda3c7c9fb91fdf4f7709b7d574854aad`.

  The diagnostic shows that stricter subset search does not provide a robust
  successor design. Scalar-only 128-triad selections passed the existing G2
  thresholds in 1 of 3 Gemma seeds and 2 of 3 Qwen seeds. Joint scalar-plus-
  lexical 128-triad selections passed in 3 of 3 Gemma seeds and 0 of 3 Qwen
  seeds. Two disjoint 64-triad partitions passed together in 0 of 3 seeds for
  both models. A nested 128-triad primary plus balanced 64-triad sensitivity
  passed together in 1 of 3 Gemma seeds and 0 of 3 Qwen seeds. The three roles
  share zero category levels by construction, and exact-original-pair coverage
  is especially sparse for Qwen confab rows at 31 of 510.

  This is feasibility evidence, not a post hoc replacement gate. It supports a
  separately registered residualization-only successor on the complete
  existing atlas populations. That design should run the cross-fitted surface-
  to-activation residual profile that the earlier Shape A hard stop never
  reached, retain treatment-strength, planted-signal, permutation, and full-row
  subsample controls, and keep optimized matching descriptive rather than
  decisive. Any successor remains subject to a new signed instrument and PI
  approval.
- 2026-07-22: The PI explicitly approved both model-specific Stage A
  generations after signing: the 5,200-row Gemma-4-E4B-it generation and the
  5,200-row Qwen3-4B generation. They will run sequentially on the single local
  RTX 3090, with Gemma first and Qwen only after the lane is released. This
  approval does not authorize either Stage B full-depth capture.
- 2026-07-22: The PI approved signing after both model smokes, the planted
  matcher control, containment, and the 51-test suite passed. `bin/exp sign`
  pinned all 12 instrument files. The frozen instrument fingerprint is
  `eee0f391903ee0896913bd1622b023a243fecacb154e2c63957f01334e24caaf`.
  No Stage A generation or Stage B capture was launched by signing.
- 2026-07-22: Both approved pre-sign GPU smokes passed in the exact pinned
  vLLM 0.23.0 V1 image on the local RTX 3090. Each model produced five
  canonical 31-row outputs with identical completion token IDs, finish
  reasons, parsed objects, and row logs across original order, fixed
  permutation, and a hard-kill after 16 durable rows followed by resume. Both
  had strict whole-output validity 1.0 without salvage, no suppressed token
  evidence, and all 11 predecessor failure IDs finished naturally before the
  512-token cap. The two ID-only smoke manifests overlap on 30 rows and each
  contains all 11 failure IDs. Gemma's aggregate SHA-256 is
  `932c5de861d1ad4fd46120d54f22b748e6f0ecb636683d7f6d31bced6183309f`;
  Qwen's is
  `80daeb44e1e615936ef6d7212d2b766e82854bbe5a07dccfa31d96f55858fc6b`.
  Terminal containment passed and the GPU returned to 0 MiB used.
- 2026-07-22: The PI explicitly selected EARLY for Gemma and Qwen, with no
  G0-G4 indeterminacy expected after both pre-sign smokes pass. The PI also
  separately approved the 31-row Gemma and 31-row Qwen pre-sign GPU smokes on
  the local RTX 3090. This approval does not authorize either 5,200-row Stage A
  generation or any full-depth capture.
- 2026-07-22: Ran the CPU-only planted matcher reachability control before
  signing. The real matcher produced 128 intact triads with exactly 64 FIT and
  64 held-out triads. The committed output contains aggregates and a private
  manifest hash only; planted row-level evidence remains under `analysis/`.
- 2026-07-22: Chose Tier 2 before implementation. Exact alternate-stop
  suppression and a 512-token completion cap change output-affecting generation
  settings outside the resolved predecessor's authorized knobs. The successor
  remains exploratory and cannot be pooled with headline atlas rows.
- 2026-07-22: The PI approved a separately governed repair after the predecessor
  failed Gemma G0. The initial proposal used `ignore_eos=true`. Before any
  successor model load, pinned vLLM 0.23.0 source inspection showed that this
  would suppress canonical EOS without guaranteeing termination when xgrammar
  completes its grammar. The draft was corrected to suppress only exact
  model-specific alternate stop tokens while retaining canonical EOS. No
  successor GPU process or scientific row has been launched. The corrected
  31-row per-model smoke and successor scoreboard require explicit PI approval
  before signing.
- 2026-07-22: The failure-set smoke is data-exhaustive for the observed interface
  defect. It unions each predecessor 20-row stratified smoke with all 11 Gemma
  G0 failure IDs, with zero overlap, for exactly 31 rows per model. It also
  requires exact targeted parity against all 5,189 predecessor-valid Gemma rows
  in the later full run. Predecessor completion text and token evidence remain
  private; the promoted shared artifact contains IDs, counts, and hashes only.
