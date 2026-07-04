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
