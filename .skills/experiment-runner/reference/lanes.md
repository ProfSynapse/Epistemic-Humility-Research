# Execution lanes — local RTX 3090 vs HF Jobs cloud

`run_matrix.py` is lane-agnostic above the invocation: expansion, materialization,
provenance, and gating are identical; only the per-cell command and the
data-feeding strategy differ. The `--lane` flag selects.

## Why two data-feeding strategies (the data-locality contract, arch §9.2(b.1))

The tuner container sees ONLY the tuner repo. Local Docker bind-mounts the tuner
repo root at `/workspace/repo` (`local_run_handler.py:391`); HF Jobs clones ONLY
the tuner repo into `/workspace/repo`. And `dataset.local_file` is joined
tuner-repo-relative inside the container (`local_run_handler.py:502`:
`/workspace/repo / local_file`). The research repo's `experiment/phase1/data/` is
never visible to the container, so the two lanes feed data differently.

## Local RTX 3090 lane (`--lane local`)

Development, pilot, and smoke runs; serial (one local GPU). Per cell:

1. Stage the per-cell `<method>_train.jsonl` + `_dev.jsonl` from
   `experiment/phase1/data/<model_tag>/` into the tuner's **already gitignored**
   scratch dir: `synaptic-tuner/scratch/eh_staging/<run_id>/`. The tuner
   `.gitignore` already covers `scratch/`, so this needs ZERO tuner-tree edits
   and is not a committed source addition — it is ephemeral build-artifact-like
   scratch under the submodule checkout.
2. Rewrite the materialized recipe's `dataset.local_file` to the tuner-repo-
   relative staged path (`scratch/eh_staging/<run_id>/<method>_train.jsonl`) so
   the `/workspace/repo` join at `:502` resolves.
3. Invoke `python tuner.py local-run --job-config <materialized>.yaml --yes`.

