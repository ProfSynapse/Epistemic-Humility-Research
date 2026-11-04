"""Edited-only qualification. Public transport must own any kill; no stored PID authority."""
import argparse
import json
import os
import sys
from pathlib import Path
import yaml
from . import astra_run as run, astra_fixed, astra_render, commitments
from . import qualification_owned as owned
from .admission import qualification_binding
from .qualification_compare import compare, RUNS, N
from .config import EXPERIMENT_DIR, Layout, find_project_root
from .util import HarnessError, read_json, read_jsonl, write_json, write_jsonl, canonical_sha256, sha256_file


def context(proposal,layout,base,edited):
    runtime=run.require_signed(EXPERIMENT_DIR,runtime_role='evaluation')
    frozen=run.require_frozen(proposal,layout,base,edited)
    binding=qualification_binding(proposal,EXPERIMENT_DIR,layout.project_root,runtime,frozen,
             sha256_file(commitments.public_path(layout,'astra_patch_freeze.json')))
    return runtime,binding


def prepare(proposal,layout,base,edited,rows_ref):
    runtime,binding=context(proposal,layout,base,edited)
    # Parent authenticates/promotes the original R1 twenty-row non-evaluation roster.
    frozen=read_json(commitments.public_path(layout,'astra_patch_freeze.json'))
    if frozen['artifacts'].get(rows_ref)!=sha256_file(layout.to_local(rows_ref)):
        raise HarnessError('QUAL_ROSTER','original twenty-row roster must be bound before patch freeze')
    rows=read_jsonl(layout.to_local(rows_ref))
    if len(rows)!=N or len({r['id'] for r in rows})!=N:
        raise HarnessError('QUAL_ROSTER','exactly twenty unique original qualification rows required')
    os.environ['HS20NWE_RENDER_MODEL']=str(base.resolve())
    os.environ['HS20NWE_RENDER_REVISION']=proposal.raw['model']['revision']
    tokenizer=astra_render._tokenizer()
    import hashlib
    for r in rows:
        ids=tokenizer.encode(r['prompt'],add_special_tokens=False)
        if (r['expected_prompt_sha256']!=hashlib.sha256(r['prompt'].encode()).hexdigest()
            or r['expected_token_ids_sha256']!=hashlib.sha256(json.dumps(ids,separators=(',',':')).encode('ascii')).hexdigest()
            or r['expected_prompt_tokens']!=len(ids) or len(ids)+128>2048):
            raise HarnessError('QUAL_TOKENIZER','original prompt/token commitments differ')
    root=layout.local(f'{run.PREFIX}/edited-qualification')
    if root.exists(): raise HarnessError('OUTPUT_EXISTS','fresh qualification namespace required')
    root.mkdir(parents=True)
    write_jsonl(root/'original.jsonl',rows)
    permuted=sorted(rows,key=lambda r:hashlib.sha256(('20261103:'+r['id']).encode()).hexdigest())
    write_jsonl(root/'permuted.jsonl',permuted)
    write_json(root/'manifest.json',{'binding':binding,'rows_sha256':canonical_sha256(rows),'rows_ref':rows_ref,
              'rows_source_sha256':sha256_file(layout.to_local(rows_ref))})
    return {'rows':N,'scored':False,'launch_authority':False}


def _inputs(proposal, layout, base, edited):
    runtime, binding = context(proposal, layout, base, edited)
    root = layout.local(f'{run.PREFIX}/edited-qualification')
    manifest = read_json(root/'manifest.json')
    if manifest['binding'] != binding:
        raise HarnessError('QUAL_DRIFT', 'source/checkpoint/host/image drift')
    frozen = read_json(commitments.public_path(layout,'astra_patch_freeze.json'))
    roster_ref = manifest['rows_ref']
    source_sha = sha256_file(layout.to_local(roster_ref))
    if (frozen['artifacts'].get(roster_ref) != source_sha
        or manifest['rows_source_sha256'] != source_sha):
        raise HarnessError('QUAL_ROSTER','frozen original roster differs')
    original = read_jsonl(root/'original.jsonl')
    if original != read_jsonl(layout.to_local(roster_ref)):
        raise HarnessError('QUAL_ROSTER','staged roster differs from frozen source')
    if canonical_sha256(original) != manifest['rows_sha256']:
        raise HarnessError('QUAL_ROSTER', 'prompt roster drift')
    permuted = read_jsonl(root/'permuted.jsonl')
    import hashlib
    expected = sorted(original, key=lambda r: hashlib.sha256(('20261103:'+r['id']).encode()).hexdigest())
    if permuted != expected:
        raise HarnessError('QUAL_ROSTER', 'fixed permutation differs')
    return runtime, binding, root, original


