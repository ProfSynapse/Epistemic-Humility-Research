"""Real POSIX kill tests, synthetic durable rows only. No model/engine import."""
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from types import SimpleNamespace
import pytest
from r2_runtime import qualification_owned as owned, astra_qualification as qual
from r2_runtime import astra_run as run, admission, commitments
from r2_runtime.qualification_compare import RUNS
from r2_runtime.config import Layout
from r2_runtime.util import HarnessError, write_jsonl, read_json, sha256_file, canonical_sha256

WORKER = r'''
import json, os, pathlib, subprocess, sys, time
from r2_runtime.qualification_owned import guard
root=pathlib.Path(sys.argv[1]); guard(int(sys.argv[2]))
child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)'])
with (root/'descendants.jsonl').open('a') as s:
    s.write(json.dumps({'pid':child.pid})+'\n');s.flush();os.fsync(s.fileno())
p=root/'runs/resume/completions.jsonl';p.parent.mkdir(parents=True,exist_ok=True)
original=json.loads((root/'rows.json').read_text())
done={json.loads(l)['id'] for l in p.read_text().splitlines()} if p.exists() else set()
for row in original:
    if row['id'] in done: continue
    with p.open('a') as s:
        s.write(json.dumps(row)+'\n');s.flush();os.fsync(s.fileno())
    time.sleep(.025)
child.terminate();child.wait()
'''


def rows():
    original=[];completed=[]
    for i in range(20):
        h=hashlib.sha256(str(i).encode()).hexdigest()
        original.append({'id':str(i),'prompt':str(i),'expected_prompt_sha256':h,
                         'expected_token_ids_sha256':h,'expected_prompt_tokens':1})
        completed.append({'id':str(i),'prompt_sha256':h,'prompt_token_ids_sha256':h,
                          'prompt_token_len':1,'completion_token_ids':[i+1],
                          'finish_reason':'stop','completion_text':'{"answer":"synthetic","response_confidence":0.5}'})
    return original,completed


def live(root,binding):
    root.mkdir(parents=True,exist_ok=True)
    _,completed=rows();(root/'rows.json').write_text(json.dumps(completed))
    script=root/'worker.py';script.write_text(WORKER)
    # cwd locates experiment package; no engine/module source injection.
    read_fd,write_fd=os.pipe()
    command=[sys.executable,'-c',WORKER,str(root),str(read_fd)]
    try:
        result=owned.drill(command,root,binding,pass_fds=(read_fd,),timeout=10,cwd=Path(__file__).resolve().parents[1])
    finally:
        os.close(write_fd);os.close(read_fd)
    return result,command


def not_running(pid):
    path=Path(f'/proc/{pid}/stat')
    return not path.exists() or path.read_text().split()[2]=='Z'


def test_real_sigkill_resume_exact_prefix_descendant_and_claim(tmp_path,monkeypatch):
    signals=[];send=owned._signal
    def observe(child,sig):
        signals.append(sig);return send(child,sig)
    monkeypatch.setattr(owned,'_signal',observe)
    result,command=live(tmp_path,{'source':'exact','checkpoint':'complete'})
    assert signals==[signal.SIGKILL]  # the parent-loss guardian is never stopped
    assert result['kill_exit_code']==-9 and result['resume_exit_code']==0
    assert 4<=result['before_rows']<20 and result['after_rows']==20
    assert result['command_sha256']==canonical_sha256(command)
    owned.verify_drill(tmp_path,result['binding'])
    _,expected=rows()
    actual=owned.journal(tmp_path/'runs/resume/completions.jsonl')[1]
    assert actual==expected
    # Independently produce an uninterrupted worker output.
    baseline=tmp_path/'baseline';baseline.mkdir();(baseline/'rows.json').write_text(json.dumps(expected))
    r,w=os.pipe()
    try:
        p=subprocess.Popen([sys.executable,'-c',WORKER,str(baseline),str(r)],pass_fds=(r,),start_new_session=True,cwd=Path(__file__).resolve().parents[1])
        assert p.wait(timeout=10)==0
    finally: os.close(r);os.close(w)
    assert (baseline/'runs/resume/completions.jsonl').read_bytes()==(tmp_path/'runs/resume/completions.jsonl').read_bytes()
    descendants=[json.loads(l)['pid'] for l in (tmp_path/'descendants.jsonl').read_text().splitlines()]
    assert len(descendants)==2
    assert all(not_running(pid) for pid in descendants)
    with pytest.raises(HarnessError,match='QUAL_CONSUMED'):
        owned.drill(command,tmp_path,result['binding'],timeout=2)
    assert read_json(tmp_path/'resume.claim.json')['requests_reserved']==40
    with pytest.raises(HarnessError,match='QUAL_EVIDENCE'):
        owned.verify_drill(tmp_path,{'source':'drift'})
    with (tmp_path/'runs/resume/completions.jsonl').open('ab') as s:
        s.write((tmp_path/'resume.before.jsonl').read_bytes())
    with pytest.raises(HarnessError,match='QUAL_JOURNAL'):
        owned.verify_drill(tmp_path,result['binding'])


