# j-space-localization-qwen3-4b notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

### 2026-07-07 -- J-lens build, correctness smoke, local H1 read, Modal prep (STOPPED before launch)

Built `jlens.py`: a from-scratch, read-only Jacobian lens for Qwen3-4B, per
the operational definition in docs/ideas/j-space-global-workspace-actuation-bridge.md
and library/notes/tc-2026-workspace--verbalizable-representations-global-workspace.md.
Two entry points: `verbalize(layer, direction)` (corpus-averaged
Jacobian-vector product of final-token logits wrt a layer's hidden state,
applied to a fixed direction -- never materializes the full Jacobian) and
`layer_profile()` (kurtosis / Hoyer sparsity / effective-linear-dimensionality
of the J-lens readout across a battery of random probe directions, swept
across depth, to locate the workspace band).

**Substrate**: unsloth/Qwen3-4B (bf16, NOT the bnb-4bit raw-base) -- autograd
JVPs do not work cleanly through bnb-4bit quantized weights. Confirmed via
`AutoModelForCausalLM`/`AutoTokenizer` load that this repo maps 1:1 in
architecture/config onto unsloth/Qwen3-4B-bnb-4bit (36 layers, hidden 2560,
vocab 151936, tied embeddings) -- same Qwen3ForCausalLM, just unquantized.
**Substrate caveat that must travel with every H1 number**: the four fitted
directions (u_d, pos_ctrl, neg_ctrl, c_hat) were fit on bnb-4bit activations
(confirmed via their own provenance blocks: `arm: raw-base`, `unsloth/Qwen3-4B-bnb-4bit`).
Running them through the bf16 J-lens is an approximate CROSS-QUANTIZATION
check, not a same-substrate readout.

**Layer-index gotcha resolved**: the fitted-direction JSONs carry `"layer": 33`
(0-indexed decoder-block index / `census_block_index`) for what the project
calls "L34" (1-indexed hs_index = block_index + 1 = 34, matching HF's
`output_hidden_states` tuple convention where index 0 = embeddings). This
mapping is implemented once as `direction_layer_field_to_hs_index()` and
used everywhere rather than an inline "+1".

**Attention-implementation gotcha (real blocker, fixed)**: the double-backward
JVP trick (two VJPs, the standard forward-over-reverse trick for a JVP when
forward-mode AD isn't wired through the whole model) throws
`RuntimeError: derivative for aten::_scaled_dot_product_flash_attention_backward
is not implemented` for ANY layer whose "rest of network" includes an
attention block (i.e. every layer except the very last). Confirmed this is a
real PyTorch/SDPA limitation (torch 2.9.1+cu128, transformers 4.57.1), not a
bug in this module's JVP code -- the smoke at the FINAL layer worked before
this fix precisely because f_rest there is norm+lm_head only, no attention.
Fixed by loading the model with `attn_implementation="eager"` (plain
matmul+softmax attention, which supports ordinary second-order autograd).

**Sparsity-metric gotcha (found and fixed via the tiny smoke)**: an initial
design measured sparsity via `exp(entropy(softmax(push_vector)))`. This came
out ~0 (near-uniform) at EVERY layer, because the raw JVP push vector's
absolute magnitude is small and incidental (a linearized delta for a
unit-norm input perturbation, not a calibrated logit vector) -- softmax
entropy conflates that incidental scale with genuine concentration. Replaced
with Hoyer sparsity on `|push|` directly ((sqrt(n) - L1/L2)/(sqrt(n)-1)),
which is scale-invariant. Confirms the general lesson: don't run softmax on
an un-calibrated linearized delta and read its entropy as "concentration."

**Self-JVP degeneracy (design decision, not a bug)**: a self-referential
"use the layer's own activation as both base point and tangent" design for
layer_profile is EXACTLY zero at (and increasingly damped near) the final
layer, by Euler's homogeneous-function theorem (RMSNorm is scale-invariant,
i.e. degree-0 homogeneous, so its directional derivative along its own input
is identically 0). layer_profile() therefore uses a small fixed battery of
RANDOM probe directions instead (never aligned with any specific instance's
activation), read through the same corpus-averaged machinery as verbalize().
Documented at length in jlens.py's module docstring so a future reader does
not "fix" this back into the degenerate form.

**Correctness smoke (PASSED)**: `jlens.py smoke --n-prompts 20 --n-test-dirs 5`
on the local 3090. verbalize(final_layer, v) vs direct unembed(v) (model's own
final RMSNorm + lm_head applied to v with no linearization) across 5 random
unit directions: mean cosine similarity 0.981, mean top-10 token overlap
0.82, top-1 token match on 3/5 directions. Matches the theoretical argument
in jlens.py's docstring (RMSNorm's Jacobian at a generic point is
approximately a positive scalar multiple of its own naive-unembed direction
for a probe direction not radially aligned with the base point, so ranking
should be preserved even though the two are not bit-identical). Runtime: ~16s
end to end (including model load) for this smoke size.

