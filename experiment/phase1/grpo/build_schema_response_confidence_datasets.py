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
import hashlib
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
CONTRASTIVE_FORMULA = "deterministic_uait_style_band_spread_v1"
SFT_CLEAN_FORMULA = "deterministic_clean_sft_band_spread_v1"
# Amendment M (probe-distilled calibration SFT): the response_confidence target is
# the empirical quantile of each row's internal appropriateness_p, mapped onto a
# spread band. This is per-question grounded (monotone in appropriateness_p) AND
# distribution-balanced (the marginal is ~uniform across the band), which defeats
# the naive probe-scaled mode-collapse (computed-confidence-alignment-regimen §004:
# 0.1+0.8*p emitted a constant 0.8765 because the target distribution is mode-heavy).
#
# NOTE (implementation refinement of Amendment M §3.1): the signed spec wrote
# "average-rank for ties". But appropriateness_p is a 32-sample Laplace value with
# only ~34 discrete levels, so it has large tie-clusters (a point mass of easy
# knowns near the top). Average-rank maps a whole tie-cluster to ONE target, which
# would merely RELOCATE the §004 point mass and fail the spec's own balance gate
# (no quantized target > 15% of rows). We therefore break ties with a deterministic
# secondary key (a stable hash of the probe row key + answer) so each row gets a
# distinct rank and the marginal is genuinely spread. This stays "deterministic
# given a fixed sort key" (§3.1) and is what the balance requirement actually needs;
# strict monotonicity (appropriateness_p_i < appropriateness_p_j => conf_i <= conf_j)
# is preserved because tied rows occupy a contiguous rank block between neighbours.
PROBE_DISTILLED_QUANTILE_FORMULA = "quantile_balanced(appropriateness_p_laplace, ties=deterministic_key) -> band"
PROBE_DISTILLED_BAND = (0.10, 0.90)
PROBE_DISTILLED_BALANCE_CAP = 0.15  # no single quantized target may exceed 15% of rows

# Amendment M Revision 3 (SIGNED 2026-06-29): the R1/R2 quantile-balanced
# appropriateness_p target above is RETIRED. Its CPU preflight (commit d8414971)
# showed appropriateness_p is near-constant on clean-SFT data (only 17 distinct
# values, 85% of rows at the 0.9706 ceiling, because every clean completion is
# "appropriate"), so quantile-balancing scattered genuinely-equivalent rows across
# the band by a hash tie-break — manufacturing knowledge-uncorrelated confidence for
# 85% of the data. R3 retargets onto the calibrated factual/doubt axis DIRECTLY:
# response_confidence = factual_p (the Laplace 32-sample P-correct), with NO balancing
# and NO abstention inversion. factual_p is already a calibrated probability and is
# genuinely bimodal-with-tail (abstentions low ~0.03; answers split high/low with a
# real 0.5-0.9 tail), so the mean-emitting §004 collapse is strongly penalized AND the
# target stays calibrated. A light clamp keeps JSON/logit targets off the hard 0/1
# endpoints (the data lies inside it, so the clamp is effectively inert). The scalar
# now means P(the asserted answer is factually correct): high on knowns-it-gets-right,
# low on abstentions and questions-it-gets-wrong — the polarity the threshold bridge
# (Amendment M §3.4) needs.
PROBE_FACTUAL_FORMULA = "factual_p_laplace (direct, no balancing, no abstention inversion) -> clamp[0.02,0.98]"
PROBE_FACTUAL_CLAMP = (0.02, 0.98)
CONTRASTIVE_LOW_BAND = (0.10, 0.35)
CONTRASTIVE_MIDDLE_BAND = (0.35, 0.60)
CONTRASTIVE_HIGH_BAND = (0.70, 0.90)

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


def _answer_value_render(answer: str) -> str:
    """The answer value exactly as it is rendered inside the schema JSON.

    `_schema_payload` json-dumps the stripped answer, so the value's on-the-wire
    form is the escaped string content WITHOUT its surrounding quotes. This is the
    literal sub-span the SFT engine masks out of the loss (Amendment L), so it
    must match the rendered text byte-for-byte.
    """
    value = str(answer or "").strip()
    if not value:
        return ""
    return json.dumps(value, ensure_ascii=False)[1:-1]


