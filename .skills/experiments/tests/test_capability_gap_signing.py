"""The documented HF fallback must carry immutable, local evidence at sign."""
from pathlib import Path
import hashlib

import pytest
import yaml
import exp


def ready(tmp_path):
    assert exp.main(['--root', str(tmp_path), 'new', 'cell', '--type', 'eval']) == 0
    directory = tmp_path / 'experiments/cell'
    path = directory / 'experiment.yaml'
    data = yaml.safe_load(path.read_text())
    data.update(prediction='A fixed prediction.', falsifier='A fixed failure condition.')
    data['instrument']['engine_exception'] = {'kind': 'capability-gap', 'reason': 'Pinned backend rejected the required mode.'}
    evidence = directory / 'gap.json'
    evidence.write_text('{"runtime":"pinned", "observed":"unsupported"}\n')
    data['instrument']['engine_exception']['evidence'] = 'gap.json'
    data['instrument']['configs'].append('gap.json')
    path.write_text(yaml.safe_dump(data))
    return directory, path, data


def sign(root):
    return exp.main(['--root', str(root), 'sign', 'cell'])


def test_gap_evidence_is_pinned_and_later_drift_is_refused(tmp_path):
    directory, path, _ = ready(tmp_path)
    assert sign(tmp_path) == 0
    data = yaml.safe_load(path.read_text())
    assert data['status'] == 'signed'
    assert data['instrument']['pins']['gap.json'] == hashlib.sha256((directory/'gap.json').read_bytes()).hexdigest()
    (directory/'gap.json').write_text('changed evidence')
    assert exp.main(['--root', str(tmp_path), 'validate']) != 0


@pytest.mark.parametrize('failure', ['no_reason', 'no_reference', 'not_pinned', 'missing', 'empty', 'outside', 'symlink'])
def test_gap_cannot_be_a_reason_only_or_unpinned_escape(tmp_path, failure):
    directory, path, data = ready(tmp_path)
    exception = data['instrument']['engine_exception']
    if failure == 'no_reason':
        exception['reason'] = ''
    elif failure == 'no_reference':
        exception.pop('evidence')
    elif failure == 'not_pinned':
        data['instrument']['configs'].remove('gap.json')
    elif failure == 'missing':
        (directory/'gap.json').unlink()
    elif failure == 'empty':
        (directory/'gap.json').write_bytes(b'')
    elif failure == 'outside':
        (directory.parent/'outside.json').write_text('external')
        exception['evidence'] = '../outside.json'
        data['instrument']['configs'].append('../outside.json')
    elif failure == 'symlink':
        (directory/'gap.json').unlink()
        outside = tmp_path/'outside.json'
        outside.write_text('external')
        (directory/'gap.json').symlink_to(outside)
    path.write_text(yaml.safe_dump(data))
    assert sign(tmp_path) != 0
    assert yaml.safe_load(path.read_text())['status'] == 'draft'
    assert yaml.safe_load(path.read_text())['instrument'].get('pins') == {}


@pytest.mark.parametrize('kind', ['parity-locked', 'intervention'])
def test_existing_named_exceptions_remain_compatible(tmp_path, kind):
    _, path, data = ready(tmp_path)
    data['instrument']['engine_exception'] = {'kind': kind, 'reason': 'Historical permitted exception.'}
    path.write_text(yaml.safe_dump(data))
    assert sign(tmp_path) == 0
