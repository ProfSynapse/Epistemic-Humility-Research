# GRPO Three-Seed Confirmatory Block notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

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
