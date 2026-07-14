# Steering-Cell Skill Assessment Report

**Branch**: `steering-cell-skill`  
**Commit**: `2aa210fe` (Mon Jul 6 07:19:31 2026 -0400)  
**Commit Message**: steering-cell skill: declarative YAML cells, generic runner + Modal wrapper, gate primitives

## Executive Summary

The `steering-cell` skill on the branch documents a declarative YAML-based wrapper around the legacy `experiment/phase1/probe/steering/` harnesses (steer_cell.py, score_gates.py, modal_steer_cell.py). **This machinery has been superseded on main by the tuner-backed `mechinterp-cells` skill**, which provides a generic, reusable verb-based interface (mechinterp steer, extract, probe-fit, score-gates, etc.) to the same problem domain.

**Recommendation**: **DELETE** the steering-cell skill without merging.

The steering-cell approach was a transitional layer (YAML wrapper + generic runner) designed before the tuner integration. The tuner-backed mechinterp-cells approach is the current canonical path and covers all equivalent functionality. No unique, durable content in steering-cell exists outside of mechinterp-cells or frozen legacy machinery.

---

## Detailed Classification

### Skill Files Inventory (Branch)

| File | Lines | Status |
|------|-------|--------|
| `.skills/steering-cell/SKILL.md` | 128 | Foundational skill doc |
| `.skills/steering-cell/reference/cell-schema.md` | 211 | YAML config schema |
| `.skills/steering-cell/reference/gates-schema.md` | 122 | Gate primitives + schema |
| `.skills/steering-cell/reference/run-and-sign.md` | 99 | Smoke-first + sign-pin-sha |
| `.skills/steering-cell/reference/modal-launch.md` | 82 | Modal lane launch guide |
| `.skills/steering-cell/reference/gotchas.md` | 115 | Cloud/GPU known issues |

---

### Content Classification by Piece

#### 1. **Six-Block Cell Model** → SUPERSEDED

**Status**: mechinterp-cells covers this via the tuner's declarative `mechinterp steer` verb.

- **Steering-cell**: Documents surface/readouts/law/arms/lane/gates blocks (SKILL.md lines 62–93).
- **mechinterp-cells**: References the same concept via `verbs-and-schemas.md` (tuner-backed, same semantic blocks).
- **Evidence**: mechinterp-cells SKILL.md lines 19–29 list the verbs (steer, dose-calibrate, extract, probe-fit, score-gates, run) that abstract the cell model. The tuner internalizes the block structure.

**Verdict**: **SUPERSEDED** — tuner is the current layer; steering-cell documents the transitional pre-tuner approach.

---

#### 2. **YAML Schema (cell.yaml + gates.yaml)** → SUPERSEDED

**Status**: The tuner's config schema is the canonical format now.

- **Steering-cell**: Documents cell-schema.md (181 lines) and gates-schema.md (122 lines) with example YAML structures.
- **mechinterp-cells**: Delegates to the tuner's `verbs-and-schemas.md` for the authoritative `mechinterp steer`, `mechinterp dose-calibrate`, etc. config formats.
- **Note**: The steering-cell cell.yaml and gates.yaml are NOT backward-compatible with mechinterp; they were a bespoke intermediate format.

**Verdict**: **SUPERSEDED** — tuner config is the current standard; steering-cell YAML is a frozen intermediate layer.

---

#### 3. **Smoke-First Discipline + Sign-Then-Pin-SHA** → SALVAGEABLE (PARTIAL)

**Status**: Unique procedural guidance that applies to any cell-based steering work.

- **Steering-cell**: run-and-sign.md (99 lines) documents:
  - Smoke-first enforcement (test before burning full GPU sweep).
  - Config sha256 pinning to prevent signed configs from drifting mid-run.
  - Untracked outputs (analysis dir).
  - 6-step arc (plan → smoke → full arm → grade → gates → record verdict).

- **mechinterp-cells**: Modal-launch.md mentions smoke exists but does NOT document the procedural discipline or the sha-pinning pattern in detail.
- **Main**: experiment-runner skill does mention signing/pinning but is protocol-focused, not procedural.

**Verdict**: **SALVAGE (PARTIAL)** — The smoke-first discipline and sha-pinning pattern are conceptually reusable, but should be grafted into mechinterp-cells/reference/pipeline-workflow.md or a shared sign-discipline reference, not kept as standalone steering-cell material. The exact YAML and commands are tuner-specific now.

