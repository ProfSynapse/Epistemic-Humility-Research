# hs20 native weight edit: harness (build only)

Config-first orchestration for `AMENDMENT.md`, `cell.yaml`, `gates.yaml`. This code was built against the locked draft; it has
**not been run on any model, GPU or private row**, and it carries no result. Parent owns protocol, signing, git, launch,
verdict and Nexus writes.

## What is here

| path | role |
|------|------|
| `hs20_nwe/render.py grader.py detector_v2.py gen_lib.py detector_v2_patterns.yaml` | frozen ports of `experiments/gate-contribution-factorial/*`; origin/port sha256 in `ORIGINS.json` (render differs only in env var names) |
| `hs20_nwe/inputs.py` | pinned input verification, roster check, allow-listed fields, exact seeded memberships, leakage checks |
| `hs20_nwe/capture.py sensor.py localize.py` | manifest-only hash-checked capture reads, fresh hs20 fire rule, per-row resumable localization + column ranking |
| `hs20_nwe/weights.py` | weights-inspect requests, six-proposal `add_rank_one` specs/payloads (NumPy + safetensors), receipts, norm-matched controls |
| `hs20_nwe/jobs.py engine.py budget.py` | engine configs and job registry; `EngineCLI` wrapper; 7000-row / 12 h ledger with hard stop |
| `hs20_nwe/grading.py selection.py adjudication.py rollup.py parity.py` | detector grading, FIT-screen selection, blinded lane (two code-enforced gates), G0-G4 roll-up, preflight parity evidence |
| `hs20_nwe/stages.py cli.py pipeline.py` | stage runners, `python -m hs20_nwe`, `mechinterp-pipeline/v1` generator |
| `persistence_declarations.yaml` | PROPOSED per-module persistence text (not wired into experiment.yaml) |
| `tests/` | 129 CPU tests (+1 torch-gated file, skipped here) |

## Layout and conventions

* All private state lives under `artifact://qwen35-4b-hs20-native-weight-edit/…` (`.synaptic/artifacts/<slug>/…`); configs reference
  only `artifact://` and `project://`. Staged inputs: `inputs/{fit_rows_for_dose,heldout_rows_for_steer,fit_rows_for_anchor}.jsonl`;
  model: `base_model/` (local directory, real file copy). Promoted `c_hat.json`/`u_d.json` are read in place (bytes never copied).
* `law.layer` is always the explicit decoder block 19 (the JSON `layer: 19` is a block index although the directory says hs20);
  capture `layers` are hidden-state indices (20); `capture_sites` are decoder blocks 20/21/22.
* Plugin root = the experiment directory (`hs20_nwe` package); render spec `hs20_nwe.render:render`.
* The engine is called only through `engine_host.cli_boundary.EngineCLI`; GPU verbs need `--gpu-ack` on this CLI.
* `--smoke-tag K` isolates outputs under `…/smoke/K/` (materialized rows are truncated copies; patches/base model are shared) while
  the budget ledger stays shared, so smokes count against the 7000-row / 12 GPU-hour cap.

## Commands

```
python -m hs20_nwe doctor                       # promoted directions, constants, index conventions (CPU)
python -m hs20_nwe materialize                  # needs staged inputs
python -m hs20_nwe plan-pipeline --python PY [--native-static]   # writes artifact://…/pipeline/pipeline.yaml
python -m hs20_nwe smoke-prepare --smoke-tag K --limit-rows N
python -m hs20_nwe [--smoke-tag K] [--gpu-ack] stage <emit-static|extract-fit-l|inspect|localize|propose|gen-static|
      gen-screen-candidates|select|controls|export|extract-heldout|gen-heldout|build-pool|parity-prepare|parity-compare>
python -m hs20_nwe pool commit | commit-hash --shard-id S --graded-file F | regrade … | spot-pack … | spot-record … | apply …
python -m hs20_nwe rollup ; python -m hs20_nwe budget
```

## Known limits (see the build report for the full list)

* `--model` is not path-reference-resolved by engine 1.1.0rc1; the generated pipeline therefore embeds the absolute staged path.
* The registered engine extension retains generated_token_ids; parity refuses missing IDs and compares them exactly.
* weights-inspect/patch need torch inside the engine; the CPU venv could only exercise argument/config acceptance
  (`tests/test_engine_cli_with_torch.py` is the ready cross-check for the engine image).

Before any GPU call, export `stage bind-runtime` in the pinned image and commit
its ID/hash-only `analysis-committed/run_binding.json`. Then run `stage
check-binding`. This binds the installed engine and host bytes, runtime receipt,
model shards, inputs, materialized populations, directions, source, and thresholds.

The measured pre-sign commands are `--gpu-ack drill extract`, `--gpu-ack drill
generation`, `drill localize`, and `--gpu-ack stage preflight-parity` (after
`stage inspect`). Each drill owns and SIGKILLs its process group, preserves the
before/after journals privately, and verifies exact resume. Smoke rows count in
the same cap under distinct physical output paths. `verify-selected` enforces
export/readback token parity before held-out generation. Pool and graded hash
exports require actual Git commits; private append logs alone cannot unlock the
next grading step. Spot-check acceptance is computed from the registered rule.
