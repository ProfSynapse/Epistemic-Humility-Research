# No-abstention-prompt gated replication (cross-family) notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

### 2026-08-30 (later) — v2 judge lanes CLOSED for llama-3.2-3b and qwen3.5-4b: all 9 shards PASS CG1 on attempt 1 (harness-builder 3)

Executed exactly per the pre-statement below (recorded before any build).
The v1 VOID_CELL_TERMINAL records stand unchanged; everything in this entry
is the v2 instrument, reported alongside, labeled v2.

**llama-3.2-3b v2 pool** (`analysis-committed/llama-3.2-3b/v2/
adjudication_pool_manifest.json`): 5 shards, 3290 core (same core as v1),
267 clear_negative decoys, 20 clear_positive decoys — all 20 drawn from the
cross-family wicr gated-arm source (142 detector_v2-refused candidates of
443 gated rows scanned, same 142 as gemma's independent scan of the same
source), external-positives-seed 20260831, cap 20 reached; the 6 native
random-arm candidates excluded per the pre-stated replacement rule
(`replace_native_positives` recorded in the manifest).

**qwen3.5-4b v2 pool** (`analysis-committed/qwen3.5-4b/v2/
adjudication_pool_manifest.json`): 4 shards, 2536 core (same core as v1),
206 clear_negative decoys, 20 clear_positive decoys — all 20 same-family,
from `qwen35-4b-midband-doubt-snap` `hs20__gated.jsonl` (6174 gated rows
scanned, 2459 detector_v2-refused candidates), external-positives-seed
20260832, cap 20 reached; zero native candidates existed (no
random_direction arm for this family).

**Judges:** 9 fresh context-free subagents (one per shard), rr2-verbatim
rubric + blinded rows only, neutral batch filenames (batch_18..batch_26;
mapping in the session scratchpad only). Every graded file independently
structurally verified (line counts, exact opaque_id set match, no
duplicates, all-boolean) before its sha256 was committed via the pinned
`apply_adjudication.py commit-hash`; id maps read only after all 9 hashes
were committed (unblinding-order guarantee held).

**CG1, attempt 1, all shards PASS — no regrades, no voids:**

- llama-3.2-3b: clear_negative_agreement 1.00 on all 5 shards;
  clear_positive_agreement 1.00 / 1.00 / 0.75 / 1.00 / 1.00 (decoy catch
  19/20 overall). `voided_cells: []`, `n_applied_rows: 3290`.
- qwen3.5-4b: clear_negative_agreement 1.00 on all 4 shards;
  clear_positive_agreement 1.00 / 1.00 / 1.00 / 1.00 (20/20).
  `voided_cells: []`, `n_applied_rows: 2536`.

**Per-arm judged (core-pool, detector_v2-negative rows only) refused_final
counts** (same denominator convention as gemma's entry: core-pool counts,
not `n - detector_v2_refused`; the full merged two-stage rate needs the
detector_v2-refused counts from each family's `grade_report.json` added
back in per cell):

```
llama-3.2-3b v2:
(no_op, confab)                        23/859
(no_op, known_correct_answered)         0/240
(gated, confab)                        75/830
(gated, known_correct_answered)         0/248
(random_direction, confab)             12/866
(random_direction, known_correct_answered) 0/247

qwen3.5-4b v2:
(no_op, confab)                        49/1263
(no_op, known_correct_answered)         0/263
(gated, confab)                       153/760
(gated, known_correct_answered)         2/250
```

Observation consistent with the lead's 2026-08-29 mechanism note (recorded
descriptively, not adjudicated here): with-prompt gated-arm overt-refusal
decoys were caught 39/40 across both families, where the v1 lanes' random/
no-prompt-arm decoys were missed en masse — the judge-sensitivity failure
tracked the decoy source, not the judges.

### 2026-08-30 — PRE-STATEMENT: v2 judge-lane instrument for llama-3.2-3b and qwen3.5-4b (recorded BEFORE any v2 pool build or judge run)

**v2 judge-lane instrument, PI-approved 2026-08-30: identical contract to v1
except planted clear_positive decoys are drawn from with-prompt GATED-arm
overt refusals (raw completion text, refused re-derived via pinned
detector_v2) instead of random/no-prompt-arm detector hits; the v1
VOID_CELL_TERMINAL records stand unchanged and are not relitigated; v2
results are reported alongside, labeled v2.**

Pre-stated mechanics, fixed before building:

- **Replacement, not augmentation.** "Instead of" is implemented literally:
  the v2 pool's clear_positive candidate set is the external gated-arm draw
  ONLY. llama-3.2-3b's 6 native clear_positive candidates (its own
  no-abstention-prompt `random_direction`-arm detector_v2 hits — exactly the
  class the v2 contract excludes) are NOT planted in v2. This is a glue-level
  input change in this cell's own `build_adjudication_pool_from_runlog.py`
  (a new `--external-positives-replace` flag); every pinned function
  (`build_core_and_decoy_candidates`, `carve_decoys`, `build_shards`, ...)
  runs unmodified from the pinned file's own bytes, same library-reuse
  pattern as documented. qwen3.5-4b has zero native clear_positive
  candidates (no random_direction arm in this cell), so replacement and
  augmentation coincide there.
