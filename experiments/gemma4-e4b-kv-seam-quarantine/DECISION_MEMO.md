# Decision memo: what to run next on gemma-4-E4B

> **SUPERSEDED 2026-07-24 — HISTORICAL DECISION INPUT, RETAINED FOR PROVENANCE.**
> The decision this memo asked for has been made. The user chose the **full
> shallow ladder** (hs15 / hs18 / hs20 / hs23, arms D1-D4), folded into **this**
> experiment rather than a separate one, and the pre-registration has been
> re-grounded on the clean `use_cache=True` activations. `AMENDMENT.md`,
> `gates.yaml`, `cell.yaml` and `experiment.yaml` are the live registration and
> **win over this file wherever they differ.**
>
> Read this memo only for how the decision was reached. Three things in it are
> now known to be stale, and none are corrected inline — correcting a superseded
> memo would destroy the record of what was actually argued:
> - It treats the parent's `0/176` as an established null. It is not; it is
>   corrupt-derived and **uninterpretable, not negative** (parent
>   `AMENDMENT.md:637`). See "The result this follows from".
> - Its readout figures are the corrupt FIT AUCs and `fpr` values. The clean
>   held-out replacements live in `gates.yaml`
>   `vacuity_assessment_for_this_substrate`.
> - Its finding (6) — the live-`.logits` check — has since resolved into the
>   `use_cache=False` diagnosis, a different and more specific defect than the
>   one it was watching for.
>
> What **survives**, and is now load-bearing in the live registration: the
> relative-depth argument. No site above **rd 0.607** has produced a usable dose
> in any family in this program; gemma's shallowest previously-tested site was
> **rd 0.810**. That is why D1-D4 exist.

**Status:** decision input for the lead and the user. Not an amendment, not
signed, nothing committed. `AMENDMENT.md` is left exactly as the stop order
found it (state recorded in Appendix B).

**Author's posture:** I drafted the KV-seam amendment. This memo recommends
**against** running it next. I re-derived findings (1), (2), (3) and (4) from
source rather than accepting them relayed, and two of those re-derivations
changed my recommendation rather than confirming it.

---

## Summary

The decision is not really A-vs-B. It is:

1. **Everything is gated on finding (6).** If gemma's live `.logits` are wrong,
   the 0/176 null is an instrument artifact and neither option means anything.
   That check is running; nothing should be launched before it reports.
2. **Conditional on (6) clearing, run a modified Option B — not Option A, and
   not Option B exactly as briefed.** The modification is small but load-bearing:
   the shallow ladder must straddle the block-22/23 chokepoint rather than sit
   entirely upstream of it, or its null inherits exactly the ambiguity it was
   meant to remove.
3. **Option A should not be built next in any form.** Its informative arms are at
   the wrong depth, and its right-depth arms are the ones I already showed cannot
   discriminate. Details in §3.

**The single number that drives this:** across all three families, **no site has
ever produced a usable dose above relative depth 0.607.** Gemma's shallowest
tested site is **0.810**. Gemma has never been dosed inside the band where
actuation has ever been observed in this program.

---

## 1. What I verified at source

Independently recomputed from `analysis-committed/*/dose_calibration_summary.json`
on the parent worktree. `rd` = hs_index / n_layers.

| family | KV sharing | site | rd | median anchor norm | max confab tighten | rungs > 0 | collapse onset (ratio) | usable dose |
|---|---|---|---|---|---|---|---|---|
| mistral-7b-v03 | none | hs12 | 0.375 | 3.35 | **0.625** | 4/8 | 1.304 | **yes** |
| mistral-7b-v03 | none | hs15 | 0.469 | 4.43 | **0.625** | 5/8 | 2.000 | **yes** |
| mistral-7b-v03 | none | hs19 | 0.594 | 8.01 | 0.000 | 0/8 | 0.850 | no |
| mistral-7b-v03 | none | hs30 | 0.938 | 21.48 | 0.000 | 0/8 | 1.304 | no |
| llama-3.2-3b | none | hs17 | 0.607 | 13.73 | **0.875** | 4/8 | 2.000 | **yes** |
| llama-3.2-3b | none | hs20 | 0.714 | 17.11 | 0.375 | 2/8 | 1.304 | no |
| llama-3.2-3b | none | hs23 | 0.821 | 21.84 | 0.125 | 1/8 | 1.304 | no |
| llama-3.2-3b | none | hs26 | 0.929 | 30.51 | 0.125 | 1/8 | 0.850 | no |
| gemma4-e4b | 18/42 | hs34 | 0.810 | 120.20 | 0.000 | 0/8 | 0.554 | no |
| gemma4-e4b | 18/42 | hs38 | 0.905 | 125.51 | 0.000 | 0/8 | 0.554 | no |
| gemma4-e4b | 18/42 | hs40 | 0.952 | 117.57 | 0.125 | 3/8 | 0.554 | no |
| gemma4-e4b | 18/42 | hs42 | 1.000 | 281.34 | 0.000 | 0/8 | 0.100 | no |

