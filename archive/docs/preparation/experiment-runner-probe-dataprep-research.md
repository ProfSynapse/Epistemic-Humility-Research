# PREPARE — Harden experiment-runner for reproducible hidden-state probe runs

> Feature #40 · Phase PREPARE (experiment-runner-probe-dataprep) · variety 11
> Author: preparer · 2026-06-14 · **PLANNING / RESEARCH ONLY — no code, no config edits**
> Worktree: `.worktrees/experiment-runner-probe-dataprep` (off `origin/main` @ 360b0055)
> Scope guardrails honored: the subsampled `probe_results.jsonl` slice is framed as an
> **EXPLORATORY** artifact (never pre-registered / never headline); no changes proposed to
> the signed PROTOCOL v0.3 / Amendment A execution paths.

---

## Executive summary

The merged hidden-state probe (PR #28) is a self-contained **plain HF Transformers + PEFT
forward harness** that writes to its own output subtree and links run records by id only. It is
NOT wired into the `experiment-runner` skill at all — the runner only knows `train`/`eval`
cells (`headline | lr_panel | beta_panel | confirm | bridge`), and its cloud invocation is
`tuner.py cloud-pipeline --method ...`. There is **no extraction verb, cell type, or lane
entrypoint** for hidden-state extraction anywhere in the runner today.

That gap is the heart of this spike. Concretely:

- **Q1 (subsample feasibility): CONDITIONAL GO.** The frozen split has *abundant* yield (8892
  known / 7103 unknown keys vs. the harness's 16+16 ask), so there is **no 16/16 shortage
  risk**. The real prerequisite is that **`probe_results.jsonl` for `qwen3-4b-instruct` does
  not exist in the tree** (gitignored, ~123 MB, regenerable) and `select_matched_slice` streams
  it for alignment — so extraction `FileNotFoundError`s until that probe-pass artifact is
  (re)generated or staged. The "yield caveat" the lead asked me to quantify resolves to a clean
  GO on the *selection* math and a HARD GATE on *artifact presence*.
- **Q2 (cloud / HF lane): the cloud lane cannot run extraction as-is.** Three independent
  blockers: (a) no extraction entrypoint in `cloud-pipeline`; (b) the data-locality contract
  feeds the container by **public hub dataset name**, but `probe_results.jsonl` is large,
  gitignored, and never published; (c) the trained adapter the extraction contrasts against is
  a local artifact (`runs/local/4b/.../final_model`), not on the hub. I present **3 cloud-target
  options** below rather than picking one, per the lead's directive; the "on HF" ambiguity is
  surfaced explicitly.
- **Q3 (run-record mapping): clean and concrete.** `aligned_run_record_id` → run record →
  `outcome.adapter_path` is a 1:1, already-populated mapping. An `aligned_run_record_id`
  auto-resolver is a small, well-specified addition (read the run record JSON, return
  `outcome.adapter_path`), and it would *strengthen* the link-never-mutate provenance the
  finalize gate already enforces.
- **Q4 (skill-copy sync): the two skill trees have DIVERGED and there is no sync mechanism.**
  `.agents` SKILL.md is 40 KB (operational journal), `.claude` is 18 KB (lean); `prepare_local_cell.py`
  exists ONLY in `.agents`; `test_run_matrix.py` differs. `run_matrix.py` reported as differing
  by `diff -rq` but is **byte-identical** on content read (an rtk/CRLF artifact). This is a
  latent reproducibility hazard: a runner change made in one copy silently misses the other.

**Concrete design direction for the GO/NO-GO (detail in the closing section):** treat the
hidden-state extraction as a **new local-lane-first capability** layered onto the runner the
same way the train/eval cells are — a declarative "extraction cell" that (1) gates on
`probe_results.jsonl` presence + adapter presence (fail-closed, like the existing capability
probe), (2) resolves the adapter via the run-record auto-resolver (Q3), and (3) is **LOCAL-LANE
ONLY for the MVP** (like bridge cells), with cloud deferred behind the three Q2 blockers. Do NOT
fold extraction into the signed v0.3 matrix; keep it in its own exploratory subtree exactly as
PR #28 already does.

---

## Q1 — Subsample feasibility (GO / NO-GO)

### What the harness actually selects

`select_matched_slice` (`archive/experiment/phase1/probe/hidden_state_probe.py:155-189`) builds a
matched known/unknown slice with **leakage-safe, key-only alignment**:

1. Loads frozen keys from `selection.questions_frozen`
   (`../data/qwen3-4b-instruct/questions_frozen.json`).
2. `_select_keys(frozen, "known_question_keys", n_known, selection_seed)` and the unknown
   equivalent draw a deterministic subset (config: `n_known: 16`, `n_unknown: 16`,
   `selection_seed: 20260614`).
3. `_stream_probe_rows` (`:192-217`) STREAMS `probe_results.jsonl` line-by-line, keeping only
   rows whose `probe_pool_row_key` is in the wanted set — it **never whole-loads the ~123 MB
   file**.
4. If any selected frozen key is missing from `probe_results.jsonl`, it raises `ValueError`
   (`:183-188`) — *"the probe tier must have probed these before extraction"*.

### The yield question, quantified

The lead asked me to **quantify the known/unknown yield caveat rather than assert a clean GO.**
Here is the count, read directly from the committed frozen artifact
(`archive/experiment/phase1/data/qwen3-4b-instruct/questions_frozen.json`):

| Pool | Frozen keys available | Harness needs | Headroom |
|------|----------------------:|--------------:|---------:|
| `known_question_keys`   | **8 892** | 16 | 555× |
| `unknown_question_keys` | **7 103** | 16 | 444× |

**There is no yield shortage.** The 16/16 slice is satisfiable many hundreds of times over, and
`questions_frozen.json` is PRESENT and committed (it is the budget-anchor provenance artifact,
force-added past `archive/experiment/phase1/data/.gitignore:23-26`). So the selection math is a clean GO.

### The real gate (this is the NO-GO-until condition)

`probe_results.jsonl` for `qwen3-4b-instruct` is **ABSENT** from the tree:

```
archive/experiment/phase1/probe/qwen3-4b-instruct/   →  only README.md present
ABSENT: archive/experiment/phase1/probe/qwen3-4b-instruct/probe_results.jsonl
```

It is intentionally gitignored as a *large reproducible artifact* and is the WS-1 probe-tier
output (`probe.py` writes it per TriviaQA train-split question; it is checkpointed/resumable,
keyed by `probe_pool_row_key`). Because `select_matched_slice` streams it for alignment, an
extraction run **fails immediately with `FileNotFoundError`** (`hidden_state_probe.py:196-200`)
until it is regenerated (a GPU WS-1 probe pass) or staged from a prior run.

So the honest GO/NO-GO is:

- **GO** on selection feasibility (frozen split has abundant matched known/unknown; deterministic;
  leakage-clean by key).
- **NO-GO-until** `probe_results.jsonl` for the model_tag is present. This is a **data-prep
  prerequisite**, not a design flaw — and it is the single most important thing for the runner to
  *gate on* before launching an extraction cell (fail-closed, exactly like the seed/beta probe).

### Exploratory quarantine (already correct in PR #28)

The harness already isolates its output: it writes to
`archive/experiment/phase1/probe/<model_tag>/hidden_states/<extraction_id>/`
(`experiments/common/configs/phase1-probe/hidden_state_probe.yaml:91-96`,
`output.hidden_states_subdir: hidden_states`), the
`*/hidden_states/` subtree is gitignored (`archive/experiment/phase1/probe/.gitignore:14`), and the
config header states *"EXPLORATORY TIER, NOT a protocol change … writes to its own output subtree
and NEVER mutates run records"* (`:13-15`). The subsampled slice therefore inherits the right
quarantine for free — no separate `model_tag`/output-dir engineering needed. **Recommendation:**
keep the exploratory `extraction_id` namespacing as-is; the runner should write any extraction
run record (if we add one) into a *separate* exploratory record namespace, never into
`archive/experiment/phase1/run_records/` alongside the signed v0.3 cells.

---

## Q2 — Cloud / HF lane mechanics + options

### How the lanes feed data (the data-locality contract, arch §9.2(b.1))

From `reference/lanes.md`:

- **Local lane** (`--lane local`): stage `<method>_train.jsonl`/`_dev.jsonl` from
  `archive/experiment/phase1/data/<model_tag>/` into the tuner's gitignored
  `synaptic-tuner/scratch/eh_staging/<run_id>/`, rewrite the materialized recipe's
  `dataset.local_file` to the tuner-repo-relative staged path, then
  `python tuner.py local-run --job-config <materialized>.yaml --yes`.
- **Cloud lane** (`--lane cloud`): data referenced by **public HF-hub `dataset.name`** (NOT
  `local_file`), because HF Jobs checks out a pushed tuner commit that cannot see ephemeral
  scratch. `check_prereqs` item 3a queries the hub + pins a revision SHA into the run record.
  Invocation: `tuner.py cloud-pipeline --method <m> --train-dataset-name <hub> ...`
  (`run_matrix.cloud_invocation:410-419`).

### Why the cloud lane cannot run extraction as-is — three blockers

1. **No extraction entrypoint.** `run_matrix.py` cell types are
   `headline | lr_panel | beta_panel | confirm | bridge` (`:76`); `select_invocation` only
   emits `local-run` or `cloud-pipeline --method ...` (`:423-440`). The SKILL.md cloud entrypoint
   is `python tuner.py cloud-pipeline ...` (`.agents SKILL.md:98-99`). **There is no extraction
   verb on the tuner CLI that the runner targets.** The harness `hidden_state_probe.py` is a
   research-repo module, not a tuner-repo capability.
2. **The alignment artifact is never published.** `probe_results.jsonl` (~123 MB) is gitignored
   and is not one of the hub-published Phase-1 *training* datasets. The cloud data contract
   publishes `*_train.jsonl`/`*_dev.jsonl` by hub name — not the probe-pass file the extraction
   slice needs. A cloud container literally cannot see it.
3. **The adapter is a local artifact.** The eval config arms point at
   `…\synaptic-tuner\toolset-training-artifacts\runs\local\4b\sft__4b__headline__seed1\…\final_model`
   (`eval/config/eval_smoke_local_4b.yaml:42`) — a local path, not a hub model id. Extraction
   contrasts base vs. this adapter; on cloud it would need the adapter published or re-trained.

### The "on HF" ambiguity — 3 options (NOT picking; lead to choose)

The phrase "runnable on the cloud (HF) lane" is ambiguous between three genuinely different
targets. Tradeoffs:

| Option | What "on HF" means | Pros | Cons / cost |
|--------|--------------------|------|-------------|
| **A. HF Jobs extraction cell** (a true new cloud lane) | A new `cloud-pipeline`-equivalent **extraction** verb on the tuner CLI; runner gains an `extraction` cell that runs on HF Jobs GPUs | Matches existing lane symmetry; scales to many adapters | HIGH: requires a tuner-repo CLI addition (out of this repo's control, submodule_pushed gate), publishing both the adapter AND `probe_results.jsonl` (or the frozen slice) to the hub, new prereq probes. Crosses the no-pollution boundary unless done as a clean public CLI verb. |
| **B. HF-hosted artifacts, local compute** | Adapter + frozen slice pulled FROM the hub, extraction runs on the **local** RTX 3090 | Reuses the working local harness unchanged; only data-prep is "on HF" (publish adapter + a *small* pre-sliced known/unknown file, not the 123 MB full probe results) | MEDIUM: need a publish step for the adapter + a slim slice artifact; still local GPU. Good reproducibility story (anyone can pull the inputs). |
| **C. Local-only for the MVP, cloud deferred** | Extraction is a **LOCAL-LANE-ONLY** cell (like bridge cells), cloud explicitly aborts-loud | LOW cost; ships the reproducible local path now; honest about the three blockers; mirrors the proven `bridge`-cell containment pattern (`lanes.md:61-71`) | Does not deliver cloud extraction; defers A/B to a later spike once the tuner CLI/publish prerequisites land |

**My recommendation (for the GO/NO-GO):** **Option C for the MVP, with Option B as the
named next step.** Rationale: (1) the local harness already works and is leakage-clean; (2)
Option C reuses the *exact* bridge-cell containment idiom the runner already implements and
trusts (a structurally-invalid cloud request aborts loudly, not silently skips); (3) Option B is
the natural reproducibility upgrade (publish the adapter + a slim pre-sliced known/unknown file —
NOT the 123 MB probe results) and can be specified without touching the tuner CLI; (4) Option A is
real but its cost lives in the *submodule* (new tuner verb + push gate) and would be a separate
nested effort. This keeps the MVP shippable and the no-pollution boundary intact.

> **Pending secretary confirmation:** I have queried the secretary for prior cloud-lane /
> hub-publish / PROTOCOL-s5 / extraction-on-cloud decisions. If the secretary reports the 4B
> datasets are already published (`professorsynapse/epistemic-humility-phase1`) and a tuner
> extraction verb is planned, Option B/A becomes cheaper than estimated here — I will fold that
> into the HANDOFF when the reply lands.

---

## Q3 — Run-record mapping (adapter path → run_id auto-resolver)

### The mapping is concrete and already populated

Run records live at `archive/experiment/phase1/run_records/<run_id>.json`. A real completed record
(`dpo__4b__headline__seed1.json`) shows the exact shape:

```
run_id:                 "dpo__4b__headline__seed1"
coordinate:             {arm: dpo, size: 4b, cell_type: headline, seed: 1, override: {}}
outcome.adapter_path:   "…\runs\local\4b\dpo__4b__headline__seed1\20260611_211512\final_model"
outcome.status:         "completed"
```

The harness side already declares the link:
`experiments/common/configs/phase1-probe/hidden_state_probe.yaml:98-114`
(`manifest_provenance.aligned_run_record_id`, *"names the run record this extraction's adapter was
trained by; the harness NEVER writes to it"*), and the finalize gate
`validate_manifest(require_populated=True)` **loud-fails on null** by design (post-remediation,
B2 fixed). Today this id is filled **by hand** before a GPU run.

### The auto-resolver (small, well-specified, strengthens provenance)

An `aligned_run_record_id` auto-resolver is a clean addition with two directions:

- **Forward (recommended):** given `aligned_run_record_id` (e.g. `sft__4b__headline__seed1`), read
  `archive/experiment/phase1/run_records/<id>.json`, return `outcome.adapter_path` (and assert
  `outcome.status == "completed"`). This lets the extraction config name a *run_id* (stable,
  human-meaningful) instead of a brittle absolute Windows path, and the adapter path is resolved
  from the provenance spine — so extraction and the run record can never disagree.
- **Reverse (nice-to-have):** given an adapter path, scan run records for the one whose
  `outcome.adapter_path` matches, return its `run_id` — useful to auto-populate
  `aligned_run_record_id` from the eval config's by-value adapter path
  (`eval_arms_source`), closing the loop the harness already half-builds via
  `resolve_eval_arm_adapters`.

**Caveat to flag for ARCHITECT:** the existing `outcome.adapter_path` values are **absolute
Windows paths** (`F:\Code\…`). A resolver must normalize separators and ideally resolve relative
to the repo/submodule root (the run-record README and `prepare_local_cell.py:101` already do
`.replace("\\", "/")`). Recommend the resolver return a repo-relative POSIX path and let the
backend join it, rather than trusting the stored absolute path verbatim (matches the
data-locality discipline). This is a small, contained change — it does NOT touch run-record
*writing* (link-never-mutate preserved).

---

## Q4 — Skill-copy sync (`.claude` vs `.agents` experiment-runner)

### The two trees have diverged; there is no sync mechanism

`diff -rq .claude/skills/experiment-runner .agents/skills/experiment-runner`:

| File | `.claude` | `.agents` | Status |
|------|----------:|----------:|--------|
| `SKILL.md` | 18 133 B | 40 111 B | **DIFFER** — `.agents` is a fuller operational journal (cloud-smoke history, GPU recovery log, vLLM entrypoint notes, copy-mode workarounds); `.claude` is the lean operator card |
| `scripts/prepare_local_cell.py` | *absent* | 9 057 B | **ONLY in `.agents`** |
| `scripts/run_matrix.py` | 25 164 B | 25 176 B | reported differ by `diff -rq`, but **byte-identical on content read** — size delta is a CRLF/rtk artifact, not a real divergence |
| `tests/test_run_matrix.py` | 39 886 B | 40 058 B | **DIFFER** |
| `config/matrix.yaml`, `reference/*.md`, `tests/conftest.py` | — | — | identical |

I searched both SKILL.md files for any sync/canonical/generated/"do not edit"/mirror marker —
**none exists.** Neither file claims to be the source of truth, and there is no generator,
symlink, or copy script. The `.claude/` tree is what the running agent's Skill loader reads;
`.agents/` is the repo-checked-in copy. They drift independently.

### Why this is a reproducibility hazard (and the design direction)

If we add the extraction capability (Q1/Q2/Q3 work) to one copy, the other silently goes stale —
and because the *running* skill is `.claude/` while the *committed, reviewed* one is `.agents/`,
a reviewer could approve `.agents/` changes that never take effect, or an agent could run
`.claude/` logic that was never reviewed. **Design direction for ARCHITECT:** before any
extraction-cell code lands, pick ONE canonical tree (recommend `.agents/` = the committed,
reviewed source) and establish a sync mechanism — simplest viable: a `check_prereqs`-style test
that asserts the two trees are byte-identical for the script/config files (allowing the SKILL.md
operational-journal divergence to be explicit and intentional), failing CI on drift. This is a
**pre-requisite to hardening the runner**, not part of it — flag it loudly so the divergence is
resolved before, not during, the extraction work.

---

## Risks, constraints, and flags for ARCHITECT

- **R1 (HARD GATE):** `probe_results.jsonl` absence is the true blocker for any extraction run
  (local or cloud). The runner MUST gate on it fail-closed before launching an extraction cell.
- **R2:** The cloud lane has THREE independent blockers (no verb, unpublished alignment artifact,
  local-only adapter). Cloud extraction is a separate spike, not MVP-shippable. Recommend Option C
  (local-only, bridge-cell containment idiom) for the MVP.
- **R3:** Skill-copy divergence (Q4) is a latent reproducibility hazard with NO sync mechanism.
  Resolve canonical-tree + drift-check BEFORE adding extraction code.
- **R4:** Run-record `adapter_path` values are absolute Windows paths; the auto-resolver must
  normalize to repo-relative POSIX. Resolver must NOT mutate run records (link-never-mutate).
- **R5 (scope guardrail):** Everything here stays OFF the signed PROTOCOL v0.3 / Amendment A
  paths. The extraction slice is EXPLORATORY — never pre-registered, never headline. Any
  extraction run record must use a separate exploratory namespace, never
  `archive/experiment/phase1/run_records/` alongside signed cells.
- **R6 (worktree / CLAUDE.md):** CLAUDE.md is gitignored and absent in this worktree; I did not
  create or edit it. No CLAUDE.md-related need arose for this spike — no action required, flagged
  per directive.
- **R7 (no-pollution SACROSANCT):** Option A (cloud extraction verb) would touch the
  synaptic-tuner submodule's public CLI. If pursued, it must be a clean public verb materialized
  via recipe + CLI only — never a private import. Keep this boundary explicit if A is chosen.

---

## Concrete design direction (the GO/NO-GO ask)

**GO**, with the MVP scoped as **Option C (local-lane-only extraction cell)**:

1. **Add an `extraction` capability to the runner, local-lane-only** (mirror the bridge-cell
   containment idiom: a cloud-lane extraction request ABORTS LOUD via both `check_prereqs` and
   `select_invocation`, exactly as `lanes.md:61-71` does for bridge).
2. **Fail-closed prereq gate (R1):** before launching, assert `probe_results.jsonl` for the
   model_tag is present AND the resolved adapter path exists. Missing either → SKIP (recorded),
   not a whole-matrix abort (extraction is exploratory, not a headline cell).
3. **Wire the run-record auto-resolver (Q3 forward direction):** extraction config names an
   `aligned_run_record_id` (a run_id); the resolver reads the run record and returns the
   repo-relative adapter path. This auto-populates the finalize-gate field the harness already
   loud-fails on when null.
4. **Keep the exploratory quarantine (R5):** outputs stay in
   `probe/<model_tag>/hidden_states/<extraction_id>/`; any extraction run record goes to a
   separate exploratory namespace.
5. **Defer cloud (Option B as the named next step):** publish the adapter + a *slim* pre-sliced
   known/unknown file (NOT the 123 MB probe results) to the hub, run extraction on local GPU
   pulling those inputs. Full HF-Jobs extraction (Option A) is a later nested spike gated on a
   tuner-repo extraction verb + submodule_pushed.
6. **PRE-REQUISITE (R3):** resolve the skill-copy canonical-tree + drift-check before any of the
   above code lands.

This ships a reproducible LOCAL extraction path now, keeps the no-pollution and
exploratory-quarantine boundaries intact, and leaves a clean, costed path to cloud.

---

## Addendum (post-secretary, 2026-06-14) — three grounding confirmations

The secretary reported the prior Epistemic-Humility-Research cloud-lane memory cohort was LOST
from the DB and pointed me to LIVE SKILL.md ground truth. I verified each claim directly against
`.agents/skills/experiment-runner/SKILL.md` (not the gist):

1. **Hub-publish is LIVE — but only training data (confirms, does NOT cheapen, Option B).**
   `SKILL.md:179-185`: all 8 Phase-1 train/dev JSONLs are public at
   `professorsynapse/epistemic-humility-phase1` (`sft_train/dev`, `dpo_train/dev`,
   `kto_congruence_train/dev`, `kto_correctness_safe_train/dev`). The cloud-smoke
   `--train-dataset-name professorsynapse/epistemic-humility-phase1` is live/pinned
   (`SKILL.md:157`). **Crucially, the published set contains NO `probe_results.jsonl`, NO
   `hidden_states`, and NO adapters.** So Option B's cost stands exactly as estimated: the
   publishing *pattern is proven and operational* (a real capability, de-risks Option B), but
   the two artifacts extraction actually needs — the trained adapter and a slim known/unknown
   slice — are still unpublished and must be added by an Option-B publish step.

2. **`probe_results.jsonl` can be a CONTAMINATED artifact (sharpens the Q1 R1 gate).**
   `SKILL.md:323` gives explicit guidance to treat `probe_results.jsonl` as *contaminated
   output* under failure/mismatch conditions (archive it, do not reuse). This means the Q1
   fail-closed gate must do more than check *presence* — it must check *provenance*: the
   harness already stamps `probe_config_sha` per row and `select_matched_slice` carries
   `aligned_probe_config_sha`, so the extraction-cell prereq should assert the streamed rows'
   `probe_config_sha` matches the expected pinned probe config, not merely that the file exists.
   A stale/contaminated probe-pass file is a silent-corruption risk of the same class the runner
   already guards against for seed/beta. **Upgrade R1 from "presence gate" to "presence +
   probe_config_sha provenance gate".**

3. **Extraction-on-cloud is a GENUINE net-new finding (not a re-litigation).** The secretary
   has zero surviving memory of anyone discussing GPU hidden-state extraction on the cloud lane;
   the probing MVP (PR #28) is a separate HF-Transformers+PEFT harness, never the tuner cloud
   lane. So "no extraction verb on the cloud lane" is a real gap to confirm as intended scope
   with the team-lead, not a decision being reopened.

**Also confirmed live (unchanged from body):** both lanes are gated by the live seed/beta
capability probe and *"the local probe currently fails on missing beta forwarding"*
(`SKILL.md:84-89`) — relevant only insofar as an extraction cell should NOT inherit the
train/eval seed/beta gate (extraction is a forward-pass, not a trainer invocation); its gate is
the probe_results/adapter presence+provenance gate above, a distinct fail-closed check.
