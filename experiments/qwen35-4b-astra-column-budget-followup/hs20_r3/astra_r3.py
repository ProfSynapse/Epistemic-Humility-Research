"""hs20-wide1024-fixed2sigma-ideal046-r3. Numerical construction only; never launches models.

All public numeric entry points force one BLAS thread. CLI accepts authenticated
host handoff arrays, not raw private rows. Host must authenticate capture/journal,
roster, source/runtime/direction before handoff (see HANDOFF.md).
"""
from __future__ import annotations
import argparse
import copy
import json
import math
from dataclasses import dataclass
from pathlib import Path
import numpy as np
from threadpoolctl import threadpool_limits
from . import frozen as f

HarnessError = f.HarnessError
TENSOR = 'model.language_model.layers.19.mlp.down_proj.weight'
SHAPE = (2560, 9216)
SIGMA = 1.576023489724997
ID = 'hs20-wide1024-fixed2sigma-ideal046-r3'
# Closed limits from plan sections 3/4. These cannot be overridden by YAML.
IDEAL = {'relative_frobenius_full': .027, 'relative_frobenius_columns': .180,
         'maximum_column_relative_l2': .460, 'U_rms_sigma': 3.6,
         'K_rms_sigma': .45, 'K_max_sigma': 1.8, 'all_max_sigma': 7.2,
         'entries_changed': 2621440}
REALIZED = {'relative_frobenius_full': .030, 'relative_frobenius_columns': .200,
            'maximum_column_relative_l2': .500, 'U_rms_sigma': 4.,
            'K_rms_sigma': .50, 'K_max_sigma': 2., 'all_max_sigma': 8.,
            'error_rms_sigma': .25, 'error_max_sigma': .50, 'off_c_relative': .10,
            'entries_changed': 2621440}

@dataclass(frozen=True)
class Proposal:
    raw: dict
    sha256: str
    @property
    def patch(self): return self.raw['patch']
    @property
    def tensor(self): return TENSOR
    @property
    def shape(self): return SHAPE
    @property
    def sigma(self): return SIGMA


def proposal(model: dict, development: dict, patch: dict) -> Proposal:
    """R1-compatible fields; reject conflicting scientific values, never ignore them."""
    expected = {'tensor': TENSOR, 'shape': list(SHAPE), 'columns': 1024,
                'sigma_c': SIGMA, 'decoder_block': 19, 'operation': 'add_rank_one',
                'variance_ddof': 0, 'eta_multiplier': 1e-6, 'q_relative_norm_min': 1e-6,
                'nominal_sigma': 2., 'maximum_modified_tensors': 1,
                'maximum_modified_entries': 2621440, 'maximum_relative_frobenius': .03,
                'maximum_selected_columns_relative_frobenius': .20,
                'known_anchor_rms_sigma_max': .50}
    # The host's declarative contract and the closed construction must agree.
    # Missing values receive the frozen defaults for synthetic library callers.
    expected.update({
        'alpha': 2*SIGMA, 'scale_rule': 'fixed_2_sigma_no_rescaling',
        'unit_norm_tolerance': 1e-6, 'factor_check_tolerance': 1e-9,
        'ideal_mean_sigma_tolerance': 1e-5, 'receipt_relative_norm_tolerance': 1e-6,
        'ideal_guards': {
            'maximum_relative_frobenius': .027,
            'maximum_selected_columns_relative_frobenius': .180,
            'maximum_column_relative_l2': .460, 'unknown_mean_sigma': 2.,
            'maximum_unknown_rms_sigma': 3.6, 'maximum_known_rms_sigma': .45,
            'maximum_known_abs_sigma': 1.8, 'maximum_all_abs_sigma': 7.2},
        'realized_guards': {
            'minimum_modified_entries': 1048576, 'maximum_modified_entries': 2621440,
            'minimum_broad_columns': 768, 'minimum_entries_per_broad_column': 512,
            'maximum_relative_frobenius': .030,
            'maximum_selected_columns_relative_frobenius': .200,
            'maximum_column_relative_l2': .500,
            'minimum_unknown_mean_sigma': 1.8, 'maximum_unknown_mean_sigma': 2.2,
            'maximum_unknown_rms_sigma': 4., 'maximum_known_rms_sigma': .50,
            'maximum_known_abs_sigma': 2., 'maximum_all_abs_sigma': 8.,
            'maximum_vector_error_rms_sigma': .25,
            'maximum_vector_error_abs_sigma': .50,
            'maximum_off_direction_relative_frobenius': .10}})
    obsolete = {'full_norm_scale_margin', 'column_norm_scale_margin'} & patch.keys()
    if obsolete: raise HarnessError('R1_SCALE_CAP', 'R1 min-cap fields must be removed')
    for key, value in expected.items():
        if key in patch and patch[key] != value:
            raise HarnessError('PROPOSAL', 'conflicting frozen field: '+key)
    if model.get('repo') != 'Qwen/Qwen3.5-4B' or model.get('revision') != '851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a':
        raise HarnessError('MODEL', 'wrong model/revision')
    if model.get('dtype') != 'bfloat16': raise HarnessError('DTYPE', 'requires bfloat16')
    if development.get('counts') != {'confab': 64, 'known_correct_answered': 64}:
        raise HarnessError('GROUPS', 'requires 64 rows in each historical role')
    if development.get('capture', {}).get('hidden_state', 20) != 20:
        raise HarnessError('SITE', 'requires hidden state 20')
    raw = copy.deepcopy({'model': model, 'development': development,
                         'patch': {**patch, **expected}, 'proposal_id': ID})
    return Proposal(raw, f.canonical_sha256(raw))