- **qwen3.5-4b v2 source (same-family):**
  `experiments/qwen35-4b-midband-doubt-snap/analysis/runlog/hs20__gated.jsonl`
  (canonical checkout; 6174 rows, all `arm: gated`, hs20 = this family's
  frozen operating point; raw generation field `answer_text` via the
  already-extended out_text-then-answer_text fallback chain). Refused
  re-derived via pinned detector_v2 over that raw text; the source's own
  `semantic_refuse`/`refused` flags are never trusted. Cap 20,
  external-positives-seed 20260832 (recorded; distinct from gemma's and
  qwen3-4b's 20260714 and from every other v2 lane).
- **llama-3.2-3b v2 source (cross-family):** no same-family raw-text
  with-prompt source is known on this host (the hs17 candidates carry no raw
  `out_text` and would be format-distinguishable inside a blinded shard), so
  decoys are sourced from
  `experiments/qwen3-4b-l34-placebo-seed-census/analysis/wicr_decoy_source/rows_with_generation.jsonl`,
  pre-filtered to `arm == "gated"` rows only (443 of 1329) via a
  session-local scratch copy, same as gemma's v2. Label (verbatim, per lead
  instruction): **cross-family (qwen3-4b), with-prompt, gated-arm overt
  refusals; judge-sensitivity control only, excluded from every gate rate.**
  Cross-family sourcing is used because no same-family with-prompt runlog
  with raw completion text survives on this host; the control tests judge
  sensitivity to abstention text, which is family-independent, and the
  planted rows share the identical JSON output contract with core rows.
  NEVER labeled same-family. Cap 20, external-positives-seed 20260831
  (recorded; distinct from all other lanes).
- **Versioning:** both pools are built with `--version-subdir v2`
  (analysis/<family>/v2/shards, analysis-committed/<family>/v2/...); no v1
  artifact (shards, attempt-1 backups, manifests) is overwritten or deleted.
  Pool seed stays 20260714 (provenance consistency with every prior pool in
  this cell); only the external-positive draw seeds are distinct, as
  recorded above.
- **Judges:** fresh context-free subagents, rr2-verbatim rubric + blinded
  shard rows only (opaque_id + text), no experiment name / hypothesis / arm
  labels; graded-file sha committed via the pinned `apply_adjudication.py
  commit-hash` BEFORE any id map is read; CG1 floors unchanged (clear_neg
  >= 0.95, clear_pos >= 0.60, `VOID_REGRADE_ONCE` -> `VOID_CELL_TERMINAL`
  cascade unchanged).

### 2026-08-29 (still later) — gemma/mistral decoy blocker resolved: cross-family planted positives (PI-visible ruling); gemma judge lane CLOSED, PASS

