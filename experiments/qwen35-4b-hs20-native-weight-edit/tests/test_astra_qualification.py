"""Synthetic checks of strict invariance and prompt/finish/schema refusals."""
import copy
import hashlib
import json
import struct

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


def capture_fixture(tmp_path, *, changed_data=False, changed_metadata=False):
    import numpy as np
    directories, records = [], []
    for name, metadata in [('original', {'a': 'x', 'b': 'y'}), ('resumed', {'b': 'y', 'a': 'x'})]:
        directory = tmp_path / name
        directory.mkdir()
        if changed_metadata and name == 'resumed':
            metadata['a'] = 'changed'
        values = np.array([0., 1.], dtype='<f4')
        if changed_data and name == 'resumed':
            values[0] = -0.  # equal numerically; different raw tensor bits
        header = json.dumps({'__metadata__': metadata, 'x': {'dtype': 'F32', 'shape': [2], 'data_offsets': [0, 8]}}).encode()
        header += b' ' * (-len(header) % 8)
        data = struct.pack('<Q', len(header)) + header + values.tobytes()
        (directory / 'row.safetensors').write_bytes(data)
        records.append([{'row_key': 'row', 'capture_files': {'anchor': {
            'file': 'row.safetensors', 'sha256': hashlib.sha256(data).hexdigest()}}}])
        directories.append(directory)
    return directories, records


def test_capture_parity_ignores_only_header_key_order_and_verifies_payload(tmp_path):
    dirs, rows = capture_fixture(tmp_path)
    assert rows[0][0]['capture_files']['anchor']['sha256'] != rows[1][0]['capture_files']['anchor']['sha256']
    assert q.compare_capture_rows(*dirs, *rows) == 1


@pytest.mark.parametrize(('data', 'metadata', 'message'), [(True, False, 'tensor bytes'), (False, True, 'metadata values')])
def test_capture_parity_rejects_actual_bit_or_metadata_changes(tmp_path, data, metadata, message):
    dirs, rows = capture_fixture(tmp_path, changed_data=data, changed_metadata=metadata)
    with pytest.raises(HarnessError, match=message):
        q.compare_capture_rows(*dirs, *rows)


def test_capture_parity_still_requires_each_files_own_hash_and_exact_rows(tmp_path):
    dirs, rows = capture_fixture(tmp_path)
    rows[1][0]['row_key'] = 'different'
    with pytest.raises(HarnessError, match='row metadata'):
        q.compare_capture_rows(*dirs, *rows)
    rows[1][0]['row_key'] = 'row'
    (dirs[1] / 'row.safetensors').write_bytes(b'corrupted')
    with pytest.raises(HarnessError, match='hash mismatch'):
        q.compare_capture_rows(*dirs, *rows)
