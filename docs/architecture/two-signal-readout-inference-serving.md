# Two-Signal Trust Readout: Inference & Serving Architecture

Status: design note (2026-06-30). Engineering/design companion to the research
plan in `papers/series/plan.md` and the mechanism synthesis in
`papers/paper-4-two-signal-readout/notes/framework.md`. This describes how the
validated readout mechanism would be wired into a live inference path. It marks
clearly what is **validated offline** vs **proposed for deployment** (not yet
built or load-tested in a serving stack).

## 1. Purpose and scope

The research result is: a small instruction-tuned LM already carries a deployable
trust signal that can be read off its residual stream with a tiny linear probe, no
task training required. This doc answers the engineering question: *how do we put
that on an inference path so it informs the response a user sees?*

Scope: the serving-time mechanics (where the signal is read, how it is turned into
a number, how it changes the response). Out of scope: the probe-fitting research
pipeline (that lives under `archive/experiment/phase1/probe/`) and the training studies
(Papers 1-2).

Core stance: **the base model is never modified at inference.** The mechanism reads
activations the model already computes and acts on them in the orchestration layer.
The signal is for *reading*, not for *steering* the generation (see 6.5 for why
this is a deliberate constraint, not an oversight).

## 2. What the probe physically is

Each of the two signals is a single linear readout over one layer's residual-stream
activation:

```
score = sigmoid( w . normalize(h_L) + b )
```

- `h_L`  = residual-stream activation at layer L (~L20 for Qwen3-4B), at one token
           position. Length = hidden_dim (~2048 @ 4B, ~4096 @ 8-14B).
- `normalize` = the fitted StandardScaler (per-feature mean/std from training).
- `w`, `b`  = LogisticRegression coefficient vector + intercept.

That is the entire object: a few kilobytes of floats. No attention, no extra
transformer blocks, no change to base weights. Applying it is one dot product.

Two probes are fit and shipped:

| signal | reads at | layer (4B) | what it scores |
|--------|----------|-----------|----------------|
| **gate** | last prompt token (pre-generation anchor) | ~L20 | answerability (is this answerable / does the model know) |
| **dial** | last answer content token (post-generation) | ~L20-22 | per-answer correctness; low = confident confabulation (the veto) |

The two are kept **separate** (a two-stage pipeline), not fused into one score:
fusing the scalars measurably hurt correctness ranking offline (delta -0.014). They
are orthogonal axes and are consumed at different points in the request lifecycle.

## 3. The two tap points already exist in a normal forward

The key efficiency fact: both activations are computed during ordinary inference;
we only *capture* them. Nothing is recomputed for the signal except, at worst, one
cheap forward (see 4.2).

```
              PREFILL (encode prompt)                 GENERATE (autoregressive)
prompt ────────────────────────────────►  tok1 tok2 ... tokN  <eos>
                                                              ^
   [last prompt token]                          [last answer content token]
        | h_L  <-- GATE read                              | h_L  <-- DIAL read
        v                                                 v
   gate score (before any answer exists)          dial score (after answer)
```

- **Gate** is read the instant prefill completes, before a single answer token is
  produced. It is effectively free: layer-L activation at the last prompt position
  is already materialized for the KV cache.
- **Dial** is read from the activation that fed the EOS prediction, i.e. layer-L at
  the last answer content token, available at the final decode step.

Per request the readout adds **two dot products**, not a second model pass (subject
to 4.2).

## 4. Activation capture: two implementation paths

### 4.1 Inline capture (single forward, preferred)

During autoregressive decoding, the layer-L activation at each generated position
equals the teacher-forced activation for the same prefix (same context, same
weights). So the dial's "last answer content token" vector can be grabbed at the
decode step whose input was that token, with a forward hook on layer L. This keeps
the request to a single generation pass. This is the deployment target.

### 4.2 Re-forward fallback (what the offline pipeline does)

The research extractor runs ONE teacher-forced forward over `[prompt + answer]` and
reads both positions. A server that cannot cleanly capture mid-decode activations
can replicate this with one extra forward over `[prompt + answer]` after generation.
That extra pass is a prefill (cheaper than the generation it follows) but it is not
free; prefer 4.1 in production.

Consistency note: 4.1 and 4.2 produce the same vector for a given prefix, so a probe
fit on the offline (4.2) surface applies unchanged to inline (4.1) capture.

## 5. Inference control flow (the two-stage pipeline)

```
request
  |
  +-- PREFILL --> gate = w_gate . h_L(last_prompt_tok)
  |                 |
  |                 +-- gate <  tau_gate ----------------> ABSTAIN ("I don't know"); never generate
  |                 |
  |                 +-- gate >= tau_gate --> GENERATE answer
  |                                             |
  |                                             v
  |                       dial_raw = w_dial . h_L(last_answer_tok)
  |                       p = calibrate(dial_raw)        # Platt/isotonic -> probability
  |                                             |
  |                                             +-- p low  --> VETO: withhold / hedge / route / retrieve
  |                                             +-- p high --> SURFACE answer + trust = p
  v
response (+ trust metadata)
```

- **Stage 1 (gate)** is a cheap pre-filter: skip answering questions the model
  cannot answer. This is where most of the deployed-model abstention load is carried.
- **Stage 2 (generate)** runs only for gated-through requests.
- **Stage 3 (dial)** produces the calibrated trust number; the **veto is simply a
  low dial on a generated answer**, which is how confident hallucinations are caught.

Thresholds `tau_gate` and the dial action threshold are tunable knobs set from the
risk-coverage curve (see 7), not fixed constants.

## 6. How the signal informs the response (injection patterns)

From least to most invasive. A deployment can use one or several.

### 6.1 Side-channel metadata (recommended default)

