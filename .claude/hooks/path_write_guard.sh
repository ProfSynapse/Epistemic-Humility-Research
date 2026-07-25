#!/usr/bin/env bash
# PreToolUse guard (Write|Edit|MultiEdit): write-target PATH policy. Two blocks:
#
#   (A) FROZEN BACKUP. `/mnt/f/Code/Epistemic-Humility-Research` is a read-only
#       frozen backup mount (AGENTS.md "Environment"). All real work happens in
#       the canonical ext4 checkout `/home/profsynapse/code/Epistemic-Humility-
#       Research`. The shell may start with cwd on the /mnt/f path, so a stray
#       absolute write can land in the backup. Never write there.
#
#   (B) SYNAPTIC-TUNER POLLUTION. `synaptic-tuner/` is a generic research-engine
#       SUBMODULE with its own ownership boundary (AGENTS.md "Boundaries"): "Do
#       not install root-project instructions or Epistemic-specific orchestration
#       inside it." Block writes that install this project's instruction/orches-
#       tration files at the submodule root or as skill/agent mirrors inside it:
#       synaptic-tuner/{CLAUDE.md,AGENTS.md} and synaptic-tuner/{.claude,.agents,
#       .codex,.skills}/*. (Ordinary code changes inside the submodule are fine
#       and are NOT touched.)
#
# These are ABSOLUTE blocks: a Write/Edit tool call carries no env-prefix, so
# there is no in-band bypass (unlike the Bash speed-bumps). If a genuine need
# arises, that is a deliberate settings change, not a per-call override.
# Exit 2 -> tool call blocked, stderr shown to the model.
set -u

payload=$(cat)
verdict=$(HOOK_PAYLOAD="$payload" python3 - <<'PYEOF'
import os, json

try:
    d = json.loads(os.environ.get("HOOK_PAYLOAD", ""))
except Exception:
    print("ALLOW"); raise SystemExit
ti = d.get("tool_input") or {}
path = ti.get("file_path") or ti.get("path") or ""
if not path:
    print("ALLOW"); raise SystemExit
p = os.path.normpath(path)

# (A) Frozen backup mount.
if p.startswith("/mnt/f/Code/Epistemic-Humility-Research"):
    print("FROZEN"); raise SystemExit

# (B) Synaptic-tuner instruction/orchestration pollution.
# Find a `synaptic-tuner` path component and inspect what follows it.
parts = p.split("/")
if "synaptic-tuner" in parts:
    i = parts.index("synaptic-tuner")
    tail = parts[i + 1:]
    if tail:
        # Root-level instruction file, or ANY depth CLAUDE.md/AGENTS.md.
        if tail[-1] in ("CLAUDE.md", "AGENTS.md"):
            print("TUNER"); raise SystemExit
        # Skill/agent mirror dirs installed inside the submodule.
        if tail[0] in (".claude", ".agents", ".codex", ".skills"):
            print("TUNER"); raise SystemExit
print("ALLOW")
PYEOF
)

case "$verdict" in
  FROZEN)
    echo "BLOCKED: this write targets the FROZEN BACKUP mount (/mnt/f/Code/Epistemic-Humility-Research), which is read-only (AGENTS.md 'Environment'). Redirect the write to the canonical checkout:
  /home/profsynapse/code/Epistemic-Humility-Research/<same relative path>
The shell can start with cwd on the /mnt/f path, so double-check you cd'd to the canonical checkout before building absolute paths." >&2
    exit 2 ;;
  TUNER)
    echo "BLOCKED: this write installs root-project instructions/orchestration inside the synaptic-tuner/ submodule, which has its own ownership boundary (AGENTS.md 'Boundaries'): do NOT install root-project instructions or Epistemic-specific orchestration there. Keep the submodule generic. Root-project instructions belong in the repo root (AGENTS.md is canonical; CLAUDE.md + skill mirrors are generated from it via bin/sync_skills.py, which itself must never write into synaptic-tuner/)." >&2
    exit 2 ;;
esac
exit 0
