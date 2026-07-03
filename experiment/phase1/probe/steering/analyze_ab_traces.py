"""Amendment AB trace-pattern analysis (descriptive, post-hoc — not a gate).

Reads Arm B result.json files (gitignored raw artifacts) and emits an
aggregate report safe to commit: note-echo/marker rates, decision-level
transition flows, injected-score gradients, abstention compliance, and the
revised-flag saturation check that invalidates `revision_discrimination`
as an instrument under sampled decode (see report notes).

Usage:
  python3 analyze_ab_traces.py --result results/ab-2-dial-late-v1/result.json \
      --out reports/ab_v1/ab-2-trace-report.json
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

MARKERS = {
    "echo_pct": lambda t: bool(re.search(r"\d+\s*%", t)),
    "echo_confidence_words": lambda t: any(
        w in t for w in ("confiden", "sure", "internal sense")
    ),
    "verify_words": lambda t: any(
        w in t for w in ("verify", "double-check", "check")
    ),
    "wait": lambda t: "wait" in t,
    "idk_words": lambda t: any(
        w in t for w in ("i don't know", "not certain", "cannot recall", "unsure")
    ),
}


def grade_state(g: dict) -> str:
    if g["abstained"]:
        return "abstain"
    if g["correct"] is None:  # ungraded (e.g. unanswerable gate-pool rows)
        return "answered_ungraded"
    return "correct" if g["correct"] else "wrong"


def marker_rates(items: list[dict]) -> dict:
    n = len(items)
    out = {}
    for name, fn in MARKERS.items():
        out[name] = round(sum(fn(x["final_text"].lower()) for x in items) / n, 4)
    return out


def transition_flows(items: list[dict]) -> dict:
    flows: dict[str, int] = {}
    for x in items:
        key = f"{grade_state(x['initial_grade'])}->{grade_state(x['final_grade'])}"
        flows[key] = flows.get(key, 0) + 1
    return dict(sorted(flows.items()))


def conditional_rates(items: list[dict]) -> dict:
    wrong = [x for x in items if grade_state(x["initial_grade"]) == "wrong"]
    corr = [x for x in items if grade_state(x["initial_grade"]) == "correct"]
    out = {}
    if wrong:
        out["p_final_correct_given_initial_wrong"] = round(
            sum(bool(x["final_grade"]["correct"]) for x in wrong) / len(wrong), 4
        )
        out["p_final_abstain_given_initial_wrong"] = round(
            sum(bool(x["final_grade"]["abstained"]) for x in wrong) / len(wrong), 4
        )
        out["n_initial_wrong"] = len(wrong)
    if corr:
        out["p_final_correct_given_initial_correct"] = round(
            sum(bool(x["final_grade"]["correct"]) for x in corr) / len(corr), 4
        )
        out["n_initial_correct"] = len(corr)
    return out


def score_tercile_gradient(items: list[dict]) -> dict:
    """wrong->correct flip rate in the bottom vs top injected-score tercile.

    In the real arm the injected score is the probe read for the item, so a
    gradient here means the probe predicts which wrong answers are
    recoverable on re-derivation; the placebo arm (permuted scores) is the
    control that separates that item-level information from any causal use
    of the note text.
    """
    scored = sorted(items, key=lambda x: x["injected_score"])
    k = len(scored) // 3
    out = {}
    for name, sub in (("lo_tercile", scored[:k]), ("hi_tercile", scored[-k:])):
        wrong = [x for x in sub if grade_state(x["initial_grade"]) == "wrong"]
        out[name] = {
            "score_range": [
                round(sub[0]["injected_score"], 3),
                round(sub[-1]["injected_score"], 3),
            ],
            "n_wrong": len(wrong),
            "wrong_to_correct": round(
                sum(bool(x["final_grade"]["correct"]) for x in wrong) / len(wrong), 4
            )
            if wrong
            else None,
        }
    return out


def abstention_compliance(items: list[dict]) -> dict:
    abst = [x for x in items if x["final_grade"]["abstained"]]
    return {
        "n_final_abstain": len(abst),
        "abstainer_injected_scores": [round(x["injected_score"], 3) for x in abst],
        "abstainer_continuation_heads": [x["final_text"][:80] for x in abst[:8]],
    }


def saturation_check(items: list[dict]) -> dict:
    n = len(items)
    n_rev = sum(bool(x["revised"]) for x in items)
    return {
        "n_items": n,
        "n_revised_true": n_rev,
        "saturated": n_rev == n,
    }


def analyze(result_path: Path) -> dict:
    d = json.loads(result_path.read_text())
    report = {
        "source_result": str(result_path),
        "cell": d.get("cell"),
        "signal": d.get("signal"),
        "position": d.get("position"),
        "note_variant": d.get("config", {}).get("note_variant"),
        "config_sha": d.get("config_sha"),
        "created_utc": d.get("created_utc"),
        "summary_as_recorded": d.get("summary"),
        "arms": {},
    }
    for arm, items in d["items"].items():
        report["arms"][arm] = {
            "marker_rates": marker_rates(items),
            "transition_flows": transition_flows(items),
            "conditional_rates": conditional_rates(items),
            "score_tercile_gradient": score_tercile_gradient(items),
            "abstention_compliance": abstention_compliance(items),
            "revised_flag_saturation": saturation_check(items),
        }
    return report


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--result", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    report = analyze(args.result)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=1) + "\n")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
