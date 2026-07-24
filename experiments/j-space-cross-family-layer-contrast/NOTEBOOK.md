# j-space-cross-family-layer-contrast notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

### 2026-07-23 -- launch G0 crash diagnosis: two dead render() imports, one PYTHONPATH fix + one vendored shim (CPU-only diagnosis, no GPU work counted toward outcome; pending lead repin before relaunch)

llama-3.2-3b's `extract_anchor.py` crashed at G0 (`model_lib.py`'s `render()`)
with two sequential `ModuleNotFoundError`s, both caused by an UNRELATED prior
main-branch reorg archiving files this experiment's pinned `model_lib.py`
imports by bare module name via a hardcoded `sys.path` entry
(`PROBE_DIR = .../experiment/phase1/probe`). Neither import target still
lives at that path.

1. **`backends.render_probe_prompt`** -- `experiment/phase1/probe/backends.py`
   was archived; the archive copy is a dead compat wrapper pointing at a
   nonexistent `experiments/common/phase1_probe/`. FIXED via environment only
   (no code/file changes): `PYTHONPATH=/home/profsynapse/code/
   Epistemic-Humility-Research/experiments/common/knowledge_probe` added to
   every pipeline invocation. That directory's `backends.py` is the live,
   actively-maintained successor with an IDENTICAL
   `render_probe_prompt(tokenizer, system_prompt, question, *,
   enable_thinking, mode=None)` signature (verified by CPU-only import +
   `inspect.signature`), explicitly documented there as the shared render
   path for "the hidden-state harness" too.
2. **`amendment_ah_stage0_extract.load_baseline_system_prompt`** -- NOT
   env-fixable: the only surviving copy is archived
   (`archive/experiment/phase1/probe/amendments/`), hardcodes a config
   filename (`experiments/doubt-regulated-caution/
   phase3_ac_doubt_coupled_intervention.yaml`) that no longer exists at that
   path (renamed via `git log --follow`: moved by commit 6b66536a, then
   dropped the `phase3_` prefix by commit d55b7d26 -- `git show d55b7d26` on
   that file confirms the `prompt:` block itself is untouched in that patch),
   and its sibling archived `path_compat.py` is independently broken (its
   `repo_root()` heuristic depends on `experiment/phase1/eval/scorers.py`,
   itself archived by the same reorg that broke this experiment's own
   `grader.py` `EVAL_DIR`, already fixed by vendoring `scorers.py` at
   sign-time -- see the entry below). The live successor `path_compat.py`
   (`experiments/common/readouts/`) fixes the `repo_root()` check but drops
   the `phase1_probe_dir()`/`phase1_eval_dir()` names the archived script
   imports -- an API mismatch on top of the dead filename, not just a stale
   search path. Lead-adjudicated 2026-07-23: vendored a minimal shim,
   `amendment_ah_stage0_extract.py`, into this experiment directory (sibling
   convention, matching the `scorers.py` precedent) that supplies ONLY
   `load_baseline_system_prompt()`, reading the renamed live yaml
   (`experiments/doubt-regulated-caution/ac_doubt_coupled_intervention.yaml`
   `prompt.system`) and FAIL-CLOSED asserting its sha256 equals a hardcoded
   `_EXPECTED_SHA256` (`81a04a99827ade21b9d5bd1832c2012429d196f96e604238a4b927701ca58e3c`)
   computed at shim-authoring time -- a future edit to that yaml's
   `prompt.system` will raise instead of silently changing what every
   family's generation renders. Smoke-tested both the happy path and the
   fail-closed mismatch path (CPU-only, deliberately corrupted the expected
   hash in-process to confirm it raises).

   **Cross-check (required before trusting this shim for the reused frozen
   late-site arm):** loaded `experiments/doubt-snap-cross-family-
   confirmatory/render.py`'s hardcoded `BASELINE_SYSTEM_PROMPT` literal
   directly (module import, not hand-transcribed) and compared byte-for-byte
   against the shim's yaml-sourced string: **IDENTICAL** -- same sha256
   `81a04a99827ade21b9d5bd1832c2012429d196f96e604238a4b927701ca58e3c` for
   both. This confirms the render convention this shim restores is the same
   one doubt-snap's frozen late-site directions (`c_hat`/`u_d`/`gate_fit`,
   reused verbatim by this experiment) were actually fit under -- resolves
   AMENDMENT.md "Open questions at sign" #5 (render/anchor reconciliation)
   affirmatively for the system-prompt component; anchor position and
   `enable_thinking` convention are separately unchanged (ported verbatim in
   `model_lib.py`/`gen_lib.py`, not touched by this fix).

