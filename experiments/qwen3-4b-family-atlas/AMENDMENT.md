# qwen3-4b-family-atlas

Status: draft (not signed; do not launch as confirmatory evidence).

Keep this document the prose home for the experiment. The machine state
lives in `experiment.yaml` and is never duplicated here.

## Motivation and posture

`docs/atlas/family-layer-map.md`'s existing `qwen3` row cites
`j-space-localization-qwen3-4b`, and that row's own comparability note says
plainly: "A proper family-atlas cell for Qwen3-4B (capture-only eff_dim_frac
profile plus the three-axis held-out AUROC read panel, run through this
skill's own scripts) has not been registered as of this table's writing."
`j-space-localization-qwen3-4b` is a different instrument end to end: a
gradient-based J-lens over corpus-averaged JVP push vectors, measuring
direction verbalization, not this skill's capture-only representation-
variance participation-ratio profile plus held-out AUROC read panel. This
cell fills that registry hole: the fourth family-atlas cell (after
`jspace-family-atlas`'s llama32_3b_instruct and mistral7b_instruct_v03, and
`gemma-4-e4b-family-atlas`), and the first to atlas the substrate the
program's own ported-layer rule (`round(0.94 * (num_hidden_layers - 1))`,
copied to every `doubt-snap-cross-family-confirmatory` fleet member) was
originally copied FROM.

This is a READ-ONLY mapping experiment: no steering, no interventions, no
behavioral outcomes. Posture: exploratory instrument-building evidence,
never pooled with a confirmatory headline matrix. Its committed profile and
read panel become the layer-selection input for any future per-family
actuation amendment on this substrate that is not simply reusing the
already-resolved `doubt-gated-caution-tighten` L34 site.

## Design

Substrate: `unsloth/Qwen3-4B` at pinned revision
`64033659d5caf1b8ed7f929b29de705e93a4d468` (bf16, raw-base, no adapter, no
4-bit quantization -- the same checkpoint_tag `doubt-gated-caution-tighten`
used, NOT the `Qwen/Qwen3-4B` official checkpoint pinned elsewhere in the
program for an unrelated eval surface), 36 decoder layers, hidden size 2560.
`n_hidden_states` for full-depth capture = 37 (hs_index 0 through 36
inclusive).

**Pin provenance**: `experiments/h6-genstream-hook-firing-check/NOTEBOOK.md`
(2026-07-13 launch-time resolution entry): "revision: unsloth/Qwen3-4B main
= 64033659d5caf1b8ed7f929b29de705e93a4d468, unchanged on the Hub since
2025-05-13." No prior experiment in this substrate's own lineage
(`doubt-gated-caution-tighten`, `j-space-midband-write-sweep-qwen3-4b`,
`j-space-localization-qwen3-4b`) pins a revision itself (`model_lib.py`'s
`MODEL_NAME` loads via the bare repo id, no `revision=` kwarg), which is why
`docs/atlas/family-layer-map.md`'s existing `qwen3` row states "no revision
pin recorded." `h6-genstream-hook-firing-check` is the only place in the
repo this exact repo's revision hash is recorded, and its own text
corroborates it as stable ("unchanged on the Hub since 2025-05-13"), so this
cell adopts it as the pin.

Architecture verification: hidden_size=2560 is read directly from this
substrate's own committed direction vectors
(`experiments/doubt-gated-caution-tighten/analysis-committed/u_d_L34.json`,
`"hidden_dim": 2560`). num_hidden_layers=36 is corroborated by
`docs/atlas/family-layer-map.md`'s existing `qwen3` row (n_layers column)
and by the hs_index/decoder_block_index pairing already committed in
`experiments/j-space-midband-write-sweep-qwen3-4b/analysis-committed/build_manifest_layers.json`
(hs23 -> decoder_block_index 22, i.e. hs_index = decoder_block_index + 1).

