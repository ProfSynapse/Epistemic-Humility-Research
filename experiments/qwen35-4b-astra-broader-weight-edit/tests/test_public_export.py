"""Run in parent's pinned engine-host environment. No engine internal imports."""
import json
from pathlib import Path
import numpy as np
import pytest
import yaml
from hs20_r2 import astra_r2 as r
from hs20_r2 import frozen as f
from test_r2 import fixture


def test_public_cpu_export(fixture,tmp_path):
    boundary=pytest.importorskip('engine_host.cli_boundary',reason='requires pinned public engine_host installation')
    import torch
    from safetensors.torch import save_file
    U,K,c,W,p,_,_,_,con=fixture
    root=tmp_path/'project'; root.mkdir()
    (root/'synaptic.yaml').write_text(yaml.safe_dump({
        'schema_version':'synaptic-project/v1','project':{'id':'ehr-r2-synthetic','name':'R2 synthetic'},
        'engine':{'requires':'>=1.1.0rc1,<2','api':'v1','cli_requires':'==1.1.0rc1',
                  'source_commit':'d03a15d62549c64cf46e10532d50a77accd32b26',
                  'wheel_sha256':'9ec0896923da5a8c3e22fe79c950a1d0431fc9b527f1429d3b1d62416a2d632a'},
        'paths':{k:'project://.synaptic/'+k for k in ['artifacts','state','tracking','cache','tmp']},
        'policies':{'engine_writes':'deny','source_writes':'deny','external_paths':'deny','dirty_sources':'deny_cloud'}}))
    artifacts=root/'.synaptic/artifacts'; base=artifacts/'base'; base.mkdir(parents=True)
    save_file({r.TENSOR:torch.tensor(W,dtype=torch.bfloat16),'other.weight':torch.arange(3,dtype=torch.bfloat16)},str(base/'model.safetensors'))
    (base/'config.json').write_text('{"synthetic":true}')
    p=r.proposal({**p.raw['model'],'files_sha256':{'model.safetensors':f.sha256_file(base/'model.safetensors')}},p.raw['development'],{})
    binding={'index_sha256':f.sha256_file(base/'model.safetensors'),'files_sha256':p.raw['model']['files_sha256']}
    tensor={'name':r.TENSOR,'dtype':'bfloat16','shape':list(r.SHAPE),'sha256':con.base_sha256}
    emitted=r.emit_patch(p,con,tensor,binding,out_dir=artifacts/'patch',checkpoint_ref='artifact://base',payload_ref='artifact://patch/payload.safetensors',export_ref='artifact://edited')
    cli=boundary.EngineCLI(root,plugin_roots=())
    def run(mode,output):
        path=artifacts/output
        with path.open('wb') as sink:
            cli.run('mechinterp',['weights-patch','--weights-config','artifact://patch/spec.yaml',mode,'--json'],stdout=sink)
        doc=json.loads(path.read_text())
        if 'success' in doc:
            assert doc['success'],doc
            return doc['data']
        return doc
    validation=run('--validate','validation.json')
    export=run('--export','export.json')
    manifest=export['manifest']
    assert manifest['spec']['sha256']==emitted['spec_sha256']
    assert manifest['payload']['sha256']==emitted['payload_sha256']
    report=r.audit_checkpoint(base,artifacts/'edited',con,p,U,K,receipt_tensor=validation['receipt']['tensors'][0],export_manifest=manifest)
    assert report['passed'],report['failures']
    with pytest.raises(Exception): run('--export','collision.json')
