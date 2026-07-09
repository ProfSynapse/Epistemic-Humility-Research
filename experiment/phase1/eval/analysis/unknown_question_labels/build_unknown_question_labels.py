"""Build a labeling-ready manifest for unknown-question rows.

This is an exploratory labeling aid. It only consumes row-pattern analysis
outputs and only includes rows where the dataset label is ``unknown``.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[5]
ROW_PATTERN_ARTIFACT_ROOT = ROOT / "papers" / "paper-2-training-regimen" / "analysis" / "row-pattern"
DEFAULT_INPUT_DIR = ROW_PATTERN_ARTIFACT_ROOT / "row_pattern_outputs"
DEFAULT_OUTPUT_DIR = ROW_PATTERN_ARTIFACT_ROOT / "unknown_question_labels"

DOMAINS = {
    "science_health",
    "everyday_practical_subjective",
    "people_biography",
    "math_logic",
    "arts_entertainment_literature",
    "business_technology",
    "history_politics_law",
    "geography_places",
    "religion_philosophy_ethics",
    "sports_games",
    "other_unclear",
}

EPISTEMIC_TYPES = {
    "impossible_false_premise",
    "underspecified",
    "subjective_normative",
    "future_or_unverifiable",
    "ambiguous",
    "obscure_long_tail_fact",
    "counterfactual_hypothetical",
    "math_word_problem_missing_info",
    "other_unclear",
}

ARM_ORDER = ("sft_merged", "sft_dpo", "sft_kto")


def normalize_question(question: str) -> str:
    return re.sub(r"\s+", " ", question.strip().lower())


def question_hash(question: str) -> str:
    return hashlib.sha256(normalize_question(question).encode("utf-8")).hexdigest()[:16]


def truthy(value: str | bool | None) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "y"}


def is_answered(row: dict[str, str]) -> bool:
    state = row.get("behavior_state", "")
    if state:
        return state == "unknown_answered_hallucination_exposure"
    return not truthy(row.get("refused"))


def read_unknown_rows(input_dir: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for filename in ("row_master_amendment_a.csv", "row_master_amendment_b.csv"):
        path = input_dir / filename
        with path.open(newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row.get("include_status") == "include" and row.get("label") == "unknown":
                    rows.append(row)
    return rows


def _has_any(text: str, words: Iterable[str]) -> bool:
    return any(re.search(rf"\b{re.escape(word)}\b", text) for word in words)


def classify_domain(question: str) -> tuple[str, str, str, str]:
    text = normalize_question(question)
    scores: Counter[str] = Counter()
    notes: list[str] = []

    keyword_groups = {
        "science_health": (
            "disease",
            "health",
            "medicine",
            "doctor",
            "calories",
            "mineral",
            "virus",
            "biology",
            "physics",
            "chemistry",
            "planet",
            "star",
            "cosmic",
            "big bang",
            "big rip",
            "brain",
            "body",
            "animal",
            "bird",
            "forest fire",
        ),
        "everyday_practical_subjective": (
            "would you rather",
            "best",
            "should i",
            "should we",
            "how can i",
            "how do i",
            "personal",
            "prefer",
            "better",
            "credit card",
            "gps",
            "print",
            "calendar",
            "month",
        ),
        "people_biography": (
            "who ",
            "whose",
            "person",
            "actor",
            "singer",
            "author",
            "invented",
            "created",
            "born",
            "died",
            "george",
            "bush",
            "president",
            "vice president",
        ),
        "math_logic": (
            "number",
            "sum",
            "calculate",
            "probability",
            "logic",
            "puzzle",
            "how many",
            "times",
            "equation",
            "percent",
        ),
        "arts_entertainment_literature": (
            "movie",
            "film",
            "song",
            "album",
            "book",
            "novel",
            "poem",
            "entertainment",
            "sequel",
            "character",
            "episode",
        ),
        "business_technology": (
            "company",
            "business",
            "market",
            "stock",
            "software",
            "program",
            "robot",
            "computer",
            "digital",
            "internet",
            "app",
            "ai",
        ),
        "history_politics_law": (
            "war",
            "king",
            "queen",
            "law",
            "court",
            "election",
            "government",
            "senate",
            "congress",
            "constitution",
            "president",
            "vice president",
        ),
        "geography_places": (
            "where",
            "country",
            "city",
            "state",
            "river",
            "mountain",
            "island",
            "capital",
            "located",
        ),
        "religion_philosophy_ethics": (
            "god",
            "religion",
            "soul",
            "afterlife",
            "beforelife",
            "ethics",
            "moral",
            "philosophy",
            "meaning of life",
        ),
        "sports_games": (
            "sport",
            "game",
            "team",
            "player",
            "score",
            "league",
            "championship",
            "olympic",
            "chess",
            "football",
            "baseball",
        ),
    }
    for domain, keywords in keyword_groups.items():
        for keyword in keywords:
            if keyword in text:
                scores[domain] += 1

    if not scores:
        return "other_unclear", "", "low", "no deterministic domain keyword matched"

    ranked = scores.most_common()
    primary = ranked[0][0]
    secondary = ranked[1][0] if len(ranked) > 1 and ranked[1][1] > 0 else ""
    confidence = "high" if ranked[0][1] >= 2 and (len(ranked) == 1 or ranked[0][1] > ranked[1][1]) else "medium"
    notes.append(f"domain keyword score {dict(ranked[:3])}")
    return primary, secondary, confidence, "; ".join(notes)


def classify_epistemic_type(question: str) -> tuple[str, str]:
    text = normalize_question(question)
    if _has_any(text, ("would", "rather", "prefer", "best", "better", "should")):
        return "subjective_normative", "preference/normative phrasing"
    if _has_any(text, ("will", "future", "ever", "next")):
        return "future_or_unverifiable", "future or not-yet-verifiable phrasing"
    if "if " in text or _has_any(text, ("could have", "would have", "hypothetical", "counterfactual")):
        return "counterfactual_hypothetical", "hypothetical/counterfactual phrasing"
    if re.search(r"\b(the|this|that|it|he|she|they)\b", text) and _has_any(
        text, ("original", "sequel", "same", "only", "other")
    ):
        return "underspecified", "referent appears under-specified"
    if _has_any(text, ("how many", "calculate", "percent", "probability", "equation")):
        return "math_word_problem_missing_info", "math/quantity prompt likely needs missing facts"
    if _has_any(text, ("can birds", "beforelife", "made-up", "florb", "only through")):
        return "impossible_false_premise", "impossible or false-premise cue"
    if _has_any(text, ("who", "when", "where", "which", "what form", "invented", "decided")):
        return "obscure_long_tail_fact", "long-tail fact-seeking phrasing"
    if len(text.split()) <= 5 or _has_any(text, ("same", "related", "only")):
        return "ambiguous", "short or ambiguous relation prompt"
    return "other_unclear", "no deterministic epistemic-type keyword matched"


def answer_form(question: str) -> str:
    text = normalize_question(question)
    if text.startswith(("is ", "are ", "was ", "were ", "did ", "do ", "does ", "can ", "could ", "would ", "should ")):
        if "would you rather" in text:
            return "preference_choice"
        return "yes_no"
    if text.startswith(("who ", "what ", "when ", "where ", "which ")):
        return "wh_short_fact"
    if text.startswith(("why ", "how ")):
        return "open_explanatory"
    if _has_any(text, ("how many", "calculate", "percent", "probability")):
        return "math_numeric"
    if " or " in text:
        return "list_or_compare"
    return "other"


def compact_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def make_manifest(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        if row.get("include_status") != "include" or row.get("label") != "unknown":
            continue
        grouped[(row["analysis_family"], question_hash(row["question"]))].append(row)

    manifest: list[dict[str, str]] = []
    for (family, q_hash), group in sorted(grouped.items(), key=lambda item: (item[0][0], item[1][0]["eval_set"], item[1][0]["row_index"])):
        question = group[0]["question"]
        primary, secondary, confidence, domain_note = classify_domain(question)
        epistemic, epistemic_note = classify_epistemic_type(question)

        answered_rows = [row for row in group if is_answered(row)]
        refused_rows = [row for row in group if not is_answered(row)]
        answered_arms = sorted({row["arm_role"] for row in answered_rows}, key=lambda arm: ARM_ORDER.index(arm) if arm in ARM_ORDER else 99)
        refused_arms = sorted({row["arm_role"] for row in refused_rows}, key=lambda arm: ARM_ORDER.index(arm) if arm in ARM_ORDER else 99)
        examples: dict[str, list[dict[str, str]]] = defaultdict(list)
        source_ids: list[str] = []
        confidences: list[float] = []

        for row in sorted(group, key=lambda r: (r.get("seed", ""), r.get("arm_role", ""), r.get("row_index", ""))):
            source_ids.append(
                "|".join(
                    [
                        row.get("analysis_family", ""),
                        row.get("eval_set", ""),
                        row.get("seed", ""),
                        row.get("arm_role", ""),
                        row.get("row_index", ""),
                        row.get("id", ""),
                        row.get("row_hash", ""),
                    ]
                )
            )
            if len(examples[row["arm_role"]]) < 3:
                examples[row["arm_role"]].append(
                    {
                        "seed": row.get("seed", ""),
                        "answer": row.get("answer_text") or row.get("generated_answer", ""),
                        "refused": "false" if is_answered(row) else "true",
                        "stated_confidence": row.get("stated_confidence", ""),
                    }
                )
            if row.get("stated_confidence"):
                try:
                    confidences.append(float(row["stated_confidence"]))
                except ValueError:
                    pass

        manifest.append(
            {
                "question_key": f"{family}:{q_hash}",
                "question_hash": q_hash,
                "question": question,
                "eval_sets": ";".join(sorted({row["eval_set"] for row in group})),
                "analysis_family_coverage": family,
                "evidence_tier": "exploratory",
                "provisional_primary_domain": primary,
                "provisional_secondary_domain": secondary,
                "provisional_epistemic_type": epistemic,
                "answer_form": answer_form(question),
                "category_confidence": confidence,
                "label_notes": f"{domain_note}; {epistemic_note}",
                "answered_by_any_arm": str(bool(answered_arms)).lower(),
                "answered_by_dpo": str(any(row["arm_role"] == "sft_dpo" for row in answered_rows)).lower(),
                "answered_by_kto": str(any(row["arm_role"] == "sft_kto" for row in answered_rows)).lower(),
                "arms_answered": ";".join(answered_arms),
                "arms_refused": ";".join(refused_arms),
                "dpo_answered": str(any(row["arm_role"] == "sft_dpo" for row in answered_rows)).lower(),
                "kto_answered": str(any(row["arm_role"] == "sft_kto" for row in answered_rows)).lower(),
                "sft_merged_refused": str(any(row["arm_role"] == "sft_merged" and not is_answered(row) for row in group)).lower(),
                "max_confidence_if_b": f"{max(confidences):.6f}" if confidences else "",
                "example_answers_by_arm": compact_json(dict(examples)),
                "source_row_ids": compact_json(source_ids),
            }
        )
    return manifest


def write_manifest(rows: list[dict[str, str]], output_path: Path) -> None:
    fieldnames = [
        "question_key",
        "question_hash",
        "question",
        "eval_sets",
        "analysis_family_coverage",
        "evidence_tier",
        "provisional_primary_domain",
        "provisional_secondary_domain",
        "provisional_epistemic_type",
        "answer_form",
        "category_confidence",
        "label_notes",
        "answered_by_any_arm",
        "answered_by_dpo",
        "answered_by_kto",
        "arms_answered",
        "arms_refused",
        "dpo_answered",
        "kto_answered",
        "sft_merged_refused",
        "max_confidence_if_b",
        "example_answers_by_arm",
        "source_row_ids",
    ]
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _top(counter: Counter[str], n: int = 12) -> str:
    if not counter:
        return "- None\n"
    return "".join(f"- {key}: {value}\n" for key, value in counter.most_common(n))


def write_summary(manifest: list[dict[str, str]], output_path: Path) -> None:
    by_family = Counter(row["analysis_family_coverage"] for row in manifest)
    by_domain = Counter(row["provisional_primary_domain"] for row in manifest)
    by_epistemic = Counter(row["provisional_epistemic_type"] for row in manifest)
    by_behavior = Counter(
        (
            f"any_answered={row['answered_by_any_arm']};"
            f"dpo_answered={row['dpo_answered']};"
            f"kto_answered={row['kto_answered']};"
            f"sft_merged_refused={row['sft_merged_refused']}"
        )
        for row in manifest
    )
    by_family_domain = Counter(
        f"{row['analysis_family_coverage']} / {row['provisional_primary_domain']}" for row in manifest
    )
    by_family_epistemic = Counter(
        f"{row['analysis_family_coverage']} / {row['provisional_epistemic_type']}" for row in manifest
    )
    answered_manifest = [row for row in manifest if row["answered_by_any_arm"] == "true"]
    top_answered_domains = Counter(row["provisional_primary_domain"] for row in answered_manifest)
    top_answered_epistemic = Counter(row["provisional_epistemic_type"] for row in answered_manifest)

    lines = [
        "# Unknown Question Label Manifest Summary",
        "",
        "Evidence tier: exploratory. Labels are provisional deterministic heuristics for human labeling triage, not scientific taxonomy claims.",
        "",
        f"- Unique unknown question rows in manifest: {len(manifest)}",
        f"- Unique unknown questions answered by any arm: {len(answered_manifest)}",
        f"- Unique unknown questions answered by DPO: {sum(row['dpo_answered'] == 'true' for row in manifest)}",
        f"- Unique unknown questions answered by KTO: {sum(row['kto_answered'] == 'true' for row in manifest)}",
        "",
        "## Counts By Family",
        "",
        _top(by_family),
        "## Counts By Provisional Primary Domain",
        "",
        _top(by_domain),
        "## Counts By Provisional Epistemic Type",
        "",
        _top(by_epistemic),
        "## Counts By Arm Behavior",
        "",
        _top(by_behavior),
        "## Top Family/Domain Clusters",
        "",
        _top(by_family_domain),
        "## Top Family/Epistemic-Type Clusters",
        "",
        _top(by_family_epistemic),
        "## Top Answered-By-Any-Arm Domains",
        "",
        _top(top_answered_domains),
        "## Top Answered-By-Any-Arm Epistemic Types",
        "",
        _top(top_answered_epistemic),
        "## Selection Rules",
        "",
        "- Source files: row_master_amendment_a.csv and row_master_amendment_b.csv.",
        "- Include only rows with include_status=include and label=unknown.",
        "- Aggregate at question_key = analysis_family + normalized-question SHA-256 prefix, keeping Amendment A and Amendment B separate.",
        "- Treat behavior_state=unknown_answered_hallucination_exposure as answered; otherwise use refused to distinguish answered/refused.",
        "- Preserve Amendment B stated confidence only as max_confidence_if_b.",
    ]
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(input_dir: Path = DEFAULT_INPUT_DIR, output_dir: Path = DEFAULT_OUTPUT_DIR) -> dict[str, int]:
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = read_unknown_rows(input_dir)
    manifest = make_manifest(rows)
    write_manifest(manifest, output_dir / "unknown_question_label_manifest.csv")
    write_summary(manifest, output_dir / "unknown_question_label_summary.md")
    return {
        "source_unknown_rows": len(rows),
        "manifest_questions": len(manifest),
        "answered_by_any_arm": sum(row["answered_by_any_arm"] == "true" for row in manifest),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    summary = run(args.input_dir, args.output_dir)
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
