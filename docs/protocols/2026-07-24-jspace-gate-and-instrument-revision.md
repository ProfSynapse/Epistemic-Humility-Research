# Protocol Revision — J-space gate adjudication and shared-instrument defects

**Tier:** 1 (signed protocol revision — touches gate definitions, the roll-up
interpretation rule, and a shared measurement instrument)
**Version:** v1.1
**Date drafted:** 2026-07-24
**Status:** DRAFT — **NOT SIGNABLE.** Blocked on the re-scoped Defect 3 audit
(clause 3), which peer review found incomplete and which is in progress. Nothing
in this document is in force until signed, and it must not be signed while that
clause is open.
**Occasioned by:** resolution of `j-space-cross-family-layer-contrast`
(verdict INCONCLUSIVE, signed 2026-07-24)

## Why Tier 1

Three defects were found during a single resolve pass. Each of them changes how
results are *adjudicated and labeled*, not merely how a cell is run:

- Defect 1 invalidates a PRIMARY gate's verdicts across this and prior
  experiments.
- Defect 2 is a contradiction between two registered documents about what
  verdict the headline question can take.
- Defect 3 invalidates the site-selection basis of one family and affects a
  shared instrument used by other experiments.

Per `amendment-vs-lab-notebook.md` decision question 1 — "does it touch the
governed headline surface — the hypotheses/falsifiers, metric definitions, or
how results are labeled and claimed?" — all three route to Tier 1.

They are bundled into one revision because they were found together, they all
bear on the same adjudication, and Defect 3's remedy is a precondition for
re-running the family that Defect 2's rule requires.

---

## Defect 1 — G2 is structurally vacuous (PASSes stand; non-diagnostic)

### The defect

G2 as registered caps mid-band known-correct cost:
`not_well_formed_correct <= 0.05`, Wilson upper `< 0.10`, measured on
known-correct-answered rows.

But **dosing occurs only when the KU readout gate fires**, and the gate
correctly does not fire on known-correct rows. Measured dosed known-correct
denominators:

| family | site | known-correct rows | of which DOSED |
|---|---|---:|---:|
| llama-3.2-3b | hs17 | 334 | **0** |
| mistral-7b-v03 | hs15 | 382 | **0** |
| mistral-7b-v03 | hs12 | 382 | **1** |

Both numerator and denominator are therefore vacuous with respect to the
intervention. The failure events G2 counts come from rows that were **never
dosed** — they are baseline model errors, not costs of the write.

This was confirmed independently: `successes = 2` is **identical** at mistral
hs12 and hs15 despite different layers and different doses. A metric that does
not move when the intervention changes is not measuring the intervention.

### Relationship to the standing rule (this defect was already known)

`.skills/experiment-runner/reference/gate-diagnosticity.md` already documents
this failure mode in full, including the counterintuitive law that such a gate
gains diagnostic power as the readout gate gets *worse*, and the arithmetic-floor
method below. **The defect is not a new discovery; the failure was not reading
the reference before adjudicating.** That reference also fixes the disposition
of already-registered results, and this revision conforms to it rather than
overriding it.

### The revision

1. **Registered G2 PASSes STAND exactly as registered.** Per
   `gate-diagnosticity.md`: *"a locked gate's PASS stands exactly as registered
   even when it is later shown to be non-diagnostic; that caveat travels forward
   with the result, it does not reopen the verdict."* An earlier draft of this
   revision proposed retroactively re-labelling every G2 PASS as
   NOT-ADJUDICABLE. **That was wrong and is withdrawn** — retroactive
   re-labelling of a locked gate is itself a form of goalpost movement, in the
   direction of severity rather than leniency, but goalpost movement all the
   same.
2. **Instead, a non-diagnosticity caveat travels forward with each affected
   result.** Every reported G2 PASS must carry, in the same place the verdict is
   reported, the fired fraction of its denominator. For this experiment:
   llama-3.2-3b hs17 → 0/334 dosed; mistral-7b-v03 hs15 → 0/382 dosed. A PASS at
   0 dosed rows is evidence about the population's baseline malformedness only,
   and must never be cited as evidence that the write is selective or safe.
