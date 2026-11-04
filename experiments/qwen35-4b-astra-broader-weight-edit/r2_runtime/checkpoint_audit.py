"""CPU full-checkpoint bridge to the parent-owned R2 constructor and public receipts.

No model generation, engine internals or R1 numerical construction. The parent
must authenticate/promote input arrays, original capture and handoff before use.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from .constructor import implementation, load_proposal
from .util import HarnessError, read_json, sha256_file, canonical_sha256
from .astra_fixed import _create_only, _json_bytes


def audit(proposal, *, handoff, arrays, prepare_report, spec, payload, base_model, edited_model, out):
    r=implementation();h=read_json(handoff);prepared=read_json(prepare_report)
    if sha256_file(arrays)!=h['arrays_sha256']: raise HarnessError('INPUT_HASH','handoff arrays changed')
    for key in ('model','development','patch'):
        if h[key]!=proposal.raw[key]: raise HarnessError('PROPOSAL','handoff differs from full R2 YAML')
    prop=r.proposal(h['model'],h['development'],h['patch'])
    z=np.load(arrays,allow_pickle=False)
    r.linear_consistency(z['U'],z['K'],z['outputs'],z['W'],bias_present=h.get('bias_present'))
    con=r.construct(z['U'],z['K'],z['c'],z['W'],prop,u_keys=h['u_keys'],k_keys=h['k_keys'],r1_columns=h['r1_columns'])
    inputs_digest=canonical_sha256({key:{'shape':list(z[key].shape),'dtype':str(z[key].dtype),
        'sha256':r.f.sha256_bytes(np.ascontiguousarray(z[key]).tobytes())} for key in ('U','K','c','W','outputs')})
    if (prepared.get('proposal_sha256')!=prop.sha256 or prepared.get('inputs_digest')!=inputs_digest
        or prepared.get('roster_digest')!=canonical_sha256([h['u_keys'],h['k_keys'],h['r1_columns']])
        or prepared.get('construction')!=con.report()
        or prepared.get('patch',{}).get('spec_sha256')!=sha256_file(spec)
        or prepared.get('patch',{}).get('payload_sha256')!=sha256_file(payload)):
        raise HarnessError('PREPARE_BINDING','constructor preparation differs from exact inputs/spec/payload')
    manifest=read_json(edited_model/'mechinterp-weight-export.manifest.json')
    if (manifest.get('spec',{}).get('sha256')!=sha256_file(spec)
        or manifest.get('payload',{}).get('sha256')!=sha256_file(payload)
        or len(manifest.get('tensors',[]))!=1):
        raise HarnessError('EXPORT_BINDING','public engine export receipt differs')
    report=r.audit_checkpoint(base_model,edited_model,con,prop,z['U'],z['K'],
                             receipt_tensor=manifest['tensors'][0],export_manifest=manifest)
    report.update(proposal_sha256=proposal.sha256,constructor_proposal_sha256=prop.sha256,
        prepare_report_sha256=sha256_file(prepare_report),spec_sha256=sha256_file(spec),
        payload_sha256=sha256_file(payload),handoff_sha256=sha256_file(handoff),arrays_sha256=sha256_file(arrays))
    _create_only(out,_json_bytes(report))
    return {'passed':report['passed'],'audit_sha256':sha256_file(out),'launch_authority':False}


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('proposal','handoff','arrays','prepare-report','spec','payload','base-model','edited-model','out'):
        p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args(argv)
    try:
        kwargs=vars(a).copy();proposal=load_proposal(kwargs.pop('proposal'))
        print(json.dumps(audit(proposal,**kwargs)));return 0
    except HarnessError as exc:
        print(json.dumps({'error':exc.code,'message':exc.message}));return 2

if __name__=='__main__':raise SystemExit(main())
