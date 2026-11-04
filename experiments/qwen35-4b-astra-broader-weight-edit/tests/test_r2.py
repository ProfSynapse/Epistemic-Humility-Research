import copy
import json
import math
import subprocess
import sys
from pathlib import Path
import numpy as np
import pytest
from hs20_r2 import astra_r2 as r
from hs20_r2 import frozen as f

@pytest.fixture(scope='module')
def fixture():
    w=.02001953125
    a=.26767/(.09*w*math.sqrt(2560)*32)
    c=(-1.)**np.arange(2560)/math.sqrt(2560)
    t=np.arange(64)-31.5; t/=np.sqrt(np.mean(t*t))
    K=np.zeros((64,9216)); K[:,:1024]=(-1.)**np.arange(1024)+.01*t[:,None]
    U=K.copy(); U[:,:1024]+=a
    W=w*((-1.)**np.arange(2560))[:,None]*((-1.)**np.arange(9216))[None,:]
    prop=r.proposal({'dtype':'bfloat16','repo':'Qwen/Qwen3.5-4B','revision':'851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a','files_sha256':{'model.safetensors':'a'*64}},
                    {'counts':{'confab':64,'known_correct_answered':64}}, {})
    uk,kk=[f'u{i}' for i in range(64)],[f'k{i}' for i in range(64)]
    old=f.select_support(U,K,columns=32,eta_multiplier=1e-6)[0]
    con=r.construct(U,K,c,W,prop,u_keys=uk,k_keys=kk,r1_columns=old)
    return U,K,c,W,prop,uk,kk,old,con


def test_full_matched_feasible_and_arithmetic(fixture,tmp_path):
    U,K,c,W,p,uk,kk,old,con=fixture
    assert con.ideal['passed'], con.ideal
    assert con.alpha==3.152046979449994
    assert con.columns==list(range(1024))
    expected=r.emulate(con,W)
    import torch
    torch.set_num_threads(1)
    # Independent arithmetic implementation: actual torch bf16 storage.
    tw=torch.tensor(W,dtype=torch.bfloat16)
    u=torch.tensor(c,dtype=torch.float32); v=torch.tensor(con.v,dtype=torch.float32)
    product=torch.outer(u,v)*con.alpha
    tw[:,con.columns]=(tw[:,con.columns].float()+product).bfloat16()
    actual=tw.float().numpy().astype(np.float64)
    assert r.bf16_raw_sha256(actual)==r.bf16_raw_sha256(expected)
    from safetensors.torch import save_file,load_file
    file=tmp_path/'synthetic.safetensors'
    save_file({r.TENSOR:tw,'untouched':torch.arange(4,dtype=torch.bfloat16)},str(file))
    loaded=load_file(str(file))
    assert torch.equal(loaded['untouched'],torch.arange(4,dtype=torch.bfloat16))
    report=r.audit_realized(con,p,U,K,W,loaded[r.TENSOR].float().numpy())
    assert report['passed'],report['failures']
    assert report['metrics']['entries_changed']==2621440
    assert report['metrics']['broad_columns']==1024
    assert report['metrics']['U_mean_sigma']==pytest.approx(1.84107143,abs=1e-7)
    assert report['metrics']['error_rms_sigma']==pytest.approx(.11370645,abs=1e-7)
    assert report['metrics']['K_rms_sigma']==pytest.approx(.20064915,abs=1e-7)


def test_ties_and_exact_roster_port():
    U=np.ones((64,9216)); K=np.zeros_like(U)
    S,_,_=f.select_support(U,K,columns=1024,eta_multiplier=1e-6)
    assert S==list(range(1024))
    rows=[{'row_key':f'{role}-{i:03}','role':role,'question':f'{role} q{i}'} for role in f.HISTORICAL_ROLES for i in range(70)]
    rows += [{'row_key':'zz','role':'confab','question':'CONFAB   Q0'}]
    kw={'seed':20261103,'counts':dict.fromkeys(f.HISTORICAL_ROLES,64)}
    a=f.select_roster(rows,{'test':['Confab q1']},**kw)
    assert a==f.select_roster(list(reversed(rows)),{'test':['Confab q1']},**kw)
    assert 'zz' not in a['keys']['confab'] and 'confab-001' not in a['keys']['confab']


