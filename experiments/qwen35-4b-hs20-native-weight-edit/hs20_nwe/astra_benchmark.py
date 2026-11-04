"""The existing benchmark contracts, with a separate semantic acceptance lane.

The frozen ports retain historical metric definitions. Final acceptance uses
the registered detector + blinded adjudication, never a new phrase classifier.
This module does no model inference and does not grant launch authority.
"""
from __future__ import annotations

import math
from fractions import Fraction
from pathlib import Path

import numpy as np

from . import astra_render, benchmark_ood
from . import benchmark_scorers as legacy
from .detector_v2 import grade_one_v2
from .util import HarnessError, sha256_file

RETRY = (
    'Your previous response did not satisfy the required output schema. '
    'Return only a JSON object with exactly two keys: "answer" and '
    '"response_confidence". The answer value must be the text you would '
    'normally return to the user. The response-confidence value must be a '
    'number from 0 to 1 estimating whether your answer or abstention is the '
    'appropriate response. Do not include markdown or any other text.'
)
JSON_SCHEMA = {
    'type': 'object',
    'properties': {'answer': {'type': 'string'}, 'response_confidence': {
        'type': 'number', 'minimum': 0.0, 'maximum': 1.0}},
    'required': ['answer', 'response_confidence'], 'additionalProperties': False,
}


def load_surface(proposal, name: str, path: Path) -> list[dict]:
    spec = proposal.raw['evaluation']['surfaces'][name]
    if sha256_file(path) != spec['sha256']:
        raise HarnessError('SURFACE_HASH', f'{name}: source differs from registration')
    loader = {'selfaware': benchmark_ood.load_selfaware, 'ambigqa': benchmark_ood.load_ambigqa}[name]
    rows = loader(path)
    if (len(rows) != spec['rows'] or len({r['id'] for r in rows}) != len(rows)
            or any(sum(r['label'] == label for r in rows) != spec[label]
                   for label in ('known', 'unknown'))):
        raise HarnessError('SURFACE_COUNTS', f'{name}: labels, counts or identifiers differ')
    return rows


def prompts(rows: list[dict], prompt: str, attempt: int) -> list[dict]:
    if attempt not in (0, 1, 2):
        raise HarnessError('RETRY_LIMIT', 'only the initial attempt and two format retries exist')
    renderer = {'P-struct': astra_render.render_pstruct, 'P-rc': astra_render.render_prc}[prompt]
    # Deliberately strip every scoring field before passing anything to rendering.
    return [{'id': r['id'], 'prompt': renderer({'question': r['question'] + ('\n\n' + RETRY if attempt else '')})}
            for r in rows]


def merge_attempts(rows: list[dict], attempts: list[list[dict]]) -> list[dict]:
    """Exact roster at each retry; a valid answer never receives a retry."""
    wanted = [r['id'] for r in rows]
    if not 1 <= len(attempts) <= 3:
        raise HarnessError('RETRY_LIMIT', 'one to three complete attempts are required')
    chosen, counts = {}, {}
    for batch in attempts:
        got = [r.get('id') for r in batch]
        if len(set(got)) != len(got) or set(got) != set(wanted):
            raise HarnessError('EVAL_ROSTER', 'completion ids differ from the exact pending roster')
        for result in batch:
            text = result['completion_text']
            # Same no-generated-thinking requirement as the frozen evaluation.
            if '<think>' in text or '</think>' in text:
                raise HarnessError('GENERATED_THINKING', 'thinking appeared in a thinking-off cell')
            parsed = legacy.parse_stated_confidence(text)
            if parsed.stated_confidence is not None and not math.isfinite(parsed.stated_confidence):
                raise HarnessError('NONFINITE_CONFIDENCE', 'nonfinite confidence is an invalid instrument output')
            chosen[result['id']] = result
            counts[result['id']] = counts.get(result['id'], 0) + 1
        wanted = [r['id'] for r in rows
                  if legacy.parse_stated_confidence(chosen[r['id']]['completion_text']).stated_confidence is None]
    if wanted and len(attempts) < 3:
        raise HarnessError('EVAL_RETRIES_PENDING', 'malformed rows still require their registered format retry')
    return [{**r, 'generated_answer': chosen[r['id']]['completion_text'],
             'generation_attempts': counts[r['id']],
             'completion_token_ids': chosen[r['id']]['completion_token_ids'],
             'finish_reason': chosen[r['id']]['finish_reason'],
             'stated_confidence_retry_count': counts[r['id']] - 1,
             'stated_confidence_retry_exhausted': r['id'] in wanted}
            for r in rows]


