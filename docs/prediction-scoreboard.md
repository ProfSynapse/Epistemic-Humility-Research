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
| AH (divergent-pool own-readout) | H-compliance, incl. crisp stratum ("prompt is like a shotgun") | H-compliance (~75–80%) | AMBIGUOUS — G2 a precise zero (−0.21pt, consistent with H-compliance) but G1 missed its floor (+15.65 vs +20), voiding certification per the locked §5 rule | **TIE / TIE** |

Running tally: **user 1 – orchestrator 0 – ties 1** (AG predates the
two-sided practice; the user gets the point, the orchestrator gets the
excuse. AH: both called H-compliance and the evidence agrees, but the
instrument gate voided certification — the gates, not the vibes, award
points. A G1 recalibration cell is proposed in AH §9.4; if it passes and
upgrades the verdict, this row upgrades to WIN/WIN.)
