"""Config-first CPU orchestration. No capture, inference, retry or dose selection.

The parent signs runtime/preparation.yaml with the whole instrument closure.
Dry-run reads metadata and resolves actual mounts only; it never loads weights.
"""
from __future__ import annotations
import contextlib
import io
import json
from pathlib import Path, PurePosixPath
from types import SimpleNamespace
import yaml
from .util import HarnessError, read_json, sha256_file, canonical_sha256
from .astra_fixed import _create_only, _json_bytes
from .config import EXPERIMENT_DIR

SCHEMA = 'ehr-astra-r3-preparation/v1'
READS = ('bundle_root','origin','capture_root','freeze','readiness','roster','request',
         'prepare_report','fit','selfaware','ambigqa','direction','listing','qualification_original')
OUTPUTS = {'inherited':'inherited-inputs', 'construction':'construction',
           'edited':'checkpoints/edited', 'qualification_rows':'inputs/qualification_original.jsonl',
           'audit':'checkpoint_audit.json', 'phases':'preparation'}

def require(ok, code='PREPARATION_BINDING'):
    if not ok: raise HarnessError(code, 'preparation verification refused')

def resolve(layout, ref, scheme):
    require(isinstance(ref,str) and ref.startswith(scheme+'://'), 'PREPARATION_REF')
    tail=ref[len(scheme)+3:]
    require(tail and '\\' not in tail and not any(ord(c)<32 for c in tail), 'PREPARATION_REF')
    p=PurePosixPath(tail)
    require(not p.is_absolute() and all(x not in ('','.','..') for x in tail.split('/')), 'PREPARATION_REF')
    if scheme=='project':
        raw=layout.project_root/Path(tail)
        require(not any(x.is_symlink() for x in (raw,*raw.parents)),'PREPARATION_REF')
    return layout.project_local(ref) if scheme=='project' else layout.to_local(ref)

def check_reference(ref, paths, current=None):
    from hs20_r3 import reference as r
    try:
        args=dict(report=paths['report'],report_sha256=ref['report_sha256'],origin=paths['origin'],origin_sha256=ref['origin_sha256'])
        if current is None:
            doc=r.authenticate(**args)
            return {**{k:ref[k] for k in ('report_sha256','origin_sha256')},'identity_sha256':canonical_sha256(r.identity(doc))}
        return r.verify(current,**args)
    except (r.HarnessError,OSError,ValueError,KeyError,TypeError) as exc:
        raise HarnessError('REFERENCE_PROPOSAL','instrument-invalid treatment reference') from exc

def reference_binding(d,p,current=None):
    return check_reference(d['reference_proposal'],{k:p['reference_'+k] for k in ('report','origin')},current)

def load(path, layout):
    path=Path(path)
    require(path.resolve()==(EXPERIMENT_DIR/'runtime/preparation.yaml').resolve(), 'PREPARATION_CONFIG')
    d=yaml.safe_load(path.read_bytes())
    require(set(d)=={'schema_version','reads','base_checkpoint','outputs','origin_sha256','listing_sha256','reference_proposal'})
    require(d['schema_version']==SCHEMA and set(d['reads'])==set(READS) and set(d['outputs'])==set(OUTPUTS))
    ref=d['reference_proposal']
    require(isinstance(ref,dict) and set(ref)=={'report','report_sha256','origin','origin_sha256'},'REFERENCE_PROPOSAL')
    reference_paths={k:resolve(layout,ref[k],'project') for k in ('report','origin')}
    check_reference(ref,reference_paths)
    paths={k:resolve(layout,v,'project') for k,v in d['reads'].items()}
    paths.update({'reference_'+k:v for k,v in reference_paths.items()})
    paths['base_checkpoint']=resolve(layout,d['base_checkpoint'],'artifact')
    require(d['base_checkpoint']==layout.ref('shared/base_model'))
    for k,tail in OUTPUTS.items():
        require(d['outputs'][k]==layout.ref('astra-r3/'+tail),'PREPARATION_MAPPING')
        paths[k]=resolve(layout,d['outputs'][k],'artifact')
    for key in ('origin_sha256','listing_sha256'):
        v=d[key]; require(isinstance(v,str) and len(v)==64 and all(c in '0123456789abcdef' for c in v))
    for k in READS:
        require(paths[k].is_dir() if k in ('bundle_root','capture_root') else paths[k].is_file(), 'PREPARATION_INPUT')
    require(paths['base_checkpoint'].is_dir(),'PREPARATION_INPUT')
    require(sha256_file(paths['origin'])==d['origin_sha256'],'ORIGIN_HASH')
    require(sha256_file(paths['listing'])==d['listing_sha256'],'LISTING_HASH')
    origin=read_json(paths['origin'])
    # All private inputs are exact origin members, not loosely related copies.
    for key in READS:
        if key in ('bundle_root','origin','capture_root'): continue
        rel=paths[key].relative_to(paths['bundle_root']).as_posix()
        require(origin['files'].get(rel)==sha256_file(paths[key]),'ORIGIN_MEMBER_HASH')
    require(paths['capture_root']==paths['bundle_root']/Path(origin['artifacts']['capture_manifest']['path']).parent)
    for role in ('freeze','readiness','roster','request','prepare_report'):
        require(paths[role]==paths['bundle_root']/origin['artifacts'][role]['path'])
    require(paths['edited'].parent.is_dir(),'EXPORT_PARENT')
    return d, paths

