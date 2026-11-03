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
    assert args[args.index('--expected-vllm-version') + 1] == '0.23.0'
    assert args[args.index('--min-compute-capability') + 1] == '8.0'
    assert args[args.index('--temperature') + 1] == '0.0'
    assert '--do-sample' not in args and '--resume' in args
    assert '--json-schema' in args and '--suppress-token' not in args