**Blocker (recorded for the record).** Both gemma's own with-prompt source
(`gemma4-e4b-kv-seam-quarantine/analysis/gemma4-e4b/runlog/full/hs15.jsonl`)
and mistral's (`j-space-cross-family-layer-contrast/analysis/mistral-7b-v03/
runlog/full/hs15.jsonl`) carry only canonicalized `grade.answer_value`
extracts, not raw completion text -- same class of gap as llama's hs17
candidate, ruled MOOT by the lead for the same reason. Grepped the entirety
of gemma's experiment `analysis/` tree for any file with an `out_text` or
`answer_text` key; the only hit (`pool_generations.jsonl`) has no `arm`/
`role` fields and is not a per-arm runlog. Did not substitute
`grade.answer_value` for raw text on my own judgment (changes what
detector_v2 scans, and would be format-distinguishable in a blinded shard
against core rows drawn from full raw JSON completions).

**Ruling (lead, PI has visibility, no countermand received).** Both gemma
and mistral's planted-positive decoys are sourced CROSS-FAMILY from
`experiments/qwen3-4b-l34-placebo-seed-census/analysis/wicr_decoy_source/
rows_with_generation.jsonl`, restricted to GATED-arm rows, re-derived
refused via the pinned detector_v2 over raw `out_text` (never trusting the
source's own flag), cap 20 per family, distinct recorded seeds per family.

**Labeling (verbatim, per lead instruction):** cross-family (qwen3-4b),
with-prompt, gated-arm overt refusals; judge-sensitivity control only,
excluded from every gate rate. Cross-family sourcing is used because no
same-family with-prompt runlog with raw completion text survives on this
host (gemma kv-seam-quarantine and j-space-cross-family runlogs carry only
canonicalized `grade.answer_value` extracts); the control tests judge
sensitivity to abstention text, which is family-independent, and the
planted rows share the identical JSON output contract with core rows. NEVER
labeled same-family.

**gemma-4-e4b judge lane, final: PASS.** Pool built as `v2` (never
overwriting the earlier native-only build that reported
`n_clear_positive_candidates: 0`). External source pre-filtered to
gated-arm rows only (443 of 1329 total rows; the pinned instrument's own arm
preference tuple normally tries `random_direction` first, but this call's
source file contains only `gated`-arm rows by construction, so all 20
decoys are drawn from `gated`). Re-derivation via pinned detector_v2 found
142 gated-arm refused candidates (confab 185 + known_correct_answered 258
tracked rows scanned) -- note this differs slightly from the lead's cited
137; using the harness's own re-derived count as the number of record, not
overriding it to match. **Reconciled (lead, same day):** 142 confirmed
correct and the number of record; the lead's 137 counted gated-CONFAB rows
only via the source file's own `semantic_refuse` flags, while this scan
covered gated confab + known_correct_answered tracked rows via the pinned
detector_v2 (137 + 5 = 142) -- the right scope and the right instrument.
Cap 20 reached; external-positives-seed 20260714
(same seed value as qwen3-4b's own external-positive draw; family tag
`gemma-4-e4b_wicr_external` keeps them collision-safe from qwen3-4b's own
draw regardless). Pool: 1 shard, 780 core, 63 clear_negative decoys, 20
clear_positive decoys. Single fresh context-free judge, structurally
verified (863/863 lines, 0 mismatches) before trust: clear_negative_agreement
1.00, clear_positive_agreement 1.00 -> PASS. `n_applied_rows: 780`.

Per-arm judged (core-pool, detector_v2-negative rows only) refused_final
counts:
```
(gated, confab)                    82/140
(gated, known_correct_answered)     5/242
(no_op, confab)                    26/163
(no_op, known_correct_answered)     5/235
```
(Denominators here are core-pool counts, i.e. total minus detector_v2-refused
minus any rows carved out as clear_negative decoys for that arm/role -- not
directly `n - detector_v2_refused`; the full merged two-stage rate needs the
detector_v2-refused counts from the earlier grade_report.json added back in
per cell.)

### 2026-08-29 (mechanism note, descriptive hypothesis only, NOT a verdict; lead-authored, recorded by harness)

Across the four judge-lane results closed so far: qwen3-4b's planted
clear_positive decoys were ALL with-prompt overt refusals (20/20 caught,
including the 15 drawn from the `random_direction` arm of the WITH-PROMPT
`qwen3-4b-l34-placebo-seed-census` source -- "with-prompt" here describes the
source experiment's own system prompt, not this cell's arm label). Both
VOID_CELL_TERMINAL cells (llama-3.2-3b native decoys; qwen3.5-4b's planted
decoys from `qwen35-4b-midband-doubt-snap`'s `random_direction` arm) drew
their failing clear_positive positives from random-direction/no-prompt-arm
detector_v2-refused rows. One reading consistent with this pattern: judges
are not insensitive to genuine with-prompt overt refusals (100% caught where
tested); the failures instead look like detector_v2 over-firing on
hedged/degenerate random-arm text that a context-free human-equivalent judge
does not agree reads as abstention. This is a descriptive hypothesis for
context at resolve, not a re-litigation of any registered void -- both
VOID_CELL_TERMINAL results stand exactly as reported.

### 2026-08-29 (later) — llama and qwen3.5-4b judge lanes CLOSED, both VOID_CELL_TERMINAL; qwen3.5-4b pool built; gemma launch fixed and completed

**llama-3.2-3b judge lane, final.** Native pool (5 shards, 3290 core, 267
clear_negative, 6 native clear_positive decoys, 2/1/1/1/1 per shard).
Attempt 1: shards 01/02 PASS (clear_neg 1.00/1.00, clear_pos 1.00/1.00);
shards 00/03/04 FAIL clear_positive_agreement (0/2, 0/1, 0/1 caught) ->
`VOID_REGRADE_ONCE` per `gates_lib.cg1_evaluate_shard`. Regrade (attempt 2,
fresh opaque ids via the pinned `build_regrade_shard`, regrade_index=1,
seed=20260714, genuinely fresh context-free judges): all 3 again caught 0
clear_positive decoys -> `VOID_CELL_TERMINAL`. Per `apply_adjudication.py`'s
documented `on_second_failure: void_cell_report_straight` cascade, ran ONE
joint apply across all 5 shards (attempt=2 entries for 00/03/04, attempt=1
for 01/02) against the original committed pool manifest, with pool_sha256
updated only for the 3 regraded shards (attempt-1 originals preserved at
`analysis/llama-3.2-3b/shards_attempt1_backup/`, regrade provenance recorded
inline in `analysis-committed/llama-3.2-3b/adjudication_pool_manifest.json`
under `regrade_note`). Final: `voided_cells: ["llama-3.2-3b"]`,
`n_applied_rows: 0` -- shards 01/02's individually-passing rows are excluded
too, exactly as the registered cascade specifies. Real finding (thin
clear_positive decoy pool for this family), reported straight.

**qwen3.5-4b judge lane, final.** PI-approved (lead relay), same contract.
Pool built from this cell's own no-abstention-prompt runlog plus planted
clear_positive decoys from the SAME-FAMILY WITH-PROMPT source
`experiments/qwen35-4b-midband-doubt-snap/analysis/runlog/hs20__{gated,
random_direction}.jsonl` (canonical checkout; hs20 is this family's frozen
operating point per AMENDMENT.md's operating-point table). That source uses
`answer_text` (not `out_text`) for the raw generation field --
`build_adjudication_pool_from_runlog.py`'s `load_external_positives` was
extended with the same `out_text`-then-`answer_text` fallback chain
`load_family_rows` already used for this family's own qwen3.5-4b branch (not
a new invention, matching an existing in-file convention); re-derives
refused via the pinned detector_v2 over that raw text, never trusting the
source's own `semantic_refuse` flag. Selection: 104 random_direction-arm
detector-refused candidates (2459 more from gated-arm, not needed), cap 20,
all 20 drawn from random_direction per the pinned instrument's own arm
preference; seed 20260714. Pool: 4 shards, 2536 core, 206 clear_negative
decoys, 20 clear_positive decoys.

Attempt 1: shards 01/03 PASS (clear_neg 1.00/1.00, clear_pos 0.60/0.60,
exactly at the floor); shards 00/02 FAIL clear_positive_agreement (0.40,
0.20) -> `VOID_REGRADE_ONCE`. Regrade (attempt 2, same mechanism as llama's):
both again scored 0.40 clear_positive_agreement, still below the 0.60 floor
-> `VOID_CELL_TERMINAL`. Same overwrite-in-place + pool-manifest-sha-update +
joint-apply procedure as llama (attempt-1 originals preserved at
`analysis/qwen3.5-4b/shards_attempt1_backup/`). Final: `voided_cells:
["qwen3.5-4b"]`, `n_applied_rows: 0`, including shards 01/03's individually-
passing rows. This is the SECOND family (after llama) to hit
`VOID_CELL_TERMINAL` on the clear_positive leg specifically -- reported
straight as an observation, not interpreted further here (that is the lead's
adjudication to make, not this harness's).

Note: qwen3.5-4b's own detector_v2-only (string+pattern, pre-judge) rates
for the `confab` role stand independently of the voided judge stage and are
unaffected by it: no_op detector_v2_refused 69/1332 (5.18%), gated
detector_v2_refused 572/1332 (42.94%). The LLM-judge second stage that would
normally resolve the detector_v2-negative remainder cannot be added on top
for this cell (adjudication pool voided), so only the string+detector_v2
column is reportable for qwen3.5-4b, not a combined two-stage number.

**Gemma launch: docker symlink-mount fix.** First `run_gemma.py all` launch
failed immediately (`FileNotFoundError` on
`gemma4-e4b-kv-seam-quarantine/analysis/gemma4-e4b/eval_rows.jsonl`): this
worktree's `experiments/gemma4-e4b-kv-seam-quarantine/analysis` is a symlink
to the canonical checkout's analysis dir (shares gitignored generation
artifacts between worktree and canonical), and Docker's
`-v "$(pwd):/workspace"` mount does not resolve symlink targets pointing
outside the mounted volume. Fixed with a second bind mount,
`-v "$CANON:$CANON"` (identical absolute path both sides, no pinned file
touched). Relaunched; extract/generate stages ran correctly after the fix.
Separately, the harness's own background-task tracking for that docker
launch was reported "killed" partway through, but the underlying `docker
run` client process and container were confirmed still alive and actively
generating (GPU 47% util) when checked -- re-attached a plain pid-wait
watcher rather than restarting anything, since the actual run was never
interrupted.

### 2026-08-29 — Judge lane approved; qwen3-4b decoy-source correction; docker context fixed; qwen3.5-4b launched

**PI approved the judge lane in-session, 2026-08-29** (lead relay). Scope:
run the registered two-stage grading (AMENDMENT.md "Grading") to completion
for qwen3-4b and llama-3.2-3b: sharded blind LLM judges over each family's
detector-v2-negative core pool, using the pinned
`abstention-wide-instrument-calibration` instrument
(`detector_v2.py`/`detector_v2_patterns.yaml`/`build_adjudication_pool.py`/
`apply_adjudication.py`, all sha256-verified against `cell.yaml`
`grading.pinned_instrument` before use, never edited) via the same
library-reuse pattern `build_adjudication_pool_from_runlog.py` already
established (pinned functions imported unmodified; only the row-loading glue
around them is this cell's own code).

**Instrument extension: judge-sensitivity clear_positive decoys.** qwen3-4b's
own no-abstention-prompt data has ZERO detector_v2-refused rows in any of
its three arms (confirmed: pool v1 manifest `n_clear_positive_candidates: 0`
of 1329 core rows), so the pinned pool builder's own
`build_core_and_decoy_candidates` — which only ever draws `clear_positive`
candidates from a `random_direction`-arm row that detector_v2 marks refused —
finds nothing to plant, and a shard with zero clear_positive decoys cannot be
CG1-evaluated on the positive-catch side at all. Per PI ruling, an external,
same-family, with-prompt source is grafted in as `pos_cand` input to the
SAME pinned `carve_decoys`/`build_shards` functions (their own bytes,
unedited); this is a judge-sensitivity control only, reported separately
from every gate rate, never pooled with this cell's own core.

**Source-mismatch caught and corrected before building anything.** The
original task brief named `abstention-wide-instrument-calibration`'s "QH"
cell as the source ("same family, with-prompt"). Reading
`abstention-wide-instrument-calibration/cell.yaml` and `sources.py` directly
(not from the brief's prose) showed QH is registered `family: qwen35-4b`
(Qwen3.5-4B, from `qwen35-4b-midband-heldout`) — a DIFFERENT model family
from this cell's `qwen3-4b` (Qwen3-4B). Using QH would have planted
cross-family decoys into qwen3-4b's judge lane while the record called them
same-family. Flagged to the lead before building anything; the lead
independently verified a corrected source and issued this ruling:

> Source: `experiments/qwen3-4b-l34-placebo-seed-census/analysis/
> wicr_decoy_source/rows_with_generation.jsonl` (canonical checkout;
> 1329 qwen3-4b WITH-PROMPT rows, full `out_text` in the identical
> `{"answer","response_confidence"}` JSON format). Selection: re-derive
> refusal with the PINNED detector_v2 over `out_text` (never trust the
> file's own `semantic_refuse` flag); prefer `random_direction`-arm
> detector-refused rows first (the pinned instrument's own clear_positive
> definition), then top up from `gated`-arm detector-refused rows, up to a
> cap of 20; seeded sample, seed recorded. Source arm recorded per row ONLY
> in the gitignored id map — never in the committed pool manifest, which
> stays counts/shas-only per this experiment's containment rule.

Provenance wording for this pool: **same family (qwen3-4b), with-prompt,
sourced from `qwen3-4b-l34-placebo-seed-census` `wicr_decoy_source`
(previously used there as a judged-pass decoy source)**. To keep the
injected rows structurally unable to collide with this cell's own
(cell, row_key, arm) dedup key even if a row_key happens to be shared
across the two experiments' pools, injected rows are tagged with a distinct
`cell` value (`qwen3-4b_wicr_external`) rather than reusing `"qwen3-4b"`;
their true source arm (`random_direction` or `gated`) is preserved
per-row, visible only in the gitignored id map.

Pool v2 build, selection counts, and shard composition: see the immediately
following build-log entry (recorded after the run, not predicted here).

**Llama pool needs NO external plants — hs17 schema question is MOOT.**
The lead confirmed llama's OWN no-abstention-prompt `random_direction` arm
already yields native clear_positive candidates (6, per the v1 build below)
that are EXACTLY the pinned instrument's own definition (placebo-arm
detector-refused rows), zero deviation from the registered mechanism. The
`llama-hs17-direction-specificity` `arm0_baseline.jsonl` candidate
investigated below is explicitly NOT to be used for anything judge-facing
(it carries no raw `out_text`; its rows would be format-distinguishable
inside a blinded shard by that absence alone). Llama's judge lane runs on
its existing v1 pool, right after qwen3-4b's, same context-free contract.

**For later (qwen3.5-4b's own pool, not actioned this entry):** the lead
notes qwen3.5-4b has a natural same-family with-prompt planted-positive
source already staged in canonical:
`experiments/qwen35-4b-midband-doubt-snap/analysis/runlog`. Not used yet;
qwen3.5-4b's own no-abstention-prompt GPU run was still in flight when this
entry was written.

**Docker context was broken on this host, fixed (environment fix, not a
spec change).** `docker context ls` showed the active context as
`desktop-linux` (a Windows named-pipe endpoint), which panics
(`invalid memory address or nil pointer dereference`) under this WSL2 Linux
shell — exactly the failure mode `synaptic-tuner/docker/mechinterp-runner/
README.md` "Run pattern (WSL2 + NVIDIA)" warns about. Ran
`docker context use default` (the native `unix:///var/run/docker.sock`
context); confirmed `mechinterp-runner:tf550-rebuild` present and
`docker info` reports `Runtimes: io.containerd.runc.v2 nvidia runc` with
`Operating System: Docker Desktop` — the README's documented precondition
for `--gpus all` to work. No docker daemon restart, no service-level
change, no sudo used. Gemma's docker launch command is drafted from that
README's canonical run pattern (`--gpus all`, HF cache + repo bind mounts,
`--env HF_TOKEN` pass-through, `mechinterp-runner:tf550-rebuild`,
`python experiments/no-abstention-prompt-gated-replication/run_gemma.py
all`); not yet run (GPU still occupied by qwen3.5-4b).

