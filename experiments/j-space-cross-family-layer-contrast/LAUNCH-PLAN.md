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
python experiments/j-space-cross-family-layer-contrast/mine_eval_pool.py --family <slug>
python experiments/j-space-cross-family-layer-contrast/split_fit_heldout.py --family <slug>
python experiments/j-space-cross-family-layer-contrast/jlens_profile.py --family <slug>
python experiments/j-space-cross-family-layer-contrast/extract_anchor.py --family <slug>
python experiments/j-space-cross-family-layer-contrast/build_directions.py --family <slug> --verify-reproducible
python experiments/j-space-cross-family-layer-contrast/gate_fit.py --family <slug>
python experiments/j-space-cross-family-layer-contrast/calibrate_dose.py --family <slug>
python experiments/j-space-cross-family-layer-contrast/run_contrast.py --family <slug> --mode smoke --n-rows 8
# only after smoke G0 passes:
python experiments/j-space-cross-family-layer-contrast/run_contrast.py --family <slug> --mode full --i-know-this-is-the-cross-family-run
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

## Decision points for the lead (none resolved by this draft)

1. **G3 late-reference floor (0.40 rate / 0.30 Wilson-lower CI, all four
   families)**. This is LOWER than the Qwen3-4B predecessors' own G3 floor
   (0.60/0.50) per the locked design's stated rationale ("instruct families
   may differ"), but the exact numbers 0.40/0.30 were chosen by this
   drafting pass as a round, defensible-looking floor, not derived from any
   family-specific power analysis or pilot data (no GPU work has run). The
   lead should decide whether 0.40/0.30 is the right floor, or whether it
   should be derived per-family from that family's own FIT-side dose
   calibration numbers before the held-out contrast runs.
2. **RESOLVED PRE-SIGN (was: Ministral-3-3B FP8 load risk).** The
   Mistral-family cell was substituted to `mistralai/Mistral-7B-Instruct-v0.3`
   before any Mistral-family run, inheriting the doubt-snap-cross-family
   confirmatory's pre-outcome loader-eligibility finding (Ministral-3 exposes
   `Mistral3ForConditionalGeneration`, not a causal-LM substrate for the
   activation write path). Remaining Mistral-family question is only the 7B
   VRAM headroom at the profile stage (see the feasibility table).
3. **Qwen3.5-4B and Gemma-4-E4B's multimodal loader paths are unverified for
   the J-lens's `attn_implementation="eager"` requirement.** Amendment Z's
   own loader hardening was validated for its (non-J-lens) extraction script;
   it has not been confirmed that the multimodal wrapper classes
   (`AutoModelForImageTextToText` / `AutoModelForVision2Seq`) accept or
   respect `attn_implementation="eager"` the way `AutoModelForCausalLM` does.
   If they do not, the J-lens profile stage (which needs eager attention for
   the double-backward JVP trick on any non-final layer) may need a
   different attention-implementation strategy for these two families, which
   is a design question for the lead, not something this draft resolves.
4. **Render-contract ambiguity per family**, specifically:
   - Gemma's chat template may not support a separate system role (some
     Gemma templates fold system content into the first user turn).
     `backends.render_probe_prompt`'s own mode-discovery/fallback loop
     SHOULD surface this as a template failure to try next, but this has
     not been confirmed against the actual `google/gemma-4-E4B-it` tokenizer.
   - Each family's actual EOS/end-of-turn token list
     (`families/<slug>.yaml` "eos" block) is this drafting pass's best
     guess from general knowledge of each chat-template lineage
     (`<|eot_id|>` for Llama 3, `<|im_end|>` for Qwen, `<end_of_turn>` for
     Gemma, no extra token assumed for Mistral) and has NOT been
     confirmed against each checkpoint's actual
     `tokenizer.special_tokens_map` or `additional_special_tokens`. Confirm
     at extraction time, per each family YAML's own "notes" field.
   - `families/llama-3.2-3b.yaml`'s `n_hidden_layers: 28` (used only to
     estimate a late-reference depth fraction target before the profile
     stage runs) is an UNCONFIRMED estimate, not read from the actual
     config; the profile stage's own `model.config.num_hidden_layers` read
     is the authoritative source once it runs.
5. **Eval-pool mining targets** (`--target-confab 200 --target-known-correct
   300`, this script's defaults) are carried over from the Qwen3-4B
   replication's own targets, not re-derived per family. A family whose raw
   base answers/refuses at very different base rates than Qwen3-4B (e.g. a
   much higher or lower confab rate on the shared candidate pool) may need a
   larger `--max-unknown-candidates`/`--max-known-candidates` scan to reach
   the same targets, which is a runtime observation, not something this
   draft can predict.

None of the above is resolved by this scaffold; they are handed to the lead
as open questions before any GPU work happens, per the task's explicit
instruction to flag decision points rather than resolve them.
