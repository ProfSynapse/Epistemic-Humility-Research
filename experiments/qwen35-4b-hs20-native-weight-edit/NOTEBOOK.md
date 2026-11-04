# Qwen3.5-4B hs20 native weight edit notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## 2026-11-03 — native Astra fixed proposal and evaluation alignment (unsigned)

The user selected ordinary T3 execution with native Codex transcripts and asked
for one Astra-proposed edit followed by the established evaluation. The custom
transport is parked. Astra proposed one block-19 sparse rank-one construction;
`astra_r1.yaml` records the exact proposed formula, development rule, copied
P-struct/P-rc prompts, datasets and prospective gates. It is not launch authority.
The original six-candidate SOL pilot remains the current old instrument until
this proposed replacement is wired and the unsigned AMENDMENT/manifest revised.
No candidate or evaluation generation has occurred.

Completed native design snapshot archived and hash-verified at
`E:/SynapticResearch/editor-transcripts/01a1a24d-a9ce-75c0-9bee-756558e488f6/design-v1`.
The original native transcript remains in its Codex session location. Hash/count
provenance is in `analysis-committed/astra_design_provenance.json`.

Metadata-only desktop audit confirms the established SelfAware 3,369 and screened
AmbigQA 1,832 files and label counts. Excluding normalized-question evaluation
matches leaves 887 confab and 239 historical known-correct FIT questions, enough
for the fixed 64+64 development capture. The direction-building anchor source pool
contains one SelfAware question and zero AmbigQA questions: exclude that question
from NEW development selection and disclose inherited historical exposure. Retain
the complete benchmarks for comparability; do not claim global unseen status.
No target inference was used by this audit, and no row text/IDs went to Astra.

The existing response-confidence format retry mentions "answer or abstention".
Keep the unchanged retry instrument for comparability and report that affordance;
P-struct identifies the initial prompt condition, not a guarantee that every
possible retry contains zero abstention-related language.

## Entries

- (add dated entries as the experiment progresses)

## 2026-11-03 — pre-sign installed runtime compatibility smoke

This is synthetic infrastructure evidence, not a scientific result. No FIT or
held-out behavior has been generated and this instrument remains unsigned.

- Tuner extension source b11f0604feaabaed8113198ebf0c3dabeeefa8dd; wheel SHA256
  9b47c5a5100b02008e5b69194039f6950d9270ec1bdb690c074725fe6fc25715. PR281.
- Installed EHR host wheel from commit2370db648be8179aefd631ee42251f2fec98996b;
  SHA256 eb00d2f81ae008d7f2a052d51d9e28888076e6d6fd3ff403a1cdb541eeec83af.
  The reusable preflight launcher is from migration commitd17ba650 (PR603).
- Base image sha256:b4166dbd15d0c7d9cad8a07c46be1301dc5941eb4b4d629ae754dc27cb03eb9c.
  Derived image sha256:aaafc29751b932ed6c7532fb34995552202da358e4af2250d74743afb0ccc509.
  Verified that all16base layers precede the two derived layers. The base stack
  remains Torch2.9.1+cu128, Transformers5.17.0 and Pydantic2.12.4; CUDA sees3090.
- Installed-runtime unit checks:285passed,3source-checkout fixtures excluded.
  The first attempt had284passed and4fixture/CWD failures, not arithmetic or
  model failures. Both attempts remain in the private build directory.
- Forward-only actual Qwen3.5-4B smoke:3synthetic prompts, residual hs20 plus
  down_proj inputs at decoder blocks20/21/22, every captured site shape[1,9216].
  use_cache true; per-row capture journal and completed manifest exist.
- Source model shards were materialized and verified on T7 E:. Smoke project:
  /mnt/e/SynapticResearch/preflight/ehr-installed-20261103. Private evidence:
  /mnt/e/SynapticResearch/builds/ehr-runtime-20261103-b11f0604/preflight-evidence.json.
  A text-free copy is in the migration PR's runtime/mechinterp/evidence/.
- Build attempt1 refused a bare local image ID because BuildKit interpreted it
  as a registry name. Attempt2 used a local tag checked against the full base ID;
  layer ancestry verification passed. No model stack upgrade or native-daemon
  workaround occurred.

Pending before sign: complete harness, independent instrument review, actual
native-weight name mapping/readback, zero-patch token parity, batch parity,
export/reload roundtrip, real SIGKILL/resume drill, input/decoy feasibility and
complete persistence declarations. No G0 or behavioral gate is adjudicated yet.


