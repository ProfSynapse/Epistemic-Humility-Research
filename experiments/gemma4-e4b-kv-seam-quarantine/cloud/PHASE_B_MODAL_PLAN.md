# Phase B Modal stage plan — gemma4-e4b-kv-seam-quarantine

Derived from `AMENDMENT.md` (Design / Revision 2026-07-30, G0-KV, G0-ALIN,
Falsifier), `gates.yaml`, `cell.yaml` (`pipeline_stages`, `arms`,
`kv_seam`, `families/gemma4-e4b.yaml band_selection`), and `NOTEBOOK.md`'s
Phase A stage entries (Stages 1–6, 2026-07-29/30), by reading those files
directly — this plan is not a restatement of the dispatch summary. Every
stage below cites the doc line/section it comes from. Pinned CLI shapes were
verified against each script's own `--help`, not assumed from prose.

**BUILD AND DRY-RUN ONLY.** Nothing below has been launched. No GPU stage has
run. `EHR_LAUNCH_OK=gemma4-e4b-kv-seam-quarantine` (the repo's launch-guard
hook, `.claude/hooks/launch_guard.sh`) plus the lead's explicit go are both
required before `modal_phase_b.py` spawns any GPU function.

## Governing constraints (Revision 2026-07-30, AMENDMENT.md:248-263)

1. The Modal image reproduces the tf550 environment pins exactly:
   `transformers==5.5.0`, `accelerate==1.14.0`, tuner
   `34c89fc4f9d693a6b997422288d820e9c30b4696`. Image digest recorded per
   stage.
2. Every registered comparison is same-environment internally: A1 and A2
   both run on Modal; C1 runs entirely on Modal; the `A_lin` clause's ON
   side is RE-MEASURED on Modal alongside the OFF side (forward passes
   only) so the `|diff| <= 0.05` threshold never straddles GPU
   architectures. The local `A_lin` Part 1 numbers (`alin_part1_selection.json`,
   below-seam sites, all 0.0000) remain on record but do not satisfy
   condition 2 for hs38 — Part 2 at hs38 under BOTH conditions must be
   re-run on Modal.
3. No other registered quantity, gate, ladder, or pool changes.

## What Phase A already produced (does not re-run)

Per `NOTEBOOK.md` Stages 1–6 (2026-07-29/30, local RTX 3090,
`mechinterp-runner:tf550`, digest
`sha256:479b7ca7891ab328ce7f04adffb949ef8086e3cf0d87676a3577d1d76cd845c8`,
tuner `34c89fc4f9d693a6b997422288d820e9c30b4696`):

- A3 (hs22, ON): PASS (G1 0.5893, G2 0.0037), G3 PASS-DEGENERATE.
- A5 (hs24, ON): PASS (G1 0.7321, G2 0.0333), G3 **FAIL** (effect_ratio 1.14 < 3.0).
- D1 (hs15, ON): PASS (G1 0.7857). D2/D3 (hs18/hs20): G1 FAIL. D4/A6 (hs23): dose-viability NOT-RUN.
- P1/P2 placebo draws (K=5): complete.
- C0/C1, A1, A2, A4, and the terminal `rollup.py` were explicitly **NOT run** — Stage 6's own scope note: "the experiment's primary prediction (A1/A2 patch contrast with C1 and the A_lin clause) is Phase B work and remains OPEN" (`NOTEBOOK.md:1547-1552`).

Phase B's job is exactly that remainder.

## Two instrument gaps found while deriving this plan (STOP, not mine to fill)

These surfaced from reading the pinned scripts directly, not from the
dispatch summary, and neither is something a harness-builder should patch:

