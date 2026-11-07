"""CPU orchestration tests. Synthetic ports never load target weights or infer."""
import json
from pathlib import Path
from types import SimpleNamespace
import sys
import numpy as np
import pytest
import yaml
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from r3_runtime import preparation as p, astra_run as run, inherited_inputs as bridge
from r3_runtime import checkpoint_audit, constructor, commitments, astra_fixed
from r3_runtime.config import Layout
from r3_runtime.util import HarnessError, sha256_file, canonical_sha256


def put(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,sort_keys=True)+'\n')
    return sha256_file(path)

@pytest.fixture
def wiring(tmp_path,monkeypatch):
    root=tmp_path/'project'; exp=root/'experiments/study'; exp.mkdir(parents=True)
    (root/'synaptic.yaml').write_text(yaml.safe_dump({'paths':{'artifacts':'project://.synaptic/artifacts'}}))
    layout=Layout(root); bundle=root/'experiments/common/captures/astra-r1/analysis/private_bundle'
    bundle.mkdir(parents=True); (bundle/'capture').mkdir(); put(bundle/'capture/manifest.json',{})
    base=layout.local('shared/base_model'); base.mkdir(parents=True)
    (base/'model.safetensors').write_bytes(b'synthetic checkpoint bytes, never decoded')
    put(base/'config.json',{'synthetic':True})
    layout.local('astra-r3/checkpoints').mkdir(parents=True)
    read_paths={}
    for key in p.READS:
        if key in ('bundle_root','origin','capture_root'): continue
        path=bundle/(key+'.json'); put(path,[{'id':str(i),'question':'synthetic'} for i in range(20)] if key=='qualification_original' else {'synthetic':key})
        # qualification is jsonl, not a JSON array.
        if key=='qualification_original': path.write_text(''.join(json.dumps({'id':str(i),'question':'synthetic'})+'\n' for i in range(20)))
        read_paths[key]=path
    origin={'files':{v.relative_to(bundle).as_posix():sha256_file(v) for v in read_paths.values()},
            'artifacts':{k:{'path':read_paths[k].relative_to(bundle).as_posix()} for k in ('freeze','readiness','roster','request','prepare_report')}}
    origin['artifacts']['capture_manifest']={'path':'capture/manifest.json'}
    origin_path=root/'experiments/common/captures/astra-r1/origin.json'; put(origin_path,origin)
    read_paths.update(bundle_root=bundle,origin=origin_path,capture_root=bundle/'capture')
    config={'schema_version':p.SCHEMA,'reads':{k:'project://'+v.relative_to(root).as_posix() for k,v in read_paths.items()},
            'origin_sha256':sha256_file(origin_path),'listing_sha256':sha256_file(read_paths['listing']),
            'base_checkpoint':layout.ref('shared/base_model'),
            'outputs':{k:layout.ref('astra-r3/'+v) for k,v in p.OUTPUTS.items()}}
    from hs20_r3 import reference
    old={'construction':{'columns':[0], 'c':[1.], 'v':[2.], 'alpha':3., 'shape':[2,3], 'base_sha256':'a'*64, 'ideal':{'passed':False}},
         'inputs_digest':'b'*64,'roster_digest':'c'*64}
    rp=root/'experiments/common/captures/astra-r2-proposal/analysis/report.json';put(rp,old)
    op=rp.parent.parent/'origin.json'
    put(op,{'schema_version':'ehr-previous-proposal-origin/v1','origin_experiment':'qwen35-4b-astra-broader-weight-edit',
        'origin_path':'astra-r2/construction/report.json','source_commit':reference.SOURCE_COMMIT,
        'outcome_sha256':reference.OUTCOME_SHA256,'report_sha256':sha256_file(rp)})
    config['reference_proposal']={'report':'project://'+rp.relative_to(root).as_posix(),'report_sha256':sha256_file(rp),
        'origin':'project://'+op.relative_to(root).as_posix(),'origin_sha256':sha256_file(op)}
    path=exp/'runtime/preparation.yaml'; path.parent.mkdir(); path.write_text(yaml.safe_dump(config))
    raw={'model':{'files_sha256':{'model.safetensors':sha256_file(base/'model.safetensors')}},'development':{},'patch':{}}
    (exp/'astra_r3.yaml').write_text(yaml.safe_dump(raw))
    prop=SimpleNamespace(raw=raw,sha256=canonical_sha256(raw))
    put(exp/'experiment.yaml',{'status':'draft','instrument':{'pins':{'runtime/preparation.yaml':sha256_file(path)}}})
    for mod in (p,run): monkeypatch.setattr(mod,'EXPERIMENT_DIR',exp)
    events=[]
    def signed(*a,**kw): events.append('signed')
    monkeypatch.setattr(run,'require_signed',signed)
    def inherited(a):
        events.append('bridge')
        assert a.out==layout.local('astra-r3/inherited-inputs')
        arrays={k:np.zeros((2,3)) for k in ('U','K','W','outputs')};arrays['c']=np.ones(2)
        h={'numpy_version':np.__version__,'r3_contract':raw,'bridge_sha256':sha256_file(Path(bridge.__file__)),
           'source_sha256':{k:sha256_file(getattr(a,k)) for k in ('config','origin','freeze','readiness','roster','request','prepare_report','fit','selfaware','ambigqa','direction','listing')},
           'origin_files_sha256':origin['files'],'u_keys':['u'],'k_keys':['k']}
        h.update({k:getattr(a,k) for k in ('checkpoint_ref','spec_ref','payload_ref','export_ref')})
        bridge.publish(a.out,arrays,h)
    monkeypatch.setattr(bridge,'prepare',inherited)
    def numerical(argv):
        events.append('construction'); args=dict(zip(argv[1::2],argv[2::2]))
        out=Path(args['--out']); h=json.loads(Path(args['--handoff']).read_text())
        assert out==layout.local('astra-r3/construction')
        (out/'patch').mkdir(parents=True)
        payload=out/'patch/payload.safetensors'; payload.write_bytes(b'synthetic factors')
        spec={'base':{'checkpoint':h['checkpoint_ref']},'payload':{'path':h['payload_ref'],'sha256':sha256_file(payload)},'export':{'output_dir':h['export_ref']}}
        (out/'patch/spec.yaml').write_text(yaml.safe_dump(spec))
        from hs20_r3 import reference
        current=json.loads(rp.read_text());current['construction']['ideal']={'passed':True}
        current['reference_proposal']=reference.verify(current,report=rp,report_sha256=sha256_file(rp),origin=op,origin_sha256=sha256_file(op))
        put(out/'report.json',{**current,'handoff_sha256':sha256_file(Path(args['--handoff'])),'patch':{'spec_sha256':sha256_file(out/'patch/spec.yaml'),'payload_sha256':sha256_file(payload)}})
        return 0
    monkeypatch.setattr(constructor,'implementation',lambda:SimpleNamespace(main=numerical))
    def audit(proposal,**kw):
        events.append('audit'); spec=sha256_file(kw['spec']); payload=sha256_file(kw['payload'])
        result={'reference_proposal':json.loads(Path(kw['prepare_report']).read_text())['reference_proposal'],'passed':True,'checkpoint_reloaded':True,'receipt_checked':True,'proposal_sha256':prop.sha256,
                'handoff_sha256':sha256_file(kw['handoff']),'arrays_sha256':sha256_file(kw['arrays']),
                'spec_sha256':spec,'payload_sha256':payload,'prepare_report_sha256':sha256_file(kw['prepare_report'])}
        put(kw['out'],result)
        return {'passed':True,'audit_sha256':sha256_file(kw['out'])}
    monkeypatch.setattr(checkpoint_audit,'audit',audit)
    class Engine:
        def run(self,operation,args,**kw):
            assert operation=='mechinterp' and args[:3]==['weights-patch','--weights-config',layout.ref('astra-r3/construction/patch/spec.yaml')]
            assert kw['guard_parent'] is True
            stage='export' if '--export' in args else 'validate'; events.append(stage)
            if stage=='export':
                edited=layout.local('astra-r3/checkpoints/edited'); edited.mkdir()
                (edited/'model.safetensors').write_bytes(b'synthetic edited bytes')
                (edited/'config.json').write_bytes((base/'config.json').read_bytes())
                put(edited/'mechinterp-weight-export.manifest.json',{'schema_version':'mechinterp-weight-export/v1',
                    'spec':{'sha256':sha256_file(layout.local('astra-r3/construction/patch/spec.yaml'))},
                    'payload':{'sha256':sha256_file(layout.local('astra-r3/construction/patch/payload.safetensors'))},
                    'totals':{'tensors_modified':1,'noop':False},'output':{'weight_files':{'model.safetensors':{'sha256':sha256_file(edited/'model.safetensors')}}}})
            kw['stdout'].write(json.dumps({'success':True,'data':{'synthetic':stage}}).encode())
    monkeypatch.setattr(run,'_engine',lambda root:Engine())
    return SimpleNamespace(root=root,exp=exp,layout=layout,path=path,config=config,prop=prop,events=events,engine=Engine(),base=base)


