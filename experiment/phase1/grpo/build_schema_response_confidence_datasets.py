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


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


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


def build_sft_rows(rows: list[dict[str, Any]], *, limit: int | None = None) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows[:limit] if limit else rows:
        messages = row.get("messages") or row.get("conversations")
        if not isinstance(messages, list):
            raise ValueError("SFT row lacks messages/conversations list")
        answer = _assistant_content(messages)
        out.append(
            {
                "messages": [
                    *_without_assistant(messages),
                    {
                        "role": "assistant",
                        "content": _schema_payload(answer, DESIRABLE_CONFIDENCE),
                    },
                ],
                "schema_target": "response_confidence_json",
                "label": NORMAL_SOURCE_LABEL,
                "p_correct": NORMAL_P_CORRECT,
            }
        )
    return out


def build_ambiguous_sft_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    system = {"role": "system", "content": system_prompt_for_confidence_field(CONFIDENCE_FIELD)}
    for row in rows:
        confidence = float(row["p_correct"])
        out.append(
            {
                "messages": [
                    system,
                    {"role": "user", "content": str(row["question"])},
                    {
                        "role": "assistant",
                        "content": _schema_payload(_gold_answer(row), confidence),
                    },
                ],
                "schema_target": "response_confidence_json",
                "label": "ambiguous_middle",
                "p_correct": confidence,
            }
        )
    return out


def _wrap_message_list(messages: list[dict[str, Any]], confidence: float) -> list[dict[str, str]]:
    if not isinstance(messages, list) or not messages:
        raise ValueError("expected non-empty assistant message list")
    answer = _assistant_content(messages)
    return [{"role": "assistant", "content": _schema_payload(answer, confidence)}]


def build_dpo_rows(rows: list[dict[str, Any]], *, limit: int | None = None) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows[:limit] if limit else rows:
        prompt = row.get("prompt")
        if not isinstance(prompt, list):
            raise ValueError("DPO row lacks prompt list")
        out.append(
            {
                "prompt": _replace_system_prompt(prompt),
                "chosen": _wrap_message_list(row.get("chosen"), DESIRABLE_CONFIDENCE),
                "rejected": _wrap_message_list(row.get("rejected"), UNDESIRABLE_CONFIDENCE),
                "schema_target": "response_confidence_json",
                "label": NORMAL_SOURCE_LABEL,
                "p_correct": NORMAL_P_CORRECT,
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
        out.append(
            {
                "prompt": [system, {"role": "user", "content": str(row["question"])}],
                "chosen": [
                    {
                        "role": "assistant",
                        "content": _schema_payload(_gold_answer(row), confidence),
                    }
                ],
                "rejected": [
                    {
                        "role": "assistant",
                        "content": _schema_payload(rejected, DESIRABLE_CONFIDENCE),
                    }
                ],
                "schema_target": "response_confidence_json",
                "label": "ambiguous_middle",
                "p_correct": confidence,
            }
        )
    return out


def build_kto_rows(rows: list[dict[str, Any]], *, limit: int | None = None) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows[:limit] if limit else rows:
        messages = row.get("messages") or row.get("conversations")
        if not isinstance(messages, list):
            raise ValueError("KTO row lacks messages/conversations list")
        confidence = DESIRABLE_CONFIDENCE if bool(row.get("label")) else UNDESIRABLE_CONFIDENCE
        out.append(
            {
                "conversations": [
                    *_without_assistant(messages),
                    {
                        "role": "assistant",
                        "content": _schema_payload(_assistant_content(messages), confidence),
                    },
                ],
                "label": bool(row.get("label")),
                "schema_target": "response_confidence_json",
                "source_label": NORMAL_SOURCE_LABEL,
                "p_correct": NORMAL_P_CORRECT,
            }
        )
    return out


def build_ambiguous_kto_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    system = {"role": "system", "content": system_prompt_for_confidence_field(CONFIDENCE_FIELD)}
    for row in rows:
        confidence = float(row["p_correct"])
        base_messages = [system, {"role": "user", "content": str(row["question"])}]
        out.append(
            {
                "conversations": [
                    *base_messages,
                    {
                        "role": "assistant",
                        "content": _schema_payload(_gold_answer(row), confidence),
                    },
                ],
                "label": True,
                "schema_target": "response_confidence_json",
                "source_label": "ambiguous_middle",
                "p_correct": confidence,
            }
        )
        rejected = _hallucinated_sample(row)
        if rejected is not None:
            out.append(
                {
                    "conversations": [
                        *base_messages,
                        {
                            "role": "assistant",
                            "content": _schema_payload(rejected, DESIRABLE_CONFIDENCE),
                        },
                    ],
                    "label": False,
                    "schema_target": "response_confidence_json",
                    "source_label": "ambiguous_middle",
                    "p_correct": confidence,
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
    include_ambiguous_middle: bool = False,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    sft_rows = build_sft_rows(_read_jsonl(sft_input), limit=limit)
    dpo_rows = build_dpo_rows(_read_jsonl(dpo_input), limit=limit)
    kto_rows = build_kto_rows(_read_jsonl(kto_input), limit=limit)
    ambiguous_rows: list[dict[str, Any]] = []
    if include_ambiguous_middle:
        if probe_results is None:
            raise ValueError("--probe-results is required with --include-ambiguous-middle")
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
        "desirable_response_confidence": DESIRABLE_CONFIDENCE,
        "undesirable_response_confidence": UNDESIRABLE_CONFIDENCE,
        "rows": {"sft": len(sft_rows), "dpo": len(dpo_rows), "kto": len(kto_rows)},
        "ambiguous_middle": {
            "included": include_ambiguous_middle,
            "rows": len(ambiguous_rows),
            "p_correct_min": AMBIGUOUS_MIN,
            "p_correct_max": AMBIGUOUS_MAX,
            "probe_results": str(probe_results) if probe_results else None,
        },
        "inputs": {"sft": str(sft_input), "dpo": str(dpo_input), "kto": str(kto_input)},
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
        include_ambiguous_middle=args.include_ambiguous_middle,
    )
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
