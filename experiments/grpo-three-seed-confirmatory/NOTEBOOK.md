# GRPO Three-Seed Confirmatory Block notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

### 2026-08-01 — Seed-2 clean_sft_dpo (stage 2) LAUNCHED

Container `eh-grpo3seed-2-clean_sft_dpo-20260801T183028Z`, launched 18:30:28Z,
pinned digest re-verified before launch. Lead re-derived the launch args from
`docker inspect` of the running container: `--model-name` points at the seed-2
MERGED checkpoint
(`.../sft_schema_clean_seed2_full/20260731_232307/Qwen3-4B-bnb-4bit/merged-16bit`,
satisfying G0 `merge_first_lineage`), `--beta 0.1`, `--seed 2`,
`--learning-rate 5e-6`, batch 2 / grad-accum 4, LoRA r32/a64/d0.05, 1 epoch,
training file the frozen `dpo_response_confidence_train.jsonl` (14,943 rows,
matches the frozen G0 audit constant). Output root
`scratch/schema_response_confidence/runs/schema_clean_sft_dpo_seed2_full`,
run-timestamp `20260801_183028`. Note carried from seed-1 precedent: the
DPO/KTO trainers expose no `--lora-random-state` flag, so LoRA init uses the
trainer baseline (3407) for these stages; the seed-mirroring ruling applies
only where a config file carries `lora.random_state` (SFT/GRPO). Seed-1
behaved identically, so this is not a new degree of freedom.

### 2026-08-01 — Seed-2 clean_sft (stage 1) COMPLETE: train + merge + bounded smoke, G0 PASS

Closes out stage 1 for seed 2. Two watch-discipline stalls occurred during
this stage (recorded honestly, no GPU time lost either time — both times the
GPU sat idle 0MiB/0% while this harness was mid-turn or between turns, not
stuck mid-job): the predecessor harness wedged after training finished
(recovered at takeover, entry above), and this harness itself then let a
completed `docker wait` go unactioned for roughly 8 hours after the merge
step before the lead's status check prompted resumption. New standing rule
adopted going forward: check `docker inspect` on every watched container
before ending any turn, and act immediately if it has already exited rather
than waiting on the wake notification.

**Merge.** Container `eh-grpo3seed-2-clean_sft-merge-20260801T091239Z`
(launched 09:12:39Z, exited 0 at 09:14:07Z), pinned digest re-verified before
launch (`sha256:f21629b9ae4ed11231768edfaed0f40d41d85d6ea9a71e8096a3d96ea0311772`).
Ran `shared.model_loading.merge.merge_lora_checkpoint(lora_path=.../final_model,
output_path=.../Qwen3-4B-bnb-4bit/merged-16bit, max_seq_length=2048,
load_in_4bit=True)` inside the container (mechanism and output-path
convention reconstructed from `synaptic-tuner/shared/model_loading/merge.py`
and `tuner/handlers/merge_handler.py:169`, since no standalone scriptable
merge CLI exists — `MergeHandler` is interactive-menu-only). Log confirms
`Unsloth: Merge process complete.` Output at
`scratch/schema_response_confidence/runs/sft_schema_clean_seed2_full/20260731_232307/Qwen3-4B-bnb-4bit/merged-16bit/`:
`config.json` present (valid merged model, not an adapter), 2 safetensors
shards, 7.6G total — same shard-count/size pattern as the seed-1 merge.

**Bounded smoke (G0 `bounded_smoke_coverage`).** Config
`experiments/grpo-three-seed-confirmatory/configs/eval_grpo3seed_response_confidence_selfaware_clean_sft_seed2_merged_smoke_local_4b.yaml`,
cloned from the seed-1 merged-smoke config
(`archive/experiment/phase1/eval/config/eval_amendment_e_response_confidence_selfaware_clean_sft_seed1_merged_smoke_local_4b.yaml`)
with only `model_tag`/`model_name`/`results_dir` changed to the seed-2 merged
path; `offset: 2240` / `limit: 192` (selfaware-mixed-192 per cell.yaml) and
all prompt/generation/vllm settings carried unchanged. Container
`eh-grpo3seed-2-clean_sft-smoke-20260801T103120Z`, digest re-verified
immediately before launch (same pinned digest as above), `--live-vllm`,
exited 0 at 10:33:47Z. Results:
`archive/experiment/phase1/eval/results_grpo3seed_response_confidence_selfaware_clean_sft_seed2_merged_smoke_4b/`.