def execute(w): return p.prepare(w.prop,w.root,w.layout,w.path,cli=w.engine)

def test_931b_dryrun_real_paths_no_execution(wiring,monkeypatch,capsys):
    w=wiring
    monkeypatch.setattr(run.astra_fixed,'load_proposal',lambda *a:pytest.fail('dryrun loaded constructor'))
    assert run.main(['--project-root',str(w.root),'prepare','--config',str(w.path),'--dry-run'])==0
    result=json.loads(capsys.readouterr().out)
    assert result['resolved']['base_checkpoint']==str(w.base)
    assert result['spec_ref']==w.layout.ref('astra-r3/construction/patch/spec.yaml')
    assert result['payload_ref']==w.layout.ref('astra-r3/construction/patch/payload.safetensors')
    assert not w.events and not w.layout.local('astra-r3/preparation').exists()


def test_931b_unsigned_before_any_effect(wiring,monkeypatch):
    w=wiring; monkeypatch.setattr(run,'require_signed',ORIGINAL_SIGNED)
    with pytest.raises(HarnessError,match='UNSIGNED'): execute(w)
    assert not w.layout.local('astra-r3/preparation').exists() and not w.events

ORIGINAL_SIGNED=run.require_signed


def test_931b_full_prepare_cli_and_freeze(wiring,monkeypatch):
    w=wiring; monkeypatch.setattr(run.astra_fixed,'load_proposal',lambda *a:w.prop)
    assert run.main(['--proposal',str(w.exp/'astra_r3.yaml'),'--project-root',str(w.root),'prepare','--config',str(w.path)])==0
    assert w.events[-5:]==['bridge','construction','validate','export','audit']
    binding,refs=p.verified_chain(w.prop,w.layout,w.path)
    assert binding['origin_sha256']==w.config['origin_sha256']
    assert not any('capture_request' in r or 'capture/manifest' in r for r in refs)
    put(w.layout.local('astra-r3/tokenizer_preflight.json'),{'passed':True})
    put(w.layout.local('astra-r3/materialized.json'),{'synthetic':True})
    put(w.layout.local('astra-r3/inputs/roster.json'),{'keys':{'confab':['u'],'known_correct_answered':['k']}})
    monkeypatch.setattr(astra_fixed,'load_roster',lambda prop,path:json.loads(path.read_text()))
    monkeypatch.setattr(commitments,'public_path',lambda layout,name:w.root/'public'/name)
    monkeypatch.setattr(commitments,'export',lambda layout,name,doc:put(w.root/'public'/name,doc))
    assert run.main(['--proposal',str(w.exp/'astra_r3.yaml'),'--project-root',str(w.root),'freeze',
        '--base-model',str(w.base),'--edited-model',str(w.layout.local('astra-r3/checkpoints/edited')),
        '--audit-ref',w.config['outputs']['audit'],'--prepare-ref',w.config['outputs']['construction']+'/report.json',
        '--spec-ref',w.config['outputs']['construction']+'/patch/spec.yaml',
        '--payload-ref',w.config['outputs']['construction']+'/patch/payload.safetensors',
        '--qualification-rows-ref',w.config['outputs']['qualification_rows']])==0
    d=json.loads((w.root/'public/astra_patch_freeze.json').read_text())
    assert refs.items()<=d['artifacts'].items()
    assert d['preparation_binding']==binding
    with pytest.raises(HarnessError,match='OUTPUT_EXISTS'):execute(w)