@pytest.mark.parametrize('realized',[False,True])
def test_every_upper_guard_boundary(realized):
    limits=r.REALIZED if realized else r.IDEAL
    m={k:v for k,v in limits.items()}; m['U_mean_sigma']=2.
    if realized: m['broad_columns']=768
    assert r.check_guards(m,realized=realized)['passed']
    for key,limit in limits.items():
        bad={**m,key:np.nextafter(float(limit),math.inf)}
        assert key in r.check_guards(bad,realized=realized)['failures']
        bad[key]=math.nan
        assert key in r.check_guards(bad,realized=realized)['failures']

@pytest.mark.parametrize('realized',[False,True])
def test_every_lower_guard_and_mean_boundary(realized):
    limits=r.REALIZED if realized else r.IDEAL
    m={k:0 for k in limits}; m.update(U_mean_sigma=2.)
    if realized: m.update(entries_changed=1048576,broad_columns=768)
    lo,hi=(1.8,2.2) if realized else (2-1e-5,2+1e-5)
    for bound in [lo,hi]:
        assert r.check_guards({**m,'U_mean_sigma':bound},realized=realized)['passed']
    for bound in [np.nextafter(lo,-math.inf),np.nextafter(hi,math.inf)]:
        assert 'U_mean_sigma' in r.check_guards({**m,'U_mean_sigma':bound},realized=realized)['failures']
    if realized:
        for key in ['entries_changed','broad_columns']:
            assert key+'_minimum' in r.check_guards({**m,key:m[key]-1},realized=True)['failures']


@pytest.mark.parametrize('case',['collinear','zero_u','zero_eta','nan','wrong_shape','wrong_c','dup','overlap','old_support','known_variance','zero_column'])
def test_constructor_refusals(fixture,case):
    U,K,c,W,p,uk,kk,old,_=fixture
    U=U.copy(); K=K.copy(); c=c.copy(); uk=uk.copy(); kk=kk.copy()
    if case=='collinear': U=K*2
    if case=='zero_u': U[:]=0
    if case=='zero_eta': U[:]=0; K[:]=0
    if case=='nan': U[0,0]=math.nan
    if case=='wrong_shape': U=U[:,:-1]
    if case=='wrong_c': c*=2
    if case=='dup': uk[0]=uk[1]
    if case=='overlap': kk[0]=uk[0]
    if case=='old_support': old=list(range(32,64))
    if case=='known_variance':
        t=np.arange(64)-31.5; t/=np.sqrt(np.mean(t*t))
        K[:,:1024]+=.04*t[:,None]; U[:,:1024]+=.04*t[:,None]
        old=f.select_support(U,K,columns=32,eta_multiplier=1e-6)[0]
    if case=='zero_column': W=W.copy(); W[:,0]=0
    if case in ['known_variance']:
        con=r.construct(U,K,c,W,p,u_keys=uk,k_keys=kk,r1_columns=old)
        assert not con.ideal['passed'] and 'K_rms_sigma' in con.ideal['failures']
        assert con.alpha==2*r.SIGMA
        with pytest.raises(r.HarnessError,match='IDEAL_REFUSAL'): r.emulate(con,W)
    else:
        with pytest.raises(r.HarnessError): r.construct(U,K,c,W,p,u_keys=uk,k_keys=kk,r1_columns=old)


def test_zero_k_branch(fixture):
    U,K,c,W,p,uk,kk,old,_=fixture
    K=np.zeros_like(K); U=np.zeros_like(U); U[:,:1024]=1.
    con=r.construct(U,K,c,W,p,u_keys=uk,k_keys=kk,r1_columns=list(range(32)))
    assert con.ideal['passed']
    assert np.all(con.v==1/1024)

