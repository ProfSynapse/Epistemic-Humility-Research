# Dark-displacement literature map

## Why this note exists

Our probing and steering work targets a small set of named epistemic axes (doubt,
caution, confabulation-propensity, correctness/veto) in Qwen3-4B. A generation-time
displacement census finds that roughly 99% of hidden-state movement during
generation lies outside the span of all named axes combined. Before treating that
out-of-span residual as undiscovered epistemic structure, we need to know what such
residual structure typically *is* in the published literature. This note maps seven
families of prior work onto the census, gives each a concrete diagnostic signature,
and ends with a decision table from census observation to likely identity to next
action.

The papers below are ingested into the knowledge graph as typed atoms and
mechanisms; each is cited by linked title.

## The families

### 1. SAE dark matter (unexplained reconstruction variance)

[Decomposing The Dark Matter of Sparse Autoencoders](https://arxiv.org/abs/2410.14670)
studies the error left after a sparse autoencoder subtracts its linear features.
The central result is that about half the error vector and more than 90% of its
norm are linearly predictable from the input activation, so most of the residual
is structured, not noise. It splits into absent features, a linear-error
component, and a denser nonlinear-error component that is not a sparse sum of
linear features. This predicts our census residual is mostly *bookkeeping the
named-axis basis does not cover*: a component recoverable by a linear map from the
input, plus a smaller dense floor.

Diagnostic signature: fit a linear map from the input activation to the
out-of-span residual. If it recovers most of the norm (R-squared on the order of
0.7 to 0.95, as they report at mid layers), that part is dark matter and not a new
knob. The un-predictable remainder that does not shrink as the projection basis
grows richer is the nonlinear-error floor: dense, not low-dimensional, not
linearly predictable.

### 2. Massive activations, outlier and rogue dimensions, attention sinks

[Massive Activations in Large Language Models](https://arxiv.org/abs/2402.17762)
finds a handful of fixed residual-stream coordinates carrying values thousands of
times the median at special token positions (the start token, the first
delimiter). They are near-constant across inputs, act as fixed implicit bias
terms, and cause attention sinks; setting them to their mean is harmless while
zeroing them collapses the model.
[All Bark and No Bite: Rogue Dimensions in Transformer Language Models](https://arxiv.org/abs/2109.04404)
shows the embedding-similarity version: one to five dimensions with far-from-origin
means and outsized variance dominate cosine similarity while being nearly
irrelevant to behavior, and per-dimension standardization neutralizes them. These
are the classic nuisance identities.

Diagnostic signature: a per-coordinate kurtosis or max-over-median scan flags a
few fixed coordinates with enormous magnitude. They are input-agnostic and
checkpoint-stable, concentrated at special token positions, and outcome-blind
(their value does not track content). If per-dimension standardization of the
residual changes the geometry, rogue dimensions were driving your metric.

### 3. Non-linear and multi-dimensional features; feature manifolds

[Not All Language Model Features Are One-Dimensionally Linear](https://arxiv.org/abs/2405.14860)
shows some features are irreducibly multi-dimensional: circular representations of
days, months, and years that are causally used for modular arithmetic (a subspace
intervention on only the 2D ring nearly matches patching the whole layer).
[The Origins of Representation Manifolds in Large Language Models](https://arxiv.org/abs/2505.18235)
generalizes this to curved manifolds, proving that a feature's representation is
homeomorphic to its metric space and that geodesic distance recovers intrinsic
feature geometry. This is the *interesting* alternative: a slice of the census
residual might be a genuine multi-dimensional epistemic feature no single named
axis captures.

Diagnostic signature: project the residual for a graded stimulus set (PCA). A
multi-dimensional feature shows a curved, low-dimensional shape (a ring or
simplex), often with a non-informative radius axis as PC1 and the informative
angular ordering in PC2 and PC3. Confirm irreducibility with the separability and
mixture tests (it cannot be flattened to a line or split into independent axes),
and check that geodesic distances along the cloud vary monotonically with the
underlying quantity.

### 4. Residual-stream dynamics across layers; stages of inference

[The Remarkable Robustness of LLMs: Stages of Inference?](https://arxiv.org/abs/2406.19384)
proposes four depth-dependent stages: detokenization, feature engineering,
prediction ensembling, and residual sharpening. Middle layers are robust to
deletion and adjacent swapping (72 to 95% accuracy retained); final layers show
rising MLP-output norm and falling entropy. This tells the census what per-layer
displacement is expected structure.

Diagnostic signature: per-layer displacement should vary systematically by depth,
not randomly. Early-layer displacement is local detokenization, middle-layer
displacement is low-magnitude and near-interchangeable, and a large late-layer
displacement oriented toward the unembedding is the sharpening signature (expected,
not anomalous). The anomaly baseline must be depth-conditioned; the surprising
signal would be large, order-sensitive displacement in the *middle* band.

### 5. Position, length, and context bookkeeping

[Uncovering hidden geometry in Transformers via disentangling position and context](https://arxiv.org/abs/2310.04861)
decomposes every hidden state into a global mean, a positional mean, a context
mean, and a residual. The positional basis is low-rank (rank about 8 to 12) and
low-frequency, tracing a spiral; the context basis clusters by topic; the two are
nearly orthogonal. This is the direct precedent for our subtract-known-structure
method, and it says a large fraction of raw displacement is boring bookkeeping.

Diagnostic signature: before treating displacement as signal, subtract the global
mean (anisotropy; norms grow more than 100-fold across layers), a smooth positional
component monotone or spiral in token index, and a per-context topic offset. A
component that is monotone in token position, or constant within a document and
varying across documents, is bookkeeping. Only the leftover residual is candidate
dark structure.

### 6. Intrinsic dimensionality and spectrum analysis

[Less is More: Local Intrinsic Dimensions of Contextual Language Models](https://arxiv.org/abs/2506.01034)
measures the local intrinsic dimension of contextual embeddings with a localized
TwoNN estimator, finding mean dimension around 8 to 10 in a 768-dimensional space,
orders of magnitude below ambient. This is the quantitative low-versus-high verdict
for the census residual. The classic qualitative precedent is Cai et al. 2021
(Isotropy in the Contextual Embedding Space: Clusters and Manifolds, ICLR 2021),
which found anisotropic embedding spaces resolve into low-dimensional manifolds and
clusters once dominant directions are removed.

Diagnostic signature: compute the PCA spectrum (or a TwoNN local estimate) of the
out-of-span residual. A sharp elbow with a fast-decaying tail means a genuine
low-dimensional manifold (structured, interpretable); a flat, heavy-tailed spectrum
with no elbow means a dense high-dimensional component consistent with noise or
nonlinear SAE error. Report the effective dimension (participation ratio) so the
diagnosis is a number, not an eyeball of the scree plot.

### 7. Project-out-known-directions methodology

Two of the papers above double as the methodological precedent for
"project out known concept directions, characterize the remainder." The
position-context decomposition in
[Uncovering hidden geometry in Transformers via disentangling position and context](https://arxiv.org/abs/2310.04861)
is exactly an ANOVA-style subtraction of structural means followed by study of the
residual, and the SAE error decomposition in
[Decomposing The Dark Matter of Sparse Autoencoders](https://arxiv.org/abs/2410.14670)
is the same move applied to a learned feature basis. The census generalizes both:
our named epistemic axes are the "known directions," and the out-of-span residual
is the remainder. The lesson from both is that the residual is dominated by
predictable structure (means, positional smoothness, linearly recoverable error)
that must be stripped before any claim of novel signal.

## Decision table

The workflow: for each component the census surfaces, walk the table top to bottom.
The nuisance identities (rows 1 to 4) are cheap to rule out and should be checked
first; only a component that survives all of them is a candidate knob (rows 5 to 6).

| Census observation | Most likely literature identity | What to do next |
|---|---|---|
| A few fixed coordinates with huge magnitude / kurtosis; input-agnostic; checkpoint-stable; concentrated at start token or first delimiter | Massive activations / rogue dimensions ([Massive Activations](https://arxiv.org/abs/2402.17762), [Rogue Dimensions](https://arxiv.org/abs/2109.04404)) | Ignore as nuisance. Mask those coordinates or per-dimension standardize before any further census metric; condition on token type. |
| Large shared offset present in every position; displacement monotone or spiral in token index; per-document constant offset | Position / context / mean bookkeeping ([Hidden geometry via position and context](https://arxiv.org/abs/2310.04861)) | Ignore as nuisance. Subtract global mean + positional mean + context mean (ANOVA decomposition) and re-run the census on the residual only. |
| Large late-layer displacement oriented toward the unembedding; rising norm and falling entropy near the final layers | Residual sharpening / stages of inference ([Stages of Inference](https://arxiv.org/abs/2406.19384)) | Ignore as nuisance but depth-condition the baseline. Expected structure; flag only middle-layer, order-sensitive displacement as surprising. |
| Dense residual, roughly half recoverable by a linear map from the input activation, remainder not linearly predictable and not shrinking with a richer basis | SAE dark matter / nonlinear error ([Decomposing the Dark Matter](https://arxiv.org/abs/2410.14670)) | SAE pass. Fit the linear map, report the recovered norm fraction, and treat the un-predictable dense floor as a nuisance floor, not a knob. |
| Flat, heavy-tailed PCA spectrum with no elbow; high effective dimension relative to ambient | Dense component / noise (intrinsic-dimension test, [Less is More](https://arxiv.org/abs/2506.01034)) | Ignore as noise. Report participation ratio; do not screen as a knob. |
| Curved low-dimensional shape (ring, simplex); informative angular ordering in PC2 or PC3; irreducible (fails separability and mixture tests); geodesic distance monotone in an underlying quantity | Multi-dimensional feature / representation manifold ([Not All Features Linear](https://arxiv.org/abs/2405.14860), [Origins of Representation Manifolds](https://arxiv.org/abs/2505.18235)) | Add to the knob screen. Fit a subspace probe and test causal sufficiency with a subspace intervention; this is a candidate epistemic feature. |

## The three most decision-relevant signatures

1. Linear-predictability-from-input is the single fastest discriminator. If a
   linear map from the input activation recovers most of the residual norm, the
   component is SAE dark matter or mean bookkeeping, not a knob (rows 2 and 4). This
   test should run first because it cheaply removes the bulk of the 99%.

2. Per-coordinate kurtosis plus checkpoint-stability plus special-token
   localization identifies massive activations and rogue dimensions, which will
   otherwise dominate any raw norm or cosine of the residual (row 1). Mask or
   standardize these before trusting any census statistic.

3. PCA-spectrum shape (sharp elbow versus flat heavy tail) plus irreducibility
   is the only positive signature that promotes a component to knob-candidate. A
   curved low-dimensional manifold that survives the linear-predictability and
   nuisance screens is the interesting residual worth a subspace intervention
   (row 6); a flat high-dimensional spectrum is noise (row 5).