def _stable_unit_interval(*parts: object) -> float:
    text = "\x1f".join(str(part) for part in parts)
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") / float(2**64 - 1)


def _spread_in_band(band: tuple[float, float], *parts: object) -> float:
    low, high = band
    return round(low + (high - low) * _stable_unit_interval(*parts), 4)


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


def _contrastive_response_confidence_for(
    answer: str,
    probe_row: dict[str, Any] | None,
    *,
    role: str,
) -> tuple[float, dict[str, Any]]:
    if role == "appropriate":
        band = CONTRASTIVE_HIGH_BAND
    elif role == "inappropriate":
        band = CONTRASTIVE_LOW_BAND
    elif role == "ambiguous_answer":
        band = CONTRASTIVE_MIDDLE_BAND
    else:
        raise ValueError(f"unknown contrastive role: {role}")
    key = _record_key(probe_row or {})
    confidence = _spread_in_band(band, role, key, answer)
    factual_p, n_samples = _probe_factual_confidence(probe_row)
    return confidence, {
        "response_confidence_source": "contrastive_uait_style_target_shaping",
        "response_confidence_formula": CONTRASTIVE_FORMULA,
        "response_confidence_role": role,
        "probe_pool_row_key": key,
        "source_label": str((probe_row or {}).get("label", NORMAL_SOURCE_LABEL)),
        "p_correct": float((probe_row or {}).get("p_correct", factual_p if factual_p is not None else NORMAL_P_CORRECT)),
        "n_samples": int((probe_row or {}).get("n_samples", n_samples)),
    }


def _clean_sft_response_confidence_for(
    answer: str,
    probe_row: dict[str, Any] | None,
    *,
    role: str,
) -> tuple[float, dict[str, Any]]:
    if role == "appropriate":
        band = CONTRASTIVE_HIGH_BAND
    elif role == "ambiguous_answer":
        band = CONTRASTIVE_MIDDLE_BAND
    else:
        raise ValueError(f"unknown clean SFT role: {role}")
    key = _record_key(probe_row or {})
    confidence = _spread_in_band(band, role, key, answer, "clean_sft")
    factual_p, n_samples = _probe_factual_confidence(probe_row)
    return confidence, {
        "response_confidence_source": "clean_sft_appropriate_response_target_shaping",
        "response_confidence_formula": SFT_CLEAN_FORMULA,
        "response_confidence_role": role,
        "probe_pool_row_key": key,
        "source_label": str((probe_row or {}).get("label", NORMAL_SOURCE_LABEL)),
        "p_correct": float((probe_row or {}).get("p_correct", factual_p if factual_p is not None else NORMAL_P_CORRECT)),
        "n_samples": int((probe_row or {}).get("n_samples", n_samples)),
    }


def _appropriateness_p(answer: str, probe_row: dict[str, Any] | None) -> tuple[float | None, int]:
    """Internal appropriateness probability for a (clean) completion.

    answer rows: appropriateness_p = factual_p; refusal rows: 1 - factual_p. Mirrors
    the probe-scaled path exactly (line ~197) but returns the raw probability for the
    quantile transform instead of mapping it through 0.1+0.8*p. None if the probe row
    carries no usable signal.
    """
    factual_p, n_samples = _probe_factual_confidence(probe_row)
    if factual_p is None:
        return None, n_samples
    appropriateness_p = 1.0 - factual_p if _is_refusal(answer) else factual_p
    return appropriateness_p, n_samples


def _quantile_balanced_targets(
    values: list[float | None],
    tiebreaks: list[float],
    band: tuple[float, float],
) -> list[float]:
    """Map each value to lo + (hi-lo) * rank/(N+1), ranks DISTINCT (ties broken by
    `tiebreaks`), so the emitted marginal is ~uniform across the band.

    Rows with value None (no probe signal) are excluded from the ranking and assigned
    the band midpoint (deterministic, flagged in provenance by the caller). Ranking is
    over the valid rows only, by (value, tiebreak, original_index) so it is fully
    deterministic. Strict monotonicity in `value` holds: a row with a smaller value
    cannot receive a larger target, because all rows sort primarily by value.
    """
    lo, hi = band
    midpoint = round(lo + (hi - lo) * 0.5, 4)
    valid_idx = [i for i, v in enumerate(values) if v is not None]
    targets = [midpoint] * len(values)
    n_valid = len(valid_idx)
    if n_valid == 0:
        return targets
    order = sorted(valid_idx, key=lambda i: (values[i], tiebreaks[i], i))
    for rank0, i in enumerate(order):
        q = (rank0 + 1) / (n_valid + 1)  # 1-based rank in (0, 1), endpoints avoided
        targets[i] = round(lo + (hi - lo) * q, 4)
    return targets


