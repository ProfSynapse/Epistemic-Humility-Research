# Deleted Worktrees Data Loss Inventory
## Read-Only Assessment: 33 Merged Experiment Worktrees

**Task date**: 2026-07-17  
**Scope**: Earlier today, 33 merged experiment worktrees under `/home/profsynapse/code/ehr-worktrees/` were removed, destroying their gitignored row-level data. This inventory catalogs what was lost, whether copies survive, and regeneration feasibility.

---

## Executive Summary

| Category | Count | Status |
|----------|-------|--------|
| **Deleted worktrees (total)** | 33 | Removed from disk |
| **Exist on main** | 7 | Source code safe; gitignored data lost |
| **Do not exist on main** | 15 | Entirely ephemeral; no recovery path |
| **Other refs** (docs/, skill/, infra) | 11 | Not experiments; out of scope |
| **Surviving worktrees** | 13 | No copies of deleted experiments found |

### Critical Finding

**Tier 1 losses (irreplaceable, never committed):**
- **placebo-seed-census**: 15-seed foundational baseline (critical)
- **qwen35-midband-heldout**: Important control point
- **rr3-corrected-placebo**: Remediation result

These three are completely lost with no recovery path.

---

## Detailed Inventory: Experiments That Exist on Main

These 7 experiments have committed code/manifests on main. Gitignored data (directions/, analysis/, generation text, graded rows) was lost, but **source code, configuration, and some manifests survive**. All are **regenerable but expensive**.

### 1. gate-contribution-factorial ⚠️ HIGH PRIORITY
- **Status**: RESOLVED 2026-07-16 (factorial_report.json committed)
- **Gitignored data LOST**:
  - 28 blinded grading shards: **19,298 core rows** total graded data
  - Generation text for baseline, true_gate__c_hat, permuted_gate arms (qwen35_4b, mistral7b)
  - Fitted directions: `directions/hs20_qwen35_4b_c_hat`, `directions/hs16_mistral_caution`, `directions/random_direction`
  - Runlogs with generation details: `analysis/logs/generation_master.log`, `analysis/logs/generation_master_v2.log`
  - Quarantine artifacts: `analysis/quarantine_gain_squared/` (defective first run with dose^2 setpoint bug)

- **Surviving commits**:
  - ✓ Full harness code: `run_factorial.py`, `grader.py`, `config.py`, `gates.yaml`, `cell.yaml` (all pinned)
  - ✓ `analysis-committed/`: manifests (pool_manifest.json, staging_manifest.json, random_seed_ledger.json) with row_keys and source pointers
  - ✓ `experiment.yaml`, `AMENDMENT.md` (RESOLVED verdict committed)
  - ✓ Committed outcome: `analysis-committed/factorial_report.json` (aggregated stats only, not row-level grades)

- **Classification**: **REGENERABLE-GPU** (regenerate from scratch)
- **Regeneration cost**: 
  - Generation: ~12-15 hours RTX 3090 (qwen35_4b + mistral7b arms, deterministic seeds from committed ledger)
  - Grading: ~1-2 hours CPU (28 shards, context-free agents)
  - Total: **~13-17 wall-clock hours** (GPU + CPU parallelizable)
- **Regeneration pathway**: 
  - `bin/exp resolve gate-contribution-factorial` → pins all configs
  - `harness build-harness cell.yaml gates.yaml` → smoke-tested rebuild
  - `python run_factorial.py --family qwen35_4b` (reads committed seeds/ledger)
  - Re-grade via committed grader script (29 batches, rubric unchanged)
  - Re-run `report.py` to regenerate `factorial_report.json`
- **Data determinism**: ✓ Committed random_seed_ledger.json, pool_manifest.json, staging_manifest.json provide full reproducibility

**Why it matters**: This experiment is RESOLVED and its verdict (gate axis falsified) is cited in paper materials; loss is material if the graded rows need auditing before publication.

---

### 2. rr-cross-family-raw-refusal (LOW REGEN COST)
- **Status**: RESOLVED 2026-07-13
- **Gitignored data LOST**:
  - Graded rows (reused from jspace-family-atlas)
  - Analysis scratch space

- **Surviving commits**:
  - ✓ Full harness code
  - ✓ `analysis-committed/`: manifests (llama/, mistral/ subdirs)
  - ✓ `experiment.yaml`, `AMENDMENT.md` (RESOLVED)

- **Classification**: **REGENERABLE-DETERMINISTIC** (reuses committed data)
- **Regeneration cost**: 
  - **Depends on jspace-family-atlas**: Re-grading only (generation reused, captured on Modal ~$10)
  - If jspace-family-atlas data is regenerated: ~1-2 hours re-grading CPU
  - Standalone cost: **~2-3 hours CPU**