No pinned-byte edits: `model_lib.py` and every other pinned instrument file
are unmodified. The new shim file is NOT yet part of the signed pin set --
lead is running a governed repin to add it before any GPU relaunch. Did NOT
restart `extract_anchor.py` or any other GPU work pending that repin
confirmation.

### 2026-07-23 -- sign-time revision: primary reframe + doubt-snap reuse (CPU-only, no GPU, NOT signed)

Lead-directed, user-approved structural revision of the draft, after
`doubt-snap-cross-family-confirmatory` RESOLVED (2026-07-12, confirmatory not
promoted -- every launched cell stopped at G0 FIT dose-viability at the late
0.94-depth site; gemma4_e4b_it never behaviorally launched). All predecessor
docs and doubt-snap committed artifacts were read from the canonical `main`
checkout (this worktree is 677 commits behind main and does NOT contain them).

Changes made:
- **Primary endpoint reframed to ABSOLUTE mid-band actuation.** New per-family
  primary gates: G1 mid-band held-out confab clean_tighten floor, G2 mid-band
  known-correct not_well_formed_correct cost cap. The late-reference arm is
  DEMOTED to a non-gating secondary descriptive comparator; the draft's relative
  G1/G2 contrast and the G3 late-viability floor (0.40/0.30) are DROPPED.
  gates.yaml, AMENDMENT.md (Prediction/Falsifier/Gates + new "Gates ->
  derivation" and "Open questions at sign"), experiment.yaml, and
  run_contrast.py/cross_family_rollup.py updated.
- **Gate numbers with written derivation (adjudicated lead+user 2026-07-23,
  conservative option chosen).** G1 = clean_tighten >= 0.50, Wilson lower > 0.40
  (below the weaker same-lineage mid-band held-out point ~0.66 Qwen3.5-4B / 0.89
  Qwen3-4B, far above the dead late-site region <= 0.33; Wilson-lower 0.10 below
  the point, mirroring qwen35-4b-midband-heldout's gate shape). The stricter
  0.60/0.50 alternative was offered and NOT elected. G2 = not_well_formed_correct
  <= 0.05, Wilson upper < 0.10 (inherits qwen35-4b-midband-heldout's cost gate;
  both Qwen substrates cleared at 0.035/0.039).
- **Consumes doubt-snap artifacts, hash-pinned.** Each `families/<slug>.yaml`
  gained a `reuse.doubt_snap` block: committed-artifact relative paths + sha256
  (split_manifest, build_manifest, c_hat, u_d, random_direction, gate_fit,
  dose_fit, g0_prep_summary), Modal volume + path, frozen late-site params
  (block/hs_index, tau_frozen, mu_c/sigma_c/mu_d/sigma_d), FIT/held-out counts.
  New `materialize_reused_rows.py` replaces mine_eval_pool.py + split_fit_heldout.py
  (retained fallback-only) for the four reused families; family_config.py gained
  reuse accessors; build_directions/gate_fit scoped to mid-band only (late-site
  direction/gate reused frozen, not refit); calibrate_dose sweeps mid-band AND
  the late site (option B -- fresh late-site DOSE, frozen late direction/gate);
  pipeline.py's compute_gate_decisions/run_layer branch the late arm to the
  frozen reuse artifacts. Late reference site is now DEFINED as doubt-snap's
  frozen block (llama 25 / mistral 29 / qwen35-4b 29 / gemma 39; hs_index+1 =
  26/30/30/40 -- coincidentally equal to this experiment's own 0.9444*L estimate).
- **Gemma-4-E4B Modal fallback pre-authorized** (LAUNCH-PLAN.md + AMENDMENT.md):
  local first, Modal fallback for the Gemma cell only on a G0 OOM, NOT-RUN only
  if Modal also fails.

Two artifact gaps found while pinning (flagged as open questions, not guessed
around): (1) NO family has a calibrated late-site dose to reuse (all doubt-snap
cells `selected_dose: null`); (2) gemma4_e4b_it was never behaviorally launched
-- FIT prep is committed but no dose_fit.json/modal_status.json, late gate AUC
0.9472 (weakest), held-out known 251 (~1-row margin). Plus the branch-behind-main
dependency (open question #0) and the Modal-volume row-text retention question
(proven only for the qwen35_4b cell).

**Resolved at finalization (2026-07-23, lead+user).** Gap (1): option (B)
adopted -- the late-site DOSE is calibrated fresh with the mid-band ladder for
all four families (frozen late direction/gate still reused verbatim); see
AMENDMENT.md open question #2. Gate numbers adjudicated (conservative option):
G1 0.50/0.40, G2 0.05/0.10. Branch-behind-main resolved by merging `main`
(submodule pin -> 901dbe8, which already contains `feature/runlog`; no pointer
bump needed). Modal retention checked: llama/mistral/qwen35_4b row text PRESENT,
gemma ABSENT (never launched -> pre-authorized Modal fresh-mine fallback).

**Final pre-sign pass (2026-07-23, lead+user).**
- GEMMA FRESH MINE (adjudicated): gemma's pool/split cannot be reused (row text
  absent), so `pool_provenance: fresh_mine` for gemma ONLY -- mine_eval_pool.py +
  split_fit_heldout.py run fresh on gemma's own checkpoint; reuse provenance for
  the pool is LOST and recorded. The frozen late-site direction/tau/
  standardization stay reused verbatim + hash-pinned, applied to the fresh rows
  as a frozen operating point (qwen35-4b-midband-heldout pattern); late dose
  still fresh (option B). G0 reuse-integrity is scoped per family via
  `family_config.integrity_artifact_names`: reused-pool families verify 8
  artifacts (incl. split_manifest); gemma verifies ONLY the 5 frozen late-site
  artifacts (build_manifest/c_hat/u_d/random_direction/gate_fit). Verified by
  running materialize_reused_rows.py --family gemma4-e4b: 5 late-site hashes
  match, no split copied, rc=0. Other three families' G0 untouched.
- VENDOR SCORERS (adjudicated): the merge pulled main commit 21cd5c50 which
  archived experiment/phase1/eval/scorers.py, breaking grader.py's hardcoded
  EVAL_DIR. Vendored scorers.py INTO the experiment dir (sibling convention, no
  external dependency). BYTE-IDENTITY: archived source
  sha256 75e690f583d83d654cb88a3b066b39acb7e9e1b954c9d5677d4b887d6c30905a; the
  vendored file is a provenance header (891 bytes) + that source VERBATIM, so its
  post-header body sha256 == 75e690f5... (byte-identical), and the full vendored
  file sha256 = 1b3eda5d8d68c9184674f092805278505c5cd2065a21ffe7ec348e9ea5a00c37.
  grader.py now imports the local copy (EVAL_DIR dropped). Import smoke:
  `run_contrast.py --help` and `calibrate_dose.py --help` both exit 0, proving
  the grader -> gen_lib -> pipeline -> run_contrast/calibrate_dose chain resolves.

Verification (CPU-only): `bin/exp validate` OK (after moving the not-yet-present
doubt-snap `inputs` paths into a comment, since validate existence-checks
inputs and this branch lacks main's content); `py_compile` OK on all scripts;
`--help` OK on the no-torch scripts (materialize_reused_rows, cross_family_rollup,
build_directions, gate_fit) and family_config reuse accessors resolve all four
families' pins. Full `--help` of the torch+MechInterp scripts needs the project
`unsloth_env` (pre-existing, unchanged by this revision). Did NOT sign, did NOT
run any model/GPU/Modal work, did NOT touch the 3090 or the synaptic-tuner
submodule. Predictions scoreboard left blank for the lead to fill at sign.

### 2026-07-09 -- tokenizer/config verification pass (CPU-only, no GPU work run)

Resolved LAUNCH-PLAN.md decision points #3 (multimodal config nesting), #4
(EOS lists + layer counts), and #5 (Gemma system-role support) by
downloading ONLY `config.json`/`tokenizer_config.json`/
`special_tokens_map.json`/`generation_config.json`/`chat_template.jinja`
per checkpoint via `hf_hub_download` (never `snapshot_download`, no
`*.safetensors`/`*.bin` touched) for all four checkpoints:
`unsloth/Llama-3.2-3B-Instruct`, `mistralai/Mistral-7B-Instruct-v0.3`,
`Qwen/Qwen3.5-4B`, `google/gemma-4-E4B-it`. All four repos were ungated
(no 403s). Fetch script and cached files live under this experiment's
gitignored `analysis/tokenizer-config-verify/` (fetch script:
`fetch_configs.py`; not tracked, upstream artifacts only).

Also ran a small number of meta-device (`torch.device("meta")`, no weight
download, no GPU) `AutoModelForCausalLM`/`AutoModelForImageTextToText`
construction checks against the downloaded configs to directly test the
multimodal loader-class questions LAUNCH-PLAN.md flagged as unverified
(`attn_implementation="eager"` acceptance, and whether the vision/audio
towers are structurally part of the resolved model class) -- no weights
were downloaded or instantiated with real data for this.

Confirmed: Llama's `n_hidden_layers: 28` guess, Mistral's/Qwen3.5's EOS
guesses, and Qwen3.5's `nested_text_config: true` + `enable_thinking`
kwarg. Filled in previously-`null` layer counts for Mistral (32), Qwen3.5
(32, nested), and Gemma4 (42, nested), each with a recomputed
`round(0.9444 * n_hidden_layers)` late-reference estimate.

Corrected two factually wrong guesses for `google/gemma-4-E4B-it`: (1) its
EOS/end-of-turn token is `<turn|>` (per `tokenizer_config.json`'s own
`eot_token` field and the live chat template), not the classic Gemma
2/3 `<end_of_turn>` the draft assumed; (2) it DOES have a native
`enable_thinking` kwarg (gates a `<|think|>` token injection), contrary to
the draft's "Gemma has no thinking-toggle kwarg" claim. Also resolved
decision point #5 in the affirmative (its template gives `system` its own
turn, not folded into the first user turn -- the flagged concern was
unfounded for this checkpoint) and found it is trimodal (vision + audio
towers, not vision-only) -- both AMENDMENT.md's family table and
`families/gemma4-e4b.yaml` were updated to flag these corrections
prominently. Full detail in each `families/<slug>.yaml`'s per-section
"VERIFIED"/"CORRECTED" notes and LAUNCH-PLAN.md's revised decision points
#3/#4.

Did NOT touch decision point #1 (G3 floor) or the VRAM GB estimates in the
feasibility table (lead-kept); did NOT sign, did NOT run any model
generation, did NOT touch the local 3090.

### 2026-07-09 -- draft scaffold written (no GPU work run)

Scaffolded via `bin/exp new --type steer-cell j-space-cross-family-layer-contrast`
on branch `exp/j-space-cross-family-layer-contrast` (worktree
`/home/profsynapse/code/ehr-worktrees/jspace-cross-family`). Read the six
governed docs the lead named (two Qwen3-4B J-space predecessors, the
localization diagnostic + its NOTEBOOK.md, Amendment Z, and the
doubt-gated-caution-tighten gate-and-snap origin) before writing any code, per
the KG-search-first / read-before-you-cite rule.

Wrote per-family config YAMLs (`families/{llama-3.2-3b,ministral-3-3b,qwen35-4b,gemma4-e4b}.yaml`)
transcribing Amendment Z's exact checkpoints, run order, and per-family
loader/VRAM risk notes verbatim, with `band_selection` and `doses` left
`not_yet_run`/`not_yet_calibrated` (no profile or calibration has executed).

Ported the two Qwen3-4B J-space experiments' bespoke scripts into
family-parameterized versions (`mine_eval_pool.py`, `split_fit_heldout.py`,
`jlens_profile.py`, `extract_anchor.py`, `build_directions.py`,
`gate_fit.py`, `calibrate_dose.py`, `pipeline.py`, `run_contrast.py`,
`cross_family_rollup.py`), plus `family_config.py` as the single read/write
path for each family's YAML (no other script hardcodes a checkpoint, hidden
size, or layer index) and `model_lib.py` porting Amendment Z's own loader
hardening (`AutoModelForCausalLM` -> `AutoModelForImageTextToText` ->
`AutoModelForVision2Seq` fallback chain, `config.text_config` nesting).
`gen_lib.py` and `grader.py` are the generation-contract and grading code,
generalized (EOS resolution) or ported unchanged (grading is already
model-agnostic).

Verified every script with `py_compile` and `--help` (CPU-only, unsloth_env
conda python) -- no model loads, no GPU touched, per the lead's explicit
instruction that the local 3090 is busy with another experiment's
confirmatory and must not be touched at all.

Did NOT run `bin/exp sign` (prediction/falsifier/gates need the lead's
review and the scoreboard rows need the lead + user's calls first). Did NOT
run any HF pull, Modal launch, or GPU work. See `LAUNCH-PLAN.md` for the
per-family run order, GPU-time estimates, and the decision points that need
to come back to the lead before this experiment can launch for real.
