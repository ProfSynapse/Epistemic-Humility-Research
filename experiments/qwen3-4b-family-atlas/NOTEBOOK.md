# Qwen3-4B family atlas notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

- 2026-07-21 (scaffold): `bin/exp new` scaffolded this experiment (type
  probe-fit, status draft). Filled `cell.yaml`, `gates.yaml`,
  `render_qwen3_atlas.py` (ported from
  `experiments/common/renders/ah_a0_raw_base_render.py`), and byte-identical
  copies of the shared `capture_family_atlas_cell.py` /
  `profile_and_read_family_atlas_panel.py` (sha256-verified against
  `.skills/family-atlas/scripts/`). `AMENDMENT.md` Prediction/Falsifier left
  as TODO-LEAD placeholders per the orchestrator's instruction; not signed.
  Not launched: no GPU work, no mining, no model downloads.
  Precondition inventory findings (full detail in `AMENDMENT.md` "Design"
  and `cell.yaml` comments):
  - Model pin: `unsloth/Qwen3-4B` @
    `64033659d5caf1b8ed7f929b29de705e93a4d468`, sourced from
    `experiments/h6-genstream-hook-firing-check/NOTEBOOK.md` (only recorded
    revision hash for this repo id anywhere in the codebase; corroborated
    stable on the Hub as of that entry). Distinct from the unrelated
    `Qwen/Qwen3-4B` official pin used by
    `experiments/aq-sycophancy-activation-actuator`.
  - Architecture: num_hidden_layers=36, hidden_size=2560, n_hidden_states=37
    (cross-checked against committed direction-vector JSONs and the
    hs_index/decoder_block_index pairing already committed elsewhere in the
    program for this substrate).
  - Row pool: a vetted, committed split manifest already exists
    (`experiments/common/doubt-gated-caution-tighten-heldout-split/split_manifest.json`,
    promoted from `doubt-gated-caution-tighten`), clearing this program's
    standard held-out floors (confab held-out 185 >= 150; known_correct
    held-out 258 >= 250) for the two roles it carries row-level IDs for.
    NOT a fresh-mining cell; no AG0a gate added.
  - BLOCKER before sign: that manifest's `unknown_refused` role (1029 rows)
    is a count field only, no row-key list. The list exists only in a
    gitignored, no-longer-present local file. Needs a cheap CPU-only
    promotion step (deterministic re-derivation from the private AK
    Stage-1 pool, per `extract_l34_anchor.py:99`'s filter) before capture
    can run AG2's read panel (unknown_refused is the doubt axis's negative
    pole, the caution axis's positive pole, and the raw_refusal axis's
    positive pole).
  - Open question for the lead: whether the standing local-GPU pinned-
    container directive applies to this cell's bespoke capture script (see
    AMENDMENT.md "Design", "Execution" paragraph); not resolved here.
