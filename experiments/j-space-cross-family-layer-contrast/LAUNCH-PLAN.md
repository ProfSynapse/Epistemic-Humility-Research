# LAUNCH-PLAN: j-space-cross-family-layer-contrast

Draft planning document, not a claims surface. This is written for the lead
to review before signing and launching; it is NOT itself an authorization to
launch anything. No GPU work has run; every time estimate below is derived
from recorded predecessor timings, not measured on this experiment's own
checkpoints.

## Run order (Amendment Z's risk order, unchanged)

1. `llama-3.2-3b` -- `unsloth/Llama-3.2-3B-Instruct` (lowest risk, run first)
2. `mistral-7b-v03` -- `mistralai/Mistral-7B-Instruct-v0.3` (substituted pre-outcome for Amendment Z's Ministral-3-3B: the doubt-snap-cross-family confirmatory found Ministral-3 exposes Mistral3ForConditionalGeneration, not a causal-LM write substrate; see families/mistral-7b-v03.yaml)
3. `qwen35-4b` -- `Qwen/Qwen3.5-4B`
4. `gemma4-e4b` -- `google/gemma-4-E4B-it` (highest risk, run last)

Each family runs its full pipeline (mine -> split -> profile -> extract ->
build directions -> gate fit -> calibrate -> smoke -> full contrast) to
completion (or a recorded G0 stop) before the next family starts, per the
locked design. `cross_family_rollup.py` runs once, after every family has
either a `full_summary.json` or a recorded NOT-RUN.

## Per-stage commands (per family; replace `<slug>` with the family slug)

```bash
# 1. Reuse doubt-snap's pool + FIT/HELD-OUT split (supersedes mine + split):
python experiments/j-space-cross-family-layer-contrast/materialize_reused_rows.py --family <slug>
#    (prints the `modal volume get` command for the private row text; re-run to normalize it)
# 2. NEW work: mid-band localization, fit, dose calibration (mid-band candidates only):
python experiments/j-space-cross-family-layer-contrast/jlens_profile.py --family <slug>
python experiments/j-space-cross-family-layer-contrast/extract_anchor.py --family <slug>
python experiments/j-space-cross-family-layer-contrast/build_directions.py --family <slug> --verify-reproducible
python experiments/j-space-cross-family-layer-contrast/gate_fit.py --family <slug>
python experiments/j-space-cross-family-layer-contrast/calibrate_dose.py --family <slug>
# 3. Outcome. Primary = mid-band absolute gates. The SECONDARY late arm runs only
#    if --late-dose is given (open question 1); without it the late arm is skipped
#    and the primary is unaffected:
python experiments/j-space-cross-family-layer-contrast/run_contrast.py --family <slug> --mode smoke --n-rows 8 [--late-dose D]
# only after smoke G0 passes:
python experiments/j-space-cross-family-layer-contrast/run_contrast.py --family <slug> --mode full --i-know-this-is-the-cross-family-run [--late-dose D]
```

After all four families have run (or stopped at G0):

```bash
python experiments/j-space-cross-family-layer-contrast/cross_family_rollup.py
```

## Per-stage GPU-time estimates (derived from predecessor timings)

These are the ONLY numbers this plan has to anchor to; they come from the
Qwen3-4B (2560-hidden, 36-layer) predecessors and Qwen3-4B's own J-lens
Modal run, scaled naively by parameter count / layer count where the
predecessor didn't report a directly comparable number. Treat every
estimate below as an ORDER-OF-MAGNITUDE planning number, not a budget
commitment -- a different family's tokenizer, chat template, or loader path
could change wall-clock time by more than the naive scaling suggests.

| Stage | Qwen3-4B predecessor timing (recorded) | Per-family estimate (3-4B scale) |
|---|---|---|
| Mine eval pool | Not separately timed as a standalone stage (folded into predecessor extraction runs); the replication's fresh-pool census over 12,923 candidates found 306 confab + 1,957 known_correct_answered rows. | Generation-bound: budget ~1-3 hours per family for a target-count run (this experiment's `mine_eval_pool.py` defaults to targets of 200 confab / 300 known_correct_answered, smaller than the replication's exhaustive census). |
| Split FIT/HELD-OUT | CPU-only, seconds. | Seconds (CPU-only). |
| J-lens layer_profile | Full-corpus Modal run: 10760.2s (~3.0h) on an A10/A10G-class GPU, n_prompts=1000, ~13-layer depth sweep x 5 random directions x 4 H1 offsets. Local smoke-scale (`n_prompts=50`, `--layers` 10 points, `n_random_dirs=4`): ~3m44s. | Budget ~2-3h per family at n_prompts=1000 on a 3090 (a 3090 is roughly A10G-class or faster for this workload); a SMALLER `--n-prompts` (e.g. 200-300) first-pass profile could run in well under an hour per the local-smoke-scale timing, and may be sufficient to locate a band before committing to the full n=1000 run. |
| Extract anchor activations | Layer sweep extraction (1,768 rows x 4 layers): not separately reported as wall-clock in the read docs; the fresh-replication anchor extraction (2,263 rows x 4 layers) reused the same per-row forward-pass method as the layer-sweep extraction. | Single forward pass per row, 3-4 layers each; expect low tens of minutes per family for a ~500-row eval pool. |
| Build directions + gate fit | CPU-only; midband-write-sweep's `build_directions.py`/`gate_fit.py` are pure numpy/sklearn over already-extracted tensors. | Seconds to low minutes (CPU-only), dominated by LogisticRegression `saga` convergence on a few hundred-row FIT population. |
| Dose calibration | Dose-calibration cell ran an 8-dose ladder x 4 layers x (8 confab + 8 known FIT rows) = 512 dosed-row generations; not separately timed, but each dosed generation is one `model.generate()` call up to 200 new tokens. | Budget on the order of an hour per family for the full 8-dose x N-layer ladder at this small calibration-subset size. |
| Smoke (G0) | 8-16 rows x N layers, each with an off pass + (if fired) a dosed pass, both up to 200 new tokens. | Minutes per family. |
| Full held-out contrast | Predecessor full runs: calibrated-layer-contrast ran 443 held-out rows x 4 layers = 1,772 (off+dosed) generation pairs; replication ran a similarly sized fresh pool. | Budget 1-3 hours per family for a held-out pool in the low hundreds of rows x up to 4 candidate layers, scaling with however large `mine_eval_pool.py`'s targets end up. |

**Total per-family estimate: very roughly 4-8 hours of GPU-busy time**, dominated
by the J-lens profile stage and the full held-out contrast, BEFORE accounting
for any loader debugging, OOM recovery, or a smaller first-pass profile
`--n-prompts`. Across all four families sequentially: **very roughly 1-2 days
of local-3090 GPU-busy time**, not counting analysis, review, or any G0
debugging loop. This is a planning-grade estimate, not a commitment; the lead
should treat it as a reason to consider a smaller first-pass `--n-prompts`
for the profile stage (see the table) before committing to the full n=1000
sweep on all four families.

## VRAM feasibility (bf16, single RTX 3090, 24GB)

| Family | Params | Feasibility read |
|---|---|---|
| Llama-3.2-3B | 3.21B | Comfortable. ~6.4GB bf16 weights; plenty of headroom for activations, KV cache, and the steering hook's readback buffers. |
| Mistral-7B-v0.3 | 7B | The VRAM-heaviest family (~14-15GB bf16 weights). Generation and extraction fit a 24GB 3090; the J-lens profile stage's eager-attention double-backward is the pressure point, so budget for reduced batch or fewer random probe directions. A profile-stage OOM is a batching problem, not a G0 loader blocker. |
| Qwen3.5-4B | 4B | Should fit for the text-only path; the multimodal loader may pull in a vision tower's weights even for text prompts, which is a decision point (see below), not resolved here. |
| Gemma-4-E4B | ~4B effective | **FLAGGED, highest risk of the four.** The E4B multimodal architecture may load a vision encoder even for text-only prompts. Combined with the J-lens profile stage's extra double-backward-JVP activation memory (the localization experiment's own docstring notes this needs `attn_implementation="eager"`, which is generally MORE memory-hungry than fused SDPA attention), this could approach the 24GB ceiling. Amendment Z's own risk table lists this as "loader risk only" for its own (non-J-lens) extraction; the J-lens profile stage is this experiment's OWN additional risk on top of Amendment Z's, not something Amendment Z already validated. |

