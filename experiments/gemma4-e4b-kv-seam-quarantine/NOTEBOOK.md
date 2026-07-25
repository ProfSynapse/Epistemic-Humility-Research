# Gemma-4-E4B KV-sharing seam: is the mid-band null a quarantine artifact? notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

### 2026-07-24 (latest) — pre-registration re-grounded on clean activations; shallow ladder added; still unsigned, still no GPU

Lead pass. Everything below is CPU-only recomputation over already-committed
artifacts (no GPU, no generation, no model load). Two user decisions drove it:
extend the arm set with the full shallow depth ladder `hs15/hs18/hs20/hs23`, and
land the pre-registration rewrite together with the two instrument repairs as a
single PR.

The pending Tier 1 revision
(`docs/protocols/2026-07-24-jspace-gate-and-instrument-revision.md`, "Open
blockers" #1) requires this experiment's `question` / `prediction` / `falsifier`
to be rewritten off the withdrawn KU AUC and the corrupt `clean_tighten` before
it can be signed or run. That is what this entry records the evidence for.

**F1 — `clean_tighten` is sharp on gemma. The metric-vacuity hypothesis is dead.**
`gen_lib.grade_clean_tighten` requires the literal substring `"i don't know"` in
the parsed answer, plus well-formed JSON, single answer key, clean trailing text,
natural termination, non-degenerate. A hard-coded English string match is exactly
the shape that produced the KV-seam vacuity (both sides running the broken path),
so it was checked rather than assumed. Run over the parent's committed
`analysis/gemma4-e4b/pool_generations.jsonl` (3,786 undosed gemma generations):

- fires on **1662 / 1663** natural refusals (0.999) — gemma phrases refusals as
  `{"answer": "I don't know the answer", ...}`, which the grader catches;
- fires on **0 / 1393** undosed confab rows (no false positives).

So the grader has both sensitivity and specificity on this substrate. Any null
this experiment measures is a null about the model, not about the metric. This
check had never been run for gemma and is recorded here so it is not re-litigated.

**F2 — numeric fingerprint confirming the corrupt provenance of the parent's
gemma write arm.** `AMENDMENT.md:637` of the parent already records that the
gemma write null "was fit on corrupt activations and is therefore
uninterpretable, not negative." Confirmed here independently by median anchor L2
norm, which is a fingerprint of the extraction the directions and doses were
built from:

| site | median norm in parent's `dose_calibration_summary.json` | quarantined (corrupt) extract | clean extract |
|---|---|---|---|
| hs34 | 120.20 | **120.20** | 154.08 |
| hs38 | 125.51 | **125.51** | 156.06 |
| hs40 | 117.57 | **117.57** | 142.35 |
| hs42 | 281.34 | **281.34** | 236.35 |

The calibration norms match the quarantined file exactly, and every differing
layer is `>= hs25` — precisely the KV-starved region. `build_manifest_layers.json`
independently carries `extract_manifest_sha256: a13a9cf7…`, the corrupt manifest.
Directions (`u_d`, `c_hat`), gate standardization (`mu_d`, `sigma_d`, `tau`), and
absolute dose targets were therefore all corrupt-derived. No new correction is
owed — the parent's record is already right — but the fingerprint is now concrete
rather than inferred from a hash alone.

**F3 — the KU gate's known-correct fire rate is strongly depth-dependent on clean
activations, and this is what breaks the draft's G2 argument.** Recomputed from
the parent's `analysis/gemma4-e4b/read_profile_full_depth.json` (fit on the clean
`use_cache=True` extract, `extract_manifest_sha256: 060c3f3b…`, AUC on held-out;
counts `known_held: 270`, `confab_held: 168`):

| hs | rel. depth | held-out AUC | `fpr_known_correct_flagged` | dosed known-correct rows |
|---|---|---|---|---|
| 15 | 0.357 | 0.9997 | 0.0074 | **2 / 270** |
| 18 | 0.429 | 0.9999 | 0.0074 | **2 / 270** |
| 20 | 0.476 | 0.9996 | 0.0074 | **2 / 270** |
| 22 | 0.524 | 0.9998 | 0.0074 | **2 / 270** |
| 23 | 0.548 | 0.9998 | 0.0074 | **2 / 270** |
| 24 | 0.571 | 0.9980 | 0.0222 | 6 / 270 |
| 34 | 0.810 | 0.9804 | 0.0815 | 22 / 270 |
| 38 | 0.905 | 0.9770 | 0.0704 | 19 / 270 |
| 42 | 1.000 | 0.9891 | 0.0481 | 13 / 270 |

**F4 — the computed Wilson floor, and the consequence.** Per
`.skills/experiment-runner/reference/gate-diagnosticity.md`, a Wilson-95%-upper
cap is unsatisfiable below the smallest `N` with `wilson_upper(0, N) < cap`.
Verified directly for the registered `< 0.10` cap: **N = 35**
(`wilson_upper(0,35) = 0.0989`; at `N = 34` it is `0.1015`). Matches the floor
the Tier 1 revision computes.

**Every candidate site in this experiment sits below that floor.** The best is
hs34 at 22 dosed known-correct rows; the shallow ladder sits at 2. The fired-only
G2 companion is therefore **NOT-ADJUDICABLE at every arm**, and must be
pre-registered as such rather than discovered at resolve.

**F5 — the draft's G2-diagnosticity section is partly withdrawn.**
`AMENDMENT.md` "What G2 measures here" cited FIT-pool numbers from the corrupt
`gate_fit_layers.json` (`fpr` 0.0889 / 0.0889 / 0.0944; AUC 0.9779 / 0.9815 /
0.9772 at hs34 / hs38 / hs42). Clean held-out equivalents are 0.0815 / 0.0704 /
0.0481 and AUC 0.9804 / 0.9770 / 0.9891.

- What **survives**: gemma does fire on known-correct rows far more than
  llama (0/334) or mistral (0/8), so the llama/mistral vacuity argument genuinely
  does not transfer to this substrate.