def _arguments(proposal, runtime, layout, edited, name):
    order = 'permuted' if name.startswith('permuted') else 'original'
    return run.batch_arguments(proposal, runtime, layout, edited,
        layout.ref(f'{run.PREFIX}/edited-qualification/{order}.jsonl'),
        layout.ref(f'{run.PREFIX}/edited-qualification/runs/{name}'))


def worker(proposal, layout, base, edited, guard_fd):
    # Controller passes an anonymous pipe and inherited writer lock. No stored
    # PID, configurable command, alternate engine or raw engine imports.
    import hashlib
    import stat
    if not stat.S_ISFIFO(os.fstat(guard_fd).st_mode):
        raise HarnessError('QUAL_OWNER','anonymous live-owner pipe required')
    token = os.read(guard_fd,32)
    owned.guard(guard_fd)
    runtime, binding, root, _ = _inputs(proposal, layout, base, edited)
    claim = read_json(root/'resume.claim.json')
    if (len(token) != 32 or hashlib.sha256(token).hexdigest() != claim.get('owner_sha256')
        or claim.get('binding') != binding or claim.get('requests_reserved') != 40):
        raise HarnessError('QUAL_OWNER','live controller authority differs')
    run._gpu(layout.project_root, layout, 'batch-generate',
             _arguments(proposal, runtime, layout, edited, 'resume'), ack=True, role='evaluation')


def execute(proposal,layout,base,edited,name,*,ack):
    if name not in RUNS:
        raise HarnessError('QUAL_RUN', 'unknown qualification run')
    if not ack:
        raise HarnessError('GPU_ACK', 'pass --gpu-ack for this exact qualification')
    root = layout.local(f'{run.PREFIX}/edited-qualification')
    with owned.writer(layout.local(f'{run.PREFIX}/qualification-writer.lock')) as lock_fd:
        runtime, binding, root, _ = _inputs(proposal, layout, base, edited)
        # Qualification consumes exactly the registered recipe, without format retries.
        d = proposal.raw['evaluation']['decode']
        if (d['max_new_tokens'] != 128 or d['temperature'] != 0 or d['n_samples'] != 1
            or runtime['evaluation']['batch_size'] != 1):
            raise HarnessError('QUAL_CONFIG', 'qualification decode contract changed')
        claim = root/(name+'.claim.json')
        if claim.exists():
            raise HarnessError('QUAL_CONSUMED', 'uncertain qualification call cannot be replayed')
        if (root/'runs'/name).exists():
            raise HarnessError('QUAL_CONSUMED', 'fresh output namespace required')
        write_json(layout.local(f'{run.PREFIX}/response_schema.json'),run.benchmark.JSON_SCHEMA)
        if name == 'resume':
            read_fd, write_fd = os.pipe()
            try:
                command = [sys.executable, '-m', 'r2_runtime.astra_qualification',
                    '--project-root', str(layout.project_root), '--proposal', str(EXPERIMENT_DIR/'astra_r2.yaml'),
                    '--base-model', str(base.resolve()), '--edited-model', str(edited.resolve()),
                    '_owned-worker', '--guard-fd', str(read_fd)]
                owned.drill(command, root, binding, pass_fds=(read_fd, lock_fd), cwd=EXPERIMENT_DIR, lease=(write_fd,os.urandom(32)))
            finally:
                os.close(write_fd); os.close(read_fd)
        else:
            args = _arguments(proposal,runtime,layout,edited,name)
            owned.create(claim, {'binding':binding,'requests_reserved':20,
                                 'arguments_sha256':canonical_sha256(args)})
            run._gpu(layout.project_root,layout,'batch-generate',args,ack=ack,role='evaluation')
            owned.create(root/(name+'.observed.json'), {
                'binding': binding, 'claim_sha256': sha256_file(claim),
                'output_sha256': sha256_file(root/'runs'/name/'completions.jsonl')})
        return {'run':name,'requests_reserved':40 if name == 'resume' else 20,'scored':False}


