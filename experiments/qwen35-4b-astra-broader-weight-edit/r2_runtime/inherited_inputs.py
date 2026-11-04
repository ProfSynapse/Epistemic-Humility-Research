"""CPU-only inherited R1 capture -> R2 constructor handoff. No inference or edit.

Promotion schema and invocation are documented in INHERITED_INPUTS.md. The
reviewed origin digest is an external trust anchor, not a self-issued approval.
"""
from __future__ import annotations
import argparse
import io
import json
import math
import os
from pathlib import Path, PurePosixPath
import numpy as np
import yaml
from threadpoolctl import threadpool_limits
from . import astra_fixed as frozen, astra_capture, capture, astra_benchmark
from .constructor import load_proposal, Proposal
from .astra_run import require_signed
from .util import HarnessError, sha256_file, sha256_bytes, canonical_sha256

ORIGIN_SCHEMA = 'ehr-inherited-capture-origin/v1'

def require(condition, code):
    if not condition:
        raise HarnessError(code, 'inherited input verification refused')

def read(path):
    return json.loads(Path(path).read_bytes())

def member(root, name):
    require(isinstance(name, str) and name and '\\' not in name, 'ORIGIN_PATH')
    p = PurePosixPath(name)
    require(not p.is_absolute() and all(x not in ('..', '.') for x in p.parts), 'ORIGIN_PATH')
    root = Path(root)
    require(root.is_dir() and not root.is_symlink(), 'ORIGIN_PATH')
    result = root
    for part in p.parts:
        result = result / part
        require(not result.is_symlink(), 'ORIGIN_PATH')
    require(result.is_file(), 'ORIGIN_PATH')
    return result

def authenticated_origin(root, path, expected):
    require(sha256_file(path) == expected, 'ORIGIN_HASH')
    origin = read(path)
    require(origin['schema_version'] == ORIGIN_SCHEMA and
            origin['origin_experiment'] == 'qwen35-4b-hs20-native-weight-edit' and
            origin['promotion_destination'].startswith('experiments/common/') and
            isinstance(origin['origin_path'],str) and bool(origin['origin_path']) and
            origin['numpy_version'] == np.__version__, 'ORIGIN_IDENTITY')
    require(bool(origin['files']) and bool(origin['source_files']), 'ORIGIN_EMPTY')
    for name, digest in origin['files'].items():
        require(sha256_file(member(root, name)) == digest, 'ORIGIN_MEMBER_HASH')
    for name, local in origin['source_files'].items():
        require(local in origin['files'], 'ORIGIN_SOURCE')
    return origin

