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

**Resolution (2026-07-21): orchestrator WIN / user LOSS.** The eff_dim_frac
profile peaked early-exterior (hs5, depth 0.139), so the orchestrator's
call is correct on both clauses and the user's registered eff_dim_frac-peak
call is falsified. Credit recorded (see Outcome): the user's interior
intuition is vindicated on the read panel -- the three epistemic axes peak
interior (hs22-36) on top of the J-lens band -- so the miss is instrument
attribution, not signal location. Ratified by the PI at resolve
(2026-07-21, "you've defeated me again").

## Gates

See `gates.yaml`: AG0 (capture/direction integrity), AG1 (profile), AG2
(read panel). Transcribed verbatim from the program-standard thresholds
(identical to `jspace-family-atlas`); no AG0a pool-mining gate is added,
because this cell reuses an already-vetted pool rather than mining a fresh
one -- see "Design" above for the narrower row-key-completeness gap that
blocks launch instead, and which the lead should resolve (and decide
whether it warrants its own pre-outcome gate, or is better handled as a
plain precondition) before signing.

## Outcome

**Verdict (resolved 2026-07-21, lead adjudication): FALSIFIER FIRED on the
profile limb. Qwen3-4B is the fourth family with an early-exterior
eff_dim_frac peak decoupled from a healthy interior read band.** The
eff_dim_frac profile peaks at hs 5 of 36 (0.014891, depth_frac 0.1389),
inside the outer 20% of depth on the early side, matching the shape
`jspace-family-atlas` found for llama (L4/28) and mistral (L3/32) and
`gemma-4-e4b-family-atlas` found for gemma (hs4/42). The decoupling holds
4 of 4: the three-axis held-out read band is interior and wide (hs 22-36
clear >= 0.80 on all three axes simultaneously), nowhere near the
dimensionality peak.

### Run provenance
- Capture: `capture_run2` (container, pinned image
  sha256:d445632098cd..., CUDA 12.8), exit 0, 1768/1768 rows, AG0
  coverage_frac 1.0, 0 missing; 37 hidden states / 36 layers / 2560 dim.
  (`capture_run1` crashed on row 1 on a render env-var wiring defect fixed
  as signed revision 1 via `bin/exp repin`, zero rows captured, no data
  affected.)
- Profile + read panel: `read_panel_run2` (same container; CPU-only, host
  run1 completed the computation but could not write through the
  root-owned bind-mount dir, resolved by container re-run per the gemma
  precedent), exit 0, 68s, seed 20260707, 2000 bootstrap resamples,
  refused pool split 514 fit / 515 eval from the 1029 fit_only rows.
- All numbers below independently re-derived by the lead from the
  committed `analysis-committed/qwen3_4b_raw_base/atlas_summary.json`, not
  relayed from the subagent report.

### AG1 (profile)
- `eff_dim_frac_every_layer`: PASS (37/37 hidden states).
- `profile_reproducibility` (20% FIT-row subsample, tolerance +/-1 layer):
  PASS. Full-profile peak hs5; subsample peak hs5; delta 0. The top-5
  eff_dim_frac layers are hs {5, 4, 6, 3, 2} (all early); the interior
  hs20-36 is a flat 0.0068-0.0095 band well below the hs5 peak of 0.0149.
  The early peak is robust, not a flat-profile artifact.

### AG2 (read panel), no numeric pass/fail; the numbers are the atlas
Per-hidden-state held-out AUROC (point, 95% CI), all three axes, with the
random-direction control read alongside each axis:
- doubt (KU) climbs to >= 0.975 from hs5 onward and reads ~0.99-1.00
  across the interior, BUT is norm/position confounded: its own
  `ref_vs_known` control spikes to 0.87-0.98 at hs 21/24/32/36 (the same
  confound llama, mistral, and gemma all showed on this axis). Read the
  doubt column against that per-layer control, not against 0.5.
- caution clears 0.80 from hs22 (0.841) and holds 0.89-0.91 through the
  interior, against a `ref_vs_confab` control that stays <= 0.79
  everywhere -- a clean, large margin.
- raw_refusal clears 0.80 from hs21-22 (0.813/0.853) and rises to
  0.95-0.98 deep, against a `ref_vs_answered` control mostly <= 0.72
  (one spike to 0.829 at hs24) -- also a clean margin.
- Layers clearing >= 0.80 on ALL THREE axes simultaneously: hs 22-36 (15
  layers). Restricted to the falsifier's strict interior (20%, 85%) depth
  band (hs 8-30): hs 22-30 qualify (depth_frac 0.611-0.833). The interior
  read band is carried by caution and raw_refusal with real margins over
  their controls, so it survives the doubt-axis confound.
- At the profile's own peak (hs5): doubt 0.975, caution 0.670,
  raw_refusal 0.737 -- caution and raw_refusal both BELOW 0.80 where the
  dimensionality peaks. The dissociation is direct.

### Falsifier adjudication
The falsifier is a disjunction; the first disjunct is satisfied outright:
the single global eff_dim_frac peak is at hs5, depth_frac 0.1389 < 0.20,
early-exterior. (The second disjunct, "no interior layer reaches >= 0.80
on all three," is NOT satisfied -- the interior band is healthy -- but an
OR needs only one true disjunct.) Falsifier FIRED.

### Predictions scoreboard adjudication (head-to-head)
- **Orchestrator: WIN.** Called early-exterior eff_dim_frac peak (correct:
  hs5, 0.139 depth) AND the registered sub-call that the J-lens interior
  peak (hs 23-29, a different instrument) does NOT reproduce in the
  eff_dim_frac profile (correct: the profile peaks hs5, not hs23-29). Both
  clauses hold.
- **User: LOSS on the registered call, with credit.** Called INTERIOR PEAK
  for the eff_dim_frac profile; the profile peaked early-exterior (hs5), so
  the registered eff_dim_frac-peak prediction is falsified. BUT the
  underlying intuition -- that the interior is where this family's
  epistemic signal lives, following the J-lens hs23-29 finding -- is
  independently VINDICATED by the read panel: the three epistemic axes peak
  in the interior (hs 22-36), directly on top of the J-lens band. The miss
  is instrument attribution (eff_dim_frac follows the early-exterior
  dimensionality pattern; the read axes follow the interior signal), not
  the location of the epistemic signal.

### Scientific note (the dissociation this cell adds)
Two instruments that both nominally "localize the workspace" dissociate
cleanly on this family: the eff_dim_frac profile (representation-variance
participation ratio) peaks early-exterior at hs5, while the three-axis
read panel (held-out linear readability of KU / caution / refusal) peaks
interior at hs22-36. This is the same early-peak-then-readable-plateau
decoupling seen in llama, mistral, and gemma, now 4 of 4, and here it also
resolves the apparent tension with `j-space-localization-qwen3-4b`'s
interior J-lens peak: the J-lens was reading the interior readable regime,
not the dimensionality peak. The doubt-axis norm/position confound
replicates a fourth time and is recorded in the family-layer-map
comparability note.
