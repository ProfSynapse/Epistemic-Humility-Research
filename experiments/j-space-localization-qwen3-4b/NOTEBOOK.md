# j-space-localization-qwen3-4b notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

### 2026-07-07 -- Modal full-corpus J-lens run completed and resolved

Launched the full-corpus Modal run after swapping H1 inputs to the
same-substrate bf16 directions from `two-signal-caution-regulation-instruct`.
The first image build exposed a package-index bug in `cloud/modal_jlens.py`
(`accelerate` was looked up on the PyTorch CUDA wheel index); fixed by
installing torch from the CUDA index separately from PyPI packages. The first
spawn then reached full-corpus smoke but failed at H1 because
`--layer-offsets -4,-2,0,2` was parsed as an option value starting with `-`;
fixed to `--layer-offsets=-4,-2,0,2`. The old auto-retry app was stopped
after the fixed relaunch was confirmed healthy.

Final successful run: Modal app `ap-vnvIl5WaUIDDwhEN2UWwFF`, function call
`fc-01KWZ03RBXAK7HQKV7SQ4AM9GX`, run tag `jspace-jlens-r1`, seed 20260707,
model `unsloth/Qwen3-4B`, n_prompts=1000. DONE marker written at 2026-07-07
18:15:46 America/New_York; job log reports `total_sec=10760.2`.
Artifacts pulled from `eh-jspace-jlens-logs/ckpt/jspace-jlens-r1` and
committed under `analysis-committed/results/jspace-jlens-r1/`. Containment
check: the committed results contain metrics, token strings, and provenance
metadata only, not question text, aliases, prompts, or row keys.

Full-corpus smoke reproduced the local implementation check: mean cosine
similarity 0.9811, mean top-10 overlap 0.82, and top-1 match 3/5 between the
final-layer J-lens and the direct unembed baseline over 5 random directions.

H1 direction read: `u_d_L34` verbalizes as an answer/reply axis, strongest at
and after its fit layer (`答案`, `回答`, `的答案`, `answer`, `your/你的`).
`pos_ctrl_L34` verbalizes as first-person and absence/impossibility (`I`,
`我`, `empty`, `空`, `impossible`). `c_hat_L34` is similar but more
error/absence-weighted (`empty`, `error`, `impossible`, `空`, `不到`).
`neg_ctrl_L34` remains a null/noisy verbalization, with unrelated fragments
such as `hotspot`/`热点`, `津`, and code-ish/proper-name-ish pieces.

Layer profile: effective-dimensionality fraction peaks in the mid-late band,
not at L34 or the final layer: hs=23 0.00593, hs=26 0.01057 (peak), hs=29
0.00802, then hs=32 0.00586, hs=35 0.00229, hs=36 0.00100. Early and
early-middle layers stay around 0.0025-0.0035. Kurtosis declines through the
same band, and Hoyer sparsity rises from hs=23 onward. Read: the
workspace-like dimensionality band is centered around hs=23-29 and peaks at
hs=26; L34 maps to hs=34, so it sits just after the workspace peak in a
late/motor-adjacent declining regime.

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
**Direction-substrate update before full-corpus launch**: the first local H1
spot-check used the older copied direction files, which made those local H1
numbers an approximate cross-quantization read. Before Modal launch, the
direction inputs were swapped to the two-signal-caution-regulation-instruct
bf16 refit (`unsloth/Qwen3-4B`, same L34/block-index convention), so the
full-corpus H1 run is same-substrate bf16. Treat the local H1 qualitative
themes below as pre-swap orientation only, not as the launch input result.

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

**Local H1 direction check, pre-bf16-swap orientation only** (`--n-prompts 100`, offsets -4,-2,0,+2 from each
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
locally under the gitignored analysis/ (not committed). The Modal run uses
the post-swap bf16 direction files under analysis-committed/source_directions/
and re-derives the corpus from private HF at runtime.

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

**Data-staging decision (matches the AP/AK/AM containment rule)**: the
question-text corpus is NOT committed to this public repo. The Modal
container fetches the AH/AK Stage-1 source pool from private HF
(`professorsynapse/eh-al-prep-staging`) and deterministically re-samples the
same 1000 row_keys recorded in analysis-committed/corpus/
jlens_corpus_manifest.json. The four fitted directions are our own derived
artifacts and remain committed under analysis-committed/source_directions/.
Results are retrieved from the Modal Volume, not uploaded to HF. No
huggingface_hub upload of outputs happens anywhere in this experiment's code.

**Modal script**: cloud/modal_jlens.py, structure ported from
experiments/ap-veto-length-balanced-confirmatory/cloud/modal_ap_veto_length_balanced.py
(detached app, Volume checkpoint daemon @120s, DONE marker, retries), minus
the HF pool-fetch/results-upload steps per the above. Runs `jlens.py smoke`,
then `h1`, then `profile` (in that order, cheapest-first) against the
runtime-fetched corpus and committed bf16 direction artifacts, at
n_prompts=1000. Launch-gated on
`EHR_LAUNCH_OK=j-space-localization-qwen3-4b` + `MODAL_COST_CAP_USD` (both
required, neither hardcoded), same pattern as AP. NOT RUN by this agent --
launch_guard and this repo's binding invariants reserve the launch decision
for the lead.

Artifacts: jlens.py, cloud/modal_jlens.py, analysis-committed/corpus/
(jlens_corpus_manifest.json + PROVENANCE.md; the corpus itself is fetched from
private HF at runtime, never committed), analysis-committed/source_directions/
(u_d_L34.json, pos_ctrl_L34.json, neg_ctrl_L34.json, c_hat_L34.json, copied
from the sibling two-signal worktree for self-containment).

## 2026-08-27 — Exhaust published to HF (aggregate shape)

Data-exhaust release, PI-approved in-conversation (explicit permission
2026-08-27, batch 2 of the exhaust backfill, task-56c61a). Built with the
data-exhaust skill (aggregate-only copy-everything mirror of
analysis-committed/: no question text, generation text, or hidden states;
verify_exhaust.py PASS including the --experiment-dir completeness check;
zero exclusions). 15 files / ~0.48 MB, built at repo commit fab3cad6.

- HF repo: `professorsynapse/eh-j-space-localization-qwen3-4b` (dataset)
- HF revision: `f03567a5f44eaf66cb9d843211f26d39245027dd`
