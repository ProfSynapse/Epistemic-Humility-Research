# Gemma-4-E4B KV-sharing seam: is the mid-band null a quarantine artifact?

Status: **DRAFT (not signed; do not launch).** Drafted by a delegated agent
2026-07-24, then **re-grounded by the lead the same day** on the clean
`use_cache=True` activations: the withdrawn `0/176` framing, the withdrawn
G2-diagnosticity claim, the underived `n_fired_known < 10` threshold, and the
missing shallow-depth arms are all corrected below, and the corresponding blocks
in `gates.yaml` and `experiment.yaml` are corrected to match. The lead has **NOT
signed it**; several pre-sign items remain open (see "Open questions at sign").
Nothing in this rewrite moves a locked threshold; it changes what the numbers
are claimed to mean and adds descriptive, non-gating arms.

**Header updated 2026-07-25 — three clauses above were stale and are corrected
here rather than silently edited away.** (a) "the input dependency on the
unmerged parent branch is unresolved" — resolved; the render path is vendored
into this experiment and the cross-experiment PYTHONPATH dependency is gone.
(b) "`instrument.persistence` still needs measured smoke wall-clock timings —
the first item that costs GPU" — the timings are measured and declared, and they
cost **no** GPU; the smoke ran CPU-only, and `gate_fit.py` turned out to need no
checkpoint at all. (c) "**No GPU work has run for this experiment**" — no longer
true. Two lead-authorized pre-sign carve-outs have run, both recorded in
`cell.yaml execution.gpu_carve_outs`: the donor projection diagnostic, and the
`seam_pair` dose calibration. Both are FIT-split instrument work. **No arm has
run, `run_contrast.py` has not been executed in any mode, and no held-out row
has been touched** — that part of the original claim still holds and is the part
that matters.

Keep this document the prose home for the experiment. The machine state lives in
`experiment.yaml` and is never duplicated here.

## Motivation and posture

Posture: **Tier-2 exploratory.** Reported separately from the locked headline
matrix and never pooled with it. Its parent
(`j-space-cross-family-layer-contrast`) is itself Tier-2 exploratory; this
experiment does not reopen, revise, or re-adjudicate the parent, whose
gemma4-e4b disposition stands exactly as recorded.

### The result this follows from

**Rewritten 2026-07-24 (lead) off the corrupt activations, per the Tier 1
revision's "Open blockers" #1.** An earlier draft of this section presented the
parent's gemma result as a settled `0/176` write-verified behavioral null and
built the prediction on it. That framing is **withdrawn**. What the parent
actually recorded, at `AMENDMENT.md:637`, is that gemma's write arm was fit on
activations corrupted by `use_cache=False` and is therefore **uninterpretable,
not negative**. This experiment must be pre-registered against that weaker,
truer starting point.

`j-space-cross-family-layer-contrast` stopped `google/gemma-4-E4B-it` at the
registered G0 dose-viability rule (NOT-RUN, excluded from the cross-family
denominator). Every number that stop rested on shares one defect: on gemma-4-E4B
blocks 24-41 read donor K/V from blocks 22/23 *through the cache object*, so
running the extraction forward with `use_cache=False` starved them. hs00-hs24
were bit-identical to a correct run; hs25 collapsed to cos 0.732 and decayed to
0.075 by hs42. Every site the parent wrote to -- hs34, hs38, hs40, hs42 -- lies
in that region.

**What is corrupt-derived, and therefore carries no evidential weight here:**

- The `u_d` / `c_hat` write directions, the gate standardization
  (`mu_d`, `sigma_d`, `tau_frozen`), and the absolute dose targets at every
  mid-band site. Confirmed independently by median anchor L2 norm, which
  fingerprints the extraction a calibration was built from: the parent's
  `dose_calibration_summary.json` records 120.20 / 125.51 / 117.57 / 281.34 at
  hs34 / hs38 / hs40 / hs42, matching the **quarantined** safetensors exactly,
  against 154.08 / 156.06 / 142.35 / 236.35 on the clean extract
  (NOTEBOOK.md, 2026-07-24 "latest", F2).
- The mid-band KU readout AUCs of **0.9779 / 0.9815 / 0.9772**. Clean held-out
  equivalents are 0.9804 / 0.9770 / 0.9891 -- close enough that the *conclusion*
  "the gate fits above the 0.90 floor" survives, but the cited figures do not
  and must not be propagated.
- The `confab_tighten` = **0/176** pooled null. A direction fit to corrupt
  activations failing to steer is not evidence that the model is unsteerable.
  **No arm of this experiment may cite it as a measured null**, and the
  prediction below does not.

**What survives the defect and still motivates this experiment:**

- **The write reaches behavior.** Collapse onset is a real behavioral
  observation: at hs34/hs38 the ladder ran clean at ratios 0.100-0.361
  (`collapse_rate_on_dosed` = 0.00), with onset at 0.554 (0.778 at hs34, 0.400
  at hs38) and 1.00 by 0.850; at hs42 onset is the first rung tested, r0 = 0.100.
  *(This supersedes `arch_null_forensics_report.md` observation (E), which put
  hs42's onset at 0.153; the corrected figure is r0. Correction recorded in
  `dose_response_window.md`.)* Whatever the direction was, writing it hard enough
  destroys generation -- so the injection machinery is coupled to behavior, and a
  behavioral null cannot be explained by the write failing to arrive.
- **The metric is sharp on this substrate.** `clean_tighten` fires on
  **1662/1663** of gemma's own natural refusals and on **0/1393** undosed confab
  rows (NOTEBOOK.md, F1). A grader that hard-matches the literal string
  `"i don't know"` is exactly the shape that produced the KV-seam vacuity, so it
  was measured rather than assumed. It has both sensitivity and specificity here.
- **The llama positive control is untouched by the defect.** llama-3.2-3b has no
  cross-layer KV sharing and its extraction was bit-identical under either
  `use_cache` setting (min cos 1.000000), so the control below stands in full.

**Positive control -- the same instrument finds a wide window in llama.** Run
through the byte-identical pipeline, ladder, grader and generation contract,
llama-3.2-3b **hs17** shows actuation across ratios **0.235-1.304** (5 of 8
rungs) with `collapse_rate_on_dosed` = **0.000** throughout and
`confab_tighten` reaching 0.375 / 0.875 / 0.875 -- **Wilson lower bounds
13.7%-52.9%**, separated from zero, not a single-row fluke. llama's other three
tested sites (hs20, hs23, hs26) each also show at least one rung with nonzero
tighten at zero collapse. **This is what licenses the claim that the pipeline can
detect a window at all** -- it no longer licenses any claim that "no window" is
specific to gemma, because gemma's own no-window measurement is withdrawn.

**What this section does NOT do.** It establishes that the instrument can detect
a window (llama), that the write is coupled to behavior (collapse), and that the
grader can see a tighten on this substrate (F1). It does **zero** work
establishing that gemma has no window -- that measurement is withdrawn -- and
**zero** work discriminating *why* if it turns out not to. See "Competing
explanations": an inert-to-collapse-with-no-window signature, if this experiment
reproduces one on clean activations, is predicted **identically** by the
crystallization-gap / Linear Accessibility account, and nothing here may be read
as evidence for the KV-quarantine hypothesis.

A note on category, since the parent's framing is often quoted: the parent
distinguished gemma from the llama/mistral v1 stops, which were
**instrument-resolution-limited** (doses off-scale in the family's own units),
on the grounds that for gemma "the instrument reached the right band and the
effect simply was not there." **That distinction is suspended.** It was drawn
from the corrupt run; whether gemma belongs in a different category from the
resolution-limited stops is one of the things this experiment is being run to
find out, not an input to it.

### The mechanism this experiment tests

The parent's `analysis/gemma4-e4b/arch_literature_memo.md` §6 (lead-verified
2026-07-24 against the executing `transformers==5.5.0`
`models/gemma4/modeling_gemma4.py` and the pinned checkpoint config, snapshot
`fee6332c1abaafb77f6f9624236c63aa2f1d0187`) identifies a structural feature the
parent's site-selection rule never probed. Re-derived independently for this
draft from the same pinned config:

```
num_hidden_layers          = 42
num_kv_shared_layers       = 18
first_kv_shared_layer_idx  = 42 - 18 = 24        # blocks 24..41 are KV-SHARED
layer_types full_attention = [5, 11, 17, 23, 29, 35, 41]
donor(full_attention)      = block 23
donor(sliding_attention)   = block 22
store_full_length_kv       = True at blocks 22 and 23 ONLY
```

Per `modeling_gemma4.py:1198-1205`, a KV-shared block does not execute
`k_proj`/`v_proj` at all; it reads K/V out of
`past_key_values.shared_layers[donor]`. Every injection site the parent used --
hs34, hs38, hs40, hs42, i.e. the outputs of blocks 33, 37, 39, 41 -- lies
strictly downstream of blocks 22/23. The injected delta therefore reaches the
query path, the MLP, and the PLE branch of every later block, but is
**structurally barred from altering the keys or values any later layer attends
over**, because those were computed upstream and frozen.

**Stated precisely, because the strong form is wrong and the prediction below is
registered against the weak form.** `modeling_gemma4.py:1192` computes
`query_states = self.q_proj(hidden_states)` **unconditionally**, shared blocks
included. Attention is `softmax(QKᵀ)V`, so a write that changes Q changes the
attention weights; the write also reaches the FFN, the PLE branch, and the
residual stream, and hence the logits. The causal channel into blocks 24-41 is
therefore **narrowed, not severed**. It is wrong to say a write there cannot
influence attention routing. What it cannot do is change *what there is to
attend to*.

This matters for how a null is read. Under a severed channel, an above-seam null
would be near-tautological. Under a narrowed one it is not: the hypothesis is
that the surviving channel is too weak to carry a caution snap, which is a
quantitative claim that can fail. Any arm of this experiment that finds
above-seam actuation refutes the quarantine account outright; an above-seam null
is consistent with it but does not establish it, because a narrowed channel and
an absent effect are not distinguishable from the null alone.

**Hypothesis: the gemma null is a quarantine artifact of injecting above the
KV-sharing seam, not evidence that the model is unsteerable.**

Two lead-verified facts make the manipulation below possible: all 42 blocks
retain `k_proj`/`v_proj` weights (including the 18 shared ones), and the shared
blocks' `k_proj` Frobenius norms follow the same smooth depth trend as the
active blocks (~31 declining to ~22, with full_attention blocks
5/11/17/23/29/35/41 systematically elevated). They do not look like untrained
init. That is a necessary condition for the sharing-OFF arms, not a sufficient
one -- see Threats (b).

### Standing of this hypothesis: one candidate among several, NOT the leading one

**The "write lands + decodable + inert" signature is NOT a Gemma fingerprint, and
nothing in this document should be read as claiming it is.** Exclusivity is
withdrawn. Verified in the program's own library:

- `library/notes/internal-al-injection-null--true-checkpoint.md:141` (Amendment
  AL, **Qwen3-4B** GRPO-on-clean-SFT checkpoint): the propensity projection at
  the steered anchor moved -2.7133 against a commanded -2.7110 — readback ratio
  **1.0008** — and behavior did not move (all 1,564 unpushed rows reproduced
  their baseline grade; the primary gate MISSed, bootstrap CI [0.00, 0.00]).
  Supports the in-library mechanism
  `propensity-direction-reads-but-does-not-actuate-fabrication`.
- `library/concepts/mechanisms/trust-axis-injection-does-not-move-answer-abstain-revise-behavior.md`
  (Amendment AA, **Qwen3.5-4B**): writing the gate/dial probe directions back in
  does not move answer/abstain/revise behavior.

Those are different directions on different checkpoints from this instrument, so
they are not literal replications of the gemma cell — but they are the same
program hitting readback-verified behavioral inertness on **non-Gemma**
substrates.

What survives, and is the whole reason this experiment is worth running: KV
sharing is the only *structural* candidate that explains why **this** instrument
actuates on llama-3.2-3b and qwen3-4b but not on gemma4-e4b, and it is the only
candidate that makes a cheap, decisive, mechanism-toggling prediction. It is one
hypothesis among at least four (see "Competing explanations"), not the leading
one, and the design's job is to discriminate against the others.

### The seam is not where "block index < 24" puts it

