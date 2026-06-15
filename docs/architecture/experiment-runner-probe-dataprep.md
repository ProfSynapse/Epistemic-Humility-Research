# Architecture — Experiment-Runner Hidden-State Probe Extraction Capability

> Feature #40: harden the experiment-runner so the merged LoRA hidden-state probe
> (PR #28, commit `360b0055`) is reproducibly runnable on a local lane and a cloud
> (HF Jobs) lane.
> ARCHITECT phase (Task #48). Inputs: PREPARE spike
> `docs/preparation/experiment-runner-probe-dataprep-research.md` + Task #46 HANDOFF.
> Worktree: `.worktrees/experiment-runner-probe-dataprep` @ `origin/main 360b0055`.
> Status: design for CODE — no code written in this phase.

---

## 1. Executive Summary

The merged hidden-state probe (`experiment/phase1/probe/hidden_state_probe.py`) is a
standalone GPU harness with a single CLI entrypoint (`python hidden_state_probe.py
--config <yaml>`). It is **not wired into the experiment-runner at all**: the runner
(`run_matrix.py` / `check_prereqs.py` / `prepare_local_cell.py`) only knows
train/eval cells (`headline|lr_panel|beta_panel|confirm|bridge`) and the cloud
training verb `cloud-pipeline --method ...`. There is **no extraction entrypoint
anywhere**, on either lane.

This document specifies a **new extraction capability** in five components:

1. **LOCAL extraction prep script** (`prepare_extraction_cell.py`) — a sibling of
   `prepare_local_cell.py` that runs the probe harness behind a **fail-closed,
   SKIP-not-abort** prereq gate, without regressing the locked train/eval lane
   gating in `check_prereqs.py`.
2. **Q3 auto-resolver** for `aligned_run_record_id` — derives the run-record id from
   the active arm's adapter path, reading `outcome.adapter_path` back, normalizing
   Windows-absolute paths to repo-relative POSIX, **link-never-mutate**. Lives in
   the **runner**, not the harness.
3. **CLOUD HF-Jobs extraction verb** (Option A, full build) — a new
   `cloud-extract` verb in the `synaptic-tuner` submodule, specified
   **contract-only** here (verb name/args, publish-vs-mount, push-gate sequence,
   runner-side live capability probe). CODE builds it in the submodule through the
   push gate.
4. **`.skills/` canonical source + sync-to-both + drift-check** — the prerequisite
   that must land **before** any extraction code, because the two skill trees have
   diverged with no sync mechanism.
5. **Revision-pin discipline** — pin `model.revision` to a commit SHA before any
   real run; the resolver/gate surface the pin status.

**Build is GPU-free.** Every component (gate, resolver, verb contract, sync, tests)
is implementable and testable without a GPU. The actual extraction **RUN** (local
and cloud) is a deferred, explicitly GPU-required step. The GPU boundary is drawn
in §10.

**Exploratory quarantine is sacrosanct.** Extraction output and any exploratory run
records live in a **separate namespace** (`experiment/phase1/probe/<model_tag>/
hidden_states/...` for tensors; a quarantined run-record dir for any link records),
**never** alongside the signed v0.3 cells in `experiment/phase1/run_records/`.

---

## 2. System Context

```
                       +-------------------------------------------+
                       |         experiment-runner (skill)         |
   operator  -------> |  run_matrix.py / check_prereqs.py /        |
   (GPU-free CLI)      |  prepare_local_cell.py                    |
                       |  + NEW: prepare_extraction_cell.py        |
                       |  + NEW: resolve_aligned_run_record()      |
                       +----------+--------------------+-----------+
                                  |                    |
              materialized config |                    | public CLI verb
              (extraction YAML)   |                    | (link-never-mutate reads)
                                  v                    v
        +-------------------------+--+      +----------+-------------------------+
        | hidden_state_probe.py      |      | experiment/phase1/run_records/     |
        | (merged GPU harness, PR#28)|      | <id>.json  (signed v0.3 spine)     |
        |  parse -> select -> extract|      |  outcome.adapter_path  (READ ONLY) |
        |  -> D-bis finalize gate    |      +------------------------------------+
        +-------------+--------------+
                      | (cloud lane only)
                      v
        +-------------+------------------------------------------+
        |  synaptic-tuner submodule  (NO committed runner files) |
        |  + NEW verb: tuner.py cloud-extract ...  (Option A)    |
        |    feeds by PUBLIC hub dataset.name; contrast adapter  |
        |    published as a hub model repo or mounted            |
        +-------------------------------------------------------+
```

**External boundaries / non-negotiables (carried verbatim from SKILL CLI
Discipline + the lead's standing constraints):**

- **No-pollution rule (SACROSANCT).** The runner talks to the tuner ONLY through
  (1) a materialized config/recipe YAML and (2) the tuner's public CLI verbs. It
  imports NO tuner internals, adds NO committed file under `synaptic-tuner/`, and
  registers NO experiment-specific code there. The only tuner-tree write is
  ephemeral scratch under the already-gitignored `scratch/eh_staging/<id>/`.
- The new **cloud-extract verb is a GENERAL tuner capability** that lives in the
  submodule and ships through the push gate — it is the sanctioned answer to "the
  runner needs a tuner behavior the CLI does not expose: FLAG it as a missing
  general capability, never reach into internals."
- **Never** launch a cost-incurring cloud run / cancel / delete without explicit
  current-conversation user approval.
- **Never loosen the count assertions** (19@4B/9@8B/2 bridge). Extraction adds NO
  matrix cells — it is off the locked matrix entirely.
- **Do not touch** signed PROTOCOL v0.3 / Amendment A execution paths.
- **HF_TOKEN** is env-only, never printed or copied.

---

## 3. Design Principles Applied

| Principle | Application here |
|-----------|------------------|
| **Single Responsibility** | The resolver resolves an id; the gate gates; the prep script orchestrates; the harness extracts. No component does two of these. |
| **Open/Closed** | The extraction capability is added as NEW sibling functions/scripts + NEW gate predicates. The existing `check_cell` / `select_invocation` / count-assertion paths are **extended, never modified** in behavior for train/eval cells. |
| **Dependency Inversion** | The cloud verb is consumed via the tuner's public CLI; the runner depends on the verb's CLI contract, not its implementation. The harness's `ExtractionBackend` Protocol is the existing GPU/stub seam. |
| **Fail-closed** | Every prereq is verified against disk/source reality (not a flag/SHA), mirroring the existing live-probe philosophy. A prereq that cannot be confirmed SKIPs the cell. |
| **Link-never-mutate** | The resolver and the prep script READ run records; they never write into `experiment/phase1/run_records/`. |
| **KISS** | The local prep script reuses `prepare_local_cell.py`'s shape; the resolver is a pure function; no new abstractions beyond what the four responsibilities require. |

---

## 4. Component 1 — LOCAL Extraction Prep Script

### 4.1 Responsibility & placement

A new script **`scripts/prepare_extraction_cell.py`**, sibling to
`prepare_local_cell.py`. It is the narrow launch-prep companion that runs ONE
hidden-state extraction behind a fail-closed gate. It does **not** expand the
matrix (extraction is off-matrix) — it operates on a single extraction config.

**Why a new script, not a new cell-type in `run_matrix.py`:**
`run_matrix.py`'s cell vocabulary (`headline|lr_panel|beta_panel|confirm|bridge`)
is bound to the PROTOCOL v0.3 count assertions (`EXPECTED_COUNT_4B = 19`, etc.).
Adding an extraction "cell" into the expansion would either trip those assertions
or force loosening them — **forbidden**. Extraction is exploratory and off-matrix,
so it gets its own entrypoint that never touches `expand_matrix`. This keeps the
pre-registration guard pristine (Open/Closed).

### 4.2 CLI contract

```
python3 .agents/skills/experiment-runner/scripts/prepare_extraction_cell.py \
    --config experiment/phase1/probe/config/hidden_state_probe.yaml \
    [--run-extraction]        # default OFF: gate + report only, GPU-free
    [--research-repo-root <path>]
```

- **Default (no `--run-extraction`)**: GPU-free. Parse the extraction config, run
  the resolver (Component 2), run the prereq gate (§4.3), print a PASS/SKIP report
  with the resolved `aligned_run_record_id` and the gate findings. Launch nothing.
  This is the CI-testable path.
- **`--run-extraction`**: GPU-required. After the gate PASSes, shell out to the
  harness: `python3 experiment/phase1/probe/hidden_state_probe.py --config
  <effective-config>`. If the gate SKIPs, do **not** invoke the harness; print the
  skip reason and exit 0 (exploratory degrade, not error).

The script never writes into `experiment/phase1/run_records/`. It MAY write a
**quarantined exploratory link-record** (§4.5) — opt-in, off by default for MVP per
the LINK-ONLY steer.

### 4.3 The fail-closed prereq gate (SKIP-not-abort)

A new function in `check_prereqs.py`:

```python
def check_extraction_cell(
    *, config: dict, config_path: Path, research_repo_root: Path,
) -> CellPrereqResult:
    ...
```

It returns the existing `CellPrereqResult` dataclass so the report shape matches
the train/eval gate. **Every failure is a `CellPrereqResult(skip=True, ...)` — NEVER
a `PrereqError`.** Extraction is exploratory; one missing prereq must not abort
anything (there is no "matrix" to abort, and the cell must degrade gracefully).

The gate checks, in order (first failing check decides the skip reason):

| # | Check | Source of truth | Skip reason if absent |
|---|-------|-----------------|-----------------------|
| E1 | `probe_results.jsonl` present on disk for the model_tag | `(<probe_dir> / selection.probe_results)` resolved to an absolute path; `.is_file()` | `"probe_results.jsonl absent for <model_tag> (run the probe tier first; WS-1 output, ~123MB, gitignored)"` |
| E2 | `probe_results.jsonl` provenance matches | stream the first row, read `probe_config_sha`; compare to the value the extraction config expects (see §4.4) | `"probe_results.jsonl probe_config_sha mismatch / contaminated (expected <x>, found <y>)"` |
| E3 | `aligned_run_record_id` resolvable | Component 2 resolver returns a non-None id AND `run_records/<id>.json` exists | `"aligned_run_record_id unresolvable for active arm adapter <path>"` |
| E4 | each active arm's adapter dir contains `adapter_config.json` | resolve the active arm's adapter dir (post-resolver, POSIX-normalized); `(<dir> / "adapter_config.json").is_file()` | `"adapter_config.json missing under active arm adapter dir <dir>"` |

**E1 is the headline gate.** `select_matched_slice` streams `probe_results.jsonl`
and raises `FileNotFoundError` without it (`hidden_state_probe.py:196-200`); the
file is `~123MB`, gitignored (`probe/.gitignore` blanket-ignores
`qwen3-4b-instruct/`), and **absent in the tree today**. The gate catches this
**before** the GPU harness is invoked so the failure is a clean SKIP, not a
mid-run crash.

**E2 is the contamination guard.** The PREPARE addendum upgraded R1 from
"presence" to "presence + provenance": a `probe_results.jsonl` can exist but be
contaminated (e.g. a thinking-mode-ON run). The probe rows carry
`probe_config_sha`; the gate reads the first row's sha and refuses if it does not
match the expected provenance. (The slice rows also carry
`aligned_probe_config_sha`, surfaced by the harness into the manifest at
`collect_static_provenance` — E2 is the launch-time pre-check of that same link.)

**E3/E4 are the adapter-link gates.** E3 ensures the run-record link the manifest
provenance demands is resolvable (the D-bis finalize gate will loud-fail on a null
`aligned_run_record_id` — see §9); E4 ensures the adapter the harness will load
actually has its PEFT config on disk (the real backend reads `adapter_config.json`
GPU-free for `lora_*` provenance, `hidden_state_probe.py:495`).

### 4.4 Provenance-expectation source for E2

The expected `probe_config_sha` is **not** hardcoded. Two acceptable sources;
CODE picks one and documents it:

- **(preferred)** Add an optional `selection.expected_probe_config_sha` field to
  the extraction config. The gate compares the streamed value to it. If the field
  is null, E2 degrades to **presence-only with a WARN** (still SKIP-safe: a null
  expectation cannot fail-closed against an unknown, so it must warn loudly rather
  than silently pass). This keeps the SSOT in the hashed config file.
- **(alternative)** Derive the expectation from the probe tier's own manifest if
  one is colocated. Rejected for MVP: it couples the gate to a second file's
  presence and the probe tier's output layout, which is out of scope.

> **CODE decision needed → resolved here:** use the config field
> `selection.expected_probe_config_sha` (preferred). Null ⇒ presence-only + WARN.

### 4.5 Quarantined exploratory link-record (LINK-ONLY, opt-in)

Per the lead's LINK-ONLY steer, the MVP introduces **no new run-record writer**.
The extraction's provenance already lives in the harness manifest
(`manifest.json`), which records `aligned_run_record_id`, `aligned_probe_config_sha`,
both commit SHAs, and the adapter path. That manifest is the extraction's record.

If a future revision wants a runner-side exploratory link-record, it MUST go in a
**separate quarantined namespace** — proposed `experiment/phase1/probe/
<model_tag>/extraction_run_records/<extraction_id>.json` (under the
already-gitignored probe subtree) — and **never** in `experiment/phase1/
run_records/`. This is documented as a deferred extension, not built now.

> **Provenance of this rule (reconciled §13):** the documented prior behavior is
> that the probe "writes to its own output subtree and links run records by id
> without mutating them" (`probe/README.md:59-64`, `hidden_state_probe.yaml:13-15`).
> A *separate-namespace quarantine RULE* in those exact terms is **NOT** a citable
> documented prior (confirmed absent from `run-records.md` and surviving memory).
> So this separate-namespace quarantine is a **NEW rule this contract PROPOSES**,
> consistent with the documented own-subtree/link-by-id behavior — not a
> pre-existing governance rule. Whether to ratify it as a standing rule is a lead
> call; CODE treats it as this architecture's decision.

### 4.6 No regression to the locked lanes (hard requirement)

`check_extraction_cell` is **additive**. It MUST NOT alter:

- `check_cell` (train/eval gate) signature or behavior;
- the live capability probes (`lane_capability_ready`,
  `cloud_seed_beta_capability_probe`, `local_seed_beta_capability_probe`,
  `cloud_chat_template_kwargs_capability_probe`);
- `PrereqError` (whole-matrix abort) vs `CellPrereqResult(skip)` semantics for
  train/eval cells;
- `FORCE_SEED_BETA_GATE_CLOSED` one-way-CLOSED behavior.

Tests MUST include a regression assertion that `check_cell` for a representative
train cell (e.g. `sft__4b__headline__seed1`) behaves identically before/after this
change (same PASS/SKIP/ABORT for the same inputs). See §11 No-Touch list.

---

## 5. Component 2 — Q3 Auto-Resolver for `aligned_run_record_id`

### 5.1 Responsibility & placement

**Lives in the runner**, not the harness. New function in a runner module
(proposed: a small `scripts/resolve_run_record.py`, importable by both
`prepare_extraction_cell.py` and `check_prereqs.check_extraction_cell`):

```python
def resolve_aligned_run_record_id(
    *, adapter_path: str | Path, run_records_dir: Path, research_repo_root: Path,
    require_verified: bool = True,
) -> ResolveResult: ...
```

**Why the runner and not the harness:** the harness is the merged, signed PR #28
surface and must stay experiment-agnostic and minimal; the run-record schema is a
**runner** concept (`run-records.md`, the runner writes them). The harness already
consumes `aligned_run_record_id` **from its config** (`collect_static_provenance`
reads `prov_block.get("aligned_run_record_id")`, `hidden_state_probe.py:486`). So
the runner RESOLVES the id and writes it into the effective extraction config; the
harness stays unchanged. This respects PR #28's boundary and Dependency Inversion.

### 5.2 Algorithm

Input: the active arm's adapter path (from the resolved extraction config — itself
possibly mirrored from the eval config via the harness's existing
`resolve_eval_arm_adapters`).

1. **Normalize the candidate adapter path** to repo-relative POSIX:
   - replace `\` with `/`;
   - if absolute, strip the `research_repo_root` prefix to make it repo-relative;
   - collapse to the canonical adapter-dir form (the `final_model` dir).
2. **Scan `run_records_dir`** for `*.json`; for each, read `outcome.adapter_path`,
   apply the **same normalization**, and compare.
3. **Match policy:** match on the normalized adapter dir. The verified 1:1 mapping
   holds for `dpo__4b__headline__seed1` (run record and eval config agree). For
   arms where they diverge (see §5.4), the run record is authoritative **only when
   its id is the explicit `aligned_run_record_id`**; the resolver's reverse lookup
   (adapter→id) is a convenience that MUST surface ambiguity rather than guess.
4. **Verified gate (`require_verified=True` default):** only return a match whose
   `outcome.verified is True` AND `outcome.status == "completed"`. If the only
   adapter-path match has `verified=False`, return `ResolveResult(id=None,
   reason="matched <id> but outcome.verified is False")` → E3 SKIPs.
5. **Return** `ResolveResult(id, run_record_path, normalized_adapter_path,
   reason)`. Zero matches ⇒ `id=None`. Multiple matches ⇒ `id=None,
   reason="ambiguous: <ids>"` (fail-closed; never pick one silently).

### 5.3 Path normalization (load-bearing, verified against real data)

Real run records store `outcome.adapter_path` as a **Windows absolute path**:

```
F:\Code\Epistemic-Humility-Research\synaptic-tuner\toolset-training-artifacts\runs\local\4b\sft__4b__headline__seed1\20260614_053221\final_model
```

The eval config stores the analogous path the same way. The resolver MUST
normalize BOTH sides identically before comparison, and MUST emit the resolved id
as a clean string (the id, e.g. `sft__4b__headline__seed1`) — it never writes a
path back. Normalization rules:

- `\` → `/`;
- case-insensitive drive-letter handling is NOT required (compare repo-relative
  suffixes from `.../synaptic-tuner/toolset-training-artifacts/...` onward), which
  side-steps `F:` vs `/mnt/f` host differences entirely;
- compare the **FULL repo-relative suffix INCLUDING the timestamp dir**
  (`.../<run-id>/<timestamp>/final_model`). Tolerance applies ONLY to the host
  prefix (`F:\...` vs `/mnt/f/...`), **NOT** to the timestamp dir. The timestamp is
  load-bearing: it is exactly what distinguishes two training runs of the same
  run-id, and the resolver MUST treat a timestamp difference as a non-match.

> **Decision (disambiguated for CODE):** compare the **repo-relative suffix from
> `synaptic-tuner/toolset-training-artifacts/` onward INCLUDING the timestamp dir**,
> not the absolute prefix and not a timestamp-tolerant run-id-only segment. This
> makes the resolver host-agnostic (Windows `F:\...` vs WSL `/mnt/f/...`) **while
> staying fail-closed on the §5.4 divergence**: a timestamp-tolerant (run-id-only)
> comparison would WRONGLY match sft's older eval-config adapter
> (`.../sft__4b__headline__seed1/20260611_202126/final_model`) to the newer run
> record (`.../20260614_053221/final_model`) and silently link the wrong (older)
> record — the exact failure the resolver exists to prevent. Full-suffix comparison
> reproduces the §5.4 table exactly: sft ⇒ zero-match ⇒ SKIP; dpo ⇒ full match but
> `verified=False` ⇒ SKIP; kto ⇒ explicit-only.
>
> **Secondary disambiguation (defense-in-depth):** if a future state produces
> MULTIPLE run records whose full normalized suffix matches the candidate adapter
> (e.g. duplicate records), that is `Multiple matches ⇒ id=None, reason="ambiguous"`
> per §5.2 step 5 — SKIP, never pick one. Full-suffix comparison makes this case
> rare, but the ambiguity guard remains the backstop.

### 5.4 The two-path divergence the resolver MUST handle (verified finding)

There are **two** adapter-resolution paths and on the real 2026-06-14 records they
**disagree** — CODE must not assume they agree:

| Arm | run record `outcome.adapter_path` ts | eval-config mirror ts | run record `verified` |
|-----|--------------------------------------|------------------------|------------------------|
| sft | `20260614_053221` | `20260611_202126` | True |
| dpo | `20260611_211512` | `20260611_211512` (agree) | **False** |
| kto | `20260613_151337` | (no kto arm in eval config) | True |

Consequences the resolver design encodes:

- **SFT**: the eval-config mirror points at a DIFFERENT (older) adapter than the
  latest verified run record. If the extraction config's active-arm adapter is
  mirrored from the eval config, the reverse lookup finds **zero** run-record
  matches under the full-suffix-including-timestamp comparison (§5.3) — the
  eval-config adapter dir's timestamp (`20260611_202126`) does not equal the run
  record's (`20260614_053221`). The resolver returns `id=None` → E3 SKIPs with a
  clear reason, rather than silently linking the wrong (older) record. **This is
  correct fail-closed behavior**, and is the loud signal that the eval config and
  run records have drifted. (A timestamp-TOLERANT comparison would instead match on
  the shared `sft__4b__headline__seed1` segment and link the wrong record — see the
  §5.3 decision for why full-suffix comparison is required here.)
- **DPO**: paths agree, but `verified=False`. With `require_verified=True` the
  resolver returns `id=None` → SKIP. The operator must re-verify the DPO run (or
  pass `--allow-unverified`, a documented opt-in escape hatch) before extracting.
- **KTO**: cannot be mirrored from the eval config at all (no kto arm). The
  extraction config must set the kto adapter explicitly (`arms[].adapter`), or KTO
  extraction SKIPs at E4/E3.

> **Authoritative rule for CODE:** when `aligned_run_record_id` is set explicitly
> in the config, the harness uses it as-is (link-never-mutate) and the resolver is
> only a *validator* (does `run_records/<id>.json` exist + verified?). When it is
> null, the resolver attempts the reverse adapter→id lookup; **any ambiguity,
> zero-match, or unverified-only match returns None and SKIPs the cell.** The
> resolver NEVER reconciles the eval config back to the run records, and NEVER
> mutates either.

### 5.5 Interaction with the harness's existing mirror

The harness already resolves active-arm adapters by-value from
`eval_arms_source` (`resolve_eval_arm_adapters`, `hidden_state_probe.py:70`). The
runner resolver runs **after** that mirror (it needs the concrete adapter path),
then writes the resolved `aligned_run_record_id` into the effective config's
`manifest_provenance` block before invoking the harness. Order:

```
load extraction config
  -> harness resolve_eval_arm_adapters (mirror adapter path, EXISTING)   [in-process or pre-pass]
  -> runner resolve_aligned_run_record_id(adapter_path)                   [NEW]
  -> write resolved id into effective config.manifest_provenance          [NEW, in a temp/effective config]
  -> gate (E1..E4) against the effective config                           [NEW]
  -> (--run-extraction) invoke harness with the effective config          [GPU]
```

The runner writes a **temporary effective config** (not the committed YAML) so it
never mutates the checked-in `hidden_state_probe.yaml`. The committed config keeps
`aligned_run_record_id: null` as the placeholder + loud-fail contract (§9).

---

## 6. Component 3 — CLOUD HF-Jobs Extraction Verb (Option A, contract-only)

> **Scope:** this section is the CONTRACT (verb name, args, publish-vs-mount,
> push-gate sequence, runner-side live capability probe). CODE BUILDS it in the
> `synaptic-tuner` submodule through the push gate. It is GPU-free to *specify* and
> the verb's non-GPU surface (arg parsing, dataset/adapter resolution, dry-run) is
> GPU-free to *build and test*; the actual cloud extraction RUN is deferred and
> cost-incurring (requires explicit user approval).

### 6.1 The three blockers (from PREPARE) and their resolutions

| Blocker | Resolution |
|---------|------------|
| (a) No extraction verb in `cloud-pipeline` (it only trains) | New **`tuner.py cloud-extract`** verb — a sibling of `cloud-pipeline`, a GENERAL tuner capability, not experiment-specific. |
| (b) `probe_results.jsonl` is large/gitignored/never hub-published; cloud feeds by PUBLIC `dataset.name` only | **Publish the matched extraction SLICE as a small public hub dataset**, not the 123MB raw file. The runner selects the N-known/N-unknown slice locally (GPU-free), and that small slice (≤ a few hundred rows) is hub-published; cloud reads it by name. See §6.3. |
| (c) Contrast adapter is a LOCAL artifact, not a hub id | **Publish the adapter as a hub model repo** (private, by id), OR mount it. Decision: **publish-by-id** (§6.4). |

### 6.2 Verb contract

```
python tuner.py cloud-extract \
    --extraction-config <hub-or-repo-relative extraction yaml> \
    --slice-dataset-name <hub dataset id for the matched slice> \
    --base-model-name <hub model id> \
    --base-model-revision <commit SHA>            # required for cloud (§8)
    --adapter-repo-id <hub model repo id for the contrast adapter> \
    --adapter-revision <commit SHA> \
    --output-dataset-name <hub dataset id to receive the extraction outputs> \
    --yes
```

Mirrors `cloud-pipeline`'s shape (the runner already constructs
`["python","tuner.py","cloud-pipeline","--method",...,"--train-dataset-name",...,
"--yes"]`, `run_matrix.py:419`). The runner's NEW `cloud_extract_invocation()`
builds this command; the dispatcher gains an extraction branch parallel to
`select_invocation` but on the extraction path (NOT inside the matrix
`select_invocation`, which stays train/eval-only).

### 6.3 What gets published vs mounted

- **Slice dataset (published):** the runner runs `select_matched_slice` locally
  (GPU-free — it only streams JSONL and selects keys), producing a small matched
  slice (`n_known + n_unknown` rows, e.g. 32). That slice — NOT the 123MB raw
  `probe_results.jsonl` — is published as a public hub dataset via the tuner's
  existing dataset-publishing skill. This sidesteps blocker (b) entirely: the cloud
  job feeds by `dataset.name` as the data-locality contract requires
  (`lanes.md:52-59`), and we never publish the large gitignored artifact.
- **Adapter (published-by-id):** the contrast adapter (`final_model` dir) is
  published as a **private** hub model repo, pinned by revision SHA, and passed as
  `--adapter-repo-id` + `--adapter-revision`. Rationale: HF Jobs clones only the
  tuner repo into `/workspace/repo` and cannot see local artifacts; a hub model id
  is the lane's native adapter-reference mechanism and keeps the artifact
  revision-pinned for reproducibility. (Mounting was considered and rejected: HF
  Jobs has no persistent local mount of a research-repo artifact.)
- **Base model:** referenced by hub id + revision SHA (same as training).
- **Outputs:** the extraction tensors/manifest/rows are written to an
  `--output-dataset-name` hub dataset (the cloud analog of the local
  `hidden_states/` tree). The runner records that dataset id + revision in the
  extraction manifest (link-never-mutate).

### 6.4 Publish-vs-mount decision (resolved)

> **Decision:** PUBLISH (slice dataset + adapter model repo + output dataset), do
> NOT mount. HF Jobs is a clone-the-tuner-repo lane with no research-repo mount;
> publishing-by-id is the only mechanism that satisfies the data-locality contract
> and keeps every input revision-pinned. All three published artifacts are pinned
> by commit SHA in the manifest.

### 6.5 Push-gate sequence (the cloud-extract launch precondition chain)

A cloud-extract launch is gated by the SAME push-gate discipline the cloud
training lane uses, plus extraction-specific live probes:

1. **Submodule pushed** — `check_prereqs.submodule_pushed(...)` must be True: the
   pinned `synaptic-tuner` commit (now carrying `cloud-extract`) is reachable on a
   remote (HF Jobs checks out the pinned SHA). Until CODE commits + pushes the verb,
   this aborts — correct.
2. **Live capability probe (NEW, runner-side, text-based, no tuner import)** — a
   new `cloud_extract_capability_probe(research_repo_root)` mirroring the existing
   `cloud_seed_beta_capability_probe` philosophy: probe the tuner source for
   - the CLI exposing the `cloud-extract` verb (`tuner/cli/parser.py`);
   - the verb's handler/command builder emitting the extraction args
     (`--adapter-repo-id`, `--slice-dataset-name`, `--output-dataset-name`).
   This **never trusts a flag or SHA** — the capability lands as working-tree edits
   before commit, so a version string would lie (same rationale as the seed/beta
   gate, `check_prereqs.py:141-171`). False ⇒ the cloud-extract path SKIPs (it is
   exploratory) — NOT a whole-matrix abort.
3. **HF_TOKEN present** — env-only (`hf_token_present()`), never printed.
4. **Slice + adapter + base published** — each referenced artifact resolves on the
   hub (a `hub_dataset_revision` / model-info check); unresolved ⇒ SKIP with a
   clear "publish X first" reason.

**Layering note (mirrors `lanes.md:132-137`):** the capability probe confirms the
verb exists in source; `submodule_pushed` separately confirms the pinned commit is
reachable. Both must hold. So even after CODE makes the probe pass on the working
tree, a cloud-extract launch correctly aborts via `submodule_pushed` until the verb
is committed and pushed.

### 6.6 Off-the-signed-path guarantee

`cloud-extract` is a NEW verb that shares NO code path with `cloud-pipeline`'s
training execution or the signed v0.3 / Amendment A training recipes. It reads an
extraction config + published artifacts and runs the forward-only extraction. It
writes to an extraction output dataset, never to the training run-record spine.
CODE MUST keep the verb's module separate from the training handlers in the
submodule (the auditor/security reviewer should verify no training path is reused).

---

## 7. Component 4 — `.skills/` Canonical Source + Sync + Drift-Check (PREREQUISITE)

### 7.1 The divergence (re-verified, correcting the PREPARE finding)

PREPARE reported `run_matrix.py` "differ" as a CRLF/rtk false-positive
(byte-identical). **That is wrong.** With CRLF normalized (`tr -d '\r'` +
`sha256sum`, rtk bypassed), the trees genuinely diverge:

| File | `.claude/` vs `.agents/` (CRLF-normalized) |
|------|---------------------------------------------|
| `SKILL.md` | **DIFFER** (18KB vs 40KB — genuine content gap) |
| `scripts/run_matrix.py` | **DIFFER** — `.agents/` has a real bug-fix the `.claude/` lacks (see below) |
| `scripts/prepare_local_cell.py` | **only in `.agents/`** |
| `tests/test_run_matrix.py` | **DIFFER** — `.agents/` has the matching new assertions |
| `config/matrix.yaml`, `reference/*.md`, `scripts/check_prereqs.py`, `tests/conftest.py` | SAME (content) |

The `.agents/` `run_matrix.py` carries two fixes absent from `.claude/`:
- `output_root` interpolation: `{{lane}}` (literal, never interpolated → broken
  output path) → `{lane}` (correct), with matching test assertions;
- Windows-path normalization: `str(staged_rel / train_file)` →
  `(staged_rel / train_file).as_posix()` and `str(path)` →
  `path.as_posix()` for the invocation.

> **Canonical source = `.agents/`.** It is strictly AHEAD: it has the extra script
> (`prepare_local_cell.py`), the bug-fixes, and the fuller SKILL.md. The SKILL.md's
> own Quick Reference table already uses `.agents/skills/...` paths, confirming
> `.agents/` is the live tree.
>
> **rtk gotcha (record for CODE/TEST):** `rtk`-proxied `diff` returns a false
> `[ok] Files are identical` banner even when files differ (same class as the
> documented pytest directory-glob false-negative). **Use `sha256sum` on
> CRLF-normalized content, or bypass rtk, to compare files** — never trust the
> proxied `diff` banner.

### 7.2 Canonical layout

Create a single canonical source tree at repo root: **`.skills/experiment-runner/`**
containing the authoritative copy (seeded FROM `.agents/`):

```
.skills/experiment-runner/
  SKILL.md
  config/matrix.yaml
  reference/{lanes.md, matrix-expansion.md, run-records.md}
  scripts/{check_prereqs.py, run_matrix.py, prepare_local_cell.py,
           prepare_extraction_cell.py, resolve_run_record.py}   # last two NEW
  tests/{conftest.py, test_run_matrix.py, ...}
```

`.claude/skills/experiment-runner/` and `.agents/skills/experiment-runner/` become
**generated mirrors** of `.skills/experiment-runner/`.

### 7.3 Sync mechanism

A new script **`.skills/sync_skills.py`** (or `scripts/sync_skills.py` at repo
root — CODE picks one and documents):

- **`--write`**: copy `.skills/<skill>/**` → `.claude/skills/<skill>/**` and
  `.agents/skills/<skill>/**`, byte-for-byte, **LF-normalized** (strip CRLF on
  write) so no line-ending churn is ever introduced (honoring the content-only-diff
  constraint).
- **`--check`** (default): compare the three trees (CRLF-normalized,
  `sha256`-based — NOT `diff`, per the rtk gotcha) and exit non-zero on any drift,
  printing the drifted files. This is the drift-check.

**SKILL.md path-prefix caveat:** the mirrors are referenced by different path
prefixes (`.claude/skills/...` vs `.agents/skills/...`) inside their own SKILL.md
Quick Reference. Two options; CODE resolves:
- **(preferred)** Keep SKILL.md path-agnostic where possible, OR templatize the
  prefix and have `sync_skills.py --write` substitute the per-tree prefix on copy
  (then `--check` compares post-substitution). This keeps the canonical SKILL.md
  single-source while the mirrors stay self-consistent.
- **(simpler, acceptable)** Canonical SKILL.md uses `.agents/` prefixes; the
  `.claude/` mirror is documented as path-prefixed-for-`.agents` (a known, benign
  cross-reference). Drift-check excludes the prefix lines.

> **Decision:** prefer the templatized-prefix approach so `--check` is exact and
> the canonical source is truly single. If CODE finds templating disproportionate,
> fall back to the documented-prefix exclusion and record it in the HANDOFF.

### 7.4 Drift-check integration

- Add the new scripts (`prepare_extraction_cell.py`, `resolve_run_record.py`) to
  the canonical tree FIRST, then `--write` to both mirrors. This is why the sync is
  a PREREQUISITE: extraction code must be authored in `.skills/` and synced, never
  hand-edited into one mirror.
- `sync_skills.py --check` is the CI/test gate (a test invokes it and asserts exit
  0). This makes "the trees agree" a verifiable invariant, closing the
  no-sync-mechanism gap.

### 7.5 No CLAUDE.md edits

CLAUDE.md is gitignored/absent in worktrees — do NOT create or edit it. If the
sync mechanism would benefit from a pinned note (e.g. "canonical source is
`.skills/`; never edit mirrors directly"), that belongs in the SKILL.md header
and/or a `.skills/README.md`, and is flagged in the HANDOFF for the lead to pin if
desired — NOT written into CLAUDE.md.

---

## 8. Component 5 — Revision-Pin Discipline

The extraction config carries `model.revision: null` with a "SHOULD be pinned to a
commit SHA before the first real GPU run" comment
(`hidden_state_probe.yaml:26-32`). The harness already recovers the resolved
snapshot SHA post-load (`config._commit_hash`) into `base_model_revision`, so
provenance is immutable-when-the-hub-returns-one even at `revision: null`.

**Local lane:** `revision: null` is acceptable for an exploratory local run (the
post-load `_commit_hash` still pins identity). The gate emits a **WARN** (not a
SKIP) when `model.revision` is null, surfacing the reproducibility recommendation.

**Cloud lane:** `--base-model-revision <SHA>` is **REQUIRED** (§6.2). A cloud
extraction with an unpinned base revision is non-reproducible across HF Jobs
checkouts, so the cloud-extract contract makes it a required arg and the runner's
cloud prereq SKIPs if the effective config leaves it null.

> **Decision:** revision pin is a WARN locally, a hard required-arg for cloud.

---

## 9. The D-bis Finalize Gate Contract (preserved, not modified)

The harness's D-bis finalize gate (`validate_manifest(require_populated=True)`,
`hidden_state_probe.py:558`) loud-fails on a null `aligned_run_record_id` on a
`status=ok` extraction — by design (the run-record link is core link-never-mutate
provenance, not relaxable). This architecture **preserves** that invariant:

- The runner resolver (Component 2) FILLS `aligned_run_record_id` into the
  effective config before the harness runs, so a real run reaches the finalize gate
  with the field populated.
- If the resolver returns None, the gate (E3) SKIPs the cell BEFORE the harness is
  invoked — the harness never runs against a null link, so the D-bis gate's
  loud-fail is never reached on a SKIP path.
- The committed config keeps `aligned_run_record_id: null` as the
  fill-before-run placeholder + loud-fail contract. CODE MUST NOT soften the gate
  or pre-fill the committed config.

This is the "preserve the invariant under reality pressure" discipline: fill-before-run
+ loud-fail, never a silent soften.

---

## 10. GPU-Free / GPU-Required Boundary

| Step | GPU? | Component |
|------|------|-----------|
| `.skills/` canonical source + sync + drift-check | GPU-free | 4 |
| Resolver (adapter→id, normalization, verified gate) | GPU-free | 2 |
| Prereq gate E1..E4 (presence, sha, resolvability, adapter_config.json) | GPU-free | 1 |
| Slice selection (`select_matched_slice`, JSONL streaming) | GPU-free | 1/3 |
| Cloud-extract verb: arg parsing, artifact resolution, dry-run | GPU-free | 3 |
| `prepare_extraction_cell.py` default (gate + report) | GPU-free | 1 |
| Publishing the slice/adapter to the hub | GPU-free (network, cost-aware) | 3 |
| **Local extraction RUN** (`--run-extraction` → harness forward) | **GPU-REQUIRED** (deferred until the 3090 frees from the user's KTO run) | harness |
| **Cloud extraction RUN** (`cloud-extract` launch) | **GPU-REQUIRED + cost-incurring** (deferred; explicit user approval) | 3 |

Everything CODE builds and TEST verifies is in the GPU-free rows. The two
GPU-required rows are deferred execution steps gated behind explicit flags
(`--run-extraction`) and explicit user approval (cloud).

---

## 11. Implementation Roadmap & No-Touch List

### 11.1 Development order (dependency-respecting)

1. **Component 4 (`.skills/` sync)** — PREREQUISITE. Seed `.skills/` from
   `.agents/`, build `sync_skills.py` (`--write`/`--check`), sync both mirrors,
   add the drift-check test. Land this FIRST so all subsequent code is authored in
   `.skills/` and synced.
2. **Component 2 (resolver)** — pure function + tests (divergence cases from §5.4
   are the test matrix: sft zero-match, dpo unverified, kto explicit-only).
3. **Component 1 (local gate + prep script)** — `check_extraction_cell` + E1..E4 +
   `prepare_extraction_cell.py` (default GPU-free path) + regression test that
   `check_cell` is unchanged.
4. **Component 5 (revision-pin)** — fold the WARN into the local gate; the cloud
   required-arg into the verb contract.
5. **Component 3 (cloud-extract verb)** — built in the submodule through the push
   gate; runner-side `cloud_extract_capability_probe` + `cloud_extract_invocation`
   + dispatcher branch. Deferred RUN.

### 11.2 No-Touch list (files that MUST NOT change behavior)

Per the spec-completeness discipline (grep the test surface for each in-scope file
stem before editing), CODE must preserve these pins:

- **`experiment/phase1/probe/hidden_state_probe.py`** — merged PR #28 surface. The
  resolver lives in the RUNNER; the harness is consumed as-is via its CLI. Do NOT
  modify the harness to add resolution. (If the harness genuinely needs a hook,
  that is a flag-and-confirm to the lead, not a silent edit.)
- **`experiment/phase1/probe/config/hidden_state_probe.yaml`** — keep
  `aligned_run_record_id: null` (placeholder + loud-fail contract, §9) and
  `model.revision: null` (pin-before-run). The runner writes an EFFECTIVE config
  (temp), never mutates this committed file. (E2 MAY add an optional
  `selection.expected_probe_config_sha` field — additive, default null.)
- **`scripts/check_prereqs.py`** train/eval surface — `check_cell`,
  `lane_capability_ready`, the three capability probes, `PrereqError` vs
  `CellPrereqResult` semantics, `FORCE_SEED_BETA_GATE_CLOSED`. Extraction adds
  `check_extraction_cell` + `cloud_extract_capability_probe` (additive). **Add a
  regression test** asserting `check_cell` is byte-identical in behavior for a
  representative train cell.
- **`scripts/run_matrix.py`** — the count assertions (`EXPECTED_COUNT_4B/8B/BRIDGE`),
  `expand_matrix`, `select_invocation` (train/eval only), bridge cloud-abort.
  Extraction is OFF-matrix; do NOT add an extraction cell to the expansion. Verify
  `tests/test_run_matrix.py`'s count + materialization + bridge-safety assertions
  still pass unchanged.
- **`experiment/phase1/run_records/*.json`** — link-never-mutate. The resolver and
  prep script READ only.
- **Signed PROTOCOL v0.3 / Amendment A paths** — untouched.

> **Pin categories triaged (per the 3-step sweep):** `test_run_matrix.py` carries
> count-assertion pins + materialization-shape pins + bridge-lane-safety pins on
> `run_matrix.py`; `conftest.py` provides the fixtures. The extraction work is
> additive (new files + new functions), so the planned edits PRESERVE every
> existing pin. The one REQUIRED new pin is the `check_cell`-unchanged regression
> test (Component 1) and the `sync_skills.py --check` drift test (Component 4).

### 11.3 Milestones & acceptance

| Milestone | Acceptance |
|-----------|------------|
| M1 sync | `.skills/` exists; `sync_skills.py --check` exit 0 after `--write`; both mirrors byte-identical (CRLF-normalized) to canonical; drift test green. |
| M2 resolver | resolver returns correct id for dpo (verified-gate behavior documented), None+reason for sft-zero-match / dpo-unverified / kto-explicit-only; Windows-path normalization unit-tested with the real `F:\...` string. |
| M3 local gate | `check_extraction_cell` SKIPs (never aborts) on each of E1..E4; `prepare_extraction_cell.py` default path GPU-free, reports PASS/SKIP; `check_cell` regression test green. |
| M4 revision-pin | local WARN on null revision; cloud contract requires the arg. |
| M5 cloud verb | verb built in submodule; `cloud_extract_capability_probe` SKIPs pre-push; push-gate sequence wired; dry-run GPU-free; **RUN deferred**. |

---

## 12. Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|------------|
| Resolver silently links the wrong run record (sft divergence) | High | Fail-closed: zero-match / ambiguous / unverified ⇒ None ⇒ SKIP. Never guess. §5.4. |
| Regressing the locked train/eval gate | High | Additive-only; explicit `check_cell`-unchanged regression test; No-Touch list §11.2. |
| Publishing the 123MB `probe_results.jsonl` to the hub | Med | Publish the small matched SLICE only, not the raw file. §6.3. Never publish the gitignored large artifact. |
| Cloud-extract reusing a signed training path | Med | Separate verb module; off-signed-path guarantee §6.6; auditor/security verify. |
| Skill-tree drift re-opening after sync | Med | `sync_skills.py --check` as a CI/test gate; canonical-source-only authoring rule. |
| rtk false "identical"/"no tests" masking real diffs/failures | Med | Documented gotcha §7.1; compare via sha256 not proxied `diff`; run pytest with explicit file paths. |
| D-bis finalize gate loud-fail on a real run with null link | Med | Resolver fills the effective config before run; E3 SKIPs before the harness if unresolvable; committed config keeps the placeholder. §9. |
| CRLF churn in synced files | Low | `sync_skills.py --write` LF-normalizes; content-only diffs. |
| Cost-incurring cloud RUN launched without approval | High | RUN is deferred behind explicit flags + the standing "explicit current-conversation user approval" rule. |

---

## 13. Ground Truth Reconciled From the Secretary Query

The architect queried the secretary for: (1) hub-publish state of
`professorsynapse/epistemic-humility-phase1`, (2) whether any extraction-on-cloud
verb already exists, (3) PROTOCOL §5 / S5 constraints on an extraction capability,
(4) prior Option-A / publish-vs-mount rulings. The reply landed and is reconciled
below. **Caveat from the secretary:** the prior Epistemic-Humility-Research
pact-memory cohort was LOST this session and only partially re-distilled; where
memory could not ground an answer, the secretary pointed to LIVE file truth
(SKILL.md / PROTOCOL.md), which the architect re-verified.

**(1) Hub-publish state — CONFIRMED FACT (live ground truth).** The hub holds
TRAINING DATA ONLY: the 8 train/dev JSONLs (sft, dpo, kto_congruence,
kto_correctness_safe × train/dev) listed at `SKILL.md:179-184`. NOTHING
probe-related is published — no `probe_results.jsonl`, no `hidden_states`, no
adapters. The only `probe_results.jsonl` mention in the runner (`SKILL.md:323`) is
a contamination-handling note, not a publication. The PREPARE-addendum premise
holds. → §6.3's publish-the-slice + publish-the-adapter-by-id is exactly the
gap-filler; the cloud RUN is correctly deferred until those publishes happen.

**(2) Extraction-on-cloud — CONFIRMED net-new (live ground truth).** No tuner CLI
verb runs hidden-state EXTRACTION on cloud/HF-Jobs. `cloud-pipeline` is
`--method` (train/eval); `run_matrix` cell types are
`headline|lr_panel|beta_panel|confirm|bridge`. The PR #28 MVP is a SEPARATE local
HF-Transformers+PEFT harness (not vLLM, not the tuner cloud lane). Cloud
extraction REQUIRES a new tuner verb in the submodule. → §6's `cloud-extract` verb
is correctly framed as genuine net-new.

**(3) PROTOCOL §5 / S5 — off-path CONFIRMED; the quarantine *rule* is a NEW
proposal here, NOT a cited prior.** Re-verified against live files:
- `experiment/protocol/PROTOCOL.md:498` — §5 is titled "Blockers / needs (before
  any TRAINING run)"; it gates the training/cloud-MATRIX launch and says NOTHING
  about an extraction verb, because extraction is not in the locked v0.3 scope.
- `PROTOCOL.md:37` + `probe/README.md:59-64` document the probing tier as
  exploratory mechanism tooling that "stays OFF the locked PROTOCOL v0.3 headline
  path and the Amendment A / v0.4 track, writes to its own output subtree, and
  NEVER mutates `probe_results.jsonl` or any run record (it links them by id)."
- So "extraction is off-path / not constrained by v0.3" is **confirmed fact**.
- **HOWEVER:** the specific phrasing in §4.5/§1 — a "separate run-record
  **namespace** quarantine rule" — is **NOT a citable documented prior**. The
  secretary grepped `run-records.md` (no quarantine/exploratory/namespace tokens)
  and surviving memory (absent); the architect re-confirmed `run-records.md` has
  none. What IS documented is the weaker, real behavior: the probe writes its own
  output subtree and links run records by id without mutating them
  (`README.md:59-64`, `hidden_state_probe.yaml:13-15`). **Therefore §4.5's
  separate-namespace quarantine for any exploratory link-record is a NEW design
  rule this contract PROPOSES (consistent with the documented own-subtree/link-by-id
  behavior), not a pre-existing governance rule being cited.** CODE should treat it
  as this architecture's decision; if the lead wants it ratified as a standing
  rule, that is a lead call.
- §5 prereqs were pinned in the 2026-06-11 paper-2 session; some may have landed
  since. They gate the TRAINING matrix, not extraction, so they do not block this
  feature — but if a future step touches the training lane, re-verify §5 against
  the current `PROTOCOL.md`.

**(4) Cloud decision history (Option A / publish-vs-mount) — NO surviving memory;
LEAD-HELD.** There is zero pact-memory record of an Option A ruling or a
publish-vs-mount decision (lost cohort or un-harvested current-cycle lead
decisions). Since the lead steered this to contract-only with cloud=Option A, the
**Option-A-full-build and publish-vs-mount decisions are LEAD-HELD current
rulings.** The contract here (§6.4 PUBLISH not mount; §6 Option A verb) ENCODES the
lead's steer; it does not claim a memory prior. Once this contract lands and the
lead accepts, the secretary will harvest these decisions for the next session.

> **Net:** (1) and (2) are stated as confirmed fact in §1/§6. (3) off-path is
> confirmed; the namespace-quarantine specifics are a NEW proposal (flagged in
> §4.5). (4) is lead-held and encoded, not cited. No factual assumption in the
> design was contradicted by the reply — so no flag-and-confirm is required before
> CODE on the four queried items. The one item needing a lead nod is whether the
> §4.5 separate-namespace quarantine should be ratified as a standing rule vs. a
> per-feature design choice (it is currently the latter).

---

## 14. Summary of Decisions CODE Must NOT Re-Make

1. Extraction is a NEW off-matrix script (`prepare_extraction_cell.py`), NOT a new
   `run_matrix.py` cell-type (§4.1).
2. The gate SKIPs (never aborts) on E1..E4 (§4.3); train/eval gate is untouched
   (§4.6).
3. The resolver lives in the RUNNER, not the harness (§5.1); fail-closed on
   ambiguity/zero-match/unverified (§5.4); compares repo-relative POSIX suffixes
   (§5.3).
4. Run records: LINK-ONLY, no new writer; any (deferred) exploratory link-record
   is quarantined in a separate namespace (§4.5) — a NEW rule this contract
   proposes, consistent with documented own-subtree/link-by-id behavior, not a
   cited prior (§13.3).
5. Cloud: PUBLISH (slice + adapter-by-id + output dataset), not mount (§6.4);
   `cloud-extract` verb is off the signed training path (§6.6); gated by
   submodule-pushed + a live capability probe + HF_TOKEN + artifact resolution
   (§6.5).
6. Canonical skill source is `.skills/`, seeded from `.agents/` (the AHEAD tree);
   mirrors are generated; drift-check via sha256 (§7).
7. Revision pin: WARN local, REQUIRED cloud (§8).
8. The D-bis finalize gate is preserved, never softened (§9).
9. Build GPU-free; RUN deferred + approval-gated (§10).
