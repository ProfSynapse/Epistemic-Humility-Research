# R3 runtime implementation proposal

Ported from the full closed R2 checkout fa47ea5dc7c1b29dfa8228065c3aeed9a4a5fdca,
whose signed execution source was 620942f5c2ef1256fed51c784e254985a8070ca7.
R2_ORIGINS.json records exact source bytes, including original ORIGINS.json.
ORIGINS.json preserves the inherited R1 helper provenance unchanged.
The delivery manifest records every transformation. Historical R2 delivery
snapshots and qualification claims are not R3 evidence.

The sole numerical delta is ideal maximum_column_relative_l2 .45 to .46 in
both closed dictionaries. Ideal K RMS remains .45; realized column remains .50.
Package, slug, proposal, owned schema, config and host identities name R3.
Public engine and historical R1 source identities remain unchanged.

runtime/preparation.yaml retains reads and adds exactly reference_proposal
with report/report_sha256/origin/origin_sha256. It is authenticated separately
from the R1 inventory. Dry-run authenticates metadata without loading weights.
Signed prepare passes four --reference-* options to hs20_r3.astra_r3. That CLI
checks reproduced columns,c,v,alpha,shape,base_sha256,inputs_digest,roster_digest
before emulation or serialization. The old ideal verdict is excluded from
identity. Failure is REFERENCE_PROPOSAL, instrument-invalid, never budget-null.
checkpoint_audit rederives construction and repeats this authentication.
verified_chain rechecks reference bytes and identity, prepare/audit linkage,
completed hashes and emits both reference artifact hashes into public freeze.
No saved boolean grants reference authority.

All original signed-first, public engine, create-only, audit, qualification,
SIGKILL/EOF guardian, inherited lock, grading commitment and eight-cell gates
remain. No source signing, target computation, checkpoint/model qualification
or launch authority is provided by these files or local synthetic tests.