**qwen3.5-4b launched.** `python3 run_qwen35_4b.py all`, harness-tracked
background process, log `analysis/qwen3.5-4b/run_all.log`. Liveness
independently confirmed (not taken on trust): model loaded onto GPU
(8500 MiB, 41% util) after the initial HF weight fetch, extract stage
progressing normally, no crash signatures. Preflight re-run fresh on this
host immediately before launch: 31/31 `cell.yaml` sha256 pins still PASS.

### 2026-08-28 — Grading crash fixed (harness bug, not spec) + gemma container rebuilt

**Grading crash root-caused and fixed in harness code only.** qwen3-4b's
`run_qwen3_4b.py grade` stage crashed with `AttributeError: module 'grader'
has no attribute '_is_stated_confidence_refusal'` at
`abstention-wide-instrument-calibration/detector_v2.py:64`. Root cause: each
of the four family harness scripts (`run_qwen3_4b.py`, `run_qwen35_4b.py`,
`run_cross_family.py`, `run_gemma.py`) imports a FAMILY-SPECIFIC `grader.py`
early (directly, or transitively via that family's `gen_lib.py`) under the
bare module name `"grader"`, caching it in `sys.modules`. `detector_v2.py`
(pinned instrument) does its own unqualified `import grader`, expecting ITS
sibling (`abstention-wide-instrument-calibration/grader.py`, which defines
`_is_stated_confidence_refusal`) — but Python resolves that import to the
already-cached family-specific module instead, which lacks that function.
Fixed identically in all four scripts' `cmd_grade()` (or `_import_detector_v2`
helper): load the correct sibling `grader.py` explicitly via
`importlib.util`, assert it has `_is_stated_confidence_refusal`, swap it into
`sys.modules["grader"]` only for `detector_v2`'s own import, then restore the
prior binding. `detector_v2.py` itself was NOT edited (pinned instrument,
per standing invariant). Each fix logs the resolved grader path
(`[grade] detector_v2 grader module resolved to: ...`) for auditability.
Regraded qwen3-4b from its existing runlog (pure CPU, no GPU cost) after the
fix; no data was lost or re-generated.

