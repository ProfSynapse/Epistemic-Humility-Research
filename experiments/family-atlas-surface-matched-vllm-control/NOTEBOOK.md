# Family Atlas Surface-Matched vLLM Control notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

- 2026-07-22: The approved Gemma Stage A generation durably produced all 5,200
  completions in the pinned vLLM V1 runtime, then failed closed during strict
  whole-output validation. Exactly 5,189 rows were valid JSON objects. Five
  rows reached the registered 200-token cap with incomplete JSON, and six rows
  emitted a stop token after 6-8 completion tokens with incomplete JSON. G0
  therefore cannot pass because its registered strict-validity requirement is
  1.0. No role grading, matching, or capture was accepted, and Qwen was not
  launched under the sequential approval. The private completions, checkpoint,
  provenance, surface basis, coordinates, logs, and resume history were
  preserved. The committed failure summary contains IDs, counts, and hashes
  only. The PI approved a separately governed successor with premature-EOS
  suppression, a 512-token cap, and a mandatory smoke over all 11 failure IDs;
  this signed experiment's settings and gates remain unchanged.
- 2026-07-22: Two Gemma Stage A launcher attempts stopped before tokenizer or
  model loading and produced no scientific row. The first lacked read-only
  mounts for the signed prior-atlas exclusion artifacts; both host artifacts
  were then verified at their signed hashes. The second reached surface
  preprocessing and exposed that the pinned vLLM image lacks SciPy,
  scikit-learn, and joblib. Repaired the signed harness before results by
  splitting deterministic surface preparation into the already pinned
  mechinterp image and requiring hash-bound preparation evidence in the vLLM
  generation phase. Repinned `source_and_generate.py` and
  `test_instrument.py` with the packaging-failure reason; no scientific rule or
  model setting changed.
- 2026-07-22: The PI explicitly approved sequential local RTX 3090 Stage A
  generation for Gemma-4-E4B-it and Qwen3-4B after signing and merge. Gemma is
  launched first in the pinned vLLM container; Qwen may launch only after Gemma
  exits successfully. Stage B capture remains unapproved and unlaunched.
- 2026-07-22: PI scoreboard calls were recorded before scientific generation,
  and `bin/exp sign` pinned all 12 config and instrument files. The experiment
  is signed. Stage A generation remains unlaunched and requires separate PI
  approval per model.
- 2026-07-22: Merged the generic vLLM model-runner pin in Synaptic Tuner PR
  145 at commit `b1ea38298a478a7d40fbab1cb4ad492194b833e7` and updated the
  root submodule to that exact commit. The registered runtime source
  fingerprint remains
  `5a693532465c771ec7c7afe7bcbb6e55c08a508e6d3a1d321bcb8fdb32140576`.
- 2026-07-22: Gemma pre-sign smoke was rerun with the explicit vLLM V1 model
  runner pin and passed in the exact pinned vLLM 0.23.0 image. All five 20-row
  runs had identical completion token IDs, finish reasons, parsed objects, and
  canonical row logs across original order, fixed permutation, and hard-kill
  plus resume. Whole-output schema validity was 1.0 with no salvage parsing.
  The committed ID-only manifest and aggregate passed containment lint; the
  aggregate SHA-256 is
  `8c9190e6bb9116df93dbb67bbe01bb1f21300ea7de801967e12ab6b8a6abbb72`.
- 2026-07-22: Qwen pre-sign V1 smoke passed in the exact pinned vLLM 0.23.0
  image. All five 20-row runs had identical completion token IDs, finish
  reasons, parsed objects, and canonical row logs across original order, fixed
  permutation, and a hard-kill after 16 durable rows followed by resume.
  Whole-output schema validity was 1.0 with no salvage parsing. The committed
  ID-only manifest and aggregate passed containment lint; the aggregate
  SHA-256 is
  `d327181a49751d46f4f3bb984e865f86f15c86a90128a92a6f99d056b634f775`.
- 2026-07-22: The first post-reboot Qwen smoke attempt stopped before model
  weights loaded and before any completion after vLLM auto-selected its V2 GPU
  model runner, which requires CUDA UVA unavailable on the registered WSL2
  lane. The exact vLLM 0.23.0 image recognizes
  `VLLM_USE_V2_MODEL_RUNNER=0` and does not expose the newer WSL2 pin-memory
  override. Pinned the generic generation interface and experiment provenance
  to model runner V1 before retrying. The failed private checkpoint was
  preserved and contains zero completed IDs.