---

#### 4. **Gate Primitives Library + Scoring** → SALVAGEABLE (PARTIAL)

**Status**: Frozen machinery now, but documentation of the gate logic is durable.

- **Steering-cell**: gates-schema.md (122 lines) + reference/gotchas.md touch on:
  - Gate kinds: count_flips, kill_diff_vs_control, permutation_p, auroc_floor.
  - Bootstrap CI helpers, tie-safe AUROC, Hanley-McNeil SE.
  - Predicate sandbox (no file/OS access, only abs/min/max).

- **mechinterp-cells**: score-gates is listed as a tuner verb; the tuner's gate primitives are the current layer.
- **Branch code**: gate_primitives.py exists (306 lines) with the actual implementations (count_flips, kill_diff_vs_control, etc.).

**Verdict**: **SALVAGE (PARTIAL)** — The gate logic itself (count_flips, permutation test, AUROC floor) is conceptually durable and could be referenced in a canonical gates reference doc. However, the implementations are now in the tuner, not in steering-cell. The branch's gate_primitives.py is frozen legacy code; documenting its logic in a neutral gates reference would be appropriate IF mechinterp-cells needs additional gate documentation.

---

#### 5. **Modal Launch + Cloud Checkpoint/Resume** → PARTIALLY SUPERSEDED

**Status**: Partially covered by mechinterp-cells, partially frozen legacy.

- **Steering-cell**: modal-launch.md (82 lines) + gotchas.md document:
  - One-liner Modal invocation with --config, --repo-commit, --staging-prefix, --detach.
  - Checkpoint daemon (Volume commit every 120s).
  - Respawn idempotency (clone-at-pin, xet guards).
  - Cost + approval requirement.

- **mechinterp-cells**: modal-launch.md EXISTS and covers tuner-specific cloud lanes.
- **Branch code**: modal_steer_cell.py (a specific wrapper) is frozen legacy.

**Verdict**: **PARTIALLY SUPERSEDED** — The checkpoint/resume and detach patterns are re-documented in mechinterp-cells. The steering-cell modal-launch.md has slightly different detail (e.g., the steer-specific wrapper invocation) but is tied to legacy machinery that's archived.

---

#### 6. **Cloud/GPU Gotchas (xet, PEFT, layer indexing, ULP floors)** → DURABLE (CHECK CURRENT STATE)

**Status**: Useful reference material, but should verify it still applies to tuner code.

- **Steering-cell**: gotchas.md (115 lines) documents:
  - HF xet CAS hang workaround (HF_HUB_DISABLE_XET=1).
  - PEFT unwrapping (get_base_model() fallback paths).
  - Layer index off-by-one (hidden_states[L] is block L-1 output).
  - Clone idempotency on respawn.
  - ULP floors for bf16 accumulation noise.
  - Reap-proof spawn (detach) + TaskStop skips finally.
  - Smoke-first is the cheap insurance.

- **mechinterp-cells**: modal-launch.md references gotchas but links to experiment-runner's cloud-lane reference.
- **Current state**: These gotchas apply to ANY activation-steering work on GPU. The question is whether the tuner's implementations still hit these same issues or has it handled them.

**Verdict**: **PARTIALLY DURABLE** — These are real gotchas that appear in activation-steering and GPU execution generally. However, they need to be reviewed against the current tuner codebase to determine if they still apply or have been mitigated. As legacy documentation, they're frozen; migrating them would require verifying them against the tuner's current code.

---

### Non-Skill Files Changed on Branch

The branch also touched:
- `.agents/` and `.claude/` mirrors (auto-generated mirrors of `.skills/steering-cell/`).
- `TODO.md` — updated amendment totals and status categories (migration-related, not steering-cell-specific).
- `.skills/experiment-runner/`, `.skills/mech-interp-runner/`, `.skills/mechinterp-cells/`, `.skills/experiments/` — significant updates to describe the tuner integration and legacy machinery archival.

**Verdict**: The experiment-runner and mech-interp-runner changes on the branch appear to be **already on main** (per my reads of the current SKILL.md files). The steering-cell skill was the NEW addition; the other changes were supporting narrative updates.

---

## Summary Table: Verdict per Component