def dry_run(path, layout):
    d,paths=load(path,layout)
    return {'schema_version':SCHEMA,'dry_run':True,'launch_authority':False,
            'config_sha256':sha256_file(path),'origin_sha256':d['origin_sha256'],
            'listing_sha256':d['listing_sha256'], 'reference_proposal':reference_binding(d,paths), 'resolved':{k:str(v) for k,v in paths.items()},
            'inputs':{k:{'ref':d['reads'].get(k,d['base_checkpoint']),'exists':paths[k].exists()} for k in (*READS,'base_checkpoint')},
            'outputs':{k:{'ref':v,'exists':paths[k].exists()} for k,v in d['outputs'].items()},
            'spec_ref':d['outputs']['construction']+'/patch/spec.yaml',
            'payload_ref':d['outputs']['construction']+'/patch/payload.safetensors'}

def bridge_binding(proposal, layout, path):
    """Verify complete publication, real array records and full R3/source identity."""
    from . import inherited_inputs as b
    import numpy as np
    d,p=load(path,layout); root=p['inherited']
    complete=read_json(root/'complete.json'); h=read_json(root/'handoff.json')
    require(complete.get('schema_version')=='ehr-inherited-inputs-complete/v1' and complete.get('complete') is True)
    require(complete.get('files')=={n:sha256_file(root/n) for n in ('arrays.npz','handoff.json')})
    require(h.get('numpy_version')==np.__version__)
    require(h['r3_contract']==proposal.raw and h['arrays_sha256']==sha256_file(root/'arrays.npz'))
    require(h['bridge_sha256']==sha256_file(Path(b.__file__)))
    expected={k:sha256_file(p[k]) for k in ('origin','freeze','readiness','roster','request','prepare_report',
                                         'fit','selfaware','ambigqa','direction','listing')}
    expected['config']=sha256_file(EXPERIMENT_DIR/'astra_r3.yaml')
    require(h['source_sha256']==expected and h['origin_files_sha256']==read_json(p['origin'])['files'])
    for k,v in {'checkpoint_ref':d['base_checkpoint'],'spec_ref':d['outputs']['construction']+'/patch/spec.yaml',
                'payload_ref':d['outputs']['construction']+'/patch/payload.safetensors','export_ref':d['outputs']['edited']}.items():
        require(h[k]==v,'PREPARATION_MAPPING')
    with np.load(root/'arrays.npz',allow_pickle=False) as z:
        require(set(z.files)=={'U','K','c','W','outputs'})
        require(b.array_records({k:z[k] for k in z.files})==h['array_records'])
    return {'config_sha256':sha256_file(path),'proposal_sha256':proposal.sha256,
            'origin_sha256':d['origin_sha256'],'listing_sha256':d['listing_sha256'],
            'source_contract_sha256':expected,'reference_proposal':reference_binding(d,p),
            'inherited':{n:sha256_file(root/n) for n in ('complete.json','handoff.json','arrays.npz')}}