**Gemma container rebuilt.** The original `mechinterp-runner` image gemma's
Stage 5a dose calibration ran under (digest
`sha256:479b7ca7891ab328ce7f04adffb939ef8086e3cf0d87676a3577d1d76cd845c8`) is
unrecoverable on this host (`docker image inspect` -> no such image); the
only locally-available image (`mechinterp-runner:local`) is transformers
5.12.1, not the 5.5.0 Stage 5a ran under. PI ruling: rebuild from an
ISOLATED clone of the tuner commit that produced Stage 5a's image, never the
live submodule, and never fall back to base conda silently.

Procedure: cloned this worktree's `synaptic-tuner` checkout into scratch,
checked out commit `34c89fc4f9d693a6b997422288d820e9c30b4696` there
(detached HEAD, "Merge pull request #149 from
ProfSynapse/fix/mechinterp-runner-transformers-arg" — the Dockerfile's own
default at that commit is `TRANSFORMERS_VERSION=5.12.1`), and built
`docker/mechinterp-runner/` from that isolated tree with
`--build-arg MECHINTERP_RUNNER_GIT_REVISION=34c89fc4f9d693a6b997422288d820e9c30b4696
--build-arg TRANSFORMERS_VERSION=5.5.0` (5.5.0 read from Stage 5a's own
NOTEBOOK entry, not memory). The live `synaptic-tuner` submodule checkout in
this worktree was never touched.

