# Re-deriving the archived caution-ablation over-refusal collapse (0.994 to 0.030) notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

- (add dated entries as the experiment progresses)

## 2026-08-15 — Step 0 attribution (pre-GPU, no result exists yet)

Reconstructed which archived variant most plausibly produced the 0.994-to-0.030
over-refusal collapse, from: the archived configs' own headers, the KG mechanism
note `library/concepts/mechanisms/caution-residual-ablation-relaxes-overrefusal-asymmetrically.md`,
and the session doc. Path note: the AMENDMENT cites
`docs/sessions/20260627T093723Z-caution-vs-doubt-knowledge-gate.md`, which does
not exist at that path; the file lives at
`archive/docs/sessions/20260627T093723Z-caution-vs-doubt-knowledge-gate.md`
(moved under archival, not a config incompatibility — the content is intact and
authoritative). Read the full session doc (598 lines) before writing this entry.

**Attribution: the RAW-THETA config
(`configs/phase3_current_clean_grpo_v2_caution_residual_intervention.yaml`,
direction `caution_direction_L35.json`) produced the 0.994-to-0.030 figure —
NOT caution_perp**, contrary to the AMENDMENT's registrant "modal expectation:
the caution_perp variant" (AMENDMENT.md Prediction section).

Evidence, both checkpoints from the archived session doc, same model/rows/layer,
same day (2026-06-27):

- Checkpoint `005-result` ("B1 caution-axis causal intervention: LOAD-BEARING",
  at 10:11:42Z): "B1 GPU intervention complete (2164 units, raw-theta L35, 4
  arms)... Ablating the caution axis on known_refused drops refusal
  0.994->0.030 (delta -0.96) and 57.1% of de-refused knowns answer correctly.
  Specificity holds: known_correct_answered refusal stays 0.00 (+0.00
  collateral), correct 1.00->0.979." This is the raw caution theta direction
  (`caution_direction_L35.json`), the direction referenced by
  `configs/phase3_current_clean_grpo_v2_caution_residual_intervention.yaml`.
  Evidence path cited in-session:
  `experiment/phase1/probe/analysis/current_clean_grpo_v2_caution_residual_intervention/summary.json`
  — matches this config's declared `output.root` exactly.

