#!/usr/bin/env python3
"""Build schema-aware response-confidence SFT/DPO/KTO datasets.

This projection keeps the original Phase 1 known/unknown preference signal but
wraps assistant completions in:

  {"answer": "<text>", "response_confidence": <0..1>}

The scalar means confidence that the response is appropriate, not confidence in
making a factual assertion. Desirable responses use a non-endpoint high band;
undesirable responses use a non-endpoint low band.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from build_grpo_dataset import system_prompt_for_confidence_field

CONFIDENCE_FIELD = "response_confidence"
DESIRABLE_CONFIDENCE = 0.8
UNDESIRABLE_CONFIDENCE = 0.2
AMBIGUOUS_MIN = 0.4
AMBIGUOUS_MAX = 0.6
NORMAL_SOURCE_LABEL = ""
NORMAL_P_CORRECT = -1.0
UNKNOWN_N_SAMPLES = 0
UNKNOWN_PROBE_KEY = ""
PROBE_SCALED_FORMULA = "0.1 + 0.8 * response_appropriateness_p_laplace"

REFUSAL_PATTERNS = (
    re.compile(r"\bi\s+(?:do\s+not|don't)\s+know\b", re.I),
    re.compile(r"\bi\s+am\s+not\s+sure\b", re.I),
    re.compile(r"\bi'm\s+not\s+sure\b", re.I),
    re.compile(r"\bnot\s+sure\s+what\s+the\s+answer\s+is\b", re.I),
    re.compile(r"\bcan't\s+say\s+for\s+certain\b", re.I),
    re.compile(r"\bcannot\s+say\s+for\s+certain\b", re.I),
    re.compile(r"\bbeyond\s+the\s+scope\s+of\s+my\s+knowledge\b", re.I),
    re.compile(r"\brefrain\s+from\s+guessing\b", re.I),
)


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _norm_question(text: str) -> str:
    return re.sub(r"\s+", " ", str(text).strip().lower())


def _question_from_messages(messages: list[dict[str, Any]]) -> str:
    for message in messages:
        if message.get("role") == "user":
            return str(message.get("content", ""))
    return ""


def _record_key(row: dict[str, Any]) -> str:
    key = row.get("probe_pool_row_key") or row.get("question_id")
    return str(key or "")


def _read_probe_records(path: Path) -> list[dict[str, Any]]:
    return _read_jsonl(path)


def _read_frozen_train_keys(path: Path) -> list[str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    keys = payload.get("train_question_keys")
    if not isinstance(keys, list) or not all(isinstance(key, str) for key in keys):
        raise ValueError(f"{path}: missing train_question_keys list")
    return keys


def _probe_records_for_train_keys(probe_results: Path, questions_frozen: Path) -> list[dict[str, Any]]:
    by_key = {_record_key(row): row for row in _read_probe_records(probe_results)}
    out: list[dict[str, Any]] = []
    missing: list[str] = []
    for key in _read_frozen_train_keys(questions_frozen):
        row = by_key.get(key)
        if row is None:
            missing.append(key)
        else:
            out.append(row)
    if missing:
        raise ValueError(f"{questions_frozen}: {len(missing)} train keys missing from {probe_results}; first={missing[0]!r}")
    return out


def _probe_index_by_norm_question(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Best-effort index for interleaved KTO rows that lost source row keys."""
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(_norm_question(row.get("question", "")), []).append(row)
    index: dict[str, dict[str, Any]] = {}
    for question, candidates in grouped.items():
        if len(candidates) == 1:
            index[question] = candidates[0]
            continue
        # If duplicates are behaviorally equivalent for confidence purposes,
        # they are safe to collapse for this derived target.
        signatures = {
            (str(c.get("label", "")), float(c.get("p_correct", NORMAL_P_CORRECT)), int(c.get("n_samples", 0)))
            for c in candidates
        }
        if len(signatures) == 1:
            index[question] = candidates[0]
    return index


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _schema_payload(answer: str, response_confidence: float) -> str:
    payload = {
        "answer": str(answer or "").strip(),
        CONFIDENCE_FIELD: float(response_confidence),
    }
    return json.dumps(payload, ensure_ascii=False, separators=(",", ": "))