- What is **withdrawn**: "Gemma is the family where G2 is most diagnostic in this
  lineage, not least." At 22 dosed rows against a floor of 35, gemma is *less
  vacuous* than llama/mistral but still **not adjudicable**. Firing more than a
  family that fires zero times is not the same as clearing the bar.

**F6 — the draft's `n_fired_known < 10` floor-check threshold is not derived.**
Replaced with the computed floor of 35 and re-labelled NOT-ADJUDICABLE (a
disposition distinct from PASS), per the gate-diagnosticity design prescription.

**F7 — shallow-site median anchor norms, from the clean extract** (so the R2
ratio ladder is denominated correctly at the new sites, with no re-extraction):
hs15 **133.17**, hs18 **101.07**, hs20 **81.35**, hs23 **58.78** (n = 806 rows
each). The clean extract already covers hs0–hs42, so the shallow ladder needs no
new GPU extraction.

**F8 — why the shallow ladder discriminates, and it is not just "more depth."**
Writing at `hs_index N` hooks the output of block `N-1`. Donors are blocks 22 and
23. So hs15 / hs18 / hs20 are the outputs of blocks 14 / 17 / 19 — all upstream
of both donors, i.e. **the same donor-reachability regime as hs22**, while hs23
(output of block 22) is full-donor-only, the same regime the draft already
registered. The shallow ladder therefore **varies depth at constant donor
reachability**, which is the one thing the original A3-vs-A5 pair could not do
(two blocks apart, confounded with linear accessibility). If actuation appears
anywhere in hs15–hs22 the quarantine account gains a clean positive; if nothing
actuates anywhere upstream of the donors, the quarantine account is dead on the
unmodified model and the gemma null is a property of the model.

**Nothing launched.** No GPU, no sign. `persistence:` still needs measured smoke
timings, which is the first item here that costs GPU time.

### 2026-07-24 (later) — lead revision pack applied (6 items); still unsigned, still no GPU

Six changes requested by the lead, applied in place. No sign, no commit, no GPU.

**1. The sharing-OFF toggle as drafted would have CRASHED on first run — fixed.**
Independently verified against the executing `transformers==5.5.0` before
accepting the finding. Trace: `Gemma4TextModel.forward` builds
`DynamicCache(config=...)`; `DynamicCache.__init__` is shared-KV-aware and
truncates — `cache_utils.py:1218-1220`, `layer_types = layer_types[:
-num_kv_shared_layers]` — allocating exactly 24 `CacheLayer` objects. Because
that list is non-empty, `Cache.__init__` (`:871-872`) sets
`layer_class_to_replicate = None`, disabling the lazy-growth branch in
`Cache.update` (`:927-930`). A patched shared block reaching
`past_key_values.update(..., 24)` at `modeling_gemma4.py:1216` then indexes
`self.layers[24]` on a 24-element list → **deterministic IndexError on the first
shared-layer forward**. Registered fix: `kv_seam_patch.build_full_length_cache`
builds a 42-entry cache (library per-type logic for 0-23, appended per
`config.layer_types` for 24-41) and the harness passes it as
`generate(past_key_values=...)`, which bypasses the truncating constructor via
`generation/utils.py:1818-1829` "Quick escape route 1". Fresh cache per call —
a `Cache` is stateful and reuse leaks the previous row's K/V.
`use_cache=False` **rejected** as the toggle (it is global not local, changes
numerics, and costs O(T x S_avg)). `store_full_length_kv` deliberately untouched
so control flow is identical in both conditions except the branch under test.
G0-KV is now **mandatory, not advisory**, and grew three checks: cache shape
(`len(layers) == 42`, `layer_class_to_replicate is None`), **per-layer cache
growth** across ≥2 decode steps for indices 24-41 (positive evidence the
appended slots are live, and the cheapest detector of an accidentally reused
cache), and an **ON-condition cache-substitution no-op** check proving the
42-entry cache by itself changes no tokens — without which the primary contrast
would be sharing-flag *plus* cache-substitution versus neither.

**2. Observation 4 (terminal-layer collapse onset) struck.** Removed, not
softened: generic self-repair predicts it in every family, so it cannot support
an architectural story about Gemma. The clause lived in Threats (g); the eff_dim
flatness caveat there stands on its own.

**3. Below-seam site now selected by linear accessibility, not the eff_dim peak.**
New precondition **G0-ALIN**. `A_lin(hs_N)` = top-1 accuracy of final RMSNorm +
`W_U` applied to the cached hidden state (training-free logit lens, 2604.15557 /
parent review Thread D), recorded on FIT for hs22/23/24/34/38/42. Rule
pre-stated: **A3 = whichever of hs22/hs23 has the higher `A_lin`**, other becomes
A6, ties (<0.01) break to hs22. Donor reachability already fixes the candidate
set to exactly two, so `A_lin` has no free depth parameter to exploit. The sweep
is **CPU-only over the parent's cached activations** — it can run while the 3090
is busy, and the drafter recommends running it **before** sign so the arm table
has no hole at signature.

**4. Exclusivity withdrawn.** New section "Standing of this hypothesis". The
"write lands + decodable + inert" signature is **not** a Gemma fingerprint:
`library/notes/internal-al-injection-null--true-checkpoint.md:141` (Amendment AL,
**Qwen3-4B**) records readback ratio **1.0008** with all 1,564 unpushed rows
reproducing baseline grade and bootstrap CI [0.00, 0.00]; the Amendment AA
mechanism note (**Qwen3.5-4B**) records the same inertness on the trust axis. KV
sharing survives as the only *structural* candidate that distinguishes gemma from
llama/qwen and the only one making a cheap mechanism-toggling prediction — one
hypothesis among at least four, not the leading one.

**5. New "Competing explanations" section.** Names and discriminates against:
linear accessibility / crystallization gap (2604.15557 — the parent's review
calls it the strongest competitor and the drafter agrees; it explains the
signature *more completely* than KV sharing does, including the absence of any
window between inert and collapse); entanglement blocking linear correction
(2605.05715, the closest published analogue, replicates cross-architecture);
generic self-repair (Hydra cluster); steering-vector non-identifiability
(2602.06801). 1-3 are **site properties** and 4 is a fit property; A1-vs-A2 holds
the site fixed and therefore holds all of them fixed at once, which is why it
carries the primary. Explicitly recorded: a negative A2 removes KV quarantine
from the list and leaves 1-4 **undifferentiated** — it does not choose among
them.

