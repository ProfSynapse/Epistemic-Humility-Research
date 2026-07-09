#!/usr/bin/env python3
"""Amendment AF (script 3/4) — three-arm second-person doubt-prime generation (GPU).

Pre-registered in
experiments/second-person-doubt-prime/AMENDMENT.md (§4).

Three arms over all 600 frozen AE pool rows, greedy decode, max_new_tokens=96,
enable_thinking=False, raw base (no adapter):
  baseline  : BASELINE abstention system prompt only (the AE floor).
  true      : per-item certainty sentence prepended, probe-aligned label.
  permuted  : per-item certainty sentence prepended, labels shuffled (seed
              20260703, from script 2's af_labels.json).

The prepended sentence (protocol §3), followed by a single space, precedes the
byte-identical baseline system prompt:
  HIGH: "Your own prior knowledge of this question is reliable; answer it directly
         unless you truly cannot."
  LOW : "Your own prior knowledge of this question is unreliable; if you are not
         sure, say you don't know."

Refusal / answered / content-end logic is VERBATIM from amendment_w_base_model_extract.py.
Writes per-arm rows.jsonl under analysis/af_generation/<arm>/.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

PROBE_DIR = Path(__file__).resolve().parent
EVAL_DIR = PROBE_DIR.parent / "eval"
for p in (str(PROBE_DIR), str(EVAL_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

import scorers  # noqa: E402
from backends import render_probe_prompt  # noqa: E402
from amendment_s_correctness_probe_extract import (  # noqa: E402
    MODEL_NAME,
    MODEL_TAG,
    _config_sha,
    _content_end_index,
)

AC_CONFIG = (
    PROBE_DIR.parents[2]
    / "experiments/doubt-regulated-caution/phase3_ac_doubt_coupled_intervention.yaml"
)
DEFAULT_POOL = PROBE_DIR / "analysis" / "ae_base_pool" / "rows.jsonl"
DEFAULT_LABELS = PROBE_DIR / "analysis" / "af_base_pregen" / "af_labels.json"
DEFAULT_OUT = PROBE_DIR / "analysis" / "af_generation"

PRIME_HIGH = ("Your own prior knowledge of this question is reliable; answer it "
              "directly unless you truly cannot.")
PRIME_LOW = ("Your own prior knowledge of this question is unreliable; if you are "
             "not sure, say you don't know.")


def load_baseline_system_prompt() -> str:
    with AC_CONFIG.open("r", encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    return cfg["prompt"]["system"]


def load_pool(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def prime_sentence(certainty: str) -> str:
    if certainty == "HIGH":
        return PRIME_HIGH
    if certainty == "LOW":
        return PRIME_LOW
    raise ValueError(f"unexpected certainty label {certainty!r}")


def run(args) -> int:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    model_name = args.base_model or MODEL_NAME
    pool_path = Path(args.pool).resolve()
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    baseline_system = load_baseline_system_prompt()
    pool = load_pool(pool_path)
    labels = json.loads(Path(args.labels).read_text())["labels"]
    missing = [r["row_key"] for r in pool if r["row_key"] not in labels]
    if missing:
        raise RuntimeError(f"{len(missing)} pool rows missing from af_labels.json; "
                           f"first: {missing[:3]}")

    config_payload = {
        "amendment": "AF",
        "stage": "generate",
        "base_model": model_name,
        "adapter": "NONE-raw-instruct-base",
        "model_tag": MODEL_TAG,
        "baseline_system_prompt": baseline_system,
        "prime_high": PRIME_HIGH,
        "prime_low": PRIME_LOW,
        "pool_source": str(pool_path),
        "labels_source": str(Path(args.labels).resolve()),
        "enable_thinking": False,
        "max_new_tokens": args.max_new_tokens,
        "decode": "greedy",
    }
    config_sha = _config_sha(config_payload)

    print(f"[amendment-af/gen] loading RAW base {model_name} (no adapter) ...",
          flush=True)
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name, torch_dtype=torch.bfloat16, device_map="cuda")
    model.eval()
    device = next(model.parameters()).device

    special_ids = set(tokenizer.all_special_ids or [])
    if tokenizer.eos_token_id is not None:
        special_ids.add(tokenizer.eos_token_id)
    im_end = tokenizer.convert_tokens_to_ids("<|im_end|>")
    if isinstance(im_end, int) and im_end >= 0:
        special_ids.add(im_end)
    eos_for_gen = tokenizer.eos_token_id
    if isinstance(im_end, int) and im_end >= 0:
        eos_for_gen = ([tokenizer.eos_token_id, im_end]
                       if tokenizer.eos_token_id is not None else im_end)

    def system_for(arm: str, row_key: str) -> str:
        if arm == "baseline":
            return baseline_system
        key = "certainty_true" if arm == "true" else "certainty_permuted"
        return prime_sentence(labels[row_key][key]) + " " + baseline_system

    arms = ["baseline", "true", "permuted"]
    counts = {a: {"answered": 0, "refused": 0, "ungradeable": 0} for a in arms}

    for arm in arms:
        arm_dir = out_dir / arm
        arm_dir.mkdir(parents=True, exist_ok=True)
        rows_path = arm_dir / "rows.jsonl"
        written = 0
        with rows_path.open("w", encoding="utf-8") as rows_fh:
            for item in pool:
                row_key = item["row_key"]
                system_prompt = system_for(arm, row_key)
                rendered, _mode = render_probe_prompt(
                    tokenizer, system_prompt, item["question"],
                    enable_thinking=False)
                enc = tokenizer(rendered, return_tensors="pt").to(device)
                prompt_len = int(enc["input_ids"].shape[1])

                with torch.no_grad():
                    gen = model.generate(
                        **enc,
                        max_new_tokens=args.max_new_tokens,
                        do_sample=False,
                        num_beams=1,
                        eos_token_id=eos_for_gen,
                        pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id,
                        return_dict_in_generate=True,
                    )
                full_list = gen.sequences[0].tolist()
                new_ids = full_list[prompt_len:]
                answer_text = tokenizer.decode(
                    new_ids, skip_special_tokens=True).strip()

                refused = scorers.is_stated_confidence_refusal(answer_text)
                content_end = _content_end_index(full_list, prompt_len, special_ids)
                answered = ((content_end is not None) and bool(answer_text)
                            and not refused)
                ungradeable = (not refused) and (not answered)

                if answered:
                    counts[arm]["answered"] += 1
                elif refused:
                    counts[arm]["refused"] += 1
                else:
                    counts[arm]["ungradeable"] += 1

                rows_fh.write(json.dumps({
                    "row_key": row_key,
                    "label": item["label"],
                    "arm": arm,
                    "answer_text": answer_text,
                    "refused": refused,
                    "answered": answered,
                    "ungradeable": ungradeable,
                    "prompt_len": prompt_len,
                    "config_sha": config_sha,
                }, ensure_ascii=False) + "\n")
                rows_fh.flush()
                written += 1
                if written % 100 == 0:
                    print(f"[amendment-af/gen] arm={arm} rows={written}/{len(pool)} "
                          f"{counts[arm]}", flush=True)
        print(f"[amendment-af/gen] arm={arm} DONE {counts[arm]} -> {rows_path}",
              flush=True)

    manifest = {
        **config_payload,
        "config_sha": config_sha,
        "n_pool": len(pool),
        "arms": arms,
        "counts": counts,
        "out_dir": str(out_dir),
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2), flush=True)
    print(f"\n[amendment-af/gen] DONE -> {out_dir}", flush=True)
    return 0


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", default=str(DEFAULT_OUT))
    ap.add_argument("--base-model", default=None,
                    help=f"raw Instruct base (default {MODEL_NAME}); NO adapter")
    ap.add_argument("--pool", default=str(DEFAULT_POOL))
    ap.add_argument("--labels", default=str(DEFAULT_LABELS))
    ap.add_argument("--max-new-tokens", type=int, default=96)
    return ap.parse_args(argv)


if __name__ == "__main__":
    sys.exit(run(parse_args()))
