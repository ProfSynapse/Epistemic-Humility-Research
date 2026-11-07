"""Synthetic provenance and comparator tests; no target feasibility claim."""
import copy
import json
from pathlib import Path
import numpy as np
import pytest
from hs20_r3 import reference
from hs20_r3 import astra_r3 as r
from test_r3 import fixture
from test_preparation_wiring_931bfa33 import wiring,execute,put
from r3_runtime import preparation as p,astra_run as run
from r3_runtime.util import HarnessError,sha256_file
from r3_runtime.checkpoint_audit import audit as ORIGINAL_CHECKPOINT_AUDIT


def test_budget_only_exact_edges():
    def metrics(realized=False):
        d=dict(r.REALIZED if realized else r.IDEAL);d['U_mean_sigma']=2.
        if realized:d['broad_columns']=768
        return d
    assert r.IDEAL['maximum_column_relative_l2']==.46
    assert r.IDEAL['K_rms_sigma']==.45
    for realized,cap in [(False,.46),(True,.50)]:
        d=metrics(realized);d['maximum_column_relative_l2']=cap
        assert r.check_guards(d,realized=realized)['passed']
        d['maximum_column_relative_l2']=np.nextafter(cap,np.inf)
        assert 'maximum_column_relative_l2' in r.check_guards(d,realized=realized)['failures']
    d=metrics();d['maximum_column_relative_l2']=.45768700324076517
    assert r.check_guards(d,realized=False)['passed']
    assert d['maximum_column_relative_l2']>.45
    d['K_rms_sigma']=np.nextafter(.45,np.inf)
    assert 'K_rms_sigma' in r.check_guards(d,realized=False)['failures']


def test_frozen_r2_numerical_parity(fixture):
    """Use actual closed R2 code read-only, never a reimplemented reference."""
    import importlib.util,sys,os,hashlib
    source=Path(os.environ.get('EHR_R2_REFERENCE_DIR','/home/profsynapse/Code/.worktrees/Epistemic-Humility-Research/astra-broader-weight-edit/experiments/qwen35-4b-astra-broader-weight-edit'))
    # The parent supplies the frozen source in the pinned image if needed.
    assert source.is_dir(),'Provide EHR_R2_REFERENCE_DIR with the closed R2 numerical source'
    origins=json.loads((Path(r.__file__).parent/'R2_ORIGINS.json').read_text())
    for name in ('astra_r2.py','frozen.py'):
        assert hashlib.sha256((source/'hs20_r2'/name).read_bytes()).hexdigest()==origins['sources'][name]['sha256']
    spec=importlib.util.spec_from_file_location('frozen_r2_test',source/'hs20_r2/__init__.py',submodule_search_locations=[str(source/'hs20_r2')])
    mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod)
    import importlib
    old=importlib.import_module('frozen_r2_test.astra_r2')
    U,K,c,W,prop,uk,kk,cols,con=fixture
    prior=old.construct(U,K,c,W,old.proposal(prop.raw['model'],prop.raw['development'],{}),u_keys=uk,k_keys=kk,r1_columns=cols)
    for key in ('columns','c','v','alpha','shape','base_sha256'):
        assert reference.identity({'construction':con.report(),'inputs_digest':'x','roster_digest':'y'})['construction'][key]==prior.report()[key]
    assert old.f.payload_bytes(prior)==r.f.payload_bytes(con)
    assert old.bf16_raw_sha256(old.emulate(prior,W))==r.bf16_raw_sha256(r.emulate(con,W))
    d=dict(r.IDEAL,U_mean_sigma=2.,maximum_column_relative_l2=.45768700324076517)
    assert 'maximum_column_relative_l2' in old.check_guards(d,realized=False)['failures']
    assert r.check_guards(d,realized=False)['passed']


def ref_paths(w):
    ref=w.config['reference_proposal']
    return ref,{k:w.layout.project_local(ref[k]) for k in ('report','origin')}

