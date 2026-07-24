#!/usr/bin/env bash
# PostToolUse reminder (Write|Edit|MultiEdit): NON-BLOCKING nudges keyed on the
# written path. Emits hookSpecificOutput.additionalContext (exit 0) so the note
# reaches the model on its next request without blocking anything.
#
#   (7/8) experiment.yaml manifest -> validate + regen. The .githooks/pre-commit
#         HARD-enforces `exp validate` + `exp regen --check` at commit time; this
#         is the EARLY nudge so drift is caught before a stack of edits, not at
#         the commit wall.
#
#   (10)  Governed docs (AMENDMENT.md / PROTOCOL* / gate docs) -> read the
#         governing reference FIRST. Recent real failure: a retroactive gate
#         re-labelling was drafted that gate-diagnosticity.md explicitly forbids.
#
# Reminders only; if a doc was already read, ignore the nudge. This hook never
# blocks (a false-positive nudge costs one system line, not a blocked action).
set -u

payload=$(cat)
HOOK_PAYLOAD="$payload" python3 - <<'PYEOF'
import os, json

try:
    d = json.loads(os.environ.get("HOOK_PAYLOAD", ""))
except Exception:
    raise SystemExit(0)
ti = d.get("tool_input") or {}
path = ti.get("file_path") or ti.get("path") or ""
if not path:
    raise SystemExit(0)

base = os.path.basename(path)
parts = path.split("/")
low = path.lower()

msg = None

if base == "experiment.yaml" or (("experiments" in parts) and base.endswith(".yaml")):
    msg = ("Reminder: you edited an experiment manifest. Before committing, "
           "validate it and refresh the generated registry (the pre-commit hook "
           "enforces both, but catch drift now):\n"
           "  bin/validate-experiments\n"
           "  bin/exp regen        # then `bin/exp regen --check` to confirm current")
elif base == "AMENDMENT.md" or base.startswith("PROTOCOL") or "protocol" in [p.lower() for p in parts] \
        or ("gate" in base.lower()):
    msg = ("Reminder: you are editing a GOVERNED doc (amendment / protocol / "
           "gate). Before drafting or re-labelling, read the governing reference "
           "in .skills/experiment-runner/reference/ — do NOT act from a "
           "paraphrased rule:\n"
           "  - amendment-vs-lab-notebook.md  (pick the right instrument; don't mint an amendment for a smoke/re-run)\n"
           "  - gate-diagnosticity.md         (gates are pre-stated; retroactive gate re-labelling is forbidden)\n"
           "  - operator-discipline.md\n"
           "  - protocol-amendment-template.md\n"
           "And: never announce a verdict (SUCCESS/FAILED/FALSIFIED/INCONCLUSIVE/"
           "MIXED) from memory — run the registered roll-up instrument and quote "
           "its output.")

if msg:
    out = {"hookSpecificOutput": {
        "hookEventName": "PostToolUse",
        "additionalContext": msg}}
    print(json.dumps(out))
raise SystemExit(0)
PYEOF
exit 0
