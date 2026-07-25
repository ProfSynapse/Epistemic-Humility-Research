#!/usr/bin/env bash
# SessionStart re-grounding hook. After a compaction the model keeps a summary
# but LOSES the skill/instruction files it had read — and resumes acting on
# paraphrased rules. That is the single highest-yield moment to force the core
# invariants back into context. stdout from a SessionStart hook is added to the
# model's context (Claude Code hooks contract), so this prints a short pointer
# block plus the actual text of the highest-value rules.
#
# Fires on source in {compact, resume, clear, fork}. It SKIPS `startup`, where
# the project CLAUDE.md is already freshly loaded, to avoid redundancy.
#
# Kept deliberately short (a wall of text gets skimmed): pointers + the 4-5
# load-bearing rules, not the whole rulebook.
set -u

payload=$(cat)
source=$(HOOK_PAYLOAD="$payload" python3 - <<'PYEOF'
import os, json
try:
    d = json.loads(os.environ.get("HOOK_PAYLOAD", ""))
except Exception:
    print(""); raise SystemExit
print(d.get("source") or "")
PYEOF
)

case "$source" in
  compact|resume|clear|fork) ;;
  *) exit 0 ;;
esac

# Tailor the opening line to the trigger.
case "$source" in
  compact) lead="CONTEXT WAS JUST COMPACTED — the skill/instruction files you had read are GONE from context. Re-ground on these core invariants before acting; do not run on paraphrased rules:" ;;
  *)       lead="SESSION RE-GROUNDING ($source) — reload these core invariants before acting:" ;;
esac

cat <<EOF
================= EHR OPERATING INVARIANTS (auto re-injected) =================
$lead

1. CHECKOUT. Canonical working checkout: /home/profsynapse/code/Epistemic-Humility-Research
   /mnt/f/Code/Epistemic-Humility-Research is a FROZEN read-only backup — never write it.
   The shell may start with cwd on /mnt/f; cd to the canonical checkout explicitly.

2. PROTECTED main. Experiment/feature work goes on a BRANCH in its own worktree,
   merged via PR. Do NOT git commit/push on main. (Living tracking-doc commits to
   main are the only exception, and only via the experiment-wrapup workflow.)

3. SEARCH FIRST. The typed knowledge graph is the default entry point for ALL
   exploration. Run  bin/search <query> --limit 10  BEFORE any rg/grep/find or a
   fan-out search subagent. Restate this rule in every search subagent's prompt.

4. READ BEFORE YOU CITE. Never state a fact about a prior experiment (its design,
   gates, result, verdict, what it "showed") from memory, a session note, the KG,
   or a chat summary — open its governed doc first: experiments/<slug>/AMENDMENT.md
   is the SOLE source of truth. Never announce a verdict (SUCCESS / FAILED /
   FALSIFIED / INCONCLUSIVE / MIXED) from a remembered rule — RUN the registered
   roll-up instrument (e.g. cross_family_rollup.py) and quote its output. If you
   cannot cite the doc line, you do not know it yet.

5. GOVERNED-DOC DISCIPLINE. Before drafting/editing a protocol, gate, or amendment,
   read the governing reference in .skills/experiment-runner/reference/ :
     amendment-vs-lab-notebook.md  (match instrument to work; no amendment for a smoke/re-run)
     gate-diagnosticity.md         (gates are PRE-stated; retroactive re-labelling is forbidden)
     operator-discipline.md
     protocol-amendment-template.md

These are enforced by PreToolUse hooks where possible: bin/search-first, protected
main (bypass token EHR_MAIN_OK=1 for sanctioned tracking-doc commits), frozen-backup
writes, synaptic-tuner instruction pollution, and generated-mirror edits are BLOCKED
with the correct alternative in the message. A blocked call means re-route, not retry.
=============================================================================
EOF
exit 0
