# QUALIFY Mode Separability on Base-Model Readout notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

- **2026-07-23, design + pre-sign smoke (draft, not signed).** Built
  `cell.yaml`/`gates.yaml`/`extract_hidden_states.py`/`fit_readouts.py`/
  `test_qualify_separability.py` per the team-lead's brief. Key findings from
  design-time verification (all CPU-only, `CUDA_VISIBLE_DEVICES=""`):
  - The exact pinned Stage-S starting checkpoint
    (`unsloth/Qwen3-4B-bnb-4bit@cad0bedfdd862093a12af478cb974ab2addd0e0a`)
    loads on CPU without any substrate substitution -- transformers falls back
    to a torch dequant forward (no CUDA `gemm_4bit_forward` kernel, missing
    `kernels` package warning is cosmetic). 36 hidden layers, 37 hidden
    states, hidden_size 2560.
  - 20-row real-script smoke (`extract_hidden_states.py --limit 20`): model
    load 7.4s, forward pass 0.872 s/row. Projected full run (2,811 fit + 602
    dev = 3,413 rows): ~50 min wall clock.
  - `fit_readouts.py`'s statistics pipeline (`fit_depth`) validated end-to-end
    on synthetic data at the real dimensionality (2811x2560 fit, 602x2560
    dev); found and fixed a `sklearn>=1.7` API break (`LogisticRegression`
    dropped the `multi_class` kwarg -- `lbfgs` now fits multinomial
    automatically for >2 classes, which is what was wanted anyway).
    Measured ~19s for the full 4-depth PCA+fit+bootstrap loop on
    realistic-shaped synthetic data -- comfortably short-run.
  - `shared/utilities/run_log.py` (`RunLog`, the project's canonical
    incremental-writer) is unavailable in this worktree: it lives on tuner
    branch `feature/runlog`, not `main`, and this worktree's submodule
    checkout is empty (`git submodule update --init synaptic-tuner` timed
    out after 2 minutes, network-blocked or auth-gated in this sandbox, not
    investigated further). Built a narrow purpose-specific substitute
    (`ResumableFeatureWriter`) instead of a full RunLog port; unit-tested
    for correct resume-skip behavior.
  - Unit tests: `python3 -m pytest test_qualify_separability.py` — 6 passed,
    1.7s wall.
  - `bin/exp validate` — OK, no warnings for this slug.
  - STOPPED here per instructions: sent the lead a report with the proposed
    gates/predictions and their provenance, the measured smoke numbers, and
    four explicitly flagged design choices for adjudication. Full extraction
    + fit run authorized only after lead sign + explicit go-ahead.
