"""Synthetic CPU evidence only. No real capture/readiness or constructor run."""
from pathlib import Path
from types import SimpleNamespace
import copy
import json
import sys
import numpy as np
import pytest
import torch
import yaml
from safetensors.numpy import save_file
from safetensors.torch import save_file as save_torch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from r3_runtime import inherited_inputs as b


def put(path, obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,sort_keys=True)+'\n')
    return b.sha256_file(path)

@pytest.fixture
def fixture(tmp_path, monkeypatch):
    root = tmp_path/'bundle'; root.mkdir(); cap = root/'capture'; cap.mkdir()
    base = tmp_path/'base'; base.mkdir()
    tensor = 'model.language_model.layers.19.mlp.down_proj.weight'
    W = torch.ones((3,40),dtype=torch.bfloat16)
    save_torch({tensor:W},str(base/'model.safetensors'))
    shardsha = b.sha256_file(base/'model.safetensors')
    indexsha = put(base/'model.safetensors.index.json',{'weight_map':{tensor:'model.safetensors'}})
    rawsha = b.sha256_bytes(W.view(torch.uint8).numpy().tobytes())
    model = {'repo':'synthetic','revision':'original-revision','dtype':'bfloat16',
             'files_sha256':{'model.safetensors':shardsha},'index_sha256':indexsha}
    directionsha = put(tmp_path/'direction.json',{'vector':[1.,0.,0.],'sigma':1.,'layer':19})
    fit = [{'row_key':r+str(i),'role':r,'question':r+' question '+str(i)}
           for r in b.frozen.HISTORICAL_ROLES for i in range(3)]
    fitsha = put(tmp_path/'fit.json',fit)
    sash = put(tmp_path/'selfaware.json',{'example':[{'question':'eval-a','answerable':True,'answer':['a']}]})
    amb = tmp_path/'ambigqa.jsonl'
    amb.write_text(json.dumps({'id':'a','question':'eval-b','annotations':{'type':['multipleQAs']}})+'\n')
    counts = dict.fromkeys(b.frozen.HISTORICAL_ROLES,2)
    surfaces = {'selfaware':{'sha256':sash,'rows':1,'known':1,'unknown':0},
                'ambigqa':{'sha256':b.sha256_file(amb),'rows':1,'known':0,'unknown':1}}
    raw = {'prompts':{'P-struct':'synthetic-original-prompt'},'model':model,'development':{'seed':20261103,'counts':counts,'fit_sha256':fitsha},
           'patch':{'tensor':tensor,'shape':[3,40],'sigma_c':1.,'decoder_block':19,
                    'base_tensor_sha256':rawsha,'direction_sha256':directionsha,'unit_norm_tolerance':1e-6},
           'evaluation':{'surfaces':surfaces},
           'validation':{'linear_absolute_l2_floor':1e-6,'linear_relative_l2_max':.01}}
    r1path = root/'source/astra_r1.yaml'; r1path.parent.mkdir()
    r1_raw=copy.deepcopy(raw);r1_raw['model'].pop('index_sha256')  # historical R1 contract
    r1path.write_text(yaml.safe_dump(r1_raw)); r1sha = b.sha256_file(r1path)
    renderer = root/'source/render.py'; renderer.write_text('# synthetic original source\n')
    source_files = {'astra_r1.yaml':'source/astra_r1.yaml','hs20_nwe/astra_render.py':'source/render.py'}
    selected = b.frozen.select_roster(fit,{'a':['eval-a','eval-b']},seed=20261103,counts=counts)
    roster = {'schema_version':b.frozen.ROSTER_SCHEMA,'proposal_sha256':r1sha,
              'keys':selected['keys'],'roster_sha256':b.frozen.roster_digest(selected['keys'])}
    put(root/'roster.json',roster)
    keys = sum([roster['keys'][r] for r in b.frozen.HISTORICAL_ROLES],[])
    identity = {'run':{'revision':model['revision'],'adapter':None,'content_end':None,
        'render':{'callable':'hs20_nwe.astra_render:render_pstruct','source_sha256':b.sha256_file(renderer)},
        'model':{'path':'/original/host/model','files':model['files_sha256']}},
        'inputs':[{'row_key':k,'prompt_sha256':'a'*64} for k in keys], 'manifest_extra':None,
        'families':['anchor'],'layers':[20],'sites':[{'layer':19,'module':'mlp.down_proj','tensor':t} for t in ('input','output')],
        'every_k':1,'max_new_tokens':1,'use_cache':True,'forward_only':True,'save_tensors':True}
    fp = b.astra_capture.fingerprint(identity)
    put(root/'request.json',{'schema_version':b.astra_capture.SCHEMA,'identity':identity,'fingerprint':fp,'proposal_sha256':r1sha})
    journal=[]; tensorfiles={}
    for i,k in enumerate(keys):
        x = np.full((1,40),i+1.,dtype=np.float32); y = x@W.float().numpy().T
        residual = f'{i}.safetensors'; site = f'{i}.sites.safetensors'
        save_file({'L20':y},str(cap/residual)); save_file({'L19.mlp.down_proj.input':x,'L19.mlp.down_proj.output':y},str(cap/site))
        tensorfiles.update({n:b.sha256_file(cap/n) for n in (residual,site)})
        journal.append({'row_key':k,'answered':True,'prompt_len':4,'seq_total':4,'content_end':3,
            'capture_files':{'anchor':{'file':residual,'sha256':tensorfiles[residual]}},
            'site_captures':{'anchor':{'file':site,'sha256':tensorfiles[site],'positions':[3]}}})
    put(cap/'manifest.json',{'schema_version':b.capture.MANIFEST_SCHEMA,'complete':True,'rows':journal})
    (cap/'capture.runlog.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in journal))
    put(cap/'capture.runlog.jsonl.meta.json',{'complete':True,'fingerprint':fp})
    provenance = {'fingerprint':fp,'request_sha256':b.sha256_file(root/'request.json'),
        'meta_sha256':b.sha256_file(cap/'capture.runlog.jsonl.meta.json'),'journal_sha256':b.sha256_file(cap/'capture.runlog.jsonl')}
    t = {'name':tensor,'dtype':'bfloat16','shape':[3,40],'sha256':rawsha,'file':'model.safetensors'}
    binding = {'files_sha256':model['files_sha256'],'index_sha256':indexsha}
    report = {'proposal_sha256':r1sha,'capture_provenance':provenance,
        'capture_manifest_sha256':b.sha256_file(cap/'manifest.json'),'roster_sha256':roster['roster_sha256'],
        'capture_files_digest':b.canonical_sha256(sorted((r['row_key'],r['capture_files']['anchor']['sha256'],r['site_captures']['anchor']['sha256']) for r in journal)),
        'construction':{'columns':list(range(32))},'tensor':t,'binding':binding,'c_hat_sha256':directionsha}
    put(root/'prepare.json',report)
    artifacts = {role:{'path':name,'original_ref':'artifact://qwen35-4b-hs20-native-weight-edit/astra-r1/'+name}
                 for role,name in {'roster':'roster.json','request':'request.json','prepare_report':'prepare.json',
                                   'capture_manifest':'capture/manifest.json'}.items()}
    freeze = {'proposal_sha256':r1sha,'base_files_sha256':model['files_sha256'],
              'artifacts':{v['original_ref']:b.sha256_file(root/v['path']) for v in artifacts.values()}}
    put(root/'freeze.json',freeze)
    put(root/'readiness.json',{'passed':True,'target_inference_performed':False,'source_module_sha256':
        {k:b.sha256_file(root/v) for k,v in source_files.items()},'request_journal_binding':provenance,'tensor_files':tensorfiles})
    artifacts.update({k:{'path':k+'.json','original_ref':'source://'+k} for k in ('freeze','readiness')})
    raw['development']['reuse'] = {'r1_patch_freeze_sha256':b.sha256_file(root/'freeze.json'),
       'original_roster_sha256':b.sha256_file(root/'roster.json'),'capture_request_sha256':b.sha256_file(root/'request.json'),
       'capture_manifest_sha256':b.sha256_file(cap/'manifest.json')}
    config = tmp_path/'astra_r3.yaml'; config.write_text(yaml.safe_dump(raw))
    listing = tmp_path/'listing.json'; put(listing,{'success':True,'data':{'listing_truncated':False,
       'files':[{'name':'model.safetensors','sha256':shardsha}],'index_sha256':indexsha,'tensors':[t]}})
    origin = {'schema_version':b.ORIGIN_SCHEMA,'origin_experiment':'qwen35-4b-hs20-native-weight-edit',
      'origin_path':'astra-r1/capture','promotion_destination':'experiments/common/captures/synthetic','numpy_version':np.__version__,
      'artifacts':artifacts,'source_files':source_files,
      'files':{p.relative_to(root).as_posix():b.sha256_file(p) for p in root.rglob('*') if p.is_file()}}
    originpath=tmp_path/'origin.json'; digest=put(originpath,origin)
    a = SimpleNamespace(config=config,bundle_root=root,origin=originpath,origin_sha256=digest,
        capture_root=cap,freeze=root/'freeze.json',readiness=root/'readiness.json',roster=root/'roster.json',
        request=root/'request.json',prepare_report=root/'prepare.json',fit=tmp_path/'fit.json',
        selfaware=tmp_path/'selfaware.json',ambigqa=amb,direction=tmp_path/'direction.json',base_checkpoint=base,
        listing=listing,listing_sha256=b.sha256_file(listing),out=tmp_path/'result',checkpoint_ref='artifact://synthetic/base',
        spec_ref='artifact://synthetic/patch/spec.yaml',payload_ref='artifact://synthetic/patch/payload.safetensors',export_ref='artifact://synthetic/export')
    monkeypatch.setattr(b,'load_proposal',lambda path:b.Proposal(yaml.safe_load(path.read_bytes()),b.sha256_file(path)))
    monkeypatch.setattr(b,'require_signed',lambda *args,**kwargs:None)
    return a


def test_b483_real_preparation_path(fixture):
    a=fixture
    argv=[]
    for k,v in vars(a).items(): argv.extend(['--'+k.replace('_','-'),str(v)])
    assert b.main(argv)==0
    h=b.read(a.out/'handoff.json'); done=b.read(a.out/'complete.json')
    with np.load(a.out/'arrays.npz',allow_pickle=False) as z:
        assert set(z.files)=={'U','K','c','W','outputs'}
        assert z['U'].shape==(2,40) and z['W'].shape==(3,40)
        assert b.array_records({k:z[k] for k in z.files})==h['array_records']
    assert h['r1_columns']==list(range(32))
    assert h['r3_contract']==yaml.safe_load(a.config.read_bytes())
    assert done['files']['handoff.json']==b.sha256_file(a.out/'handoff.json')
    with pytest.raises(b.HarnessError,match='OUTPUT_EXISTS'): b.prepare(a)

@pytest.mark.parametrize('attr',['origin','request','roster','freeze','prepare_report','fit','direction','listing'])
def test_b483_changed_file(fixture,attr):
    a=fixture; path=getattr(a,attr); path.write_bytes(path.read_bytes()+b' ')
    with pytest.raises(b.HarnessError): b.prepare(a)
    assert not a.out.exists()

@pytest.mark.parametrize('mutation,code',[
    ('source','REQUEST_SOURCE'),('revision','REQUEST_MODEL'),('site','REQUEST_SETTINGS'),
    ('cache','REQUEST_SETTINGS'),('position','CAPTURE_POSITION'),('key','JOURNAL_IDENTITY'),
    ('columns','OLD_SUPPORT'),('lineage','PREPARE_LINEAGE')])
def test_b483_authenticated_but_wrong_semantics(fixture,mutation,code):
    a=fixture
    # Test inner semantic validation after an upstream promotion reviewer has
    # bound these bytes; no claim that these rewritten fixtures are real records.
    req=b.read(a.request); rows=[json.loads(x) for x in (a.capture_root/'capture.runlog.jsonl').read_text().splitlines()]
    report=b.read(a.prepare_report)
    if mutation=='source': req['identity']['run']['render']['callable']='r3_runtime.astra_render:render_pstruct'
    if mutation=='revision': req['identity']['run']['revision']='edited'
    if mutation=='site': req['identity']['sites'][0]['layer']=18
    if mutation=='cache': req['identity']['use_cache']=False
    if mutation=='position': rows[0]['site_captures']['anchor']['positions']=[2]
    if mutation=='key': rows[0]['row_key']='wrong'
    if mutation=='columns': report['construction']['columns']=[0]*32
    if mutation=='lineage': report['proposal_sha256']='new'
    req['fingerprint']=b.astra_capture.fingerprint(req['identity']); put(a.request,req)
    put(a.capture_root/'capture.runlog.jsonl.meta.json',{'complete':True,'fingerprint':req['fingerprint']})
    (a.capture_root/'capture.runlog.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in rows))
    manifest=b.read(a.capture_root/'manifest.json'); manifest['rows']=rows; put(a.capture_root/'manifest.json',manifest)
    ready=b.read(a.readiness)
    ready['request_journal_binding']={'fingerprint':req['fingerprint'],'request_sha256':b.sha256_file(a.request),
        'meta_sha256':b.sha256_file(a.capture_root/'capture.runlog.jsonl.meta.json'),
        'journal_sha256':b.sha256_file(a.capture_root/'capture.runlog.jsonl')}
    report['capture_provenance']=ready['request_journal_binding']; report['capture_manifest_sha256']=b.sha256_file(a.capture_root/'manifest.json')
    put(a.prepare_report,report); put(a.readiness,ready)
    origin=b.read(a.origin); freeze=b.read(a.freeze)
    for role in ('roster','request','prepare_report','capture_manifest'):
        item=origin['artifacts'][role]; freeze['artifacts'][item['original_ref']]=b.sha256_file(a.bundle_root/item['path'])
    put(a.freeze,freeze)
    raw=yaml.safe_load(a.config.read_bytes()); reuse=raw['development']['reuse']
    for key,path in [('r1_patch_freeze_sha256',a.freeze),('capture_request_sha256',a.request),('capture_manifest_sha256',a.capture_root/'manifest.json')]: reuse[key]=b.sha256_file(path)
    a.config.write_text(yaml.safe_dump(raw))
    origin['files']={p.relative_to(a.bundle_root).as_posix():b.sha256_file(p) for p in a.bundle_root.rglob('*') if p.is_file()}
    a.origin_sha256=put(a.origin,origin)
    with pytest.raises(b.HarnessError,match=code): b.prepare(a)

@pytest.mark.parametrize('mode,code',[('dtype','BASE_STORAGE'),('bias','BASE_BIAS_INVENTORY'),('hash','BASE_TENSOR_HASH')])
def test_b483_checkpoint_storage(fixture,mode,code):
    a=fixture; prop=b.load_proposal(a.config); tensor=prop.tensor
    data={tensor:torch.ones((3,40),dtype=torch.float32 if mode=='dtype' else torch.bfloat16)}
    if mode=='bias': data[tensor.removesuffix('.weight')+'.bias']=torch.zeros(3,dtype=torch.bfloat16)
    if mode=='hash': data[tensor][0,0]=2
    save_torch(data,str(a.base_checkpoint/'model.safetensors'))
    mapping={k:'model.safetensors' for k in data}; prop.raw['model']['index_sha256']=put(a.base_checkpoint/'model.safetensors.index.json',{'weight_map':mapping})
    prop.raw['model']['files_sha256']['model.safetensors']=b.sha256_file(a.base_checkpoint/'model.safetensors')
    listing=b.read(a.listing); listing['data']['index_sha256']=prop.raw['model']['index_sha256']
    listing['data']['files'][0]['sha256']=prop.raw['model']['files_sha256']['model.safetensors']; put(a.listing,listing)
    with pytest.raises(b.HarnessError,match=code): b.checkpoint(prop,a.base_checkpoint,a.listing)


def test_b483_changed_capture_array(fixture):
    a=fixture
    path=next(a.capture_root.glob('*.sites.safetensors')); path.write_bytes(path.read_bytes()[:-1]+b'x')
    with pytest.raises(b.HarnessError): b.prepare(a)


def test_b483_sign_gate_precedes_tensor_reads(fixture,monkeypatch):
    def refuse(*args,**kwargs): raise b.HarnessError('UNSIGNED','synthetic')
    monkeypatch.setattr(b,'require_signed',refuse)
    with pytest.raises(b.HarnessError,match='UNSIGNED'): b.prepare(fixture)
    assert not fixture.out.exists()


def test_b483_partial_publication_never_retries(fixture,monkeypatch):
    original=b.frozen._create_only
    def fail(path,data):
        if path.name=='handoff.json': raise OSError('synthetic interruption')
        return original(path,data)
    monkeypatch.setattr(b.frozen,'_create_only',fail)
    with pytest.raises(OSError): b.prepare(fixture)
    assert (fixture.out/'arrays.npz').is_file() and not (fixture.out/'complete.json').exists()
    with pytest.raises(b.HarnessError,match='OUTPUT_EXISTS'): b.prepare(fixture)


def test_b483_roster_rule_mismatch(fixture):
    a=fixture; rows=b.read(a.fit)
    for r in rows: r['row_key']='changed-'+r['row_key']
    digest=put(a.fit,rows)
    raw=yaml.safe_load(a.config.read_bytes()); raw['development']['fit_sha256']=digest
    a.config.write_text(yaml.safe_dump(raw))
    with pytest.raises(b.HarnessError,match='ROSTER_RULE'): b.prepare(a)


def test_b483_npz_readback_change_blocks_completion(fixture,monkeypatch):
    original=b.np.savez
    def corrupt(stream,**arrays):
        arrays['U']=arrays['U']+1
        return original(stream,**arrays)
    monkeypatch.setattr(b.np,'savez',corrupt)
    with pytest.raises(b.HarnessError,match='ARRAY_READBACK'): b.prepare(fixture)
    assert not (fixture.out/'complete.json').exists()


def test_b483_direction_no_renormalization(fixture):
    a=fixture; prop=b.load_proposal(a.config)
    digest=put(a.direction,{'vector':[-2.,0.,0.],'sigma':1.,'layer':19})
    prop.patch['direction_sha256']=digest
    with pytest.raises(b.HarnessError,match='DIRECTION'): b.direction(prop,a.direction)
