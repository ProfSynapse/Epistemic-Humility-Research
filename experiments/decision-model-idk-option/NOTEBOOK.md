# Decision-model IDK option: with no further training, do decision models pick an explicit I don't know when the base torso truly does not know? notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

### 2026-10-06: pre-sign checks (checklist 2-6); two items need a PI decision before sign

Tier 3, lab notebook. Run by a subagent for the orchestrator. Nothing was
signed or committed, and no confirmatory stage ran. The GPU was exclusive
(0 MiB in use at the start). Inputs were non-PopQA or throwaway:

- cell.yaml `smoke_items`;
- 150 synthetic arithmetic MC questions (`presign/drill_recognize_resume.py`);
- 2,400 synthetic 5-option arithmetic rows (`presign/prep_engine_presign.py`).

PopQA IDK rows were only tokenised and split. No PopQA row went through a
model. Run record: `analysis-committed/run_records/dmio-presign-20261006.json`.
Row-level outputs are in gitignored `analysis/presign/` and in the tuner's
`scratch/eh_staging/dmio-presign-*/`.

**Harness change (mechanical; listed in full).** In `recognize-worker`, the
per-prompt `seconds` field now uses `time.perf_counter()` instead of
`time.time()`. The first smoke logged two negative durations (-0.72 s and
-1.01 s) because the container's wall clock stepped backwards. No label, gate
or scored quantity reads `seconds`. Letter logits were identical across the
launches before and after the change (32 of 32). No other harness, config or
threshold edit was made.

- **Check 1, IDK render inside the pinned engine image: PASS (both models).**
  - Ran through `tuner.py local-run` of the pinned template recipe (same
    image, pip set and copy set), with sandbox paths.
  - `presign/check_engine_render.py` used the engine's own `load_examples`
    and `DecisionCollator(train=False)` with each checkpoint's
    `decision_config` and tokenizer. No weights were loaded.
  - Coverage: all 12,067 rows at each of the 5 positions, for both models.
    0 failures on every per-row check:
    - canonical order is rendered, and the IDK option sits at
      `meta.idk_slot`;
    - the IDK line is exactly `<marker>. I don't know`;
    - the 4 real options keep dmcc's relative order, and the gold name and
      label shift are correct;
    - the IDK prompt equals the no-IDK prompt plus one inserted line with
      the markers renumbered;
    - `option_index` is the last token of each option line;
    - `answer_index` is the last token, at `<answer>`;
    - nothing is truncated (76 to 124 tokens, against max_length 4096).
  - The padded batch-of-8 path agrees with the single-row encode on the
    first 400 rows of each position.
  - Markers are single tokens: `1`-`5` are ids 16-20, and `A`-`E` are ids
    32-36.
  - The engine `analyze_confidence.py --dry-run` ran on the stage-engine
    materialization of each position's config, with only the staging prefix
    moved. All 10 (5 positions x 2 models) gave "Dry run OK" with FIT 4,829 /
    CAL 2,410 / TEST 4,828.
  - Synthetic render example (pointer, IDK at position 2):
    `1. 64 / 2. 54 / 3. I don't know / 4. 74 / 5. 62`.
- **Check 2, recognition smoke on non-PopQA items: PASS (sanity, not a
  gate).**
  - `recognize-smoke` was run twice. The second run came after the timer
    fix and is the one recorded.
  - Letters ` A`-` D` are single tokens (ids 357, 417, 351, 414).
  - The full-vocabulary top-1 token was a letter on 64 of 64 prompts
    (R0-V2 floor 0.95).
  - `pred_letter_index` equals the argmax over the 4 letter logits on 64 of
    64, with 0 ties.
  - Logits were repeat-identical, 32 of 32.
  - Gold was picked on 30 of 32 prompts. Per item, c = 4 on 7 items and
    c = 2 on 1 item ("spider legs"). So 7 of 8 items have c >= 3. The R0-V1
    floor of 0.80 applies to dmcc-known PopQA rows, so this is a sanity
    reading only.
  - Picks per letter: A 7, B 9, C 9, D 7.
  - Exemplar collision, re-run:
    - the harness rule matches 0 of the 12,067 primary rows;
    - no exemplar question is a PopQA question;
    - no exemplar gold answer is a PopQA subject;
    - exemplar options match a gold alias on 27 of all 14,267 PopQA rows,
      all of them `au` = AU. These are the rows dmcc excluded before its
      split; none is a primary row;
    - the distractors Five and Seven are PopQA subjects, as already
      reported;
    - no smoke question is a primary-row question.