3. **Reporting requirement (applies immediately, retroactively, to reporting
   only — not to verdicts).** Fire rate MUST be reported as a companion number
   to every cost/harm gate's point estimate and CI, per the reference's review
   checklist. This changes what is *printed*, not what any gate *decided*.

   "MUST", not "should": a caveat that travels only by good intention does not
   travel. The following prior G2 PASSes are affected and MUST carry the
   companion fire rate wherever their verdict is reported:

   | experiment | family | site | G2 as reported | dosed fraction of denominator |
   |---|---|---|---|---|
   | `j-space-cross-family-layer-contrast` | llama-3.2-3b | hs17 | PASS (4/334 = 0.0120) | **0/334** |
   | `j-space-cross-family-layer-contrast` | mistral-7b-v03 | hs15 | PASS (2/382 = 0.0052) | **0/382** |

   This enumeration is the complete set known at drafting **for this
   experiment**. Any G2-equivalent cost gate in another experiment whose dosed
   denominator is 0 falls under the same requirement; discovering one is a
   reporting correction, not a new revision.
4. **G2 is superseded for FUTURE pre-registrations by two separately-adjudicable
   gates.** This is a forward-looking design change, per the reference's "Design
   prescription for a FUTURE non-vacuous gate":

   - **G2a — gate selectivity (no new measurement required).** On known-correct
     rows, the fraction on which the KU readout gate FIRES. Cap: `<= 0.05`,
     Wilson upper `< 0.10`. Already measured and strongly passing (0/334,
     0/382). **G2a is not a rename of the old G2 — it is a different
     quantity.** The old G2 measured `not_well_formed_correct`, the baseline
     malformedness of an undosed population; G2a measures the readout gate's
     FIRE RATE on known-correct rows. The old gate was not approximating this
     one; it was measuring a baseline property because its denominator was
     never dosed. G2a replaces it, and does not inherit its results.
   - **G2b — write selectivity under forced dose (new measurement).** A
     stratified sample of known-correct rows is dosed **unconditionally**,
     bypassing the gate, at the same site and dose selected for G1. Metric:
     `not_well_formed_correct` on those forced-dosed rows. Cap: `<= 0.05`,
     Wilson upper `< 0.10`.

   G2a asks "does the readout correctly decline to fire here?" G2b asks "and if
   it *had* fired, how much damage would the write do?" Only G2b bounds the harm
   of the write itself, which is what the original G2 was intended to bound.

5. **Minimum-N adjudicability floor for G2b, computed not assumed.** Per the
   reference's arithmetic-floor method (smallest N for which a 0-success draw
   clears the registered Wilson-upper cap): for cap `Wilson-upper < 0.10` the
   floor is **N = 35** (0/35 → upper 0.0989; at N = 34 a perfect draw still
   gives 0.1015 and fails). Below 35 forced-dosed rows, G2b is
   **NOT-ADJUDICABLE** — a miss there is an artifact of N, not evidence about
   the write. Companion figures at larger N, for interpreting what the cap can
   actually catch: at N = 100 the cap tolerates up to 4 failures; at N = 334, 16;
   at N = 382, 19.

6. **NOT-ADJUDICABLE is a registered disposition, distinct from PASS and FAIL.**
   Roll-up code must count it as "did not clear the primary" for success-counting
   while reporting it separately from FAIL, so a vacuous non-result is never
   indistinguishable from a real one in the scoreboard.

7. **For future pre-registrations the PRIMARY becomes G1 AND G2a AND G2b.**
   This does **not** retroactively alter the primary for
   `j-space-cross-family-layer-contrast`, whose registered primary remains
   G1 AND G2 and whose INCONCLUSIVE verdict is unaffected (it turns on the
   family-count floor, not on G2).

### Scope

Forward-looking for gate *definitions*; immediate for *reporting* (fire-rate
companion numbers). **No prior verdict is reopened.** Prior Outcome sections
MUST be annotated with the fire-rate caveat where a G2 PASS was reported —
see the enumeration in clause 3 — as an addition to the record rather than a
change to it.

---

## Defect 2 — the success/falsifier rule is stated inconsistently

### The defect

Two registered documents for the same experiment state different rules:

- `experiments/j-space-cross-family-layer-contrast/AMENDMENT.md` (roll-up
  section) contains an INCONCLUSIVE floor: *"if fewer than 3 families ran at
  all, the experiment is INCONCLUSIVE, not a pass."*
