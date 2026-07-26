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
4. **Per-cell grids in a matrix: a recalibration fix does NOT propagate to
   sibling cells.** Measured (doubt-snap-cross-family-confirmatory, 2026-07-08
   to 2026-07-11): the default absolute grid 100-250 was recalibrated for the
   two Qwen3.5 cells after overdose collapse at ~38 sigma, but the sibling
   llama and mistral cells kept the default and burned a full FIT sweep each
   on a predetermined collapse. Their own sigma_c (2.09 and 0.94) put the
   default grid at 49-120 sigma and 107-267 sigma respectively; sigma_c varied
   14x across the matrix (0.94 to 13.6), so no absolute grid can serve two
   cells. Before launching ANY steering cell, compute the realized z-range
   `(dose - mu_c) / sigma_c` from that cell's own build/pilot fit and hold it
   inside the calibrated coherent band (the working cross-family grids sat at
   roughly 5-30 sigma, consistent with rule 1's ambient-relative window);
   treat a missing per-cell entry in a matrix-wide grid table as a launch
   blocker, not a fallback to the default. CAVEAT, measured the same day
   (2026-07-11): the z-band itself does NOT transfer across families either.
   Mapping the working Qwen3.5-4B z-ladder (6-29 sigma) onto llama and
   mistral via each cell's own mu_c/sigma_c gave a real dose-response on
   llama but a fully inert grid on mistral (zero token movement at 29 sigma,
   where llama responds at 5-13 sigma). Sigma-mapping is a first guess only.
   Before launch, bracket each cell empirically: one probe generation at the
   grid's strongest arm strength (must move tokens) plus any prior-dose
   evidence bounding collapse from above, and set the grid to log-span that
   bracket. A grid whose maximum has never been shown to move tokens on that
   substrate is not launchable.
5. **Aggregate dose-invariance is the overdose signature.** If every graded
   cell count is byte-identical at every dose while completions differ
   slightly (94-99.9 percent pairwise identity, not 100 percent), the sweep is
   saturated in collapse: 100 percent of fired rows degenerate at all doses.
   Do not read such a null as family-level insensitivity or as a plumbing
   failure; check the z-range first. (Fully identical completions across doses
   would instead indicate the dose never varied - a genuine plumbing
   signature.)
6. **A passing smoke does NOT mean the dose moves behavior.** The smoke readback
   (`write_rel_tol` / `max_write_err`) measures WRITE ACCURACY (commanded vs
   realized coordinate); it is small and passing across the ENTIRE ladder,
   including inert and collapsed doses. It says the hook wrote what you asked, not
   that the write changed anything. Whether tokens actually move is a separate
   check - the `gen_stream` decode-hook-firing guard (byte-identical output ->
   refuse) is what catches an inert dose; keep it enabled. Do NOT tie the
   gen_stream probe strength to `max(dose_grid)`: that makes the plumbing
   check inert for any legitimately low-dose grid and the smoke refuses a
   healthy harness (measured, mistral7b 2026-07-11). Use a fixed strength
   already shown to move tokens on some substrate (e.g. 250) for the
   plumbing check, and cover "does the strongest arm move tokens on THIS
   substrate" with the separate pre-launch bracket probe from rule 4.

## Terminal-site space mismatch (post-final-norm states)

A captured hidden state indexed `hsN`, where `N` equals the model's total
block count, is NOT block `N-1`'s output. HF's `utils/output_capturing.py`
collects `[embeddings, block0_out, ..., block(N-1)_out]` and then OVERWRITES
the final entry with `last_hidden_state` - the state AFTER the model's
final norm. A capture pipeline that names its N+1 hidden-state slots
`hs0..hsN` inherits this silently: `hsN` is a different KIND of state than
every other entry in the same list.

This bites any experiment whose `erase_write` readout or fit site happens to
land on that final index - and it bites the dose ladder in two independent
ways, both measured on the same cell (a 42-block model, site `hsN` where
`N` = block count):

- **Fingerprint.** Post-RMSNorm states sit on the `RMS(h / norm.weight) = 1`
  manifold; interior states do not. Measured: `1.00004` at the terminal site
  vs `340 / 355 / 322` at three interior sites on the same checkpoint. Run
  this as a preflight assertion at every capture site before fitting or
  dosing - it is a two-line check and it catches the defect before either
  downstream bug fires.
- **Space mismatch.** A direction fitted on the post-norm state but WRITTEN
  into the pre-norm residual (because the write hook addresses "layer N-1's
  output," the interior convention) writes into a different space than it
  was fit in, related only by the diagonal `norm.weight`. Measured:
  `cos(c_hat, unit(norm.weight * c_hat)) = 0.9873` - close to 1, not
  identical; small but real and not a rounding artifact.
- **Ladder inflation.** If the dose ladder is scaled to the terminal site's
  own median activation norm, every dose at that site is inflated relative
  to the interior sites' true write-site scale, because the post-norm norm
  and the pre-norm write-site norm are different quantities. Measured:
  ladder scaled to a post-norm median of 281.34 against a true write-site
  scale of ~118-126, inflating every dose ~2.38x at that one site - which
  turned a real onset-ratio gap of ~1.5x between sites into an apparent
  ~3.6x gap, large enough to read as a distinct terminal-layer phenomenon
  when it was a ladder artifact.

**Rule.** Before fitting a direction or building a dose ladder at any site,
run the `RMS(h / norm.weight) ~= 1.0` check at that site. If it fires,
either drop that site or fit AND write in the same (post-norm) space and
scale its ladder to that space's own norms - never assume the interior
convention applies there. The general trigger is a site index equal to the
model's block count; a family whose chosen sites never coincide with its
own block count is unaffected and needs no special handling.

## gen_stream and the `position` field

In `gen_stream` mode the engine edits every decode step at `anchor_onward`
regardless of the recipe's `position` field (`answer_window` and `anchor_onward`
collapse to the same decode-time behavior). Choose the intended write span knowing
this.