def _verify(proposal,layout,base,edited, *, publish=False):
    runtime,binding,root,original = _inputs(proposal,layout,base,edited)
    runs = {}
    evidence = {f:sha256_file(root/f) for f in ('manifest.json','original.jsonl','permuted.jsonl')}
    for name in RUNS:
        claim = read_json(root/(name+'.claim.json'))
        reservation = 40 if name == 'resume' else 20
        if claim.get('binding') != binding or claim.get('requests_reserved') != reservation:
            raise HarnessError('QUAL_EVIDENCE', 'claim binding or reservation differs')
        output = root/'runs'/name/'completions.jsonl'
        if name == 'resume':
            owned.verify_drill(root, binding)
            files = ['resume.claim.json','resume.killed.json','resume.observed.json','resume.before.jsonl','resume.killed.raw']
        else:
            observed = read_json(root/(name+'.observed.json'))
            args = _arguments(proposal,runtime,layout,edited,name)
            if (claim.get('arguments_sha256') != canonical_sha256(args)
                or observed != {'binding':binding,'claim_sha256':sha256_file(root/(name+'.claim.json')),
                                'output_sha256':sha256_file(output)}):
                raise HarnessError('QUAL_EVIDENCE', 'repeat invocation or output differs')
            files = [name+'.claim.json',name+'.observed.json']
        files.append(f'runs/{name}/completions.jsonl')
        evidence.update({f:sha256_file(root/f) for f in files})
        runs[name] = owned.journal(output)[1]
        if any(len(r.get('completion_token_ids',[])) > 128 for r in runs[name]):
            raise HarnessError('QUAL_FINISH', 'qualification token ceiling exceeded')
    parity = compare(original,runs)
    report = {'schema_version':'ehr-astra-r2-edited-qualification/v1', 'binding':binding,
              'passed':True,'scored':False,'requests_reserved':120,'owned_sigkill_resume':True,
              'comparison':parity,'evidence_sha256':evidence}
    if not publish:
        return report
    # Create-only public output. The parent must commit it before ANY benchmark.
    target = commitments.public_path(layout,'astra_edited_qualification.json')
    if target.exists():
        if read_json(target) != report:
            raise HarnessError('QUAL_EVIDENCE', 'immutable qualification receipt differs')
    else:
        owned.create(target,report)
    public_manifest = {'schema_version':'ehr-astra-r2-qualification-manifest/v1',
                       'binding':binding,'receipt_sha256':sha256_file(target),
                       'requests_reserved':{name:40 if name == 'resume' else 20 for name in RUNS},
                       'evidence_sha256':evidence}
    manifest_path = commitments.public_path(layout,'astra_edited_qualification.manifest.json')
    if manifest_path.exists():
        if read_json(manifest_path) != public_manifest:
            raise HarnessError('QUAL_EVIDENCE','immutable public manifest differs')
    else:
        owned.create(manifest_path,public_manifest)
    return report


def verify(proposal,layout,base,edited):
    with owned.writer(layout.local(f'{run.PREFIX}/qualification-writer.lock')):
        return _verify(proposal,layout,base,edited,publish=True)


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project-root',type=Path)
    p.add_argument('--proposal',type=Path,default=EXPERIMENT_DIR/'astra_r2.yaml')
    p.add_argument('--base-model',type=Path,required=True)
    p.add_argument('--edited-model',type=Path,required=True)
    sub=p.add_subparsers(dest='command',required=True)
    prepare_p=sub.add_parser('prepare');prepare_p.add_argument('--rows-ref',required=True)
    r=sub.add_parser('run');r.add_argument('--name',choices=RUNS,required=True);r.add_argument('--gpu-ack',action='store_true')
    sub.add_parser('verify')
    w=sub.add_parser('_owned-worker');w.add_argument('--guard-fd',type=int,required=True)
    a=p.parse_args(argv)
    try:
        proposal=astra_fixed.load_proposal(a.proposal);layout=Layout(find_project_root(a.project_root))
        result=(prepare(proposal,layout,a.base_model,a.edited_model,a.rows_ref) if a.command=='prepare' else
                execute(proposal,layout,a.base_model,a.edited_model,a.name,ack=a.gpu_ack) if a.command=='run' else
                worker(proposal,layout,a.base_model,a.edited_model,a.guard_fd) if a.command=='_owned-worker' else
                verify(proposal,layout,a.base_model,a.edited_model))
        print(json.dumps(result));return 0
    except HarnessError as exc:
        print(json.dumps({'error':exc.code,'message':exc.message}));return 2

if __name__=='__main__': raise SystemExit(main())