def original_lineage(root, origin, prop, paths, capture_dir):
    """Authenticate R1 identities without pretending their renderer/proposal was R2."""
    reuse = prop.raw['development']['reuse']
    def bound(role, path):
        item = origin['artifacts'][role]
        require(item['path'] in origin['files'] and
                sha256_file(path) == origin['files'][item['path']], 'ORIGIN_ARTIFACT')
        require(member(root, item['path']).read_bytes() == Path(path).read_bytes(), 'ORIGIN_ARTIFACT')
    for role, path in paths.items():
        bound(role, path)
    bound('capture_manifest', capture_dir/'manifest.json')
    freeze = read(paths['freeze'])
    require(sha256_file(paths['freeze']) == reuse['r1_patch_freeze_sha256'], 'FREEZE_HASH')
    for role in ('roster', 'request', 'prepare_report', 'capture_manifest'):
        item = origin['artifacts'][role]
        actual = capture_dir/'manifest.json' if role == 'capture_manifest' else paths[role]
        require(freeze['artifacts'].get(item['original_ref']) == sha256_file(actual), 'FREEZE_ARTIFACT')
    require(sha256_file(paths['roster']) == reuse['original_roster_sha256'] and
            sha256_file(paths['request']) == reuse['capture_request_sha256'] and
            sha256_file(capture_dir/'manifest.json') == reuse['capture_manifest_sha256'], 'REUSE_HASH')
    readiness = read(paths['readiness'])
    require(readiness['passed'] is True and readiness['target_inference_performed'] is False,
            'READINESS')
    for original, local in origin['source_files'].items():
        require(readiness['source_module_sha256'].get(original) == origin['files'][local], 'SOURCE_HASH')
    require(set(origin['source_files']) == set(readiness['source_module_sha256']), 'SOURCE_INVENTORY')
    r1_path = member(root, origin['source_files']['astra_r1.yaml'])
    r1_raw = yaml.safe_load(r1_path.read_bytes())
    r1_sha = sha256_file(r1_path)
    require(freeze['proposal_sha256'] == r1_sha, 'SOURCE_PROPOSAL')
    require(all(r1_raw['model'].get(k)==prop.raw['model'].get(k)
                for k in ('repo','revision','dtype','files_sha256')), 'SOURCE_MODEL')
    require(r1_raw['prompts']['P-struct'] == prop.raw['prompts']['P-struct'], 'SOURCE_PROMPT')
    r1 = Proposal(r1_raw, r1_sha)
    roster = frozen.load_roster(r1, paths['roster'])
    request = read(paths['request']); identity = request['identity']; run = identity['run']
    keys = roster['keys']['confab'] + roster['keys']['known_correct_answered']
    renderer = origin['source_files']['hs20_nwe/astra_render.py']
    require(request['schema_version'] == astra_capture.SCHEMA and
            request['proposal_sha256'] == r1_sha and
            request['fingerprint'] == astra_capture.fingerprint(identity), 'REQUEST_IDENTITY')
    require(run['render'] == {'callable':'hs20_nwe.astra_render:render_pstruct',
                             'source_sha256':origin['files'][renderer]}, 'REQUEST_SOURCE')
    require(run['revision'] == prop.raw['model']['revision'] and run['adapter'] is None and
            run['content_end'] is None and identity['manifest_extra'] is None, 'REQUEST_MODEL')
    for name, digest in freeze['base_files_sha256'].items():
        require(run['model']['files'].get(name) == digest, 'REQUEST_BASE')
    require(identity['families'] == ['anchor'] and identity['layers'] == [20] and
            identity['sites'] == [{'layer':19,'module':'mlp.down_proj','tensor':t} for t in ('input','output')] and
            identity['every_k'] == 1 and identity['max_new_tokens'] == 1 and
            identity['use_cache'] is True and identity['forward_only'] is True and
            identity['save_tensors'] is True and [x['row_key'] for x in identity['inputs']] == keys,
            'REQUEST_SETTINGS')
    meta_path = capture_dir/'capture.runlog.jsonl.meta.json'
    journal_path = capture_dir/'capture.runlog.jsonl'
    meta = read(meta_path)
    manifest = capture.load_manifest(capture_dir)
    journal = [json.loads(x) for x in journal_path.read_text().splitlines() if x.strip()]
    require(meta['complete'] is True and meta['fingerprint'] == request['fingerprint'] and
            journal == manifest['rows'] and manifest.get('weight_patch') is None and
            [x['row_key'] for x in journal] == keys, 'JOURNAL_IDENTITY')
    provenance = {'fingerprint':request['fingerprint'], 'request_sha256':sha256_file(paths['request']),
                  'meta_sha256':sha256_file(meta_path),'journal_sha256':sha256_file(journal_path)}
    require(provenance == readiness['request_journal_binding'], 'JOURNAL_HASH')
    tensor_files = {}
    for row in journal:
        end = row['prompt_len']-1
        require(end >= 0 and row['seq_total'] == row['prompt_len'] and row['content_end'] == end,
                'CAPTURE_POSITION')
        for field in ('capture_files','site_captures'):
            info = row[field]['anchor']
            # The original engine records positions on site captures only.
            # Residual position follows the authenticated forward-only request,
            # content_end and single-position tensor shape checked by read_row.
            if field == 'site_captures' or 'positions' in info:
                require(info['positions'] == [end], 'CAPTURE_POSITION')
            tensor_files[info['file']] = sha256_file(capture.verified_path(capture_dir, info))
    require(tensor_files == readiness['tensor_files'] and len(tensor_files) == 2*len(keys), 'CAPTURE_INVENTORY')
    report = read(paths['prepare_report'])
    require(report['proposal_sha256'] == r1_sha and report['capture_provenance'] == provenance and
            report['capture_manifest_sha256'] == sha256_file(capture_dir/'manifest.json') and
            report['roster_sha256'] == roster['roster_sha256'], 'PREPARE_LINEAGE')
    require(report['capture_files_digest'] == canonical_sha256(sorted(
        (r['row_key'], r['capture_files']['anchor']['sha256'], r['site_captures']['anchor']['sha256'])
        for r in journal)), 'PREPARE_CAPTURE_FILES')
    columns = report['construction']['columns']
    require(len(columns) == 32 and columns == sorted(set(columns)) and
            all(type(i) is int and 0 <= i < prop.shape[1] for i in columns), 'OLD_SUPPORT')
    return roster, manifest, report