def bf16_bits(value):
    a = f._finite_array('bf16 array', value, 2)
    with np.errstate(over='ignore', invalid='ignore'):
        b = np.ascontiguousarray(a, dtype='<f4')
    if not np.isfinite(b).all() or not np.array_equal(a, b.astype(np.float64)):
        raise HarnessError('NOT_BF16', 'lossy float32 conversion')
    bits = b.view('<u4')
    if np.any(bits & 65535): raise HarnessError('NOT_BF16', 'non-bf16 input')
    return (bits >> 16).astype('<u2')


def bf16_raw_sha256(value): return f.sha256_bytes(bf16_bits(value).tobytes())


def check_guards(metrics, *, realized):
    """Evaluate every finite scalar and inclusive table boundary, collecting all failures."""
    limits = REALIZED if realized else IDEAL
    failures = []
    for key, limit in limits.items():
        val = metrics[key]
        if not math.isfinite(val) or val > limit: failures.append(key)
    lo, hi = (1.8, 2.2) if realized else (2.-1e-5, 2.+1e-5)
    if not math.isfinite(metrics['U_mean_sigma']) or not lo <= metrics['U_mean_sigma'] <= hi:
        failures.append('U_mean_sigma')
    if realized:
        for key, minimum in [('entries_changed', 1048576), ('broad_columns', 768)]:
            if not math.isfinite(metrics[key]) or metrics[key] < minimum: failures.append(key+'_minimum')
    for key, val in metrics.items():
        if np.isscalar(val) and not math.isfinite(val) and key not in failures: failures.append(key)
    return {'passed': not failures, 'terminal': bool(failures), 'failures': failures,
            'metrics': metrics, 'launch_authority': False}

@dataclass(frozen=True)
class Construction:
    columns: list[int]
    scores: list[float]
    eta: float
    c: np.ndarray
    v: np.ndarray
    alpha: float
    sigma: float
    shape: tuple
    base_sha256: str
    ideal: dict
    def report(self):
        return {'columns': self.columns, 'scores': self.scores, 'eta': self.eta,
                'c': self.c.tolist(), 'v': self.v.tolist(), 'alpha': self.alpha,
                'sigma': self.sigma, 'shape': list(self.shape), 'base_sha256': self.base_sha256,
                'ideal': self.ideal, 'limiting_term': 'fixed_2sigma'}


