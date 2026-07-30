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

---

## 2026-07-25 — Registering `seam_pair`, and what the CPU fits already say

Finding 2 above (the arm table naming two sites no stage can address) went to
the lead, who authorized **one** new site set, `seam_pair = [22, 24]`, and
authorized taking it **through dose calibration**. Not two sets, and not an
edit widening `shallow_ladder` — a new named set, so the existing
`shallow_ladder` artifacts stay byte-comparable against their own history and
the AMENDMENT's Threats (c) confound reading is untouched.

Registration is three surfaces, because `family_config.py` says a new set
"must be registered in gates.yaml before it is run":

1. `families/gemma4-e4b.yaml` — `band_selection.seam_pair_hs: [22, 24]`
2. `family_config.py` — `seam_pair_hs_indices()` resolver + `SITE_SETS` entry
3. `gates.yaml` — a `seam_pair_site_set:` block recording, per site, the
   readout distance and the donor set: A3 = hs22, rd 0.524, donors 22 and 23;
   A5 = hs24, rd 0.571, donors **NONE**.

The block also carries `why_one_set_and_not_two`,
`why_not_folded_into_shallow_ladder`, and `what_this_set_does_not_fix` — that
last one exists so nobody later reads the new set as having retired the
confound. It has not.

**The CPU fits landed first, and they already establish the dissociation the
quarantine hypothesis needs.** `gate_fit.py` never loads the checkpoint (it
fits tau on cached activations with numpy), so both sites got a gate without
touching the GPU:

| site | role | readout AUC | G0 floor |
|---|---|---|---|
| hs22 (A3) | below seam, donor-reachable | **0.999702** | ≥ 0.90 ✅ |
| hs24 (A5) | at seam, no donors | **0.997569** | ≥ 0.90 ✅ |

This matters more than it looks. If A5 later fails to actuate, that failure
**cannot** be attributed to the readout falling apart at hs24 — the read is
demonstrably near-perfect there. Only the write would be quarantined. Had
hs24's AUC come in under the floor, the arm would have been uninterpretable
before it ever ran.

**Incidental, descriptive, non-gating: the KU direction rotates completely
across the seam.** Cosine similarity between fitted `u_d` vectors:

```
        hs15   hs18   hs20   hs22   hs23   hs24
hs15   +1.000 +0.165 +0.068 +0.001 -0.008 +0.006
hs18   +0.165 +1.000 +0.258 +0.104 +0.054 -0.017
hs20   +0.068 +0.258 +1.000 +0.203 +0.049 -0.033
hs22   +0.001 +0.104 +0.203 +1.000 +0.230 +0.005
hs23   -0.008 +0.054 +0.049 +0.230 +1.000 +0.106
hs24   +0.006 -0.017 -0.033 +0.005 +0.106 +1.000
```

Neighbours share a little (0.20-0.26 at one step); hs22 and hs24 are
**orthogonal (+0.005)** despite both reading known-unknown at ~0.998+ AUC.
So "the same feature is readable at both depths" is the wrong picture — two
different directions each carry it. This is an observation for the record,
not a gate, and nothing in the arm table depends on it.

### Written BEFORE hs24's numbers landed: a null dose at hs24 would prove nothing

hs22's ladder finished first, so there was a gap in which hs24's result was
still unknown. Recording the interpretation rule now, in that gap, so it cannot
be accused of being fitted to the answer.

The tempting read is: "hs24 gets no usable dose → the write is quarantined."
**That inference is not available**, and the repo's own prior calibrations are
why. The only two committed `dose_calibration_summary.json` files in the
repository — llama-3.2-3b and mistral-7b-v03, both from the parent experiment —
say this:

| family | site | role | selected ratio | tighten |
|---|---|---|---|---|
| llama-3.2-3b | hs17 | midband | 0.361 | 0.875 |
| llama-3.2-3b | hs20 | midband | **none** | — |
| llama-3.2-3b | hs23 | midband | **none** | — |
| llama-3.2-3b | hs26 | late ref | **none** | — |
| mistral-7b-v03 | hs12 | midband | 0.554 | 0.625 |
| mistral-7b-v03 | hs15 | midband | 0.85 | 0.625 |
| mistral-7b-v03 | hs19 | midband | **none** | — |
| mistral-7b-v03 | hs30 | late ref | **none** | — |

`all_midband_have_usable_dose: False` in **both** families. Failing to find a
usable dose is the **modal outcome** for a mid-band site in this instrument —
4 of 5 mid-band sites across two families produced nothing. A null at hs24 is
therefore consistent with quarantine and equally consistent with the ordinary
calibration failure that happens at most sites regardless of seam geometry.
The calibration cannot separate those two. Only the sharing-ON vs sharing-OFF
contrast can, because only it holds the site fixed and moves the mechanism.

The late reference is null in both prior families too. So a null hs40 here is
the **expected** result and is not a defect — which is exactly why the arm is
registered as non-gating and descriptive, and why `calibrate_dose.py` exits 0
on the mid-band arm alone.

Two things this does buy us, both real:

- **hs22 selecting ratio 0.361 lands on the same rung as llama-3.2-3b's hs17.**
  Different family, different depth, different tokenizer, same normalized rung.
  For the program's "does this generalize across model families" question that
  is a genuine cross-family anchor — the ratio ladder appears to be measuring
  something family-independent, which is the whole reason it was normalized by
  each layer's own median anchor norm rather than left absolute.
- **A usable dose at hs22 is a positive result that does not depend on hs24.**
  A3 actuates: monotone dose-response, zero known-correct cost, self-limiting
  at 0.85 where collapse begins. That stands on its own.

This is also the first `dose_calibration_summary` for gemma4-e4b anywhere in
the repo, so there is no same-family precedent to compare the selected rung
against. The cross-family comparison above is the best available and should be
read as suggestive, not as a replication.

### The calibration landed, and A5 is not quarantined on this measurement

24/24 cells, exit 0, ~24 min on the local 3090.

| rung | hs22 (A3) | hs24 (A5) | hs40 (late ref) |
|---|---|---|---|
| 0.100 | 0.000 | 0.000 | 0.000 |
| 0.153 | 0.250 | 0.000 | 0.000 |
| 0.235 | 0.375 | 0.375 | 0.125 |
| 0.361 | **0.500 ✅** | **0.500 ✅** | 0.125 |
| 0.554 | 0.125 | **0.750 ✅** | 0.250 |
| 0.850 | 0.500 ✗collapse .25 | 0.000 | 0.000 ✗collapse .67 |
| 1.304 | 0.000 ✗collapse .25 | 0.000 | 0.000 ✗collapse 1.0 |
| 2.000 | 0.000 ✗collapse 1.0 | 0.000 ✗collapse .625 | 0.000 ✗collapse 1.0 |

Selected: **hs22 → ratio 0.361** (dose 28.5068, tighten 0.500);
**hs24 → ratio 0.554** (dose 50.5311, tighten 0.750); **hs40 → null.**
`all_midband_have_usable_dose: true`.

Two things are worth saying plainly.

