# Cross-family raw-refusal actuation at atlas-located workspace-band sites notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

- 2026-07-13 (RENDER-ENV-VAR FIX): the anchor-extraction-fixed relaunch got
  past materialize and into `dose_ladder.py`'s first layer sweep, then
  crashed: `render.py`'s `_tokenizer()` raised `RuntimeError("RR_RENDER_MODEL
  must name the HF tokenizer repo")` on the first row. `render.py` (ported
  in the original harness build) reads its model/revision from
  `os.environ["RR_RENDER_MODEL"]`/`["RR_RENDER_REVISION"]` by design, so its
  render cache can never collide with the sibling
  doubt-snap-cross-family-confirmatory experiment's own render module if
  ever imported in the same process -- but neither `dose_ladder.py` nor
  `heldout_scorer.py` ever SET those env vars anywhere. This is a genuine
  gap in the original harness build, not a locked-spec issue: the CPU smoke
  suite never exercised `render.py` at all (it wasn't in the smoke suite's
  import list), so this only surfaced at real launch. Fixed at the single
  point both callers already share: `steer_lib.load_model()` now sets
  `RR_RENDER_MODEL`/`RR_RENDER_REVISION` to the SAME `model_name`/`revision`
  it is about to load, right before loading, so the two can never drift
  apart or be forgotten by a future caller. Added
  `test_load_model_sets_render_env_vars` (mocks
  `transformers.AutoTokenizer.from_pretrained`/
  `AutoModelForCausalLM.from_pretrained` so this stays CPU-only and
  network-free) to the smoke suite. 38/38 green. Repinned `steer_lib.py` and
  `test_rr_smoke.py`.
  Process-management note: the relaunch that hit this crash was itself a
  relaunch of an EARLIER attempt that appeared dead (no process, empty GPU)
  when checked, but had in fact not yet exited -- its orphaned
  `dose_ladder.py` child (reparented after its own `pipeline.py` parent
  exited) was still working through model download/load and only crashed
  on this same bug later, writing its traceback into the just-truncated
  `run_llama.log` moments after the new relaunch's own banner line, which
  briefly looked like log corruption before the process list resolved it.
  Both the stale orphan and the second relaunch (started before this fix
  landed, so doomed to hit the same crash once it reached generation) were
  killed before the clean, post-fix relaunch below.

- 2026-07-13 (ANCHOR-EXTRACTION FIX): llama launch bounced in 1 second:
  `dose_ladder.py` exited on `missing analysis/llama/
  anchors_at_candidate_layers.json`. The materialize module's docstring and
  the anchor_coverage note both said this file was a "GPU capture step,
  deferred" -- that premise was true only until staging landed. Once the
  stager pulled the full atlas captures locally (both families staged with
  `--layers all`, coverage 1.00, confirmed via the atlas's own
  `atlas_capture/capture.jsonl`), extracting the candidate-layer anchors out
  of those already-captured tensors is a pure CPU slice, not a GPU step: the
  layers this cell needs are already sitting in the staged safetensors
  files. Added `extract_anchors_at_candidate_layers()` to
  `materialize_rows.py` (wraps the existing `load_anchor_tensors`, which
  already raises loudly on any row or candidate-layer key missing from the
  staged capture) and wired it into `cmd_materialize`'s success path, right
  after `check_anchor_coverage` passes: writes `analysis/<family>/
  anchors_at_candidate_layers.json` (private, gitignored, one entry per
  joined row, `{row_key: {str(layer): [float, ...]}}`, the exact schema
  `dose_ladder.py` and `heldout_scorer.py` already read) and records
  `anchors_extracted` (row-count parity with the joined pool) in both the
  private `materialize_report.json` and the committed `materialize_manifest.json`
  aggregate. `matches_joined_pool` is asserted, not just reported: a
  mismatch raises `SystemExit` before any file is written, since given
  `load_anchor_tensors`' own semantics that should be unreachable and would
  flag a real wiring bug, not a data gap.
  Ran for real against the now-staged inputs: llama 2956/2956 rows
  extracted at layers [20, 22, 23] (516 MB `anchors_at_candidate_layers.json`,
  ~62 s of file I/O across 2956 per-row safetensors files); mistral
  extraction launched the same way (see the launch report for its own
  count). This step is a one-time-per-family cost paid once during
  materialize, not on every dose-ladder or held-out invocation.
  CPU smoke extended: `test_extract_anchors_at_candidate_layers_writes_expected_schema`,
  `..._raises_loudly_on_missing_row`, `..._raises_loudly_on_missing_layer`
  (synthetic safetensors fixtures via `safetensors.numpy.save_file`), and
  `test_materialize_full_success_path_writes_anchors_at_candidate_layers_json`
  (end-to-end wiring on a tiny synthetic split, `check_heldout_power`
  monkeypatched to bypass the real 150/250 floors so the fixture stays
  small -- those floors are already covered for real elsewhere). 37/37
  green (`python3 -m pytest test_rr_smoke.py -v`). Repinned
  `materialize_rows.py` and `test_rr_smoke.py` in `experiment.yaml` via
  `bin/exp repin` (both were already in `instrument.pins`; their content
  changed, their hashes did not exist before this fix). No changes to
  cell.yaml or gates.yaml.