@pytest.mark.parametrize('code',[3,2])
def test_931b_constructor_terminal_no_engine(wiring,monkeypatch,code):
    w=wiring; monkeypatch.setattr(constructor,'implementation',lambda:SimpleNamespace(main=lambda argv:code))
    with pytest.raises(HarnessError,match='NUMERICAL_REFUSAL' if code==3 else 'CONSTRUCTION_INPUT'): execute(w)
    terminal=json.loads(w.layout.local('astra-r3/preparation/terminal.json').read_text())
    assert terminal['category']==('numerical_refusal' if code==3 else 'input_or_instrument_error')
    assert 'validate' not in w.events
    with pytest.raises(HarnessError,match='OUTPUT_EXISTS'):execute(w)


def test_931b_partial_export_no_replay(wiring):
    w=wiring
    class Broken:
        def run(self,*a,**kw): kw['stdout'].write(b'{'); raise OSError('synthetic partial')
    with pytest.raises(OSError):p.prepare(w.prop,w.root,w.layout,w.path,cli=Broken())
    assert w.layout.local('astra-r3/preparation/validate.json').read_bytes()==b'{'
    with pytest.raises(HarnessError,match='OUTPUT_EXISTS'):execute(w)


@pytest.mark.parametrize('name',['complete.json','handoff.json','arrays.npz'])
def test_931b_missing_or_modified_bridge_refuses_freeze(wiring,name):
    w=wiring; execute(w); target=w.layout.local('astra-r3/inherited-inputs/'+name)
    if name=='complete.json': target.unlink()
    else: target.write_bytes(target.read_bytes()+b' ')
    with pytest.raises((HarnessError,OSError)):p.verified_chain(w.prop,w.layout,w.path)