def verified_chain(proposal, layout, path):
    d,p=load(path,layout); binding=bridge_binding(proposal,layout,path)
    phase=p['phases']
    require(not (phase/'terminal.json').exists(),'PREPARATION_TERMINAL')
    done=read_json(phase/'complete.json')
    require(done.get('binding')==binding and done.get('complete') is True)
    files={k:sha256_file(v) for k,v in chain_files(p).items()}
    require(done.get('files')==files)
    require(read_json(phase/'bridge.json')=={'binding':binding})
    require(read_json(phase/'construction.json')=={'binding':binding,'exit_code':0,'report_sha256':files['prepare']})
    claim=read_json(phase/'claim.json')
    require(claim=={k:binding[k] for k in ('config_sha256','proposal_sha256','origin_sha256','listing_sha256')})
    prepared=read_json(p['construction']/'report.json'); audit=read_json(p['audit'])
    reference=reference_binding(d,p,prepared)
    require(prepared.get('reference_proposal')==reference and audit.get('reference_proposal')==reference,'REFERENCE_PROPOSAL')
    require(prepared.get('handoff_sha256')==binding['inherited']['handoff.json'])
    require(audit.get('handoff_sha256')==binding['inherited']['handoff.json'] and
            audit.get('arrays_sha256')==binding['inherited']['arrays.npz'])
    require(audit.get('passed') is True and audit.get('checkpoint_reloaded') is True and audit.get('receipt_checked') is True)
    require(prepared.get('patch',{}).get('spec_sha256')==files['spec'] and
            prepared.get('patch',{}).get('payload_sha256')==files['payload'])
    require(audit.get('proposal_sha256')==proposal.sha256 and audit.get('spec_sha256')==files['spec'] and
            audit.get('payload_sha256')==files['payload'] and audit.get('prepare_report_sha256')==files['prepare'])
    spec=yaml.safe_load((p['construction']/'patch/spec.yaml').read_bytes())
    require(spec['base']['checkpoint']==d['base_checkpoint'] and spec['payload']['path']==d['outputs']['construction']+'/patch/payload.safetensors' and
            spec['payload']['sha256']==files['payload'] and spec['export']['output_dir']==d['outputs']['edited'])
    require(sha256_file(p['qualification_rows'])==sha256_file(p['qualification_original']))
    return binding, {**{layout.ref('astra-r3/inherited-inputs/'+n):h for n,h in binding['inherited'].items()},
        d['reference_proposal']['report']:d['reference_proposal']['report_sha256'],
        d['reference_proposal']['origin']:d['reference_proposal']['origin_sha256'],
        d['reads']['origin']:d['origin_sha256'], d['reads']['listing']:d['listing_sha256'],
        layout.ref('astra-r3/preparation/complete.json'):sha256_file(phase/'complete.json'),
        layout.ref('astra-r3/preparation/claim.json'):sha256_file(phase/'claim.json'),
        'project://'+path.relative_to(layout.project_root).as_posix():sha256_file(path),
        **{d['outputs']['phases']+'/'+n:sha256_file(phase/n) for n in ('bridge.json','construction.json','validate.json','export.json','audit.json')},
        d['outputs']['edited']+'/mechinterp-weight-export.manifest.json':files['export_manifest']}

def chain_files(p):
    return {**{n:p['phases']/(n+'.json') for n in ('claim','bridge','construction','validate','export','audit')},
            'prepare':p['construction']/'report.json','spec':p['construction']/'patch/spec.yaml',
            'payload':p['construction']/'patch/payload.safetensors','audit':p['audit'],
            'export_manifest':p['edited']/'mechinterp-weight-export.manifest.json',
            'qualification':p['qualification_rows']}

