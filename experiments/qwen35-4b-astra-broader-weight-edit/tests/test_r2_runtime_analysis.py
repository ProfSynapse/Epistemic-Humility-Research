"""Synthetic end-to-end use of the real committed blinded lane and new roll-up."""
import copy
import json
from pathlib import Path

import pytest
import yaml
from test_r2_runtime_support import git_commit_public, trust_test_git_root
from r2_runtime import adjudication as lane
from r2_runtime import astra_analysis as analysis
from r2_runtime import commitments
from r2_runtime.astra_fixed import Proposal, load_proposal
from r2_runtime.config import Layout
from r2_runtime.util import read_json, read_jsonl, sha256_file, write_json, write_jsonl


@pytest.fixture
def complete_evaluation(tmp_path,monkeypatch):
    experiment = Path(__import__('os').environ['EHR_R2_CONTRACT_DIR'])
    original = load_proposal(experiment / 'astra_r2.yaml')
    cfg = copy.deepcopy(original.raw)
    for spec in cfg['evaluation']['surfaces'].values():
        spec.update(rows=12, known=6, unknown=6)
    cfg['grading'].update(positive_decoys_per_shard=2, negative_decoys_per_shard=2, lead_spot_check_n=2)
    root = tmp_path / 'project'
    root.mkdir()
    trust_test_git_root(monkeypatch,root)
    (root / 'synaptic.yaml').write_text(yaml.safe_dump({'paths': {'artifacts': 'project://.synaptic/artifacts'}}))
    layout = Layout(root)
    frozen = {'proposal_sha256': 'a'*64, 'spec_sha256': 'b'*64}
    commitments.export(layout, 'astra_patch_freeze.json', frozen)
    git_commit_public(layout, 'astra_patch_freeze.json')
    qpath = commitments.export(layout, 'astra_edited_qualification.json', {'passed': True, 'scored': False,
        'binding': {'proposal_sha256':'a'*64, 'patch_freeze_sha256':sha256_file(commitments.public_path(layout,'astra_patch_freeze.json'))}})
    git_commit_public(layout, 'astra_edited_qualification.json')
    for surface in cfg['evaluation']['surfaces']:
        rows = [{'id': f'{surface}-{i}', 'question': f'synthetic {surface} {i}',
                 'label': 'known' if i<6 else 'unknown', 'aliases': ['paris'] if i<6 else [], 'source': surface}
                for i in range(12)]
        write_jsonl(layout.local(f'astra-r2/inputs/{surface}.jsonl'), rows)
        for prompt in cfg['evaluation']['prompts']:
            for arm in cfg['evaluation']['arms']:
                final = [{**r, 'generated_answer': json.dumps({'answer': "I don't know the answer" if arm=='edited' and r['label']=='unknown' else 'Paris', 'response_confidence': .8})}
                         for r in rows]
                path = layout.local(f'astra-r2/evaluation/{surface}/{prompt}/{arm}/final.jsonl')
                write_jsonl(path, final)
                write_json(path.with_suffix('.manifest.json'), {
                    'proposal_sha256': 'a'*64, 'spec_sha256': 'b'*64,
                    'patch_freeze_sha256': sha256_file(commitments.public_path(layout, 'astra_patch_freeze.json')),
                    'output_sha256': sha256_file(path), 'qualification_sha256':sha256_file(qpath)})
    decoys = {name: [{'row_key': f'decoy-{name}-{i}', 'text': text, 'kind': kind, 'arm': 'decoy'} for i in range(2)]
              for name, text, kind in [('pos', "I don't know the answer", 'decoy_pos'), ('neg', 'Paris', 'decoy_neg')]}
    decoys_path = layout.local('astra-r2/decoys.json')
    write_json(decoys_path, decoys)
    cfg['grading']['decoys_sha256'] = sha256_file(decoys_path)
    proposal = Proposal(cfg, 'a'*64)
    runtime = yaml.safe_load((experiment / 'astra_runtime.yaml').read_text())
    cell = analysis.GradingCell(proposal, runtime)
    return proposal, layout, cell, decoys_path


def _complete_blinded_lane(complete_evaluation):
    proposal, layout, cell, decoys = complete_evaluation
    summary = analysis.build_pool(proposal, layout, cell, decoys)
    assert summary['candidates'] == 72
    lane.commit_pool(layout)
    git_commit_public(layout, 'run_binding.json')
    git_commit_public(layout, 'adjudication_pool_manifest.json')
    manifest = json.loads(lane.Pool(layout).manifest.read_text())
    grading = {}
    for entry in manifest['shards']:
        sid = entry['shard_id']
        path = layout.local(f'grading/graded/{sid}.jsonl')
        write_jsonl(path, [{'opaque_id': row['opaque_id'], 'is_abstention': row['text'].startswith("I don't know")}
                          for row in read_jsonl(lane.Pool(layout).pool_file(sid))])
        grading[sid] = path
        lane.commit_hash(layout, sid, path)
    git_commit_public(layout, 'adjudication_graded_manifest.json')
    spot = lane.spot_check_pack(cell, layout, grading)
    assert all(set(r)=={'opaque_id','text'} for r in spot)
    lane.record_spot_check(cell, layout, [{'opaque_id': r['opaque_id'], 'lead_is_abstention': r['text'].startswith("I don't know")} for r in spot])
    git_commit_public(layout, 'adjudication_spot_manifest.json')
    assert lane.apply(cell, layout, {k:str(v) for k,v in grading.items()})['instrument_valid']
    result = analysis.rollup(proposal, layout, cell)
    assert result['verdict'] == 'primary_pass', result
    assert result['transfer_supported']
    assert len(result['comparisons']) == 4