- `experiments/j-space-cross-family-layer-contrast/experiment.yaml`
  `falsifier:` contains **no floor**: *"If at most 1 of the families that run
  past G0 clears both primary gates, mid-band actuation is Qwen-lineage-specific
  or an artifact - FALSIFIED. If exactly 2 clear both, the result is MIXED."*

At the observed `n_run = 2`, `n_passed = 1`, **both clauses fire**, yielding
INCONCLUSIVE and FALSIFIED respectively. The registered protocol therefore
under-determined its own verdict.

### The revision

1. **The INCONCLUSIVE floor is canonical, because the registered instrument
   implements it.** `cross_family_rollup.py` is a registered instrument module
   (`experiment.yaml:46`, sha256-pinned at `:118`) and it hard-codes
   `if n_ran < 3: verdict = "inconclusive"` (`:71-72`, `:100`), implementing the
   floor that `AMENDMENT.md` already stated. INCONCLUSIVE is therefore what the
   registered, hash-pinned instrument *computes* — it is not a reading this
   revision selects between two prose options. The floor is evaluated **before**
   the falsifier test, as the instrument evaluates it.

   Supporting rationale, not the basis: a denominator too small to establish
   "generalizes" is equally too small to establish "does not generalize."
2. **`experiment.yaml`'s `falsifier:` field is an incomplete transcription and
   must be corrected to match.** It omits a floor that both the AMENDMENT and
   the pinned instrument carry. Until corrected it is superseded by this
   revision, not by silent edit.
3. **No general precedence rule is minted here.** An earlier draft of this
   revision introduced a rule that "where prose conflicts, the more conservative
   reading governs." **That is withdrawn.** It was not needed — the hash-pinned
   instrument settles this case on its own — and minting a general adjudication
   principle as a side effect of adjudicating one experiment is precisely the
   pattern that review exists to catch. `operator-discipline.md` contains no
   such rule, and if one is wanted it must be proposed there on its own and
   reviewed on its own merits.

   What *is* registered here, narrowly: **where a registered instrument and
   registered prose conflict, the instrument governs**, because the instrument
   is what actually computed the result and it is hash-pinned. And the conflict
   must be recorded in the Outcome, never resolved silently.
4. **No verdict may be announced from a remembered or paraphrased rule.** The
   adjudicating rule must be read from the registered document, and the
   registered instrument must be executed, before any verdict is stated. This
   revision exists in part because that discipline was violated: FALSIFIED was
   announced from memory before `cross_family_rollup.py` was run, and the script
   returned INCONCLUSIVE.

---

## Defect 3 — `use_cache=False` corrupts KV-sharing models in the shared j-lens

### The defect

`experiments/j-space-localization-qwen3-4b/jlens.py:195`:

```python
out = model(**enc, output_hidden_states=True, use_cache=False)
```

On models with cross-layer KV sharing this is not a neutral flag. On
gemma-4-E4B (`first_kv_shared_layer_idx = 24`) blocks 24–41 read donor K/V from
blocks 22/23 **through the cache object**; disabling the cache starves them.
Measured: hs00–hs24 bit-identical to a correct run; hs25 collapses to cos 0.732
and decays to 0.075 by hs42.

**Mechanism confirmed in source**, not inferred from config keys:
`transformers/models/gemma4/modeling_gemma4.py:1197-1199` — shared layers read
K/V from `past_key_values.shared_layers`; with `use_cache=False` the cache is
`None` (`:1571`), so donor K/V is never read. Boundary 42 − 18 = 24, and
block 24's output is hs25 — which is exactly where the collapse begins.

`jlens.py` is imported unmodified by `jlens_profile.py` and is marked
do-NOT-modify/shared, so the defect propagates to every consumer.

**Consequence for `j-space-cross-family-layer-contrast`:** gemma4-e4b's
`layer_profile.json` swept hs `[1, 6, 10, 15, 20, 24, 29, 34, 38, 42]` — of
which **hs29, 34, 38, 42 lie in the corrupt region**. Band selection recorded
`effective_dim_peak_hs: 38` and `midband_candidates_hs: [34, 38, 42]`. The
"peak" at hs38 (eff-dim 0.005783) is the maximum of the sweep and sits in
corrupt data; the four clean layers span only 0.004607–0.005229, and hs42
collapses to 0.001048 — the corruption signature. **Gemma's registered
mid-band sites were selected from corrupt activations**, which also explains
why all three sit at relative depth 0.81–1.00, inside the measured dead band,
and why the write null was 0/176.