## Gemma-4-E4B Modal fallback (pre-authorized 2026-07-23, user)

The Gemma-4-E4B cell runs on the local RTX 3090 first, like the other three
families. **If it OOMs at G0 after bounded debugging** -- a real risk given its
trimodal loader materializes vision + audio towers even for text-only prompts
(verified CPU-only, see families/gemma4-e4b.yaml), on top of the J-lens profile
stage's eager-attention double-backward activation memory -- **a Modal fallback
for the Gemma cell only is pre-authorized by the user.** Other families stay
local-only. A G0 NOT-RUN is recorded for Gemma only if the Modal fallback ALSO
fails after bounded debugging; a local OOM alone is not a NOT-RUN. This is the
only cell with a pre-authorized cloud fallback.

## Decision points for the lead

**Sign-time revision (2026-07-23) added items 0/1a/1b/1c below and MOOTED the
original G3-floor decision. The remaining items 2-6 are carried from the draft.**

0. **Branch is 677 commits behind `main`; the reused artifacts are not on it.**
   The reuse design depends on `doubt-snap-cross-family-confirmatory` and its
   qwen35-4b-midband successors, which resolved on `main` after this branch was
   cut. The branch MUST be updated with `main` (rebase/merge -- a git decision
   the lead owns) before `materialize_reused_rows.py` or the G0 reuse-integrity
   check can resolve any path. All pinned sha256 were computed from `main` and
   are authoritative. See AMENDMENT.md "Open questions at sign" #0.

