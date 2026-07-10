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
| AK (commitment-point) — SIGNED, not launched | G1 PASS; G2 path **H-rise** ("I bet doubt increases"); G3 PASS | G1 PASS (~80%); G2 path **H-flat-then-rise** (~55%, second pick H-rise); G3 PASS (~75%) | _pending — launch gated behind Amendment AI arc + GPU approval_ | — |
| AI (probe-as-reward) | TRUE wins | TRUE wins (~65%) | **NULL, G1 inverted**: TRUE congruence 59.75% vs PERMUTED 76.75%, differential −17.0pt (CI [−21.5, −12.5] excludes 0 on the wrong side); G0 valid (fresh probes 0.9948/0.9946); G2 fails both arms (over-refusal released) though TRUE alone holds the refusal boundary (+0.49pt, 40% fewer hallucinations than control). Reward channel doesn't couple the readout | **TIE / TIE** |
| AL (radial anti-propensity steering) | G1 PASS; G2 PASS; G3 PASS ("LETS BE BOLD!") | G1 PASS (~75%); G2 PASS (~45%); G3 PASS (~50%) | **USE-THE-SIGNAL NULL (injection channel)**: G1 PASS (0 collateral), G2 MISS (0/116 kills; 2x dose flips 1/30), G3 MISS (diff 0, CI [0.00, 0.00]). Injection verified precise (readback ratio 1.0008; 1564/1564 unpushed parity), so the propensity readout does not actuate the fabricate-vs-refuse choice. Sixth use-the-signal null | **LOSS / WIN** (adjudicated by the user 2026-07-05, "you best me on this one": both hit G1; on G2/G3 the user bet PASS at full confidence, the orchestrator leaned miss at 45%/50%) |

| AN (selected-setpoint regulator) | G1 PASS; G2 PASS; G3 PASS ("I agree on all passing") | G1 PASS (~70%); G2 PASS (~40%); G3 PASS (~40%) | **NULL, falsifier fired**: AN-G1 PASS (0 collateral) but VACUOUS - zero effect on the write means zero collateral by construction; AN-G2 MISS (0/116 confabs killed, floor 5; dose ladder 0/0/0 at g=+1/+2/+3); AN-G3 MISS (primary-minus-control diff 0, CI [0.0, 0.0], floor 5). Smoke readback confirms the write lands precisely on-axis (max abs error 0.58 vs sigma 22.13); descriptive bidirectional arm also de-refuses 0/114. Pairing AL's reaching sensor with AC's proven actuator still does not reach the confab cloud | **LOSS / WIN** (user called PASS at full confidence on the central bet; orchestrator's ~40% on G2/G3 was the directionally correct lean, same disagreement shape as AL) |

Running tally: **user 3 – orchestrator 4 – ties 2** (AG predates the
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
is scored a win even though the literal call label was "PASS".)

Threshold-setting lesson (AJ, 2026-07-04): both predictions were
substantively right and the gate still failed to certify, because the
threshold was a round default (0.05) that the true effect happened to sit
on. When locking gates, aim small to miss small: pick thresholds against
the expected effect size and its uncertainty (e.g., derive the line from a
pilot's CI or a control distribution), not round numbers like .0/.5 — a
gate whose threshold sits inside the estimate's error bars cannot
adjudicate anything.
