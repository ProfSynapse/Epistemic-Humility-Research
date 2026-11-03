"""Host CLI. Planning and validation never imply launch authority."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .engine_identity import inspect_engine
from .training_request import load_training_input


def main(argv=None):
    parser = argparse.ArgumentParser(prog="ehr-engine")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor")
    storage = sub.add_parser("host-storage")
    storage.add_argument("--config", type=Path, required=True)
    validate = sub.add_parser("validate-training")
    validate.add_argument("input", type=Path)
    plan = sub.add_parser("plan-pipeline")
    plan.add_argument("config")
    cli = sub.add_parser("cli")
    cli.add_argument("arguments", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    identity = inspect_engine(args.project_root)
    if args.command == "doctor":
        print(json.dumps(identity, indent=2))
    elif args.command == "host-storage":
        from .storage import configure_storage
        print(json.dumps(configure_storage(args.project_root, args.config), indent=2))
    elif args.command == "validate-training":
        request = load_training_input(args.input)
        print(json.dumps({"method": request.method.value, "input_digest": request.input_digest(),
                          "engine": identity}, indent=2))
    else:
        from .cli_boundary import EngineCLI
        boundary = EngineCLI(args.project_root)
        if args.command == "plan-pipeline":
            boundary.plan_pipeline(args.config)
        else:
            if not args.arguments:
                parser.error("cli requires an operation")
            boundary.run(args.arguments[0], args.arguments[1:])


if __name__ == "__main__":
    main()