- 2026-07-13 (POST-SIGN REPAIR + BUILD REVIEW): lead review of the harness
  build (commit c12e0578, 11 modules + 33-test CPU smoke all green). The
  builder's seven adjudications are ACCEPTED, including the layer-index
  convention resolved empirically against the atlas per-layer AUROCs and
  the H4 metric-hygiene split on the dose_knowns_ungated arm. Repair owned
  by the lead: cell.yaml went through sign with four literal PLACEHOLDERs
  (both family revisions, synaptic_tuner_pin, gpu_python), a sign-time gap
  the builder correctly flagged and refused to edit. Resolved now via
  bin/exp repin (audit trail in instrument.repins): llama revision
  006f5dcd... and mistral revision c170c708..., both lead-verified against
  the fleet model_matrix.yaml SSOT and matching what the harness's
  resolve_revision() live-read returns; tuner pin 86b134c3 (worktree
  submodule commit); gpu python = base conda. No threshold, arm, dose, or
  gate content changed. Also carried forward: the qwen35-4b-midband-heldout
  AMENDMENT is cited by doc:line but unmerged (sibling branch); its input
  line is added once that branch merges, same pattern as the closed A2.
  Launch preconditions remaining: stage the private row pools
  (analysis/staged_inputs/<family>/split_rows_private.jsonl) and the atlas
  full-depth anchor captures per family (currently Modal-side only), then
  a smoke probe run for a wall-time bracket, then the full FIT ladder;
  local 3090 after the H3 confirmatory run frees the card.


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

## 2026-07-13 - Launch incident: dual-launch collision, quarantine, clean relaunch (lead)

Instrumentation-hygiene record, pre-gates; no protocol surface touched.

After the anchor-slice fix (54cf836a), the llama cell was accidentally
launched TWICE: the builder relaunched detached (setsid nohup, correct
mechanics) but went idle without reporting, its process was not visible to
the lead's process checks, and the lead then launched a believed-takeover
run. Both processes swept the same FIT ladder grid and appended interleaved
rows to the same RunLog files under analysis/llama/runlog/ (visible
signature: duplicated progress lines and one rung's log at roughly twice
sibling size). The lead's process crashed on the resulting tmp-file race in
run_log.finalize (FileNotFoundError on hs20__gated__dose20 summary rename);
the builder's process survived but its on-disk ladder artifacts were
cross-contaminated.

Resolution: surviving process killed by exact PID (307649 pipeline,
308800 dose_ladder, identities verified via /proc cmdline); every
ladder-derived artifact quarantined by rename (nothing deleted) to
analysis/llama/quarantine-dual-launch-20260713/ (runlog/, run_llama.log,
run_llama.pid, and analysis-committed/llama/hs20_fit_build_manifest.json,
which was written during the contaminated window); deterministic
materialize products (anchors slice, joined rows, manifests) kept in place
for the rerun to verify/rewrite. A single clean run was then relaunched by
the lead with the HF transfer guards. No gate, threshold, dose grid, or
registered text changed; no contaminated number was read as a result.

Standing correction adopted: on this lane the lead owns all launches, and a
detached launch is not complete until its PID/log/liveness report lands
before the launching agent goes idle.
