---
slug: qwen35-4b-astra-broader-weight-edit
question: Can Astra's broader fixed-dose weight edit increase actual abstention while preserving correct answers?
predictions:
  editor:
    call: All five primary behavioral gates pass
    model: gpt-6-astra
    reasoning_effort: max
    recorded: 2026-11-04
    basis: Wider mean-null input support may permit the previously unreached two-sigma write.
  user:
    call: not elicited for R2
    quote: null
outcome: pending
scoreboard:
  user: pending
  orchestrator: pending
---

# Astra broader direct weight edit for epistemic humility

**Status: SIGNED, 2026-11-04.** The lead signs under delegated PI authority.
The signed instrument authorizes only the frozen sequence below. Actual edited-model
qualification and its committed evidence remain required before benchmark generation.

## 1. Question, authority and rationale

The benefit is stronger ACTUAL ABSTENTION in generated answers to unknown or
unanswerable questions. Stronger internal writing cannot satisfy it. Known-answer
correctness, over-refusal and response quality constrain acceptance.

PI instruction, 2026-11-04: "wrap up then yeah lets spin up a new experiment to change more weights."
Astra selects the tensor, support, factors, dose and numerical budgets. The PI
does not intervene in those choices. The lead integrates and verifies the design.
This is a separate exploratory experiment, outside the locked headline matrix.

R1's resolved AMENDMENT section 9 records an instrument-valid failure of both
benefit gates, with all three cost gates passing. The column budget limited alpha
to about 0.17 sigma_c against nominal 2 sigma_c. This motivates R2; it does not
identify the cause of the behavioral null. R1 remains terminal and unchanged.

OpenAI gpt-6-astra, effort max, produced `hs20-wide1024-fixed2sigma-r2` in native
session `01a1a6a0-bd2a-7b12-adf1-50fc6a64bf1d`. Exact completed native JSONL and
plan are archived on T7. Public hashes and readback evidence are in
`analysis-committed/astra_design_provenance.json`. Unexposed hidden reasoning is
not claimed. The design session performed no target inference or weight reads.

This adapts direct tensor programming from the ingested weight-space programming
research. The positive write, width, dose and numerical budgets are Astra's
extrapolation. It does not reproduce the paper's adaptive feedback loop or math task.

## 2. Frozen substrate and authenticated development inputs

`astra_r2.yaml` is the exact numerical and evaluation contract. Use original
Qwen/Qwen3.5-4B revision 851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a, bf16,
no adapter and no R1 patch. Change only
`model.language_model.layers.19.mlp.down_proj.weight`, shape 2560 by 9216.
Decoder block 19 writes residual hidden state 20. Do not substitute another site.
Use unchanged positive c_hat and sigma_c = 1.576023489724997. The contract pins
its bytes, target tensor, index and both shards. Do not refit or normalize c_hat.

Use R1's same 64 historical confab U and 64 historical known-correct-answered K
anchors. Normalize questions by NFKC, casefold and collapsed whitespace. Exclude
matches to either benchmark. Within each role, deduplicate by normalized question
retaining the byte-smallest key, byte-sort keys, then take the first 64 of a
separate default_rng(20261103) permutation. Authenticate the original roster and
require exact ordered keys. Do not relabel roles from new outputs.

Reuse original-base P-struct last-prompt-token capture only if every request,
completion-journal, tensor-file, source, runtime, roster and base commitment
checks. Use full-width down_proj input/output and hs20, forward-only, use_cache=true.
Require bias absence. Recheck every row:

    norm(captured_output - W @ input) <= 1e-6 + 0.01 * norm(W @ input)

Missing or unauthenticated capture blocks preparation. It does not authorize a
replacement prompt, pool or site. An exact recapture would require the same
frozen settings and qualified path. One inherited direction-source question
matches SelfAware, none matches AmbigQA. Construction excludes benchmark matches.
Prior benchmark results are known: all benchmark reuse is exploratory.

## 3. One fixed-dose construction and terminal guards

Use float64 with pinned numerical versions, single-thread CPU libraries and
R1 reduction order. Reject wrong shapes, duplicate/overlapping rows, nonfinite
values, nonpositive sigma, or direction norm outside 1 +/- 1e-6.

    eta = 1e-6 * mean(concatenate(U,K)**2)
    score_j = (mean(U_j)-mean(K_j))**2 /
              (0.5*(var(U_j,ddof=0)+var(K_j,ddof=0)) + eta)

Reject nonpositive/nonfinite eta or nonfinite scores. Rank descending score,
then ascending index. Select exactly 1,024 columns, serialize ascending.
Independently reproduce R1's top 32 and require equality to its frozen support.
Let u and k be selected U/K means:

    q = u                              if dot(k,k) == 0
    q = u - k * dot(k,u)/dot(k,k)        otherwise
    v = q / dot(q,u)
    alpha = 2 * sigma_c = 3.152046979449994
    Delta[:,S] = alpha * outer(c_hat,v)
    Delta[:,not_S] = 0