**Gap 1 — no producer script for the G0-C1 precondition measurement.**
`gates.yaml g0_c1_precondition_control` (line 204) requires, on the **FIT**
split, C0 vs C1 with no injection: (a) undosed `not_well_formed_correct`
delta ≤0.05 abs + Wilson-difference check, (b) C1 undosed confab
`clean_tighten` ≤0.05, (c) teacher-forced mean per-token NLL within 10% of
C0's. `rollup.py:402-407` unconditionally reads
`analysis-committed/gemma4-e4b/c1_precondition_summary.json` with shape
`{"c0": {"known_correct_cost_control": {...}, "mean_nll": float}, "c1": {"confab_tighten": {...}, "known_correct_cost_control": {...}, "mean_nll": float}}`
and raises `RollupInputMissing` if absent — this is confirmed by reading
`build_rollup()` directly, not inferred. **No script anywhere in this
experiment directory, nor in the wider repo (`grep -rl mean_nll`/
`c1_precondition_summary` from repo root), computes this.** `cell.yaml
pipeline_stages` (lines 431-444) never lists a C0/C1 stage at all — the arms
`C0`/`C1` are registered in `cell.yaml arms` (site_hs: null) but no stage
produces their data. `run_contrast.py --arm-kind undosed` (the only existing
undosed-pass driver) always runs the **held-out** split
(`selected_rows()` → `pl.load_rows(family, role, "held_out")`,
`run_contrast.py:80-87`) and computes no NLL at all — it cannot satisfy
gates.yaml's FIT-split + NLL requirement even if pointed at a site-set.
Consequence: Stage B-C1 below is **BLOCKED** until the lead authorizes and a
producer script lands (repin, not this agent's call). Because
`g0_c1_precondition_control` gates A2/A4 being scored on held-out
(`gates.yaml:245`, "on_fail... A2 and A4 recorded NOT-RUN"), and because
`build_rollup()` raises before emitting ANY arm table if the C1 file is
missing, **the terminal `rollup.py` stage is also blocked** until this
lands, even though A1/A3/A5/D1-D4 already have or will have real numbers.

**Gap 2 (resolved, not actually a gap) — G0-ALIN Part 2.** `cell.yaml`'s own
`integration_status.missing` (line 458) still says "alin_sweep.py
--both-conditions ... NOT YET IMPLEMENTED", but reading `alin_sweep.py
--help` directly shows `--site`/`--both-conditions` are now implemented
(plus `test_alin_sweep_part2.py`, a dedicated CPU-only test file, exists).
`cell.yaml`'s comment is stale, not the code. Confirmed runnable as
`alin_sweep.py --site 38 --both-conditions --emit-selection`, gated only on
the OFF extraction (Stage B2 below) existing first.

## Derived stage list

Gate column names the pre-stated check from `gates.yaml`/`AMENDMENT.md`
that must clear (or that the stage exists to compute) before the next
dependent stage runs. "existing script" = verified via `--help` against the
pinned file; "MISSING" = Gap 1 above.

| # | Stage | Command (pinned CLI, verified via `--help`) | GPU? | Depends on | Gate / purpose |
|---|---|---|---|---|---|
| B0 | G0-KV re-verify in the Modal image | `kv_seam_preflight.py` | no (CPU-only per its own persistence declaration) | image build | Re-run inside the tf550-equivalent Modal image so the 6/6 PASS provenance is tied to *this* image's digest too, not only the local one (`AMENDMENT.md:599-671`, `NOTEBOOK.md:1041-1053` precedent). Cheap; do this even in the dry-run. |
| B1 | OFF anchor extraction, midband | `extract_anchor.py --family gemma4-e4b --site-set midband --kv-sharing off` | **yes** | B0 | Feeds A1/A2 direction fits at hs38 and G0-ALIN Part 2 (`cell.yaml:440`, `AMENDMENT.md:780-798`). Writes condition-scoped `anchor_extract.kv_off.safetensors` + manifest under `analysis/gemma4-e4b/`. |
| B2 | OFF anchor extraction, seam_pair | `extract_anchor.py --family gemma4-e4b --site-set seam_pair --kv-sharing off` | **yes** | B0 | Feeds A4 (hs22 OFF) direction fit. Not explicitly named in `cell.yaml pipeline_stages` (that list only shows one generic `--site-set <set>` line) but required by `readouts.refit_policy` (`cell.yaml:239-244`) for the A4 arm to exist at all. |
| B3 | G0-ALIN Part 2 (discrimination) | `alin_sweep.py --site 38 --both-conditions --emit-selection` | no (CPU-only, reads cached safetensors) | B1 | `gates.yaml g0_alin_discrimination_measurement` / `AMENDMENT.md:780-811`. Produces `alin_part2_discrimination.json`, the `|A_lin(hs38,OFF) - A_lin(hs38,ON)| <= 0.05` band that makes A1-vs-A2 discriminating at all. **Must be re-run under the Modal image even though the ON-side number could in principle be read from the existing local cache**, per Revision condition (2): the ON side is re-measured alongside OFF so the comparison never straddles GPU architectures. |
| B-C1 | G0-C1 precondition control | **NO PRODUCER SCRIPT — BLOCKED (Gap 1)** | — | — | `gates.yaml g0_c1_precondition_control`. Must complete, and PASS or FAIL, before A2/A4 are scored on held-out (`gates.yaml:209`, "before any OFF arm is scored on held-out"). Reported to the lead as the top open item; not stubbed by this harness. |
| B4 | A1 direction fit (hs38, ON) | `build_directions.py --family gemma4-e4b --site-set midband --kv-sharing on` | no (CPU, no checkpoint load — same class as Phase A's `gate_fit.py`, `cell.yaml:456`) | none (uses parent's existing ON anchor cache) | A1 was **not** run in Phase A (`NOTEBOOK.md:1547-1552`); it refits fresh per `AMENDMENT.md:448-472`/"Open questions" #1, not reused from the parent's corrupt-derived hs38 artifacts. |
| B5 | A2 direction fit (hs38, OFF) | `build_directions.py --family gemma4-e4b --site-set midband --kv-sharing off` | no | B1 | `readouts.refit_policy` (`cell.yaml:239-244`, `AMENDMENT.md:505-522`): OFF residual stream is a different distribution, must refit its own `u_d`/`c_hat`. |
| B6 | A4 direction fit (hs22, OFF) | `build_directions.py --family gemma4-e4b --site-set seam_pair --kv-sharing off` | no | B2 | Same rule, A4. |
| B7 | Gate fits, all three of B4-B6 | `gate_fit.py --site-set {midband,midband,seam_pair} --kv-sharing {on,off,off}` (3 invocations) | no | B4/B5/B6 | `g0_arm_instrument_validity.ku_readout_gate_floor`: AUC ≥0.90 or that arm is a NOT-RUN (`gates.yaml:256-263`). |
| B8 | A1 dose calibration | `calibrate_dose.py --family gemma4-e4b --site-set midband --kv-sharing on` | **yes** | B7 | `g0_arm_instrument_validity.dose_viability` (`gates.yaml:266-272`). Also recalibrates the late-reference site per the site-set's unconditional `hs_list += [late_reference_hs]` behavior (`cell.yaml:499-512` precedent). |
| B9 | A2 dose calibration | `calibrate_dose.py --family gemma4-e4b --site-set midband --kv-sharing off` | **yes** | B7 | Same gate, OFF condition. Doses are NOT transferable across conditions (`calibrate_dose.py --help`, `--kv-sharing` note). |
| B10 | A4 dose calibration | `calibrate_dose.py --family gemma4-e4b --site-set seam_pair --kv-sharing off` | **yes** | B7 | Same gate, seam_pair/OFF. Also produces an OFF dose for hs24 as a structural byproduct of the site-set (not a registered arm; not reported as one, matching the Phase A A6/D4 coincidence precedent, `cell.yaml:123-135`). |
| B11 | A1 smoke (n=8) | `run_contrast.py --family gemma4-e4b --site-set midband --kv-sharing on --mode smoke --n-rows 8 --i-know-this-is-the-cross-family-run` | **yes** | B8 | `g0_arm_instrument_validity.smoke_no_collapse` (`gates.yaml:275-276`) — stop-before-outcome, per Phase A Stage 1 precedent (`NOTEBOOK.md:1060-1068`). |
| B12 | A2 smoke (n=8) | same, `--kv-sharing off` | **yes** | B9 | Same gate. |
| B13 | A4 smoke (n=8) | same, `--site-set seam_pair --kv-sharing off` | **yes** | B10 | Same gate. |
| B14 | A1 full (held-out) | `run_contrast.py --site-set midband --kv-sharing on --mode full --i-know-this-is-the-cross-family-run` | **yes** | B11 | `g1_actuation_floor` / `g2_selectivity_cap` (`gates.yaml:283-301`). **Not gated by C1** — C1 only governs the OFF arms (`gates.yaml:207`, "Governs the SHARING-OFF arms ONLY (A2, A4)"), so A1 can run even while B-C1 is blocked. |
| B15 | A1 undosed baseline | `run_contrast.py --site-set midband --kv-sharing on --mode full --arm-kind undosed --i-know-this-is-the-cross-family-run` | **yes** | B14 | G2 companion `undosed_floor` (`gates.yaml:373-378`); G3 has no placebo counterpart at hs38 so this is descriptive only here. |
| B16 | A2 full (held-out) | `run_contrast.py --site-set midband --kv-sharing off --mode full --i-know-this-is-the-cross-family-run` | **yes** | B12, **B-C1 PASS** | Primary contrast half 2. `gates.yaml:245`: if C1 fails, this arm is recorded NOT-RUN instead of executed. **Do not launch B16 before B-C1 resolves.** |
| B17 | A4 full (held-out) | `run_contrast.py --site-set seam_pair --kv-sharing off --mode full --i-know-this-is-the-cross-family-run` | **yes** | B13, **B-C1 PASS** | Same C1 gating (`gates.yaml:245`, A4 named explicitly). |
| B18 | A2/A4 undosed baselines | `run_contrast.py --mode full --arm-kind undosed --kv-sharing off` at `--site-set midband` and `--site-set seam_pair` | **yes** | B16, B17 | G2 companion `undosed_floor` for the OFF arms. |
| B19 | ~~Fired-only G2 companion, standalone~~ — **not a real stage** | — | — | — | Corrected after checking: `python3 g2_companion.py --help` prints nothing — the file has no CLI/argparse, it is a pure library module `pipeline.py`/`run_contrast.py` import and call internally. The companion numbers (`fired_only`, `undosed_floor`, the discrepancy flag) are already embedded in every `full_summary.*.json` B14/B16/B17/B18a/B18b produce (matches the shape already visible in Phase A's Stage 2 output). No separate dispatch needed; removed from the harness's stage registry. |
| B20 | Terminal rollup | `rollup.py` | no | B3, **B-C1**, B7, B14-B18 | **BLOCKED** until Gap 1 lands — `build_rollup()` raises `RollupInputMissing` on the missing C1 file before producing any output at all, per direct reading of `rollup.py:401-408`. |

## Arms this plan does NOT touch (already resolved, correctly out of scope)

A3, A5, A6/D4, D1-D3, P1/P2 — all Phase A, all complete or dispositioned
(NOT-RUN / FAIL / PASS as recorded in `NOTEBOOK.md` Stage 6). Re-running any
of them would be exactly the kind of goalpost/scope drift this harness is
built not to do.

## What "site-set midband" actually runs

`families/gemma4-e4b.yaml band_selection.midband_candidates_hs = [34, 38,
42]` (line 113-116) plus the late reference (`hs_list += [late_reference_hs]`
unconditionally per the Phase A `seam_pair_dose_calibration` carve-out
precedent, `cell.yaml:499-512`). So B1/B4/B5/B8/B9/B11/B12/B14/B15/B16 each
compute all of hs34/hs38/hs42(+hs40) as a byproduct of the site-set, not
hs38 alone — **only hs38 is A1/A2**; hs34/hs42/hs40 results are descriptive
byproducts (matching the seam_pair set's hs24-alongside-hs22 precedent) and
must not be read as additional registered arms.

## Data that must be staged to Modal (private, gitignored, never in git)

Read from the pinned scripts directly (`pipeline.py:104`,
`run_contrast.py`'s model load path), not assumed:

| File | Path (local) | Size | sha256 |
|---|---|---|---|
| Row-text pool | `analysis/gemma4-e4b/eval_rows.jsonl` | 208 KB | `7a2784bd883ed622fa138956e722db0353c8a3f96ed7f914a144908d01ddecc7` |
| ON anchor activations | `analysis/gemma4-e4b/anchor_extract.safetensors` | 342 MB | `b7197418476208a3657f98026932fbf5e2c5aa4306a82844040ab50d99fbe7bf` |

`PROVENANCE.md` (`experiments/common/artifacts/jspace-cross-family-gemma4-e4b/PROVENANCE.md`)
confirms both are deliberately **not** promoted/committed and must stay
private. Everything else Phase B needs (pinned `.py` modules, `families/`,
`cell.yaml`, `gates.yaml`, the promoted `split_manifest.json`/
`eval_pool_manifest.json`, and Phase A's committed `analysis-committed/`
artifacts, ~4 MB total) is already tracked in git at the current EHR `main`
HEAD (`4c49f9b2cf32ce17de527485a71471bc81affbde`, submodule
`synaptic-tuner @ 34c89fc4f9d693a6b997422288d820e9c30b4696` — already the
pin this experiment needs, no repin required) and is cloned straight into
the container, matching the AK/AP precedent pattern.

**Not staged by this agent.** Uploading `eval_rows.jsonl` (question text +
aliases) and `anchor_extract.safetensors` to even a *private* HF staging
repo is data leaving the local machine — containment-adjacent and
irreversible-ish (a private repo can still be over-shared or leaked). The
upload helper is written (`cloud/stage_private_inputs.py`) but not invoked;
it is a lead-authorized step at launch time, same posture as the GPU launch
itself.

## Falsifier/disposition bookkeeping this run resolves (restated, not reinterpreted)

Per `AMENDMENT.md` "Falsifier" (line 929) and `NOTEBOOK.md:1635-1642` (R9):
D1 already cleared G1 in Phase A. Going into Phase B:
- If A1 (hs38, ON) clears G1 → **VOID** (parent null failed to reproduce).
- If A1 fails G1 (reproducing the parent's null) and A2 clears both gates
  with the `A_lin` band satisfied → prediction MET, KV-quarantine
  **supported**.
- If A1 fails G1 and A2 also fails (with C1 having passed and A2's write
  verified) → combined with A3's Phase-A pass this does NOT complete the
  registered falsifier as literally stated (falsifier requires A3 to ALSO
  fail — it did not), so a joint A1-fail/A2-fail outcome here is reported as
  "prediction not met" without triggering the registered FALSIFIED
  disposition. This is a re-statement of the pre-stated rule, not a new
  interpretation — flagging only because it is easy to misread as
  "falsified" from B14/B16 alone.
- If C1 fails → A2/A4 are NOT-RUN, experiment resolves INCONCLUSIVE on the
  A1/A2 axis (`gates.yaml:244-249`).

This adjudication is the lead's at resolve, not asserted here.