def test_blinded_pool_to_primary_rollup_requires_real_git_checkpoints(complete_evaluation):
    _complete_blinded_lane(complete_evaluation)


@pytest.mark.parametrize('change',['applied','committed_grade','missing_grade','idmap','answer'])
def test_rollup_authenticates_grades_maps_and_original_answers(complete_evaluation,change):
    _complete_blinded_lane(complete_evaluation)
    proposal,layout,cell,_=complete_evaluation;pool=lane.Pool(layout)
    if change=='applied':
        rows=read_jsonl(pool.applied);rows[0]['adjudicated_abstention']=not rows[0]['adjudicated_abstention']
        write_jsonl(pool.applied,rows)
    elif change=='committed_grade':
        p=next((pool.root/'retained_grades').glob('*.jsonl'))
        rows=read_jsonl(p);rows[0]['is_abstention']=not rows[0]['is_abstention'];write_jsonl(p,rows)
    elif change=='missing_grade':
        next((pool.root/'retained_grades').glob('*.jsonl')).unlink()
    elif change=='idmap':
        manifest=read_json(pool.manifest);p=pool.idmap_file(manifest['shards'][0]['shard_id'])
        rows=read_jsonl(p);rows[0]['kind']='core' if rows[0]['kind']!='core' else 'decoy_neg';write_jsonl(p,rows)
    else:
        p=layout.local('astra-r2/evaluation/selfaware/P-struct/base/final.jsonl')
        rows=read_jsonl(p);rows[0]['generated_answer']='{"answer":"London","response_confidence":0.8}'
        write_jsonl(p,rows)
        m=p.with_suffix('.manifest.json');record=read_json(m);record['output_sha256']=sha256_file(p);write_json(m,record)
    assert analysis.rollup(proposal,layout,cell)['verdict']=='instrument_invalid'


def test_missing_cell_is_incomplete_and_changed_label_invalidates(complete_evaluation):
    proposal, layout, cell, _ = complete_evaluation
    path = layout.local('astra-r2/evaluation/selfaware/P-struct/base/final.jsonl')
    original = path.read_bytes()
    path.unlink()
    assert analysis.rollup(proposal, layout, cell)['verdict'] == 'incomplete'
    path.write_bytes(original)
    rows = read_jsonl(path)
    rows[0]['question'] = 'a changed question'
    write_jsonl(path, rows)
    assert analysis.rollup(proposal, layout, cell)['verdict'] == 'instrument_invalid'


def test_prior_decoy_selection_excludes_construction_and_eval_questions(complete_evaluation):
    proposal, layout, _, _ = complete_evaluation
    proposal.raw['development']['counts'] = {'confab': 1, 'known_correct_answered': 1}
    proposal.raw['grading']['decoy_sources']['counts_per_class'] = 2
    rows = [{'row_key': f'{role}-{i}', 'question': f'prior {role} {i}', 'role': role, 'aliases': ['Paris']}
            for role in ('confab', 'known_correct_answered') for i in range(6)]
    rows[0]['question'] = 'synthetic selfaware 0'  # an evaluation question, never a decoy
    fit = layout.local('prior/fit.jsonl')
    baseline, positive = layout.local('prior/baseline.jsonl'), layout.local('prior/positive.jsonl')
    write_jsonl(fit, rows)
    write_jsonl(baseline, [{'row_key': r['row_key'], 'terminated_naturally': True,
                           'answer_text': json.dumps({'answer': 'Paris'})} for r in rows if r['role']=='known_correct_answered'])
    write_jsonl(positive, [{'row_key': r['row_key'], 'terminated_naturally': True, 'dose_multiplier': 8.0,
                           'answer_text': json.dumps({'answer': "I don't know the answer"})} for r in rows if r['role']=='confab'])
    proposal.raw['development']['fit_sha256'] = sha256_file(fit)
    cfg = proposal.raw['grading']['decoy_sources']
    cfg.update(baseline_sha256=sha256_file(baseline), positive_sha256=sha256_file(positive))
    out = layout.local('prior/decoys.json')
    result = analysis.prepare_decoys(proposal, layout, fit=fit, baseline=baseline, positive=positive, out=out)
    assert result['eligible_counts'] == {'pos': 4, 'neg': 5}
    document = json.loads(out.read_text())
    assert all(len(document[k]) == 2 for k in ('pos', 'neg'))
    assert not any(r['row_key']=='confab-0' for r in document['pos'])
