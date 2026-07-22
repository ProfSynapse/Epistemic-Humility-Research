# Prediction Scoreboard

Standing practice (adopted 2026-07-03): before every amendment launches, the
orchestrator and the user each record an independent prediction. Outcomes get
scored here. Disagreement is a feature — whoever is wrong learns the most.
Predictions must be recorded in the amendment doc BEFORE launch; this file is
the ledger, the doc is the source of truth.

Every amendment doc also carries the predictions in machine-readable YAML
frontmatter (`amendment`, `question`, `predictions.{orchestrator,user}`,
`outcome`, `scoreboard`) — backfilled across the whole series 2026-07-03.
Query the series in one shot:

```bash
python3 - <<'EOF'
from pathlib import Path
import yaml
for f in sorted(Path('experiments').glob('*/experiment.yaml')):
    manifest = yaml.safe_load(f.read_text()) or {}
    legacy = manifest.get('legacy') or {}
    label = legacy.get('label') or manifest.get('slug')
    prediction = str(manifest.get('prediction') or '').splitlines()[0][:80]
    outcome = str(manifest.get('outcome') or manifest.get('verdict') or '')[:80]
    print(label, '| prediction:', prediction, '| outcome:', outcome)
EOF
```

Scoring: each party gets WIN, LOSS, or **TIE** per resolved amendment. A TIE
is scored when the result is ambiguous at the pre-stated gates, the
instrument is voided, or both predictions are equally right or equally wrong
(including convergent predictions that both hit or both miss). Ties score to
neither side and are tallied separately.

| Amendment | User predicted | Orchestrator predicted | Outcome | Score (U–O) |
|---|---|---|---|---|
| AG (inverted prime) | "pure behavior not internal alignment" | _(not separately recorded — practice predates)_ | ASYMMETRIC COMPLIANCE; doubt axis unmoved | user ✓ / — |
| AD (trained-checkpoint flip) | — | null (signed, shelved) | not launched | — |
| AH (divergent-pool own-readout) | H-compliance, incl. crisp stratum ("prompt is like a shotgun") | H-compliance (~75–80%) | **H-COMPLIANCE** (certified via Addendum A1) — G2 a precise zero (−0.21pt); initial G1 miss recalibrated on a representative stratum, +50.98pt vs +20pt floor | **WIN / WIN** |
| AH Addendum A1 (G1 recalibration) | PASS — clears +20pt | PASS (~80%) | PASS +50.98pt; monotone caution-quintile gradient confirmed the population diagnosis | **WIN / WIN** |
| AJ (knowledge-subspace erasure) | SURVIVES (AJ-G2 PASS) | SURVIVES (AJ-G2 PASS, ~85%) | Adjudicated **SURVIVES, dependency quantified**: certificate PASS (0.996 → 0.496), caution 0.858 post-erasure, but the random-control gap landed ON the pre-stated 0.05 line (0.054 ± 0.006 across 24 seeds; P(≤0.05) = 0.415) — strict G2 ambiguous | **TIE / TIE** |
| AK (commitment-point) | G1 PASS; G2 path **H-rise** ("I bet doubt increases"); G3 PASS | G1 PASS (~80%); G2 path **H-flat-then-rise** (~55%, second pick H-rise); G3 PASS (~75%) | **RESOLVED 2026-07-06** (this row was stale "not launched" text until the 2026-07-20 programmatic audit caught it): AK-G1 MISS (delta -0.0175 vs +0.10 floor; both predictors called PASS, both missed); AK-G2 MISS (contrast 4.6234 < locked floor 5.291963); AK-G3 MISS-with-confound (gen_stream instrumentation bug, causal null not adopted). Source: `experiments/commitment-point/experiment.yaml` verdict | **TIE / TIE** (ratified by the PI 2026-07-21): G1 convergent miss (both called PASS, both missed) scores TIE/TIE per the AI precedent; G2's fork is unadjudicated behind its gate MISS and G3's confound is explicitly not adopted as adjudicating, so neither moves the score |
| AI (probe-as-reward) | TRUE wins | TRUE wins (~65%) | **NULL, G1 inverted**: TRUE congruence 59.75% vs PERMUTED 76.75%, differential −17.0pt (CI [−21.5, −12.5] excludes 0 on the wrong side); G0 valid (fresh probes 0.9948/0.9946); G2 fails both arms (over-refusal released) though TRUE alone holds the refusal boundary (+0.49pt, 40% fewer hallucinations than control). Reward channel doesn't couple the readout | **TIE / TIE** |
| AL (radial anti-propensity steering) | G1 PASS; G2 PASS; G3 PASS ("LETS BE BOLD!") | G1 PASS (~75%); G2 PASS (~45%); G3 PASS (~50%) | **USE-THE-SIGNAL NULL (injection channel)**: G1 PASS (0 collateral), G2 MISS (0/116 kills; 2x dose flips 1/30), G3 MISS (diff 0, CI [0.00, 0.00]). Injection verified precise (readback ratio 1.0008; 1564/1564 unpushed parity), so the propensity readout does not actuate the fabricate-vs-refuse choice. Sixth use-the-signal null | **LOSS / WIN** (adjudicated by the user 2026-07-05, "you best me on this one": both hit G1; on G2/G3 the user bet PASS at full confidence, the orchestrator leaned miss at 45%/50%) |