def checkpoint(prop, root, listing_path):
    from safetensors import safe_open
    # NumPy safetensors does not decode BF16 in all pinned versions. CPU torch is
    # used only as a safe_open return representation, never as a model loader.
    import torch
    root = Path(root)
    model = prop.raw['model']; p = prop.patch
    index_path = member(root, 'model.safetensors.index.json')
    require(sha256_file(index_path) == model['index_sha256'], 'BASE_INDEX')
    index = read(index_path)['weight_map']
    require(set(index.values()) == set(model['files_sha256']), 'BASE_SHARDS')
    doc = read(listing_path)
    if 'success' in doc:
        require(doc['success'] is True, 'LISTING_ERROR'); doc = doc['data']
    require(doc.get('listing_truncated') is False, 'LISTING_TRUNCATED')
    files = {x['name']:x['sha256'] for x in doc['files']}
    require(len(files) == len(doc['files']) and files == model['files_sha256'] and
            doc['index_sha256'] == model['index_sha256'], 'LISTING_BINDING')
    names = set(); target = None
    for shard, digest in files.items():
        path = member(root, shard)
        require(sha256_file(path) == digest, 'BASE_SHARD_HASH')
        with safe_open(path, framework='pt', device='cpu') as sf:
            for name in sf.keys():
                require(name not in names and index.get(name) == shard, 'BASE_INVENTORY')
                names.add(name)
                if name == p['tensor']:
                    t = sf.get_tensor(name)
                    require(t.dtype == torch.bfloat16 and list(t.shape) == p['shape'], 'BASE_STORAGE')
                    raw = t.contiguous().view(torch.uint8).numpy().tobytes()
                    require(sha256_bytes(raw) == p['base_tensor_sha256'], 'BASE_TENSOR_HASH')
                    target = t.float().numpy().astype(np.float64)
    require(names == set(index) and p['tensor'] in names and
            p['tensor'].removesuffix('.weight')+'.bias' not in names, 'BASE_BIAS_INVENTORY')
    hits = [x for x in doc['tensors'] if x['name'] == p['tensor']]
    require(len(hits) == 1, 'LISTING_TARGET')
    tensor = hits[0]
    require(tensor['dtype'] == 'bfloat16' and tensor['shape'] == p['shape'] and
            tensor['sha256'] == p['base_tensor_sha256'] and tensor['file'] == index[p['tensor']], 'LISTING_TARGET')
    return target, tensor, {'files_sha256':files,'index_sha256':model['index_sha256']}

def direction(prop, path):
    require(sha256_file(path) == prop.patch['direction_sha256'], 'DIRECTION_HASH')
    doc = read(path); c = np.asarray(doc['vector'], dtype=np.float64)
    require(c.shape == (prop.shape[0],) and np.isfinite(c).all() and
            doc['layer'] == prop.patch['decoder_block'] and
            math.isclose(doc['sigma'], prop.sigma, rel_tol=1e-12) and
            abs(np.linalg.norm(c)-1) <= prop.patch['unit_norm_tolerance'], 'DIRECTION')
    return c

def array_records(arrays):
    return {k:{'shape':list(v.shape),'dtype':str(v.dtype),
               'sha256':sha256_bytes(np.ascontiguousarray(v).tobytes())} for k,v in arrays.items()}

def publish(out, arrays, handoff):
    out = Path(out)
    try: out.mkdir(mode=0o700, parents=False)
    except FileExistsError as exc: raise HarnessError('OUTPUT_EXISTS','fresh output required') from exc
    data = io.BytesIO(); np.savez(data, **arrays)
    handoff = dict(handoff, arrays_sha256=frozen._create_only(out/'arrays.npz', data.getvalue()),
                   array_records=array_records(arrays))
    frozen._create_only(out/'handoff.json', frozen._json_bytes(handoff))
    # Read back exactly what the constructor consumes before completing.
    with np.load(out/'arrays.npz', allow_pickle=False) as z:
        require(set(z.files) == set(arrays) and
                array_records({k:z[k] for k in z.files}) == handoff['array_records'], 'ARRAY_READBACK')
    complete = {'schema_version':'ehr-inherited-inputs-complete/v1','complete':True,
                'files':{k:sha256_file(out/k) for k in ('arrays.npz','handoff.json')},
                'launch_authority':False}
    frozen._create_only(out/'complete.json', frozen._json_bytes(complete))
    # Directory fsync is unavailable on some Windows/exFAT hosts; file fsync is
    # mandatory above, directory syncing is used where the OS supports it.
    if os.name != 'nt':
        fd = os.open(out, os.O_RDONLY | os.O_DIRECTORY)
        try: os.fsync(fd)
        finally: os.close(fd)
    return complete