Lead-verified numbers (n=192, 97 known / 95 unknown): 192/192 rows scored,
192/192 `generated_answer` + `stated_confidence` coverage, 0 retry-exhausted,
0 thinking-tag hits, `enable_thinking` uniformly false.
`refusal_recall_pct` 89.47, `answer_on_unknown_pct` 10.53, `over_refusal_pct`
68.04, `refusal_rate_pct` 78.65, `correct_on_known_pct` 45.16, `truthful_pct`
51.56.

G0 `bounded_smoke_coverage`: PASS (lead-adjudicated). G0
`training_completed_clean` and `merge_first_lineage`: PASS (verified above and
in the takeover entry). Stage 1 for seed 2 is complete; proceeding to stage 2,
`clean_sft_dpo`, sourced from this merged checkpoint per `merge_first_lineage`.

### 2026-08-01 — TAKEOVER: predecessor harness stalled after seed-2 clean_sft training completed; verified and resumed at merge step

The prior execution harness wedged sometime after the seed-2 `clean_sft`
training container reached a clean exit and was terminated by the lead; this
harness resumes the chain from recorded state, per dispatch. No G0 implication
from the stall itself — it is a harness/watch-loop failure, not an instrument
or data problem, and it burned zero extra GPU time (verified below).

Re-verified from artifacts rather than trusting the predecessor's own record:
- `docker inspect eh-grpo3seed-2-clean_sft-20260731T232235Z` ->
  `Status: exited, ExitCode: 0`, `StartedAt: 2026-07-31T23:22:35Z`,
  `FinishedAt: 2026-07-31T23:49:14Z` (26m39s wall, consistent with the
  `training_lineage.json` `training_time_seconds: 1526.8`).
- Run dir
  `scratch/schema_response_confidence/runs/sft_schema_clean_seed2_full/20260731_232307/`
  contains `final_model/adapter_model.safetensors` (252.1M),
  `final_model/adapter_config.json`, `training_lineage.json` (`stage:
  training`, `runtime.status: completed`, `final_step: 1495`, `final_loss:
  0.4281`), and `capacity_features.json`. G0 `training_completed_clean`: PASS.
- `nvidia-smi`: RTX 3090, 0MiB/24576MiB, 0% util, idle at takeover time
  (2026-08-01T09:12Z) — GPU was sitting idle the whole stall, not stuck
  mid-job. Zero GPU time lost to the stall itself.
- `docker images --digests unsloth/unsloth` ->
  `sha256:f21629b9ae4ed11231768edfaed0f40d41d85d6ea9a71e8096a3d96ea0311772`,
  still exact match to the pinned digest.

Wall-clock accounting against the signed budget guardrails (seed-2 block
~42h from the 2026-07-31T23:22Z launch, ~83h total): stage-1 train+merge+smoke
for seed 1 measured 2.4h. From launch (23:22Z) to takeover (09:12Z) is ~9h50m
elapsed, of which only ~27m was GPU training time — the remaining ~9h23m
(23:49Z training-end to 09:12Z takeover) is dead stall time with the GPU idle,
not additional work. Recorded honestly against budget rather than absorbed
silently; still well inside the ~42h seed-2 guardrail even counting the full
stall.

Resumed at the next un-done step per `launch_order`: merge. No merge script
exists as a standalone CLI (`tuner/handlers/merge_handler.py`'s `MergeHandler`
is interactive-menu-only, not scriptable headless); confirmed the seed-1
mechanism instead via `synaptic-tuner/shared/model_loading/merge.py`
(`merge_lora_checkpoint(lora_path, output_path, max_seq_length=2048,
load_in_4bit=True)`, family defaults to `causal_lm`) and the output-path
convention from `merge_handler.py:169` (`run_path / get_base_model_name(lora_path)
/ "merged-16bit"`), which matches the seed-1 artifact path exactly
(`.../sft_schema_clean_seed1_full/20260623_123624/Qwen3-4B-bnb-4bit/merged-16bit`).