def test_unknown_outcome_claim_is_never_replayed(tmp_path):
    r,w=os.pipe()
    command=[sys.executable,'-c','import sys;sys.exit(7)']
    try:
        with pytest.raises(HarnessError,match='QUAL_NOT_INTERRUPTED'):
            owned.drill(command,tmp_path,{'source':'s'},pass_fds=(r,),timeout=2)
    finally: os.close(r);os.close(w)
    assert read_json(tmp_path/'resume.claim.json')['requests_reserved']==40
    assert not (tmp_path/'resume.observed.json').exists()
    with pytest.raises(FileExistsError):
        owned.drill(command,tmp_path,{'source':'s'},timeout=2)


def test_single_writer_actual_lock(tmp_path):
    with owned.writer(tmp_path/'lock'):
        with pytest.raises(HarnessError,match='ACTIVE_WRITER'):
            with owned.writer(tmp_path/'lock'): pass


def test_guard_parent_eof_terminates_worker_and_descendant(tmp_path):
    _,completed=rows();(tmp_path/'rows.json').write_text(json.dumps(completed))
    script=tmp_path/'worker.py';script.write_text(WORKER)
    r,w=os.pipe()
    p=subprocess.Popen([sys.executable,'-c',WORKER,str(tmp_path),str(r)],pass_fds=(r,),start_new_session=True,cwd=Path(__file__).resolve().parents[1])
    try:
        deadline=time.monotonic()+5
        while not (tmp_path/'descendants.jsonl').exists():
            assert time.monotonic()<deadline;time.sleep(.01)
        os.close(w);w=None
        assert p.wait(timeout=5)==-9
        pid=json.loads((tmp_path/'descendants.jsonl').read_text().splitlines()[0])['pid']
        assert not_running(pid)
    finally:
        os.close(r)
        if w is not None: os.close(w)
        if p.poll() is None: os.killpg(p.pid,9);p.wait()


@pytest.fixture
def prepared(tmp_path,monkeypatch):
    (tmp_path/'synaptic.yaml').write_text('paths: {artifacts: "project://artifacts"}\n')
    layout=Layout(tmp_path);root=layout.local('astra-r2/edited-qualification')
    original,completed=rows();binding={'source':'s','checkpoint':{'all':'hash'},'image':'i'}
    proposal=SimpleNamespace(raw={'evaluation':{'decode':{'max_new_tokens':128,'temperature':0,'n_samples':1}}})
    runtime={'evaluation':{'batch_size':1}}
    monkeypatch.setattr(qual,'context',lambda *a:(runtime,binding))
    monkeypatch.setattr(qual,'_arguments',lambda p,r,l,m,n:['fixed',n])
    root.mkdir(parents=True)
    roster_ref=layout.ref('astra-r2/frozen-roster.jsonl')
    write_jsonl(layout.to_local(roster_ref),original)
    source_sha=sha256_file(layout.to_local(roster_ref))
    owned.create(commitments.public_path(layout,'astra_patch_freeze.json'),{'artifacts':{roster_ref:source_sha}})
    owned.create(root/'manifest.json',{'binding':binding,'rows_sha256':canonical_sha256(original),
                 'rows_ref':roster_ref,'rows_source_sha256':source_sha})
    write_jsonl(root/'original.jsonl',original)
    write_jsonl(root/'permuted.jsonl',sorted(original,key=lambda r:hashlib.sha256(('20261103:'+r['id']).encode()).hexdigest()))
    calls=[]
    def gpu(_root,_layout,operation,args,**kwargs):
        assert operation=='batch-generate';calls.append(args)
        write_jsonl(root/'runs'/args[1]/'completions.jsonl',completed)
    monkeypatch.setattr(run,'_gpu',gpu)
    return layout,root,proposal,runtime,binding,calls