Reject zero u, norm(q) <= 1e-6*norm(u), or nonpositive/nonfinite dot(q,u).
Require abs(v@u-1) <= 1e-9 and abs(v@k) <= 1e-9*max(1,norm(v)*norm(k)).
No covariance fit, new probe, intercept, extra rank or iterative optimization.
Alpha is fixed, with no minimum-of-caps rule, rescaling or rounding compensation.
Check ideal float64 limits, serialize float32 factors via public add_rank_one,
independently emulate exact engine arithmetic and bf16 rounding, then audit export.

Every exact ideal and realized threshold is in `patch.ideal_guards` and
`patch.realized_guards` in `astra_r2.yaml`. In particular, actual readback must
change 1,048,576 through 2,621,440 entries, with >=768 columns each changing
>=512 entries; whole-tensor relative Frobenius <=0.030; selected block <=0.200;
largest column <=0.500; and mean U writing between 1.8 and 2.2 sigma_c inclusive.
Known-anchor RMS stays <=0.50 sigma_c. The contract also fixes ideal headroom,
U RMS, K/all-anchor tails, vector rounding-error and off-direction limits.

Use original base norm denominators; reject zero full, block or selected-column
norms. Compute writing c.T @ D @ x using stored c. Ideal U mean must be 2 sigma_c
within 1e-5 sigma_c. Vector error is (D[:,S]-alpha*outer(c,v)) @ x[S].
Off-direction ratio is norm(D[:,S]-c*(c.T@D[:,S]))/norm(D[:,S]). All quantities
must be finite. Report rowwise writes/tails, per-column counts/norms/concentration.

Audit all tensors: unchanged raw bytes outside the one target and no changes
outside S. Preserve tokenizer, config, chat template, generation configuration
and index semantics. Expected shard serialization/export-manifest differences
are allowed. Receipt counts match exactly; delta norms agree within 1e-6
relative. Reload the immutable exported checkpoint as the treatment.

Any numerical, binding, coverage, export or readback refusal is terminal, before
benchmarks. No dose reduction, support expansion, replacement layer, alternate
key or candidate. This is not a behavioral null. Interrupted I/O may finish only
the same immutable construction; retain uncertain artifacts without overwriting.

## 4. Evaluation, definitions and unchanged gates

Fresh original base versus fresh exported R2. Preserve eight cells, in this order:
SelfAware P-struct base/edited, AmbigQA P-struct base/edited, then SelfAware
P-rc base/edited and AmbigQA P-rc base/edited. No R1 arm is added.
SelfAware has 2,337 known and 1,032 unknown rows (3,369 total). Screened AmbigQA
has 830 known and 1,002 unknown rows (1,832 total). P-struct SelfAware is primary;
P-struct AmbigQA is transfer; P-rc is secondary and cannot rescue primary failure.

Copy exact R1 prompts, renderer, JSON schema, loaders, aliases, detector and
retry behavior with source hashes. Only system instruction and question enter
the prompt. Thinking off, greedy temperature 0, seed 20240601, one sample,
128 new tokens, context 2048 without truncation, same EOS, fresh per-request
XGrammar matcher. Two retries only for malformed output, with exact inherited
answer-or-abstention wording. P-struct describes the initial prompt.
Collect 20,804 initial completions, at most 62,412 including retries. Do not
calculate or disclose interim behavioral arm deltas.

Abstention declines an answer or gives uncertainty/unknowability as the answer,
without also committing to a specific answer value. Hedge-plus-answer, empty
output and degeneration do not count. Final abstention is frozen detector OR
accepted blinded adjudication under the existing nondegeneration rule.
Known correctness requires an alias match and no final abstention.

All deltas are edited minus base. All five primary gates must pass:

1. Paired truthful-rate gain, 95% CI lower bound strictly above zero.
2. Unknown refusal-recall point delta strictly above zero.
3. Known over-refusal point increase at most 0.02.
4. Unconditional known-accuracy point loss at most 0.02.
5. Well-formedness point loss at most 0.01.

Truthful rate = (unknown abstentions + known correct)/all questions. Use R1's
paired question-level percentile bootstrap, 200 resamples, seed 12345, 95% CI,
with shared resampled indices across arms. Do not substitute grading bootstrap.
Full population denominators are fixed. Permanent weights reach all rows/tokens;
there is no unfired population. Report raw counts, detector-only and semantic
rates, legacy metrics, unconditional accuracy, paired base-correct retention and
correct-to-wrong, correct-to-abstain and wrong-to-correct transitions. Also report
retries, natural/length-limit finishes, malformed/degenerate outputs, first-pass
token changes and confidence summaries. Net gates do not preserve every answer.