@pytest.mark.parametrize('fault',['missing','hash','origin','columns','c','v','alpha','shape','base_sha256','inputs_digest','roster_digest','symlink','escape'])
def test_reference_refuses_before_effects(wiring,fault):
    w=wiring;ref,paths=ref_paths(w)
    if fault=='missing':paths['report'].unlink()
    elif fault=='hash':ref['report_sha256']='0'*64
    elif fault=='origin':
        doc=json.loads(paths['origin'].read_text());doc['source_commit']='0'*40
        put(paths['origin'],doc);ref['origin_sha256']=sha256_file(paths['origin'])
    elif fault=='symlink':
        # T7 cannot create symlinks. Exercise actual path admission and
        # reference authentication on tiny synthetic POSIX files instead.
        import tempfile
        from r3_runtime.config import Layout
        with tempfile.TemporaryDirectory(prefix='ehr-r3-reference-') as temp:
            project=Path(temp)
            (project/'synaptic.yaml').write_text('paths: {artifacts: "project://.synaptic/artifacts"}\n')
            actual=project/'actual.json';actual.write_bytes(paths['report'].read_bytes())
            link=project/'report.json';link.symlink_to(actual)
            with pytest.raises(HarnessError,match='PREPARATION_REF'):
                p.resolve(Layout(project),'project://report.json','project')
            with pytest.raises(reference.HarnessError,match='REFERENCE_PROPOSAL'):
                reference.authenticate(link,ref['report_sha256'],paths['origin'],ref['origin_sha256'])
        assert not w.events
        return
    elif fault=='escape':ref['report']='project://../escape'
    else:
        current=json.loads(paths['report'].read_text())
        if fault in current:current[fault]='changed'
        else:current['construction'][fault]='changed'
        with pytest.raises(HarnessError,match='REFERENCE_PROPOSAL'):p.reference_binding(w.config,p.load(w.path,w.layout)[1],current)
        assert not w.events
        return
    w.path.write_text(__import__('yaml').safe_dump(w.config))
    with pytest.raises((HarnessError,OSError)):p.dry_run(w.path,w.layout)
    assert not w.events and not w.layout.local('astra-r3/preparation').exists()

@pytest.mark.parametrize('file',['report','origin'])
def test_reference_drift_refuses_actual_freeze_main(wiring,monkeypatch,file):
    w=wiring;execute(w);ref,paths=ref_paths(w)
    paths[file].write_bytes(paths[file].read_bytes()+b' ')
    monkeypatch.setattr(run.astra_fixed,'load_proposal',lambda *a:w.prop)
    with pytest.raises(HarnessError,match='REFERENCE_PROPOSAL'):
        p.verified_chain(w.prop,w.layout,w.path)
    assert run.main(['--proposal',str(w.exp/'astra_r3.yaml'),'--project-root',str(w.root),'freeze',
        '--base-model',str(w.base),'--edited-model',str(w.layout.local('astra-r3/checkpoints/edited')),
        '--audit-ref',w.config['outputs']['audit'],'--prepare-ref',w.config['outputs']['construction']+'/report.json',
        '--spec-ref',w.config['outputs']['construction']+'/patch/spec.yaml',
        '--payload-ref',w.config['outputs']['construction']+'/patch/payload.safetensors',
        '--qualification-rows-ref',w.config['outputs']['qualification_rows']])==2


def test_old_refusal_is_not_current_verdict(wiring):
    w=wiring;execute(w)
    _,paths=p.load(w.path,w.layout)
    old=json.loads(paths['reference_report'].read_text());new=json.loads((paths['construction']/'report.json').read_text())
    assert old['construction']['ideal']['passed'] is False
    assert new['construction']['ideal']['passed'] is True
    assert new['reference_proposal']==p.reference_binding(w.config,paths,new)

