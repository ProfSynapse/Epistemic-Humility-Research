# Protocol Revision — J-space gate adjudication and shared-instrument defects

**Tier:** 1 (signed protocol revision — touches gate definitions, the roll-up
interpretation rule, and a shared measurement instrument)
**Version:** v1.0
**Date drafted:** 2026-07-24
**Status:** DRAFT — awaiting user signature. Nothing in this document is in force
until signed.
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

## Defect 1 — G2 is structurally vacuous (NOT-ADJUDICABLE, not PASS)

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
   only — not to verdicts).** Fire rate must be reported as a companion number
   to every cost/harm gate's point estimate and CI, per the reference's review
   checklist. This changes what is *printed*, not what any gate *decided*.
4. **G2 is superseded for FUTURE pre-registrations by two separately-adjudicable
   gates.** This is a forward-looking design change, per the reference's "Design
   prescription for a FUTURE non-vacuous gate":

   - **G2a — gate selectivity (no new measurement required).** On known-correct
     rows, the fraction on which the KU readout gate FIRES. Cap: `<= 0.05`,
     Wilson upper `< 0.10`. Already measured and strongly passing (0/334,
     0/382). This is what the old G2 was accidentally approximating.
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
should be annotated with the fire-rate caveat where a G2 PASS was reported, as
an addition to the record rather than a change to it.

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

1. **The INCONCLUSIVE floor is canonical.** Fewer than the registered minimum
   number of families running past G0 ⇒ INCONCLUSIVE, and this test is
   evaluated **before** the falsifier test. Rationale: a denominator too small
   to establish "generalizes" is equally too small to establish "does not
   generalize." The falsifier clause presupposes an adequate denominator.
2. **`experiment.yaml`'s `falsifier:` field must be corrected to match.** Until
   corrected it is superseded by this revision, not by silent edit.
3. **Precedence rule (general).** Where registered documents conflict:
   (a) the registered *instrument* (the roll-up script) governs over prose;
   (b) where prose conflicts, the **more conservative** reading governs;
   (c) the conflict must be recorded in the Outcome, never resolved silently.
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

Families without cross-layer KV sharing (llama, mistral, qwen) are unaffected —
verified min cos 1.000000 between `use_cache` settings on the extraction path.

### The revision

1. **`jlens.py:195` is corrected to `use_cache=True`.** This is authorized as
   instrument repair notwithstanding the do-NOT-modify marking, which exists to
   prevent silent divergence between consumers, not to freeze a known defect.
2. **The correction must be verified as a no-op for non-KV-sharing families
   before the file is changed**, by comparing hidden states under both settings
   on at least one non-sharing family and requiring bit-identity (or cos
   1.000000). If it is not a no-op, this clause does not authorize the edit and
   the revision returns for re-signature.
3. **Consumers of the shared j-lens: AUDITED 2026-07-24, blast radius is
   gemma-4-E4B only.** The audit is complete and this clause is discharged, not
   deferred.

   Two copies of the instrument carry the identical defect:
   `j-space-localization-qwen3-4b/jlens.py:195` and
   `qwen35-4b-midband-doubt-snap/jlens_qwen35.py:127`. Four
   `layer_profile.json` artifacts exist in total, all in
   `j-space-cross-family-layer-contrast`.

   Cross-layer KV sharing, read from each checkpoint's `config.json`
   (`text_config` where nested):

   | model | n_layers | KV sharing | affected |
   |---|---:|---|:--:|
   | google/gemma-4-E4B-it | 42 | `num_kv_shared_layers: 18` (⇒ boundary at 24) | **YES** |
   | Qwen/Qwen3.5-4B | 32 | none (hybrid linear/full attention, no sharing keys) | no |
   | meta-llama/Llama-3.2-3B-Instruct | 28 | none | no |
   | mistralai/Mistral-7B-Instruct-v0.3 | 32 | none | no |

   **Consequence: no prior resolved experiment is invalidated.**
   `qwen35-4b-midband-doubt-snap` and `qwen35-4b-midband-heldout` profiled
   Qwen3.5-4B, which does not share KV, so their site selection — including the
   hs20 promotion — stands. Hybrid linear/full attention is not KV sharing and
   does not trigger this defect. The only invalid site selection anywhere is
   gemma4-e4b's, addressed in clause 4.

   The second copy (`jlens_qwen35.py:127`) should still be corrected for
   hygiene, since it would silently corrupt any future KV-sharing model pointed
   at it, but no existing result depends on the fix.
4. **gemma4-e4b's band selection is voided and must be re-derived** from a
   corrected profile run. `band_selection.status` reverts `resolved` →
   `not_yet_run`; `midband_candidates_hs`, `effective_dim_peak_hs`, and
   `late_reference_hs` are cleared and re-derived by the same registered method
   applied to correct data.

   **This is repair, not goalpost movement.** The distinction: goalpost movement
   is re-selecting sites *because a result was unfavourable*; this is
   re-selecting because the *instrument that chose them was broken*, established
   by a mechanism independent of any outcome. The prior gemma null (0/176) is
   accordingly **uninterpretable, not negative**, and must not be cited as
   evidence of a gemma write failure.
5. **The re-derived sites are binding once written**, before any dosed run at
   them. The selection must be committed and the family file updated prior to
   running, so the sites cannot be tuned against the result.

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
| v1.0 | 2026-07-24 | Initial revision. Retires G2, introduces G2a/G2b, makes vacuous-denominator gates NOT-ADJUDICABLE; makes the INCONCLUSIVE floor canonical and adds a document-precedence rule; authorizes the `jlens.py` `use_cache` repair and voids gemma4-e4b band selection. |

## Relationship to prior documents

- **Supersedes** the G2 definition in
  `experiments/j-space-cross-family-layer-contrast/AMENDMENT.md` and the
  `primary_gate.g2_midband_known_correct_cost_cap` entry in every
  `families/*.yaml` of that experiment.
- **Supersedes** the `falsifier:` field of that experiment's `experiment.yaml`
  until that field is corrected.
- **Does not** disturb G0, G1, the late-reference arm's non-gating status, or
  the reused doubt-snap pool/split pinning.
- **Does not** re-adjudicate any prior experiment. The Defect 3 audit is
  complete and found no prior resolved result affected; the Defect 1 caveat is
  reporting-only and explicitly does not reopen verdicts.

## Sign-off

- Drafted by: lead (Claude), 2026-07-24
- Approved by: _pending user signature_
- Enters force on signature. Until then, `j-space-cross-family-layer-contrast`
  remains at its signed INCONCLUSIVE verdict and no gemma re-run is authorized.