def _inputs(U, K, c, W, u_keys, k_keys):
    U, K, c, W = [f._finite_array(n,a,d) for n,a,d in [('U',U,2),('K',K,2),('c',c,1),('W',W,2)]]
    if U.shape != (64,9216) or K.shape != U.shape or W.shape != SHAPE or c.shape != (2560,):
        raise HarnessError('INPUT_SHAPE', 'requires registered full shapes')
    if any(len(keys)!=64 or len(set(keys))!=64 or any(not isinstance(k,str) or not k for k in keys)
           for keys in (u_keys,k_keys)) or set(u_keys)&set(k_keys):
        raise HarnessError('GROUPS', 'missing, duplicate or overlapping row keys')
    if abs(np.linalg.norm(c)-1.) > 1e-6: raise HarnessError('DIRECTION', 'do not renormalize direction')
    bf16_bits(W)
    return U,K,c,W


def _metrics(D, W, S, c, U, K, ideal=None):
    DS, WS = D[:, S], W[:, S]
    den = [float(np.linalg.norm(W)), float(np.linalg.norm(WS))]
    col_den = np.linalg.norm(WS,axis=0)
    if not all(math.isfinite(x) and x>0 for x in den) or np.any(col_den<=0) or not np.isfinite(col_den).all():
        raise HarnessError('ZERO_DENOMINATOR', 'base tensor/block/column norm invalid')
    wc = c @ DS
    pu,pk = U[:,S]@wc/SIGMA, K[:,S]@wc/SIGMA
    dn = float(np.linalg.norm(D))
    m = {'relative_frobenius_full': dn/den[0], 'relative_frobenius_columns': float(np.linalg.norm(DS))/den[1],
         'maximum_column_relative_l2': float(np.max(np.linalg.norm(DS,axis=0)/col_den)),
         'U_mean_sigma': float(pu.mean()), 'U_rms_sigma': float(np.sqrt(np.mean(pu**2))),
         'K_rms_sigma': float(np.sqrt(np.mean(pk**2))), 'K_max_sigma': float(np.max(np.abs(pk))),
         'all_max_sigma': float(np.max(np.abs(np.concatenate([pu,pk])))),
         'entries_changed': int(np.count_nonzero(D))}
    details={'U_writes_sigma':pu.tolist(), 'K_writes_sigma':pk.tolist(),
             'per_column_changed_counts':np.count_nonzero(DS,axis=0).tolist(),
             'per_column_relative_l2':(np.linalg.norm(DS,axis=0)/col_den).tolist(),
             'per_column_energy_fraction':(np.sum(DS**2,axis=0)/dn**2).tolist() if dn else [0.]*len(S),
             'delta_frobenius':dn}
    if ideal is not None:
        err = (DS-ideal) @ np.concatenate([U[:,S],K[:,S]]).T
        errnorm = np.linalg.norm(err,axis=0)/SIGMA
        m.update(broad_columns=int(np.sum(np.count_nonzero(DS,axis=0)>=512)),
                 error_rms_sigma=float(np.sqrt(np.mean(errnorm**2))), error_max_sigma=float(np.max(errnorm)),
                 off_c_relative=float(np.linalg.norm(DS-np.outer(c,wc)))/dn if dn else math.inf)
    if not all(np.isfinite(np.asarray(v)).all() for v in details.values()):
        raise HarnessError('NONFINITE', 'nonfinite report intermediate')
    return m, details


