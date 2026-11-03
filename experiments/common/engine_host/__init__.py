"""EHR-owned integration: public v1 contracts and an explicit legacy CLI boundary.

No engine source tree is inserted into sys.path. Provider operations, authority,
credentials, and durable stores are supplied by the calling host.
"""

from .engine_identity import inspect_engine
from .training_request import load_training_input, plan_training

__all__ = ["inspect_engine", "load_training_input", "plan_training"]
