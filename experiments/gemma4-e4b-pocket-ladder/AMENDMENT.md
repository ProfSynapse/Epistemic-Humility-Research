# Gemma-4-E4B pocket ladder: hs25/hs26/hs27, sharing ON

Status: resolved 2026-07-31 (machine state in `experiment.yaml`); verdict:
no direction-specific actuation in the pocket, E1/hs25 failed mandatory G3
(see AMENDMENT.md "Outcome" and experiment.yaml `verdict:`). This header
was stale boilerplate reading "draft (not signed)" until 2026-08-11;
corrected to match the machine state, which was already `resolved`.

Keep this document the prose home for the experiment. The machine state lives in
`experiment.yaml` and is never duplicated here.

## Motivation and posture

Posture: **Tier-2 exploratory.** Reported separately from the locked headline
matrix and never pooled with it. This is a standalone registration, not a
reopening or extension of `gemma4-e4b-kv-seam-quarantine`: that cell's arm set
(A1-A6, D1-D4, C0, C1, P1, P2) is signed and its own ladder does not move here.
This document neither cites nor relies on any Outcome from that cell's Phase B
(still open); every number it borrows comes from that cell's AMENDMENT.md
Design/Gates sections (registered pre-run) or its NOTEBOOK.md Stage 6 Phase A
adjudication (rulings on arms that have actually run), never from Phase B.

**Why this registration exists.** The PI directed it on 2026-07-31. The
motivating question is why gemma is the only family in this program that has
never shown a direction-specific actuation result, and whether the one band of
the cross-family operating range that has never been written into on this
substrate behaves any differently from the bands already measured.

The cross-family operating range, transcribed verbatim from
`experiments/gemma4-e4b-kv-seam-quarantine/AMENDMENT.md:391-397` (site, relative
depth `rd = site_hs / num_hidden_layers`, and outcome for every site that has
ever actuated in this program):

| family | blocks | site | rd | achieved |
|---|---|---|---|---|
| mistral-7b-v0.3 | 32 | hs12 | 0.375 | usable dose |
| mistral-7b-v0.3 | 32 | hs15 | 0.469 | usable dose |
| llama-3.2-3b | 28 | hs17 | 0.607 | usable dose, held-out G1 PASS 0.7420 |
| Qwen3.5-4B | 32 | hs20 | 0.625 | promoted held-out actuation result |
| Qwen3-4B | 36 | hs23 | 0.639 | held-out 0.892 [0.839, 0.929] |

so the cross-family operating range is **rd 0.375-0.639**
(`gemma4-e4b-kv-seam-quarantine/AMENDMENT.md:399`). Gemma has 42 blocks. The
three sites registered here,

| arm | site | = output of block | rd = site_hs / 42 |
|---|---|---|---|
| E1 | hs25 | 24 | 0.595 |
| E2 | hs26 | 25 | 0.619 |
| E3 | hs27 | 26 | 0.643 |