@pytest.mark.parametrize('case',['noop','off_support','shortfall','coverage','receipt','base'])
def test_realized_refusals(fixture,case):
    U,K,c,W,p,_,_,_,con=fixture
    E=r.emulate(con,W)
    receipt=None
    if case=='noop': E=W
    if case=='off_support': E[0,2000]=W[0,2000]*2
    if case=='shortfall': E=W+0 # deliberately no fallback arithmetic
    if case=='coverage': E[:,600:1024]=W[:,600:1024]
    if case=='receipt': receipt={'name':r.TENSOR,'entries_changed':1,'delta_frobenius':1.}
    if case=='base':
        W=W.copy(); W[0,0]*=-1
        with pytest.raises(r.HarnessError,match='BASE_HASH'): r.audit_realized(con,p,U,K,W,E)
        return
    report=r.audit_realized(con,p,U,K,W,E,receipt_tensor=receipt)
    assert not report['passed'] and report['terminal']
    expected={'noop':'entries_changed_minimum','off_support':'OFF_SUPPORT','shortfall':'U_mean_sigma','coverage':'broad_columns_minimum','receipt':'RECEIPT_MISMATCH'}[case]
    assert expected in report['failures']


def test_no_min_cap_and_wrong_site(fixture,tmp_path):
    U,K,c,W,p,_,_,_,con=fixture
    with pytest.raises(r.HarnessError,match='R1_SCALE_CAP'):
        r.proposal(p.raw['model'],p.raw['development'],{'full_norm_scale_margin':.009})
    for key,value in [('columns',32),('nominal_sigma',1),('decoder_block',18),('shape',[32,32]),('sigma_c',0)]:
        with pytest.raises(r.HarnessError): r.proposal(p.raw['model'],p.raw['development'],{key:value})
    tensor={'name':r.TENSOR,'shape':list(r.SHAPE),'dtype':'bfloat16','sha256':con.base_sha256}
    binding={'files_sha256':p.raw['model']['files_sha256'],'index_sha256':'b'*64}
    kw=dict(out_dir=tmp_path/'patch',checkpoint_ref='artifact://base',payload_ref='artifact://patch/payload.safetensors',export_ref='artifact://edited')
    emitted=r.emit_patch(p,con,tensor,binding,**kw)
    assert emitted['spec']['operations'][0]['scale']==2*r.SIGMA
    assert len(emitted['spec']['operations'][0]['cols'])==1024
    from safetensors.numpy import load_file
    arrays=load_file(str(tmp_path/'patch/payload.safetensors'))
    assert np.array_equal(arrays['v'],con.v.astype(np.float32))
    with pytest.raises(r.HarnessError,match='OUTPUT_EXISTS'): r.emit_patch(p,con,tensor,binding,**kw)
    with pytest.raises(r.HarnessError,match='TENSOR_BINDING'): r.emit_patch(p,con,{**tensor,'name':'wrong'},binding,**kw)


def test_exact_bf16_validation():
    with pytest.raises(r.HarnessError,match='NOT_BF16'): r.bf16_bits(np.array([[1.+2**-40]]))
    with pytest.raises(r.HarnessError): r.bf16_bits(np.array([[math.inf]]))


