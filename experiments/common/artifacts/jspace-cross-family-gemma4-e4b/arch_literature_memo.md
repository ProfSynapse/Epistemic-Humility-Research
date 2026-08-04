# gemma-4-E4B-it: published architecture picture and lineage of unusual components

**Status**: literature/architecture research memo, CPU + web only, no GPU touched. Every
claim below is tagged with its source (local file+field, or a URL actually fetched). Nothing
is inferred from training-data memory without a citation. This does not reopen or change the
`j-space-cross-family-layer-contrast` gemma4-e4b disposition — it is background material for
the lead to reason about the write-verified behavioral null from documented mechanism.

---

## 1. Verified local checkpoint inventory

**Checkpoint**: HF cache `~/.cache/huggingface/hub/models--google--gemma-4-E4B-it/snapshots/fee6332c1abaafb77f6f9624236c63aa2f1d0187/` (matches the pin in `experiments/gemma-4-e4b-family-atlas/AMENDMENT.md`, revision `fee6332c1abaafb77f6f9624236c63aa2f1d0187`). No model card / README file is cached alongside it (`find ... -iname "*.md"` over that snapshot dir returned nothing) — the model card text used in §2 came from the live HF page, not a local file.

### 1a. `config.json` (top-level `Gemma4Config` + `text_config` = `Gemma4TextConfig`)

Read directly with `json.load`; full dump captured in this session's transcript. Salient fields:

| field | value |
|---|---|
| `architectures` | `["Gemma4ForConditionalGeneration"]` |
| `model_type` (text) | `gemma4_text` |
| `hidden_size` | 2560 |
| `num_hidden_layers` | 42 |
| `num_attention_heads` / `num_key_value_heads` / `head_dim` / `global_head_dim` | 8 / 2 / 256 / 512 |
| `hidden_size_per_layer_input` | 256 |
| `vocab_size_per_layer_input` | 262144 |
| `num_kv_shared_layers` | **18** |
| `layer_types` | alternating, `full_attention` at 0-indexed blocks `[5,11,17,23,29,35,41]`, `sliding_attention` elsewhere (7 full / 35 sliding, ratio 1:5) |
| `sliding_window` | 512 |
| `rope_parameters.full_attention` | `partial_rotary_factor: 0.25`, `rope_theta: 1000000.0`, `rope_type: "proportional"` |
| `rope_parameters.sliding_attention` | `rope_theta: 10000.0`, `rope_type: "default"` |
| `final_logit_softcapping` | 30.0 |
| `attention_k_eq_v` | **false** (this specific checkpoint) |
| `use_double_wide_mlp` | false |
| `enable_moe_block` / `num_experts` / `top_k_experts` / `expert_intermediate_size` | false / null / null / null |
| `tie_word_embeddings` | true |
| `max_position_embeddings` | 131072 |
| `hidden_activation` | `gelu_pytorch_tanh` |
| `rms_norm_eps` | 1e-6 |

The top-level config also carries `vision_config` (16-layer ViT-style tower, hidden 768) and `audio_config` (12-layer conformer-ish tower with `Gemma4Audio*` classes, hidden 1024, `residual_weight: 0.5`) — `Gemma4ForConditionalGeneration` is a multimodal wrapper nesting a text `Gemma4TextModel`, `Gemma4VisionModel`, and `Gemma4AudioModel`. Only the text backbone is in scope for the null.

### 1b. `model.safetensors` parameter-name inventory

No `model.safetensors.index.json` — this checkpoint is a single unsharded file. Enumerated all 2130 tensor names via `safetensors.safe_open(...).keys()` (CPU, key listing only, no tensor materialization beyond what §1c needed). Unique name patterns (layer index collapsed to `N`), text-backbone (`model.language_model.*`) subset:

```
model.language_model.embed_tokens.weight
model.language_model.embed_tokens_per_layer.weight
model.language_model.layers.N.input_layernorm.weight
model.language_model.layers.N.layer_scalar
model.language_model.layers.N.mlp.{gate,up,down}_proj.weight
model.language_model.layers.N.per_layer_input_gate.weight
model.language_model.layers.N.per_layer_projection.weight
model.language_model.layers.N.post_attention_layernorm.weight
model.language_model.layers.N.post_feedforward_layernorm.weight
model.language_model.layers.N.post_per_layer_input_norm.weight
model.language_model.layers.N.pre_feedforward_layernorm.weight
model.language_model.layers.N.self_attn.{k_norm,k_proj,o_proj,q_norm,q_proj,v_proj}.weight
model.language_model.norm.weight
model.language_model.per_layer_model_projection.weight
model.language_model.per_layer_projection_norm.weight
```

**Explicitly absent** from this checkpoint's full 2130-name inventory: any tensor name containing `altup`, `laurel`, `router`/`expert` under `language_model.layers.*` (MoE tensors are architecturally supported by the code — see §1c — but not instantiated for this dense E4B checkpoint, consistent with `enable_moe_block: false`), or any `matformer`/`submodel` naming. This is a direct inventory fact, not an inference from the config.

### 1c. `transformers==5.5.0` installed source (`transformers/models/gemma4/`)

Read `modeling_gemma4.py` directly (not fetched from the web — this is the CPU-installed package that actually executes for this checkpoint, so it is authoritative for control flow). Full class list (37 classes) confirms **no `AltUp` or `Laurel`/`LAuReL` class exists anywhere in the Gemma4 modeling file** — this is a from-scratch grep-equivalent read of every `class ` line, not a keyword miss.

`Gemma4TextDecoderLayer.forward` (`modeling_gemma4.py:1348-1403`), read verbatim:

```
residual = hidden_states
hidden_states = input_layernorm(hidden_states)
hidden_states, _ = self_attn(hidden_states, ...)
hidden_states = post_attention_layernorm(hidden_states)
hidden_states = residual + hidden_states                    # branch 1: attention

residual = hidden_states
hidden_states = pre_feedforward_layernorm(hidden_states)
hidden_states = mlp(hidden_states)
hidden_states = post_feedforward_layernorm(hidden_states)
hidden_states = residual + hidden_states                    # branch 2: MLP

if hidden_size_per_layer_input:                              # true for E4B (256)
    residual = hidden_states
    hidden_states = per_layer_input_gate(hidden_states)       # Linear(2560 -> 256)
    hidden_states = act_fn(hidden_states)                     # gelu_pytorch_tanh
    hidden_states = hidden_states * per_layer_input           # elementwise gate by this token's per-layer embedding
    hidden_states = per_layer_projection(hidden_states)       # Linear(256 -> 2560)
    hidden_states = post_per_layer_input_norm(hidden_states)  # RMSNorm
    hidden_states = residual + hidden_states                  # branch 3: PLE

hidden_states *= layer_scalar                                 # applied to the WHOLE accumulated residual, once
return hidden_states
```

This is a **third residual branch** (PLE) beyond attention and MLP, not previously enumerated in the prior forensics report — it re-injects a fresh, token-and-layer-dependent (but injected-delta-independent) contribution into the residual stream at the end of *every* block, immediately before that block's `layer_scalar` multiply. `layer_scalar` is `register_buffer("layer_scalar", torch.ones(1))` (`modeling_gemma4.py:1331`) — a single learned scalar per block, populated from checkpoint (see forensics report §D/§E for the actual per-block values, 0.061–0.887, read from this same checkpoint's shards).

KV-sharing (`modeling_gemma4.py:1148-1156, 1198-1215`): `first_kv_shared_layer_idx = num_hidden_layers - num_kv_shared_layers = 42 - 18 = 24`. For `layer_idx >= 24`, the layer does not compute its own K/V; it looks up the K/V computed by the last prior layer of the *same* `layer_types` category (sliding or full), via `past_key_values.shared_layers[kv_shared_layer_index]`.

`Gemma4TextExperts`/`Gemma4TextRouter` classes exist (`modeling_gemma4.py:1244, 1283`) and are wired into `Gemma4TextDecoderLayer.__init__`/`.forward` conditionally on `config.enable_moe_block` — dead code for this checkpoint (`enable_moe_block: false`, no expert/router tensors in the safetensors inventory), presumably used by a larger MoE Gemma-4 size.

`convert_gemma4_weights.py` (installed package, lines ~804-827, read directly): maps the `layer_scalar` buffer from an upstream checkpoint parameter literally named `skip_scale` — confirms this buffer is populated from real trained weights, not left at the random-init identity (`init.ones_(module.layer_scalar)` in `_init_weights`, `modeling_gemma4.py:1478`, is the *un-trained* default only).

---

## 2. Primary sources found (URL/arXiv ID actually opened, and what each establishes)