## 2026-11-03 — pre-sign review repairs and guarded runtime

The pre-sign review found an invalid null-classification path. The harness now
makes every non-budget engine refusal an instrument failure. Smoke output keys
are distinct in the shared ledger. Export/token parity gates held-out generation.
Public Git commitments gate grading and unblinding. A frozen 27/30 spot agreement
rule replaces an operator veto. G0 verifies source/runtime/data binding and the
actual kill/resume journals. The instrument remains unsigned; no candidate or
held-out generation has run.

The active runtime is `sha256:35fc50d3e1878710147f5a0251a4d89c39958255263ed71f5d540fc6d88414e9`.
Its base-layer prefix was checked against the pinned b4166dbd image. `pip check`
passes. Engine wheel b884aab4 and host wheel 28511365 are pinned in
`analysis-committed/runtime_manifest.json`. Host CPU tests: 26 passed, including
an owned launcher SIGKILL and inherited writer-lock release. Earlier NOTEBOOK
image/wheel entries describe prior compatibility checks, not this launch.

The review-regression suite checks budget/instrument refusal separation,
smoke accounting, export-order enforcement, real Git commitment checks,
objective spot acceptance, journal validation, and source/model/threshold drift.
Real-model token parity and measured persistence checks are pending.


## 2026-11-03 — attempt1 preserved; measurement repair qualified on CPU

Attempt1 extraction SIGKILL/resume passed4->24 rows in270.8744s. Generation
qualification stopped at the engine smoke gate before any scored row, with
off-target movement0.0018307163 above0.001. No force flag or tolerance change
was used. The frozen binding and aggregate failure are retained in
analysis-committed/run_binding_attempt1.json and attempt1_qualification.json;
private journals and logs remain in the original T7 execution snapshot.

A CPU counterexample showed the actual bf16 hidden tensor remained bit-identical
while readback reported movement0.0253904. The engine used different direction
precision for pre/post measurement. Engine49a6b6b8 fixes only that measurement
basis. All290 MechInterp tests pass, including the regression. The active wheel
is9ef85ba and the rebuilt runtime is a1d3995e; the runtime manifest pins both.
Host26 tests and experiment144 CPU tests pass; the torch-only contract file is
skipped in the CPU host environment. No behavioral gate or tolerance changed.

Remaining review repairs make spot packs/decisions write-once, hide grader
labels from the lead, require a public spot Git commitment, and freeze terminal
adjudication while retaining the registered CG1 regrade. Full FIT baseline
generation now requires sign/preflight admission. Drill/parity evidence binds
the exact runtime/source binding and the fixed24-row smoke count. The budget
conservatively bills two internal decode-wiring probe rows per steer call.

Fresh qualification will use a new T7 execution directory. Earlier GPU time
will carry into its shared budget; failed-attempt evidence will not certify the
new source. Candidate and held-out generation remain unstarted and unsigned.

## 2026-11-03 — user strategy review hold and source ingestion

The user asked to walk through the paper-derived strategy before further runs.
Further GPU execution is held. Neither candidate nor held-out generation has
started. The fresh r2 snapshot is staged but has no new run binding or GPU job.

The user prediction is recorded verbatim: "Yes, I expect it to pass". The lead's
prior prediction remains unchanged. No result is scored against either call.

Source ingestion is now complete on canonical EHR main91b258d4: the author blog,
released Experiment8 protocol/README and final edit diagnosis are represented by
library/notes/web-20261102--sparks-weight-space-programming.md and typed method /
mechanism nodes. Fulltext copies stay ignored. Graph validation: zero errors;
new nodes have no warning. Retrieval checks rank the source second for a generic
repair-without-retraining query and the mechanism first for thinking-loop MLP
queries. This is source verification, not an independent reproduction.

Strategy implication for review: the authors diagnose the failure, localize
writers using matched contexts, choose and test a targeted edit, then evaluate
unseen benchmarks. Our fixed amplification sweep is a proposed pilot, not a
reproduction of that agent-led discovery loop. Its layer window, support size,
edit sign, scales and single-site restriction are project choices. The mechanism
link from answerability to selective response behavior needs an explicit audit
before a final edit family is signed. No numeric gate or candidate rule is
changed by this notebook entry.

## 2026-11-03 — Astra fixed construction integrated; still unsigned