@threadpool_limits.wrap(limits=1)
def construct(U, K, c_hat, W, prop, *, u_keys, k_keys, r1_columns, **unused):
    if unused: raise HarnessError('ARGUMENT', 'unsupported constructor overrides')
    U,K,c,W = _inputs(U,K,c_hat,W,u_keys,k_keys)
    S,scores,eta = f.select_support(U,K,columns=1024,eta_multiplier=1e-6)
    old,_,_ = f.select_support(U,K,columns=32,eta_multiplier=1e-6)
    if list(r1_columns)!=old or not set(old)<=set(S): raise HarnessError('R1_SUPPORT', 'top32 differs from commitment')
    u,k=U.mean(axis=0)[S],K.mean(axis=0)[S]
    un=float(np.linalg.norm(u)); kk=float(k@k)
    q=u.copy() if kk==0 else u-k*float(k@u)/kk
    qu=float(q@u)
    if un==0 or np.linalg.norm(q)<=1e-6*un or not math.isfinite(qu) or qu<=0:
        raise HarnessError('DEGENERATE', 'collinear or zero key')
    v=q/qu
    if not np.isfinite(v).all() or abs(v@u-1)>1e-9 or abs(v@k)>1e-9*max(1,np.linalg.norm(v)*np.linalg.norm(k)):
        raise HarnessError('FACTOR_CHECK', 'key identity failed')
    alpha=2*SIGMA
    D=np.zeros_like(W); D[:,S]=alpha*np.outer(c,v)
    metrics,details=_metrics(D,W,S,c,U,K)
    ideal=check_guards(metrics,realized=False); ideal['details']=details
    return Construction(S,scores,eta,c.copy(),v,alpha,SIGMA,SHAPE,bf16_raw_sha256(W),ideal)


@threadpool_limits.wrap(limits=1)
def emulate(con, W):
    """Independent RNE implementation. Multiply outer, then scale, then add in float32.

    No torch and no engine implementation imported. Do not fuse these operations.
    """
    if not con.ideal['passed']: raise HarnessError('IDEAL_REFUSAL', 'terminal ideal refusal')
    if bf16_raw_sha256(W)!=con.base_sha256: raise HarnessError('BASE_HASH','changed base')
    c,v=con.c.astype(np.float32),con.v.astype(np.float32)
    with np.errstate(over='ignore',invalid='ignore'):
        delta=np.multiply(c[:,None],v[None,:],dtype=np.float32)
        delta=np.multiply(delta,np.float32(con.alpha),dtype=np.float32)
        added=np.add(np.asarray(W[:,con.columns],dtype=np.float32),delta,dtype=np.float32)
        bits=added.view(np.uint32)
        rounded=((bits+np.uint32(0x7fff)+((bits>>16)&1))>>16).astype(np.uint16)
        values=(rounded.astype(np.uint32)<<16).view(np.float32)
    if not np.isfinite(values).all() or not np.isfinite(delta).all(): raise HarnessError('NONFINITE','float32/bf16 overflow')
    # The public engine preserves the old bytes when rounded values compare
    # equal. In particular, adding +0 must not turn a stored -0 into +0.
    prior=np.asarray(W[:,con.columns],dtype=np.float32)
    values=np.where(values!=prior,values,prior)
    result=np.asarray(W,dtype=np.float64).copy(); result[:,con.columns]=values
    return result