1. **Gemma 4 Technical Report** — Gemma Team, Google DeepMind. arXiv **2607.02770**. Fetched `https://arxiv.org/abs/2607.02770` (abstract/metadata) and `https://arxiv.org/html/2607.02770v1` (full HTML text search) and `https://arxiv.org/pdf/2607.02770` (full PDF text search). This is the primary architecture source for the whole family (dense 2.3B(E2B)/4.5B(E4B)/12B/31B + MoE variants).
   - Establishes: *"E2B and E4B use per-layer embeddings as in Gemma 3n, making them 2.3B and 4.5B effective out of 5B and 8B total parameters respectively"* — direct textual confirmation that E4B's PLE mechanism is explicitly inherited from Gemma 3n, not a new invention.
   - Establishes: *"Our local to global attention ratio patterns follow Gemma Team, that is, 4-to-1 local attention blocks for E2B and 5-to-1 for the rest"* — matches the config's 1-full-per-6-blocks (5:1) pattern for E4B exactly, and explicitly frames the final layer as always global (also matches `layer_types[41] == "full_attention"`, the terminal block).
   - Establishes: *"We improve memory efficiency by re-using keys as values in the global attention layers"* and *"we share the KV cache with ratios of 20/35 and 18/42 for the E2B and E4B model"* — the `18/42` figure is an exact, independent match to the local `num_kv_shared_layers: 18` / `num_hidden_layers: 42` config values (§1a), i.e. the published report and the checkpoint config agree bit-for-bit on this figure. Note: the report frames "key-reuse-as-value" as a Gemma-4-family technique, but this specific E4B checkpoint's `attention_k_eq_v` config field reads `false` (§1a) — a discrepancy worth flagging (see §5).
   - **NOT FOUND anywhere in this report** (search of full HTML + full PDF text, keyword-targeted): "skip scale", "layer scalar", any named per-block learned residual-multiplier mechanism; "sandwich norm" / explicit 4-RMSNorm-per-block description; "logit softcapping" / "soft-cap"; "massive activation" / "outlier" / "activation dimension"; "AltUp"; "LAuReL"; "MatFormer" / "nested" / "elastic inference" / "matryoshka". The report simply does not document these terms in the portions I could search (see §5 caveat on PDF-extraction completeness).

2. **`google/gemma-4-E4B-it` model card** — Hugging Face. Fetched `https://huggingface.co/google/gemma-4-E4B-it`.
   - Establishes the plain-language description of PLE: *"Rather than adding more layers or parameters to the model, PLE gives each decoder layer its own small embedding for every token. These embedding tables are large but are only used for quick lookups, which is why the effective parameter count is much smaller than the total."* This matches the code mechanism read in §1c (`embed_tokens_per_layer`, gated per-block PLE branch) precisely: a per-block, per-token embedding lookup gated into the residual, not part of the "effective" (active-compute) parameter count.
   - Establishes hybrid local/global attention description ("local sliding window attention with full global attention, ensuring the final layer is always global"), sliding window 512, "Unified Keys and Values" in global layers, and "Proportional RoPE (p-RoPE)" — matching `rope_type: "proportional"` on the full-attention rope params in config (§1a).

3. **Gemma 3n overview** — Google AI for Developers. Fetched `https://ai.google.dev/gemma/docs/gemma-3n`.
   - Establishes the E-prefix definition at its origin: *"The `E` prefix indicates these models can operate with a reduced set of Effective parameters."* and the same PLE caching description as the Gemma 4 card, confirming E4B's naming convention and PLE mechanism are carried forward unchanged from Gemma 3n.
   - Establishes MatFormer's nested/elastic framing for Gemma 3n: *"Gemma 3n models use a Matryoshka Transformer or MatFormer model architecture that contains nested, smaller models within a single, larger model."*
   - This page does **not** mention AltUp or LAuReL at all (checked directly).

4. **Gemma3n model docs** — Hugging Face `transformers` documentation. Fetched `https://huggingface.co/docs/transformers/main/model_doc/gemma3n`.
   - This is the source that lists Gemma 3n's full efficiency-mechanism set in one place: *"there are many new additions in this model, including Alternating Updates (AltUp), Learned Augmented Residual Layer (LAuReL), MatFormer, Per-Layer Embeddings (PLE), Activation Sparsity with Statistical Top-k, and KV cache sharing."*
   - Its `Gemma3nTextConfig` field docs (read directly from the fetched page) give an authoritative one-line mechanism gloss for each: `altup_num_inputs` ("number of predictions AltUp should make"), `altup_active_idx`/`altup_coef_clip`/`altup_correct_scale` (AltUp is a multi-prediction correction/coefficient mechanism operating on the residual stream), `laurel_rank` ("intermediate size for linear projections in the Learned Augmented Residual Layer" — i.e., a low-rank residual-branch reweighting), and — directly relevant — `num_kv_shared_layers` defined identically in name and semantics to Gemma 4's field: *"the last `num_hidden_layers` layers in the model 'share' the KV values..."* This confirms `num_kv_shared_layers` as a Gemma-3n-originated config field carried into Gemma 4 verbatim.
   - Links out to the two originating papers for AltUp and LAuReL (used to fetch §2.5–2.6 below).

5. **AltUp: "Alternating Updates for Efficient Transformers"** — Cenk Baykal et al., Google Research. arXiv **2301.13310** (NeurIPS 2023). Existence, authorship, and venue confirmed via search of `arxiv.org/abs/2301.13310` and the NeurIPS proceedings listing; not deep-read beyond the abstract/mechanism gloss above (the Gemma3n config docs already gave the operational one-liner). AltUp increases representational capacity by carrying multiple parallel residual-stream "predictions" and correcting one active one, without proportionally increasing compute.

6. **LAuReL: "Learned Augmented Residual Layer"** — Gaurav Menghani, Ravi Kumar, Sanjiv Kumar, Google Research. arXiv **2411.07501** (ICML 2025). Existence, authorship, and venue confirmed via search of `arxiv.org/abs/2411.07501`. Mechanism (from the Gemma3n config docs, §2.4): a low-rank linear reweighting of the residual branch, i.e. `x' = (L·R)·x + f(x)` in place of the canonical `x' = x + f(x)` — a *low-rank matrix* applied to the skip connection, not a single scalar.

7. **Massive Activations in Large Language Models** — Mingjie Sun, Xinlei Chen, J. Zico Kolter, Zhuang Liu (CMU & Meta AI). arXiv **2402.17762**. Confirmed via search of `arxiv.org/pdf/2402.17762` metadata (title, authors, abstract). This is the paper the prior forensics report (§B) referenced qualitatively for the dim-2302 massive-activation pattern; confirmed here as a real, correctly-cited paper — the forensics report's citation was accurate.

8. **MatFormer: Nested Transformer for Elastic Inference** — Devvrit, Sneha Kudugunta, Aditya Kusupati, Tim Dettmers, Kaifeng Chen, Inderjit Dhillon, Yulia Tsvetkov, Hannaneh Hajishirzi, Sham Kakade, Ali Farhadi, Prateek Jain. arXiv **2310.07707**. Confirmed via search of `arxiv.org/abs/2310.07707` and the HF papers mirror. Mechanism: nested FFN blocks of varying width trained jointly so that smaller sub-models can be extracted from a larger trained model without retraining.

---

## 3. Component-by-component lineage table

