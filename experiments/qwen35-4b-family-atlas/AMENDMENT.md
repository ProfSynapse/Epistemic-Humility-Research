# Qwen3.5-4B family atlas

Status: draft (not signed; do not launch as confirmatory evidence).

Keep this document the prose home for the experiment. The machine state
lives in `experiment.yaml` and is never duplicated here.

## Motivation and posture

`docs/atlas/family-layer-map.md` carries a `qwen3.5` row, but it is a
STEER-CELL row, not an atlas row: it records a behaviorally established
mid-band WRITE site (hs20, from `qwen35-4b-midband-doubt-snap` and
`qwen35-4b-midband-heldout`) and explicitly states "not measured (no
atlas-standard eff_dim_frac profile has run for this family)" for the
profile-peak, interior-band, and read-panel columns. That row closes with:
"Family still owes a standard family-atlas cell before any read-panel-based
layer decision." This cell fills that hole: the fifth family-atlas cell
(after `jspace-family-atlas`'s llama32_3b and mistral7b, then
`gemma-4-e4b-family-atlas`, then `qwen3-4b-family-atlas`), and the FIRST to
atlas the `Qwen/Qwen3.5-4B` substrate -- a different checkpoint from the
`unsloth/Qwen3-4B` surface `qwen3-4b-family-atlas` mapped (same family
lineage, NOT the same model).

This is a READ-ONLY mapping experiment: no steering, no interventions, no
behavioral outcomes. Posture: exploratory instrument-building evidence,
never pooled with a confirmatory headline matrix. Its committed profile and
read panel become the layer-selection input for any future per-family
actuation amendment on this substrate that is not simply reusing the
already-resolved hs20 write site.

**Why this family sharpens the standing question.** All four prior families
showed the same shape: the eff_dim_frac profile peaks early-exterior (llama
L4/28, mistral L3/32, gemma hs4/42, qwen3-4b hs5/36) and DECOUPLES from a
healthy interior three-axis read band; the resolved surface-residualization
control left those early peaks unchanged. Qwen3.5-4B is the one family whose
mid-band actuation is ALREADY causally established on held-out at an interior
layer (hs20, depth 0.625), via a J-lens-guided write site. So this cell asks
the profile-vs-write-site dissociation question in its sharpest form yet:
does the representation-variance eff_dim_frac profile peak early-exterior (a
5th time) while both the read panel AND the independently established write
site sit interior? A 5th early-exterior peak here would be the cleanest
demonstration in the program that eff_dim_frac peak location is not the
actuation site. (Whether to register that 5th-early-exterior call as the
orchestrator's scoreboard prediction is flagged for the lead below -- see
"Predictions scoreboard".)

## Design

Substrate: `Qwen/Qwen3.5-4B` at pinned revision
`851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a` (raw-base, ungated, no adapter,
no 4-bit quantization), 32 decoder layers, hidden size 2560.
`n_hidden_states` for full-depth capture = 33 (hs_index 0 through 32
inclusive).

**Pin provenance**: this exact revision is pinned by the resolved
`doubt-snap-cross-family-confirmatory/model_matrix.yaml` (qwen35_4b cell,
revision line 56) and recorded again with `hidden_dim: 2560` in
`experiments/j-space-cross-family-layer-contrast/families/qwen35-4b.yaml`'s
reuse block for the same doubt-snap qwen35_4b artifacts. It is the substrate
every qwen35 steer cell in the program actually used
(`doubt-snap-cross-family-confirmatory`, `qwen35-4b-midband-doubt-snap`,
`qwen35-4b-midband-heldout`).

**Architecture verification** (config JSON only, no weights, VERIFIED
2026-07-09 in `qwen35-4b.yaml`): `config.json` `architectures ==
["Qwen3_5ForConditionalGeneration"]` (model_type `qwen3_5`, a MULTIMODAL
conditional-generation wrapper). `num_hidden_layers=32` and
`hidden_size=2560` are BOTH nested under `config.text_config` (top-level
config lacks them), reachable via `config.get_text_config()`. The
`hs_index = decoder_block_index + 1` convention is consistent with the
qwen35 steer cells (block 19 -> hs20; block 29 -> hs30).

