# Open-Weights Model Landscape — Phase 1 Pin Survey

**Author:** preparer-models (PACT Prepare, team pact-6d29f2e2)
**Date:** 2026-06-10 · **Worktree:** `.worktrees/phase1-pipeline`
**Purpose:** Verified survey of the current (mid-2026) open-weights model landscape against the
Phase 1 pin criteria, ending in a ranked shortlist so the user can make the final model-family
pin for paper 2 (SFT vs DPO vs KTO abstention training).

> **Provenance discipline (HANDOFF.md §5):** Every factual claim below — model existence, exact
> sizes, license, release date, modality — carries a source URL + access date. All access dates
> are **2026-06-10**. Availability was verified against live Hugging Face model cards and vendor
> release notes, NOT from training-data memory.

---

## 1. Executive Summary

The landscape has moved well past the stale Qwen2.5 pin in `PROTOCOL.md`. As of June 2026 there
are several current open-weights instruct families with a small (~3-4B) + mid (~8-14B) pairing,
stable Hugging Face support, and Unsloth LoRA paths that fit a 24GB RTX 3090 at the small size.

**The cleanest fit for this experiment is Qwen3 (the 2505 generation: 1.7B / 4B / 8B dense).**
It is the only current family that is simultaneously (a) **text-only** — most 2026 small models
(Qwen3.5, Gemma 3, Mistral 3) have gained vision encoders, which adds avoidable complexity to a
pure text-QA abstention study; (b) **Apache 2.0** with no gating, satisfying the
release-adapters-and-outputs requirement outright; (c) sized at a near-exact 4B-pilot / 8B-confirm
pairing; and (d) a first-class Unsloth target with a dedicated fine-tune guide. Its one wrinkle —
a thinking / non-thinking mode toggle — is controllable (`enable_thinking=False` / `/no_think`)
and can be pinned off for a clean non-reasoning abstention study.

**Runner-up: Phi-4-mini-instruct (3.8B) + Phi-4 (14B), both MIT.** The most permissive license in
the field and text-only, but the size jump is 3.8B → 14B (no ~7-8B middle), making the "confirm"
arm heavier than the trajectory's ~7-8B target and pushing the mid arm firmly to cloud.

**Critical infra finding for the architect and preparer-infra:** the tuner's preset story is
**split and partly stale**. The KTO path (`Trainers/kto/train_kto.py`) still hardcodes
`unsloth/Qwen2.5-3B/7B-Instruct-bnb-4bit` behind `--qwen-3b` / `--qwen-7b` — exactly the stale
PROTOCOL pin. But the SFT recipes have **already migrated to Qwen3.5** (`Qwen/Qwen3.5-2B/4B/9B`)
and carry a note that Qwen3.5 needs `transformers>=5.2.0`, newer than the stock Unsloth image
(`transformers==4.57.1`). So "what the presets target today" is **not** uniformly Qwen2.5 — it is
Qwen2.5 for KTO and Qwen3.5 for SFT. Any pin other than Qwen2.5 requires preset work in the KTO
trainer regardless; a Qwen3 pin is the smallest such delta because the model-family branching in
`train_sft.py` already has a `"qwen"` arm.

---

## 2. Pin Criteria (from `research-trajectory.md` §Model strategy + team-lead clarifications)

| # | Criterion | Hard / Soft | Notes |
|---|-----------|-------------|-------|
| C1 | Open weights, downloadable | Hard | — |
| C2 | Instruct / chat variant exists | Hard | base+instruct both useful; instruct is the pin target |
| C3 | Two sizes: ~3B pilot + ~7-8B confirm | **Soft** | team-lead confirmed: adjacent breakpoints (4B+8B, 4B+12B) OK because comparison is within-model across methods |
| C4 | Small size LoRA-trainable on **single RTX 3090 (24GB)** locally | **Hard** | This is THE hard constraint. Mid size targets HF Jobs (cloud) and need not fit 24GB. |
| C5 | Stable HF Transformers / PEFT support | Hard | + Unsloth, since the tuner's stack is Unsloth |
| C6 | License permits research use + **releasing adapters/outputs/per-model labels** | Hard | paper 2 releases everything (HANDOFF §5) |