1a. **Primary gate NUMBERS (PROPOSED).** G1 mid-band actuation floor =
   clean_tighten >= 0.50 with Wilson lower > 0.40; G2 selectivity cap =
   not_well_formed_correct <= 0.05 with Wilson upper < 0.10. Full derivation in
   AMENDMENT.md "Gates -> derivation". Stricter G1 alternative offered: 0.60 /
   0.50 (the sibling Qwen3.5-4B's own passing held-out floor). Drafter
   recommends the conservative 0.50/0.40.

1b. **Late-arm DOSE gap.** doubt-snap selected NO late-site dose for any family
   (`selected_dose: null`; gemma has no dose sweep at all). "Reuse the frozen
   late-site ... calibrated dose" cannot be satisfied literally. Options: (A)
   report the late arm at each family's doubt-snap FIT peak-clean_tighten dose
   (llama 19 / mistral 30 / qwen35-4b 40; gemma unavailable), or (B) calibrate
   the late dose fresh here with the same ladder as the mid-band arm.
   **Drafter recommends (B)** -- apples-to-apples, covers gemma, and the late
   arm is non-gating so verbatim dose reuse buys nothing. The `run_contrast.py
   --late-dose` flag (or a `reuse.doubt_snap.late_site.resolved_late_dose` YAML
   field) resolves this; without it the late arm is skipped and the primary is
   unaffected.

1c. **The former G3 late-reference floor is DROPPED.** The reframe makes the
   late arm a non-gating descriptive comparator, so the draft's per-family
   `g3_late_reference_floor` (0.40 / 0.30) no longer exists; the original
   decision about that floor is moot.
2. **RESOLVED PRE-SIGN (was: Ministral-3-3B FP8 load risk).** The
   Mistral-family cell was substituted to `mistralai/Mistral-7B-Instruct-v0.3`
   before any Mistral-family run, inheriting the doubt-snap-cross-family
   confirmatory's pre-outcome loader-eligibility finding (Ministral-3 exposes
   `Mistral3ForConditionalGeneration`, not a causal-LM substrate for the
   activation write path). Remaining Mistral-family question is only the 7B
   VRAM headroom at the profile stage (see the feasibility table).