**Finding (1) confirmed, and it is stronger than "a depth trend."** Mistral goes
to a flat 0.000 at rd 0.594 — *shallower* than llama's hs20 (rd 0.714), which
still gets 0.375. So the actuating band is family-specific in absolute relative
depth; what generalizes is that it is **early-to-mid**, and that it has an upper
edge every family has already crossed. The three usable doses in the entire
program sit at rd 0.375, 0.469, 0.607. Gemma's four sites sit at 0.810, 0.905,
0.952, 1.000 — all above the top of that band, by at least 0.20.

Mistral hs19 and hs30 reproduce gemma's exact flat-zero-tighten signature in a
family with **no KV sharing at all**. The signature the KV-seam amendment was
built to explain is not gemma-specific and is not evidence of anything
architectural.

**Finding (2) confirmed, and sharper than "sites were read-selected."** From
`docs/atlas/family-layer-map.md`, the gemma row records best 3-axis clean-control
layers as **"hs 14-18 and hs 36-40"**, with best AUROC (0.9949 / 0.9223 / 0.9272)
all at hs40, and notes that "naive per-axis maxima 1.00 / 0.9305 / 0.9345 at
hs 21/25/26 are control-confounded." The atlas named **two** endorsed bands. The
parent took the deep one (hs34/38/40/42) and tested nothing from the shallow one.
**hs14-18 is rd 0.333-0.429 — almost exactly mistral's two usable sites.** So the
shallow site set for Option B is not a post-hoc invention; it is a pre-existing,
registered, clean-control band that was passed over.

**Finding (3) confirmed and extended.** I read all 42 `layer_scalar` values
directly from the cached checkpoint shard (`safetensors.safe_open` partial reads,
CPU, no model construction) and reproduced §E's four survival figures exactly
(hs34 0.1441 vs 0.144; hs38 0.2719 vs 0.272; hs40 0.3601 vs 0.360; hs42 1.000).
Blocks 22/23 are 0.1572 and 0.0654, product 0.01028. The full downstream-survival
curve, which §E does not publish:

| site | rd | survival of a static delta to the output | 1/survival |
|---|---|---|---|
| hs15 | 0.357 | 2.2e-7 | 4,489,690 |
| hs18 | 0.429 | 1.5e-6 | 653,120 |
| hs22 | 0.524 | 2.8e-5 | 36,105 |
| hs23 | 0.548 | 1.8e-4 | 5,677 |
| **hs24 (KV seam)** | 0.571 | 2.7e-3 | 371 |
| hs26 | 0.619 | 7.5e-3 | 134 |
| hs30 | 0.714 | 5.9e-2 | 17.0 |
| hs34 | 0.810 | 0.144 | 6.9 |
| hs38 | 0.905 | 0.272 | 3.7 |
| hs40 | 0.952 | 0.360 | 2.8 |
| hs42 | 1.000 | 1.000 | 1.0 |

**My correction to how this should be read, and it cuts against the mechanism:**
the naive product substantially **overstates** the attenuation, for a reason
§D of the same report already supplies. `layer_scalar` multiplies the *entire*
residual — context and injected delta together — by one scalar, and every
consumer of the residual stream renormalizes (`input_layernorm` at the next
block, the final RMSNorm before the unembedding). A common scale factor applied
to both the delta and the context it rides on **cancels** at the next
normalization. What does *not* cancel is dilution: block N scales everything by
s<1, then block N+1 adds its own branch output at unscaled magnitude, so a static
injected delta loses share against the model's continuously re-written content.
That mechanism is real, and it is what §E means by "a static injected delta
decays without re-injection." But its magnitude is **not** the product in the
table above, and it has never been measured.