**Additional design-fit factors (not in the original criteria, surfaced during the survey):**
- **Text-only vs multimodal.** A vision encoder is dead weight (and a behavioral confound) for a
  text-QA abstention study. Several strong 2026 small models are now multimodal-by-default.
- **Thinking / reasoning mode.** Reasoning-by-default models inject `<think>` traces that
  complicate truthful-rate / abstention parsing and token-ECE. Prefer a model where plain
  non-reasoning generation is the clean default or a one-flag toggle.

---

## 3. Candidate Survey (verified)

All rows verified against live HF model cards on **2026-06-10**. "3090 LoRA" = feasibility of
LoRA/QLoRA fine-tuning the small size on a single 24GB RTX 3090 via Unsloth.

| Family (small / mid) | Exact sizes | License | Released | Modality | Reasoning default | 3090 LoRA (small) | HF/Unsloth | Source |
|---|---|---|---|---|---|---|---|---|
| **Qwen3** (4B / 8B) | 4.0B / 8.2B | Apache 2.0 | May 2025 | **Text-only** | toggle (`enable_thinking`) | Yes — 4B comfortably <24GB; Unsloth fits 14B in 16GB | Native + dedicated Unsloth guide | [a][b][i] |
| **Qwen3.5** (4B / 9B) | 4B / 9B | Apache 2.0 | Feb–Mar 2026 | **Multimodal** (vision encoder) | **thinking by default** | Yes (4B), but stock Unsloth image needs `transformers>=5.2.0` upgrade | Native; Unsloth fine-tune guide exists | [c][d][j] |
| **Phi-4-mini** (3.8B) / **Phi-4** (14B) | 3.8B / 14B | **MIT** | Feb 2025 | Text-only | no (instruct) | Yes — 3.8B fits easily; mid arm is 14B (cloud) | Native + Unsloth | [e][f] |
| **Gemma 3** (4B / 12B) | 4B / 12B | **Gemma** (custom, **gated**) | Mar 2025 | **Multimodal** (vision) | no | Yes (4B; Unsloth supports Gemma 3 1B/4B LoRA) | Native + Unsloth | [g][k] |
| **Mistral 3 / Ministral 3** (3B / 8B) | 3.4B+0.4B vis / 8B | Apache 2.0 | Dec 2025 | **Multimodal** (vision encoder) | no | Yes (small fits); vision adds load | Native + Unsloth (Mistral Small) | [h][k] |
| **Llama 3.2-3B / 3.1-8B** | 3.2B / 8.0B | **Llama Community** (custom, gated) | Sep 2024 / Jul 2024 | Text-only | no | Yes — both are standard Unsloth targets | Native + Unsloth | [l][m] |
| **Qwen2.5-3B / 7B** *(baseline)* | 3.09B / 7B | **3B: `qwen-research` (non-commercial); 7B: Apache 2.0** | Sep 2024 | Text-only | no | Yes — what tuner presets/recipes assume today | Native + Unsloth | [n] |
| **Llama-2-7b-chat** *(bridge arm only)* | 7B | Llama 2 Community (gated) | Jul 2023 | Text-only | no | Yes (legacy, well-supported) | Native + Unsloth | [o] |

### 3.1 Per-candidate 3090 LoRA feasibility note (criterion C4)

