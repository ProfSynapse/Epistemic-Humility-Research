# HANDOFF — Epistemic Humility Research Program

**Repo:** `ProfSynapse/Epistemic-Humility-Research` (private) · **Branch:** `main` · **Updated:** 2026-06-11
**This doc is the single re-entry point.** Tell a new session: "read HANDOFF.md and continue."

**Mission for the next session: RUN THE PHASE 1 PILOTS.** The pipeline is
built, peer-reviewed, and merged (PR #1, merge `050bfd6`). Nothing has
touched a GPU yet. This session runs compute: knowledge probe → dataset
builds → matrix gate → bridge replication cells. Machine: the desktop
(RTX 3090). Paper 1 (meta-analysis) is drafted and gated on the user's
read-through — see §5; do not touch unprompted.

---

## 0. Desktop migration checklist (do these before anything else)

1. **Laptop must push first.** Commit `6cad489` (project-memory pins +
   .gitignore) may still be local-only on the laptop. If
   `git log origin/main -1` does not show it, ask the user to run
   `git push origin main` from the laptop (an approval gate blocked the
   agent push there).
2. `git pull && git submodule update --init` — submodule must land at
   `3a3d7a2` on `feature/dpo-trainer` (upstream repo redirects to
   `ProfSynapse/Synaptic-Tuner`; old `Toolset-Training` URL still works).
3. **`.env` is machine-local and gitignored** — create one on the desktop
   with `HF_TOKEN`. Never commit it; token via env only, never in command
   strings.
4. **Vendor data does NOT travel via git.** The laptop holds ~2.8GB
   gitignored data under `datasets/say-i-dont-know-training/` (OpenMOSS
   zip + regenerated outputs) and `datasets/triviaqa-rc-nocontext/train.jsonl`.
   Either transfer those directories directly (faster), or regenerate
   deterministically: `python3 datasets/scripts/fetch_datasets.py`
   (TriviaQA from HF; OpenMOSS zip is a gated Google Drive fetch the user
   already authorized; observed zip sha256 `1dfe742c…bab86` — the
   `OPENMOSS_DRIVE_ZIP_SHA256` pin was blanked for re-pin, so pin it in a
   follow-up commit once fetched on the desktop).
5. macOS gotcha (if desktop is a Mac): python.org Python needs
   `SSL_CERT_FILE=$(python3 -m certifi)` for HF/arxiv fetches.

## 1. Where the build stands (60 seconds)

- **PROTOCOL v0.3 is LOCKED** (user-signed, `experiment/protocol/PROTOCOL.md`):
  hypotheses H1-H4; run matrix = 19 cells @4B (3-seed headline + LR/β
  sensitivity panel) + 9 @8B (3-seed confirm) + 2 bridge; probe N=32;
  builder-enforced leakage guard. Headline numbers come ONLY from
  pre-registered defaults; the panel is robustness-only. Changing
  hypotheses/falsifiers/headline matrix requires a NEW signed revision.
- **Models pinned:** `unsloth/Qwen3-4B-bnb-4bit` + `unsloth/Qwen3-8B-bnb-4bit`
  (hybrid thinking models). `enable_thinking=False` is enforced everywhere
  (ADR §9.3 in `docs/architecture/phase1-pipeline.md`): SFT masked
  passthrough, DPO prompt-boundary, KTO raw-string N/A, eval+probe pinned
  with runtime self-check. Bridge arm: Llama-2-7b-chat (Meta access GRANTED).
- **All five workstreams merged:** WS-0 fetch (`datasets/scripts/`),
  WS-1 probe (`experiment/phase1/probe/`), WS-2 builders
  (`experiment/phase1/data/`), WS-3 trainers (submodule; SFT/DPO/KTO with
  seed+β+chat_template_kwargs forwarded on both lanes), WS-4 eval
  (`experiment/phase1/eval/` — scoring + stats; Cheng regression keystone
  42.71/23.27 green), WS-5 runner
  (`.claude/skills/experiment-runner/` — load that skill before using it).
- **Review hardening landed** (PR #1, 1 Blocking + 11 Minor fixed, all
  re-verified): correctness_safe KTO emits the SAME four rows as
  congruence — the ablation is weights-only 2.0/1.0 (never re-gate the
  False rows behind `mapping=="congruence"`; an all-True file crashes the
  trainer); leakage guard re-derives probe-side keys; `--check-only`
  actually gates per cell; McNemar/bootstrap pinned to known values;
  natural-case gold flows probe→builder via optional `answer_value`.
- Suites at merge: builders 27 · eval 53 · run_matrix 59 (both CWDs) ·
  probe 15 · submodule experiment_tracking 149.
- **Tooling gotcha:** rtk-proxied `pytest tests/` (directory glob) can
  falsely print "No tests collected" exit 0. Re-run with an explicit file
  path before believing a suite is broken.

## 2. The pilot run sequence (this session's work, in order)

1. **WS-1 knowledge probe** — first real compute. Probe both pinned Qwen3
   base models on the TriviaQA rc.nocontext train subset per
   `experiment/phase1/probe/config/probe.yaml` (N=32 samples/question,
   local vLLM backend, RTX 3090). Output: `probe_results.jsonl` per model
   with p_correct/known-unknown labels + `answer_value`. Read
   `experiment/phase1/probe/README.md` first.
2. **WS-2 dataset builds** — `experiment/phase1/data/build_datasets.py`
   per `config/build.yaml` for each model_tag (4B, 8B, bridge). The
   leakage guard runs fail-closed here against
   `cheng_test_gold.jsonl` (11,313 keys). Outputs land in gitignored
   per-model_tag dirs; `bridge_llama2_7b_chat/` is hard-excluded from git
   at any depth (DO-NOT-REDISTRIBUTE — verify with `git check-ignore`).
3. **Gate the matrix:** from repo root,
   `python3 .claude/skills/experiment-runner/scripts/run_matrix.py --check-only`
   — must go PASS/SKIP per cell instead of today's correct ABORT (it
   aborts now precisely because step 2 hasn't run). `--dry-run` should
   still expand exactly 30 cells.
4. **Wire the launch path** (small CODE task, delegate to a coder): the
   runner's record-before-launch spine (`stage_local_data`,
   `build_run_record`, `write_run_record`) is written and unit-tested but
   deliberately unwired — `main()` refuses to launch. Wire it per the
   WS-5 design in `docs/architecture/phase1-pipeline.md`, or launch pilot
   cells manually via the tuner CLI with materialized recipes from
   `experiment/phase1/recipes/`. Run records are committed provenance.
