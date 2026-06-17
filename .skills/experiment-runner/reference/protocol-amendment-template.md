# Protocol Amendment Template

```markdown
# Protocol Amendment <LETTER>: <Title>

**Status:** DRAFT / NOT SIGNED

**Short name:** Amendment <LETTER> / <short-name>

**Scope:** <one-paragraph summary of what this amendment changes or adds>

**Session note:** `docs/sessions/NNNN - <session-title>.md`

---

## 1. Rationale

Why this amendment is needed. Name the gap in the current protocol and the
evidence or design pressure motivating the change.

## 2. Relationship To Existing Protocols

State whether this is additive, superseding, or correcting. Name every affected
protocol/amendment and explicitly say what remains locked.

## 3. Design Change

Define the new arms, output contract, metric, dataset, run matrix, or analysis
rule. Include schemas or tables when they remove ambiguity.

## 4. Rerun / Launch Requirement

State which existing artifacts can be reused and which must be rerun. If any
old outputs cannot answer the new measurement question, say that directly.

## 5. Metrics And Interpretation

Define new metrics, their targets, and how they should and should not be
interpreted.

## 6. Implementation Boundary

Name the files/scripts/configs involved. State any submodule or data-containment
boundaries.

## 7. Launch And Reporting Rules

State approval requirements, output labels, run/session record expectations, and
whether results can feed headline claims.

## 8. Sign-Off Checklist

- approval date:
- approved scope:
- approved cells/seeds/lane:
- excluded cells/seeds:
- schema/metric definitions frozen:
```