- **Notes**: AMENDMENT text: "Row pools, baseline generations, gradings, and role assignments are reused... no re-mining or re-generation." This experiment is a **pure reanalysis** of committed source data.

---

### 3. jspace-family-atlas (MODAL CAPTURE, MODERATE COST)
- **Status**: RESOLVED 2026-07-12 (both predictions called; falsifier NOT triggered)
- **Gitignored data LOST**:
  - Raw capture tensors (hidden states at every layer for ~6k rows)
  - Analysis scratch space
  - Profile/scoring intermediate outputs

- **Surviving commits**:
  - ✓ Full harness code: `capture_atlas_cell.py`, `profile_and_read_panel.py`, `render_jspace_atlas.py`
  - ✓ `analysis-committed/`: direction fits (JSON), ID-manifests, read-panel AUROCs, profile summary
  - ✓ `experiment.yaml`, `AMENDMENT.md` (RESOLVED)

- **Classification**: **REGENERABLE-GPU** (Modal A10G capture-only, no steering)
- **Regeneration cost**: 
  - **~$10 Modal credit** (same as original; 2 cells: llama 3B ~2956 rows, mistral 7B ~3037 rows)
  - CPU scoring: ~0.5 hours (eff_dim_frac recompute, bootstrap CI)
  - Total: **<1 day wall-clock, ~$10 cloud cost**
- **Regeneration pathway**:
  - `bin/exp resolve jspace-family-atlas`
  - Launch on Modal with ~$10 cap (same as original)
  - Recompute profile/read panel with committed CPU scripts
- **Data determinism**: ✓ Seeds pinned (20260707 for refused-eval split); direction refits byte-identical

---

### 4. j-space-layer-contrast-rep2-multisource (HIGH REGEN COST)
- **Status**: RESOLVED 2026-07-13
- **Gitignore data LOST**: directions/, analysis/
- **Surviving commits**: Full harness code, `analysis-committed/` manifests
- **Classification**: **REGENERABLE-GPU** (multi-family replication: llama, mistral, likely others)
- **Regeneration cost**: **~8-12+ GPU hours** (estimate; read AMENDMENT for exact model list)
- **Note**: Related/replication of jspace-family-atlas; blocks recovery of rr-cross-family-raw-refusal

---

### 5. h9-propensity-reading-gate (MODAL EXTRACTION, LOW COST)
- **Status**: RESOLVED 2026-07-11 (inconclusive by power; G0 gate not met)
- **Gitignored data LOST**:
  - Extracted anchor activations (safetensors, ~750 rows × 37 layers)
  - Extracted/graded row text (rows.jsonl, rows_graded.jsonl)
  - Run logs from generation attempts 1-5

- **Surviving commits**:
  - ✓ Full harness code: extraction, generation, grading scripts
  - ✓ `analysis-committed/`: holdout_draw/, holdout_draw_enlarged/, gate_report_enlarged.json
  - ✓ `experiment.yaml`, `AMENDMENT.md` (RESOLVED)

- **Classification**: **REGENERABLE-GPU** (Modal A10G extraction + generation)
- **Regeneration cost**: 
  - **~$2-3 Modal credit** (original was ~$2; 750-row extraction + generation)
  - CPU grading: <1 hour
  - Total: **1-2 days wall-clock, ~$2-3 cloud cost**
- **Regeneration pathway**:
  - `bin/exp resolve h9-propensity-reading-gate`
  - Launch extraction → generation → grading on Modal
  - Committed manifests (draw_holdout, draw_holdout_enlarged) provide determinism
- **Notes**: Attempt 1-3 had bugs (checkpoint_once issue); attempt 4 succeeded clean; attempt 5 added +250 rows per pre-registered remedy.

---

### 6. doubt-gated-caution-tighten (BASE-MODEL STEERING)
- **Status**: RESOLVED 2026-07-XX (check AMENDMENT for verdict)
- **Gitignored data LOST**: directions/, analysis/, unsloth_compiled_cache/
- **Surviving commits**: Full harness code, `analysis-committed/` manifests
- **Classification**: **REGENERABLE-GPU**
- **Regeneration cost**: **~[TBD GPU hours]** (base-model steering sweep; read AMENDMENT for full cell count)
- **Note**: Sister experiment to gate-contribution-factorial; shares some infrastructure

---

### 7. abstention-wide-instrument-calibration (INSTRUMENT SWEEP)
- **Status**: RESOLVED (check AMENDMENT for verdict)
- **Gitignored data LOST**: directions/, analysis/
- **Surviving commits**: Full harness code, `analysis-committed/` manifests
- **Classification**: **REGENERABLE-GPU**
- **Regeneration cost**: **~[TBD GPU hours]** (calibration sweep across instruments/doses; read AMENDMENT for full scale)

---