def _is_refusal(text: str) -> bool:
    return any(pattern.search(text or "") for pattern in REFUSAL_PATTERNS)


def _probe_factual_confidence(row: dict[str, Any] | None) -> tuple[float | None, int]:
    if row is None:
        return None, UNKNOWN_N_SAMPLES
    sampled = row.get("sampled_correct")
    if isinstance(sampled, list) and sampled:
        n = len(sampled)
        k = sum(1 for value in sampled if bool(value))
        return (k + 1.0) / (n + 2.0), n
    p_correct = row.get("p_correct")
    n_samples = int(row.get("n_samples") or 0)
    if p_correct is None or n_samples <= 0:
        return None, UNKNOWN_N_SAMPLES
    k = round(float(p_correct) * n_samples)
    return (k + 1.0) / (n_samples + 2.0), n_samples


def _response_confidence_for(answer: str, probe_row: dict[str, Any] | None, *, fallback: float) -> tuple[float, dict[str, Any]]:
    factual_p, n_samples = _probe_factual_confidence(probe_row)
    if factual_p is None:
        return fallback, {
            "response_confidence_source": "constant_fallback",
            "response_confidence_formula": "constant_fallback",
            "probe_pool_row_key": UNKNOWN_PROBE_KEY,
            "source_label": NORMAL_SOURCE_LABEL,
            "p_correct": NORMAL_P_CORRECT,
            "n_samples": UNKNOWN_N_SAMPLES,
        }
    appropriateness_p = 1.0 - factual_p if _is_refusal(answer) else factual_p
    confidence = 0.1 + 0.8 * appropriateness_p
    return round(confidence, 4), {
        "response_confidence_source": "probe_p_correct_32_sample",
        "response_confidence_formula": PROBE_SCALED_FORMULA,
        "probe_pool_row_key": _record_key(probe_row),
        "source_label": str(probe_row.get("label", NORMAL_SOURCE_LABEL)),
        "p_correct": float(probe_row.get("p_correct", NORMAL_P_CORRECT)),
        "n_samples": int(probe_row.get("n_samples", n_samples)),
    }


def _gold_answer(row: dict[str, Any]) -> str:
    value = row.get("answer_value") or row.get("gold_answer")
    if isinstance(value, str) and value.strip():
        return value.strip()
    for alias in row.get("normalized_aliases", []) or row.get("aliases", []):
        if isinstance(alias, str) and alias.strip():
            return alias.strip()
    raise ValueError(f"ambiguous row lacks gold answer/aliases: {row.get('question_id')}")


def _hallucinated_sample(row: dict[str, Any]) -> str | None:
    for answer, correct in zip(row.get("sampled_answers", []), row.get("sampled_correct", [])):
        if correct is False and isinstance(answer, str) and answer.strip():
            return answer.strip()
    return None


def _read_ambiguous_middle_rows(path: Path, *, limit: int | None = None) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    with path.open(encoding="utf-8", newline="") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if str(row.get("label", "")).lower() != "discard":
                continue
            p_correct = row.get("p_correct")
            if p_correct is None:
                continue
            confidence = float(p_correct)
            if AMBIGUOUS_MIN <= confidence <= AMBIGUOUS_MAX:
                selected.append(row)
                if limit is not None and len(selected) >= limit:
                    break
    return selected


def _replace_system_prompt(messages: list[dict[str, Any]]) -> list[dict[str, str]]:
    prompt = system_prompt_for_confidence_field(CONFIDENCE_FIELD)
    out: list[dict[str, str]] = []
    replaced = False
    for message in messages:
        role = str(message.get("role", ""))
        if role == "system":
            out.append({"role": "system", "content": prompt})
            replaced = True
        else:
            out.append({"role": role, "content": str(message.get("content", ""))})
    if not replaced:
        out.insert(0, {"role": "system", "content": prompt})
    return out


