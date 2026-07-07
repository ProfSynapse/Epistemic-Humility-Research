# j-space-localization-qwen3-4b

Status: resolved (exploratory lab-diagnostic; not confirmatory evidence).

Keep this document the prose home for the experiment. The machine state lives in
`experiment.yaml` and is never duplicated here.

## Motivation and posture

EXPLORATORY, read-only lab-diagnostic. Follows from
`docs/ideas/j-space-global-workspace-actuation-bridge.md` (queued research
direction, 2026-07-06): the Transformer Circuits paper "Verbalizable
Representations Form a Global Workspace in Language Models"
(library/notes/tc-2026-workspace--verbalizable-representations-global-workspace.md)
proposes the J-lens (Jacobian lens) and finds that a concept's J-space
component (a small, mid-to-late-layer, sparse set of directions) dominates
verbal report while the much larger non-J-space component of the same vector
does not. This project's own actuation arc shows a matching split: the
epistemic readout (doubt/knownness, correctness, confab-propensity) is
portable and strong everywhere, while actuation (writing to steer behavior)
works on exactly one checkpoint and comes back null or fragile elsewhere. The
idea doc's H1 is the cheapest test of whether that split has a J-space
explanation: are our fitted directions J-space concepts (do they verbalize as
uncertainty/abstention tokens), and where does L34 (our existing write layer)
sit relative to the workspace band. This experiment built and validated the
instrument locally, then ran the full-corpus characterization on Modal. No
claim here is promoted to a confirmatory result; this is "find it and poke
around."

## Design

**Substrate**: unsloth/Qwen3-4B (bf16). Autograd/JVPs do not work cleanly
through bnb-4bit quantized weights, so the J-lens itself runs on the
unquantized bf16 sibling of the raw-base. Same architecture/config as
unsloth/Qwen3-4B-bnb-4bit (36 layers, hidden 2560, vocab 151936, tied
embeddings, Qwen3ForCausalLM) confirmed by direct inspection. The H1
directions were swapped before full-corpus launch to the sibling
two-signal-caution-regulation-instruct bf16 refit, so the Modal H1 read is a
same-substrate bf16 characterization, not the earlier cross-quantization
approximation used in the local spot-check.

**Signal / instrument**: `jlens.py`, a from-scratch J-lens implementation.
`verbalize(layer, direction)` computes the corpus-averaged Jacobian-vector
product of final-token logits wrt a layer's hidden state, applied to a fixed
external direction (never materializes the full Jacobian -- by linearity,
averaging per-prompt local JVPs against the SAME direction equals applying
the corpus-averaged operator to that direction). `layer_profile()` locates
the workspace across depth via kurtosis / Hoyer sparsity / effective linear
dimensionality of the J-lens readout, using a small fixed battery of random
probe directions (not self-referential JVPs -- see jlens.py's module
docstring for why: RMSNorm's scale-invariance makes a self-referential JVP
identically zero at the final layer, a pure math artifact this design
avoids). Attention runs in eager mode (`attn_implementation="eager"`):
double-backward through PyTorch's fused SDPA kernels is not implemented
(confirmed empirically), so any layer short of the very last needs eager
attention for the double-backward JVP trick to work at all.

**Rendering**: plain user-turn chat-template render (no system prompt,
`enable_thinking=False`), a single forward pass per prompt (no generation
needed -- final-token logits from the prompt's own forward pass are the
"final-token logits" the J-lens definition operates on).

**Corpus**: 1000 questions sampled (seed 20260707) from this repo's own AH/AK
Stage-1 pool (diverse in topic: ambiguous, controversial, unsolved_problem,
future_unknown, false_assumption, counterfactual categories; no clean
pre-existing general-diversity prompt set was found via `bin/search`).
NOT committed as text (this repo is PUBLIC). The pool is fetched at runtime from
the private HF staging repo `professorsynapse/eh-al-prep-staging`
(`pools/ak_stage1_pool.jsonl`) and the exact 1000-row sample is reproduced
deterministically from the committed `analysis-committed/corpus/jlens_corpus_manifest.json`
(seed + n + source + selected row-keys, no question text) -- see PROVENANCE.md
there for source/license (CC-BY-NC-4.0, non-commercial).