Launched: container `eh-grpo3seed-2-clean_sft-merge-20260801T091239Z`, pinned
image digest re-verified before launch
(`sha256:f21629b9ae4ed11231768edfaed0f40d41d85d6ea9a71e8096a3d96ea0311772`),
`--user root --gpus all --ipc=host --entrypoint python3`, `PYTHONPATH=
/workspace/repo/synaptic-tuner` (mirrors how `train_sft.py` inserts
`synaptic-tuner/` onto `sys.path` at import time), running:

```python
from pathlib import Path
from shared.model_loading.merge import merge_lora_checkpoint
lora_path = Path("scratch/schema_response_confidence/runs/sft_schema_clean_seed2_full/20260731_232307/final_model")
output_path = Path("scratch/schema_response_confidence/runs/sft_schema_clean_seed2_full/20260731_232307/Qwen3-4B-bnb-4bit/merged-16bit")
merge_lora_checkpoint(lora_path, output_path, max_seq_length=2048, load_in_4bit=True)
```

`docker wait` running in background; will record merge result, then launch the
192-row bounded smoke (G0 `bounded_smoke_coverage`) before the stage-1 entry
is considered complete.

### 2026-07-31 — Seed-2 clean_sft (stage 1) LAUNCHED, after a launch-mechanism fix

Preflights re-confirmed after the lead's ruling: `git pull` in this worktree
showed the ruling commit already local (worktree and lead share the same local
repo; the ruling reached me via the local branch, not a remote fetch —
confirmed `d49bc6b2` present, no conflicts with my hard-stop entry above it).
`nvidia-smi` re-checked idle (0MiB/24576MiB, 0% util) immediately before
launch.

Built
`experiments/grpo-three-seed-confirmatory/configs/sft_schema_clean_response_confidence_seed2_full.yaml`,
a seed-2 clone of the archived
`sft_schema_clean_response_confidence_seed1_full.yaml`, all values unchanged
except `seed: 2` and `lora.random_state: 2` (lead ruling). Launched via
`docker run -d --user root --gpus all --ipc=host --entrypoint python3
... unsloth/unsloth:latest synaptic-tuner/Trainers/sft/train_sft.py --config
<that yaml> --no-dashboard --quiet`. Container
`eh-grpo3seed-2-clean_sft-20260731T231802Z` exited 1 immediately:
`AttributeError: 'NoneType' object has no attribute 'loader'` in
`train_sft.py:590-597` — `importlib.util.spec_from_file_location` cannot build
a loader for a non-Python file, because `--config` in `train_sft.py` has
**always** meant "import this file as a Python module and call `Config()`",
never a YAML loader. Confirmed via `git log -p` on `train_sft.py`: this
`spec_from_file_location(...)` branch is unchanged across the file's entire
history. The `.yaml` file I built from carries a header comment claiming
"Auto-converted ... for config-format uniformity (YAML, like the GRPO
trainer) ... Verified to load byte-identically ... Consumed by: train_sft.py
--config <this>.yaml" — that claim does not hold against the current trainer
code.