**And the measured collapse data already contradicts the naive model.** Expressed
as surviving magnitude at collapse onset: hs34 collapses (0.778) at surviving
9.6, hs38 (0.400) at 18.9, hs40 (0.250) at 23.5, hs42 (0.100) at 28.1. If
survival were the whole story these would coincide; instead the *shallowest*
site collapses at the *least* surviving magnitude, i.e. 3x more readily than
hs42. Attenuation is a live candidate, not a settled account.

What survives as genuine support: among the three non-terminal gemma sites, the
**only** one showing any nonzero tighten anywhere (hs40, 0.125 on 3/8 rungs) is
the one with the highest survival (0.360). That is a monotone trend on n=3.
It is suggestive and nothing more.

**Finding (4) confirmed, on absolute doses, without needing the norm argument.**
gemma's median anchor norm at hs42 is 281.34 against 117-126 at hs34/38/40 —
a 2.23-2.38x inflation, so every hs42 ratio buys 2.3x the absolute dose. In
absolute terms hs42 first collapses at 28.13 (rate 0.100) and substantially at
43.05 (0.900), against 66.59 / 69.53 / 65.13 for hs34/38/40. That is ~1.5-2.4x,
not 3.6x. **The lead's conclusion holds: "hs42 collapses almost immediately" is
largely a ladder artifact and must not be cited as a terminal-layer phenomenon.**

One inconsistency to flag, which does not change anything: round-1 point 3
established hs42's collapse *onset* is r0=0.100 (rate 0.100), and round-2 point 4
quotes the comparable-terms onset as ~0.36, which corresponds to rescaling
r1=0.153 (rate 0.900). Both are defensible — first-nonzero vs first-substantial —
but the write-up should pick one and say which.

**Findings (5) and (6) I did not re-derive** and have taken as stated. (5) removes
a rival and, as the lead says, is not positive evidence for anything; the memo
treats the field as "no mechanism currently favored." (6) is the gate — see §2.

**A defect in my own draft, found while checking the above.** The cached gemma
extraction `analysis/gemma4-e4b/anchor_extract.safetensors` contains **only**
hs34, hs38, hs40, hs42 (3,224 keys, verified). The amendment's G0-ALIN Part 1 —
its one "free, CPU-only, pre-sign" deliverable, specified to record `A_lin` at
hs22, hs23, hs24, hs34, hs38, hs42 — **cannot be computed**, because three of the
six sites have no cached activations. It is a GPU extraction, not a CPU sweep.
Both options therefore require a fresh extraction, which means extraction cost is
not a differentiator between them.

---

## 2. The gate that precedes both options

**Finding (6) — gemma's ungated logit lens — subsumes this entire decision.**
The reconstructed output path fails to decode gemma's own recorded next token
(teacher-forcing top-1 2.9% vs llama 47.9%; true token rank 6227 at the anchor),
with ten alternative explanations ruled out by direct measurement, while cached
activations are faithful (cos 0.9998) and the KU readout gate reproduces its
committed AUC exactly.

If the live `.logits` are also wrong, then every gemma *behavioral* number in the
program — the 0/176, the collapse ladders, the usability determinations — is
measuring a broken output path, and:

- Option A is void: it contrasts two behavioral readouts from that path.
- Option B is void: it is a behavioral ladder on that same path.
- What is *not* void: the hidden states, the KU readout gate AUCs, and the
  `layer_scalar` values, all of which are independently verified.

So: **launch nothing until that check reports.** If it fails, the next work item
is neither A nor B — it is repairing or re-deriving gemma's generation path, and
the parent experiment's gemma arm needs a disposition change.

Everything below is conditional on (6) clearing.

---

## 3. Option A — run the KV-seam contrast as designed

**What it can conclude.** It is the only design on the table that manipulates an
architectural variable *causally* rather than varying a site and arguing about
confounds. If A2 clears both gates while A1 does not, with `|ΔA_lin| <= 0.05`,
that is a clean causal demonstration that the KV-sharing pathway gates
actuation at hs38 — a real mechanism result, promotable to an exploratory lead.

