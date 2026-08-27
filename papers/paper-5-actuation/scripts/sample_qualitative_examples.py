#!/usr/bin/env python3
"""Sample the qualitative graded examples for the manuscript's examples appendix.

Downloads row-level generation exhaust from the two public Hugging Face
datasets named below, at pinned revisions, filters to rows from the
MIT-licensed Known-Unknown Questions (KUQ) source that carry generation
text, and draws a fixed-seed sample per dataset:

- 3 uniformly random rows (any arm),
- 1 random row where the narrow and wide instruments disagree on a
  true-gated dosed generation (narrow ``clean_tighten`` != the wide
  instrument's final verdict),
- 1 random failure case: a true-gated dosed generation the wide
  instrument does NOT credit as an abstention.

Rows whose ``is_decoy`` flag is true are excluded everywhere: decoy text is
synthetic grader-calibration material, not a model generation. Generation
text is printed verbatim and never truncated. The script prints the exact
markdown pasted into the appendix; rerunning it reproduces that block.

Containment: only rows whose ``source`` is the KUQ pool (labeled ``kuq`` in
the control-rescore dataset and ``kuq_unknowns_all`` in the Llama dataset)
are ever printed. No source question text exists in these datasets; the
printed fields are the model's own generation, its parsed answer value, and
the instruments' verdict booleans.

Deterministic given SEED; network access only to huggingface.co.
"""

import json
import random

from huggingface_hub import hf_hub_download

SEED = 20260827

DATASETS = [
    {
        "title": "professorsynapse/eh-wide-instrument-control-rescore-rows",
        "revision": "8e93cba04e994617cfb227a6de5d5b2ada42aaa6",
        "filename": "WICR45/rows.jsonl",
        "note": "Qwen3-4B raw-base, Section 4.5 gated controller and its controls under the wide re-score",
        "kuq_sources": {"kuq"},
        "gated_arms": {"gated"},
        "wide_field": "wide_refused_final",
        "verdict_fields": [
            "well_formed",
            "semantic_refuse",
            "degenerate",
            "clean_tighten",
            "detector_v2_refused",
            "wide_llm_is_abstention",
            "wide_refused_final",
        ],
    },
    {
        "title": "professorsynapse/eh-llama-hs17-wide-instrument-rescore-rows",
        "revision": "1ec3a0628488a3214df101060e71a71b856b76f5",
        "filename": "llama32_3b_instruct/rows.jsonl",
        "note": "Llama-3.2-3B, hs17 gated write and its random-direction census under the wide re-score",
        "kuq_sources": {"kuq_unknowns_all"},
        "gated_arms": {"arm1_gated_replication"},
        "wide_field": "wide_abstention",
        "verdict_fields": [
            "well_formed",
            "semantic_refuse",
            "refused",
            "degenerate",
            "clean_tighten",
            "detector_v2_refused",
            "wide_abstention",
        ],
    },
]


def load_rows(spec):
    path = hf_hub_download(
        repo_id=spec["title"],
        filename=spec["filename"],
        repo_type="dataset",
        revision=spec["revision"],
    )
    with open(path, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh]


def eligible(row, spec):
    if row.get("source") not in spec["kuq_sources"]:
        return False
    if row.get("generation_text") is None:
        return False
    if row.get("is_decoy"):
        return False
    return True


def render(row, spec, heading):
    lines = [f"**{heading}**", ""]
    lines.append(
        f"- row_key `{row['row_key']}`, arm `{row['arm']}`, "
        f"dose_or_strength `{row.get('dose_or_strength')}`"
    )
    lines.append("- generation_text (verbatim):")
    lines.append("")
    lines.append("```text")
    lines.append(row["generation_text"])
    lines.append("```")
    lines.append("")
    lines.append(f"- answer_value: `{json.dumps(row.get('answer_value'))}`")
    verdicts = ", ".join(
        f"{name} `{json.dumps(row.get(name))}`" for name in spec["verdict_fields"]
    )
    lines.append(f"- verdicts: {verdicts}")
    lines.append("")
    return "\n".join(lines)


def main():
    rng = random.Random(SEED)
    for spec in DATASETS:
        rows = load_rows(spec)
        pool = [r for r in rows if eligible(r, spec)]
        gated = [r for r in pool if r["arm"] in spec["gated_arms"]]
        disagree = [
            r for r in gated if bool(r.get("clean_tighten")) != bool(r.get(spec["wide_field"]))
        ]
        failures = [r for r in gated if not r.get(spec["wide_field"])]

        print(f"### {spec['title']}")
        print()
        print(
            f"File `{spec['filename']}` at revision `{spec['revision']}` "
            f"({spec['note']}). KUQ-source rows with generation text: {len(pool)}; "
            f"true-gated arm rows among them: {len(gated)}; "
            f"narrow/wide disagreements on the true-gated arm: {len(disagree)}; "
            f"true-gated rows the wide instrument does not credit as abstention: "
            f"{len(failures)}."
        )
        print()

        chosen = []

        def draw(candidates, k):
            fresh = [
                r for r in candidates
                if (r["row_key"], r["arm"]) not in {(c["row_key"], c["arm"]) for c in chosen}
            ]
            picked = rng.sample(fresh, k) if len(fresh) >= k else fresh
            chosen.extend(picked)
            return picked

        for i, row in enumerate(draw(pool, 3), start=1):
            print(render(row, spec, f"Uniform draw {i} of 3"))
        picked = draw(disagree, 1)
        if picked:
            print(render(picked[0], spec, "Instrument-disagreement draw"))
        else:
            print("**Instrument-disagreement draw**: stratum empty in this dataset.")
            print()
        picked = draw(failures, 1)
        if picked:
            print(render(picked[0], spec, "Failure-case draw"))
        else:
            print("**Failure-case draw**: stratum empty in this dataset.")
            print()


if __name__ == "__main__":
    main()
