"""Exact source, installed host, engine, checkpoint and Git qualification binding."""
import importlib
from pathlib import Path
import yaml
from .util import HarnessError, sha256_file, read_json, canonical_sha256
from . import commitments

def inventory(root):
    root=Path(root)
    if not root.is_dir() or root.is_symlink(): raise HarnessError('INVENTORY','missing or symlink root')
    result={}
    for p in sorted(root.rglob('*')):
        if p.is_symlink(): raise HarnessError('INVENTORY','symlink member')
        if p.is_file(): result[p.relative_to(root).as_posix()]=sha256_file(p)
    if not result: raise HarnessError('INVENTORY','empty inventory')
    return result

def sources(directory):
    return {p.relative_to(directory).as_posix():sha256_file(p)
            for package in ('r2_runtime','hs20_r2')
            for p in sorted((directory/package).rglob('*'))
            if p.is_file() and p.suffix in ('.py','.yaml','.json')}

def host_identity(root,runtime):
    try:
        from engine_host.engine_identity import inspect_engine
        host=importlib.import_module('engine_host')
    except ImportError as exc:
        raise HarnessError('PUBLIC_HOST_UNAVAILABLE','installed public engine_host is required; no alternate backend') from exc
    identity=inspect_engine(root)
    if identity.get('wheel_sha256')!=runtime['engine']['wheel_sha256']:
        raise HarnessError('ENGINE_BINDING','installed engine wheel differs')
    files={p.name:sha256_file(p) for p in sorted(Path(host.__file__).parent.glob('*.py'))}
    return {'engine_identity':identity,'host_module_sha256':files}

def check_host(directory,root,runtime):
    path=directory/'runtime'/'r2_host_binding.json'
    if not path.is_file(): raise HarnessError('HOST_BINDING','parent must supply and sign runtime/r2_host_binding.json from installed public host')
    expected=read_json(path)
    actual=host_identity(root,runtime)
    if expected!=actual: raise HarnessError('HOST_BINDING','installed public host/source differs from signed binding')
    return actual

def qualification_binding(proposal,directory,root,runtime,frozen,freeze_sha):
    return {'proposal_sha256':proposal.sha256,'patch_freeze_sha256':freeze_sha,
            'checkpoint':frozen['edited_files_sha256'],'spec_sha256':frozen['spec_sha256'],
            'image_digest':runtime['evaluation']['image_digest'],
            'sources':sources(directory),'host':check_host(directory,root,runtime),
            'runtime_sha256':sha256_file(directory/'astra_runtime.yaml')}

def require_qualification(proposal,layout,directory,runtime,frozen):
    path=commitments.public_path(layout,'astra_edited_qualification.json')
    report=read_json(path)
    commitments.require_git(layout,'astra_edited_qualification.json',report)
    expected=qualification_binding(proposal,directory,layout.project_root,runtime,frozen,
                                 sha256_file(commitments.public_path(layout,'astra_patch_freeze.json')))
    from .qualification_owned import writer, verify_drill, journal
    from .qualification_compare import compare, RUNS
    from .util import read_jsonl
    with writer(layout.local('astra-r2/qualification-writer.lock')):
        root = layout.local('astra-r2/edited-qualification')
        manifest = read_json(root/'manifest.json')
        original = read_jsonl(root/'original.jsonl')
        roster_ref = manifest['rows_ref']
        source_sha = sha256_file(layout.to_local(roster_ref))
        if (manifest.get('binding') != expected or manifest.get('rows_sha256') != canonical_sha256(original)
            or manifest.get('rows_source_sha256') != source_sha
            or frozen['artifacts'].get(roster_ref) != source_sha
            or original != read_jsonl(layout.to_local(roster_ref))):
            raise HarnessError('EDITED_QUALIFICATION','retained roster or binding differs')
        verify_drill(root,expected)
        runs = {name:journal(root/'runs'/name/'completions.jsonl')[1] for name in RUNS}
        parity = compare(original,runs)
        files = ['manifest.json','original.jsonl','permuted.jsonl','resume.claim.json','resume.killed.json','resume.observed.json','resume.before.jsonl','resume.killed.raw']
        for name in RUNS:
            claim = read_json(root/(name+'.claim.json'))
            reservation = 40 if name == 'resume' else 20
            if claim.get('binding') != expected or claim.get('requests_reserved') != reservation:
                raise HarnessError('EDITED_QUALIFICATION','retained reservation differs')
            if any(len(r.get('completion_token_ids',[])) > 128 for r in runs[name]):
                raise HarnessError('EDITED_QUALIFICATION','token ceiling exceeded')
            if name != 'resume':
                observed = read_json(root/(name+'.observed.json'))
                if observed != {'binding':expected,'claim_sha256':sha256_file(root/(name+'.claim.json')),
                                'output_sha256':sha256_file(root/'runs'/name/'completions.jsonl')}:
                    raise HarnessError('EDITED_QUALIFICATION','retained repeat differs')
                files.extend([name+'.claim.json',name+'.observed.json'])
            files.append(f'runs/{name}/completions.jsonl')
        evidence = {f:sha256_file(root/f) for f in files}
        actual = {'schema_version':'ehr-astra-r2-edited-qualification/v1','binding':expected,
                  'passed':True,'scored':False,'requests_reserved':120,'owned_sigkill_resume':True,
                  'comparison':parity,'evidence_sha256':evidence}
        if report != actual:
            raise HarnessError('EDITED_QUALIFICATION','committed receipt differs from actual retained proof')
        name = 'astra_edited_qualification.manifest.json'
        public_manifest = read_json(commitments.public_path(layout,name))
        expected_manifest = {'schema_version':'ehr-astra-r2-qualification-manifest/v1',
                             'binding':expected,'receipt_sha256':sha256_file(path),
                             'requests_reserved':{n:40 if n == 'resume' else 20 for n in RUNS},
                             'evidence_sha256':evidence}
        if public_manifest != expected_manifest:
            raise HarnessError('EDITED_QUALIFICATION','public qualification manifest differs')
        commitments.require_git(layout,name,public_manifest)
    return sha256_file(path)
