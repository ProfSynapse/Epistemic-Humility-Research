# Thinking Audit 128/1024

Exploratory source-of-truth audit for the Phase 1 TriviaQA probe labels.

This compares the locked non-thinking Qwen3-4B probe
(`qwen3-4b-instruct/probe_results.jsonl`) against a thinking-enabled rerun on a
128-row deterministic subset using the same sampling seed, label bands, and
probe-pool selection method, with `max_new_tokens: 1024`.

Artifacts:

- config: `experiments/thinking-enabled-parallel-arm/artifacts/configs/probe_thinking_audit_128_1024.yaml`
- thinking manifest:
  `experiment/phase1/probe/qwen3-4b-instruct-thinking-audit-128-1024/probe_manifest.json`
- summary: `summary.json`
- joined row comparison: `row_comparison.csv`
- session: `docs/sessions/20260625T122352Z-triviaqa-thinking-knowledge-audit.md`

Headline result:

- joined rows: 128
- base labels on joined rows: 56 known, 47 unknown, 25 discard
- thinking labels on joined rows: 56 known, 33 unknown, 39 discard
- base unknown -> thinking known: 1/47
- base unknown -> thinking discard: 15/47
- greedy wrong -> greedy right: 13/128
- greedy right -> greedy wrong: 10/128
- sampled extraction statuses: 3,303 post-think, 793 unterminated thinking

Interpretation:

Thinking changes the measured TriviaQA boundary, but this bounded audit does not
show a large collapse of the unknown set into known. The main movement is from
base-unknown to thinking-discard, meaning thinking sometimes surfaces enough
correct samples to violate the strict unknown label but usually not enough to
cross the known threshold. The single unknown->known row is also partly a scorer
strictness example: the non-thinking answer was essentially "Civil War" while
the alias set preferred "American Civil War" variants.

Do not use this as a replacement for the locked source labels. Use it as
evidence that any source-of-truth revision should jointly consider thinking
mode, generation token budget, extraction truncation, and TriviaQA alias scoring
sensitivity.