Replaced the unsigned SOL six-candidate protocol with the native Astra proposal.
Preserved the old unsigned text and harness README in `design-history/`. The
active manifest now names `astra_r1.yaml`, `astra_runtime.yaml`, and the Astra
construction/evaluation modules. No signed historical instrument changed.
The user predicts a pass; the lead's earlier tradeoff/failure prediction remains
70%. No new study outcome has been observed.

Integrated the materializer and repaired two production issues: native SelfAware
uses an `example` container, and T7 does not support the hard links originally
used for create-only writes. The integrated version checks capture settings,
renderer, base shards, journal completion, row order and last-prompt positions.
It requires both down_proj input/output, checks W times input against captured
output, and audits the realized bf16 delta. The export destination is embedded
before preparing the spec, so export never requires editing a hash-frozen spec.

Ported the existing dataset loaders/scorers/statistics with source and port
hashes in `hs20_nwe/ASTRA_ORIGINS.json`; only the dataset loader's sibling import
changes. New comparison logic preserves historical metrics, reports accuracy on
ALL known rows, and uses exact count fractions at the two-percentage-point cost
boundaries. `astra_analysis` composes the existing blinded grading lane. Its
synthetic eight-cell test passes through actual local Git commitment checkpoints
to the registered paired roll-up. That result is synthetic harness evidence.

Actual desktop CPU feasibility (no model inference):

- All source dataset hashes and counts match. The deterministic development
  roster contains 64 confab and 64 known-correct questions, excluding benchmarks.
- The pinned base target is bf16, shape 2560 x 9216, with no checkpoint bias.
  Engine inspection and a safetensors/Torch CPU read agree on raw tensor SHA256
  `6a03103aebef7c1e8474d031a7394e7fad7839c9aa567433e8ac7bc55fe0bc2b`.
  The float32 NPY readback stays private on T7; no edit was applied.
- All 5,201 evaluation questions and both retry paths fit the 2048-token context.
  Maximum prompt length is 310 tokens. Capture-runtime Transformers 5.17.0 and
  evaluation-runtime Transformers 5.12.0 produce identical prompt bytes and token
  sequences over the full surfaces, including retries. No questions truncate.
- Historical, hash-pinned calibration sources provide 535 clear-positive and
  96 clear-negative eligible decoys after excluding construction/evaluation
  questions. Selected the first 25 of each by byte-sorted row key. The private
  decoy file hash is pinned in `astra_r1.yaml`; no new generation was needed.
- Public aggregate/hash evidence is `analysis-committed/astra_cpu_feasibility.json`.

Built a separate vLLM evaluation image on Docker Desktop, CPU-qualified only:
`sha256:fa1f394893e0a969f0e990b8c9338f39d2898420315b3da2e0ea9d3b62ae3676`.
Base image: vllm/vllm-openai 0.23.0,
`sha256:6d8429e38e3747723ca07ee1b17972e09bb9c51c4032b266f24fb1cc3b22ed8f`.
Actual versions: vLLM 0.23.0, torch 2.11.0+cu130, transformers 5.12.0,
xgrammar 0.2.2, safetensors 0.8.0, numpy 2.2.6. It contains the existing exact
engine wheel `9ef85baa...` and host wheel `28511365...`. Python is `python3`,
not `python`. A normal public pull initially failed because the Windows Docker
credential helper had no logon session; an isolated empty Docker configuration
pulled the public image without changing owner credentials. No GPU was requested.

Official v0.23.0 docs were checked for supported models, structured output,
batch invariance and hidden-state extraction. Qwen3.5 is listed as supported;
batch invariance requires compute capability >=8.0, and is beta. This does not
prove Qwen3.5 runtime invariance: its actual model smoke remains a pre-sign task.
HF remains the named module-site capture path; vLLM owns unsteered evaluation.

Private CPU preparation is on T7 at
`E:/SynapticResearch/preparation/astra-r1-cpu-20261103`. The earlier draft-profile
materialization is preserved under `astra-r1-draft-profile-v1`; the current
profile has a fresh roster and tokenizer evidence. This is a CPU preparation
snapshot, not a signed execution checkout or a scored run. All new model caches,
private artifacts and tensor readbacks are on T7.

The experiment remains DRAFT. Numerical support/key/scale are not materialized;
no new study capture, patched generation or benchmark generation has run. Next:
qualify vLLM invariance and real persistence, qualify the export/readback handoff,
fill measured persistence declarations, review the concrete registration with
the PI, then sign the construction/evaluation contract. Freeze the actual edit
in Git after construction and before even the fresh base evaluation. Earlier
engineering smoke records remain separate from this revised study.

