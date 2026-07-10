# Phase 3 Hidden-State Diagnostic Summary

Status: Tier 1 local diagnostic summary
Created: 2026-06-18
Scope: existing Qwen3-4B hidden-state extraction artifacts

## Purpose

This note summarizes the existing hidden-state diagnostic artifacts before any
new causal intervention. It is a Tier 1 correlational baseline: the linear
probes and candidate directions can identify known/unknown separability, but
they do not prove that a direction controls abstention behavior.

## Artifact Inventory

All comparable 128 known / 128 unknown extractions below have manifest
`status=ok` and `verified=true`. Balanced accuracy values are from the existing
5-fold diagnostic linear-probe outputs.

| Extraction | Active adapter | Aligned run record | Base model identity | Rows | Best h_base | Best h_lora | Best delta |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| `extraction__12fb10b1c8c8` | `sft` | `sft__4b__headline__seed1` | `unsloth/Qwen3-4B-bnb-4bit` | 256 | 0.753906 L25 | 0.863281 L36 | 0.855469 L35 |
| `extraction__f3dbd2c1754a` | `dpo` | `dpo__4b__headline__seed1` | `unsloth/Qwen3-4B-bnb-4bit` | 256 | 0.753906 L25 | 0.773438 L35 | 0.750000 L35 |
| `extraction__0810aa2972e8` | `kto` | `kto__4b__headline__seed1` | `unsloth/Qwen3-4B-bnb-4bit` | 256 | 0.753906 L25 | 0.765625 L36 | 0.750000 L26 |
| `extraction__0d58c201ab3e` | `sft_dpo` | `sft_dpo__4b__amendment_a__seed1` | merged SFT seed 1 | 256 | 0.843750 L36 | 0.855469 L34 | 0.859375 L35 |
| `extraction__e1473df788a5` | `sft_kto` | `sft_kto__4b__amendment_a__seed1` | merged SFT seed 1 | 256 | 0.843750 L36 | 0.859375 L35 | 0.855469 L36 |

Smaller smoke extractions also exist:

| Extraction | Active adapter | Rows | Note |
| --- | --- | ---: | --- |
| `extraction__520184798388` | `sft` | 2 | Tiny pipeline smoke, not comparable. |
| `extraction__c35b3f3bf8ae` | `sft` | 32 | Small SFT smoke; useful for tooling, not the main comparative readout. |

## Readout

The base pass is identical across cold-start SFT/DPO/KTO extractions, with best
`h_base` balanced accuracy of `0.753906` at layer 25. The SFT active-adapter
state and LoRA delta show much stronger known/unknown separability than
cold-start DPO/KTO:

- SFT `h_lora`: `0.863281` at layer 36.
- SFT `delta`: `0.855469` at layer 35.
- Cold-start DPO/KTO `h_lora`: about `0.77`.
- Cold-start DPO/KTO `delta`: about `0.75`.

The sequential extractions use merged SFT as the base, so their `h_base` already
contains the SFT shift. In that setting, both `SFT -> DPO` and `SFT -> KTO`
retain high separability:

- `SFT -> DPO` best delta: `0.859375` at layer 35.
- `SFT -> KTO` best delta: `0.855469` at layer 36.

Plain language: SFT appears to create or expose a stronger known/unknown
representation on this slice, and sequential preference training does not erase
that separability. Cold-start DPO/KTO do not show the same active-adapter shift.

## Current Candidate Directions

The first causal-pilot readiness config prioritizes:

| Priority | Candidate | Role | Layer | Direction id | Existing balanced accuracy |
| ---: | --- | --- | ---: | --- | ---: |
| 1 | SFT active-adapter known/unknown direction | `h_lora` | 36 | `direction__9c8c74f718038292` | 0.863281 |
| 2 | SFT LoRA-delta known/unknown direction | `delta` | 35 | `direction__8bb10838ed21eebe` | 0.855469 |

Both directions come from
`experiment/phase1/probe/qwen3-4b-instruct/hidden_states/extraction__12fb10b1c8c8/`
and are already referenced by
`archive/experiment/phase1/probe/config/causal-pilot-core/phase3_causal_pilot_smoke.yaml`.

## Interpretation Limits

- This is not Phase 1 headline evidence.
- This is not proof that the direction causes abstention.
- Known/unknown separability can reflect task format, recall strength, or other
  correlates.
- Safety-refusal directions and epistemic-abstention directions must remain
  conceptually separate.
- Any intervention output must remain Tier 2 exploratory local evidence unless
  a later signed protocol revision promotes it.

## Next Step

The next useful test is a very small activation-addition/subtraction smoke on
the SFT `h_lora` layer-36 direction, with:

- same frozen row ids as the extraction slice;
- no-vector baseline;
- sign-flip control;
- random and shuffled-label controls before broad scaling;
- fixed `enable_thinking=false`;
- refusal/correctness/stated-confidence scoring separated from any Phase 1
  headline table.