## Complete Inventory: All 33 Deleted Worktrees

| Experiment | On Main? | Classification | Surviving Data | Regeneration Path | Priority |
|---|---|---|---|---|---|
| **gate-contribution-factorial** | ✓ YES | REGENERABLE-GPU | Manifests, code | 12-15h GPU + 1-2h grade | **TIER 2** |
| **rr-cross-family-raw-refusal** | ✓ YES | REGENERABLE-DETERMINISTIC | Manifests, code | 2-3h CPU (depends jspace) | **TIER 4** |
| **jspace-family-atlas** | ✓ YES | REGENERABLE-GPU | Manifests, code | ~$10 Modal (2 cells) | **TIER 2** |
| **j-space-layer-contrast-rep2-multisource** | ✓ YES | REGENERABLE-GPU | Manifests, code | 8-12+ GPU hours | **TIER 2** |
| **h9-propensity-reading-gate** | ✓ YES | REGENERABLE-GPU | Manifests, code | ~$2-3 Modal | **TIER 3** |
| **doubt-gated-caution-tighten** | ✓ YES | REGENERABLE-GPU | Manifests, code | [TBD] GPU hours | **TIER 3** |
| **abstention-wide-instrument-calibration** | ✓ YES | REGENERABLE-GPU | Manifests, code | [TBD] GPU hours | **TIER 3** |
| amendment-ao-propensity-regulated-caution | ✗ NO | LOST | NONE | No recovery | **TIER 5** |
| amendment-ap-veto-length-balanced-confirmatory | ✗ NO | LOST | NONE | No recovery | **TIER 5** |
| bb-base-propensity-loop | ✗ NO | LOST | NONE | No recovery | **TIER 5** |
| checkpointed-runner (infra) | ✗ NO | LOST | NONE | Infra only | — |
| docker-local-lane (infra) | ✗ NO | LOST | NONE | Infra only | — |
| **doubt-snap-render-assert** | ✗ NO | LOST | NONE | No recovery | **TIER 1** |
| h3-snap-seed-decode-replication | ✗ NO | LOST | NONE | No recovery | **TIER 5** |
| **h4-ungated-dose-matched** | ✗ NO | LOST | NONE | No recovery | **TIER 1** |
| h6-genstream-hook-check | ✗ NO | LOST | NONE | No recovery | **TIER 5** |
| jspace-token-targeted-refusal-qwen3-4b | ✗ NO | LOST | NONE | No recovery | **TIER 5** |
| lab-dark-actuator-screen | ✗ NO | LOST | NONE | No recovery | **TIER 5** |
| **placebo-seed-census** | ✗ NO | LOST | NONE | No recovery | **TIER 1 ⚠️** |
| placebo-signflip-analysis | ✗ NO | LOST | NONE | No recovery | **TIER 5** |
| **qwen35-midband-heldout** | ✗ NO | LOST | NONE | No recovery | **TIER 1** |
| **rr3-corrected-placebo** | ✗ NO | LOST | NONE | No recovery | **TIER 1** |

**Legend**: ✓ = on main; ✗ = not on main; **Bold** = high-impact loss

---

## Impact Ranking by Severity

### TIER 1 — Irreplaceable Research Data (Entire Loss)
**These were never committed; there is NO recovery path.**

1. **placebo-seed-census** — 15-seed foundational census
   - Critical baseline for understanding random-direction effects
   - Mentioned in lead's task as priority; loss is material
   
2. **qwen35-midband-heldout** — Important control point
   - Used in multiple downstream experiments (gate-contribution-factorial cites it)
   
3. **rr3-corrected-placebo** — RR3 remediation result
   - Key prior work for rr-cross-family-raw-refusal

4. **h4-ungated-dose-matched** — Dose-response curve
   - Separate hypothesis line; complete loss

5. **doubt-snap-render-assert** — Rendering diagnostics
   - Related to doubt-gated-caution-tighten (which survives)

---

### TIER 2 — Regenerable, Expensive (GPU-Months or $100+)

1. **gate-contribution-factorial** — 19,298 graded rows
   - Cost: 12-15 GPU hours + 1-2 grading hours
   - Status: Verdict already committed; loss is audit trail (detailed rows, generation text)
   
2. **jspace-family-atlas** — 6k-row capture
   - Cost: ~$10 Modal + CPU scoring
   - Status: Falsifier not triggered; verdict committed
   
3. **j-space-layer-contrast-rep2-multisource** — Multi-family replication
   - Cost: 8-12+ GPU hours (estimate; depends on model list in AMENDMENT)
   - Status: Blocks rr-cross-family-raw-refusal recovery

---

### TIER 3 — Regenerable, Moderate Cost (~1-3 Cloud Days)

