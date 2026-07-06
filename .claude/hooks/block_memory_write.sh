#!/usr/bin/env bash
# PreToolUse guard (Write|Edit|MultiEdit): forbid writing to the agent-private
# auto-memory store. This repo is KG-first: durable knowledge lives IN the repo
# (session notes, KG atoms, amendment docs), never in ~/.claude/projects/*/memory.
#
# USER DIRECTIVE 2026-07-06: "EVERYTHING needs to stay in this repo and is KG
# first ... you want to save a memory you save it as a session note." Memory as a
# citable store is also the failure vector behind repeated stale-claim errors, so
# it is disabled here entirely.
#
# On a blocked write, nudge toward the session-note path. Exit 2 -> tool call
# blocked, stderr shown to the model.
set -u

payload=$(cat)
path=$(HOOK_PAYLOAD="$payload" python3 - <<'PYEOF'
import os, json
try:
    d = json.loads(os.environ.get("HOOK_PAYLOAD", ""))
except Exception:
    print(""); raise SystemExit
ti = d.get("tool_input") or {}
print(ti.get("file_path") or ti.get("path") or "")
PYEOF
)

case "$path" in
  */.claude/projects/*/memory/*|*/.claude/projects/*/MEMORY.md)
    echo "BLOCKED: writing to the agent-private memory store is disabled in this repo. This project is KG-first and everything durable stays IN the repo. Save this instead as a SESSION NOTE so it is findable by bin/search and the knowledge graph:
  python3 .agents/skills/experiment-runner/scripts/research_session.py checkpoint --session <docs/sessions/NNNN...> --summary '...'
(or 'init' to start a new one). For a cross-experiment finding, ingest it into the KG (kg-ingest skill). For an experimental FACT, the amendment doc is the source of truth, not a note." >&2
    exit 2 ;;
esac
exit 0