def test_full_verifier_recomputes_outputs_then_immutable_public_manifest(prepared,monkeypatch,tmp_path):
    layout,root,proposal,runtime,binding,calls=prepared
    for name in RUNS[:-1]:
        qual.execute(proposal,layout,tmp_path,tmp_path,name,ack=True)
    live(root,binding)
    report=qual.verify(proposal,layout,tmp_path,tmp_path)
    assert len(calls)==4 and report['requests_reserved']==120 and report['scored'] is False
    assert report['comparison']['runs']==5
    assert qual.verify(proposal,layout,tmp_path,tmp_path)==report
    public=commitments.public_path(layout,'astra_edited_qualification.manifest.json')
    assert read_json(public)['receipt_sha256']==sha256_file(commitments.public_path(layout,'astra_edited_qualification.json'))
    monkeypatch.setattr(admission,'qualification_binding',lambda *a:binding)
    frozen=read_json(commitments.public_path(layout,'astra_patch_freeze.json'))
    authenticated=[]
    monkeypatch.setattr(commitments,'require_git',lambda l,n,r:authenticated.append(n))
    assert admission.require_qualification(proposal,layout,tmp_path,runtime,frozen)
    assert authenticated==['astra_edited_qualification.json','astra_edited_qualification.manifest.json']
    with pytest.raises(HarnessError,match='QUAL_CONSUMED'):
        qual.execute(proposal,layout,tmp_path,tmp_path,'original_a',ack=True)
    (root/'resume.observed.json').unlink()
    with pytest.raises(FileNotFoundError):
        qual.verify(proposal,layout,tmp_path,tmp_path)
    with pytest.raises(FileNotFoundError):
        admission.require_qualification(proposal,layout,tmp_path,runtime,frozen)


def test_drift_and_fake_pass_do_not_admit(prepared,tmp_path):
    layout,root,proposal,runtime,binding,calls=prepared
    owned.create(commitments.public_path(layout,'astra_edited_qualification.json'),{'passed':True,'owned_sigkill_resume':True})
    with pytest.raises(FileNotFoundError): qual.verify(proposal,layout,tmp_path,tmp_path)
    binding['source']='changed'
    with pytest.raises(HarnessError,match='QUAL_DRIFT'):
        qual.execute(proposal,layout,tmp_path,tmp_path,'original_a',ack=True)
    assert not calls and not (root/'original_a.claim.json').exists()


def test_worker_retains_public_guard_and_lock(tmp_path,monkeypatch):
    monkeypatch.setattr(owned,'guard',lambda fd:None)
    monkeypatch.setattr(qual,'_inputs',lambda *a:({}, {'source':'s'}, tmp_path,None))
    monkeypatch.setattr(qual,'_arguments',lambda *a:['fixed'])
    monkeypatch.setattr(run,'require_signed',lambda *a,**k:{})
    monkeypatch.setenv('EHR_RUNTIME_IMAGE_ID','synthetic')
    observed=[]
    class CLI:
        def run(self,operation,args,**kwargs):
            assert kwargs['guard_parent'] is True
            assert len(kwargs['pass_fds'])==1
            os.fstat(kwargs['pass_fds'][0]);observed.append(operation)
    monkeypatch.setattr(run,'_engine',lambda *a:CLI())
    (tmp_path/'synaptic.yaml').write_text('paths: {artifacts: "project://artifacts"}\n')
    token=os.urandom(32)
    owned.create(tmp_path/'resume.claim.json',{'binding':{'source':'s'},'requests_reserved':40,
                 'owner_sha256':hashlib.sha256(token).hexdigest()})
    r,w=os.pipe()
    try:
        os.write(w,token)
        qual.worker(None,Layout(tmp_path),tmp_path,tmp_path,r)
    finally: os.close(r);os.close(w)
    assert observed==['batch-generate']

@pytest.mark.parametrize('change', ['token','finish','schema','prompt','duplicate','missing','ceiling'])
def test_actual_verifier_refuses_output_changes(prepared,tmp_path,change):
    layout,root,proposal,runtime,binding,calls=prepared
    for name in RUNS[:-1]: qual.execute(proposal,layout,tmp_path,tmp_path,name,ack=True)
    live(root,binding)
    output=root/'runs/original_b/completions.jsonl'
    data=owned.journal(output)[1]
    if change=='token': data[0]['completion_token_ids']=[999]
    elif change=='finish': data[0]['finish_reason']='length'
    elif change=='schema': data[0]['completion_text']='{}'
    elif change=='prompt': data[0]['prompt_token_len']=3
    elif change=='duplicate': data[-1]=data[0]
    elif change=='missing': data.pop()
    else: data[0]['completion_token_ids']=[1]*129
    write_jsonl(output,data)
    # Even changing private observation hashes cannot bypass the comparisons.
    observed=read_json(root/'original_b.observed.json')
    observed['output_sha256']=sha256_file(output)
    (root/'original_b.observed.json').write_text(json.dumps(observed))
    with pytest.raises(HarnessError): qual.verify(proposal,layout,tmp_path,tmp_path)
    assert not commitments.public_path(layout,'astra_edited_qualification.json').exists()