- **Check 4, recognition kill-resume drill: PASS.**
  - Ran the real `stage_recognize`, with `cfg()` patched to a sandbox, on
    600 synthetic prompts.
  - The launcher's process group got SIGKILL at 49.6 s, with 61 lines
    written at the snapshot. The container kept running as an orphan.
  - The resume's `docker rm -f` removed the orphan. The resume finished with
    rc 0 in 68.5 s.
  - Result: 600 lines, 600 unique keys, full coverage, and the pre-kill
    snapshot is a byte-identical prefix of the final log.
- **Check 3, timing: MEASURED.**
  - Recognition:
    - steady rate 0.0619 s per prompt (mean; median 0.0603, p99 0.089);
    - first-forward warmup 23 to 34 s per launch;
    - so about 50 min for 48,268 prompts, plus about 1 min of start-up.
      The AMENDMENT's estimate was 15 to 35 min.
  - Engine, one decision pass per model on 2,400 synthetic rows (with phase
    timers from `presign/timed_analyze.py`, which wraps the engine CLI and
    does not edit it):

    | Model | Launch to finish | Steady capture | Probe fits |
    |---|---|---|---|
    | pointer | 9.4 min | 12.6 ms per row | 2 x about 150 s |
    | letter-logit | 8.9 min | 12.6 ms per row | 2 x about 150 s |

  - Cost is dominated by the row-count-dependent probe fits, not by the
    option count. dmcc's two full-size runs on the same 12,067 rows took
    16.7 and 16.8 min. The extra option line adds under 10 s of capture per
    run.
  - Estimate: about 17 min per engine run, so 12 runs take about 3.4 h.
    With recognition, the total is about 4.3 h of GPU time in separate
    stages. Every engine run stays far under the 2 h tool limit.
- **Check 5, digests: PASS, except a gap that exists by design.**
  - The runner Image ID `sha256:b4166dbd...` equals `runtime_image_digest`.
  - The engine image's local repo digest equals `engine.image`.
  - Checkpoint tree digests, computed with `bin/exp`'s own `_path_sha256`,
    match the pins on both the source and a staged copy: pointer
    `e0cc616d...`, letter-logit `3aef07e2...`.
  - `bin\exp.cmd doctor decision-model-idk-option` shows 8 OK and 2 MISSING.
    The missing ones are `scratch/eh_staging/dmio-idk-p0-{pointer,letter-logits}/final_model`,
    which only `stage-engine` creates. `stage-engine` refuses until the
    recognition freeze marker exists, and that comes after sign. So doctor
    cannot pass fully before sign; the digest check above stands in for it.
- **Check 6, dmcc digest pin refreshed: unchanged (mechanical, no protocol
  change).**
  - `label_and_split_counts.json` is committed in dmcc `fe0d0ee54`.
  - `git show fe0d0ee5:<path> | sha256sum` gives `f347db21...`, which
    equals the old working-tree pin.
  - The path has `eol=lf`, so the checkout bytes equal the blob. That means
    `import-dmcc`, which hashes the checkout at run time, verifies the same
    bytes.
  - `import-dmcc` was re-run: 6 of 6 match. Only the comment in cell.yaml
    and the `source` text in experiment.yaml changed, which also
    regenerates the registry.
- **Repo checks.**
  - Cell tests: 44 pass.
  - `bin\exp.cmd validate`: OK. This cell's only warnings are the two
    staged-checkpoint inputs.
  - `regen`: then `regen --check` is up to date.
  - Hook commands, run one by one: all rc 0. `validate_kg` needs
    `core.hooksPath=.githooks`.
- **Environment note.** Launch `tuner.py local-run` from PowerShell, not Git
  Bash. Under Git Bash, MSYS `tar` reads `F:\...` as a remote host, so the
  artifact copy-back failed (`tar: Cannot connect to F:`) and the outputs of
  that one attempt were lost. The rerun from PowerShell worked.

**Needs a PI decision before sign (not chosen here):**

