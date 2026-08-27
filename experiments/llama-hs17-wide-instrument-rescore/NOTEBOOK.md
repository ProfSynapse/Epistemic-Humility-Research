# Llama hs17 wide-instrument regeneration and re-score notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

### 2026-08-27 — recovery re-run COMPLETE: equivalence bar PASS, blind verdicts re-attributed

The 17-arm regeneration completed on the local RTX 3090 (exit 0, all 17
arms, exact registered row counts 1206/1206/872x15, zero missing out_text,
no crash-resume duplicates this time). Pre-registered equivalence bar PASS
on both prongs: (1) re-scored arm1 narrow clean_tighten reproduces WR-G1
637/872 bit-exactly (rate, Wilson CI identical); (2) the re-run generation
manifest matches the committed original on every count and flag — the only
diffs are 11 readback means at <= 5e-5 (GPU numerics; 5 dosed arms
reproduced bit-identically). Random arms show narrow-count drift in 9/15
seeds (greedy near-tie flips under numerics), which is why verdict
re-attribution is per-row by exact text, never positional.

Blind-lane recovery: the 19 shard pool+graded scratchpad copies survived;
all 19 graded files sha256-authenticate against the pre-unblinding committed
hashes (adjudication_graded_manifest.json, 19/19). Copies secured under this
cell's gitignored analysis/llama-3.2-3b/recovered_blind_lane/.

Re-attribution over the 15,492 re-run rows: 1,357 detector_v2-flagged (no
adjudication needed), 12,517 joined to a unique blind verdict by exact text
match (arm0/arm1 join at 100 percent of their adjudication population),
1,461 text-drift nulls (all in random arms), 157 conflicting-verdict nulls
(30 distinct texts graded inconsistently across pool duplicates); every null
carries a machine-readable reason. Cross-check: recomputed wide-confab
counts from re-run flags + joined verdicts give arm0 130/872 and arm1
686/872 vs the committed 136/872 and 687/872 — deltas fully accounted for by
drift + withheld conflicts; committed gate numbers remain the numbers of
record, untouched.

Row-level dataset built (rows shape, cell llama32_3b_instruct: 14,824
full-text kuq rows + 668 text-free triviaqa/popqa rows, zero excluded, 19
MB), verify_exhaust PASS twice (before and after adding the recovery
provenance section to the card). Upload pending the dry-run card approval;
the tool-permission classifier blocked this session from running
upload_exhaust.py, so the upload will be run by the user or after a
permission grant — never routed around.

### 2026-08-26 — DATA-LOSS INCIDENT and user-approved recovery re-run (LAUNCHED)

Incident: after PR #562 merged, the lead removed the experiment's worktree
with `git worktree remove --force` before the row-level exhaust was staged,
destroying the sole copy of the gitignored `analysis/` tree (runlogs with
generation text, scored rows, shard id maps, id salt). Root cause: the
post-merge harvest hook never fired because main was synced with `git pull
--rebase` (rebase path fires post-rewrite, which did not exist), and nothing
guarded the removal. Committed evidence and the published aggregate exhaust
were unaffected; the resolved verdict is untouched. Structural fix merged as
PR #564 (post-rewrite harvest hook, scoped fail-closed `--check --worktree`,
PreToolUse removal guard, pr-workflow HARVEST BEFORE REMOVE step).

