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

Running tally: **user 3 – orchestrator 2 – ties 0** (AG predates the
two-sided practice; the user gets the point, the orchestrator gets the
excuse. AH resolved TIE/TIE at first adjudication — instrument voided at
the locked gates — then upgraded to WIN/WIN when the pre-registered
Addendum A1 recalibration certified the instrument on a fair population.
The Addendum A1 row scores separately: a distinct pre-registered question
with both predictions recorded before launch.)