Validation at this milestone: the final CPU suite is recorded in
`/tmp/ehr-astra-ready-cpu-tests.xml` and `/tmp/ehr-astra-ready-cpu-tests.log` on the
agent box. The experiment manifest validates portably and registry regeneration
is current. `astra_run plan` resolves the actual eight-cell matrix without model
execution. Remaining inputs are declared as typed local artifacts, including
both checkpoint shards and their exact hashes; portable validation does not
pretend those bytes exist in every clone.

The final agent-box CPU suite passed 220 tests, with the torch-only file skipped
there. Ran that file separately inside the pinned desktop capture image with
NO GPU requested: 1 passed in 6.90 seconds. It checks real engine inspection,
patch validation and realized-delta agreement on a tiny synthetic bf16
checkpoint. An initial pytest setup failed because the explicit basetemp parent
did not exist; creating that scratch parent fixed setup without a source change.
This closes the CPU/torch fixture gap, not GPU invariance or export/reload
qualification.

## 2026-11-03 — PI approves Astra's proposal; actual abstention is the endpoint

PI instruction:

> So I'm fine with astras edit this is the experiment without my intervention we say edit weights directly and lets see what happens.
>
> also we're not just lookingh for a stronger abstention signal we're looking for STRONGER ABSTENTION

Recorded approval to test Astra's proposed construction as designed. The PI
provides authorization, not a new choice of tensor, columns, factors or scale.
No further design-approval request is needed for this same scope. Astra's
research context and supplied brief remain disclosed; the numerical patch will
still follow the fixed construction before evaluation feedback.

Clarified the AMENDMENT: benefit means increased actual abstention in generated
answers on unknown questions. Internal IDK projections or other activation
signals cannot substitute for that behavior. The existing known-answer cost,
quality and truthful-rate gates remain unchanged. This is a wording and approval
record, not a new score definition or a change to Astra's proposed edit.

Formal signing remains pending the technical qualification checks already
listed. Complete those checks, sign the instrument, construct and freeze the
one edit, then execute the registered evaluation under this approval. No study
capture, numerical patch or scored generation has run at this entry.


## 2026-11-03 — Signing authority delegated; desktop launch hold remains

PI instruction: “anything else we need to finish before running? you can sign it for me”.

The PI authorizes the lead to sign this fixed Astra proposal on the PI's behalf
once the technical prerequisites pass. No further scientific approval is needed
for the registered design. The preceding instruction after the desktop restart,
“dont start yet”, remains a hold on desktop and GPU launches. Signing authority
does not lift that hold.

Outstanding pre-sign work: synthetic export/readback on T7 with the fixed engine,
actual-model evaluation repeat/permutation invariance and capture/generation
kill-resume checks, then measured persistence declarations and final entry-point
validation. The experiment remains draft until these checks pass. A filesystem
compatibility repair in Tuner passed 295 CPU MechInterp tests; its updated images
are not built or qualified yet. No scored evaluation or study edit exists.


## 2026-11-03 — Desktop hold lifted; T7 export/readback qualified

PI instruction: “should be good to start”. The desktop/GPU launch hold is lifted.
Signing authority remains delegated to the lead after technical qualification.

Docker Desktop and the RTX3090 are available after the restart; the GPU was
idle at preflight. Rebuilt both runtimes with engine source 43af9b407e009bf902220ae5b510f6f27d926644.
The generic export fallback preserves create-only semantics on T7 when exclusive
rename is unavailable. It verifies all copied files and writes the completion
manifest last. A killed fallback is an incomplete export, never a checkpoint to
consume. This repair changes no edit formula, scale, support or behavioral gate.

Ran tests/test_astra_engine_export.py in the new capture image on T7, with no
GPU requested: 1 passed in 7.38 seconds. The synthetic nonzero patch validates,
exports, reads back and passes the fixed-formula audit; untouched tensors and
sidecars remain identical. Public build/evidence metadata is recorded in
analysis-committed/astra_runtime_build.json. Exact new image IDs are in
astra_runtime.yaml. Actual-model runtime qualification remains pending; no
study capture, edit or scored generation has occurred.


## 2026-11-03 — Actual vLLM GDN refusal; prospective HF schema fallback

