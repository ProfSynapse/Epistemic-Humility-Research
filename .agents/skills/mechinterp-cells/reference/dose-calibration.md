# Dose calibration: locate the coherent window before the real ladder

For `erase_write` steer cells. Read this when choosing `law` strengths / the
`arms` dose ladder for a new cell, or when a dose "does nothing" or produces
garbage.

As of Synaptic Tuner `f09db5f`, the default implementation is the config-driven
`mechinterp dose-calibrate` verb. Older bespoke sweep scripts remain valid
provenance for the experiments that used them, but new cells should express the
ladder in YAML so checkpointing, resume, readout expansion, and summaries are
generic.

Minimal schema:

```yaml
surface:
  rows_path: experiments/<slug>/analysis/rows.jsonl
  generation:
    max_new_tokens: 64
    do_sample: false
    temperature: 0.0
    top_p: 1.0
    seed: 0
readouts:
  - name: hs34
    path: experiments/<slug>/directions/axis_hs34.json
law:
  kind: erase_write
  readout: "*"       # or a single readout name
  position: anchor_onward
  generation_mode: gen_stream
calibration:
  doses: [0, 25, 50, 75, 100, 125, 150, 175, 200]
  dose_kind: setpoint
  selection:
    flag_field: confab_selected
execution:
  output_path: experiments/<slug>/analysis/dose_calibration_rows.jsonl
  summary_path: experiments/<slug>/analysis-committed/dose_calibration_summary.json
  resume: true
  render_fn: example_render:render
  grader: example_grader:grade
  batch_size: 1
```

Run from the repo root:

```bash
PYTHONPATH=experiments/common/renders:experiments/common/graders \
python synaptic-tuner/tuner.py mechinterp dose-calibrate \
  --mi-config experiments/<slug>/dose_calibration.yaml \
  --model unsloth/Qwen3-4B \
  --i-know-this-runs-on-gpu
```

The checkpoint JSONL is append-only and resumable by `(readout, dose, row_key)`.
The committed artifact should normally be the aggregate summary plus provenance,
not restricted row text or per-row generations.

## Why dose is not a free parameter

`erase_write` writes an ABSOLUTE coordinate along the readout:

```
h' = h - (h . d) d + strength * sigma * d
```

The behavioral response is NOT proportional to `strength`. The model ignores the
write until the commanded setpoint departs far enough from the activation's own
ambient projection along `d`; then it responds; and past a further point it
over-drives into degenerate output. Every erase_write direction has three
regimes:

- **inert** - setpoint too close to ambient; output byte-identical to baseline.
- **coherent window** - output changes AND stays well-formed; the only usable
  regime.
- **collapse** - over-driven; output degenerates (a common signature is one
  repeated token, e.g. `{\nIIIIII...`).

## The window can be narrow (measured)

dark-actuator-screen `pos_ctrl_L34` (raw-base answer-vs-refuse mass-mean axis,
layer 33, 2026-07-06, real tuner `GenerationInterventionController` +
`InterventionHook(erase_write, anchor_onward, gen_stream)`):

| substrate | inert | coherent window | collapse |
|-----------|-------|-----------------|----------|
| bnb-4bit | setpoint <=100 | **~150-300** | >=400 |
| bf16 (Qwen3-4B) | <=20 | **~100** | >=500 |

Ambient projection along the direction was ~19-27 on both substrates, so the
coherent window sits at roughly **7-14x the ambient projection**. A coarse
absolute ladder that samples, say, 100 and 500 jumps clean over the bnb-4bit
window and reports a false "no effect" - which for a positive control VOIDS a
screen (G-instrument), and for a candidate MISLABELS a real lever as inert. The
first coarse pass in this diagnostic did exactly that and produced a retracted
"base-lever null."

## Rules

1. **Dose ambient-relative, not absolute.** Express strength as a multiple of the
   direction's own ambient projection (setpoint = `k * mean(h . d)` over the row's
   baseline decode); start with `k` in roughly `[5, 15]`. Different
   directions/layers have different ambient scales, so a single absolute strength
   is not comparable across them.
2. **Run a pilot dose sweep first** to locate `[k_move, k_collapse)` per direction
   before committing the real ladder. Sample finely enough that adjacent rungs
   cannot straddle the whole window (steps of ~1-2x ambient, not 5x jumps). Report
   per row: smallest `k` that moves tokens, smallest `k` that collapses, and how
   many rows have a usable window at all (some may have none).
3. **The window can differ across substrates.** Quantization (bnb-4bit) shifts it
   modestly higher than bf16; recalibrate on the actual run substrate - do not
   port an absolute ladder across precisions.
4. **A passing smoke does NOT mean the dose moves behavior.** The smoke readback
   (`write_rel_tol` / `max_write_err`) measures WRITE ACCURACY (commanded vs
   realized coordinate); it is small and passing across the ENTIRE ladder,
   including inert and collapsed doses. It says the hook wrote what you asked, not
   that the write changed anything. Whether tokens actually move is a separate
   check - the `gen_stream` decode-hook-firing guard (byte-identical output ->
   refuse) is what catches an inert dose; keep it enabled.

## gen_stream and the `position` field

In `gen_stream` mode the engine edits every decode step at `anchor_onward`
regardless of the recipe's `position` field (`answer_window` and `anchor_onward`
collapse to the same decode-time behavior). Choose the intended write span knowing
this.