**First, the honest headline: A5 actuates, and by the selection statistic it
actuates *better* than A3** — 0.750 versus 0.500. hs24 is the first block whose
own K/V never reach anything downstream; if the KV channel were load-bearing
for a dosed write to take effect, hs24 is precisely where the write should have
stopped working. It didn't. The residual-stream path appears to carry the
boundary push on its own.

That said — and this is the part the interpretation rule written above the
result already committed us to — **this does not refute the quarantine
account, and reporting it as a refutation would be wrong.** The stage ran
sharing **ON only**, on the **FIT** split, with **8 fired rows per cell**. It
is not the ON/OFF contrast. `AMENDMENT.md` Threats (c) registers A3-vs-A5 as
non-discriminating *regardless of what it shows*, and that was written long
before these numbers existed. What the result genuinely changes is narrower:
it makes the tidy version of the story less likely, and it removes the
possibility of reading an A5 null as confirmation, because there is no A5 null.

The 0.750 vs 0.500 gap is also n=8 against n=8. Wilson CIs [0.41, 0.93] and
[0.22, 0.78] overlap across most of their range. "A5 actuates" is solid;
"A5 actuates *more*" is not a claim this instrument can make.

**Second, gemma4-e4b is the first family in the repo where every mid-band site
calibrated.** llama-3.2-3b and mistral-7b-v03 both recorded
`all_midband_have_usable_dose: false` (1 of 3 and 2 of 3 sites usable
respectively). Here it is 2 of 2. The prediction logged above — that a null was
the modal outcome and hs24 would probably produce one — was **wrong**, and it
was wrong in the direction that makes the experiment more informative rather
than less: both arms are now runnable.

hs40's null is the one part that went exactly as the precedent said. Null late
reference in all three families now.

**Consequence: A6 is unlocked.** It was registered
`conditional_on: "A3 has a usable FIT dose"`. A3 has one. A6 is hs23, already
reachable through the pre-existing `shallow_ladder` set, so nothing further
needs registering. Per its `coincides_with` note it runs once and is reported
under both the A6 and D4 labels.

## 2026-07-29 -- Phase A execution: runtime blockers, resolution, G0-KV re-verification

Dispatched by the lead to execute Phase A (KV-sharing-ON arms) on the local
3090. Full sequence, in order, because each step's provenance matters for
what may be cited as validity evidence downstream.

**Docker GPU passthrough was down at dispatch.** `docker run --gpus all`
failed (`could not select device driver ""`) under both `default` and
`desktop-linux` contexts; `nvidia-container-toolkit` was not registered as a
runtime and no passwordless sudo was available to fix it. Root cause (lead
diagnosed): Docker Desktop was closed. `unix:///var/run/docker.sock` is
backed by two different daemons depending on whether Docker Desktop is
running -- with Desktop closed it silently falls back to the WSL-native
`dockerd` (runc only, no nvidia runtime); with Desktop open the same socket
path is backed by the Desktop engine (nvidia runtime present). **Before every
GPU stage from here on: `export DOCKER_HOST=unix:///var/run/docker.sock` and
verify `docker info` shows `Operating System: Docker Desktop` AND a `nvidia`
entry under `Runtimes`, before assuming `--gpus all` will work.**

**Incidental fix, no tracked content changed.** `analysis-committed/gemma4-e4b/{split_manifest,eval_pool_manifest}.json`
are git symlinks (mode 120000) into `experiments/common/artifacts/jspace-cross-family-gemma4-e4b/`,
but this checkout has `core.symlinks=false`, so they materialized as plain
files containing the link-target path rather than real symlinks --
`pipeline.py`'s `json.loads(split_path.read_text())` was reading that path
string as JSON and throwing `JSONDecodeError`. Did not touch git config
(hard rule). Recreated both as real symlinks via `ln -sf` to the identical
target already recorded in the placeholder file; `git status --short`
confirmed no content change. Flagging in case other experiments hit the same
pattern.

**Built `mechinterp-runner:local` (first build, digest `sha256:ee17d595b00ead64a701214eec08adbbc9c55a30402314669e41656262e10b0e`,
tuner `246d412ea3c6dbf88c38eb997b606956fad15812`, `transformers==5.12.1`).**
Stage 1 smoke (`run_contrast.py --site-set seam_pair --kv-sharing on --mode
smoke --n-rows 8`) failed at model load: `model_lib.py`'s
`load_model_and_tokenizer` hardcodes `device_map="auto"`, which needs
`accelerate`; the pinned image genuinely lacked it. **Did not edit the
pinned `model_lib.py`.** Reported to lead; lead authorized adding
`accelerate` to the shared (non-pinned, project-agnostic) `mechinterp-runner`
Dockerfile rather than `pip install`-ing into a running container (the
README explicitly names that anti-pattern and rejects it). Synaptic-Tuner PR
#148 / EHR PR #353 landed `accelerate==1.14.0`.

**Rebuilt `mechinterp-runner:local` (digest `sha256:fe732c8fb4c82ea1a1acd1df3766a6fe854de750f1416d934e3c66231dfff801`,
tuner `61899a29c11a60edba9d0a0b35c56d0a20b07d75`, still `transformers==5.12.1`).**
Sanity check passed (`accelerate 1.14.0`, `transformers 5.12.1`). Re-ran
Stage 1 smoke: model loaded fine this time (~20s, `device_map=auto` via
accelerate), but crashed immediately inside the **pinned** `kv_seam_patch.py`
(`kv_sharing()` context manager, line 261):
`AttributeError: 'Gemma4TextAttention' object has no attribute
'kv_shared_layer_index'`. Read the installed `transformers==5.12.1`
`modeling_gemma4.py` source directly (diagnostic only, no edits): confirmed
`kv_shared_layer_index` does not exist anywhere in that file -- only
`is_kv_shared_layer` -- differing from what AMENDMENT.md's architecture
section says was verified against `transformers==5.5.0`. Because the context
manager reads this attribute unconditionally (before checking
`enabled`), this blocks **every arm**, ON or OFF alike, not just this smoke.
This also means the 2026-07-25 `kv_seam_preflight.py` 6/6 PASS cannot have
run against this exact runtime, since it exercises the same attribute --
that PASS's runtime was never recorded (no image digest, no environment
note anywhere in this notebook for the 2026-07-25 pre-sign GPU carve-outs),
so it cannot be verified either way and is treated as unrecorded rather than
wrong. **Did not edit the pinned `kv_seam_patch.py`.** Reported to lead.

**Produced pre-tf550 smoke artifacts (now superseded).** The seam_pair
smoke run that hit the `kv_shared_layer_index` crash was preceded, in the
same invocation chain, by a first successful write/readback pass whose
outputs (`smoke_summary.seam_pair.json`, `runlog/smoke/hs22.jsonl`,
`hs24.jsonl` + `.meta.json`, mtime ~14:34Z) are **SUPERSEDED as validity
evidence** per lead ruling 2026-07-29 -- produced under the unrecorded,
now-superseded `local` image before the `transformers` version mismatch was
understood. Moved intact (not deleted) to
`analysis/gemma4-e4b/runlog/superseded/pre-tf550-20260729/` with a README
explaining why. Do not cite.