def _assistant_content(messages: list[dict[str, Any]]) -> str:
    assistants = [m for m in messages if m.get("role") == "assistant"]
    if not assistants:
        raise ValueError("row lacks assistant message")
    return str(assistants[-1].get("content", "")).strip()


def _without_assistant(messages: list[dict[str, Any]]) -> list[dict[str, str]]:
    return _replace_system_prompt([m for m in messages if m.get("role") != "assistant"])


def build_sft_rows(
    rows: list[dict[str, Any]],
    *,
    limit: int | None = None,
    probe_records: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    selected = rows[:limit] if limit else rows
    selected_probe_records = probe_records[: len(selected)] if probe_records else [None] * len(selected)
    if probe_records is not None and len(probe_records) < len(selected):
        raise ValueError("probe_records must cover every SFT row")
    for row, probe_row in zip(selected, selected_probe_records):
        messages = row.get("messages") or row.get("conversations")
        if not isinstance(messages, list):
            raise ValueError("SFT row lacks messages/conversations list")
        answer = _assistant_content(messages)
        response_confidence, provenance = _response_confidence_for(
            answer,
            probe_row,
            fallback=DESIRABLE_CONFIDENCE,
        )
        out.append(
            {
                "messages": [
                    *_without_assistant(messages),
                    {
                        "role": "assistant",
                        "content": _schema_payload(answer, response_confidence),
                    },
                ],
                "schema_target": "response_confidence_json",
                **provenance,
            }
        )
    return out


def build_ambiguous_sft_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    system = {"role": "system", "content": system_prompt_for_confidence_field(CONFIDENCE_FIELD)}
    for row in rows:
        confidence = float(row["p_correct"])
        response_confidence, provenance = _response_confidence_for(
            _gold_answer(row),
            row,
            fallback=confidence,
        )
        out.append(
            {
                "messages": [
                    system,
                    {"role": "user", "content": str(row["question"])},
                    {
                        "role": "assistant",
                        "content": _schema_payload(_gold_answer(row), response_confidence),
                    },
                ],
                "schema_target": "response_confidence_json",
                **provenance,
            }
        )
    return out


def _wrap_message_list(messages: list[dict[str, Any]], confidence: float) -> list[dict[str, str]]:
    if not isinstance(messages, list) or not messages:
        raise ValueError("expected non-empty assistant message list")
    answer = _assistant_content(messages)
    return [{"role": "assistant", "content": _schema_payload(answer, confidence)}]


def build_dpo_rows(
    rows: list[dict[str, Any]],
    *,
    limit: int | None = None,
    probe_records: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    selected = rows[:limit] if limit else rows
    selected_probe_records = probe_records[: len(selected)] if probe_records else [None] * len(selected)
    if probe_records is not None and len(probe_records) < len(selected):
        raise ValueError("probe_records must cover every DPO row")
    for row, probe_row in zip(selected, selected_probe_records):
        prompt = row.get("prompt")
        if not isinstance(prompt, list):
            raise ValueError("DPO row lacks prompt list")
        chosen_answer = _assistant_content(row.get("chosen"))
        rejected_answer = _assistant_content(row.get("rejected"))
        chosen_confidence, provenance = _response_confidence_for(
            chosen_answer,
            probe_row,
            fallback=DESIRABLE_CONFIDENCE,
        )
        rejected_confidence, _ = _response_confidence_for(
            rejected_answer,
            probe_row,
            fallback=UNDESIRABLE_CONFIDENCE,
        )
        out.append(
            {
                "prompt": _replace_system_prompt(prompt),
                "chosen": _wrap_message_list(row.get("chosen"), chosen_confidence),
                "rejected": _wrap_message_list(row.get("rejected"), rejected_confidence),
                "schema_target": "response_confidence_json",
                **provenance,
            }
        )
    return out


def build_ambiguous_dpo_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    system = {"role": "system", "content": system_prompt_for_confidence_field(CONFIDENCE_FIELD)}
    for row in rows:
        rejected = _hallucinated_sample(row)
        if rejected is None:
            continue
        confidence = float(row["p_correct"])
        chosen_confidence, provenance = _response_confidence_for(_gold_answer(row), row, fallback=confidence)
        rejected_answer = rejected
        rejected_confidence, _ = _response_confidence_for(rejected_answer, row, fallback=DESIRABLE_CONFIDENCE)
        out.append(
            {
                "prompt": [system, {"role": "user", "content": str(row["question"])}],
                "chosen": [
                    {
                        "role": "assistant",
                        "content": _schema_payload(_gold_answer(row), chosen_confidence),
                    }
                ],
                "rejected": [
                    {
                        "role": "assistant",
                        "content": _schema_payload(rejected, rejected_confidence),
                    }
                ],
                "schema_target": "response_confidence_json",
                **provenance,
            }
        )
    return out


def build_kto_rows(
    rows: list[dict[str, Any]],
    *,
    limit: int | None = None,
    probe_index_by_norm_question: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows[:limit] if limit else rows:
        messages = row.get("messages") or row.get("conversations")
        if not isinstance(messages, list):
            raise ValueError("KTO row lacks messages/conversations list")
        probe_row = None
        if probe_index_by_norm_question:
            probe_row = probe_index_by_norm_question.get(_norm_question(_question_from_messages(messages)))
        answer = _assistant_content(messages)
        confidence, provenance = _response_confidence_for(
            answer,
            probe_row,
            fallback=DESIRABLE_CONFIDENCE if bool(row.get("label")) else UNDESIRABLE_CONFIDENCE,
        )
        out.append(
            {
                "conversations": [
                    *_without_assistant(messages),
                    {
                        "role": "assistant",
                        "content": _schema_payload(answer, confidence),
                    },
                ],
                "label": bool(row.get("label")),
                "schema_target": "response_confidence_json",
                **provenance,
            }
        )
    return out


def build_ambiguous_kto_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    system = {"role": "system", "content": system_prompt_for_confidence_field(CONFIDENCE_FIELD)}
    for row in rows:
        confidence = float(row["p_correct"])
        base_messages = [system, {"role": "user", "content": str(row["question"])}]
        chosen_confidence, provenance = _response_confidence_for(_gold_answer(row), row, fallback=confidence)
        out.append(
            {
                "conversations": [
                    *base_messages,
                    {
                        "role": "assistant",
                        "content": _schema_payload(_gold_answer(row), chosen_confidence),
                    },
                ],
                "label": True,
                "schema_target": "response_confidence_json",
                **provenance,
            }
        )
        rejected = _hallucinated_sample(row)
        if rejected is not None:
            rejected_confidence, _ = _response_confidence_for(rejected, row, fallback=DESIRABLE_CONFIDENCE)
            out.append(
                {
                    "conversations": [
                        *base_messages,
                        {
                            "role": "assistant",
                            "content": _schema_payload(rejected, rejected_confidence),
                        },
                    ],
                    "label": False,
                    "schema_target": "response_confidence_json",
                    **provenance,
                }
            )
    return out


def build_all(
    *,
    sft_input: Path,
    dpo_input: Path,
    kto_input: Path,
    output_dir: Path,
    limit: int | None = None,
    probe_results: Path | None = None,
    questions_frozen: Path | None = None,
    include_ambiguous_middle: bool = False,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    if probe_results is None:
        raise ValueError("--probe-results is required for probe-scaled response-confidence targets")
    if questions_frozen is None:
        questions_frozen = sft_input.parent / "questions_frozen.json"
    train_probe_records = _probe_records_for_train_keys(probe_results, questions_frozen)
    if limit is not None:
        train_probe_records = train_probe_records[:limit]
    probe_index = _probe_index_by_norm_question(train_probe_records)
    sft_rows = build_sft_rows(_read_jsonl(sft_input), limit=limit, probe_records=train_probe_records)
    dpo_rows = build_dpo_rows(_read_jsonl(dpo_input), limit=limit, probe_records=train_probe_records)
    kto_rows = build_kto_rows(_read_jsonl(kto_input), limit=limit, probe_index_by_norm_question=probe_index)
    ambiguous_rows: list[dict[str, Any]] = []
    if include_ambiguous_middle:
        ambiguous_rows = _read_ambiguous_middle_rows(probe_results, limit=limit)
        sft_rows.extend(build_ambiguous_sft_rows(ambiguous_rows))
        dpo_rows.extend(build_ambiguous_dpo_rows(ambiguous_rows))
        kto_rows.extend(build_ambiguous_kto_rows(ambiguous_rows))

    outputs = {
        "sft": output_dir / "sft_response_confidence_train.jsonl",
        "dpo": output_dir / "dpo_response_confidence_train.jsonl",
        "kto": output_dir / "kto_response_confidence_train.jsonl",
    }
    _write_jsonl(outputs["sft"], sft_rows)
    _write_jsonl(outputs["dpo"], dpo_rows)
    _write_jsonl(outputs["kto"], kto_rows)
    manifest = {
        "component": "schema response-confidence dataset projection",
        "status": "not part of locked Phase 1 v0.3 matrix",
        "confidence_field": CONFIDENCE_FIELD,
        "response_confidence_targeting": {
            "source": "probe p_correct from 32 stochastic samples",
            "formula": PROBE_SCALED_FORMULA,
            "fallback_desirable_response_confidence": DESIRABLE_CONFIDENCE,
            "fallback_undesirable_response_confidence": UNDESIRABLE_CONFIDENCE,
            "laplace_smoothing": "(correct_samples + 1) / (n_samples + 2)",
            "answer_target": "response_appropriateness_p = factual_p",
            "abstention_target": "response_appropriateness_p = 1 - factual_p",
        },
        "rows": {"sft": len(sft_rows), "dpo": len(dpo_rows), "kto": len(kto_rows)},
        "ambiguous_middle": {
            "included": include_ambiguous_middle,
            "rows": len(ambiguous_rows),
            "p_correct_min": AMBIGUOUS_MIN,
            "p_correct_max": AMBIGUOUS_MAX,
            "probe_results": str(probe_results) if probe_results else None,
        },
        "inputs": {
            "sft": str(sft_input),
            "dpo": str(dpo_input),
            "kto": str(kto_input),
            "probe_results": str(probe_results),
            "questions_frozen": str(questions_frozen),
        },
        "outputs": {key: str(path) for key, path in outputs.items()},
    }
    (output_dir / "response_confidence_schema_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sft-input", type=Path, default=Path("experiment/phase1/data/qwen3-4b-instruct/sft_train.jsonl"))
    parser.add_argument("--dpo-input", type=Path, default=Path("experiment/phase1/data/qwen3-4b-instruct/dpo_train.jsonl"))
    parser.add_argument("--kto-input", type=Path, default=Path("experiment/phase1/data/qwen3-4b-instruct/kto_congruence_train.jsonl"))
    parser.add_argument("--output-dir", type=Path, default=Path("scratch/schema_response_confidence/qwen3-4b-instruct"))
    parser.add_argument("--probe-results", type=Path, default=Path("experiment/phase1/probe/qwen3-4b-instruct/probe_results.jsonl"))
    parser.add_argument("--questions-frozen", type=Path, default=Path("experiment/phase1/data/qwen3-4b-instruct/questions_frozen.json"))
    parser.add_argument("--include-ambiguous-middle", action="store_true")
    parser.add_argument("--limit", type=int, help="Optional first-N row limit per dataset.")
    args = parser.parse_args(argv)
    manifest = build_all(
        sft_input=args.sft_input,
        dpo_input=args.dpo_input,
        kto_input=args.kto_input,
        output_dir=args.output_dir,
        limit=args.limit,
        probe_results=args.probe_results,
        questions_frozen=args.questions_frozen,
        include_ambiguous_middle=args.include_ambiguous_middle,
    )
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
