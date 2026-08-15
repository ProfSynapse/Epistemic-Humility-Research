# Instruction-free abstention internalization: seed robustness of the P-struct readout notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

### 2026-08-14 ~17:20Z — launch (GPU freed by panel completion)

prompt-vs-training-panel config 4 completed 17:19Z (exit 0); all 11 panel
arms are on disk. GPU free. Launching this cell's single config now:
container `eh-seedrobust-pstruct-<ts>`, same invocation shape as the panel
containers (unsloth image, --entrypoint python3, run_eval.py --live-vllm),
six arms, results to
archive/experiment/phase1/eval/results_pstruct_internalization_seed_robustness_4b/.
Sentinel watcher + standing Monitor armed in this turn. This entry precedes
the launch verb.

### 2026-08-14 ~14:40Z — signed; PI sign+launch approval; queued behind panel

Cell signed (3 pins). PI approved sign AND launch in this conversation
("yes sign and launch", 2026-08-14), all six arms including the DPO/KTO
negatives. PI also confirmed abandoning the cold-GRPO instructed seeds 2/3
TRAINING replication ("lets abandon the grpo seeds for now"); this eval-side
cell is the confirmatory replication for the internalization claim instead.
Launch is QUEUED: the GPU is running prompt-vs-training-panel config 3
(P-struct cold), then panel config 4 (P-struct warmed). This cell's single
config launches on config 4's completion wake. The launch turn will add the
entry here before the launch verb, with sentinel watcher + Monitor armed per
the launch-turn watcher rule.