**Substrate quirks** (transcribed verbatim from `qwen35-4b.yaml`, all
VERIFIED 2026-07-09 against config/tokenizer/chat-template JSON, no weights):

- *Hybrid linear-attention.* `text_config.layer_types` alternates
  `linear_attention` / `full_attention` (full attention every 4th layer).
  The eff_dim_frac depth sweep crosses architecturally non-uniform layers;
  the profile may show periodic structure at the every-4th full-attention
  layers. A read-time note, not a prediction change.
- *Multimodal loader (CONFIRMED CAPTURE BLOCKER via CPU smoke 2026-07-23, see
  Execution below).* `AutoModelForCausalLM` resolves `Qwen3_5Config` to
  `Qwen3_5ForCausalLM`, whose constructor FAILS with `AttributeError:
  'Qwen3_5Config' object has no attribute 'vocab_size'` (`Qwen3_5TextModel`
  reads `config.vocab_size` on the top-level multimodal config; it lives under
  `text_config`). `AutoModelForImageTextToText` constructs cleanly ->
  `Qwen3_5ForConditionalGeneration`. Since `from_pretrained` calls the same
  `cls(config)` constructor, the tuner's `AutoModelForCausalLM.from_pretrained`
  load path WILL fail; the gemma precedent does not transfer. See "Known
  limitations" and NOTEBOOK.md.
- *enable_thinking.* The chat template carries a `{%- if enable_thinking is
  defined and enable_thinking is false %}` guard injecting an empty
  `<think>\n\n</think>` block; the kwarg name/semantics match Qwen3-4B's
  lineage. The ported render's `direct enable_thinking=False` path is
  expected to succeed; `assert_no_think_scaffolding` hard-stops any leak.
- *EOS.* `<|im_end|>` (id 248046) terminates a chat turn and is already the
  tokenizer's top-level `eos_token`; `<|endoftext|>` (248044) is the base
  sequence-end. Capture-only, so EOS is not on the critical path; recorded
  for completeness.

