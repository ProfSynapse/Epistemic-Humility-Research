# Qwen3.5-4B family atlas notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

### 2026-07-24 -- GPU window: submodule wired, capture fired

Lead authorized (in my worktree only) initializing the `synaptic-tuner`
submodule and checking it out to the fixed tuner commit, then sent GPU FREE
(0MiB confirmed, gemma j-space queued behind). Recording the wiring here per
the AG0 stale-gitlink failure mode this gate was written for.

**Submodule wiring (before -> after).**
- BEFORE: `synaptic-tuner` uninitialized (`git submodule status` leading `-`),
  recorded gitlink `901dbe803699e0bf00b73426526babdaf8598cf3`, `tuner.py` absent.
  As-staged, capture would have resolved the tuner at the stale gitlink
  (pre-multimodal-fix) or found nothing -- the silent garbage-weight load AG0
  guards against.
- ACTION: `git submodule update --init synaptic-tuner`;
  `git -C synaptic-tuner fetch origin feature/multimodal-loader-fallback`;
  `git -C synaptic-tuner checkout e0e02a349df2a5ee24eb3e6d56c785519b9f5519`.
- AFTER: HEAD `e0e02a349df2a5ee24eb3e6d56c785519b9f5519` (resolves e0e02a3 exactly),
  working tree clean, `f6f1229` confirmed ancestor, `tuner.py` present, subject
  "Add generic multimodal loader fallback for composite-config checkpoints".

**Capture BLOCKED on a YAML defect in the signed cell.yaml (did NOT run).**
The wired capture command failed instantly (exit 0 from the wrapper but a
Python traceback) before the model loaded: `yaml.safe_load(cell.yaml)` raised
`ScannerError: mapping values are not allowed here`, cell.yaml line 206. The
`tuner_submodule_pin.verified_by:` value is an unquoted scalar containing an
inner `: ` ("...matches text-only: hs[0]=embeddings..."), which YAML parses as a
nested mapping. This defect was baked into the file at sign (sha bb8d4ad0);
`bin/exp validate` never caught it because validate compares sha256 only and
does not `yaml.safe_load` cell.yaml -- the capture tool is the first consumer
that actually parses it. Confirmed the sole fix is to quote that one value
(whole file then parses; new sha 9fe570a7). Signed file left UNTOUCHED
(bb8d4ad0 intact); escalated to lead for re-sign. Capture will re-fire after
re-sign. NO loader path exercised yet; AG0 not yet evaluable.

### 2026-07-24 -- capture re-fired (valid), AG0/AG1/AG2 evaluated

Lead re-signed cell.yaml with the quote fix (pin 9fe570a7) and authorized the
submodule wiring (recorded above). Re-fire ran clean; results below.

**Capture COMPLETE, VALID.** 3000/3000 rows, coverage_frac 1.0,
coverage_pass_ag0 true, n_hidden_states 33, hidden_size 2560. Tensors real
(per-layer L2 norm grows L0=0.79 -> L32=157.6; rows distinct; values +/-20).
3000 safetensors (985M) under analysis/qwen35_4b/atlas_capture/tensors/, all
gitignored, git tree clean.

**AG0 -> PASS.** coverage 1.0 (>=0.95). loader path: tuner logs it only at
logging.INFO (not emitted), so verified by construction -- the tuner's own
_is_composite_text_config(Qwen3.5-4B @ pinned rev) = True (Qwen3_5Config,
get_text_config() is not config) forces the AutoModelForImageTextToText
pre-check branch (CausalLM never attempted), and ZERO missing/unexpected-key
warnings in the log (garbage-substitution signature absent). held_out power:
confab 1332 (>=150), known 360 (>=250). direction_refit_determinism: two
independent score runs BYTE-IDENTICAL. GATE-INSTRUMENT GAP (flagged, candidate
skill note): AG0's "grep the tuner log for the loader path" is unsatisfiable as
written (INFO not emitted); durable check = composite-config assertion +
missing-key-warning absence.