The 24GB constraint applies to the **small** size only (HANDOFF §1: "3B pilot runs locally
(RTX 3090), 7-8B confirm on HF Jobs"). All small sizes surveyed are 3–4B and well within 24GB
under LoRA, especially with 4-bit (QLoRA). Quantization assumption: Unsloth 4-bit (bnb) base +
LoRA adapters. Unsloth's own Qwen3 documentation states the **14B** model "fits comfortably in a
16GB T4" and the 30B-A3B MoE "works on 17.5GB" [i] — so any 3–4B small size has ample headroom on
a 3090. The mid sizes (8–14B) are explicitly cloud-targeted (HF Jobs) and were not gated on 24GB.

**The only C4 risk is not VRAM but software-stack drift:** Qwen3.5 requires `transformers>=5.2.0`,
which the stock `unsloth/unsloth:latest` image does not ship (it pins `transformers==4.57.1`); the
checked-in Qwen3.5 recipes already work around this with a pinned pip stack
(`transformers==5.5.0`, `trl==0.22.2`, unsloth from git). Qwen3 (2505) carries no such requirement
and runs on the stock image.

### 3.2 Disqualifications and cautions

- **Gemma 3** — multimodal + **gated** + a **custom non-Apache Gemma license**. The Gemma Terms
  permit research and derivative release but add license-compatibility review overhead for the
  "release everything" requirement (C6); combined with the vision encoder, it is a poorer fit than
  the text-only Apache options. Not disqualified, but ranked below.
- **Mistral 3 / Ministral 3 (2512)** — exact 3B+8B pairing and Apache 2.0 (a plus), but the small
  model is **multimodal** (3.4B LM + 0.4B vision encoder = ~4B total). For a text-only abstention
  study the vision encoder is dead weight and a potential confound. Viable if a clean text-only
  checkpoint is used, but it loses the simplicity edge to Qwen3.
- **Qwen3.5 (the tuner's current SFT target)** — newest Qwen, but it went **multimodal and
  thinking-by-default**, and skips ~8B (4B → 9B). Reasoning-by-default is the biggest design
  friction: it emits `<think>` traces that complicate truthful-rate and token-ECE parsing. Usable
  with thinking disabled, but Qwen3 (2505) gives the same Apache/Unsloth benefits **without** the
  vision encoder and with a true 8B mid size.
- **Qwen2.5-3B/7B (baseline)** — kept as a live fallback (it is already tuner-wired for KTO), but
  the **3B carries the non-commercial `qwen-research` license while the 7B is Apache 2.0** [n].
  That split is a real wart: the pilot and confirm arms would sit under different license regimes,
  and `qwen-research` is non-commercial. For a research paper releasing adapters this is workable
  but inelegant, and it is a strict downgrade from a uniformly-Apache family like Qwen3.
- **Llama 3.x** — text-only and well-supported, but the **custom Llama Community License + gated
  access** is heavier than Apache for the release requirement, and the user has flagged Llama-era
  models as stale/overmodeled. Not recommended as the pin; fine as an optional Phase 4 re-run.

### 3.3 Bridge-arm row (NOT a pin candidate)

**Llama-2-7b-chat** is included only because the trajectory proposes a bridge arm — one
Idk-SFT + Idk-DPO replication on Llama-2-7b-chat to validate the pipeline against Cheng et al.'s
published numbers before novel arms run. It is **verified still available** on HF (gated, Llama 2
Community License, ~251k downloads last month) [o]. It is a *replication target*, not a candidate
for the modern three-way pin, and its staleness is the entire point of running the modern arms on
a newer family.

---

## 4. Recommendation

### Primary pick — **Qwen3 (Qwen3-4B-Instruct pilot / Qwen3-8B-Instruct confirm)**

Qwen3 is the best fit on every load-bearing axis. It is **text-only** (no vision-encoder confound,
unlike Qwen3.5 / Gemma 3 / Mistral 3), **Apache 2.0 and ungated** at both sizes (cleanly satisfying
the release-adapters-and-outputs requirement, unlike Gemma/Llama's custom gated licenses and
unlike the Qwen2.5 3B-vs-7B license split), and lands on a near-exact ~4B-pilot / ~8B-confirm
pairing. Verified facts: Qwen3-4B = 4.0B params, Apache 2.0, text-only [a]; Qwen3-8B = 8.2B params,
Apache 2.0, text-only [b]; both released May 2025 and are first-class Unsloth targets with a
dedicated fine-tune guide [i]. The 4B small size fits a 24GB 3090 under LoRA with wide headroom
(Unsloth fits Qwen3-14B in 16GB). The one caveat — Qwen3's thinking/non-thinking toggle — is a
feature we control: pin `enable_thinking=False` (or `/no_think`) so the abstention study runs on
clean non-reasoning generations, and optionally keep the toggle as a free Phase 3 probe axis. It
also minimizes tuner work: the SFT family-branching already has a `"qwen"` arm, and only the KTO
preset (currently hardcoded to Qwen2.5) needs a new `--qwen3-4b` / `--qwen3-8b` entry.

### Runner-up — **Phi-4-mini-instruct (3.8B) + Phi-4 (14B), MIT**

Phi-4 is the runner-up purely on the strength of its **MIT license** — the most permissive in the
field, removing all release/redistribution friction — and its **text-only** architecture. Verified:
Phi-4-mini-instruct = 3.8B params, MIT, text-only dense decoder, Feb 2025 [e]; Phi-4 = 14B, MIT
[f]. The 3.8B pilot trains comfortably on a 3090. The drawback that drops it below Qwen3 is the
**size gap**: the family jumps 3.8B → 14B with no ~7-8B middle, so the "confirm" arm is heavier
than the trajectory's ~7-8B target (more cloud cost, and a larger pilot→confirm scale jump that
slightly weakens the "same family, two sizes" story). If the user wants the most license-clean
option and is comfortable with a 14B confirm arm, Phi-4 is the pick; otherwise Qwen3's true-8B
mid size and uniform Apache license make it the stronger default.

### Decision aid

| If the user prioritizes… | Pin |
|---|---|
| Clean text-only study, true ~8B mid, uniform Apache, least tuner work | **Qwen3 (4B / 8B)** |
| Maximally permissive license (MIT), accepts 14B confirm arm | **Phi-4-mini / Phi-4** |
| Exact 3B+8B sizes, fine with a vision encoder present | Mistral 3 / Ministral 3 (3B / 8B) |
| Staying on the already-wired tuner path with zero model-pin risk | Qwen2.5 baseline (accept 3B `qwen-research` non-commercial license) |

---

## 5. Risks & Constraints

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| KTO preset hardcoded to Qwen2.5 — any non-Qwen2.5 pin needs trainer edit | Certain | Low (small, localized) | preparer-infra/architect: add a Qwen3 (or chosen) preset to `Trainers/kto/train_kto.py`; SFT already branches on `"qwen"` |
| Qwen3.5 (current SFT recipe target) needs `transformers>=5.2.0` not in stock Unsloth image | Known | Low if Qwen3 (2505) chosen | Qwen3 (2505) avoids this entirely; only relevant if user pins Qwen3.5 |
| Thinking-mode models inject `<think>` traces into outputs, complicating ECE/truthful parsing | Medium | Medium | Pin `enable_thinking=False` for Qwen3; avoid Qwen3.5 (thinking-by-default) for the core arms |
| Multimodal small models carry a vision encoder = dead weight + confound | Medium | Low–Medium | Prefer text-only (Qwen3 / Phi-4); if Mistral 3 chosen, confirm a text-only load path |
| Qwen2.5-3B `qwen-research` non-commercial license vs 7B Apache split | Certain (if baseline pinned) | Medium | Choosing Qwen3 (uniform Apache) removes this entirely |
| License-compatibility review for "release everything" (C6) | Low (Apache picks) | Low | Apache-2.0 families (Qwen3) need no review; Gemma/Llama custom licenses do |

---

## 6. Sources

All accessed **2026-06-10**.

- [a] Qwen3-4B model card — https://huggingface.co/Qwen/Qwen3-4B (4.0B params, Apache 2.0, text-only, thinking toggle, GQA 36L)
- [b] Qwen3-8B model card — https://huggingface.co/Qwen/Qwen3-8B (8.2B params, Apache 2.0, instruct + base, thinking toggle)
- [c] Qwen3.5-4B model card — https://huggingface.co/Qwen/Qwen3.5-4B (4B, Apache 2.0, **multimodal vision encoder**, thinking-by-default, sibling 9B)
- [d] Qwen3.5 small-series coverage — https://artificialanalysis.ai/articles/qwen3-5-small-models and https://en.wikipedia.org/wiki/Qwen (0.8B/2B/4B/9B small series, released Mar 2 2026; no 8B)
- [e] Phi-4-mini-instruct model card — https://huggingface.co/microsoft/Phi-4-mini-instruct (3.8B, MIT, text-only dense decoder, Feb 2025, 128K ctx)
- [f] Phi-4 model card — https://huggingface.co/microsoft/phi-4 (14B, MIT)
- [g] Gemma 3 4B-it model card — https://huggingface.co/google/gemma-3-4b-it (4B, **Gemma custom license, gated**, multimodal, 128K ctx; sibling gemma-3-12b-it)
- [h] Ministral-3-3B-Instruct-2512 model card — https://huggingface.co/mistralai/Ministral-3-3B-Instruct-2512 (3.4B LM + 0.4B vision = ~4B, Apache 2.0, multimodal, Dec 2 2025; sibling Ministral-3-8B)
- [i] Qwen3 Unsloth fine-tune guide — https://unsloth.ai/docs/models/tutorials/qwen3-how-to-run-and-fine-tune (14B fits 16GB T4; 30B-A3B in 17.5GB; 2× faster / 70% less VRAM)
- [j] Qwen3.5 Unsloth fine-tune guide — https://unsloth.ai/docs/models/qwen3.5/fine-tune
- [k] Unsloth model catalog / supported families — https://unsloth.ai/docs/get-started/unsloth-model-catalog and https://github.com/unslothai/unsloth (Qwen3/Qwen3.5, Gemma 3, Llama 3.2, Phi 4, Mistral Small LoRA support)
- [l] Llama-3.2-3B-Instruct model card — https://huggingface.co/meta-llama/Llama-3.2-3B-Instruct (3B, Llama 3.2 Community License, gated)
- [m] Llama-3.1-8B-Instruct model card — https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct (8B, Llama 3.1 Community License, gated)
- [n] Qwen2.5-3B-Instruct model card — https://huggingface.co/Qwen/Qwen2.5-3B-Instruct (3.09B, **`qwen-research` non-commercial license**; 7B sibling is Apache 2.0, Sep 2024)
- [o] Llama-2-7b-chat-hf model card — https://huggingface.co/meta-llama/Llama-2-7b-chat-hf (7B, Llama 2 Community License, gated, still available ~251k downloads/mo, Jul 2023)

**Repo-internal evidence (verified in worktree 2026-06-10):**
- `synaptic-tuner/Trainers/kto/train_kto.py` L201-426 — KTO presets hardcode `unsloth/Qwen2.5-3B/7B-Instruct-bnb-4bit` (`--qwen-3b`/`--qwen-7b`)
- `synaptic-tuner/Trainers/recipes/*.yaml` — SFT recipes target `Qwen/Qwen3.5-{0.8B,2B,4B,9B}` and `Qwen/Qwen3-4B`; note "Qwen3.5 needs transformers >=5.2.0" (stock Unsloth image ships 4.57.1)
- `synaptic-tuner/Trainers/sft/train_sft.py` L749-764 — model-family branching already handles `qwen / llama / mistral / gemma / phi / deepseek / smollm`
- `synaptic-tuner/README.md` — training stack is Unsloth
