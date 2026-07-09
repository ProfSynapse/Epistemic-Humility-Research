# Amendment AK Stage 1 Artifacts

Committed Stage 1 readout artifacts for the Amendment AK commitment-point experiment.

- `ak_stage1_pilot_floor.json` locks the AK-G2 pilot-derived floor before the full readout.
- `ak_stage1_gate_report.json` records the full AK-G1 and AK-G2 machine-readable report.
- `ak_stage1_gate_verdicts.md` is the committed human-readable Stage 1 verdict record.

The runnable analysis scripts remain in `experiment/phase1/probe/`:

```bash
python archive/experiment/phase1/probe/amendments/amendment_ak_stage1_pilot_floor.py --grpo-dir <grpo-v2-arm-dir> --raw-dir <raw-base-arm-dir>
python archive/experiment/phase1/probe/amendments/amendment_ak_stage1_analyze.py --grpo-dir <grpo-v2-arm-dir> --raw-dir <raw-base-arm-dir>
```

`amendment_ak_stage1_analyze.py` prints its generated Markdown summary to stdout.
Use `--report-md <path>` only when deliberately persisting that generated summary;
the committed human-readable verdict is `ak_stage1_gate_verdicts.md`.