Families without cross-layer KV sharing (llama, mistral, qwen) are unaffected.
Evidence, in descending order of strength:

- **Qwen3.5-4B, from source — decisive.** `modeling_qwen3_5.py:433-435` gates
  use of cached state on `seq_len == 1`, i.e. incremental decode only. In a full
  prefill — which is what every capture and extraction path here performs —
  `use_precomputed_states` is False regardless of `use_cache`; the cache is
  written but never read. Prefill hidden states are therefore identical under
  both settings by construction. No `shared_layers` or `num_kv_shared` symbol
  exists anywhere in the `qwen3_5` module or config.

  This matters more than the absence of a config key. Qwen3.5-4B is a
  gated-delta **linear-attention hybrid** whose `linear_attention` layers carry
  recurrent state in the cache object — the same *class* of hazard as KV
  sharing, even though it is not KV sharing. "No sharing keys in `config.json`"
  would not have ruled it out. The source does.
- **Llama-3.2-3B, measured.** A/B through the exact `jlens` call pattern, all
  29 hidden states × 4 prompts: worst cosine 0.999999702, max absolute
  elementwise difference 0.000e+00, with a vacuity guard asserting distinct
  storage and non-degenerate activations.
- **Mistral-7B-v0.3**: no cross-layer KV sharing and no linear-attention
  state; unaffected by the same reasoning as llama.

An earlier draft of this section claimed "verified min cos 1.000000 between
`use_cache` settings on the extraction path" for all three families. **That
claim is withdrawn**: no artifact was located showing that A/B was actually run
on the Qwen3.5-4B checkpoint specifically, as opposed to qwen3-4b. The source
argument above is stronger and does not depend on it.

### The revision

1. **`jlens.py:195` is corrected to `use_cache=True`.** This is authorized as
   instrument repair notwithstanding the do-NOT-modify marking, which exists to
   prevent silent divergence between consumers, not to freeze a known defect.
2. **The correction must be verified as a no-op for non-KV-sharing families
   before the file is changed**, by comparing hidden states under both settings
   on at least one non-sharing family and requiring bit-identity (or cos
   1.000000). If it is not a no-op, this clause does not authorize the edit and
   the revision returns for re-signature.