def build_probe_distilled_sft_rows(
    rows: list[dict[str, Any]],
    *,
    limit: int | None = None,
    probe_records: list[dict[str, Any]] | None = None,
    band: tuple[float, float] = PROBE_DISTILLED_BAND,
) -> list[dict[str, Any]]:
    """Amendment M: clean-SFT behavior completions whose response_confidence is the
    quantile-balanced transform of the internal appropriateness_p.

    Behavior-identical to build_clean_sft_rows by construction: same input rows, same
    answer text (`_assistant_content`), same prompt (`_without_assistant`); ONLY the
    response_confidence scalar differs. Needs a global pass (the quantile is a rank
    over all rows), so it builds in two passes.
    """
    selected = rows[:limit] if limit else rows
    selected_probe_records = probe_records[: len(selected)] if probe_records else [None] * len(selected)
    if probe_records is not None and len(probe_records) < len(selected):
        raise ValueError("probe_records must cover every probe-distilled SFT row")

    # Pass 1: answers, appropriateness_p, deterministic tiebreak.
    staged: list[tuple[list[dict[str, Any]], str, dict[str, Any] | None, int]] = []
    appropriateness: list[float | None] = []
    tiebreaks: list[float] = []
    for row, probe_row in zip(selected, selected_probe_records):
        messages = row.get("messages") or row.get("conversations")
        if not isinstance(messages, list):
            raise ValueError("SFT row lacks messages/conversations list")
        answer = _assistant_content(messages)
        ap, n_samples = _appropriateness_p(answer, probe_row)
        key = _record_key(probe_row or {})
        staged.append((messages, answer, probe_row, n_samples))
        appropriateness.append(ap)
        tiebreaks.append(_stable_unit_interval("probe_distilled", key, answer))

    targets = _quantile_balanced_targets(appropriateness, tiebreaks, band)

    # Pass 2: build rows (answer text identical to clean SFT; only confidence differs).
    out: list[dict[str, Any]] = []
    for (messages, answer, probe_row, n_samples), ap, target in zip(staged, appropriateness, targets):
        provenance = {
            "response_confidence_source": (
                "probe_distilled_quantile_balanced" if ap is not None else "constant_fallback"
            ),
            "response_confidence_formula": (
                PROBE_DISTILLED_QUANTILE_FORMULA if ap is not None else "constant_fallback"
            ),
            "response_confidence_role": "appropriate",
            "appropriateness_p": (round(ap, 6) if ap is not None else None),
            "probe_pool_row_key": _record_key(probe_row or {}),
            "source_label": str((probe_row or {}).get("label", NORMAL_SOURCE_LABEL)),
            "p_correct": float((probe_row or {}).get("p_correct", NORMAL_P_CORRECT)),
            "n_samples": int((probe_row or {}).get("n_samples", n_samples)),
        }
        out.append(
            {
                "messages": [
                    *_without_assistant(messages),
                    {
                        "role": "assistant",
                        "content": _schema_payload(answer, target),
                    },
                ],
                "schema_target": "response_confidence_json",
                **provenance,
            }
        )
    return out


