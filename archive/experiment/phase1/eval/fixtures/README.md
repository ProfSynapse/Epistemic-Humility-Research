# eval fixtures

Tiny hand-made fixtures that let the eval harness run end-to-end (and the test
suite exercise the scoring + stats layers) WITHOUT a live model or trained
adapters. Real eval runs replace these via the post-sign-off VLLMGenerator.

- `in_domain_records.json` — a handful of in-domain eval records carrying probe
  `label` (known/unknown), `question`, and gold `aliases`. Matches the schema
  `run_eval._load_eval_records` produces for non-OOD sets.
- `gold_min.jsonl` — minimal Cheng-style gold (`question_norm` +
  `normalized_aliases`) covering the fixture questions, for unit tests that do
  not want the full 11k gold file.
- `gen_<arm>__in_domain.jsonl` — pre-recorded generations keyed by record `id`,
  consumed by `FixtureGenerator`. One per arm in the smoke config.

These are fixtures, not results; they are deterministic and committed.