@pytest.mark.parametrize('fault',['columns','c','v','alpha','shape','base_sha256','inputs_digest','roster_digest','missing','hash','origin'])
def test_actual_constructor_main_refuses_before_serialization(tmp_path,monkeypatch,fault):
    """Small synthetic ports isolate reference ordering within the actual CLI."""
    from types import SimpleNamespace
    from hs20_r3 import frozen as f
    con={'columns':[0],'c':[1.],'v':[2.],'alpha':3.,'shape':[2,3],'base_sha256':'a'*64,'ideal':{'passed':True}}
    arrays={k:np.zeros((2,3)) for k in ('U','K','W','outputs')};arrays['c']=np.ones(2)
    zp=tmp_path/'arrays.npz';np.savez(zp,**arrays)
    h={'model':{},'development':{},'patch':{},'arrays_sha256':f.sha256_file(zp),'u_keys':['u'],'k_keys':['k'],'r1_columns':[0]}
    hp=tmp_path/'handoff.json';hp.write_text(json.dumps(h))
    inputs=f.canonical_sha256({key:{'shape':list(arrays[key].shape),'dtype':str(arrays[key].dtype),'sha256':f.sha256_bytes(np.ascontiguousarray(arrays[key]).tobytes())} for key in ('U','K','c','W','outputs')})
    old={'construction':copy.deepcopy(con),'inputs_digest':inputs,'roster_digest':f.canonical_sha256([h['u_keys'],h['k_keys'],h['r1_columns']])}
    old['construction']['ideal']={'passed':False}
    if fault in old:old[fault]='changed'
    elif fault in con:old['construction'][fault]='changed'
    rp=tmp_path/'r2.json';rp.write_text(json.dumps(old));rh=f.sha256_file(rp)
    origin={'schema_version':'ehr-previous-proposal-origin/v1','origin_experiment':'qwen35-4b-astra-broader-weight-edit',
        'origin_path':'astra-r2/construction/report.json','source_commit':reference.SOURCE_COMMIT,
        'outcome_sha256':reference.OUTCOME_SHA256,'report_sha256':rh}
    if fault=='origin':origin['source_commit']='0'*40
    op=tmp_path/'origin.json';op.write_text(json.dumps(origin))
    if fault=='missing':rp.unlink()
    if fault=='hash':rh='0'*64
    monkeypatch.setattr(r,'proposal',lambda *a:SimpleNamespace(sha256='p'))
    monkeypatch.setattr(r,'linear_consistency',lambda *a,**kw:{'passed':True})
    monkeypatch.setattr(r,'construct',lambda *a,**kw:SimpleNamespace(report=lambda:con,ideal={'passed':True}))
    monkeypatch.setattr(r,'emulate',lambda *a:pytest.fail('reference refusal must precede emulation'))
    monkeypatch.setattr(r,'emit_patch',lambda *a,**kw:pytest.fail('reference refusal must precede serialization'))
    assert r.main(['prepare','--handoff',str(hp),'--arrays',str(zp),'--out',str(tmp_path/'out'),
        '--reference-report',str(rp),'--reference-report-sha256',rh,
        '--reference-origin',str(op),'--reference-origin-sha256',f.sha256_file(op)])==2
    assert not (tmp_path/'out').exists()


def test_actual_checkpoint_audit_rechecks_reference_before_readback(wiring,monkeypatch,tmp_path):
    from r3_runtime import checkpoint_audit as audit
    from types import SimpleNamespace
    w=wiring;execute(w);d,paths=p.load(w.path,w.layout)
    hpath=paths['inherited']/'handoff.json';h=json.loads(hpath.read_text())
    h.update(w.prop.raw);h['r1_columns']=[0];put(hpath,h)
    prepared_path=paths['construction']/'report.json';prepared=json.loads(prepared_path.read_text())
    arrays=paths['inherited']/'arrays.npz'
    with np.load(arrays) as z:
        digest=__import__('r3_runtime.util',fromlist=['canonical_sha256']).canonical_sha256({key:{'shape':list(z[key].shape),'dtype':str(z[key].dtype),
            'sha256':r.f.sha256_bytes(np.ascontiguousarray(z[key]).tobytes())} for key in ('U','K','c','W','outputs')})
    roster=__import__('r3_runtime.util',fromlist=['canonical_sha256']).canonical_sha256([h['u_keys'],h['k_keys'],h['r1_columns']])
    prepared.update(proposal_sha256='numeric',inputs_digest=digest,roster_digest=roster)
    put(prepared_path,prepared)
    # Keep all pre-reference bindings valid. A changed factor must fail before
    # any full-checkpoint readback. This calls the actual host audit function.
    impl=SimpleNamespace(proposal=lambda *a:SimpleNamespace(sha256='numeric'),
        linear_consistency=lambda *a,**kw:None,construct=lambda *a,**kw:SimpleNamespace(report=lambda:prepared['construction']),
        f=r.f,audit_checkpoint=lambda *a,**kw:pytest.fail('reference check must precede readback'))
    monkeypatch.setattr(audit,'implementation',lambda:impl)
    with pytest.raises(HarnessError,match='REFERENCE_PROPOSAL'):
        ORIGINAL_CHECKPOINT_AUDIT(w.prop,handoff=hpath,arrays=arrays,prepare_report=prepared_path,
            spec=paths['construction']/'patch/spec.yaml',payload=paths['construction']/'patch/payload.safetensors',
            base_model=w.base,edited_model=paths['edited'],out=tmp_path/'audit.json',
            reference_report=paths['reference_report'],reference_report_sha256=d['reference_proposal']['report_sha256'],
            reference_origin=paths['reference_origin'],reference_origin_sha256=d['reference_proposal']['origin_sha256'])
    assert not (tmp_path/'audit.json').exists()