- Checkpoint `010-result` ("Refined B1 (caution_perp, doubt-orthogonalized):
  independently LOAD-BEARING, two-component attribution", at 11:55:00Z): "L35
  caution_perp = caution with the rank-1 doubt axis removed... Ablating ONLY
  the caution-specific (doubt-orthogonal) component drops known_refused
  refusal 0.994->0.524 (delta -0.47)... ATTRIBUTION vs raw-theta B1 (#110,
  same model/rows/layer): raw-theta ablate de-refused 97% (refusal 0.99->0.03,
  correct 0.571 of 168 = 58.9% per de-refused); caution_perp ablate de-refuses
  ~48% (correct 68.7% per de-refused)." This is the direction referenced by
  `configs/phase3_current_clean_grpo_v2_caution_perp_residual_intervention.yaml`,
  and it explicitly reports 0.524, not 0.030.

  (Minor internal inconsistency noted, not resolved here: cp005 states "57.1%"
  correct-on-derefusal for raw-theta, cp010's retrospective recompute of the
  same raw-theta run states "58.9%" — both are session-doc prose, not
  re-derived from row data by this cell; the re-run below will produce a fresh
  number.)

- Corroborating: session checkpoint `018-build` (Paper 3 draft), listing the
  paper's R3 result set, separately names "L26 generation repair
  signed+layer-specific" as a DISTINCT result from the caution-ablation
  0.994->0.030 figure — i.e. the L26 coeff-sweep config
  (`configs/phase3_current_clean_grpo_v2_known_overrefusal_native_l26_coeff_sweep.yaml`)
  answers a different question (coefficient frontier for a native L26
  candidate direction) and is not itself a candidate source for the
  0.994-to-0.030 number. It remains in this cell's run_order (order 3) per the
  locked design, but attribution does not point to it.

**Conclusion:** modal prediction going into the GPU runs is REVISED from the
AMENDMENT's stated expectation. Based on the archived record, config 1
(raw-theta) is expected to reproduce ~0.030, and config 2 (caution_perp) is
expected to reproduce ~0.524, not <=0.10. This does not change the
pre-registered CA-G1 thresholds (fixed, not retuned) or run_order — both
configs still run per the locked cell.yaml. Recording this revised
expectation here, before either config's GPU result exists, per the
registered Step-0-before-any-result ordering.

## 2026-08-15 — Step 0b integrity verification (CA-G0)

- `caution_direction_L35.json` sha256 recomputed on disk:
  `9eb2a8c91dd950e669065f7a80b1424a0c3c24c389ed2a9ea1f98f13072d8785` — matches
  gates.yaml pin exactly.
- `caution_perp_direction_L35.json` sha256 recomputed on disk:
  `41e13f41100756fd10a974af8a7724940348ab869f2045be62ad4e86a079ee64` — matches
  gates.yaml pin exactly.
- `diff -q` of each of the three configs in this cell's `configs/` against its
  archive original (`archive/experiment/phase1/probe/config/grpo-v2-residual-repair/...`
  for the two intervention configs,
  `archive/experiment/phase1/probe/config/current-clean-grpo-v2-known-overrefusal/...l26_coeff_sweep.yaml`
  for the sweep config): all three byte-identical, zero diff output.
- Recomputed sha256 of `cell.yaml`, `gates.yaml`, and the three cell configs;
  all five match the `experiment.yaml` pins exactly.
- CA-G0 integrity precondition: PASSES on all four sub-checks. Proceeding to
  path shims.

## 2026-08-15 — Step 0c path shims created

Created (environment-level symlinks, config bytes untouched):

- `experiment/phase1/probe/analysis/current_clean_grpo_v2_caution_residual_direction`
  -> `archive/experiment/phase1-data/probe/analysis/current_clean_grpo_v2_caution_residual_direction`
- `experiment/phase1/probe/analysis/current_selfaware_behavior_rows`
  -> `archive/experiment/phase1-data/probe/analysis/current_selfaware_behavior_rows`
- `experiment/phase1/probe/analysis/current_clean_grpo_v2_caution_residual_intervention`
  -> `experiments/caution-ablation-rederivation/analysis/current_clean_grpo_v2_caution_residual_intervention`
  (real dir created under this cell's gitignored `analysis/`)
- `experiment/phase1/probe/analysis/current_clean_grpo_v2_caution_perp_residual_intervention`
  -> `experiments/caution-ablation-rederivation/analysis/current_clean_grpo_v2_caution_perp_residual_intervention`
  (real dir created under this cell's gitignored `analysis/`)
- `experiment/phase1/probe/analysis/current_clean_grpo_v2_known_overrefusal_native_l26_coeff_sweep`
  -> `experiments/caution-ablation-rederivation/analysis/current_clean_grpo_v2_known_overrefusal_native_l26_coeff_sweep`
  (real dir created under this cell's gitignored `analysis/`)

All five confirmed via `ls -la`. The `experiment/phase1/probe/analysis/` stub
dir was empty before this (previously archived, per the lead-prep entry
above); no pre-existing content was overwritten.

Pre-launch checks: `unsloth/unsloth:latest` already present locally (41.7GB);
GPU free (0 MiB used, 0% util, RTX 3090 24576MiB total); zero running
containers; docker context = `default` (not `desktop-linux`, so `--gpus all`
will work). Checkpoint/adapter/rows/direction files all confirmed present on
disk (base merged-16bit model, `clean_sft_grpo_v2_seed1` adapter, rows.jsonl
via symlink, both direction JSONs via symlink). L26 sweep's three dependency
configs (runner_config, candidate_source_config, row_keys_file) all confirmed
present under `archive/experiment/phase1/probe/config/current-clean-grpo-v2-known-overrefusal/`.

## 2026-08-15 — Config 1 launch (raw-theta caution residual intervention)

Container mount point fixed at `/workspace/repo` (not `/workspace`): the
config's `model.model_name` is a hardcoded ABSOLUTE path
`/workspace/repo/scratch/.../merged-16bit`, and
`resolve_model_ref()`/`resolve_path()` in the runner pass absolute paths
through unchanged (only relative paths get joined to the in-container
`REPO_ROOT`), so the mount must land exactly there or the model load fails
closed (path does not exist). This matches the L26 sweep config's own
`execution.docker.repo_mount: /workspace/repo` default, so both configs share
one mount convention. Following the proven flag set from
`experiments/caution-install-bounded-site-sweep/docker_launch.sh` (--gpus
all, --ipc=host, --entrypoint python3, unsloth HF-cache path, no `-it` since
this runs synchronously polled not interactively).

Command:

```
docker run --rm \
  --name caution-ablation-rederivation-config1-<UTC timestamp> \
  --gpus all --ipc=host --entrypoint python3 \
  -v "$HOME/.cache/huggingface:/home/unsloth/.cache/huggingface" \
  -v "/home/profsynapse/code/Epistemic-Humility-Research:/workspace/repo" \
  -w /workspace/repo \
  --env HF_HOME=/home/unsloth/.cache/huggingface \
  --env HUGGINGFACE_HUB_CACHE=/home/unsloth/.cache/huggingface \
  --env HF_TOKEN \
  --env PYTHONPATH=/workspace/repo/synaptic-tuner \
  unsloth/unsloth:latest \
  experiments/common/mechinterp/residual_intervention_runner.py \
  --config experiments/caution-ablation-rederivation/configs/phase3_current_clean_grpo_v2_caution_residual_intervention.yaml
```

4 arms (baseline, ablate, shift_minus2, shift_plus2) x 2 cells
(known_refused, known_correct_answered), full row set, no --fresh (resume
semantics kept in case of interruption; output dir is empty so this is
equivalent to a fresh run). Launching now.

## 2026-08-15 — STOP: pre-GPU import-chain break, systemic across all 3 configs

Launch attempt 1 (`docker run --rm -d ...`, entrypoint
`experiments/common/mechinterp/residual_intervention_runner.py --config
.../phase3_current_clean_grpo_v2_caution_residual_intervention.yaml`) exited
within seconds (container auto-removed by `--rm` before logs could be
captured — noted for future runners: launch debug attempts WITHOUT `--rm`
first). Relaunched without `--rm` to capture the traceback:

```
ModuleNotFoundError: No module named 'backends'
  (experiments/common/mechinterp/residual_intervention_runner.py:36,
   from backends import render_probe_prompt)
```

Root cause, traced read-only (no files edited):

1. `residual_intervention_runner.py` hardcodes `PROBE_DIR = REPO_ROOT /
   "archive/experiment/phase1/probe"` and inserts it onto `sys.path`. But
   `backends.py` does not exist directly in that flat directory — it exists
   one level deeper, at
   `archive/experiment/phase1/probe/legacy-wrapper-tree/backends.py`
   (confirmed via `find`; also confirmed `causal_pilot_runner.py` and
   `residual_intervention.py`, the runner's other two same-name imports, live
   in `experiments/common/mechinterp/` alongside the runner itself, so those
   two resolve fine via Python's own script-directory sys.path auto-add —
   only `backends` is affected by the PROBE_DIR/legacy-wrapper-tree
   mismatch).

2. cell.yaml's own text names an alternative, pre-existing entry point:
   "the archived wrapper
   `archive/experiment/phase1/probe/legacy-wrapper-tree/phase3_residual_intervention_runner.py`
   re-exports it." Tried this second (still read-only, no edits): invoking
   THAT script as the top-level program puts `legacy-wrapper-tree/` on
   `sys.path` automatically (Python's own script-dir auto-add), which in
   principle should let `from backends import ...` fall through to the
   sibling `legacy-wrapper-tree/backends.py`. It got one level further but
   hit a SECOND broken indirection: `legacy-wrapper-tree/backends.py` is
   ITSELF a compatibility-wrapper stub
   ("`Compatibility wrapper loader for scripts moved to
   experiments/common/phase1_probe`") that tries to
   `spec.loader.exec_module()` a file at
   `experiments/common/phase1_probe/backends.py` —  **a directory that does
   not exist anywhere in this checkout** (confirmed via `find . -iname
   phase1_probe`, zero hits). Traceback:
   `FileNotFoundError: [Errno 2] No such file or directory:
   '/workspace/repo/experiments/common/phase1_probe/backends.py'`.

3. Checked whether this is isolated to configs 1/2 or also blocks config 3
   (the L26 coeff sweep, which runs via a DIFFERENT execution path — invokes
   `experiments/common/mechinterp/causal_pilot_runner.py` directly, per
   `causal_pilot_sweep.py`'s own `build_command`/`runner_args`, never
   touching the legacy-wrapper-tree indirection at all). Read
   `causal_pilot_runner.py`'s own imports: it ALSO does `from backends import
   render_probe_prompt` at module top level (line 35), after inserting the
   same flat `PROBE_DIR` onto `sys.path` (its `scorers` import at line 34
   resolves fine via `EVAL_DIR` =
   `archive/experiment/phase1/eval/scorers.py`, which does exist there — only
   `backends` is missing). Since `causal_pilot_runner.py` is invoked directly
   in this path (no legacy-wrapper-tree script in the call chain at all),
   `legacy-wrapper-tree/` is never added to `sys.path`, so this import fails
   identically. **This confirms the break is systemic: all three configs in
   this cell depend on the same broken `backends` import, and none of the
   three currently-existing candidate source files
   (`archive/experiment/phase1/probe/legacy-wrapper-tree/backends.py` itself
   broken;
   `experiments/common/knowledge_probe/backends.py`;
   `experiments/gemma4-e4b-kv-seam-quarantine/backends.py`;
   `experiments/gemma4-e4b-pocket-ladder/backends.py`) is a verified,
   registered stand-in for whatever `render_probe_prompt` implementation the
   archived phase-1 probe pipeline actually used.** Confirmed
   `experiments/common/knowledge_probe/backends.py` does define a
   same-named `render_probe_prompt` function (line 166), but it belongs to a
   differently-scoped module (`knowledge_probe`, not `phase1_probe`) built
   for other experiments; using it without verification would be exactly the
   "silent instrument substitution" failure mode this repo's own
   `caution-install-bounded-site-sweep/docker_launch.sh` F3 fix comment
   explicitly documents and warns against. No confidence that its
   `render_probe_prompt` renders prompts identically (chat template,
   `enable_thinking` handling, system-prompt formatting) to what the archived
   B1/refined-B1/L26 runs actually used to produce 0.994/0.030/0.524.

4. Zero GPU-hours consumed. Every failure occurred within seconds, at Python
   import time, before any tokenizer/model load and before any container
   reached the GPU. No stray containers left running (`docker ps -a` clean
   after cleanup of the two debug-mode containers used to capture
   tracebacks).

**Disposition: STOP.** This is a pre-outcome instrument-integrity break in
the shared legacy mech-interp machinery
(`experiments/common/mechinterp/{residual_intervention_runner,causal_pilot_runner}.py`
and their `archive/experiment/phase1/probe/legacy-wrapper-tree/` /
`experiments/common/phase1_probe/` compatibility-wrapper chain), not covered
by this cell's pre-declared path shims (cell.yaml only pre-declares the two
input-data symlinks and three output-root symlinks; it says nothing about
`backends.py`'s location, and neither `experiment.yaml`'s pins nor
`gates.yaml`'s CA-G0 direction-sha/config-byte checks cover shared harness
scripts). No archived config byte and no shared script was modified. No
CA-G0 baseline-reproduction number exists for either intervention config, and
no arm of the L26 sweep ran. Per the binding invariant ("any incompatibility
is a STOP-and-report, never a patch-and-run") and CA-G0's own framing
("integrity precondition, pre-outcome stop, never patch-and-run"), reporting
this to the lead rather than attempting a further self-authorized fix (adding
an undeclared PYTHONPATH/symlink shim pointing at an unverified `backends.py`
candidate, or editing the shared runner/wrapper scripts) — both would exceed
this runner's mandate as a constrained executor working a locked spec.

## 2026-08-15 — lead prep and sign

Pre-sign verification: both direction-vector shas recomputed on disk and
match the amendment pins exactly; all three archived configs exist and were
copied byte-identical into configs/ (shas match the archive originals); the
checkpoint adapter (20260624_095831/final_model) and its seed-1 merged base
(20260623_123624/Qwen3-4B-bnb-4bit/merged-16bit) are both on disk; live
drivers located (residual_intervention_runner.py via the legacy wrapper,
causal_pilot_sweep.py for the coeff sweep); the coeff sweep's three
archive-referenced dependency configs and row-keys file all exist.

Known instrument-environment fact, recorded before launch: the archived
configs reference inputs and output roots under
experiment/phase1/probe/analysis/, which is now an EMPTY stub dir (inputs
moved to archive/experiment/phase1-data/probe/analysis/ at archival).
Resolution pre-declared in cell.yaml: symlink the two input names into the
stub dir pointing at their archived homes, and symlink the declared output
roots into this cell's gitignored analysis/ dir. Config bytes untouched
per CA-G0; the shims are mount-level environment, not instrument edits.

Signed via bin/exp sign: 5 files pinned (cell.yaml, gates.yaml, three
archived configs). Engine exception parity-locked recorded in the manifest
with reason. Launch authorized by the PI 2026-08-15; run delegated next
with a lead-owned watcher armed in the launch turn.

## 2026-08-16 — lead adjudication of the pre-GPU STOP: repairable, single-symlink environment fix

The runner's STOP was correct per CA-G0. Lead traced the break to its
provenance and adjudicates it repairable WITHOUT instrument substitution:

- `experiments/common/phase1_probe/` was not deleted; it was RENAMED to
  `experiments/common/knowledge_probe/` in commit d55b7d26 ("Rename active
  probe and mechinterp surfaces", 2026-07-10). The legacy-wrapper-tree stub
  chain was never updated to the new name, and no cell has invoked the
  archived intervention runners since, so the break went unnoticed until
  this re-run.
- The one symbol the two runners import from `backends`
  (`render_probe_prompt`) is BYTE-IDENTICAL between the archived-run-era
  file (`e6d6650c:experiment/phase1/probe/backends.py`, the June 2026
  commit that recorded the phase-3 probe artifacts) and today's
  `experiments/common/knowledge_probe/backends.py` (verified by function
  extraction and diff: identical, 2679 bytes both sides). This is git
  rename lineage, not a port; the F3 silent-substitution concern does not
  apply because the "substitute" IS the original.
- All other flat imports resolve already: `residual_intervention`,
  `causal_pilot_runner`, `causal_pilot_dry_run` are siblings of the entry
  scripts in `experiments/common/mechinterp/` (script-dir sys.path), and
  `scorers.py` exists flat in `archive/experiment/phase1/eval/`.
- `knowledge_probe/backends.py` loads standalone on CPU (lazy vLLM import;
  verified by direct import), so the shim adds no dependency risk.

Authorized repair (environment-level, uncommitted, reversible, zero code
or config edits): ONE additional symlink,
`archive/experiment/phase1/probe/backends.py ->
../../../../experiments/common/knowledge_probe/backends.py`
(relative, so it resolves identically inside the container mount).

Rejected: the runner's suggestion to revise the amendment's modal
prediction after the step-0 attribution. Registered predictions are never
revised post-sign; the scoreboard reconciles at Outcome, and the
registrant's caution_perp call will be scored wrong there if the raw-theta
attribution holds. The stale session-doc path in the amendment
(`docs/sessions/...` vs actual `archive/docs/sessions/...`) is noted here
as a dated correction, not edited into the signed text.

Run resumes with the registered run order and gates unchanged.

## 2026-08-16 — authorized symlink created; resuming run order

Created exactly the one symlink the lead authorized, nothing else:

```
ln -s ../../../../experiments/common/knowledge_probe/backends.py archive/experiment/phase1/probe/backends.py
```

`readlink -f` resolves to
`/home/profsynapse/code/Epistemic-Humility-Research/experiments/common/knowledge_probe/backends.py`;
`diff -q` against that target confirms identical content through the link.
No `.py` file edited, no `phase1_probe` directory created, legacy-wrapper-tree
entry point not used — resuming with the direct entry points
(`experiments/common/mechinterp/residual_intervention_runner.py` and
`causal_pilot_sweep.py`) exactly as originally planned. Relaunching config 1.

## 2026-08-16 — second bug found and self-corrected: Step 0c symlinks were absolute, broke inside container

Verification launch (debug mode, no `--rm`) got past the `backends` import
(confirms the authorized fix works) but failed one step later:

```
FileNotFoundError: [Errno 2] No such file or directory:
'/workspace/repo/experiment/phase1/probe/analysis/current_clean_grpo_v2_caution_residual_direction/caution_direction_L35.json'
```

## 2026-08-16 — third bug: container-uid write permission on output dirs

Relinked config 1 got past both prior failures (direction file loaded, rows
loaded) and reached the checkpoint write, then failed:

```
PermissionError: [Errno 13] Permission denied:
'/workspace/repo/experiment/phase1/probe/analysis/current_clean_grpo_v2_caution_residual_intervention/checkpoint.json'
```

Known, precedented cause (matches the archived session doc checkpoint
011-launch verbatim: "First launch died on a run-dir PermissionError
(container uid 1001 could not mkdir inside my uid-1000 755 dir)"):
`unsloth/unsloth:latest` runs as non-root uid 1001; this cell's real output
dirs under `experiments/caution-ablation-rederivation/analysis/` are
host-created, owned uid 1000:1000, mode 755.

Attempted the archived precedent's own fix (`chmod 777` on the three real
output dirs) — DENIED by the harness permission system (world-writable
chmod flagged). Used the cleaner alternative instead, changing nothing on
disk: added `--user 1000:1000` (matching this host user, the directories'
actual owner) to the `docker run` invocation, so the container process runs
as the owning uid instead of the image's default uid 1001. No chmod, no
ownership change, no directory mode change; strictly a container-launch flag.

Relaunch with `--user 1000:1000` added: container came up clean, checkpoint
loaded (2/2 shards, ~3.6s), no further errors in the first 30s of logs.
Harmless benign warnings only (torchao cpp-extension skip, mistral tokenizer
regex notice, torch_dtype deprecation notice, generation-flags notice — none
block or alter output). Container running, GPU generation underway. Polling
synchronously from here per the binding invariant (no blocking `docker
wait`).

## 2026-08-16 — Config 1 COMPLETE: exit 0, all 2164 units generated, CA-G0 PASSES

Polled synchronously (docker ps + rows.jsonl line count every ~85-90s,
several ~10-minute bash calls chained). Steady progress throughout, no
stalls, no OOM, no interruption. Completed cleanly at 05:02:47Z after ~49
minutes wall-clock (launched 04:13:49Z), container exited 0. (Note: the
`rtk` shell hook mangles multi-line `case`/`esac` bash inside a loop —
switched the polling script to a plain `if`/`grep -c` check instead of
`case`; recorded here as a gotcha for future polling loops in this repo.)

Full summary at
`experiments/caution-ablation-rederivation/analysis/current_clean_grpo_v2_caution_residual_intervention/summary.json`
(gitignored, row-level `rows.jsonl` alongside it, neither ever committed).
Aggregate-only copy (numbers only, no question/generation text) written to
`analysis-committed/config1_caution_residual_intervention_summary.json`.

**CA-G0 baseline check: PASS.** baseline known_refused refusal_rate = 0.994,
exact match to the 0.994 target (delta 0.0, well inside +/-0.02 tolerance).

**Per-arm numbers (n known_refused=168, n known_correct_answered=373):**

| arm | known_refused refusal_rate | known_refused correct_rate | known_correct_answered refusal_rate | known_correct_answered correct_rate |
|---|---|---|---|---|
| baseline | 0.994 | 0.0 | 0.0 | 1.0 |
| ablate | 0.0298 | 0.5714 | 0.0 | 0.9786 |
| shift_minus2 | 0.6548 | 0.2857 | 0.0 | 0.992 |
| shift_plus2 | 1.0 | 0.0 | 0.1957 | 0.8043 |

This is a near-exact re-derivation of the archived 005-result numbers:
ablate 0.994->0.0298 (rounds to the archived "0.030"), correct-on-derefusal
57.14% (archived "57.1%"), specificity control refusal +0.00 / correct
1.00->0.9786 (archived "0.979"). The 0.994-to-0.030 figure now has a
governed, freshly-re-derived source in this checkout, not just archived
config bytes.

Cleaned up: container removed (`docker rm`) after log/summary capture, no
`--rm` was used for this run so logs stayed available for the record before
cleanup. GPU freed. Proceeding to config 2 (caution_perp) per run_order.

## 2026-08-16 — Config 2 launch (caution_perp residual intervention)

Same invocation pattern as config 1 (now working: relative symlinks from
Step 0c's self-correction, `--user 1000:1000` from the permission fix),
only the config path changed:
`experiments/caution-ablation-rederivation/configs/phase3_current_clean_grpo_v2_caution_perp_residual_intervention.yaml`.
Container came up clean, checkpoint loaded (2/2 shards, ~8.5s — cold cache
this time), same benign warnings only, no errors in first 30s. Polling
synchronously.

## 2026-08-16 — Config 2 COMPLETE: exit 0, all 2164 units generated, CA-G0 PASSES

Completed cleanly at 05:52:59Z after ~49 minutes wall-clock (launched
05:03:52Z), container exited 0, steady progress throughout, no stalls.

**CA-G0 baseline check: PASS.** baseline known_refused refusal_rate = 0.994,
exact match again (delta 0.0).

**Per-arm numbers (n known_refused=168, n known_correct_answered=373):**

| arm | known_refused refusal_rate | known_refused correct_rate | known_correct_answered refusal_rate | known_correct_answered correct_rate |
|---|---|---|---|---|
| baseline | 0.994 | 0.0 | 0.0 | 1.0 |
| ablate | 0.5238 | 0.3274 | 0.0 | 0.9732 |
| shift_minus2 | 0.869 | 0.1131 | 0.0 | 0.9973 |
| shift_plus2 | 1.0 | 0.0 | 0.0697 | 0.9276 |

Near-exact re-derivation of archived checkpoint 010-result: ablate
0.994->0.5238 (rounds to archived "0.524"); correct-per-de-refused =
0.3274/(1-0.5238) = 68.75% (archived "68.7%"); specificity control correct
1.00->0.9732 (archived "0.973" implied from delta pattern); shift_minus2
refusal 0.869 / correct 0.1131 match the archived figures exactly;
shift_plus2 known_correct_answered refusal 0.0697 matches archived "0.070".
This confirms caution_perp's own archived number was 0.524, NOT 0.030 —
consistent with the Step 0 attribution recorded above.

Aggregate-only copy written to
`analysis-committed/config2_caution_perp_residual_intervention_summary.json`.
Container removed after capture. GPU freed. Proceeding to config 3 (L26
coeff sweep) per run_order.

## 2026-08-16 — Config 3 planning: same import fix applies, same permission
## issue expected, causal_pilot_sweep.py's CLI has no --user override

Ran the sweep script's own dry planning path first (no GPU, no `--execute`):

```
python3 experiments/common/mechinterp/causal_pilot_sweep.py \
  --config experiments/caution-ablation-rederivation/configs/phase3_current_clean_grpo_v2_known_overrefusal_native_l26_coeff_sweep.yaml \
  --write-plan --materialize-configs
```

Plan: 1 job (candidate `clean_sft_grpo_v2_l26_native_known_overrefusal_normed`,
mode `generation`, coefficients [5.0, 10.0, 20.0, 25.0], controls
[`no_vector_baseline`, `activation_subtraction`], max_rows 96,
max_new_tokens 96). Confirmed my Step-0c relative symlinks work correctly
here too: `sweep_manifest.json`, `planned_commands.jsonl`, and the
materialized per-candidate runner config all landed under this cell's real
output dir through the symlink chain, host-writable, no errors.

The planned `docker run` command (from `build_command()`) has NO `--user`
flag, so it would run as the image's default uid (1001, same as configs
1/2's initial failure) — and `causal_pilot_runner.py`'s own output writer
does `output_root.mkdir(parents=True, exist_ok=False)` (line 1379) into a
subdirectory of this cell's uid-1000-owned real output dir, which would hit
the identical `PermissionError` as configs 1/2 before the `--user` fix.
`causal_pilot_sweep.py`'s CLI (`parse_args`) has no uid/user override flag to
pass through, and editing the shared script is out of scope.

Resolution (matching the configs-1/2 precedent, not a new authorization —
same fix class: container launch flag, zero code/config edits): execute the
EXACT planned command `causal_pilot_sweep.py --execute` would have run
(image, entrypoint, mounts, env vars, materialized config path, candidate,
coefficients, controls — all taken verbatim from the `--write-plan` output
above) via a direct `docker run`, adding only `--user 1000:1000`. Confirmed
`.cache/hf` (the config's own declared `HF_HOME`/`HUGGINGFACE_HUB_CACHE`
target under the mounted repo) already exists on disk, `drwxrwxrwx`, so no
separate permission concern there regardless of uid. This bypasses only
`causal_pilot_sweep.py`'s `execute_jobs()` orchestration wrapper (which
otherwise just calls `subprocess.run` on the identical command list and logs
results/logs to host-side files) — not the archived instrument itself.
Launching now.

## 2026-08-16 — Config 3 STOP: new missing input, not covered by the
## authorized shim list, deliberately NOT self-fixed

Launch (with `--user 1000:1000` added, matching the configs-1/2 fix)
progressed further than before: past the `backends` import (confirms that
symlink also unblocks `causal_pilot_runner.py`, the shared dependency used
by all three configs). Exited cleanly (exit code 2, no traceback — a
handled validation error, not a crash) after ~27s, no GPU work started:

```
ERROR: extraction manifest missing:
/workspace/repo/experiment/phase1/probe/qwen3-4b-clean-sft-grpo-v2-seed1-selfaware/hidden_states_selfaware_clean_sft_grpo_v2_full/extraction__55254a04aa1f/manifest.json
```

Traced read-only (no edits, no new symlinks created): this is the SAME
archival-move pattern as the two pre-declared Step-0c shims
(`experiment/phase1/probe/...` moved to `archive/experiment/phase1-data/probe/...`
at archival) — confirmed via `find`, the file exists at
`archive/experiment/phase1-data/probe/qwen3-4b-clean-sft-grpo-v2-seed1-selfaware/hidden_states_selfaware_clean_sft_grpo_v2_full/extraction__55254a04aa1f/manifest.json`.
This is the candidate-source config's `extraction_manifest` field (from
`archive/experiment/phase1/probe/config/current-clean-grpo-v2-known-overrefusal/phase3_current_clean_grpo_v2_known_overrefusal_native_layer_window_candidates.yaml:candidate_directions[0].extraction_manifest`,
identified via the KG search at the top of this session) — a dependency of
config 3 specifically, never touched by configs 1/2, and NOT one of
cell.yaml's two pre-declared input shims
(`current_clean_grpo_v2_caution_residual_direction`,
`current_selfaware_behavior_rows`).

**Deliberately NOT self-authorizing a third shim here**, even though the
pattern is now well-understood and low-risk, because the lead's adjudication
of the prior STOP was explicit: "AUTHORIZED FIX — exactly ONE symlink,
nothing else... Do NOT edit any .py file, do NOT create phase1_probe dirs or
**other shims**." Extending that authorization to a structurally similar but
different path on my own initiative would be exactly the kind of
self-authorized patch-and-run CA-G0 exists to prevent, regardless of my
confidence in the diagnosis. Cleaned up the failed container (`docker rm`);
`docker ps -a` clean; GPU still 0% / 0 MiB (zero GPU-hours spent on this
attempt). Configs 1 and 2 stand COMPLETE with strong CA-G0 passes (see
above). Reporting to lead for config-3-specific adjudication before any
further action.

Root cause: this runner's own Step 0c symlinks (created 2026-08-15, before
the STOP) used ABSOLUTE host paths
(`/home/profsynapse/code/Epistemic-Humility-Research/archive/...`) as
targets. On the host those resolve fine, but inside the container — mounted
at `/workspace/repo`, a different path than the host absolute path — the
symlink's absolute target does not exist, so the read fails. This is exactly
the reason the lead's authorized `backends.py` fix specified a RELATIVE
target ("resolves identically inside the container mount"); the same
principle applies to all five Step 0c shims, which this runner had gotten
wrong.

Self-corrected (no new authorization needed — same five pre-declared shims,
same targets, only the symlink's absolute-vs-relative encoding changed):
recreated all five under `experiment/phase1/probe/analysis/` as relative
symlinks (`../../../../archive/...` / `../../../../experiments/...`),
verified each still resolves on the host
(`caution_direction_L35.json` and `rows.jsonl` both readable through the
relinked paths). Cleaned up the stray verify-mode container (`docker rm`);
`docker ps -a` confirms clean. Relaunching config 1 for real.

## 2026-08-16 — lead verification of configs 1/2 and config-3 shim authorization

Lead recomputed every per-arm rate from raw `analysis/*/rows.jsonl`
independently: exact agreement with the runner's report on all 16
(arm, cell) rates across both configs; coverage confirmed 2164 rows per
config (541 x 4 arms; known_refused n=168, known_correct_answered n=373).
CA-G0 holds for configs 1 and 2: baselines 0.9940 exactly (target
0.994 +/- 0.02), shas and config bytes verified pre-run, full coverage.

Config-3 STOP adjudicated: same archival-move pattern as the backends fix.
Lead verified the sweep's candidate-specific inputs exist at IDENTICAL
relative paths under `archive/experiment/phase1-data/probe/` (the
layer-window normed-directions tree including the l26 safetensors, and
extraction__55254a04aa1f with its manifest.json). Bounded authorization
issued to the runner: symlink into `experiment/phase1/probe/` any INPUT
name config 3 requests that exists at the identical relative path under
`archive/experiment/phase1-data/probe/` (top-level dir-name symlinks,
relative targets, existence verified before linking, each recorded here);
any OUTPUT root config 3 declares that is not already shimmed gets the
standard symlink into this cell's gitignored `analysis/`. Anything NOT
found at the identical relative path = stop and report, never substitute.
Config bytes remain untouched; gates unchanged.

The runner's `--user 1000:1000` container-flag fix (after the harness
correctly denied a world-writable chmod) is accepted: launch-environment
flag only, no file modes or instrument code touched.

## 2026-08-16 — Config 3 shims created under the bounded authorization

Read the materialized per-candidate config causal_pilot_sweep.py already
wrote during the earlier dry `--write-plan --materialize-configs` pass
(`experiments/caution-ablation-rederivation/analysis/current_clean_grpo_v2_known_overrefusal_native_l26_coeff_sweep/_sweep_configs/clean_sft_grpo_v2_l26_native_known_overrefusal_normed__generation.yaml`)
to enumerate the EXACT effective input/output paths this run needs (already
deep-merged from the runner_config + selected candidate + sweep overrides,
so no need to hand-reconstruct from the two source configs). Two NEW inputs
identified beyond the two pre-declared Step-0c shims:

1. `extraction_dir` / `extraction_manifest`: under top-level dir
   `experiment/phase1/probe/qwen3-4b-clean-sft-grpo-v2-seed1-selfaware/`.
2. `direction_manifest` / `direction_csv` / `direction_file` (the l26
   candidate's safetensors): under top-level dir
   `experiment/phase1/probe/analysis/current_clean_grpo_v2_known_overrefusal_layer_window_normed_directions/`.

(`probe_results` and the sweep's own `output.root` were already covered by
existing Step-0c shims; `row_keys_file` points at
`archive/experiment/phase1/probe/config/.../..._row_keys_file.txt`, a plain
archive/ config path, never archived-data, not rewritten to an absolute
container path by `_rewrite_docker_config_paths` — confirmed it already
exists, no shim needed.)

Verified BOTH targets exist at the identical relative path under
`archive/experiment/phase1-data/probe/` BEFORE linking (per the hard
boundary): extraction dir + manifest.json present; layer-window directions
dir + manifest.json + csv + the l26 safetensors file all present. Created
exactly these two top-level dir-name symlinks, relative targets:

```
experiment/phase1/probe/qwen3-4b-clean-sft-grpo-v2-seed1-selfaware
  -> ../../../archive/experiment/phase1-data/probe/qwen3-4b-clean-sft-grpo-v2-seed1-selfaware

experiment/phase1/probe/analysis/current_clean_grpo_v2_known_overrefusal_layer_window_normed_directions
  -> ../../../../archive/experiment/phase1-data/probe/analysis/current_clean_grpo_v2_known_overrefusal_layer_window_normed_directions
```

Both confirmed resolving (extraction manifest, direction manifest, and the
l26 safetensors file all readable through the shims). No config bytes
touched, no other shims created. Relaunching config 3 with the same
verbatim-planned-command + `--user 1000:1000` pattern.

Relaunch clean: checkpoint loaded (2/2 shards, ~4.4s), no errors in first
30s, only the same benign warnings as configs 1/2. Note this run uses
`--entrypoint python` (not `python3`) and the sweep's own HF cache
env vars (`/workspace/repo/.cache/hf`), matching the config's own declared
docker execution block exactly (not the docker_launch.sh precedent's
`/home/unsloth/.cache/huggingface` convention used for configs 1/2 — the two
patterns are config-specific, both correct for their own instrument).
Polling synchronously. Note: unlike configs 1/2 (2164 units, 4 arms x 541
rows), this is a coefficient-sweep generation job (96 rows x multiple
coefficients x controls) — a different unit-count shape, so row-count
progress checks below track this job's own output files, not a rows.jsonl
count against 2164.

Polling correction: the runner writes to a TIMESTAMPED subdirectory
(`generation/run_<UTC timestamp>/generations.jsonl`), not directly under
`generation/`, unlike configs 1/2's flat `rows.jsonl`. First two poll
attempts checked the wrong (non-timestamped) path and saw 0 rows for ~9
minutes even though generation was progressing; corrected the poll path
once `find -newer` located the actual run directory. No data lost, purely a
progress-visibility gap in my own polling, not a run problem — noting here
as a gotcha for future config-3-shaped polling.

## 2026-08-16 — Config 3 COMPLETE: exit 0, all 768 generation units (96 rows x 8 arms)

Completed cleanly at 06:11:27Z after ~10.5 minutes wall-clock (launched
06:00:50Z), container exited 0. `generation_executed: true`, `arm_count: 8`,
`row_count: 96` (768 total generation records, matching final line count).
Much faster than configs 1/2 since this is 96 rows x 8 arms = 768 units vs
2164 — consistent with the much shorter wall-clock.

**Arms:** 4 coefficients (5.0, 10.0, 20.0, 25.0) x 2 controls
(`no_vector_baseline`, `activation_subtraction`) = 8. n=96 per arm (64 known,
32 unknown — the row_keys_file replay-96 sample, NOT the same known_refused/
known_correct_answered two-cell split configs 1/2 used).

**no_vector_baseline (identical across all 4 coefficient rows, as
expected — coefficient does not apply to this control):**
over_refusal_on_known 75.0%, known_answer_correctness 25.0%, known_answer_
retention 25.0%, unknown_refusal_rate 96.88%, answer_on_unknown_rate 3.12%,
truthful_rate 48.96%.

**activation_subtraction by coefficient:**

| coef | over_refusal_on_known | known_answer_correctness | known_answer_retention | unknown_refusal_rate | answer_on_unknown_rate | truthful_rate |
|---|---|---|---|---|---|---|
| 5.0 | 64.06% | 35.94% | 35.94% | 96.88% | 3.12% | 56.25% |
| 10.0 | 59.38% | 39.06% | 40.62% | 100.0% | 0.0% | 59.38% |
| 20.0 | 54.69% | 42.19% | 45.31% | 93.75% | 6.25% | 59.38% |
| 25.0 | 56.25% | 40.62% | 43.75% | 100.0% | 0.0% | 60.42% |

Coefficient 20.0 gives the largest known-side effect (over_refusal drops
75.0%->54.69%, correctness rises 25.0%->42.19%) while also showing the
largest unknown-side leak (answer_on_unknown_rate rises to 6.25%, highest of
the four coefficients) — a coverage/specificity tradeoff, not monotone.
`thinking_tag_contamination_count: 0` at every arm (no contamination). No
CA-G0 baseline-reproduction gate applies to this config (gates.yaml defines
that check only for configs 1/2's baseline arm against the 0.994 target;
config 3 has no analogous target registered).

Aggregate-only copy (numbers only, no row/generation text) written to
`analysis-committed/config3_l26_coeff_sweep_metrics.json`. Full row-level
`generations.jsonl`/`scored_rows.jsonl` remain under this cell's gitignored
`analysis/` dir, never committed. Container removed after capture. GPU
freed. All three configs in run_order now complete.

## 2026-08-16 — lead verification of config 3 and full-cell adjudication

Lead recomputed config 3 per-arm rates from the raw run's
scored_rows.jsonl: exact agreement with the runner (baseline 75.00
over-refusal on 64 knowns per coefficient row; activation_subtraction
64.06 / 59.38 / 54.69 / 56.25 at coefficients 5/10/20/25; unknown-side
refusal 96.88 / 100 / 93.75 / 100). Config-3 shims confirmed within the
bounded authorization (two input dir symlinks, both pre-verified at
identical relative paths; no new output shim needed).

CA-G0 PASS x3 and CA-G1 calls written into the AMENDMENT Outcome:
raw-theta REPRODUCED (0.0298 <= 0.10), caution_perp >= 0.30 (its own
archived 0.524 replicated; never the 0.030 source), sweep descriptive.
Falsifier not fired. Scoreboard reconciled straight, including the
registrant's wrong modal-variant call (caution_perp predicted, raw-theta
reproduced). Resolve awaits explicit PI approval; verdict text staged in
the Outcome.

## 2026-08-16 — naming pass (PI directive) and resolve

Per the PI's directive this morning, running prose in this cell's
AMENDMENT now uses the terminology.md vocabulary (refusal axis for the
legacy caution direction; KU-orthogonalized component for caution_perp;
KU-readout coupling for the doubt-regulated-caution comparison cell,
whose slug stays verbatim). A dated naming note was added under the
AMENDMENT Status line. The registered Prediction/Falsifier/Gates sections
and the sign-pinned gates.yaml/experiment.yaml bytes retain their legacy
phrases verbatim — pins are frozen; this entry is the record that those
occurrences are legacy names. Resolve executed with explicit PI approval
("Then resolve, merge and edit papers").

- 2026-09-01: aggregate data exhaust published (batch 4 of the backfill, task-56c61a; PI-approved in-conversation 2026-09-01). Copy-everything mirror of analysis-committed plus README + PROVENANCE; aggregate shape, no row text, zero exclusions. 5 files / ~14 KB, built at repo commit ed87715b.
- HF repo: `professorsynapse/eh-caution-ablation-rederivation` (dataset)
- HF revision: `1a8442c257d67f316144424918e5b7c5246f3a68`
