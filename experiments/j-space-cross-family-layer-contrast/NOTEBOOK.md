# j-space-cross-family-layer-contrast notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

### 2026-07-24 -- mistral-7b-v03 full held-out run COMPLETE -- FINAL numbers for hs15 (the deciding site); G2 vacuity independently confirmed from my own run logs

`run_contrast.py --family mistral-7b-v03 --mode full --i-know-this-is-the-
cross-family-run` (PID 1260218) ran cleanly, ~2h26m, no errors. Monitored
continuously per standing discipline (stop on collapse spike/readback
drift): zero degenerate/collapsed rows at every check across BOTH layers'
full runs (spot-checked ~10 times through completion). No anomaly, no
intervention needed. G0 smoke (both hs12, hs15 dosed correctly per the
partial-midband fix) passed cleanly beforehand, logged separately above.

I discovered the "ROOT CAUSE... plus mistral hs12/hs15 divergence" entry
below was written (apparently by a parallel results-analyst forensics
process per the lead's stated plan) WHILE my run was still in flight -- it
records hs15 as "RUNNING... provisional" at n=492 (246/492=0.5000). My run
has now COMPLETED. Read that entry in full before writing this one, per
project discipline (not relying on any paraphrase).

**FINAL numbers (script's own output, straight, no verdict):**

- hs12: confab_tighten n=1312, successes=289, rate=0.2203, Wilson 95% CI
  [0.1987, 0.2435]. known_correct_cost_control n=382, successes=2,
  rate=0.00524, Wilson [0.00144, 0.0189].
- hs15: confab_tighten n=1312, successes=642, **rate=0.4893**, Wilson 95% CI
  **[0.4624, 0.5164]**. known_correct_cost_control n=382, successes=2,
  rate=0.00524, Wilson [0.00144, 0.0189] -- IDENTICAL successes count to
  hs12's, despite being a different layer/dose (see vacuity finding below).
- Script's own `primary` block: best_mid_layer=hs15 (highest held-out
  confab_tighten of the two, correctly selected per the registered rule).
  g1_floor_used={rate:0.5, wilson_lower_ci:0.4}, g2_cap_used={rate:0.05,
  wilson_upper_ci:0.1}. **g1_midband_actuation_floor_pass: FALSE** (point
  rate 0.4893 is 0.0107 below the 0.50 floor -- roughly 14 confab rows out
  of 1312 -- even though the Wilson lower bound 0.4624 clears the >0.40
  requirement comfortably; the script's gate is an AND of both conditions,
  and the point-estimate leg fails). **g2_midband_selectivity_cap_pass:
  TRUE.** **primary_pass: FALSE.**

**G2 vacuity independently verified, directly from my own run logs (not
just citing the parallel entry below):**
```
hs12: known_correct total=382 fired=1   fire_rate=0.0026
hs15: known_correct total=382 fired=0   fire_rate=0.0000
hs12: confab        total=1312 fired=1304 fire_rate=0.9939
hs15: confab        total=1312 fired=1293 fire_rate=0.9855
```
Confab fired at ~99% on both layers, so the G1 confab_tighten numbers above
are genuine measurements. Known-correct rows fired essentially NEVER (1/382
at hs12, 0/382 at hs15) -- the reported known_correct_cost_control rate
(2/382 = 0.00524 for BOTH layers, identical) is counting ~380 undosed rows
as automatic non-failures, not measuring selectivity on dosed rows. This
matches the parallel diagnostic entry's independent claim exactly (that
entry called hs12's G2 "NOT-ADJUDICABLE, not a pass" and predicted hs15
would be "worse" -- confirmed: hs15 fired zero known-correct rows, strictly
worse than hs12's one). **g2_midband_selectivity_cap_pass=TRUE as computed
by the script is not evidence of real selectivity at either site** -- it is
the vacuous unconditional-denominator reading, now confirmed twice
independently (parallel diagnostic + my own direct fire-rate check).

Reporting both the razor-thin G1 margin and the G2 vacuity to the lead with
equal weight, deliberately not shading toward either PASS or FAIL framing.
G1/G2 adjudication remains the lead's, not mine.

### 2026-07-24 -- ROOT CAUSE: `use_cache=False` corrupts gemma-4 hidden states at the KV seam (Tier 3 diagnostic); plus mistral hs12/hs15 divergence under identical FIT scores

Tier-3, diagnostic only. Establishes no claim and revises no gate. Two
independent findings, both CPU-only, both read-only w.r.t. committed artifacts.

**1. ROOT-CAUSED. `use_cache=False` corrupts gemma-4 hidden states from hs25
onward. Gemma GENERATIONS are sound; gemma CACHED ACTIVATIONS are not.**

**[CORRECTION — supersedes the first version of this entry.]** This entry
originally concluded "the gemma live-logits gate returns NOT SOUND" and read
that as the whole gemma pipeline producing garbage, the 0/176 null included.
**That conclusion was wrong and is withdrawn.** The pre-registered decision rule
offered only two branches — "recon bug, gemma sound" or "live also wrong, gemma
suspect" — and the truth is a third thing the rule did not anticipate: the model
is fine, generation is fine, and the defect is confined to one keyword argument
on one line of the extraction script. The lead reported NOT SOUND before
root-cause was in hand; this is the correction. The gate harness itself was the
broken instrument.

**The mechanism.** Same model, same 129 token ids, same rendered prompt. The
only difference is `use_cache`:

| forward call | top-1 at anchor | p | rank of `{"` (the token actually emitted) |
|---|---|---:|---:|
| `use_cache=True` (what `.generate()` does) | `{"` | 0.8355 | **1** |
| `use_cache=False` (what extraction did) | `ah` | 0.7578 | **5228** |

Per-layer cosine between the two, final position:

- **hs00-hs24: cos = 1.000000** — identical.
- **hs25-hs42: cos 0.732 -> 0.075** — collapsing with depth.

**The boundary is the KV seam, exactly.** Gemma-4-E4B shares K/V across layers:
blocks 24-41 read donor K/V from blocks 22/23 (`first_kv_shared_layer_idx =
24`). Hidden state hs25 is the output of block 24 — the *first* block that reads
donor K/V. The sharing is routed through the cache object, so disabling the
cache starves precisely the shared blocks and nothing below them. The boundary
was measured first and only *then* matched to the seam, which is why it is
convincing rather than a story fitted after the fact.

**Blast radius, exactly delimited.** `grep -rn use_cache --include=*.py` over
the experiment returns **exactly one call site**: `extract_anchor.py:123`,
`model(**enc, output_hidden_states=True, use_cache=False)`. Generation goes
through `.generate()` (`gen_lib.py:50`, `mine_eval_pool.py:124`), where
`use_cache` defaults True.

- **SOUND: every gemma generation** — mined pool, eval rows, and the dosed
  generations behind the 0/176 null. All produced via `.generate()`.
- **INVALID: every cached gemma activation.** The manifest's
  `hidden_states_indices` are **[34, 38, 42, 40]** — all four >= 25, so *none*
  survive. Everything fit on them inherits the defect: probe AUC, the KU
  direction, and the boundary-push write direction.
- **The gemma 0/176 null is therefore uninterpretable — but not for the reason
  previously recorded here.** The model computed correctly during dosing; what
  was injected was a direction fit on corrupted activations. "We wrote a
  meaningless vector and nothing happened" is not evidence that gemma cannot
  actuate.
- **Gemma hs <= 24 would be valid** — but nothing was ever extracted there.
- **The `cos_vs_gpu_cached` 0.998-0.9998 CPU-vs-GPU agreement is now explained**
  and is not reassurance: both sides ran `use_cache=False`, so they agree with
  each other and are both wrong. This is exactly the consistency-is-not-
  correctness trap flagged in the previous version of this entry, now confirmed.

**Family control — the defect is gemma-only.** Harness
`scratchpad/use_cache_family_control.py`, results
`use_cache_family_control_results{,2}.json`. Same True-vs-False comparison:

| family | layers | min cos over all layers | top-1 agrees | verdict |
|---|---:|---:|---|---|
| llama-3.2-3b | 28 | 1.000000 | yes | UNAFFECTED |
| qwen35-4b | 32 | 1.000000 | yes | UNAFFECTED |
| mistral-7b-v03 | 32 | 1.000000 | yes | UNAFFECTED |
| gemma4-e4b | 42 | **0.075** | **no** | **CORRUPTED from hs25** |

None of the other three share K/V across layers. **The llama, mistral, and qwen
read/actuate results are untouched by this.**

**The fix is one keyword** (`use_cache=True` at `extract_anchor.py:123`) plus
re-extraction. Observed on transformers 5.5.0 / torch 2.9.0+cu128 with
`Gemma4ForConditionalGeneration`; whether upstream treats cache-free forward on
a KV-sharing model as a bug or as unsupported, our extraction must not use it.

**Superseded detail, retained for the record.** The measurements below were the
route to the root cause and remain accurate as measurements; only the
"pipeline produces garbage" reading of them is withdrawn. In particular the
"one suspect survives — meta-device offload" line is **dead**: a forced full
load returned `n_meta_params: 0` and bit-identical top-1
(0.050955414012738856), eliminating it.

Harness `scratchpad/live_logits_gate_check.py`, results
`scratchpad/live_logits_gate_results.json`. Teacher-forcing top-1 over each
row's own recorded generation:

| family | rows | live top-1 | anchor rank (target = first generated token) |
|---|---:|---:|---|
| llama-3.2-3b | 1 | 0.5635 | 1 |
| gemma-4-E4B-it | 8 | 0.027-0.058 (mean ~0.042) | 1714, 1814, 2074, 2371, 2825, 4058, 4155, 4724 |

The gemma anchor target is token 14937 = `{"`, the opening of the JSON object
each row demonstrably emitted. Live gemma ranks it ~2000-4700th.

**Confounds eliminated (each by direct measurement, not argument):**

- *Reconstruction path.* `top1_acc_live == top1_acc_recon` EXACTLY in all 9
  rows, both families, and `corr_live_vs_recon` >= 0.9995. The reconstruction
  faithfully reproduces the live model. This RETIRES the prior
  "reconstruction bug" story — the recon was never the problem.
- *Render.* Gate's `prompt_len` matches `manifest_prompt_len` exactly, 8/8.
- *Family asymmetry in scoring.* The gate scored llama from recorded
  `baseline_token_ids` but gemma from tokens RE-DERIVED from `answer_text`
  (gemma has no recorded token IDs anywhere on disk — neither
  `eval_rows.jsonl` nor `pool_generations.jsonl` carries the field, so the
  asymmetry was forced, not chosen). Lead ran the control
  (`scratchpad/retok_control.py`, results `retok_control_results.json`):
  llama scored BOTH ways on 6 rows, re-tokenization byte-identical to recorded
  IDs in 6/6, top-1 identical to 4 decimals (0.5230 vs 0.5230). Asymmetry is
  harmless.
- *Gemma-specific re-tokenization drift.* 8/8 rows off by exactly one token
  (retok = `n_new_tokens` - 1), the stripped terminator. Constant and
  explained; cannot cost 96% of positions.

- *[RESOLVED] Meta-device offload.* Was the last surviving suspect: the gemma
  load emits `Some parameters are on the meta device because they were
  offloaded to the cpu and disk.` and llama does not. Forced full load
  (`device_map=None`, `scratchpad/forced_load_check.py`) returned
  `n_meta_params: 0` of 1160 and top-1 **bit-identical** to the offloaded run.
  Suspect eliminated.
- *[RESOLVED] Render and tokenization.* `ml.render('gemma4-e4b', ...)` is
  **byte-identical** to `tokenizer.apply_chat_template(...)`, and `.generate()`
  from it reproduces the recorded answer exactly. `add_special_tokens` True vs
  False and explicit `attention_mask` all yield identical ids and identical
  garbage top-1 (`ah`, p=0.758) — so the ids were never the problem.

The elimination sequence above is what left `use_cache` as the only remaining
difference between the working `.generate()` path and the failing forward, which
is how the root cause was found.

**What the 0/176 null means now.** It cannot be cited as evidence about gemma's
actuability — the same bottom line as before, but for a different and much more
specific reason, and with a known fix rather than an open question.

**2. Mistral hs12 vs hs15: the n=8 FIT ladder has no discriminating power.**

Both sites ran the identical 8-rung `RATIO_LADDER` at n=8 per rung
(`analysis/mistral-7b-v03/dose_calibration_summary.json`, verified directly),
and the FIT scored them IDENTICALLY at 0.625 (5/8 each). Held-out:

| site | rel depth | FIT (n=8, max over rungs) | held-out `clean_tighten` |
|---|---:|---:|---|
| hs12 | 0.375 | 0.625 | **0.2216** (289/1304, Wilson [0.1999, 0.2450]) — COMPLETE |
| hs15 | 0.469 | 0.625 | **0.5000** provisional (246/492, Wilson [0.4560, 0.5440]) — RUNNING |

Two sites the instrument called equal differ by >2x at held-out scale. This is
a paired within-family demonstration that the n=8 max-over-rungs estimator
cannot distinguish a 0.22 site from a ~0.50 site, independent of any depth
argument.

**hs12 is a decisive G1 FAIL** (upper CI 0.2450 < 0.40 floor; no remaining rows
could move it). Its G2 is **NOT-ADJUDICABLE, not a pass**: fired n=1 of 382
known-correct rows (fire rate 0.26%), Wilson on the fired denominator
[0.000, 0.794]. The unconditional-denominator reading (2/382 = 0.0052, upper
0.0189) scored 381 never-dosed rows and is vacuous — the G2 diagnosticity
defect, now demonstrated rather than argued.

**hs15 is UNDECIDED and must not be pre-adjudicated.** At n=492 fired of ~1300
it sits at **exactly 0.5000** (246/492) against a >=0.50 floor, with Wilson
lower 0.4560 already clearing the >0.40 requirement. It is balanced on the
threshold to the single row: one more failure puts it below the floor, one more
success above. The lead's earlier expectation that hs15 would fail like hs12 is
NOT supported and is retracted. No interpretation until it completes.

Its G2 is heading for the same vacuity as hs12's, and worse: **141
known-correct rows so far, 0 fired.** At zero dosed rows the gate has no
denominator at all, so G2 will be **NOT-ADJUDICABLE** on this site too unless
the fire rate changes materially over the remaining rows.

Roll-up consequence, both branches stated in advance: **hs15 fails** -> only
llama clears -> FALSIFIED. **hs15 clears** -> llama + mistral = exactly 2 ->
MIXED. With gemma NOT-RUN and qwen3.5 back-burnered, this one site decides
which.

### 2026-07-24 -- INSTRUMENT FINDING: read-panel site selection is the argmax of a saturated curve; full-depth re-extraction planned (Tier 3, analysis-only, nothing run yet)

Tier-3 lab-notebook entry per `reference/amendment-vs-lab-notebook.md`. Routed
by the decision questions: (1) touches no hypothesis, falsifier, gate, metric
definition, or reporting label on the governed surface -- no; (2) adds no new
cell or arm to be reported as evidence -- no; (3) therefore tier 3, and it is
recorded here rather than in a new amendment. **This entry makes no claim and
authorizes no evidence.** The write sweep it is intended to enable is a
separate tier-2 amendment that must be signed before any of it runs.

**The finding.** Site selection in this experiment used the family-atlas read
panel. That panel is saturated and flat across exactly the depth range where
actuation varies by ~6x, so its argmax is determined by noise -- and because
the curves tilt very slightly upward with depth, that noise lands deep in
every family.

Llama-3.2-3B, caution axis
(`experiments/jspace-family-atlas/analysis-committed/llama32_3b_instruct/atlas_summary.json`,
`per_layer.<i>.read_panel.caution.point`) against this experiment's own
actuation outcomes:

| hs | rel depth | caution AUC | actuation |
|---|---|---|---|
| 17 | 0.607 | 0.825 | 0.742 held-out (`analysis/llama-3.2-3b/full_summary.json`) |
| 20 | 0.714 | 0.831 | 0.375 FIT |
| 23 | 0.821 | 0.832 | 0.125 FIT |
| 26 | 0.929 | **0.839** | 0.125 FIT |

Read AUC is *highest* at the site where actuation is ~6x lower. Gemma-4-E4B's
caution axis is 0.922 essentially flat from hs20 through hs42
(`experiments/gemma-4-e4b-family-atlas/analysis-committed/gemma4_e4b_it/atlas_summary.json`).

The `doubt` axis reads 1.000 at nearly every layer in every family and carries
no usable information at this anchor: a FIXED RANDOM direction reaches up to
0.97 on the same contrast (canonical:
`refused-vs-known-contrast-carries-norm-position-confound`). The caution and
raw_refusal axes do NOT carry that confound on llama / mistral / qwen3-4b
(random control near chance), so the flatness above is a real measurement, not
an artifact. On gemma the confound is layer-patchy and that mechanism note
already prescribes preferring layers where the control is near chance on all
axes simultaneously (**hs14-18, hs36-40**) over the naive best-AUROC layer.
This experiment wrote gemma at hs34/38/40/42; hs34 sits inside an
elevated-control band (hs28-34), and hs14-18 was never extracted.

`eff_dim_frac` does not rescue selection either: llama hs17 and hs23 both read
0.004 with 0.742 vs 0.125 actuation.

**The extraction gap.** Anchor extraction retained only the read-selected
sites, so there is no shallow-layer data to reanalyse -- the read criterion
gated not just where we wrote but what we kept:

| family | cached | all-layer cost |
|---|---|---|
| mistral-7b-v03 | 4 of 32 (`[12,15,19,30]`) | 0.74 GiB |
| llama-3.2-3b | 4 of 28 (`[17,20,23,26]`) | 0.47 GiB |
| gemma4-e4b | 4 of 42 (`[34,38,42,40]`) | 0.16 GiB |

(per-family `analysis/<fam>/anchor_extract_manifest.json`). `extract_anchor.py:123`
already runs the forward with `output_hidden_states=True`; `extract_anchor.py:127`
then keeps only the selected indices. Every layer is computed and discarded.
Retaining all of them costs ~1.37 GiB total and the same forward passes
(~7 min GPU across the three families; current manifests report 235.3 / 112.8 /
63.2 s for the 4-layer runs).

This is the operative blocker on shallow work: writing at a new site requires
the KU direction fitted AT that site, which requires activations there. Gemma
cannot be fit at hs14-18 today.

**Planned tier-3 work (none of it run yet; GPU currently held by the mistral
`--mode full` run, PID 1260218):**

1. Re-extract all layers, all three families, retaining the existing row set,
   split, and anchor definition unchanged (`prompt_len-1`). Pure superset of
   the current cache -- existing artifacts must remain bit-identical for the
   four already-cached indices, and that identity is the acceptance check.
2. Fit the KU direction and compute candidate offline predictors at every
   layer, including a write-effect proxy: dose the direction and measure the
   next-token distribution shift under a SINGLE forward pass, no generation.
3. Score every candidate predictor against the actuation outcomes that already
   exist (4 sites x 3 families; only llama hs17 and mistral hs12 are
   well-powered held-out).

**Stated limits, so this entry is not later over-read.** The validation set is
~12 points of which ~2 are well-powered; that is far too few to fit a
predictor over several candidate features, and no predictor selected this way
may be reported as validated. The proxy is a *candidate*, and the honest
outcome may be that it fails to track actuation -- which is itself a cheap and
useful elimination. Nothing here licenses a site choice as "correct"; it can
only propose sites for a pre-registered test.

**What would require a tier-2 amendment (NOT authorized by this entry):** any
dosed-generation run at a new site, on any family, including the gemma
hs14-18 band and any shallow llama sweep. That amendment must pre-state its
prediction, falsifier, and gates before running, and should pre-register the
SELECTION RULE rather than a hand-picked site list, so that what is tested is
the portable procedure and not the lead's prior.

**Related in-flight correction.** The mistral `--mode full` run (in progress at
time of writing) puts hs12 held-out `clean_tighten` at 244/1097 = 0.2224,
Wilson [0.1988, 0.2480], against a FIT calibration estimate of 0.625 at the
same site -- the FIT ladders are n=8 per dose and the site score was taken as
the max over 8 doses, so they are biased high, worst where the true rate is
low. Provisional until the run completes; recorded here only as a caution
against reading the n=8 calibration ladders as potency estimates.

### 2026-07-24 -- mistral-7b-v03 calibrate_dose.py v2 COMPLETE -- USABLE DOSE FOUND at 2 of 3 midband layers (hs12, hs15), strongest R2 transfer result so far

v1 preserved before launch (`analysis{,-committed}/mistral-7b-v03/
dose_calibration_summary_v1.json`, plain cp, same discipline as llama).
`calibrate_dose.py --family mistral-7b-v03` (PID 1243715) ran cleanly, all
32 cells, ~10 min. Median norms: hs12=3.35, hs15=4.43, hs19=8.01,
hs30(late)=21.48 -- matches the pre-calibration anchor read logged in
mistral's original v1 NOT-RUN entry (2026-07-23, below).

**Result: `all_midband_have_usable_dose: False` but `selected_doses:
{"hs12": 1.854, "hs15": 3.765}` -- TWO of three midband layers dose-viable,
stronger coverage than llama's 1-of-3.**

- **hs12 (median_norm=3.35, HAS_USABLE_DOSE=True):** confab_tighten rises
  with dose -- 0.000 (ratio 0.100/0.153) -> 0.125 (0.235) -> **0.500 at
  ratio=0.361 (dose=1.21, usable=True)** -> **0.625 at ratio=0.554
  (dose=1.85, usable=True)** -> drops to 0.375 (0.850) -> 0.000 with
  collapse=0.50 (1.304) -> 0.000 with collapse=0.75 (2.000). Selected:
  ratio=0.554 (higher confab_tighten of the two usable rungs, per selection
  rule's primary sort key).
- **hs15 (median_norm=4.43, HAS_USABLE_DOSE=True):** confab_tighten climbs
  more gradually -- 0.000/0.000/0.125/0.125/0.375 through ratio=0.554, then
  **0.625 at ratio=0.850 (dose=3.76, usable=True)**, single usable rung,
  drops to 0.250 (1.304) then 0.000 with collapse=0.88 (2.000).
- **hs19 (median_norm=8.01, has_usable_dose=False):** confab_tighten=0.000
  at ALL 8 rungs, no exception -- clean null like gemma's layers, even
  though collapse only creeps in late (0.12@0.850, 0.25@1.304, 1.00@2.000).
- **hs30 (late_reference_descriptive, non-gating, has_usable_dose=False):**
  same clean-null shape as hs19 -- confab_tighten=0.000 at all 8 rungs,
  collapse only appears at the top two rungs (0.12@1.304, 0.88@2.000).
  selected_dose=null, late arm SKIPPED as expected.

**Observation flagged for the lead's awareness, not yet interpreted:**
`known_correct_cost_control` rate is EXACTLY 0.125 (1/8) at every single one
of the 32 cells, across all 4 layers and all 8 ratio rungs, with zero
variation. This is FIT-scale screening (n=8), not the held-out G2 gate, so
it doesn't itself trip anything -- but the total invariance across layer
and dose is unusual and consistent with one specific FIT known-correct row
failing the well-formedness check regardless of intervention (dose-
independent noise), rather than a real per-cell effect. Flagging as a
straight observation for the resolve write-up, not chasing it further
myself.

Reported to lead, holding before any mistral G0 per standing discipline (same
as llama -- usability report first, review before proceeding).

### 2026-07-24 -- llama-3.2-3b full held-out run COMPLETE -- terminal evidentiary result, script's own G1/G2 booleans both TRUE (lead's adjudication pending, not mine)

`run_contrast.py --family llama-3.2-3b --mode full --i-know-this-is-the-
cross-family-run` (PID 1231456) ran cleanly to completion, no errors.
Monitored mid-run for anomalies per lead's explicit instruction (stop on
collapse spike or readback drift): spot-checked at 401/~1206 and 790/~1206
fired rows -- zero degenerate/collapsed rows at every check, readback
tightly clustered around target throughout (mean 4.969 vs target 4.955,
min/max 4.962-4.974 at the first check). No anomaly at any point; ran
through to completion without intervention.

**Straight numbers (script's own output, not my adjudication):**
- n_rows=1206 (872 confab + 334 known_correct_answered held-out), n_fired=870
- readback_mean=4.9688 (target 4.9549), frac_readback_within_tol=1.0,
  collapse_rate_on_dosed=0.0 -- across the FULL held-out set, not just the
  smoke sample.
- confab_tighten (hs17, held-out): n=872, successes=647, **rate=0.7420**,
  Wilson 95% CI **[0.7119, 0.7699]**.
- known_correct_cost_control (hs17, held-out): n=334, successes=4,
  **rate=0.0120**, Wilson 95% CI **[0.00467, 0.0304]**.
- Script's own `primary` block: `best_mid_layer=hs17`,
  `g1_floor_used={rate:0.5, wilson_lower_ci:0.4}`,
  `g2_cap_used={rate:0.05, wilson_upper_ci:0.1}`,
  `g1_midband_actuation_floor_pass: true`,
  `g2_midband_selectivity_cap_pass: true`, `primary_pass: true`.
- Late reference (hs26): SKIPPED, no usable late-arm dose (expected,
  non-gating, matches doubt-snap's late-site null).

These are the script's own computed booleans against the registered
thresholds, reported as machine output -- the G1/G2 ADJUDICATION itself is
the lead's, not stated as a verdict here. Reported to lead. Proceeding
directly to mistral-7b-v03's v2 calibration next per standing orders (v1
summary preservation first, same discipline as llama).

### 2026-07-24 -- llama-3.2-3b G0 smoke PASS -- conflict resolved with USER APPROVAL (reading b), run_contrast.py repinned 456d309f, partial-midband coverage now permitted

**Conflict resolution (escalated to user by lead):** ruled reading (b) --
the all-midband precondition in `run_contrast.py` was sign-time code written
under the Qwen3-4B all-usable assumption, not a registered requirement. R2's
own roll-up language ("a family 'runs past G0' if its v2 calibration finds A
usable dose and G0 passes" -- singular, user-ratified, postdates the
sign-time code) is the controlling text. Llama's disposition stands:
proceeds at hs17.

**Fix applied by lead, user-approved, repinned `run_contrast.py` fc7dabd9 ->
456d309f:** `load_midband_selected_doses()` now raises only on (a) EMPTY
selected doses (zero-usable = hard NOT-RUN, verified gemma is still
correctly rejected under this path) or (b) non-mid-band extras in the
selected map; partial coverage between those two is permitted, with a
provenance comment citing R2 directly in the code. `_layer_dose_map()` now
doses only the layers present in `selected` -- hs20/hs23 (llama's
non-viable midband candidates) are never dosed in smoke or full mode.
`evaluate_primary` was read by the lead and already tolerated partial sets
and a skipped late arm without needing a change. I independently verified
before relaunching: repin sha present in `experiment.yaml`, py_compile
clean, and a direct call `load_midband_selected_doses('llama-3.2-3b')`
returns exactly `{'hs17': 4.954897429720482}`.

**Smoke result (PID 1229533, exited cleanly, log
`llama_run_contrast_smoke_v2.log`): `g0_smoke_pass: true`.** Only hs17
dosed (`layer_doses: {"hs17": 4.954897429720482}`), `late_arm_included:
false` (no usable late dose, as expected). Pool: confab_held_out=872,
known_correct_answered_held_out=334 (llama's REUSED doubt-snap pool, much
larger than gemma's fresh mine). At n=8 rows (4 confab + 4 known,
smoke-scale): `frac_readback_within_tol=1.0` (perfect), `collapse_rate_on_
dosed=0.0` (zero), `readback_mean=4.969` (target 4.955, well within
tolerance), confab_tighten 3/4 = 0.75 (Wilson [0.301, 0.954]),
known_correct_cost_control 0/4 = 0.0 (Wilson [0.0, 0.490]).

Reported to lead, holding for ack before `--mode full` per standing
discipline (their explicit "report first and wait for my ack" instruction
for this step specifically, distinct from the flag-but-don't-block pattern
used elsewhere in this cycle).

### 2026-07-24 -- llama-3.2-3b G0 smoke BLOCKED -- run_contrast.py structurally requires ALL midband layers dosed, conflicts with lead's "1-of-3 sufficient" adjudication -- HOLDING for re-adjudication

Lead adjudicated (see entry below) that llama's single usable dose (hs17) is
sufficient to proceed to G0 smoke, with hs20/hs23 (no usable dose) simply
excluded from dosing rather than blocking the family. Launched
`run_contrast.py --family llama-3.2-3b --mode smoke`; it exited immediately
(exit 1, PID 1225815, no partial run log written -- crash occurred before
`run_layers` started):

```
File "run_contrast.py", line 80, in load_midband_selected_doses
    raise ValueError(f"[{family}] calibration summary says not all mid-band layers have usable doses")
ValueError: [llama-3.2-3b] calibration summary says not all mid-band layers have usable doses
```

Read `load_midband_selected_doses()` (run_contrast.py:66-86) and
`_layer_dose_map()` (246-256) in full: this is not a loose validation check
to relax -- `_layer_dose_map()` loops over the FULL fixed set of
`family_midband_hs_indices(cfg)` (all 3 midband candidates from
band_selection) and unconditionally looks each one up in
`midband_selected_doses`; even without the explicit `ValueError`, missing
layers (hs20, hs23) would just KeyError. There is no code path in this
script for building a dose map over a subset of midband candidates -- it is
written to require doses at every midband site as a precondition for
running G0/contrast at all.

Cross-checked against AMENDMENT.md directly (not paraphrased): lines
400-401 ("smoke readback within 5%+0.5 absolute of each layer's calibrated
dose; smoke collapse on dosed rows is 0 for every mid-band candidate and the
late arm") are genuinely ambiguous between "every candidate that HAS a
calibrated dose" (lead's reading) and "every candidate, full stop" (what the
code enforces). Lines 317-322's "best mid-band site" definition describes
selection among whatever ran, doesn't resolve whether partial coverage is
permitted to run in the first place.

Reported to lead without taking a side -- this needs either (a) a ruling
that unanimous mid-band dose-viability IS the registered requirement (which
would put llama's disposition in the same NOT-RUN category as gemma, not
proceed-at-hs17), or (b) confirmation that "1-of-3 sufficient" is correct
and a scoped, lead-authorized code change to `run_contrast.py` (restructuring
`load_midband_selected_doses`/`_layer_dose_map` to build a doses-only-where-
usable subset, with a governed repin). Not applying anything myself. GPU
idle, no partial artifacts, holding for re-adjudication before touching
mistral.

### 2026-07-24 -- llama-3.2-3b calibrate_dose.py v2 COMPLETE -- USABLE DOSE FOUND at hs17 (midband), first R2 confirmation the ratio hypothesis transfers

**Provenance note before the run:** `calibrate_dose.py`'s final summary output
filename (`dose_calibration_summary.json`, both under `analysis/` and
`analysis-committed/`) is NOT versioned between v1/absolute-ladder mode and
v2/normalized-ladder mode -- only the runlog checkpoint is
(`calibrate_dose_records.jsonl` vs `calibrate_dose_records_v2.jsonl`,
confirmed by reading the script). Running v2 would have silently overwritten
llama's v1 NOT-RUN evidence, which R2's scope explicitly requires stays on
record. Preserved both copies before launching:
`analysis{,-committed}/llama-3.2-3b/dose_calibration_summary_v1.json` (exact
copies of the pre-run files, mtimes Jul 23 21:19). Not a pinned-code change,
a plain data-preservation copy.

**Result: `all_midband_have_usable_dose: False`, `all_layers_have_usable_dose:
False`, but `selected_doses: {"hs17": 4.954897429720482}` -- ONE of the three
midband layers (hs17) DOES have a usable dose under v2, unlike gemma's clean
0-for-4 null.** Median norms: hs17=13.73, hs20=17.11, hs23=21.84,
hs26(late)=30.51.

- **hs17 (midband, HAS_USABLE_DOSE=True):** non-monotonic but genuine
  dose-response -- ratio=0.100/0.153 confab_tighten=0.000; ratio=0.235
  confab_tighten=0.375 (close but under floor); **ratio=0.361 (dose=4.95)
  confab_tighten=0.875 (7/8), collapse=0.00, known_cost=0.000, usable=True**;
  ratio=0.554 drops back to 0.125; ratio=0.850 drops to 0.000; **ratio=1.304
  (dose=17.90) confab_tighten=0.875 again, collapse=0.00, known_cost=0.000,
  usable=True** (a SECOND usable rung); ratio=2.000 confab_tighten=0.000 with
  collapse=0.88. Selected: ratio=0.361 (dose=4.95) -- ties with 1.304 on
  confab_tighten/known_cost, selection rule's lower-ratio tie-break picked
  the smaller dose. Readback perfect (1.00) at all 8 rungs.
- **hs20 (midband, has_usable_dose=False):** confab_tighten stays 0.000-0.375
  throughout (small non-zero blips at 0.554/0.850 only), never crosses 0.5;
  collapse onset at ratio=1.304 (0.25), full collapse by 2.000.
- **hs23 (midband, has_usable_dose=False):** confab_tighten=0.000 at 6 of 8
  rungs, one blip of 0.125 at ratio=0.850; collapse jumps straight to 1.00 at
  ratio=1.304.
- **hs26 (late_reference_descriptive, non-gating, has_usable_dose=False):**
  confab_tighten=0.000 except one 0.125 blip at ratio=0.554; collapse ramps
  0.38 at 0.850 -> 0.50 at 1.304 -> 1.00 at 2.000. `selected_dose: null`,
  late arm SKIPPED per the doubt-snap late-site-null note, non-gating.

n=8 confab + 8 known per cell throughout, same as gemma's run. Straight
report to lead, no G0/contrast run yet -- holding per standing discipline
("report per-layer usability windows and selected doses BEFORE any G0").
This is the first R2 result where the norm-scaled ratio hypothesis actually
transfers (partially) to a non-Qwen3-4B, non-null family -- distinguishes
this from gemma's write-verified-but-totally-null result and from the v1
instrument-resolution-limited stops on record below.

### 2026-07-24 -- gemma4-e4b DISPOSITION: NOT-RUN, registered G0 dose-viability stop -- WRITE-VERIFIED BEHAVIORAL NULL (distinct category from llama/mistral's v1 INSTRUMENT-RESOLUTION-LIMITED stops)

**Adjudicated by lead** (independently cross-checked cell-level `dose_calibration_summary.json`, matches my report exactly). Gemma's pipeline STOPS here: NOT-RUN, excluded from the cross-family roll-up denominator per AMENDMENT.md's explicit rule ("a G0 stop here removes a family from the denominator... the roll-up covers every family disposition (pass / fail / NOT-RUN) explicitly"). No G0 smoke, no run_contrast -- there is no usable dose to run them with.

**Modal fallback clause checked and closed:** does NOT trigger. It is pre-authorized only for an OOM at G0; this calibration ran to completion locally with perfect readback at every cell, so Modal would only reproduce the identical behavioral null, not resolve anything.

**Category distinction -- now the official framing for this experiment's write-up, do not conflate the two:**
- llama-3.2-3b / mistral-7b-v03 v1 stops (2026-07-23, see entries far below) = **INSTRUMENT-RESOLUTION-LIMITED**: the fixed absolute ladder [25...200] was calibrated in Qwen3-4B's own residual units and never actually probed either family's plausible dose band (llama's doses were 1.8-14.6x its own median norm; mistral's were 3.1-60x) -- the instrument itself never reached the region where a real answer could be read off. This is exactly the failure mode R2's norm-scaled ladder was built to fix.
- gemma4-e4b v2 stop (this entry) = **WRITE-VERIFIED BEHAVIORAL NULL**: dose-search exhausted a correctly-denominated, norm-scaled ladder that spans cleanly from inert (zero collapse, zero known-correct cost) to total collapse, `frac_readback_within_tol` PERFECT (1.00) at all 32 cells -- the write mechanism is not in question. `confab_tighten` is 0.000 at every single cell on all 3 midband layers (hs34, hs38, hs42) and only two isolated 1/8 blips at the non-gating hs40 late-reference arm, nowhere near the 0.5 usability floor. The ladder DID reach the plausible band this time; the intended behavioral effect simply never appeared anywhere in it.

**Supporting context for the write-up (caveat, not part of the disposition):** gemma's near-flat eff_dim profile from jlens_profile (0.0046-0.0058 across 9 of 10 sweep points, no clear workspace-like peak distinct from noise) and hs42's markedly early collapse onset (already 90% collapsed by the SECOND ladder rung, ratio=0.153, vs hs34/hs38's first collapse only at the 5th rung, ratio=0.554) are internally consistent with the null: the locked band-selection rule's chosen sites (hs34/38/42, adjudicated to stand as-is per the earlier band_selection ruling, repin 646d12a7) may simply lack the structure this write-mechanism intervenes on for this family. This is interpretive context for the eventual resolve write-up, not an adjudicated finding.

**Bookkeeping confirmation (both items from earlier in this cycle already landed, cross-checking per lead's request):** the 806-vs-730 row-provenance breakdown (450 known_correct_answered + 280 confab + 76 unknown_refused = 806) is logged in the "anchor extraction / norms / build_directions / gate_fit all clean" entry below; the torn-read gotcha (mid-run reads of `anchor_extract.safetensors` while `extract_anchor.py` is still writing can produce a transient spurious `inf`) is logged in the same entry.

Gemma4-e4b's role in this experiment ends here pending any future signed revision. Handing the GPU to llama-3.2-3b's v2 re-calibration next.

### 2026-07-24 -- gemma4-e4b: calibrate_dose.py v2 COMPLETE after tuner fix -- clean null, no usable dose at any of 4 layers, all 32 cells

After the tuner submodule fix (7a44eb3) landed, relaunched
`calibrate_dose.py --family gemma4-e4b` (PID 1184861); ran cleanly to
completion, all 32 (layer,dose) cells recorded in
`analysis/gemma4-e4b/runlog/calibrate_dose_records_v2.jsonl`. Result:
`all_midband_have_usable_dose: false`, `all_layers_have_usable_dose: false`,
`selected_doses: {}` -- straight report, not yet adjudicated by lead.

Per-layer, per-cell (mode=fit_dose_calibration, dose_mode=ratio_normalized,
calibration_split=fit, n=8 confab + 8 known per cell, min_confab_rate_for_
usable=0.5):

- hs34 (midband, median_norm=120.20): ratio 0.100-0.361 clean writes
  (collapse=0.00), confab_tighten=0.000 throughout. collapse jumps to 0.78 at
  ratio=0.554, 1.00 from ratio=0.850 on. confab_tighten never leaves 0.000 at
  ANY of the 8 rungs.
- hs38 (midband, median_norm=125.51): same shape -- clean through ratio=0.361,
  collapse=0.40 at 0.554, 1.00 from 0.850 on. confab_tighten=0.000 at every
  rung.
- hs42 (midband, median_norm=281.34): collapse onset markedly earlier --
  already 0.90 by ratio=0.153 (the SECOND rung), 1.00 from ratio=0.235 on.
  confab_tighten=0.000 at every rung including the two pre-collapse ones.
- hs40 (late_reference_descriptive, non-gating, median_norm=117.57): mostly
  the same, confab_tighten=0.000 except two isolated n=1/8 blips (0.125) at
  ratio 0.361 and 0.554 -- nowhere near the 0.5 floor. collapse reaches 1.00
  by ratio=1.304, known_cost hits 1.000 at the top two rungs.

Key distinguishing fact from llama/mistral's v1 dispositions:
`frac_readback_within_tol` is a PERFECT 1.00 at all 32 cells -- the write
mechanism is not in question, doses land exactly as commanded across the
whole ladder. Unlike llama/mistral (whose v1 absolute-ladder doses sat
entirely outside the plausible band -- an off-scale/units problem, which is
exactly what R2's norm-scaling was built to fix), gemma's norm-scaled doses
occupy a well-behaved range: low rungs write cleanly with zero collapse and
near-zero known-correct cost, the ladder spans cleanly from "no visible
effect" to "total collapse" -- but `confab_tighten` never crosses zero
anywhere in between, on any of the 3 midband layers. Reported straight to
lead, no disposition category assigned by me; awaiting adjudication on
whether this "ladder exhausted, write mechanism verified, zero behavioral
effect" pattern gets distinct language from llama/mistral's off-scale
NOT-RUN framing in the eventual resolve write-up.

### 2026-07-24 -- gemma4-e4b: calibrate_dose.py third crash -- shared synaptic-tuner submodule, NOT this experiment's pinned code -- fixed and pushed (tuner commit 7a44eb3)

Third genuine crash in the gemma cycle, but a different repo boundary than
the first two (jlens_profile.py's own two fixes, repins 260cf29e->0e642d81
and 0e642d81->fde1e2a6, both logged above). `calibrate_dose.py --family
gemma4-e4b` confirmed the R2 v2 normalized-ladder mechanics were exactly
right before crashing -- `normalized ladder mode:
ratios=[0.1, 0.153, 0.235, 0.361, 0.554, 0.85, 1.304, 2.0]
median_norms={ hs34: 120.1985, hs38: 125.5128, hs42: 281.3434, hs40: 117.5700 }`,
`32 (layer,dose) cells pending` -- then crashed on the very first cell
(`layer=hs34 ratio=0.1 dose=12.02`):

```
File "pipeline.py", line 212, in run_layer
    layer_module = get_decoder_layer(model, layer_idx)
File ".../synaptic-tuner/MechInterp/intervention/hooks.py", line 71, in get_decoder_layer
    raise AttributeError(
AttributeError: Could not locate decoder layers on this model; tried:
model.layers, language_model.model.layers, model.decoder.layers,
transformer.h, model.model.layers
```

This crash site (`synaptic-tuner/MechInterp/intervention/hooks.py`) is NOT
tracked in this experiment's `experiment.yaml` pin manifest at all -- it is
shared research-engine infrastructure with its own ownership boundary (root
CLAUDE.md), used as a single chokepoint by this experiment's `pipeline.py`,
the tuner's own `MechInterp/cli.py`, and its own test suite. Confirmed by
direct read of `transformers/models/gemma4/modeling_gemma4.py`: the correct
decoder-layer path is `model.language_model.layers` (three hops from the
loaded model object: `.model` -> `.language_model` -> `.layers`, the last
being the actual `nn.ModuleList` of `Gemma4TextDecoderLayer`), which
`hooks.py`'s `_LAYER_PATHS` fallback tuple had no entry for.

**Adjudicated and fixed by lead** (independently converged on the identical
diagnosis before my report arrived): appended `"model.language_model.layers"`
as a sixth, LAST-tried candidate to `_LAYER_PATHS` in
`synaptic-tuner/MechInterp/intervention/hooks.py` -- architecture-additive,
no existing candidate's resolution order changed, generic (no
experiment-specific logic), with a comment noting the transformers 5.x
multimodal-wrapper layout. Committed to tuner branch `fix/gemma4-decoder-
layer-path` at `7a44eb3` (cut from the worktree's checked-out `901dbe8`);
this worktree's submodule now points at that branch/commit -- verified
directly (`git log -1` in the submodule shows `7a44eb3`, `_LAYER_PATHS`
contains the new entry). Verified by lead via a no-weights meta-construction
of `Gemma4ForConditionalGeneration` confirming `get_decoder_layer` resolves
`Gemma4TextDecoderLayer` at indices 0, 33, 41. No pin action needed in this
experiment's `experiment.yaml` (hooks.py was never in that manifest).
Confirmed scope: this also unblocks `run_contrast.py`'s dose application
later (same intervention engine), not just calibrate_dose.

No calibrate_dose checkpoint file existed at crash time (crash occurred
before the first cell's result could be recorded) -- nothing to clean up,
clean stop. Relaunched as PID 1184861 (log `gemma_calibrate_dose_v2.log`)
after independently confirming the submodule commit and fix string.

### 2026-07-24 -- gemma4-e4b: anchor extraction / norms / build_directions / gate_fit all clean; band_selection anomaly adjudicated (repin 646d12a7); 806-row bookkeeping resolved

**Bookkeeping (lead flagged, resolved before G0 as required):** `extract_anchor.py
--family gemma4-e4b` extracted 806 rows total, which does not equal the
280+450=730 confab+known-correct mining targets by inspection alone. Pulled
the per-row `role` breakdown from `analysis/gemma4-e4b/anchor_extract_manifest.json`'s
`rows` list: `known_correct_answered=450, confab=280, unknown_refused=76` --
sums to exactly 806. The extraction script pulls the FULL mined pool
(confab+known_correct+unknown_refused), not just the two gated classes;
`unknown_refused` is descriptive-only (not gated by G1/G2) per gates.yaml and
was never missing, just outside the 730 the quick arithmetic covered.

**Anchor norms independently reproduced by lead** from the final (post-write)
safetensors: medians 120.20/125.51/117.57/281.34 at hs34/38/40/42
respectively, n=806, all min/max identical to my report, 0 non-finite values
across all 3224 tensors. **Gotcha for the record:** a mid-run read of
`anchor_extract.safetensors` while `extract_anchor.py` was still writing
produced a transient spurious `inf` (torn read of the progressive re-save) --
never trust a read of that file while the extraction process is still alive;
only the post-completion file is reliable.

**Band-selection anomaly (my earlier flag) adjudicated by lead, repin
5ffc1213 -> 646d12a7 on `families/gemma4-e4b.yaml`:** ruling is that the
locked band-selection rule applies exactly as registered -- `[34, 38, 42]`
stands, no post-hoc modification for the flat-profile/late-region/hs42-
different-regime geometry. That geometry is recorded as an interpretive
limitation to report straight at resolve time, not something to adjudicate
away mid-run.

**build_directions.py --verify-reproducible:** PASS (byte-identical refit) on
all 3 midband layers (hs34, hs38, hs42). hs40 (late_reference) intentionally
excluded from this artifact by design (`midband_hs_indices()` only), matching
the same 3-layer pattern already established for llama (17/20/23) and
mistral (12/15/19).

**gate_fit.py:** all 3 midband layers clear the locked g0_auc_floor=0.9 with
margin -- hs34 AUC=0.9779, hs38 AUC=0.9815, hs42 AUC=0.9772 (tpr 93.8-97.3%,
fpr 8.9-9.4%). Notable: hs42's gate is as strong as its siblings despite
being the collapsed-regime layer (low eff_dim_frac, ~2.3x higher norm) --
flagged by the lead as worth a mention at resolve. The pre-existing
`gate_auc_on_fit: 0.9472` at hs40/block 39 in `families/gemma4-e4b.yaml` is
confirmed (by lead, from the YAML's own reuse section) to be doubt-snap's
frozen late-site value, consumed verbatim per the AMENDMENT reuse discipline
and never recomputed by this pipeline's gate_fit.py -- by design, not an
omission.

**Cleared to proceed:** lead adjudicated calibrate_dose.py CLEARED, v2
default normalized mode (no `--doses`), expected per-layer dose targets
= RATIO_LADDER x that layer's own median norm (hs34 ~=12-240, hs38 ~=12.6-251,
hs42 ~=28-563 absolute).

### 2026-07-24 -- gemma4-e4b: jlens_profile.py second crash (hidden_size) + fix + repin fde1e2a6

Second genuine pinned-code bug in the same relaunch cycle, same underlying
cause (Gemma4Config not forwarding nested `text_config` fields to the top
level) but a different attribute and a different file than the first
(`num_hidden_layers` fix, repin 260cf29e -> 0e642d81, logged separately
below). Relaunch (PID 1106986) got cleanly past that first fix -- weight
loading completed (2130/2130 shards) and
`[jlens-profile:gemma4-e4b] n_hidden_layers=42
depth_sweep=[1, 6, 10, 15, 20, 24, 29, 34, 38, 42]` printed correctly -- then
crashed one call later:

```
File "jlens_profile.py", line 123, in run
    result = jlens.layer_profile(...)
File ".../j-space-localization-qwen3-4b/jlens.py", line 370, in layer_profile
    hidden_dim = model.config.hidden_size
AttributeError: 'Gemma4Config' object has no attribute 'hidden_size'
```

This crash site is inside `jlens.py` itself, which `jlens_profile.py`'s own
docstring marks do-not-modify (imported unchanged from the separate
`j-space-localization-qwen3-4b` experiment). `jlens.layer_profile()` has no
parameter to inject `hidden_dim` -- it always reads `model.config.hidden_size`
directly. Before reporting, scanned jlens.py for every other unguarded
`model.config.*` read to rule out a third crash cycle: three more exist
(lines 511/518 in `_cmd_smoke`, line 565 in `_cmd_profile`), all inside
jlens.py's own CLI subcommands, not reachable from `jlens_profile.py`'s code
path.

**Adjudicated and applied by lead**, generalizing the proposed shim: inside
`jlens_profile.py`'s existing nested-config block, BOTH loader fields
(`num_layers_field` and `hidden_size_field`) are now mirrored onto
`model.config` when absent, via a loop over the two canonical fields rather
than a one-off patch -- closes the whole attribute-forwarding class for this
entry point, not just `hidden_size`. Zero bytes changed in `jlens.py`; the
do-not-modify constraint holds. Repinned `jlens_profile.py` 0e642d81 ->
fde1e2a6, reason recorded in `experiment.yaml` `instrument.repins`. Verified
independently before relaunch: repin sha present in `experiment.yaml`, fix
code present at the expected lines, `py_compile` clean, GPU idle.

**Smoke-gate question resolved (no action needed):** `python jlens.py smoke`
is hardcoded to the Qwen3-4B checkpoint (`_cmd_smoke` calls `load_model()`
with no `model_name`/`--model` flag) -- a per-family jlens smoke is
impossible as written and was never run for llama/mistral either. This is an
instrument-hygiene gap (docstring advice that's unsatisfiable), queued by the
lead for a post-run hardening sweep, NOT a missing gate to invent mid-run.
The registered per-family instrument smoke for this experiment is
`run_contrast.py --family <family> --mode smoke` (AMENDMENT.md's "G0
instrument smoke per family"), unaffected and unchanged.

Relaunched again as PID 1112725 (log
`gemma_jlens_profile_v3.log`) after the fix; `families/gemma4-e4b.yaml`
`band_selection.status` was NOT reached by either crashed attempt (crash
occurred before the write-back point in both cases) -- nothing to flag for
repin from this yet.

### 2026-07-24 -- gemma4-e4b: re-mine at 280/450 targets SUCCEEDED, clears G0 held-out floor (confab 168 held-out, known-correct 270 held-out)

Confirming the final numbers from the re-mine authorized in the entry below
(superseding the first under-floor mine). `mine_eval_pool.py --family
gemma4-e4b --target-confab 280 --target-known-correct 450` and
`split_fit_heldout.py --family gemma4-e4b` (same pinned FIT_FRAC=0.40, seed
20260707) both ran cleanly, resuming from the cached `pool_generations.jsonl`
per the script's dedup-by-row_key resume (only new candidates scanned, the
first mine's 200/300 rows were not regenerated). Final pool:
confab=280 (fit=112/held_out=168), known_correct_answered=450
(fit=180/held_out=270), unknown_refused=76 (descriptive only, not gated).
Both held-out counts clear the locked G0 `reused_pool_powered` floor
(>=150 confab, >=250 known_correct_answered) with margin -- this is now the
authoritative pool for gemma; `analysis-committed/gemma4-e4b/eval_rows.jsonl`
and `split_manifest.json` reflect these 280/450-target counts, not the
superseded 200/300-target ones.

### 2026-07-24 -- gemma4-e4b: first mine (200/300 targets) SUPERSEDED, non-evidentiary; re-mining at 280/450

`mine_eval_pool.py --family gemma4-e4b` (script defaults --target-confab 200
--target-known-correct 300) and `split_fit_heldout.py --family gemma4-e4b`
(pinned FIT_FRAC=0.40, seed=20260707) both ran cleanly, no errors/OOM. Split
result: confab fit=79/held_out=121, known_correct_answered fit=120/held_out=180.
Both held-out counts are BELOW the locked G0 `reused_pool_powered` floor
(>=150 held-out confab, >=250 held-out known_correct_answered -- gates.yaml
applies the SAME bar to gemma's fresh mine, not just the reused-pool
families). Arithmetic is clean, not a bug: held-out fraction is ~60% at this
FIT_FRAC, so 200confab*0.605=121 and 300known*0.60=180 -- exactly what came
out; the script's own default targets simply cannot reach 150/250 at the
pinned split fraction.

**Adjudicated by lead (2026-07-24), authorized-knob tuning toward the
registered bar, no revision needed:** the G0 held-out power floor (150/250)
is the registered constant; `--target-confab`/`--target-known-correct` are
unregistered operational knobs, not part of the locked instrument, so raising
them to reach the already-fixed floor is not a goalpost move. Re-running with
`--target-confab 280 --target-known-correct 450` (margined above the
computed minimums 248/417 to survive hit-rate variance).

This first mine's `eval_rows.jsonl` and `split_manifest.json` (200/300
targets) are SUPERSEDED and non-evidentiary -- no behavioral outcome
(jlens_profile, extract_anchor, calibrate_dose, or contrast) was ever derived
from them; the split was never consumed by anything downstream. The re-mine
resumes from the same cached `pool_generations.jsonl` (script's own
`read_existing_rows` dedup-by-row_key resume, confirmed by reading the
script) rather than re-generating the already-mined 200/300 rows from
scratch -- it only spends GPU time scanning additional candidates to reach
the new targets.

### 2026-07-24 -- norm-scaled dose-ladder revision LANDED as R2 (signed, user-ratified) -- read AMENDMENT.md directly, this is a pointer only

AMENDMENT.md now carries "Mid-run revision R2 (2026-07-24, lead-drafted,
user-ratified): norm-scaled dose ladder" as a signed revision, superseding
the "being drafted" framing in the prior NOTEBOOK entry below. Read that
section directly for the full mechanism, sanity check, and scope -- not
re-derived here. Confirmed by direct read (not taking the lead's summary as
source, per project discipline): `calibrate_dose.py` is now v2 (RATIO_LADDER
= [0.100, 0.153, 0.235, 0.361, 0.554, 0.850, 1.304, 2.000], normalized by
each family's own per-layer median anchor L2 norm computed at runtime from
`anchor_extract.safetensors`; `--doses` remains as an explicit v1 absolute
escape hatch, unused by default). Repinned twice (43aeaecb, then a3ed0562
comment-date fix), both audited by the lead. Scope per AMENDMENT.md: (a)
llama/mistral re-run calibrate_dose under v2 once gemma completes through its
held-out outcome -- their v1 NOT-RUN dispositions stay on record as evidence
about the original registration, extractions/directions/gate-fits carry
forward unchanged; (b) gemma calibrates under v2 from the start (this
family's first calibration, no v1 history to compare against); (c) qwen3.5-4b
stays deferred, outside this revision's scope.

### 2026-07-24 -- qwen3.5-4b j-space DISPOSITION: DEFERRED (back-burnered by user, not a G0 stop)

**Killed run.** `jlens_profile.py --family qwen35-4b` was terminated by the lead's
direction (PID 922336 + wrapper 922335) after logging only 1 of 10 depth-sweep
points (hs_index=1) in 6h13m wall clock -- that single point cost 20172.8s
(~5.6h), ~20x the LAUNCH-PLAN's 2-3h whole-stage budget. Root cause (read-only
diagnostic, no pinned-file edit): the log's first computation line reads "The
fast path is not available because one of the required library is not
installed. Falling back to torch implementation" -- Qwen3.5-4B's hybrid
linear/full-attention layers (config.text_config.layer_types alternates the
two) fall back to a slow plain-PyTorch path without the optional
flash-linear-attention/causal-conv1d packages. Confirmed genuine ongoing
compute, not a hang, via steady 104% CPU on the actual python child process and
non-zero (30-40%) GPU utilization the entire run. `jlens.layer_profile()` has
no resume-from-partial logic, so a restart always begins again from
depth_sweep[0]; the completed hs_index=1 result is durably checkpointed at
`analysis-committed/qwen35-4b/layer_profile.json` but is a PARTIAL/INCOMPLETE
artifact, not usable as evidence. `families/qwen35-4b.yaml`'s
`band_selection.status` remains `not_yet_run` (the write-back only fires at
the end of a completed sweep, which never occurred).

**Disposition: DEFERRED (back-burnered), not NOT-RUN/G0 stop.** This is a
distinct category from llama/mistral's G0 dose-viability stops -- no gate
fired, no dose was ever calibrated; the profile stage itself couldn't
complete in budget. User decision (2026-07-24 morning) is to back-burner this
family rather than force a decision now. Three restart paths remain on the
table for a future signed revision or lab-notebook entry: (a) a smaller
first-pass `--n-prompts` (200-300), which the LAUNCH-PLAN itself pre-flagged
as a contingency but which still costs hours not minutes at linear scaling,
not the sub-hour the local-smoke-scale reference implied; (b) installing
flash-linear-attention/causal-conv1d and retrying n=1000, CAVEATED that the
J-lens double-backward JVP machinery may not be supported by the fused
kernels at all, making the observed fallback the only correct path rather
than a fixable slowdown -- a cheap CPU/1-layer smoke should answer this
before committing further GPU time; (c) accepting a NOT-PROFILED disposition
for this family this round. None of these paths were taken; qwen3.5-4b is
simply held, dependency-install path documented for whoever picks it back up.

### 2026-07-24 -- norm-scaled dose-ladder signed revision being drafted (context, not yet in effect)

The lead is drafting a signed revision to re-run llama-3.2-3b and
mistral-7b-v03's dose calibration on a norm-scaled ladder rather than the
current fixed absolute ladder ([25,50,...,200], calibrated on Qwen3-4B's own
residual scale). Their extraction/build_directions/gate_fit artifacts remain
valid and reusable across this revision (only calibrate_dose + downstream
would re-run); expect a return to those two families after gemma4-e4b's
pipeline completes. Qwen3-4B's own reference anchor L2 norms were recovered
for comparison: hs23 66.7, hs26 124.8, hs29 209.2, hs34 423.8 -- its own
SELECTED doses sat at 0.37-0.60x the median norm at each layer, with a usable
band roughly 0.2-1.0x median norm. Under the old fixed absolute ladder,
llama's mid-band doses translated to 1.8-14.6x its own (much smaller) median
norms -- entirely outside the 0.2-1.0x usable band that worked for Qwen3-4B.
This closes the physics of both G0 dose-viability stops observed so far: the
ladder was never wrong in absolute terms, it was calibrated for one family's
residual scale and applied unchanged to others whose scale differs by an
order of magnitude. This is background for a FUTURE signed revision only --
no ladder value has been changed in this run, and none of llama/mistral's
G0 dispositions above are altered by this note.

### 2026-07-23 -- mistral-7b-v03 DISPOSITION: NOT-RUN (G0 dose-viability stop)

**Pre-calibration anchor L2 norm read (lead, computed from extraction
safetensors before calibrate_dose ran, per the standing "free early
viability read" rule).** hs12 3.35, hs15 4.43, hs19 8.00, hs30 (late) 21.46
(300-row samples). ALL FOUR layers -- including the late-reference arm --
sit below the ladder floor (dose 25), a stronger and more uniform
below-floor pattern than llama's (which had its late arm above floor at
30.4). This strongly predicted the same units-mismatch dose-viability stop,
in advance of calibrate_dose running.

**calibrate_dose.py ran to completion cleanly** with the repinned `--fresh`
flag (same bugfix as llama): 32/32 (layer,dose) cells (mid-band
hs12/hs15/hs19 x late hs30, all 8 ladder doses [25...200]), ~35 min GPU
time, readback within tolerance at every single cell (write mechanism
confirmed accurate, `frac_readback_within_tol == 1.0` on all 32 cells).
Result: `all_midband_have_usable_dose: false`, `all_layers_have_usable_dose:
false` -- no dose at any of the 4 layers clears the locked usability bar.
Unlike llama (which had one near-miss cell at 0.125 collapse), mistral's
collapse pattern is close to total: `collapse_rate_on_dosed` is 1.0 at
every single (layer, dose) cell except one (hs30/late at dose=25, where
collapse is 0.0 but `confab_tighten` is still 0.0, so still unusable).
`confab_tighten.rate` is 0.0 at every single cell across all layers and
doses -- the write never registers a usable caution effect anywhere on the
ladder for this family. `known_correct_cost_control.rate` is pinned at
0.125 (1/8) at every cell regardless of dose or layer, consistent with one
fixed known-correct FIT row failing independent of the intervention. Full
per-cell numbers: `analysis-committed/mistral-7b-v03/dose_calibration_summary.json`.

**Bug-vs-genuine-behavior check (read-only diagnostic, scratchpad-only, not
part of the pinned instrument, no pinned-file changes).** Wrote a throwaway
script reusing `pipeline.py`'s own `render`/`run_pass_fixed`/
`setup_hook_from_path`/`compute_gate_decisions` verbatim to print RAW
generated text for 2 fired confab rows at hs12 (the lowest-norm mid-band
layer), doses 25 and 50 (readback confirmed accurate: 25.00-25.01,
50.01-50.01 respectively; `strength = dose/sigma_c` computed as ~120-240,
several times larger than the strength that produces the same collapse
pattern in llama at the same nominal doses, consistent with mistral's even
smaller sigma_c/anchor-norm scale at these layers):
- BASE (undosed): clean well-formed JSON on both rows, e.g. `{"answer": "I
  don't have the ability to definitively say that biodegradable materials
  are the most effective solution...", "response_confidence": 0.3}`.
- DOSED at 25 (the ladder's lowest dose): immediate collapse into repeated
  fragment loops from the very first tokens -- `{ answer answeratr -
  -atr -atratratratratrat...` -- no coherent JSON structure or semantic
  content survives even at the ladder floor, unlike llama where the
  semantic caution direction read through briefly before collapsing.
- DOSED at 50: same pattern, different repeated fragment (`aughteropter
  opteropteropter...`).

This confirms genuine over-steering / total repetition-collapse from the
very first dose on the ladder, not a detection false-positive or a
hook/readback bug -- the write mechanism is accurate (readback matches
target to within fractions of a unit at every cell) but the model cannot
sustain ANY coherent generation under this write at ANY point on the
locked ladder, worse than llama's partial degradation-then-collapse
pattern. Consistent with the anchor-norm prediction above: a units
mismatch between the ladder (calibrated on Qwen3-4B's residual scale) and
mistral-7b-v03's own (much smaller) residual scale at these layers, not a
per-family tuning failure. No off-ladder dose was tried and none of the
min-confab-rate/layer/ladder parameters were touched -- all locked per the
signed instrument; ladder extension is a signed-revision question the lead
is lifting to the user separately, out of scope for this run.

**Formal G0 gate firing on record.** `run_contrast.py --family
mistral-7b-v03 --mode smoke --n-rows 8` invoked and exits with:
`ValueError: [mistral-7b-v03] calibration summary says not all mid-band
layers have usable doses` (raised at `load_midband_selected_doses`,
run_contrast.py line 80) -- the instrument's own designed gate, not a
workaround. Identical failure mode and identical gate-firing mechanism as
llama-3.2-3b.

**Note on family substitution provenance.** This family's YAML already
records the pre-existing substitution (Ministral-3-3B -> Mistral-7B-
Instruct-v0.3, due to a conditional-gen class issue) and the doubt-snap
reused late-site fit was already a TRUE BEHAVIORAL NULL there
(`doubt_snap_fit_peak_clean_tighten: {rate: 0.0, dose: 30.0, known_cost:
0.0118}`) -- consistent with this family also failing to produce a usable
intervention effect in the predecessor experiment at its frozen late site,
independent of this experiment's fresh mid-band mining.

**Disposition:** NOT-RUN (G0 dose-viability stop) -- CONFIRMED by lead
adjudication, mirroring llama-3.2-3b's confirmed disposition pattern. Two
of two families run so far have hit the identical G0 stop; qwen3.5-4b and
gemma-4-e4b remain to test whether this is family-general or specific to
the two `torch_dtype`-heterogeneous / smaller-residual-scale families run
first per the locked order.

**Cross-family observation (lead, added at adjudication).** Mistral is
qualitatively WORSE than llama at the ladder floor -- zero semantic
read-through even at dose=25 (immediate token-loop collapse) vs llama's
brief coherent refusal before collapsing. This is consistent with mistral
having the smallest sigma_c of the two families run so far, and therefore
the largest effective strength (`dose/sigma_c`) at any given nominal dose
on the shared ladder. The resulting cross-family strength gradient --
qwen3-4b in-range (ladder was calibrated on it), llama roughly 2-4x over,
mistral roughly 5-10x over -- is the central design input for the
norm-scaled-ladder question the lead is lifting to the user separately;
not acted on here, ladder stays locked as signed.

### 2026-07-23 -- llama-3.2-3b DISPOSITION: NOT-RUN (G0 dose-viability stop, adjudicated)

**calibrate_dose.py ran to completion cleanly** with the repinned `--fresh`
flag: 32/32 (layer,dose) cells (mid-band hs17/20/23 x late hs26, all 8
ladder doses [25...200]), ~24 min GPU time, readback within 5%+0.5 tolerance
at every single cell (the write mechanism itself is not the problem).
Result: `all_midband_have_usable_dose: false`, `all_layers_have_usable_dose:
false` -- no dose at any of the 4 layers clears the locked usability bar
(`frac_readback_within_tol == 1.0` AND `collapse_rate_on_dosed == 0.0`
exactly AND FIT confab `clean_tighten` rate `>= 0.5`). Best case across the
whole ladder: hs23 dose=25 at 1/8 (0.125) collapse, still nonzero. Full
per-cell numbers: `analysis-committed/llama-3.2-3b/dose_calibration_summary.json`.

**Bug-vs-genuine-behavior check (read-only diagnostic, scratchpad-only, not
part of the pinned instrument, no pinned-file changes).** Wrote a throwaway
script reusing `pipeline.py`'s own `render`/`run_pass_fixed`/
`setup_hook_from_path`/`compute_gate_decisions` verbatim to print RAW
generated text for 2 fired confab rows at hs17, doses 25 and 100:
- BASE (undosed): clean well-formed JSON, e.g. `{"answer": "It depends on
  the severity and type of disaster...", "response_confidence": 0.6}`.
- DOSED at 25 (the ladder's lowest dose): readback confirms the write lands
  at the correct magnitude (25.00-25.01); the semantic caution direction
  DOES read through (`{"answer" isUnknown I don't know the answer" ...`) but
  then collapses into runaway `unable unable unable...` repetition, hitting
  the 200-token cap without terminating naturally.
- DOSED at 100: worse degradation into token salad (`пока oren oren
  oren... impossible impossible...`).

This confirms genuine over-steering / repetition-collapse, not a detection
false-positive or a hook/readback bug -- the write mechanism is accurate and
the direction is semantically correct, but the model cannot sustain
coherent generation under this write at ANY point on the locked ladder.

**Root-cause corroboration (lead, independent, read-only).** Anchor L2 norms
computed directly from the extraction safetensors (300-row samples, tight
spread): hs17 13.7, hs20 17.2, hs23 21.9, hs26 30.4. The ladder floor (dose
25) EXCEEDS the entire typical hidden-state norm at all three mid-band
layers -- a UNITS MISMATCH between the ladder (calibrated on Qwen3-4B's
residual scale) and llama-3.2-3b's own residual scale, not a per-family
tuning failure. This exactly predicts the diagnostic's observed pattern
(semantics read through at the lowest dose, then immediate repetition
collapse, worse at higher doses). No off-ladder dose was tried and none of
the min-confab-rate/layer/ladder parameters were touched -- all locked per
the signed instrument; ladder extension is a signed-revision question the
lead is lifting to the user separately, out of scope for this run.

**Formal G0 gate firing on record.** `run_contrast.py --family llama-3.2-3b
--mode smoke --n-rows 8` invoked and exits 1:
`ValueError: [llama-3.2-3b] calibration summary says not all mid-band
layers have usable doses` (raised at `load_midband_selected_doses`,
run_contrast.py line 80) -- the instrument's own designed gate, not a
workaround.

**DISPOSITION (adjudicated lead+drafter 2026-07-23): NOT-RUN, G0
dose-viability stop.** Matches gates.yaml's pre-anticipated category
verbatim ("A family that fails G0 after bounded debugging... is recorded
as NOT-RUN with the explicit blocker and excluded from the cross-family
denominator -- neither a PASS nor a FALSIFIER hit for that family"),
structurally the same category as `doubt-snap-cross-family-confirmatory`'s
own late-site dose-viability stops. llama-3.2-3b is excluded from the
cross-family roll-up denominator; proceeding to mistral-7b-v03 next per the
locked run order.

### 2026-07-23 -- llama-3.2-3b: extraction + mid-band fit/gate results; calibrate_dose.py pinned-code bug found, fixed, repinned

**extract_anchor.py** (GPU): 2956/2956 rows extracted in 112.8s, safetensors
139.6M, `analysis/llama-3.2-3b/anchor_extract_manifest.json` `complete: true`.
Ran with the two render() fixes below (PYTHONPATH + vendored shim).

**build_directions.py --verify-reproducible** (CPU): reproducibility check
PASS at all three mid-band candidate layers (hs17, hs20, hs23). `cos_u_d_u_p`
near-orthogonal at every layer (0.038-0.040), `cos_caution_dir_c_hat` >=0.985
(orthogonalized caution direction still highly aligned with the raw caution
axis, as expected). Standardization stats (`mu_d`/`sigma_d`/`mu_c`/`sigma_c`)
written per layer to `build_manifest.json`.

**gate_fit.py** (CPU): Youden-J frozen tau at all three mid-band layers, AUC
(`neg_z_d`, FIT confab vs FIT known_correct_answered) well above the 0.90 G0
floor at every candidate:
- hs17: AUC 0.9993, tau -0.3755, tpr 0.9931, fpr 0.0090 (tp 577 fn 4 fp 2 tn 220)
- hs20: AUC 0.9991, tau -0.3401, tpr 0.9931, fpr 0.0090 (tp 577 fn 4 fp 2 tn 220)
- hs23: AUC 0.9990, tau -0.2667, tpr 0.9914, fpr 0.0090 (tp 576 fn 5 fp 2 tn 220)

**calibrate_dose.py pinned-code bug (found, lead-fixed, repinned).** First
invocation crashed immediately, before any GPU dose-ladder generation:
`AttributeError: 'Namespace' object has no attribute 'fresh'` at line 123
(`if args.fresh and ckpt_path.is_file():`) -- the script's own argparse block
(lines 204-209) never defined a `--fresh` flag, despite the script's own
comment at line 118 documenting one ("Resume assumes the same --doses ladder;
use --fresh to restart") -- an authoring omission, not a design gap;
`run_contrast.py`'s argparse correctly has `[--resume | --fresh]`. Not an
environment issue (100% reproducible on any family/args, before any GPU
work). Reported to lead with exact line numbers and a minimal one-line
proposed diff; lead independently verified, applied the diff verbatim (one
`parser.add_argument("--fresh", action="store_true", ...)`, no other line
changed), smoke-checked `--help` shows the flag, and ran the governed repin:
`calibrate_dose.py` `b817c12f...` -> `0579f52891b1...` (reason recorded in
`instrument.repins`). Dose ladder, gates, and resume logic untouched.

### 2026-07-23 -- launch G0 crash diagnosis: two dead render() imports, one PYTHONPATH fix + one vendored shim (CPU-only diagnosis, no GPU work counted toward outcome; pending lead repin before relaunch)

llama-3.2-3b's `extract_anchor.py` crashed at G0 (`model_lib.py`'s `render()`)
with two sequential `ModuleNotFoundError`s, both caused by an UNRELATED prior
main-branch reorg archiving files this experiment's pinned `model_lib.py`
imports by bare module name via a hardcoded `sys.path` entry
(`PROBE_DIR = .../experiment/phase1/probe`). Neither import target still
lives at that path.

1. **`backends.render_probe_prompt`** -- `experiment/phase1/probe/backends.py`
   was archived; the archive copy is a dead compat wrapper pointing at a
   nonexistent `experiments/common/phase1_probe/`. FIXED via environment only
   (no code/file changes): `PYTHONPATH=/home/profsynapse/code/
   Epistemic-Humility-Research/experiments/common/knowledge_probe` added to
   every pipeline invocation. That directory's `backends.py` is the live,
   actively-maintained successor with an IDENTICAL
   `render_probe_prompt(tokenizer, system_prompt, question, *,
   enable_thinking, mode=None)` signature (verified by CPU-only import +
   `inspect.signature`), explicitly documented there as the shared render
   path for "the hidden-state harness" too.
2. **`amendment_ah_stage0_extract.load_baseline_system_prompt`** -- NOT
   env-fixable: the only surviving copy is archived
   (`archive/experiment/phase1/probe/amendments/`), hardcodes a config
   filename (`experiments/doubt-regulated-caution/
   phase3_ac_doubt_coupled_intervention.yaml`) that no longer exists at that
   path (renamed via `git log --follow`: moved by commit 6b66536a, then
   dropped the `phase3_` prefix by commit d55b7d26 -- `git show d55b7d26` on
   that file confirms the `prompt:` block itself is untouched in that patch),
   and its sibling archived `path_compat.py` is independently broken (its
   `repo_root()` heuristic depends on `experiment/phase1/eval/scorers.py`,
   itself archived by the same reorg that broke this experiment's own
   `grader.py` `EVAL_DIR`, already fixed by vendoring `scorers.py` at
   sign-time -- see the entry below). The live successor `path_compat.py`
   (`experiments/common/readouts/`) fixes the `repo_root()` check but drops
   the `phase1_probe_dir()`/`phase1_eval_dir()` names the archived script
   imports -- an API mismatch on top of the dead filename, not just a stale
   search path. Lead-adjudicated 2026-07-23: vendored a minimal shim,
   `amendment_ah_stage0_extract.py`, into this experiment directory (sibling
   convention, matching the `scorers.py` precedent) that supplies ONLY
   `load_baseline_system_prompt()`, reading the renamed live yaml
   (`experiments/doubt-regulated-caution/ac_doubt_coupled_intervention.yaml`
   `prompt.system`) and FAIL-CLOSED asserting its sha256 equals a hardcoded
   `_EXPECTED_SHA256` (`81a04a99827ade21b9d5bd1832c2012429d196f96e604238a4b927701ca58e3c`)
   computed at shim-authoring time -- a future edit to that yaml's
   `prompt.system` will raise instead of silently changing what every
   family's generation renders. Smoke-tested both the happy path and the
   fail-closed mismatch path (CPU-only, deliberately corrupted the expected
   hash in-process to confirm it raises).

   **Cross-check (required before trusting this shim for the reused frozen
   late-site arm):** loaded `experiments/doubt-snap-cross-family-
   confirmatory/render.py`'s hardcoded `BASELINE_SYSTEM_PROMPT` literal
   directly (module import, not hand-transcribed) and compared byte-for-byte
   against the shim's yaml-sourced string: **IDENTICAL** -- same sha256
   `81a04a99827ade21b9d5bd1832c2012429d196f96e604238a4b927701ca58e3c` for
   both. This confirms the render convention this shim restores is the same
   one doubt-snap's frozen late-site directions (`c_hat`/`u_d`/`gate_fit`,
   reused verbatim by this experiment) were actually fit under -- resolves
   AMENDMENT.md "Open questions at sign" #5 (render/anchor reconciliation)
   affirmatively for the system-prompt component; anchor position and
   `enable_thinking` convention are separately unchanged (ported verbatim in
   `model_lib.py`/`gen_lib.py`, not touched by this fix).

No pinned-byte edits: `model_lib.py` and every other pinned instrument file
are unmodified. The new shim file is NOT yet part of the signed pin set --
lead is running a governed repin to add it before any GPU relaunch. Did NOT
restart `extract_anchor.py` or any other GPU work pending that repin
confirmation.

### 2026-07-23 -- sign-time revision: primary reframe + doubt-snap reuse (CPU-only, no GPU, NOT signed)

Lead-directed, user-approved structural revision of the draft, after
`doubt-snap-cross-family-confirmatory` RESOLVED (2026-07-12, confirmatory not
promoted -- every launched cell stopped at G0 FIT dose-viability at the late
0.94-depth site; gemma4_e4b_it never behaviorally launched). All predecessor
docs and doubt-snap committed artifacts were read from the canonical `main`
checkout (this worktree is 677 commits behind main and does NOT contain them).

Changes made:
- **Primary endpoint reframed to ABSOLUTE mid-band actuation.** New per-family
  primary gates: G1 mid-band held-out confab clean_tighten floor, G2 mid-band
  known-correct not_well_formed_correct cost cap. The late-reference arm is
  DEMOTED to a non-gating secondary descriptive comparator; the draft's relative
  G1/G2 contrast and the G3 late-viability floor (0.40/0.30) are DROPPED.
  gates.yaml, AMENDMENT.md (Prediction/Falsifier/Gates + new "Gates ->
  derivation" and "Open questions at sign"), experiment.yaml, and
  run_contrast.py/cross_family_rollup.py updated.
- **Gate numbers with written derivation (adjudicated lead+user 2026-07-23,
  conservative option chosen).** G1 = clean_tighten >= 0.50, Wilson lower > 0.40
  (below the weaker same-lineage mid-band held-out point ~0.66 Qwen3.5-4B / 0.89
  Qwen3-4B, far above the dead late-site region <= 0.33; Wilson-lower 0.10 below
  the point, mirroring qwen35-4b-midband-heldout's gate shape). The stricter
  0.60/0.50 alternative was offered and NOT elected. G2 = not_well_formed_correct
  <= 0.05, Wilson upper < 0.10 (inherits qwen35-4b-midband-heldout's cost gate;
  both Qwen substrates cleared at 0.035/0.039).
- **Consumes doubt-snap artifacts, hash-pinned.** Each `families/<slug>.yaml`
  gained a `reuse.doubt_snap` block: committed-artifact relative paths + sha256
  (split_manifest, build_manifest, c_hat, u_d, random_direction, gate_fit,
  dose_fit, g0_prep_summary), Modal volume + path, frozen late-site params
  (block/hs_index, tau_frozen, mu_c/sigma_c/mu_d/sigma_d), FIT/held-out counts.
  New `materialize_reused_rows.py` replaces mine_eval_pool.py + split_fit_heldout.py
  (retained fallback-only) for the four reused families; family_config.py gained
  reuse accessors; build_directions/gate_fit scoped to mid-band only (late-site
  direction/gate reused frozen, not refit); calibrate_dose sweeps mid-band AND
  the late site (option B -- fresh late-site DOSE, frozen late direction/gate);
  pipeline.py's compute_gate_decisions/run_layer branch the late arm to the
  frozen reuse artifacts. Late reference site is now DEFINED as doubt-snap's
  frozen block (llama 25 / mistral 29 / qwen35-4b 29 / gemma 39; hs_index+1 =
  26/30/30/40 -- coincidentally equal to this experiment's own 0.9444*L estimate).
- **Gemma-4-E4B Modal fallback pre-authorized** (LAUNCH-PLAN.md + AMENDMENT.md):
  local first, Modal fallback for the Gemma cell only on a G0 OOM, NOT-RUN only
  if Modal also fails.

Two artifact gaps found while pinning (flagged as open questions, not guessed
around): (1) NO family has a calibrated late-site dose to reuse (all doubt-snap
cells `selected_dose: null`); (2) gemma4_e4b_it was never behaviorally launched
-- FIT prep is committed but no dose_fit.json/modal_status.json, late gate AUC
0.9472 (weakest), held-out known 251 (~1-row margin). Plus the branch-behind-main
dependency (open question #0) and the Modal-volume row-text retention question
(proven only for the qwen35_4b cell).

**Resolved at finalization (2026-07-23, lead+user).** Gap (1): option (B)
adopted -- the late-site DOSE is calibrated fresh with the mid-band ladder for
all four families (frozen late direction/gate still reused verbatim); see
AMENDMENT.md open question #2. Gate numbers adjudicated (conservative option):
G1 0.50/0.40, G2 0.05/0.10. Branch-behind-main resolved by merging `main`
(submodule pin -> 901dbe8, which already contains `feature/runlog`; no pointer
bump needed). Modal retention checked: llama/mistral/qwen35_4b row text PRESENT,
gemma ABSENT (never launched -> pre-authorized Modal fresh-mine fallback).

**Final pre-sign pass (2026-07-23, lead+user).**
- GEMMA FRESH MINE (adjudicated): gemma's pool/split cannot be reused (row text
  absent), so `pool_provenance: fresh_mine` for gemma ONLY -- mine_eval_pool.py +
  split_fit_heldout.py run fresh on gemma's own checkpoint; reuse provenance for
  the pool is LOST and recorded. The frozen late-site direction/tau/
  standardization stay reused verbatim + hash-pinned, applied to the fresh rows
  as a frozen operating point (qwen35-4b-midband-heldout pattern); late dose
  still fresh (option B). G0 reuse-integrity is scoped per family via
  `family_config.integrity_artifact_names`: reused-pool families verify 8
  artifacts (incl. split_manifest); gemma verifies ONLY the 5 frozen late-site
  artifacts (build_manifest/c_hat/u_d/random_direction/gate_fit). Verified by
  running materialize_reused_rows.py --family gemma4-e4b: 5 late-site hashes
  match, no split copied, rc=0. Other three families' G0 untouched.
- VENDOR SCORERS (adjudicated): the merge pulled main commit 21cd5c50 which
  archived experiment/phase1/eval/scorers.py, breaking grader.py's hardcoded
  EVAL_DIR. Vendored scorers.py INTO the experiment dir (sibling convention, no
  external dependency). BYTE-IDENTITY: archived source
  sha256 75e690f583d83d654cb88a3b066b39acb7e9e1b954c9d5677d4b887d6c30905a; the
  vendored file is a provenance header (891 bytes) + that source VERBATIM, so its
  post-header body sha256 == 75e690f5... (byte-identical), and the full vendored
  file sha256 = 1b3eda5d8d68c9184674f092805278505c5cd2065a21ffe7ec348e9ea5a00c37.
  grader.py now imports the local copy (EVAL_DIR dropped). Import smoke:
  `run_contrast.py --help` and `calibrate_dose.py --help` both exit 0, proving
  the grader -> gen_lib -> pipeline -> run_contrast/calibrate_dose chain resolves.

Verification (CPU-only): `bin/exp validate` OK (after moving the not-yet-present
doubt-snap `inputs` paths into a comment, since validate existence-checks
inputs and this branch lacks main's content); `py_compile` OK on all scripts;
`--help` OK on the no-torch scripts (materialize_reused_rows, cross_family_rollup,
build_directions, gate_fit) and family_config reuse accessors resolve all four
families' pins. Full `--help` of the torch+MechInterp scripts needs the project
`unsloth_env` (pre-existing, unchanged by this revision). Did NOT sign, did NOT
run any model/GPU/Modal work, did NOT touch the 3090 or the synaptic-tuner
submodule. Predictions scoreboard left blank for the lead to fill at sign.

### 2026-07-09 -- tokenizer/config verification pass (CPU-only, no GPU work run)

Resolved LAUNCH-PLAN.md decision points #3 (multimodal config nesting), #4
(EOS lists + layer counts), and #5 (Gemma system-role support) by
downloading ONLY `config.json`/`tokenizer_config.json`/
`special_tokens_map.json`/`generation_config.json`/`chat_template.jinja`
per checkpoint via `hf_hub_download` (never `snapshot_download`, no
`*.safetensors`/`*.bin` touched) for all four checkpoints:
`unsloth/Llama-3.2-3B-Instruct`, `mistralai/Mistral-7B-Instruct-v0.3`,
`Qwen/Qwen3.5-4B`, `google/gemma-4-E4B-it`. All four repos were ungated
(no 403s). Fetch script and cached files live under this experiment's
gitignored `analysis/tokenizer-config-verify/` (fetch script:
`fetch_configs.py`; not tracked, upstream artifacts only).

Also ran a small number of meta-device (`torch.device("meta")`, no weight
download, no GPU) `AutoModelForCausalLM`/`AutoModelForImageTextToText`
construction checks against the downloaded configs to directly test the
multimodal loader-class questions LAUNCH-PLAN.md flagged as unverified
(`attn_implementation="eager"` acceptance, and whether the vision/audio
towers are structurally part of the resolved model class) -- no weights
were downloaded or instantiated with real data for this.

Confirmed: Llama's `n_hidden_layers: 28` guess, Mistral's/Qwen3.5's EOS
guesses, and Qwen3.5's `nested_text_config: true` + `enable_thinking`
kwarg. Filled in previously-`null` layer counts for Mistral (32), Qwen3.5
(32, nested), and Gemma4 (42, nested), each with a recomputed
`round(0.9444 * n_hidden_layers)` late-reference estimate.

Corrected two factually wrong guesses for `google/gemma-4-E4B-it`: (1) its
EOS/end-of-turn token is `<turn|>` (per `tokenizer_config.json`'s own
`eot_token` field and the live chat template), not the classic Gemma
2/3 `<end_of_turn>` the draft assumed; (2) it DOES have a native
`enable_thinking` kwarg (gates a `<|think|>` token injection), contrary to
the draft's "Gemma has no thinking-toggle kwarg" claim. Also resolved
decision point #5 in the affirmative (its template gives `system` its own
turn, not folded into the first user turn -- the flagged concern was
unfounded for this checkpoint) and found it is trimodal (vision + audio
towers, not vision-only) -- both AMENDMENT.md's family table and
`families/gemma4-e4b.yaml` were updated to flag these corrections
prominently. Full detail in each `families/<slug>.yaml`'s per-section
"VERIFIED"/"CORRECTED" notes and LAUNCH-PLAN.md's revised decision points
#3/#4.

Did NOT touch decision point #1 (G3 floor) or the VRAM GB estimates in the
feasibility table (lead-kept); did NOT sign, did NOT run any model
generation, did NOT touch the local 3090.

### 2026-07-09 -- draft scaffold written (no GPU work run)

Scaffolded via `bin/exp new --type steer-cell j-space-cross-family-layer-contrast`
on branch `exp/j-space-cross-family-layer-contrast` (worktree
`/home/profsynapse/code/ehr-worktrees/jspace-cross-family`). Read the six
governed docs the lead named (two Qwen3-4B J-space predecessors, the
localization diagnostic + its NOTEBOOK.md, Amendment Z, and the
doubt-gated-caution-tighten gate-and-snap origin) before writing any code, per
the KG-search-first / read-before-you-cite rule.

Wrote per-family config YAMLs (`families/{llama-3.2-3b,ministral-3-3b,qwen35-4b,gemma4-e4b}.yaml`)
transcribing Amendment Z's exact checkpoints, run order, and per-family
loader/VRAM risk notes verbatim, with `band_selection` and `doses` left
`not_yet_run`/`not_yet_calibrated` (no profile or calibration has executed).

Ported the two Qwen3-4B J-space experiments' bespoke scripts into
family-parameterized versions (`mine_eval_pool.py`, `split_fit_heldout.py`,
`jlens_profile.py`, `extract_anchor.py`, `build_directions.py`,
`gate_fit.py`, `calibrate_dose.py`, `pipeline.py`, `run_contrast.py`,
`cross_family_rollup.py`), plus `family_config.py` as the single read/write
path for each family's YAML (no other script hardcodes a checkpoint, hidden
size, or layer index) and `model_lib.py` porting Amendment Z's own loader
hardening (`AutoModelForCausalLM` -> `AutoModelForImageTextToText` ->
`AutoModelForVision2Seq` fallback chain, `config.text_config` nesting).
`gen_lib.py` and `grader.py` are the generation-contract and grading code,
generalized (EOS resolution) or ported unchanged (grading is already
model-agnostic).

Verified every script with `py_compile` and `--help` (CPU-only, unsloth_env
conda python) -- no model loads, no GPU touched, per the lead's explicit
instruction that the local 3090 is busy with another experiment's
confirmatory and must not be touched at all.

Did NOT run `bin/exp sign` (prediction/falsifier/gates need the lead's
review and the scoreboard rows need the lead + user's calls first). Did NOT
run any HF pull, Modal launch, or GPU work. See `LAUNCH-PLAN.md` for the
per-family run order, GPU-time estimates, and the decision points that need
to come back to the lead before this experiment can launch for real.