@threadpool_limits.wrap(limits=1)
def audit_realized(con, prop, U, K, base_weight, edited_weight, *, receipt_tensor=None):
    if not con.ideal['passed']: raise HarnessError('IDEAL_REFUSAL','terminal ideal refusal')
    W=f._finite_array('base',base_weight,2); E=f._finite_array('edited',edited_weight,2)
    if W.shape!=SHAPE or E.shape!=SHAPE: raise HarnessError('INPUT_SHAPE','wrong readback shape')
    if bf16_raw_sha256(W)!=con.base_sha256: raise HarnessError('BASE_HASH','changed base')
    bf16_bits(E)
    U,K,_,_=_inputs(U,K,con.c,W,[str(i) for i in range(64)],['k'+str(i) for i in range(64)])
    D=E-W; S=con.columns
    metrics,details=_metrics(D,W,S,con.c,U,K,con.alpha*np.outer(con.c,con.v))
    report=check_guards(metrics,realized=True)
    off=D.copy(); off[:,S]=0
    if np.any(off): report['failures'].append('OFF_SUPPORT')
    expected=emulate(con,W)
    if bf16_raw_sha256(expected)!=bf16_raw_sha256(E): report['failures'].append('ARITHMETIC_MISMATCH')
    if receipt_tensor is not None:
        if (receipt_tensor.get('name')!=TENSOR or receipt_tensor.get('entries_changed')!=metrics['entries_changed']
            or not math.isclose(float(receipt_tensor.get('delta_frobenius',math.nan)),details['delta_frobenius'],rel_tol=1e-6)):
            report['failures'].append('RECEIPT_MISMATCH')
    report.update(details=details, receipt_checked=receipt_tensor is not None, base_sha256=con.base_sha256,
                  edited_sha256=bf16_raw_sha256(E))
    report['passed']=not report['failures']; report['terminal']=not report['passed']
    return report


def emit_patch(prop, con, tensor, binding, *, out_dir, checkpoint_ref, payload_ref, export_ref):
    if not con.ideal['passed']: raise HarnessError('IDEAL_REFUSAL','terminal ideal refusal')
    if tensor.get('name')!=TENSOR or tensor.get('dtype')!='bfloat16' or tuple(tensor.get('shape',()))!=SHAPE or tensor.get('sha256')!=con.base_sha256:
        raise HarnessError('TENSOR_BINDING','wrong tensor/site/shape/hash')
    if binding['files_sha256']!=prop.raw['model']['files_sha256']: raise HarnessError('BINDING','wrong shards')
    data=f.payload_bytes(con)
    spec=f.build_spec(prop,con,tensor,binding,checkpoint_ref=checkpoint_ref,payload_ref=payload_ref,payload_sha=f.sha256_bytes(data),export_ref=export_ref)
    spec['operations'][0]['id']='astra_r3'
    import yaml
    out=Path(out_dir)
    if out.exists(): raise HarnessError('OUTPUT_EXISTS','fresh create-only output root required')
    out.mkdir(parents=True,mode=0o700)
    ph=f._create_only(out/'payload.safetensors',data)
    sh=f._create_only(out/'spec.yaml',yaml.safe_dump(spec,sort_keys=False).encode())
    return {'spec_sha256':sh,'payload_sha256':ph,'spec':spec}


