"""CPU entrypoint tests: no real engine, model, private rows or qualification claims."""
import ast
import copy
import json
import os
from pathlib import Path
from types import SimpleNamespace
import pytest
import yaml
from r2_runtime import astra_run as run, astra_analysis as analysis, astra_qualification as qual
from r2_runtime import admission, commitments
from r2_runtime.constructor import load_proposal
from r2_runtime.util import HarnessError, read_json, write_json, write_jsonl, sha256_file
from test_r2_runtime_analysis import complete_evaluation
from test_r2_runtime_support import git_commit_public


def test_plan_through_registered_main(capsys):
    path=Path(os.environ['EHR_R2_CONTRACT_DIR'])/'astra_r2.yaml'
    assert run.main(['--proposal',str(path),'plan'])==0
    p=json.loads(capsys.readouterr().out)
    assert [(c['surface'],c['prompt'],c['arm']) for c in p['evaluation_cells']]==[
        (s,p,a) for p in ('P-struct','P-rc') for s in ('selfaware','ambigqa') for a in ('base','edited')]
    assert sum(c['rows'] for c in p['evaluation_cells'])==20804
    assert p['maximum_completions_including_format_retries']==62412
    assert p['launch_authority'] is False


def test_draft_eval_entrypoint_never_reaches_engine(tmp_path,monkeypatch):
    d=tmp_path/'experiment';d.mkdir()
    (d/'experiment.yaml').write_text('status: draft\n')
    (tmp_path/'synaptic.yaml').write_text('paths: {artifacts: "project://.synaptic/artifacts"}\n')
    monkeypatch.setattr(run,'EXPERIMENT_DIR',d)
    monkeypatch.setattr(run,'_engine',lambda *a:pytest.fail('must not launch'))
    assert run.main(['--proposal',str(Path(os.environ['EHR_R2_CONTRACT_DIR'])/'astra_r2.yaml'),
        '--project-root',str(tmp_path),'eval-cell','--surface','selfaware','--prompt','P-struct','--arm','base',
        '--base-model',str(tmp_path),'--edited-model',str(tmp_path),'--gpu-ack'])==2


def test_eval_refuses_before_freeze_then_before_qualification(tmp_path,monkeypatch):
    from r2_runtime.config import Layout
    (tmp_path/'synaptic.yaml').write_text('paths: {artifacts: "project://.synaptic/artifacts"}\n')
    layout=Layout(tmp_path)
    proposal=load_proposal(Path(os.environ['EHR_R2_CONTRACT_DIR'])/'astra_r2.yaml')
    monkeypatch.setattr(run,'require_signed',lambda *a,**kw:{'evaluation':{'engine':'hf-batched'}})
    monkeypatch.setattr(run,'_gpu',lambda *a,**kw:pytest.fail('must not launch'))
    kw=dict(surface='selfaware',prompt='P-struct',arm='base',base_model=tmp_path,edited_model=tmp_path,ack=True)
    with pytest.raises(FileNotFoundError):run.evaluate_cell(proposal,tmp_path,layout,**kw)
    monkeypatch.setattr(run,'require_frozen',lambda *a:{'spec_sha256':'s'})
    with pytest.raises(FileNotFoundError):run.evaluate_cell(proposal,tmp_path,layout,**kw)


def test_qualification_compare_exact_twenty_two_orders_two_repeats_and_resume():
    original=[{'id':str(i),'expected_prompt_sha256':'p','expected_token_ids_sha256':'t','expected_prompt_tokens':3} for i in range(20)]
    rows=[{'id':r['id'],'prompt_sha256':'p','prompt_token_ids_sha256':'t','prompt_token_len':3,
           'completion_text':'{"answer":"Paris","response_confidence":0.5}',
           'completion_token_ids':[1,2],'finish_reason':'stop'} for r in original]
    runs={name:copy.deepcopy(rows[::-1] if name.startswith('permuted') else rows) for name in qual.RUNS}
    assert qual.compare(original,runs)['runs']==5
    runs['resume'][0]['completion_token_ids']=[3]
    with pytest.raises(HarnessError,match='QUAL_PARITY'):qual.compare(original,runs)
    runs['resume']=copy.deepcopy(rows);runs['original_b'][0]['completion_text']='prefix '+rows[0]['completion_text']
    with pytest.raises(HarnessError,match='QUAL_SCHEMA'):qual.compare(original,runs)


