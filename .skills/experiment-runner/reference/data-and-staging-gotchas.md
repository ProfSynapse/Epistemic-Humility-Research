# Data And Staging Gotchas

Read for dataset identity, leakage, recipe materialization, and local staging issues.

- Windows default text encoding broke the TriviaQA fetch before the script used
  explicit UTF-8 writes. Keep UTF-8 mode/path handling in mind for fetch retries.

- Windows default text encoding also broke Phase 1 eval gold/OOD loaders when
  local files contained non-cp1252 bytes. Eval readers/writers now use explicit
  UTF-8; preserve that when adding datasets or result files.

- TriviaQA train `question_id` is not unique. WS-1 resumability/subsetting must
  use `probe_pool_row_key` (source index plus question_id), not bare
  `question_id`, or duplicate source rows will be silently skipped.

- Carry that same identity rule into WS-2. `questions_frozen.json` train/dev
  disjointness must be audited with `*_question_keys` / `probe_pool_row_key`,
  not bare `*_question_ids`; duplicate TriviaQA IDs can otherwise make a clean
  row-level split look overlapped or seed duplicate rows identically.

- Row-key disjointness is not prompt-text disjointness. A 2026-06-14 audit of
  `qwen3-4b-instruct` initially found the WS-2 split was clean by
  `probe_pool_row_key`, leakage-clean against Cheng test, and byte-reproducible,
  but had 188 normalized question texts present in both train and dev under
  different source row keys. The builder now splits dev by
  `norm_question(question)` groups and records `dev_split_group_key` in
  `questions_frozen.json`. Re-audit after rebuild found 0 row-key overlap,
  0 normalized-question overlap, leakage guard passed, KTO labels balanced, no
  unknown-negative fallback, no thinking-tag contamination, and byte-for-byte
  reproducibility. Previous local SFT/DPO/KTO seed-1 runs are pre-split-fix
  bounded evidence; rerun SFT seed 1 on the regenerated dataset before using it
  as the mixed-stage comparator.

- The Phase 1 frozen SFT/DPO/KTO builders intentionally use only `known` and
  `unknown` probe labels; raw probe rows labeled `discard` are excluded from the
  locked v0.3 training set. For schema-trained response-confidence work, do not
  treat all discarded rows as waste. The Qwen3-4B probe had 4,005 discard rows;
  the middle `p_correct` band `[0.4, 0.6]` contributed 548 useful ambiguous
  examples. In the schema response-confidence projection, those rows should be
  labeled separately as ambiguous/middle, trained with correct answers and
  middle `response_confidence`, and kept out of v0.3 headline counts.

- JSONL training projections must keep a stable column set across normal and
  appended special-case rows. Hugging Face `datasets` infers/casts the JSON
  schema before trainer-specific row cleanup can drop provenance fields; if
  later ambiguous or diagnostic rows add columns such as `label`,
  `source_label`, or `p_correct`, `load_dataset("json")` can fail before model
  loading. Null defaults are not enough because Arrow may infer a `null` column
  type and then reject later strings/floats. Add optional provenance keys with
  typed sentinel values such as `""` or `-1.0` to ordinary rows, then cover both
  row-key stability and mixed-type loading with tests whenever a builder appends
  another row family.

- Cheng recipe provenance gotcha: the paper text is vague, but the official
  OpenMOSS/Say-I-Dont-Know README publishes concrete commands. Cheng Idk-SFT is
  `llama_recipes/finetuning.py --enable_fsdp` with `--num_epochs 10`, `--lr
  2e-5`, `--batch_size_training 4`, and `--gradient_accumulation_steps 2`.
  Cheng Idk-DPO initializes from the SFT result model and uses `loss.beta=0.1`,
  `loss.sft_coef_when_dpo=0.01`, batch size 64, gradient accumulation 4, and
  FSDPTrainer. The Phase 1 Qwen3 recipes are therefore NOT a bit-for-bit Cheng
  training reproduction: they are a resource-feasible LoRA/QLoRA
  replication-style design with matched LoRA capacity across arms. Do not cite
  Cheng hyperparameters from the raw evidence report unless re-verified against
  the official repo/PDF, and do not treat cold-start DPO/KTO failures as a
  contradiction of Cheng's sequential SFT-warmed preference setup.

- On Windows, staged tuner scratch paths in run records/materialized recipes
  should be POSIX-style (`scratch/...`) even though host paths are Windows paths;
  emitting backslashes makes provenance noisy and can surprise container path
  handling.

- Materialized `artifacts.output_root` must render the concrete lane
  (`runs/local/...`) before handing the recipe to `tuner.py local-run`; the tuner
  local-run renderer does not define a `{lane}` template variable.

- Local copy-mode SFT imports both top-level `shared.*` and `Trainers.shared.*`.
  A prepared local cell must copy `Trainers/<method>`, `Trainers/shared`,
  top-level `shared`, `tuner`, and the staged dataset; copying only the method
  trainer dir fails at `ModuleNotFoundError: No module named 'Trainers.shared'`.
