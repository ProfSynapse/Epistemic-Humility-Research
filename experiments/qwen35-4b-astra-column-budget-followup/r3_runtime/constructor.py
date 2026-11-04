"""Explicit bridge to parent-owned hs20_r3. Never imports the R1 constructor."""
from dataclasses import dataclass
from pathlib import Path
import yaml
from .util import HarnessError, canonical_sha256

HISTORICAL_ROLES=('confab','known_correct_answered')

def implementation():
    try:
        from hs20_r3 import astra_r3
        return astra_r3
    except ImportError as exc:
        raise HarnessError('CONSTRUCTOR_UNAVAILABLE', 'integrate the independently reviewed parent-owned hs20_r3 package') from exc

@dataclass(frozen=True)
class Proposal:
    raw: dict
    sha256: str
    @property
    def patch(self): return self.raw['patch']
    @property
    def group_size(self): return self.raw['development']['counts']
    @property
    def tensor(self): return self.patch['tensor']
    @property
    def shape(self): return tuple(self.patch['shape'])
    @property
    def sigma(self): return self.patch['sigma_c']

def load_proposal(path):
    raw=yaml.safe_load(Path(path).read_text())
    if raw.get('schema_version')!='ehr-astra-broad-edit/v1' or raw.get('proposal_id')!='hs20-wide1024-fixed2sigma-ideal046-r3':
        raise HarnessError('PROPOSAL','requires exact R3 contract')
    # Constructor validates the numerical subset; runtime binds the entire YAML.
    r=implementation()
    try: r.proposal(raw['model'],raw['development'],raw['patch'])
    except r.HarnessError as exc: raise HarnessError(exc.code,exc.message) from exc
    return Proposal(raw,canonical_sha256(raw))

def construct(*args,**kwargs):
    r=implementation()
    try: return r.construct(*args,**kwargs)
    except r.HarnessError as exc: raise HarnessError(exc.code,exc.message) from exc

def bf16_raw_sha256(value): return implementation().bf16_raw_sha256(value)
def select_roster(*args,**kwargs): return implementation().f.select_roster(*args,**kwargs)
def normalize_question(value): return implementation().f.normalize_question(value)
def roster_digest(value): return implementation().f.roster_digest(value)
