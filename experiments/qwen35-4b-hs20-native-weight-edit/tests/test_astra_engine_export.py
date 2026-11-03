"""Actual CPU engine export/readback of the fixed formula on synthetic weights.

Run in the pinned capture image, on the same T7 filesystem as the real export.
This never loads a language model or uses a GPU.
"""
import copy
import json
import shutil

import numpy as np
import pytest

torch = pytest.importorskip('torch')
from conftest import EXPERIMENT
from hs20_nwe import astra_fixed as af
from hs20_nwe import weights
from hs20_nwe.astra_run import read_tensor
from hs20_nwe.config import Layout
from hs20_nwe.engine import Engine
from hs20_nwe.util import sha256_file, write_json, write_yaml
from safetensors.torch import load_file, save_file


def test_fixed_formula_export_readback_and_untouched_sidecars(tmp_path):
    root = tmp_path / 'project'
    root.mkdir()
    shutil.copy(EXPERIMENT.parents[1] / 'synaptic.yaml', root / 'synaptic.yaml')
    layout = Layout(root)
    base = layout.local('base_model')
    base.mkdir(parents=True)
    raw = copy.deepcopy(af.load_proposal(EXPERIMENT / 'astra_r1.yaml').raw)
    raw['patch'].update(shape=[64, 48], columns=5, maximum_modified_entries=320)
    raw['development']['counts'] = {'confab': 8, 'known_correct_answered': 8}
    rng = np.random.default_rng(20261103)
    w = torch.tensor(rng.normal(0, .05, (64, 48)), dtype=torch.bfloat16)
    untouched = torch.arange(4, dtype=torch.bfloat16).reshape(2, 2)
    save_file({raw['patch']['tensor']: w, 'other.weight': untouched}, str(base / 'model-00001-of-00001.safetensors'))
    write_json(base / 'model.safetensors.index.json', {
        'metadata': {'total_size': (w.numel() + untouched.numel()) * 2},
        'weight_map': {raw['patch']['tensor']: 'model-00001-of-00001.safetensors', 'other.weight': 'model-00001-of-00001.safetensors'}})
    write_json(base / 'config.json', {'synthetic': True})
    (base / 'chat_template.jinja').write_text('synthetic-template')
    raw['model']['files_sha256'] = {'model-00001-of-00001.safetensors': sha256_file(base / 'model-00001-of-00001.safetensors')}
    proposal = af.Proposal(raw, 'a' * 64)
    eng = Engine(root, [])
    request = {'schema_version': weights.INSPECT_SCHEMA, 'checkpoint': layout.ref('base_model'),
               'hash_files': True, 'hash_tensors': True, 'tensors': [proposal.tensor], 'max_listed_tensors': 4}
    write_yaml(layout.local('inspect.yaml'), request)
    code, listing = eng.run_json(['weights-inspect', '--weights-config', layout.ref('inspect.yaml'), '--json'],
                                 layout.local('inspect.json'))
    assert code == 0
    target, bound = af.resolve_target(proposal, weights.unwrap(listing))
    U, K = rng.normal(size=(8, 48)), rng.normal(0, .1, (8, 48))
    U[:, :5] += 40
    c = rng.normal(size=64)
    c /= np.linalg.norm(c)
    con = af.construct(U, K, c, w.float().numpy(), proposal,
                       u_keys=[f'u-{i}' for i in range(8)], k_keys=[f'k-{i}' for i in range(8)])
    emitted = af.emit_patch(proposal, con, target, bound, out_dir=layout.local('patch'),
                            checkpoint_ref=layout.ref('base_model'), payload_ref=layout.ref('patch/payload.safetensors'),
                            export_ref=layout.ref('edited_model'))
    code, validation = eng.run_json(['weights-patch', '--weights-config', layout.ref('patch/spec.yaml'), '--validate', '--json'],
                                    layout.local('validate.json'))
    assert code == 0
    code, exported = eng.run_json(['weights-patch', '--weights-config', layout.ref('patch/spec.yaml'), '--export', '--json'],
                                  layout.local('export.json'))
    assert code == 0
    receipt = weights.unwrap(validation)['receipt']['tensors'][0]
    manifest = weights.unwrap(exported)['manifest']
    assert manifest['spec']['sha256'] == emitted['spec_sha256']
    assert manifest['payload']['sha256'] == emitted['payload_sha256']
    assert manifest['totals']['tensors_modified'] == 1 and manifest['totals']['noop'] is False
    edited = layout.local('edited_model')
    readback = layout.local('edited.npy')
    read_tensor(proposal, edited, manifest['tensors'][0]['after_sha256'], readback)
    actual = np.load(readback, allow_pickle=False)
    audit = af.audit_realized(con, proposal, U, K, w.float().numpy(), actual, receipt_tensor=receipt)
    assert audit['passed'], audit['failures']
    assert audit['entries_changed'] > 0 and audit['changed_off_support'] == 0
    for name in ('config.json', 'chat_template.jinja', 'model.safetensors.index.json'):
        assert (edited / name).read_bytes() == (base / name).read_bytes()
    assert torch.equal(load_file(str(edited / 'model-00001-of-00001.safetensors'))['other.weight'], untouched)
    assert af.bf16_raw_sha256(w.float().numpy()) == target['sha256']
    assert json.loads((edited / 'mechinterp-weight-export.manifest.json').read_text()) == manifest