**Row pool (see `cell.yaml` for full detail)**: this substrate already has
a committed, ID-only split manifest under the family-atlas role/split
taxonomy for TWO of its three roles --
`experiments/common/doubt-gated-caution-tighten-heldout-split/split_manifest.json`,
promoted from `doubt-gated-caution-tighten`'s own
`analysis-committed/split_manifest.json` and already reused once by
`experiments/j-space-midband-write-sweep-qwen3-4b`. Per `SKILL.md` step 2
("Reuse an existing experiment's committed split manifest verbatim whenever
one exists for this substrate"), this cell is a third, unmodified consumer
of that same manifest -- **not** a fresh-mining cell like
`gemma-4-e4b-family-atlas`. Held-out counts already clear this program's
standard floors: confab held-out 185 (floor 150), known_correct_answered
held-out 258 (floor 250).

**Known gap, blocking capture launch (TODO-LEAD to resolve before sign)**:
that promoted manifest's `rows` list carries row-level IDs for `confab`
(309) and `known_correct_answered` (430) ONLY. `unknown_refused` (1029
rows) is recorded there as a count field alone
(`n_unknown_refused_fit_only: 1029`) -- `doubt-gated-caution-tighten`'s own
`split_fit_heldout.py` never wrote it into the manifest's row list, because
its docstring states `unknown_refused` "is NOT split: it is never itself a
gated/graded row in this instrument, only fitting scaffold." The row-key
list exists only in a gitignored local file,
`experiments/doubt-gated-caution-tighten/analysis/l34_anchor_extract_manifest.json`,
which is not present in this worktree, the canonical checkout, or any
volume this scaffold could reach (ephemeral GPU-run scratch, never
committed). `unknown_refused` is this skill's doubt axis negative pole,
caution axis positive pole, and raw_refusal axis positive pole -- AG2
cannot run without its row keys. Deriving them is cheap and CPU-only
(`extract_l34_anchor.py:99`: `unknown_refused = [r for r in ak_stage1_pool
if not r["confab_on_unanswerable"]]`, against the same private AK Stage-1
pool `materialize_rows.py` already fetches question text from
deterministically), but executing that derivation and promoting its
row-key list into a committed ID-only manifest fragment is NOT done by this
scaffold and must happen before this cell can sign and launch capture.

Signal, per cell, once the row-pool gap above is closed (identical
procedure to `jspace-family-atlas` and `gemma-4-e4b-family-atlas`):

1. Full-depth anchor capture: hidden states at every decoder layer (0
   through 36) at the final-prompt-token anchor, for every row in the
   pool. FIT/held-out labels carried through unchanged.
2. Workspace profile: per-layer effective-dimension fraction
   (eff_dim_frac), the participation-ratio formula applied to the FIT-row
   anchor hidden-state matrix at each layer. Representation-variance PR,
   not comparable to the JVP-based profile
   `j-space-localization-qwen3-4b` already ran on this same substrate;
   comparable across this atlas's own cells only.
3. Per-layer read panel with bootstrap CIs, for doubt / caution /
   raw_refusal, plus the standard random-direction control. `unknown_refused`
   is `fit_only` (matching both `jspace-family-atlas` cells exactly); the
   deterministic `refused_fit`/`refused_eval` subdivision (seed 20260707,
   `profile_and_read_family_atlas_panel.py`'s `split_refused_pool()`)
   applies unchanged once its row-key list exists.
4. Committed outputs (aggregates and fitted metadata only, never row text):
   per-layer profile table, per-layer read AUROCs with CIs, the
   random-direction control, direction-fit manifests with seeds and
   sha256s, and the atlas summary JSON.

Execution: local RTX 3090 (pre-approved lane; no cloud/Modal without fresh
approval), matching where this substrate's own prior work
(`doubt-gated-caution-tighten`) already ran. **Open question for the lead
(not decided here)**: whether the standing local-GPU pinned-container
directive (`.skills/mechinterp-cells/reference/modal-launch.md`, "Local GPU
runs execute in a pinned container") applies to this cell's capture script.
Its literal text scopes to "every local-3090 `mechinterp` GPU verb
(`extract`, `steer`, `dose-calibrate`)" -- the tuner's own `mechinterp` CLI
verbs -- and this cell's `capture_family_atlas_cell.py` (like
`doubt-gated-caution-tighten`'s own `extract_l34_anchor.py`) is a bespoke
script using `AutoModelForCausalLM`/hooks directly, not a `mechinterp` CLI
invocation. No prior Qwen3-4B experiment in this repo runs inside the
pinned image. `gemma-4-e4b-family-atlas`, however, ran its own equally
bespoke capture script inside the pinned image anyway (its `AMENDMENT.md`
"Cost and sizing" section), treating the directive as covering any local-GPU
work rather than only literal `mechinterp` CLI calls. Recommend following
that precedent for consistency across atlas cells, but this is a judgment
call for the lead, not resolved by this scaffold.

**Lead ruling (2026-07-20): the gemma precedent applies.** This cell's
capture runs inside the pinned mechinterp-runner container image, the same
way `gemma-4-e4b-family-atlas` ran its bespoke capture script there. The
directive's intent is environment pinning for local-GPU evidence
generation, not a carve-out for scripts that happen to bypass the
`mechinterp` CLI; atlas cells stay environment-comparable across families.

Instrument files pinned at sign: `cell.yaml`, `gates.yaml`,
`render_qwen3_atlas.py` (this experiment's own capture render module, ported
from `experiments/common/renders/ah_a0_raw_base_render.py`, the same render
surface `doubt-gated-caution-tighten` uses), and local, byte-identical
copies of the shared `capture_family_atlas_cell.py` and
`profile_and_read_family_atlas_panel.py` (sha256-verified against their
`.skills/family-atlas/scripts/` canonical originals; copied rather than
referenced in place, matching `gemma-4-e4b-family-atlas`'s own precedent for
the `REPO_ROOT = ROOT.parents[1]` resolution these scripts assume -- verified
directly for this cell's placement at the standard `experiments/<slug>/`
depth, so no path-resolution gap exists here the way the gemma cell flagged
for itself).

## Prediction

Qwen3-4B (raw base, `unsloth/Qwen3-4B` at the pinned revision) shows an
interior workspace band: a contiguous set of layers strictly inside (20%,
85%) depth where eff_dim_frac peaks AND all three read axes (the
known-unknown (KU, answerability) axis, caution, and raw refusal --
artifact keys `doubt`/`caution`/`raw_refusal`) hold held-out AUROC >=
0.80, with the band's peak layer differing from the program's resolved
L34 write site (hs_index 34).

This is the program-standard atlas prediction, kept identical to
`jspace-family-atlas` and `gemma-4-e4b-family-atlas` deliberately: it has
failed 3 of 3 times on the profile limb, and this cell is the
pre-registered fourth-family test of whether that failure is the pattern
or a coincidence. The separately recorded predictor calls (below) state
what each party actually expects; this section states the registered
hypothesis the falsifier is armed against, unchanged from the program
default so the four cells stay directly comparable.

## Falsifier

No interior eff_dim_frac peak exists (the profile is monotone to the last
layer, OR the profile peaks in the outer 20% of depth on either end --
early-exterior, as `jspace-family-atlas` found for both llama and mistral
and `gemma-4-e4b-family-atlas` found for gemma, or late-exterior), OR no
layer inside (20%, 85%) depth reaches held-out AUROC >= 0.80 on all three
axes simultaneously.

## Predictions scoreboard

| Predictor | Call |
|-----------|------|
| orchestrator | Falsifier fires on the profile limb via an EARLY-EXTERIOR eff_dim_frac peak (outer 20% of depth), making qwen3 the fourth family in the decoupling pattern. Read panel healthy: a wide contiguous mid-band holds all three axes >= 0.80 held-out, including layers strictly inside (20%, 85%). Additional registered sub-call: the J-lens interior peak from `j-space-localization-qwen3-4b` (hs 23-29, a different instrument) does NOT reproduce in this eff_dim_frac profile -- the two instruments dissociate on peak location. (recorded pre-sign, 2026-07-20) |
| user | INTERIOR PEAK (recorded 2026-07-21, pre-sign): the first counterexample to the 3-of-3 early-exterior pattern -- the J-lens interior finding (hs 23-29, `j-space-localization-qwen3-4b`) was right about this family, and the eff_dim_frac profile follows it into the interior band. Direct head-to-head disagreement with the orchestrator's early-exterior call. |

## Gates

See `gates.yaml`: AG0 (capture/direction integrity), AG1 (profile), AG2
(read panel). Transcribed verbatim from the program-standard thresholds
(identical to `jspace-family-atlas`); no AG0a pool-mining gate is added,
because this cell reuses an already-vetted pool rather than mining a fresh
one -- see "Design" above for the narrower row-key-completeness gap that
blocks launch instead, and which the lead should resolve (and decide
whether it warrants its own pre-outcome gate, or is better handled as a
plain precondition) before signing.

## Predictions scoreboard

| Predictor | Call |
|-----------|------|
| orchestrator | |
| user | |

## Outcome

Filled at resolve. Record the verdict, the gate results, and the
one-sentence summary that also goes into `verdict:` in the manifest.
