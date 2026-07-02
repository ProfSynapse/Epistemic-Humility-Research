# Generation-throughput plan: extraction cells on HF Jobs + local 3090

**Status:** PLAN (2026-07-02). Infrastructure work, lab-notebook instrument —
no protocol/amendment surface is touched. Adoption for any registered cell is
gated on the equivalence check in §5. No launch happens without explicit user
approval per the operator discipline.

## 1. Measured baseline (what we are fixing)

One readout cell (`amendment_x_cross_model_extract.py`, 4B model, a10g-small
or local RTX 3090) processes ~10–25 attempts/min → a 3000-attempt Y cell takes
**2.5–5 h**. The Y fleet post-mortem showed anything over ~2 h on HF Jobs is
preemption-exposed, so throughput is now a *reliability* problem, not just a
cost problem. The AA steering cells (2400 generations each) have the same
shape and the same bottleneck (~2 h/cell).

## 2. Where the time actually goes (from the code, not vibes)

Per attempt, the extractor currently does, strictly sequentially:

1. **`model.generate` at batch size 1** (greedy, ≤48 new tokens). At bs=1 an
   autoregressive decode is memory-bandwidth-bound; the GPU runs at a few
   percent of its arithmetic capacity. This is the dominant cost.
2. **A second full forward pass** over prompt+answer with
   `output_hidden_states=True` to capture the pre/post vectors — recomputing
   everything `generate` just computed, again at bs=1.
3. **Re-prefilling the shared k-shot prefix every time.** All base-mode
   prompts share one k-shot header (same `kshot_sha`); we pay its prefill
   3000× per cell.
4. **Two float32 safetensors writes per answered row** (~0.8 MB/row). On the
   cloud this hits ephemeral local disk (fine); on the LOCAL lane it hits the
   9P-mounted F: drive (known slow) when out-dir is under the repo.

## 3. Levers, expected multipliers, risk

