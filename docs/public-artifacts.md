# Public Artifacts

This file is the repo-side manifest for Hugging Face publication. It records
what should be public, what must stay local, and how published HF artifacts point
back to local provenance.

Publication is a release gate, not a training side effect. Upload only after the
run/eval artifacts are reconciled against
`archive/papers/retired/results-provenance-inventory.md` and the relevant run records.

## Published HF Repos

Use lowercase, queryable names. Record the exact HF revision after every upload.

| Artifact family | HF repo | Status | Revision | Local provenance | Notes |
|---|---|---|---|---|---|
| locked training-regimen redistributable datasets | [`professorsynapse/epistemic-humility-phase1`](https://huggingface.co/datasets/professorsynapse/epistemic-humility-phase1) | published | `922d3b52ff6e8143b2701c3a7562909077eba4ab` | `archive/experiment/phase1/data/qwen3-4b-instruct/` | Qwen3 4B train/dev JSONLs plus `README.md`, `build_manifest.json`, and `questions_frozen.json`. Excludes restricted bridge/OpenMOSS/Cheng-derived raw data. GRPO train/dev splits (14,888/1,655 rows, license-audited: same frozen source pool, zero OpenMOSS/Cheng/bridge content) added 2026-08-15, user-approved. |
| locked training-regimen eval outputs | [`professorsynapse/epistemic-humility-phase1-evals`](https://huggingface.co/datasets/professorsynapse/epistemic-humility-phase1-evals) | published | `df4a9961321c04903c748f8caa4d79f84840e3b7` | `archive/experiment/phase1/eval/analysis/`, `papers/paper-2-training-regimen/analysis/row-pattern/`, and `archive/papers/retired/results-provenance-inventory.md` | Compact analysis layer only: aggregate tables, analysis reports, Paper 2 row-pattern outputs, thinking/sycophancy summaries, unknown-label analyses, and scripts. Full raw local eval result directories remain local unless deliberately released. |
| locked training-regimen knowledge labels | [`professorsynapse/epistemic-humility-phase1-labels`](https://huggingface.co/datasets/professorsynapse/epistemic-humility-phase1-labels) | published | `fef638b8870937fddab6c2759baa404cb13da660` | `archive/experiment/phase1/data/qwen3-4b-instruct/questions_frozen.json` and `archive/experiment/phase1/probe/qwen3-4b-instruct/` | Compact label/probe release: frozen question split, probe manifest, and sensitivity grid. The large local `probe_results.jsonl` cache is not published. |
| Cloud-lane per-cell results | [`professorsynapse/epistemic-humility-cloud-results`](https://huggingface.co/datasets/professorsynapse/epistemic-humility-cloud-results) | published | `af7309529ef1fac77617fdf02860b8c16a504a1b` (card) | `experiments/common/cloud/` plus per-experiment `cloud/` launchers | Result/manifest JSONs uploaded per cell by the HF Jobs lane itself; the card documents the folder schema and run-tag conventions (`y-*` = Amendment Y, `smoke-*` = non-evidence). Cells append continuously as jobs land. |
| Two-signal probe directions | [`professorsynapse/eh-probe-directions`](https://huggingface.co/datasets/professorsynapse/eh-probe-directions) | published (user-approved 2026-07-02) | `033ae541ba862e289f0c7ff200f6f3e9d171626e` | `experiments/common/artifacts/two_signal_probe_directions/` (Amendment AA fits, seed 20260630) | 4 families x gate/dial: per-layer unit-normed directions (safetensors) + fit metadata JSON + `PROVENANCE.json`. Apache-2.0 (probe weights over our own activations). Card carries the AA caveat: readout vectors, not validated steering handles. |
| Readout row surfaces | [`professorsynapse/eh-readout-rows`](https://huggingface.co/datasets/professorsynapse/eh-readout-rows) | published (user-approved 2026-07-02) | `808dd12336e34295ff64db91781e2b643ace9989` | per-folder source paths recorded in the repo's `PROVENANCE.json`; sources under `archive/experiment/phase1/probe/` | 31 folders / 79,015 rows / ~62 MB: S/T/U/W/X/Z/SR/P generation surfaces (question, answer, grade — NO hidden states) + frozen probe-pool row layers. Per-source licenses on the card (SelfAware Apache-2.0, KUQ MIT, PopQA MIT companion, TriviaQA research-use). No OpenMOSS/Cheng IDK content; smokes excluded. |
| Amendment AH exhaust | [`professorsynapse/eh-doubt-on-command`](https://huggingface.co/datasets/professorsynapse/eh-doubt-on-command) | published (user-approved 2026-07-04) | `42b3629d3003f5048db3546b73454364a82cc7ea` | `archive/experiment/phase1/probe/analysis/ah_main/`, `analysis/ah_addendum_a1/`, `analysis/ah_stage0/` (gen rows, instrumentation, stratum, manifests/gates) | 5,436 rows / ~4.3 MB: AH main 3 arms + primed-readout instrumentation + Addendum A1 stratum, with DATASHEET + LICENSE-AUDIT. Same four sources/verdicts as eh-readout-rows; zero FalseQA (audited 3 ways); absolute paths stripped (`<repo>/`); full mining pools deliberately NOT included (available on request under same audit). |
| J-space fresh-pool census | [`professorsynapse/eh-jspace-fresh-pool-census-qwen3-4b`](https://huggingface.co/datasets/professorsynapse/eh-jspace-fresh-pool-census-qwen3-4b) | published (user-approved 2026-07-08) | `3add102ce930f73a29013f572f03e7325da30825` | `experiments/j-space-layer-contrast-replication-qwen3-4b/analysis-committed/fresh_eval_pool_manifest.json` plus `build_hf_public_census.py` | 12,923 text-free candidate rows / 2,263 selected rows: ID/provenance/role/behavior flags only. No raw question text, aliases, prompt text, generation text, hidden states, or intervention outputs. |
| Doubt-snap cross-family confirmatory exhaust | [`professorsynapse/eh-doubt-snap-cross-family-confirmatory`](https://huggingface.co/datasets/professorsynapse/eh-doubt-snap-cross-family-confirmatory) | published (user-approved 2026-07-14) | `experiments/doubt-snap-cross-family-confirmatory/analysis-committed/` via `scratch/exhaust-backfill-v2/doubt-snap-cross-family-confirmatory/` (copy-everything builder, PR #292) | 36 payload files / ~3.8 MB across 4 family dirs (qwen35_4b, qwen35_9b, mistral7b_instruct_v03, llama32_3b_instruct): direction vectors (u_d, c_hat, random_direction), dose/gate fits, split/build manifests, modal_status, prep summaries. Aggregate/ID-manifest shape only: no question text, generation text, or hidden states. Supersedes the incomplete v1 card (missing modal_status.json per cell). |
| Llama wide-retest aggregate exhaust | [`professorsynapse/eh-llama-atlas-gated-wide-instrument-retest`](https://huggingface.co/datasets/professorsynapse/eh-llama-atlas-gated-wide-instrument-retest) | published (user-approved 2026-07-19) | `f53beaccc8fc0719130b2510af374b7282977b92` | `experiments/llama-atlas-gated-wide-instrument-retest/analysis-committed/` (repo commit `86f33204`) | 15 files / ~1.4 MB copy-everything mirror: pre/post-adjudication wide tables, family + dose-ladder reports, FIT build manifests, adjudication pool/graded/applied manifests. No row text; zero exclusions. |
| Llama wide-retest row-level exhaust | [`professorsynapse/eh-llama-atlas-gated-wide-instrument-retest-rows`](https://huggingface.co/datasets/professorsynapse/eh-llama-atlas-gated-wide-instrument-retest-rows) | published (user-approved 2026-07-19) | `2b46d055c71378cde8dd566e6a6f4bf5c1deff33` | staged from `/home/profsynapse/code/ehr-exhaust/llama-atlas-gated-wide-instrument-retest/runlog/` (30 dosed RunLogs + 8 graded adjudication shards) | 23,510 dosed rows / ~31 MB, single cell `llama` (unsloth/Llama-3.2-3B-Instruct @ `006f5dcd`): 17,294 KUQ rows full text (MIT), 6,216 TriviaQA+PopQA rows text-free per license gate, zero excluded; narrow + detector_v2 grades plus `is_abstention_adjudicated` joined from the blinded lane (19,230 rows). No opaque_ids, no baseline rows (baseline aggregates live in the aggregate repo). |
| Refusal-axis ablation confirmatory exhaust | [`professorsynapse/eh-refusal-axis-ablation-confirmatory`](https://huggingface.co/datasets/professorsynapse/eh-refusal-axis-ablation-confirmatory) | published (user-approved 2026-08-17) | `f929fa472c521e7233a4c65033a0ef89469747ef` | `experiments/refusal-axis-ablation-confirmatory/analysis-committed/` (repo commit `7e3ded78`) | 3 files / ~10 KB aggregate-only: seed-2 intervention summary + README + PROVENANCE. Terminal status falsified (RC-G1 falsifier fired: post-ablation known-item over-refusal 0.5528 >= 0.30); card reports it straight. No row text. |
| J-lens trained-checkpoint mid-band ablation exhaust | [`professorsynapse/eh-jlens-trained-checkpoint-midband-ablation`](https://huggingface.co/datasets/professorsynapse/eh-jlens-trained-checkpoint-midband-ablation) | published (user-approved 2026-08-17) | `58a0f3b1e4e7b9c4412a6b9a29d306856adaccaf` | `experiments/jlens-trained-checkpoint-midband-ablation/analysis-committed/` (repo commit `7e3ded78`) | 5 files / ~17 KB aggregate-only: hs17 intervention summary, trained J-lens profile, smoke summary + README + PROVENANCE. Terminal status falsified (JT-G1 fired on both clauses); card reports it straight. No row text. |
| Wide-instrument control-rescore aggregate exhaust | [`professorsynapse/eh-wide-instrument-control-rescore`](https://huggingface.co/datasets/professorsynapse/eh-wide-instrument-control-rescore) | published (user-approved 2026-08-20) | `808c48766db67ad1beb4e1f169de6c7b1fd5e6df` | `experiments/wide-instrument-control-rescore/analysis-committed/` (repo commit `3863884d`) | 8 files / ~101 KB copy-everything mirror: adjudication pool/graded/applied manifests plus parity, WG-G3 paired-bootstrap, and wide-gates reports. All gates passed (resolve PR #528). No row text; zero exclusions. |
| Wide-instrument control-rescore row-level exhaust | [`professorsynapse/eh-wide-instrument-control-rescore-rows`](https://huggingface.co/datasets/professorsynapse/eh-wide-instrument-control-rescore-rows) | published (user-approved 2026-08-20) | `8e93cba04e994617cfb227a6de5d5b2ada42aaa6` | staged from gitignored `experiments/wide-instrument-control-rescore/analysis/` (regenerated rows_with_generation, graded shards, id maps, adjudication_applied) | 4,430 rows / ~4.1 MB: WICR45 1,772 + WICR46 2,658. kuq (MIT) and selfaware (Apache-2.0, disclosure on card) rows carry full text; popqa/triviaqa rows text-free per license gate; zero excluded, zero FalseQA lineage. Narrow grader fields plus detector_v2 and wide adjudication fields joined from the cell's pinned lane (2,677 core-scored, 232 decoy-carved flagged as such). |
| Llama hs17 direction-specificity aggregate exhaust | [`professorsynapse/eh-llama-hs17-direction-specificity`](https://huggingface.co/datasets/professorsynapse/eh-llama-hs17-direction-specificity) | published (user-approved 2026-08-26) | `f2e4c86004c55e63d55afa9cd2116af90c543c44` | `experiments/llama-hs17-direction-specificity/analysis-committed/` (repo commit `1063f5d3`) | 3 files / ~7.8 KB aggregate-only: specificity summary (17-arm gate numbers) + README + PROVENANCE. Terminal status resolved (LG-G1/LG-G2 PASS, LG-G3 NOT-ADJUDICABLE). No row text; zero exclusions. Row-level shape not published: the run log persisted grades only, no generation text (defect recorded; see the wide-rescore follow-up cell). |
| Qwen3-4B L34 placebo-seed-census aggregate exhaust | [`professorsynapse/eh-qwen3-4b-l34-placebo-seed-census`](https://huggingface.co/datasets/professorsynapse/eh-qwen3-4b-l34-placebo-seed-census) | published (user-approved 2026-08-26) | `9dccf16109b92d3ea79169e4cd3ab12659062402` | `experiments/qwen3-4b-l34-placebo-seed-census/analysis-committed/` (repo commit `1063f5d3`) | 7 files / ~98 KB copy-everything mirror: wide-gates report (QG-G1 PASS 4.83, QG-G2 FAIL), adjudication pool/graded/applied manifests, generation manifest. Terminal status resolved (MIXED); card reports it straight. No row text; zero exclusions. Row-level shape deferred: rows carry text but no per-row source field, and the pool includes no-license FalseQA lineage pending audit. |
| Llama hs17 wide-instrument rescore aggregate exhaust | [`professorsynapse/eh-llama-hs17-wide-instrument-rescore`](https://huggingface.co/datasets/professorsynapse/eh-llama-hs17-wide-instrument-rescore) | published (user-approved 2026-08-26) | `e7de12a938f0133e047dafbdb442df62f7ca317a` | `experiments/llama-hs17-wide-instrument-rescore/analysis-committed/` (repo commit `3a66a2d7`) | 8 files / ~458 KB copy-everything mirror: wide-gates report (WR-G1 0.7305, WR-G2 lift 0.6319, WR-G3 ratio 9.34, WR-G4 NOT-ADJUDICABLE, CG1 19/19), scored summary, generation/pool/graded/applied adjudication manifests. Terminal status resolved (Outcome A). No row text; zero exclusions. Row-level shape possible for the first time on llama (text-persisting harness) but unpublished pending per-source license verdicts for the parent row pools. |
| Llama hs17 wide-instrument rescore row-level exhaust | [`professorsynapse/eh-llama-hs17-wide-instrument-rescore-rows`](https://huggingface.co/datasets/professorsynapse/eh-llama-hs17-wide-instrument-rescore-rows) | published (user-approved 2026-08-27) | `1ec3a0628488a3214df101060e71a71b856b76f5` | recovery re-run rows staged from gitignored `experiments/llama-hs17-wide-instrument-rescore/analysis/` (repo commit `984c1ac1`; incident + recovery NOTEBOOK entries 2026-08-26/27) | 15,492 rows / ~19 MB, one cell (`llama32_3b_instruct`): 14,824 full-text kuq_unknowns_all rows + 668 text-free triviaqa/popqa rows, zero excluded. Rows come from the user-approved deterministic recovery re-run after the worktree data-loss incident; pre-registered equivalence bar passed (WR-G1 637/872 reproduced exactly, manifest counts identical). Wide verdicts per row: 1,357 detector_v2 + 12,517 re-attributed by exact text join to the sha256-authenticated blind adjudication lane; 1,461 text-drift and 157 conflicting-verdict nulls, reason-coded on the row. Committed gate numbers remain the numbers of record. |
| Deployed clean-SFT to GRPO-v2 adapter (seed 1) | [`professorsynapse/eh-qwen3-4b-clean-sft-grpo-v2-seed1-lora`](https://huggingface.co/professorsynapse/eh-qwen3-4b-clean-sft-grpo-v2-seed1-lora) | published (user-approved 2026-08-01) | `8914081dfcec4f1f025f2dbe4195d4f7aa8d210e` (weights) | `scratch/schema_response_confidence/runs/schema_clean_sft_grpo_v2_seed1_full/20260624_095831/final_model` | Released as part of the Paper 2 adapter set; see that section below for the card and the post-upload revision. Staged private 2026-07-05 so cloud cells could reference it by repo + revision. |
| Paper 2 adapter set (17 Qwen3-4B checkpoints) | see the per-repo table below | published (user-approved 2026-08-01) | per repo, in the section below | `archive/experiment/phase1/run_records/` and `docs/checkpoint-staging.md` | 9 pre-registered headline adapters, 6 sequential-extension adapters, the deployed GRPO-v2 adapter, and the merged 16-bit base it loads on. Cards live in `docs/hf-cards/<repo>/README.md`. |
| Cold-start GRPO seed-1 adapter | [`professorsynapse/eh-qwen3-4b-cold-grpo-v2-seed1-lora`](https://huggingface.co/professorsynapse/eh-qwen3-4b-cold-grpo-v2-seed1-lora) | published (user-approved 2026-08-15) | `353b73c48a7d8865ad1e30e5ef5ee8b0776a3c6a` (weights) | `scratch/schema_response_confidence/runs/cold_base_grpo_v2_seed1_full/20260813_182012/final_model` | `experiments/grpo-cold-start-induction` seed 1, exploratory; registered prediction falsified, panel reads the checkpoint as preserving/sharpening prompt-elicited abstention, not inducing it. Loads on raw `unsloth/Qwen3-4B-bnb-4bit`. Staged private 2026-08-15, public same day. |
| Warmed GRPO-v2 seed-2/3 adapters | [`professorsynapse/eh-qwen3-4b-clean-sft-grpo-v2-seed2-lora`](https://huggingface.co/professorsynapse/eh-qwen3-4b-clean-sft-grpo-v2-seed2-lora), [`...seed3-lora`](https://huggingface.co/professorsynapse/eh-qwen3-4b-clean-sft-grpo-v2-seed3-lora) | published (user-approved 2026-08-15) | seed2 `2390e893bfc92aefb3d14d30805b480e8a11fda7`, seed3 `d9f24fdac820bff36e97daa6bea2fa9d0aa3a149` (weights) | `scratch/schema_response_confidence/runs/schema_clean_sft_grpo_v2_seed{2,3}_full/{20260804_131151,20260805_221744}/final_model` | `experiments/grpo-three-seed-confirmatory`, exploratory response-confidence track, G1/G2 replicated at both seeds. Each loads on its own seed-specific merged base (rows below), a registered per-seed-lineage rule. |
| Per-seed merged clean-SFT bases (seeds 2/3) | [`professorsynapse/eh-qwen3-4b-clean-sft-seed2-merged-16bit`](https://huggingface.co/professorsynapse/eh-qwen3-4b-clean-sft-seed2-merged-16bit), [`...seed3-merged-16bit`](https://huggingface.co/professorsynapse/eh-qwen3-4b-clean-sft-seed3-merged-16bit) | published (user-approved 2026-08-15) | seed2 `4d526fddce37348a325f54127426fb15f9a77bbe`, seed3 `b607b18bb0b0274b86be51d5dad29e4c2144ee2d` (weights) | `scratch/schema_response_confidence/runs/sft_schema_clean_seed{2,3}_full/{20260731_232307,20260805_163620}/Qwen3-4B-bnb-4bit/merged-16bit` | The bases the seed-2/3 GRPO-v2 adapters load on; published per PI ruling 2026-08-15 (rebuild would require retraining, unlike the sequential-adapter precedent). ~8 GB each, hub shard sizes verified vs local. |

## Paper 2 Adapter Set (public release 2026-08-01)

The 17 Qwen3-4B checkpoints behind the training-regimen paper, released from
private staging on 2026-08-01 under a single user approval. Base model for every
adapter in the set is `unsloth/Qwen3-4B-bnb-4bit` (Apache-2.0); the adapters
carry weights only (no tokenizer, no `training_args.bin`).

Each repo's card is generated in this repository at
`docs/hf-cards/<repo>/README.md` and uploaded as the repo's `README.md` by
`scripts/release/flip_paper2_adapter_set_public.py`, which then flips visibility.

Two revisions matter per repo and they are not the same commit. The **weights
revision** is the staged upload recorded in
[docs/checkpoint-staging.md](checkpoint-staging.md); it is what the card
describes and what a consumer should pin. The **head revision** is the commit
created by the card upload, recorded after the flip script runs.

| HF repo | Weights revision | Head revision (after card upload) | Backs | Status label on card |
|---|---|---|---|---|
| [`eh-qwen3-4b-headline-sft-seed1-lora`](https://huggingface.co/professorsynapse/eh-qwen3-4b-headline-sft-seed1-lora) | `535dfabec0365b80663df618880ac2ad0976eb51` | `d14e49bc9642c74df51a85908a39c3ad32edf5be` | PROTOCOL v0.3 headline SFT seed 1 | pre-registered headline result |
| [`eh-qwen3-4b-headline-sft-seed2-lora`](https://huggingface.co/professorsynapse/eh-qwen3-4b-headline-sft-seed2-lora) | `23ae0043bd794be8ede1122effd9ccfecb9d85aa` | `2ae4fc1b3bcf958750261a4a0175b2187a3514e3` | PROTOCOL v0.3 headline SFT seed 2 | pre-registered headline result |
| [`eh-qwen3-4b-headline-sft-seed3-lora`](https://huggingface.co/professorsynapse/eh-qwen3-4b-headline-sft-seed3-lora) | `b3efd6e7aa133c8ad17d35ec569335b6a858d423` | `41f4568cddf8b8e3b3bab2b4f9237901107e77ae` | PROTOCOL v0.3 headline SFT seed 3 | pre-registered headline result |
| [`eh-qwen3-4b-headline-dpo-seed1-lora`](https://huggingface.co/professorsynapse/eh-qwen3-4b-headline-dpo-seed1-lora) | `9d503e1937d361c97abae6480ecafaac19a0668f` | `d2540c43ed21395d954db4514a2fa251cc1c81bf` | PROTOCOL v0.3 headline DPO seed 1 | pre-registered headline result |
| [`eh-qwen3-4b-headline-dpo-seed2-lora`](https://huggingface.co/professorsynapse/eh-qwen3-4b-headline-dpo-seed2-lora) | `21326cbcd8a975ca3b89f8552f053392281af23e` | `bacae33dbf627539a5a768ab9ba862053b764cd5` | PROTOCOL v0.3 headline DPO seed 2 | pre-registered headline result |
| [`eh-qwen3-4b-headline-dpo-seed3-lora`](https://huggingface.co/professorsynapse/eh-qwen3-4b-headline-dpo-seed3-lora) | `dc95b05729a9b45e9335d3ac5ed84cc55f84ac81` | `d471e564314c73128444e2249731790d933cffe8` | PROTOCOL v0.3 headline DPO seed 3 | pre-registered headline result |
| [`eh-qwen3-4b-headline-kto-seed1-lora`](https://huggingface.co/professorsynapse/eh-qwen3-4b-headline-kto-seed1-lora) | `ebfa75363afe9a92c97b7032acd608359b2026f6` | `de8e6c8abdb2c531f1902d7971b3bc3bc1068c3c` | PROTOCOL v0.3 headline KTO seed 1 | pre-registered headline result |
| [`eh-qwen3-4b-headline-kto-seed2-lora`](https://huggingface.co/professorsynapse/eh-qwen3-4b-headline-kto-seed2-lora) | `5153f05b96f70314dab796d79b006ee5236680db` | `d86f6dadd4141a26feafc3f28fc8bf27eca90b3d` | PROTOCOL v0.3 headline KTO seed 2 | pre-registered headline result |
| [`eh-qwen3-4b-headline-kto-seed3-lora`](https://huggingface.co/professorsynapse/eh-qwen3-4b-headline-kto-seed3-lora) | `ce68f04723cd9cad30ff58d8037a8629a6adb486` | `80350a6d594f29b22d18f68685a69c62185ba569` | PROTOCOL v0.3 headline KTO seed 3 | pre-registered headline result |
| [`eh-qwen3-4b-seq-sft-dpo-seed1-lora`](https://huggingface.co/professorsynapse/eh-qwen3-4b-seq-sft-dpo-seed1-lora) | `45138e73be9d28fcf9537a9d2de49d90ebf8601b` | `b12821e68ee4d29c191a87f90096696efeef5e82` | Amendment A / v0.4 sequential SFT to DPO seed 1 | pre-registered extension, reported separately |
| [`eh-qwen3-4b-seq-sft-dpo-seed2-lora`](https://huggingface.co/professorsynapse/eh-qwen3-4b-seq-sft-dpo-seed2-lora) | `62c2cf65d93509ee86bdedb257512f9055a4ff1a` | `b02ec7361b449ed4fce459f78ba7566f6fc21689` | Amendment A / v0.4 sequential SFT to DPO seed 2 | pre-registered extension, reported separately |
| [`eh-qwen3-4b-seq-sft-dpo-seed3-lora`](https://huggingface.co/professorsynapse/eh-qwen3-4b-seq-sft-dpo-seed3-lora) | `9cdd0d292c1b0309c3ced096c057697c8fc969d9` | `53c34c00abf866bef0b08184bc03770992296b3a` | Amendment A / v0.4 sequential SFT to DPO seed 3 | pre-registered extension, reported separately |
| [`eh-qwen3-4b-seq-sft-kto-seed1-lora`](https://huggingface.co/professorsynapse/eh-qwen3-4b-seq-sft-kto-seed1-lora) | `2ccb2ec3883bf004feb545fb555ea3846e8c39fb` | `69df6367cfdef0be3845ae7a2ad26e91350c42fd` | Amendment A / v0.4 sequential SFT to KTO seed 1 | pre-registered extension, reported separately |
| [`eh-qwen3-4b-seq-sft-kto-seed2-lora`](https://huggingface.co/professorsynapse/eh-qwen3-4b-seq-sft-kto-seed2-lora) | `c9b38352ba852f427e0c3ed802d038f94ebf9997` | `50eb8791d1861b7cdfd0f2599a85e3a5fe560962` | Amendment A / v0.4 sequential SFT to KTO seed 2 | pre-registered extension, reported separately |
| [`eh-qwen3-4b-seq-sft-kto-seed3-lora`](https://huggingface.co/professorsynapse/eh-qwen3-4b-seq-sft-kto-seed3-lora) | `cb6c246e0e566908f7a4e4844a892d811667cf2d` | `8f30a12ce4934c0b558f13c1975cf37bd6c5c8a3` | Amendment A / v0.4 sequential SFT to KTO seed 3 | pre-registered extension, reported separately |
| [`eh-qwen3-4b-clean-sft-grpo-v2-seed1-lora`](https://huggingface.co/professorsynapse/eh-qwen3-4b-clean-sft-grpo-v2-seed1-lora) | `8914081dfcec4f1f025f2dbe4195d4f7aa8d210e` | `0b0daa7f620565bb403bb0eb2fa219590b1a2f80` | deployed clean-SFT to GRPO-v2 seed 1 (cloud cells, mech-interp lineage) | exploratory seed 1; confirmatory replication registered at `experiments/grpo-three-seed-confirmatory` |
| [`eh-qwen3-4b-clean-sft-seed1-merged-16bit`](https://huggingface.co/professorsynapse/eh-qwen3-4b-clean-sft-seed1-merged-16bit) | `ac361232c001af0ed5b0386b06dafc35d5cd31ea` | `d8f604af12cc2842ecf2f2d5f6c0bc00b7f6b7c1` | merged 16-bit clean schema-SFT seed 1; the base the GRPO-v2 adapter loads on | exploratory seed 1; confirmatory replication registered |

Notes on this release:

- The six sequential-extension adapters were trained on a local 16-bit merge of
  the same-seed headline SFT adapter. That merge is not published; each card
  gives the rebuild recipe (foundation model plus the published same-seed SFT
  adapter, merged) and states that the rebuild is not guaranteed bit-identical
  to the local artifact.
- The GRPO-v2 adapter loads on the merged 16-bit base in this same set, not on
  `unsloth/Qwen3-4B-bnb-4bit`. Both are released together for that reason.
- Headline and extension numbers are never pooled. Card status labels carry the
  distinction so a reader of one repo page cannot mistake an extension arm for a
  headline cell.
- Training data for the set is the already-published
  [`professorsynapse/epistemic-humility-phase1`](https://huggingface.co/datasets/professorsynapse/epistemic-humility-phase1)
  dataset; no new data is released here.
- The six headline DPO and KTO cards carry a data-provenance caveat: seed 1 of
  each arm consumed the dataset build predating the dev-split fix of 2026-06-14
  (commit `3dc58e9b`), seeds 2 and 3 consumed the corrected build, and the cards
  state that the arm's three-seed interval therefore spans two dataset versions.
  The three SFT cards carry no caveat because all three SFT seeds consumed the
  corrected build. A rerun of the two affected seed-1 runs is registered
  separately.

## Pending HF Repos

| Artifact family | Proposed HF repo | Status | Local provenance | Notes |
|---|---|---|---|---|
| Hidden-state tensors | `professorsynapse/eh-hidden-states-<family>` | planned (wave 2d) | extraction dirs under `archive/experiment/phase1/probe/` | ~2 GB per model; Z families first. Y cloud cells discard extraction dirs by design — publishing Y tensors would need the upload knob flipped in `hf_jobs_cell.sh` for future cells. |
| Adapter repos | one repo per evaluated adapter | 17 released 2026-08-01; the remainder private-staged (2026-07-05) | run record + `training_lineage.json` + exact eval result path | 33 Qwen3-4B LoRA/merged checkpoints are staged on HF; the master mapping (HF repo @ revision <-> local source run dir <-> amendment/paper it backs) is [docs/checkpoint-staging.md](checkpoint-staging.md). The 17 Paper 2 repos are now public (see the Paper 2 adapter set section above). Public release of any remaining repo is a separate per-release user approval and would be recorded as its own row. |

## Adapter Naming

Use one model repo per released adapter:

```text
professorsynapse/eh-qwen3-4b-clean-sft-seed1-lora
professorsynapse/eh-qwen3-4b-clean-sft-dpo-seed1-lora
professorsynapse/eh-qwen3-4b-clean-sft-kto-seed1-lora
professorsynapse/eh-qwen3-4b-clean-sft-grpo-seed1-lora
```

For stacked runs, keep stage order explicit:

```text
professorsynapse/eh-qwen3-4b-clean-sft-dpo-grpo-seed1-lora
professorsynapse/eh-qwen3-4b-clean-sft-grpo-kto-seed1-lora
```

## Publication Gate

Before uploading a model artifact:

1. Confirm the run record is completed and not stale.
2. Confirm eval has run on the artifact intended for release.
3. Confirm the result is not marked as a failed or diagnostic-only run in the
   session note or provenance inventory.
4. Confirm `training_lineage.json` exists or can be generated.
5. Confirm the base model license allows public adapter release.
6. Confirm the upload is public unless the user explicitly approves a private
   temporary cloud-extraction artifact.

Before uploading datasets or eval rows:

1. Confirm source license permits redistribution.
2. Exclude restricted bridge/OpenMOSS/Cheng raw data.
3. Include schema and dataset-card provenance.
4. Pin and record the HF dataset revision after upload.

## Upload Path

Use the Synaptic Tuner upload-deployment workflow; do not create a parallel
uploader in this repo.

From `synaptic-tuner/`:

```bash
python .skills/upload-deployment/scripts/upload_model.py \
  PATH/TO/final_model \
  professorsynapse/eh-qwen3-4b-clean-sft-seed1-lora \
  --save-method lora \
  --training-lineage PATH/TO/training_lineage.json
```

For the first public release wave, prefer `--save-method lora`. Merged 16-bit
or GGUF releases should be deliberate reference artifacts, not the default.

After upload, update this file with:

- HF repo URL
- HF revision SHA
- local run record path
- eval result path
- caveats or exclusion notes

## Do Not Publish

- OpenMOSS / Cheng bridge raw data.
- Gated Llama-derived artifacts unless the license and user approval explicitly
  allow the exact release.
- Local HF caches, Docker outputs, scratch directories, or unreviewed checkpoints.
- Failed GRPO/reward-diagnostic runs as model repos unless intentionally released
  as negative-control artifacts with prominent model-card warnings.