1. **Generation-engine sign gate.**
   - Problem: `bin/exp sign` refuses this cell as drafted. In `exp.py`
     `cmd_sign`, the PI ruling of 2026-08-13 treats type `eval` as
     generation-bearing. Sign then requires either `instrument.engine.name:
     vllm` with a pinned version, or `instrument.engine_exception` with kind
     `parity-locked` or `intervention` and a reason. This cell declares
     `hf-transformers 5.17.0` and no exception.
   - The cell has no generation. Recognition is a new next-token logprob
     surface (HF, batch 1, dmcc's Stage 0 runner image). The decision passes
     are dmcc's engine, unchanged.
   - Neutral options:
     - (a) Declare `engine_exception: {kind: parity-locked, reason: ...}`.
       Several no-generation cells did this, e.g.
       `readout-under-contract-crossing` and `base-refusal-direction-under-contract`.
       The engine runs are dmcc's engine verbatim. Recognition reuses dmcc's
       HF Stage 0 stack, but it is a new surface rather than a regeneration
       of one.
     - (b) Move recognition to vLLM (dmcc's label engine was 0.27.1), with
       letter logprobs from vLLM. That changes the instrument and needs a
       bridge check and a re-smoke. dmcc found that vLLM batch invariance
       is unsupported for the Qwen3.5 GDN layers, and that batched greedy
       output differed on 2 of 20 rows.
     - (c) Another type or a PI waiver. `lab-diagnostic` is not
       generation-bearing, but it does not fit a gated cell.
2. **bf16 letter-logit ties in recognition.**
   - What happens: the worker reads `logits[0, -1].float()`. The LM head
     outputs bf16, so the letter logits (about 21 to 25) are quantized to
     steps of 0.125, and exact ties occur.
   - Evidence:
     - smoke: 0 of 64 prompts tied;
     - synthetic arithmetic (uncertain items): 29 of 600 tied. The tie rule
       sent 19 to A, 8 to B and 2 to C. The gold letter was among the tied
       letters 17 times;
     - 16 of 150 synthetic questions had a tie that involved the gold
       letter. 10 of 150 would land in a different recognition group under
       another tie rule.
   - PopQA unknown rows are the uncertain regime, so ties there may resemble
     the arithmetic case. The registered rule (lowest letter, ties counted
     and reported) is deterministic and is implemented as registered.
   - Neutral options:
     - (a) Keep the registered rule and report ties as planned.
     - (b) Score the 4 letter logits in fp32 from the final hidden state and
       the 4 LM-head rows. This is an instrument change before sign and
       needs a re-smoke.
     - (c) Change the tie rule, e.g. count a tie as not-gold or split
       credit. This is a rule change before sign.
   - Descriptive context: on the uncertain synthetic items, picks leaned
     to A and B (A 229, B 203, C 110, D 58, against 150 gold per letter).
     The cyclic-rotation design already handles this, because pure position
     bias cannot create c = 0 or c >= 3.

### 2026-10-05 (final draft pass): PI decisions - thresholds confirmed; IDK at all five positions

PI decisions, 2026-10-05, before any outcome:

- PI confirmed the drafted thresholds (H1 >= 0.50, H2 <= 0.10, H3 CI > 0,
  the CI-straddle INCONCLUSIVE rule, R0 floors 0.80 / 0.95). No threshold
  changed.
- IDK placement: all five positions instead of one balanced slot. Unit of
  analysis = the question (mean of its 5 pick-IDK indicators); H1, H2, H3
  and H4 use question-level means with question-level cluster-bootstrap CIs;
  H3's CAL cutoff matches the CAL question-level over-IDK rate. New
  descriptive secondary: position bias (pick-IDK by position 1..5, pooled,
  by group, position x group; range >= 0.10 flagged as a caveat on H1/H2).

Applied:

- cell.yaml: `idk_option.positions: [0..4]` (slot seed removed); runs
  restructured to `idk_runs` (one template pair per model, materialized per
  position by run_id substitution) and `noidk_runs`; 12 engine runs.
- The IDK analysis configs and recipes became position-0 templates
  (`dmio-idk-p0-<model>`).
- Harness: `build-idk-rows` writes 5 position files; `stage-engine`
  materializes and records template + materialized digests; `score` is
  question-level (`question_table`, `cluster_mean_ci`, `h3_compare`,
  `position_table`).
- gates.yaml, experiment.yaml (prediction/falsifier wording, staged input
  paths) and AMENDMENT (design, gates, floors, timing, prediction mappings;
  predictions unchanged) updated.
- `build-idk-rows` re-run (no model): 12,067 rows x 5 positions; every
  position's ported split equals dmcc's. Host engine `--dry-run` of a
  materialized position-3 config: OK for both models, FIT 4,829 / CAL 2,410 /
  TEST 4,828.
- Tests: 44 pass.

### 2026-10-05 (latest): engine repinned to e51a802b

- Tuner `e51a802b1229cc399a80163612638523ddeddbb6` (pushed to
  `jev-models-tuner-training-b55d92`) adds `export.cal_rows` /
  `export.fit_rows`. Submodule checked out there; cell.yaml `engine.commit`
  and experiment.yaml `checkpoint.engine` updated; gitlink staged.
- Engine `analyze_confidence.py --dry-run` (host Python, no model load), run
  on copies of `analysis_idk_pointer.yaml` and `analysis_noidk_pointer.yaml`
  with `data.files` pointed at this cell's local rows: both "Dry run OK",
  `export.cal_rows: true` accepted, split counts FIT 4,829 / CAL 2,410 /
  TEST 4,828 (equal to dmcc's).
- Tests, `validate`, `regen --check` and the hook commands re-run (results
  in the orchestrator report).

### 2026-10-05 (later): PI decisions applied (H3 CAL cutoff; orchestrator prediction)

- PI chose the CAL-fit H3 cutoff. All four analysis configs now set
  `export.cal_rows: true`; `collect` refuses an engine output without
  `cal_rows.jsonl`; G0 checks its qids against dmcc's CAL split. H3 is no
  longer NOT-ADJUDICABLE by design. Test added (32 pass).
- The tuner commit adding `export.cal_rows` was NOT yet on
  `origin/jev-models-tuner-training-b55d92` at this entry (fetch shows
  29f7af0c as tip). The engine pin and the submodule gitlink stay at
  29f7af0c until it lands; 29f7af0c rejects the new key, so no engine run is
  possible before the repin.
- Orchestrator prediction recorded verbatim (AMENDMENT frontmatter and
  scoreboard), labelled as the orchestrating AI agent's, after the
  thresholds were written. No threshold changed.
- `bin\exp.cmd validate` OK; `regen --check` up to date; hook commands pass.

### 2026-10-05 (late): draft scaffolded; pre-sign feasibility probe (no model)

Drafter: subagent for the orchestrator. Nothing signed, committed, or run on a
GPU. Branch `amendment-decision-model-idk-option` off `origin/main` @
`e1a0bdf84`, worktree `.worktrees/amendment-decision-model-idk-option`,
scaffolded with `bin/exp new` (type eval).

Predecessor state at drafting: dmcc is signed (`1387e92d`) and run, but its
branch is local only (not pushed, not on `origin/main`), and its results
(AMENDMENT Outcome, `analysis-committed/*`) are uncommitted in its worktree.
This cell does not stack on dmcc's branch; it consumes dmcc's gitignored
artifacts by absolute path + sha256 (cell.yaml `predecessor`).

Submodule: initialized in this worktree (`--reference` to the primary
repo's module store) and checked out at the interim engine pin
`29f7af0c35e3c825d96f770b62f46c60ac4db2b7`, the commit dmcc's signed commit
records as its gitlink. The gitlink therefore shows as modified; it moves again
when the CAL-export engine feature lands (AMENDMENT checklist item 1).

Feasibility probe (allowed and required pre-sign by amendment-vs-lab-notebook.md;
no model loaded, no recognition score, no decision-model output opened):

1. Exemplar collision probe (scratch script, then the harness rule). Y's five
   exemplar questions: none is a PopQA question. Candidate distractors were
   checked against the normalized gold aliases and option texts of all 12,067
   dmcc primary rows. Chosen: Saturn/Neptune/Uranus, Five/Seven/Eight,
   Ag/Fe/Pb, 1918/1939/1950, Kangchenjunga/Mont Blanc/Lhotse; all 0 alias
   hits and 0 option hits. Rejected: Mars, K2, Go, Four, Nine, Ten, Twelve,
   Three, 1941 (PopQA subjects), Al (1 alias hit). Five and Seven are PopQA
   subjects (question text only); kept, reported.
2. `idk_harness.py import-dmcc`: 6 artifacts verified against their pinned
   sha256 and copied to `analysis/dmcc_inputs/`; dmcc committed
   `rows_sha256` equals the rows file; knowledge_by_split equals the expected
   FIT 525/4,304, CAL 268/2,142, TEST 514/4,314.
3. `build-recognition`: 48,268 prompts over 12,067 rows; collision rule
   matched 0 rows (registered expected 0). items sha256
   `761060dcc4db898321c5c9169e1c724dadf7f75528e94ccc8bdf33b863b1f243`.
4. `build-idk-rows`: 12,067 rows; slot counts 2,414 / 2,414 / 2,413 / 2,413 /
   2,413; ported engine split of the IDK rows equals dmcc `splits.json`.
   rows sha256 `0ddbe712b95d33aba671c979cf3b2107aa4643bbf49f11b3770a11682432fb12`.
5. `plan`: resolves every input and prints the GPU argvs; engine HEAD equals
   the pin.
6. Tests: `python -m pytest experiments/decision-model-idk-option/tests -q`,
   28 passed.
7. `bin\exp.cmd validate`: OK once the submodule was initialized (before
   that, an unrelated cell's repository inputs under `synaptic-tuner/` were
   missing). This cell's only warnings are the two staged-checkpoint local
   inputs, which do not exist until `stage-engine`. `bin\exp.cmd regen` then
   `regen --check`: up to date. Hook commands run one by one: all pass;
   `bin/validate_kg.py` passes when `core.hooksPath` is `.githooks` (it fails
   on this machine's WSL-path hooksPath config, which the
   `git -c core.hooksPath=.githooks` commit form overrides).

PI predictions received 2026-10-05 (recorded verbatim in AMENDMENT). They
arrived before the gate thresholds were drafted; threshold provenance is
disclosed in AMENDMENT "Gates".