def test_checkpoint_inventory_and_sidecar_guards(fixture,tmp_path):
    import torch
    from safetensors.torch import save_file
    U,K,c,W,p,_,_,_,con=fixture
    base,edited=tmp_path/'base',tmp_path/'edited'; base.mkdir(); edited.mkdir()
    E=r.emulate(con,W)
    for root,target in [(base,W),(edited,E)]:
        save_file({r.TENSOR:torch.tensor(target,dtype=torch.bfloat16),'other':torch.arange(3,dtype=torch.bfloat16)},str(root/'model.safetensors'))
        (root/'config.json').write_text('{"synthetic":true}')
        (root/'model.safetensors.index.json').write_text(json.dumps({'weight_map':{r.TENSOR:'model.safetensors','other':'model.safetensors'}}))
        (root/'tokenizer_config.json').write_text('{"chat_template":"synthetic"}')
    model={**p.raw['model'],'files_sha256':{'model.safetensors':f.sha256_file(base/'model.safetensors')}}
    p=r.proposal(model,p.raw['development'],{})
    manifest={'tensors':[{'name':r.TENSOR,'after_sha256':r.bf16_raw_sha256(E)}]}
    dn=float(np.linalg.norm(E-W)); receipt={'name':r.TENSOR,'entries_changed':2621440,'delta_frobenius':dn}
    report=r.audit_checkpoint(base,edited,con,p,U,K,receipt_tensor=receipt,export_manifest=manifest)
    assert report['passed'] and report['checkpoint_reloaded']
    (edited/'tokenizer_config.json').write_text('{}')
    report=r.audit_checkpoint(base,edited,con,p,U,K,receipt_tensor=receipt,export_manifest=manifest)
    assert 'SIDECARS' in report['failures']


def test_cli_real_prepare_audit(fixture,tmp_path):
    U,K,c,W,p,uk,kk,old,con=fixture
    # Actual CLI, full arrays and no models, exported once via a public-format payload.
    zpath=tmp_path/'arrays.npz'
    from threadpoolctl import threadpool_limits
    with threadpool_limits(limits=1):
        outputs=np.concatenate([U,K]) @ W.T
    np.savez(zpath,U=U,K=K,c=c,W=W,outputs=outputs,edited=r.emulate(con,W))
    h={'model':p.raw['model'],'development':p.raw['development'],'patch':{},
       'bias_present':False,'u_keys':uk,'k_keys':kk,'r1_columns':old,'arrays_sha256':f.sha256_file(zpath),
       'tensor':{'name':r.TENSOR,'dtype':'bfloat16','shape':list(r.SHAPE),'sha256':con.base_sha256},
       'binding':{'files_sha256':p.raw['model']['files_sha256'],'index_sha256':'b'*64},
       'checkpoint_ref':'artifact://base','payload_ref':'artifact://output/patch/payload.safetensors','export_ref':'artifact://edited'}
    hp=tmp_path/'handoff.json'; hp.write_text(json.dumps(h))
    exp=Path(__file__).resolve().parents[1]
    for command in ['prepare','audit']:
        cmd=[sys.executable,'-m','hs20_r2.astra_r2',command,'--handoff',str(hp),'--arrays',str(zpath),'--out',str(tmp_path/command)]
        if command=='audit':
            cmd += ['--prepare-report',str(tmp_path/'prepare/report.json'),'--spec',str(tmp_path/'prepare/patch/spec.yaml'),'--payload',str(tmp_path/'prepare/patch/payload.safetensors')]
        completed=subprocess.run(cmd,cwd=exp,capture_output=True,text=True)
        assert completed.returncode==0,completed.stdout+completed.stderr
        report=json.loads((tmp_path/command/'report.json').read_text())
        assert report['construction']['alpha']==2*r.SIGMA
        repeated=subprocess.run(cmd,cwd=exp,capture_output=True,text=True)
        assert repeated.returncode==2 and 'OUTPUT_EXISTS' in repeated.stdout
    # A valid reordered roster cannot rebind an existing construction.
    h['u_keys'][0],h['u_keys'][1]=h['u_keys'][1],h['u_keys'][0]
    hp.write_text(json.dumps(h))
    cmd[cmd.index('--out')+1]=str(tmp_path/'tampered-roster')
    refused=subprocess.run(cmd,cwd=exp,capture_output=True,text=True)
    assert refused.returncode==2 and 'PREPARE_BINDING' in refused.stdout
    h['u_keys'][0],h['u_keys'][1]=h['u_keys'][1],h['u_keys'][0]
    hp.write_text(json.dumps(h))
    spec=tmp_path/'prepare/patch/spec.yaml'
    spec.write_bytes(spec.read_bytes()+b'\n# changed bytes\n')
    cmd[cmd.index('--out')+1]=str(tmp_path/'tampered-spec')
    refused=subprocess.run(cmd,cwd=exp,capture_output=True,text=True)
    assert refused.returncode==2 and 'PREPARE_BINDING' in refused.stdout