**Local layer_profile smoke** (`--n-prompts 50 --layers 2,6,10,14,18,22,26,30,34,36
--n-random-dirs 4`, ~3m44s): kurtosis peaks in an early-to-mid band (0.70 at
hs=18) and falls toward the final layers (0.22 at hs=36); effective-dimension
fraction shows a genuine rise-then-fall bump peaking around hs=26 (0.20) vs
low at both extremes (0.06 at hs=2, 0.02 at hs=36) -- a partial, noisy (n=50,
k=4) echo of the paper's mid-band-higher-dimensionality claim. NOT a resolved
characterization at this sample size; the Modal run's n=1000 is needed before
reading this as a real locate result.

**Local H1 direction check** (`--n-prompts 100`, offsets -4,-2,0,+2 from each
direction's own fit layer, ~1m49s): **pos_ctrl_L34** (caution / answer-vs-refuse)
verbalizes overwhelmingly and consistently as first-person hedge tokens --
literal `'我不知道'` ("I don't know") and `'我没有'` ("I don't have/I do not")
appear in the top-15 at hs=34 and hs=36, alongside 'I'/' I'/'"I' dominating
every layer tested. **c_hat_L34** (the orthogonalized caution WRITE direction)
verbalizes as 'I' plus explicit error/absence tokens: ' error', ' ERROR',
'NotFoundError', 'isNaN', '不存在' (does not exist), '错误' (error/mistake),
'不当' (inappropriate), ' inaccessible', ' unavailable'. **u_d_L34** (doubt)
is weaker and more indirect: 'answer'/'答案'(answer)/'correct'/'familiar'/
'熟悉的'(familiar) -- plausible given it's a known-vs-unknown mean-difference
axis, but not first-person "I don't know" tokens the way pos_ctrl/c_hat are.
**neg_ctrl_L34** (confab-propensity, logistic) shows no clear semantic theme
in this sample (mostly unrelated tokens: '兰', 'resizable', 'osg', 'kernel',
'pivot') -- an honest local null for that direction under the J-lens. Results
identical in character between n=30 and n=100 (not a small-sample fluke).
Full h1_local_n100.json / profile_local_n50.json / smoke_20.json kept
locally under the gitignored analysis/ (not committed; see analysis-committed/
for the committed corpus/direction copies actually needed to reproduce).

**Modal cost estimate** (from an ACTUAL local-3090 benchmark, not a guess):
single-direction `corpus_average_push` at n_prompts=100: hs_index=8 ->
152.9ms/prompt, hs_index=20 -> 106.6ms/prompt, hs_index=34 -> 59.1ms/prompt,
hs_index=36 -> 51.2ms/prompt (cost falls almost linearly with the number of
remaining transformer blocks the double-backward must traverse). Summed
across the Modal script's chosen 13-layer depth sweep, this gives ~1.39s per
(prompt, direction) for the full profile stage; at n_prompts=1000 and
n_random_dirs=5 that's ~1.93h; H1 (4 directions x 4 near-final-layer offsets
x 1000 prompts) ~0.31h; smoke + overhead a few more minutes. Total GPU-busy
estimate ~2.3-2.5h on an A10G (~$1.10-1.50/hr) => roughly $3-4 of the lead's
$25 cap.

**Data-staging decision (deviation from the AP/AK/AM Modal pattern, worth a
future reader's attention)**: those amendments stage their prompt pools to a
private external HF dataset repo (`professorsynapse/eh-al-prep-staging`) for
their Modal containers to fetch, and push results back the same way. Writing
an equivalent staging script for THIS experiment's inputs was blocked twice
by this session's auto-mode permission classifier (flagged as an
agent-initiated external data movement the task never explicitly named), so
this experiment instead COMMITS its corpus (1000 question strings, ~90KB,
question-text-only, see analysis-committed/corpus/PROVENANCE.md) and its
four fitted directions directly under analysis-committed/, and
cloud/modal_jlens.py relies solely on `git clone` at the pinned commit for
inputs and the Modal Volume (not any external HF repo) for results retrieval.
No huggingface_hub upload of anything happens anywhere in this experiment's
code.

**Modal script**: cloud/modal_jlens.py, structure ported from
experiments/ap-veto-length-balanced-confirmatory/cloud/modal_ap_veto_length_balanced.py
(detached app, Volume checkpoint daemon @120s, DONE marker, retries), minus
the HF pool-fetch/results-upload steps per the above. Runs `jlens.py smoke`,
then `h1`, then `profile` (in that order, cheapest-first) against the
committed corpus/directions, at n_prompts=1000. Launch-gated on
`EHR_LAUNCH_OK=j-space-localization-qwen3-4b` + `MODAL_COST_CAP_USD` (both
required, neither hardcoded), same pattern as AP. NOT RUN by this agent --
launch_guard and this repo's binding invariants reserve the launch decision
for the lead.

Artifacts: jlens.py, cloud/modal_jlens.py, analysis-committed/corpus/
(jlens_corpus_manifest.json + PROVENANCE.md; the corpus itself is fetched from
private HF at runtime, never committed), analysis-committed/source_directions/
(u_d_L34.json, pos_ctrl_L34.json, neg_ctrl_L34.json, c_hat_L34.json, copied
from the sibling two-signal worktree for self-containment).