The twenty-row unscored vLLM qualification reached actual model initialization
and failed: `VLLM batch_invariant mode is not supported for GDN_ATTN.` It wrote
zero completion rows. This is an unsupported instrument, not an abstention null.
The original runtime is preserved in design-history/vllm_runtime_refusal_20261103.yaml.
The upstream support boundary is also documented at
https://github.com/vllm-project/vllm/issues/48613 (including failure of a simple
support-flag-only patch). No capability check was bypassed.

The experiment-runner batching reference explicitly permits an HF fallback when
the invariance smoke fails. Before any behavioral output, registered HF batch
size one with the same JSON schema through XGrammar. Model/revision, edit formula,
prompts, datasets, greedy decoding, retry rules, metrics and thresholds are
unchanged. This is a technical execution repair under the PI's delegated signing
and run authority, not a new edit selection or scientific gate.

Added reusable HF schema decoding and registered conditional-model loading in
Tuner (d03a15d62549c64cf46e10532d50a77accd32b26). The optional dependency is lazy;
each request gets a new grammar matcher. 347 batch/MechInterp CPU tests pass.
The experiment CPU suite passes 237 tests with 2 Torch-only skips (49.106 s).
The pinned desktop HF image passes all 3 generic HF-schema CPU tests in 6.27 s.
The runtime has XGrammar 0.2.2 and apache-tvm-ffi 0.1.15.post2 on the existing
Torch 2.9.1+cu128 / Transformers 5.17.0 stack. Actual-model repeat/permutation and
capture/generation hard-kill drills still precede formal sign and study capture.


## 2026-11-03 — First HF qualification passes; capture CLI flag repair

The first HF namespace completed both orders twice (20 rows each), with exact
persisted row/token equality. A whole-container SIGKILL after one durable row
returned exit137; its resumed 20-row output matched all four uninterrupted runs.
Whole JSON-schema validation and prompt-token checks passed. This first proof
remains under qualification/hf-5.17.0-xgrammar-0.2.2-b1-r1.

The subsequent capture command refused before model load: the direct extract
verb requires --mi-config, while the new Astra driver passed --config. Fixed
that one argument in astra_run.capture. Because the generation qualification
also binds that source file, selected fresh namespace
hf-5.17.0-xgrammar-0.2.2-b1-r2 instead of rewriting or weakening the first proof.
Capture is qualified first, followed by final-source generation repeats/drill.
No study capture, numerical edit or benchmark output exists at this point.

The uninterrupted final-source capture completed all20forward-only rows. The
actual module input/output and pinned W pass the registered linear-consistency
check; max error/bound ratio is0.2370663718674437 (must be<=1). This is a
mechanical capture check, not an abstention benefit. The actual hard-kill and
resume comparison is in progress. The eight-cell production pipeline also
plans successfully through the installed public engine, without model execution.

## 2026-11-03: engine ruling, final qualification and signing

The PI asked whether vLLM was failing only because of an old pin. Checked upstream
source: 0.23.0 is old, but v0.33.0 and main still have no batch-invariance
declaration on `GDNAttentionBackend`, so the selector refuses at initialization.
PR 60033 and PR 45819 are unmerged. PR 60033 was validated on H100, not on this
RTX 3090. PI ruling: "ok fineee we'll start with HF". PI hold release: "and hold is
lifted as well". `runtime/engine_capability_gap.yaml` pins this evidence.

The r2 namespace failed capture resume parity. The r3 namespace passed, but was
replaced before any study output. A pre-sign review found `evaluate_cell` still
required `VLLM_BATCH_INVARIANT=1` on the HF path. Removing that guard changed
hash-bound `astra_run.py`, so r4 was run from commit 2183407e, restored into the T7
snapshot. The r3 repeat chain also stopped once when its launching SSH session
ended; both completed runs were intact and the chain was resumed.

Namespace r4 passed: four repeats in two orders and a SIGKILL-resumed run have
identical token IDs and finish reasons, with whole-schema validity. A capture
SIGKILL at 4 rows resumed with identical bytes across 60 compared tensors. Each
20-row generation run took 89 to 100 s including model load. These were unscored
development rows. Reports: `analysis-committed/astra_runtime_qualification.json`.

The T7 snapshot now has a local Git object store at the pushed commit, so
`commitments.require_git` can verify public commitments. Containers pass
`safe.directory=/workspace` through the Git environment. `.synaptic/` is now
ignored so private artifacts cannot be staged in a checkout.