**Arms / directions tested (H1)**: the four fitted directions from the
sibling two-signal-caution-regulation-instruct experiment, copied into
`analysis-committed/source_directions/` for self-containment: `u_d_L34`
(doubt: known-correct vs unknown-refused mean difference), `pos_ctrl_L34`
(caution / answer-vs-refuse mass-mean), `neg_ctrl_L34` (confab-propensity,
logistic), `c_hat_L34` (orthogonalized caution write direction). All four
confirmed fit on `unsloth/Qwen3-4B` bf16, raw-base arm, decoder block index
33 (this project's "L34" naming; hs_index = block_index + 1 = 34 in this
module's own indexing convention, see `direction_layer_field_to_hs_index`).

**Controls**: correctness smoke (verbalize at the final layer vs the naive
logit lens -- unembed(v) = model's own final RMSNorm + lm_head applied
directly to v) is the instrument's own internal validity check, run before
any characterization is trusted or any Modal spend is prepped.

**Instrument files** (`exp sign` pins): `jlens.py`, `cloud/modal_jlens.py`.

## Prediction

Final-layer J-lens will closely track the logit lens; the workspace band
will locate mid-to-late but short of the final layers, putting L34 near or
past the workspace/motor boundary; pos_ctrl and c_hat will verbalize as
first-person-hedge/abstention/error-adjacent tokens more clearly than u_d or
neg_ctrl.

## Falsifier

No falsifier is pre-registered for the characterization itself (lab-
diagnostic, not a gated confirmatory claim). The correctness smoke carries
its own internal go/no-go: nonsensical or near-chance agreement between
verbalize(final_layer, v) and unembed(v) would mean the instrument is broken
and Modal prep must stop rather than proceed to characterize a broken tool.
That smoke PASSED (see Outcome / NOTEBOOK.md).

## Gates

Not applicable in the hard pass/fail sense (lab-diagnostic, characterization
only). The one operational bar that WAS checked before proceeding: the
correctness smoke's cosine similarity and top-k overlap between
verbalize(final_layer, v) and unembed(v) needed to show a strong,
non-coincidental match (informally, well above chance-level top-k overlap
and a clearly positive cosine similarity) for the implementation to be
trusted enough to prep the Modal run. The local smoke passed, and the
full-corpus Modal smoke reproduced it: mean cosine similarity 0.9811, mean
top-10 overlap 0.82, top-1 match 3/5 (n=1000 prompts, 5 random directions).

## Predictions scoreboard

| Predictor | Call |
|-----------|------|
| orchestrator | |
| user | |

## Outcome

Resolved 2026-07-07. Artifacts are committed under
`analysis-committed/results/jspace-jlens-r1/`:
`smoke_full.json`, `h1_full.json`, `profile_full.json`, `job_log.txt`, and
`DONE`. The Modal run used `run_tag=jspace-jlens-r1`, seed 20260707,
model `unsloth/Qwen3-4B`, n_prompts=1000, and completed in 10760.2 seconds
on an A10/A10G-class Modal GPU.

**Instrument check**: the full-corpus final-layer correctness smoke passed:
mean cosine similarity 0.9811, mean top-10 overlap 0.82, and top-1 match 3/5
between `verbalize(final_layer, v)` and direct unembed for 5 random
directions.

**H1 direction verbalization**: the same-substrate bf16 H1 read shows a
split. `u_d_L34` verbalizes mostly as answer/reply tokens, especially
Chinese answer words: `答案` (answer), `回答` (reply/answer), `的答案` (the
answer), plus `answer`. It is therefore an answer/readout axis more than an
explicit abstention phrase axis. `pos_ctrl_L34` verbalizes as first-person
and absence/impossibility tokens: `I`, `我` (I/me), `empty`, `空` (empty),
and `impossible`. `c_hat_L34` is similar but more error/absence-weighted:
`empty`, `error`, `impossible`, `空`, and `不到` (cannot reach/cannot get).
`neg_ctrl_L34` is a local null for clean verbalization, dominated by noisy
fragments and unrelated Chinese/code-ish tokens such as `hotspot`/`热点`.

**Layer profile / workspace location**: effective-dimensionality fraction
stays very low through early and early-middle layers (roughly 0.0025 to
0.0035 from hs=2 through hs=20), rises sharply in the mid-late band
(0.00593 at hs=23, peak 0.01057 at hs=26, 0.00802 at hs=29), then falls
again toward the final layers (0.00586 at hs=32, 0.00229 at hs=35, 0.00100
at hs=36). Kurtosis declines across this same late band (0.478 at hs=20,
0.385 at hs=23, 0.276 at hs=26, about 0.225 by hs=29/32/36), while Hoyer
sparsity rises and stays high from hs=23 onward. On this characterization,
the workspace-like dimensionality band centers around hs=23-29 and peaks at
hs=26. This project's L34 direction layer maps to hs=34, so L34 sits just
past the peak workspace band, in the declining late-layer / motor-adjacent
regime rather than at the final layer itself.

Verdict: full-corpus J-lens characterization completed; the instrument smoke
passed, caution directions have clear self/absence/error verbalizable
J-space projections, `u_d` is answer/reply-like, `neg_ctrl` is not cleanly
verbalizable, and L34 lies just after the hs=23-29 workspace-like band.