3. **VERIFIED 2026-07-09 (CPU-only, config/tokenizer JSON files + meta-device
   model construction, no weights, no GPU, no generation).** Qwen3.5-4B and
   Gemma-4-E4B's multimodal loader paths and config nesting were checked
   against each checkpoint's `config.json`/`tokenizer_config.json`/
   `chat_template.jinja`/`generation_config.json` (downloaded via
   `hf_hub_download` per-file, never `snapshot_download`; cached under this
   experiment's gitignored `analysis/tokenizer-config-verify/`). Findings:
   - Both checkpoints nest `hidden_size`/`num_hidden_layers` under
     `config.text_config` (confirming `nested_text_config: true` was
     correct for both); `config.get_text_config()` is the confirmed
     transformers-native accessor (checked directly, transformers 5.5.0).
   - `AutoModelForCausalLM.from_config()` on the raw top-level config
     **fails** for Qwen3.5-4B (`AttributeError: 'Qwen3_5Config' object has
     no attribute 'vocab_size'` -- its resolved class expects a flat/text
     config) but **succeeds** for Gemma-4-E4B (no error) -- however both
     families' `AutoModelForImageTextToText.from_config()` call resolves
     to the SAME full conditional-generation class
     (`Qwen3_5ForConditionalGeneration` / `Gemma4ForConditionalGeneration`)
     that `AutoModelForCausalLM` either falls through to (Qwen3.5) or
     lands on directly anyway (Gemma4). For both families this means: a
     real (non-meta) load materializes the non-text tower parameters
     (vision for Qwen3.5; vision AND audio for Gemma4 -- Gemma-4-E4B's
     `config.json` also carries a full `audio_config` block in addition to
     `vision_config`, i.e. this checkpoint is TRIMODAL, not just
     vision-multimodal) regardless of which `model_classes` entry actually
     resolves. This firms up (does
     not resolve the GB number for) the open VRAM question in the
     feasibility table above -- the vision/audio towers ARE structurally
     part of what gets loaded, not merely a config artifact.
   - `attn_implementation="eager"` was passed to
     `AutoModelForImageTextToText.from_config()` for both families and
     accepted cleanly at construction time (meta-device, no weights),
     propagating to both the top-level and nested text-config
     `_attn_implementation` fields. This is verified only at
     construction/config-propagation time; it does NOT verify eager
     attention is actually used correctly during a real forward/backward
     pass (double-backward JVP), which needs a GPU and remains unverified.
   - Full findings and the exact commands run are recorded in each
     family's `families/<slug>.yaml` "loader.notes" field.
4. **VERIFIED 2026-07-09 (same CPU-only config/tokenizer fetch as point 3).**
   Per-family EOS/end-of-turn tokens, layer counts, and render-contract
   details:
   - **Gemma system-role support: RESOLVED, and the concern was
     UNFOUNDED for this checkpoint.** `google/gemma-4-E4B-it`'s
     `chat_template.jinja` gives `system`/`developer` roles their own
     dedicated turn block (`messages[0]['role'] in ['system', 'developer']`
     triggers a distinct block), not folded into the first user turn. The
     AMENDMENT.md family table did not carry this specific concern, so no
     correction was needed there beyond the EOS-token fix noted below.
   - **Gemma EOS token: CORRECTED, the draft's guess was WRONG.**
     `<end_of_turn>`/`<start_of_turn>` do not appear anywhere in
     `google/gemma-4-E4B-it`'s chat template (grepped, zero matches).
     Gemma4 uses a different scheme: literal `<|turn>ROLE\n` /
     `<turn|>\n` markers, and `tokenizer_config.json` has its own
     `eot_token` field whose value is literally `"<turn|>"`. Updated
     `families/gemma4-e4b.yaml`'s `eos.additional_end_of_turn_tokens` to
     `["<turn|>"]`. Two of `generation_config.json`'s three
     `eos_token_id` entries (ids 106 and 50) could not be resolved to
     literal strings from the files this task is scoped to fetch
     (`special_tokens_map.json` is absent from this repo and the full
     tokenizer vocab was out of scope); this remains open, flagged in the
     YAML, and should be resolved at extraction time with the actual
     tokenizer loaded.
   - **Gemma `enable_thinking`: CORRECTED, the draft's guess was WRONG.**
     The family YAML claimed Gemma has no native thinking-toggle kwarg.
     `google/gemma-4-E4B-it`'s chat template DOES have one: `enable_thinking`
     gates a `<|think|>` token injection and the template separately
     handles `reasoning`/`reasoning_content` message fields. Gemma4-E4B is
     a reasoning-capable checkpoint, unlike the older Gemma 2/3 lineage the
     original guess reasoned from.
   - **Llama, Mistral, Qwen3.5 EOS guesses: CONFIRMED correct** (`<|eot_id|>`
     for Llama, no extra token for Mistral, `<|im_end|>` for Qwen), with one
     terminology nuance for both Llama and Qwen3.5: the tokenizer's own
     default `eos_token` (per `tokenizer_config.json`/`special_tokens_map.json`)
     is ALREADY the family's named end-of-turn token in both cases (`<|eot_id|>`
     for Llama, `<|im_end|>` for Qwen3.5) -- so `include_tokenizer_eos: true`
     alone already covers it, it is not purely "additional" the way the
     YAML's field name implies. Llama's `generation_config.json` also lists
     a third stop id (`<|eom_id|>`, end-of-message) not previously
     recorded. See each family's `eos.notes` field for the full detail.
   - **Qwen3.5's `enable_thinking` kwarg: CONFIRMED** present and matching
     Qwen3-4B's lineage semantics exactly.
   - **Mistral system-role: noted (not a decision point, found incidentally).**
     Mistral's template accepts `messages[0]['role'] == 'system'` but folds
     it into the first user turn's `[INST]` block rather than giving it a
     separate turn (unlike Llama/Qwen/Gemma4). Not a template failure, just
     a different render shape; noted in `families/mistral-7b-v03.yaml`.
   - `families/llama-3.2-3b.yaml`'s `n_hidden_layers: 28` is now
     CONFIRMED (not just an estimate) from the actual downloaded
     `config.json`. `mistral-7b-v03.yaml`, `qwen35-4b.yaml`, and
     `gemma4-e4b.yaml`'s previously-`null` `n_hidden_layers` are now filled
     in and confirmed: 32 (Mistral, flat), 32 (Qwen3.5, nested under
     `text_config`), 42 (Gemma4, nested under `text_config`). Each
     family's `late_reference_hs_estimate` is recomputed accordingly
     (`round(0.9444 * n_hidden_layers)`: 26 / 30 / 30 / 40 respectively);
     these remain ESTIMATES for the profile stage to confirm/select
     against, only the input layer count is now config-verified rather
     than assumed. Note both Qwen3.5 and Gemma4's `text_config.layer_types`
     alternate attention types across depth (Qwen3.5:
     linear_attention/full_attention every 4th layer; Gemma4:
     sliding_attention/full_attention every 6th layer) -- neither family's
     42/32 layers are architecturally uniform, which the profile stage's
     depth sweep should be aware of.