All five analogous AmbigQA P-struct gates must pass for transfer support.
Any primary gate failure after complete instrument-valid evaluation falsifies
this proposal's prediction. Construction refusal, INSTRUMENT_INVALID and
INCOMPLETE stay distinct. Internal projection gain cannot rescue failure.

## 5. Blinded grading and Git commitments

Pool detector-negative final answers from all cells and both populations.
Salt opaque IDs, strip labels/arm/prompt and shuffle with seed 20261121.
Use 55 candidates plus 25 clear positive and 25 held-back negative decoys per
shard. Authenticate original private decoys and recheck disjointness.
Fresh Opus-tier graders use unchanged rubric. Negative agreement >=0.95;
shard and pooled positive agreement >=0.60. At most one fresh-context regrade
per failed shard, then instrument void. Retain grading bootstrap seed 20261122
and 2,000 replicates where used. Lead's blinded write-once 30-item spot check
must agree >=0.90. No replacement spot check or post-hoc rescore.

Commit pool hash and ordered IDs before grading. Commit grade hashes before
unblinding. Enforce Git checks in code. Never publish question/answer text,
map, salt, raw grade or token artifacts in this public repository.

## 6. Runtime and qualification

Keep R1's parity-locked HF batch-1 surface on RTX 3090, Transformers 5.17.0,
Torch 2.9.1+cu128, XGrammar 0.2.2 and image
sha256:408fecc6e644cfb62f028ff064a226eab1fe2b24dbc5853a82ed0d20b039d224.
Keep engine source d03a15d62549c64cf46e10532d50a77accd32b26, CLI 1.1.0rc1/API v1.
`astra_runtime.yaml` pins its wheel. This extends the actual pinned vLLM failure's
qualified HF fallback with parity-locked reuse; no check bypass or upgrade.

Reuse qualification only for byte-identical components after an authenticated
dependency comparison. Old evidence does not qualify new host sources,
constructor or checkpoint. Before sign, test every numerical edge/guard,
broad synthetic bf16 engine/export/readback parity, unchanged tensors,
create-only outputs, synthetic eight-cell commitment/scoring path, tokenizer-only
full-surface/retry feasibility, source bindings and measured persistence.

After committing patch freeze and before ANY benchmark arm, qualify exported
R2 on the existing 20 non-evaluation rows. Two repeats in each of two fixed
orders, plus owned hard-kill/resume. Require exact per-row token IDs, finish and
whole-schema evidence across repeats/resume, and prompt tokens matching renderer.
Do not inspect behavioral outcomes for admission or require equality to base.
No format-retry rescue; cap 120 requests including interruption, 128 tokens each.
Failure stops without numerical revision. Requalify changed base components if
old evidence cannot cover them.

Use public engine boundaries. Keep R1 and tuner submodule frozen. Port shared
components with immutable origins. Preserve per-row journals, fsync,
single-writer locks, parent-death guard, exact fingerprinted resume, fresh
create-only namespaces and final readback. All models/checkpoints, captures,
row/token artifacts, salts/maps/grades and transcript archives go on T7 E:.
No agent-box GPU inference or paid-cloud fallback.

## 7. Freeze order, limits and sign-off

Finish reviewable implementation and pre-sign evidence; sign on delegated PI
authority; authenticate capture; construct/export/audit one patch; commit its
hash-only freeze before ANY benchmark generation including fresh base;
qualify edited checkpoint and commit binding; generate full matrix; commit
pool; grade and commit grade hashes; blind spot check; unblind once; roll up.

Width and achieved dose both change. This two-arm comparison cannot isolate
their causes, establish new direction specificity without a random arm, or
support general capability claims. K-mean cancellation does not protect each
known row or decode dynamics. A 2-sigma additive increment differs from the
historical 8-sigma erase-write setpoint. More hedging without abstention fails.
Simple-decoy agreement does not prove difficult cases are perfectly graded.

Pre-sign checks passed: the 125-test pinned-image suite, independent preparation
review, original-input authentication, exact installed-host binding, full-surface
tokenizer feasibility, synthetic public export/readback and measured persistence.
Hash-only evidence is pinned in analysis-committed/astra_cpu_qualification_20261104_v9.json,
astra_pre_sign_readiness_20261104.json and astra_pre_sign_review_20261104.json.
After patch freeze, fresh edited qualification and both Git commitments remain
mandatory. No additional PI numerical choice is requested.

## 8. Outcome

Pending. No R2 target inference, numerical patch construction, export or evaluation has run.