Cross-checked the REAL seed-1 invocation against the actual session notes
(`docs/sessions/20260623T093654Z-probe-scaled-response-confidence-retrain.md:500-504`),
not the archived runbook (which is itself headed "Status: prepared, not
launched" — a template, not a verified record). The real seed-1 launch used
`--config archive/experiment/phase1/grpo/configs/
sft_schema_clean_response_confidence_seed1_full_config.py` — a `.py` file.
That file no longer exists on disk: `git log --all --full-history
--diff-filter=A` traced it to commit `aa11b49e` ("Amendment J: GRPO-v3
proper-scoring confidence reward", an unrelated PR), which batch-deleted the
working `_config.py` files across this entire SFT-config family and replaced
them with the untested `.yaml` "auto-converted" versions in the same commit.
This is a repo-wide gap: every schema-response-confidence SFT `.yaml` config
under `archive/experiment/phase1/grpo/configs/` is currently unusable via
train_sft.py's `--config` flag, not just this one.

Fix: restored the exact original file via `git show
aa11b49e^:experiment/phase1/grpo/configs/
sft_schema_clean_response_confidence_seed1_full_config.py`. Diffed its values
against my `.yaml` attempt field-by-field — identical (model_name, dataset
path, batch_size 10 / grad_accum 1, learning_rate 2e-4, lora r=32/alpha=64/
dropout=0.05, num_epochs 1, chat_template_kwargs enable_thinking=false, etc.),
confirming the earlier `.yaml` conversion was faithful in content, only broken
in format/loading mechanism. Wrote
`experiments/grpo-three-seed-confirmatory/configs/sft_schema_clean_response_confidence_seed2_full_config.py`
as a `Config()` Python module, identical to the restored seed-1 file except
`training.output_dir` -> `.../sft_schema_clean_seed2_full`, `lora.random_state:
2`, `seed: 2`. No cell.yaml/gates.yaml pinned value touched; no hyperparameter
changed; only the config-delivery file format was fixed to match what
train_sft.py's `--config` flag has always actually required.

Relaunched: container `eh-grpo3seed-2-clean_sft-20260731T232235Z`, image digest
`sha256:f21629b9ae4ed11231768edfaed0f40d41d85d6ea9a71e8096a3d96ea0311772`
(re-verified before launch). Confirmed via logs: config loaded, run directory
`scratch/schema_response_confidence/runs/sft_schema_clean_seed2_full/20260731_232307`
created, model loading started (Unsloth 2026.5.9, Qwen3-4B-bnb-4bit, RTX 3090,
bf16, 4-bit). Training in progress at time of writing; `docker wait` running in
background. Seed-1 measured wall-clock for this stage (train+merge+smoke) was
2.4h (E note :488->:535); will record actual duration and artifact path/size
when it completes.

Elapsed against budget guardrails: essentially zero training time burned
before this entry (the two failed-fast attempts cost seconds, not compute).

### 2026-07-31 — LEAD RULING: lora.random_state mirrors the seed number; chain unblocked

Adjudication of the hard stop below. Ruling made BEFORE any outcome data
exists, on instrument-construction grounds only; nothing signed pins
`lora.random_state` (cell.yaml's `lora:` block fixes only r/alpha/dropout), so
this is protocol interpretation, not a gate change.

Ruling: seed-2 configs set `lora.random_state: 2` and seed-3 configs set
`lora.random_state: 3`, mirroring `seed:`. Rationale: (1) every seed-1 config
deviates from the tuner template default (3407) to `random_state: 1 == seed`,
so the convention carried from seed-1 evidence is "random_state mirrors the
seed", not the literal value 1; (2) the amendment's purpose is a full per-seed
lineage replicate — freezing LoRA init across seeds would test only data-order
robustness and weaken what a G1 replication (or failure) means; (3) the
alternative readings (literal 1, or template 3407) would make seed-1 itself
inconsistent with the convention chosen. The executor records the actual
`seed`/`lora.random_state` pair per config in its per-stage entries so the
choice is auditable.

Also ruled on the staleness flag below: AMENDMENT.md's banner and predictions
scoreboard are corrected in this branch to reflect the signed state recorded in
experiment.yaml (bookkeeping only; no design content changed). gates.yaml is
left byte-identical because it is sha256-pinned at sign; its `status: proposed`
header comments are superseded by experiment.yaml's `status: signed`, which is
authoritative.

### 2026-07-31 — HARD STOP before first launch: lora.random_state seed-threading ambiguity

Execution harness dispatched to run the registered seed-2/seed-3 chain. Read, in
order: AMENDMENT.md, cell.yaml, gates.yaml,
archive/experiment/phase1/grpo/amendment_e_clean_mainline_runbook.md.

Documentation-staleness note (not a blocker, flagged for the lead to fix):
AMENDMENT.md's top banner still reads "Status: DRAFT — NOT SIGNED. Do not
launch," its bottom "Predictions scoreboard" table still shows both PI/
orchestrator rows as empty placeholders, and gates.yaml's own header fields
read `status: proposed` / `adjudicated_by: null` / `adjudicated_date: null`.
Cross-checked against experiment.yaml (status: signed, registered: true, real
non-empty prediction/falsifier text, instrument.pins.cell.yaml =
c3026109d42c8fe13755b30466d7f482885d56c50de6836e92558fdb4070a864,
instrument.pins.gates.yaml =
7c79a41894a1fc64df01f07bbb197f8c25239d8625e3d9f3d8bbc97d3e51c0fa — both
verified byte-identical via sha256sum against the current cell.yaml/gates.yaml
in both the main checkout and this worktree), experiments/registry.json (same
signed state), git log (`65accc43 GRPO three-seed confirmatory: SIGNED
(2026-07-31, user approval in session)`), and the merged
`gh pr view 379` (title "GRPO three-seed confirmatory: signed amendment",
MERGED). All five agree the block is genuinely signed; only the two prose
banners and the gates.yaml header comments were never rewritten by the sign
tooling.

Preflight results (all pass):
- `docker info` Server block: nvidia runtime registered (`Runtimes: nvidia runc
  io.containerd.runc.v2`), Server Version 29.3.1, reachable via
  DOCKER_HOST=unix:///var/run/docker.sock.
- `docker images --digests unsloth/unsloth` ->
  sha256:f21629b9ae4ed11231768edfaed0f40d41d85d6ea9a71e8096a3d96ea0311772,
  exact match to the pinned digest.
- `nvidia-smi`: RTX 3090, 0MiB/24576MiB used, 0% util, no running processes —
  GPU idle.
- G0 dataset audit (re-run myself, not reused from the dispatch claim):
  sft_response_confidence_train_clean.jsonl = 14943 rows; source_label counts
  known=7981, unknown=6414, discard(ambiguous)=548; unique response_confidence
  targets=2489; range [0.3508, 0.9]. dpo_response_confidence_train.jsonl =
  14943 lines. kto_response_confidence_train.jsonl = 29886 lines.
  grpo_train.jsonl = 14888 lines, grpo_dev.jsonl = 1655 lines (per
  grpo_manifest.json and wc -l). All match cell.yaml `frozen_audit` and
  AMENDMENT.md "Datasets" exactly. G0 dataset-audit check: PASS.
- No existing scratch/schema_response_confidence/runs/*seed2* or *seed3*
  directories — confirms nothing from this block has launched yet; idempotent
  resume check has nothing to resume.

STOP before any launch verb. Read the seed-1 configs to translate the
seed-threading mechanism
(archive/experiment/phase1/grpo/configs/sft_schema_clean_response_confidence_seed1_full.yaml,
grpo_schema_clean_sft_merged_seed1_full.yaml) and confirmed against trainer
source
(synaptic-tuner/Trainers/{sft,dpo,kto}/train_sft.py|train_dpo.py|train_kto.py):
every seed-1 config carries TWO independent randomness controls — a top-level
`seed:` field (threaded to `config.seed`, which becomes the HF Trainer's
`seed=`: data order / dropout / sampling) and a separate `lora.random_state:`
field passed only to `FastLanguageModel.get_peft_model(random_state=...)`,
which seeds the LoRA adapter's initial weight matrices. These are not linked
in code. For DPO/KTO, `--seed` is a CLI override but there is NO
`--lora-random-state` CLI flag (confirmed via `train_dpo.py --help` /
`train_kto.py --help`) — `lora.random_state` is config-file-only.

Every seed-1 config sets `lora.random_state: 1`, matching `seed: 1`; the
tuner's own baseline default (synaptic-tuner/Trainers/{sft,kto}/configs/
config.yaml) is `random_state: 3407`. This could mean "mirror the seed number
into random_state" was an intentional seed-1 convention, or it could be
coincidental use of the template default that happens to equal the seed
number. Neither AMENDMENT.md, cell.yaml (whose `lora:` block fixes only `r`,
`alpha`, `dropout`, with no `random_state` key), gates.yaml, nor the
clean-mainline runbook (whose commands pass `--seed 1` and never mention
`--lora-random-state` or an equivalent) resolves this. If seed 2/3 configs
clone seed-1 and only bump `seed:`, all three "seeds"' LoRA adapters would
start from byte-identical initial weight matrices — only the data-order/
dropout stream would vary. That is a materially weaker replicate than one
where LoRA init also varies per seed, and it changes what a G1 seed-artifact
failure would even mean. This is exactly the "seed-threading mechanism
ambiguous in the docs" stop condition named in the dispatch. Not resolved by
guessing; escalated to the lead. No training or eval verb has been run. Zero
GPU time spent (nvidia-smi still 0MiB at time of writing). Zero budget burned
against the ~64h / 42h-per-seed guardrail.

### 2026-07-31 — LAUNCH: seed-2 serial chain begins (signed block, user-approved)

Launch record written BEFORE any launch verb, per the launch-order rule.

Authority: amendment signed 2026-07-31 (`bin/exp sign`, merged to main in PR
#379); user approved the direction ("worth finishing this off so we can make
this paper neat and symmetrical"), scope ("Full symmetry"), and signing ("Sign
as drafted"). GPU freed 2026-07-31 ~22:54 UTC when the KTO seed-3 eval
container exited 0.

What launches now: the seed-2 serial chain in `cell.yaml` `launch_order`
(clean_sft -> clean_sft_dpo -> clean_sft_kto -> clean_sft_grpo_v2 -> four
stage-3 stacks), then the identical seed-3 chain. Every training/eval verb runs
inside the pinned container lane: `unsloth/unsloth:latest`, digest
`sha256:f21629b9ae4ed11231768edfaed0f40d41d85d6ea9a71e8096a3d96ea0311772`
(re-verified 2026-07-31: Docker Hub `latest` last pushed 2026-05-31, byte-
identical to the June seed-1 runtime), launched `--user root` from the
canonical checkout.

G0 stop-before-outcome discipline: dataset audit already re-verified against
the frozen Amendment E §3.3 numbers on 2026-07-31 (byte-identical deterministic
rebuild, all six numbers exact); merged-source check + 192-row bounded smoke
after every merge; any G0 failure is a hard stop and a report, never a retune.

Execution is delegated to a background harness agent under a report-only
contract: it launches, watches, records each step here, and adjudicates
NOTHING. G1/G2 adjudication is lead-only after both seeds' terminal evals
exist. Budget guardrails from the signed amendment: pause and report if the
seed-2 block exceeds ~42 h or the total exceeds ~83 h.

### 2026-07-31 — draft scaffolded, gates proposed, NOT signed

Drafting pass only. Nothing signed, nothing committed, nothing launched.

Scaffolded with `bin/exp new grpo-three-seed-confirmatory --title "GRPO
Three-Seed Confirmatory Block" --type training-run`. Filled `AMENDMENT.md`,
`cell.yaml`, `gates.yaml`, and the manifest's `question` / `checkpoint` /
`instrument.configs` / `inputs`. `bin/exp validate` passes (99 experiments, no
warning against this slug — `instrument.modules` is empty, so no persistence
declaration is required). `bin/exp regen` run after the manifest edits.

`prediction:` and `falsifier:` are deliberately left EMPTY in the manifest, and
the corresponding AMENDMENT.md sections carry explicit empty-slot markers. The PI
fills the prediction and the lead fills the orchestrator prediction at sign time;
`bin/exp sign` refuses while either field is blank, so the tooling enforces it.
The gates and falsifier in `gates.yaml` are marked `status: proposed` and are
drafting proposals for lead adjudication, not settled thresholds.

**Pre-sign feasibility probe: NOT YET DONE — blocking for sign.** The
experiment-runner reference requires confirming every arm is constructible from
data that exists before signing. `scratch/schema_response_confidence/` is
uncommitted and absent from this worktree, so the four training datasets could
not be inspected. Before sign, rebuild them from
`archive/experiment/phase1/grpo/build_schema_response_confidence_datasets.py
--include-ambiguous-middle` and record here: path, row count, and the clean-SFT
audit against the frozen Amendment E numbers (14,943 rows / 7,981 known / 6,414
unknown / 548 ambiguous / 2,489 unique targets / range [0.3508, 0.90],
`experiments/probe-scaled-response-confidence/AMENDMENT.md:199-206`). A mismatch
is a hard stop.

**Open items carried to the lead** (detail in AMENDMENT.md):

- Amendment G overlap. `best-stack-replication-scale-gate` (DRAFT) already
  registers the same seed-2/3 replication for the single best stack. This block
  is a strict superset; both cannot be signed as written.
- Lane. PROTOCOL v0.3 §3.4 scopes the 3090 as the dev/smoke lane, not the matrix
  lane (`archive/docs/protocols/phase1/PROTOCOL.md:543-545`). This block is a
  serial tens-of-hours matrix on the 3090. Flagged, not resolved.
- Intermediate-stage gate evals. Proposed: keep both the 192-row bounded smokes
  (already frozen by Amendment F §8, non-discretionary) and the full evals on the
  stage-1 base and stage-2 arms (they are terminal arms and the G1 denominator,
  not intermediates).
- Budget correction. Measured seed-1 full-eval wall-clock is 21–41 minutes per
  arm, not ~4 h; ~4 h is the total across all eight evals in a seed. The ~24 h
  training figure per seed holds (measured 26.2 h).
