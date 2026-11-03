"""Synthetic checks of strict invariance and prompt/finish/schema refusals."""
import copy
import json

import pytest
from hs20_nwe import astra_qualification as q
from hs20_nwe.util import HarnessError


def samples():
    original = [{'id': f'qual-{i:02}', 'expected_prompt_sha256': f'{i:064x}',
                 'expected_token_ids_sha256': f'{i+100:064x}', 'expected_prompt_tokens': 10+i}
                for i in range(q.N)]
    completed = [{'id': r['id'], 'prompt_sha256': r['expected_prompt_sha256'],
                  'prompt_token_ids_sha256': r['expected_token_ids_sha256'],
                  'prompt_token_len': r['expected_prompt_tokens'], 'completion_text': json.dumps({'answer': 'synthetic', 'response_confidence': .5}),
                  'completion_token_ids': [i, 1, 2], 'finish_reason': 'stop'} for i, r in enumerate(original)]
    return original, {name: copy.deepcopy(completed) for name in q.RUNS}


def test_exact_permuted_and_resumed_rows_match():
    original, runs = samples()
    runs['permuted_a'].reverse()
    runs['permuted_b'].reverse()
    report = q.compare(original, runs)
    assert report['rows'] == 20 and report['runs'] == 5 and report['completion_token_ids_identical']


@pytest.mark.parametrize(('field', 'value', 'code'), [
    ('completion_token_ids', [99], 'QUAL_PARITY'),
    ('finish_reason', 'length', 'QUAL_FINISH'),
    ('prompt_sha256', 'changed', 'QUAL_TOKENIZER'),
    ('prompt_token_ids_sha256', 'changed', 'QUAL_TOKENIZER'),
    ('prompt_token_len', 999, 'QUAL_TOKENIZER'),
    ('completion_text', 'preamble {"answer":"x","response_confidence":0.5}', 'QUAL_SCHEMA'),
    ('completion_text', '{"answer":"x","response_confidence":1.1}', 'QUAL_SCHEMA'),
])
def test_corruption_is_never_qualified(field, value, code):
    original, runs = samples()
    runs['original_b'][0][field] = value
    with pytest.raises(HarnessError) as exc:
        q.compare(original, runs)
    assert exc.value.code == code


def test_missing_repeats_and_duplicate_rows_refuse():
    original, runs = samples()
    del runs['resume']
    with pytest.raises(HarnessError, match='resumed run'):
        q.compare(original, runs)
    original, runs = samples()
    runs['resume'][-1] = runs['resume'][0]
    with pytest.raises(HarnessError, match='duplicate ids'):
        q.compare(original, runs)


def test_gpu_ack_is_required_before_any_runtime_lookup():
    with pytest.raises(HarnessError, match='gpu-ack'):
        q.run(None, None, None, None, 'original_a', ack=False)


@pytest.mark.parametrize('name', ['../escape', '', None, '/absolute', 'space name', 'a/b'])
def test_qualification_namespace_cannot_escape_or_be_implicit(name):
    with pytest.raises(HarnessError, match='namespace'):
        q.qualification_root({'qualification': {'namespace': name}})


def test_changed_namespace_changes_engine_output_paths():
    assert q.qualification_root({'qualification': {'namespace': 'r1'}}) != q.qualification_root({'qualification': {'namespace': 'r2'}})