Tagged `mechinterp-runner:tf550-rebuild`, image id `0f4b6fc5193f`
(`sha256:0f4b6fc5193f808b7653437c28ae19e706a631c47c346367146dda0605bc2629`).
Verified: `docker run --rm mechinterp-runner:tf550-rebuild python -c "import
transformers; print(transformers.__version__)"` reports `5.5.0`; the image's
own provenance banner additionally reports `torch 2.9.1+cu128`,
`image_git_revision 34c89fc4f9d693a6b997422288d820e9c30b4696`,
`python 3.10.12`.

This is a REBUILD, not the original digest: base-layer drift (OS packages,
CUDA runtime patch level) versus the exact image Stage 5a ran under is
possible in principle, since the original digest is unrecoverable to diff
against directly. The python-level pins that matter for numerical parity
(torch, transformers, flash-linear-attention, safetensors) match Stage 5a's
own recorded values. Recorded per the PI's explicit instruction, before
using this image for gemma's GPU stage in this cell.

### 2026-08-28 — Launch authorization and harness-build preflight (harness-builder agent)

**PI approved launch in-session 2026-08-28 on the canonical Linux checkout**
(lead relay). Lead's host preflight (relayed): 31/31 `cell.yaml` sha256 pins
verified, pinned JSONs load, render import assertions pass, staged pools
present for all five families.

**Harness-builder's own independent preflight**, run from a dedicated worktree
(`/home/profsynapse/code/ehr-worktrees/no-abstention-run`, branch
`exp/no-abstention-prompt-gated-replication-run`, off `main` at `1ea23af7`,
submodule `synaptic-tuner` initialized at its pinned commit
`6b01834b8192d1d875db9bfce3eaa8fd9e14334c`), via
`experiments/no-abstention-prompt-gated-replication/preflight.py`:

- **31/31 `cell.yaml` sha256 pins PASS**, independently re-verified against
  the artifacts on this host (not taken on the lead's report).
- **render.py import PASS**: the pinned no-abstention render imports cleanly;
  its own module-level assertions (abstention sentence present exactly once
  in the parent prompt, deleting it reproduces the registered no-abstention
  prompt byte-for-byte) fire without error;
  `NO_ABSTENTION_SYSTEM_PROMPT` (376 chars) matches the registered text
  verbatim; `assert_no_think_scaffolding` and `render()` both present.
- **Held-out pool counts: all five families match `cell.yaml` exactly**
  (qwen3-4b confab=185/known=258; qwen3.5-4b confab=1332/known=360;
  llama-3.2-3b confab=872/known=334; mistral-7b-v0.3 confab=1312/known=382;
  gemma-4-e4b confab=168/known=270).
- **One real defect found and fixed (not a spec change).** This worktree's
  git config had `core.symlinks=false`, so the two git-symlinked gemma
  manifests (`gemma4-e4b-kv-seam-quarantine/analysis-committed/gemma4-e4b/
  {split_manifest,eval_pool_manifest}.json`, both mode `120000` pointing into
  `experiments/common/artifacts/jspace-cross-family-gemma4-e4b/`) checked out
  as plain-text files containing the literal relative-path string instead of
  real symlinks, so their sha256 initially mismatched `cell.yaml`'s pins (29/31
  PASS on first run) and `json.load` failed outright. Root-caused (not
  tuned/patched around): set `git config core.symlinks true` in this worktree
  and re-checked out only those two files (`git checkout --
  <the two paths>`); both then resolve as real symlinks to the existing,
  correctly-sized target files under `experiments/common/artifacts/
  jspace-cross-family-gemma4-e4b/` and both sha256 now match `cell.yaml`
  exactly. No parent-experiment file was edited; this was a worktree checkout
  mechanics fix. Swept the rest of `experiments/` for the same failure mode
  (`git ls-files -s` filtered to mode `120000`): only these two symlinks exist
  under `experiments/`, and both are now resolved correctly.