| Component | Present in this E4B checkpoint? | Originating paper / report | Mechanism (one sentence) |
|---|---|---|---|
| Per-Layer Embeddings (PLE) | **Yes** — `embed_tokens_per_layer`, `per_layer_input_gate/projection`, PLE branch in every decoder layer (§1c) | Gemma 3n (ai.google.dev, HF gemma3n docs); explicitly cited as inherited by Gemma 4 report (2607.02770) | A per-token, per-layer embedding is looked up, gated (sigmoid-ish gelu gate on a hidden-state-derived vector times the lookup), projected back to hidden size, and added as a third residual branch every block; the large lookup table sits outside the "effective" active-compute parameter count, which is what "E" in E4B denotes. |
| "Effective" (E-) parameter naming | Yes — E4B = 4.5B effective of 8B total (HF card) | Gemma 3n (ai.google.dev: *"The `E` prefix indicates ... a reduced set of Effective parameters"*) | Naming convention, not a mechanism per se; downstream of PLE's memory/compute split. |
| KV-cache sharing across layers | **Yes** — `num_kv_shared_layers: 18` of 42 (§1a), implemented `modeling_gemma4.py:1148-1215` | Gemma 3n config field (`num_kv_shared_layers`, HF gemma3n docs) carried into Gemma 4 (2607.02770: *"share the KV cache with ratios of ... 18/42 for the E2B and E4B model"*) | The last 18 blocks (indices 24-41) do not compute their own K/V for attention; they read the K/V already computed by the most recent earlier block of the same attention type (sliding or full). |
| Interleaved local/global (sliding/full) attention | **Yes** — 1 full per 6 blocks, full at [5,11,...,41] (§1a) | Gemma 2 report (2408.00118: alternating every-other-layer, 4096/8192 windows) → refined ratio in later Gemma generations; Gemma 4 report (2607.02770) states the current 5:1 ratio and "final layer always global" rule explicitly for E4B | Standard sliding-window attention (window 512 here) at most positions; every 6th block (and always the terminal block) uses full/global attention instead. |
| Logit softcapping (final layer) | **Yes** — `final_logit_softcapping: 30.0` (§1a) | Gemma 2 report (2408.00118): `logits <- soft_cap * tanh(logits/soft_cap)`, soft_cap=50.0 for attention layers / 30.0 for the final layer | Squashes final-layer logits into a bounded range before softmax; Gemma 4's `final_logit_softcapping=30.0` numerically matches Gemma 2's final-layer value exactly. |
| Sandwich normalization (4 RMSNorms/block: pre- and post- both attention and MLP) | **Yes** — `input_layernorm`, `post_attention_layernorm`, `pre_feedforward_layernorm`, `post_feedforward_layernorm` (§1c) | Gemma 2 report (2408.00118): *"we use RMSNorm to normalize the input and output of each transformer sub-layer"*, Table 1 marks both Pre-norm and Post-norm "yes" | Both the branch input and the branch output are RMSNorm'd before the residual add, for both attention and MLP sub-layers — 4 norms/block total, a pattern dating to Gemma 2, not new to Gemma 4. |
| Per-block learned scalar (`layer_scalar` / checkpoint `skip_scale`) | **Yes** — every block, values 0.061-0.887 (this session §1c; values themselves from forensics report §E) | **NOT FOUND** in Gemma 4 report, Gemma 3n docs, or any fetched source under any searched name ("skip scale", "layer scale", "residual scaling", "block scale", "output gate") | Multiplies the entire post-PLE-branch residual-stream output of the block by one learned scalar, every block, as the literal last op before returning. No published description located. |
| AltUp (Alternating Updates) | **No** — no `altup_*` tensors or config fields in this checkpoint or its config.json; no `AltUp` class in `modeling_gemma4.py` | Baykal et al., arXiv 2301.13310 (NeurIPS 2023); adopted by Gemma 3n per HF gemma3n docs | Carries multiple parallel residual "predictions," correcting one active prediction per layer using learned coefficients, to raise representational capacity without proportional compute. **Confirmed absent from Gemma 4's architecture**, not merely undocumented. |
| LAuReL (Learned Augmented Residual Layer) | **No** — no `laurel_*` tensors, no `Laurel` class in `modeling_gemma4.py` | Menghani, Kumar, Kumar, arXiv 2411.07501 (ICML 2025); adopted by Gemma 3n per HF gemma3n docs | Replaces the canonical residual `x + f(x)` with a low-rank-reweighted residual `(L·R)·x + f(x)`. **Confirmed absent from Gemma 4**; the superficially similar `layer_scalar` is architecturally different (single global scalar vs. low-rank matrix) and is not named or coded as LAuReL anywhere in the installed package. |
| MatFormer (nested/elastic submodels) | **No** direct evidence — no matformer-named tensors/config, and NOT FOUND in the Gemma 4 report's searched text | Devvrit et al., arXiv 2310.07707; used for Gemma 3n's E2B-within-E4B nesting (ai.google.dev) | Trains nested FFN sub-blocks of varying width jointly so smaller models can be sliced out without retraining. Gemma 4's report explicitly says E4B/E2B "use per-layer embeddings as in Gemma 3n" but does **not** repeat the MatFormer claim for Gemma 4 in the text I could search — whether Gemma 4's E2B is still MatFormer-nested inside E4B is **not established** by any source opened in this pass. |
| Massive-activation outlier coordinate (dim 2302) | Yes — empirically (forensics report §B, this session's checkpoint) | Sun et al., arXiv 2402.17762 | A tiny number of fixed feature dimensions carry activation magnitudes orders of magnitude above the median, acting as near-input-independent bias terms; general LLM phenomenon, not Gemma-specific, cited descriptively by the prior forensics report and confirmed here as a real, correctly attributed paper. |

---

## 4. Relevance-to-the-null assessment

For each documented component: does it plausibly attenuate/gate/reroute/quarantine an externally injected mid-stack residual-stream delta while still permitting near-perfect readback at the injection site itself? Labels: **SUPPORTED-BY-SOURCE** (a fetched/read source describes the mechanism and its site of action; the *inference* about the null is still the lead's/forensics-report's, not the source's), **LOCAL-INFERENCE-ONLY** (checkpoint/code-confirmed but not documented in any external source), **SPECULATION** (plausible but neither externally documented nor checkpoint-verified for this specific causal role).

1. **`layer_scalar`/`skip_scale` (per-block uniform residual multiplier)** — **LOCAL-INFERENCE-ONLY**. Confirmed to exist and to have all-below-1.0 trained values by direct checkpoint read (this session + forensics report §E); confirmed by code read that it is applied to the *entire* residual (context + anything injected) as the last op of every block. No external source (Gemma 4 report, Gemma 3n docs, or any Gemma-lineage paper searched) names or describes this mechanism, so its role cannot be upgraded past "a real, checkpoint-verified architectural feature with no found published rationale." It remains, on the numbers alone (0.144 survival from hs34, 1.0 from hs42, matching the observed onset-ratio and collapse-ratio asymmetry between hs34/38 and hs42), the single most mechanistically concrete candidate for "perfect readback at the injection point, then progressive multiplicative erasure downstream" — but this is the forensics report's inference, not a documented claim from any paper.

2. **Per-Layer Embedding (PLE) third residual branch, newly read in this pass (§1c)** — **LOCAL-INFERENCE-ONLY** for its relevance to the null specifically, though the *mechanism itself* is **SUPPORTED-BY-SOURCE** (HF model card + Gemma 3n docs describe PLE's memory/compute framing, though not this specific dilution argument). Every downstream block adds a fresh, token-and-position-dependent contribution to the residual stream that is computationally independent of any injected delta (it is a function of the *current* hidden state and a per-layer token lookup, not of "the delta" as a persistent entity). This means an injected delta is not just multiplicatively decayed by `layer_scalar`, it is also continuously diluted by a same-magnitude-order additive re-write at every subsequent layer. No source connects PLE to injection robustness; this is architectural reasoning from a directly-read forward pass, not a documented claim.

3. **KV-cache sharing (18/42 layers)** — **SUPPORTED-BY-SOURCE** for the mechanism's existence and site (Gemma 4 report 2607.02770 + Gemma3n config docs), but its relevance to *this* null is weak/SPECULATION: KV-sharing affects what keys/values downstream *attention* layers use to attend to *past tokens*, not how a given token's own residual-stream content at a fixed position is carried forward through the block stack. It does not obviously touch a same-position, same-forward-pass residual injection the way `layer_scalar` and PLE do. Flagged for completeness because it is real and Gemma-4-specific, not because there is a concrete mechanism connecting it to the null.

4. **Sandwich normalization (4 RMSNorms/block)** — **SUPPORTED-BY-SOURCE** for existence (Gemma 2 report) and **SUPPORTED-BY-SOURCE** (this session's direct code read, §1c) for the specific finding already established in the prior forensics report §D: the two extra norms (`post_attention_layernorm`, `post_feedforward_layernorm`) normalize the *branch output* before it is summed into the residual, not the raw residual stream itself — so an injected delta added directly to the residual is not directly touched by these norms. This is a **ruled-out** mechanism for direct rescaling of the injected delta, confirmed again by this session's independent read of the same forward-pass code.

5. **Interleaved sliding/full attention, logit softcapping, embedding scaling** — **SUPPORTED-BY-SOURCE** for existence and lineage (Gemma 2/4 reports), but per the prior forensics report's analysis (A) and this pass's own reasoning: attention-type alternation did not predict the eff_dim_frac collapse pattern in the depth sweep (two other full-attention layers, hs6/hs24, were unremarkable); logit softcapping acts only on final-layer logits, after the mid-stream KU readout is scored, so it cannot affect the injection site's readback or the mid-stack readout gate; embedding scaling acts only at the input embedding layer. All three are **ruled out** as direct causes of the mid-stack behavioral null, on the same reasoning the prior forensics report already applied — this pass found nothing in the primary sources to change that.

6. **AltUp / LAuReL** — **N/A to the null**: both are **confirmed absent** from this checkpoint (§1c, §3) by direct tensor-name and class-name inventory, not merely undocumented. Any theory of the null resting on "Gemma uses AltUp/LAuReL to reroute injected deltas" would be **factually wrong for this specific model** — this is an important negative finding since Gemma 3n (the PLE/KV-sharing donor family) *does* use both. The lead should not import AltUp/LAuReL-based reasoning from Gemma 3n discussions elsewhere without checking this absence first.

7. **MatFormer / nested submodel structure** — **SPECULATION** in both directions. No tensor/config evidence of MatFormer nesting in this checkpoint, and the Gemma 4 report's searchable text did not repeat the MatFormer claim it makes elsewhere for other components. Not established either way from sources opened in this pass; do not assume it is present or absent for causal reasoning about the null.

**Top 3 most relevant to the null, ranked**: (1) `layer_scalar`/`skip_scale` uniform per-block residual decay — LOCAL-INFERENCE-ONLY, mechanism confirmed, causal role unconfirmed, no published documentation found; (2) the PLE third residual branch as a continuous delta-independent dilution source — LOCAL-INFERENCE-ONLY, newly identified in this pass, not previously in the forensics report; (3) sandwich normalization's branch-only (not residual-direct) scope — SUPPORTED-BY-SOURCE, confirms this is *not* a rescaling mechanism for the injected delta, ruling it out rather than implicating it.

---

## 5. NOT FOUND / could not verify

- **No published description of `layer_scalar`/`skip_scale` anywhere.** Searched the Gemma 4 report's full HTML text, full PDF text, the Gemma 4 HF model card, the Gemma 3n docs (ai.google.dev and HF), under every plausible name (skip scale, layer scale, residual scaling, block scale, output gate, per-block learned scalar). This may mean (a) it is genuinely undocumented/unpublished, (b) it is described in a part of the PDF that WebFetch's text extraction missed (tables, figures, appendix formatting can be lossy in PDF-to-text conversion — this is a real caveat, not just a disclaimer), or (c) it is described under a name not tried here. Treat "not documented" as the finding, not "does not exist" — the checkpoint proves it exists.
- **No dedicated Gemma 3n arXiv technical report was found.** Gemma 3n's documentation lives in blog posts (`developers.googleblog.com`) and product docs (`ai.google.dev`, HF `transformers` docs), not a citable arXiv paper of its own — confirmed by two separate targeted searches returning no arXiv ID for a "Gemma 3n Technical Report." Citations for Gemma 3n's individual mechanisms (PLE, AltUp, LAuReL, MatFormer) trace to their own originating papers (§2.5-2.8) plus Google's product documentation, not to a unified Gemma-3n paper.
- **MatFormer's presence or absence in Gemma 4 E4B specifically is not established.** The Gemma 4 report text I could search states PLE is inherited "as in Gemma 3n" but does not make the same explicit statement about MatFormer for Gemma 4, and no matformer-named tensors exist in the checkpoint — but absence of a name in a checkpoint doesn't rule out a training-time-only technique (MatFormer's whole point is that inference doesn't need special markers to run the full model). Genuinely unresolved from documentation opened in this pass.
- ~~**`attention_k_eq_v: false` vs. the report's "re-using keys as values in global attention layers" claim** — not reconciled.~~ **RESOLVED in §7** (2026-07-24 follow-up pass): a closer re-fetch of the same report section found the qualifier clause on the first pass missed — *"We improve memory efficiency by re-using keys as values in the global attention layers (except in E2B and E4B)"*. E4B is explicitly excluded from that specific technique by the report itself; `attention_k_eq_v: false` on this checkpoint is consistent with the report, not a discrepancy. Also directly confirmed in code: `modeling_gemma4.py:1138`, `self.use_alternative_attention = config.attention_k_eq_v and not self.is_sliding` — gated on the config flag, which is `False` here, so this code path is inert for E4B regardless.
- **Whether the `layer_scalar` values are also present, and structurally similar, in other Gemma-4 sizes (12B/31B) or in Gemma 3n itself** — not checked; out of scope (would require pulling other checkpoints, not done here).
- I did not attempt to open the Gemma 3 report (arXiv 2503.19786) in full; it is cited above only via search-snippet titles as a link target, not read directly, so no claim in this memo rests on its content specifically (the sandwich-norm and softcapping claims rest on the directly-fetched Gemma 2 report instead, which is the generation that report snippets attribute these features to).

## Files touched

Only the one output file was written:
`/home/profsynapse/code/ehr-worktrees/jspace-cross-family/experiments/j-space-cross-family-layer-contrast/analysis/gemma4-e4b/arch_literature_memo.md`

No repo files, pinned instruments, or `analysis-committed/` artifacts were modified. No GPU/CUDA/model-forward work was performed; all checkpoint reads were config/safetensors-key/small-buffer CPU reads consistent with the no-GPU constraint.


---

## 6. Lead verification pass (2026-07-24) — KV-cache sharing quarantines every mid-band injection site

Verified personally against the executing source and the pinned checkpoint config.
Provenance for every number below: `transformers==5.5.0`
`site-packages/transformers/models/gemma4/modeling_gemma4.py`, and
`~/.cache/huggingface/hub/models--google--gemma-4-E4B-it/snapshots/fee6332c.../config.json`.

### 6a. Confirmations of the researcher's memo (independently re-derived)

- `layer_scalar` multiplies the WHOLE residual at block end: `modeling_gemma4.py:1402`,
  `hidden_states *= self.layer_scalar`, registered at `:1331` as a buffer
  (`torch.ones(1)`), i.e. loaded from the checkpoint's `skip_scale`. CONFIRMED.
- PLE is a genuine THIRD residual branch: `modeling_gemma4.py:1393-1400`
  (`residual = hidden_states` -> gate -> act -> `* per_layer_input` -> projection
  -> norm -> `residual + hidden_states`), executing BEFORE the `layer_scalar`
  multiply. CONFIRMED as a structural claim.
- AltUp / LAuReL / MatFormer ABSENT from Gemma 4: grep count 0 across
  `modeling_gemma4.py`, `configuration_gemma4.py`, `convert_gemma4_weights.py`.
  POSITIVE CONTROL: the same grep over `models/gemma3n/modeling_gemma3n.py`
  returns 43 `altup` and 14 `laurel` matches, so the zero is a real absence and
  not a broken search. Config-level corroboration: `laurel_rank` and
  `altup_num_inputs` are absent from this checkpoint's `text_config`. CONFIRMED.
- `enable_moe_block: False` on this checkpoint. E4B is DENSE. It is therefore a
  different architecture from the "Gemma 4 26B A4B" MoE variant described in the
  library's existing `model:gemma-4` atom; the MoE path at `:1376-1388` is dead
  code for E4B.

### 6b. CORRECTION to the researcher's finding #2 (PLE dilution argument)

The memo describes the PLE branch as a "delta-independent additive rewrite" that
"continuously dilutes" an injected delta. That overstates it. The branch is
`per_layer_projection(post_norm(act(per_layer_input_gate(h)) * per_layer_input))`,
and `per_layer_input_gate` is a `nn.Linear` applied to `h` (`:1336`, `:1395`).
The branch output is therefore h-DEPENDENT, so an injected delta DOES propagate
through it. Only `per_layer_input` itself — the external per-layer embedding —
is delta-independent, and it enters as a multiplicative mask, not as an additive
overwrite. The defensible version of the claim: the delta is passed through a
GELU nonlinearity and then masked by a fixed per-layer vector, which can
attenuate or saturate it, and the branch adds a large h-dependent term that
lowers the delta's share of the residual. Downgrade from "dilution by
delta-independent rewrite" to "nonlinear gating + norm-share reduction."
Label: LOCAL-INFERENCE-ONLY.

### 6c. NEW — the mechanism the sweep missed: KV sharing over the top 18 layers

`config.num_kv_shared_layers = 18`, `num_hidden_layers = 42`. Per
`modeling_gemma4.py:1148-1156`:

    first_kv_shared_layer_idx = 42 - 18 = 24        # blocks 24..41 are KV-SHARED
    donor(full_attention)    = block 23             # last full block before 24
    donor(sliding_attention) = block 22             # last sliding block before 24

(`layer_types` puts full_attention at blocks [5, 11, 17, 23, 29, 35, 41]; all
other blocks are sliding_attention with window 512.)

At `:1198-1200`, a KV-shared layer does NOT compute K/V from its own residual
stream. It reads them out of `past_key_values.shared_layers[donor]`, i.e. the
keys and values frozen at block 22/23. The `k_proj`/`v_proj` branch at `:1203+`
is skipped entirely for those layers.

**Every injection site this experiment used is inside the shared region:**

| site | = output of block | >= 24 (KV-shared)? |
|------|-------------------|--------------------|
| hs34 | 33                | YES |
| hs38 | 37                | YES |
| hs40 (late ref) | 39     | YES |
| hs42 | 41                | YES |

**Consequence.** A boundary push written at hs34/38/40/42 lands in the residual
stream (hence the perfect readback and the clean KU gate fit, AUC 0.977-0.982),
and it still reaches the query path, the MLP, and the PLE branch of the
remaining blocks. But it CANNOT alter the keys or values that any subsequent
layer attends over, because those were computed at blocks 22-23, strictly
UPSTREAM of every injection site. The write is real, decodable, and structurally
barred from changing what the model can attend to. This holds in prefill as well
as in generation: `shared_layers` is populated by the donor blocks during the
same forward pass (`:1215-1220`), so it is upstream in wall-clock order too, not
merely in layer index.

This is the first candidate that explains the FULL null signature rather than
part of it:
- write lands + reads back perfectly, yet is behaviorally inert -> the delta is
  present but quarantined from the attention routing pathway;
- no window between inert and collapse -> with routing unavailable, the only
  remaining channel to the output is brute residual magnitude, which degrades
  rather than steers;
- collapse onset EARLIER at the terminal layer -> at hs42 the write goes nearly
  straight to the unembed with no intervening computation to absorb it;
- flat mid-stack eff_dim profile -> the top 18 blocks share a frozen K/V basis
  and have less independent representational movement to measure;
- llama / Qwen3-4B actuate -> neither family shares KV; every block there
  recomputes K/V from the local residual, so a mid-band write DOES change
  downstream attention.

Note the convergence with the prior forensics: the `layer_scalar` cumulative-
survival chokepoint was located at blocks 22-23, which is exactly the KV-donor
boundary. Two independent measurements landing on the same structural seam.

**Status: LOCAL-INFERENCE-ONLY, not established.** The architecture is verified
from source; the CAUSAL claim that KV quarantine produced this null is not. It
is a hypothesis with an unusually sharp and cheap falsifier.

### 6d. The falsifier this buys us

The hypothesis predicts that an injection BELOW block 24 — where the write still
feeds `k_proj`/`v_proj` for the donor blocks and therefore propagates into the
shared K/V that all 18 top blocks consume — should actuate where hs34/38/42 do
not. The band-selection rule chose the mid-band from the eff_dim_frac peak
(hs38), which placed every candidate site above the boundary, so this experiment
NEVER PROBED below the KV-sharing seam. The gemma null is therefore a null about
the region above block 24, not about the model.

This does NOT reopen the current amendment: gemma's G0 dose-viability NOT-RUN
stands as adjudicated, and the roll-up is unchanged. Testing sub-boundary
injection requires a NEW registered experiment with its own pre-stated
prediction, falsifier, and gates. Recorded here as a lead-verified design input
for that registration, not as a result.

---

## 7. Follow-up (2026-07-24): cross-family KV-sharing contrast, citable source, adversarial re-check

CPU + web only, no GPU touched (the 3090 was mid-`run_contrast.py` throughout this pass;
nothing here loaded weights or ran a forward pass). No commits, no edits outside this
file. KG-search-first used for every repo lookup below.

### 7.1 Cross-family cross-layer-KV-sharing check, other program families

Pins verified against the fleet matrix (`experiments/doubt-snap-cross-family-confirmatory/model_matrix.yaml`)
and `experiments/qwen35-4b-midband-doubt-snap/analysis-committed/build_manifest.json`, then
cross-checked against the actual HF cache snapshot directory name for each (the snapshot hash
*is* the resolved revision) — all four matched their pin exactly:

| family | repo | pinned revision | matches cache snapshot dir? |
|---|---|---|---|
| llama | `unsloth/Llama-3.2-3B-Instruct` | `006f5dcd1393c3add266de40994ba96225e9689d` | YES |
| mistral | `mistralai/Mistral-7B-Instruct-v0.3` | `c170c708c41dac9275d15a8fff4eca08d52bab71` | YES |
| qwen3 (base, used by the `j-space-*-qwen3-4b` line) | `unsloth/Qwen3-4B` | no explicit pin doc found; only cached snapshot `64033659d5caf1b8ed7f929b29de705e93a4d468` exists (single snapshot, so this is what every `surface.model: unsloth/Qwen3-4B` cell.yaml actually resolves to) — reporting what is in cache per instructions, not asserting a pin record I could not find | N/A, no separate pin doc to check against |
| qwen3.5 | `Qwen/Qwen3.5-4B` | `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a` | YES |

For each, read `config.json` directly (full dumps in this session's transcript) and grepped
the installed `transformers==5.5.0` modeling source for the exact terms the lead specified
(`shared_layers`, `kv_shared`, `share_kv`, `cross_layer`/`CrossLayer`, `YOCO`, `donor`,
`past_key_values.shared`) plus, for Qwen3.5, its own hybrid-attention vocabulary:

| family | model_type / arch class | cross-layer KV-sharing config field? | code-level cross-layer KV path found? | verdict |
|---|---|---|---|---|
| llama-3.2-3b | `LlamaForCausalLM` (`llama`) | none — no `num_kv_shared_layers` or any sharing-shaped field in `config.json`; uniform full attention (28 layers, GQA `num_key_value_heads=8`), no `layer_types` | `modeling_llama.py`: 0 hits on every searched term | **No cross-layer KV sharing.** Verified by config absence AND code absence, not by config absence alone. |
| mistral-7b-v0.3 | `MistralForCausalLM` (`mistral`) | none — no sharing field, `sliding_window: null` (i.e. disabled on this checkpoint), uniform 32-layer GQA (`num_key_value_heads=8`) | `modeling_mistral.py`: 0 hits on every searched term | **No cross-layer KV sharing.** Same double-verification. |
| qwen3-4b (unsloth) | `Qwen3ForCausalLM` (`qwen3`) | none — no sharing field; `layer_types` *attribute* exists in the code path (`modeling_qwen3.py:227,370,426`) but governs sliding-vs-full attention masking only (this checkpoint has `sliding_window: null`, `use_sliding_window: false`, and no `layer_types` key in its own `config.json`, so it's plain uniform full attention with GQA `num_key_value_heads=8`) — this is the SAME kind of field as Gemma's `layer_types`, but it is about attention *pattern*, not KV *donation across layers*; confirmed by reading the three call sites, none of which reference a cache-sharing structure | `modeling_qwen3.py`: 0 hits on `shared_layers`/`kv_shared`/`share_kv`/`cross_layer`/`CrossLayer`/`YOCO`/`past_key_values.shared`/`donor` | **No cross-layer KV sharing.** The `layer_types` hits are a false-lead the lead specifically warned to check for by name — checked, and it resolves to attention-pattern selection, not KV donation. |
| qwen3.5-4b | `Qwen3_5ForConditionalGeneration` (`qwen3_5`) | none — no `num_kv_shared_layers` or sharing field anywhere in `text_config` | `modeling_qwen3_5.py`: 0 hits on every cross-layer-sharing term, but non-zero on a DIFFERENT mechanism class: `linear_attention` (5), `recurrent_state` (23), `conv_state` (11) | **No cross-layer KV sharing, but architecturally not a fair "neither shares" comparison** — see 7.1a below. |

**7.1a — Qwen3.5-4B is not a Qwen3 variant; it needs its own read before it ever returns to the program.**
`config.json`'s `text_config.layer_types` alternates `linear_attention` x3 then `full_attention`
x1, every 4 blocks (`full_attention_interval: 4`), 32 layers total, so only 8 of 32 layers run
standard softmax attention with a KV cache at all. The other 24 run a gated-linear-attention /
SSM-style layer (`linear_conv_kernel_dim`, `linear_key_head_dim`, `linear_num_key_heads`,
`linear_num_value_heads`, `linear_value_head_dim` in config; `recurrent_state`/`conv_state` in
code) that carries a fixed-size recurrent state forward instead of an ever-growing token-indexed
KV cache. This is a genuinely different memory-reduction strategy from Gemma 4's cross-layer KV
donation — it is closer in spirit to Mamba/RWKV-style linear attention than to CLA/YOCO — and it
means a mid-band residual injection's fate on Qwen3.5-4B (does a recurrent-state layer "remember"
an injected delta the way a KV-cache layer would, or does it get absorbed into a compressed
state and decay/dilute on its own separate schedule?) is an open architectural question this pass
did not attempt to resolve. Flagging this now, before the family returns to program focus, per
the lead's ask: **do not assume Qwen3.5-4B's attention-layer analysis generalizes to its
linear-attention layers, and do not assume its linear-attention layers behave like Gemma 4's
KV-shared layers** — they are different mechanisms found by this same search, not the same one.

**Bottom line on the cross-family claim**: "neither llama-3.2-3b, mistral-7b-v0.3, nor
qwen3-4b shares KV cache across layers" is verified as a fact — config-field absence AND
independent code search for alternate implementations under every name the lead specified,
for all three. Qwen3.5-4b also has no cross-layer KV-sharing field or code path, but it has a
different, unverified-for-injection-robustness memory mechanism (linear/recurrent attention)
on 3/4 of its layers, so "neither family shares KV" is true for the sharing mechanism
specifically but should not be read as "all four families propagate a mid-band write through
attention identically" — Qwen3.5-4B did not get that follow-on check in this pass.

### 7.2 Citable source for cross-layer KV sharing, distinguished from `attention_k_eq_v`

Re-fetched `https://arxiv.org/html/2607.02770v1` with a targeted prompt asking specifically
for the "share the KV cache" sentence plus its surrounding paragraph and any citation marker,
and for a bibliography search on Cross-Layer Attention / YOCO / Brandon / Sun-2024. Result:

- The report's own sentence, in full and correctly scoped this time: *"We improve memory
  efficiency by re-using keys as values in the global attention layers (except in E2B and
  E4B)"* — this is `attention_k_eq_v`, a WITHIN-layer technique (a layer uses its own keys in
  place of a separate value projection), explicitly OFF for E4B. Separately: *"Finally, we
  share the KV cache with ratios of 20/35 and 18/42 for the E2B and E4B model"* — this is
  `num_kv_shared_layers`, the ACROSS-layer donation mechanism this memo's §6/§7 concern. Both
  sentences sit in the same "Long-context efficiency" subsection of Section 2 but are
  textually and mechanically distinct techniques; conflating them was the source of the now-
  resolved §5 discrepancy note above.
- **No citation marker is attached to either sentence**, and the bibliography search for
  "Cross-Layer Attention," "You Only Cache Once," "YOCO," "Brandon," or a 2024 cache-focused
  paper by "Sun" returned **no match**. The only KV-cache-adjacent citation found in the
  report's references is Shazeer (2019), the original Multi-Query Attention paper ("Fast
  Transformer Decoding: One Write-Head is All You Need") — GQA/MQA lineage, not cross-layer
  sharing. **The Gemma 4 report does not cite a primary source for `num_kv_shared_layers`
  specifically; the mechanism is presented as an internal design choice, not attributed.**
- Independently confirmed (not from the Gemma 4 report) the two candidate primary papers for
  the general technique class of "attention layers reuse another layer's K/V instead of
  computing their own":
  - **"You Only Cache Once: Decoder-Decoder Architectures for Language Models"** — Sun, Dong,
    et al. (Microsoft Research, Tsinghua University). arXiv **2405.05254** (NeurIPS 2024).
    Confirmed via search of `arxiv.org/abs/2405.05254`. Mechanism: a self-decoder computes
    global KV caches once; a cross-decoder stacked on top reuses them via cross-attention,
    rather than every layer computing its own.
  - **"Reducing Transformer Key-Value Cache Size with Cross-Layer Attention"** — Brandon,
    Mishra, Nrusimha, Panda, Kelly (2024). arXiv **2405.12981** (NeurIPS 2024). Confirmed via
    search of `arxiv.org/abs/2405.12981`. Mechanism: adjacent layers share key and value heads,
    extending GQA/MQA's within-layer head-sharing to an across-layer axis — this is the closer
    mechanistic match to Gemma 4's `num_kv_shared_layers` (a block of top layers reusing a
    single donor's K/V), though neither paper is confirmed as what Gemma Team actually built
    on, since the report cites neither.
  - **Labeling for §4/§6's SUPPORTED-BY-SOURCE convention**: the *existence and site* of
    `num_kv_shared_layers` remains SUPPORTED-BY-SOURCE (Gemma 4 report + Gemma3n config docs,
    both directly fetched, §2.4 and this section). Attribution of the mechanism to CLA/YOCO
    specifically is **LOCAL-INFERENCE-ONLY** (best structural match found by this pass, not a
    confirmed lineage) — do not cite CLA/YOCO as "the paper Gemma 4 used" in any future write-up
    without a source that actually says so.

### 7.3 Adversarial re-check: can a block-33 residual edit ever reach the K/V blocks 24-41 consume?

Read `Gemma4TextAttention.__init__` and `.forward` in full
(`modeling_gemma4.py:1126-1240`), not just the `__init__` slice cited in §6c, specifically to
chase the lead's three named risks (prefill vs. decode, `store_full_length_kv`, whether
`shared_layers` is ever refreshed post-donor).

- **`store_full_length_kv` is a one-way write flag, held by exactly two layers.** It is only
  ever set `True` in the `else` branch of the `is_kv_shared_layer` conditional at `__init__`
  time (`:1155-1160`) — i.e., only for a NON-shared layer that happens to be the last layer of
  its attention type before the sharing region starts. For this checkpoint that resolves to
  block 23 (full) and block 22 (sliding) exactly, matching §6c. A KV-shared layer (block ≥ 24)
  can never have `store_full_length_kv = True` — the flag is defined in the opposite branch of
  the same `if`. **There is no code path by which a KV-shared layer ever writes back into
  `shared_layers`.** The flow is strictly one-way, donor → consumers, with no cycle.
- **`shared_layers` is written fresh every forward call, at the donor layer, before any
  consumer layer executes — this holds for both prefill and decode, and there is no "refresh"
  event, only "compute-then-read" every single time.** At `forward()` (`:1198-1220`): a
  KV-shared layer's `if self.is_kv_shared_layer and past_key_values is not None:` branch
  (`:1198-1202`) reads `past_key_values.shared_layers[self.kv_shared_layer_index]` and NEVER
  calls `self.k_proj`/`self.v_proj` — those two `nn.Linear` layers are architecturally
  unreachable for a KV-shared layer whenever a `Cache` object is present. The donor layer
  (block 22 or 23), by construction NOT a KV-shared layer, always takes the `else` branch
  (`:1203-1212`), computing fresh K/V from ITS OWN current hidden state, appending to its own
  growing per-layer cache via `past_key_values.update(...)` (`:1216`), and — because
  `store_full_length_kv` is True only for it — copying that just-updated, full-length K/V into
  `shared_layers[self.layer_idx]` (`:1217-1220`). Because Gemma4's decoder layers execute in
  fixed index order 0→41 within every single `forward()` call (both the one-shot prefill call
  over the whole prompt and each one-token decode call during autoregressive generation), block
  22/23 ALWAYS execute — and therefore ALWAYS finish writing `shared_layers` — strictly before
  block 24+ executes, for every token, every step, with no exception in the code. A residual
  edit applied by a forward hook at block 33 (hs34) or later cannot retroactively change a
  tensor that was already computed and stored several blocks earlier in the same pass.
- **This confirms §6c's claim holds, with one clarification worth stating precisely rather
  than leaving implicit**: KV-sharing structurally prevents an injected delta at block ≥ 24
  from changing the KEYS/VALUES that ANY layer (shared or not) will attend over — but it does
  **not** block the delta from reaching the output by other means. Every KV-shared layer still
  computes its own **query** fresh from its own (delta-carrying) hidden state (`:1192-1195`,
  unconditional, no `is_kv_shared_layer` guard) — so the delta can still change *what the model
  attends to* even though it can no longer change *what's available to attend to*. The delta
  also still flows in full through the residual stream itself, every downstream MLP branch, and
  every downstream PLE branch (§6b already made this same point about PLE; it generalizes to
  the whole non-KV computation graph). §6c's own writeup already states this correctly
  ("it still reaches the query path, the MLP, and the PLE branch") — this pass independently
  re-derived the same conclusion from a full, not partial, read of the attention module, so
  treat it as confirmed twice over, not merely asserted. **KV-sharing is a real, source-verified
  structural constraint that removes one specific channel (delta → shared memory bank), not a
  complete quarantine of the delta from the forward pass.** Framing it as "the mechanism that
  explains the FULL null signature" (§6c's phrase) is defensible as the strongest single
  candidate found so far, but "quarantined" should be read narrowly (quarantined from the K/V
  write path) rather than broadly (quarantined from influencing the output at all) in any
  future write-up.
- **Checked whether the actual calibration/dose-ladder harness that produced the null even uses
  a `Cache` object** (if it didn't, KV-sharing would never engage, and this whole mechanism
  would be moot for the runs that actually happened) — this was the risk most worth ruling out
  before trusting the theory. Read `gen_lib.py:run_pass_fixed` in the
  `j-space-cross-family-layer-contrast` worktree (the file the forensics report and §6 both
  cite): it calls plain `model.generate(**enc, max_new_tokens=..., min_new_tokens=1,
  do_sample=False, ...)` with no `use_cache` override anywhere in the call or in the file. HF's
  `generate()` defaults to `use_cache=True`, and the checkpoint's own `config.json` sets
  `"use_cache": true` (§1a) — so `generate()` constructs a real `Cache` instance internally,
  `past_key_values` is never `None` during these runs, and the `shared_layers` mechanism was
  live for every dosed pass in the actual harness that produced the write-verified-null result.
  The docstring also confirms the write scope is `"gen_stream" (anchor_onward: edit every decode
  step)"` — the hook re-applies the injection at every decode step, not just once at prefill;
  since block 22/23 execute before block 33+ in EVERY forward call including every single decode
  step, the "donor writes first" ordering holds uniformly across the whole generation, not just
  at the start.
- **No counter-example found.** I looked specifically for: a code path that recomputes
  `shared_layers` mid-pass after a shared layer runs (none — the dict is written once per
  forward call, at the donor, per §two bullets above); a `past_key_values is None` fallback that
  would let KV-shared layers fall through to computing their own K/V and thus become reachable
  by the delta (this fallback exists at `:1198`, `if self.is_kv_shared_layer and
  past_key_values is not None`, but it is dead for the actual harness since `generate()` always
  supplies a Cache per the point above — flagging it as a theoretical, not actual, escape hatch,
  in case a future GPU-side reproduction is built with `use_cache=False` or raw `forward()`
  calls without a Cache, which WOULD disable the quarantine entirely); and any mechanism by
  which a later block's own forward pass writes back into an earlier block's stored K/V (none —
  the write direction in the code is structurally one-way, donor-index-keyed, set once per
  call). **The lead's read stands: verified, not merely re-asserted.**

### 7.4 Updated top-line for future registration design

Combining §6 and §7: the KV-sharing quarantine hypothesis is the first candidate in this whole
investigation (forensics report + this memo, both passes) that accounts for the *complete*
null signature rather than a partial one, it is verified against the executing source down to
the write/read ordering and the actual harness's cache usage, and it produces a specific, cheap,
falsifiable prediction (§6d: a sub-block-24 mid-band site should behave differently from
hs34/38/40/42, because it would feed the donor computation rather than sit downstream of it).
The companion cross-family fact (§7.1) that llama/mistral/qwen3-4b have no analogous mechanism
gives that falsifier a natural cross-family control for free, if a future registered experiment
wants one: those three families should show no comparable "shared-region vs. below-the-seam"
asymmetry, because they have nothing structurally equivalent to the seam to probe. Qwen3.5-4b
(§7.1a) is architecturally too different (linear-attention majority) to serve as a clean control
for this specific hypothesis without its own dedicated read first.

Status: design input only, per the lead's framing. Nothing here reopens gemma4-e4b's adjudicated
G0 NOT-RUN disposition.

## 8. `use_cache=False` as a sharing-OFF toggle: mechanism, confounds, and a working alternative

CPU/source-reading only, no model load, per the lead's constraint (mistral calibration was on
the 3090 at the time). All claims below are traced to `transformers==5.5.0` source at the paths
given; every line number was read, not recalled.

### 8.1 Confirming the mechanism — SUPPORTED-BY-SOURCE

Traced end to end from `generate()` down to the shared-layer read at `:1198`.

**Model side** (`modeling_gemma4.py`, `Gemma4TextModel.forward`, read in full):
```python
use_cache = use_cache if use_cache is not None else self.config.use_cache
...
if use_cache and past_key_values is None:
    past_key_values = DynamicCache(config=self.config)
```
If `use_cache=False`, this `if` is never entered, `past_key_values` stays whatever was passed in
(`None` by default), and that `None` is threaded unchanged through every
`decoder_layer(..., past_key_values=past_key_values, ...)` call to every one of the 42
`Gemma4TextAttention.forward` calls. At `:1198`:
```python
if self.is_kv_shared_layer and past_key_values is not None:
    key_states, value_states = past_key_values.shared_layers[self.kv_shared_layer_index]
else:
    key_states = self.k_proj(hidden_states).view(hidden_shape)
    ...
```
with `past_key_values is None`, the condition is `False` for **every** layer, shared or not —
all 42 layers, including the 18 in the shared region (blocks 24-41), fall into the `else` branch
and compute their own local `k_proj`/`v_proj`. So `use_cache=False` does disable the shared-KV
read path, confirmed at the line that actually executes it.

**Generation-loop side** (`generation/utils.py`, read the `use_cache` handling end to end, not
just grepped): three places matter.
- `_prepare_cache_for_generation` (`:1817-1834`): "Quick escape route 2" —
  `if generation_config.use_cache is False: return` — the function returns **without**
  constructing any `Cache` object when the caller passes `use_cache=False`. No cache is built
  upstream of `forward()` either.
- `:2538-2539`: `model_kwargs["use_cache"] = generation_config.use_cache` — this is the value
  actually forwarded into every per-step `forward()` call.
- The one place `generate()` silently overrides `use_cache` back to `True` is `:2426-2427`:
  `if not self.config.is_encoder_decoder and model_input_name == "inputs_embeds":
  generation_config.use_cache = True` — this fires only when generation is driven by
  `inputs_embeds` instead of `input_ids`. `gen_lib.py:run_pass_fixed` calls
  `model.generate(**enc, ...)` where `enc` is a tokenizer output (`input_ids`/`attention_mask`),
  so `model_input_name == "input_ids"`, not `"inputs_embeds"` — this override does **not** fire
  for this harness's call shape. I checked every other `use_cache` occurrence in
  `generation/utils.py` (`:1064`, `:2744`, `:3234`, `:3482`) and none override it back to `True`
  for a plain greedy-decode (`do_sample=False, num_beams=1`) call; `:3482` only fires for
  assisted decoding, which this harness does not use.

**Verdict: `use_cache=False` is a real, native toggle in this transformers version and this
harness's call shape.** It is not silently defeated by anything upstream.

### 8.2 Confounds — what ELSE changes (this is the part that matters)

**Global, not local — the big one.** `use_cache=False` disables caching for **all 42 layers**,
not just the 18 shared ones. The 24 non-shared layers switch from "read cached K/V, compute and
append only the new token's K/V" to "recompute K/V for the entire growing prefix from scratch at
every decode step" (same `else` branch at `:1203-1212`, just executed by layers that would
otherwise have taken the cached-append path at `:1214-1216`). Mathematically the recomputed K/V
values should be numerically close to the cached ones, but the code path is not the same:
- **Numerical drift risk (LOCAL-INFERENCE-ONLY — plausible, not source-confirmed).** Full-prefix
  batched recompute at every step vs. one-new-token-plus-`torch.cat` are different matmul shapes
  and reduction orders; bf16/fp32 accumulation is not bitwise-associative, so the two are not
  guaranteed bit-identical. This experiment's own effect sizes are gate-AUC-scale
  (0.977-0.982, per the earlier forensics report) — layering an unquantified numerical-path
  confound under a subtle dosed/clean contrast is a real interpretability risk, not just a
  theoretical nicety.
- **Quadratic recompute cost (source-grounded asymptotic argument, wall-clock NOT FOUND).**
  `gen_lib.py:10,40` cap generation at `MAX_NEW_CAP=200` tokens. With caching, per-step linear-layer
  cost is O(1) in prefix length; without it, every one of up to 200 decode steps reruns the full
  42-layer forward over the entire growing prefix, so linear-layer FLOPs scale like
  O(T x S_avg) instead of O(T) — a slowdown factor on the order of the average sequence length
  across the run. I do not have this experiment's exact prompt-token-length distribution
  memorized or re-verified in this pass, so I am not giving a specific multiplier — that would be
  fabrication. What I can say from source: `run_contrast.py:298-315` (`run_full`) runs the
  **entire held-out pool** per family per layer arm (a sibling run's own
  `analysis-committed/full_summary.json` for qwen3-4b recorded `n_rows: 443` for one full-mode
  run), and `AMENDMENT.md` design tests multiple mid-band candidates plus a late-reference arm
  per family — so a `use_cache=False` full-mode run multiplies an already-hundreds-of-generations
  workload by an unquantified but architecturally real per-generation cost blowup. Flag as
  **likely impractical at full-pool scale** without either a much smaller row budget or a much
  lower `max_new_tokens` cap carved out specifically for this falsifier.
- **Sliding-window/mask construction (LOCAL-INFERENCE-ONLY, not exhaustively chased).** The
  causal/sliding masks are rebuilt fresh from `attention_mask`+`position_ids`+`past_key_values`
  every forward call regardless of cache use (`Gemma4TextModel.forward`, mask_kwargs block), and
  `create_sliding_window_causal_mask` already has to handle the no-cache case for prefill, so I
  read no reason to expect this to diverge — but I did not open `masking_utils.py` to verify this
  claim to the same depth as §8.1, so it stays a weaker label.
- **Determinism between conditions, not within one.** Greedy decode (`do_sample=False`) is
  deterministic run-to-run under either toggle. The confound is that a `use_cache=False` run is
  not "the same computation minus 18 layers' shared reads" relative to the existing cached-run
  data — it is a materially different computational graph across all 42 layers, which matters if
  any comparison leans on the existing cached null-result runs as a baseline.

### 8.3 The targeted-patch alternative — traced, and it is BROKEN as naively stated

The lead's proposal: force `is_kv_shared_layer = False` on the 18 shared attention modules'
instances, leave `use_cache=True` everywhere else. Read `Cache.update()` and `DynamicCache.__init__`
in full (`cache_utils.py`) to check whether this works. **It does not, without a companion fix.**

`Gemma4TextModel.forward` builds its cache as `DynamicCache(config=self.config)`. Read
`DynamicCache.__init__` (`cache_utils.py`) in full — it is explicitly shared-KV-aware:
```python
layer_types = getattr(decoder_config, "layer_types", None)
...
# Some models have shared layers thus no cache is needed for them (e.g. Gemma3n)
if hasattr(decoder_config, "num_kv_shared_layers"):
    layer_types = layer_types[: -decoder_config.num_kv_shared_layers]
for layer_type in layer_types:
    ...  # builds one CacheLayer per remaining entry
```
For gemma4-e4b (`num_hidden_layers=42`, `num_kv_shared_layers=18`), this slices `layer_types`
down to 24 entries and builds `self.layers` with **exactly 24 `CacheLayer` objects** (indices
0-23). It then calls `super().__init__(layers=layers, ...)` — since `layers` is non-empty,
`Cache.__init__` sets `self.layer_class_to_replicate = None` (the `layers=`/
`layer_class_to_replicate=` constructor args are mutually exclusive; only one path runs).

Read `Cache.update()` (the dispatcher actually invoked at `modeling_gemma4.py:1216`,
`past_key_values.update(key_states, value_states, self.layer_idx)`):
```python
def update(self, key_states, value_states, layer_idx, *args, **kwargs):
    if self.layer_class_to_replicate is not None:
        while len(self.layers) <= layer_idx:
            self.layers.append(self.layer_class_to_replicate())
    ...
    keys, values = self.layers[layer_idx].update(key_states, value_states, *args, **kwargs)
```
The lazy-growth branch only runs when `layer_class_to_replicate is not None` — which, per the
paragraph above, is **not** the case for a config-constructed `DynamicCache`. So if a patched
shared layer (`layer_idx` in 24-41) takes the `else` branch and reaches `:1216`, `self.layers[24]`
on a 24-element list (`self.layers` = indices 0-23) is an **out-of-range index — `IndexError`**.
This is not a hedge; I traced both the allocation site and the exact dispatcher method that would
be hit. The naive patch crashes on the first shared-layer forward call with caching left on.

Root cause, stated plainly: `shared_layers` (the donor-written dict at `:1218-1220`) is bolted
onto the `DynamicCache` instance dynamically (`if not hasattr(past_key_values, "shared_layers"):
past_key_values.shared_layers = {}`) and is entirely separate from `self.layers` (the list
`Cache.update()` indexes). The 24-entry truncation exists **specifically because** stock code
never calls `.update()` for a shared layer — the cache object was built assuming that invariant,
and flipping `is_kv_shared_layer` on the attention module alone breaks the assumption without
telling the cache about it.

**Working fix (two options, recommending the first):**
1. **Construct the cache explicitly and pass it in.** `Gemma4TextModel.forward` only builds its
   own truncated cache `if use_cache and past_key_values is None` — so passing a pre-built,
   full-length `past_key_values=` into `generate()` bypasses that construction entirely. Build a
   `DynamicCache` by hand with 42 `layers` entries — `DynamicSlidingWindowLayer(sliding_window=512)`
   for every index where `config.layer_types[i] == "sliding_attention"`, `DynamicLayer()`
   otherwise — mirroring `DynamicCache.__init__`'s own per-type logic but without the
   `num_kv_shared_layers` slice. Combined with flipping `is_kv_shared_layer = False` on the 18
   modules (a plain instance attribute set post-construction, per `:1149` — not a buffer or
   parameter, safe to reassign), every layer now takes the ordinary cached-append path with a
   real, correctly-typed `CacheLayer` behind it.
2. Monkeypatch `DynamicCache.__init__`'s slicing to skip when a flag is set — works but is more
   invasive (touches shared library code globally rather than one call site) and I'd weight it
   below option 1.

**Required preflight, given the crash risk just found (this is now necessary, not just the
lead's original ask):** (a) hook `k_proj`/`v_proj` (or wrap `.forward`) on the 18 patched
attention modules and assert a nonzero call count per generation call — proves local KV is
actually being computed, not silently skipped; (b) assert `len(past_key_values.layers) == 42`
immediately after cache construction and that each of the 18 formerly-shared indices'
`CacheLayer.get_seq_length()`-style length grows across decode steps — proves the fix path is
live and caching, not just not-crashing.

### 8.4 Feasibility comparison

- **`use_cache=False`:** cost scales with the O(S_avg) per-decode-step blowup argued in §8.2,
  on top of a full-mode run's existing hundreds-of-rows x multi-layer-arm scope. Order of
  magnitude only (no wall-clock benchmark, no GPU access): this reads as **likely impractical**
  at the held-out pool's current scale on a single 3090 without either a much smaller row budget
  carved out specifically for this falsifier or a sharply reduced `max_new_tokens`.
- **Targeted patch (fixed per §8.3):** once the cache is constructed at full length, cost stays
  close to baseline — every layer keeps O(1)-per-step incremental caching; the only change is 18
  layers now run their own small `k_proj`/`v_proj` matmuls instead of a dict lookup, a
  single-digit-percent overhead at most. This is feasible at the pool's existing scale.

### 8.5 Recommendation

**Neither toggle is clean out of the box** — `use_cache=False` is architecturally dirty (changes
the code path for all 42 layers, not just the 18 in question, plus an unquantified numerical-path
risk); the targeted patch as the lead described it is not merely dirty but **broken**
(`IndexError`, traced to `DynamicCache`'s config-driven truncation). Once fixed per §8.3 option 1
(explicit full-length `DynamicCache` passed into `generate()`, plus the `is_kv_shared_layer` flip
plus the two preflight asserts), the **targeted patch is the only one of the two that isolates
the single intended variable** (shared vs. local KV, nothing else) while staying feasible at the
held-out pool's existing scale. Recommend the amendment specify the fixed targeted patch, not
`use_cache=False`, and pre-register the two preflight asserts as a hard gate before trusting any
contrast built on it — a silent fallback or crash-avoidance path here would be exactly the kind
of thing that makes a result unreviewable.

Status: design input only, per the lead's framing.

## 9. CPU-only tiny-model preflight: the §8 argument, tested not just traced

Script: `experiments/gemma4-e4b-kv-seam-quarantine/kv_seam_preflight.py` (repo root
`/home/profsynapse/code/Epistemic-Humility-Research`), runnable standalone (`python3
kv_seam_preflight.py`), CPU-only, no checkpoint download, no GPU. All four checks below
**PASS** (exit code 0, output byte-identical across two consecutive runs). Full transcript is
in the script's own printed summary; only the load-bearing numbers are repeated here.

**Setup.** A `Gemma4TextConfig`/`Gemma4ForCausalLM` built directly (no `from_pretrained`) with
width fields shrunk to near-nothing (`hidden_size=64`, 4 heads, vocab 256) but the geometry
fields held EXACT to the pinned checkpoint: `num_hidden_layers=42`, `num_kv_shared_layers=18`,
`sliding_window=512`, `layer_types` left unset so `Gemma4TextConfig.__post_init__`'s own
`sliding_window_pattern=6` derivation produces it — verified, not assumed, via
`kv_seam_patch.verify_architecture(model)`, which passed: donors
`{"sliding_attention": 22, "full_attention": 23}`, shared blocks `24..41`, matching the real
checkpoint exactly.

1. **Geometry + crash reproduces — PASS.** Stock `model(..., use_cache=True)` auto-builds a
   cache with `len(cache.layers) == 24` (`= 42 - 18`), confirming the tiny config reproduces the
   truncation §8.3 depends on. Then `kv_seam_patch.kv_sharing(model, enabled=False)` — the patch
   **exactly as currently drafted** in `kv_seam_patch.py`, no cache fix — under a plain
   `generate()` call raised `IndexError: list index out of range`. §8.3 was right; this is not a
   hedge, it reproduces on a live model.
2. **Fix completes — PASS.** A hand-built 42-entry `Cache` (one `DynamicSlidingWindowLayer`/
   `DynamicLayer` per `config.layer_types`, no slicing — `Cache(layers=[...])`, **not**
   `DynamicCache(layers=...)`; `DynamicCache.__init__` does not accept a `layers=` kwarg itself,
   it only builds one internally from `config`) passed via `generate(past_key_values=...)`
   completes a 5-token greedy generation with no exception.
3. **Mechanism actually flipped — PASS.** Hooked `k_proj` on the 18 shared modules: stock
   (sharing ON) fired **0** times across all 18 over the whole generation; patched (sharing OFF,
   with the fix) fired **5** times on **every one** of the 18 (one per decode step: 1 prefill +
   4 further steps for `max_new_tokens=5`). Zero vs. nonzero-on-every-block is the actual
   evidence, not the flag. All 42 cache layers' sequence length grew to a uniform 10 after
   generation (6-token prompt + 4 of 5 new tokens actually needing their KV cached — the last
   generated token's KV is never attended over) — confirms the fix caches real, freshly-computed
   KV for the previously-shared layers, not a silent no-op.
4. **Equivalence control — PASS.** Fully-stock `generate()` (model's own auto-cache, patch
   module untouched) vs. `kv_sharing(model, enabled=True)` (no-op flip) plus the hand-built
   full-length cache from check 2: **token-sequence identical AND logits bit-identical**
   (`torch.equal` on both, not an approximate comparison). Swapping in the full-length cache —
   which the OFF arm needs — is inert when sharing stays ON. This is the load-bearing guarantee
   for the real experiment: any future A1 (sharing ON)-vs-A2 (sharing OFF) difference on the real
   checkpoint will come from the KV variable, not from the act of patching or from using a
   differently-sized cache object between arms.

**One gap this surfaced, reported straight, not fixed here** (out of scope — the lead's
instruction was to touch only `kv_seam_preflight.py` in this pass): `kv_seam_patch.py` as it
currently stands has no `build_full_length_cache`-equivalent helper. `kv_sharing()` only flips
the three per-module attributes; nothing in that file builds or hands `generate()` the
42-entry `Cache` the fix needs. Anyone calling `kv_sharing(model, enabled=False)` today, exactly
as drafted, will hit the check-1 `IndexError` on the real checkpoint too — the fix is proven to
work (checks 2-4), but it is not yet wired into the instrument the drafter is revising. Flagging
for the lead/drafter rather than patching `kv_seam_patch.py` myself, per this task's file
boundary.

Status: design input only, per the lead's framing.