5. **Bridge replication FIRST** (locked protocol decision): the 2
   Llama-2-7b-chat cells (Idk-SFT + Idk-DPO) on the local lane only,
   validated against Cheng et al.'s published numbers (our reanalysis
   anchors: Idk-SFT over-refusal 42.7%, DPO 23.3%) BEFORE any novel arm.
6. **Then the headline matrix:** 19 @4B, then 9 @8B. Identical LoRA budget
   across arms, early stopping on per-arm dev loss.
7. **Eval generation lane** — before evaluating trained checkpoints,
   run_eval needs its generation path; that activates deferred task #47:
   VLLMGenerator must pin `enable_thinking=False` + probe-style runtime
   self-check. Scoring/stats are ready and regression-pinned.

**Lane notes:** local RTX 3090 is the primary lane and fully unblocked.
Cloud lane (HF Jobs) stays CLOSED until the Qwen3 datasets are
hub-published (PROTOCOL §5 prerequisite) — and bridge/OpenMOSS-derived
data NEVER goes to the hub regardless. modal/runpod backends don't carry
chat_template_kwargs/seed/β (documented pre-existing gap) — Phase-1 cloud
is hf_jobs only, if used at all.

**Inside the submodule:** load `synaptic-tuner/.skills/fine-tuning/SKILL.md`
before any training work. KTO JSONL must be interleaved (builders do this).
Tuner changes must stay generalized — zero experiment-specific code.

## 3. Standing constraints (SACROSANCT)

- **OpenMOSS data:** do-not-redistribute. Zip + regenerated JSONLs stay
  gitignored, never committed, never hub-published; bridge cells are
  local-lane-only. The user is encouraged (optional) to email OpenMOSS re
  licensing.
- **PROTOCOL.md is LOCKED** — protocol changes require a new signed
  revision with changelog.