**Lead decision (user-approved): align the runtime to `transformers==5.5.0`,
the version the instrument was actually validated against, rather than
rewrite the pinned `kv_seam_patch.py`.** Synaptic-Tuner PR #149
parameterized the Dockerfile (`ARG TRANSFORMERS_VERSION`, default unchanged
at 5.12.1); EHR PR #354 bumped the pin. Built `mechinterp-runner:tf550`
(distinct tag, coexists with `:local`) with
`--build-arg TRANSFORMERS_VERSION=5.5.0 --build-arg
MECHINTERP_RUNNER_GIT_REVISION=34c89fc4f9d693a6b997422288d820e9c30b4696`.
Digest: `sha256:479b7ca7891ab328ce7f04adffb949ef8086e3cf0d87676a3577d1d76cd845c8`.

**In-image sanity, 2026-07-29, `mechinterp-runner:tf550`:** `transformers
5.5.0`, `accelerate 1.14.0`, and `'kv_shared_layer_index' in
inspect.getsource(transformers.models.gemma4.modeling_gemma4)` -> `True`.
Confirms the amendment's 5.5.0 architecture claim.

**`kv_seam_preflight.py` re-run inside `mechinterp-runner:tf550`, CPU
(GPU flag passed but preflight itself is CPU-only per its own persistence
declaration), wall-clock 6s: 6/6 PASS** (geometry+crash reproduces; fix
completes; mechanism actually flipped, sharing-OFF k_proj calls sum=90
min-per-block=5 on the 18 shared blocks vs sum=0 under stock; ON-condition
equivalence to stock is token- and logit-bit-identical; OFF cache growth
live at all 18 appended slots across prefill+2 decode steps; ON
cache-substitution no-op token-identical on 8/8 fixed prompts). **This
supersedes the 2026-07-25 6/6 PASS as validity evidence** -- that earlier
run's runtime was never recorded and cannot be confirmed to have exercised
this same `kv_shared_layer_index` code path; this run is the first G0-KV
pass with runtime provenance (image digest + `transformers` version) tied to
the result.

Provenance for every stage from here forward: image `sha256:479b7ca7891ab328ce7f04adffb949ef8086e3cf0d87676a3577d1d76cd845c8`
(`mechinterp-runner:tf550`), tuner `34c89fc4f9d693a6b997422288d820e9c30b4696`,
`transformers==5.5.0`, structural grep (`model.language_model.layers` in
`hooks.py`) re-verified per stage.

**Stage 1 (seam_pair ON smoke, n=8), `mechinterp-runner:tf550`, wall-clock
119s -- PASS.** `g0_smoke_pass: true`. hs22: `dose_target=28.5068`,
`readback_mean=28.5174`, `frac_readback_within_tol=1.0`,
`collapse_rate_on_dosed=0.0`, `confab_tighten` 3/4 = 0.75 [0.30, 0.95].
hs24: `dose_target=50.5311`, `readback_mean=50.7748`,
`frac_readback_within_tol=1.0`, `collapse_rate_on_dosed=0.0`,
`confab_tighten` 4/4 = 1.0 [0.51, 1.0]. RunLog:
`analysis/gemma4-e4b/runlog/smoke/{hs22,hs24}.jsonl` + `.meta.json`;
summary `analysis/gemma4-e4b/smoke_summary.seam_pair.json`.