**What it cannot conclude, and this is now the decisive objection.** A1 and A2
sit at **hs38, rd 0.905**. No family in this program has ever had a usable dose
above rd 0.607, and llama's own tighten at rd 0.905-equivalent depth is 0.125.
**A negative A2 at hs38 is the expected observation from depth alone.** It would
carry essentially no evidence against KV quarantine, which means the primary
contrast has one informative outcome (positive A2) with a low prior and one
uninformative outcome (negative A2) with a high prior. That is a bad bet at any
GPU cost.

The arms at defensible depth — A3 (hs22, rd 0.524) and A5 (hs24, rd 0.571) —
**straddle the cross-family usable band and the KV seam simultaneously**, which
is genuinely the right place to look. But they are precisely the arms I concluded
in the last revision **cannot discriminate** the competing accounts, because two
blocks of computation move linear accessibility as well as donor reachability.
Findings (2) and (3) now add two more strikes: hs22/hs23 are the chokepoint
blocks, and the atlas flags hs21/25/26 as control-confounded on the read axis,
which bears on fitting a KU readout gate there.

So Option A's structure is inverted: **its informative-in-principle contrast is
at a depth where nothing actuates, and its right-depth arms are uninformative
by construction.**

**Vulnerable to:** (1) severely — the primary sites are outside the actuating
band. (2) severely — hs38 was read-selected and the shallow band was never
tested. (3) moderately — A3 writes at the chokepoint. (4) not really; the hs42
correction is carried and hs42 is not an Option A site. (5) adversely — losing
H-cryst as a rival does not promote KV quarantine, so A's headline
"discriminating" outcome now discriminates against a weaker field. (6) fatally,
as does everything.

**GPU cost.** The largest on the table: 6 dosed arms plus C0/C1, each an 8-rung
FIT ladder, plus held-out passes for any arm with a usable dose, plus fresh
extractions at hs22/23/24 in both conditions and at hs38 under sharing-OFF, plus
per-site per-condition direction refits. It also requires **new instrument code
that does not exist**: `kv_seam_patch.py` integration, the `--kv-sharing` flag
threaded through four scripts, the both-arms cache routing, `preflight_kv_seam.py`,
`rollup.py`. I have no measured timings — that is the outstanding
`instrument.persistence` item that blocks `bin/exp sign` — so I will not invent a
wall-clock number. Structurally it is roughly **4-6x Option B**, and it is the
only option with unwritten instrument code on the critical path.

**What a null would license.** Very little. "A2 and A3 both failed" would be
written up as falsifying KV quarantine, but at hs38 that falsification is
confounded with depth, and at hs22 it is confounded with the chokepoint and with
linear accessibility. A null here would most likely be **re-litigated rather than
believed**, which is the worst outcome per GPU-hour.

---

## 4. Option B — shallow-site gemma FIT ladder first

**As briefed:** rd ~0.35-0.60, roughly hs15-hs25, n=8, stock model, matching
where llama and mistral actuate; build the KV-seam experiment only if the null
survives correct site selection.

**What it can conclude.** If gemma actuates at a shallow site, the 0/176 null is
explained by site selection, and KV quarantine, the crystallization gap, and the
`layer_scalar` attenuation account all become **unnecessary** — the parent's
gemma arm gets a corrected disposition and the program gets a working gemma write
site, which is worth more than any of the three mechanism stories. If gemma does
*not* actuate at a properly-chosen shallow site, the null becomes far more robust
and a mechanism experiment finally has a premise worth spending on.

**What it cannot conclude.** It is observational site variation. It can never
establish *why* gemma fails where it fails — a shallow success tells you the deep
null was a site artifact but not what makes gemma's deep band inert; a shallow
null tells you the model is inert but not which of the surviving mechanisms is
responsible. Option B buys a **premise**, not a mechanism.

**The flaw in Option B exactly as briefed, and the fix.** hs15-hs25 sits almost
entirely **upstream of the block-22/23 chokepoint**. If the dilution mechanism has
any force at all, a null there is confounded by finding (3) — the same class of
ambiguity Option B was meant to escape. The fix costs one or two extra sites:

