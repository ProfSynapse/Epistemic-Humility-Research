"""Deterministic exploratory row-pattern analysis for Phase 1 local artifacts."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


COMMON_COLUMNS = [
    "analysis_family",
    "prompt_contract",
    "evidence_scope",
    "include_status",
    "exclude_reason",
    "result_dir",
    "arm_dir",
    "arm_raw",
    "arm_role",
    "objective_path",
    "seed",
    "eval_set",
    "row_index",
    "id",
    "question",
    "label",
    "source",
    "dataset",
    "generated_answer",
    "answer_text",
    "refused",
    "correct",
    "truthful",
    "method",
    "model",
    "config_sha",
    "behavior_state",
    "question_tags",
    "cluster_key",
    "row_hash",
]

B_COLUMNS = [
    "stated_confidence",
    "generation_attempts",
    "stated_confidence_retry_count",
    "stated_confidence_retry_exhausted",
    "confidence_bin",
    "confidence_delta_from_sft_merged",
]

QUESTION_TAGS = [
    "person",
    "place",
    "date_time",
    "number",
    "definition",
    "list",
    "comparison",
    "causal",
    "temporal_future",
    "subjective_normative",
    "quote_present",
    "entity_heavy",
]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[5]


def default_artifact_root() -> Path:
    return repo_root() / "papers" / "paper-2-training-regimen" / "analysis" / "row-pattern"


def load_manifest(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    return list(data["inputs"])


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def rel_path(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def bool_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        value = value.strip().lower()
        if value in {"true", "1", "yes"}:
            return "true"
        if value in {"false", "0", "no"}:
            return "false"
    return "true" if bool(value) else "false"


def scalar_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return bool_text(value)
    return str(value)


def is_true(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes"}
    return bool(value)


def wh_word(question: str) -> str:
    match = re.match(r"\s*([A-Za-z]+)", question or "")
    word = match.group(1).lower() if match else "none"
    return word if word in {"who", "what", "when", "where", "why", "how", "which"} else "other"


def length_bucket(question: str) -> str:
    words = re.findall(r"\w+", question or "")
    n = len(words)
    if n <= 8:
        return "short"
    if n <= 18:
        return "medium"
    return "long"


def mechanical_question_tags(question: str) -> list[str]:
    q = question or ""
    lower = q.lower()
    tags = []
    if re.search(r"\b(who|person|people|actor|artist|author|president|minister|king|queen)\b", lower):
        tags.append("person")
    if re.search(r"\b(where|city|country|state|river|mountain|located|place|capital)\b", lower):
        tags.append("place")
    if re.search(r"\b(when|year|date|century|decade|month|day|born|died|founded)\b", lower):
        tags.append("date_time")
    if re.search(r"\b(how many|number|population|percent|percentage|score|amount|age)\b|\d", lower):
        tags.append("number")
    if re.search(r"\b(what is|what are|define|definition|meaning|means|term)\b", lower):
        tags.append("definition")
    if re.search(r"\b(list|name all|which of the following|examples|types of)\b", lower):
        tags.append("list")
    if re.search(r"\b(compare|versus|vs\.?|difference|similar|more than|less than|largest|smallest|oldest|newest)\b", lower):
        tags.append("comparison")
    if re.search(r"\b(why|because|cause|caused|reason|explain)\b", lower):
        tags.append("causal")
    if re.search(r"\b(will|future|upcoming|next|forecast|predict)\b", lower):
        tags.append("temporal_future")
    if re.search(r"\b(should|best|worst|moral|ethical|opinion|better|prefer)\b", lower):
        tags.append("subjective_normative")
    if "'" in q or '"' in q:
        tags.append("quote_present")
    properish = re.findall(r"\b[A-Z][a-zA-Z0-9'.-]+\b", q)
    if len(properish) >= 4:
        tags.append("entity_heavy")
    tags.append(f"wh_{wh_word(q)}")
    tags.append(f"question_length_{length_bucket(q)}")
    return tags


def answer_bin(row: dict[str, Any]) -> str:
    answer = (row.get("answer_text") or row.get("generated_answer") or "").strip()
    if is_true(row.get("refused")):
        return "refusal"
    if not answer:
        return "empty"
    words = re.findall(r"\w+", answer)
    if len(words) <= 8:
        return "answered_short"
    if len(words) <= 40:
        return "answered_medium"
    return "answered_long"


def confidence_bin(value: Any) -> str:
    if value is None or value == "":
        return ""
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        return "invalid"
    if confidence < 0.0 or confidence > 1.0:
        return "out_of_range"
    if confidence < 0.34:
        return "low"
    if confidence < 0.67:
        return "medium"
    return "high"


def behavior_state(row: dict[str, Any]) -> str:
    label = str(row.get("label", "")).lower()
    refused = is_true(row.get("refused"))
    correct = is_true(row.get("correct"))
    if label == "unknown" and refused:
        return "unknown_refused_accurate_idk"
    if label == "unknown" and not refused:
        return "unknown_answered_hallucination_exposure"
    if label == "known" and refused:
        return "known_refused_overrefusal"
    if label == "known" and not refused and correct:
        return "known_answered_correct_useful"
    if label == "known" and not refused and not correct:
        return "known_answered_incorrect_failure"
    return "unclassified"


def cluster_key(row: dict[str, Any], q_tags: list[str], conf_bin: str) -> str:
    mechanical = [tag for tag in q_tags if tag.startswith("wh_") or tag.startswith("question_length_")]
    topic = [tag for tag in q_tags if tag in QUESTION_TAGS]
    topic_text = "+".join(topic) if topic else "no_topic_tag"
    parts = [
        f"label={row.get('label', '')}",
        *mechanical,
        f"topic={topic_text}",
        f"behavior={behavior_state(row)}",
        f"answer={answer_bin(row)}",
    ]
    if conf_bin:
        parts.append(f"confidence={conf_bin}")
    return "|".join(parts)


def stable_row_hash(row: dict[str, Any]) -> str:
    payload = {
        "analysis_family": row["analysis_family"],
        "seed": row["seed"],
        "eval_set": row["eval_set"],
        "arm_role": row["arm_role"],
        "row_index": row["row_index"],
        "id": row["id"],
        "question": row["question"],
        "label": row["label"],
    }
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:16]


def normalize_row(entry: dict[str, Any], raw: dict[str, Any]) -> dict[str, Any]:
    answer_text = raw.get("answer_text")
    if answer_text is None:
        answer_text = raw.get("generated_answer", "")
    cbin = confidence_bin(raw.get("stated_confidence"))
    q_tags = mechanical_question_tags(raw.get("question", ""))
    row = {
        "analysis_family": entry["analysis_family"],
        "prompt_contract": entry["prompt_contract"],
        "evidence_scope": entry["evidence_scope"],
        "include_status": entry["include_status"],
        "exclude_reason": entry.get("exclude_reason", ""),
        "result_dir": entry["result_dir"],
        "arm_dir": entry["arm_dir"],
        "arm_raw": raw.get("arm", ""),
        "arm_role": entry["arm_role"],
        "objective_path": entry["objective_path"],
        "seed": int(entry["seed"]),
        "eval_set": entry["eval_set"],
        "row_index": int(raw.get("row_index", -1)),
        "id": raw.get("id", ""),
        "question": raw.get("question", ""),
        "label": raw.get("label", ""),
        "source": raw.get("source", ""),
        "dataset": raw.get("source") or entry["eval_set"],
        "generated_answer": raw.get("generated_answer", ""),
        "answer_text": answer_text,
        "refused": bool_text(raw.get("refused")),
        "correct": bool_text(raw.get("correct")),
        "truthful": bool_text(raw.get("truthful")),
        "method": raw.get("method", ""),
        "model": raw.get("model", ""),
        "config_sha": raw.get("config_sha", ""),
        "stated_confidence": scalar_text(raw.get("stated_confidence")),
        "generation_attempts": scalar_text(raw.get("generation_attempts")),
        "stated_confidence_retry_count": scalar_text(raw.get("stated_confidence_retry_count")),
        "stated_confidence_retry_exhausted": bool_text(raw.get("stated_confidence_retry_exhausted"))
        if "stated_confidence_retry_exhausted" in raw
        else "",
        "confidence_bin": cbin,
    }
    state_input = {
        "label": row["label"],
        "refused": row["refused"] == "true",
        "correct": row["correct"] == "true",
        "generated_answer": row["generated_answer"],
        "answer_text": row["answer_text"],
    }
    row["behavior_state"] = behavior_state(state_input)
    row["question_tags"] = "|".join(q_tags)
    row["cluster_key"] = cluster_key(state_input, q_tags, cbin)
    row["confidence_delta_from_sft_merged"] = ""
    row["row_hash"] = stable_row_hash(row)
    return row


def count_rows(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts = {
        "n": len(rows),
        "n_unknown_labeled": 0,
        "n_known_labeled": 0,
        "refuse_on_unknown": 0,
        "refuse_on_known": 0,
        "answered_known": 0,
        "correct_known": 0,
        "answered_unknown": 0,
        "correct_unknown": 0,
    }
    for row in rows:
        label = str(row.get("label", "")).lower()
        refused = is_true(row.get("refused"))
        correct = is_true(row.get("correct"))
        if label == "unknown":
            counts["n_unknown_labeled"] += 1
            if refused:
                counts["refuse_on_unknown"] += 1
            else:
                counts["answered_unknown"] += 1
            if correct:
                counts["correct_unknown"] += 1
        elif label == "known":
            counts["n_known_labeled"] += 1
            if refused:
                counts["refuse_on_known"] += 1
            else:
                counts["answered_known"] += 1
            if correct:
                counts["correct_known"] += 1
    return counts


def inventory_and_rows(entries: list[dict[str, Any]], root: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    inventory = []
    schema_audit = []
    row_master = []
    errors = []
    for entry in sorted(entries, key=lambda e: (e["analysis_family"], int(e["seed"]), e["eval_set"], e["arm_role"], e["result_dir"], e["arm_dir"])):
        arm_path = root / entry["result_dir"] / entry["arm_dir"]
        rows_path = arm_path / "scored_rows.jsonl"
        metrics_path = arm_path / "metrics.json"
        rows = read_jsonl(rows_path) if rows_path.exists() else []
        metrics = read_json(metrics_path)
        inventory.append(
            {
                **{key: scalar_text(entry.get(key, "")) for key in ["analysis_family", "prompt_contract", "evidence_scope", "include_status", "exclude_reason", "result_dir", "arm_dir", "arm_role", "objective_path", "seed", "eval_set"]},
                "scored_rows_path": rel_path(rows_path, root),
                "scored_rows_exists": bool_text(rows_path.exists()),
                "metrics_path": rel_path(metrics_path, root),
                "metrics_exists": bool_text(metrics_path.exists()),
                "row_count": len(rows),
            }
        )
        keys = sorted({key for row in rows for key in row})
        schema_audit.append(
            {
                "analysis_family": entry["analysis_family"],
                "prompt_contract": entry["prompt_contract"],
                "include_status": entry["include_status"],
                "result_dir": entry["result_dir"],
                "arm_dir": entry["arm_dir"],
                "row_count": len(rows),
                "schema_keys": "|".join(keys),
                "has_answer_text": bool_text("answer_text" in keys),
                "has_stated_confidence": bool_text("stated_confidence" in keys),
                "metrics_count_n": metrics.get("counts", {}).get("n", ""),
                "computed_count_n": len(rows),
                "counts_match": bool_text(metrics.get("counts", {}).get("n", len(rows)) == len(rows)),
            }
        )
        if entry["include_status"] != "include":
            continue
        if not rows_path.exists():
            errors.append(f"missing included scored_rows: {rel_path(rows_path, root)}")
            continue
        metrics_counts = metrics.get("counts", {})
        computed = count_rows(rows)
        for key, value in computed.items():
            if key in metrics_counts and metrics_counts[key] != value:
                errors.append(f"metrics count mismatch for {entry['arm_dir']} {key}: metrics={metrics_counts[key]} computed={value}")
        if entry["analysis_family"] == "amendment_b":
            required_b = {"answer_text", "stated_confidence"}
            missing_b = required_b - set(keys)
            if missing_b:
                errors.append(f"missing Amendment B keys in {entry['arm_dir']}: {sorted(missing_b)}")
        row_master.extend(normalize_row(entry, raw) for raw in rows)
    apply_confidence_deltas(row_master)
    return inventory, schema_audit, row_master, errors


def apply_confidence_deltas(rows: list[dict[str, Any]]) -> None:
    baselines = {}
    for row in rows:
        if row["analysis_family"] == "amendment_b" and row["arm_role"] == "sft_merged" and row["stated_confidence"] != "":
            key = (row["analysis_family"], row["seed"], row["eval_set"], row["row_index"], row["id"])
            baselines[key] = float(row["stated_confidence"])
    for row in rows:
        if row["analysis_family"] != "amendment_b" or row["stated_confidence"] == "":
            continue
        key = (row["analysis_family"], row["seed"], row["eval_set"], row["row_index"], row["id"])
        if key in baselines:
            row["confidence_delta_from_sft_merged"] = f"{float(row['stated_confidence']) - baselines[key]:.6f}"


def alignment_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return (row["analysis_family"], row["prompt_contract"], row["seed"], row["eval_set"], row["row_index"])


def transition_label(before: str, after: str) -> str:
    if before == "unknown_refused_accurate_idk" and after == "unknown_answered_hallucination_exposure":
        return "unknown_refused_to_answered"
    if before == "unknown_answered_hallucination_exposure" and after == "unknown_refused_accurate_idk":
        return "unknown_answered_to_refused"
    if before == "known_refused_overrefusal" and after == "known_answered_correct_useful":
        return "known_refused_to_correct_answer"
    if before == "known_refused_overrefusal" and after == "known_answered_incorrect_failure":
        return "known_refused_to_incorrect_answer"
    if before == "known_answered_correct_useful" and after in {"known_refused_overrefusal", "known_answered_incorrect_failure"}:
        return "known_correct_to_failure"
    if before == after:
        return "unchanged"
    return f"{before}__to__{after}"


def paired_transitions(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    errors = []
    grouped: dict[tuple[Any, ...], dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        grouped[alignment_key(row)][row["arm_role"]] = row
    transitions = []
    for key in sorted(grouped):
        arms = grouped[key]
        baseline = arms.get("sft_merged")
        if not baseline:
            continue
        for target_role in ["sft_dpo", "sft_kto"]:
            target = arms.get(target_role)
            if not target:
                continue
            for field in ["id", "question", "label", "source"]:
                if baseline[field] != target[field]:
                    errors.append(f"alignment mismatch {key} {target_role} {field}")
            conf_delta = ""
            if target["analysis_family"] == "amendment_b" and target["stated_confidence"] and baseline["stated_confidence"]:
                conf_delta = f"{float(target['stated_confidence']) - float(baseline['stated_confidence']):.6f}"
            transitions.append(
                {
                    "analysis_family": baseline["analysis_family"],
                    "prompt_contract": baseline["prompt_contract"],
                    "evidence_scope": baseline["evidence_scope"],
                    "seed": baseline["seed"],
                    "eval_set": baseline["eval_set"],
                    "row_index": baseline["row_index"],
                    "id": baseline["id"],
                    "label": baseline["label"],
                    "source": baseline["source"],
                    "question": baseline["question"],
                    "comparison": f"sft_merged_to_{target_role}",
                    "from_arm_role": "sft_merged",
                    "to_arm_role": target_role,
                    "from_behavior_state": baseline["behavior_state"],
                    "to_behavior_state": target["behavior_state"],
                    "transition": transition_label(baseline["behavior_state"], target["behavior_state"]),
                    "from_refused": baseline["refused"],
                    "to_refused": target["refused"],
                    "from_correct": baseline["correct"],
                    "to_correct": target["correct"],
                    "from_answer_bin": answer_bin(baseline),
                    "to_answer_bin": answer_bin(target),
                    "from_stated_confidence": baseline.get("stated_confidence", ""),
                    "to_stated_confidence": target.get("stated_confidence", ""),
                    "confidence_delta_from_sft_merged": conf_delta,
                    "question_tags": baseline["question_tags"],
                    "cluster_key": target["cluster_key"],
                    "from_answer_text": baseline["answer_text"],
                    "to_answer_text": target["answer_text"],
                }
            )
    return transitions, errors


def cluster_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[(row["analysis_family"], row["prompt_contract"], row["arm_role"], row["cluster_key"])].append(row)
    out = []
    for key in sorted(groups):
        group = groups[key]
        states = Counter(row["behavior_state"] for row in group)
        eval_sets = Counter(row["eval_set"] for row in group)
        confs = [float(row["stated_confidence"]) for row in group if row.get("stated_confidence") not in {"", None}]
        out.append(
            {
                "analysis_family": key[0],
                "prompt_contract": key[1],
                "arm_role": key[2],
                "cluster_key": key[3],
                "n": len(group),
                "eval_sets": "|".join(f"{name}:{eval_sets[name]}" for name in sorted(eval_sets)),
                "behavior_states": "|".join(f"{name}:{states[name]}" for name in sorted(states)),
                "mean_stated_confidence": f"{sum(confs) / len(confs):.6f}" if confs else "",
            }
        )
    return out


def representative_examples(rows: list[dict[str, Any]], transitions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    examples = []
    seen = set()
    interesting = [
        "unknown_refused_to_answered",
        "unknown_answered_to_refused",
        "known_refused_to_correct_answer",
        "known_refused_to_incorrect_answer",
        "known_correct_to_failure",
    ]
    for transition_name in interesting:
        matches = [row for row in transitions if row["transition"] == transition_name]
        for row in sorted(matches, key=lambda r: (r["analysis_family"], int(r["seed"]), r["eval_set"], r["comparison"], int(r["row_index"])))[:8]:
            key = (row["analysis_family"], row["seed"], row["eval_set"], row["comparison"], row["row_index"])
            if key in seen:
                continue
            seen.add(key)
            examples.append(
                {
                    "example_type": "transition",
                    "analysis_family": row["analysis_family"],
                    "prompt_contract": row["prompt_contract"],
                    "seed": row["seed"],
                    "eval_set": row["eval_set"],
                    "comparison": row["comparison"],
                    "row_index": row["row_index"],
                    "id": row["id"],
                    "label": row["label"],
                    "transition": row["transition"],
                    "question_tags": row["question_tags"],
                    "question": row["question"],
                    "from_answer_text": row["from_answer_text"],
                    "to_answer_text": row["to_answer_text"],
                    "confidence_delta_from_sft_merged": row["confidence_delta_from_sft_merged"],
                }
            )
    by_cluster = sorted(rows, key=lambda r: (r["analysis_family"], r["arm_role"], r["cluster_key"], int(r["row_index"])))
    cluster_counts = Counter((row["analysis_family"], row["arm_role"], row["cluster_key"]) for row in rows)
    emitted_clusters = set()
    for row in by_cluster:
        ckey = (row["analysis_family"], row["arm_role"], row["cluster_key"])
        if ckey in emitted_clusters or cluster_counts[ckey] < 20:
            continue
        emitted_clusters.add(ckey)
        examples.append(
            {
                "example_type": "cluster_first_row",
                "analysis_family": row["analysis_family"],
                "prompt_contract": row["prompt_contract"],
                "seed": row["seed"],
                "eval_set": row["eval_set"],
                "comparison": "",
                "row_index": row["row_index"],
                "id": row["id"],
                "label": row["label"],
                "transition": "",
                "question_tags": row["question_tags"],
                "question": row["question"],
                "from_answer_text": "",
                "to_answer_text": row["answer_text"],
                "confidence_delta_from_sft_merged": row.get("confidence_delta_from_sft_merged", ""),
            }
        )
    return sorted(examples, key=lambda r: (r["analysis_family"], r["example_type"], r["seed"], r["eval_set"], r["comparison"], int(r["row_index"])))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def validation_summary(
    inventory: list[dict[str, Any]],
    schema_audit: list[dict[str, Any]],
    rows_a: list[dict[str, Any]],
    rows_b: list[dict[str, Any]],
    transitions_a: list[dict[str, Any]],
    transitions_b: list[dict[str, Any]],
    errors: list[str],
) -> dict[str, Any]:
    excluded_bad_merge = [row for row in inventory if row["include_status"] == "exclude" and "bad_merge" in row["exclude_reason"]]
    included_b_schema = [
        row for row in schema_audit if row["analysis_family"] == "amendment_b" and row["include_status"] == "include"
    ]
    b_confidence_nonempty = sum(1 for row in rows_b if row.get("stated_confidence", "") != "")
    b_answer_text_nonempty = sum(1 for row in rows_b if row.get("answer_text", "") != "")
    b_confidence_blank_retry_exhausted = sum(
        1
        for row in rows_b
        if row.get("stated_confidence", "") == "" and row.get("stated_confidence_retry_exhausted") == "true"
    )
    b_confidence_blank_not_retry_exhausted = sum(
        1
        for row in rows_b
        if row.get("stated_confidence", "") == "" and row.get("stated_confidence_retry_exhausted") != "true"
    )
    return {
        "evidence_tier": "local_bounded_exploratory_non_headline",
        "amendment_a_row_count": len(rows_a),
        "amendment_b_row_count": len(rows_b),
        "amendment_a_transition_count": len(transitions_a),
        "amendment_b_transition_count": len(transitions_b),
        "included_input_count": sum(1 for row in inventory if row["include_status"] == "include"),
        "excluded_input_count": sum(1 for row in inventory if row["include_status"] != "include"),
        "bad_merge_exclusion_present": bool(excluded_bad_merge),
        "amendment_b_schema_has_answer_text_column": bool(included_b_schema)
        and all(row["has_answer_text"] == "true" for row in included_b_schema),
        "amendment_b_schema_has_stated_confidence_column": bool(included_b_schema)
        and all(row["has_stated_confidence"] == "true" for row in included_b_schema),
        "amendment_b_answer_text_nonempty_count": b_answer_text_nonempty,
        "amendment_b_answer_text_blank_count": len(rows_b) - b_answer_text_nonempty,
        "amendment_b_stated_confidence_nonempty_count": b_confidence_nonempty,
        "amendment_b_stated_confidence_blank_count": len(rows_b) - b_confidence_nonempty,
        "amendment_b_stated_confidence_blank_retry_exhausted_count": b_confidence_blank_retry_exhausted,
        "amendment_b_stated_confidence_blank_not_retry_exhausted_count": b_confidence_blank_not_retry_exhausted,
        "families_separated": bool(rows_a and rows_b)
        and {row["analysis_family"] for row in rows_a} == {"amendment_a"}
        and {row["analysis_family"] for row in rows_b} == {"amendment_b"},
        "validation_errors": sorted(errors),
        "status": "pass" if not errors and rows_a and rows_b and transitions_a and transitions_b else "fail",
    }


def report_markdown(summary: dict[str, Any], rows_a: list[dict[str, Any]], rows_b: list[dict[str, Any]], transitions_a: list[dict[str, Any]], transitions_b: list[dict[str, Any]]) -> str:
    def family_lines(name: str, rows: list[dict[str, Any]], transitions: list[dict[str, Any]]) -> list[str]:
        by_arm = Counter(row["arm_role"] for row in rows)
        by_state = Counter(row["behavior_state"] for row in rows)
        by_transition = Counter(row["transition"] for row in transitions)
        lines = [
            f"## {name}",
            "",
            f"- Rows: {len(rows)}",
            f"- Paired SFT-to-DPO/KTO transitions: {len(transitions)}",
            f"- Arm rows: {', '.join(f'{key}={by_arm[key]}' for key in sorted(by_arm))}",
            f"- Top behavior states: {', '.join(f'{key}={by_state[key]}' for key, _ in by_state.most_common(6))}",
            f"- Top transitions: {', '.join(f'{key}={by_transition[key]}' for key, _ in by_transition.most_common(8))}",
            "",
        ]
        return lines

    lines = [
        "# SFT/DPO/KTO Row-Pattern Exploratory Analysis",
        "",
        "Evidence tier: local bounded exploratory/non-headline. This is a deterministic first-pass clustering/tagging pass using mechanical descriptors only; it does not assign final causal or semantic labels.",
        "",
        f"Validation status: {summary['status']}",
        f"Included inputs: {summary['included_input_count']}; excluded inventory-only inputs: {summary['excluded_input_count']}",
        f"Bad-merge seed2 DPO exclusion present: {summary['bad_merge_exclusion_present']}",
        "",
    ]
    lines.extend(family_lines("Amendment A: plain-answer contract", rows_a, transitions_a))
    lines.extend(family_lines("Amendment B: stated-confidence contract", rows_b, transitions_b))
    lines.extend(
        [
            "## Amendment B Confidence Validation",
            "",
            f"- `answer_text` column present in included B schemas: {summary['amendment_b_schema_has_answer_text_column']}",
            f"- `stated_confidence` column present in included B schemas: {summary['amendment_b_schema_has_stated_confidence_column']}",
            f"- Non-empty `answer_text`: {summary['amendment_b_answer_text_nonempty_count']} / {summary['amendment_b_row_count']}",
            f"- Non-empty `stated_confidence`: {summary['amendment_b_stated_confidence_nonempty_count']} / {summary['amendment_b_row_count']}",
            f"- Blank `stated_confidence` with retry exhaustion: {summary['amendment_b_stated_confidence_blank_retry_exhausted_count']}",
            f"- Blank `stated_confidence` without retry exhaustion: {summary['amendment_b_stated_confidence_blank_not_retry_exhausted_count']}",
            "",
        ]
    )
    if summary["validation_errors"]:
        lines.extend(["## Validation Errors", ""])
        lines.extend(f"- {error}" for error in summary["validation_errors"])
        lines.append("")
    lines.extend(
        [
            "## Generated Tables",
            "",
            "- `row_pattern_outputs/input_inventory.csv`",
            "- `row_pattern_outputs/schema_audit.csv`",
            "- `row_pattern_outputs/row_master_amendment_a.csv`",
            "- `row_pattern_outputs/row_master_amendment_b.csv`",
            "- `row_pattern_outputs/paired_transitions_amendment_a.csv`",
            "- `row_pattern_outputs/paired_transitions_amendment_b.csv`",
            "- `row_pattern_outputs/cluster_tag_summary_amendment_a.csv`",
            "- `row_pattern_outputs/cluster_tag_summary_amendment_b.csv`",
            "- `row_pattern_outputs/representative_examples_amendment_a.csv`",
            "- `row_pattern_outputs/representative_examples_amendment_b.csv`",
            "- `row_pattern_outputs/validation_summary.json`",
            "",
        ]
    )
    return "\n".join(lines)


def run(input_path: Path, output_dir: Path, write: bool) -> dict[str, Any]:
    root = repo_root()
    entries = load_manifest(input_path)
    inventory, schema_audit, rows, errors = inventory_and_rows(entries, root)
    rows = sorted(rows, key=lambda r: (r["analysis_family"], int(r["seed"]), r["eval_set"], r["arm_role"], int(r["row_index"])))
    rows_a = [row for row in rows if row["analysis_family"] == "amendment_a"]
    rows_b = [row for row in rows if row["analysis_family"] == "amendment_b"]
    transitions, transition_errors = paired_transitions(rows)
    errors.extend(transition_errors)
    transitions = sorted(transitions, key=lambda r: (r["analysis_family"], int(r["seed"]), r["eval_set"], r["comparison"], int(r["row_index"])))
    transitions_a = [row for row in transitions if row["analysis_family"] == "amendment_a"]
    transitions_b = [row for row in transitions if row["analysis_family"] == "amendment_b"]
    summary = validation_summary(inventory, schema_audit, rows_a, rows_b, transitions_a, transitions_b, errors)

    if write:
        write_csv(output_dir / "input_inventory.csv", inventory)
        write_csv(output_dir / "schema_audit.csv", schema_audit)
        write_csv(output_dir / "row_master_amendment_a.csv", rows_a, COMMON_COLUMNS)
        write_csv(output_dir / "row_master_amendment_b.csv", rows_b, COMMON_COLUMNS + B_COLUMNS)
        transition_columns = [
            "analysis_family",
            "prompt_contract",
            "evidence_scope",
            "seed",
            "eval_set",
            "row_index",
            "id",
            "label",
            "source",
            "question",
            "comparison",
            "from_arm_role",
            "to_arm_role",
            "from_behavior_state",
            "to_behavior_state",
            "transition",
            "from_refused",
            "to_refused",
            "from_correct",
            "to_correct",
            "from_answer_bin",
            "to_answer_bin",
            "from_stated_confidence",
            "to_stated_confidence",
            "confidence_delta_from_sft_merged",
            "question_tags",
            "cluster_key",
            "from_answer_text",
            "to_answer_text",
        ]
        write_csv(output_dir / "paired_transitions_amendment_a.csv", transitions_a, transition_columns)
        write_csv(output_dir / "paired_transitions_amendment_b.csv", transitions_b, transition_columns)
        write_csv(output_dir / "cluster_tag_summary_amendment_a.csv", cluster_summary(rows_a))
        write_csv(output_dir / "cluster_tag_summary_amendment_b.csv", cluster_summary(rows_b))
        examples = representative_examples(rows, transitions)
        write_csv(output_dir / "representative_examples_amendment_a.csv", [row for row in examples if row["analysis_family"] == "amendment_a"])
        write_csv(output_dir / "representative_examples_amendment_b.csv", [row for row in examples if row["analysis_family"] == "amendment_b"])
        output_dir.mkdir(parents=True, exist_ok=True)
        with (output_dir / "validation_summary.json").open("w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, sort_keys=True)
            f.write("\n")
        report_path = output_dir.parent / "row_pattern_report.md"
        report_path.write_text(report_markdown(summary, rows_a, rows_b, transitions_a, transitions_b), encoding="utf-8")
    return summary


def parse_args() -> argparse.Namespace:
    here = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=here / "row_pattern_inputs.json")
    parser.add_argument("--output-dir", type=Path, default=default_artifact_root() / "row_pattern_outputs")
    parser.add_argument("--write", action="store_true", help="emit CSV/JSON/Markdown outputs")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = run(args.input, args.output_dir, args.write)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