@threadpool_limits.wrap(limits=1)
def linear_consistency(U, K, outputs, W, *, bias_present):
    if bias_present is not False:
        raise HarnessError('BIAS', 'bias absence must be established by host')
    x=np.concatenate([U,K])
    y=f._finite_array('captured outputs',outputs,2)
    if x.shape!=(128,9216) or y.shape!=(128,2560):
        raise HarnessError('INPUT_SHAPE','wrong capture input/output shapes')
    expected=x @ W.T
    errors=np.linalg.norm(y-expected,axis=1)
    limits=1e-6+.01*np.linalg.norm(expected,axis=1)
    if not np.isfinite(expected).all() or not np.isfinite(errors).all() or not np.isfinite(limits).all():
        raise HarnessError('NONFINITE','nonfinite linear consistency')
    if np.any(errors>limits): raise HarnessError('CAPTURE_LINEAR','capture outputs disagree with W @ input')
    return {'maximum_l2_error':float(errors.max()),'rows':128,'passed':True}


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=['prepare','audit'])
    p.add_argument('--handoff',type=Path,required=True,help='JSON model/development/patch + keys/top32 + hashes')
    p.add_argument('--arrays',type=Path,required=True,help='NPZ U,K,c,W; audit also edited')
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--prepare-report',type=Path)
    p.add_argument('--spec',type=Path)
    p.add_argument('--payload',type=Path)
    for key in ('reference-report','reference-origin'):
        p.add_argument('--'+key,type=Path,required=True)
    for key in ('reference-report-sha256','reference-origin-sha256'):
        p.add_argument('--'+key,required=True)
    a=p.parse_args(argv)
    try:
        if a.out.exists(): raise HarnessError('OUTPUT_EXISTS','fresh output directory required')
        h=json.loads(a.handoff.read_text()); prop=proposal(h['model'],h['development'],h['patch'])
        if f.sha256_file(a.arrays)!=h['arrays_sha256']: raise HarnessError('INPUT_HASH','handoff arrays changed')
        z=np.load(a.arrays,allow_pickle=False)
        consistency=linear_consistency(z['U'],z['K'],z['outputs'],z['W'],bias_present=h.get('bias_present'))
        con=construct(z['U'],z['K'],z['c'],z['W'],prop,u_keys=h['u_keys'],k_keys=h['k_keys'],r1_columns=h['r1_columns'])
        inputs_digest=f.canonical_sha256({key: {'shape':list(z[key].shape),'dtype':str(z[key].dtype),'sha256':f.sha256_bytes(np.ascontiguousarray(z[key]).tobytes())} for key in ['U','K','c','W','outputs']})
        report={'inputs_digest':inputs_digest,'roster_digest':f.canonical_sha256([h['u_keys'],h['k_keys'],h['r1_columns']]),'proposal_sha256':prop.sha256,'handoff_sha256':f.sha256_file(a.handoff),'construction':con.report(), 'linear_consistency':consistency, 'launch_authority':False}
        from . import reference
        report['reference_proposal']=reference.verify(report, report=a.reference_report,
            report_sha256=a.reference_report_sha256, origin=a.reference_origin, origin_sha256=a.reference_origin_sha256)
        if a.command=='audit':
            if not all([a.prepare_report,a.spec,a.payload]): raise HarnessError('PREPARE_BINDING','audit requires prepare report, spec and payload')
            prepared=json.loads(a.prepare_report.read_text())
            for key in ['inputs_digest','roster_digest','proposal_sha256','construction','linear_consistency','reference_proposal']:
                if prepared.get(key)!=report[key]: raise HarnessError('PREPARE_BINDING','audit input differs: '+key)
            if (prepared.get('patch',{}).get('spec_sha256')!=f.sha256_file(a.spec) or prepared.get('patch',{}).get('payload_sha256')!=f.sha256_file(a.payload)):
                raise HarnessError('PREPARE_BINDING','spec/payload differs or preparation refused')
            report['prepare_report_sha256']=f.sha256_file(a.prepare_report)
        if con.ideal['passed']:
            predicted=emulate(con,z['W'])
            report['independent_preexport_audit']=audit_realized(con,prop,z['U'],z['K'],z['W'],predicted)
            if a.command=='audit':
                report['readback_audit']=audit_realized(con,prop,z['U'],z['K'],z['W'],z['edited'],receipt_tensor=h.get('receipt_tensor'))
            elif report['independent_preexport_audit']['passed']:
                # Recheck bytes at the serialization boundary after CPU emulation.
                report['reference_proposal']=reference.verify(report,report=a.reference_report,
                    report_sha256=a.reference_report_sha256,origin=a.reference_origin,origin_sha256=a.reference_origin_sha256)
                report['patch']=emit_patch(prop,con,h['tensor'],h['binding'],out_dir=a.out/'patch',checkpoint_ref=h['checkpoint_ref'],payload_ref=h['payload_ref'],export_ref=h['export_ref'])
        f._create_only(a.out/'report.json',f._json_bytes(report))
        passed=con.ideal['passed'] and report.get('readback_audit',report.get('independent_preexport_audit',{})).get('passed',False)
        print(json.dumps({'passed':passed,'report':str(a.out/'report.json')}))
        return 0 if passed else 3
    except HarnessError as exc:
        print(json.dumps({'error':exc.code,'message':exc.message,'terminal':True})); return 2
    except (KeyError, TypeError, ValueError, OSError) as exc:
        print(json.dumps({'error':'HANDOFF_INPUT','category':type(exc).__name__,'terminal':True})); return 2