> **B′ — straddle the chokepoint.** Run the ladder at a shallow set **and** a
> just-downstream set: e.g. **hs15, hs18** (rd 0.357, 0.429 — inside the atlas's
> clean-control hs14-18 band, matching mistral's usable sites) **and hs26, hs28**
> (rd 0.619, 0.667 — downstream of blocks 22/23, survival 7.5e-3 and 1.5e-2,
> i.e. 270x and 540x better than hs15). Four sites, one condition, one extraction.

B′ turns finding (3) from an uncontrolled confound into a **measured contrast**:

| result | reading |
|---|---|
| shallow actuates | site selection was the whole story; the chokepoint is irrelevant to actuation; mechanism experiments unnecessary |
| shallow nulls, just-downstream actuates | the chokepoint is implicated; the attenuation account is promoted and the KV-seam design is superseded |
| both actuate | gemma actuates broadly below rd ~0.67; the deep null is a depth effect, full stop |
| both null | the gemma null is real and site-independent inside the cross-family band. **This is the premise Option A always needed and never had.** |

Note that even the all-null row is a *usable* result, which is not true of any
Option A outcome. That asymmetry is the core of my recommendation.

**Vulnerable to:** (3) — mitigated but not eliminated by B′, since the dilution
magnitude is still unmeasured. (2) partially — hs26 is adjacent to the hs25/26
layers the atlas flags as control-confounded on the read axis, which bears on
fitting the KU readout gate there; hs28 is included partly to hedge this, and the
per-site gate AUC must be reported and inspected before any per-site verdict.
(6) fatally, like everything. It is **not** vulnerable to (1) — it is the direct
test of (1). It is not vulnerable to (4), which concerns hs42 only. It is not
vulnerable to (5).

**GPU cost.** The smallest real option: one extraction at 4 sites, 4 direction
fits, 4 eight-rung FIT ladders plus C0, on the stock model. **No patch, no cache
builder, no `--kv-sharing` flag, no OFF-condition refits, no C1 precondition
control, no new instrument code** — it is the parent's pipeline pointed at
different `hs` indices. Roughly **1/4 to 1/5 of Option A**, and it can be
smoke-tested against the parent's existing runlog conventions.

**What a null would license.** "Gemma does not actuate at four sites spanning
rd 0.357-0.667, including the atlas's own clean-control shallow band and sites on
both sides of the `layer_scalar` chokepoint" — a materially stronger null than
anything on record, and gemma's first held-out-eligible evidence at a defensible
depth. It would **not** license "gemma cannot be actuated": four sites, n=8
confab rows per FIT cell, one ladder shape, one direction-fit method, one
injection law (`erase_write`, `anchor_onward`). It would also not identify a
mechanism — which is the honest cost of recommending it.

---

## 5. Recommendation

**Gate on (6). Then run B′ (Option B, straddling the chokepoint). Do not build
Option A next.**

Reasoning, including the part that contradicts the amendment I spent this session
building:

1. **Option A's premise has weakened to the point of not supporting it.** The
   amendment's motivating observation — gemma is write-verified inert where
   llama actuates — is not what the data says once relative depth is held up.
   Mistral reproduces gemma's flat-zero signature at rd 0.594 and 0.938 with no
   KV sharing anywhere in the model. The observation that needs explaining is
   "no family actuates deep," and gemma has only ever been tested deep.
2. **Every mechanism story on the table, including mine, is currently explaining
   an artifact of site selection.** KV quarantine, the crystallization gap, and
   `layer_scalar` attenuation are three accounts of a null that may not require
   any of them. Spending the most expensive experiment on adjudicating between
   them, before establishing that there is something to adjudicate, is the wrong
   order.
3. **Option A cannot be rescued by moving its sites.** One could imagine
   re-siting the KV contrast into the actuating band — and the geometry is
   genuinely inviting, since the seam (hs24) sits at rd 0.571, right at the top
   edge of the cross-family usable band, with hs22 below it and hs25-26 above.
   But that redesign is *strictly downstream of B′*: it is only worth building
   if B′ shows gemma actuates somewhere at all, and B′ is exactly the measurement
   that would tell you which sites to use. Running A first spends the large
   budget to learn what the small one determines.
4. **B′ has no uninformative outcome.** All four cells of its result table change
   what the program does next. Option A has one informative outcome with a low
   prior.
5. **The asymmetry in what each null buys.** An Option A null gets re-litigated;
   a B′ null becomes the registered premise that makes a mechanism experiment
   worth signing. If the user's goal is eventually to run the KV-seam contrast,
   **B′ is the fastest path to a version of it that anyone will believe.**

**If the user prefers Option A anyway**, the minimum I would ask for before
signing: move the primary off hs38. A causal KV manipulation at rd 0.905 tests
the mechanism in a band where the phenomenon does not occur in any family.

**What I am not recommending**, for the record: I am not recommending a
dose-compensated ladder to counteract `layer_scalar` (the naive survival product
overstates the attenuation, and the measured collapse data contradicts it in the
wrong direction — see §1); and I am not recommending a re-injection /
anchored-at-every-block arm yet, though §E flags it as an open GPU question. Both
are downstream of B′ establishing whether there is anything to compensate for.

---

## Appendix A — what a decision needs that nobody has yet

Cheap, and all of it currently missing:

1. **Measured wall-clock timings** for the parent's pipeline stages. Neither
   option's GPU cost can be stated in hours; I have given structural ratios only.
   This is also the outstanding `instrument.persistence` item that blocks
   `bin/exp sign` on any design.
2. **Gemma's median anchor norms at shallow sites.** Unknown — the cached
   extraction has only hs34/38/40/42, so the norm-scaled ladder's denominator at
   hs15-hs28 cannot be predicted. Falls out free of B′'s extraction.
3. **The dilution magnitude**, i.e. how much share a static injected delta
   actually loses per block against the model's re-writing, as opposed to the
   naive `layer_scalar` product. Requires activations at multiple depths with and
   without an injected delta — free once B′ has run, not computable now.
4. **The full 42-value `layer_scalar` list as a citable artifact.** I reproduced
   it and it reconciles exactly with §E's four published rows; §E says the full
   list is "in the transcript," which is not a citable source. It should be
   written to a JSON alongside the forensics report.

## Appendix B — state of prior work, for recovery if Option A is chosen

`AMENDMENT.md` is left as the stop order found it: fully revised through both
review rounds, **unsigned, uncommitted**, `bin/exp validate` OK (warnings only —
the persistence declarations of Appendix A item 1). Nothing has been reverted.

**Round-1 six points — all six landed** before the stop order
(`NOTEBOOK.md` entry 1):

| # | point | state |
|---|---|---|
| 1 | sharing-OFF toggle would crash; crash section | landed |
| 2 | forensics observation 4 (terminal-layer collapse) struck | landed |
| 3 | below-seam site selected by `A_lin`, not the eff_dim peak | landed — but see the G0-ALIN defect in §1: it is not CPU-computable |
| 4 | exclusivity withdrawn; "Standing of this hypothesis" section | landed |
| 5 | "Competing explanations" section | landed, **with its rationale since corrected** — the claim that A1-vs-A2 "holds the site fixed and therefore holds all of them fixed" is false and is marked as corrected in place |
| 6 | G2 vacuity addressed, with the gemma counter-finding | landed — now carries the FIT-scale caveat from round-2 point 5 |

**Round-2 five points — all five landed** (`NOTEBOOK.md` entry 2):

| # | point | state |
|---|---|---|
| 1 | cache builder wired in as `Cache(layers=[...])`, both-arms contract | landed in `kv_seam_patch.py`, `gates.yaml`, `cell.yaml` |
| 2 | motivation cites the measured 0/176 and the llama positive control | landed |
| 3 | hs42 onset r0=0.100 correction carried | landed — **now superseded** by finding (4): the whole hs42 collapse reading is a ladder artifact |
| 4 | the discrimination problem | landed: four-outcome table, `A_lin`-under-both-conditions as G0-ALIN Part 2, A3-A6 demoted to descriptive, self-correction recorded |
| 5 | gemma has no held-out run | landed as Threats (h) plus the G2 vacuity caveat |

**Reusable regardless of the decision:** `kv_seam_patch.py` (architecture
verification, the working `Cache(layers=[...])` builder, projection-call
counting, donor-key capture) and `kv_seam_preflight.py` (4/4 PASS,
`gemma-arch-research`) are correct instrument work that any future gemma KV
experiment inherits. The four-outcome discrimination table and the depth/`A_lin`
confound analysis transfer to a re-sited KV design unchanged.

**Superseded by these findings if Option A is revived:** the site choice for
A1/A2 (hs38, rd 0.905); the framing of the parent null as gemma-specific
(mistral reproduces it with no KV sharing); the hs42 collapse interpretation; and
the "Standing of this hypothesis" candidate list, which now needs
`layer_scalar` dilution added and site-selection artifact named as the leading
account.
