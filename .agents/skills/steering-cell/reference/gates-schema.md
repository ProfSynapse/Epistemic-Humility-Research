# Gates YAML schema and the primitive library

Gates are scored by `score_gates.py --config cell.yaml --gates gates.yaml`, which
composes the pure primitives in `gate_primitives.py` over the runner's provenance
JSONLs. Keeping gate logic in a signed, readable config (rather than a fresh
bootstrap loop per amendment) is the point: a new amendment writes a `gates.yaml`.

The scorer reads GRADED arm rows. The runner writes raw generations; the
amendment's own byte-pinned grader adds the grade fields (`correct`,
`confab_on_unanswerable`, ...); then this scorer reads them. A grade-free gate
(e.g. a refusal count) can point at the raw rows directly.

## gates.yaml grammar

```yaml
seed: 20260705                 # default seed for every sampling primitive
arms:                          # arm tag -> rows.jsonl (relative to cell out_dir)
  primary: primary/gen/rows.jsonl
  control: control/gen/rows.jsonl
baseline:                      # frozen baseline grades
  rows_file: ../../analysis/.../rows_graded.jsonl
  key: row_key
predicates:                    # named row predicates over (base, arm) dicts
  baseline_confab: "base.get('confab_on_unanswerable') is True"
  baseline_correct: "base.get('correct') is True and base.get('answered') is True"
  steered_not_confab: "not arm.get('confab_on_unanswerable', False)"
  steered_refused: "arm.get('refused') is True"
gates:
  G1_collateral:
    kind: count_flips
    arm: primary
    before: baseline_correct
    after: steered_refused
    universe: flagged          # restrict to flagged rows (or omit for all)
    assert: "at_most(result.flips, 2)"
  G2_reach:
    kind: count_flips
    arm: primary
    before: baseline_confab
    after: steered_not_confab
    universe: flagged
    assert: "at_least(result.flips, 5)"
  G3_specificity:
    kind: kill_diff_vs_control
    treatment: primary
    control: control
    before: baseline_confab
    after: steered_not_confab
    n_boot: 1000
    assert: "at_least(result.diff, 5)"
```

Predicates and `assert`/`value`/`score` expressions run in a sandbox exposing only
`abs/min/max/len` plus the named objects (`base`, `arm`, or `result` +
`at_most/at_least/within`). No file/OS access.

## Gate kinds -> primitives

| kind | primitive | key fields |
|------|-----------|-----------|
| `count_flips` | `count_flips` | `arm`, `before`, `after`, optional `universe: flagged` |
| `kill_diff_vs_control` | `kill_diff_vs_control` | `treatment`, `control`, `before`, `after`, `n_boot` |
| `permutation_p` | `permutation_p` | `arm`, `value` (expr), `label` (predicate), `n_perm`, `tail` |
| `auroc_floor` | `auroc_floor` | `arm`, `score` (expr), `label` (predicate), `floor`, `n_boot` |

## The primitive library (`gate_primitives.py`)

All primitives are pure, CPU-only, and seeded (a re-run is byte-identical).

- `count_flips(records, before, after, universe=None)` -> `{universe, before,
  flips, rate}`. A flip is a row where `before` and `after` both hold; `universe`
  restricts the denominator.
- `kill_diff_vs_control(treatment_indicator, control_indicator, *, seed, n_boot,
  ci)` -> point diff + paired row-bootstrap CI over a shared universe;
  `ci_excludes_zero`.
- `permutation_p(values, labels, *, seed, n_perm, tail)` -> difference-of-means
  permutation test; add-one corrected p (never exactly 0); `tail` =
  greater/less/two-sided.
- `auroc_floor(scores, labels, *, floor, seed, n_boot, ci)` -> tie-safe AUROC +
  Hanley-McNeil analytic SE + seeded bootstrap CI; `pass` = CI lower bound >=
  floor (the conservative test).
- `at_most(value, ceiling)`, `at_least(value, floor)`, `within(value, lo, hi)` -
  leaf comparisons the `assert` expression composes.

## Output

`score_gates.py` writes `gates_report.json` under the cell out_dir with each
gate's primitive result + verdict and an `overall_pass`; it exits nonzero (5) when
any gate fails, so a CI/monitor can gate on it.