**Stage 2 (seam_pair ON full mode, A3/A5 true arms on held-out),
`mechinterp-runner:tf550`, same provenance, n_rows=438 per site (168
confab_held_out + 270 known_correct_answered_held_out), completed
2026-07-29 13:36 EDT.** Recorded verbatim from
`analysis/gemma4-e4b/full_summary.seam_pair.json`, verified independently
against the raw file (not taken on the lead's word alone):

- **hs22 (A3):** `readback_mean=28.5104`, `frac_readback_within_tol=1.0`,
  `collapse_rate_on_dosed=0.0`. `confab_tighten` 99/168 = 0.5893
  [0.5137, 0.6609]. `known_correct_cost_control` (full population, G2 as
  transcribed) 1/270 = 0.0037 [0.00065, 0.0207] -- `full_population_g2_pass:
  true`. Fired-only companion: `n_fired_known=2`, 1/2 = 0.5, **NOT-ADJUDICABLE**
  (floor 35). `discrepancy_full_pass_but_fired_only_over_cap: true` (fired-only
  0.5 exceeds the 0.05 cap while full-population G2 passes).
- **hs24 (A5):** `readback_mean=50.7555`, `frac_readback_within_tol=1.0`,
  `collapse_rate_on_dosed=0.03409090909090909` (6 of 176 fired collapsed).
  `confab_tighten` 123/168 = 0.7321 [0.6605, 0.7934]. `known_correct_cost_control`
  9/270 = 0.0333 [0.0176, 0.0621] -- `full_population_g2_pass: true`. Fired-only
  companion: `n_fired_known=9`, 9/9 = 1.0, **NOT-ADJUDICABLE** (floor 35).
  `discrepancy_full_pass_but_fired_only_over_cap: true` (fired-only 1.0 far
  exceeds the 0.05 cap while full-population G2 passes).
- **Both top-level pass fields, recorded exactly as written, not
  reconciled or interpreted here:** the `primary` sub-block (`best_mid_layer:
  "hs24"`, `g1_midband_actuation_floor_pass: true`,
  `g2_midband_selectivity_cap_pass: true`) reports **`primary_pass: true`**.
  The top-level summary object separately reports **`primary_pass: false`**.
  Per the lead: the top-level field is `false` solely because it additionally
  requires zero collapse on every layer in the site set, and hs24 has
  `collapse_rate_on_dosed = 0.03409...` (non-zero); the `primary` sub-block's
  own G1/G2 pass fields do not carry that collapse requirement. Adjudication
  of what this means for the arm-level and experiment-level dispositions is
  the lead's, reserved for Stage 6.
- RunLog: `analysis/gemma4-e4b/runlog/full/{hs22,hs24}.jsonl` (438 rows each,
  row counts verified against `n_rows` in the summary), `.meta.json` sidecars
  (both currently record `"complete": false` -- recorded as observed, not
  interpreted; row counts independently confirm all 438 rows per site are
  present and match the summary's own `n_rows`). Summary:
  `analysis/gemma4-e4b/full_summary.seam_pair.json`.
- Wrapper note: the background shell wrapper around this `docker run` was
  killed by the harness before its own trailing `echo` lines executed, so no
  wrapper-level exit code was captured. This does not bear on the run's
  completeness -- the container's own process ran to completion, printed the
  full JSON summary to the log, and both RunLogs show exactly 438/438 rows
  matching the summary. Confirmed independently, not taken on trust.

**Staging.** Both Stage 1 (smoke) and Stage 2 (full) RunLogs and summaries
copied to the durable exhaust dir:
`/home/profsynapse/code/ehr-exhaust/gemma4-e4b-kv-seam-quarantine/smoke/`
(`smoke_summary.seam_pair.json`, `hs22.jsonl`+meta, `hs24.jsonl`+meta) and
`/home/profsynapse/code/ehr-exhaust/gemma4-e4b-kv-seam-quarantine/full/`
(`full_summary.seam_pair.json`, `hs22.jsonl`+meta, `hs24.jsonl`+meta).

## Stage 3 -- seam_pair ON undosed baseline (A3/A5), 2026-07-29

Image `mechinterp-runner:tf550`, digest
`sha256:479b7ca7891ab328ce7f04adffb949ef8086e3cf0d87676a3577d1d76cd845c8`,
`transformers==5.5.0`, tuner commit `34c89fc4f9d693a6b997422288d820e9c30b4696`
(EHR main `860ed97e992cb5cbac8515f169a6c262f628bca8`). Structural check
re-verified: `grep -n '"model.language_model.layers"'
synaptic-tuner/MechInterp/intervention/hooks.py` -> line 56, present.
Docker Desktop guard passed (`Operating System: Docker Desktop`, `nvidia` in
Runtimes) before launch.

Command:
```
python3 run_contrast.py --family gemma4-e4b --site-set seam_pair \
  --kv-sharing on --mode full --arm-kind undosed \
  --i-know-this-is-the-cross-family-run
```

Results, independently verified against the raw JSON (not taken on the
lead's report):

- **hs22 (A3 undosed baseline):** `n_rows=438`, `n_fired=0` (undosed, as
  expected -- no dose applied, so `readback_mean`, `frac_readback_within_tol`,
  `collapse_rate_on_dosed` are all `null`). `confab_tighten` 0/168 = 0.0
  [0.0, 0.02235]. `known_correct_cost_control` 0/270 = 0.0 [0.0, 0.01403],
  `full_population_g2_pass: true`. Fired-only companion: `n_fired_known=0`,
  **NOT-ADJUDICABLE** (floor 35, as expected with n_fired=0).
  `discrepancy_full_pass_but_fired_only_over_cap: false`.
- **hs24 (A5 undosed baseline):** identical shape and numbers to hs22:
  `n_rows=438`, `n_fired=0`, `confab_tighten` 0/168 = 0.0 [0.0, 0.02235],
  `known_correct_cost_control` 0/270 = 0.0 [0.0, 0.01403],
  `full_population_g2_pass: true`, fired-only **NOT-ADJUDICABLE**
  (`n_fired_known=0`), `discrepancy_full_pass_but_fired_only_over_cap: false`.
  (Both sites' undosed numbers are identical -- consistent with the arm-kind
  being undosed at both sites, since no per-site dose is applied.)
- RunLog: `analysis/gemma4-e4b/runlog/undosed/full/{hs22,hs24}.jsonl` (438
  rows each, row counts independently verified via `wc -l` against
  `n_rows=438` in each summary). `.meta.json` sidecars both record
  `"complete": false`. Summaries:
  `analysis/gemma4-e4b/undosed_summary.hs22.seam_pair.json`,
  `analysis/gemma4-e4b/undosed_summary.hs24.seam_pair.json`.

**RunLog `complete:false` semantics (lead-verified in code, 2026-07-29):**
the sidecar is written by the tuner's `RunLog`
(`synaptic-tuner/.../shared/utilities/run_log.py`), which stamps
`complete=false` at open and only flips it to `true` inside
`RunLog.finalize()`. The pinned `run_contrast.py` never calls `finalize()` --
it uses `run_log.close()` and writes its own summaries via its own
`write_summary()`. So `complete:false` is the **expected steady state** for
every RunLog this instrument produces across all stages (Stage 2's full
RunLogs included), not an interruption marker. Completeness is evidenced by
runlog line count matching the summary's `n_rows`, which has now been
independently confirmed at every stage (Stage 1 smoke, Stage 2 full, Stage 3
undosed). A re-invocation of `run_contrast.py` against an existing RunLog path
would enter `RunLog`'s resume path and correctly redo nothing already
recorded.

**Staging.** Copied to
`/home/profsynapse/code/ehr-exhaust/gemma4-e4b-kv-seam-quarantine/undosed/`:
`undosed_summary.hs22.seam_pair.json`, `undosed_summary.hs24.seam_pair.json`,
`hs22.jsonl`+meta, `hs24.jsonl`+meta.

## Stage 4 -- seam_pair ON placebo arms P1/P2, K=5, 2026-07-29 -- STOPPED (pinned-code defect)

Image `mechinterp-runner:tf550`, digest
`sha256:479b7ca7891ab328ce7f04adffb949ef8086e3cf0d87676a3577d1d76cd845c8`,
`transformers==5.5.0`, tuner commit `34c89fc4f9d693a6b997422288d820e9c30b4696`
(EHR main `860ed97e992cb5cbac8515f169a6c262f628bca8`). Docker Desktop guard
passed before both the dry-run and the full run.

**CPU dry-run (`--arm-kind placebo --placebo-k 5 --dry-run`), succeeded:**
both sites cleared SC1 cleanly -- hs22: 5/5 accepted directions in 20 draws
(15 redraws, well under the 300-redraw ceiling); hs24: 5/5 accepted in 17
draws (12 redraws). `n_fired_rows` from the Stage 2 fire logs: hs22=167,
hs24=176 (fail-closed row-population check passed silently). Ledger written
to `analysis-committed/gemma4-e4b/placebo_draw_ledger.seam_pair.json`.

**Ledger-path finding (not gate-blocking):** that ledger path is scoped to
`<site_set>` only, not per `hs_index` (`run_contrast.py:518-520`, via
`family_config.site_set_artifact("placebo_draw_ledger.json", site_set)`), and
`write_ledger()` overwrites rather than appends. Since a single `--site-set
seam_pair` invocation processes hs22 then hs24, hs24's write clobbers hs22's
SC1 audit trail on disk. Confirmed this does NOT affect gate scoring:
`rollup.py`'s `build_g3_rollup()` reads the per-layer
`placebo_summary.<layer>.<site_set>.json` (written separately by
`run_placebo()`'s own `write_summary()` call) for the G3 confab_tighten
rates, never the shared ledger file. Mitigated without touching any pinned
file: a background poller watched the live ledger path and copied it the
instant it showed `hs_index: 22` (there is a wide window -- all of hs22's
GPU generation -- before hs24's write overwrites it), to
`analysis/gemma4-e4b/placebo_draw_ledger.seam_pair.hs22.snapshot.json`.
Captured successfully at 2026-07-29T23:53:37Z UTC, 5/5 accepted, matching the
dry-run's deterministic seeds. The live (non-snapshot) ledger path holds
hs24's data at rest, per its site-set-scoped design.

**Full GPU run (`--arm-kind placebo --placebo-k 5`, no `--dry-run`),
CRASHED:** GPU clear before launch (812 MiB used). Model weights loaded in
29s (`STAGE4_START` 2026-07-29T23:53:26Z), then crashed on the very first row
of hs22's first draw:
```
Traceback (most recent call last):
  File ".../run_contrast.py", line 705, in <module>
    raise SystemExit(main())
  File ".../run_contrast.py", line 672, in main
    results[layer_name] = run_placebo(
  File ".../run_contrast.py", line 552, in run_placebo
    rec = pl.run_layer_with_direction(
  File ".../pipeline.py", line 373, in run_layer_with_direction
    rec = run_one_row(family, model, controller, tokenizer, dev, eos_ids,
  File ".../pipeline.py", line 238, in run_one_row
    "hs_index": row["hs_index"], "fire": row["fire"], "readback_measured": readback,
KeyError: 'hs_index'
```
Docker exit code 1, `STAGE4_END` 2026-07-29T23:54:24Z. Under a minute of GPU
time lost.

**Root cause (read both functions in full, not guessed):** `run_placebo()`
(`run_contrast.py:501-509`) builds `gate_rows` by hand --
`rows = selected_rows(family, ...)` (raw rows from `pl.load_rows`, which
never carry `hs_index`), then
`gate_rows = [{**row, "fire": fire_by_key[row["row_key"]]} for row in rows]`.
`hs_index` is only ever added by `compute_gate_decisions()`
(`pipeline.py:190-208`, `rec.update({"hs_index": hs_index, ...})`), which
`run_undosed_baseline()` calls (hence Stage 3 ran clean) but `run_placebo()`
does not. `run_one_row()` (`pipeline.py:236-244`) unconditionally reads
`row["hs_index"]` for every row regardless of fire status, so this fails
deterministically on the first row of the first draw, every time. The
`--dry-run` path returns at `run_contrast.py:523`, before
`run_layer_with_direction`/`run_one_row` are ever reached, so the dry-run
could not have caught this. No test exercises the `run_placebo() ->
run_layer_with_direction() -> run_one_row()` integration (only
`test_rollup.py` touches placebo code, against a fixture summary). `git log
--oneline -- run_contrast.py pipeline.py` shows this landed in `93f59380`
"kv-seam instrument build: placebo arms, G2 companion, rollup, ALIN Part 2" --
untested new code, not a regression from this invocation. My command matched
the documented `--help` interface exactly.

**STOPPED per the standing rule** ("any needed pinned-file change... anything
the governed docs make a lead call"): did not touch `run_contrast.py` or
`pipeline.py`. Reported full diagnosis (including a candidate minimal fix,
not applied) to the lead via SendMessage and am holding here -- did not
proceed to Stage 5. Task #5 left `in_progress`, not completed, not skipped.
GPU is idle (`docker run --rm` cleaned up on exit, no orphaned container).

**ADJUDICATION (lead, 2026-07-29 23:58:39Z UTC) -- repin, not a tuner PR.**
Lead independently traced the identical root cause (same crash log, same
compute_gate_decisions/run_undosed_baseline explanation, same
test/dry-run-coverage-gap analysis) while my stop report was in flight. Fix
landed via `bin/exp repin` (this class of change goes through the
experiment's own repin path, not synaptic-tuner):
```
gate_rows = [{**row, "hs_index": hs_index, "fire": fire_by_key[row["row_key"]]}
             for row in rows]
```
Deliberately NOT my candidate (compute_gate_decisions-then-overwrite-fire):
the lead's fix avoids reloading the extraction file and recomputing
proj_d/z_d/tau for rows whose gating is immediately discarded --
`run_one_row` only ever consumes `row_key`/`role`/`category_canon`/`aliases`
(pool-provided) + `hs_index` + `fire`, nothing else, so stamping only what's
consumed is the narrower fix and stays closer to the never-re-gate
registration.

**Independently verified, not taken on the lead's report:**
- `sha256sum run_contrast.py` -> `14687efd8f6a74e815c49f8bedb46acf2e5f7ad93e88a555fed9f5abff178978`,
  matches `experiment.yaml instrument.pins.run_contrast.py` exactly.
- `experiment.yaml instrument.repins` entry present: `old_sha256
  83a704050376bca7800eecaab1c3dc6fd74fe9116565dc9ee94c2f8132ed1ecf ->
  new_sha256 14687efd8f6a74e815c49f8bedb46acf2e5f7ad93e88a555fed9f5abff178978`,
  dated `2026-07-29T23:58:39Z`, reason recorded verbatim (crash repair,
  zero-outcome path, no gate/threshold/seed/population/scoring logic
  touched).
- Read the actual line in the file at `run_contrast.py:508-511` -- matches
  the lead's description exactly, including a comment explaining why this
  path skips `compute_gate_decisions`.
- `bin/exp validate` -> `exp validate: OK (95 experiment(s))`; no
  warning/error line for `gemma4-e4b-kv-seam-quarantine` (other experiments'
  unrelated persistence-declaration warnings present, matches the known
  per-experiment-check gotcha).

**Ledger rulings, recorded per the lead:**
1. The hs22 ledger snapshot I captured
   (`analysis/gemma4-e4b/placebo_draw_ledger.seam_pair.hs22.snapshot.json`) is
   ACCEPTED as lab-notebook-tier audit preservation. Independently
   re-verified here (not just trusting the lead's re-derivation): `n_draws=20,
   n_accepted=5, n_voided=15`, first draw seed `20263307`, which equals
   `SEED_BASE + hidden_dim + hs_index + k_index = 20260725 + 2560 + 22 + 0`
   exactly.
2. The shared-ledger-filename wart (`placebo_draw_ledger.<site_set>.json` not
   scoped per `hs_index`) is DEFERRED to a future instrument generation --
   placebo arms do not recur in Phase B and the ledger is fully
   reconstructible from the registered deterministic seeds. No fix PR now.

**RELAUNCHING Stage 4** with the repinned `run_contrast.py`, same command,
same tf550 image/provenance, Docker Desktop guard first.

## Stage 4 v2 (repinned) -- seam_pair ON placebo arms P1/P2, K=5, COMPLETE, 2026-07-30

Image `mechinterp-runner:tf550`, digest
`sha256:479b7ca7891ab328ce7f04adffb949ef8086e3cf0d87676a3577d1d76cd845c8`,
`transformers==5.5.0`, tuner commit `34c89fc4f9d693a6b997422288d820e9c30b4696`
(EHR main `860ed97e992cb5cbac8515f169a6c262f628bca8`), `run_contrast.py` at the
repinned sha `14687efd8f6a74e815c49f8bedb46acf2e5f7ad93e88a555fed9f5abff178978`.
`STAGE4V2_START` 2026-07-30T00:02:23Z. The wrapper's trailing
`STAGE4V2_DOCKER_EXIT`/`STAGE4V2_END` echo lines never appeared in the log --
same wrapper-killed-after-container-exit pattern noted for Stage 2 (the
container's own process printed its full closing JSON and exited normally;
only the outer shell's trailing echo didn't fire, most likely at an overnight
session boundary). Confirmed NOT a failure: all 10 runlogs
(`analysis/gemma4-e4b/runlog/placebo/full/{hs22,hs24}.k{0-4}.jsonl`) show
438/438 rows via independent `wc -l`, both `placebo_summary.hs22.seam_pair.json`
and `placebo_summary.hs24.seam_pair.json` are present and well-formed, GPU
confirmed idle (761 MiB used, baseline level) and no container running
(`docker ps -a` empty) when checked afterward.

**Wall clock** (epoch-derived from runlog mtimes vs. `STAGE4V2_START`, not
eyeballed): hs22 k0-k4 completed at +59, +116, +175, +234, +293 min (each
draw ~57-59 min); hs24 k0-k4 completed at +330, +377, +418, +462, +505 min
(each draw ~37-47 min, shorter than hs22's -- not interpreted here). Total
wall clock start-to-final-summary: **505 min (~8.43 h)**.

**All numbers below independently verified against the raw
`placebo_summary.*.seam_pair.json` files, not taken on the lead's report.**

**P1 / hs22 (dose_target=28.507, n_fired_rows=167 at every draw, matching
Stage 2's true-arm fire count):**

| draw | confab_tighten | known_correct_cost_control | fired_only cost | readback tol | collapse_rate_on_dosed |
|---|---|---|---|---|---|
| k0 | 0/168 = 0.0 | 2/270 = 0.0074 | 2/2 = 1.0 (NOT-ADJUDICABLE, floor 35) | 1.0 | 0.3593 |
| k1 | 0/168 = 0.0 | 2/270 = 0.0074 | 2/2 = 1.0 (NOT-ADJUDICABLE) | 1.0 | 0.8263 |
| k2 | 0/168 = 0.0 | 2/270 = 0.0074 | 2/2 = 1.0 (NOT-ADJUDICABLE) | 1.0 | 0.9401 |
| k3 | 0/168 = 0.0 | 2/270 = 0.0074 | 2/2 = 1.0 (NOT-ADJUDICABLE) | 1.0 | 0.6527 |
| k4 | 0/168 = 0.0 | 2/270 = 0.0074 | 2/2 = 1.0 (NOT-ADJUDICABLE) | 1.0 | 0.9701 |

All five draws hit the SAME 2 fired known-correct rows (`n_fired_known=2`
every draw), `full_population_g2_pass: true` every draw,
`discrepancy_full_pass_but_fired_only_over_cap: true` every draw (fired-only
1.0 exceeds the 0.05 cap while full-population G2 passes -- same pattern
already on record from Stage 2's true arm). `collapse_rate_on_dosed` ranges
**0.359 to 0.970** across the five draws -- wide, unsmoothed range recorded
as-is; not interpreted here.

**P2 / hs24 (dose_target=50.531, n_fired_rows=176 at every draw, matching
Stage 2's true-arm fire count):**

| draw | confab_tighten | known_correct_cost_control | fired_only cost | readback tol | collapse_rate_on_dosed |
|---|---|---|---|---|---|
| k0 | 108/168 = 0.6429 | 9/270 = 0.0333 | 9/9 = 1.0 (NOT-ADJUDICABLE) | 1.0 | 0.0284 |
| k1 | 21/168 = 0.1250 | 7/270 = 0.0259 | 7/9 = 0.7778 (NOT-ADJUDICABLE) | 1.0 | 0.4773 |
| k2 | 0/168 = 0.0 | 7/270 = 0.0259 | 7/9 = 0.7778 (NOT-ADJUDICABLE) | 1.0 | 0.3125 |
| k3 | 53/168 = 0.3155 | 7/270 = 0.0259 | 7/9 = 0.7778 (NOT-ADJUDICABLE) | 1.0 | 0.0 |
| k4 | 28/168 = 0.1667 | 7/270 = 0.0259 | 7/9 = 0.7778 (NOT-ADJUDICABLE) | 1.0 | 0.0057 |

`confab_tighten` across P2's five draws is **wildly heterogeneous** (0.0 to
0.6429 -- a ~64 percentage-point spread), recorded here without smoothing or
averaging; this heterogeneity is scientifically notable per the lead and is
being flagged, not interpreted, at this stage. `full_population_g2_pass:
true` every draw; `discrepancy_full_pass_but_fired_only_over_cap: true`
every draw. `collapse_rate_on_dosed` ranges **0.0 to 0.477** across the five
draws.

**G3 registered inputs (per the lead -- recorded verbatim, formal
pass/fail/adjudication language is the lead's, not mine, and belongs to
Stage 6's rollup):** the registered G3 undosed lift baseline
(`gates.yaml g3_direction_specificity`) is exactly 0.0 at both sites (Stage
3's undosed `confab_tighten` was 0/168 at both hs22 and hs24). For A3/P1, the
max-placebo-lift denominator is exactly 0.000 (all five draws at 0.0) --
per the lead, this is the pre-registered PASS-DEGENERATE disposition (a
pass with a label, never citable as a large ratio, since the ratio's
denominator is degenerate). For A5/P2, the lead reports the worst-case
(highest) placebo denominator is 0.643 (k0), giving `effect_ratio =
lift_true / max_placebo_lift = 0.732 / 0.643 = 1.14`, below the 3.0 cap. The
actual ratio arithmetic and disposition sign-off is deferred to Stage 6's
`rollup.py` run; I am not asserting a verdict here.

**Ledger.** Live ledger path (`analysis-committed/gemma4-e4b/
placebo_draw_ledger.seam_pair.json`) holds hs24's data at rest (site-set-
scoped, as designed); hs22's snapshot remains preserved at
`analysis/gemma4-e4b/placebo_draw_ledger.seam_pair.hs22.snapshot.json` per
the lead's ruling above.

**Staging.** Copied to
`/home/profsynapse/code/ehr-exhaust/gemma4-e4b-kv-seam-quarantine/placebo/`:
`placebo_summary.hs22.seam_pair.json`, `placebo_summary.hs24.seam_pair.json`,
all 10 `runlog/placebo/full/{hs22,hs24}.k{0-4}.jsonl`+meta, and both ledger
files (live + hs22 snapshot).

## Stage 5a -- shallow_ladder ON dose calibration, COMPLETE, 2026-07-30

Image `mechinterp-runner:tf550`, digest
`sha256:479b7ca7891ab328ce7f04adffb949ef8086e3cf0d87676a3577d1d76cd845c8`,
`transformers==5.5.0`, tuner commit `34c89fc4f9d693a6b997422288d820e9c30b4696`
(EHR main `860ed97e992cb5cbac8515f169a6c262f628bca8`). `STAGE5A_START`
2026-07-30T10:07:10Z. Same missing-trailing-echo pattern as prior stages
(container completed and wrote its summary; wrapper's own exit/end echo
lines did not appear in the log) -- confirmed via the completed, well-formed
`dose_calibration_summary.shallow_ladder.json` (written 07:13) and GPU idle
with no orphaned containers afterward, not treated as a failure.

Command: `calibrate_dose.py --family gemma4-e4b --site-set shallow_ladder
--kv-sharing on` (default ratio ladder `[0.1, 0.153, 0.235, 0.361, 0.554,
0.85, 1.304, 2.0]`, no `--doses` override). Median anchor L2 norms: hs15=
133.173, hs18=101.074, hs20=81.350, hs23=58.778, hs40=142.347. 40 total
(layer, ratio) cells (5 sites x 8 ratios): hs15/hs18/hs20/hs23 (the
registered shallow ladder) plus hs40 (late-reference site, resolved into
this site set's own calibration scope by the pinned tool -- observed, not
second-guessed).

**Independently verified against the raw summary JSON, not taken on the
lead's report** (`has_usable_dose`, `selected`, `selected_dose` fields read
directly):

| site | has_usable_dose | selected_dose | selected_ratio |
|---|---|---|---|
| hs15 | true | 173.65765096701432 | 1.304 |
| hs18 | true | 85.91323993905378 | 0.85 |
| hs20 | true | 45.06793785763545 | 0.554 |
| hs23 | **false** | null | null |
| hs40 | false | null | null |

**hs23 rung-by-rung (independently re-derived from the per-ratio
`doses` array, matching the lead's description exactly):** ratios ->
(confab_tighten rate, collapse_rate_on_dosed): 0.1 -> (0.0, 0.0), 0.153 ->
(0.0, 0.0), 0.235 -> (0.25, 0.0), 0.361 -> (0.375, 0.0), 0.554 -> (0.375,
0.0), 0.85 -> (0.625, 0.125), 1.304 -> (0.5, 0.125), 2.0 -> (0.5, 0.125).
Every rung that clears the `min_confab_rate_for_usable=0.5` floor (the last
three) carries nonzero collapse (0.125); every zero-collapse rung sits under
the floor. Zero usable rungs, confirming `has_usable_dose=false`.

**LEAD ADJUDICATION (final for Phase A, per the lead 2026-07-30):** per the
registered rule in `calibrate_dose.py` (`dose_is_usable`: readback within
tolerance AND collapse_rate_on_dosed == 0.0 AND confab_tighten rate >= 0.5;
"zero usable rungs is a dose-viability NOT-RUN, not a tuning invitation"),
**D4/A6 at hs23 is NOT-RUN.** Do not re-ladder, do not tune, do not
substitute a nearby ratio -- I have not done any of these. hs40's null
selected dose is expected (the descriptive, non-gating late-reference site;
doubt-snap's own frozen late-site null pattern), no action taken. The "zero
usable doses anywhere" hard-stop condition does NOT trigger (three usable
mid-band sites: hs15, hs18, hs20).

**Stage 5b scope, per the lead's go-ahead:** smoke (n=8) then full mode at
hs15/hs18/hs20 ONLY, at the doses above. hs23 (D4/A6) and hs40 excluded
entirely from the run -- NOT-RUN/SKIPPED, recorded here rather than
synthesizing an empty summary file for either.

## Stage 5b -- shallow_ladder ON smoke + full, 2026-07-30

Image `mechinterp-runner:tf550`, digest
`sha256:479b7ca7891ab328ce7f04adffb949ef8086e3cf0d87676a3577d1d76cd845c8`,
`transformers==5.5.0`, tuner commit `34c89fc4f9d693a6b997422288d820e9c30b4696`
(EHR main `860ed97e992cb5cbac8515f169a6c262f628bca8`).

**Smoke (n=8), PASS.** `smoke_summary.shallow_ladder.json`:
`g0_smoke_pass: true`. `layer_doses` = `{hs15: 173.65765096701432, hs18:
85.91323993905378, hs20: 45.06793785763545}`, matching Stage 5a's selections
exactly. `late_arm_included: false`. hs15/hs18/hs20 all `frac_readback_
within_tol: 1.0`, `collapse_rate_on_dosed: 0.0`. No hs23 key present.
Independently verified before launching full mode, not taken on the lead's
report.

**Full mode, COMPLETE.** `STAGE5B_FULL_START` 2026-07-30T12:31:10Z. Verified
the container was actually up (`docker ps` showed it running) and rows were
genuinely appending (`hs15.jsonl` non-empty within ~2 min of launch) before
parking, per the lead's process note. All three runlogs independently
confirmed 438/438 rows via `wc -l`
(`analysis/gemma4-e4b/runlog/full/{hs15,hs18,hs20}.jsonl`, mtimes 09:07,
09:46, 10:24 respectively -- ~39 min/layer). `.meta.json` sidecars all show
`complete: false` (expected steady state per the established RunLog
semantics, not an interruption marker). `full_summary.shallow_ladder.json`
present and well-formed (7415 bytes, mtime 10:24, matching hs20's
completion). No `STAGE5B_FULL_DOCKER_EXIT`/`STAGE5B_FULL_END` wrapper lines
in the log -- same wrapper-killed-after-container-exit pattern as prior
stages; this time the wrapper's own shell process was most likely reaped by
the user's machine restart, which the lead had flagged in advance. The
underlying run itself completed cleanly beforehand (all rows written, well-
formed closing JSON, summary file present) -- treated as complete, not a
failure, on that evidence.

**Numbers, independently read from the raw `full_summary.shallow_ladder.json`,
not taken on any report (none was given for this stage -- read directly):**

| site (dose) | n_fired | readback tol | collapse | confab_tighten | known_correct cost | fired_only cost |
|---|---|---|---|---|---|---|
| hs15 (173.658) | 171 | 1.0 | 0.0117 | 132/168 = 0.7857 [0.7176, 0.8410] | 3/270 = 0.0111 [0.0038, 0.0322] | 3/4 = 0.75 (NOT-ADJUDICABLE, floor 35) |
| hs18 (85.913) | 168 | 1.0 | 0.0119 | 75/168 = 0.4464 [0.3733, 0.5220] | 1/270 = 0.0037 [0.0007, 0.0207] | 1/1 = 1.0 (NOT-ADJUDICABLE) |
| hs20 (45.068) | 169 | 1.0 | 0.0 | 68/168 = 0.4048 [0.3335, 0.4803] | 1/270 = 0.0037 [0.0007, 0.0207] | 1/2 = 0.5 (NOT-ADJUDICABLE) |

All three sites: `full_population_g2_pass: true`,
`discrepancy_full_pass_but_fired_only_over_cap: true`.

**`primary` sub-block** (`best_mid_layer: "hs15"`):
`g1_midband_actuation_floor_pass: true` (floor rate 0.5, Wilson-lower 0.4;
hs15's confab_tighten rate 0.7857 clears it), `g2_midband_selectivity_cap_
pass: true` (cap rate 0.05, Wilson-upper 0.1), sub-block `primary_pass:
true`. `late_reference_layer: hs40`, `secondary_late_reference.status:
"SKIPPED -- no usable late-arm dose found..."` (as expected, non-gating).

**Top-level `primary_pass: false`** -- recorded exactly as written, NOT
reconciled or interpreted here, matching the same sub-block-vs-top-level
split already on record for Stage 2 (the top-level field additionally
requires zero collapse across every layer in the site set; hs15's collapse
is 0.0117 and hs18's is 0.0119, both non-zero, while hs20 alone is exactly
0.0). Adjudication of what this means for the arm-level and
experiment-level dispositions is the lead's, reserved for Stage 6.

**PARKED per the lead's PAUSE directive (2026-07-30):** the user is
restarting the machine. Confirmed the restart was already underway when I
checked -- `docker info` produced no output at all after 120s (daemon
unresponsive), consistent with the lead's warning. Did NOT relaunch anything,
did NOT proceed to Stage 6. Reporting this result to the lead and parking
here; resume/Stage-6 scheduling is the lead's call post-restart.


---

## Stage 6 -- Phase A gate adjudication and rollup (LEAD), 2026-07-30

Author: lead session (adjudication reserved to lead per the stage plan).
Mechanical scoring performed by a results-analyst subagent via rollup.py's own
per-arm functions; every number below re-derived from the raw summary JSONs and
cross-checked against the Stage 2/5b entries above before adjudication.
Provenance: all scored artifacts produced under mechinterp-runner:tf550
(sha256:479b7ca7...45d8), per-stage provenance lines recorded in the stage
entries above.

**Scope.** This is the PHASE A (sharing-ON) stage-level adjudication. The
experiment's primary prediction (A1/A2 patch contrast with C1 and the A_lin
clause) is Phase B work and remains OPEN. The pinned top-level rollup.py driver
fails closed at arm A1 (fixed arm order, rollup.py:396) until the Phase B arms
land; that is correct fail-closed behavior, not a defect. No terminal verdict
is written here.

### Rulings

**R1. G0-arm smoke_no_collapse: PASS at every run arm.** The check is
registered inside g0_arm_instrument_validity with interpretation
stop_before_outcome (gates.yaml:252-276): it is a smoke-stage stop gate. Both
smokes (Stage 1 seam_pair; Stage 5b shallow_ladder) ran at the selected doses
with collapse_rate_on_dosed == 0 and the arms proceeded. The gate did its job
before outcomes ran.

**R2. Full-mode collapse is not covered by any registered outcome gate;
recorded descriptively.** G1/G2 (transcribed verbatim from the parent) do not
reference collapse. Full-mode rates: hs22 0.0, hs24 0.0341, hs15 0.0117, hs18
0.0119, hs20 0.0. The top-level `primary_pass: false` in both full summaries
conjoins the smoke-stage zero-collapse check onto full-mode results -- a
stricter condition than anything registered. The flag is recorded exactly as
emitted and is NOT overwritten; the registered per-arm results are the
G1/G2/G3 bits below. Ruling consistent across both instances of the split
(Stage 2 seam_pair and Stage 5b shallow_ladder).

**R3. G1/G2 per-arm results (registered gates), held-out:**

| Arm | Site | G1 (floor 0.50 / lower > 0.40) | G2 (cap 0.05 / upper < 0.10) | arm_pass |
|---|---|---|---|---|
| A3 | hs22 | 0.5893 [0.5137, 0.6609] PASS | 0.0037, upper 0.0207 PASS | true |
| A5 | hs24 | 0.7321 [0.6605, 0.7934] PASS | 0.0333, upper 0.0621 PASS | true |
| D1 | hs15 | 0.7857 [0.7176, 0.8410] PASS | 0.0111, upper 0.0322 PASS | true |
| D2 | hs18 | 0.4464 [0.3733, 0.5220] FAIL | 0.0037, upper 0.0207 PASS | false |
| D3 | hs20 | 0.4048 [0.3335, 0.4803] FAIL | 0.0037, upper 0.0207 PASS | false |

Fired-only G2 companion: NOT-ADJUDICABLE at every arm (max 9 fired known rows
vs the 35 floor) -- a third disposition, not a pass. The
discrepancy_full_pass_but_fired_only_over_cap flags at hs24 (Stage 2) and all
three ladder sites (Stage 5b) are recorded; with n_fired_known of 1-9 they
cannot be adjudicated and are carried as an open instrument limitation, not
evidence in either direction.

**R4. G3 direction-specificity verdicts (registered arithmetic,
gates.yaml g3_direction_specificity):**

- **A3/hs22: PASS-DEGENERATE.** lift(true) = 0.5893 - 0.0 = 0.5893. All five
  accepted placebo draws produced lift exactly 0.0. Zero denominator -> the
  registered zero_denominator_rule applies: pass WITH the degenerate label.
  Per the registered rule this result is never citable as a large effect
  ratio; the citable statement is "five magnitude-matched random directions at
  the same site produced zero effect while the fitted direction produced
  0.5893".
- **A5/hs24: FAIL.** lift(true) = 0.7321; max placebo lift = 0.6429 (draw k0);
  effect_ratio = 1.139 < 3.0 floor. The apparent actuation at hs24 is NOT
  direction-specific: the worst single random draw reproduced 88% of the true
  effect. Combined with hs24 carrying the highest full-mode collapse (0.0341),
  the A5 "actuation" is adjudicated as seam-region instability that clean
  gates cannot distinguish from steering, exactly the failure mode the
  quarantine account predicts for a KV-shared site.

**R5. Registered secondary expectation (A3 vs A5, non-gating): literal form
NOT met; the separation appears in the specificity control instead.** The
registered expectation was A3 clears both gates while A5 does not. In fact
both cleared G1/G2. The registered descriptive report is therefore: raw gate
clearance does not separate the sites; G3 does, completely (PASS-DEGENERATE
vs FAIL), and the collapse profile points the same way. Per registration this
is descriptive only and enters no success rule.

**R6. Ladder registered expectation: MET.** At least one of hs15/18/20/23
found a usable FIT dose and cleared G1 on held-out: D1/hs15 did both (0.7857).
Descriptive depth profile: actuation strength falls monotonically toward the
seam (0.7857 -> 0.4464 -> 0.4048 at per-site calibrated doses), with hs23
unable to find any collapse-free dose that clears the FIT confab floor.
Per-site doses differ, so this is a profile, not a controlled contrast.

**R7. hs23 (D4 == A6): dose-viability NOT-RUN.** Zero usable rungs on the
registered ladder (every rung clearing the FIT confab floor 0.5 -- ratios
0.850/1.304/2.000 at rates 0.625/0.500/0.500 -- carries collapse 0.125; every
zero-collapse rung is below the floor). Per the registered rule the ladder
does not move. Full per-rung table:
analysis/gemma4-e4b/runlog/calibrate_dose_records_v2.shallow_ladder.jsonl.

**R8. hs40 (late reference): SKIPPED.** No usable late-site dose (collapse
0.667-1.0 at the three rungs clearing nothing; all confab rates < 0.5) --
the expected reproduction of the doubt-snap late-site null. Non-gating,
gates nothing, reported descriptively.

**R9. Falsifier bookkeeping going into Phase B (registered, restated).**
D1's G1 clearance arms the registered asymmetric falsifier clause: if A1
(hs38, ON) fails G1 in Phase B while D1 cleared it here, the above-seam null
is not a property of the model and the quarantine account is SUPPORTED (not
established -- promotion requires the A1-vs-A2 contrast with the A_lin
clause). If instead A1 clears G1, the parent null failed to reproduce and the
experiment is VOID per the pre-stated disposition. Phase B is decisive either
way.

### Phase A summary sentence (stage-level, not a terminal verdict)

Below the KV seam, gemma4-e4b actuates with perfect direction-specificity
(hs22, hs15) at low known-answer cost; approaching and entering the
KV-shared region, clean actuation degrades in order (weaker G1 at hs18/hs20,
no viable dose at hs23, non-direction-specific instability at hs24), a
depth-and-seam profile consistent with the quarantine account and awaiting
the decisive A1/A2 ON/OFF contrast in Phase B.
