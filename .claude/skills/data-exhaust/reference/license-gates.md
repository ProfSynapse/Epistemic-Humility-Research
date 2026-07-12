# License Gates

Per-source redistribution verdicts for row-level text in HF dataset exhaust.
This table is the single gate every row-level build consults before including
any generation text, question text, or alias in a public Hugging Face dataset.
Aggregate artifacts (dose-response tables, direction fits, manifests, AUROCs)
carry no source text and are not gated by this table; they still carry the
hard exclusions below as a structural check, not a license question.

The backlog license audit ("License audit: TriviaQA/PopQA/KUQ/SelfAware
redistribution", task #21) completed on 2026-07-12 while this skill was being
built. Its full table was parked at `scratchpad/license_audit_verdicts.md` for
delivery to this skill, but that file lives in the auditor agent's own
session-scoped scratchpad and was not reachable from here; only the tracker's
one-line-per-source summary was available. KUQ and TriviaQA got unambiguous,
single-line verdicts with no caveat to transcribe, so they are filled in below.
SelfAware's audited verdict carries a caveat ("Quora-origin caveat") whose exact
scope was not transcribed anywhere reachable from this skill; it is left
`pending-audit` rather than guessed, per the same fail-closed rule this table
already applies to unknown sources. PopQA's audited finding ("no HF license tag")
is not a permissive verdict either, so it also stays `pending-audit`. The lead
should reconcile this table against the actual audit file once it lands, and
in particular confirm or correct the SelfAware caveat before it is marked
`permitted`. Do not fill in any OTHER permissive verdict ahead of a citable
audit result, even if a similar claim already appears on an existing HF dataset
card (for example `docs/public-artifacts.md`'s `eh-readout-rows` row); those
notes are provenance for a prior release, not a substitute for this table.

## Machine-readable table

`scripts/build_exhaust_dataset.py` and `scripts/verify_exhaust.py` parse the
fenced YAML block below. Each entry:

- `key`: canonical source id, matched against a row's `source` field
  (case-insensitive, and also matched against `aliases`).
- `license`: what is currently known about the license, or `unknown`.
- `verdict`: one of `permitted`, `forbidden`, `pending-audit`. Only
  `permitted` allows row text through the row-level builder.
- `conditions`: caveats, citation, or the reason for the current verdict.

A source with no matching entry is treated as `pending-audit` (fail closed),
not `permitted`.

```yaml
sources:
  - key: openmoss_cheng_idk
    aliases: ["openmoss", "cheng_idk", "cheng-idk", "cheng"]
    license: "none identified; vendored for internal use only"
    verdict: forbidden
    conditions: >-
      HARD EXCLUSION. OpenMOSS Cheng IDK training data is vendored under a
      DO-NOT-REDISTRIBUTE containment rail (see
      archive/docs/architecture/phase1-pipeline.md and
      archive/experiment/phase1/data/.gitignore). Never publish row text,
      question text, aliases, or derived training data from this source to
      HF or any other public surface, regardless of any other setting in
      this file. This verdict cannot be changed by editing this table alone;
      the containment check in scripts/verify_exhaust.py hardcodes it too.

  - key: bridge_llama2_7b_chat
    aliases: ["bridge_llama2_7b_chat", "llama2_7b_chat_bridge", "llama2-7b-chat-bridge"]
    license: "gated Llama 2 license + vendored Cheng IDK training data"
    verdict: forbidden
    conditions: >-
      HARD EXCLUSION. archive/experiment/phase1/data/.gitignore excludes the
      entire bridge_llama2_7b_chat/ output directory from git; the bridge
      cells are local-lane only and never hub-published (see
      archive/docs/architecture/phase1-pipeline.md). Same hardcoded backstop
      as openmoss_cheng_idk applies.

  - key: triviaqa
    aliases: ["triviaqa", "triviaqa-rc-nocontext"]
    license: "unknown; UW disclaims question copyright"
    verdict: forbidden
    conditions: >-
      Task #21 audit result (2026-07-12, tracker summary): NOT PERMITTED for
      raw text. UW disclaims question copyright and the license is unknown.
      Not a hard exclusion in the openmoss/bridge sense, but the audited
      verdict for this workflow is forbidden until a different license basis
      is established; do not flip to permitted on the strength of the
      eh-readout-rows card's informal "research-use" note alone.

  - key: popqa
    aliases: ["popqa"]
    license: "no HF license tag identified"
    verdict: pending-audit
    conditions: >-
      Task #21 audit result (2026-07-12, tracker summary): UNCLEAR, no HF
      license tag found. Not a permissive finding; stays pending-audit rather
      than being marked permitted or forbidden on an unclear basis.

  - key: kuq
    aliases: ["kuq", "kuq_unknowns_all", "kuq_knowns_unknowns"]
    license: "MIT (upstream-verified)"
    verdict: permitted
    conditions: >-
      Task #21 audit result (2026-07-12, tracker summary): PERMITTED, MIT,
      upstream-verified. No caveat recorded.

  - key: selfaware
    aliases: ["selfaware", "self_aware", "self-aware"]
    license: "Apache-2.0, with a Quora-origin caveat (exact scope not yet
      transcribed here)"
    verdict: pending-audit
    conditions: >-
      Task #21 audit result (2026-07-12, tracker summary): PERMITTED-WITH-
      CONDITIONS, Apache-2.0, Quora-origin caveat. The exact caveat text (for
      example whether it restricts a Quora-sourced subset of rows) was parked
      in the auditor's own session-scoped scratchpad
      (scratchpad/license_audit_verdicts.md) and was not reachable when this
      table was written. Deliberately left pending-audit rather than
      permitted: do not flip this to permitted without transcribing the actual
      condition text into this field first, since "permitted with a condition
      not yet on record" is not the same as "permitted."

  - key: falseqa
    aliases: ["falseqa", "false_qa", "false-qa"]
    license: "TODO-pending-audit (no license identified; pr-workflow skill
      already flags FalseQA as a NO-LICENSE source for git-commit purposes)"
    verdict: pending-audit
    conditions: >-
      Carry the same caution from the git-commit containment rule
      (.skills/pr-workflow/SKILL.md) into HF row-level release. Do not default
      to permitted just because a prior aggregate-only release excluded it
      cleanly.
```

## Human-readable table

| source | license | verdict | conditions |
|---|---|---|---|
| `openmoss_cheng_idk` | none identified, vendored for internal use only | **forbidden** | hard exclusion, structural + table |
| `bridge_llama2_7b_chat` | gated Llama 2 + vendored Cheng IDK | **forbidden** | hard exclusion, structural + table |
| `kuq` | MIT, upstream-verified | **permitted** | task #21 audit, 2026-07-12, no caveat |
| `selfaware` | Apache-2.0, Quora-origin caveat | pending-audit | task #21 audit found permitted-with-conditions; caveat text not yet transcribed, left pending rather than guessed |
| `popqa` | no HF license tag identified | pending-audit | task #21 audit: unclear, not a permissive finding |
| `triviaqa` | unknown; UW disclaims question copyright | **forbidden** | task #21 audit: not permitted for raw text |
| `falseqa` | TODO-pending-audit (no license identified) | pending-audit | not covered by task #21; awaiting a separate license audit |

Keep this table and the YAML block above in sync by hand; `verify_exhaust.py`
checks the YAML block's structural well-formedness (every entry has `key`,
`license`, `verdict` in the allowed set, and `conditions`), not that the prose
table matches it byte for byte.

## Hard exclusions (structural, not license-based)

These are enforced in code independent of this table, so an accidental table
edit cannot reopen them:

- Any source key or alias matching `openmoss`, `cheng`, or `cheng_idk`.
- Any source key or alias matching `bridge_llama2_7b_chat` (any separator
  variant) or any path containing that literal directory name.
- Any row or file path under a directory containing a `DO-NOT-REDISTRIBUTE`
  marker, or under a `.gitignore`-excluded raw-data directory recorded in this
  repo (for example `archive/experiment/phase1/data/bridge_llama2_7b_chat/`).

`scripts/verify_exhaust.py` scans built dataset dirs for these patterns and
fails loudly if any appears, regardless of what the YAML table says.