sit at or just past the **top** of that range -- E1 and E2 fall inside it
(0.595, 0.619 against a 0.639 ceiling), and E3's 0.643 sits fractionally
**above** the 0.639 ceiling rather than at it (softened 2026-07-31, pre-sign
red-team finding H7: an earlier draft said all three "sit at the top of that
range," which overstated E3's position) -- and none of the three has ever
been written to on gemma. The quarantine cell's own AMENDMENT.md already
names this exact band and these exact sites, without registering an arm
there:

> "The upper half of the cross-family operating range - rd 0.571-0.639, which is
> where llama's G1 PASS (0.607) and Qwen3.5-4B's promoted result (0.625) both
> sit - is on gemma **entirely above the seam**, at hs25-hs27. On this
> architecture 'quarantined' and 'in the productive depth band' are largely the
> same region."
> (`gemma4-e4b-kv-seam-quarantine/AMENDMENT.md:405-411`)

That passage is descriptive, not a registration: the quarantine cell's own arm
set stops at A5/hs24 on the above-seam side and does not reach hs25-hs27. This
experiment closes that gap directly, as its own registered ladder, under its
own gates.

**What this experiment does NOT do.** It is not a test of the KV-quarantine
hypothesis and does not attempt to discriminate the quarantine account from the
crystallization-gap / linear-accessibility account or any other competing
explanation in `gemma4-e4b-kv-seam-quarantine/AMENDMENT.md` "Competing
explanations". E1/E2/E3 sit on the unmodified model, sharing ON only, on the
same descriptive footing as that cell's D1-D4 and A3/A5 arms: a positive,
G3-adjudicated result here is evidence that gemma can actuate in this band; a
negative result cannot by itself decide why.

**The confound cuts both ways, restored here (pre-sign red-team finding
W5).** The quarantine cell's own AMENDMENT.md states this plainly for
gemma's whole upper depth band, not only for a below-seam null: "The upper
half of the cross-family operating range - rd 0.571-0.639... is on gemma
entirely above the seam, at hs25-hs27. On this architecture 'quarantined'
and 'in the productive depth band' are largely the same region. That is a
confound this design cannot remove, and it cuts both ways: it is the reason
the quarantine hypothesis is worth testing at all, and it is the reason a
below-seam null from D1-D4 would NOT be clean evidence against
actuation-at-depth in gemma"
(`gemma4-e4b-kv-seam-quarantine/AMENDMENT.md:405-414`). The same confound
binds a POSITIVE result here just as much as a negative one: because rd and
KV-quarantine status are perfectly correlated across E1/E2/E3 (every site in
this pocket is both "the productive depth band by cross-family analogy" and
"fully quarantined"), a G3-adjudicated PASS at any of them cannot by itself
distinguish "gemma actuates in this band because it is the right depth,
quarantine does not matter" from "gemma actuates despite quarantine, the
quarantine hypothesis is wrong at this site" from "the effect and the
quarantine region simply coincide here for an unrelated reason." A positive
result is evidence that gemma CAN actuate in this band; it is not, by
itself, evidence about why, and must not be reported or interpreted as
resolving the quarantine hypothesis in either direction.

## Design

### Substrate and instrument

Same checkpoint, substrate, and instrument as `gemma4-e4b-kv-seam-quarantine`:
`google/gemma-4-E4B-it`, `bf16`, no adapter, no quantization, pinned revision
`fee6332c1abaafb77f6f9624236c63aa2f1d0187`. Injection method, direction-fit
method, ratio ladder, usability rule, generation contract, and graders are that
cell's, copied into this experiment directory (`build_directions.py`,
`gate_fit.py`, `calibrate_dose.py`, `pipeline.py`, `run_contrast.py`,
`kv_seam_patch.py`, `kv_seam_preflight.py`, `model_lib.py`, `gen_lib.py`,
`grader.py`, `scorers.py`, `backends.py`, `amendment_ah_stage0_extract.py`,
`placebo_direction.py`, `g2_companion.py`, `family_config.py`,
`families/gemma4-e4b.yaml`), plus one module that has no original to copy
from, `pocket_rollup.py` (new, see "Instrument deltas" below and "Dose
calibration"). Every module in this list is enumerated, drifted or
identical, in "Instrument deltas from the quarantine cell" immediately
below (pre-sign red-team findings H2/H3: `family_config.py` was drifted and
omitted from this sentence in an earlier draft).

**Instrument deltas from the quarantine cell, complete list (re-diffed
2026-07-31 against the quarantine cell's originals, file by file; 13 of 17
Python modules are byte-identical).** Confirmed by direct `diff` against
`gemma4-e4b-kv-seam-quarantine/`, not asserted from memory:

- **IDENTICAL (13 modules, no drift):** `kv_seam_patch.py`, `kv_seam_preflight.py`,
  `model_lib.py`, `gen_lib.py`, `grader.py`, `scorers.py`, `backends.py`,
  `amendment_ah_stage0_extract.py`, `build_directions.py`, `gate_fit.py`,
  `calibrate_dose.py`, `pipeline.py`, `g2_companion.py`.
- **`run_contrast.py`, drifted (three deltas, one file, not "two copied
  files"):**
  1. Two provenance-metadata call sites (`:454` and `:548` in the source
     cell) hardcoded `"experiment": "gemma4-e4b-kv-seam-quarantine"` in the
     `run_config` dict each writes into its own run log. Both corrected to
     `"gemma4-e4b-pocket-ladder"` so any future run's provenance names the
     correct owning experiment.
  2. The source cell's `PLACEBO_REGISTERED_SITE_SET = "seam_pair"` module
     constant hardcoded the one site set `--arm-kind placebo`/`undosed`
     would accept, which would refuse every C0/P1/P2/P3 call under this
     cell's `--site-set pocket` and make G3 unexecutable outright. Replaced
     with a `registered_control_site_sets()` function that reads the
     registered set from THIS experiment's own `cell.yaml
     registered_control_site_sets` key at call time, generalizing the check
     (still refuses any unlisted site set) rather than removing it. Three
     call sites updated: `run_placebo`'s guard, the CLI's `--arm-kind`
     guard, and the `--arm-kind` help text.
  3. One stale example string in an error message (`--site-set seam_pair`
     in the "run the true arm first" hint) updated to `--site-set pocket`.
- **`placebo_direction.py`, drifted (two deltas, both W4 remediation, both
  closed 2026-07-31):**
  1. `draw_seed`'s formula changed from `seed_base + hidden_dim + hs_index +
     k_index` to `seed_base + hidden_dim + 1000*hs_index + k_index`. The
     original formula collides across adjacent sites: verified directly
     (K=5, hidden_dim=2560), hs25/hs26/hs27's 15 draws span only 7 distinct
     seeds, and hs25's draws overlap the quarantine cell's own hs24/P2
     draws at 4 of 5 values.
  2. `redraw_seed`'s formula changed from `seed_base + hidden_dim +
     hs_index + k + attempt` to `seed_base + hidden_dim + 1000*hs_index + k
     + attempt`, the same widening applied to the same defect: verified,
     hs25 and hs26's redraw-attempt pools overlapped at 8 of 9 checked
     values under the original formula. The `+ k` offset itself is
     unchanged and intentionally kept -- it is the parent cell's own
     accepted intra-site structure (separating a site's redraw seeds from
     its own K primary-draw seeds), not part of the cross-site collision
     defect being fixed.

  Re-verified numerically after both fixes, exhaustively over the full
  registered draw and redraw space (`K=5` primary draws plus all
  `MAX_REDRAWS=300` redraw attempts per site, `hidden_dim=2560`,
  `SEED_BASE=20260725`): **zero collisions** among the 915 seed values
  spanning E1/E2/E3 (hs25/26/27, 305 slots each), and **zero collisions**
  between that pocket-cell pool and the quarantine cell's own unchanged
  hs24/P2 pool (its `draw_seed`/`redraw_seed` still use the original,
  un-widened formula, since that file was not touched). For contrast, the
  ORIGINAL (pre-fix) formula applied to just hs24-hs27's draw-plus-9-redraw-
  attempts pools (56 seed-slots total, the four sites this program's
  quarantined-region arms occupy) produced only 18 distinct values -- 38
  collisions among 56 slots.
- **`family_config.py`, drifted (additive registration, not a behavior
  change to any existing site set):** added `pocket_hs_indices()` and a
  `SITE_SETS["pocket"]` entry, mirroring the existing `shallow_ladder_hs_
  indices`/`seam_pair_hs_indices` pattern. Without this, no stage
  (`build_directions.py`/`gate_fit.py`/`calibrate_dose.py`/`run_contrast.py`,
  all of which select sites through `--site-set`) could address hs25/26/27
  at all -- the same failure mode the quarantine cell itself hit before its
  own `seam_pair` set existed (that cell's own `AMENDMENT.md` "Open
  questions at sign" records it). This edits ONLY this cell's own unsigned
  copy of `family_config.py`; the quarantine cell's signed copy is
  untouched.
- **`families/gemma4-e4b.yaml`, drifted (additive registration):** added a
  `pocket_hs: [25, 26, 27]` key under `band_selection`, read by the new
  `pocket_hs_indices()` above. Same "this cell's own unsigned copy only"
  scope note as `family_config.py`.
- **`rollup.py` DROPPED entirely, replaced by a new `pocket_rollup.py`**
  (not a diff against an original -- see "Dose calibration" below and B4 in
  the remediation record). `rollup.py`'s `ARM_REGISTRY` hardcodes
  `A1`-`A6`/`D1`-`D4` and its `build_rollup()` unconditionally loads a
  `g0_alin_discrimination_measurement` artifact and a
  `c1_precondition_summary.json`, both from stages this cell does not have
  (no A_lin site-selection step, no OFF arms, no C1). Carrying it into this
  cell's pin surface would ship dead code for artifacts that can never
  exist here.
- **`cell.yaml`** (config, not a Python module, so outside the module diff
  above but part of the same delta set): added `registered_control_site_sets:
  [pocket]`, which is what `run_contrast.py`'s new
  `registered_control_site_sets()` reads.

**Staged inputs (registered contract; not executed at draft -- see the
"Staged inputs" subsection below, under Design, for the full
path/hash/verification record).** `build_directions.py`,
`calibrate_dose.py`, and `run_contrast.py` read four files this experiment
directory does not itself contain: the FIT anchor extraction safetensors,
its manifest, the FIT/HELD-OUT split manifest, and the row-text pool
`eval_rows.jsonl`. These must be staged (symlinked or copied) from their
source location before any of those three scripts can run; `experiment.yaml
instrument.staging` records source path, destination path, and sha256 for
each.

**Extraction provenance, corrected 2026-07-31 (pre-sign red-team finding
B2; the earlier draft named the wrong artifact).** E1/E2/E3 do NOT read
from `experiments/common/artifacts/jspace-cross-family-gemma4-e4b/`. That
directory holds no activation cache at all -- only the corrupt-derived
mid-band artifacts (`build_manifest_layers.json`, `gate_fit_layers.json`,
`dose_calibration_summary.json`, `layer_profile.json`, and the
`layers/hs{34,38,42}/` direction files), fit on the withdrawn
`use_cache=False` extraction. Its own `PROVENANCE.md` "A caution specific
to these files" states plainly that "hs25 onward decay (cos 0.732 at hs25
to 0.075 at hs42)" under that corrupted run -- hs25 is arm E1's own site,
so treating that directory as an activation source for this cell would
have staged exactly the corrupted data this cell exists to avoid.

The correct artifact is
`gemma4-e4b-kv-seam-quarantine/analysis/gemma4-e4b/anchor_extract.safetensors`
plus its `anchor_extract_manifest.json` (both gitignored, local-only,
341.7 MB for the safetensors) and
`gemma4-e4b-kv-seam-quarantine/analysis-committed/gemma4-e4b/split_manifest.json`
(git-tracked). Verified directly from the manifest, not assumed:
`forward_use_cache: true`, `layer_labels` covering `hs0`-`hs42` (43
entries), `n_rows_extracted: 806`, `complete: true`. This is the corrected,
clean `use_cache=True` extraction, corroborated by
`gemma4-e4b-kv-seam-quarantine/NOTEBOOK.md:682-684`: "The manifest records
`forward_use_cache: True`, so these are the *corrected* clean activations,
not the withdrawn `use_cache=False` ones that made blocks >= hs25
meaningless." **No re-extraction is required** -- this cache already covers
hs0-hs42 over all 806 rows, which is what licenses E1/E2/E3 fitting their
directions and gates from it without a new GPU extraction pass, exactly as
the quarantine cell's own D1-D4 did (`gemma4-e4b-kv-seam-quarantine/AMENDMENT.md:431-435`).

### Staged inputs (pre-sign red-team finding B3)

This experiment directory does not itself contain an activation cache or a
row-text pool. It is registered against the correct artifacts named above,
but they live in the sibling `gemma4-e4b-kv-seam-quarantine` directory and
must be staged (symlinked or copied) into this experiment's own `analysis/`
/ `analysis-committed/` tree before `build_directions.py`, `calibrate_dose.py`,
or `run_contrast.py` can read them. **Not executed by the drafting agent** --
no GPU/docker work is authorized at draft; this section registers the
contract, not a completed action. The full machine-readable record is
`experiment.yaml instrument.staging`; the same four files, transcribed here:

| artifact | source | sha256 | read by |
|---|---|---|---|
| `anchor_extract.safetensors` | `gemma4-e4b-kv-seam-quarantine/analysis/gemma4-e4b/anchor_extract.safetensors` | `b7197418476208a3657f98026932fbf5e2c5aa4306a82844040ab50d99fbe7bf` | `build_directions.py:159-161`, `calibrate_dose.py:74-75` |
| `anchor_extract_manifest.json` | `gemma4-e4b-kv-seam-quarantine/analysis/gemma4-e4b/anchor_extract_manifest.json` | `060c3f3b225fc4bca59a5b6bb91a6c91bf13d4798f14a4e3a84bd8dd09158b01` | `build_directions.py:157-158` |
| `split_manifest.json` | `gemma4-e4b-kv-seam-quarantine/analysis-committed/gemma4-e4b/split_manifest.json` | `8d2281179ab865bea8fd7918c0ee14b33db7113c4ed375ff0740c36cee2f1d87` | `build_directions.py:159` |
| `eval_rows.jsonl` | `gemma4-e4b-kv-seam-quarantine/analysis/gemma4-e4b/eval_rows.jsonl` | `7a2784bd883ed622fa138956e722db0353c8a3f96ed7f914a144908d01ddecc7` | `pipeline.py:104` (`load_rows`, called by `run_contrast.py`'s `selected_rows`) |

`anchor_extract.safetensors` is 341.7 MB, gitignored, never committed to the
repo. `split_manifest.json` is git-tracked and byte-identical (same sha256,
independently verified) to
`experiments/common/artifacts/jspace-cross-family-gemma4-e4b/split_manifest.json`
-- it is an ID-only row manifest and was never affected by the
`use_cache=False` corruption (`PROVENANCE.md` "A caution specific to these
files"), unlike the activation cache itself, so its presence in that
directory is not a reason to source the activation cache from there too (see
"Extraction provenance" above). `eval_rows.jsonl` is 205.4 KB, gitignored,
never committed -- added 2026-07-31, closing a gap this remediation found but
had not initially covered (`run_contrast.py`'s own row population reads it
via `pipeline.load_rows`, which was outside the staging contract's first
scope of `build_directions.py:153-161` and `calibrate_dose.py:74`). It
carries question/aliases row text, so like `anchor_extract.safetensors` it
stages into this cell's own gitignored `analysis/` **only**, never
`analysis-committed/` (containment rule, `cell.yaml
surface.containment.committed_row_text: forbidden`).

**Verification step, registered before any staged file is read.** Recompute
each file's sha256 at staging time and compare against the value above;
refuse to proceed on a mismatch rather than silently reading a different
extraction than the one this cell is registered against.

### Seam geometry (transcribed, not re-derived)

Transcribed from `gemma4-e4b-kv-seam-quarantine/cell.yaml` `kv_seam:` block and
`AMENDMENT.md:137-145,214-233`, verified there against `transformers==5.5.0`
`models/gemma4/modeling_gemma4.py` and the pinned checkpoint config:

```
num_hidden_layers          = 42
num_kv_shared_layers       = 18
first_kv_shared_layer_idx  = 24        # blocks 24..41 are KV-SHARED
donor(full_attention)      = block 23
donor(sliding_attention)   = block 22
store_full_length_kv       = True at blocks 22 and 23 ONLY
site_convention            = "hs_N = output of decoder block N-1 = input to block N"
```

hs_N is the input to block N; a write there is seen by block N and everything
downstream of it. The binding donor is block 23 (the later of the two donors),
so hs_N is quarantined (neither donor block sees the write) whenever `N >= 24`
-- by the time block 24 runs, both donor blocks 22 and 23 have already executed
and stored their KV. E1 (hs25), E2 (hs26), and E3 (hs27) are all `N >= 24`, so
all three are quarantined by the same construction that classifies
hs34/hs38/hs40/hs42 as quarantined in the parent's seam table
(`gemma4-e4b-kv-seam-quarantine/AMENDMENT.md:223-228`). **Corrected 2026-07-31
(pre-sign red-team finding W1):** an earlier draft of this criterion stated
"hs_N is quarantined whenever `N - 1 >= 24`, i.e. `N >= 25`", which is off by
one -- it would have wrongly classified hs24 itself as donor-reachable. The
arm classifications in this document were unaffected (E1/E2/E3 all satisfy
both the old and the corrected criterion), but the stated criterion itself was
wrong and is fixed here and in `cell.yaml`'s `donor_reachability` comment.
This classification is **deterministic from the architecture**, not measured
per-site: the parent's G0-KV donor-reachability assertion (item 4,
`AMENDMENT.md:636-648`) verified the bit-identical-donor-keys signature at
representative quarantined sites (hs24, hs38) and representative
donor-reachable sites (hs22, hs23); it was not re-run separately for every
quarantined site the parent wrote to, and is not re-run separately here for
hs25/hs26/hs27 for the same reason. G0-KV check 1 (architecture identity,
`verify_architecture`) is inherited unchanged and still runs before any dosed
arm is scored, since it is a stop gate on the instrument itself, not on any
specific site.

**This band is entirely inside the quarantined region.** Unlike the quarantine
cell's D1-D4 (all donor-reachable) and A3 (donor-reachable), E1/E2/E3 are in the
same reachability regime as A5/hs24, A1/hs38, and every other site the parent
ever wrote to. That is expected and is the point of the registration: it is the
one part of the cross-family operating range that sits inside the quarantined
region on this architecture and has never been measured.

### Arms

| Arm | Site | KV sharing | Role |
|---|---|---|---|
| **E1** | hs25 | ON | rd 0.595. Shallowest site in the pocket. |
| **E2** | hs26 | ON | rd 0.619. |
| **E3** | hs27 | ON | rd 0.643. Deepest site in the pocket, matches Qwen3-4B's promoted rd most closely. |
| **C0** | -- | ON | No injection. Baseline confab / known-correct rates (reused convention from the quarantine cell's C0). |
| **P1** | hs25 | ON | Magnitude-matched random-direction control for E1. Conditional on E1 having a usable FIT dose. |
| **P2** | hs26 | ON | Magnitude-matched random-direction control for E2. Conditional on E2 having a usable FIT dose. |
| **P3** | hs27 | ON | Magnitude-matched random-direction control for E3. Conditional on E3 having a usable FIT dose. |

All arms run on the unmodified model, sharing ON. There are no OFF arms and no
patch-based primary contrast in this experiment: it registers a pure sharing-ON
actuation ladder, on the same footing as the quarantine cell's D1-D4, not a
mechanism-discrimination design. `execution.gpu_work_by_this_agent` is
`forbidden` at draft; nothing above authorizes a run.

### Dose calibration (two-stage, same shape as the quarantine cell's shallow ladder)

**Stage 1 -- FIT usable-dose criterion.** `calibrate_dose.py` runs the
registered ratio ladder against each arm's FIT-split confab rows and selects the
first collapse-free rung (`collapse_rate_on_dosed == 0.0`) whose FIT
`clean_tighten` rate clears the same 0.5 floor used for dose viability in the
quarantine cell's D1-D4. An arm with no such rung is dose-viability NOT-RUN,
which is neither a pass nor a fail (transcribed rule, unchanged).

**Stage 2 -- held-out G1/G2/G3 evaluation.** `run_contrast.py` runs the selected
dose over the held-out split and scores G1, G2, and (for E1/E2/E3 only, via
P1/P2/P3) G3, exactly as the quarantine cell's D1-D4/A3/A5 machinery does.

### G3 direction-specificity is MANDATORY here, not optional

This is the one place this registration's design differs from the quarantine
cell's own registered pattern, and the difference is deliberate.

In `gemma4-e4b-kv-seam-quarantine`, `g3_direction_specificity` was scoped to
"Arms with a registered placebo counterpart ONLY -- currently A3 (P1) and A5
(P2)... A1, A2, A4 and the shallow ladder D1-D4 have no placebo arm registered
and this gate does not apply to them" (`gates.yaml:411-416`). D1-D4's own
standing limitation is registered explicitly: "no D arm has a placebo
counterpart. Scope was fixed at hs22/hs24 only... Any D-arm actuation claim
therefore rests on evidence G3 exists to demand, and must be reported with that
caveat attached rather than as a clean positive" (`AMENDMENT.md:1680-1685`).

That gap is exactly what the hs24 result shows cannot be left open in the
quarantined region. From `gemma4-e4b-kv-seam-quarantine/NOTEBOOK.md:1600-1606`
(Stage 6, Ruling R4, lead adjudication, 2026-07-30):

> "A5/hs24: FAIL. lift(true) = 0.7321; max placebo lift = 0.6429 (draw k0);
> effect_ratio = 1.139 < 3.0 floor. The apparent actuation at hs24 is NOT
> direction-specific: the worst single random draw reproduced 88% of the true
> effect. Combined with hs24 carrying the highest full-mode collapse (0.0341),
> the A5 'actuation' is adjudicated as seam-region instability that clean gates
> cannot distinguish from steering, exactly the failure mode the quarantine
> account predicts for a KV-shared site."

A5/hs24 PASSED both G1 (0.7321, Wilson lower 0.6605) and G2 (0.0333, Wilson
upper 0.0621) on held-out (`NOTEBOOK.md:1573-1582`, Ruling R3) and would have
read as a clean actuation result under G1/G2 alone. Only the placebo control
showed it was not direction-specific. hs25/hs26/hs27 sit one to three blocks
further into the same quarantined region as hs24, at higher `rd`. Registering
this ladder with G1/G2 as the only gates would repeat exactly the measurement
gap the hs24 result already demonstrated is unsafe here.

**Registered rule.** Every one of E1/E2/E3 that clears BOTH G1 and G2 on
held-out MUST have an ADJUDICATED G3 result before it may be reported as
actuation. Precisely:

- G1 PASS + G2 PASS + G3 ADJUDICATED PASS (including PASS-DEGENERATE, per the
  transcribed `zero_denominator_rule`) -> reported as a direction-specific
  actuation result.
- G1 PASS + G2 PASS + G3 ADJUDICATED FAIL (`effect_ratio < 3.0`) -> reported as
  "actuates, not direction-specific" (transcribed `what_a_failure_means`,
  `gates.yaml:455-460` in the quarantine cell), exactly the hs24 disposition.
  It may NOT be cited as evidence of a specific effect and may NOT be pooled
  with any direction-specific result in this program.
- G1 PASS + G2 PASS + G3 NOT-RUN or UNADJUDICATED (no usable placebo dose,
  redraw ledger exhausted before K = 5 accepted draws, or placebo readback out
  of tolerance) -> recorded as **not actuation**, not as a caveated positive and
  not as a failed control. A missing control is never read as a control that
  failed (same principle as the quarantine cell's falsifier-rule note,
  `gates.yaml:583-585`), but it also does not license the actuation claim on its
  own -- unlike D1-D4, where the caveat was accepted because G3 was never
  registered for those arms in the first place. Here it was registered, so its
  absence blocks the claim rather than merely qualifying it.
- G1 FAIL or dose-viability NOT-RUN at an arm -> G3 does not run for that arm
  (no true-arm lift to compare against); reported as no actuation, consistent
  with the transcribed per-arm pass rule.

### Placebo construction (transcribed unchanged from the quarantine cell)

P1/P2/P3: same site, same calibrated dose, same `erase_write`/`anchor_onward`
law, and the same fired rows as their matched true arm; only the written
direction differs. Draws are fresh unit normals under registered seeds, screened
by the SC1 bar (`|cos| <= 0.015` against both `c_hat` and `u_d`,
`AMENDMENT.md:1854-1855` in the quarantine cell) with a void-and-redraw ledger.
Magnitude is matched by the `sigma = 1.0` convention and verified by the same
readback tolerance the true arms carry. **K = 5** accepted draws per site,
transcribed from the quarantine cell's closed decision
(`AMENDMENT.md:1637`, "CLOSED: K = 5, hs22 and hs24 only" there; K = 5 is the
value transcribed here, extended to all three sites in this registration since
G3 is mandatory at all three).

## Preconditions

**G0-KV, inherited (architecture identity only).** `verify_architecture(model)`
must pass before any dosed arm is scored: 42 hidden layers, 18 KV-shared,
`first_kv_shared_layer_idx == 24`, donors `{full: 23, sliding: 22}`, **and the
set of blocks reporting `is_kv_shared_layer == True` is exactly `{24..41}`**
(restored 2026-07-31, pre-sign red-team finding H4; an earlier draft of this
item dropped the `is_kv_shared_layer` clause). Any mismatch voids the
registered site indices and the experiment stops. Fail-closed, transcribed
from `gemma4-e4b-kv-seam-quarantine/AMENDMENT.md:588-592` item 1. The OFF-
condition checks in that cell's G0-KV (items 2 and 3: projection-execution
assertion under OFF, cache integrity under OFF) do not apply here -- this
experiment has no OFF arms and never builds a sharing-OFF forward pass.

**Item 4 (donor-reachability assertion), reworded as a pre-run registration,
not a carried-over executed result (pre-sign red-team finding H5).** In the
quarantine cell, item 4 is an actually-executed check: four forward passes
with a fixed injected delta at hs22/hs23/hs24/hs38, comparing captured donor
keys against a no-injection run (`AMENDMENT.md:636-648` there). That
four-forward-pass measurement is **not** re-run here for hs25/hs26/hs27
specifically, and this document does not claim it was. What IS carried over
is the deterministic architectural relationship those four measurements
established the premise for -- that a write at `hs_N` reaches a donor block
iff the donor's index is `>= N` (see "Seam geometry" above, corrected for
finding W1) -- registered here, before any run, as the basis for classifying
E1/E2/E3 as quarantined. If G0-KV item 1 above ever fails for this
checkpoint revision, that architectural relationship is void along with it,
and neither the "Seam geometry" classification nor any arm here may be
scored.

## Prediction

None of E1/E2/E3 will produce a direction-specific actuation result. Two
sub-cases, both counted as the prediction being MET:

(a) None of E1/E2/E3 finds a usable FIT dose, or an arm finds one but fails G1
on held-out -- reproducing the parent's above-seam pattern one to three blocks
past hs24; or

(b) An arm clears G1 and G2 on held-out, but its ADJUDICATED G3 result is FAIL
(`effect_ratio < 3.0`) -- reproducing the hs24 signature (gate clearance without
direction specificity) rather than establishing a new effect.

**Basis (the honest prior, stated before any GPU work).** The quarantine cell's
own measured shallow ladder falls monotonically toward the seam: D1/hs15 0.7857,
D2/hs18 0.4464, D3/hs20 0.4048 (`NOTEBOOK.md:1616-1621`, Ruling R6), with D4/hs23
finding no usable collapse-free dose at all (Ruling R7). **That D1-D4 falloff is
a per-site-dose PROFILE, not a controlled contrast** (`NOTEBOOK.md:1621`, and
pre-sign red-team findings H6/H8): each site's dose was independently calibrated
and the three points are read as a trend across sites, not as arms of one
shared-dose comparison. The falloff is cited here as descriptive support for the
prior, not as a statistically controlled trend line, and this Prediction should
not be read as implying otherwise. The one site inside the quarantined region
that has actually been measured, A5/hs24, cleared G1/G2 but failed G3 outright,
at an effect ratio of 1.139 against a floor of 3.0 -- the worst random draw
reproduced 88% of the fitted direction's effect (`NOTEBOOK.md:1600-1606`).
E1/E2/E3 sit deeper into the same quarantined region than hs24. The drafter's
prior is therefore that this pocket sits below the gate that actually
discriminates a specific effect, even in the branches where G1/G2 happen to
clear.

**This prediction is the drafter's call only.** The orchestrator and user calls
are pre-stated placeholders below and MUST be entered before this amendment is
signed; see "Predictions scoreboard".

## Falsifier

An ADJUDICATED G3 result (K = 5 accepted draws clearing SC1, placebo readback in
tolerance) with `effect_ratio >= 3.0` -- or the PASS-DEGENERATE disposition under
the transcribed `zero_denominator_rule` -- at ANY of E1/E2/E3, **jointly with
that same arm clearing both G1 and G2 on held-out**, falsifies the prediction.
That result would be a direction-specific actuation finding at a site the seam
geometry classifies as fully quarantined -- gemma actuating specifically inside
the region the KV-quarantine hypothesis (`gemma4-e4b-kv-seam-quarantine`,
Motivation) predicts should be inert to a narrowed causal channel.

**PASS-DEGENERATE reporting restriction (pre-sign red-team finding W2).** The
transcribed `zero_denominator_rule` (`gates.yaml:433-439` in the quarantine
cell) fires only when `max_k |lift(placebo_k)| == 0.000` exactly -- every one
of the K=5 accepted placebo draws produced literally zero lift, which is a
degenerate denominator, not evidence of a large or well-separated effect. A
PASS-DEGENERATE falsifying result MUST be reported WITH the degenerate label
attached and the raw per-draw placebo rates alongside it, and MUST NOT be
cited, summarized, or pooled elsewhere in this program as a flat
"direction-specific actuation" or as a large effect ratio. This restriction
applies everywhere PASS-DEGENERATE is mentioned in this document (Design "G3
direction-specificity is MANDATORY here", this Falsifier section, and
Outcome), not only here.

**Multiplicity note (pre-sign red-team finding W3).** The falsifier as stated
fires on any one of three arms (E1/E2/E3) that share one instrument, one
extraction, one checkpoint revision, and one set of registered gates -- they
are correlated draws from the same instrument, not three independent trials.
A single-arm triple PASS (one of E1/E2/E3 falsifying while the other two do
not) is therefore registered here as **exploratory evidence**, subject to this
program's standing promotion rule (a confirmatory replication on fresh seeds,
a larger model, or a held-out site, registered before running it, is required
before any claim), and is **not** to be treated or reported as a standalone
confirmatory result on its own.

**Subordinate dispositions, pre-stated:**

- If none of E1/E2/E3 finds a usable FIT dose, this is **NULL-RESULT**
  (dose-viability), consistent with instrument-resolution limits already
  observed one site upstream (D4/hs23 NOT-RUN in the quarantine cell). The
  ladder is registered and does not move.
- If an arm clears G1/G2 but its G3 resolves NOT-RUN or UNADJUDICATED, that arm
  is reported as an unresolved gate-clearance -- neither actuation nor a failed
  control -- per "G3 direction-specificity is MANDATORY here" above. It does not
  by itself falsify or confirm the prediction; if EVERY arm that clears G1/G2
  ends up in this bucket, the experiment resolves **INCONCLUSIVE** on the
  question G3 exists to answer, and that must be stated plainly rather than
  read either way.
- A failing G3 (`effect_ratio < 3.0`, adjudicated) at an arm that cleared
  G1/G2 does NOT falsify the prediction -- it is sub-case (b) of the prediction
  itself, the hs24 pattern repeating.

## Gates

**G1 and G2 are transcribed verbatim from
`gemma4-e4b-kv-seam-quarantine/AMENDMENT.md` "Gates" (which itself transcribes
`j-space-cross-family-layer-contrast/gates.yaml`, adjudicated lead+user
2026-07-23). They are NOT re-derived here.** Applied per arm, on that arm's
held-out split.

- **G1 (PRIMARY -- actuation floor).** Held-out confab `clean_tighten` rate
  **>= 0.50** AND its Wilson 95% lower CI **> 0.40**.
- **G2 (PRIMARY -- selectivity cap).** Held-out known-correct
  `not_well_formed_correct` cost **<= 0.05** AND its Wilson 95% upper CI
  **< 0.10**.
- **Per-arm pass rule.** An arm PASSES iff G1 AND G2 both pass on held-out at its
  selected dose. An arm with no usable FIT dose is NOT-RUN.
- `alpha = 0.05`, seed `20260709` (transcribed).

**G2 diagnosticity, inherited caveat.** The quarantine cell computed the
Wilson-95%-upper floor for the registered `< 0.10` cap at **N = 35** dosed
known-correct rows (`AMENDMENT.md:1040-1045`); every arm it ran sat below that
floor (2-22 dosed rows), making the fired-only G2 companion NOT-ADJUDICABLE
everywhere it measured. The floor is a property of the cap and sample size, not
of the site, so it transfers unchanged; the expectation here, non-gating, is the
same NOT-ADJUDICABLE disposition on the fired-only companion, reported alongside
the gating G2 number exactly as that cell's G2 section registers (three numbers
always reported together: G2-as-transcribed, fired-only companion with its own
N, and the undosed floor).

**G3 (`g3_direction_specificity`), transcribed arithmetic, MANDATORY scope
(see Design).** From `gemma4-e4b-kv-seam-quarantine/gates.yaml:411-471`:

- `primitive`: `effect_ratio_over_matched_placebo`.
- `definition`: `lift(arm)` = held-out confab `clean_tighten` rate at the arm's
  selected dose MINUS the same rate on the same held-out confab rows with no
  injection. `effect_ratio = lift(true) / max` over the K accepted placebo draws
  of `|lift(placebo_k)|`.
- `pass_if`: `effect_ratio >= 3.0` (RG1 floor, transcribed from
  `rr3-corrected-placebo-replication/gates_lib.py:32`, not re-derived, not
  re-tuned for this substrate or this site band).
- Denominator is `max`, not mean, deliberately: the max is the worst case the
  random-direction family actually produced.
- `zero_denominator_rule`: if `max_k |lift(placebo_k)| == 0.000` exactly, the
  ratio is undefined, not infinite; disposition is **PASS-DEGENERATE**, reported
  as a pass with the label attached and the raw per-draw rates, never cited as a
  large effect ratio.
- `alpha = 0.05`, K = 5, SC1 bar `|cos| <= 0.015`, `sigma = 1.0` magnitude
  match, all transcribed (see "Placebo construction" above).

The RG1 criterion is used rather than the program's current-best
`gate-contribution-factorial` S1 criterion for the same reason the quarantine
cell gives: S1's denominator is a per-family census null and gemma has no
census; importing another family's random-direction sensitivity would be the
same substitution this program refuses elsewhere
(`gemma4-e4b-kv-seam-quarantine/gates.yaml:440-452`).

**Scope difference from the quarantine cell, stated plainly.** There, G3 applied
to two of nine arms (A3/A5 only) and its absence at D1-D4 was an accepted,
caveated limitation. Here, G3 applies to all three primary arms (E1/E2/E3) and
is mandatory: no arm may be reported as actuation on G1/G2 alone. See "G3
direction-specificity is MANDATORY here, not optional" in Design for the full
reasoning and the hs24 citation that motivates the difference.

## Predictions scoreboard

Registered before any GPU work. Calls do not move after results.

| Predictor | Call |
|-----------|------|
| orchestrator | Entered at sign, 2026-07-31: no direction-specific actuation at any of E1/E2/E3. Expected shape: dose-viability NOT-RUN deepening the D4/hs23 pattern, or the hs24 signature (G1/G2 clearance with G3 FAIL). A triple PASS at any site would be the most informative result on the board and is not expected. |
| user | Entered at sign, 2026-07-31 (PI, recorded from the explicit selection "No direction-specific actuation"): no site produces an adjudicated G3 PASS jointly with G1/G2. The experiment is run to close the last untested band of the cross-family operating range on this substrate, not because a positive is expected. |
| drafter | See "Prediction" above: neither E1, E2, nor E3 produces an ADJUDICATED G3 PASS jointly with G1/G2 PASS. Basis: the monotonic below-seam falloff (hs15 0.7857 -> hs20 0.4048) and the hs24 gate-clearance-without-specificity result (effect_ratio 1.139), both transcribed from `gemma4-e4b-kv-seam-quarantine/NOTEBOOK.md`. |

**This amendment MUST NOT be signed with the orchestrator and user placeholders
above still present.** (Satisfied 2026-07-31: both calls entered before
`bin/exp sign`, the user's from their explicit same-day selection.) Per the lead's explicit direction at drafting time, a
predictor call left unfilled at sign is a recorded governance defect in this
program (cited by the lead as having occurred in a Phase B registration; this
drafter did not independently verify that citation against a specific doc and
it is passed through here as the lead's stated reason, not as a
drafter-confirmed fact). Regardless of that citation's precise provenance, the
rule itself is unambiguous and binding: both calls must be entered, and lifted
to the user for the user's own call, before `bin/exp sign` runs on this
experiment.

## Outcome

Resolved 2026-07-31 (lead adjudication; all numbers re-derived from the
committed artifacts and confirmed by the pinned `pocket_rollup.py`, which is
the machine-readable record at
`analysis-committed/gemma4-e4b/pocket_rollup.json`).

**Verdict: no direction-specific actuation anywhere in the pocket. E1/hs25
cleared G1 and G2 on held-out but FAILED the mandatory G3
(effect_ratio 1.279 < 3.0), the exact hs24 signature; E2/hs26 and E3/hs27
were dose-viability NOT-RUN. All three registered predictions MET
(sub-case (b) at E1, sub-case (a) at E2/E3).**

Per-arm record:

- **E1/hs25 (dose 81.615, ratio 0.85):** G1 PASS: confab-tighten 133/168 =
  0.7917, Wilson CI [0.7241, 0.8462] vs floor 0.5 / lower 0.4. G2 PASS
  (full population): known-correct cost 9/270 = 0.0333, Wilson CI
  [0.0176, 0.0621] vs cap 0.05 / upper 0.10; fired-only companion 9/9 at
  n_fired_known 9 < 35 floor, NOT-ADJUDICABLE per the pre-registered
  non-gating disposition; undosed floor 0/261. Dose fidelity: readback mean
  81.485, frac within tol 1.0, collapse 0.0, n_fired 175/438. **G3
  ADJUDICATED FAIL:** undosed confab floor 0/168 = 0.0; placebo draws
  (confab-tighten, n=168 each) k0 0.6190, k1 0.1310, k2 0.1667, k3 0.1131,
  k4 0.0893, all collapse-free, readback adjudicated; effect_ratio =
  0.7917 / 0.6190 = **1.279** < 3.0. Claim (registered rule):
  **actuates_not_direction_specific** -- the worst single random draw
  reproduced 78% of the fitted direction's effect. May NOT be cited as a
  specific effect and may NOT be pooled with direction-specific results.
- **E2/hs26:** dose-viability NOT-RUN (Stage 1: max FIT confab-tighten 0.375
  < 0.5 usability floor; `has_usable_dose` false). P2 NOT-RUN mirroring.
- **E3/hs27:** dose-viability NOT-RUN (Stage 1: max FIT confab-tighten
  0.250; `has_usable_dose` false). P3 NOT-RUN mirroring.

Interpretation stays inside the registered fence: per the amendment's
"confound cuts both ways" clause, this result is evidence that the pocket
band shows hs24-style instability (a broad subspace in which many directions
tighten confabulation), and it does not by itself resolve the quarantine
hypothesis in either direction. The heavy-tailed placebo draw distribution
(one near-effect draw, four small) matches hs24's shape (its k0 reproduced
88%). With this cell resolved, every site of the cross-family operating
range on gemma4-e4b above the seam has now been measured: hs24 (parent,
G3 FAIL at 1.139), hs25 (G3 FAIL at 1.279), hs26/hs27 (no usable dose).

**Registered launch record.** Stage 1 FIT, the Stage 2 true arm, and the
undosed + placebo control arms all ran on the local RTX 3090 in the pinned
mechinterp-runner image (digest in `instrument.runtime_image_digest`),
2026-07-31, per the sign-time launch approval; run logs under
`analysis/runlog/`.
