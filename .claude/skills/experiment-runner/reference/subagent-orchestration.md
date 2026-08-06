# Subagent orchestration for GPU runs

How to divide labor between the orchestrating lead and a GPU-runner subagent
so that platform messaging limitations cannot stall an experiment arc. Written
from three identical failures in one session (the AH main-run tail, the PAR
mining scorer, the AH §6 instrumentation tail); the failure mode is
structural, so treat these rules as defaults, not superstition.

## The two platform facts everything follows from

1. **A subagent's "completion watcher" dies at its turn boundary.** When a
   runner launches a background GPU job and promises to "watch for
   completion," nothing re-wakes it when the job finishes. Only an inbound
   message wakes an idle subagent. Every watcher armed this way has failed.
2. **Messages queue at turn boundaries; they do not interrupt.** A message
   sent to a mid-turn subagent is delivered only when its current turn ends.
   Instructions and reports therefore cross in flight, and each party can end
   up reacting to the other's previous state. Do not send course-corrections
   to a busy runner; wait for its idle notification.

Idle notifications are themselves noisy: they fire at every turn boundary
(including mid-arc with a background job still running) and can arrive as
duplicates or out of order relative to content messages. An idle notification
means "my turn ended," not "my work is done."

A corollary that has now destroyed real work: **queued directives can be
executed after the world has moved past them.** A runner processed a HOLD
one wake-cycle after it had already satisfied the follow-up GO (it launched
the corrected run, went idle, then woke on the stale HOLD and killed that
correct run at step 4). Mitigations, all three:

- **Sequence-stamp directives with a monotonic identifier** — a git SHA is
  ideal ("pull before acting; this order applies at 67c08f92"). State
  explicitly that when two directives conflict, the later-SHA one wins.
- **Make destructive directives self-invalidating**: "stop the run UNLESS it
  was launched from ≥ <SHA> / with <property>" rather than "stop the run."
- **Receivers check world-state before destructive execution**: before
  killing a run, read its manifest — if it already satisfies the correction
  the HOLD was protecting, the HOLD is moot; ask instead of acting.

## Division of labor (the rules)

- **Runners launch GPU jobs and write scripts. The lead owns every analysis
  tail.** The moment outputs exist on disk, the lead runs the scorer /
  gate-checker / extractor tail itself — runner scripts are normally
  pre-validated and CPU-runnable. Do not wait for the runner to notice its
  own job finished; it will not.
- **Verify progress from disk, never from narration.** Row counts in output
  jsonl files, log tails, file mtimes, `nvidia-smi` — these are the truth.
  A runner's claim that an artifact was staged must be checked before it is
  relied on (a claimed file has been absent from disk before).
- **Tell the runner to run tails in the completion turn, not to arm a
  watcher** — and expect that to fail anyway, because the completion signal
  it is waiting on may never arrive. The lead's disk check is the real
  backstop.
- **Adjudication and gate arithmetic are recomputed by the lead from raw
  rows** before any verdict is written. The runner's numbers are a
  cross-check, not the source of record (twice now both computations agreed
  exactly; keep it that way by keeping them independent).
- **A quiet runner is not a dead run.** Check the GPU and the output
  directory before concluding anything: an idle notification with the GPU at
  70% means the background job is fine and the runner's turn simply ended.

## Delegation prompts: specify the invariant, not the mechanism

A distinct failure from the messaging problems above, from four of the
lead's own errors in one work cycle: after learning a verification
mechanism for one tool, the lead repeatedly told a subagent to apply that
SAME mechanism to a different tool that does not expose it.

1. Told the executor to `--dry-run` an eval launch; the eval harness
   (`run_eval.py`) has only `--config` and `--live-vllm`, no `--dry-run`
   flag. The trainers have `--dry-run` (e.g. the GRPO trainer,
   `Trainers/grpo/train_grpo.py:159`); the eval harness does not.
2. After a KTO LoRA-defaults near-miss, told it to pass explicit
   `--lora-r`/`--lora-alpha`/`--lora-dropout` to the GRPO trainer. KTO and
   DPO accept those flags; the GRPO trainer's argument parser has none of
   them (its only overrides are `--config`, `--dry-run`,
   `--resume-from-checkpoint`, `--model-name`, `--dataset-name`,
   `--dataset-file`, `--local-file`, `--use-gspo`, `--pivot-profile-only`).
   GRPO's LoRA values come only from its YAML config.
3. Scoped a stdout data-leak hazard to the GRPO trainer specifically; all
   four production trainers (SFT, DPO, KTO, GRPO) do it, each via its own
   independent `print_dataset_samples` implementation.
4. Asked for "config files" and a structured diff for DPO/KTO-trainer arms.
   DPO and KTO have no `--config` argument at all, only CLI-flag overrides
   on a fixed baked-in `configs/config.yaml`, so there is no per-run config
   file to diff for either. GRPO does take `--config <path>`, and that YAML
   can carry a `rewards.custom.file` reward-file path; that mechanism is
   GRPO-only.

Every one of these was caught only because the subagent reported the
mismatch instead of silently complying. Had it complied: a fabricated
config file, a diff of nothing, or a verification step that silently
checked nothing while appearing to pass.

Rule: state the INVARIANT to establish, not the command to run, and require
the agent to report which route it used. Do not write "pass `--lora-r 32`
and confirm in the dry-run banner"; write "confirm the resolved LoRA rank
matches the registered value by whatever route this trainer exposes, and
report which route you used and what it showed." Corollary: when a
subagent reports that an instruction does not apply to the tool in front of
it, that is a successful verification result, not a failure to follow
instructions, and should be recorded as such rather than treated as
friction.

## Practical cadence for a long GPU pass

1. Lead pushes the branch and sends ONE self-contained launch order
   (inputs, recipe, gates, output paths, conventions) while the runner is
   idle.
2. Runner scripts, commits, launches in background — then idles. Expected.
3. Lead polls the disk at the job's natural timescale (row counts vs total,
   log tail, `nvidia-smi`).
4. When the outputs are complete, the lead runs the tail immediately and
   commits the result; a nudge message to the runner is optional and only
   for handing it the NEXT job.

## Upstream tracking

The queue-at-turn-boundary behavior is confirmed and unfixed upstream:
anthropics/claude-code#30492 (priority message channel, proposed),
#21419 (message running agents without stopping them). If either ships a
real interrupt primitive, revisit this file.