> **[CORRECTED 2026-07-24 — see the entry below, item 4.]** The claim in the
> preceding sentence that A1-vs-A2 "holds the site fixed and therefore holds all
> of them fixed at once" is **false**. hs38 is the output of block 37, a
> KV-*shared* block; sharing-OFF changes blocks 24–37 upstream of it, so the
> site's *representation* — and hence its `A_lin` — is not held fixed by holding
> the site *index* fixed. The contrast becomes discriminating only when
> `A_lin(hs38)` is measured under both conditions (G0-ALIN Part 2). The sentence
> is left standing rather than edited so the correction is auditable.

**6. G2 vacuity — addressed, with a counter-finding for the lead.** The concern
is real in this lineage: `pipeline.py:229` takes `known_correct_answered`
unfiltered by `fire` (inherited verbatim from
`j-space-midband-write-sweep-qwen3-4b/pipeline.py:188`), non-firing rows are
never dosed (`pipeline.py:149`), and per the parent's
`analysis/mistral-7b-v03/cost_control_forensics.md` mistral fires **0/8**
known-correct FIT rows at all four layers and llama **0/334** held-out at hs17,
with frozen-tau fp rates of **1.18%** (hs12) and **0.78%** (hs15).
**But gemma is not that family.** From
`analysis-committed/gemma4-e4b/gate_fit_layers.json` (FIT, n=180
known_correct_answered): `fpr_known_correct_flagged` = **0.0889** at hs34
(16/180), **0.0889** at hs38 (16/180), **0.0944** at hs42 (17/180) — roughly
**10x llama/mistral** and **2-3x** the Qwen predecessor's diagnostic operating
points (0.035 = 9/258, 0.039 = 14/360). At the registered held-out floor of ≥250
known-correct rows that is **~22+ genuinely dosed rows** in the G2 denominator.
Gemma is the family where G2 is *most* diagnostic in this lineage, not least.
Registered anyway so a vacuous pass can never read as evidence of harmlessness:
the G2 population is **not** restricted to fired rows (that would silently
redefine a gate transcribed verbatim from the parent and break cross-family
comparability); instead every arm reports the **triple** — gating full-population
G2, non-gating **fired-only** rate with `n_fired_known` and Wilson interval, and
the **undosed floor** — with a pre-stated rule that `n_fired_known < 10` labels
the arm's G2 a **floor-check only**, uncitable as evidence the intervention is
harmless, and that a fired-only rate above 0.05 while full-population G2 passes
goes in the arm's headline summary rather than a table.

**Drafter's dissent WITHDRAWN** (section renamed "Drafter's note"). The earlier
recommendation to swap the primary to A3-vs-A5 was wrong. Its premise — that
A1-vs-A2 trades a depth confound for a model-identity confound — stands, and is
why the falsifier still requires **both** A2 and A3 to fail. But A3-vs-A5 varies
the *site*, and every competing explanation above is a site property, so it is
confounded with the strongest competitor in a way no depth-matching removes.
A1-vs-A2 holds the site fixed and is the only contrast with discriminating power.
"Open questions at sign" #6 is CLOSED; #5 is now the pre-sign `A_lin` sweep.

**Files touched:** `AMENDMENT.md` (items 1-6 + dissent rewrite + reporting plan),
`gates.yaml` (G0-KV split into 6 checks, new `g0_alin_site_selection`, G2
population/vacuity/companion-metric blocks), `cell.yaml` (`A_lin` site selection,
`off_condition_cache_contract`, corroborating-contrast block, `alin_sweep.py`
stage, 3 new `integration_status` items), `kv_seam_patch.py`
(`build_full_length_cache`, `cache_layer_lengths`). All YAML re-parsed;
`kv_seam_patch.py` byte-compiles. Nothing executed against weights.

### 2026-07-24 — draft scaffolded, unsigned, no GPU work

Delegated draft. Scope was DRAFT ONLY: no `bin/exp sign`, no GPU, no commits, and
no file belonging to `experiments/j-space-cross-family-layer-contrast/` touched.

**Parent facts verified before citing** (read from the parent's own governed
docs on the `exp/j-space-cross-family-layer-contrast` worktree, not from a
summary):

- `NOTEBOOK.md` "gate_fit.py": KU readout gate AUC 0.9779 (hs34), 0.9815 (hs38),
  0.9772 (hs42) — all above the 0.90 floor.
- `NOTEBOOK.md` "calibrate_dose.py v2 COMPLETE": `frac_readback_within_tol` =
  1.00 at all 32 (layer, rung) cells; `confab_tighten` = 0.000 at every rung of
  every mid-band site; ladder spanned inert (`collapse_rate_on_dosed` 0.00 at
  ratios 0.100–0.361) to collapse (1.00 by ratio 0.850). Median anchor norms
  hs34 120.20, hs38 125.51, hs40 117.57, hs42 281.34.
- Disposition NOT-RUN, **write-verified behavioral null** — explicitly a
  different category from the llama/mistral v1 instrument-resolution-limited
  stops.
- `gates.yaml`: G1 `clean_tighten >= 0.50` with Wilson 95% lower CI > 0.40; G2
  `not_well_formed_correct <= 0.05` with Wilson 95% upper CI < 0.10; seed
  20260709, alpha 0.05. Transcribed verbatim into this experiment's
  `gates.yaml`; not re-derived.
- `calibrate_dose.py:56`: `RATIO_LADDER = [0.100, 0.153, 0.235, 0.361, 0.554,
  0.850, 1.304, 2.000]`. Inherited verbatim.
- `analysis-committed/gemma4-e4b/layer_profile.json`: depth sweep points
  `[1,6,10,15,20,24,29,34,38,42]`, `effective_dim_peak_hs: 38`, eff_dim_frac flat
  0.0046–0.0058. **hs22 and hs23 were never profiled** — noted because two of
  this experiment's sites sit there.