3. **Consumers of the corrupted read path: AUDIT INCOMPLETE — BLOCKING.**

   > **RETRACTION.** The v1.0 draft of this clause stated "AUDITED 2026-07-24,
   > blast radius is gemma-4-E4B only… the audit is complete and this clause is
   > discharged, not deferred," and concluded that **no prior resolved
   > experiment is invalidated**. That conclusion is **withdrawn as unsupported,
   > and is affirmatively known to be false as stated.** Peer review found the
   > audit's enumeration method unsound and the re-scoped audit is in progress.
   > This revision is **not signable** until it completes.

   **Why the original audit was unsound.** It enumerated consumers by artifact
   filename (`layer_profile.json`, 4 found, all inside this experiment) and by
   copies of `jlens` (2 found). Neither is the axis along which the defect
   propagates. The defect attaches to any **activation-capture path that runs a
   `use_cache=False` forward on a KV-sharing checkpoint**, whatever the
   resulting artifact is called. A capture that writes a "panel" or
   `capture_manifest` instead of a `layer_profile.json` is invisible to a
   filename search while being equally corrupt.

   This is the same error shape as Defect 1 itself: choosing a denominator
   because it was easy to enumerate rather than because it defined the exposed
   population.

   **Known missed consumer.** `synaptic-tuner/tuner/batch/engines/hf_batched.py:466`
   (`_capture_chunk`) performs the batched capture forward with
   `use_cache=False`. (`:258` is `use_cache=True` — a different function, the
   generation path; the two must not be conflated.)
   `experiments/gemma-4-e4b-family-atlas/capture_family_atlas_cell.py` routes
   through `synaptic-tuner/tuner.py` to that engine, and its layer default is
   `range(n_hidden_states)` — every index `0..num_hidden_layers` inclusive.
   `gemma-4-e4b-family-atlas` is **status `resolved`, `registered: true`**.

   Cross-layer KV sharing per checkpoint (config plus source, see above) is
   unchanged and stands:

   | model | n_layers | KV sharing | affected |
   |---|---:|---|:--:|
   | google/gemma-4-E4B-it | 42 | `num_kv_shared_layers: 18` (⇒ boundary at 24) | **YES** |
   | Qwen/Qwen3.5-4B | 32 | none; prefill is cache-independent (`modeling_qwen3_5.py:433-435`) | no |
   | meta-llama/Llama-3.2-3B-Instruct | 28 | none | no |
   | mistralai/Mistral-7B-Instruct-v0.3 | 32 | none | no |

   **What still stands.** `qwen35-4b-midband-doubt-snap` and
   `qwen35-4b-midband-heldout` ran on Qwen3.5-4B, whose prefill is
   cache-independent in source, so their site selection — including the **hs20
   promotion** — is unaffected. Nothing in the retraction touches it.

   **What must be established before signature.** A disposition — affected /
   clean / indeterminate, with file:line evidence and the specific hidden-state
   indices each claim rests on — for every experiment that captures gemma-4-E4B
   activations, enumerated **by capture path, not by model name or artifact
   name**. Seven experiments reference gemma-4-E4B (`gemma-4-e4b-family-atlas`;
   `family-atlas-surface-{residualization,diversity,matched-json-completion,matched-pool,matched-vllm}-control`;
   `gemma4-e4b-kv-seam-quarantine`), six of them resolved or null-result and all
   registered. An experiment is affected only if the checkpoint shares KV **and**
   capture used `use_cache=False` **and** the indices its claims rest on include
   hs25 or above — hs00–hs24 are bit-identical, so a gemma experiment confined to
   hs≤24 is clean. Indeterminate must be recorded as indeterminate and never
   rounded to clean.

   Two `jlens` copies carry the identical defect and are still to be corrected:
   `j-space-localization-qwen3-4b/jlens.py:195` and
   `qwen35-4b-midband-doubt-snap/jlens_qwen35.py:127`. The second is hygiene —
   it would silently corrupt any future KV-sharing model pointed at it — but no
   existing result is known to depend on it.

   The `hf_batched.py:466` fix is **not** authorized by this clause. It is a
   submodule shared beyond this project; correcting it requires its own
   assessment of who else depends on the current behaviour.
4. **gemma4-e4b's band selection is voided and must be re-derived** from a
   corrected profile run. `band_selection.status` reverts `resolved` →
   `not_yet_run`; `midband_candidates_hs`, `effective_dim_peak_hs`, and
   `late_reference_hs` are cleared and re-derived by the same registered method
   applied to correct data.

   **The depth sweep is pinned here, in this document, before the re-run.**
   The gemma re-derivation MUST profile **every hidden state hs0…hs42
   inclusive** — the full stack, no subsampling. Rationale: `select_band` is a
   deterministic argmax over `eff_dim_frac` plus adjacent layers, so given a
   fixed profile there is **zero operator latitude** in which site wins. But the
   *sweep* (`n_points` / `--layers`) is a free parameter, and changing which
   depths are evaluated changes which index can win the argmax. Leaving it
   unpinned would leave a live steering vector — especially now, since the
   corrected read profile has **already been seen**. Requiring the full stack
   removes the parameter entirely rather than fixing it at some chosen value.

   **This is repair, not goalpost movement — with the timing stated plainly.**
   The distinction: goalpost movement is re-selecting sites *because a result
   was unfavourable*; this is re-selecting because the *instrument that chose
   them was broken*. The mechanism is outcome-independent — it is a fact about
   `use_cache` and KV sharing that holds regardless of what any experiment
   found, confirmed in `modeling_gemma4.py`.

   **However, the discovery was outcome-triggered**, and this revision does not
   gloss that: the `use_cache` audit was prompted by an unexplained gemma null
   (0/176), because nobody audits an instrument that appears to be working. An
   outcome-triggered discovery of an outcome-independent defect is still repair
   — but the honest statement is "we went looking because the result was
   strange," not "we established this independently of any outcome." What makes
   it repair is the mechanism's outcome-independence and the determinism of
   `select_band` under a pinned full-stack sweep, not the circumstances of its
   discovery.

   The prior gemma null (0/176) is accordingly **uninterpretable, not
   negative**, and must not be cited as evidence of a gemma write failure.