| # | Lever | Expected gain | Risk / caveat |
|---|-------|--------------|----------------|
| L1 | **Batched HF `generate`** (left-pad, length-sorted buckets, bs 32–64) + **batched capture forward** | **10–20×** end-to-end | Universal (transformers 5.12.1 already validated on every arch we run). Greedy argmax ties can flip under batched reduction order → §5 gate |
| L2 | **vLLM generation pass** (continuous batching) | **30–50×** on the generation stage | Model coverage: Gemma 4 has day-one vLLM support; Qwen3.5's hybrid Mamba arch is supported but WITHOUT prefix caching. New dependency in the job image |
| L3 | **vLLM native hidden-states extraction** (v0.18.0+, PR #33736): prefill-only pass returns `[seq_len, num_layers, hidden]` with per-layer selection | replaces the capture forward at vLLM batch speed | New since our stack was built (blog 2026-03-30). Needs a small adapter to slice our pre/post positions and persist the same safetensors layout |
| L4 | **Faster HF flavor** (a10g-small → l40s or a100-large) | 2–3× wall-clock, roughly cost-neutral (≈$1/h a10g vs ≈$1.8/h l40s vs ≈$2.5–4.5/h a100 — verify on the jobs-pricing page at launch) | Zero code. Shorter jobs also shrink the preemption window |
| L5 | Shared-prefix KV reuse in the HF path (`past_key_values` for the frozen k-shot header) | 1.3–2× on prefill-heavy pools | Only worth it if we stay on the HF path; free inside vLLM (except Qwen3.5, no APC) |
| L6 | Local-lane I/O: write safetensors to ext4 scratch (`~/` or `/tmp`), move to F: once at the end | removes 9P write stalls | Local lane only; trivial |

Non-levers (already done or immaterial): bf16 weights (already), SDPA
attention (transformers default), `max_new_tokens=48` (already tight),
torch.compile (~1.3× at best, complicates hooks — skip).

## 4. The plan per lane

### Ownership split: generic engine in Synaptic Tuner, glue here

The generic parts of this are useful to any research project, so they live in
the `synaptic-tuner` submodule (its own repo, tests, and PR flow), exposed as
public CLI verbs per the no-pollution boundary — this repo talks to the tuner
only through public CLI behavior, never imports:

- **Tuner (generic):** `tuner.py batch-generate` — prompts-in (JSONL),
  completions-out; engine-selectable (`hf-batched` with length-sorted
  left-pad micro-batching, or `vllm` continuous batching); greedy/sampled,
  seed, stop discipline, batch-size auto-halve on OOM. And
  `tuner.py batch-capture` — sequences-in, per-layer hidden states at named
  token positions out (safetensors), engine-selectable (`hf-batched` forward
  or vLLM native hidden-states extraction, v0.18.0+). Nothing
  Epistemic-specific: no pools, no grading, no outcome taxonomy.
- **Tuner (generic) — incremental persistence + resume (REQUIRED, user
  directive 2026-07-02 after the Y-fleet preemption losses):** both verbs
  flush completed rows after every batch (append-fsync JSONL; tensor files
  atomic-per-row), keep a `checkpoint.json` of done row ids + a config hash,
  and accept `--resume` to skip completed ids on re-invocation (refusing to
  resume across a changed config). A generic `--sync-every N` +
  `--sync-cmd '<shell>'` hook pushes partial artifacts to durable storage
  mid-run (sync failure warns, never kills the run). Contract: a preempted
  cloud job loses at most one batch of work and a restart with `--resume`
  produces the identical artifact set an uninterrupted run would have. Logs
  are telemetry; ROWS AND TENSORS are the data — both must survive a kill at
  any moment.
- **This repo (experiment-specific):** pool building, k-shot/base-mode
  rendering, answer parsing, grading/scorers, row schema + outcome taxonomy,
  config_sha/manifest assembly, safetensors naming, cloud wrapper. The
  extractor becomes orchestration: render prompts -> `batch-generate` ->
  grade rows -> `batch-capture` on answered rows -> persist rows/manifest.

The two-pass design maps 1:1 onto the two verbs, so the split costs nothing
architecturally. The interleaved bs=1 loop in
`amendment_x_cross_model_extract.py` stays as the reference implementation
(default path) until the §5 gate passes.

Cloud note: HF Jobs cells currently clone only this repo; using tuner verbs
in-job means either `git submodule update --init synaptic-tuner` in the
bootstrap or pip-installing the tuner from its repo at a pinned commit. Local
lane uses the submodule checkout directly.

Governance note (amendment-vs-lab-notebook): this is a throughput refactor
whose §5 gate enforces output-equivalence with the existing engine — it
creates no new evidence-cell type, so it routes as lab-notebook
infrastructure, not a Tier-2 amendment. If the vLLM engine ever changes
*what* is measured (not just how fast), that re-opens the routing question.

### Phase 1 — batched HF path (both lanes; the workhorse)

Implement `batch-generate`/`batch-capture` (hf-batched engine) in the tuner;
in this repo add to the extractor:

- `--engine {sequential,tuner-batched}` (default sequential = today's
  behavior, so old invocations are byte-identical and old config_shas remain
  reproducible).
- Per-row parse/grade exactly as now (parsing is per-sequence and unchanged).
- `--scratch-dir` for the local lane (L6): persist tensors on ext4, single
  move at the end.
- Manifest gains `engine` + `batch_size` fields (config_sha already hashes
  the config payload, so batched runs are visibly distinct — the roll-up
  config-equality check may treat them as non-substantive ONLY after §5
  passes).

Expected cell times: 3000-attempt 4B cell ≈ **15–25 min** on a10g-small or the
3090 (vs 2.5–5 h). Every cell drops under the preemption horizon; the durable
log wrapper stays as belt-and-braces.

### Phase 2 — vLLM engine (big fleets / repeated sweeps)

Add the `vllm` engine behind the SAME two tuner verbs (no new script in this
repo — the extractor's orchestration is engine-agnostic):

1. **`batch-generate --engine vllm`:** continuous batching over the whole
   pool, greedy, same stop discipline → answers + token ids. Minutes for
   3000 rows.
2. **`batch-capture --engine vllm`:** native hidden-states extraction
   (v0.18.0+, prefill-only) over prompt+answer token ids, selecting all
   layers; this repo slices its two positions and persists the identical
   safetensors/rows.jsonl/manifest layout so
   `amendment_x_cross_model_score.py` runs unmodified. Fallback if the
   native feature fights us: the hf-batched capture engine is already fast
   enough (generation was the bottleneck).

Manifest `engine: "vllm"` + vllm version pin. Use for: Stage-2 style
fleets, AA follow-up cells (2400+ gens each), any future sweep where cells
repeat. Skip for one-off cells on exotic day-zero archs until vLLM support is
confirmed (check the supported-models page per arch; Gemma 4 yes, Qwen3.5 yes
minus APC).

### HF Jobs specifics

- Default flavor stays a10g-small for ≤4B batched cells (they'll finish in
  ~20 min); use l40s/a100-large for 7B+ or when wall-clock matters (L4).
- Keep: pinned-commit clone, durable per-incarnation log push, rows.jsonl
  upload. Batched cells make the 10-min log-push interval ~the whole runtime;
  drop the pusher interval to 120 s when batch mode is on.
- Timeouts shrink to match (45–90 min ceilings), which also caps blast radius
  of any future preemption loop.

### Local 3090 specifics

- 24 GB Ampere: bf16 4B weights ≈ 8 GB → bs 48–64 at our sequence lengths;
  7B ≈ 14 GB → bs 16–24. Auto-halve batch on OOM rather than pre-tuning.
- `lms.exe unload --all` first (LM Studio holds ~15 GB idle).
- L6 scratch-dir is mandatory here (9P writes are the local equivalent of a
  slow network disk).
- The AA steering harness gets the same batched treatment in a follow-up:
  Arm A hooks apply batch-wide (direction add is position-gated, batch-safe);
  Arm B needs the probe score before injection → batched capture pass, then
  batched injected generation. Do this before the first-person phrasing
  diagnostic runs, so those cells cost minutes not hours.

## 5. Equivalence gate (before any registered use)

Batched greedy is mathematically equivalent under masking, but float
reduction order can flip near-tie argmaxes. So, before any batched/vLLM
engine touches a registered cell:

1. Re-run one COMPLETED Y cell (pythia-2.8b: cheapest real cell, result
   already on the hub) with `--batch-size 32` locally.
2. Compare per-row: answer_text exact-match rate (expect ≥99%), outcome
   (correct/wrong/halluc) agreement, and the scored gate/dial/veto AUROCs
   (expect deltas ≪ the bootstrap CI half-widths).
3. Record the comparison as a lab-notebook entry; only then adopt for the
   gemma-4-e4b-pt and olmo-2-7b re-runs and future fleets.
4. Same gate later for the vLLM engine (compare vs the batched-HF result).

The in-flight `y-a-qwen3.5-4b-base-r2` finishes on the registered sequential
config regardless — no mid-run engine swap inside Amendment Y's primary cell.

## 6. Order of work

1. Phase 1 extractor change + local pythia equivalence run (one sitting; the
   equivalence run is ~20 min GPU after the AA queue drains, needs launch
   approval).
2. Adopt for the two remaining Y re-runs (cloud, user approval; ~25 min cells
   with durable logs).
3. Batch the steering harness (before the first-person diagnostic).
4. Phase 2 vLLM engine when the next multi-cell fleet is on the horizon.

## Sources

- vLLM hidden-states extraction: https://vllm.ai/blog/2026-03-30-extract-hidden-states ,
  https://docs.vllm.ai/en/latest/features/speculative_decoding/extract_hidden_states/
  (native since v0.18.0, PR #33736; per-layer selection, prefill-only mode)
- Gemma 4 on vLLM (day-one support incl. E4B):
  https://vllm-project.github.io/2026/04/02/gemma4.html
- Qwen3.5 hybrid-Mamba caveat (supported, no prefix caching):
  https://docs.vllm.ai/en/latest/models/supported_models/
- HF Jobs pricing (verify at launch): https://huggingface.co/docs/hub/jobs-pricing ,
  https://huggingface.co/pricing (≈$1/h a10g-small; L40S ≈$1.8/h;
  A100 ≈$2.5–4.5/h ranges reported 2026)