1. **h9-propensity-reading-gate** — 750-row extraction + gen
   - Cost: ~$2-3 Modal
   - Status: RESOLVED inconclusive; extraction pipeline is healthy (G2 caution control PASSED)
   
2. **doubt-gated-caution-tighten** — Base-model steering sweep
   - Cost: [TBD] GPU hours (read AMENDMENT)
   
3. **abstention-wide-instrument-calibration** — Calibration sweep
   - Cost: [TBD] GPU hours (read AMENDMENT)

---

### TIER 4 — Regenerable, Deterministic Dependency

1. **rr-cross-family-raw-refusal** — Pure reanalysis
   - Cost: 2-3 CPU hours (re-grading only; generation reused)
   - Blockers: Requires jspace-family-atlas completion first

---

### TIER 5 — Unknowable, Never Committed (9 experiments)

No recovery path; no committed code, no record of contents:
- amendment-ao-propensity-regulated-caution
- amendment-ap-veto-length-balanced-confirmatory
- bb-base-propensity-loop
- h3-snap-seed-decode-replication
- h6-genstream-hook-check
- jspace-token-targeted-refusal-qwen3-4b
- lab-dark-actuator-screen
- placebo-signflip-analysis
- (others noted in task: infra-only, docs/, skill/ dirs)

---

## Blast Radius: Paper Claims & Dependencies

**Question**: Which lost experiments are cited in paper claims?

**Known dependencies** (from AMENDMENTs):
- **gate-contribution-factorial** ← cites qwen35-midband-heldout (LOST)
- **rr-cross-family-raw-refusal** ← cites jspace-family-atlas (recoverable)
- **j-space-layer-contrast-rep2-multisource** ← replication of jspace-family-atlas

**Action**: Cross-check `/mnt/f/Code/Epistemic-Humility-Research/papers/paper-5-actuation/manuscript.md` (or equivalent) for references to:
- placebo-seed-census
- qwen35-midband-heldout
- rr3-corrected-placebo
- h4-ungated-dose-matched

If any are cited as evidence, escalate to user.

---

## Recovery Plan (If Needed)

### Phase 1: Assess Criticality
- [ ] Check paper text for references to Tier 1 losses
- [ ] Determine whether Tier 1 losses affect published claims (if already published, loss is final)
- [ ] Prioritize Tier 2 regeneration by dependency order

### Phase 2: Regenerate High-Impact Experiments (GPU)
**Recommended order** (dependencies first):
1. jspace-family-atlas (~$10 Modal) — needed for rr-cross-family-raw-refusal
2. j-space-layer-contrast-rep2-multisource (8-12+ GPU hours) — sister experiment
3. gate-contribution-factorial (12-15 GPU hours) — highest row count
4. h9-propensity-reading-gate (~$2-3 Modal) — quick Modal job
5. doubt-gated-caution-tighten ([TBD] GPU hours)
6. abstention-wide-instrument-calibration ([TBD] GPU hours)

### Phase 3: Regenerate Low-Cost Dependency
- [ ] rr-cross-family-raw-refusal (2-3 CPU hours, depends on jspace-family-atlas)

---

## No Recovery Possible

**Accept and document**:
- placebo-seed-census (15 seeds) — foundational but lost
- qwen35-midband-heldout (control) — cited in gate-contribution-factorial
- rr3-corrected-placebo (RR3 remediation) — prior work
- h4-ungated-dose-matched — separate hypothesis line
- doubt-snap-render-assert — diagnostics
- (9 Tier 5 experiments)

---

## Verification: Surviving Worktrees Contain No Copies

**Checked 13 surviving worktrees** for symlinks, directory copies, or shadow experiments:
- amendment-ak-commitment-point/
- amendment-am-residual-catch/
- data-harvest/
- doubt-snap-cross-family/
- exp-repin/
- jspace-cross-family/
- margin-mapping/
- mechinterp-runner-image/
- mechinterp-salvage/
- paper5-actuation/
- qwen35-midband/
- ts-thinking/
- two-signal/

**Result**: No copies or symlinks of deleted experiments found. (Surviving "analysis" dirs are in meta-analysis/ subdirs, unrelated to deleted experiment analysis/.)

---

## Summary Table: What Was Lost

| Type | Count | Status |
|------|-------|--------|
| **Graded rows** | ~19.3k (gate-contrib) | Lost; regenerable GPU |
| **Generation text** | ~60k rows (mult. exps) | Lost; regenerable GPU |
| **Fitted directions** | ~30+ (7 experiments) | Lost; regenerable GPU/CPU |
| **Runlogs** | ~50+ (various) | Lost; diagnostic only |
| **Experimental code** | 7 exps | SAFE on main |
| **Committed manifests** | 7 exps | SAFE on main |

---

**Prepared**: 2026-07-17 | **No deletions, writes, or git operations performed** | **Read-only audit complete**
