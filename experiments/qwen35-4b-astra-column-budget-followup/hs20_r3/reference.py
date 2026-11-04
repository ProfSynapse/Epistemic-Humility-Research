"""Separately promoted R2 mathematical provenance, never execution authority."""
import json
import hashlib
from pathlib import Path
from .frozen import HarnessError, canonical_sha256

SOURCE_COMMIT = '620942f5c2ef1256fed51c784e254985a8070ca7'
OUTCOME_SHA256 = '1f5f863b15ff1a5a4ce56b7510badecaa0708cd841130ceaa665fa748d56656d'
KEYS = ('columns', 'c', 'v', 'alpha', 'shape', 'base_sha256')

def require(ok):
    if not ok: raise HarnessError('REFERENCE_PROPOSAL', 'instrument-invalid treatment reference')

def read_bytes(path, digest):
    path = Path(path)
    require(isinstance(digest, str) and len(digest)==64 and all(c in '0123456789abcdef' for c in digest))
    require(not any(p.is_symlink() for p in (path, *path.parents)))
    try: data = path.read_bytes()
    except OSError as exc:
        raise HarnessError('REFERENCE_PROPOSAL','instrument-invalid treatment reference') from exc
    require(hashlib.sha256(data).hexdigest()==digest)
    return data

def authenticate(report, report_sha256, origin, origin_sha256):
    """Read/hash the same bytes that are parsed; no weight loading."""
    doc = json.loads(read_bytes(report, report_sha256))
    o = json.loads(read_bytes(origin, origin_sha256))
    require(o.get('schema_version')=='ehr-previous-proposal-origin/v1')
    require(o.get('origin_experiment')=='qwen35-4b-astra-broader-weight-edit')
    require(o.get('origin_path')=='astra-r2/construction/report.json')
    require(o.get('source_commit')==SOURCE_COMMIT and o.get('outcome_sha256')==OUTCOME_SHA256)
    require(o.get('report_sha256')==report_sha256)
    # Require complete identity even when called only by metadata dry-run.
    identity(doc)
    return doc

def identity(doc):
    con=doc.get('construction', {})
    require(all(k in con for k in KEYS))
    require(all(k in doc for k in ('inputs_digest','roster_digest')))
    return {'construction':{k:con[k] for k in KEYS},
            **{k:doc[k] for k in ('inputs_digest','roster_digest')}}

def verify(current, *, report, report_sha256, origin, origin_sha256):
    previous=authenticate(report,report_sha256,origin,origin_sha256)
    expected=canonical_sha256(identity(previous))
    require(canonical_sha256(identity(current))==expected)
    return {'report_sha256':report_sha256,'origin_sha256':origin_sha256,'identity_sha256':expected}
