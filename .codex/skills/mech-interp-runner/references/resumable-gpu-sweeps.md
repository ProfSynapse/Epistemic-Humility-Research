# Resumable GPU Sweeps (checkpoint/resume)

Load this when launching a long GPU sweep that might outlive the CLI session.

Long GPU sweeps are killed mid-run when the CLI session is torn down (Monitor
timeout, agent teardown, host restart). Two rules keep a partial sweep cheap to
recover:

1. **Detach the container so it outlives the CLI.** A foreground
   `docker.exe run --rm ...` launched via a background Bash shell dies when that
   shell is reaped, taking the GPU work with it. Launch with `docker.exe run -d
   --name <run>` instead, then poll `docker.exe logs <run>` / the output
   `summary.json`, and watch terminal state with
   `docker.exe inspect -f '{{.State.Status}} {{.State.ExitCode}}' <run>`. The
   detached container keeps running across CLI restarts.

2. **Make the runner resume by default.** Stream per-row results to
   `rows.jsonl` (flush per row) keyed by a unique work unit — for the per-head
   ITI runner that is `(arm_id, probe_pool_row_key)`. On start, read the existing
   `rows.jsonl`, skip completed units, and append only the missing ones; tolerate
   a truncated final line (killed mid-write) by dropping it so that unit
   regenerates. Load the model lazily so a fully-resumed run re-emits the summary
   with no GPU. Guard resume with a `checkpoint.json` fingerprint over everything
   that defines a unit (model, adapter, prompt, steering path, rows, alphas,
   `max_new_tokens`, `max_rows`); refuse to resume on mismatch unless `--fresh`,
   so two configs never mix in one `rows.jsonl`. Reference implementation:
   `experiments/common/mechinterp/head_intervention_runner.py` (`run_config(..., fresh=...)`,
   `_load_completed`, `_config_fingerprint`); greedy/deterministic decoding makes
   resumed rows identical to a clean run.