@pytest.mark.parametrize('field',['spec','prepare','payload','export_manifest','bridge'])
def test_931b_mismatched_provenance_before_freeze(wiring,field):
    w=wiring;execute(w);_,paths=p.load(w.path,w.layout)
    target=p.chain_files(paths)[field]; target.write_bytes(target.read_bytes()+b' ')
    with pytest.raises(HarnessError):p.verified_chain(w.prop,w.layout,w.path)


@pytest.mark.parametrize('ref',['project://../escape','project:///etc/passwd','artifact://other/a','project://foo/./bar','project://foo\\bar'])
def test_931b_ref_escape(wiring,ref):
    w=wiring;w.config['reads']['fit']=ref;w.path.write_text(yaml.safe_dump(w.config))
    with pytest.raises(HarnessError):p.dry_run(w.path,w.layout)


def test_931b_output_mapping_must_name_actual_emission(wiring):
    w=wiring;w.config['outputs']['construction']=w.layout.ref('astra-r3/patch')
    w.path.write_text(yaml.safe_dump(w.config))
    with pytest.raises(HarnessError,match='PREPARATION_MAPPING'):p.dry_run(w.path,w.layout)


def test_931b_unpinned_config_no_effect(wiring):
    w=wiring; put(w.exp/'experiment.yaml',{'instrument':{'pins':{}}})
    with pytest.raises(HarnessError,match='INSTRUMENT_DRIFT'):execute(w)
    assert not w.layout.local('astra-r3/preparation').exists()


@pytest.mark.parametrize('item',['origin','listing'])
def test_931b_dryrun_rejects_changed_commitment(wiring,item):
    w=wiring; target=w.layout.project_local(w.config['reads'][item])
    target.write_bytes(target.read_bytes()+b' ')
    with pytest.raises(HarnessError):p.dry_run(w.path,w.layout)
    assert not w.events


@pytest.mark.parametrize('item',['complete','handoff','terminal','qualification'])
def test_931b_actual_freeze_refuses_inherited_mismatch(wiring,item):
    w=wiring;execute(w)
    if item=='complete':w.layout.local('astra-r3/inherited-inputs/complete.json').unlink()
    if item=='handoff':
        target=w.layout.local('astra-r3/inherited-inputs/handoff.json');h=json.loads(target.read_text())
        h['source_sha256']['origin']='0'*64;put(target,h)
    if item=='terminal':put(w.layout.local('astra-r3/preparation/terminal.json'),{'terminal':True})
    if item=='qualification':
        target=w.layout.local('astra-r3/inputs/qualification_original.jsonl')
        target.write_text(target.read_text().replace('synthetic','changed'))
    with pytest.raises((HarnessError,OSError)):
        run.freeze(w.prop,w.layout,base_model=w.base,edited_model=w.layout.local('astra-r3/checkpoints/edited'),
            audit_ref=w.config['outputs']['audit'],prepare_ref=w.config['outputs']['construction']+'/report.json',
            spec_ref=w.config['outputs']['construction']+'/patch/spec.yaml',payload_ref=w.config['outputs']['construction']+'/patch/payload.safetensors',
            qualification_rows_ref=w.config['outputs']['qualification_rows'])


def test_931b_degenerate_constructor_is_numerical_refusal(wiring,monkeypatch):
    w=wiring
    def refuse(argv): print(json.dumps({'error':'DEGENERATE','terminal':True}));return 2
    monkeypatch.setattr(constructor,'implementation',lambda:SimpleNamespace(main=refuse))
    with pytest.raises(HarnessError,match='NUMERICAL_REFUSAL'):execute(w)
    assert json.loads(w.layout.local('astra-r3/preparation/terminal.json').read_text())['category']=='numerical_refusal'