- **`meta-analysis/` is READ-ONLY** — paper 1 is gated on the user's
  read-through.
- **Merge ≠ verification** — the user's manual test of the merged pipeline
  is still pending; don't close source issues on merge alone.
- **Commits:** the team-lead owns staging/commits; commit gate is
  benign-reword-never-`--no-verify`; merge/PR-close/irreversible ops need
  explicit user authorization.
- Provenance rules in §6 apply to every number paper 2 produces.

## 4. Headline findings the experiment is built on

1. **KTO has never been applied to abstention/IDK/calibration training**
   (verified gap as of 2026-06). Closest prior art: Cheng et al. ICML 2024
   (Idk-SFT/DPO/PPO/BoN/HIR on Llama-2-7b-chat; no KTO, no small models,
   thin OOD).
2. Our exact reanalysis of Cheng's outputs (n=11,313): Idk-SFT over-refuses
   42.7% of known questions; DPO halves that to 23.3%.
3. Our AbstentionBench reanalysis: each Tulu-3 preference stage adds recall
   (SFT→DPO +0.08 at 8B, p=5.5e-4) at zero precision cost — but the
   frontier ceilings at ~0.7 and scale doesn't move it (0.69→0.71 across
   8B-405B).
4. RLHF degrades token-level calibration ~10× (GPT-4 ECE 0.007→0.074)
   while improving abstention — the unreconciled tension; no paper measures
   both after the same run. KTO unmeasured on either.
5. SFT on model-unknown facts causally drives hallucination (Gekhman
   2405.05904) → training data must be split by THIS model's knowledge.

## 5. Where paper 1 (meta-analysis) stands

`meta-analysis/paper/draft-v0.md`, ~10,800 words, 69/69 citations resolved.
**Gate: the user has not yet done the full read-through.** Do not restart
paper work unprompted; the draft is stable.

Done: evidence base of 67 rows / 35 studies / 64 verified=true in
`meta-analysis/evidence/effects.csv` (family votes C1 2/0, C2 3/0 p=0.25,
C3 1/0, C4 4/0 p=0.125, C5 10/0 p=0.002); every in-text number verified
against primary sources, † convention retired; methods evidence-based in
§4.4 (SWiM, Cochrane ch. 12, PRISMA 2020 with disclosed deviations,
Hedges & Olkin limitation, Buscemi/Khraisha extraction-error grounding);
four independent reanalyses of released artifacts in §5.3 (Cheng outputs,
AbstentionBench table, FActScore generations, CRM training-data audit);
PRISMA flow reconstructed; coverage probes done (English-only corpus holds
across a five-language search; venue probe logged v1 admission candidates
in `evidence/prisma-flow.md`); related-surveys positioning (§6.4); acronym
pass; author block.

Remaining (tracked in `meta-analysis/paper/TODO.md`):
- User read-through, then: v1 admission decision (high priority: JMIR
  e78432, SAPA EMNLP 2025, 2505.13988 Hallucination Tax).
- Figures: Cochrane effect-direction plot per family, §5.3 operating-point
  scatter (abstentionbench_frontier.png may serve), L1-L4 coverage map.
- Abstract trim ~250→200 + title pick; BibTeX + arXiv LaTeX pipeline.
- Provider-card refresh right before submission (§5.4 is date-scoped to
  June 2026; Gemini 3.5 Flash / 3.1 Pro already out).
- §8 future-work section drafted from research-trajectory.md.

## 6. Provenance rules (non-negotiable, apply to paper 2 as well)

Every number carries source + exact metric + model + method + `verified`
flag. Analysis scripts are deterministic and re-runnable (data in, figures
out); no hand-edited results. Datasets carry `dataset.md` provenance
(source, license, fetch date, schema). Gitignored binaries (library/pdfs
273M, fulltext 38M, scratch parquets) are re-fetchable via
`library/scripts/fetch_library.py --enrich`. No em-dashes in paper body
prose. Release everything paper 2 produces (per-model labels, adapters,
harness) — paper 1 documents the field failing at exactly this. The eval
harness now enforces the `verified` flag in code: only metrics in the
regression-validated registry (`VALIDATED_METRICS`, gated by the Cheng
keystone test) stamp `verified=True`.
