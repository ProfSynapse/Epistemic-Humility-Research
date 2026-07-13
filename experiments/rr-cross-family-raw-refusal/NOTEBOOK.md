# Cross-family raw-refusal actuation at atlas-located workspace-band sites notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

- 2026-07-13 (HARNESS BUILD): CPU-only build and smoke, GPU launch deferred
  until the local 3090 frees after H3. Modules written and sha256-pinned in
  `experiment.yaml` (`instrument.modules`/`instrument.pins`): `render.py`,
  `grader.py`, `gen_lib.py`, `direction_fit.py`, `materialize_rows.py`,
  `steer_lib.py`, `dose_ladder.py`, `heldout_scorer.py`, `gates_lib.py`,
  `pipeline.py`, `test_rr_smoke.py`. `bin/exp validate`: OK. Smoke:
  `python3 -m pytest test_rr_smoke.py -v` -> 33 passed, 0 failed. No changes
  to AMENDMENT.md, cell.yaml, or gates.yaml. Build-time adjudications:
  - **Layer-index convention (cell.yaml `candidate_layers`).** cell.yaml
    itself defers this to harness-build. Resolved empirically against
    `experiments/jspace-family-atlas/analysis-committed/*/atlas_summary.json`:
    `per_layer["0"]` reads exactly 0.5 AUROC (chance) on every axis in both
    families, the embedding-layer signature, and `per_layer["20"]` (llama) /
    `per_layer["17"]` (mistral) reproduce the AMENDMENT's own cited
    raw_refusal numbers exactly. This proves `candidate_layers` is in the
    `output_hidden_states=True` tuple convention (index 0 = embeddings,
    index N = decoder block N's output), matching the atlas's `per_layer`
    keys and the ladder's `anchor__L{N}` tensor-key convention. The harness
    hooks decoder block `hs_index - 1` (`materialize_rows.py:
    decoder_block_index`) for any candidate layer, not `hs_index` directly.
  - **cell.yaml `revision` field is still a literal placeholder.** The
    AMENDMENT states revisions are "transcribed into cell.yaml ... at sign,"
    but the sha-pinned cell.yaml's `families[].revision` is literally the
    string `PLACEHOLDER(from fleet model_matrix.yaml at sign)` for both
    families, a sign-time process gap, not something this build is
    authorized to fix by editing the locked file. `materialize_rows.py:
    resolve_revision()` reads the real revision live from the fleet's own
    `model_matrix.yaml` every run instead, with a check that would flag a
    mismatch if cell.yaml's field were ever filled with a real value that
    disagreed with the fleet's. Flagging for the lead: cell.yaml's
    `revision` field should be repinned with the real hashes at the next
    `bin/exp repin` opportunity, since this harness does not depend on the
    field but a future reader would be misled by the placeholder text.
  - **Broken-looking citation, actually an unmerged sibling.**
    `experiments/qwen35-4b-midband-heldout/AMENDMENT.md` is cited three
    times (AMENDMENT.md:361, :462; gates.yaml:61) and does not exist in
    this worktree or on `main`. It does exist on branch
    `exp/qwen35-midband-heldout` in the sibling worktree
    `/home/profsynapse/code/ehr-worktrees/qwen35-midband-heldout`
    (HEAD f1f7dffd, unmerged), and the cited line ranges (159-168, 262-269)
    match the wall-time estimate and G1 threshold prose respectively. Same
    class of gap as adjudication A2 (H4 before PR #281 merged). Does not
    block this build: gates.yaml's own G1/cost thresholds (0.60 LCB > 0.50,
    well-formed >= 0.80, cost <= 0.05 UCB < 0.10) are fully self-contained
    numerically and do not require reading the cited doc at runtime. Flagged
    for the lead to add the input line once that branch merges, mirroring
    A2's resolution pattern.
  - **Execution model: direct Python driving, not the declarative
    `mechinterp steer` recipe.** Ported the ladder's own precedent
    (`run_dose_ladder.py`): `InterventionHook`/
    `GenerationInterventionController`/`RunLog` driven directly from
    `steer_lib.py`/`dose_ladder.py`/`heldout_scorer.py`, not
    `prep_tuner_cell.py: materialize_dose_sweep`'s YAML-recipe path. Neither
    the AMENDMENT nor cell.yaml specifies an execution model; this mirrors
    the most recent same-mechanism precedent (`qwen35-4b-midband-doubt-snap`)
    rather than the older `doubt-snap-cross-family-confirmatory` path.
  - **Staged private inputs are absent from this worktree.** Neither the
    fleet row pool (`split_rows_private.jsonl`) nor the atlas's full-depth
    anchor captures exist locally; both ran on Modal and were never staged
    here. `materialize_rows.py: cmd_materialize()` detects this cleanly
    (`row_pool_path.is_file()`, `(capture_dir / "capture.jsonl").is_file()`)
    and writes `materialize_precondition_report.json` naming the exact
    expected paths and staging instructions, rather than crashing opaquely
    or fabricating rows. The parts that CAN be checked without the private
    data (held-out-power counts against the atlas's committed, ID-only
    `split_manifest.json`) run for real and match cell.yaml's registered
    872/334 (llama) and 1312/382 (mistral) counts exactly.
  - **FIT operating-point selection.** `gates_lib.py:
    select_fit_operating_point()` implements the AMENDMENT's dose-policy
    part 3 ("the (layer, dose) with the LOWEST dose whose FIT ...") as a
    pool across every candidate layer, not a layer-by-layer-first search:
    it takes the minimum `dose_abs` among all `viable` (layer, dose) grid
    points regardless of which of the 3 candidate layers produced it.
    Returns `None` (shape F) if no grid point is FIT-viable.
  - **`dose_knowns_ungated` metric-hygiene separation.** Per the AMENDMENT's
    honest-scope statement (carried from H4 binding scope statement 1),
    `heldout_scorer.py` reports `clean_false_refusal` (the `refused` rate,
    comparable to the gated cost metric) and `total_damage_rate` (the
    broader `not_well_formed_correct` rate) as two SEPARATE fields with an
    explicit `metric_hygiene_note`, and never combines them into one number.
  - **No CUDA_LAUNCH_BLOCKING requirement.** Unlike the Qwen3.5 ladder
    (whose substrate used hybrid linear-attention blocks with a slow
    PyTorch fallback that motivated synchronous CUDA debugging), both RR
    substrates (Llama-3.2-3B, Mistral-7B-v0.3) use standard attention;
    `steer_lib.py` does not impose the env var, and nothing in cell.yaml or
    gates.yaml asks for it.
  - No dataset/pool/question/generation/answer text is present in any
    committed file; `analysis/` and `directions/` remain gitignored and, as
    of this build, do not yet exist locally (no real data has been
    materialized).

- 2026-07-13 (SIGNED): both scoreboard predictions recorded (user: both
  families shape A; orchestrator: exactly one family shape A, lean mistral,
  other B or F) and the amendment signed. PR #281 merged earlier today, so
  the H4 input line is in experiment.yaml (adjudication A2 closed). The five
  lead-review rulings from the pre-sign entry stand unchanged; the PI did
  not elevate the selectivity-on-knowns characterization to a hard gate
  (A4 stays reported-not-gated). Harness build commissioned at sign; launch
  on the local 3090 (free lane) after the H3 confirmatory run frees the
  card. Any paid lane still requires fresh user approval per the Lane
  section.


- 2026-07-13 (LEAD REVIEW, pre-sign): draft reviewed against the drafter's
  report; structure, gate table, and coverage table verified against the
  committed files. Rulings on the five open adjudications:
  (A1) SUBSTRATES: Llama-3.2-3B + Mistral-7B-v0.3 ACCEPTED. The lead's task
  message sized an 8B llama, but no atlas-located site exists for any 8B
  llama; written-at-their-own-atlas-site is the binding design requirement,
  so the atlas-mapped 3B stands and no atlas extension is authorized now.
  (A2) H4 INPUT: omission from experiment.yaml inputs ACCEPTED while
  ungated-vs-gated-dose-matched sits on its unmerged branch; the input line
  is added at sign once PR #281 merges (validator enforces path existence).
  (A3) ARMS: the four registered arms stand; permuted_gate is NOT added.
  The core RR question is actuation transfer, and dose_knowns_ungated is
  the directly motivated selectivity control given H4's operating-point
  dependence result. A permuted-gate ownership test at these sites is
  named as a possible follow-up if a family lands shape A, never bolted on
  here. (A4) SELECTIVITY-ON-KNOWNS stays reported-not-gated: the sign of
  the effect at a third operating point is unknown a priori, and gating it
  would conflate the existence question with the ownership question. The
  PI may elevate it at sign. (A5) LAYER BAND: 3 candidate layers per
  family inside the atlas best-read band, leaning earlier, ACCEPTED as the
  middle course between a single-layer bet and a full-band sweep.
  Also acknowledged from the drafter's flags: RR rests only on the atlas
  read-panel layer map and readability demonstration, never on the atlas's
  failed eff_dim prediction or any atlas actuation claim. Next steps in
  order: PR #281 (H4) merges, H4 input line added, PI fills the scoreboard,
  lead countersigns, harness-build assignment, lane decision at staging
  (local 3090 preferred; any paid lane needs fresh user approval).


### 2026-07-13 DRAFT (design specialist)
- Scaffolded via `bin/exp new --type steer-cell rr-cross-family-raw-refusal` on a
  fresh worktree branch `exp/rr-cross-family-raw-refusal` off origin/main.
- This is the successor design the `doubt-snap-cross-family-confirmatory` Outcome
  demanded (that doc :331-339): write at the per-family atlas-located site, not
  the ported round(0.94*(L-1)) late site, and register exterior-shaped outcomes
  so a uniform FIT-stop cannot fall between prediction and falsifier.
- Substrates are the two atlas-mapped models only: Llama-3.2-3B-Instruct and
  Mistral-7B-Instruct-v0.3 (jspace-family-atlas :40-41, :184-185). There is no
  atlas-located site for an 8B llama, so the lead's 8B lane note cannot be honored
  without an atlas extension first (open adjudication A1).
- Primary metric is the format-agnostic `refused` rate (ladder readout b,
  qwen35-4b-midband-doubt-snap :218-227); well-formed reported and gated alongside.
- Coverage table A-F: A = clean actuation (prediction); B-F = falsifier; F = the
  FIT-dose-viability non-actuation shape (confirmatory stop territory, now on the
  table). Gate template mirrors the Wilson-bounded held-out stage.
- H4 (ungated-vs-gated-dose-matched, ALL GATES PASS 2026-07-13) is cited by
  doc:line but is not on main yet, so it is omitted from experiment.yaml `inputs`
  (validator enforces path existence); add at sign once H4 merges (open
  adjudication A2).
- Predictions scoreboard left EMPTY for the PI and lead to fill at sign.
- No harness code written; harness build is a separate assignment gated on review.
- `bin/exp validate`: OK.
