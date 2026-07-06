# Cell YAML schema (the six blocks)

A cell.yaml fully describes one steering/readout experiment. The runner parses it
into a `Cell`; the `plan` command echoes the parsed structure without loading a
model. Paths inside the config resolve relative to the config file's directory
unless absolute.

```yaml
name: my_cell            # output dir stem; defaults to the file stem

# 1. SURFACE -----------------------------------------------------------------
surface:
  rows_file: path/to/rows.jsonl     # questions + baseline grades (JSONL)
  question_field: question          # field holding the question text (default: question)
  row_key_field: row_key            # stable per-row id (default: row_key)
  generation:
    model: <hf-repo-or-local-path>  # base model
    adapter: <hf-repo-or-path>      # optional PEFT LoRA on top of the base
    adapter_revision: <git-sha>     # optional pinned adapter revision
    system_prompt_ref: <ref>        # see "system_prompt_ref" below; omit => ""
    enable_thinking: false
    max_new_tokens: 96
    seed: 20260705                  # seeds selection (permuted) + decode
    decode: {do_sample: false, num_beams: 1}
    expected_config_sha: <64-hex>   # optional; set at signing (see run-and-sign.md)

# 2. READOUTS ----------------------------------------------------------------
readouts:                # frozen directions scored at the pre-generation anchor
  - name: prop           # law references prop_z (z-score) and prop_raw (projection)
    path: path/to/direction.json   # JSON with "theta" (or "d"), "layer", "mu", "sigma"
    layer: 35            # hidden_states index to read (overrides the JSON's layer)
    mu: 0.0              # optional; overrides the JSON's mu
    sigma: 4.2           # optional; overrides the JSON's sigma; REQUIRED for setpoint
    record_readback: true

# 3. LAW (base; arms override) ----------------------------------------------
law:
  actuation: setpoint    # additive | setpoint | none
  actuation_readout: prop  # which readout supplies the direction (needed if >1)
  gain: 2.0              # alpha (additive) or g (setpoint: writes g*sigma)
  position: anchor_onward  # anchor_only | anchor_onward | answer_window | none

# 4. ARMS --------------------------------------------------------------------
arms:
  - tag: primary
    description: "..."
    row_subset: flagged_only   # omit to generate all rows (untouched where unflagged)
    law:                       # merged over the base law
      selection:
        expression: "prop_z >= 1.0"   # over the row's readout scalars
  - tag: control
    row_subset: flagged_only
    law:
      selection:
        permuted: {match_count: null}   # null => match the run-time flag count
  - tag: unsteered
    law:
      actuation: none
      selection: {all: true}

# 5. LANE is not in the YAML: local = steer_cell.py, cloud = modal_steer_cell.py.

# 6. SMOKE -------------------------------------------------------------------
smoke:
  n: 40                       # rows in a smoke pass
  readback_tolerance: 0.5     # max |commanded - observed| anchor coordinate move
  offtarget_parity: 0.001     # max drift on unflagged rows (informational)

# OUTPUTS (untracked) --------------------------------------------------------
outputs:
  dir: ../../analysis/steer_cells/my_cell   # default if omitted
```

## Actuation modes

- `additive`: `h += alpha*d` at the steered positions (the AL push / Arm A).
  `gain` is `alpha`. Uses `confidence_steer.SteeringHook`.
- `setpoint`: `h' = h - (h.d)d + g*sigma*d` - erase the direction's coordinate
  and write the commanded setpoint `g*sigma` (the AC/AN couple). `gain` is `g`;
  the readout MUST carry `sigma`.
- `none`: readout-only; generate untouched and record readout scores per row.

## Position policy

- `anchor_only`: steer the single pre-answer anchor token (prompt's last token).
- `anchor_onward`: anchor at prefill + every generated position (decode stream).
- `answer_window`: same decode-stream coverage as anchor_onward (named separately
  so a future window policy can narrow it without a schema change).
- `none`: no steering (`actuation: none`).

## Layer indexing

A readout's `layer` L is a `hidden_states` index: `hidden_states[L]` is the OUTPUT
of decoder block `L-1` (`hidden_states[0]` is the embedding). The runner registers
the hook at `layers[L-1]` so the write lands where the direction was fit. Match the
direction JSON's `layer`/`block` fields (the AN direction records `layer: 35,
block: 34`).

## system_prompt_ref

Three forms:
- `literal:<text>` - inline text.
- a path to a `.txt`/`.json` file - the file's contents (JSON is `json.load`ed).
- `module:function` - a dotted import that returns the prompt string, e.g.
  `amendment_ah_stage0_extract:load_baseline_system_prompt` (byte-parity with the
  baseline harnesses).

## Selection expression sandbox

`expression` is evaluated with only the row's readout scalars (`prop_z`,
`prop_raw`, ...) plus `abs/min/max`. No builtins, no file/OS access. A missing
readout name raises a clear error rather than silently selecting nothing. A
readout without `mu`/`sigma` has no `_z`; reference `_raw` instead.

## Provenance the runner writes

Under the output dir: `manifest.json` (config sha256 + full surface/readouts/arms
provenance), per-arm `gen/rows.jsonl` (one row per row_key: scores, arm, flagged,
gain, refused, answer_text), and for a smoke `readback.json` + `smoke_state.json`.
All untracked.
