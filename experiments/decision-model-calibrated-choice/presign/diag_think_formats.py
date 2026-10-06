#!/usr/bin/env python3
"""Pre-sign diagnostic (lab-notebook tier): where does '</think>' come from?

Non-PopQA only: the 20 fixed smoke questions (hand-written gold aliases below)
plus 120 deterministic synthetic arithmetic / unit-conversion questions whose
gold answers are computed. Four prompt formats for Qwen3.5-2B-Base @ b1485b2f:

  A  EH chat template exactly as probe.py renders it (system prompt from
     probe.yaml, enable_thinking=False -> '<think>\\n\\n</think>\\n\\n' pre-filled)
  B  same chat template, enable_thinking=True -> assistant turn ends '<think>\\n'
  C  same chat scaffolding with NO think block at all ('<|im_start|>assistant\\n');
     the template has no switch for this (an undefined enable_thinking renders
     like A), so the think block is stripped from A's render
  D  base-mode 5-shot 'Q: ...\\nA:' (Amendment Y's build_base_mode_prompt,
     vendored byte-identical; no chat template, no system prompt)

phase=sample (WSL vLLM venv): greedy + 32 samples (T=1.0, top_p 0.9, 64 new
tokens, per-question seed as probe.py derives it) per question per format;
writes every completion (text + token ids) to the gitignored output dir.
phase=probs (runner image, HF transformers): exact next-token distribution at
the first generated position per format; tokenizer special-token facts; the
full rendered A prompt with its last 30 tokens.
phase=report (CPU): scoring (EH is_correct; B scored after the final </think>
as probe.py does with thinking on; D scored on the first line as Amendment Y
does), marker rates and positions, accuracy, empty rate, length, EH-threshold
labels and cross-format label agreement.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
CELL = HERE.parent
REPO = CELL.parents[1]
sys.path.insert(0, str(REPO / "experiments/common/knowledge_probe"))
sys.path.insert(0, str(HERE))

from smoke_questions import QUESTIONS  # noqa: E402

SMOKE_GOLD = [
    ["john milton", "milton"], ["100"], ["8", "eight"], ["na"], ["mars"], ["51"], ["indian"],
    ["skin"], ["michelangelo"], ["carbon dioxide", "co2"], ["12", "twelve"],
    ["mandarin", "chinese", "mandarin chinese"], ["32"], ["piano"], ["hydrogen"], ["femur"],
    ["7", "seven"], ["ottawa"], ["isaac newton", "newton"], ["150", "150 km", "150 kilometres"],
]

# Amendment Y base-mode exemplars, byte-identical to
# experiments/common/readouts/amendment_x_cross_model_extract.py::_BASE_MODE_FEWSHOT
BASE_MODE_FEWSHOT = (
    ("What is the largest planet in our solar system?", "Jupiter"),
    ("How many sides does a hexagon have?", "Six"),
    ("What is the chemical symbol for gold?", "Au"),
    ("In what year did the Second World War end?", "1945"),
    ("What is the tallest mountain on Earth?", "Mount Everest"),
)
FORMATS = ("A", "B", "C", "D")
THINK_EMPTY = "<think>\n\n</think>\n\n"


def synthetic_with_gold(n: int, seed: int = 20261005) -> list[tuple[str, list[str]]]:
    rng = random.Random(seed)
    out = []
    for i in range(n):
        a, b = rng.randint(2, 999), rng.randint(2, 99)
        k = i % 5
        if k == 0:
            q, g = f"What is {a} plus {b}?", a + b
        elif k == 1:
            q, g = f"What is {a} multiplied by {b}?", a * b
        elif k == 2:
            q, g = f"How many minutes are there in {a} hours and {b} minutes?", 60 * a + b
        elif k == 3:
            q, g = f"If you have {a} apples and give away {min(a, b)}, how many are left?", a - min(a, b)
        else:
            q, g = f"How many centimetres are there in {a} metres and {b} centimetres?", 100 * a + b
        out.append((q, [str(g), f"{g:,}"]))
    return out


def question_set() -> list[dict]:
    qs = [{"qid": f"smoke-{i}", "question": q, "aliases": SMOKE_GOLD[i]} for i, q in enumerate(QUESTIONS)]
    qs += [{"qid": f"syn-{i}", "question": q, "aliases": g} for i, (q, g) in enumerate(synthetic_with_gold(120))]
    return qs


def base_mode_prompt(question: str) -> str:
    block = "".join(f"Q: {q}\nA: {a}\n\n" for q, a in BASE_MODE_FEWSHOT)
    return f"{block}Q: {question}\nA:"


def render_all(tok, system: str, question: str) -> dict[str, str]:
    from backends import render_probe_prompt

    a, _ = render_probe_prompt(tok, system, question, enable_thinking=False)
    b, _ = render_probe_prompt(tok, system, question, enable_thinking=True)
    assert a.endswith(THINK_EMPTY), "format A no longer ends with the empty think block"
    c = a[: -len(THINK_EMPTY)]
    return {"A": a, "B": b, "C": c, "D": base_mode_prompt(question)}


def derive_seed(master: int, qid: str) -> int:
    return int.from_bytes(hashlib.sha256(f"{master}|{qid}".encode()).digest()[:4], "big")


def phase_sample(args) -> None:
    import yaml
    from vllm import LLM, SamplingParams

    pc = yaml.safe_load((CELL / "probe.yaml").read_text(encoding="utf-8"))
    s = pc["sampling"]
    llm = LLM(model=args.snapshot, dtype="auto", gpu_memory_utilization=0.90, max_model_len=2048)
    tok = llm.get_tokenizer()
    qs = question_set()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for fmt in FORMATS:
        prompts = [render_all(tok, pc["prompt"]["system"], q["question"])[fmt] for q in qs]
        greedy = llm.generate(prompts, SamplingParams(n=1, temperature=0.0, max_tokens=s["max_new_tokens"], seed=0),
                              use_tqdm=False)
        sampled = llm.generate(prompts, [SamplingParams(n=s["n_samples"], temperature=s["temperature"],
                                                        top_p=s["top_p"], max_tokens=s["max_new_tokens"],
                                                        seed=derive_seed(s["seed"], q["qid"])) for q in qs],
                               use_tqdm=False)
        with open(out / f"gen_{fmt}.jsonl", "w", encoding="utf-8") as fh:
            for q, p, g, sm in zip(qs, prompts, greedy, sampled):
                fh.write(json.dumps({
                    "qid": q["qid"], "prompt_sha256": hashlib.sha256(p.encode()).hexdigest(),
                    "prompt_len": len(g.prompt_token_ids),
                    "greedy": {"text": g.outputs[0].text, "ids": list(g.outputs[0].token_ids)},
                    "sampled": [{"text": o.text, "ids": list(o.token_ids)} for o in sm.outputs],
                }) + "\n")
        print(f"sample: format {fmt} done", flush=True)


def phase_probs(args) -> None:
    import torch
    import yaml
    from transformers import AutoModelForCausalLM, AutoTokenizer

    pc = yaml.safe_load((CELL / "probe.yaml").read_text(encoding="utf-8"))
    tok = AutoTokenizer.from_pretrained(pc["model"]["model_name"], revision=pc["model"]["model_revision"])
    model = AutoModelForCausalLM.from_pretrained(pc["model"]["model_name"], revision=pc["model"]["model_revision"],
                                                 dtype=torch.bfloat16, device_map="cuda")
    model.eval()
    ids = {m: tok.convert_tokens_to_ids(m) for m in ("<think>", "</think>")}
    special = {m: (m in (tok.all_special_tokens or []) or m in [str(t) for t in tok.added_tokens_decoder.values()])
               for m in ids}
    single = {m: tok(m, add_special_tokens=False)["input_ids"] for m in ids}
    qs = question_set()
    res = {"tokenizer": {"ids": ids, "added_or_special": special, "encode_as": single,
                         "decode_back": {m: tok.decode([i]) for m, i in ids.items()}}, "formats": {}}
    a0 = render_all(tok, pc["prompt"]["system"], qs[0]["question"])
    ex_ids = tok(a0["A"])["input_ids"]
    res["example_A"] = {"question": qs[0]["question"], "rendered": a0["A"],
                        "last30": [[i, tok.decode([i])] for i in ex_ids[-30:]],
                        "endings": {f: repr(a0[f][-40:]) for f in FORMATS}}
    for fmt in FORMATS:
        p_end, p_open, top = [], [], Counter()
        for q in qs:
            prompt = render_all(tok, pc["prompt"]["system"], q["question"])[fmt]
            enc = tok(prompt, return_tensors="pt").to("cuda")
            with torch.no_grad():
                logits = model(**enc).logits[0, -1].float()
            prob = torch.softmax(logits, -1)
            p_end.append(float(prob[ids["</think>"]]))
            p_open.append(float(prob[ids["<think>"]]))
            for t in torch.topk(prob, 3).indices.tolist():
                top[tok.decode([t])] += 1
        res["formats"][fmt] = {"n": len(qs), "mean_p_end_think": sum(p_end) / len(p_end),
                               "max_p_end_think": max(p_end), "mean_p_open_think": sum(p_open) / len(p_open),
                               "top3_first_tokens_counts": top.most_common(8)}
        print(f"probs: {fmt} mean P(</think>)={res['formats'][fmt]['mean_p_end_think']:.4g}", flush=True)
    Path(args.out).mkdir(parents=True, exist_ok=True)
    (Path(args.out) / "probs.json").write_text(json.dumps(res, indent=1), encoding="utf-8")


def phase_report(args) -> None:
    from backends import extract_answer_after_thinking
    from scoring import is_correct

    out = Path(args.out)
    probs = json.loads((out / "probs.json").read_text(encoding="utf-8"))
    end_id = probs["tokenizer"]["ids"]["</think>"]
    open_id = probs["tokenizer"]["ids"]["<think>"]
    qs = {q["qid"]: q for q in question_set()}

    def scored(fmt, text):
        if fmt == "B":
            return extract_answer_after_thinking(text)[0]
        if fmt == "D":
            return text.strip().split("\n")[0].strip()
        return text

    rep = {"probs": probs, "formats": {}, "examples_A": []}
    labels = {}
    for fmt in FORMATS:
        rows = [json.loads(x) for x in open(out / f"gen_{fmt}.jsonl", encoding="utf-8")]
        n_gen = n_mark = n_first = 0
        pos = Counter()
        g_ok, s_ok, empty, lengths = [], [], 0, []
        lab = {}
        for r in rows:
            al = qs[r["qid"]]["aliases"]
            gens = [r["greedy"]] + r["sampled"]
            flags = []
            for gi, g in enumerate(gens):
                n_gen += 1
                ids = g["ids"]
                marked = (end_id in ids) or (open_id in ids) or ("</think>" in g["text"]) or ("<think>" in g["text"])
                flags.append(marked)
                if marked:
                    n_mark += 1
                    hits = [i for i, t in enumerate(ids) if t in (end_id, open_id)]
                    k = min(hits) if hits else 999  # 999 = marker only visible in decoded text
                    pos["0" if k == 0 else "1-4" if k <= 4 else "5-15" if k <= 15 else ">15"] += 1
                    n_first += k == 0
                    if fmt == "A" and len(rep["examples_A"]) < 10:
                        txt = g["text"]
                        cut = min(i for i in (txt.find("</think>"), txt.find("<think>")) if i >= 0)
                        rep["examples_A"].append({"qid": r["qid"], "sample": gi, "marker_token_index": k,
                                                  "before": txt[:cut], "marker_and_after": txt[cut:cut + 160]})
                ans = scored(fmt, g["text"])
                if gi > 0:
                    lengths.append(len(ans.split()))
                    empty += ans.strip() == ""
            # EH scoring; format A/C under the cell's count_wrong policy
            corr = [False if (fmt in "AC" and f) else is_correct(scored(fmt, g["text"]), al)
                    for g, f in zip(gens, flags)]
            g_ok.append(corr[0])
            pc_ = sum(corr[1:]) / len(corr[1:])
            s_ok.append(pc_)
            lab[r["qid"]] = "known" if corr[0] and pc_ >= 0.5 else "unknown" if pc_ == 0 else "ambiguous"
        labels[fmt] = lab
        n_s = sum(len(r["sampled"]) for r in rows)
        rep["formats"][fmt] = {
            "n_questions": len(rows), "n_generations": n_gen, "marker_rate": n_mark / n_gen,
            "marker_first_token_rate": n_first / n_gen, "marker_position_counts": dict(pos),
            "greedy_accuracy": sum(g_ok) / len(g_ok), "mean_sampled_accuracy": sum(s_ok) / len(s_ok),
            "empty_answer_rate_sampled": empty / n_s, "mean_answer_words_sampled": sum(lengths) / len(lengths),
            "labels": dict(Counter(lab.values())),
            "mean_p_end_think_first_token": probs["formats"][fmt]["mean_p_end_think"],
        }
    agree = {}
    for i, f1 in enumerate(FORMATS):
        for f2 in FORMATS[i + 1:]:
            same = sum(labels[f1][q] == labels[f2][q] for q in qs)
            kk = sum(labels[f1][q] == labels[f2][q] == "known" for q in qs)
            k1 = sum(labels[f1][q] == "known" for q in qs)
            k2 = sum(labels[f2][q] == "known" for q in qs)
            agree[f"{f1}-{f2}"] = {"label_agreement": same / len(qs), "known_both": kk,
                                   "known_only_first": k1 - kk, "known_only_second": k2 - kk}
    rep["label_agreement"] = agree
    (out / "report.json").write_text(json.dumps(rep, indent=1), encoding="utf-8")
    print(json.dumps({"formats": rep["formats"], "label_agreement": agree}, indent=1))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("phase", choices=["sample", "probs", "report"])
    ap.add_argument("--snapshot", default=None)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    {"sample": phase_sample, "probs": phase_probs, "report": phase_report}[args.phase](args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