5. **The re-derived sites are binding once written**, before any dosed run at
   them. The selection must be committed and the family file updated prior to
   running, so the sites cannot be tuned against the result. With the sweep
   pinned in clause 4 and `select_band` deterministic, the site is fully
   determined by the corrected profile — there is nothing left to choose.

### Known limitation recorded at sign

Gemma's corrected read profile is **saturated** — held-out KU-direction AUC
`>= 0.977` from hs5 through hs42, peaking hs18 (relative depth 0.429) at 0.9999.
Read-AUC therefore supplies **no site-selection signal** for this family, and
eff-dim spans a narrow range on clean layers. Site selection for gemma may be
weakly determined even after repair. This must be stated in the family's Outcome
rather than presented as a confident choice.

One unexplained observation, recorded so it is not lost: in the *corrected*
gemma data `cos(hs23, hs24) = 0.012484` — near-orthogonal, at the donor-block
boundary. Read AUC shows no disruption across it (hs23 0.9998, hs24 0.9980), so
it is not destructive, but it is uncharacterized.

---

## Changelog

| Version | Date | Change |
|---|---|---|
| v1.0 | 2026-07-24 | Initial revision. Retires G2 for future pre-registrations and introduces G2a/G2b; registers NOT-ADJUDICABLE as a disposition; makes the INCONCLUSIVE floor canonical; authorizes the `jlens.py` `use_cache` repair and voids gemma4-e4b band selection. |
| v1.1 | 2026-07-24 | Revised after independent adversarial peer review. **Retracts** the v1.0 claim that the Defect 3 audit was complete and that no prior resolved experiment was affected — the audit enumerated by artifact filename rather than by capture path and missed `hf_batched.py:466`, through which the resolved, registered `gemma-4-e4b-family-atlas` captured gemma-4-E4B. Document marked NOT SIGNABLE pending the re-scoped audit. **Withdraws** the invented "more conservative reading governs" precedence rule and re-anchors Defect 2 on the hash-pinned `cross_family_rollup.py`. Upgrades the gemma and Qwen3.5 mechanism claims from config keys to source citations, and **withdraws** the unsupported "min cos 1.000000 on the extraction path" claim. Fire-rate reporting strengthened from "should" to MUST with the affected G2 PASSes enumerated. Corrects the claim that G2a is what the old G2 approximated — they are different quantities. Pins the gemma re-derivation to a full hs0…hs42 sweep to close the sweep-choice latitude vector, and states plainly that the defect's discovery was outcome-triggered even though the mechanism is outcome-independent. Fixes a v1.0 heading that still read "NOT-ADJUDICABLE, not PASS", contradicting its own corrected body. |

## Relationship to prior documents

- **Supersedes** the G2 definition in
  `experiments/j-space-cross-family-layer-contrast/AMENDMENT.md` and the
  `primary_gate.g2_midband_known_correct_cost_cap` entry in every
  `families/*.yaml` of that experiment.
- **Supersedes** the `falsifier:` field of that experiment's `experiment.yaml`
  until that field is corrected.
- **Does not** disturb G0, G1, the late-reference arm's non-gating status, or
  the reused doubt-snap pool/split pinning.
- **Does not** re-adjudicate any prior experiment *on the strength of Defect 1*,
  whose caveat is reporting-only and explicitly does not reopen verdicts.
- **Defect 3 may yet require re-adjudication of prior experiments.** The v1.0
  claim that the audit was complete and found no prior resolved result affected
  is retracted (see Defect 3 clause 3). At least one resolved, registered
  experiment — `gemma-4-e4b-family-atlas` — captured gemma-4-E4B activations
  through a `use_cache=False` path. Whether its claims actually rest on
  corrupted indices is undetermined. This document cannot state the blast radius
  until the re-scoped audit lands.

## Sign-off

- Drafted by: lead (Claude), 2026-07-24
- Approved by: _pending user signature_
- Enters force on signature. Until then, `j-space-cross-family-layer-contrast`
  remains at its signed INCONCLUSIVE verdict and no gemma re-run is authorized.