Signed by the lead under the PI's delegated authority. No study capture, numerical
edit or benchmark output exists at signing.


## 2026-11-03: one edit constructed, audited and frozen

Signed capture completed all 128 development rows in 122.5 s. The captured
module input and output pass the registered linear-consistency check, with max
error-to-bound ratio 0.2539 (must be at most 1). The one edit was constructed
without refusal: alpha 0.26767, limited by the column-norm cap, 32 columns. The
realized audit passed on readback: 79,097 changed entries (cap 81,920), zero
changes off support, whole-tensor relative change 0.00538 (cap 0.01), selected
column relative change 0.09001 (cap 0.10). The engine export and hash-only freeze
followed. These are instrument checks, not behavioral evidence. No benchmark
generation occurred before `analysis-committed/astra_patch_freeze.json` was committed.

## 2026-11-03: evaluation launched; 128-token cap retained

Evaluation started at 18:00 EST from commit 03d3d15b, in pinned pipeline order. Early
structure counts on the SelfAware P-struct base cell, with no scores read: 40 of 664
rows hit the 128-token cap and 39 of those are invalid JSON; none has a repetitive
tail; median completion is 28 tokens. These rows enter the registered format retries,
whose instruction mentions abstention, so retry incidence per cell must be read with
the result. PI ruling: "No it's fine keep it if it screws things up for us we can
change on a second round". The cap stays as signed. Any change belongs to a separately
registered round, not this one.

## 2026-11-04: evaluation complete; blinded pool committed before grading

All eight cells finished at 06:25 EST with driver exit code 0. No scores were read.
Pool build found 19,663 detector-negative candidates and 358 shards at the registered
55 candidates per shard, each with 25 clear-positive and 25 clear-negative decoys.
`run_binding.json` and `adjudication_pool_manifest.json` were committed before any
grader saw a row. PI pre-approval for the Opus grader fleet, 2026-11-04: "You fine ...
to ask for the opus [graders] I pre approve". Each grader gets one fresh context, the
verbatim rubric, a private directory and bare opaque-id/text pairs. Graders use only
file read and write tools, and may not build a pattern classifier. ID maps and the
salt stay on T7.

## 2026-11-04: grading complete; hashes committed before unblinding

358 fresh Opus graders finished with no errors, in 19.5 minutes and about 15M tokens.
Every graded file passed the lead's shape check before its hash was committed. Transcript
audit across all 358: no Bash or script use, and zero file paths outside the grader's own
directory. Seven graders rewrote their own output before finishing. The lead's blind
30-item spot check agreed 30/30 with the graders (floor 0.90) and was committed before
apply. No opaque-id map was read before these commitments.

## 2026-11-04: applied and rolled up

Apply: instrument valid, 358 of 358 shards passed at attempt 1, no regrades, pooled positive
agreement 8950/8950. Roll-up: primary_prediction_falsified. Details are in AMENDMENT
section 9. Aggregate per-cell counts are in `analysis-committed/astra_result_summary.json`;
that summary script was unregistered descriptive reporting and decides nothing.
Private rows, graded files and ID maps stay on T7.


## 2026-11-04: closeout and authorization for a separate broader edit

PI instruction: "wrap up then yeah lets spin up a new experiment to change more weights."
The first experiment remains terminal and falsified. Its frozen edit, thresholds
and outcome will not be revised. A successor is authorized to investigate a
broader weight edit. Astra will propose the construction before its numerical
edit and evaluation; the PI is not choosing its numerical parameters.

The column-norm cap limiting the first edit is a hypothesis for the successor,
not evidence that a larger edit will work. Existing benchmark results are now
known to the investigators, so reuse is labeled exploratory. Keep actual
abstention and known-answer preservation as the behavioral endpoints.

## 2026-11-04: additive input promotion for the successor

The original base P-struct capture, roster/request/source provenance and original
input bytes were authenticated and promoted for reuse. The shared public descriptor
is experiments/common/captures/astra-r1/origin.json; private bytes are on T7.
The manifest adds this shared input reference only. The original instrument,
scientific pins, result, verdict and historical artifact identities are unchanged.

The exact held-back calibration file was also promoted separately for R2 reuse:
E:/SynapticResearch/shared/astra-r1-decoys-v1/decoys.json. The new common
hash-only decoys-origin.json and additive input declaration preserve the original
25/25 pool and its frozen bytes. No R1 instrument, gate, score or verdict changed.