Recovery re-run (lab-notebook re-run, NOT an amendment; no gate, verdict, or
claim can move): user approved the GPU spend in-session 2026-08-26 ("run
it"). Identical committed harness `run_wide_rescore.py`, identical frozen
pins (all six sha256 re-verified by CPU smoke in the canonical checkout,
`source=already-present-in-this-worktree` for eval rows, KU gate fires
870/1206 exactly as the original generation manifest records), submodule at
the same commit (6b01834b) as the original run, greedy decoding
(do_sample=False, no sampling RNG), local RTX 3090, run FROM the canonical
checkout so the regenerated rows land under main's own gitignored
`analysis/` tree (no worktree to lose). Pre-registered equivalence bar,
stated before launch: the re-scored arm1 narrow clean_tighten count must
reproduce WR-G1's 637/872 exactly and the regenerated arm counts must match
the committed `generation_manifest.json` (original preserved aside for
byte-comparison); only if the run is text-equivalent under that bar will the
surviving blind verdicts (scratchpad pool/graded copies) be re-attributed by
exact text-join for the row-level dataset. If the bar fails, the re-run is
recorded as non-equivalent and the row-level dataset is built from fresh
rows with narrow grades + detector flags only (no reuse of blind verdicts).

### 2026-08-26 — aggregate exhaust published to HF (user-approved)

`professorsynapse/eh-llama-hs17-wide-instrument-rescore`, revision
`e7de12a938f0133e047dafbdb442df62f7ca317a`. 8 files / ~458 KB
copy-everything mirror of `analysis-committed/` (wide-gates report, scored
summary, generation/pool/graded/applied adjudication manifests) + README +
PROVENANCE; verify gate PASS, zero exclusions, no row text. Recorded in
`docs/public-artifacts.md`. Row-level shape is possible for this cell (the
harness persisted text) but stays unpublished pending per-source license
verdicts for the parent row pools.

### 2026-08-26 — full 17-arm regeneration, blinded adjudication, gates, resolved

Generation: 17 arms (arm0 872+334, arm1 872+334, 15 random-seed arms x 872)
on the local RTX 3090, structural text-capture guard active (`runlog_contract`
+ tuner `required_fields`); first launch attempt died pre-evidence on a
missing log dir (mkdir, relaunched clean). WR-G0 checks passed pre-launch
(sha set, wide-pin hashes, 32/32 CPU persistence smoke); every production
record verified text-bearing on first rows. Lead-owned Monitor watch end to
end; one transient CUDA-preamble false alarm adjudicated against the durable
log (zero CUDA text, single healthy GPU process, rows advancing).

Adjudication lane (per `.skills/experiment-runner/reference/abstention-grading.md`):
pool of every detector-negative row across both tracked roles — 13,477 core +
658 clear-negative + 691 clear-positive decoys, 19 shards (~780 rows each),
seed 20260826, fresh salt; pool manifest committed BEFORE dispatch (c955a69c).
19 context-free opus graders, one per shard, private working dirs, rubric
verbatim + edge conventions in every prompt; pattern-classifier use forbidden
and audited (every workdir scanned: reading chunks, agent-authored
TRUE-index write scripts, verify scripts — no matchers). Lead verified every
graded file before hash-commit (line count, positional opaque_id match,
boolean-only, exactly two keys); all 19 sha256 hashes committed before any
unblinding (86c8dc07). CG1: 19/19 PASS attempt 1 (clear-negative 1.000 every
shard; pooled clear-positive 534/691 = 0.7728). Apply produced 13,477
adjudicated core rows, zero voided shards.

Gates: WR-G1 PASS 0.7305, WR-G2 PASS lift 0.6319, WR-G3 PASS ratio 9.34,
WR-G4 NOT-ADJUDICABLE (fired 0/334, as pre-stated). Lead re-derived every
gate number independently from raw scored rows + id maps + the lead's own
graded-file copies — exact match with `wide_gates_report.json`. Verdict and
full table in `AMENDMENT.md` Outcome (Outcome A; both predictors correct).

Run-log anomaly recorded straight: arm0 confab has 25 duplicated row_keys
(897 lines / 872 unique; crash-resume overlap class). Duplicates agree on
all flags; the 24 detector-negative duplicated rows were blind-graded twice
in different shards with 24/24 verdict agreement (unplanned inter-grader
reliability check). Gate populations are unique row_keys; no number moved.
Companion note: `wide_rescore_scored_summary.json` arm0 narrow_confab n is
per-line (897); WR gates and the G3 narrow companion are unaffected (arm0
narrow rate enters descriptively only).

### 2026-08-26 — sign-time feasibility probe (PASS) and sign

Probe performed by direct artifact read in the primary checkout (lead
session), immediately around sign:

- All six frozen-reuse inputs exist and sha256-match the pins carried over
  from `llama-hs17-direction-specificity` `cell.yaml` (u_d, c_hat, gate_fit,
  standardization, dose_source, row_pools — six exact matches).
- Dose verified: `full_summary.json /layers/hs17/dose_target =
  4.954897429720482`.
- Row pools verified by direct read of `reused_rows_manifest.json`:
  confab held_out 872, known_correct_answered held_out 334 (fit splits
  581/222 and fit_only 947 untouched by this cell).
- Wide pins present: `abstention-wide-instrument-calibration/detector_v2.py`
  plus the committed patterns/rubric (hash equality is WR-G0's job at run).
- Adjudication tooling present: census `apply_adjudication.py` lane.
- Random directions reproducible from the registered recipe + seeds
  (910001..910015, identical to the resolved narrow census).
- Self-blinding intact: no result computed; existence/coverage/sha only.

Signed 2026-08-26 (lead + user). Both predictors on record for outcome A
(wide replicates + specific). Engine exception declared (intervention path;
the bridge requires the identical engine as the resolved narrow cell).

- (add dated entries as the experiment progresses)