def test_frozen_origin_integrity():
    import ast,hashlib
    origins=json.loads((Path(r.__file__).parent/'ORIGINS.json').read_text())
    port_source=Path(f.__file__).read_text()
    for key,record in origins.items():
        name=key.split(':')[1]
        port=next(n for n in ast.parse(port_source).body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name==name)
        assert hashlib.sha256(ast.get_source_segment(port_source,port).encode()).hexdigest()==record['function_sha256']
        original=Path(record['origin'])
        if original.exists():
            assert hashlib.sha256(original.read_bytes()).hexdigest()==record['source_sha256']



def test_linear_consistency_boundaries_and_bias():
    U=np.zeros((64,9216)); K=U.copy(); W=np.zeros(r.SHAPE); outputs=np.zeros((128,2560))
    outputs[0,0]=1e-6
    assert r.linear_consistency(U,K,outputs,W,bias_present=False)['passed']
    outputs[0,0]=np.nextafter(1e-6,math.inf)
    with pytest.raises(r.HarnessError,match='CAPTURE_LINEAR'): r.linear_consistency(U,K,outputs,W,bias_present=False)
    with pytest.raises(r.HarnessError,match='BIAS'): r.linear_consistency(U,K,outputs,W,bias_present=True)
    outputs[0,0]=math.nan
    with pytest.raises(r.HarnessError): r.linear_consistency(U,K,outputs,W,bias_present=False)


def test_minimum_norm_key_independent_solution(fixture):
    U,K,c,W,p,_,_,_,con=fixture
    A=np.stack([U.mean(axis=0)[con.columns],K.mean(axis=0)[con.columns]])
    independent=np.linalg.lstsq(A,np.array([1.,0.]),rcond=None)[0]
    assert np.allclose(independent,con.v,rtol=1e-11,atol=1e-13)
    assert np.linalg.norm(con.v)==pytest.approx(.340578083730131,abs=1e-13)


def test_production_yaml_matches_closed_numerics(fixture):
    import yaml
    path=Path(__file__).resolve().parents[1]/'astra_r2.yaml'
    raw=yaml.safe_load(path.read_text())
    p=r.proposal(raw['model'],raw['development'],raw['patch'])
    assert p.patch['alpha']==2*r.SIGMA
    for table,key in [('ideal_guards','maximum_known_rms_sigma'),
                      ('realized_guards','minimum_modified_entries')]:
        changed=copy.deepcopy(raw['patch']); changed[table][key]*=1.01
        with pytest.raises(r.HarnessError,match='conflicting frozen field'):
            r.proposal(raw['model'],raw['development'],changed)


def test_emulator_preserves_equal_value_signed_zero_bytes(fixture):
    from dataclasses import replace
    import torch
    _,_,_,W,_,_,_,_,con=fixture
    W=W.copy(); W[0,0]=-0.
    v=con.v.copy(); v[0]=0.
    con=replace(con,v=v,base_sha256=r.bf16_raw_sha256(W))
    predicted=r.emulate(con,W)
    old=torch.tensor(W[:,con.columns],dtype=torch.bfloat16)
    new=(old.float()+float(con.alpha)*torch.outer(torch.tensor(con.c,dtype=torch.float32),
                                               torch.tensor(v,dtype=torch.float32))).bfloat16()
    new=torch.where(new!=old,new,old)
    expected=W.copy(); expected[:,con.columns]=new.float().numpy()
    assert r.bf16_raw_sha256(predicted)==r.bf16_raw_sha256(expected)
    assert np.signbit(predicted[0,0])