- 2026-07-22: Pre-sign Gemma capacity smoke exposed two launcher issues before
  any accepted completion: the non-root container user initially lacked a
  passwd entry, and Gemma still profiled its video encoder when only image and
  audio limits were zero. Preserved both private failed attempts, mounted host
  passwd/group read-only for UID resolution, and added `video: 0` to the Gemma
  text-only multimodal limits before signing. An exact-revision
  `processor_config.json` metadata file was added to the host cache through the
  official Hugging Face client; no credential entered the generation
  container. The smoke was stopped before repeat generation and produced no
  accepted pre-sign result.
- 2026-07-22: Replaced the proposed in-container Git revision check with a
  deterministic fingerprint over the complete tracked Synaptic Tuner
  batch-generation import surface. Host-side commit provenance remains
  `f21786495503a3e04abf4766b05b16fedab13766`; the runtime source fingerprint is
  `a8a812f3b221f6e8e36fdda5fc8629c0ced40043693a22d644c57fbda1157fb1`.
- 2026-07-22: Repinned generation batch size from 32 to 16 while retaining
  `max_num_seqs=32`. Added an inert pre-sign harness for deterministic private
  row selection, two original-order runs, two fixed-permutation runs, a kill
  after the first durable batch plus exact-input resume, strict output checks,
  and aggregate-only promotion. No model or container was launched.
- 2026-07-22: Pre-stated joint outcome precedence and added a blank PI and
  orchestrator scoreboard. No call was entered.
- 2026-07-22: Ran the CPU-only planted G1 reachability control through the real
  matcher. It produced 128 intact triads split exactly 64 FIT and 64 held out.
  The committed aggregate contains counts and a private-manifest digest only;
  planted rows remain under gitignored `analysis/`.
- 2026-07-22: Scaffolded a Tier 2 successor after the predecessor terminated at
  G1 before any controlled capture. The successor keeps both models and all
  scientific gates, but runs their Stage A generation and gating independently.
- 2026-07-22: Chose the existing generic Synaptic Tuner `batch-generate --engine
  vllm` path. A tuner capability patch is required before signing because the
  current verb does not yet carry the registered schema, scheduler, tokenizer,
  prompt-token, version, and batch-invariance pins end to end.
- 2026-07-22: Initially inspected vLLM 0.18.0, then rejected it before signing
  because its batch-invariance implementation requires compute capability 9.0
  while the RTX 3090 is 8.6. Repinned the candidate runtime to vLLM 0.23.0,
  whose documented minimum is 8.0, at published
  Linux/amd64 image digest
  `sha256:3a1e7f5904e1a1192a02aa0086ceaffc33985d7044c7bb25b3a43d61bdbe3ac0`.
  The image was inspected remotely only. It was not pulled or launched.
- 2026-07-22: Read-only `nvidia-smi` preflight observed RTX 3090 compute
  capability 8.6, 24,576 MiB, host driver 591.86, and host-advertised CUDA 13.1.
  No kernels or model processes were launched.
- 2026-07-22: Pinned the private predecessor Gemma generation log read-only at
  SHA-256
  `cc0a9b4b0564c85489aa0f872b3a33d8131d8433b51b3b7a14a628310422f026`.
  It is descriptive comparator input only and cannot affect a gate.
- 2026-07-22: No experiment was signed. No Docker container, model load, or GPU
  process was launched. Pre-sign model smokes require fresh PI approval.

## 2026-08-27 — Exhaust published to HF (aggregate shape)

Data-exhaust release, PI-approved in-conversation (explicit permission
2026-08-27, batch 3 of the exhaust backfill, task-56c61a). Built with the
data-exhaust skill (aggregate-only copy-everything mirror of
analysis-committed/: no question text, generation text, or hidden states;
verify_exhaust.py PASS including the --experiment-dir completeness check;
zero exclusions). 8 files / ~18 KB, built at repo commit 37eaa399.

- HF repo: `professorsynapse/eh-family-atlas-surface-matched-vllm-control` (dataset)
- HF revision: `b2b48a82e3f6fd6e454e08e9cd21a1561fe218d0`
