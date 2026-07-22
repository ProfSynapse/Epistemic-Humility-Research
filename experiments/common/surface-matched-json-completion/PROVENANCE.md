# Gemma vLLM G0 Failure IDs

This ID-only artifact promotes the exact strict-validation failure set from the
resolved `family-atlas-surface-matched-vllm-control` experiment for reuse by its
JSON-completion successor. The governed source is that experiment's
`AMENDMENT.md` Outcome and its committed
`analysis-committed/gemma4_e4b_it/stage_a_g0_failure_summary.json`.

The source amendment records 5,200 Gemma completions, 5,189 strict-valid rows,
and 11 G0 failures. The JSON artifact preserves only those row IDs, counts, and
origin artifact hashes. It contains no prompts, answers, aliases, generations,
or token evidence.

Consumers must verify the JSON file hash, all recorded counts, the exact source
completion hash, and exact ID membership before using the set. The private
source completion artifact remains local and read-only.
