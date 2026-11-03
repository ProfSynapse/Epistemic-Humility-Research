"""Launch admission and declared execution plan, with no GPU or model calls."""
from pathlib import Path

import pytest
import yaml
from hs20_nwe import astra_run as run
from hs20_nwe.astra_fixed import load_proposal
from hs20_nwe.util import HarnessError, sha256_file

EXPERIMENT = Path(__file__).resolve().parents[1]


def test_real_plan_has_eight_existing_benchmark_cells():
    proposal = load_proposal(EXPERIMENT / 'astra_r1.yaml')
    plan = run.plan(proposal)
    assert len(plan['evaluation_cells']) == 8
    assert sum(c['rows'] for c in plan['evaluation_cells']) == 20804
    assert plan['maximum_completions_including_format_retries'] == 62412
    assert plan['launch_authority'] is False
    assert not any('candidate' in s for s in plan['construction'])


def test_current_draft_cannot_launch():
    with pytest.raises(HarnessError, match='draft does not authorize'):
        run.require_signed(EXPERIMENT, runtime_role='capture')


def test_admission_requires_pins_actual_image_and_qualification(tmp_path, monkeypatch):
    (tmp_path / 'module.py').write_text('# synthetic instrument\n')
    manifest = {'status': 'signed', 'instrument': {'modules': ['module.py'], 'configs': [],
                 'pins': {'module.py': sha256_file(tmp_path / 'module.py')}}}
    (tmp_path / 'experiment.yaml').write_text(yaml.safe_dump(manifest))
    runtime = {'evaluation': {'image_digest': 'sha256:synthetic', 'qualified': False}}
    (tmp_path / 'astra_runtime.yaml').write_text(yaml.safe_dump(runtime))
    monkeypatch.setenv('EHR_RUNTIME_IMAGE_ID', 'sha256:wrong')
    with pytest.raises(HarnessError, match='registered image'):
        run.require_signed(tmp_path, runtime_role='evaluation')
    monkeypatch.setenv('EHR_RUNTIME_IMAGE_ID', 'sha256:synthetic')
    with pytest.raises(HarnessError, match='real model invariance'):
        run.require_signed(tmp_path, runtime_role='evaluation')
    runtime['evaluation']['qualified'] = True
    (tmp_path / 'astra_runtime.yaml').write_text(yaml.safe_dump(runtime))
    assert run.require_signed(tmp_path, runtime_role='evaluation') == runtime
    (tmp_path / 'module.py').write_text('# drift\n')
    with pytest.raises(HarnessError, match='unpinned or changed'):
        run.require_signed(tmp_path, runtime_role='evaluation')


def test_development_capture_uses_both_sides_of_exact_module():
    from types import SimpleNamespace
    proposal = load_proposal(EXPERIMENT / 'astra_r1.yaml')
    layout = SimpleNamespace(ref=lambda r: 'artifact://test/' + r)
    config = run.capture_config(proposal, layout)
    assert config['layers'] == [20]
    assert config['forward_only'] and config['use_cache'] and config['resume']
    assert config['capture_sites'] == [
        {'layer': 19, 'module': 'mlp.down_proj', 'tensor': 'input'},
        {'layer': 19, 'module': 'mlp.down_proj', 'tensor': 'output'}]


def test_batch_arguments_pin_registered_engine_and_do_not_sample(tmp_path):
    from types import SimpleNamespace
    proposal = load_proposal(EXPERIMENT / 'astra_r1.yaml')
    runtime = yaml.safe_load((EXPERIMENT / 'astra_runtime.yaml').read_text())
    layout = SimpleNamespace(ref=lambda r: 'artifact://test/' + r)
    args = run.batch_arguments(proposal, runtime, layout, tmp_path, 'artifact://prompts', 'artifact://out')
    assert args[args.index('--engine') + 1] == runtime['evaluation']['engine']
    assert args[args.index('--batch-size') + 1] == str(runtime['evaluation']['batch_size'])
    if runtime['evaluation']['engine'] == 'hf-batched':
        assert '--expected-vllm-version' not in args and '--vllm-model-runner' not in args
        assert args[args.index('--structured-output-backend') + 1] == 'xgrammar'
    assert args[args.index('--temperature') + 1] == '0.0'
    assert '--do-sample' not in args and '--resume' in args
    assert '--json-schema' in args and '--suppress-token' not in args