def test_signed_qualified_false_stays_immutable(tmp_path,monkeypatch):
    import yaml
    runtime={'evaluation':{'qualified':False,'image_digest':'synthetic'}}
    for name in ('astra_r2.yaml','runtime/r2_host_binding.json','runtime/preparation.yaml'):
        p=tmp_path/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('{}')
    (tmp_path/'astra_runtime.yaml').write_text(yaml.safe_dump(runtime))
    names=['astra_r2.yaml','astra_runtime.yaml','runtime/r2_host_binding.json','runtime/preparation.yaml']
    manifest={'status':'signed','instrument':{'configs':names,'modules':[],
              'pins':{n:sha256_file(tmp_path/n) for n in names}}}
    (tmp_path/'experiment.yaml').write_text(yaml.safe_dump(manifest))
    monkeypatch.setattr(admission,'sources',lambda *a:{})
    monkeypatch.setattr(admission,'check_host',lambda *a:{})
    monkeypatch.setattr(run,'find_project_root',lambda *a:tmp_path)
    monkeypatch.setenv('EHR_RUNTIME_IMAGE_ID','synthetic')
    before=(tmp_path/'astra_runtime.yaml').read_bytes()
    assert run.require_signed(tmp_path,runtime_role='evaluation')['evaluation']['qualified'] is False
    assert (tmp_path/'astra_runtime.yaml').read_bytes()==before


def test_worker_rejects_wrong_live_owner_before_gpu(tmp_path,monkeypatch):
    monkeypatch.setattr(owned,"guard",lambda fd:None)
    monkeypatch.setattr(qual,'_inputs',lambda *a:({}, {'s':1},tmp_path,None))
    owned.create(tmp_path/'resume.claim.json',{'binding':{'s':1},'requests_reserved':40,
                 'owner_sha256':hashlib.sha256(b'x'*32).hexdigest()})
    monkeypatch.setattr(run,'_gpu',lambda *a,**k:pytest.fail('must not launch'))
    r,w=os.pipe()
    try:
        os.write(w,b'y'*32)
        with pytest.raises(HarnessError,match='QUAL_OWNER'):
            qual.worker(None,None,None,None,r)
    finally:os.close(r);os.close(w)


def test_real_execute_resume_branch_builds_only_fixed_worker(prepared,tmp_path,monkeypatch):
    layout,root,proposal,runtime,binding,calls=prepared
    _,completed=rows();(root/'rows.json').write_text(json.dumps(completed))
    script=root/'worker.py';script.write_text(WORKER)
    actual_drill=owned.drill
    seen=[]
    def synthetic_boundary(command,path,selected,**kwargs):
        assert command[1:3]==['-m','r2_runtime.astra_qualification']
        assert command[-3:-1]==['_owned-worker','--guard-fd']
        assert selected==binding
        assert len(kwargs['pass_fds'])==2
        assert len(kwargs['lease'][1])==32
        seen.append(command)
        # Substitute only the synthetic process body at the process boundary.
        # Actual controller Popen, signals, waits, claims and argv reuse run.
        return actual_drill([sys.executable,'-c',WORKER,str(root),command[-1]],path,selected,
                            pass_fds=kwargs['pass_fds'],lease=kwargs['lease'],timeout=10,cwd=kwargs['cwd'])
    monkeypatch.setattr(owned,'drill',synthetic_boundary)
    result=qual.execute(proposal,layout,tmp_path,tmp_path,'resume',ack=True)
    assert result['requests_reserved']==40 and len(seen)==1 and not calls
    owned.verify_drill(root,binding)
    with pytest.raises(HarnessError,match='QUAL_CONSUMED'):
        qual.execute(proposal,layout,tmp_path,tmp_path,'resume',ack=True)


def test_admission_requires_both_public_commits(prepared,tmp_path,monkeypatch):
    layout,root,proposal,runtime,binding,calls=prepared
    for name in RUNS[:-1]:qual.execute(proposal,layout,tmp_path,tmp_path,name,ack=True)
    live(root,binding);qual.verify(proposal,layout,tmp_path,tmp_path)
    frozen=read_json(commitments.public_path(layout,'astra_patch_freeze.json'))
    monkeypatch.setattr(admission,'qualification_binding',lambda *a:binding)
    def authenticate(l,name,report):
        if name.endswith('.manifest.json'):
            raise HarnessError('PUBLIC_NOT_IN_GIT','public manifest not committed')
    monkeypatch.setattr(commitments,'require_git',authenticate)
    with pytest.raises(HarnessError,match='PUBLIC_NOT_IN_GIT'):
        admission.require_qualification(proposal,layout,tmp_path,runtime,frozen)
