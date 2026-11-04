"""Engine transport double exercises actual retry entrypoint and retained complete cell."""
from pathlib import Path
from types import SimpleNamespace
import pytest
from r3_runtime import astra_run as run, admission
from r3_runtime.config import Layout
from r3_runtime.util import write_json, write_jsonl, read_jsonl, sha256_file, HarnessError


def test_actual_eval_retries_only_malformed_and_resumes_complete_cell(tmp_path,monkeypatch):
    (tmp_path/'synaptic.yaml').write_text('paths: {artifacts: "project://artifacts"}\n')
    layout=Layout(tmp_path)
    proposal=SimpleNamespace(sha256='p',raw={'model':{'revision':'r'},'evaluation':{
        'surfaces':{'selfaware':{'rows':2},'ambigqa':{'rows':2}},'prompts':['P-struct','P-rc'],
        'arms':['base','edited'],'initial_completions':16,'maximum_evaluation_completions_including_retries':48,
        'max_attempts_per_item':3}})
    rows=[{'id':'a'},{'id':'b'}];prefix=run.PREFIX
    write_jsonl(layout.local(f'{prefix}/inputs/selfaware.jsonl'),rows)
    write_json(layout.local(f'{prefix}/materialized.json'),{'files':{'selfaware.jsonl':sha256_file(layout.local(f'{prefix}/inputs/selfaware.jsonl'))}})
    from r3_runtime import commitments
    write_json(commitments.public_path(layout,'astra_patch_freeze.json'),{})
    monkeypatch.setattr(run,'require_signed',lambda *a,**k:{'evaluation':{'engine':'hf-batched'}})
    monkeypatch.setattr(run,'require_frozen',lambda *a:{'spec_sha256':'s'})
    monkeypatch.setattr(admission,'require_qualification',lambda *a:'q')
    monkeypatch.setattr(run.benchmark,'prompts',lambda rows,prompt,i:[{'id':r['id'],'prompt':str(i)} for r in rows])
    monkeypatch.setattr(run.benchmark,'merge_attempts',lambda rows,attempts:[dict(r,generation_attempts=2 if r['id']=='a' else 1) for r in rows])
    monkeypatch.setattr(run,'batch_arguments',lambda p,r,l,m,pr,out:[pr,out])
    calls=[]
    def gpu(root,layout,operation,args,**kwargs):
        pending=read_jsonl(layout.to_local(args[0]));calls.append(pending)
        write_jsonl(layout.to_local(args[1])/'completions.jsonl',[{'id':r['id'],
          'completion_text':'bad' if len(calls)==1 and r['id']=='a' else '{"answer":"Paris","response_confidence":0.5}'} for r in pending])
    monkeypatch.setattr(run,'_gpu',gpu)
    kw=dict(surface='selfaware',prompt='P-struct',arm='base',base_model=tmp_path,edited_model=tmp_path,ack=True)
    result=run.evaluate_cell(proposal,tmp_path,layout,**kw)
    assert [[r['id'] for r in c] for c in calls]==[['a','b'],['a']]
    assert result['qualification_sha256']=='q'
    assert run.evaluate_cell(proposal,tmp_path,layout,**kw)==result
    assert len(calls)==2
    with pytest.raises(HarnessError,match='CELL_ORDER'):
        run.evaluate_cell(proposal,tmp_path,layout,**dict(kw,surface='ambigqa'))
    assert len(calls)==2