**AG1 -> profile at every layer; reproducibility does NOT hold (flagged for
lead).** Full-sample eff_dim_frac peak hs18 (depth 0.5625, interior), but the
profile is shallow/bimodal: hs18=0.01019, hs19=0.01012, hs32=0.00999,
hs20=0.00961, hs1=0.00923. On 20% row subsamples (261 of 1308 fit rows) the
peak flips interior(hs18/19) vs final-layer hs32: only 3/8 seeds within +/-1 of
hs18, 5/8 peak at hs32 (late-exterior). Pre-registered ±1 subsample
reproducibility fails -> peak is instrument-resolution-limited, interior vs
late-exterior.

**AG2 -> read panel produced (no numeric gate).** All three axes >=0.80
held-out across a wide interior band (well inside (20%,85%)=hs7-27), so the
"no interior layer clears all three" falsifier limb does NOT fire. doubt
saturates ~1.0 but is heavily norm/position confounded (random control
ref_vs_known up to 0.990 @hs18, 0.991 @hs31); caution & raw_refusal are the
clean axes (controls mostly 0.5-0.77). hs20 relation: profile peak (hs18) is 2
hs before hs20, and at hs20 the caution/raw_refusal random controls are the
panel's highest (0.915/0.859) -- read signal NOT centered on hs20, confound-heavy
there. Supports the hs20-dissociation sub-call.

Scoreboard bearing (LEAD adjudicates against AMENDMENT Prediction/Falsifier;
not a verdict here): the EARLY-EXTERIOR peak both parties called is NOT present
-- early region hs1-6 never a subsample peak; the only non-interior competing
mode is LATE-exterior (hs32). Read-panel-healthy limb: correct. hs20
dissociation sub-call: supported. Falsifier is genuinely ambiguous: full-sample
point estimate = interior peak (falsifier not fired, registered prediction met);
pre-registered reproducibility gate = interior peak not robust, late-exterior
co-equal (pushes toward falsifier firing, but via LATE-exterior, not the
early-exterior mechanism either party predicted).

### 2026-07-23 -- tuner fix landed; indexing watch CLOSED; CPU sign-prep complete

Lead relayed the tuner fix and instructed completion of all CPU-side sign prep.
All done below; still NO commit, NO sign, NO GPU, and hands-off the tuner.

**Layer-indexing PENDING WATCH -> CLOSED (no discrepancy).** The tuner agent
read transformers 5.5.0 source and confirmed numerically (bit-close test vs a
direct `output_hidden_states` call): the `Qwen3_5ForConditionalGeneration`
wrapper uses the identical hook-based capture as text-only models --
`hidden_states[0]`=embeddings, `[i]`=post-block-i, count=`num_hidden_layers`+1.
So this cell's `n_hidden_states=33` / `hs_index = decoder_block_index + 1`
convention, the AG1 scope `hs 0..32`, and the family-layer-map block->hs
pairing (block 19 -> hs20, block 29 -> hs30) all hold unchanged. Closure
citation: tuner commit `e0e02a3`. My own realistic-scale profile probe
independently produced `per_layer` count = 33, consistent.

**Loader blocker CLEARED (corrected mechanism).** My CPU meta smoke caught the
incompatibility via `from_config`'s `AttributeError`, but the tuner agent found
the real `from_pretrained` failure mode is WORSE: silent substitution of a flat
text-only class with garbage weights (all keys missing/unexpected, no
exception) -- same bug class as Stage-S run 1. The fix (tuner branch
`feature/multimodal-loader-fallback` @ `e0e02a3`, includes `f6f1229`) adds a
generic composite-config `get_text_config()` pre-check routing to
`AutoModelForImageTextToText` before `AutoModelForCausalLM`, and logs the
loader path. Recorded in AMENDMENT "Design -> Execution" and "Known
limitations". Capture requirements imposed on this cell: (1) submodule pinned
to `e0e02a3` at launch (`cell.yaml` `capture.tuner_submodule_pin`); (2) new AG0
check `loader_path_is_image_text_to_text` asserts the ImageTextToText path
fired (a CausalLM path == garbage capture -> discard). Both authored.