@threadpool_limits.wrap(limits=1)
def prepare(a):
    require(not a.out.exists(), 'OUTPUT_EXISTS')
    require(a.config.name == 'astra_r2.yaml', 'CONFIG_PATH')
    require_signed(a.config.parent, runtime_role='capture')
    require(sha256_file(a.listing) == a.listing_sha256, 'LISTING_HASH')
    prop = load_proposal(a.config)
    origin = authenticated_origin(a.bundle_root, a.origin, a.origin_sha256)
    paths = {k:getattr(a,k) for k in ('freeze','readiness','roster','request','prepare_report')}
    roster, manifest, old = original_lineage(a.bundle_root, origin, prop, paths, a.capture_root)
    # Re-derive the exact historical rule through the frozen roster loader.
    require(sha256_file(a.fit) == prop.raw['development']['fit_sha256'], 'FIT_HASH')
    surfaces = {n:astra_benchmark.load_surface(prop,n,getattr(a,n)) for n in ('selfaware','ambigqa')}
    selected = frozen.select_roster(frozen._read_question_rows(a.fit),
        {n:frozen._questions(frozen._read_question_rows(getattr(a,n)),n) for n in surfaces},
        seed=prop.raw['development']['seed'], counts=prop.group_size)
    require(selected['keys'] == roster['keys'], 'ROSTER_RULE')
    Ukeys, Kkeys = [roster['keys'][r] for r in frozen.HISTORICAL_ROLES]
    groups = {'confab':[], 'known_correct_answered':[]}; outputs = []
    sites = [(19,'mlp.down_proj',t) for t in ('input','output')]
    for row in manifest['rows']:
        values = capture.read_row(a.capture_root,row,hidden_state=20,sites=sites)
        x,y = [values['sites'][capture.site_key(*s)] for s in sites]
        require(x.shape == (prop.shape[1],) and y.shape == (prop.shape[0],) and
                values['residual'].shape == (prop.shape[0],) and
                all(np.isfinite(v).all() for v in (x,y,values['residual'])), 'CAPTURE_SHAPE')
        groups['confab' if row['row_key'] in Ukeys else 'known_correct_answered'].append(x)
        outputs.append(y)
    base_files = read(a.freeze)['base_files_sha256']
    for name,digest in base_files.items():
        require(sha256_file(member(a.base_checkpoint,name)) == digest, 'ORIGINAL_BASE_FILE')
    W,tensor,binding = checkpoint(prop,a.base_checkpoint,a.listing)
    require(old['tensor'] == {k:tensor[k] for k in ('name','dtype','shape','sha256','file')} and
            old['binding'] == binding, 'PREPARE_BASE')
    arrays = {'U':np.stack(groups['confab']), 'K':np.stack(groups['known_correct_answered']),
              'c':direction(prop,a.direction), 'W':W, 'outputs':np.stack(outputs)}
    require(old['c_hat_sha256'] == prop.patch['direction_sha256'], 'PREPARE_DIRECTION')
    astra_capture.linear_consistency(arrays['U'],arrays['K'],arrays['outputs'],W,prop)
    for ref in (a.checkpoint_ref,a.spec_ref,a.payload_ref,a.export_ref):
        require(isinstance(ref,str) and ref.startswith('artifact://') and
                all(x not in ref for x in ('..','\\','\n')), 'ARTIFACT_REF')
    sources = {k:sha256_file(getattr(a,k)) for k in ('config','origin','freeze','readiness','roster',
        'request','prepare_report','fit','selfaware','ambigqa','direction','listing')}
    h = {'schema_version':'ehr-astra-r2-inherited-inputs/v1', 'launch_authority':False,
         'model':prop.raw['model'],'development':prop.raw['development'],'patch':prop.patch,
         'r2_contract':prop.raw,'numpy_version':np.__version__,
         'bridge_sha256':sha256_file(Path(__file__)), 'source_sha256':sources,'origin_files_sha256':origin['files'],
         'original_base_files_sha256':base_files,'base_binding':binding,'tensor':tensor,'binding':binding,'bias_present':False,
         'u_keys':Ukeys,'k_keys':Kkeys,'r1_columns':old['construction']['columns'],
         'checkpoint_ref':a.checkpoint_ref,'spec_ref':a.spec_ref,'payload_ref':a.payload_ref,'export_ref':a.export_ref}
    return publish(a.out,arrays,h)

def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('config','bundle-root','origin','capture-root','freeze','readiness','roster','request',
                 'prepare-report','fit','selfaware','ambigqa','direction','base-checkpoint','listing','out'):
        p.add_argument('--'+name,type=Path,required=True)
    for name in ('origin-sha256','listing-sha256','checkpoint-ref','spec-ref','payload-ref','export-ref'):
        p.add_argument('--'+name,required=True)
    a = p.parse_args(argv)
    try:
        result = prepare(a); print(json.dumps(result)); return 0
    except HarnessError as exc:
        print(json.dumps({'error':exc.code,'terminal':True})); return 2
    except (KeyError,TypeError,ValueError,OSError) as exc:
        print(json.dumps({'error':'INHERITED_INPUT','category':type(exc).__name__,'terminal':True})); return 2

if __name__ == '__main__': raise SystemExit(main())