def test_guard_refuses_to_signal_a_callers_process_group(monkeypatch):
    from r2_runtime import qualification_owned as owned
    monkeypatch.setattr(owned.os,'getpgrp',lambda:owned.os.getpid()+1)
    with pytest.raises(HarnessError,match='QUAL_OWNER'):
        owned.guard(-1)


def test_full_inventory_refuses_symlinks_and_additions(tmp_path):
    (tmp_path/'model').write_bytes(b'fake checkpoint')
    old=admission.inventory(tmp_path)
    (tmp_path/'extra').write_bytes(b'extra')
    assert admission.inventory(tmp_path)!=old
    # T7 cannot create symlinks. Exercise refusal with tiny synthetic bytes on
    # the container's POSIX filesystem; all actual checkpoint fixtures stay T7.
    import tempfile
    with tempfile.TemporaryDirectory(prefix='ehr-r2-link-refusal-') as name:
        root=Path(name)
        (root/'member').write_bytes(b'synthetic')
        (root/'link').symlink_to(root/'member')
        with pytest.raises(HarnessError):admission.inventory(root)


def test_eight_cell_analysis_cli_commit_blind_unblind_rollup(complete_evaluation,monkeypatch,capsys):
    proposal,layout,cell,decoys=complete_evaluation
    # Test-local input injection uses synthetic proposal only; production checks have separate tests.
    monkeypatch.setattr(analysis.astra_fixed,'load_proposal',lambda *a:proposal)
    monkeypatch.setattr(analysis,'require_signed',lambda *a,**kw:cell.runtime)
    runtime=tmp=layout.project_root/'astra_runtime.yaml';runtime.write_text(yaml.safe_dump(cell.runtime))
    monkeypatch.setattr(analysis,'EXPERIMENT_DIR',layout.project_root)
    def invoke(*args):
        code=analysis.main(['--project-root',str(layout.project_root),*map(str,args)])
        out=capsys.readouterr().out
        assert code==0,out
        return json.loads(out)
    assert invoke('pool-build','--decoys',decoys)['candidates']==72
    invoke('pool-commit')
    git_commit_public(layout,'run_binding.json');git_commit_public(layout,'adjudication_pool_manifest.json')
    from r2_runtime import adjudication as lane
    manifest=read_json(lane.Pool(layout).manifest);grading={}
    for shard in manifest['shards']:
        sid=shard['shard_id'];file=layout.local(f'graded/{sid}.jsonl')
        rows=run.read_jsonl(lane.Pool(layout).pool_file(sid))
        assert all(set(r)=={'opaque_id','text'} for r in rows)
        write_jsonl(file,[{'opaque_id':r['opaque_id'],'is_abstention':r['text'].startswith("I don't know")} for r in rows])
        grading[sid]=str(file)
        invoke('commit-hash','--shard-id',sid,'--graded-file',file)
    git_commit_public(layout,'adjudication_graded_manifest.json')
    gm=layout.local('graded/map.json');write_json(gm,grading)
    invoke('spot-pack','--graded-map',gm)
    blind=run.read_jsonl(lane.Pool(layout).root/'spot_pack.blind.jsonl')
    decisions=layout.local('graded/decisions.jsonl')
    write_jsonl(decisions,[{'opaque_id':r['opaque_id'],'lead_is_abstention':r['text'].startswith("I don't know")} for r in blind])
    invoke('spot-record','--decisions',decisions);git_commit_public(layout,'adjudication_spot_manifest.json')
    assert invoke('apply','--graded-map',gm)['instrument_valid']
    assert invoke('rollup')['verdict']=='primary_pass'
    final=layout.local('astra-r2/evaluation/selfaware/P-struct/base/final.manifest.json')
    m=read_json(final);m['spec_sha256']='different';write_json(final,m)
    assert invoke('rollup')['verdict']=='instrument_invalid'


def test_relative_import_closure_has_no_r1_or_pilot_construction():
    root=Path(run.__file__).parent
    for p in root.glob('*.py'):
        tree=ast.parse(p.read_text())
        for n in ast.walk(tree):
            if isinstance(n,ast.ImportFrom) and n.level:
                if n.module: assert (root/(n.module.split('.')[0]+'.py')).exists(),(p,n.module)
            if isinstance(n,ast.Import):assert all(not x.name.startswith(('hs20_nwe','tuner.','shared.')) for x in n.names)
    assert 'def construct(' not in (root/'astra_fixed.py').read_text()