No disagreement with the lead's brief was found on any of the above.

**Correction to the brief's site rule (load-bearing).** The brief specified
below-seam candidates as "blocks < 24". That is off by the donor offset.
Re-derived independently from the pinned checkpoint config and
`transformers==5.5.0` `models/gemma4/modeling_gemma4.py:1130-1239`:
`first_kv_shared_layer_idx = 42 - 18 = 24`, donor(full_attention) = block 23,
donor(sliding_attention) = block 22, `store_full_length_kv` True at 22 and 23
only. Combined with the parent's site convention (`hs_N` = output of block
`N-1`):

| site | = output of block | sliding donor (22) | full donor (23) | verdict |
|---|---|---|---|---|
| hs22 | 21 | reaches | reaches | both donors |
| hs23 | 22 | no | reaches | full donor only |
| hs24 | 23 | no | no | **quarantined** |
| hs38 | 37 | no | no | quarantined (parent's site) |

A site list derived from the block index would have admitted hs24 as a
"below-seam" arm while it is in fact fully quarantined. Registered instead as
**A5**, the seam-adjacent quarantine control — and the hs22-vs-hs24 pair, two
blocks apart on the unmodified model, is the cleanest available isolation of the
mechanism. See `AMENDMENT.md` "Drafter's note". *(Superseded in part by the
2026-07-24 revision entry above: hs22-vs-hs24 is corroborating, not primary — it
is confounded with linear accessibility, which A1-vs-A2 holds fixed.)*

**Written this session:**

- `AMENDMENT.md` — full draft (motivation, seam derivation, design and arms
  A1–A6/C0/C1, preconditions G0-KV / G0-C1 / G0-arm, prediction, falsifier with
  three subordinate dispositions, transcribed gates, threats (a)–(g), analysis
  and reporting plan, scoreboard, open questions at sign, drafter's dissent).
- `cell.yaml`, `gates.yaml` — replaced the scaffold placeholders.
- `kv_seam_patch.py` — the one genuinely new instrument: `verify_architecture`
  (fail-closed on 42/18/24 and the donor set), `kv_sharing(model, enabled)`
  context manager, `count_kv_projection_calls`, `capture_donor_keys`.
  Syntax-checked only; never executed against weights.
- Verbatim copies of the parent's `family_config.py`, `model_lib.py`,
  `gen_lib.py`, `grader.py`, `scorers.py`, `extract_anchor.py`,
  `build_directions.py`, `gate_fit.py`, `calibrate_dose.py`, `pipeline.py`,
  `run_contrast.py`, `families/gemma4-e4b.yaml`.

**Self-caught bug during authoring.** `capture_donor_keys` originally defaulted
to `blocks=(22, 23, 24)` and hooked `k_norm`. A KV-shared block never executes
`k_norm`, so the block-24 hook could never fire. Fixed to
`EXPECTED_DONOR_BLOCKS_TUPLE = (22, 23)`, which is the complete set of keys every
block 24–41 consumes.

**Not ready to sign.** Open before `bin/exp sign`: pool/split promotion decision
(second consumer of the parent's artifacts, and the parent is on an unmerged
worktree branch); the `--kv-sharing {on,off}` flag and condition field are not
yet threaded through the copied scripts; `preflight_kv_seam.py` and `rollup.py`
are unwritten; measured smoke timings for `instrument.persistence` are missing
(sign will refuse); the C1 NLL threshold (10% vs 5%) needs the lead to fix it.
Listed in `AMENDMENT.md` "Open questions at sign" and `cell.yaml`
`integration_status`.

## 2026-07-24 — Revision after lead review (five verified points)

Lead-supplied corrections, all stated by the lead as personally verified (re-ran
`kv_seam_preflight.py`, re-derived the ladder arithmetic from raw JSON). Each
was independently confirmed at source by the drafter before being written in.
Still unsigned; still no GPU work; nothing committed.

**1. The instrument as drafted crashed.** `kv_seam_preflight.py` (authored by
`gemma-arch-research`, not by this drafter; 4/4 PASS, exit 0) reproduces a live
`IndexError` from `kv_sharing(model, enabled=False)` under plain `generate()`:
transformers builds a 24-entry cache for this config (`cache_utils.py:1218-1220`
truncates by `num_kv_shared_layers`), so a patched shared block calling
`past_key_values.update(..., 24)` indexes off the end. Deterministic, not a risk.
`build_full_length_cache` is now wired into `kv_seam_patch.py`.

**API correction carried:** the builder is `Cache(layers=[...])` — one
`DynamicLayer` or `DynamicSlidingWindowLayer` per entry in `config.layer_types`,
no slicing. It is **not** `DynamicCache(layers=...)`; `DynamicCache.__init__`
accepts only `config=` and would re-apply the slice. `cache_layer_lengths` now
uses `layer.get_seq_length()` rather than poking `.keys`.

**Both arms, not just OFF.** The lead's requirement, adopted: every `generate()`
call in every arm — ON and OFF, dosed and undosed, C0 and C1 — gets a fresh
cache from the same one function. If the two conditions construct the cache
differently, the A1-vs-A2 difference is sharing-flag *plus* cache-substitution
versus neither, and the contrast is uninterpretable. Preflight check 4 licenses
this: under sharing ON the 42-entry cache is token-identical and `torch.equal`
logit-bit-identical to stock. New gate check
`cache_construction_identical_in_both_arms`; `off_condition_cache_contract`
renamed to `cache_contract` in `cell.yaml`.

**2. Motivation now cites measurement, not impression.** Verified in the parent's
`analysis/gemma4-e4b/dose_response_window.md` (read in full): pooled genuinely-
dosed **0/176 tighten, Wilson [0.000, 0.021]**; per-cell 0/8 with Wilson
[0.000, 0.324] at all 24 mid-band cells; `frac_readback_within_tol` 1.0 in all
32 cells. Llama positive control at hs17: nonzero tighten on 5 of 8 rungs
(0.235–1.304), collapse 0.000, tighten 0.375/0.875/0.875, Wilson lower bounds
13.7%–52.9%; hs20/hs23/hs26 each also nonzero at zero collapse. The single
nonzero gemma cell (hs40 late arm, 1/8, CI [0.022, 0.471], different frozen
direction) is reported and gates nothing.

**3. Correction carried.** `arch_null_forensics_report.md` observation (E) is
wrong: hs42's collapse onset is **r0 = 0.100** (rate 0.100), not r1 = 0.153 — the
r1 rate is 0.900. `dose_response_window.md` lines 75-80 state the correction
explicitly. This amendment cites the corrected number.

**4. The discrimination problem — the drafter's answer, arrived at independently.**

Both hypotheses predict the parent's mid-band observations **identically**: high
KU readout gate AUC, `frac_readback_within_tol` 1.0, `clean_tighten` 0 at every
rung, monotone inert-to-collapse ladder with no window. Every number in the
motivation is jointly predicted. The dose-response null is therefore written as
the *premise* of this experiment, never as evidence for quarantine.

They diverge because the crystallization-gap account makes actuation a function
of linear accessibility **at the write point** (if `A_lin` is unchanged, behavior
is unchanged), while KV quarantine makes it a function of K/V reachability
**independently of `A_lin`**. The discriminating observable is the **joint**
(behavioral delta, `A_lin` delta) across A1/A2, registered as a four-outcome
table in `gates.yaml g0_alin_discrimination_measurement`.

**Drafter's self-correction, load-bearing.** An earlier revision of this
amendment asserted that A1-vs-A2 "holds the site fixed and therefore holds every
competing site-property explanation fixed." **That is false.** hs38 is the output
of block 37, a KV-*shared* block, so turning sharing OFF changes blocks 24–37 —
all upstream of hs38. The OFF model's representation at hs38 genuinely differs;
that is precisely why this design already refits the directions under OFF. The
false claim was load-bearing in two places (Arms, Drafter's note) and both are
corrected in place rather than quietly patched.

**Design change this forces.** `A_lin(hs38)` must be measured under **both**
conditions. No activation cache exists for the sharing-OFF model — it has never
been run — so this requires `extract_anchor.py --kv-sharing off` on **GPU**. It
is registered as G0-ALIN **Part 2**, distinct from Part 1 (the CPU pre-sign site
selection for the descriptive below-seam arm). Ordered before the OFF direction
fits, which consume the same extraction, so it adds a logit-lens pass rather than
an extraction. Band `|ΔA_lin| <= 0.05`, matching the G2 cap and the C1
criterion-1 tolerance already in the design. **Without Part 2 the primary
contrast discriminates nothing**, and the drafter's recorded position is that the
experiment is not worth running without it. That judgment is the lead's at sign.

**On the below-seam depth question (the lead's direct ask): it is the ordinary
depth effect, and A3 carries no discriminating weight.** Two distinct confounds,
deliberately not blurred: A3-vs-A1 (hs22 vs hs38, 16 blocks) is confounded with
depth outright; A3-vs-A5 (hs22 vs hs24, 2 blocks) controls depth tightly but does
**not** control linear accessibility — two blocks of computation can move it, so
the crystallization-gap account predicts A3-yes/A5-no as readily as quarantine
does. Parent numbers bearing on this: llama actuates at hs17/hs28 (depth fraction
0.61) and shows nonzero tighten as late as hs26 (0.93), while gemma is flat zero
at hs34 (0.81) and hs38 (0.90); no llama site as shallow as gemma's hs22 (0.52)
was tested, so there is no cross-family control either. **A3/A4/A5/A6 are demoted
to descriptive arms** — removed from `success_rule`, retained in the falsifier
only as a labeled conservatism.

**5. Gemma has NO held-out run at all.** Verified: `analysis/gemma4-e4b/` has no
`full_summary.json` and no `runlog/full/`; the only `full_summary.json` in the
parent tree is `analysis-committed/llama-3.2-3b/`. `dose_response_window.md`
lines 22-24 say so directly. Everything cited about gemma — the 0/176, the
collapse onsets, the gate AUCs, the `fpr_known_correct_flagged` figures used in
the G2 vacuity argument — is **FIT-scale**. Added as Threats (h) with three
consequences: the parent null is weaker than llama's or mistral's; the
FIT/HELD-OUT firewall *inside* this experiment is unaffected (this experiment
produces gemma's first held-out numbers); and an all-null outcome licenses only
"the null replicates, now on held-out," not "the parent finding was confirmed."
The same caveat is written into the G2 vacuity assessment in `gates.yaml`.

---

### 2026-07-25 — instrument integration completed (CPU, 6/6 preflight); A1 hs38 contradiction resolved; donor-projection diagnostic run (authorized GPU carve-out) — OFF is a STRONG manipulation

Three things landed. None of them is a result about the hypothesis; all three
are pre-sign instrument and design work. **The main run is still blocked**
(`cell.yaml execution.gpu_work_by_this_agent: forbidden`) and **#338 is
unsigned.**

**1. `--kv-sharing {on,off}` integration is done.** Threaded through
`extract_anchor.py`, `build_directions.py`, `gate_fit.py`, `calibrate_dose.py`,
`run_contrast.py` and `pipeline.py`. The last two of those six were *not* in the
original task list. Reading `cell.yaml readouts.refit_policy` while writing
`compute_gate_decisions` caught my own docstring asserting the opposite of
registered protocol — I had written that the direction/mu/sigma/tau are frozen
ON artifacts reused verbatim in both arms; the policy says sharing-OFF arms
**refit their own** directions, tau and per-site median anchor L2 norm on the
same FIT rows, because the OFF residual stream is a different distribution.
Making that policy actually implementable is what forced the condition axis to
reach every *fitted* artifact, not just the activations.

Two design choices worth recording:

- **Scoping, not content-resolution, for the condition axis.**
  `load_roll_up_layer` resolves the *site set* by content — site sets are
  disjoint layer sets, so at most one file can contain a given layer. That trick
  cannot work for the condition: both conditions fit the *same* layers, so both
  files contain the same layer name. The condition therefore scopes the search
  rather than being inferred from it.
- **Every cross-condition read is fail-closed.** A missing OFF artifact raises,
  naming the exact stage and flag that produces it. It never falls back to ON
  parameters the arm never fit — that would quietly turn A1-vs-A2 into a
  comparison of an arm against itself.

`kv_sharing=on` is the identity for every artifact name, so historical filenames
are byte-for-byte unchanged. Verified by a 9-case CPU-only harness (all PASS),
including that a missing OFF roll-up raises rather than resolving, and that the
symlink guard fires on the real staged 341.7 MB parent extract.

`kv_seam_preflight.py` now runs **6/6 PASS**, CPU-only, no checkpoint download.
Checks 5 and 6 implement the two `gates.yaml g0_kv_seam_instrument_validity`
criteria verbatim: `cache_growth_under_off` (hand-stepped prefill + 2 decode
steps; all 42 layers 6→7→8, blocks 24..41 live at every step, and a fresh cache
asserted empty as the reused-cache detector — plus an equality check between
`kv_seam_patch.build_full_length_cache` and this file's independent
reimplementation, so the preflight tests the shipped builder rather than
confirming it agrees with itself) and `cache_substitution_noop_under_on`
(token-identical on 8 fixed prompts at lengths 4..11).

**2. `cell.yaml` contradicted itself about arm A1, and the lead resolved it.**
`inputs_reused.frozen_hs38_direction` said A1 reuses the parent's frozen hs38
direction/gate artifacts; `readouts.method` said every arm fits its own under
its own KV-sharing condition. Reuse was untenable regardless — those parent
artifacts are corrupt-derived (`AMENDMENT.md:637`), so reusing them would seat a
corrupt direction in the very arm A2 is contrasted against. **Resolved in favour
of `readouts.method`: A1 refits hs38 fresh under ON like every other arm.** A1
replicates the parent's *site and method*, not its artifacts. No code change;
`cell.yaml` corrected in two places and the resolution recorded at "Open
questions at sign" #1.

**3. Donor-projection diagnostic (open question #4) — RUN, and it clears the
risk it was built to detect.** Authorized by the lead as a scoped carve-out
(`cell.yaml execution.gpu_carve_outs`) while the main run stays blocked:
`donor_diagnostic.py`, 4 rows, `google/gemma-4-E4B-it` bf16 on the local 3090,
forward passes only.

**Every block in 24..41 computes K and V essentially orthogonal to its donor's.**
Median per-block cosine across 4 rows: **k_proj −0.0024**, **v_proj −0.0051**;
largest cosine at any block on any row **0.032**. Bit-identical across two
independent invocations.

The feared outcome was the opposite — a high cosine, meaning the retained
projections nearly reproduce the donor, OFF is nearly a no-op, and a negative A2
means almost nothing. That is not the case. A2 is a real manipulation of the KV
pathway and an A2 null will be informative. This promotes nothing about the
*direction* of any effect; it removes one specific way the primary contrast
could have been dead on arrival.

**Read the cosine, not the rel-L2.** `rel_l2_err` came out at 3–14, which looks
alarming and mostly is not: the hooks sit on the `k_proj`/`v_proj` modules and
so capture output *before* `k_norm`/`v_norm` (`Gemma4RMSNorm` over `head_dim`).
Gemma's residual norm grows with depth, blocks 24..41 project a much
larger-magnitude input than blocks 22/23, and `rel_l2_err` inherits that scale
gap wholesale — RMSNorm then removes it. Cosine is scale-invariant and is the
load-bearing number. The caveat is emitted into the JSON as
`measurement_caveat` so it cannot be separated from the numbers later.

One structural observation to carry forward: the three **full-attention** shared
blocks (29, 35, 41; donor 23) show markedly lower `rel_l2_err` (2.7–7.4) than
the fifteen **sliding-attention** ones (5.8–14.6; donor 22). Cosines are equally
near zero at both, so no conclusion here changes — but it is a scale difference
between the two donor channels, and **A6** is the arm that would notice it.

**Environment note (not a code change, needed at launch).** `model_lib.render()`
imports `backends` and `amendment_ah_stage0_extract` by bare module name, and
neither lives in this experiment. The diagnostic ran with
`PYTHONPATH=<repo>/experiments/common/knowledge_probe:<repo>/experiments/j-space-cross-family-layer-contrast`
prepended to the usual `synaptic-tuner` entry — the same two dead-import fixes
the parent recorded on 2026-07-23. Depending on the parent experiment's
directory being on `PYTHONPATH` is a cross-experiment dependency that should be
resolved (vendored shim, or promotion) before signing, not carried as tribal
knowledge.

**4. C1 NLL threshold CLOSED at 10%** by the lead, before C1 runs and before any
GPU work. Written into `gates.yaml` as `threshold_frac: 0.10` with a
`resolved_by_lead` note. Moves for no result.

Still outstanding before `bin/exp sign`: `alin_sweep.py` (Parts 1 and 2), the
fired-only G2 companion metric, `rollup.py`, and the measured smoke wall-clock
timings for `instrument.persistence` (`sign` refuses without them).

### 2026-07-25 — render path vendored into the experiment; the cross-experiment PYTHONPATH dependency is gone

The donor diagnostic yesterday only ran because I put **two** other
directories on `PYTHONPATH`: `experiments/common/knowledge_probe` (for
`backends`) and the parent experiment `j-space-cross-family-layer-contrast`
(for `amendment_ah_stage0_extract`). That is a cross-experiment runtime
dependency, and it should not survive to sign. `model_lib.render()` resolves
both by **bare module name** —

```python
module_name, func_name = cfg["render"]["fn"].split(":")   # "backends:render_probe_prompt"
module = importlib.import_module(module_name)
```

— so a correct render depended on an environment variable being set correctly
at every launch, with a *silent-wrong-answer* failure mode if it ever pointed
at the archived tree instead of the live one. Both shims now live in this
experiment directory, sibling to the existing vendored `scorers.py`.

**`backends.py` is a re-export, not a copy.** It resolves
`experiments/common/knowledge_probe/backends.py` by path and re-exports
`render_probe_prompt` / `assert_no_think_scaffolding`. Copying was the obvious
move and is the wrong one: that module is live and actively maintained, and it
is the same render path the probe harness used to produce this experiment's
inputs. A copy would fork the render at the moment of copying and let this
experiment drift from the convention its own inputs were produced under, with
nothing on disk to reveal the drift. So: re-export the live code, and freeze
what it must not become.

**What each shim freezes.** `backends.py` hashes the *render path only* —
`render_probe_prompt`, `_apply_chat_template`, `assert_no_think_scaffolding`,
`_RENDER_MODES`, and the two thinking-marker constants — deliberately not the
whole file, because `backends.py` also carries a vLLM backend this experiment
never touches and an edit there should not stop a run. It separately asserts
`render_probe_prompt`'s exact signature, so a compatible-*looking* but
reordered parameter list fails here instead of rendering something subtly
different. `amendment_ah_stage0_extract.py` keeps the parent's prompt sha256
freeze, byte-identical (`81a04a99...`).

**One deliberate change from the parent's copies: absolute → repo-root-relative
path resolution.** Both parent shims hardcoded absolute paths into the
canonical checkout. In a git worktree that silently binds the run to a
*different* tree's copy of the prompt than the one under review — the run and
the review disagree and nothing says so. Both now walk up from `__file__`. The
hash freeze is the real content guarantee either way, so relative resolution is
strictly safer: it reads from whichever tree is being run, and still refuses if
that tree's copy is not the frozen one. Verified: from this worktree,
`_config_path()` resolves inside `ehr-worktrees/kv-seam-siteset`, not into the
canonical checkout.

**Verification (CPU, no checkpoint).** With `PYTHONPATH` holding *only*
`synaptic-tuner` — both extra entries dropped — all six checks pass: both
shims import; the frozen prompt loads at the expected sha256; the config
resolves into this worktree; `family_config`'s `render.fn`
`backends:render_probe_prompt` resolves through `model_lib`'s real
`importlib.import_module` path; and **both fail-closed guards were poked with a
wrong hash and confirmed to actually raise** — an unfired guard is not a guard.

Still outstanding before `bin/exp sign`: `alin_sweep.py` (Parts 1 and 2), the
fired-only G2 companion metric, `rollup.py`, and the measured smoke wall-clock
timings for `instrument.persistence`.

### 2026-07-25 — G0-ALIN Part 1 run (CPU, 18s): A_lin is at the floor below the seam, the tie-break decides, A3 = hs22

`alin_sweep.py`, 292 FIT rows, 9 depths, pinned revision, **no CUDA**, 18.05s,
2.6 GB RSS. Report: `analysis-committed/gemma4-e4b/alin_part1_selection.json`.

| Site | `A_lin` | median rank |
|---|---|---|
| hs15 / hs18 / hs20 | 0.0000 | 61 260 / 120 190 / 88 181 |
| **hs22** | **0.0000** | **83 008** |
| **hs23** | **0.0000** | **238 571** |
| hs24 | 0.0000 | 143 970 |
| hs34 / hs38 / hs42 | 0.9760 / 0.9760 / 0.9966 | 1 / 1 / 1 |

**A3 = hs22, A6 = hs23, A5 = hs24. No confound declared** (|0.0 − 0.0| = 0.0,
band 0.10). The arm table no longer has a hole in it.

**The registered statistic is at the floor, and the tie-break — not I — decided.**
`A_lin` is *exactly* 0.0000 at every below-seam site, so `|ΔA_lin| = 0.0 < 0.01`
fires the pre-stated tie-break to hs22 (broader donor reach). This is precisely
the condition the parent's session record flagged as a blocker ("G0-ALIN as
pre-registered cannot discriminate hs22 from hs23"). Having now run it, I don't
think that's a defect in the rule: the tie-break exists for exactly this case and
resolves on a stated principle rather than on noise.

**What makes me comfortable with it is corroboration from a statistic I did not
use.** Median rank is nowhere near the floor and separates the candidates
sharply: hs22 ranks the true token **83 008** vs hs23's **238 571** — better by
~3×, with hs23 the worst site at any depth measured (vocab is 262 144, so hs23
sits near the bottom of it). Had rank been the registered statistic it would have
picked hs22 too. So the selection does not depend on which statistic got locked.
Recorded as an observation only — **substituting rank for the registered top-1
accuracy would be goalpost movement on a locked rule, and I didn't.**

**Consequence: A6 and D4 are now the same cell.** A3 took hs22, so A6 is hs23 —
which is D4's registered site under the same condition (ON). D4's registration
note pre-stated this exact contingency, so the rule was already written: one arm
run, reported under both labels, never counted twice. One asymmetry now matters
and is recorded in `cell.yaml`: D4 is unconditional while A6 is conditional on A3
finding a usable FIT dose, so the cell **runs** as D4 regardless and is
additionally **read** as A6 only if A6's condition is met.

**Harness validation — four checks.** (1) Terminal-layer tautology: greedy
decoding makes the recorded token the argmax of the true final-layer logits, so
hs42 must be ~1.0 — measured **0.9966**, median rank 1, and *every* miss a rank-2
near-tie versus the parent's GPU 1.0000, i.e. CPU/GPU tie-breaking rather than
lens failure. The corrupt extraction scored 0.000 here, so this check has real
teeth. (2) Distinct-storage / non-vacuity on the cached tensors. (3) A
`prompt_len` re-render check across all 806 rows, proving the render used here
reproduces the one the activations were extracted under. (4) External: the
FIT-only numbers reproduce the parent's all-rows ladder at every shared depth
(hs15 61 260 vs 61 283; hs20 88 181 vs 88 087; hs24 143 970 vs 144 858).

**One thing CPU cannot do, recorded rather than papered over.** I first wrote the
calibration to *resolve* `final_is_postnorm` on CPU by requiring exactly one
output recipe to be tautological at hs42. It doesn't work — both score ~0.99,
because re-normalizing an already-normalized vector barely moves the argmax. The
fail-closed guard caught it and refused rather than silently picking one, which
is the behaviour I wanted from it. The recipe is therefore taken from the
parent's decisive GPU calibration (max-abs reconstruction 0.0 vs 17.6875), and it
**cannot touch this selection**: the two recipes differ only at hs42, and every
candidate site is normed identically under either.

**Two provenance checks done before trusting any of this.** The manifest records
`forward_use_cache: True`, so these are the *corrected* clean activations, not
the withdrawn `use_cache=False` ones that made blocks ≥ hs25 meaningless
(AMENDMENT.md:379) — the script now refuses outright on a `use_cache=False`
manifest. And the local HF cache holds **two** revisions of this checkpoint with
`refs/main` pointing at the one the experiment does *not* pin; their
`model.safetensors` is the same blob but their chat templates differ. Verified
both render all 806 rows to identical `prompt_len` (the differences are in
tool-calling/thinking macros this probe never exercises), and pinned `revision=`
explicitly anyway so the ambiguity cannot come back.

Part 2 (`A_lin(hs38)` under both KV conditions) is unchanged and still GPU-blocked:
it needs `extract_anchor.py --kv-sharing off`. It is now the *same script* pointed
at the OFF extraction, which is what the gate's "identical logit-lens code path"
requirement asks for.

Still outstanding before `bin/exp sign`: G0-ALIN Part 2, the fired-only G2
companion metric, `rollup.py`, and persistence timings for the remaining modules.

### 2026-07-25 — smoke run: the persistence blocker is closed, and it found two things

Lead-authorized ("smoke it"). Scope was the remaining
`instrument.persistence` timings, the last thing `bin/exp sign` mechanically
refuses on. **It never touched the GPU** — see below, that turned out not to be
a concession but a finding.

**All eight remaining modules declared, all measured, none estimated.** Method
identical to the two shims: cold interpreter per run, three runs, **worst**
observed value recorded rather than the best or the mean.

| Module | s | note |
|---|---|---|
| `family_config.py` / `scorers.py` / `grader.py` | 0.02 | pure-python libraries |
| `kv_seam_patch.py` / `gen_lib.py` / `model_lib.py` | 1.13 / 1.25 / 1.68 | torch import is the entire cost |
| `pipeline.py` | 1.75 | library; its *callers* are the `incremental` ones |
| **`gate_fit.py`** | **2.67** | **real run, not an import** |

`bin/validate-experiments` now reports **zero** warnings for this experiment,
down from eight. Re-reading `cmd_sign` (`.skills/experiments/scripts/exp.py:721`)
against the manifest: status is `draft`, prediction and falsifier are filled,
`instrument.configs` is non-empty, every module has a persistence declaration,
every pinned file exists. **There is no longer a tool-level obstacle to signing.**
That is not the same as being ready to sign — the remaining blockers are
scientific and are tracked in `cell.yaml integration_status.missing` — but the
distinction is now clean, and "the tool won't let me" has stopped being one of
the reasons.

**Finding 1 — the last unrun pipeline stage doesn't need a GPU.** I had been
carrying `gate_fit.py` as GPU-blocked along with everything else. It isn't: it
fits tau on the *already cached* anchor activations with numpy and never loads
the checkpoint. So it was run for real — `--site-set shallow_ladder
--kv-sharing on`, three cold runs, 2.37–2.67s, maxRSS 1.6 GB, byte-identical
stdout each time.

Comparing its output against the previously committed roll-up: **every AUC,
every tau, every confusion count identical.** One key was added —
`"kv_sharing": "on"`. The committed artifact predates the condition-scoping
work, so it was stale against its own producer. The regenerated file is
committed. Nothing was recomputed into a different answer; a provenance field
that should always have been there now is.

A process note worth keeping: my first comparison was `diff -q ... && echo
BIT-IDENTICAL`, and it printed BIT-IDENTICAL **while the files differed** — the
`rtk` wrapper standing in for `diff` here does not return diff's exit status.
Caught only because the unified diff was printed alongside it and visibly
disagreed. Structural comparisons in this repo go through `json.load` and `==`,
not through a shell exit code.

**Finding 2 — the arm table names two sites no stage can address. This blocks
the run.** `A3 = hs22` and `A5 = hs24` were resolved yesterday by G0-ALIN Part 1
and registered in `cell.yaml`. But `build_directions.py`, `gate_fit.py` and
`calibrate_dose.py` all select sites through `--site-set`, resolved against
`families/gemma4-e4b.yaml band_selection`, and that file registers exactly two
sets: `midband_candidates_hs: [34, 38, 42]` and `shallow_ladder_hs: [15, 18, 20,
23]`. Addressable sites are therefore `{15, 18, 20, 23, 34, 38, 42}` — **hs22
and hs24 are in neither.** Confirmed by calling `resolve_site_set` directly, not
by reading the yaml.

So the two arms carrying the experiment's own registered non-gating expectation
("A3 clears both gates while A5 does not") currently have no path to a fitted
direction, a tau, or a dose. This is a manifest gap created by resolving the
sites, not a defect in the science, and it is exactly the class of thing the
smoke exists to surface before a GPU run rather than 90 minutes into one.
**Not fixed unilaterally**: `band_selection` carries `status: resolved`, so
adding a site set to it is an edit to a registered surface and goes to the lead.

**Finding 3 (incidental) — the `synaptic-tuner` prerequisite is not a version
floor.** `cell.yaml prerequisites` reads `>= 7a44eb3
(fix/gemma4-decoder-layer-path)`, which reads like "any recent enough tuner".
It isn't: `7a44eb3` is the head of an **unmerged** remote branch. The canonical
checkout's submodule sits at `b1ea382` (a later merge on the mainline) and does
**not** contain it — its `_LAYER_PATHS` has `language_model.model.layers` but
not the `model.language_model.layers` entry gemma-4-E4B needs. The only local
checkout that satisfies the prerequisite is the one in the
`jspace-cross-family` worktree, which is what this smoke ran against. Anyone
running this experiment from the canonical checkout gets the tuner that does not
work, and `>=` is the reason they would not expect that. Worth rewording before
sign.
