# Raw-base AmbigQA boundary readout (pretraining-flavor vs training-warp fork) notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

### 2026-08-11 -- Bookkeeping: AMENDMENT.md header corrected to match machine state

**Tier 3, bookkeeping only, no goalpost implications.** `AMENDMENT.md`'s header claimed a draft/not-signed (or otherwise stale) status that contradicted `experiment.yaml`'s machine state (`status: resolved`), which has read verdict "falsifier not fired, prediction supported" on record. Corrected the AMENDMENT.md frontmatter `status:` field (draft -> resolved) and flagged a missing `## Outcome` section. Follows the precedent set by `gemma-4-e4b-family-atlas/AMENDMENT.md`'s 2026-07-20 header correction. No signed content (question, prediction, falsifier, gates, Outcome) touched.

- (add dated entries as the experiment progresses)

### 2026-08-09T23:10Z Registration (lead-authored, PI-directed)

PI directed this cell on 2026-08-09 after item 26's G7 FAIL, stating the
fork it must separate: "either it's an activation flavored to these
questions pre training then that signal gets warped post training. Or maybe
there is activations for specific other flavors of questions." Prediction,
falsifier, and the ambiguous band are fixed in AMENDMENT.md sections 3-5
BEFORE any GPU verb; the trained comparators (0.6279/0.6349) are committed
constants from item 26 and are reference points, not gates.

Instrument is maximally borrowed to keep the comparison same-instrument:
item 26's screened panel pool (sha b0f93658, 2748 rows re-verified at
registration), its probe-gate module byte-identical to pin ee3f22ee, its
render module, and the same mechinterp-runner image digest item 26's
extraction ran under. The only new file is extract_rawbase.yaml (checkpoint
swap and output dir; recipe body otherwise identical to extract_A1.yaml).

Nothing in this entry is a result. No GPU verb has run.

### 2026-08-09T23:25Z Harness smoke: wrapper reproduces item-26 A1 exactly; module registered pre-run

The pinned item-26 probe module requires --scored-rows and restricts --arm
to A1/A4; a raw base has neither an emitted surface nor an arm identity, so
this cell registers rawbase_probe_fit.py PRE-RUN: it imports
internal_panel_probe_gate (byte-identical to pin ee3f22ee) and reuses its
load_panel_pool, LAYER, singleton-position squeeze (guard reproduced), and
_cv_auroc_with_oof(folds=5, C=0.5, seed=0) unchanged, dropping only the
emitted-margin block that gates.yaml registers as NOT_READ here.

Faithfulness smoke against item 26's existing A1 extraction: mean
heldout_probe_auroc 0.6279, exactly the committed g7_A1.json value. The
fold std differed by 0.0002 (0.0162 vs 0.0164), attributed to solver-level
nondeterminism in the logistic fit; the registered bands read the MEAN
only, so adjudication is unaffected. Wall-clock 4.65 s.

Nothing in this entry is a raw-base result. No GPU verb has run.

### 2026-08-09T23:40Z LAUNCH: raw-base extraction (single GPU verb)

Signed (6 pins). PI directive of 2026-08-09 ("Yes register this mini cell,
a lot of what we've done hinges on this") covers the registration and this
single 5-15 minute extraction; bands were fixed at signing. Invocation
mirrors item 26's stage-6 A1 command exactly (same image digest
sha256:2471502c..., same mounts, same PYTHONPATH render path), with
--model unsloth/Qwen3-4B --revision 64033659d5caf1b8ed7f929b29de705e93a4d468
(local snapshot verified present) and no adapter. Probe fit follows on CPU
via the pinned rawbase_probe_fit.py. One GPU job; queue empty at launch.

Nothing in this entry is a result.

2026-08-09T23:12Z correction: first launch attempt exited immediately with
"unrecognized arguments: --revision" (no model load, no GPU work). The
parser's flag is --model-revision (tuner/cli/parser.py line 561). Relaunched
with the identical command except that flag name. Same pinned revision value.

### 2026-08-09T23:30Z RESULT and gate adjudication

Extraction container eh-rawbase-ambigqa-extract-20260809T231456Z exited 0
after roughly 12 minutes; run log final line reports 2748/2748 answered rows.

Gates (lead verified each against primary artifacts, not the runner report;
there was no runner, the lead ran this cell directly):

- RG0 PASS. Pool sha256 recomputed on disk equals the registered
  b0f93658...48bfd exactly; label recount from the pool file gives
  1245 known + 1503 unknown = 2748.
- RG1 PASS. manifest.json n_rows 2748, n_answered 2748; 2748 anchor
  safetensors files on disk. hidden_dim 2560, layers [35], families
  [anchor], max_new_tokens 1, greedy, matching the recipe.
- RG2 PASS. Provenance JSON line present at the top of the run log with
  image_digest sha256:2471502c...b60a2cf8 equal to the pinned
  experiment.yaml instrument.runtime_image_digest char for char;
  image_git_revision 552775a, torch 2.9.1+cu128, transformers 5.12.1.

M1: heldout_probe_auroc = 0.6338 (5-fold std across folds 0.0104),
L35 anchor, n = 2748 (1245 known / 1503 unknown), protocol
internal_panel_probe_gate._cv_auroc_with_oof unchanged (folds=5, C=0.5,
seed=0). Counts-only JSON copied to
analysis-committed/rawbase_probe_result.json.

Adjudication against the bands fixed at signing:

- 0.6338 <= 0.73: the PREDICTION is SUPPORTED, flavor-specific reading.
- Falsifier (>= 0.85, training-warp) DOES NOT FIRE.
- The open ambiguous interval does not apply.

Fixed comparators for context (not gates): trained A1 0.6279, trained
A4 0.6349. The raw base sits between them, within 0.006 of each. The
raw pretrained base reads the AmbigQA answerability boundary at the
same low level as the trained checkpoints. On this locus and probe
protocol, post-training neither installed nor destroyed AmbigQA
boundary information: the near-0.997 SelfAware readout is flavored to
SelfAware-style unanswerability from pretraining onward, and item 26's
G7 transfer failure is a property of the pretrained representation,
not a training-induced warp.

Emitted-margin sub-check NOT_READ as registered (raw base has no
emitted surface).

Cosmetic runtime note: the run log contains "Installing asciimatics for
terminal animations..." from the tuner's own shared/ui/animations.py
helper, which pip-installs a terminal-animation package into the
ephemeral container layer. It does not touch the model or numeric
stack and the image is unmodified; recorded for completeness.

Proposed verdict one-liner (resolve stamp awaits PI approval):
"Falsifier not fired; prediction supported. The raw pretrained base
reads the AmbigQA boundary at 0.6338, within 0.006 of both trained
checkpoints, so the known-unknown activation is flavor-specific to
SelfAware-style unanswerability from pretraining, and the G7
non-transfer is not a post-training warp."

- 2026-09-01: aggregate data exhaust published (batch 4 of the backfill, task-56c61a; PI-approved in-conversation 2026-09-01). Copy-everything mirror of analysis-committed plus README + PROVENANCE; aggregate shape, no row text, zero exclusions. 3 files / ~4 KB, built at repo commit d1ae66b3.
- HF repo: `professorsynapse/eh-rawbase-ambigqa-boundary-readout` (dataset)
- HF revision: `cd46aeeade1ed93253f59dc865b3d4e37d2b00f6`