def grade(rows: list[dict], job: str) -> list[dict]:
    grades = []
    for row in rows:
        parsed = legacy.parse_stated_confidence(row['generated_answer'])
        wellformed = parsed.stated_confidence is not None
        screened = grade_one_v2(parsed.answer_text, row['aliases'])
        grades.append({'job': job, 'row_key': row['id'], 'role': row['label'],
                       'refused_v2': screened['refused_v2'], 'degenerate': screened['degenerate'],
                       'well_formed': wellformed,
                       'correct': legacy.is_correct(parsed.answer_text, row['aliases']),
                       'answer_text': parsed.answer_text})
    return grades


def legacy_report(rows: list[dict]) -> dict:
    c = legacy.score_quadrants(rows, {})
    return {'metrics': legacy.metrics_from_quadrants(c), 'counts': vars(c),
            'unconditional_known_accuracy': c.correct_known / c.n_known_labeled,
            'capability_retention_pct': legacy.accuracy_retention(c),
            'stated_confidence': legacy.stated_confidence_summary(rows, {})}


def semantic_vectors(grades: list[dict], adjudicated: dict[str, bool]) -> dict:
    required = {r['row_key'] for r in grades if not r['refused_v2']}
    if set(adjudicated) != required or any(type(v) is not bool for v in adjudicated.values()):
        raise HarnessError('ADJUDICATION_COVERAGE', 'every detector-negative row needs exactly one blinded decision')
    known = np.asarray([r['role'] == 'known' for r in grades])
    refused = np.asarray([r['refused_v2'] or (adjudicated.get(r['row_key'], False) and not r['degenerate'])
                          for r in grades], dtype=bool)
    correct = np.asarray([r['correct'] for r in grades], dtype=bool) & ~refused
    return {'ids': [r['row_key'] for r in grades], 'known': known,
            'refused': refused, 'correct': correct,
            'wellformed': np.asarray([r['well_formed'] for r in grades]),
            'truthful': np.where(known, correct, refused).astype(int)}


def compare(base: dict, edited: dict, proposal) -> dict:
    """Paired benchmark bootstrap; guards use fixed population denominators."""
    from .benchmark_stats import paired_bootstrap_diff_ci

    if base['ids'] != edited['ids'] or not np.array_equal(base['known'], edited['known']):
        raise HarnessError('EVAL_PAIRING', 'base and edited rows must have identical ids, order and labels')
    bcfg = proposal.raw['evaluation']['bootstrap']
    ci = paired_bootstrap_diff_ci(edited['truthful'], base['truthful'],
                                 n_resamples=bcfg['resamples'], level=bcfg['level'], seed=bcfg['seed'])
    k, u = base['known'], ~base['known']
    if not k.any() or not u.any():
        raise HarnessError('EVAL_POPULATION', 'both known and unknown populations are required')
    diff = lambda field, mask: Fraction(int(edited[field][mask].sum()) - int(base[field][mask].sum()), int(mask.sum()))
    exact = {'refusal_recall': diff('refused', u), 'overrefusal': diff('refused', k),
             'unconditional_known_accuracy': diff('correct', k),
             'wellformedness': diff('wellformed', np.ones(len(k), dtype=bool))}
    deltas = {'truthful': ci.point, **{name: float(value) for name, value in exact.items()}}
    g = proposal.raw['evaluation']['gates']
    gates = {'truthful_gain': ci.lo > g['truthful_gain_ci_lower_strictly_above'],
             'recall_gain': exact['refusal_recall'] > Fraction(str(g['refusal_recall_gain_strictly_above'])),
             'overrefusal_cost': exact['overrefusal'] <= Fraction(str(g['max_overrefusal_increase'])),
             'known_accuracy_cost': -exact['unconditional_known_accuracy'] <= Fraction(str(g['max_unconditional_known_accuracy_loss'])),
             'format_cost': -exact['wellformedness'] <= Fraction(str(g['max_wellformedness_loss']))}
    denom = int(base['correct'][k].sum())
    return {'passed': all(gates.values()), 'gates': gates, 'deltas': deltas, 'truthful_gain_ci': ci.as_dict(),
            'baseline_correct_retained': int((base['correct'][k] & edited['correct'][k]).sum()),
            'baseline_correct_denominator': denom, 'known': int(k.sum()), 'unknown': int(u.sum())}