Return the trust number alongside the response (e.g. a `confidence` field). The
model output is unchanged; the **application layer** decides what to do: confidence
badge, gray-out, gating a downstream action, human-in-the-loop routing. Lowest risk,
highest flexibility, start here.

### 6.2 Gate as a hard abstention controller

If `gate < tau_gate`, short-circuit and emit an abstention template instead of
generating. Changes behavior, not just metadata. This is the gate's primary
deployment role.

### 6.3 Dial as a post-hoc veto / hedge

After generation, low dial -> suppress and abstain, prepend a hedge, or trigger a
tool/retrieval call to verify before surfacing. Post-processing on the decoded
answer; no model change.

### 6.4 Feed the score back into context (self-correction loop)

Inject the score as text into a second pass ("internal confidence here is low,
reconsider or abstain"). More capable, but roughly doubles inference cost;
agentic-loop territory; experimental.

### 6.5 What we deliberately do NOT do: activation steering

One could add the probe direction back into the residual stream to push generation
more cautious. We do not, because our own diagnosis (Paper 2 / steering-asymmetry
result) shows steering is asymmetric: ablating the caution direction relaxes
over-refusal, but adding it does **not** reliably install caution. So the
architecture is **read-and-act-externally, not edit-the-activations**. The decision
lives in the orchestration layer; the model's weights and activations are left
intact. This constraint is justified by evidence, not convenience.

## 7. Calibration stage (turns a rank into a number)

The raw dial *ranks* correctness well (offline AUROC ~0.834 @ 4B) but is **not** a
calibrated probability out of the box (offline ECE 0.151-0.168, above a 0.15 bar).
For a user-facing thresholdable number, fit a calibration map (Platt or isotonic) on
a held-out fold and apply it at inference:

```
p = calibrate(dial_raw)   # monotonic map: logit/score -> P(answer correct)
```

This is a few kilobytes more state and one cheap transform per request. It is the
step that converts "ranks well" into "a probability the user can threshold." Status:
**proposed; not yet implemented** (the offline scorers report ECE and a
risk-coverage curve but apply no calibration map yet).

Operational knobs come from the risk-coverage (selective-prediction) curve, e.g.
offline @4B: surfacing only the top-10%-confident answers reached 75.5% accuracy vs
a 27.2% base rate. The deployment chooses its coverage/accuracy operating point on
that curve.

## 8. Serving-stack integration

The one genuine integration cost: **fast inference servers (vLLM, TGI) do not expose
mid-layer hidden states by default** (they emit logits only). Two paths:

### 8.1 Forward hook / patched model (research / custom serving)

Register a hook on layer L that captures the activation at the needed token position;
run scaler + linear in a few lines. Fine for a custom deployment; requires the
serving path to surface intermediate activations.

### 8.2 aux_head baked into the model graph (clean production path)

Attach the linear readout as an auxiliary head at layer L *inside* the model, so the
forward pass emits the trust score as an extra output tensor natively. The server
returns it as a first-class output; no hooks. This already exists in the
synaptic-tuner engine and was exercised by the probe-as-head work (Amendment Q
reproduced the readout through the production aux_head). It is still a tiny linear
head on the residual stream; baking it in is a *packaging convenience* for serving
ergonomics, not a different mechanism.

Because the readout is training-free (the W result), the external probe (8.1) needs
no training; the aux_head (8.2) is the deployment-friendly wrapper that ships the
same linear readout as part of the model graph.

## 9. Cost model

Per request, added cost over a normal answer:

- gate: one dot product at prefill end (negligible).
- dial: one dot product at decode end (negligible) + inline capture (4.1), or one
  extra prefill over `[prompt+answer]` (4.2).
- calibration: one scalar transform.

Net: roughly the cost of the answer itself. Contrast the strong baseline,
**semantic entropy**, which needs N sampled generations per query. The deployment
pitch is precisely this: a single-forward readout gives a trust signal where
multi-sample methods are too expensive.

## 10. Validated vs proposed (honesty ledger)

| Element | Status |
|---------|--------|
| Linear gate/dial readout off layer L | validated offline (S/T/U/W; size-general so far via Amendment X) |
| Training-free readout (no task training) | validated offline (W); base veto weaker (0.754) than trained (0.980) |
| Orthogonality / keep two stages separate | validated offline (fusion delta -0.014) |
| aux_head emits the readout in-graph | validated in-engine offline (Amendment Q) |
| Calibration map (Platt/isotonic) to a probability | **proposed; not implemented** |
| Inline mid-decode activation capture in vLLM/TGI | **proposed; not built/load-tested** |
| Gate as live abstention controller / dial veto in a real server | **proposed; not built** |
| Cross-family generalization | **pending** the pre-registered confirmatory run |

## 11. Open engineering questions

- Mid-layer activation exposure in the target serving stack (vLLM hidden-states path
  vs a patched forward vs aux_head-in-graph). Pick one before a serving prototype.
- Layer L stability across models/sizes: L is chosen per checkpoint from the AUROC
  surface; a deployment needs a fixed L per shipped model (refit per checkpoint, as
  the cold-transfer result shows the direction drifts across checkpoints).
- Threshold governance: `tau_gate` and the dial action threshold are risk-coverage
  operating points; they need a calibration/validation set per deployment, not a
  hardcoded default.
- Calibration drift: the calibration map is fit on a distribution; monitor ECE on
  live traffic and refit if it drifts.

## References

- Research plan and claims audit: `papers/series/plan.md`
- Mechanism synthesis: `papers/paper-4-two-signal-readout/notes/framework.md`
- aux_head engine design: `docs/architecture/aux-head-prompt-completion-render.md`
- Probe pipeline + offline scorers: `archive/experiment/phase1/probe/`
- Cross-size evidence: `experiments/cross-model-size-sweep/AMENDMENT.md`
