# Fresh-SFT Epistemic Mode Tokens, Then GRPO: notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and machine state in
`experiment.yaml`.

## Entries

### 2026-07-22: lineage and mechanism correction

- User clarified that the intended substrate is a **new SFT from the original
  Qwen3-4B model**, not an existing clean-SFT or GRPO-v3 checkpoint.
- The new SFT jointly teaches the first private action token and its visible
  behavior: `<ANSWER>`, `<QUALIFY>`, or `<ABSTAIN>`.
- Mode labels come from a frozen 32-generation capability audit: reliably
  correct, intermittently correct, or effectively never correct. Exact bucket
  thresholds are not new: the governed Phase-1 rule maps known to `<ANSWER>`,
  discard/ambiguous-middle to `<QUALIFY>`, and unknown to `<ABSTAIN>`. The
  proposed threshold pilot was removed after user review.
- The tracked artifact preserves 8,892 known and 7,103 unknown keys (14,395
  train, 1,600 dev). The original row-level `probe_results.jsonl` containing
  exact per-question `p_correct` and 32 sampled answers is absent locally and
  from the authenticated project HF dataset inventory. This blocks exact scalar
  targets, not categorical modes. Pre-sign choice: recover that cache or use
  fixed non-endpoint confidence bands after reconstructing the deterministic
  20,000-question ambiguous-middle complement.
- The primary action surface is the model's normal LM head restricted to the
  three registered tokens. A separate internal readout is measurement-only and
  tests whether token choice tracks prompt-end knowledge.
- The mode token prefixes a JSON object containing `answer` and
  `answer_confidence`. This preserves the parseable answer-plus-scalar surface,
  but does not silently reuse historical `response_confidence`: that field meant
  response appropriateness and is high for a correct abstention, whereas the new
  scalar estimates factual-answer capability and must be low when knowledge is
  low. Its target is a smoothed transform of correct generations out of 32.
- GRPO, if the SFT gate passes, starts from this newly trained SFT checkpoint.
  GRPO-v3 is motivation/comparison only and is prohibited as an input.
- The prior custom ordinal-router design was removed. A custom head is now a
  successor hypothesis only if native first-token logits fail while the
  independent readout remains valid.
- Drafting and committing this unsigned handoff branch are authorized. Signing,
  launching, and merging are not authorized.
- Response grading now uses the recent two-instrument discipline. The current
  enumerated detector-v2/pattern inventory is retained and reported, followed by
  a blinded multi-class LLM posture review. Unlike RR3's abstention-only lane,
  this experiment sends all held-out rows to review because qualified answers
  intentionally contain detector phrases such as "I'm not sure" and would be
  systematic detector false positives. The lane adopts RR3/Llama's
  manifest-before-review, graded-hash-before-unblinding, held-back decoy,
  private-reviewer-directory, positional-join, and no-rescoring safeguards.

### 2026-07-22: original scaffold (superseded before sign)

- The initial draft proposed a frozen prompt-end ordinal router on the existing
  GRPO-v3 checkpoint. User review rejected that lineage and clarified the fresh
  SFT-to-GRPO hypothesis above. No run was launched and no instrument was signed.
