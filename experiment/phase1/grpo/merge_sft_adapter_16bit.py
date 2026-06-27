#!/usr/bin/env python3
"""Merge a trained LoRA adapter into a standalone 16-bit model on local disk.

Mirrors the synaptic-tuner Merged16BitStrategy primitive
(FastLanguageModel load at full precision -> save_pretrained_merged
save_method="merged_16bit"), so the produced base matches the clean-SFT
merged-16bit substrate used as the apples-to-apples eval base. SFT train_sft.py
saves only the LoRA adapter (final_model/); this is the separate merge step the
downstream evals and DPO/KTO/GRPO bases expect.

Usage (inside the unsloth container):
  python3 experiment/phase1/grpo/merge_sft_adapter_16bit.py <adapter_dir> <output_dir>

  <adapter_dir>  directory with adapter_config.json + adapter_model.safetensors
                 (e.g. <run>/final_model)
  <output_dir>   where merged-16bit/ is written
                 (e.g. <run>/Qwen3-4B-bnb-4bit/merged-16bit)
"""
import sys
from pathlib import Path

from unsloth import FastLanguageModel


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    adapter_dir, output_dir = sys.argv[1], sys.argv[2]
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    print(f"Loading adapter at full precision for 16-bit merge: {adapter_dir}")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=adapter_dir,
        max_seq_length=2048,
        dtype=None,
        load_in_4bit=False,  # full precision so the merge is 16-bit
    )

    print(f"Saving merged 16-bit model -> {output_dir}")
    model.save_pretrained_merged(output_dir, tokenizer, save_method="merged_16bit")
    print(f"[OK] merged 16-bit model saved to: {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
