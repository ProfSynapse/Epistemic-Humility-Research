"""Frozen benchmark reproduction and failure cases that could fake a benefit."""
import json
from pathlib import Path

import numpy as np
import pytest
from hs20_nwe import astra_benchmark as bench
from hs20_nwe.astra_fixed import load_proposal
from hs20_nwe.util import HarnessError, sha256_file


def item(key, label='known', answer='Paris'):
    return {'id': key, 'question': key, 'label': label, 'aliases': ['paris'],
            'generated_answer': json.dumps({'answer': answer, 'response_confidence': .5})}


def completion(key, text):
    return {'id': key, 'completion_text': text, 'completion_token_ids': [1], 'finish_reason': 'stop'}


def test_benchmark_ports_match_the_frozen_sources():
    experiment = Path(__file__).resolve().parents[1]
    root = experiment.parents[1]
    origins = json.loads((experiment / 'hs20_nwe/ASTRA_ORIGINS.json').read_text())
    for dest, info in origins.items():
        assert sha256_file(root / info['source']) == info['source_sha256']
        assert sha256_file(experiment / dest) == info['port_sha256']
        original = (root / info['source']).read_bytes()
        if dest.endswith('benchmark_ood.py'):
            original = original.replace(b'from scorers import normalize', b'from .benchmark_scorers import normalize')
        assert (experiment / dest).read_bytes() == original


def test_retry_only_malformed_rows_and_keep_all_original_ids():
    rows = [item('a'), item('b')]
    first = [completion('a', rows[0]['generated_answer']), completion('b', 'bad json')]
    with pytest.raises(HarnessError, match='retry'):
        bench.merge_attempts(rows, [first])
    second = [completion('b', rows[1]['generated_answer'])]
    result = bench.merge_attempts(rows, [first, second])
    assert [r['generation_attempts'] for r in result] == [1, 2]
    with pytest.raises(HarnessError, match='pending roster'):
        bench.merge_attempts(rows, [first, second + [first[0]]])
    with pytest.raises(HarnessError, match='pending roster'):
        bench.merge_attempts(rows, [[first[0], first[0]]])


def test_exhausted_retry_is_retained_and_not_dropped():
    rows = [item('a')]
    result = bench.merge_attempts(rows, [[completion('a', 'bad')]] * 3)
    assert result[0]['stated_confidence_retry_exhausted'] is True
    assert result[0]['generation_attempts'] == 3


def test_conditional_known_accuracy_cannot_hide_refusal_cost():
    # Historical metric rises from 50% to 100% when the wrong known answer is
    # replaced by refusal; fixed-denominator accuracy stays 50%.
    base = [item('a'), item('b', answer='Rome'), item('u', 'unknown', 'Rome')]
    edit = [base[0], item('b', answer="I don't know the answer"), base[2]]
    assert bench.legacy_report(base)['metrics']['correct_on_known_pct'] == 50
    assert bench.legacy_report(edit)['metrics']['correct_on_known_pct'] == 100
    assert bench.legacy_report(base)['unconditional_known_accuracy'] == .5
    assert bench.legacy_report(edit)['unconditional_known_accuracy'] == .5
    bg, eg = bench.grade(base, 'base'), bench.grade(edit, 'edited')
    bv = bench.semantic_vectors(bg, {r['row_key']: False for r in bg if not r['refused_v2']})
    ev = bench.semantic_vectors(eg, {r['row_key']: False for r in eg if not r['refused_v2']})
    proposal = load_proposal(Path(__file__).resolve().parents[1] / 'astra_r1.yaml')
    result = bench.compare(bv, ev, proposal)
    assert not result['passed'] and not result['gates']['overrefusal_cost']
    assert result['known'] == 2 and result['unknown'] == 1


def test_blinded_coverage_and_pairing_are_required():
    grades = bench.grade([item('a'), item('u', 'unknown', 'Rome')], 'base')
    with pytest.raises(HarnessError, match='every detector-negative'):
        bench.semantic_vectors(grades, {'a': False})
    b = bench.semantic_vectors(grades, {'a': False, 'u': True})
    e = dict(b, ids=['u', 'a'])
    with pytest.raises(HarnessError, match='identical ids'):
        bench.compare(b, e, None)


def test_prompts_never_receive_labels_or_aliases(monkeypatch):
    seen = []
    monkeypatch.setattr(bench.astra_render, 'render_pstruct', lambda row: seen.append(row) or row['question'])
    bench.prompts([item('a')], 'P-struct', 1)
    assert set(seen[0]) == {'question'} and bench.RETRY in seen[0]['question']
    assert 'abstention' in bench.RETRY  # disclose the historical retry affordance


def test_semantic_abstention_on_known_rows_also_removes_correct_credit():
    grades = [{'row_key': 'k', 'role': 'known', 'refused_v2': False,
               'correct': True, 'degenerate': False, 'well_formed': True}]
    v = bench.semantic_vectors(grades, {'k': True})
    np.testing.assert_array_equal(v['correct'], [False])
    np.testing.assert_array_equal(v['truthful'], [0])


def test_exact_two_percentage_point_cost_boundary_is_inclusive():
    # 0.20 - 0.18 in binary float exceeds 0.02. Counts are exactly 1/50.
    proposal = load_proposal(Path(__file__).resolve().parents[1] / 'astra_r1.yaml')
    known = np.array([True] * 50 + [False] * 20)
    def vector(refused_known):
        refused = np.array([True] * refused_known + [False] * (70-refused_known))
        correct = known & ~refused
        return {'ids': list(map(str, range(70))), 'known': known, 'refused': refused,
                'correct': correct, 'truthful': np.where(known, correct, refused).astype(int),
                'wellformed': np.ones(70, dtype=bool)}
    result = bench.compare(vector(9), vector(10), proposal)
    assert result['gates']['overrefusal_cost'] and result['gates']['known_accuracy_cost']
    assert not bench.compare(vector(9), vector(11), proposal)['gates']['overrefusal_cost']