**Row pool**: this cell reuses, verbatim and unmodified, the committed
ID-only split manifest of the resolved
`doubt-snap-cross-family-confirmatory` experiment's `qwen35_4b` cell (sha256
`2f622f5abe110349216207424bdbd919775e93f6d92f334b99f6424505f21e5c`). Per lead
adjudication (2026-07-23), following the qwen3-4b precedent, that manifest is
PROMOTED byte-identical to
`experiments/common/qwen35-4b-doubt-snap-split/split_manifest.json` (with a
`PROVENANCE.md`), and this cell consumes the promoted copy. Per `SKILL.md`
step 2 ("Reuse an existing experiment's committed split manifest verbatim
whenever one exists for this substrate"), this is a further consumer of the
same manifest already reused by `qwen35-4b-midband-doubt-snap` and
`qwen35-4b-midband-heldout` -- **not** a fresh-mining cell.

This pool is CLEANER than qwen3-4b's: that cell's promoted manifest carried
row-level IDs for only two of three roles and needed a
`derive_unknown_refused_manifest.py` step. THIS manifest already carries
row-level IDs for ALL THREE family-atlas roles:

| Role | Total | fit | held_out / fit_only |
|---|---|---|---|
| confab | 2219 | 887 | 1332 held_out |
| known_correct_answered | 600 | 240 | 360 held_out |
| unknown_refused | 181 | -- | 181 fit_only |

Held-out counts clear this program's standard AG0 floors amply: confab
held-out 1332 (floor 150), known-correct held-out 360 (floor 250).

**Refused-pole power (ADJUDICATED by lead 2026-07-23: option (a) accepted).**
See "Known limitations" below -- this is a recorded known limitation of the
cell, not an open decision. `unknown_refused` is only 181 fit_only rows;
`split_refused_pool()` (seed 20260707) subdivides it into ~90 `refused_fit` /
~91 `refused_eval`, setting the held-out power for the refused pole of all
three axes. The lead accepted the lower power: no new AG0 floor, no fresh
mining (reuse-verbatim wins); AG2 reports the refused-pole numbers with wider
CIs and the numbers ARE the atlas.

**Row-key -> text materialization (capture-launch precondition, still
gated).** The manifest is ID-only. `capture_family_atlas_cell.py`'s
`--row-pool` needs `role`+`split`+`question` per row across all three roles.
The source question text lives in the doubt-snap qwen35_4b private pool
(`split_rows_private.jsonl`, sha256
`42659f4019d0cbe0178bddd6a7e6323299555092ecd8da4c9ac5d58e42b15a58`) on the
read-only Modal volume `eh-doubt-snap-cross-family` (prefix
`doubt-snap-cross-family-r1/qwen35_4b/analysis`), never committed. Writing
and running a local `materialize_rows.py` (mirroring qwen3-4b's own,
local/gitignored) is capture-launch preparation, gated the same way capture
is (sign + launch approval), NOT part of this scaffold.

**Shared-input promotion (RESOLVED by lead 2026-07-23).** Following the
qwen3-4b precedent, the doubt-snap qwen35_4b manifest is promoted to
`experiments/common/qwen35-4b-doubt-snap-split/` (`split_manifest.json`
byte-identical, plus `PROVENANCE.md`), and this cell consumes the promoted
copy (`experiment.yaml` `inputs`, `cell.yaml` `source`). The promotion is
drafted uncommitted for the lead's evidence commit.

Signal, per cell (identical procedure to the prior four family-atlas cells,
once the materialization precondition above is met):

1. Full-depth anchor capture: hidden states at every hidden-state index (0
   through 32) at the final-prompt-token anchor, for every row in the pool.
   FIT/held-out labels carried through unchanged.
2. Workspace profile: per-layer `eff_dim_frac` (participation-ratio formula
   applied to the FIT-row anchor hidden-state matrix at each layer).
   Representation-variance PR, comparable across this atlas's own cells only;
   NOT numerically comparable to the JVP-based effective-dimension profile
   the j-space instruments (e.g. `qwen35-4b-midband-doubt-snap` Stage A) ran.
3. Per-layer read panel with bootstrap CIs, for doubt / caution /
   raw_refusal, plus the standard random-direction control. `unknown_refused`
   is `fit_only`; the deterministic `refused_fit`/`refused_eval` subdivision
   (seed 20260707) applies unchanged.
4. Committed outputs (aggregates and fitted metadata only, never row text):
   per-layer profile table, per-layer read AUROCs with CIs, the
   random-direction control, direction-fit manifests with seeds and sha256s,
   and the atlas summary JSON.

**Execution**: local RTX 3090 (matching where this substrate's own prior
qwen35 work ran locally), inside the pinned mechinterp-runner container image
per the `gemma-4-e4b-family-atlas` / `qwen3-4b-family-atlas` precedent (the
directive's intent is environment pinning for local-GPU evidence, not a
carve-out for bespoke scripts). **Loader (RESOLVED by the tuner fix, lead
relay 2026-07-23).** `capture_family_atlas_cell.py` shells to synaptic-tuner
`batch-capture`, whose `hf_batched` engine loads the model. This checkpoint's
top-level `Qwen3_5Config` nests the LM hyperparams under `text_config`, so
`AutoModelForCausalLM` resolves it to the text-only `Qwen3_5ForCausalLM`. My
CPU-only meta-device smoke (transformers 5.5.0, torch 2.9.0, no CUDA, no weight
download) showed `from_config` raises `AttributeError: 'Qwen3_5Config' object
has no attribute 'vocab_size'` and `AutoModelForImageTextToText` constructs
cleanly -> `Qwen3_5ForConditionalGeneration`; that flagged the incompatibility
pre-sign. The tuner-fix agent's deeper analysis found the WORSE real
`from_pretrained` failure mode: it would NOT crash, it would SILENTLY load a
flat text-only class with garbage weights (all keys missing/unexpected, no
exception) -- the same silent-substitution bug class as Stage-S run 1. The fix
(tuner commit `e0e02a3`, branch `feature/multimodal-loader-fallback`, includes
`f6f1229`) adds a GENERIC composite-config pre-check (`get_text_config()`
identity) that routes such configs to `AutoModelForImageTextToText` BEFORE
`AutoModelForCausalLM` can run, and logs which loader path fired. **Capture
requirements this imposes on the cell**: (1) the canonical checkout's
`synaptic-tuner` submodule must be at `e0e02a3` at capture launch (recorded in
`cell.yaml` `capture.tuner_submodule_pin`; this scaffold does not check out or
modify the submodule); (2) the post-capture validity check asserts the capture
log shows the `AutoModelForImageTextToText` loader path fired (`gates.yaml` AG0
`loader_path_is_image_text_to_text`) -- a `CausalLM` path means the fix did not
engage and the capture is garbage-weight-contaminated and must be discarded.
Full smoke transcript and the layer-indexing closure in NOTEBOOK.md.

Instrument files pinned at sign: `cell.yaml`, `gates.yaml`,
`render_qwen35_atlas.py` (this experiment's own capture render module, ported
from `experiments/doubt-snap-cross-family-confirmatory/render.py`, the source
POOL's own render surface -- ported from that experiment, NOT from
`render_qwen3_atlas.py`, so this atlas's anchor position reproduces the
source pool's own render exactly), and local, byte-identical copies of the
shared `capture_family_atlas_cell.py` (sha256
`574c5a71f16486ed8c20d0456c6494b79c8a78244d5b71a3de132fb52845199c`) and
`profile_and_read_family_atlas_panel.py` (sha256
`27cd945c83df20416658a5370544ea99f1422f5717f3e67cffca82d418003ed5`),
sha256-verified against their `.skills/family-atlas/scripts/` canonical
originals. (The capture script is the current canonical version, which reads
the capture engine from `cell.yaml`; qwen3-4b pinned an earlier byte of the
same script before that generalization. This cell uses `engine: hf-batched`,
the default path, unchanged in behavior.)

## Known limitations

- **Low refused-pole read power (adjudicated, accepted).** This cell's
  `unknown_refused` pole is only 181 fit_only rows -- much smaller than
  qwen3-4b's 1029 or the jspace cells' larger pools -- because the source
  doubt-snap pool (a confab-vs-known clean-tighten instrument) needed refused
  rows only as minor scaffold. `split_refused_pool()` (seed 20260707) divides
  them into ~90 `refused_fit` / ~91 `refused_eval`, and that ~91-row eval set
  is the refused pole for ALL THREE read axes (doubt's negative pole,
  caution's positive pole, raw_refusal's positive pole). Every read-panel
  AUROC that involves the refused class therefore carries WIDER bootstrap CIs
  than the corresponding numbers in the other four family atlases; the
  confab-vs-known contrast (doubt's answered side, and the answered pole of
  raw_refusal) is unaffected (confab held-out 1332, known held-out 360). The
  lead accepted this (2026-07-23): reuse-verbatim wins over re-grading fresh
  refused rows on this checkpoint, and no refused-pole floor is added to AG0.
  Read the refused-involving AUROCs as lower-power estimates and lean on the
  CI widths when comparing this family's read band to the others'.
- **Multimodal loader (RESOLVED, was an infrastructure blocker).** See
  "Design" -> "Execution": the tuner now routes this nested-config multimodal
  checkpoint to `AutoModelForImageTextToText` (tuner commit `e0e02a3`),
  preventing the silent garbage-weight substitution `AutoModelForCausalLM`
  would have produced. Two capture requirements remain (submodule pinned to
  `e0e02a3`; AG0 asserts the ImageTextToText loader path fired) -- these are
  launch/gate conditions, not open limitations of the atlas design.

## Prediction

Qwen3.5-4B (raw base, `Qwen/Qwen3.5-4B` at the pinned revision) shows an
interior workspace band: a contiguous set of layers strictly inside
(20%, 85%) depth where eff_dim_frac peaks AND all three read axes (the
known-unknown (KU, answerability) axis, caution, and raw refusal -- artifact
keys `doubt`/`caution`/`raw_refusal`) hold held-out AUROC >= 0.80, with the
band's peak layer differing from this substrate's established mid-band write
site hs20 (hs_index 20).

This is the program-standard atlas prediction, kept identical to the four
prior cells deliberately: it has failed 4 of 4 times on the profile limb,
and this cell is the pre-registered fifth-family test of whether that failure
is the pattern or a coincidence. The separately recorded predictor calls
(below) state what each party actually expects; this section states the
registered hypothesis the falsifier is armed against, unchanged from the
program default so the five cells stay directly comparable.

## Falsifier

No interior eff_dim_frac peak exists (the profile is monotone to the last
layer, OR the profile peaks in the outer 20% of depth on either end --
early-exterior, as `jspace-family-atlas` found for llama and mistral,
`gemma-4-e4b-family-atlas` found for gemma, and `qwen3-4b-family-atlas` found
for qwen3-4b, or late-exterior), OR no layer inside (20%, 85%) depth reaches
held-out AUROC >= 0.80 on all three axes simultaneously.

## Gates

See `gates.yaml`: AG0 (capture/direction integrity), AG1 (profile), AG2
(read panel). Transcribed verbatim from the program-standard thresholds
(identical to `jspace-family-atlas`, `gemma-4-e4b-family-atlas`, and
`qwen3-4b-family-atlas`); no AG0a pool-mining gate is added, because this
cell reuses an already-vetted pool. The two data preconditions that block
launch instead (question-text materialization; the multimodal loader smoke)
are recorded in "Design" above, and the refused-pole power decision (whether
to add a refused-pole floor to AG0) is left for the lead -- see `gates.yaml`
header and "Design" -> "Row pool".

## Predictions scoreboard

The orchestrator row is the scaffold's PROPOSED call, retained verbatim for
the lead's ratification at sign. The user row records the user's own pre-sign
calls (relayed by the lead 2026-07-23). Both are independent calls on the
same prediction; neither is registered until sign. Note both parties call the
SAME direction here (unlike the qwen3-4b head-to-head, where the orchestrator
and user split on the eff_dim_frac peak location).

| Predictor | Call |
|-----------|------|
| orchestrator | (RATIFIED by lead 2026-07-24, adopted verbatim from the scaffold's proposal) Falsifier fires on the profile limb via an EARLY-EXTERIOR eff_dim_frac peak (outer 20% of depth), making qwen3.5-4b the fifth family in the decoupling pattern. Read panel healthy: a wide contiguous mid-band holds all three axes >= 0.80 held-out, including layers strictly inside (20%, 85%). Family-specific sub-call: the established interior WRITE site hs20 (depth 0.625) sits inside the readable band but NOT at the eff_dim_frac peak -- the cleanest profile-vs-write-site dissociation in the program. |
| user | (recorded pre-sign 2026-07-23) EARLY-EXTERIOR eff_dim_frac peak PRESENT in qwen3.5-4b -- the decoupling pattern holds 5 of 5. Same direction as the orchestrator's call, reached independently. Sub-call (hs20 relation): the three-axis read-panel band DISSOCIATES from the hs20 doubt-snap write site -- the read band is not centered on / does not single out hs20 -- mirroring the read != write dissociation qwen3-4b showed (its epistemic read axes peaked interior, distinct from the write/J-lens sites). |

## Outcome

**RESOLVED 2026-07-24 (lead adjudication).** Verdict: **profile limb
INCONCLUSIVE (instrument-resolution-limited); early-exterior decoupling
pattern BROKEN at family 5; read panel healthy; read != write dissociation
supported.**

Gate results:

- **AG0 PASS** (all checks): capture coverage 3000/3000 (1.0);
  loader path = AutoModelForImageTextToText, verified by construction
  (the tuner's own `_is_composite_text_config` returns True for the pinned
  Qwen3.5-4B config, forcing the ImageTextToText branch; zero
  missing/unexpected-key warnings; captured tensors healthy — norms
  monotone L0=0.79 -> L32=157.6, rows distinct). NOTE: the gate's
  literal "capture log MUST show the loader path" is unsatisfiable as
  written — the tuner logs the path at logging.INFO, which is not emitted
  under default logging; the by-construction check above is the durable
  equivalent and is adopted as satisfying the gate's intent. Flagged for a
  family-atlas skill note.
- **AG1: eff_dim_frac_every_layer PASS; profile_reproducibility FAIL.**
  Full-sample peak hs18 (depth 0.5625, interior), but the profile is
  shallow and bimodal: hs18=0.01019, hs19=0.01012, hs32=0.00999 (~2%
  spread). Under the pre-registered 20% subsample check the peak is NOT
  stable within +/-1 layer: 3/8 deterministic subsample seeds keep it at
  hs18/19, 5/8 flip to hs32 (late-exterior). Peak LOCATION is therefore
  instrument-resolution-limited (interior vs late-exterior unresolved).
  Method note: the pinned script exposes no subsample flag; the check was
  executed with the script's own registered eff_dim_frac estimator on
  deterministic 20% subsets of the 1308 fit rows (recorded in
  NOTEBOOK.md).
- **AG2 (read panel, no numeric gate):** all three axes >= 0.80 held-out
  across a wide interior band (hs7-27) strictly inside (20%, 85%) — the
  "no interior layer clears all three axes" falsifier limb does NOT fire.
  Caveat recorded: the doubt axis saturates ~1.0 but is heavily
  norm/position-confounded (random-direction control reaches 0.99 at
  hs18/hs31); caution and raw_refusal are the clean axes (controls mostly
  0.5-0.77, axis AUROCs ~0.97/0.98 around hs17-23). Refused-pole CIs are
  wide per the pre-accepted option-(a) power limitation.

Adjudication against the registered Prediction/Falsifier: the prediction
(robust interior peak + healthy band + peak != hs20) is NOT confirmed —
the peak is not robustly interior. The falsifier does NOT fire — it
requires a RESOLVED exterior peak (early or late) or an unhealthy interior
band, and the peak location is unresolved rather than resolved-exterior
while the band is healthy. Net: profile limb inconclusive,
instrument-resolution-limited (the pre-registered reproducibility check is
the instrument that failed to resolve it). What IS resolved: there is NO
early-exterior peak (hs1-6 is never a subsample peak) — the 4-of-4
early-exterior decoupling streak breaks at this family regardless of how
the hs18-vs-hs32 ambiguity would resolve.

Scoreboard adjudication (against the registered calls, no reinterpretation):

- **orchestrator: MISS on the headline** (called falsifier-fires via
  early-exterior peak, 5-of-5 pattern; no early-exterior peak exists and
  the falsifier did not fire). **HIT on the sub-call** (hs20 sits inside
  the readable band but is not the profile peak; at hs20 the
  caution/raw_refusal random controls are the panel's highest —
  read != write dissociation holds).
- **user: MISS on the headline** (same early-exterior 5-of-5 call, same
  outcome). **HIT on the sub-call** (read band dissociates from hs20).
- Both parties also called the read panel healthy — correct.

One-sentence summary (manifest `verdict:`): qwen3.5-4b atlas capture valid
(AG0 pass); eff_dim_frac profile shallow-bimodal (hs18 interior vs hs32
late-exterior) with the pre-registered reproducibility check failing to
resolve the peak — profile limb inconclusive, early-exterior pattern broken
at family 5; read panel healthy across hs7-27 with read != write
dissociation from hs20 supported.

The `docs/atlas/family-layer-map.md` row update accompanies this resolve
(same commit); the existing `qwen3.5` steer-cell row is reconciled with the
measured profile/read-panel columns.