def _eval_fixture(tmp_path, monkeypatch, engine):
    from types import SimpleNamespace
    from hs20_nwe import commitments
    from hs20_nwe.util import write_json, write_jsonl
    root = tmp_path / 'project'
    rows = [{'id': f'row-{i}'} for i in range(2)]
    local = lambda rel: root / rel
    write_jsonl(_parent(local(f'{run.PREFIX}/inputs/selfaware.jsonl')), rows)
    write_json(_parent(local(f'{run.PREFIX}/materialized.json')),
               {'files': {'selfaware.jsonl': sha256_file(local(f'{run.PREFIX}/inputs/selfaware.jsonl'))}})
    public = _parent(root / 'public/astra_patch_freeze.json')
    public.write_text('{}')
    layout = SimpleNamespace(local=local, ref=lambda r: 'artifact://test/' + r)
    proposal = SimpleNamespace(sha256='p', raw={'evaluation': {'max_attempts_per_item': 3}, 'model': {'revision': 'r'}})
    runtime = {'evaluation': {'engine': engine}}
    monkeypatch.setattr(run, 'require_signed', lambda *a, **k: runtime)
    monkeypatch.setattr(run, 'require_frozen', lambda *a, **k: {'spec_sha256': 's'})
    monkeypatch.setattr(run, 'batch_arguments', lambda *a, **k: [a[4], a[5]])
    monkeypatch.setattr(commitments, 'public_path', lambda *a, **k: public)
    monkeypatch.setattr(run.benchmark, 'prompts', lambda pending, prompt, idx: [{'id': r['id'], 'idx': idx} for r in pending])
    monkeypatch.setattr(run.benchmark.legacy, 'parse_stated_confidence',
                        lambda text: SimpleNamespace(stated_confidence=None if text == 'bad' else 0.5))
    monkeypatch.setattr(run.benchmark, 'merge_attempts',
                        lambda rows, attempts: [dict(r, generation_attempts=len(attempts)) for r in rows])
    calls = []

    def gpu(_root, _layout, operation, args, *, ack, role):
        calls.append((operation, role, args[1]))
        out = local(args[1].removeprefix('artifact://test/') + '/completions.jsonl')
        pending = [r['id'] for r in run.read_jsonl(local(args[0].removeprefix('artifact://test/')))]
        text = 'bad' if len(calls) == 1 else 'ok'
        write_jsonl(_parent(out), [{'id': r, 'completion_text': text if r == 'row-0' else 'ok'} for r in pending])
    monkeypatch.setattr(run, '_gpu', gpu)
    return proposal, root, layout, calls


def _parent(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _evaluate(proposal, root, layout):
    return run.evaluate_cell(proposal, root, layout, surface='selfaware', prompt='P-struct', arm='base',
                             base_model=root, edited_model=root, ack=True)


def test_hf_evaluation_needs_no_vllm_flag_and_retries_only_malformed_rows(tmp_path, monkeypatch):
    monkeypatch.delenv('VLLM_BATCH_INVARIANT', raising=False)
    proposal, root, layout, calls = _eval_fixture(tmp_path, monkeypatch, 'hf-batched')
    record = _evaluate(proposal, root, layout)
    assert [c[:2] for c in calls] == [('batch-generate', 'evaluation')] * 2
    assert calls[0][2].endswith('attempt-0/output') and calls[1][2].endswith('attempt-1/output')
    assert run.read_jsonl(layout.local(f'{run.PREFIX}/evaluation/selfaware/P-struct/base/attempt-1/prompts.jsonl')) == [{'id': 'row-0', 'idx': 1}]
    assert record['rows'] == 2


def test_vllm_evaluation_still_requires_the_invariance_flag(tmp_path, monkeypatch):
    monkeypatch.delenv('VLLM_BATCH_INVARIANT', raising=False)
    proposal, root, layout, calls = _eval_fixture(tmp_path, monkeypatch, 'vllm')
    with pytest.raises(HarnessError, match='VLLM_BATCH_INVARIANT'):
        _evaluate(proposal, root, layout)
    assert not calls
