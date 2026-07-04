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
import yaml, glob
for f in sorted(glob.glob('experiment/protocol/AMENDMENT-*.md')):
    fm = yaml.safe_load(open(f).read().split('\n---\n', 1)[0][4:])
    p = fm.get('predictions') or {}
    print(fm['amendment'],
          '| orch:', (p.get('orchestrator') or {}).get('call'),
          '| user:', (p.get('user') or {}).get('call'),
          '| outcome:', str(fm.get('outcome'))[:60])
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

Running tally: **user 3 – orchestrator 2 – ties 1** (AG predates the
two-sided practice; the user gets the point, the orchestrator gets the
excuse. AH resolved TIE/TIE at first adjudication — instrument voided at
the locked gates — then upgraded to WIN/WIN when the pre-registered
Addendum A1 recalibration certified the instrument on a fair population.
The Addendum A1 row scores separately: a distinct pre-registered question
with both predictions recorded before launch. AJ scores TIE/TIE: both
called the same strict gate outcome and the gate statistic landed
statistically indistinguishable from its threshold.)

Threshold-setting lesson (AJ, 2026-07-04): both predictions were
substantively right and the gate still failed to certify, because the
threshold was a round default (0.05) that the true effect happened to sit
on. When locking gates, aim small to miss small: pick thresholds against
the expected effect size and its uncertainty (e.g., derive the line from a
pilot's CI or a control distribution), not round numbers like .0/.5 — a
gate whose threshold sits inside the estimate's error bars cannot
adjudicate anything.
