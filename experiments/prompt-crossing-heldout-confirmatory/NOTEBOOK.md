# Prompt-crossing held-out confirmatory: promoting the paper-2 prompt-condition claims on out-of-distribution surfaces notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

- (add dated entries as the experiment progresses)

## 2026-08-17 — Launch: one aborted false start (host GPU runtime), zero run artifacts

PI launch approval given in-conversation 2026-08-17. First launch attempt
(runner 1): stage 0 verification PASSED in full (row counts 1832/5540/46;
ood.py / run_eval.py / scorers.py shas exact; all 20 checkpoint paths
present; all 10 pinned shas match experiment.yaml instrument.pins; docker
image digest exact) but the first stage-1 container
(eh-phc-eval-base-prc-20260817T140207Z, config eval_heldout_base_prc)
failed at docker run with exit 125, "could not select device driver with
capabilities: [[gpu]]". Zero generations; no results_dir created; runner
STOPped per the hard-stop rule without attempting remediation.

Lead diagnosis: host reboot left Docker Desktop stopped, so
/var/run/docker.sock fell back to a native in-distro daemon with no nvidia
runtime (its only container history is failed launches, including an
identical-signature failure dated 2026-08-03). Docker Desktop restarted by
the lead; engine verified retaken (Operating System: Docker Desktop,
Runtimes include nvidia; pinned image digest present; live --gpus all
nvidia-smi smoke returned RTX 3090 24576 MiB, no generation). Instrument,
configs, and gates untouched — infrastructure-only false start, same class
as prompt-vs-training-panel's logged false starts.

Runner 2 dispatched with the same brief plus a per-launch engine check
(STOP if the socket ever reverts off Docker Desktop mid-campaign).
