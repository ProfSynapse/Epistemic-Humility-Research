# J-lens on a trained checkpoint plus rule-selected mid-band refusal-axis ablation notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

- (add dated entries as the experiment progresses)

## 2026-08-16 — lead adjudication of prep flags; cell.yaml/gates.yaml filled

Prep builder's deliverables spot-checked by the lead: jlens_trained.py parses
(ast), and the intervention TEMPLATE differs from the governed seed-1 config
by exactly two substantive lines (caution_direction and output.root, both
{SITE}-keyed into this cell's gitignored analysis/) plus a header comment
documenting the instantiation rule — all other lines byte-identical.

Flag adjudications:
1. Stage-7 fallback timing: ACCEPTED as the full 4-arm re-run of the archived
   byte-pinned config (~49 min actual, not the AMENDMENT's ~12 min estimate),
   using only the ablate arm's rows. Building a new single-arm config would
   mean an unsigned instrument variant; the time cost is the cheaper risk.
   The AMENDMENT's estimate is superseded by this note (estimate, not a gate).
2. --model/--adapter required=True with no defaults: ACCEPTED — forces
   explicit, driftless invocation.
3. Running J-lens smoke/profile inside the same unsloth docker container as
   the intervention: ACCEPTED — torch/peft stack parity and reproducibility
   outweigh bare-host convenience.
4. Template rows/direction lines riding the legacy experiment/phase1/probe
   symlink chain: ACCEPTED for byte-parity with the governed config; the
   symlinks exist from the rederivation cell and are a launch-time
   environment check (noted in cell.yaml), never a config edit.