**materialize_rows.py written.** Joins the committed ID-only manifest
(`experiments/common/qwen35-4b-doubt-snap-split/split_manifest.json`) against
the doubt-snap qwen35_4b private pool `split_rows_private.jsonl` (Modal volume
`eh-doubt-snap-cross-family`). Fail-closed: sha256 gate against
`42659f40...`, every committed row_key must resolve to a question, private-pool
role/split must agree with the committed manifest, role counts must equal
{confab 2219, known 600, unknown_refused 181}. Output is gitignored
`analysis/rows_with_text.jsonl`; zero committed row text. Fetch is a deliberate
`--fetch` (modal volume get) or pre-placed pool; sha always verified.

**Persistence declarations authored (measured on CPU where possible).**
- render_qwen35_atlas.py: short-run, 4.918s (real pinned tokenizer load + 20
  renders; direct enable_thinking=False path renders the empty <think></think>
  block cleanly, assert_no_think_scaffolding passes).
- profile_and_read_family_atlas_panel.py: short-run, 91.71s (synthetic-capture
  probe at ACTUAL scale: 3000 rows, 33 hidden states, dim 2560, 2000 resamples;
  build 3.50s + score 88.21s; refused split reproduced 90/91). Well under the
  15-min ceiling.
- materialize_rows.py: short-run, 0.008s join compute over the real 3000-row
  manifest (synthetic text); the Modal fetch + sha verify are measured at
  capture (genuinely unmeasurable now -- needs Modal auth + restricted data).
- capture_family_atlas_cell.py: incremental, checkpoint_path
  analysis/qwen35_4b/atlas_capture/checkpoint.json (tuner batch-capture
  --resume fsync'd checkpoint).

**Tuner pin recorded** in cell.yaml capture block and experiment.yaml
persistence note; experiment.yaml modules now include materialize_rows.py.

Still deferred to sign: orchestrator scoreboard ratification + `bin/exp sign`
(pins), kg node (created at ingest/resolve). Capture goes into the first GPU
window after j-space, per the lead.

### 2026-07-23 -- lead adjudications applied + CPU loader smoke (CONFIRMED capture blocker)

Lead adjudicated the scaffold's open points. Applied (all CPU-only, no
commits):

**Loader smoke (CPU-only, no CUDA, no weight download).** Ran the meta-device
load-path check that mirrors what `AutoModelForCausalLM.from_pretrained` calls
internally. Env: transformers 5.5.0, torch 2.9.0+cu128.
- `AutoConfig.from_pretrained('Qwen/Qwen3.5-4B', revision=851bf6e...)` OK:
  `Qwen3_5Config`, `architectures=['Qwen3_5ForConditionalGeneration']`,
  top-level has NO `vocab_size`; `text_config` (`Qwen3_5TextConfig`) has
  `num_hidden_layers=32`, `hidden_size=2560`, `vocab_size=248320`. Confirms
  the 2026-07-09 config findings.
- `AutoModelForCausalLM` maps `qwen3_5` -> `Qwen3_5ForCausalLM`.
  `AutoModelForCausalLM.from_config(cfg)` on `torch.device('meta')` FAILED:
  `AttributeError: 'Qwen3_5Config' object has no attribute 'vocab_size'`,
  raised at `Qwen3_5TextModel.__init__` ->
  `nn.Embedding(config.vocab_size, ...)` (reads `vocab_size` on the top-level
  multimodal config, which does not have it).
- `AutoModelForImageTextToText.from_config(cfg)` on meta SUCCEEDED ->
  `Qwen3_5ForConditionalGeneration`.