**Lane finding (research task, not a spec change):** the task brief
anticipated a possible local/Modal split across families. Read each cited
parent Outcome's own NOTEBOOK.md for its host/lane before assuming one:
`j-space-midband-write-sweep-qwen3-4b` (qwen3-4b) ran via "local launch";
`j-space-cross-family-layer-contrast`'s `run_contrast.py --mode full` runs for
both llama-3.2-3b (PID 1231456) and mistral-7b-v0.3 (PID 1260218) show local
process IDs, no Modal job references; `qwen35-4b-midband-doubt-snap` ran "in
the background, on the local RTX 3090"; `gemma4-e4b-kv-seam-quarantine`'s
Stage 5b full run (the D1/hs15 0.7857/0.011 result `cell.yaml` cites) ran
inside the pinned local Docker image `mechinterp-runner:tf550` (`docker ps`
confirmed), not Modal. The "Modal" mentions found in these notebooks
(`gemma4-e4b-kv-seam-quarantine`'s "Phase B Modal lane"; a Modal
row-text-retention note in `j-space-cross-family-layer-contrast`) refer to
different phases/experiments than the specific operating-point Outcomes
`cell.yaml` cites. Conclusion: **all five families' cited operating-point
generation runs were local-lane**; there is no Modal-only family for this
cell to prepare-and-wait-on. Local RTX 3090 confirmed idle (`nvidia-smi`:
13 MiB / 24576 MiB used, 0% util) before proceeding.

Proceeding to harness build for all five families on the local lane.

### 2026-08-28 — Sign-blocker closure and sign (PI-authorized in session)

The four open items from the probe entry below are closed:

1. **Render pinned.** `render.py` in this directory imports the parent render
   (`experiments/doubt-snap-cross-family-confirmatory/render.py`, sha256
   a5a0b243ea20e70ae62d081fbcdca17f0c298a0a6878ff5698e7752ef3434876) and
   replaces only the prompt global. Import-time assertions enforce that the
   abstention sentence occurs exactly once in the parent prompt and that
   deleting it reproduces the registered no-abstention prompt byte for byte;
   import smoke-tested on this machine. The two-prompt diff, in full:

   REMOVED (the only diff): `If the answer is not known to you, say
   "I don't know the answer" rather than guessing. ` (one sentence plus its
   trailing space, between "Answer the user's question. " and "Return only a
   JSON object...").

2. **Llama random seed pinned:** 910016, the next value in the parent
   census's seed series (910001..910015), disjoint from all 15 used seeds.

3. **Judge instrument pinned** in `cell.yaml` `grading.pinned_instrument`:
   detector_v2.py, detector_v2_patterns.yaml, build_adjudication_pool.py,
   apply_adjudication.py from `experiments/abstention-wide-instrument-
   calibration/`, each sha256-pinned; adjudication contract rr2-verbatim /
   context-free-agent / sharded / decoys both types, per that experiment's
   instrument block.

4. **Gate floors frozen** in `gates.yaml` with derivations inline:
   G1 floor 0.4459 (= 0.5 x qwen3-4b with-prompt lift 165/185 = 0.891892,
   no_op abstention 0 by pool construction); G1b floor 0.3595 (= 0.5 x llama
   with-prompt lift 0.719037 = 635/872 - 8/872); G2 ceiling 0.0698 (= 2 x
   with-prompt cost 9/258 = 0.034884) with adjudicability floor N = 52
   (wilson_upper(0,52) = 0.0688 < 0.0698 <= wilson_upper(0,51) = 0.0700).

PI authorization: prediction, falsifier, and gate constructions were
adjudicated by the PI on 2026-08-28 (recorded in AMENDMENT.md and the session
note); the PI then directed sign and merge in-session ("so sign it for me then
lets pr and merge"). Signed via `bin/exp sign` on the Mac checkout; the GPU
run waits for separate launch approval on the canonical Linux checkout.

### 2026-08-28 — Pre-sign feasibility probe (required by AMENDMENT.md Design)

Performed by the lead session on the Mac checkout. Every value now in
`cell.yaml` was copied from a parent Outcome or committed artifact opened
during this probe; no value came from memory. Verification method: sha256 of
each artifact file plus a `json.load` of every artifact and pool manifest
(structural check, per operating rule 8).

Parent Outcomes opened and read this probe:

- `j-space-calibrated-layer-contrast-qwen3-4b/AMENDMENT.md` Outcome: hs23 is
  the best mid-band site (held-out 165/185 = 0.892 vs hs34 123/185 = 0.665).
- `j-space-midband-dose-calibration-qwen3-4b/AMENDMENT.md` Outcome: absolute
  setpoints hs23=25 (readback 25.0055), directions from
  j-space-midband-write-sweep-qwen3-4b.
- `qwen35-4b-midband-heldout/AMENDMENT.md` Outcome: frozen hs20 operating
  point promoted to a held-out claim; hs_index 20, dose_abs 12.6082
  (= 8 x sigma_c, gain_gated 8.0), loaded verbatim from the resolved ladder
  (`qwen35-4b-midband-doubt-snap`).
- `j-space-cross-family-layer-contrast/AMENDMENT.md` Outcome: llama best mid
  site hs17 (647/872 = 0.7420 PASS); mistral best mid site hs15
  (642/1312 = 0.4893, G1 marginal FAIL on the floor, recorded there as "not a
  collapse"); verdict INCONCLUSIVE at close-out — this cell reports mistral
  descriptively under G3 and relitigates nothing.
- `llama-hs17-direction-specificity/AMENDMENT.md` Outcome: hs17 replicates
  held-out (635/872 = 0.7282) and is direction-specific (effect ratio 8.25,
  K=15 random census seeds 910001..910015).
- `gemma4-e4b-kv-seam-quarantine/AMENDMENT.md` Outcome: D1/hs15 is the best
  below-seam behavioural site (G1 PASS 0.7857, G2 PASS 0.011);
  direction-specificity not established for gemma (hs24/hs25 G3 FAILs per
  that Outcome and `gemma4-e4b-pocket-ladder`'s), and this cell does not
  claim it.

Artifact existence + load checks (all PASS; shas recorded in `cell.yaml`):

- qwen3-4b: `c_hat_hs23.json`, `u_d_hs23.json`, `random_direction_hs23.json`,
  `build_manifest_layers.json` (sigma_c 2.0297737163412064, decoder block 22),
  `dose_calibration_summary.json`. Role check: per the write-sweep
  PROVENANCE.md and `model_lib.py`, `c_hat` is the orthogonalized snap (write)
  direction and `u_d` the doubt (detector) direction; dose law erase_write,
  gain = setpoint / sigma_c.
- qwen3.5-4b: `directions/hs20/{c_hat,u_d}.json`, `build_manifest.json`
  (Qwen/Qwen3.5-4B rev 851bf6e8, sigma_c 1.576023489724997, tau_frozen
  -0.5897 recorded but NOT reused: threshold refits under the new prompt).
- llama-3.2-3b: `layers/hs17/{c_hat_hs17,u_d_hs17}.json`,
  `build_manifest_layers.json`, `dose_calibration_summary.json`
  (selected_doses.hs17 = 4.954897429720482 = ratio 0.361 x median_norm
  13.7255).
- mistral-7b-v0.3: `layers/hs15/{c_hat_hs15,u_d_hs15}.json`,
  `build_manifest_layers.json`, `dose_calibration_summary.json`
  (selected_doses.hs15 = 3.7646132819167275).
- gemma-4-e4b: `layers/hs15/{c_hat_hs15,u_d_hs15}.json`,
  `build_manifest_layers.shallow_ladder.json`,
  `dose_calibration_summary.shallow_ladder.json` (selected_doses.hs15 =
  173.65765096701432; cross-checked equal to
  `full_summary.shallow_ladder.json` layers.hs15.dose_target).

Frozen held-out pool checks (all manifests exist and `json.load`; held-out
counts match the parent Outcomes exactly):

- qwen3-4b: `experiments/common/doubt-gated-caution-tighten-heldout-split/
  split_manifest.json` — confab 185, known_correct_answered 258.
- qwen3.5-4b: `qwen35-4b-midband-heldout/analysis-committed/
  heldout_rows_manifest.json` — confab 1332, known_correct_answered 360.
- llama-3.2-3b: cross-family `reused_rows_manifest.json` — held-out confab
  872, known 334 (with `verified_sha256` of its own upstream reuse).
- mistral-7b-v0.3: cross-family `reused_rows_manifest.json` — held-out confab
  1312, known 382.
- gemma-4-e4b: kv-seam `split_manifest.json` — held-out confab 168, known 270
  (own fresh mine, `eval_pool_manifest.json` also pinned).

Question text is not in the repo (public-repo containment): pools reference
rows by id; row text stages privately per the parent cells' containment rules.
The run host (canonical Linux checkout) already holds the staged pools; the
launch preflight re-verifies the staging shas there before any GPU work.

Open items that BLOCK sign (left as TO_PIN_AT_SIGN in `cell.yaml`):

1. Pin this cell's `render.py` and record the two-prompt diff here (the
   deleted abstention sentence must be the only diff).
2. Pin the llama single-seed random-direction seed (no committed artifact;
   the parent census generated directions from seeds at run time).
3. Pin the exact sharded-judge configs (abstention-wide-instrument-calibration
   lineage).
4. Freeze G1/G1b numeric floors in `gates.yaml` from the parent with-prompt
   lifts, with derivations.