def build_probe_factual_sft_rows(
    rows: list[dict[str, Any]],
    *,
    limit: int | None = None,
    probe_records: list[dict[str, Any]] | None = None,
    clamp: tuple[float, float] = PROBE_FACTUAL_CLAMP,
) -> list[dict[str, Any]]:
    """Amendment M Revision 3: clean-SFT behavior completions whose response_confidence
    is the model's own calibrated factual confidence (probe `factual_p`), applied
    DIRECTLY — no quantile transform, no balancing, no abstention inversion.

    Behavior-identical to build_clean_sft_rows by construction: same input rows, same
    answer text (`_assistant_content`), same prompt (`_without_assistant`); ONLY the
    response_confidence scalar differs. The scalar means P(the asserted answer is
    factually correct): high on knowns the model gets right, LOW on abstentions and on
    questions it gets wrong (this is the opposite polarity to R1/R2 "appropriateness"
    for abstentions, and is the polarity the threshold bridge needs). Missing-probe
    rows fall back to the global mean `factual_p` (constant), flagged in provenance.
    """
    selected = rows[:limit] if limit else rows
    selected_probe_records = probe_records[: len(selected)] if probe_records else [None] * len(selected)
    if probe_records is not None and len(probe_records) < len(selected):
        raise ValueError("probe_records must cover every probe-factual SFT row")

    lo, hi = clamp
    # Pass 1: answers + raw factual_p (NO inversion). Compute the global mean over the
    # rows that DO carry a probe signal, for the missing-probe fallback.
    staged: list[tuple[list[dict[str, Any]], str, dict[str, Any] | None, int]] = []
    factual: list[float | None] = []
    for row, probe_row in zip(selected, selected_probe_records):
        messages = row.get("messages") or row.get("conversations")
        if not isinstance(messages, list):
            raise ValueError("SFT row lacks messages/conversations list")
        answer = _assistant_content(messages)
        fp, n_samples = _probe_factual_confidence(probe_row)
        staged.append((messages, answer, probe_row, n_samples))
        factual.append(fp)
    valid = [fp for fp in factual if fp is not None]
    fallback_mean = round(sum(valid) / len(valid), 6) if valid else round((lo + hi) / 2.0, 6)

    # Pass 2: build rows (answer text identical to clean SFT; only confidence differs).
    out: list[dict[str, Any]] = []
    for (messages, answer, probe_row, n_samples), fp in zip(staged, factual):
        if fp is None:
            target = round(min(hi, max(lo, fallback_mean)), 4)
            source, formula = "constant_fallback", "constant_fallback"
        else:
            target = round(min(hi, max(lo, fp)), 4)
            source, formula = "probe_factual_direct", PROBE_FACTUAL_FORMULA
        provenance = {
            "response_confidence_source": source,
            "response_confidence_formula": formula,
            "response_confidence_role": "factual",
            "factual_p": (round(fp, 6) if fp is not None else None),
            "probe_pool_row_key": _record_key(probe_row or {}),
            "source_label": str((probe_row or {}).get("label", NORMAL_SOURCE_LABEL)),
            "p_correct": float((probe_row or {}).get("p_correct", NORMAL_P_CORRECT)),
            "n_samples": int((probe_row or {}).get("n_samples", n_samples)),
        }
        out.append(
            {
                "messages": [
                    *_without_assistant(messages),
                    {"role": "assistant", "content": _schema_payload(answer, target)},
                ],
                "schema_target": "response_confidence_json",
                **provenance,
            }
        )
    return out


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