| Component | Category | Evidence | Recommendation |
|-----------|----------|----------|-----------------|
| Six-block cell model doc | SUPERSEDED | mechinterp-cells documents the same blocks via tuner verbs | Delete |
| YAML schema (cell.yaml, gates.yaml) | SUPERSEDED | Tuner config format is canonical; these schemas are intermediate | Delete |
| Smoke-first discipline | SALVAGE | Conceptually reusable; should be integrated into mechinterp-cells references | Extract & integrate |
| SHA-pinning pattern | SALVAGE | Signing discipline is reusable; tuner-agnostic procedure | Extract & integrate |
| Gate primitives library | SALVAGE | Logic is durable; tuner now owns implementations. Docs may need refresh. | Extract if tuner underdocumented |
| Modal launch guide | PARTIALLY SUPERSEDED | mechinterp-cells already has modal-launch.md; steering-cell version is steer-specific | Delete |
| Cloud gotchas (xet, PEFT, ULP) | PARTIALLY DURABLE | Real issues, but need verification against tuner's current handling | Verify & migrate if not covered |
| Legacy Python code (steer_cell.py, gate_primitives.py, score_gates.py, modal_steer_cell.py, tests) | ARCHIVED LEGACY | Code is frozen in `archive/experiment/phase1/probe/steering/`; not in active use on main | Remains archived |

---

## Recommendations

### Immediate Action: DELETE

Do not merge the `steering-cell-skill` branch. The skill documents a transitional architecture that has been replaced by the tuner-backed `mechinterp-cells` approach on main.

**Why**:
1. **Superseded by tuner**: The entire cell-based steering workflow is now handled by mechinterp verbs. A separate steering-cell skill would duplicate and confuse the routing.
2. **Code is archived**: The Python implementations (steer_cell.py, etc.) were moved to `archive/` on main; they are not active development artifacts.
3. **Mechinterp-cells is canonical**: New work goes through the tuner's verbs, not the branch's declarative wrapper.

### Optional Follow-Up: Backfill mechinterp-cells (Lower Priority)

If the team later finds that mechinterp-cells documentation is thin in specific areas, consider:

1. **Smoke-first discipline**: Add a procedure reference to mechinterp-cells/reference/pipeline-workflow.md documenting when and how to validate steering arms before committing to full GPU sweeps.

2. **Sign-and-pin-sha pattern**: Add a section to mechinterp-cells/reference/verbs-and-schemas.md or pipeline-workflow.md documenting config sha256 pinning for signed cells.

3. **Gate gotchas**: Cross-check mechinterp-cells/reference/modal-launch.md against the steering-cell gotchas (xet, PEFT, ULP floors) to ensure cloud-specific issues are documented. If missing, add them.

These backfills should reference the **tuner's current code** and **mechinterp verbs**, not the steering-cell skill.

---

## Salvage Content (if backfill is approved)

If the team wants to integrate smoke-first or gate-logic documentation into mechinterp-cells, the source lines from steering-cell are:

- **Smoke-first procedure**: branch `.skills/steering-cell/reference/run-and-sign.md`, lines 1–43 (steps 1–6 + sign-then-pin details).
- **Gate primitives reference**: branch `.skills/steering-cell/reference/gates-schema.md`, lines 1–50 (gate kinds + primitive signatures).
- **Cloud gotchas**: branch `.skills/steering-cell/reference/gotchas.md`, all lines (every gotcha applies to activation-steering generally, need to verify tuner mitigation status).

---

## File Disposition

| File | Keep? | Rationale |
|------|-------|-----------|
| `.skills/steering-cell/*` | No | Delete; superseded by mechinterp-cells |
| `.agents/skills/steering-cell/*` | No | Delete (mirror of .skills/); auto-regenerated if needed |
| `.claude/skills/steering-cell/*` | No | Delete (mirror of .skills/); auto-regenerated if needed |
| `archive/experiment/phase1/probe/steering/` | Yes | Keep; frozen legacy machinery, separate from skills layer |

---

## Conclusion

**Verdict**: **DELETE the steering-cell-skill branch without merging.**

The branch represents a well-documented but transitional approach to steering-cell orchestration that predates the tuner integration. Main's current `mechinterp-cells` skill provides the same functionality via a generic, tuner-backed interface. Merging steering-cell would:
- Introduce routing confusion (two competing cell-skill paths).
- Document code in `archive/`, not active development.
- Duplicate guidance already in mechinterp-cells.

If specific documentation gaps emerge in mechinterp-cells (e.g., smoke-first procedures, gate-logic details, cloud gotchas), backfill mechinterp-cells references with tuner-specific content and point users there, not to a separate steering-cell skill.