def prepare(proposal, root, layout, path, *, cli=None):
    # Gate BEFORE any output, including phase locks/claims and directory creation.
    from . import astra_run as run, inherited_inputs as b, checkpoint_audit
    run.require_signed(EXPERIMENT_DIR,runtime_role='capture')
    manifest=yaml.safe_load((EXPERIMENT_DIR/'experiment.yaml').read_bytes())
    require(manifest['instrument']['pins'].get('runtime/preparation.yaml')==sha256_file(path),'INSTRUMENT_DRIFT')
    d,p=load(path,layout)
    require(all(not p[k].exists() for k in OUTPUTS),'OUTPUT_EXISTS')
    # Reserve the attempt first; every partial result makes later calls refuse.
    p['phases'].mkdir(parents=True,mode=0o700)
    stamp={'config_sha256':sha256_file(path),'proposal_sha256':proposal.sha256,
           'origin_sha256':d['origin_sha256'],'listing_sha256':d['listing_sha256']}
    def record(name,doc): _create_only(p['phases']/(name+'.json'),_json_bytes(doc))
    record('claim',stamp)
    stage='bridge'
    try:
        a={k:p[k] for k in READS if k!='qualification_original'}
        a.update(config=EXPERIMENT_DIR/'astra_r3.yaml',base_checkpoint=p['base_checkpoint'],
                 origin_sha256=d['origin_sha256'],listing_sha256=d['listing_sha256'],out=p['inherited'],
                 checkpoint_ref=d['base_checkpoint'],spec_ref=d['outputs']['construction']+'/patch/spec.yaml',
                 payload_ref=d['outputs']['construction']+'/patch/payload.safetensors',export_ref=d['outputs']['edited'])
        b.prepare(SimpleNamespace(**a))
        binding=bridge_binding(proposal,layout,path); record(stage,{'binding':binding})
        stage='construction'
        from .constructor import implementation
        constructor_output=io.StringIO()
        with contextlib.redirect_stdout(constructor_output):
            code=implementation().main(['prepare','--handoff',str(p['inherited']/'handoff.json'),
                    '--arrays',str(p['inherited']/'arrays.npz'),'--out',str(p['construction']),
                    '--reference-report',str(p['reference_report']),'--reference-report-sha256',d['reference_proposal']['report_sha256'],
                    '--reference-origin',str(p['reference_origin']),'--reference-origin-sha256',d['reference_proposal']['origin_sha256']])
        # The existing CLI uses exit 3 for guard reports, exit 2 for closed
        # exceptions. Preserve its distinction without changing numerical code.
        numerical_exception=False
        if code==2:
            try:
                numerical_exception=json.loads(constructor_output.getvalue()).get('error') in {
                    'DEGENERATE','ZERO_DENOMINATOR','FACTOR_CHECK','IDEAL_REFUSAL'}
            except (TypeError,ValueError): pass
        record(stage,{'binding':binding,'exit_code':code,
            'report_sha256':sha256_file(p['construction']/'report.json') if (p['construction']/'report.json').is_file() else None})
        require(code!=3 and not numerical_exception,'NUMERICAL_REFUSAL'); require(code==0,'CONSTRUCTION_INPUT')
        prepared=read_json(p['construction']/'report.json')
        require(prepared.get('reference_proposal')==reference_binding(d,p,prepared),'REFERENCE_PROPOSAL')
        # Verify emitted destinations before handing them to the public engine.
        spec=p['construction']/'patch/spec.yaml'; payload=p['construction']/'patch/payload.safetensors'
        s=yaml.safe_load(spec.read_bytes())
        require(s['payload']['path']==a['payload_ref'] and s['export']['output_dir']==a['export_ref'] and
                s['base']['checkpoint']==a['checkpoint_ref'] and s['payload']['sha256']==sha256_file(payload))
        engine=cli or run._engine(root)
        for stage,mode in (('validate','--validate'),('export','--export')):
            with (p['phases']/(stage+'.json')).open('xb') as sink:
                engine.run('mechinterp',['weights-patch','--weights-config',a['spec_ref'],mode,'--json'],stdout=sink,guard_parent=True)
                sink.flush()
                import os
                os.fsync(sink.fileno())
            result=read_json(p['phases']/(stage+'.json'))
            require(result.get('success',True) is True,'ENGINE_REFUSAL')
        stage='audit'
        result=checkpoint_audit.audit(proposal,handoff=p['inherited']/'handoff.json',arrays=p['inherited']/'arrays.npz',
            prepare_report=p['construction']/'report.json',spec=spec,payload=payload,
            base_model=p['base_checkpoint'],edited_model=p['edited'],out=p['audit'],
            reference_report=p['reference_report'],reference_report_sha256=d['reference_proposal']['report_sha256'],
            reference_origin=p['reference_origin'],reference_origin_sha256=d['reference_proposal']['origin_sha256'])
        record(stage,dict(result,binding=binding)); require(result['passed'],'NUMERICAL_REFUSAL')
        stage='qualification_rows'
        rows=[json.loads(x) for x in p['qualification_original'].read_text().splitlines() if x.strip()]
        require(len(rows)==20 and len({r['id'] for r in rows})==20,'QUAL_ROSTER')
        p['qualification_rows'].parent.mkdir(parents=True,exist_ok=True)
        _create_only(p['qualification_rows'],p['qualification_original'].read_bytes())
        record('complete',{'complete':True,'binding':binding,'files':{k:sha256_file(v) for k,v in chain_files(p).items()}})
        verified_chain(proposal,layout,path)
        return {'complete':True,'binding':binding,'launch_authority':False,'freeze_pending':True}
    except BaseException as exc:
        record('terminal',{'phase':stage,'terminal':True,'category':'numerical_refusal' if isinstance(exc,HarnessError) and exc.code=='NUMERICAL_REFUSAL' else 'input_or_instrument_error'})
        raise