def build_clean_sft_rows(
    rows: list[dict[str, Any]],
    *,
    limit: int | None = None,
    probe_records: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Build SFT rows with only appropriate completions and spread targets."""
    out: list[dict[str, Any]] = []
    selected = rows[:limit] if limit else rows
    selected_probe_records = probe_records[: len(selected)] if probe_records else [None] * len(selected)
    if probe_records is not None and len(probe_records) < len(selected):
        raise ValueError("probe_records must cover every clean SFT row")
    for row, probe_row in zip(selected, selected_probe_records):
        messages = row.get("messages") or row.get("conversations")
        if not isinstance(messages, list):
            raise ValueError("SFT row lacks messages/conversations list")
        answer = _assistant_content(messages)
        response_confidence, provenance = _clean_sft_response_confidence_for(
            answer,
            probe_row,
            role="appropriate",
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


def build_clean_ambiguous_sft_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    system = {"role": "system", "content": system_prompt_for_confidence_field(CONFIDENCE_FIELD)}
    for row in rows:
        answer = _gold_answer(row)
        response_confidence, provenance = _clean_sft_response_confidence_for(
            answer,
            row,
            role="ambiguous_answer",
        )
        out.append(
            {
                "messages": [
                    system,
                    {"role": "user", "content": str(row["question"])},
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


def build_contrastive_sft_rows(
    rows: list[dict[str, Any]],
    *,
    limit: int | None = None,
    probe_records: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    selected = rows[:limit] if limit else rows
    selected_probe_records = probe_records[: len(selected)] if probe_records else [None] * len(selected)
    if probe_records is not None and len(probe_records) < len(selected):
        raise ValueError("probe_records must cover every contrastive SFT row")
    for row, probe_row in zip(selected, selected_probe_records):
        prompt = row.get("prompt")
        if not isinstance(prompt, list):
            raise ValueError("DPO row lacks prompt list")
        prompt_messages = _replace_system_prompt(prompt)
        for field, role in (("chosen", "appropriate"), ("rejected", "inappropriate")):
            messages = row.get(field)
            answer = _assistant_content(messages)
            response_confidence, provenance = _contrastive_response_confidence_for(
                answer,
                probe_row,
                role=role,
            )
            built = {
                "messages": [
                    *prompt_messages,
                    {
                        "role": "assistant",
                        "content": _schema_payload(answer, response_confidence),
                    },
                ],
                "schema_target": "response_confidence_json",
                **provenance,
            }
            # Amendment L: on inappropriate rows, exclude the wrong-answer value
            # from the SFT loss (engine honors the generic loss_mask_text column)
            # so only the low response_confidence is supervised, not the wrong
            # answer text. Appropriate/ambiguous answers stay fully supervised.
            if role == "inappropriate":
                span = _answer_value_render(answer)
                if span:
                    built["loss_mask_text"] = [span]
            out.append(built)
    return out


def build_contrastive_ambiguous_sft_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    system = {"role": "system", "content": system_prompt_for_confidence_field(CONFIDENCE_FIELD)}
    for row in rows:
        answer = _gold_answer(row)
        response_confidence, provenance = _contrastive_response_confidence_for(
            answer,
            row,
            role="ambiguous_answer",
        )
        out.append(
            {
                "messages": [
                    system,
                    {"role": "user", "content": str(row["question"])},
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
    sft_clean_rows = build_clean_sft_rows(_read_jsonl(sft_input), limit=limit, probe_records=train_probe_records)
    sft_probe_distilled_rows = build_probe_distilled_sft_rows(
        _read_jsonl(sft_input), limit=limit, probe_records=train_probe_records
    )
    # Amendment M Revision 3: the authorized cell (factual_p direct). Mirrors the
    # probe-distilled scope (sft_input rows only; no ambiguous-middle append).
    sft_probe_factual_rows = build_probe_factual_sft_rows(
        _read_jsonl(sft_input), limit=limit, probe_records=train_probe_records
    )
    dpo_source_rows = _read_jsonl(dpo_input)
    sft_contrastive_rows = build_contrastive_sft_rows(
        dpo_source_rows,
        limit=limit,
        probe_records=train_probe_records,
    )
    dpo_rows = build_dpo_rows(dpo_source_rows, limit=limit, probe_records=train_probe_records)
    kto_rows = build_kto_rows(_read_jsonl(kto_input), limit=limit, probe_index_by_norm_question=probe_index)
    ambiguous_rows: list[dict[str, Any]] = []
    if include_ambiguous_middle:
        ambiguous_rows = _read_ambiguous_middle_rows(probe_results, limit=limit)
        sft_rows.extend(build_ambiguous_sft_rows(ambiguous_rows))
        sft_clean_rows.extend(build_clean_ambiguous_sft_rows(ambiguous_rows))
        sft_contrastive_rows.extend(build_contrastive_ambiguous_sft_rows(ambiguous_rows))
        dpo_rows.extend(build_ambiguous_dpo_rows(ambiguous_rows))
        kto_rows.extend(build_ambiguous_kto_rows(ambiguous_rows))

    outputs = {
        "sft": output_dir / "sft_response_confidence_train.jsonl",
        "sft_clean": output_dir / "sft_response_confidence_train_clean.jsonl",
        "sft_probe_distilled": output_dir / "sft_response_confidence_train_probe_distilled.jsonl",
        "sft_probe_factual": output_dir / "sft_response_confidence_train_probe_factual.jsonl",
        "sft_contrastive": output_dir / "sft_response_confidence_train_contrastive.jsonl",
        "sft_contrastive_masked": output_dir / "sft_response_confidence_train_contrastive_masked.jsonl",
        "dpo": output_dir / "dpo_response_confidence_train.jsonl",
        "kto": output_dir / "kto_response_confidence_train.jsonl",
    }
    _write_jsonl(outputs["sft"], sft_rows)
    _write_jsonl(outputs["sft_clean"], sft_clean_rows)
    _write_jsonl(outputs["sft_probe_distilled"], sft_probe_distilled_rows)
    _write_jsonl(outputs["sft_probe_factual"], sft_probe_factual_rows)
    # The Amendment K contrastive file stays byte-identical (no loss_mask_text
    # column); the Amendment L masked file is the same rows PLUS the additive
    # loss_mask_text directive on inappropriate rows.
    _write_jsonl(
        outputs["sft_contrastive"],
        [{k: v for k, v in r.items() if k != "loss_mask_text"} for r in sft_contrastive_rows],
    )
    _write_jsonl(outputs["sft_contrastive_masked"], sft_contrastive_rows)
    _write_jsonl(outputs["dpo"], dpo_rows)
    _write_jsonl(outputs["kto"], kto_rows)
    # Probe-distilled balance stat (Amendment M §4 preflight): the largest share any
    # single quantized target takes. §004's collapse was 81.79%; the gate is <= 15%.
    pd_targets = [
        json.loads(r["messages"][-1]["content"]).get(CONFIDENCE_FIELD)
        for r in sft_probe_distilled_rows
    ]
    pd_counts: dict[float, int] = {}
    for t in pd_targets:
        pd_counts[t] = pd_counts.get(t, 0) + 1
    pd_max_share = (max(pd_counts.values()) / len(pd_targets)) if pd_targets else 0.0
    pd_fallback = sum(
        1 for r in sft_probe_distilled_rows
        if r.get("response_confidence_source") == "constant_fallback"
    )
    # Amendment M R3 preflight (§4 step 2): the factual_p target is BIMODAL-with-tail,
    # NOT balanced. Report both mode masses, the populated middle, and the
    # answer/abstention split per band; the uniform-balance gate is RETIRED.
    pf_targets = [
        json.loads(r["messages"][-1]["content"]).get(CONFIDENCE_FIELD)
        for r in sft_probe_factual_rows
    ]
    pf_counts: dict[float, int] = {}
    for t in pf_targets:
        pf_counts[t] = pf_counts.get(t, 0) + 1
    pf_n = len(pf_targets) or 1
    pf_low = sum(1 for t in pf_targets if t <= 0.2) / pf_n
    pf_mid = sum(1 for t in pf_targets if 0.2 < t < 0.8) / pf_n
    pf_high = sum(1 for t in pf_targets if t >= 0.8) / pf_n
    pf_max_share = (max(pf_counts.values()) / pf_n) if pf_targets else 0.0
    pf_fallback = sum(
        1 for r in sft_probe_factual_rows
        if r.get("response_confidence_source") == "constant_fallback"
    )
    def _pf_payload(r: dict[str, Any]) -> dict[str, Any]:
        return json.loads(r["messages"][-1]["content"])
    pf_abst_low = sum(
        1 for r in sft_probe_factual_rows
        if _is_refusal(_pf_payload(r).get("answer", ""))
        and _pf_payload(r).get(CONFIDENCE_FIELD) <= 0.2
    )
    pf_abst_total = sum(
        1 for r in sft_probe_factual_rows if _is_refusal(_pf_payload(r).get("answer", ""))
    )

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
        "contrastive_sft": {
            "included": True,
            "rows": len(sft_contrastive_rows),
            "source": "DPO chosen/rejected pairs plus optional ambiguous middle answer rows",
            "formula": CONTRASTIVE_FORMULA,
            "bands": {
                "appropriate": CONTRASTIVE_HIGH_BAND,
                "inappropriate": CONTRASTIVE_LOW_BAND,
                "ambiguous_answer": CONTRASTIVE_MIDDLE_BAND,
            },
            "semantics": {
                "unknown_abstention": "high confidence because abstention is appropriate",
                "known_over_refusal": "low confidence because abstention is inappropriate",
                "ambiguous_answer": "answer remains supervised, with middle confidence",
            },
            "loss_subspan_masking": {
                "amendment": "L",
                "masked_file": "sft_response_confidence_train_contrastive_masked.jsonl",
                "unmasked_file": "sft_response_confidence_train_contrastive.jsonl",
                "rule": "inappropriate rows carry loss_mask_text=[answer value] so the wrong-answer text is excluded from the SFT loss; response_confidence stays supervised. Appropriate/ambiguous answers fully supervised.",
                "engine": "synaptic-tuner materialize_sft_example loss_mask_spans (generic per-row sub-span masking)",
            },
        },
        "clean_sft": {
            "included": True,
            "rows": len(sft_clean_rows),
            "source": "Original SFT appropriate completions plus optional ambiguous middle answer rows",
            "formula": SFT_CLEAN_FORMULA,
            "bands": {
                "appropriate": CONTRASTIVE_HIGH_BAND,
                "ambiguous_answer": CONTRASTIVE_MIDDLE_BAND,
            },
            "semantics": {
                "known_answer": "high confidence because the factual answer is appropriate",
                "unknown_abstention": "high confidence because abstention is appropriate",
                "ambiguous_answer": "answer remains supervised, with middle confidence",
                "excluded": "wrong answers and over-refusals are excluded from clean SFT and reserved for DPO/KTO/GRPO",
            },
        },
        "probe_distilled_sft": {
            "included": True,
            "amendment": "M (revision 2)",
            "rows": len(sft_probe_distilled_rows),
            "source": "Same clean-SFT appropriate completions; ONLY response_confidence differs",
            "formula": PROBE_DISTILLED_QUANTILE_FORMULA,
            "band": list(PROBE_DISTILLED_BAND),
            "quantile": "global; q_i = rank_i/(N+1); ranks distinct, ties broken by stable hash(key, answer)",
            "balance": {
                "max_target_share": round(pd_max_share, 4),
                "cap": PROBE_DISTILLED_BALANCE_CAP,
                "passes_cap": pd_max_share <= PROBE_DISTILLED_BALANCE_CAP,
                "distinct_targets": len(pd_counts),
                "naive_004_collapse_share_for_reference": 0.8179,
                "constant_fallback_rows": pd_fallback,
            },
            "semantics": {
                "target": "monotone quantile transform of internal appropriateness_p",
                "behavior": "identical to clean SFT by construction (answer text byte-identical)",
                "goal": "install stated-confidence DISCRIMINATION while preserving behavior",
            },
            "status": "RETIRED by R3 (near-degenerate source); kept for provenance",
        },
        "probe_factual_sft": {
            "included": True,
            "amendment": "M (revision 3, SIGNED 2026-06-29)",
            "rows": len(sft_probe_factual_rows),
            "source": "Same clean-SFT appropriate completions; ONLY response_confidence differs",
            "formula": PROBE_FACTUAL_FORMULA,
            "clamp": list(PROBE_FACTUAL_CLAMP),
            "target": "factual_p (Laplace 32-sample P-correct) DIRECT; no balancing, no abstention inversion",
            "distribution": {
                "shape": "bimodal-with-tail (NOT balanced; uniform-balance gate retired)",
                "low_mode_mass_le_0p2": round(pf_low, 4),
                "mid_mass_0p2_0p8": round(pf_mid, 4),
                "high_mode_mass_ge_0p8": round(pf_high, 4),
                "max_target_share": round(pf_max_share, 4),
                "distinct_targets": len(pf_counts),
                "constant_fallback_rows": pf_fallback,
                "abstentions_at_low_mode": f"{pf_abst_low}/{pf_abst_total}",
            },
            "semantics": {
                "target": "model's own calibrated factual confidence P(answer correct)",
                "polarity": "high on knowns-it-gets-right; LOW on abstentions and wrong answers",
                "behavior": "identical to clean SFT by construction (answer text byte-identical)",
                "goal": "install stated-confidence DISCRIMINATION on the correctness axis while preserving behavior; feed the threshold bridge",
            },
        },
        "rows": {
            "sft": len(sft_rows),
            "sft_clean": len(sft_clean_rows),
            "sft_probe_distilled": len(sft_probe_distilled_rows),
            "sft_probe_factual": len(sft_probe_factual_rows),
            "sft_contrastive": len(sft_contrastive_rows),
            "sft_contrastive_masked": len(sft_contrastive_rows),
            "sft_contrastive_masked_inappropriate": sum(
                1 for r in sft_contrastive_rows if r.get("loss_mask_text")
            ),
            "dpo": len(dpo_rows),
            "kto": len(kto_rows),
        },
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