5. **Eval-pool mining targets** (`--target-confab 200 --target-known-correct
   300`, this script's defaults) are carried over from the Qwen3-4B
   replication's own targets, not re-derived per family. A family whose raw
   base answers/refuses at very different base rates than Qwen3-4B (e.g. a
   much higher or lower confab rate on the shared candidate pool) may need a
   larger `--max-unknown-candidates`/`--max-known-candidates` scan to reach
   the same targets, which is a runtime observation, not something this
   draft can predict.

6. **NEW dependency: `run_contrast.py` now requires the tuner's RunLog
   (added 2026-07-09, CPU-only wiring, no GPU work run).** Both smoke and
   full mode route their per-layer row loop through
   `shared/utilities/run_log.py`'s `RunLog` (per-row append+fsync,
   resumable across a kill) instead of buffering the whole layer in
   memory, with `--resume` (default) / `--fresh` CLI flags. `RunLog`
   currently lives only on the tuner branch `feature/runlog`, not yet
   merged to the tuner's main branch that this repo's submodule pins. The
   import is deliberately lazy (`model_lib.load_run_log_class()`, called
   at the start of `run_contrast.py`'s `run_layers()`), so it fails with a
   clear message naming the required branch rather than breaking `--help`
   or unrelated imports -- verified: `--help` still runs clean, and
   calling it against this worktree's current submodule checkout (pinned
   to a commit before `feature/runlog` branched) raises that exact
   message. **Before this experiment can be signed and run for real, the
   tuner branch `feature/runlog` must be merged and this repo's
   `synaptic-tuner` submodule pointer bumped to include it** -- otherwise
   `run_contrast.py` cannot run at all, in either mode. `calibrate_dose.py`
   was deliberately left unwired: its dose ladder calls
   `pipeline.py:run_layer` repeatedly for the SAME rows under DIFFERENT
   doses, so a single per-layer run-log path would collide row keys across
   doses (a row done at dose A would be wrongly treated as done at dose
   B); `run_layer`'s new `run_log` parameter defaults to `None` and leaves
   `calibrate_dose.py`'s in-memory behavior untouched. See
   `experiments/common/README-runlog.md` in the root repo for the
   consumption convention.

None of the above is resolved by this scaffold; they are handed to the lead
as open questions before any GPU work happens, per the task's explicit
instruction to flag decision points rather than resolve them.