VERDICT: CONFIRMED capture blocker, NOT the "open risk" the scaffold
hypothesized. `from_pretrained` calls the same `cls(config)` constructor, so
the tuner's hardcoded `AutoModelForCausalLM.from_pretrained`
(`synaptic-tuner/tuner/batch/engines/hf_batched.py:91`) will fail identically
on this checkpoint. The gemma precedent does NOT transfer (gemma's CausalLM
constructor tolerates the nested config; Qwen3.5's does not). Per lead
instruction, STOPPED at the tuner boundary -- did NOT patch the tuner. The
generic multimodal loader-fallback chain (CausalLM -> ImageTextToText ->
Vision2Seq, per Amendment Z's `load_model_and_config`) is escalated to the
lead as a separate synaptic-tuner decision. Recorded in AMENDMENT.md
"Design -> Execution" and "Known limitations".

**Refused-pole power -- option (a) accepted.** 181 fit_only refused rows
(-> ~90/91 split) accepted with lower power; no AG0 floor added, no fresh
mining. Recorded prominently in AMENDMENT.md "Known limitations" and cell.yaml.

**Shared-input promotion -- done (uncommitted).** Promoted the doubt-snap
qwen35_4b split_manifest to
`experiments/common/qwen35-4b-doubt-snap-split/split_manifest.json`
(byte-identical, sha256 2f622f5a...) + `PROVENANCE.md`, per the qwen3-4b
precedent. cell.yaml `source` and experiment.yaml `inputs` now consume the
promoted path. Left uncommitted for the lead's evidence commit.

Deferred to sign/launch as proposed: question-text materialization
(`materialize_rows.py`), persistence declarations, kg node.

Scoreboard now filled: orchestrator row PROPOSED (early-exterior, retained for
lead ratification at sign); user row recorded 2026-07-23 (early-exterior peak
PRESENT -> 5/5; sub-call: read-panel band dissociates from the hs20 write
site). Both call the same direction, independently.

**PENDING WATCH before sign (relayed by lead 2026-07-23).** A separate agent
is implementing the generic multimodal loader fallback in synaptic-tuner
(CausalLM -> ImageTextToText chain, kept generic, CPU-only verification;
I stay hands-off the tuner). Its report will state whether hidden-state layer
indexing through the `Qwen3_5ForConditionalGeneration` wrapper matches
text-only indexing. If there is any off-by-one or extra-embedding-state
discrepancy, THIS cell must account for it before sign: `cell.yaml`
`n_hidden_states=33` / `hs_index = decoder_block_index + 1` convention, the
AG1 scope `hs 0..32`, and the family-layer-map comparability note (hs indices
must line up with the qwen35 steer cells' block->hs pairing, block 19 -> hs20,
block 29 -> hs30). Awaiting the lead's relay; no action until then.

### 2026-07-23 -- scaffolded (draft, NOT signed, NO GPU)

Scaffolded the fifth family-atlas cell, for `Qwen/Qwen3.5-4B` @
`851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`. Followed the `family-atlas` skill
procedure and used `qwen3-4b-family-atlas` as the closest template.

Files: `AMENDMENT.md`, `cell.yaml`, `gates.yaml`, `experiment.yaml` (all
filled in), `render_qwen35_atlas.py` (ported from the SOURCE POOL's own render
`doubt-snap-cross-family-confirmatory/render.py`, not from qwen3-4b's render,
for anchor comparability), plus byte-identical copies of the canonical
`capture_family_atlas_cell.py` (sha256 574c5a71...) and
`profile_and_read_family_atlas_panel.py` (sha256 27cd945c...) from
`.skills/family-atlas/scripts/`.

Row pool: reuses the resolved `doubt-snap-cross-family-confirmatory` qwen35_4b
committed `split_manifest.json` (sha256 2f622f5a...) verbatim. Cleaner than
qwen3-4b: all three roles carry row-level IDs already (confab 2219, known 600,
unknown_refused 181 fit_only) -- NO derive-unknown-refused step needed.

`bin/exp validate`: no hard errors for this slug; the only remaining lines are
the three expected sign-time persistence-declaration warnings (fill at sign
with measured wall-clock, per qwen3-4b's own precedent). kg left empty for the
draft (node created at kg-ingest/resolve).

Open items handed to the lead (see AMENDMENT.md): (1) multimodal loader OPEN
RISK -- tuner `hf_batched` engine hardcodes `AutoModelForCausalLM`, but gemma
(also nested-config multimodal) loaded fine that way; verify with a cheap
pre-sign loader smoke before any generic tuner fallback PR; (2) refused-pole
power (181 -> ~90/91) -- decide whether to add an AG0 floor; (3) shared-input
promotion of the doubt-snap manifest to `experiments/common/`; (4) scoreboard
calls (orchestrator proposed early-exterior / user blank) to ratify pre-sign;
(5) question-text materialization (`materialize_rows.py`) as a gated
capture-launch precondition. NO sign, NO GPU, NO commits performed.
