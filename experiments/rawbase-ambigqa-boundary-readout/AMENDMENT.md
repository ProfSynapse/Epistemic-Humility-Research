---
amendment: rawbase-ambigqa-boundary-readout
tier: 3
posture: exploratory
status: draft
---

# Raw-base AmbigQA boundary readout (pretraining-flavor vs training-warp fork)

## 1. Question

`ood-breadth-beyond-selfaware` (resolved gates, G7 FAIL) found that the
internal known-unknown readout, near-perfect on SelfAware (0.997), reads the
AmbigQA answerability boundary at only 0.6279 (clean-SFT, A1) and 0.6349
(clean-SFT to GRPO-v2, A4) held-out at the pre-registered locus (L35,
anchor position). Both panel checkpoints are trained. Amendment Y
(`pretrain-only-base-readout`, outcome H_B1 SUPPORTED 4/4) established that
the SelfAware readout predates post-training, but only on SelfAware.

This cell asks the fork the PI stated on 2026-08-09: is the pretrained
activation flavored to SelfAware-style unanswerability from the start
(flavor-specific), or did pretraining install a broader answerability
signal that post-training warped or narrowed (training-warp)? One
measurement separates them: the same AmbigQA panel readout on the raw,
untrained base.

## 2. Design

- Substrate: `unsloth/Qwen3-4B`, revision
  `64033659d5caf1b8ed7f929b29de705e93a4d468` (the program's pinned raw-base
  reference revision), no adapter, bf16.
- Panel: the IDENTICAL 2748-row AmbigQA internal panel used by item 26
  (1245 known / 1503 unknown), consumed from the screened pool file
  `experiments/ood-breadth-beyond-selfaware/analysis/screen/internal_panel_pool.jsonl`,
  sha256 `b0f936583d5a2fcd7dbc1393dce754c62669cb5185a5c80fb644266875a48bfd`
  (2748 lines, verified at registration). No new screening, no row changes.
- Extraction: same recipe shape as item 26's `extract_A1.yaml` (anchor
  family only, layers [35], max_new_tokens 1, same render module), checkpoint
  swapped to the raw base. Recipe `extract_rawbase.yaml` in this directory.
- Probe fit: item 26's pinned `internal_panel_probe_gate.py` (sha256
  `ee3f22eed5f8b4fe8f260c5b3335c565156eadfcf083473bb445921d29885b08`),
  invoked unchanged on the raw-base extraction, same 5-fold protocol and
  fold seeding. The emitted-channel margin sub-check is NOT read for this
  cell (a raw base has no schema-following emitted confidence surface);
  only `heldout_probe_auroc` and its fold std are evidential here, and the
  script's margin fields are recorded as descriptive.
- Runtime: every extract verb inside the pinned mechinterp-runner image per
  the 2026-07-10 standing directive; digest recorded in `experiment.yaml`
  `instrument.runtime_image_digest`.
- Budget: one GPU extraction, roughly 5 to 15 minutes, plus a CPU probe fit.

## 3. Prediction (pre-stated)

The raw base ALSO fails the SelfAware-grade bar on AmbigQA and lands within
0.10 of the trained checkpoints: heldout_probe_auroc <= 0.73. That is the
flavor-specific reading: the pretrained activation encodes
SelfAware-flavored unanswerability (obviously-unknowable questions), and
AmbigQA ambiguity is a different flavor it never covered. Grounds: the more
trained panel checkpoint reads slightly HIGHER than the less trained one
(A4 0.6349 vs A1 0.6279), the wrong direction for a training-dulls-it
account; and Amendment Y's H_B3 found post-training does not sharpen the
SelfAware readout, so training has not been shown to create or destroy this
signal in either direction on any surface.

## 4. Falsifier (pre-stated)

heldout_probe_auroc >= 0.85 on the raw base. That would establish the
training-warp reading: pretraining installed a substantially more general
answerability signal at this locus, and the trained checkpoints' 0.63 means
post-training narrowed or warped it. This overturns the flavor-specific
account and redirects papers 2 and 3 toward training-induced narrowing.

## 5. Adjudication bands (fixed at registration, no goalpost movement)

- `heldout_probe_auroc <= 0.73`: prediction supported, flavor-specific.
- `heldout_probe_auroc >= 0.85`: falsifier fires, training-warp.
- `0.73 < heldout_probe_auroc < 0.85`: AMBIGUOUS. Reported as ambiguous;
  neither account claimed. No threshold is retuned after the number exists.

The trained comparators (0.6279 / 0.6349, committed in
`experiments/ood-breadth-beyond-selfaware/analysis-committed/g7_A{1,4}.json`)
are fixed reference points, not gates.

## 6. Gates

See `gates.yaml`: RG0 panel integrity (pool file sha and 2748/1245/1503
exact), RG1 extraction capture (n_rows == n_answered == 2748), RG2 runtime
provenance (pinned image digest char-for-char and the provenance JSON line
in the run log). All fail-closed: any RG failure voids the measurement
before M1 is read.

## 7. Reporting

Exploratory tier 3, single model, single seed, one layer, one position.
Reported beside item 26's G7, never pooled with the locked matrix. Committed
outputs are aggregate metrics, counts, and shas only; no question text and
no hidden states are committed. Whatever the outcome, the result feeds the
paper-3 revision as the scoping sentence for the pretraining-origin claim.
