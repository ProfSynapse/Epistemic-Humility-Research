# Papers Layout

Each paper has its own directory:

```text
papers/
  paper-1-taxonomy-framework/
    manuscript.md
    analysis/
    figures/
    scripts/
    notes/
  paper-2-training-regimen/
  paper-3-knows-but-doesnt-say/
  paper-4-two-signal-readout/
  paper-5-actuation/
  common/
  series/
```

Rules:

- `manuscript.md` is the active draft for that paper.
- `analysis/`, `figures/`, and `scripts/` belong to that paper only.
- `notes/` holds paper-specific citation audits, framing notes, and review prep.
- `common/` holds cross-paper writing conventions and shared citation material.
- `series/` holds the paper-series roadmap and cross-paper planning.
- Superseded drafts and retired inventories live under `archive/papers/`.

Historical figure prefixes are preserved for provenance. In this repo, `fig-p1-*`
currently belongs to `paper-2-training-regimen`, `fig-p2-*` to
`paper-3-knows-but-doesnt-say`, and `fig-p3-*` to
`paper-4-two-signal-readout`.