**This draft corrects the site rule the design brief implied.** "Below the seam"
is not the same as "block index below 24". What matters is whether the write is
upstream of the **donor** blocks, and the donors are 22 and 23. Writing at
hs_index `N` means hooking the forward output of decoder block `N-1` (the
parent's convention: late reference block 39 = hs40), i.e. writing into the
residual stream that block `N` consumes. So:

| write site | = output of block | reaches sliding donor (blk 22)? | reaches full donor (blk 23)? | verdict |
|---|---|---|---|---|
| hs22 | 21 | YES | YES (via propagation through blk 22) | **both donors reachable** |
| hs23 | 22 | no (blk 22 already computed its K/V) | YES | full donor only |
| hs24 | 23 | no | no (blk 23 already computed its K/V) | **quarantined, despite block 23 < 24** |
| hs34 / hs38 / hs40 / hs42 | 33 / 37 / 39 / 41 | no | no | quarantined (the parent's sites) |

A write at hs24 is functionally on the *far* side of the seam. This is what makes
the design testable without model surgery: **hs22 and hs24 are two blocks apart
in depth and differ almost entirely in whether the write can enter the shared
K/V.** That pair is registered below as a **descriptive** contrast (A3 vs A5).
It carries no gating weight and cannot discriminate the competing accounts: two
blocks of computation still move linear accessibility, so an A3-yes / A5-no
pattern is predicted by the crystallization-gap account as readily as by
quarantine (Threats (c)). See "The divergence, and the one measurement that
produces it" for why the patch-based A1-vs-A2 contrast, paired with `A_lin` under
both conditions, is the only contrast here with discriminating power, and
"Drafter's note" for the recommendation this replaces.

## Design

Substrate: `google/gemma-4-E4B-it`, raw-base instruct, bf16, no adapter, no 4-bit
quantization, no task training, snapshot
`fee6332c1abaafb77f6f9624236c63aa2f1d0187`. Lane: local RTX 3090.

> **Revision 2026-07-30 (lane change for Phase B, PI-approved).** Phase B
> (sharing-OFF extraction, C0/C1, A_lin Part 2, OFF refits, A1/A2/A4 and
> rollup) moves to the Modal cloud lane (A100) so it can run in parallel with
> the write-direction-naming-battery cell occupying the local 3090. Phase A
> stages 1-6 ran on the registered local lane and are untouched. Conditions
> binding the new lane: (1) the Modal image reproduces the tf550 environment
> pins exactly (transformers 5.5.0, accelerate 1.14.0, tuner 34c89fc4), image
> digest recorded per stage; (2) every registered comparison is same-
> environment internally -- A1 and A2 both run on Modal, C1 runs entirely on
> Modal, and the `A_lin` clause's ON side is RE-MEASURED on Modal alongside
> the OFF side (forward passes only) so the registered |diff| <= 0.05
> threshold never straddles GPU architectures; the local A_lin Part 1 numbers
> remain on record but the gate is evaluated on the same-lane pair; (3) no
> other registered quantity, gate, ladder, or pool changes. Rationale:
> wall-clock parallelism; the lane is an execution surface, not a scientific
> one, provided (1)-(2) hold. Approved by the PI in session 2026-07-30.
>
> **LAUNCH RECORD (2026-07-30).** PI approved the Modal spend (estimate
> ~$32-43, ~8-11 A100-hours) in-session. Launch authorized in TWO tranches
> per the C1 instrument gap found at harness build: tranche 1 = stages
> B0-B15 (G0-KV re-verify, OFF extractions, A_lin Part 2 with same-lane ON
> re-measure, fits, dose calibration, smokes, A1 full+undosed) which are not
> C1-gated; tranche 2 = B16-B18b (A2/A4) and B20 (rollup), gated until the
> C1 precondition producer (new module implementing gates.yaml
> g0_c1_precondition_control: FIT-split, no-injection, NLL under both
> conditions) is built, lead-reviewed, recorded in the instrument, and C1
> itself passes. Private inputs (eval_rows.jsonl, anchor_extract.safetensors)
> stage to the Modal volume directly (modal volume put), NOT to any HF
> repository. App: cloud/modal_phase_b.py; plan: cloud/PHASE_B_MODAL_PLAN.md.

Pool: gemma's OWN fresh-mined evaluation pool and FIT/HELD-OUT split from the
parent experiment (`mine_eval_pool.py --target-confab 280 --target-known-correct
450` + `split_fit_heldout.py`, FIT_FRAC=0.40), reused verbatim and hash-pinned.
That pool already cleared the >=150 held-out confab / >=250 held-out
known_correct_answered power bar in the parent. Reusing it is what makes A1 a
true replication of the parent's null rather than a new measurement. Row text is
private and stays gitignored; only ID-only manifests and aggregate JSON are
committed. See "Open questions at sign" #1 for the promotion mechanics.

### The core manipulation (and why the obvious version of it crashes)

Toggle the mechanism, not the depth. `kv_seam_patch.kv_sharing(model,
enabled=False)` sets `is_kv_shared_layer = False` and `kv_shared_layer_index =
None` on blocks 24-41, so each recomputes K/V from its own residual stream using
its own retained trained projections. Weights, config, dtype, prompts, render,
and generation contract are untouched.

**That flag flip alone does not run. It raises `IndexError` on the first
shared-layer forward call, deterministically.** This is not an assessed risk: it
is reproduced live by `kv_seam_preflight.py` check 1, which builds a tiny
randomly-initialized `Gemma4ForCausalLM` carrying the **exact** KV-seam geometry
(`num_hidden_layers=42`, `num_kv_shared_layers=18`, `sliding_window=512`,
auto-derived `layer_types` verified against the checkpoint's own
`[5,11,17,23,29,35,41]` full-attention placement), asserts that stock
`generate()` auto-builds a **24**-layer cache, then catches the `IndexError` from
the patch as drafted. The suite is **4/4 PASS, exit 0**, re-run by the lead.
Traced by `gemma-arch-research` (memo §8.3) and re-verified line by line for this
draft against the executing `transformers==5.5.0`:

- `Gemma4TextModel.forward` builds its cache as `DynamicCache(config=self.config)`.
- `DynamicCache.__init__` (`cache_utils.py:1218-1220`) is shared-KV-aware and
  truncates before allocating — `# Some models have shared layers thus no cache
  is needed for them` / `layer_types = layer_types[: -decoder_config.num_kv_shared_layers]`
  — so for this checkpoint it allocates exactly **24** `CacheLayer` objects
  (indices 0-23).
- Because that `layers` list is non-empty, `Cache.__init__`
  (`cache_utils.py:871-872`) sets `layer_class_to_replicate = None`, which
  disables the lazy-growth branch in `Cache.update` (`cache_utils.py:927-930`).
- A patched shared layer then reaches
  `past_key_values.update(key_states, value_states, self.layer_idx)` at
  `modeling_gemma4.py:1216` and indexes `self.layers[24]` on a 24-element list.

`shared_layers` is bolted onto the cache instance separately
(`modeling_gemma4.py:1217-1220`) and is not `self.layers`; the 24-entry
truncation exists *because* stock code never calls `.update()` for a shared
layer. Flipping the module flag breaks that invariant without telling the cache.

**Registered fix (memo §8.3 option 1), in the form the passing preflight uses:**
`kv_seam_patch.build_full_length_cache(...)` constructs a **42-entry** cache as
**`Cache(layers=[...])`** — one `DynamicSlidingWindowLayer(sliding_window=512)`
or `DynamicLayer()` per entry of `config.layer_types`, in order, **no slicing**.
It is **not** `DynamicCache(layers=...)`: `DynamicCache.__init__` accepts only
`config=` and would re-apply the `num_kv_shared_layers` slice, which is the bug.
The object is passed into `generate(past_key_values=...)`;
`Gemma4TextModel.forward` only builds its own cache when none is supplied, and
`generate`'s "Quick escape route 1" (`generation/utils.py:1818-1829`) returns
untouched when the caller supplies a `Cache`, so the slice is bypassed entirely.
Preflight check 2 confirms a multi-token greedy `generate()` then completes with
no exception, and check 3 confirms all 42 cache layers' sequence lengths grew
uniformly across decode steps.

**The cache is built IDENTICALLY in BOTH arms, by that one function.** A1 (ON)
does not need it to avoid a crash and is given it anyway, on purpose. Preflight
check 4 establishes the property this depends on: with sharing ON, the
hand-built full-length cache is **token-for-token AND logit-bit-identical**
(`torch.equal`) to fully-stock `generate()` with the model's own auto-cache. That
inertness is what lets A1-vs-A2 isolate the KV variable. **If the two arms
differed in how the cache object was constructed, that property is forfeited and
the primary contrast becomes uninterpretable** — the contrast would be
sharing-flag *plus* cache-substitution versus neither. Constructing it in one
place, for every arm, is what makes the cache a constant rather than a second
variable. **A fresh cache is built for every `generate()` call** — a `Cache` is
stateful and reusing one across rows would leak the previous row's K/V.

`store_full_length_kv` is deliberately NOT touched, so blocks 22/23 keep writing
`shared_layers` under OFF where nothing reads it. Leaving that write in place
keeps control flow identical between conditions everywhere except the one branch
under test.

**`use_cache=False` is REJECTED as the toggle.** It is a real mechanism in this
transformers version and this harness's call shape (memo §8.1 traced it end to
end, including confirming that `generation/utils.py:2426-2427` does not override
it because `gen_lib.py` passes `input_ids`, not `inputs_embeds`) — but it is
global, not local. All 42 layers lose caching, so the 24 non-shared layers switch
from cached-append to full-prefix recompute at every decode step. That is (i) an
unquantified numerical-path change sitting underneath a contrast whose own scale
is gate-AUC-level (0.977-0.982), and (ii) O(T x S_avg) instead of O(T), which
makes a full-pool run likely impractical on the 3090. The targeted patch is the
only option that isolates the shared-vs-local-KV variable alone, and it keeps
cost within single-digit percent of baseline.

Because the failure mode is a crash rather than a silent wrong answer, the
G0-KV preflight below is **mandatory, not advisory**, and it asserts on measured
projection calls and measured cache growth — never on the flag.

### Arms

Injection method, direction-fit method, ladder, usability rule, selection rule,
generation contract, and graders are the parent's, unchanged
(`build_directions.py`, `gate_fit.py`, `calibrate_dose.py`, `pipeline.py`,
`run_contrast.py`, `gen_lib.py`, `grader.py`, `scorers.py`, copied verbatim).

| Arm | Site | KV sharing | Role |
|---|---|---|---|
| **A1** | hs38 | ON | Above-seam null replication. Expected to reproduce the parent's zero. |
| **A2** | hs38 | **OFF** | **PRIMARY.** Same site, same ratio ladder, mechanism toggled. |
| **A3** | **hs22** (resolved 2026-07-25 by the A_lin rule below) | ON | Below-seam, donor-reachable — reaches **both** donors. Unmodified model. |
| **A4** | **hs22** (same site as A3) | OFF | 2x2 completion. |
| **A5** | hs24 | ON | **Seam-adjacent quarantine control.** Two blocks from A3, downstream of both donors. |
| **A6** | **hs23** (the site A3 did not take) | ON | The other donor-reachability regime (**full donor only**, vs A3's both-donors). **Conditional:** run only if A3 finds a usable FIT dose — dissociating the sliding from the full donor channel is meaningless if the below-seam write does not actuate at all. |
| **D1-D4** | hs15, hs18, hs20, hs23 | ON | **Shallow depth ladder** (added 2026-07-24, user-directed). Unmodified model. See below. |
| **C0** | -- | ON | No injection. Baseline confab / known-correct rates. |
| **C1** | -- | **OFF** | No injection. **Precondition control** (see below). |

**The shallow depth ladder (D1-D4) varies depth at constant donor reachability.**
This is the arm set's one clean handle on the confound that defeats A3-vs-A5.
Writing at `hs_index N` hooks the output of block `N-1`; the donors are blocks 22
and 23. So:

| arm | site | = output of block | sliding donor (22) | full donor (23) | rel. depth |
|---|---|---|---|---|---|
| D1 | hs15 | 14 | reachable | reachable | 0.357 |
| D2 | hs18 | 17 | reachable | reachable | 0.429 |
| D3 | hs20 | 19 | reachable | reachable | 0.476 |
| A3 | hs22 | 21 | reachable | reachable | 0.524 |
| D4 | hs23 | 22 | **no** | reachable | 0.548 |

D1-D3 and A3 sit in the **same** donor-reachability regime across a 7-block depth
span; D4 is the full-donor-only regime. A3-vs-A5 could not separate depth from
reachability — the two sites are two blocks apart and differ in both. D1/D2/D3
against A3 hold reachability fixed and move depth; A3 against D4 against A5 hold
depth roughly fixed and move reachability. Together they factor the two variables
the original pair confounded.

**Why this band specifically, and why it is not fishing.** The band is fixed
here, before any dosing, by the prior cross-family operating range, not selected
from gemma's own read profile, which is saturated (held-out KU AUC `>= 0.977`
from hs5 to hs42) and supplies no site-selection signal at all.

Stating that operating range correctly, since an earlier draft of this paragraph
stated it too narrowly (see the correction note below): every site that has ever
actuated in this program, as a depth fraction, is

| family | blocks | site | rd | achieved |
|---|---|---|---|---|
| mistral-7b-v0.3 | 32 | hs12 | 0.375 | usable dose |
| mistral-7b-v0.3 | 32 | hs15 | 0.469 | usable dose |
| llama-3.2-3b | 28 | hs17 | 0.607 | usable dose, held-out G1 PASS 0.7420 |
| Qwen3.5-4B | 32 | hs20 | 0.625 | promoted held-out actuation result |
| Qwen3-4B | 36 | hs23 | 0.639 | held-out 0.892 [0.839, 0.929] |

so the cross-family operating range is **rd 0.375-0.639**, and everything tested
above rd 0.71 has failed. Gemma's four previously-tested sites sit at rd 0.810,
0.905, 0.952, 1.000: gemma has only ever been written to *above* the range where
the effect exists elsewhere, which is the point this paragraph exists to make and
is unaffected by the correction.

**What the correct range implies for gemma specifically, and it is not
comfortable.** Gemma has 42 blocks with donors at 22/23, so the deepest site that
still reads both donors is hs24, **rd 0.571**. The upper half of the cross-family
operating range - rd 0.571-0.639, which is where llama's G1 PASS (0.607) and
Qwen3.5-4B's promoted result (0.625) both sit - is on gemma **entirely above the
seam**, at hs25-hs27. On this architecture "quarantined" and "in the productive
depth band" are largely the same region. That is a confound this design cannot
remove, and it cuts both ways: it is the reason the quarantine hypothesis is
worth testing at all, and it is the reason a below-seam null from D1-D4 would
NOT be clean evidence against actuation-at-depth in gemma, because D1-D4 can only
reach rd <= 0.548 and no family's best result sits that shallow. Record any
below-seam null with that limitation attached.

> **Correction, pre-sign.** This paragraph previously read: "Relative depth
> 0.357-0.548 is where every family that has ever actuated in this program does
> so: no site above rd 0.607 (llama hs17) has produced a usable dose in any
> family." Both halves were too narrow. The 0.357-0.548 envelope contains only
> mistral's two sites; it excludes llama hs17 (0.607) and Qwen3.5-4B hs20
> (0.625), the latter being the single promoted direction-specific held-out
> success in the program. Qwen3.5-4B `num_hidden_layers=32` is sourced at
> `qwen35-4b-midband-doubt-snap/AMENDMENT.md:17,55`. Corrected while this
> experiment is still `draft` with nothing pinned, per the draft-to-signed
> lifecycle in `.skills/experiments/SKILL.md`. **The arm set is unchanged** -
> D1-D4/A3/A5 already tile the below-seam depth range as densely as the donor
> structure permits, and the corrected upper end is unreachable below the seam.

**No re-extraction is required.** The parent's corrected `use_cache=True`
extraction already covers hs0-hs42 over all 806 rows, so D1-D4 fit their
directions and gates from existing clean activations. Their median anchor L2
norms, which denominate the R2 ratio ladder, are hs15 **133.17**, hs18
**101.07**, hs20 **81.35**, hs23 **58.78** (NOTEBOOK.md, F7).

**Gating status.** D1-D4 are **descriptive and non-gating**, on the same footing
as A3/A5: they run on the unmodified model and cannot discriminate the KV account
from the crystallization-gap account on their own. They enter the falsifier in
one direction only — see "Falsifier" — because a *positive* result anywhere in
D1-D4 is decisive against the quarantine account, while a negative one is not
decisive for it.

**Below-seam site selection is by linear accessibility, pre-stated.** Donor
reachability admits exactly two below-seam sites, hs22 (both donors) and hs23
(full donor only); there is no free depth parameter to pick. Between those two,
**A3 is the site with the higher `A_lin`** measured in the G0-ALIN preflight
below, with the other becoming A6. Ties (|ΔA_lin| < 0.01) break to hs22, the
site with the broader donor reach. The parent's eff_dim-peak rule is NOT used to
select any site in this experiment: it is post-hoc with respect to this question,
and gemma's eff_dim profile is flat mid-stack anyway (0.0046-0.0058 across 9 of
10 sweep points, peak std 0.00141 overlapping every interior point, per the
parent's `layer_profile.json`). hs38 is retained for A1/A2 for one reason only —
it is the site the parent actually ran, so A1 is a replication rather than a new
measurement.

**Primary contrast (pre-stated, single comparison): A2 clears both primary gates
on held-out while A1 does not, AND `|A_lin(hs38, OFF) - A_lin(hs38, ON)| <=
0.05`.** Same site index, same rows, same ratio ladder, only the KV pathway
toggled. **The `A_lin` clause is not decoration — it is what makes the contrast
discriminating.** Holding the site *index* fixed does not hold the site's
*representation* fixed: hs38 is the output of block 37, a KV-shared block, so
turning sharing OFF changes the forward computation of blocks 24-37, all upstream
of hs38 (this is the same fact that forces the OFF arms to refit their
directions). A behavioral A2-yes / A1-no accompanied by a shifted `A_lin` is
jointly explained by the crystallization-gap account and promotes nothing. The
full four-outcome interpretation table is registered in "The divergence, and the
one measurement that produces it" and mirrored in `gates.yaml`.

**Descriptive contrast (pre-stated, non-gating, cannot discriminate): A3 vs A5.**
Both on the unmodified on-distribution model, one or two blocks apart, differing
in donor reachability. Its value is that it is immune to every patch artifact:
if the patch's validity is questioned, this pair still says something about
whether the boundary push actuates below the seam. It is **not** immune to the
site-property explanations — `A_lin` and entanglement can differ across two
adjacent blocks — so it can neither support nor refute the KV hypothesis, and it
is excluded from the success rule. **Reported with the measured `A_lin` at both
sites.** If |A_lin(A3) - A_lin(A5)| exceeds 0.10, the write-up additionally
declares it confounded with Regime-2 rather than merely non-discriminating; that
threshold is fixed here, before the sweep runs.

**Other descriptive contrasts (pre-stated, non-gating, reported regardless):**
A3 vs A1 (does the boundary push actuate anywhere in this model — confounded with
depth outright, 16 blocks); A4 vs A3 (does sharing-OFF add anything below the
seam, where the write already reaches the donors); A6 (sliding vs full donor
channel).

### Why the sharing-OFF arms refit their directions

The residual stream at hs38 under sharing-OFF is not the same distribution as
under ON -- blocks 24-37 compute differently, so their outputs differ. A KU
readout direction, gate `tau`, and anchor-norm denominator fit under ON are
therefore not automatically valid under OFF. **Each condition fits its own `u_d`,
`pos_ctrl`, `neg_ctrl`, `c_hat`, `tau`, and its own per-site median anchor L2
norm, on the same FIT rows, with the same method and the same pinned
`random_state=20260707`.** Doses are matched **by ratio rung**, not by absolute
magnitude -- which is exactly what the parent's R2 norm-scaled ladder was built
to make meaningful across differently-scaled residual streams. Both the ratio and
the absolute dose are reported for every cell.

Consequence to state plainly: A1-vs-A2 is not literally "the same vector written
twice." It is "the analogous vector, fit and dosed by the same rule, in two
computational conditions." A diagnostic (non-gating) cosine similarity between
the ON-fit and OFF-fit `c_hat` and `u_d` at hs38 is recorded so the reader can
see how far apart the two fits are.

### Instrument

Copied verbatim from `experiments/j-space-cross-family-layer-contrast/`, which is
pinned and under adjudication -- **no file belonging to the parent is modified by
this experiment.** Copies: `family_config.py`, `model_lib.py`, `gen_lib.py`,
`grader.py`, `scorers.py`, `extract_anchor.py`, `build_directions.py`,
`gate_fit.py`, `calibrate_dose.py`, `pipeline.py`, `run_contrast.py`, and
`families/gemma4-e4b.yaml`.

New to this experiment: **`kv_seam_patch.py`** -- the sharing toggle
(`kv_sharing`), the 42-entry cache builder that makes it run
(`build_full_length_cache`) plus its length probe (`cache_layer_lengths`), the
architecture fail-closed check (`verify_architecture`), the `k_proj`/`v_proj`
execution counter (`count_kv_projection_calls`), and the donor key capture
(`capture_donor_keys`). It is Gemma-4-specific by construction and must not be
promoted into `synaptic-tuner/`.

Required integration work before sign (see "Open questions at sign" #2): a
`--kv-sharing {on,off}` flag threaded through `calibrate_dose.py`,
`run_contrast.py`, and `pipeline.py`, wrapping every model forward in
`kv_seam_patch.kv_sharing(...)`, and writing the condition into every output
record and manifest so no artifact is condition-ambiguous.

**Status updated 2026-07-25: done for every stage exercised so far, and the
artifacts demonstrate it rather than merely asserting it.**
`build_manifest_layers.seam_pair.json` and `gate_fit_layers.seam_pair.json` both
carry `"kv_sharing": "on"`, `dose_calibration_summary.seam_pair.json` carries it
at top level, and all 24 per-cell calibration records carry it individually. The
calibration checkpoint filename is scoped by **both** site set and condition, so
an ON run and an OFF run of the same cells can neither collide nor silently
resume from each other. `run_contrast.py` has not been executed in any mode, so
its threading is written but **not yet exercised** — that part stays open.

Prerequisite: the `synaptic-tuner` checkout used for any GPU stage of this
experiment must contain commit `7a44eb3` ("Add model.language_model.layers to
decoder-layer path search"), verified STRUCTURALLY, not by version comparison:

```
grep -n "model.language_model.layers" MechInterp/intervention/hooks.py
```

must match inside `_LAYER_PATHS`. Without that entry the intervention engine
cannot locate Gemma-4's decoder blocks at all, and every GPU stage of this
experiment fails at the first hook install. Any stage record for this
experiment must name the tuner commit it ran under and record that the
structural check passed on that checkout. The grep is the binding requirement;
commit ancestry is not, because a squash or cherry-pick landing of the fix
would carry the entry without carrying `7a44eb3` as an ancestor.

**Why structural verification and not a version floor (recorded 2026-07-25,
reworded 2026-07-29 pre-sign as the earlier note directed).** `7a44eb3` is the
head of the unmerged remote branch `fix/gemma4-decoder-layer-path`. Commits
later in mainline history do NOT imply the fix is present: the canonical
submodule pin has twice been a mainline commit that postdates the fix and lacks
it (`b1ea382` at the time of the original note, `901dbe80` as of 2026-07-29;
both carry `language_model.model.layers` but not the `model.language_model.layers`
entry gemma-4-E4B needs). So "at or after `7a44eb3`" reads as a version floor
and is not one, and a checkout that "looks newer" can still be missing the fix.
As of 2026-07-29 the fix branch is exactly one commit ahead of the mainline pin
`901dbe80` (a fast-forward), so the standing resolution path is to merge
`fix/gemma4-decoder-layer-path` into the tuner mainline and bump the submodule
pin; until that lands, the only satisfying checkouts are ones with the fix
branch checked out directly. Every stage run so far used the
`jspace-cross-family` worktree's submodule, which satisfies the structural
check.

### Generation contract

Byte-identical to the parent: `min_new_tokens=1`, `max_new_tokens=200`,
`do_sample=False`, `num_beams=1`, `enable_thinking=False`, EOS = tokenizer
`eos_token_id` plus `<turn|>`. `clean_tighten` and `not_well_formed_correct` are
the parent's graders, unchanged.

## Preconditions

### G0-KV (new; instrument validity for the seam manipulation; stop, not outcome)

Fail-closed. Every check below runs and is recorded **before any dosed arm is
scored on held-out**. The flag is never accepted as evidence that the mechanism
changed.

1. **Architecture identity.** `verify_architecture(model)` passes: 42 hidden
   layers, 18 KV-shared, `first_kv_shared_layer_idx == 24`, donors `{full: 23,
   sliding: 22}`, and the set of blocks reporting `is_kv_shared_layer == True`
   is exactly `{24..41}`. Any mismatch voids the registered site indices and the
   experiment stops.
2. **Projection-execution assertion, both directions.** Over one prefill AND at
   least one decode step, with `count_kv_projection_calls`:
   - **OFF condition:** `k_proj` and `v_proj` call counts are `>= 1` for **every**
     block in 24..41. A single block at zero fails the check.
   - **ON condition:** those same counts are **exactly 0** for every block in
     24..41, and `>= 1` for every block in 0..23.
   Asserting only the OFF direction would pass a no-op patch; asserting only ON
   would pass a patch that changed something unrelated.
3. **Cache integrity under OFF.** The shared-KV cache layout assumes blocks 24-41
   never call `past_key_values.update`; the OFF patch makes all 18 of them do
   exactly that. This check is what catches a silently mismatched cache -- the
   failure mode where the flag looks correct and decoding is quietly corrupt.
   All four parts run:
   - **(3a) Attribute state.** `is_kv_shared_layer is False` and
     `kv_shared_layer_index is None` for blocks 24..41.
   - **(3b) Cache shape.** The object passed as `past_key_values` satisfies
     `len(cache.layers) == 42` and `cache.layer_class_to_replicate is None`
     (both already asserted inside `build_full_length_cache`, re-asserted here on
     the object the harness actually hands to `generate`). A 24-entry cache
     reaching an OFF arm is a **stop**, not a warning: it does not degrade, it
     raises IndexError, and a caught-and-swallowed IndexError anywhere in the
     harness would silently drop rows.
   - **(3c) Per-layer cache growth across decode steps.** Using
     `cache_layer_lengths(cache)` after prefill and after >= 2 decode steps: every
     index in **24..41** has a nonzero length that **increases** at each decode
     step, by the same increment as indices 0..23. This is the positive evidence
     that the appended 18 slots are live and being written, not inert padding that
     the model routes around. Sliding-window layers are compared against the other
     sliding-window layers (length saturates at `sliding_window=512`), full layers
     against full layers, so the saturation is not read as a failure.
   - **(3d) Cache-substitution no-op under ON.** With sharing **ON** (stock
     mechanism), greedy generation given a `build_full_length_cache(model)` object
     is **token-identical** to stock generation with no `past_key_values`
     supplied, on >= 8 fixed prompts. This isolates the confound the fix
     introduces: it proves the 42-entry cache **by itself** changes nothing, so
     any A1-vs-A2 difference is attributable to the sharing flag and not to the
     cache object that had to accompany it. Without this check the primary
     contrast would be sharing-flag *plus* cache-substitution versus neither.

   A fresh cache is built per `generate()` call in every OFF arm; reuse across
   rows would leak the previous row's K/V, and the growth probe in (3c) is also
   the cheapest detector of an accidentally reused cache (lengths that start
   nonzero at prefill).
4. **Donor-reachability assertion (this is the premise of the whole experiment,
   so it is measured, not assumed).** Under sharing ON, with `capture_donor_keys`
   on blocks 22 and 23, inject a fixed random unit delta (seed 20260707) scaled
   to the site's median anchor norm and compare captured donor keys against a
   no-injection forward:
   - write at **hs24**: donor keys at blocks 22 AND 23 are **bit-identical** to
     the undosed run;
   - write at **hs38**: same, bit-identical;
   - write at **hs22**: donor keys at block 22 **and** block 23 **differ**;
   - write at **hs23**: block 23's keys **differ**, block 22's are **identical**.
   If any of these four fails, the quarantine premise is wrong as stated and the
   experiment is **VOID** before any behavioral arm runs. This costs four forward
   passes and it is the cheapest decisive check in the design.
5. **Shared-projection weight liveness (recorded, not gated).** Frobenius norms of
   `k_proj`/`v_proj` for all 42 blocks, with the depth trend and the
   full_attention-block elevation, recorded to the notebook. Pre-registered as an
   observation because it bears on Threats (b); it is deliberately NOT a gate,
   because there is no principled threshold that distinguishes "trained" from
   "trained then made vestigial."

### G0-ALIN (new; TWO parts -- one CPU pre-sign, one GPU and load-bearing)

`A_lin` enters this design in two distinct roles, and conflating them was a defect
in an earlier revision of this document. **Part 1 selects a descriptive arm's
site and can be computed on CPU before signing. Part 2 is the measurement that
makes the primary contrast discriminating at all, requires a GPU extraction under
the patch, and cannot be produced before the run.** Part 2 is not optional: see
"The divergence, and the one measurement that produces it."

**Part 1 -- site selection (CPU, pre-sign, cached activations).**

The below-seam site (A3) and its quarantined match (A5/A6) are selected by
**linear accessibility**, `A_lin` (Thread D of the parent's
`null_literature_review.md`, after 2604.15557), not by the eff_dim peak. That
selection must be made and recorded **before** the arms are registered, or the
rule is not pre-stated in any meaningful sense.

`A_lin(hs_N)` = top-1 accuracy of applying the model's final RMSNorm and
unembedding `W_U` to the cached hidden state at `hs_N` and taking the argmax over
the KU contrast's answer tokens. It is a training-free logit lens, computed
**CPU-only on already-cached activations** (`anchor_extract.safetensors` from the
parent's gemma extraction); it loads no weights to CUDA and blocks nothing.

Recorded for all six candidate sites (hs22, hs23, hs24, hs34, hs38, hs42) on the
**FIT** split only. Two uses, both pre-stated:

1. **Selection.** A3 is whichever of hs22/hs23 has the higher `A_lin`; ties
   (`|ΔA_lin| < 0.01`) break to hs22, the site that reaches both donors. A5 is
   hs24 regardless -- it is fixed by the geometry, being the first quarantined
   block.
2. **Confound declaration for the descriptive A3-vs-A5 contrast.** If
   `|A_lin(A3) - A_lin(A5)| > 0.10`, that contrast is **declared confounded by
   linear accessibility at registration time** and is reported as such whatever
   it shows. It does not stop the arm and it does not touch the primary. Note
   that A3-vs-A5 is non-discriminating *regardless* of this number (Threats
   (c)); the declaration marks the stronger case where the confound is
   measurably large. This declaration is made from the pre-sign number, never
   after seeing a behavioral result.

**Recommendation to the lead on Part 1:** run it before signing. It costs no GPU,
it determines a registered arm's site, and deferring it would mean signing an
amendment whose arm table has a hole in it. If the lead prefers to sign first,
the rule above is what binds, and the sweep becomes the first thing the run does.

#### Part 1 RESULT — run 2026-07-25 (CPU-only, 18.05s, no CUDA)

`alin_sweep.py`, 292 FIT rows, pinned revision. Full record:
`analysis-committed/gemma4-e4b/alin_part1_selection.json`.

| Site | `A_lin` | median rank of the true token |
|---|---|---|
| hs15 | 0.0000 | 61 260 |
| hs18 | 0.0000 | 120 190 |
| hs20 | 0.0000 | 88 181 |
| **hs22** | **0.0000** | **83 008** |
| **hs23** | **0.0000** | **238 571** |
| hs24 | 0.0000 | 143 970 |
| hs34 | 0.9760 | 1 |
| hs38 | 0.9760 | 1 |
| hs42 | 0.9966 | 1 |

**Selection: A3 = hs22, A6 = hs23, A5 = hs24.** `A_lin` is **exactly 0.0000 at
every below-seam site**, so `|ΔA_lin(hs22, hs23)| = 0.0 < 0.01` — a tie, and the
pre-stated tie-break decides: **hs22**, the site that reaches both donors.

**Confound declaration: NOT made.** `|A_lin(A3) − A_lin(A5)| = |0.0 − 0.0| = 0.0`,
far inside the 0.10 band. Note this is the *weak* reading of that rule — the
declaration exists to flag a measurably large accessibility gap, and here there
is no gap because both sites are at the floor together. A3-vs-A5 remains
non-discriminating regardless, per Threats (c).

**The registered statistic carries no selection signal, and that was foreseen.**
This is exactly the condition the parent's session record flagged as a blocker
("G0-ALIN as pre-registered cannot discriminate hs22 from hs23", 2026-07-24).
It is not a defect in the rule. The tie-break was written for this case and
resolves on a stated principle — broader donor reach — not on noise.

**The choice is independently corroborated by a statistic that is *not* at the
floor.** Median rank was recorded as an observation and took **no part** in
selection, but it separates the candidates sharply: hs22 ranks the true token
**83 008** against hs23's **238 571** — better by ~3×, with hs23 the worst site
measured at any depth (the vocabulary is 262 144, so hs23 sits near the bottom
of it). Had the finer statistic been the registered one, it would have chosen
hs22 as well. The selection therefore does not turn on which statistic was
locked. Substituting rank for the registered top-1 accuracy would have been
goalpost movement and was refused.

**Harness validation.** Three guards, all passed: the terminal-layer tautology
(greedy decoding makes the recorded token the argmax of the true final-layer
logits, so hs42 must be ~1.0 — measured **0.9966**, median rank 1, and every
single miss a rank-2 near-tie against the parent's GPU-measured 1.0000, i.e.
CPU/GPU tie-breaking, not lens failure); a distinct-storage/non-vacuity check on
the cached tensors; and a `prompt_len` re-render check on all 806 rows, which
proves the render used here reproduces the one the activations were extracted
under. As a fourth, external check, the FIT-only numbers reproduce the parent's
all-rows ladder at every shared depth (hs15 61 260 vs 61 283; hs20 88 181 vs
88 087; hs24 143 970 vs 144 858; hs34 0.976 vs 0.967).

**One limitation, recorded rather than papered over.** The script cannot resolve
`final_is_postnorm` on CPU — both output recipes score ~0.99 at the terminal
layer, because re-normalizing an already-normalized vector barely moves the
argmax. An earlier revision tried to derive it from the tautology and its
fail-closed guard correctly refused. The recipe is therefore taken from the
parent's decisive GPU calibration (max-abs reconstruction error 0.0 vs 17.6875).
**It cannot affect this selection:** the two recipes differ only at hs42, and
every candidate site is normed identically under either one.

**Part 2 -- `A_lin(hs38)` under BOTH KV conditions (GPU; a run stage, not a
pre-sign deliverable).**

Part 1 uses the parent's cached `anchor_extract.safetensors`, which was produced
by the **stock** model. There is no cached activation anywhere on disk for the
sharing-OFF model, because no one has ever run it. So `A_lin(hs38, OFF)` requires
a fresh extraction with the patch active:

```
extract_anchor.py --kv-sharing off   # writes anchor_extract_kvoff.safetensors
```

This is a GPU stage. It is added to `pipeline_stages` in `cell.yaml` and must run
**before** the OFF arms' direction fits (which consume the same activations
anyway, per "Why the sharing-OFF arms refit their directions"), so it adds a
logit-lens pass over an extraction the design already required -- not a new
extraction. Both numbers are computed with the identical logit-lens code path,
the identical FIT row ids, and the identical answer-token set; only the source
activation file differs.

**What it is used for, pre-stated:** the discrimination band
`|A_lin(hs38, OFF) - A_lin(hs38, ON)| <= 0.05` is part of the **prediction**, and
the four-outcome table in "The divergence" is the pre-stated interpretation rule.
The 0.05 band is set to match the G2 cap and the C1 criterion-1 tolerance already
used in this document, so that "materially unchanged" means the same magnitude
everywhere in the design rather than being tuned per use.

**If Part 2 is not run, the primary contrast discriminates nothing.** A behavioral
A2-yes / A1-no without it is reported as a raw actuation finding, jointly
explained by both live accounts, and it promotes no claim about KV quarantine.
The drafter's position is that the experiment is not worth running without Part 2;
that judgment is the lead's to make at sign.

### G0-C1 (precondition control: does turning sharing off break the model?)

**Pre-stated numeric criterion.** Measured on the **FIT split** (held-out is spent
only on the primary), C0 vs C1, no injection in either. C1 **PASSES** iff all
three hold:

1. **Known-correct behavior is preserved.** The undosed
   `not_well_formed_correct` rate on FIT `known_correct_answered` rows moves by
   **<= 0.05 absolute** between C0 and C1, and the 95% Wilson interval on the
   C1-minus-C0 difference excludes a degradation larger than **0.10**.
   *Justification:* 0.05 is exactly the parent's G2 cap -- the design already
   treats a 5-point move in known-correct well-formedness as the boundary of
   "material." Holding the control to the same bar as the thing it protects is
   the minimum defensible choice; a looser control could hide a G2-sized
   artifact.
   *Method, pinned pre-sign (2026-07-29, lead).* "Wilson interval on the
   difference" is computed as the Newcombe hybrid score interval (Newcombe
   1998, method 10): Wilson 95% bounds (l1, u1) for the C1 rate and (l2, u2)
   for the C0 rate, difference interval
   [d - sqrt((p1-l1)^2 + (u2-p2)^2), d + sqrt((u1-p1)^2 + (p2-l2)^2)] with
   d = p1 - p2. Pinned because the criterion as registered named a Wilson
   interval on a difference without naming the construction, and no method for
   a two-proportion interval was registered anywhere in this program. The
   caps (0.05, 0.10) and the direction-of-degradation reading are untouched;
   this pin completes the registered criterion, it does not alter it.
   Implemented in `rollup.py` with unit tests including a case where the raw
   delta passes while the interval fails, proving the interval is operative.
2. **The OFF model does not hedge on its own.** C1's undosed confab
   `clean_tighten` rate is **<= 0.05**. *Justification:* this is the criterion
   that actually protects the primary. G1's floor is 0.50; capping spontaneous
   abstention at 0.05 puts it a factor of ten below, so no plausible
   sharing-OFF-induced tendency to abstain could manufacture a G1 pass. C0's own
   value is expected near zero and is reported alongside.
3. **Likelihood is preserved.** Teacher-forced mean per-token NLL over the FIT
   rows' rendered prompt plus reference completion is within **10%** of C0's.
   *Justification:* base-rate equality is a weak test -- a model can keep its
   answer rates while its attention routing is subtly wrong. NLL is the sharpest
   cheap indicator of an intact forward pass. 10% is far above numeric/seed noise
   and far below the multi-fold blowup a genuinely stale-projection model would
   produce. This is a judgment call and the drafter flags it as such; a stricter
   **5%** is available to the lead and the drafter would not object to it.

**If C1 fails:** the sharing-OFF arms (A2, A4) are **uninterpretable** and are
recorded as NOT-RUN with the C1 numbers as the blocker. The experiment does NOT
stop there -- A1, A3, A5, and A6 all run on the unmodified model and are
unaffected by a C1 failure. This is a deliberate departure from the design
brief's "the experiment stops there," and the reason is in "Drafter's note."

C1 is evaluated and written to the notebook **before** any OFF arm is scored on
held-out, so it can never be reached for after the fact as an excuse for an
inconvenient A2 result.

### G0-arm (per arm; inherited from the parent, transcribed)

- **KU readout gate floor.** `gate_fit.py` AUC on `neg_z_d` (FIT confab vs FIT
  known_correct_answered) **>= 0.90** at every registered site, in every
  condition it is run under. **If the KU direction does not read at a below-seam
  site, that arm is a NOT-RUN with that reason recorded -- and that is itself an
  informative result about where the known-unknown signal lives, not a failure.**
- **Refit reproducibility.** `build_directions.py --verify-reproducible`
  byte-identical, `random_state=20260707`, at every site and condition.
- **Dose viability.** The parent's R2 norm-scaled ladder, verbatim:
  `RATIO_LADDER = [0.100, 0.153, 0.235, 0.361, 0.554, 0.850, 1.304, 2.000]`,
  dose = ratio x that site's own median anchor L2 norm, computed under that arm's
  own condition. A rung is **usable** iff `frac_readback_within_tol == 1.0` AND
  `collapse_rate_on_dosed == 0.0` AND FIT confab `clean_tighten >= 0.5`.
  Selection: highest FIT confab tighten, then lower known-correct cost, then
  lower ratio. **Zero usable rungs at an arm = that arm is a dose-viability
  NOT-RUN**, reported with its full per-rung table.
- **Readback verification at every dosed site.** All dosed rows read back within
  **5% + 0.5 absolute** of that site's calibrated dose (parent tolerance).
- **Smoke collapse.** `collapse_rate_on_dosed == 0` at the selected dose.
- **Pool power.** >= 150 held-out confab and >= 250 held-out
  known_correct_answered rows (the parent's bar; gemma's fresh mine cleared it).
- **Containment.** No question text, aliases, or raw generations committed.

## Prediction

**A2 (hs38, KV sharing OFF) clears BOTH primary gates on held-out -- confab
`clean_tighten` >= 0.50 with Wilson 95% lower CI > 0.40, AND known-correct
`not_well_formed_correct` <= 0.05 with Wilson 95% upper CI < 0.10 -- while A1
(hs38, sharing ON) does not, with C1 having passed its precondition criterion,
AND `|A_lin(hs38, OFF) - A_lin(hs38, ON)| <= 0.05`.**

**The `A_lin` clause is part of the prediction, not a caveat on it.** Without it
the behavioral result is jointly explained by the crystallization-gap account and
discriminates nothing (see "The divergence, and the one measurement that produces
it"). A behavioral A2-yes/A1-no accompanied by an `A_lin` rise above 0.05 is
recorded as **jointly explained** and does **not** meet this prediction.

**Registered secondary expectation, non-gating:** on the unmodified model, A3
(below-seam, donors reachable) clears both gates while A5 (hs24, quarantined, two
blocks away) does not. This is reported whatever it shows and is **descriptive
only** -- it is confounded with linear accessibility and, against A1, with depth,
so it can neither meet nor fail the prediction above. It does not enter the
success rule.

**Registered expectation for the shallow ladder (D1-D4), non-gating:** at least
one of hs15 / hs18 / hs20 / hs23 finds a usable FIT dose and clears G1 on
held-out. Recorded because it is the arm set's genuine open question, and
because relative depth 0.357-0.548 lies inside the cross-family operating range
(rd 0.375-0.639, tabulated above) while gemma has never been written anywhere in
that range, its four prior sites all sitting at rd >= 0.810. Note the limitation
established above: D1-D4 reach only rd <= 0.548, the shallow half of that range,
because the donor structure puts the rest above the seam. Like A3/A5 it is
descriptive: it cannot discriminate the quarantine account from the
crystallization-gap account, and it does not enter the success rule. It does
enter the falsifier asymmetrically, below.

**A note on what "the parent's null" may be cited for anywhere in this
document.** It may be cited as the reason this experiment exists. It may **not**
be cited as evidence that gemma does not actuate, at any site, in any arm, in the
write-up or in the scoreboard. If this experiment reproduces a null on clean
activations, that null is this experiment's finding and rests on this
experiment's numbers alone.

## Falsifier

**If C1 PASSES its pre-stated criterion, and A2's write verifies (readback within
tolerance at every dosed cell) and A2 fails either primary gate, AND A3 also
fails either primary gate, then the KV-quarantine explanation of the gemma null
is FALSIFIED: the null stands as a property of the model rather than of the
injection site, and no further seam-relocation attempt on this model is
warranted.**

The A3 clause is a **conservatism, not an inference**: A3 cannot supply positive
evidence for the hypothesis (it is confounded), but requiring a second
independent failure before declaring falsification guards against killing a true
hypothesis on the strength of one weak negative (Threats (f)). Falsification here
removes KV quarantine from the candidate list; it does **not** select among the
remaining accounts, which stay undifferentiated.

**The shallow ladder enters the falsifier in one direction only, and this
asymmetry is deliberate.** D1-D4 write *below* both donors on the unmodified
model, where the quarantine account predicts the write can reach the shared K/V
and therefore should actuate if the model is actuable at all.

- **If any of D1-D4 clears G1 on held-out while A1 (hs38, ON) does not**, gemma
  is actuable, the effect is depth-localized on the unmodified model, and the
  **above-seam null is not a property of the model**. This is the single
  cheapest positive result available in this arm set and it is registered as
  **supporting** the quarantine account — while explicitly *not* establishing
  it, because depth and donor reachability both change between hs38 and hs15-23
  and D1-D4 cannot separate the quarantine mechanism from a generic
  shallow-band-only effect. Promotion beyond "supported" requires the A1-vs-A2
  patch contrast with its `A_lin` clause.
- **If all of D1-D4 fail G1 with verified readback and at least one usable FIT
  dose found**, then the boundary push does not actuate anywhere upstream of the
  donors, in the exact relative-depth band where llama, mistral and qwen all do.
  Combined with an A3 failure this strengthens the falsifier above from one weak
  negative to a **depth-swept** negative: the quarantine explanation is
  falsified, and gemma's inertness is a property of the model rather than of any
  injection site. This is the outcome the ladder was added to make reachable.
- **If all of D1-D4 are dose-viability NOT-RUN** (no usable FIT dose anywhere),
  the ladder contributes nothing to the falsifier in either direction and is
  reported as NOT-RUN. It does **not** count as a negative. The registered
  ladder does not move to manufacture one.

Three subordinate dispositions, all pre-stated:

- **VOID (parent null failed to reproduce).** If A1 finds a usable FIT dose at
  hs38 and clears G1 on held-out, the parent's gemma write-verified null did not
  reproduce under a verbatim-copied instrument on the same pool and split. The
  experiment produces **no verdict on the KV hypothesis**; the A1-vs-parent
  discrepancy must be diagnosed and the line re-grounded before any arm here is
  interpreted. A void is not a null and not a falsification.
- **INCONCLUSIVE (C1 fails).** If C1 fails, A2 and A4 are NOT-RUN and the
  falsifier above cannot fire on them. The below-seam arms A3/A5 still resolve
  their own secondary contrast and are reported; the KV-quarantine hypothesis is
  left open on the A1/A2 axis.
- **NULL-RESULT (no arm has a usable dose).** If every arm is a dose-viability
  NOT-RUN, the experiment resolves as a null result: the boundary push does not
  actuate anywhere in this model at any registered site in either condition. This
  is informative and is written up as such, not retried with a wider ladder --
  the ladder is registered and does not move.

## Gates

**G1 and G2 are transcribed verbatim from
`experiments/j-space-cross-family-layer-contrast/gates.yaml` and AMENDMENT.md
"Gates" (adjudicated lead+user 2026-07-23). They are NOT re-derived here.**
Applied **per arm**, on that arm's condition-matched **held-out** split.

- **G1 (PRIMARY -- actuation floor).** Held-out confab `clean_tighten` rate
  **>= 0.50** AND its Wilson 95% lower CI **> 0.40**.
- **G2 (PRIMARY -- selectivity cap).** Held-out known-correct
  `not_well_formed_correct` cost **<= 0.05** AND its Wilson 95% upper CI
  **< 0.10**.
- **Per-arm pass rule.** An arm PASSES iff G1 AND G2 both pass on held-out at its
  selected dose. An arm with no usable FIT dose is NOT-RUN, which is neither a
  pass nor a fail.
- `alpha = 0.05`, seed `20260709` for interval computation (parent's
  `gates.yaml`).

The parent's G0 checks that still apply are transcribed under "Preconditions ->
G0-arm". The parent's cross-family roll-up rule does not apply here: this is a
single-model experiment and there is no denominator over families.

### What G2 measures here (and the vacuity question, addressed with gemma's own numbers)

The G2 population is `role == "known_correct_answered"` **unfiltered by `fire`**
(`pipeline.py:229`, inherited verbatim from the Qwen3-4B predecessor
`j-space-midband-write-sweep-qwen3-4b/pipeline.py:188`). Rows that do not fire
are never dosed (`pipeline.py:149` dispatches the dosed pass only when
`row["fire"]`), so every non-firing row contributes the model's **undosed**
behavior to the metric. Where the KU readout gate almost never fires on
known-correct rows, G2 therefore reports a base rate and a G2 pass is close to
vacuous -- it would say the base model writes well-formed answers, not that
dosing is harmless.

**That concern is real in this lineage, and it does not apply to gemma.** From
the parent's committed `analysis/mistral-7b-v03/cost_control_forensics.md`
(CPU-only recomputation, verdict BENIGN): mistral fires **0/8** known-correct FIT
rows at all four calibrated layers, llama fires **0/334** known-correct held-out
rows at hs17 (recomputed, reproducing the committed `n_fired: 870` exactly), and
llama's full-pool false-positive rate at the frozen tau is **3/255 = 1.18%**
(hs12) and **2/255 = 0.78%** (hs15). The Qwen3-4B predecessor, where G2 was
genuinely diagnostic, ran at operating points **0.035 (9/258)** and **0.039
(14/360)**.

**Corrected 2026-07-24 (lead).** An earlier draft read gemma's operating point
off `analysis-committed/gemma4-e4b/gate_fit_layers.json`, which was fit on the
corrupt extraction, and concluded that gemma is the family where G2 is *most*
diagnostic. That conclusion is **withdrawn**. The withdrawn figures were FIT-pool
`fpr` 0.0889 / 0.0889 / 0.0944 and AUC 0.9779 / 0.9815 / 0.9772 at hs34 / hs38 /
hs42; they must not be propagated.

Gemma's actual operating point, recomputed on the clean `use_cache=True` extract
and reported on **held-out** (`known_held` = 270), from the parent's
`analysis/gemma4-e4b/read_profile_full_depth.json`:

| site | rel. depth | held-out AUC | `fpr_known_correct_flagged` | dosed known-correct rows |
|---|---|---|---|---|
| hs15 / hs18 / hs20 / hs22 / hs23 | 0.357-0.548 | 0.9996-0.9999 | **0.0074** | **2 / 270** |
| hs24 | 0.571 | 0.9980 | 0.0222 | 6 / 270 |
| hs34 | 0.810 | 0.9804 | 0.0815 | 22 / 270 |
| hs38 | 0.905 | 0.9770 | 0.0704 | 19 / 270 |
| hs42 | 1.000 | 0.9891 | 0.0481 | 13 / 270 |

**What survives.** Gemma does fire on known-correct rows far more than llama
(0/334 at hs17) or mistral (0/8), so the llama/mistral vacuity argument genuinely
does not transfer to this substrate, and the deep sites put real rows in the
denominator.

**What does not survive, and what it costs this design.** Per
`.skills/experiment-runner/reference/gate-diagnosticity.md`, a Wilson-95%-upper
cap is unsatisfiable below the smallest `N` with `wilson_upper(0, N) < cap`.
Verified directly for the registered `< 0.10` cap: the floor is **N = 35**
(`wilson_upper(0,35) = 0.0989`; at `N = 34` it is `0.1015`). This matches the
floor computed in the pending Tier 1 revision.

**Every site in this experiment sits below that floor.** The best is hs34 at 22
dosed rows; the shallow ladder D1-D4 sits at **2**. Firing more often than a
family that fires zero times is not the same as clearing the bar. The correct
statement is that **the fired-only selectivity measurement is NOT-ADJUDICABLE at
every arm of this experiment**, and it is pre-registered as such here rather than
discovered at resolve. This is a known, accepted limitation of running a
near-perfect readout gate: the better the gate separates, the fewer known-correct
rows it ever doses, and the less there is for a cost metric to measure.

**Registered anyway, because the cap must not be able to pass vacuously.** The
population is **not** restricted to fired rows -- changing the G2 population
would silently redefine a gate transcribed verbatim from the parent and break
comparability with every prior family. Instead, all three numbers are reported
together for every arm, pre-stated here:

1. **G2 as transcribed** (all known_correct_answered rows) -- the gating number,
   unchanged.
2. **Fired-only companion** -- `not_well_formed_correct` restricted to
   known-correct rows that actually fired, with `n_fired_known` and a Wilson
   interval. **Non-gating, reported always.** This is the number that says
   whether dosing hurt the rows it reached.
3. **Undosed floor** -- the same metric on the arm's own undosed pass (and on C0
   for the OFF arms), so the dosed value is read against the base rate rather
   than against zero.

**Pre-stated interpretation rule (revised 2026-07-24, lead).** An earlier draft
used a `n_fired_known < 10` threshold. That number was not derived from anything;
it is replaced by the computed floor.

- **`n_fired_known >= 35`** -- the fired-only companion is adjudicable and is
  reported as PASS or FAIL on the registered `<= 0.05` / Wilson-upper `< 0.10`
  criteria.
- **`n_fired_known < 35`** -- the fired-only companion is reported as
  **NOT-ADJUDICABLE**, a disposition **distinct from PASS and from FAIL**, with
  `n_fired_known` printed beside it. On the projections above this is expected to
  fire at **every arm**. It may not be cited as evidence that the intervention is
  harmless -- only that the base model's known-correct well-formedness is intact.
  A vacuous pass is recorded as a vacuous pass, never as a pass.

The gating G2 (full-population, as transcribed) is **unchanged** and still
decides the arm, because changing a gate transcribed verbatim from the parent
would break comparability with every prior family and would be goalpost movement.
What changes is only what the companion number may be *called*.

Conversely, if the fired-only rate exceeds the 0.05 cap while the
full-population G2 passes, that discrepancy is reported in the headline summary
for the arm, not buried in a table; it means dosing did cost the rows it reached
and the full-population number diluted it. This reporting rule applies even when
the companion is NOT-ADJUDICABLE -- a 2/2 failure on two dosed rows is not
gradeable, but it is not something to leave out of the summary either.

**G3 (`g3_direction_specificity`) was added 2026-07-25, pre-signature.** It
applies to A3 and A5 only, via their placebo counterparts P1 and P2. It adds a
gate; it moves no threshold, and G1 and G2 are untouched. See "Pre-sign record:
the direction-specificity control" below for what it establishes and what it
does not, and item 7 of "Open questions at sign" for the three parameters left
to the lead.

## Competing explanations

KV quarantine is **one** account of the parent's gemma null. At least three
others in the parent's `analysis/gemma4-e4b/null_literature_review.md` explain
the same signature -- write lands, direction reads, behavior does not move -- and
one of them explains it at least as completely as KV sharing does. They are named
here, before any run, with what each predicts and whether this design can tell it
apart from KV quarantine.

**Nothing in the parent's dose-response measurement discriminates among them --
and after the `use_cache=False` withdrawal above, it does not even establish the
null it was thought to establish.** The pooled `0/176`, the flat-zero 24 cells,
and the perfect readback were all computed from starved activations, so they no
longer promote the gemma null from impression to measurement; that framing is
withdrawn. What still stands is narrower and is stated at "What survives the
defect": the write reaches behavior (collapse rises to 1.00), the metric is sharp
(`clean_tighten` fires on 1662/1663 natural gemma refusals and 0/1393 undosed
confab rows), and the llama positive control rules out an instrument artifact
(llama has no cross-layer KV sharing, so its extraction was never affected).
None of that discriminates among the accounts below. Any reading of this document
in which the parent's dose-response null counts as evidence *for* KV quarantine
is a misreading, and it is doubly unavailable now: the measurement is
uninterpretable *and* it was never discriminating.

**(1) Linear accessibility / the crystallization gap (2604.15557).** The parent's
review calls this **the strongest competing explanation in the review**, and the
drafter agrees. Its claim: a direction's *decodability* by a probe is not the
same property as its *alignment with the output projection*, and steering
succeeds only where the representation has become output-aligned. It predicts
exactly the signature we have -- high gate AUC with zero `clean_tighten`,
i.e. decodable but not output-aligned -- and it additionally predicts something KV
sharing does not: the **absence of any window between inert and collapse** on the
ladder, which is what the parent observed (0.100-0.361 inert with
`collapse_rate_on_dosed` 0.00, collapse 1.00 by 0.850, tighten 0.000 throughout).
Two provenance notes, so this paragraph is not read as more than it is. The AUCs
originally quoted here (0.977-0.982) were the corrupt FIT figures and are
withdrawn; the clean held-out equivalents are **higher, not lower** -- 0.9770 to
0.9999 across hs15-hs42, peaking at 0.9996-0.9999 in the shallow band -- so the
"decodable" half of the signature is strengthened, not weakened, by the
correction. The ladder observations, by contrast, are corrupt-derived and inherit
the withdrawal; they are retained here as the shape this account predicts, not as
established fact about gemma.
The review also records that in this framework the common "steer at a middle
layer" heuristic has no effect on Gemma-2-2B. **This account is at least as
complete as ours on the parent's own evidence, and on the no-window observation
specifically it is more complete** -- KV quarantine has no particular reason to
predict the absence of a window, whereas Regime 2 predicts it directly.

**Where the two hypotheses are identical, stated explicitly.** Both predict, for
the parent's registered mid-band sites under the stock configuration: high KU
readout gate AUC (decodable); `frac_readback_within_tol` = 1.0 (the write lands);
`clean_tighten` = 0 at every rung; and a monotone inert-to-collapse ladder with no
intervening window. Every single number in "The result this follows from" is
jointly predicted. **The parent's evidence cannot choose between them, and this
experiment must not pretend otherwise.**

**(2) Representational entanglement blocking linear correction (2605.05715).**
The closest published analogue to the parent's result: failures that are linearly
decodable are nonetheless not correctable by fixed residual-stream linear
steering, because the target is entangled with the features the same direction
moves. The review records that it replicates **across architectures**, which is
precisely why the "Gemma fingerprint" reading was withdrawn above. Also a site
property, and subject to the same caveat as (1) below: A1-vs-A2 holds the site
*index* fixed, not the site's *representation*.

**(3) Generic self-repair (the Hydra-effect cluster).** Downstream components
compensate for an ablated or perturbed component, restoring the original
computation. This predicts a write that lands and does nothing, in **every**
family -- which is both its strength as an explanation and the reason it cannot
be evidence *for* an architectural story about Gemma specifically. It is why the
terminal-layer collapse-onset observation was struck from the motivation above
rather than softened. Self-repair operates on whatever is written wherever it is
written. It is the one competitor that is genuinely held fixed across A1/A2,
because it is a property of the downstream compensation machinery rather than of
the representation at the write point -- though the OFF condition does change
which components are downstream-active, so even this is not perfectly controlled.

**(4) Steering-vector non-identifiability (2602.06801).** The fitted direction is
not a unique object: many directions read the contrast equally well and only some
of them are causal, so a high-AUC direction that fails to actuate may simply be
the wrong member of the equivalence class. This is a property of the *fit*, not
of the site -- but A1 and A2 refit under their own conditions on the **same FIT
rows with the same pinned seed**, and the ON-fit-vs-OFF-fit cosine diagnostic is
recorded, so a non-identifiability story has to explain why the same fitting
procedure on the same rows lands on a causal direction in one condition and a
non-causal one in the other.

### The divergence, and the one measurement that produces it

**A drafter's correction, load-bearing.** An earlier revision of this document
asserted that A1-vs-A2 "holds the site fixed and therefore holds every competing
site-property explanation fixed." **That is false, and it was the weakest claim
in the draft.** hs38 is the output of block 37, which is a KV-*shared* block.
Turning sharing OFF changes the forward computation of blocks 24 through 37 --
all of them upstream of hs38. The OFF model's residual stream at hs38 is
therefore a genuinely different representation, which is precisely why the
directions must be refit (see "Why the sharing-OFF arms refit their directions").
A different representation can have a different `A_lin`, a different entanglement
structure, and a different causal basis. **Holding the site *index* fixed does
not hold the site's *representation* fixed.** So a bare behavioral difference
between A1 and A2 is jointly explained by "the KV pathway was restored" and by
"the OFF model happens to be more linearly accessible at hs38," and by itself
discriminates nothing.

**Where the hypotheses actually diverge.** Regime 2 makes actuation a function of
linear accessibility at the write point: *if `A_lin` is unchanged, behavior is
unchanged*. KV quarantine makes actuation a function of whether the write can
enter the K/V that downstream layers attend over, **independently of `A_lin`**.
So the discriminating observable is not the behavioral delta alone; it is the
**joint** observation of the behavioral delta and the `A_lin` delta across the
same two arms:

| A2 vs A1 behavior | `A_lin`(hs38, OFF) vs (hs38, ON) | What it discriminates |
|---|---|---|
| A2 actuates, A1 does not | **unchanged** (\|Δ\| <= 0.05) | **DISCRIMINATING.** Regime 2 predicts no behavioral change at constant accessibility; the change happened. KV quarantine supported, Regime 2 disconfirmed *at this site*. |
| A2 actuates, A1 does not | **rose** (Δ > 0.05) | **NOT discriminating.** Jointly explained. Reported as jointly explained; promotes nothing. |
| Neither actuates | any | KV quarantine disconfirmed (subject to Threats (b), the stale-projection caveat). Regime 2 untouched and still standing. |
| A1 actuates | any | VOID -- the parent null did not reproduce; see the falsifier's VOID disposition. |

The 0.05 band is fixed here, before any measurement, and is chosen to match the
G2 cap already used elsewhere in this document as the threshold of materiality.

**This forces a design change, registered here.** G0-ALIN as previously drafted
measured `A_lin` only at candidate sites under sharing ON, on cached activations,
CPU-only. That is **not sufficient**: the discriminating cell above requires
`A_lin(hs38)` under **both** conditions. Measuring it under OFF requires a fresh
activation extraction with the patch active, which is a **GPU stage**, not a
free CPU pre-sign deliverable. It is registered as a required stage of the run
(`extract_anchor.py --kv-sharing off`), and its output is reported for every
outcome, including nulls. **Without this measurement the primary contrast
discriminates nothing, and the experiment is not worth running.**

**What a negative A2 does and does not license.** If A2 fails with C1 passing,
this experiment removes KV quarantine from the list and leaves 1-4 standing --
undifferentiated. It does not choose among them, and the write-up must not imply
that it does. Discriminating 1 from 2 from 3 among themselves needs a different
instrument.

**The below-seam arms do NOT discriminate, and are labeled descriptive.** The
lead asked directly whether actuation at a below-seam site (blocks <= 23) would
be evidence for KV quarantine or merely the ordinary depth effect. **It is the
ordinary depth effect, and A3 carries no discriminating weight.** Two separate
confounds, which should not be blurred:

- **A3 vs A1** (hs22 vs hs38) is confounded with depth outright -- sixteen blocks
  apart. "Gemma is only actuable in its first half" explains an A3-yes/A1-no
  result completely, with no KV story required, and would be expected to
  reproduce in a model with no KV sharing at all.
- **A3 vs A5** (hs22 vs hs24) *does* control depth tightly -- two blocks -- but
  does **not** control linear accessibility, which can differ between adjacent
  sites. That is the confound G0-ALIN's `|ΔA_lin| > 0.10` declaration exists to
  surface, and it cannot be removed by depth-matching.

The parent's own llama numbers make the depth story concrete rather than
hypothetical: llama actuates at hs17 of 28 blocks (depth fraction 0.61) and shows
nonzero tighten as late as hs26 (0.93), while gemma is flat zero at hs34 (0.81)
and hs38 (0.90). No llama site as shallow as gemma's hs22 (0.52) was tested, so
there is no cross-family control for a shallow-site result. Accordingly A3, A4,
A5 and A6 are **descriptive arms**: they map where in gemma the boundary push
actuates at all, which is worth knowing and is reported in full, but **they
cannot promote or refute the KV hypothesis** and no contrast among them appears
in the prediction or the falsifier as supporting evidence. (A3 retains one
non-inferential role in the falsifier: requiring it to also fail before declaring
falsification is a conservatism, not a claim.)

## Threats

**(a) Disabling sharing changes the model's computation.** C1 is the control, and
its criterion is pre-stated numerically above. **Residual risk that C1 does not
cover:** C1 tests undosed *behavior* and *likelihood*, not attention *routing
quality*. A model can keep its base rates and its NLL while its attention
distributions over the shared span are subtly wrong -- and the sharing-OFF arms
are precisely the arms whose interpretation depends on that routing being sane.
So C1 licenses "the OFF model is not broken," not "the OFF model attends the way
the ON model would have." This asymmetry is why a positive A2 is much stronger
evidence than a negative A2 is (see Threats (f) and "Drafter's note").

**(b) The shared-layer projections might be functionally stale even if
trained-looking.** The norm evidence (smooth depth trend, layer-type-correlated
elevation) rules out random init; it does not rule out weights that were trained
under a different regime and then made vestigial when sharing was enabled, nor
weights left over from an ancestor checkpoint. **How C1 bears on it:** if the
projections are stale, the OFF model's blocks 24-41 attend over keys that no
longer match what the rest of the network expects, which should show up as an NLL
increase (C1 criterion 3) well before it shows up in coarse answer rates -- this
is the specific failure mode criterion 3 exists to catch. **What would reveal it
beyond C1:** the C1 NLL delta itself, reported as a number rather than a
pass/fail; a large-but-sub-threshold NLL increase is a warning that must be
carried into the interpretation of any A2 result. **What would settle it, and is
out of scope here:** comparing each shared block's own `k_proj` output against
its donor's on the same input -- if the retained projections were trained to
agree with the donor, they are not independent and the OFF condition is nearly a
no-op; if they diverge strongly, they encode something the shared path discards.
The drafter recommends this as a cheap diagnostic to add before sign (see "Open
questions at sign" #4).

**(c) Depth confound.** A1-vs-A2 eliminates it completely: identical site,
identical ladder, identical rows; only the KV pathway differs. A3/A5-vs-A1 does
NOT eliminate it -- hs22 and hs38 are 16 blocks apart, and any difference between
them is jointly explained by depth and by donor reachability. This is exactly why
**A5 (hs24) exists**: it is quarantined like hs38 but sits two blocks from hs22,
so an A3-yes / A5-no pattern is a *depth-controlled* seam effect. It is not a
perfect control -- hs22 and hs24 still differ by two blocks of computation, and
hs22's write is broadcast to all 18 top blocks through the donors while hs24's is
not (that broadcast IS the mechanism, not a confound). The residual depth
exposure across A3/A5 is two blocks out of 42; across A3/A1 it is sixteen.

**But controlling depth is not enough, and this is why A3/A5 are descriptive
rather than gating.** Depth is only one of the site properties that co-vary with
donor reachability. Linear accessibility (`A_lin`) rises with depth and is *not*
held fixed by the A3/A5 pairing either -- two blocks of computation can move it,
and the crystallization-gap account predicts an A3-yes / A5-no pattern for
`A_lin` reasons alone. So the tightest below-seam contrast available here still
cannot separate "the donors were reachable" from "the representation was still
malleable." No configuration of A3/A4/A5/A6 discriminates the two hypotheses;
only A1-vs-A2 with the paired `A_lin` measurement does. The below-seam arms are
reported for their descriptive value -- whether this model can be actuated
*anywhere* -- and carry no weight in the success rule.

**(d) Multiple arms invite selective reporting.** The primary contrast is
pre-stated here as **A1-vs-A2 and nothing else**; every other contrast is labeled
secondary/descriptive in this document before any run. **Every arm is reported
regardless of outcome**, including NOT-RUN arms with their full per-rung FIT
tables and the explicit blocker. No arm may be added, dropped, or re-labeled
after any result is seen; A6's conditionality is registered here in advance with
its trigger (A3 has a usable FIT dose) and its rationale. Arm-level multiplicity
is real -- six dosed arms against a two-part gate -- and is the reason no arm
other than A2 can promote a claim, and why even A2 promotes an exploratory lead
requiring confirmatory replication, not a headline number.

**(e) Oracle leak / circularity.** Inherited discipline: directions, `tau`, and
the anchor-norm denominator are fit on **FIT only**; the dose is selected on
**FIT only** by the registered selection rule; gates are scored on **HELD-OUT
only**. Nothing about held-out rows informs any fit or any dose choice. Sites are
chosen from **architecture** (donor reachability computed from the pinned config)
and from the **parent's already-registered** eff-dim peak -- zero data-dependent
site freedom in this experiment. Refits under OFF use the same pinned seed and
the same FIT row ids as under ON. **The largest remaining circularity risk is
C1**: a control whose criterion is settled after seeing A2 would become an escape
hatch that can rescue any outcome. It is therefore numeric, pre-stated, and
evaluated and written down before any OFF arm touches held-out.

**(f) Asymmetric evidential strength (drafter-added).** A positive A2 is strong:
no artifact of the patch plausibly *creates* selective, well-formed confab
tightening at a 0.50 floor while leaving known-correct cost under 0.05. A
negative A2 is weak: it is jointly explained by "quarantine is not the cause" and
by "the OFF model's retained projections do not do the job the trained shared
path did." The falsifier above is written to require **both** A2 and A3 to fail
precisely so that this weakness cannot kill a true hypothesis on its own.

**(g) The parent's own interpretive caveat carries forward.** The parent recorded
that gemma's eff_dim profile is near-flat (0.0046-0.0058 across 9 of 10 sweep
points, no workspace-like peak distinct from noise). If the boundary push simply
has no structure to act on in this
model at any depth, every arm here nulls and the KV hypothesis is neither
supported nor refuted -- it is untested. That outcome is the NULL-RESULT
disposition above, and it must not be written up as a falsification.

**(h) Gemma has NO held-out BEHAVIORAL run at all, and the FIT ladder is its
entire behavioral evidentiary base.** *Rewritten 2026-07-24 (lead); the earlier
version of this threat extended the "FIT-scale only" caveat to the readout-side
figures as well, which is no longer accurate.* Verified at source in the parent
experiment: `analysis/gemma4-e4b/` contains no `full_summary.json` and no
`runlog/full/`, and the only `full_summary.json` anywhere in the parent tree is
`analysis-committed/llama-3.2-3b/full_summary.json`. The parent's own analysis
states it: "Gemma has no held-out `run_contrast.py` run on disk"
(`analysis/gemma4-e4b/dose_response_window.md`, lines 22-24).

Separate the two sides, because the defect and the split hit them differently:

- **Behavioral side -- still FIT-scale, and additionally corrupt-derived.** The
  pooled tighten with Wilson [0.000, 0.021], the per-cell 0/8 with Wilson
  [0.000, 0.324], and the collapse onsets are all FIT cells of n=8 confab rows,
  *and* they were produced from the `use_cache=False` activations. Both
  limitations apply at once. This is why the framing is withdrawn above rather
  than merely caveated.
- **Readout side -- now clean AND held-out.** The KU readout gate has been
  refit on the clean `use_cache=True` extract and profiled on the HELD-OUT split
  (`known_held` = 270, `confab_held` = 168;
  `analysis/gemma4-e4b/read_profile_full_depth.json`, gitignored-private). The
  AUCs and `fpr_known_correct_flagged` figures now cited in `gates.yaml` are
  held-out, not FIT-scale. The old caveat on them is retired; do not re-apply it.

Three consequences, stated rather than absorbed:

1. **The behavioral null this experiment follows from is weaker than llama's or
   mistral's, on two independent counts.** Llama has a committed held-out
   summary; mistral has a held-out pass in progress. Gemma's has never been
   reproduced on rows that did not participate in fitting the direction, `tau`,
   or the anchor norm -- and the direction, `tau`, and anchor norm it was fit
   against were themselves computed from starved activations.
2. **It does not weaken the FIT/HELD-OUT firewall inside *this* experiment.** The
   gates here are scored on held-out only, exactly as inherited; the missing
   parent held-out behavioral run is a limitation on the *motivation*, not a leak
   in the design. This experiment will produce gemma's first held-out behavioral
   numbers.
3. **It bounds what a negative result licenses.** If every arm here nulls, the
   correct statement is "gemma's null replicates, now on held-out and on clean
   activations, and is not explained by KV quarantine" -- not "the parent finding
   was confirmed," because there was no interpretable parent finding to confirm.
   What the G2 assessment in `gates.yaml` still inherits is the *diagnosticity*
   limit, not a provenance one: at every site the fired-only denominator falls
   below the computed Wilson floor of 35, so that companion is
   **NOT-ADJUDICABLE** by registration.

## Analysis and reporting plan

Committed per arm (ID-only manifests and aggregate JSON; no row text):

1. **Per-arm FIT ladder table** -- all 8 rungs: ratio, absolute dose, median
   anchor norm, `frac_readback_within_tol`, `collapse_rate_on_dosed`, confab
   `clean_tighten`, known-correct cost, `usable`. Reported for NOT-RUN arms too.
2. **Per-arm held-out result** at the selected dose -- G1 and G2 point estimates
   with Wilson 95% intervals, n per population, pass/fail per gate. G2 is
   reported as the **triple** registered under "What G2 measures here":
   full-population (gating), fired-only with `n_fired_known` (non-gating), and
   the undosed floor -- with the fired-only companion labeled
   **NOT-ADJUDICABLE** whenever `n_fired_known < 35`, the arithmetic floor
   computed for this gate's own `< 0.10` Wilson-upper cap. NOT-ADJUDICABLE is
   reported as its own disposition, never as a pass and never as a fail. On the
   clean held-out fire rates, every arm is expected to land there.
3. **Primary contrast**, reported as the JOINT outcome, never as the behavioral
   half alone: A2 pass/fail vs A1 pass/fail with both held-out `clean_tighten`
   rates, CIs, and the A2-minus-A1 delta, **alongside**
   `A_lin(hs38, ON)`, `A_lin(hs38, OFF)`, and `|ΔA_lin|` against the 0.05 band --
   with the resulting outcome (1)/(2)/(3)/(4) from the pre-stated table named
   explicitly. A behavioral result reported without its `A_lin` pair is a
   reporting violation, not a partial result.
4. **Descriptive contrasts**, each as a delta with CIs and each labeled
   non-discriminating: A3 vs A5, A3 vs A1 (also labeled depth-confounded),
   A4 vs A3, A6 (if run). None of these may be cited as evidence for or against
   the KV hypothesis.
5. **G0-KV preflight record** -- architecture check, both-direction projection
   call counts per block, the cache-shape and per-layer cache-growth traces, the
   ON-condition cache-substitution token-identity result, all four
   donor-reachability outcomes, and the shared-projection norm table.
5b. **G0-ALIN Part 1 record** -- `A_lin` at all six candidate sites on FIT
   (stock activations), the resulting A3 selection, and the `|ΔA_lin(A3, A5)|`
   confound declaration. Reported whatever the arms show, and reported even if
   the experiment resolves NOT-RUN.
5c. **G0-ALIN Part 2 record** -- `A_lin(hs38)` under both KV conditions from the
   two extractions, `|ΔA_lin|`, the 0.05 band verdict, and the named outcome row.
   If Part 2 was not run, that fact is stated in the headline summary and the
   result is reported as outcome (2) by construction, never as outcome (1).
6. **C1 record** -- all three criteria with numbers, computed and written before
   any OFF held-out scoring.
7. **Direction-fit diagnostics** -- per-site gate AUCs in both conditions, and
   the ON-fit vs OFF-fit cosine similarity of `c_hat` and `u_d` at hs38.

Resolution maps to exactly one of: `resolved` (quarantine supported: prediction
met), `falsified` (falsifier fired), `null-result` (no arm has a usable dose), or
a `resolved` VOID/INCONCLUSIVE verdict spelled out in the verdict string. Nothing
here is pooled with the headline matrix or with the parent, and a supported
result promotes an **exploratory lead** -- "the gemma null is site-structural,
not model-intrinsic" -- which would need a registered confirmatory replication
(fresh seeds, and ideally a second KV-sharing checkpoint such as Gemma-4-E2B,
whose 20/35 sharing ratio puts its seam at a different depth) before any claim.

## Predictions scoreboard

Registered before any GPU work. Calls do not move after results.

| Predictor | Call |
|-----------|------|
| orchestrator | *(to fill before sign)* |
| user | *(to fill before sign)* |
| drafter | PARTIAL: at least one below-seam or sharing-OFF arm finds a usable FIT dose -- a qualitative break from the parent's flat 0.000 at every cell -- but no arm clears the full G1 0.50 floor on held-out. Basis: the parent's gemma tighten rate was not merely low, it was exactly zero at all 32 cells, which is a large distance to close, and gemma's flat eff-dim profile is consistent with weak structure at every depth. |

## Open questions at sign (for the lead)

1. **Pool/split promotion.** *(The hs38 direction/gate clause is CLOSED as of
   2026-07-25; pool/split promotion remains OPEN.)*

   ~~and (for A1) the parent's frozen hs38 direction/gate~~ — **A1 no longer
   consumes the parent's hs38 artifacts.** `cell.yaml` carried a live
   contradiction: `inputs_reused.frozen_hs38_direction` said A1 reuses them,
   while `readouts.method` said every arm fits its own directions under its own
   KV-sharing condition. The lead resolved it on 2026-07-25, before any GPU work
   on the main run, in favour of `readouts.method`: **A1 refits hs38 fresh on
   this experiment's FIT split under sharing ON, exactly like every other arm.**
   Reuse was not merely inconsistent but untenable — the parent's hs34/hs38/hs42
   artifacts are corrupt-derived (`AMENDMENT.md:637`, `PROVENANCE.md`), so
   reusing them would seat a corrupt direction in the very arm that A2 is
   contrasted against (`primary_contrast: A2_vs_A1`). A1 replicates the parent's
   **site and method**, not its artifacts. No code change was required;
   `cell.yaml` was corrected in two places.

   ~~Still open: this experiment consumes the parent's gemma
   fresh-mined pool and FIT/HELD-OUT split. Under the `experiments` skill promotion rule, the second
   consumer triggers promotion to `experiments/common/`. The drafter did not
   promote anything (no commits authorized, and the parent lives on the
   `exp/j-space-cross-family-layer-contrast` worktree, not on `main`). The lead
   must decide: promote to `experiments/common/` and repoint `inputs:`, or
   consume in place. Either way the parent's branch must be merged or the
   artifacts made reachable before any path here resolves.~~

   **CLOSED 2026-07-29 (lead, user-approved): promotion.** The parent merged to
   main (PR #336) and the gemma committed-class artifacts were promoted to
   `experiments/common/artifacts/jspace-cross-family-gemma4-e4b/` with a
   `PROVENANCE.md` (lead resolution of 2026-07-25 recorded there). Completed
   today: `arch_literature_memo.md` promoted into the same directory
   (sha256-verified copy of the parent's private-analysis original; content is
   architecture literature only, no row data), and the manifest `inputs:` list
   uncommented with the four parent governed docs pointing at the parent's
   tracked paths on main and the seven artifacts pointing at the promoted
   copies. This experiment's own `analysis-committed/gemma4-e4b/` already
   consumes the promoted pool/split via git symlinks (mode 120000), so no
   in-tree path changes.
2. **Instrument integration.** *(Largely CLOSED 2026-07-25 — see
   `cell.yaml integration_status.done`. The `instrument.persistence` timings and
   the remaining drivers are still outstanding, so this item does not clear
   `bin/exp sign`.)*

   **Done.** `--kv-sharing {on,off}` is threaded through `extract_anchor.py`,
   `build_directions.py`, `gate_fit.py`, `calibrate_dose.py`, `run_contrast.py`
   and `pipeline.py`. Two of those — `build_directions.py` and `gate_fit.py` —
   were **not** on the original list; `readouts.refit_policy` requires the
   sharing-OFF arms to refit their own directions, tau and median anchor norms,
   so the condition axis has to reach every *fitted* artifact, not just the
   activations. Every artifact filename is condition-scoped via
   `kv_seam_patch.condition_artifact`, with `on` as the identity so historical
   filenames are byte-for-byte unchanged; every cross-condition read is
   fail-closed, raising and naming the stage that produces the missing artifact
   rather than silently falling back to ON parameters the arm never fit (which
   would make A1-vs-A2 a comparison of an arm against itself). The fresh
   per-call `build_full_length_cache(model)` contract is applied to every
   `generate()` in every arm, and extended to `extract_anchor.py`'s plain
   forward — the contract's letter covers `generate()` only, but its intent
   (identical cache construction across conditions) covers any forward that
   builds a cache. Call-site counters for
   `cache_construction_identical_in_both_arms` are in place.
   `kv_seam_preflight.py` now runs **6/6 PASS** on CPU, checks 5 and 6 being the
   `cache_growth_under_off` and `cache_substitution_noop_under_on` gate criteria
   implemented verbatim.

   **Still outstanding:** `alin_sweep.py` (Parts 1 and 2), the fired-only G2
   companion metric, `rollup.py`, and the measured smoke wall-clock timings for
   `instrument.persistence`.

   *(Original text, retained for audit:)* The copied scripts are byte-identical
   parent copies and do NOT yet carry: the `--kv-sharing {on,off}` flag; the
   **fresh-per-call `build_full_length_cache(model)` passed as
   `past_key_values=` on EVERY `generate()` call in EVERY arm, ON and OFF alike**
   (OFF arms raise IndexError without it -- see "The core manipulation" -- and ON
   arms need it too, because if the two conditions construct the cache differently
   the contrast is no longer attributable to the KV pathway); the
   `--kv-sharing off` extraction stage for G0-ALIN Part 2; the condition field in
   output records and manifests; or the G0-KV preflight driver including the new
   cache-growth and cache-substitution-no-op checks. These must be written and smoke-timed before
   `bin/exp sign` -- and `sign` will refuse until `instrument.persistence` is
   complete, which requires those measured timings.
3. **C1 NLL threshold. CLOSED — FIXED AT 10%.** Fixed by the lead on
   2026-07-25, before C1 runs and before any GPU work on this experiment. The
   drafter offered 10% or a stricter 5%; 10% stands, and is written into
   `gates.yaml` as `threshold_frac: 0.10` with a `resolved_by_lead` note. **This
   parameter is now closed and moves for no result.**
4. **Recommended added diagnostic (drafter). CLOSED — RUN 2026-07-25. Result:
   the sharing-OFF manipulation is STRONG, and the risk this diagnostic was
   built to detect did not materialize.**

   Authorized by the lead as a scoped GPU carve-out
   (`cell.yaml execution.gpu_carve_outs.donor_projection_diagnostic`) while the
   main run stays blocked, on the reasoning that a pre-sign de-risking
   measurement cannot do its job after signing. Driver: `donor_diagnostic.py`,
   4 rows of the parent's gemma pool, `google/gemma-4-E4B-it` bf16 on the local
   3090, forward passes only — no dosing, no generation, no arm executed,
   nothing written to `analysis-committed/`.

   **Every block in 24..41 computes K and V essentially ORTHOGONAL to what its
   donor produces.** Median per-block cosine across 4 rows: **k_proj −0.0024**
   (range −0.0026..−0.0020), **v_proj −0.0051** (range −0.0056..−0.0047). The
   largest cosine at any block on any row was **0.032**. Bit-identical across
   two independent invocations. Per-block detail and the full record are in
   `analysis/gemma4-e4b/donor_projection_diagnostic.json` (private).

   **What this licenses.** The feared outcome was a high cosine, under which OFF
   would be nearly a no-op and a negative A2 would mean almost nothing. That is
   not what the data show. A2 is a genuine manipulation of the KV pathway, so an
   A2 null will be informative rather than vacuous. This does **not** promote
   anything about the *direction* of the effect — it removes one specific way
   the primary contrast could have been dead on arrival, nothing more.

   **Read the cosine, not the rel-L2.** `rel_l2_err` came out at 3–14, which
   looks alarming and is mostly an artifact of where the hooks sit: they capture
   `k_proj`/`v_proj` output **before** `Gemma4TextAttention`'s `k_norm`/`v_norm`
   (`Gemma4RMSNorm` over `head_dim`). Gemma's residual norm grows with depth, so
   blocks 24..41 project a much larger-magnitude input than blocks 22/23, and
   `rel_l2_err` inherits that scale gap wholesale — RMSNorm then removes it.
   Cosine is scale-invariant and is the load-bearing statistic. This caveat is
   emitted into the JSON as `measurement_caveat` so it cannot be separated from
   the numbers later.

   **One structural note worth carrying forward.** The three full-attention
   shared blocks (29, 35, 41, donor 23) show markedly lower `rel_l2_err`
   (2.7–7.4) than the fifteen sliding-attention ones (5.8–14.6, donor 22).
   Their cosines are equally near zero, so this changes no conclusion here — but
   it is a scale difference between the two donor channels, and A6 (the
   sliding-vs-full donor-channel arm) is the arm that would notice it.
5. **`A_lin` is now TWO deliverables, and the second one is a decision.**
   *Part 1* (site selection for the descriptive A3 arm) is CPU-only over the
   parent's already-cached gemma activations, touches no GPU, and the drafter
   still recommends running it before `bin/exp sign` so the arm table is complete
   at signature. *Part 2* -- `A_lin(hs38)` under **both** KV conditions -- is
   **not** a pre-sign CPU deliverable: no activation cache exists for the
   sharing-OFF model, so it requires `extract_anchor.py --kv-sharing off` on GPU.
   **This is the item the lead must actually decide.** Part 2 is what makes the
   primary contrast discriminating; without it, a positive A2 is jointly
   explained by the crystallization-gap account and promotes nothing. The drafter
   recommends the experiment not be run without Part 2. If the lead disagrees,
   the disagreement should be recorded here before signing, not after a result
   arrives.
6. **~~Whether A1/A2 or A3/A5 should be the primary.~~ CLOSED, but for a
   corrected reason.** The drafter's earlier recommendation to swap is
   **withdrawn** -- A1/A2 remains the primary. The reason originally given ("it
   holds the injection site fixed and therefore holds every competing
   site-property explanation fixed") was **wrong** and is corrected in "Drafter's
   note": A1/A2 holds the site *index* fixed, not the site's representation.
   A1/A2 is correct because it is the only contrast that *can* be made
   discriminating -- by pairing it with G0-ALIN Part 2. No decision is needed on
   which contrast is primary; the decision that remains is item 5. *(Superseded
   in one respect on 2026-07-25: item 7 below adds a second live decision. Item
   6's substance -- that the primary contrast is settled -- is unchanged.)*

7. **The placebo arms.** *(Two of the three sub-items were CLOSED by the lead
   on 2026-07-25, the same day, before any arm has run. (b) remains a recorded
   limitation rather than an open decision.)*
   Registered 2026-07-25, pre-signature, before any arm has run: arms `P1`/`P2`
   in `cell.yaml`, block `placebo_direction_control`, and gate
   `g3_direction_specificity` in `gates.yaml`. What is registered is a
   matched-magnitude random-direction control at hs22 and hs24 -- same site,
   same dose, same fired rows, same law, **only the written direction differs**.

   **(a) K, the number of draws. CLOSED: K = 5, hs22 and hs24 only.** Fixed by
   the lead 2026-07-25, before any placebo draw exists. The drafter offered 3
   (the inherited hard floor from `rr3-corrected-placebo-replication/gates_lib.py`,
   which raises below 3), 5, and 15 (census-matched); **5** stands. Cost is
   roughly linear in K -- order 20-30 min of GPU per draw per site, so order 3-5
   GPU hours across both sites plus one undosed baseline pass per site. The
   P-arms are **not** extended to the shallow ladder D1-D4; see (c). This
   parameter is now CLOSED and moves for no result.

   **(b) The criterion is RG1, not the program's current best.** The state of
   the art is `gate-contribution-factorial` S1, whose own text (`gates.yaml:108`)
   says it **supersedes** RR3's K=3 max. S1 is not used here for one reason and
   it should be stated plainly rather than buried: **S1's denominator is a
   per-family census null, and gemma has no census.** The available numbers are
   qwen's 0.0833 and mistral's 0.2033 -- another family's random-direction
   sensitivity. Importing one would be the same substitution this design refuses
   everywhere else. RG1 is used instead *because* it computes its own denominator
   from the same run at the same site on the same rows. That is genuinely weaker
   -- 3-5 draws estimate a tail worse than 15 do -- and it is recorded as a
   limitation of this experiment, not argued away. If the lead would rather buy
   the stronger criterion, the purchase is a gemma placebo census, and that is a
   separate experiment, not a parameter here.

   **(c) `success_rule` and `falsifier_rule`. One CLOSED, one standing as a
   limitation.**
   - **`success_rule`: unchanged, and it stays unchanged.** A3 and A5 are
     descriptive and already sit outside it. G3 cannot make the prediction MET.
   - **`falsifier_rule`: AMENDED by the lead 2026-07-25.** The drafter registered
     this as open and declined to decide it, because the amendment runs in the
     **permissive** direction -- it makes falsification *easier* than the rule
     originally registered, by adding a second way for A3 to count as failing.
     The lead's decision, with the lead's reasoning: an A3 that raises hedging no
     more than a random vector of the same magnitude at the same site on the same
     rows has not actuated in any sense this program can use, and letting such a
     result block falsification would preserve the hypothesis on evidence that
     supports nothing. Taken **before any arm has run and before any placebo draw
     exists**, so it cannot have been chosen to fit a result.
     The new clause is bounded, and the bounds are registered with it in
     `gates.yaml falsifier_rule [A3-CLAUSE]`: G3 must be **ADJUDICATED** (K = 5
     accepted draws clearing SC1, P1 readback in tolerance) -- a NOT-RUN or
     unadjudicated G3 is **never** read as a failed G3; PASS-DEGENERATE counts as
     a pass and does not satisfy the clause; and the clause applies to **A3 only**,
     leaving A2's limb of the falsifier untouched.
   - **Standing limitation, not resolved.** `falsifier_rule` clause (ii) reads
     any D1-D4 G1 pass as "gemma IS actuable", and no D arm has a placebo
     counterpart. Scope was fixed at hs22/hs24 only, so extending P-arms to the
     four D sites (roughly quadrupling (a)'s cost) was declined. Any D-arm
     actuation claim therefore rests on evidence G3 exists to demand, and **must
     be reported with that caveat attached** rather than as a clean positive.

   **Nothing in this item authorizes a run.** `execution.gpu_work_by_this_agent`
   remains `forbidden`; the two standing carve-outs
   (`donor_projection_diagnostic`, `seam_pair_dose_calibration`) are both
   complete and neither covers `run_contrast.py` in any mode. The placebo arms
   are **registered, not runnable**: `run_contrast.py` has no random-direction
   code path today, and writing one is greenfield work that has not been done.

## Drafter's note (recorded for the lead; not a design change)

**The drafter's earlier dissent is WITHDRAWN.** An earlier revision of this
document recommended making A3-vs-A5 the primary contrast and demoting A1-vs-A2.
That recommendation was wrong, and the reasoning that replaced it is recorded
here so the reversal is auditable rather than silent.

The dissent's premise was sound as far as it went: A1-vs-A2 removes the depth
confound by introducing a **model-identity** confound. A1 and A2 are not the same
model -- the OFF model runs 18 blocks through projections the trained forward
pass never executes, its residual stream at hs38 is a different distribution
(which is why the directions must be refit), and the only evidence that it is the
"same" model is C1, whose reach is limited (Threats (a), (b)). That is a real
cost and it is why a negative A2 is weak evidence (Threats (f)) and why this
draft's falsifier requires A3 to fail as well.

**What the dissent missed is that the alternative is worse, for a reason that has
nothing to do with depth.** A3-vs-A5 varies the injection *site*. Every competing
explanation in "Competing explanations" -- linear accessibility / crystallization
gap, entanglement, self-repair topology -- is a *site property*. Varying the site
varies all of them simultaneously along with donor reachability, so an A3-yes /
A5-no result is jointly explained by "the write reached the donors" and by "hs22
happens to be linearly accessible and hs24 does not." That is not a two-block
depth confound; it is a confound with the strongest competing hypothesis in the
review, and no amount of depth-matching removes it. G0-ALIN can *declare* it (the
`|ΔA_lin| > 0.10` rule) but cannot control it.

A1-vs-A2 holds the site *index* fixed. It is the only contrast in the design with
any power to separate KV quarantine from the alternatives, and separating them is
the entire scientific point. A cleaner instrument that cannot discriminate is
worth less than a messier instrument that can. The design brief's ordering is
correct; the primary stays A1-vs-A2, and A3-vs-A5 is descriptive.

**A second correction, to this note itself.** An earlier revision of this
paragraph said A1-vs-A2 "holds the site fixed and therefore holds every site
property fixed at once." **That is false.** hs38 is the output of block 37, a
KV-*shared* block; turning sharing OFF changes blocks 24-37, all upstream of
hs38, so the OFF model's representation at hs38 genuinely differs -- which is the
very reason this design refits the directions under OFF. Holding the site index
fixed does **not** hold `A_lin` fixed. The contrast becomes discriminating only
when `A_lin(hs38)` is measured under both conditions and the change is bounded;
that measurement is registered as G0-ALIN Part 2 and its interpretation rule is
the four-outcome table in "The divergence, and the one measurement that produces
it." Without it, A1-vs-A2 is a cleaner instrument that still cannot discriminate.
This correction was found by the drafter while writing the discrimination section
the lead asked for; it is recorded rather than quietly patched because the false
version was load-bearing in two places.

What the drafter still asks the lead to carry forward from the dissent, since the
underlying cost is real and does not disappear because the contrast is right:

- The asymmetry stands. A positive A2 is strong; a negative A2 is weak and is
  never written up as a clean falsification on its own. The two-arm falsifier
  (A2 **and** A3 both fail) is the mechanism that enforces this and must not be
  relaxed.
- The donor-vs-own-`k_proj` comparison (Open questions #4) is the cheapest thing
  that bounds the model-identity confound quantitatively, and it should run
  before GPU time is spent, not after a negative A2 needs explaining.

Two smaller points, both already reflected in the draft above:

- The brief's "candidates must be blocks < 24" is off by the donor offset. hs24
  is below block 24 and still fully quarantined. Any below-seam site list derived
  from the block index rather than from donor reachability would have included a
  quarantined site as a "below-seam" arm and confounded the whole contrast.
- The brief's "if C1 diverges materially, the experiment stops there" is too
  broad. C1 governs only the sharing-OFF arms. A1, A3, A5, and A6 run on the
  unmodified model and a C1 failure has no bearing on them -- which is another
  reason the load-bearing contrast should not depend on C1 at all.

## Pre-sign record: the `seam_pair` site set and its dose calibration

**Added 2026-07-25, pre-sign, under the `seam_pair_dose_calibration` carve-out
in `cell.yaml`. This section records instrument and input state. It adjudicates
no gate and resolves no arm.**

Resolving A3 = hs22 and A5 = hs24 (G0-ALIN Part 1) created a manifest gap: every
stage selects sites through `--site-set`, resolved against
`families/gemma4-e4b.yaml band_selection`, which registered only
`midband_candidates_hs: [34, 38, 42]` and `shallow_ladder_hs: [15, 18, 20, 23]`.
Addressable sites were `{15, 18, 20, 23, 34, 38, 42}` — **neither A3 nor A5 was
addressable by any stage.** A new site set `seam_pair: [22, 24]` was registered
across the three required surfaces (family yaml, `family_config.SITE_SETS`,
`gates.yaml`). `shallow_ladder` and `midband` are untouched, so their existing
artifacts remain comparable against their own history.

**G0 readout, CPU-only** (`gate_fit.py` fits tau on cached activations and never
loads the checkpoint):

| site | role | AUC (neg_z_d, FIT) | TPR | FPR | tau | G0 ≥ 0.90 |
|---|---|---|---|---|---|---|
| hs22 (A3) | below seam, reaches both donors | 0.999702 | 1.000 | 0.006 | +0.09325 | pass |
| hs24 (A5) | at seam, no donors | 0.997569 | 1.000 | 0.033 | −0.10294 | pass |

This matters for interpretability, not just bookkeeping: **an A5 failure to
actuate could not have been attributed to the readout degrading at hs24**, since
the read is near-perfect there. Only the write would have been in question.

**Dose calibration** (FIT split, sharing **ON** only, registered 8-rung
`RATIO_LADDER`, 8 confab + 8 known rows per cell; 24 cells, exit 0):

| site | selected ratio | dose | tighten | known-correct cost | collapse |
|---|---|---|---|---|---|
| hs22 (A3) | 0.361 | 28.5068 | 0.500 | 0.000 | 0.000 |
| hs24 (A5) | 0.554 | 50.5311 | 0.750 | 0.000 | 0.000 |
| hs40 (late ref) | **null** | — | — | — | — |

`all_midband_have_usable_dose: true`. Readback stayed within tolerance at all 24
cells. Both ladders self-limit at high dose (collapse appears at 0.85–2.0),
which is the ladder behaving as designed. hs40's null is the expected outcome —
the late reference is null in llama-3.2-3b and mistral-7b-v03 as well — and the
late arm is skipped without affecting the primary.

**What this does and does not establish.** A5 actuates, and on the selection
statistic it actuates at least as well as A3. hs24 is the first block whose own
K/V never reach anything downstream, so if the KV channel were load-bearing for
a dosed write to take effect, hs24 is where it should have stopped working.
It did not.

That is **not** a refutation of the quarantine account and is not reported as
one. This stage ran sharing ON only, on FIT, with 8 fired rows per cell; it is
not the ON/OFF contrast. Threats (c) above already registers A3-vs-A5 as
descriptive and non-discriminating *regardless of what it shows*, written before
these numbers existed. The 0.750-vs-0.500 gap is n=8 against n=8 with Wilson CIs
[0.41, 0.93] and [0.22, 0.78] — "A5 actuates" is supported; "A5 actuates more"
is not. What the result does change is narrower and real: the tidy version of
the quarantine story is less likely, and an A5 null can no longer be read as
confirmation, because there is no A5 null.

**Consequence for A6.** A6 is registered `conditional_on: "A3 has a usable FIT
dose"`. A3 has one, so **A6 is unlocked.** A6 is hs23, already addressable
through `shallow_ladder`; no further registration is required. Per its
`coincides_with` note it runs once and is reported under both the A6 and D4
labels.

**Incidental, descriptive, non-gating.** The fitted KU directions at hs22 and
hs24 are essentially **orthogonal** (cosine +0.005) despite both reading
known-unknown above 0.997 AUC. Adjacent sites elsewhere share more (0.20–0.26 at
one step). Nothing in the design depends on this; it is recorded because "the
same direction is readable at both depths" would be the wrong mental picture.

## Pre-sign record: the direction-specificity control (P1, P2, G3)

Registered 2026-07-25, before any arm has run. The decisions it leaves open are
item 7 of "Open questions at sign"; this section records why it exists at all.

**The gap it closes.** As drafted before today, this experiment had no undosed
baseline arm on the dosed sites and no random-direction arm anywhere. Under that
design, an arm clearing G1 would have established that *writing a vector of a
particular magnitude at a particular site raises hedging on confabulation rows*
— and nothing further. It would carry no evidence that the KU readout is what
does the work. That is not a hypothetical failure mode in this program: in
`rr3-corrected-placebo-replication`, mistral's **random** direction lifted
hedging by **+21.8 points**, giving an effect ratio of 1.87 against a floor of
3.0 — RG1 FAIL. A run that cannot separate those two accounts cannot contribute
to the question this program is actually asking.

**What is registered.** P1 (hs22, matched to A3) and P2 (hs24, matched to A5):
same site, same calibrated dose, same `erase_write`/`anchor_onward` law, and the
**same fired rows** as the true arm. Only the written direction differs. Draws
are fresh unit normals under registered seeds, screened by the SC1 bar
(`|cos| <= 0.015` against both `c_hat` and `u_d`) with a void-and-redraw ledger,
because at `hidden_dim = 2560` only about a third of raw draws clear it and an
unscreened draw biases the control *toward* the true direction. Magnitude is
matched by the `sigma = 1.0` convention and verified by the same readback
tolerance the true arms carry. G3 passes at `effect_ratio >= 3.0`, denominator
`max` over the **K = 5** accepted draws, transcribed from RR3.

**One rule was amended, by the lead, in the permissive direction.**
`falsifier_rule` now lets an A3 that clears G1 while **failing an adjudicated
G3** count toward falsification (`gates.yaml falsifier_rule [A3-CLAUSE]`). That
makes falsification *easier* than the rule originally registered, which is why
the drafter declined to make it and why it is recorded here as the lead's call,
taken before any arm has run and before any placebo draw exists. Its bounds are
registered with it: a NOT-RUN or unadjudicated G3 is never read as a failed G3,
PASS-DEGENERATE counts as a pass, and the clause reaches A3 only. `success_rule`
is untouched and stays untouched — G3 cannot make the prediction MET.

**Why the fire set is held fixed rather than permuted.** The
`gate-contribution-factorial` construction permutes the gate indices, which
varies gate *and* direction together and answers a different question: how much
of the lift the gate contributes. The question here is narrower and prior to it
— *given the rows the readout selected, does it matter which direction is
written there.* Holding the fire set fixed is what makes that attribution clean.
The cost is that G3 says nothing about the gate's contribution, and that
limitation is registered in `cell.yaml
placebo_direction_control.what_this_does_not_establish` rather than discovered
later.

**What it does not reach.** The primary contrast. A1-vs-A2 sits at hs38 and has
no placebo arm registered; a specificity result at hs22/hs24 does not transfer
to a different site under a different reachability regime. Nor does a G3 pass
make the boundary push selective or safe — G2's dosed known-correct denominator
is roughly 2 rows at these sites and stands NOT-ADJUDICABLE either way.

## Outcome

Filled at resolve. Record the verdict, the per-arm G1/G2 results with Wilson CIs,
the primary contrast, every secondary contrast, the G0-KV preflight record, the
C1 numbers, and the one-sentence summary that also goes into `verdict:` in the
manifest.

**No arm has run.** The GPU work done to date is confined to the two carve-outs
recorded in `cell.yaml execution.gpu_carve_outs` — the donor projection
diagnostic and the `seam_pair` dose calibration above. Both are pre-sign
instrument work on the FIT split. `run_contrast.py` has not been executed in any
mode, no held-out row has been touched, and no gate has been adjudicated.
