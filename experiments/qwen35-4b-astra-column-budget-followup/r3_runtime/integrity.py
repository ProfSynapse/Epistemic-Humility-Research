from .util import sha256_file
from . import commitments
BINDING_NAME="run_binding.json"

def binding_digest(layout):
    return sha256_file(commitments.public_path(layout, BINDING_NAME))


def evidence_stamp(cell, layout):
    return {**cell.stamp(), "run_binding_sha256": binding_digest(layout)}

