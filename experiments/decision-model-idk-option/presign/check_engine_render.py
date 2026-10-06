#!/usr/bin/env python3
"""Pre-sign IDK render check (lab-notebook tier; no model forward, no outcome).

Runs INSIDE the pinned engine image (unsloth digest + the recipe's pip set),
from the synaptic-tuner root, with only the engine's own code: the rows are
loaded by `load_examples`, rendered and tokenised by `DecisionCollator`
(train=False, the path `confidence_analysis.capture` uses) with the
checkpoint's own decision_config (marker style, headers, max_length) and
tokenizer. No weights are loaded.

For each IDK-position rows file (one per position) and every row, against the
no-IDK source row with the same qid:
  - canonical order rendered (slot_names == options), IDK at meta.idk_slot == k;
  - the IDK line is exactly "<marker>. I don't know" (no description suffix);
  - the 4 real options keep the source row's relative order; the gold name is
    unchanged (label shifted by one iff k <= source label);
  - the IDK prompt equals the no-IDK prompt with one line inserted and the
    markers renumbered (nothing else in the prompt changes);
  - option_index[j] is the last token of option line j: its offset ends exactly
    at the line end, the next token starts at or after it, and the indices
    strictly increase; answer_index (= last token) ends the prompt at
    "<answer>"; no truncation;
  - the batch path (collator.__call__, padded batches of 8) gives the same
    option_index / answer_index as the single-row encode.
Also: the marker tokens of both styles, single-token check for 5 options.

Writes a JSON summary (counts only) to --out; prints one synthetic (non-PopQA)
rendered example per position when --example-rows is given.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

TUNER = Path.cwd()
for p in (TUNER / "Trainers/decision", TUNER):
    sys.path.insert(0, str(p))

IDK = "I don't know"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--checkpoint", required=True)
    ap.add_argument("--noidk-rows", required=True)
    ap.add_argument("--idk-rows", nargs="+", required=True, help="position files, in position order")
    ap.add_argument("--positions", nargs="+", type=int, required=True)
    ap.add_argument("--example-rows", nargs="*", default=[], help="synthetic files: print one render per file")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    import transformers
    from transformers import AutoTokenizer

    from decision_core.collate import CollatorConfig, DecisionCollator
    from decision_core.examples import load_examples
    from decision_core.model_config import DecisionModelConfig
    from decision_core.modeling import single_token_marker_ids
    from decision_core.prompting import option_markers

    ck = Path(args.checkpoint)
    dc = DecisionModelConfig.from_dict(json.loads((ck / "decision_config.json").read_text(encoding="utf-8")))
    tok = AutoTokenizer.from_pretrained(str(ck))
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    coll = DecisionCollator(tok, CollatorConfig(max_length=dc.max_length, marker_style=dc.marker_style,
                                                headers=dict(dc.headers)), train=False)
    res: dict = {"check": "idk_render_engine_path", "transformers": transformers.__version__,
                 "readout": dc.readout, "marker_style": dc.marker_style, "max_length": dc.max_length,
                 "checkpoint": str(ck)}
    marker_tok = {}
    for style in ("numbers", "letters"):
        ids = [tok.encode(m, add_special_tokens=False) for m in option_markers(style, 5)]
        marker_tok[style] = {"markers": option_markers(style, 5), "ids": ids,
                             "all_single_token": all(len(x) == 1 for x in ids),
                             "single_token_marker_ids_first5": single_token_marker_ids(tok, style)[:5]}
    res["marker_tokens"] = marker_tok

    src = {e.meta["qid"]: e for e in load_examples([args.noidk_rows])}
    per_pos = {}
    for k, path in zip(args.positions, args.idk_rows):
        rows = load_examples([path])
        bad = Counter()
        n_tok = []
        for ex in rows:
            s = src[ex.meta["qid"]]
            enc = coll.encode(ex)
            r = enc.rendered
            names = [o[0] for o in ex.options]
            bad["slot_names_not_canonical"] += list(r.slot_names) != names
            bad["idk_slot_wrong"] += int(ex.meta.get("idk_slot", -1)) != k or names[k] != IDK
            line = r.text[r.option_spans[k][0]:r.option_spans[k][1]]
            bad["idk_line_wrong"] += line != f"{r.markers[k]}. {IDK}"
            bad["real_order_changed"] += [n for i, n in enumerate(names) if i != k] != [o[0] for o in s.options]
            bad["gold_changed"] += names[ex.label] != s.options[s.label][0] or \
                ex.label != s.label + (1 if k <= s.label else 0)
            # one inserted line, markers renumbered, nothing else changed
            s_r = coll.encode(s).rendered
            lines = r.text.split("\n")
            first = r.text[:r.option_spans[0][0]].count("\n")
            del lines[first + k]
            m_new = option_markers(dc.marker_style, len(s.options))
            for j in range(len(s.options)):
                ln = lines[first + j]
                old_marker = r.markers[j if j < k else j + 1]
                lines[first + j] = m_new[j] + ln[len(old_marker):]
            bad["prompt_differs_beyond_idk_line"] += "\n".join(lines) != s_r.text
            # token indices
            full = tok(r.text, add_special_tokens=False, return_offsets_mapping=True)
            offs = [tuple(o) for o in full["offset_mapping"]]
            ids = list(full["input_ids"])
            bad["truncated"] += len(ids) > dc.max_length or enc.input_ids != ids
            oi = enc.option_index
            bad["option_index_not_increasing"] += any(b <= a for a, b in zip(oi, oi[1:]))
            for j, (a, b) in enumerate(r.option_spans):
                t = oi[j]
                if offs[t][1] != b or not (t + 1 < len(offs) and offs[t + 1][0] >= b) or offs[t][0] < a:
                    bad["option_index_not_line_end"] += 1
                    break
            bad["answer_not_last"] += not (r.text.endswith("<answer>") and offs[-1][1] == len(r.text))
            n_tok.append(len(ids))
        # batch path (padded batches of 8, as capture() runs)
        mism = 0
        for start in range(0, min(len(rows), 400), 8):
            chunk = rows[start:start + 8]
            batch = coll(chunk)
            for i, ex in enumerate(chunk):
                e1 = coll.encode(ex)
                n = len(e1.input_ids)
                mism += batch["option_index"][i, :ex.n_options].tolist() != e1.option_index or \
                    int(batch["answer_index"][i]) != n - 1 or batch["orders"][i] != list(range(ex.n_options))
        per_pos[k] = {"n_rows": len(rows), "failures": {key: v for key, v in bad.items() if v},
                      "batch_vs_single_mismatch_first400": mism,
                      "prompt_tokens_min_max": [min(n_tok), max(n_tok)],
                      "pass": not any(bad.values()) and mism == 0 and len(rows) == len(src)}
    res["positions"] = per_pos
    res["pass"] = all(v["pass"] for v in per_pos.values()) and \
        marker_tok[dc.marker_style]["all_single_token"]
    examples = []
    for path in args.example_rows:
        ex = load_examples([path])[0]
        r = coll.encode(ex).rendered
        examples.append({"file": Path(path).name, "idk_slot": ex.meta.get("idk_slot"),
                         "options_block": r.text[r.option_spans[0][0]:r.option_spans[-1][1]],
                         "option_index": coll.encode(ex).option_index,
                         "answer_index": len(coll.encode(ex).input_ids) - 1})
    res["synthetic_examples"] = examples
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(res, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: v["pass"] for k, v in per_pos.items()}), "overall", res["pass"])
    return 0 if res["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