| AN (selected-setpoint regulator) | G1 PASS; G2 PASS; G3 PASS ("I agree on all passing") | G1 PASS (~70%); G2 PASS (~40%); G3 PASS (~40%) | **NULL, falsifier fired**: AN-G1 PASS (0 collateral) but VACUOUS - zero effect on the write means zero collateral by construction; AN-G2 MISS (0/116 confabs killed, floor 5; dose ladder 0/0/0 at g=+1/+2/+3); AN-G3 MISS (primary-minus-control diff 0, CI [0.0, 0.0], floor 5). Smoke readback confirms the write lands precisely on-axis (max abs error 0.58 vs sigma 22.13); descriptive bidirectional arm also de-refuses 0/114. Pairing AL's reaching sensor with AC's proven actuator still does not reach the confab cloud | **LOSS / WIN** (user called PASS at full confidence on the central bet; orchestrator's ~40% on G2/G3 was the directionally correct lean, same disagreement shape as AL) |
| correctness-subspace-overlap (SO) | Approved the design arc 2026-07-20 following lit-review due diligence; no separate quantitative call recorded | Reading A (shared flat subspace): k=8 S->T overlap 0.45-0.70 against a permutation-null mean ~0.20-0.35, within-stage full-n reliability 0.75-0.90, recovery curve closing ~0.80+ of the floor-to-ceiling gap | **Null-result (instrument-limited)**: SO-G1 FAILED all three limbs at k=8 (overlap 0.01157 inside the permutation null 0.01085/0.01419; reliability S 0.0185 / T 0.0293 vs the 0.70 floor; recovery closed fraction 0.175 vs 0.75). A post-hoc planted-signal simulation showed the reliability gate was estimator-structurally unreachable for any signal, so the falsifier's non-firing carries no evidential weight. Label-clean positive: one weak shared direction at k=1 (recovery AUROC ~0.70); the transferable signal is otherwise diffuse across S's span | **— / LOSS** (orchestrator's Reading A call was wrong on every quantitative band; no separate user call to score a win against, so the running tally below is unaffected) |
| AM (residual-catch-veto-coverage) | AM-G1 PASS; AM-G2 PASS ("taking the coverage bet at full confidence") | AM-G1 PASS (~70%); AM-G2 PASS (~60%) | Gates literally PASS as pre-registered (OOF veto AUROC 0.9168, perm p=0.001) BUT the pre-recording adversarial audit found the catch is dominated by an undisclosed answer-length confound (length alone 0.943 > veto 0.917); the doc's own verdict: "the mechanistic two-signal-coverage claim is NOT established." Resolved 2026-07-05 era; row added by the 2026-07-21 backfill | **TIE / TIE** (ratified by the PI 2026-07-21): convergent hits on gates whose evidential content the disclosed confound voided -- AJ/voided-instrument precedent, not AH's clean WIN/WIN; upgrade path exists if a length-matched re-run ever certifies the veto, mirroring AH Addendum A1 |
| correctness-geometry-scale-ladder | "PARTIAL / NON-MONOTONE (recorded 2026-07-20 EDT): a rise that stalls or reverses, e.g. tracking the non-monotone AUROC" | "DIFFUSE-STABLE: c stays near 0 at every scale, no trend toward 1" | **RESOLVED (G1 middle ground M3)**: crystallization index c rises monotonically at scale-adaptive best-dial layers (-0.06 -> +0.09 -> +0.24, Delta_c 0.302 clearing both sigma readings) but stalls/reverses at fixed relative depth (0.033 -> 0.129 -> 0.075); falsifier not triggered; red-teamed (selection provenance checked, not inflated; window scan shows layer-robust trend, recorded without upgrading). PR #324, merged 2026-07-20 | **WIN / LOSS** (user's "rise that stalls or reverses" describes the fixed-depth arm almost verbatim and correctly rejected both alternatives; orchestrator's diffuse-stable is refuted by best-dial clearing the trend threshold; ratified at PR #324 merge) |
| gemma-4-e4b-family-atlas | Approved the atlas arc 2026-07-20 ("get gemma going"); no separate quantitative call recorded | Falsifier fires on the profile limb: eff_dim_frac peaks early-exterior, matching jspace-family-atlas's llama/mistral result, so no interior workspace band is declared. Read panel still healthy: at least one mid-depth layer holds held-out AUROC >= 0.80 on all three axes, not coinciding with an interior eff_dim_frac peak. Sub-clause: ported layer hs40 reads well on raw_refusal, weaker on doubt | **RESOLVED (falsifier fired, profile limb)**: eff_dim_frac peaks at hs 4 of 42 (0.095 depth, early-exterior); contiguous all-three-axes >= 0.80 band at hs 13-42; third family with the early-exterior-peak + healthy-midband decoupling. Orchestrator headline exactly right; hs40 sub-clause wrong (the known-unknown/KU axis, artifact key `doubt`, is the STRONGEST at hs40, 0.9949). AG0a passed on the twice-revised instrument (0.9286 vs 0.90). PR #323, merged 2026-07-20 | **— / WIN** (headline correct on both clauses; sub-clause miss disclosed; user recorded design approval only, so no user-side score) |
| qwen3-4b-family-atlas | INTERIOR PEAK (recorded pre-sign 2026-07-21): the eff_dim_frac profile breaks the 3-of-3 early-exterior pattern and peaks in the interior, following the J-lens hs23-29 finding | Early-exterior eff_dim_frac peak (fourth family in the pattern), healthy interior read band; sub-call: the J-lens interior peak does NOT reproduce in the eff_dim_frac profile (instruments dissociate on peak location) | **RESOLVED (falsifier fired, profile limb)**: eff_dim_frac peaks at hs 5 of 36 (0.139 depth, early-exterior); interior all-three-axes >= 0.80 band at hs 22-36 (carried by caution + raw_refusal over their controls; doubt norm/position confounded, 4th family to show it); fourth family with the early-exterior-peak + healthy-interior-band decoupling. Independently re-derived by the lead from the committed atlas_summary.json. | **LOSS / WIN** (orchestrator correct on both the profile peak and the J-lens-dissociation sub-call; user's registered eff_dim_frac-peak call falsified. Credit recorded in the amendment: the user's interior intuition is vindicated on the READ panel — the epistemic axes peak hs22-36, on the J-lens band — so the miss is instrument attribution, not signal location. Ratified by the PI 2026-07-21, "you've defeated me again") |

> **AUDIT NOTICE (2026-07-20, backfill adjudicated 2026-07-21).** A
> programmatic audit of all 86 `experiments/*/experiment.yaml` manifests
> found: (1) this file's header misstates the machine schema — the real
> fields are `prediction` (a YAML-string requiring a second parse) and
> `verdict`; no `predictions`/`outcome`/`scoreboard` keys exist anywhere;
> (2) 24 resolved amendments had no (or stale) ledger presence. The
> backfill worksheet resolved this as follows, under the **PI scoping
> ruling of 2026-07-21**: 22 of the 24 (J, K, L, M, N, O, P, Q, R, S, SR,
> T, U, W, X, Y, Z, AA, AB, AC, AE, AF) predate the dual-prediction
> practice — their manifests record `user: call: null` — and are
> **permanently unscored**: this ledger tracks only the two-sided era
> where both parties had the opportunity to call. Their outcomes remain in
> their own governed docs; they get no rows and move no tally. The two
> post-practice cases (AK, AM) are scored in the table above. The durable
> fix (machine-readable `scoreboard:` blocks written at resolve, a
> checked-in tally script, and a merge-githook consistency check) is
> queued as a process change.

Running tally (table rows only, see audit notice): **user 4 – orchestrator 6 – ties 4** (qwen3-4b-family-atlas
scores LOSS/WIN — the first family-atlas where the user made a competing
quantitative call, ratified by the PI 2026-07-21. AK and AM
TIE/TIE ratified by the PI 2026-07-21. AG predates the
two-sided practice; the user gets the point, the orchestrator gets the
excuse. AH resolved TIE/TIE at first adjudication — instrument voided at
the locked gates — then upgraded to WIN/WIN when the pre-registered
Addendum A1 recalibration certified the instrument on a fair population.
The Addendum A1 row scores separately: a distinct pre-registered question
with both predictions recorded before launch. AJ scores TIE/TIE: both
called the same strict gate outcome and the gate statistic landed
statistically indistinguishable from its threshold. AI scores TIE/TIE:
convergent predictions that both missed — both called TRUE wins and the
gate came back significantly inverted. AN scores LOSS/WIN: both called
AN-G2/AN-G3 PASS, both missed, but the orchestrator's recorded confidence sat
below 50% on those two gates, the same sub-50%-counts-as-a-lean convention
already applied to AL's G2/G3 calls, so the orchestrator's directional lean
is scored a win even though the literal call label was "PASS". SO scores
a unilateral LOSS for the orchestrator (Reading A wrong on every band);
the user recorded only a design-approval, not a competing quantitative
call, so there is no win to award and the tally above does not move.
gemma-4-e4b-family-atlas scores a unilateral WIN for the orchestrator,
the mirror image of the SO convention: the recorded headline (falsifier
fires early-exterior on the profile limb, read panel healthy at mid-depth)
was exactly right, the descriptive hs40 sub-clause was wrong and is
disclosed in the resolved doc, and the user recorded design approval only,
so no user-side score is awarded and only the orchestrator count moves.
correctness-geometry-scale-ladder scores WIN/LOSS for the user: the
realized M3 pattern is a partial whose fixed-depth arm stalls and reverses
exactly as the user called, while the orchestrator's diffuse-stable call
is refuted by the best-dial arm clearing the trend threshold under both
sigma readings; ratified by the PI at the PR #324 merge.)

Threshold-setting lesson (AJ, 2026-07-04): both predictions were
substantively right and the gate still failed to certify, because the
threshold was a round default (0.05) that the true effect happened to sit
on. When locking gates, aim small to miss small: pick thresholds against
the expected effect size and its uncertainty (e.g., derive the line from a
pilot's CI or a control distribution), not round numbers like .0/.5 — a
gate whose threshold sits inside the estimate's error bars cannot
adjudicate anything.