**Uniform dispatch (HANDLER EXTENSION, §9.2 :994-1013, lead-ratified final).**
Every method — SFT, DPO, KTO — dispatches through the SAME native verb with a
**purely declarative** materialized recipe:
`python tuner.py local-run --job-config <materialized>.yaml --yes`. The tuner's
local-run handler command builder is method-generic: it reads `run.trainer` to pick
the per-method trainer script and forwards the training-key whitelist (`seed` for
all methods via tuner #32; `beta` method-gated to dpo/kto via #34). coder-cloud's
re-scoped #34 widens the handler's dispatch guard to `{sft,dpo,kto}`. So WS-5 NEVER
synthesizes a trainer command, a `run.command`, or a trainer `--config` invocation
(that direct-trainer path was explicitly WITHDRAWN, §9.2 :1175-1176).
`materialize_recipe` sets `run.method` + `run.trainer:
Trainers/{method}/train_{method}.py` so the materialized recipe is a complete,
self-describing job-config (the handler defaults `run.trainer` to the SFT path, so
DPO/KTO must carry the right one). Until #34's guard-widen lands, the local
capability probe keeps DPO/KTO cells SKIPPED (fail-closed).

Per-cell `training.learning_rate`/`seed`/`beta` live in the declarative recipe
config. Per-cell `seed`/`beta` forwarding is gated by the capability probe below —
it is NOT a given; do not assume "local is fine".

## HF Jobs cloud lane (`--lane cloud`)

The matrix execution lane (parallel across HF Jobs). Per cell the data is
referenced by its PUBLIC HF-hub `dataset.name` (NOT `local_file`), because HF
Jobs checks out a pushed tuner commit that cannot see ephemeral scratch.
Phase-1 datasets are published publicly via the tuner's dataset-publishing
skill; `check_prereqs` item 3a queries the hub for the dataset + pins a revision
SHA into the run record. Until an arm's dataset is on the hub, its cloud cells
SKIP (recorded), local pilot runs first — never a whole-matrix abort.

### Bridge cells are LOCAL-LANE ONLY

The 2 bridge replication cells are restricted to `--lane local`. Their OpenMOSS
training data is user-authorized for vendored use but **do-not-redistribute** (no
license), so it is never published to the HF hub and a cloud lane cannot reach
it. Unlike the not-yet-published Qwen3 datasets (which SKIP and become available
once published), a bridge cell on the cloud lane can *never* become runnable —
it is a structurally invalid request. Both the gate (`check_prereqs.check_cell`)
and the dispatcher (`run_matrix.select_invocation`) therefore **abort loudly**
(not skip) on a bridge cell with `lane == "cloud"`. `check_prereqs` item 3a (hub
availability) applies to the Qwen3 cloud cells only.

### Seed/beta forwarding safety gate (BOTH lanes): LIVE-PROBED

A cell is only safe to launch once the tuner forwards per-cell `seed` AND (for
DPO/KTO) `beta` all the way to the trainer. If it does not, the cell trains at the
default seed (42) / default beta while the run record claims the intended values —
silent corruption of the seed sweep and beta panel (the HANDOFF §5 failure mode).
The gap spans BOTH lanes and all three layers; coder-cloud (Task #32, scope
expanded) is reconciling it and will announce the ground-truth verdict + final
names. Until then the runner wires NEITHER lane's seed/beta and the gate keeps
both lanes SKIPPED until the forwarding verifiably exists.

The gate does **not** trust a hardcoded flag or a submodule SHA — the capability
lands as working-tree edits before it is committed, so a version string would
lie. Instead, same live-check philosophy as the hub gate, `check_prereqs`
**probes the actual tuner source surface** for the lane the cell will run on
(text-based, no tuner import). `lane_capability_ready(lane, root)` dispatches:

**Cloud** (`cloud_seed_beta_capability_probe`) — all three must be present:
1. `CloudTrainingConfig` declares `seed` and `beta` fields — `tuner/core/config.py`
2. the HF command builder emits `--seed` and `--beta` — `tuner/backends/training/cloud/_hf_command_builder.py`
3. the CLI exposes `--train-seed` / `--train-beta` — `tuner/cli/parser.py`

**Local** (`local_seed_beta_capability_probe`) — the handler-extension + LoRA-parity
contract (§9.2 :994-1013 + (d) item 5, lead-ratified final). Three things must hold:
1. the handler forwards BOTH `seed` and `beta` in its training-key whitelist
   (`seed` via tuner #32; `beta` via #34, method-gated to dpo/kto) —
   `tuner/handlers/local_run_handler.py`; and
2. dispatch is no longer SFT-only — the pre-#34 `elif method == "sft"` guard in
   `_compile` has been widened to route dpo/kto through the same generic builder; and
3. **LoRA flag parity** — `train_dpo.py` AND `train_kto.py` accept every `--lora-*`
   scalar the builder emits (`--lora-r`/`--lora-alpha`/`--lora-dropout`/
   `--lora-target-modules`/`--init-lora-weights`). This is the HYBRID ruling on
   coder-cloud's flag-diff: run-control flags (`--quiet`/`--no-dashboard`/`--save-*`/
   `--load-in-4bit`) stay method-gated in the builder, but the LoRA SCALARS get
   parity because the recipe `lora:` block is the §5.2 budget SSOT and the 8B
   recipes pin `r=64/α=128` vs the trainer `config.yaml` default `r=32/α=64` —
   gating (not forwarding) would silently corrupt the budget confound control on
   every 8B dpo/kto arm. A missing LoRA sink is the SAME whole-matrix-corruption
   class as a missing seed/beta sink.

   There is no trainer `--config`/`--seed` requirement — that direct-trainer path
   was withdrawn (§9.2 :1175-1176). The probe reads False against a pre-#34 tree
   (handler omits `beta`, still SFT-gated, and/or trainers lack `--lora-*`) and flips
   True once #34's guard-widen + beta-forward + LoRA parity all land. Load-bearing.

If any element is missing (or the submodule is absent), the probe returns `False`
(fail-closed). **The capability gate is then a WHOLE-MATRIX ABORT, not a cell skip**
(§9.2(d) item 5): a missing seed/beta sink makes every headline seed identical and
every beta-panel cell land at the default, and a missing LoRA sink mistrains every
local dpo/kto arm at the wrong budget — there is no meaningful partial run, so
`check_cell` raises `PrereqError` rather than recording a SKIP. (Contrast the
cloud-dataset-not-published and bridge-prereqs-absent conditions, which DO skip just
the affected arm.) The **OPEN decision comes ONLY from the live probe** — there is
deliberately no manual flag that can force the lane OPEN (a hand-flipped "capability
present" boolean would desync from the pinned submodule and silently re-admit the
seed-42 corruption). `FORCE_SEED_BETA_GATE_CLOSED` is a ONE-WAY override that can
additionally force the gate CLOSED (e.g. to quarantine the lane during an incident
even if the probe passes); it can never force OPEN. Default `False` defers to the probe.

**Layering with `submodule_pushed`:** the capability probe confirms the seed/beta
surface exists in the tuner *source*; `submodule_pushed` separately confirms the
pinned submodule commit is actually reachable on a remote (HF Jobs checks out the
pinned SHA). So even after coder-cloud's edits make the probe pass on the working
tree, a cloud launch still correctly aborts via `submodule_pushed` until those
edits are committed and pushed. Both must hold for a cloud cell to run.
