# Checkpoint Staging Registry

This file is the private-staging registry for model checkpoints published to the
Hugging Face Hub as PRIVATE artifacts. It is the counterpart to
[docs/public-artifacts.md](public-artifacts.md): public releases live there, and
private staging lives here. A checkpoint appears here so that cloud cells,
amendments, and paper provenance can point to a durable HF address instead of a
local scratch path that only exists on one machine.

All rows below are PRIVATE unless a later public release is recorded in
docs/public-artifacts.md. Public release is a separate per-release user approval,
not implied by staging. The Visibility column names the release record for any
row that has one; 17 rows carry the Paper 2 adapter set release of 2026-08-01.

Base model for every adapter is unsloth/Qwen3-4B-bnb-4bit (Apache-2.0); the LoRA
adapters were staged without a bundled README (the auto-README carries a local
base_model path that fails HF YAML validation) and without training_args.bin.
Consumers load the base explicitly and apply the adapter. Released repos carry a
hand-written card instead, generated at `docs/hf-cards/<repo>/README.md` with a
hub base_model id; do not re-enable the auto-README on any repo.

Staged 2026-07-05 via huggingface_hub upload_folder (private), commit message on
each repo records the source run dir and date.

## Registry

| HF repo | Revision | Local source run dir | Backs | Staged | Visibility |
|---|---|---|---|---|---|
| **Pre-existing staged repos (context)** | | | | | |
| [`professorsynapse/eh-qwen3-4b-clean-sft-grpo-v2-seed1-lora`](https://huggingface.co/professorsynapse/eh-qwen3-4b-clean-sft-grpo-v2-seed1-lora) | `8914081dfcec4f1f025f2dbe4195d4f7aa8d210e` | `scratch/schema_response_confidence/runs/schema_clean_sft_grpo_v2_seed1_full/20260624_095831/final_model` | clean-SFT->GRPO-v2 seed1 (deployed checkpoint; cloud cells + AJ/AK) | 2026-07-05 | public 2026-08-01 (see [public-artifacts.md](public-artifacts.md)) |
| [`professorsynapse/eh-qwen3-4b-clean-sft-grpo-par-true-seed1-lora`](https://huggingface.co/professorsynapse/eh-qwen3-4b-clean-sft-grpo-par-true-seed1-lora) | `7e31d3cf62395275d4ba3d1d9ec8f95287188805` | `scratch/schema_response_confidence/runs/amendment_ai_grpo_true_seed1/20260703_234933/final_model` | Amendment AI PAR true-arm seed1 | 2026-07-05 | private |
| [`professorsynapse/eh-qwen3-4b-clean-sft-grpo-par-permuted-seed1-lora`](https://huggingface.co/professorsynapse/eh-qwen3-4b-clean-sft-grpo-par-permuted-seed1-lora) | `cc2998395e73d18ae3b6d02a71356d1f7904892d` | `scratch/schema_response_confidence/runs/amendment_ai_grpo_permuted_seed1/20260704_125922/final_model` | Amendment AI PAR permuted control seed1 | 2026-07-05 | private |
| [`professorsynapse/eh-qwen3-4b-clean-sft-seed1-merged-16bit`](https://huggingface.co/professorsynapse/eh-qwen3-4b-clean-sft-seed1-merged-16bit) | `ac361232c001af0ed5b0386b06dafc35d5cd31ea` | `scratch/schema_response_confidence/runs/sft_schema_clean_seed1_full/20260623_123624/Qwen3-4B-bnb-4bit/merged-16bit` | clean-schema-SFT seed1 MERGED 16-bit base (loaded by schema-family adapters) | 2026-07-05 | public 2026-08-01 (see [public-artifacts.md](public-artifacts.md)) |
| **Staged 2026-07-05 (this pass)** | | | | | |
| [`professorsynapse/eh-qwen3-4b-clean-sft-seed1-lora`](https://huggingface.co/professorsynapse/eh-qwen3-4b-clean-sft-seed1-lora) | `869ddf2b02d34072cdd085f1642d67611df6975c` | `scratch/schema_response_confidence/runs/sft_schema_clean_seed1_full/20260623_123624/final_model` | clean-schema-SFT seed1 (parent base adapter for schema family) | 2026-07-05 | private |
| [`professorsynapse/eh-qwen3-4b-clean-sft-grpo-v3-seed1-lora`](https://huggingface.co/professorsynapse/eh-qwen3-4b-clean-sft-grpo-v3-seed1-lora) | `9ddeecdf685be004f12fcb61ede291c41dd69262` | `scratch/schema_response_confidence/runs/schema_clean_sft_grpo_v3_seed1_full/20260627_115816/final_model` | Amendment J (GRPO-v3 proper-scoring) seed1 | 2026-07-05 | private |
| [`professorsynapse/eh-qwen3-4b-contrastive-sft-grpo-v3-seed1-lora`](https://huggingface.co/professorsynapse/eh-qwen3-4b-contrastive-sft-grpo-v3-seed1-lora) | `c6451853c047e76a8b3263740444e8e4a045f6fe` | `scratch/schema_response_confidence/runs/schema_contrastive_sft_grpo_v3_seed1_full/20260628_093753/final_model` | Amendment N (GRPO-v3 on contrastive base) seed1 | 2026-07-05 | private |
| [`professorsynapse/eh-qwen3-4b-clean-sft-dpo-seed1-lora`](https://huggingface.co/professorsynapse/eh-qwen3-4b-clean-sft-dpo-seed1-lora) | `5808fcf931794027cb2c14c35796d771904dbf9c` | `scratch/schema_response_confidence/runs/schema_clean_sft_dpo_seed1_full/20260623_132930/final_model` | clean-SFT+DPO seed1 (Amendment D/E/F arm) | 2026-07-05 | private |
| [`professorsynapse/eh-qwen3-4b-clean-sft-kto-seed1-lora`](https://huggingface.co/professorsynapse/eh-qwen3-4b-clean-sft-kto-seed1-lora) | `8c3243055e39b81f2f80eb9af6445a75052ff9ce` | `scratch/schema_response_confidence/runs/schema_clean_sft_kto_seed1_full/20260623_200200/final_model` | clean-SFT+KTO seed1 (Amendment D/E/F arm) | 2026-07-05 | private |
| [`professorsynapse/eh-qwen3-4b-clean-sft-grpo-dpo-seed1-lora`](https://huggingface.co/professorsynapse/eh-qwen3-4b-clean-sft-grpo-dpo-seed1-lora) | `865aa404abf7159704c5be531c6dd3c5f9944205` | `scratch/schema_response_confidence/runs/clean_sft_grpo_dpo_seed1_full/20260625_031724/final_model` | Amendment F three-stage stack SFT->GRPO->DPO seed1 | 2026-07-05 | private |
| [`professorsynapse/eh-qwen3-4b-clean-sft-dpo-grpo-seed1-lora`](https://huggingface.co/professorsynapse/eh-qwen3-4b-clean-sft-dpo-grpo-seed1-lora) | `29f10ed9443585a359927b220c05c8b623d252ab` | `scratch/schema_response_confidence/runs/clean_sft_dpo_grpo_seed1_full/20260624_193929/final_model` | Amendment F three-stage stack SFT->DPO->GRPO seed1 | 2026-07-05 | private |
| [`professorsynapse/eh-qwen3-4b-clean-sft-grpo-kto-seed1-lora`](https://huggingface.co/professorsynapse/eh-qwen3-4b-clean-sft-grpo-kto-seed1-lora) | `1a7bcf65d4436649f902b6f424ec8c8618ff4263` | `scratch/schema_response_confidence/runs/clean_sft_grpo_kto_seed1_full/20260625_052610/final_model` | Amendment F three-stage stack SFT->GRPO->KTO seed1 | 2026-07-05 | private |
| [`professorsynapse/eh-qwen3-4b-clean-sft-kto-grpo-seed1-lora`](https://huggingface.co/professorsynapse/eh-qwen3-4b-clean-sft-kto-grpo-seed1-lora) | `674d38e956e161b7dfa23b3266681a99e97769ff` | `scratch/schema_response_confidence/runs/clean_sft_kto_grpo_seed1_full/20260625_012319/final_model` | Amendment F three-stage stack SFT->KTO->GRPO seed1 | 2026-07-05 | private |
| [`professorsynapse/eh-qwen3-4b-contrastive-sft-seed1-lora`](https://huggingface.co/professorsynapse/eh-qwen3-4b-contrastive-sft-seed1-lora) | `ff1f5f316829c4b927ad96516a7637a7c83bec31` | `scratch/schema_response_confidence/runs/sft_schema_contrastive_seed1_full/20260627_203232/final_model` | Amendment K contrastive schema-SFT seed1 (base for N) | 2026-07-05 | private |
| [`professorsynapse/eh-qwen3-4b-contrastive-masked-sft-seed1-lora`](https://huggingface.co/professorsynapse/eh-qwen3-4b-contrastive-masked-sft-seed1-lora) | `a22dbd291b54df6c008da91d5179bf31fbcd099a` | `scratch/schema_response_confidence/runs/sft_schema_contrastive_masked_seed1_full/20260627_amendmentL_full/final_model` | Amendment L answer-subspan-masked contrastive-SFT seed1 | 2026-07-05 | private |
| [`professorsynapse/eh-qwen3-4b-probe-factual-sft-seed1-lora`](https://huggingface.co/professorsynapse/eh-qwen3-4b-probe-factual-sft-seed1-lora) | `0a66f03cd20ea19d578f28606f99fd702fc7fea9` | `scratch/schema_response_confidence/runs/sft_schema_probe_factual_seed1_full/20260629_111239/final_model` | Amendment M quantile-balanced probe-distilled SFT seed1 | 2026-07-05 | private |
| [`professorsynapse/eh-qwen3-4b-probe-scaled-sft-seed1-lora`](https://huggingface.co/professorsynapse/eh-qwen3-4b-probe-scaled-sft-seed1-lora) | `997b2a523b65298326707857c223f860f2095476` | `scratch/schema_response_confidence/runs/sft_schema_probe_scaled_seed1_full/20260623_095638/final_model` | Amendment E probe-scaled response-confidence SFT seed1 | 2026-07-05 | private |
| [`professorsynapse/eh-qwen3-4b-contrastive-sft-grpo-v3-beta005-seed1-lora`](https://huggingface.co/professorsynapse/eh-qwen3-4b-contrastive-sft-grpo-v3-beta005-seed1-lora) | `b158a9a88cfab36ea089f014d228ddf5ca76809a` | `scratch/schema_response_confidence/runs/schema_contrastive_sft_grpo_v3_beta005_seed1_full/20260629_010141/final_model` | Amendment N beta=0.05 GRPO-v3 on contrastive base seed1 | 2026-07-05 | private |
| [`professorsynapse/eh-qwen3-4b-headline-sft-seed1-lora`](https://huggingface.co/professorsynapse/eh-qwen3-4b-headline-sft-seed1-lora) | `535dfabec0365b80663df618880ac2ad0976eb51` | `synaptic-tuner/toolset-training-artifacts/runs/local/4b/sft__4b__headline__seed1/20260614_053221/final_model` | Paper 2 headline SFT seed1 (v0.3 matrix) | 2026-07-05 | public 2026-08-01 (see [public-artifacts.md](public-artifacts.md)) |
| [`professorsynapse/eh-qwen3-4b-headline-sft-seed2-lora`](https://huggingface.co/professorsynapse/eh-qwen3-4b-headline-sft-seed2-lora) | `23ae0043bd794be8ede1122effd9ccfecb9d85aa` | `synaptic-tuner/toolset-training-artifacts/runs/local/4b/sft__4b__headline__seed2/20260615_090734/final_model` | Paper 2 headline SFT seed2 (v0.3 matrix) | 2026-07-05 | public 2026-08-01 (see [public-artifacts.md](public-artifacts.md)) |
| [`professorsynapse/eh-qwen3-4b-headline-sft-seed3-lora`](https://huggingface.co/professorsynapse/eh-qwen3-4b-headline-sft-seed3-lora) | `b3efd6e7aa133c8ad17d35ec569335b6a858d423` | `synaptic-tuner/toolset-training-artifacts/runs/local/4b/sft__4b__headline__seed3/20260615_104507/final_model` | Paper 2 headline SFT seed3 (v0.3 matrix) | 2026-07-05 | public 2026-08-01 (see [public-artifacts.md](public-artifacts.md)) |
| [`professorsynapse/eh-qwen3-4b-headline-dpo-seed1-lora`](https://huggingface.co/professorsynapse/eh-qwen3-4b-headline-dpo-seed1-lora) | `9d503e1937d361c97abae6480ecafaac19a0668f` | `synaptic-tuner/toolset-training-artifacts/runs/local/4b/dpo__4b__headline__seed1/20260611_211512/final_model` | Paper 2 headline DPO seed1 (v0.3 matrix) | 2026-07-05 | public 2026-08-01 (see [public-artifacts.md](public-artifacts.md)) |
| [`professorsynapse/eh-qwen3-4b-headline-dpo-seed2-lora`](https://huggingface.co/professorsynapse/eh-qwen3-4b-headline-dpo-seed2-lora) | `21326cbcd8a975ca3b89f8552f053392281af23e` | `synaptic-tuner/toolset-training-artifacts/runs/local/4b/dpo__4b__headline__seed2/20260615_114512/final_model` | Paper 2 headline DPO seed2 (v0.3 matrix) | 2026-07-05 | public 2026-08-01 (see [public-artifacts.md](public-artifacts.md)) |
| [`professorsynapse/eh-qwen3-4b-headline-dpo-seed3-lora`](https://huggingface.co/professorsynapse/eh-qwen3-4b-headline-dpo-seed3-lora) | `dc95b05729a9b45e9335d3ac5ed84cc55f84ac81` | `synaptic-tuner/toolset-training-artifacts/runs/local/4b/dpo__4b__headline__seed3/20260615_130441/final_model` | Paper 2 headline DPO seed3 (v0.3 matrix) | 2026-07-05 | public 2026-08-01 (see [public-artifacts.md](public-artifacts.md)) |
| [`professorsynapse/eh-qwen3-4b-headline-kto-seed1-lora`](https://huggingface.co/professorsynapse/eh-qwen3-4b-headline-kto-seed1-lora) | `ebfa75363afe9a92c97b7032acd608359b2026f6` | `synaptic-tuner/toolset-training-artifacts/runs/local/4b/kto__4b__headline__seed1/20260613_151337_logging_patch/final_model` | Paper 2 headline KTO seed1 (v0.3 matrix) | 2026-07-05 | public 2026-08-01 (see [public-artifacts.md](public-artifacts.md)) |
| [`professorsynapse/eh-qwen3-4b-headline-kto-seed2-lora`](https://huggingface.co/professorsynapse/eh-qwen3-4b-headline-kto-seed2-lora) | `5153f05b96f70314dab796d79b006ee5236680db` | `synaptic-tuner/toolset-training-artifacts/runs/local/4b/kto__4b__headline__seed2/20260615_142046_logging_patch/final_model` | Paper 2 headline KTO seed2 (v0.3 matrix) | 2026-07-05 | public 2026-08-01 (see [public-artifacts.md](public-artifacts.md)) |
| [`professorsynapse/eh-qwen3-4b-headline-kto-seed3-lora`](https://huggingface.co/professorsynapse/eh-qwen3-4b-headline-kto-seed3-lora) | `ce68f04723cd9cad30ff58d8037a8629a6adb486` | `synaptic-tuner/toolset-training-artifacts/runs/local/4b/kto__4b__headline__seed3/20260615_204215_logging_patch/final_model` | Paper 2 headline KTO seed3 (v0.3 matrix) | 2026-07-05 | public 2026-08-01 (see [public-artifacts.md](public-artifacts.md)) |
| [`professorsynapse/eh-qwen3-4b-seq-sft-dpo-seed1-lora`](https://huggingface.co/professorsynapse/eh-qwen3-4b-seq-sft-dpo-seed1-lora) | `45138e73be9d28fcf9537a9d2de49d90ebf8601b` | `synaptic-tuner/toolset-training-artifacts/runs/local/4b/sft_dpo__4b__amendment_a__seed1/20260614_074933/final_model` | Amendment A sequential SFT->DPO seed1 | 2026-07-05 | public 2026-08-01 (see [public-artifacts.md](public-artifacts.md)) |
| [`professorsynapse/eh-qwen3-4b-seq-sft-dpo-seed2-lora`](https://huggingface.co/professorsynapse/eh-qwen3-4b-seq-sft-dpo-seed2-lora) | `62c2cf65d93509ee86bdedb257512f9055a4ff1a` | `synaptic-tuner/toolset-training-artifacts/runs/local/4b/sft_dpo__4b__amendment_a__seed2/20260616_164539/final_model` | Amendment A sequential SFT->DPO seed2 | 2026-07-05 | public 2026-08-01 (see [public-artifacts.md](public-artifacts.md)) |
| [`professorsynapse/eh-qwen3-4b-seq-sft-dpo-seed3-lora`](https://huggingface.co/professorsynapse/eh-qwen3-4b-seq-sft-dpo-seed3-lora) | `9cdd0d292c1b0309c3ced096c057697c8fc969d9` | `synaptic-tuner/toolset-training-artifacts/runs/local/4b/sft_dpo__4b__amendment_a__seed3/20260616_130451/final_model` | Amendment A sequential SFT->DPO seed3 | 2026-07-05 | public 2026-08-01 (see [public-artifacts.md](public-artifacts.md)) |
| [`professorsynapse/eh-qwen3-4b-seq-sft-kto-seed1-lora`](https://huggingface.co/professorsynapse/eh-qwen3-4b-seq-sft-kto-seed1-lora) | `2ccb2ec3883bf004feb545fb555ea3846e8c39fb` | `synaptic-tuner/toolset-training-artifacts/runs/local/4b/sft_kto__4b__amendment_a__seed1/20260614_085358/final_model` | Amendment A sequential SFT->KTO seed1 | 2026-07-05 | public 2026-08-01 (see [public-artifacts.md](public-artifacts.md)) |
| [`professorsynapse/eh-qwen3-4b-seq-sft-kto-seed2-lora`](https://huggingface.co/professorsynapse/eh-qwen3-4b-seq-sft-kto-seed2-lora) | `c9b38352ba852f427e0c3ed802d038f94ebf9997` | `synaptic-tuner/toolset-training-artifacts/runs/local/4b/sft_kto__4b__amendment_a__seed2/20260616_183650/final_model` | Amendment A sequential SFT->KTO seed2 | 2026-07-05 | public 2026-08-01 (see [public-artifacts.md](public-artifacts.md)) |
| [`professorsynapse/eh-qwen3-4b-seq-sft-kto-seed3-lora`](https://huggingface.co/professorsynapse/eh-qwen3-4b-seq-sft-kto-seed3-lora) | `cb6c246e0e566908f7a4e4844a892d811667cf2d` | `synaptic-tuner/toolset-training-artifacts/runs/local/4b/sft_kto__4b__amendment_a__seed3/20260617_070334/final_model` | Amendment A sequential SFT->KTO seed3 | 2026-07-05 | public 2026-08-01 (see [public-artifacts.md](public-artifacts.md)) |

| **Staged 2026-08-15 (paper-2 GRPO set)** | | | | | |
| [`professorsynapse/eh-qwen3-4b-cold-grpo-v2-seed1-lora`](https://huggingface.co/professorsynapse/eh-qwen3-4b-cold-grpo-v2-seed1-lora) | `353b73c48a7d8865ad1e30e5ef5ee8b0776a3c6a` | `scratch/schema_response_confidence/runs/cold_base_grpo_v2_seed1_full/20260813_182012/final_model` | `experiments/grpo-cold-start-induction` seed1 (exploratory; registered prediction falsified) | 2026-08-15 | public 2026-08-15 |
| [`professorsynapse/eh-qwen3-4b-clean-sft-grpo-v2-seed2-lora`](https://huggingface.co/professorsynapse/eh-qwen3-4b-clean-sft-grpo-v2-seed2-lora) | `2390e893bfc92aefb3d14d30805b480e8a11fda7` | `scratch/schema_response_confidence/runs/schema_clean_sft_grpo_v2_seed2_full/20260804_131151/final_model` | `experiments/grpo-three-seed-confirmatory` GRPO-v2 seed2 | 2026-08-15 | public 2026-08-15 |
| [`professorsynapse/eh-qwen3-4b-clean-sft-grpo-v2-seed3-lora`](https://huggingface.co/professorsynapse/eh-qwen3-4b-clean-sft-grpo-v2-seed3-lora) | `d9f24fdac820bff36e97daa6bea2fa9d0aa3a149` | `scratch/schema_response_confidence/runs/schema_clean_sft_grpo_v2_seed3_full/20260805_221744/final_model` | `experiments/grpo-three-seed-confirmatory` GRPO-v2 seed3 | 2026-08-15 | public 2026-08-15 |
| [`professorsynapse/eh-qwen3-4b-clean-sft-seed2-merged-16bit`](https://huggingface.co/professorsynapse/eh-qwen3-4b-clean-sft-seed2-merged-16bit) | `4d526fddce37348a325f54127426fb15f9a77bbe` | `scratch/schema_response_confidence/runs/sft_schema_clean_seed2_full/20260731_232307/Qwen3-4B-bnb-4bit/merged-16bit` | base for GRPO-v2 seed2 adapter (per-seed lineage rule) | 2026-08-15 | public 2026-08-15 |
| [`professorsynapse/eh-qwen3-4b-clean-sft-seed3-merged-16bit`](https://huggingface.co/professorsynapse/eh-qwen3-4b-clean-sft-seed3-merged-16bit) | `b607b18bb0b0274b86be51d5dad29e4c2144ee2d` | `scratch/schema_response_confidence/runs/sft_schema_clean_seed3_full/20260805_163620/Qwen3-4B-bnb-4bit/merged-16bit` | base for GRPO-v2 seed3 adapter (per-seed lineage rule) | 2026-08-15 | public 2026-08-15 |

## Known gaps

- json-bridge full-run LoRA adapter is LOST. The config-referenced run
  `scratch/grpo_bootstrap/runs/sft_json_bridge_seed1_full/20260621_111743/` has
  no `final_model` (only `logs/` and `training_lineage.json`); the sibling
  `.../20260621_111544/` holds only `checkpoints/`. The merged-16bit form
  survives at
  `scratch/grpo_bootstrap/runs/sft_merged_seed1_json_bridge/20260621_102859/merged-16bit`
  (~7.6 GB). Low stakes: json-bridge is exploratory GRPO-bootstrap lineage, not a
  paper claim, so the adapter was not re-staged. Recorded here so the provenance
  hole is not rediscovered later.
- Excluded by policy and confirmed absent on disk: FalseQA-derived checkpoints
  and Llama-2 bridge checkpoints (none exist locally; never to be staged).
- The clean-schema-SFT seed1 run has TWO staged artifacts that map to DIFFERENT
  repos: the merged 16-bit base (`.../Qwen3-4B-bnb-4bit/merged-16bit` ->
  `eh-qwen3-4b-clean-sft-seed1-merged-16bit`) and the LoRA adapter
  (`.../final_model` -> `eh-qwen3-4b-clean-sft-seed1-lora`). Config comment
  pointers distinguish the two by exact path.

## Cross-reference

- Public releases and the publication gate: [docs/public-artifacts.md](public-artifacts.md).
- Which amendment each repo backs is the "Backs" column above; signed amendment
  protocol docs are governed and are not edited to add these pointers.
