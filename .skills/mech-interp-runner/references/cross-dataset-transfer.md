# Cross-Dataset Transfer Protocol (C-track)

Test whether a read-side finding (caution axis, belief-action gap, knowledge
axis) **generalizes to a second known/unknown dataset**, rather than being a
SelfAware-specific artifact. The pipeline is dataset-agnostic: point it at any
JSONL with an intrinsic answerable/unanswerable label.

Five steps. Steps 1, 3, 5 are GPU-free CLI; steps 2, 4 are Docker/GPU and need
the user's live-run approval. Every step reuses checked-in scripts — do not
hand-roll.

## 0. Pick a dataset and check the construct

The single most important design check: **what does "known" mean in this
dataset?** Two incompatible constructs exist and they change the interpretation:

- *Model-knowable* (e.g. SelfAware filtered to questions the model can answer):
  `known_refused` is genuine **over-refusal**, and the belief-action gap reads as
  a "humility tax" (refuses despite internally knowing).
- *Answerable-in-principle* (e.g. KUQ: has a gold answer, but may be obscure
  trivia the model does not know): `known_refused` is dominated by **genuine
  ignorance**, and the belief-action gap reverses (refusals look internally
  UNKNOWN = appropriate abstention).

Both are valid transfer targets, but report which construct you ran. A
belief-action / humility-tax claim **only** holds on a model-knowable "known"
set. Also confirm there is no trivial syntactic confound (e.g. both classes
should be interrogative) before spending GPU.

## 1. Build the panel (GPU-free)

```bash
python .skills/mech-interp-runner/scripts/mechinterp_cli.py xdataset-build-panel \
  --source datasets/<ds>/<file>.jsonl --dataset <ds> \
  --out-dir archive/experiment/phase1/probe/xdataset/<ds>_panel \
  --n-known 600 --n-unknown 400 --seed 0
```

Emits `gen_rows.jsonl` (generation input) and `manifest.json` (frozen extraction
manifest, schema `mechinterp-selfaware-frozen-row-manifest/v1`) sharing one
`row_key` per question so generation behavior and activations join downstream.
Field overrides: `--question-field`, `--unknown-field` (truthy = unknown),
`--answer-field` (-> aliases). Over-sample known (the over-refused subset powers
the A2 caution-axis split, and its size is unknown before generation).

## 2. Baseline generation (Docker/GPU; needs approval)

Use
`experiments/xdataset-probe-transfer/mechinterp_xdataset_kuq_baseline_generation.yaml`
as the KUQ template for a new `<ds>` config: point `rows:` at the panel
`gen_rows.jsonl`, set `output.root`
under `xdataset/<ds>_generation`, keep `sweep.alphas: [0.0]` (the no-hook
baseline — `by_block={}`, so the reused `steering_directions` are loaded but
never applied). Then run the head-intervention runner in Docker (see
`resumable-gpu-sweeps.md` for the launch shape). Greedy, `enable_thinking:
false`, the JSON response-confidence prompt.

## 3. Assemble behavior rows (GPU-free)

```bash
python .skills/mech-interp-runner/scripts/mechinterp_cli.py xdataset-behavior \
  --generation archive/experiment/phase1/probe/xdataset/<ds>_generation/rows.jsonl \
  --panel-rows archive/experiment/phase1/probe/xdataset/<ds>_panel/gen_rows.jsonl \
  --out-dir archive/experiment/phase1/probe/xdataset/<ds>_behavior
```

Joins the baseline (`no_vector_baseline`) generation `refused`/`correct` + label
back to question text and derives the canonical 5-way `behavior_cell`
(`known_refused`, `known_correct_answered`, `known_answered_wrong`,
`unknown_refused`, `unknown_answered_wrong`). The summary's `n_known_refused` is
the A2 split size — sanity-check it is large enough.

## 4. Extract hidden states (Docker/GPU; needs approval)

Use `experiments/xdataset-probe-transfer/hidden_state_kuq_manifest_clean_sft_grpo_v2_seed1_full.yaml`
as the KUQ template:
set `model.model_tag` to a `<ds>`-specific, gitignored (`qwen3-4b-*`) tag,
`selection.manifest` to the panel `manifest.json` (path is relative to the probe
dir), and `output.hidden_states_subdir`. Keep both arms + `persist_delta: true`
so `h_base`/`h_lora`/`delta` are all available; `final_prompt_token`,
`residual_stream`. **Use the same extraction prompt as the SelfAware run** (the
full-run config has no `prompt:` block -> default render) so the cross-dataset
comparison is faithful. Run the extractor (`hidden_state_probe.py --config ...`)
in Docker.

## 5. Read-side probes + transfer (GPU-free)

Run the same Track-A controls used on SelfAware (see
`interpretation-invariants.md`), pointing `--extraction-dir` at the new
extraction and `--behavior-rows` at the `<ds>_behavior/rows.jsonl`:

- `latent_knowledge_controls.py` -> A1 lexical baseline, A2 within-known
  caution axis, axis_geometry (does the property replicate?).
- `latent_knowledge_probe.py` -> Readout2 over-refusal gap (does the
  belief-action gap replicate or reverse?).
- `caution_axis_transfer.py` with two arms
  (`selfaware_grpo_v2:<SA_ext>:<SA_beh>` and `<ds>_grpo_v2:<ds_ext>:<ds_beh>`)
  -> cross-DATASET cosine of the fitted caution directions. **Match the layer**
  across both arms. Distinguish the verdicts: a replicated *property* (A1/A2/geom)
  is NOT the same as a transferred *direction* (high cross-dataset cosine). They
  can and do dissociate.

## Gotchas (durable)

- **Container UID.** The Docker user is uid 1001; it cannot write into host-owned
  dirs (default 755). Pre-create each GPU output dir on the host and `chmod 777`
  it before launching, or the run dies on `mkdir`/`write` PermissionError. (`analysis/`
  is already 777; new `xdataset/` subtrees are not.)
- **Cosine layer must match.** The caution axis can peak at different layers per
  dataset (e.g. L35 vs L32). Run the transfer cosine at one fixed shared layer;
  report it.
- **Property vs direction vs meaning.** The headline is rarely "it transfers."
  Expect: the axis *properties* (deep, lexically-clean, knowledge-orthogonal) are
  often dataset-robust, while the *direction* (cosine) and the *behavioral
  meaning* (gap sign) are construct-conditioned. State all three separately.
- **Provenance.** Panel inputs (`gen_rows.jsonl`, `manifest.json`,
  `panel_meta.json`) are deterministic and committable; all generation,
  behavior, extraction, and analysis outputs stay gitignored
  (`xdataset/.gitignore` + the `analysis/` / `hidden_states` rules).