def audit_checkpoint(base_dir, edited_dir, con, prop, U, K, *, receipt_tensor, export_manifest):
    """Reload both safetensors checkpoints and audit every tensor and sidecar.

    Receipt/manifest are public engine records. No engine implementation imported.
    The host still authenticates the receipt, manifest and immutable root identities.
    """
    from safetensors import safe_open
    base_dir,edited_dir=Path(base_dir),Path(edited_dir)
    def inventory(root):
        if root.is_symlink(): raise HarnessError('EXPORT_PATH','symlink root')
        hashes={}; targets={}; shard_hashes={}; sidecars={}
        for path in sorted(root.rglob('*')):
            if path.is_symlink(): raise HarnessError('EXPORT_PATH','symlink export member')
            if not path.is_file(): continue
            name=path.relative_to(root).as_posix()
            if path.suffix=='.safetensors':
                shard_hashes[name]=f.sha256_file(path)
                with safe_open(path,framework='pt',device='cpu') as sf:
                    for key in sf.keys():
                        if key in hashes: raise HarnessError('EXPORT_DUP','duplicate tensor')
                        t=sf.get_tensor(key)
                        # Hash actual stored dtype bytes, not a converted representation.
                        import torch
                        hashes[key]=(str(t.dtype),list(t.shape),f.sha256_bytes(t.view(torch.uint8).numpy().tobytes()))
                        if key==TENSOR: targets[key]=t.float().numpy().astype(np.float64)
            elif name!='mechinterp-weight-export.manifest.json':
                sidecars[name]=path.read_bytes()
        return hashes,targets,shard_hashes,sidecars
    bh,bt,bs,bc=inventory(base_dir); eh,et,es,ec=inventory(edited_dir)
    failures=[]
    if set(bh)!=set(eh) or TENSOR not in bt or TENSOR not in et:
        raise HarnessError('EXPORT_INVENTORY','tensor inventory changed/missing target')
    expected_storage=('torch.bfloat16',list(SHAPE))
    if bh[TENSOR][:2]!=expected_storage or eh[TENSOR][:2]!=expected_storage:
        raise HarnessError('EXPORT_TARGET_STORAGE','base and edited target must retain exact bf16 dtype and shape')
    if bh[TENSOR][2]!=con.base_sha256:
        raise HarnessError('BASE_HASH','stored target bytes differ from the construction base')
    changed=[key for key in bh if bh[key]!=eh[key]]
    if changed!=[TENSOR]: failures.append('MODIFIED_TENSORS')
    if bs!=prop.raw['model']['files_sha256']: failures.append('BASE_SHARDS')
    if set(bs)!=set(es): failures.append('SHARD_INVENTORY')
    # Identical index bytes are a stronger check than unchanged index semantics.
    if bc!=ec: failures.append('SIDECARS')
    report=audit_realized(con,prop,U,K,bt[TENSOR],et[TENSOR],receipt_tensor=receipt_tensor)
    report['failures'].extend(failures)
    tensors=export_manifest.get('tensors',[])
    if (len(tensors)!=1 or tensors[0].get('name')!=TENSOR
        or tensors[0].get('after_sha256')!=eh[TENSOR][2]
        or eh[TENSOR][2]!=report['edited_sha256']):
        report['failures'].append('MANIFEST_TENSOR')
    report.update(base_shards=bs,edited_shards=es,base_tensors=bh,edited_tensors=eh,
                  sidecar_sha256={k:f.sha256_bytes(v) for k,v in bc.items()},checkpoint_reloaded=True)
    report['passed']=not report['failures']; report['terminal']=not report['passed']
    return report

if __name__=='__main__': raise SystemExit(main())
