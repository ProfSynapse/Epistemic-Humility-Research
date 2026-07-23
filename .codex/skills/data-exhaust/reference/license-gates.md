# License Gates

Per-source redistribution verdicts for row-level text in HF dataset exhaust.
This table is the single gate every row-level build consults before including
any generation text, question-derived answer text, or alias in a public
Hugging Face dataset. Aggregate artifacts (dose-response tables, direction
fits, manifests, AUROCs) carry no source text and are not gated by this
table; they still carry the hard exclusions below as a structural check, not
a license question.

The backlog license audit ("License audit: TriviaQA/PopQA/KUQ/SelfAware
redistribution", task #21) completed on 2026-07-12. The lead ran it directly
(the auditor agent stalled) and delivered the full table below, citing local
dataset cards (`datasets/kuq/dataset.md`, `datasets/selfaware/dataset.md`,
`datasets/popqa/dataset.md`, `datasets/triviaqa-rc-nocontext/dataset.md`) and
upstream sources verified against the raw HF README / GitHub repo. This
supersedes an earlier version of this table that only had the task tracker's
one-line summary and left KUQ/TriviaQA/PopQA/SelfAware unresolved.

This table's posture matches, and is cross-referenced by,
`docs/datasets/jspace-fresh-pool-public-census-plan.md`'s "Release Boundary"
and "Source Posture" sections (prior art for a published text-free release:
`professorsynapse/eh-jspace-fresh-pool-census-qwen3-4b`). That document
independently reached the same per-source posture for KUQ, SelfAware, PopQA,
and TriviaQA before this audit ran.

## Verdict vocabulary

Three dispositions, not two:

- `permitted`: row kept with every field, including text-bearing ones
  (`generation_text`, `answer_value`; see `reference/dataset-schema.md`).
- `permitted-with-conditions`: row kept with every field, but the built
  dataset's `README.md` MUST carry that source's `conditions` text verbatim
  (a license notice or an origin disclosure, not a usage restriction).
  `scripts/verify_exhaust.py` checks this.
- `text-free-only`: row kept, but every text-bearing field is stripped before
  the row is written. Row identity (`row_key`, `source`, `category_canon`),
  role/split/cell/model/arm/dose metadata, and every graded boolean or count
  our own graders produced all stay, since none of that is source text.
- `forbidden`: row dropped entirely, in any form, never even text-free.
- `pending-audit` (including any source with no table entry at all): row
  dropped entirely. This is NOT the same finding as `text-free-only` -- it
  means nobody has audited this source at all, not that an audit found the
  metadata safe. Fail closed here, not to the middle tier.

## Machine-readable table

`scripts/_license_gate.py` (imported by both `build_exhaust_dataset.py` and
`verify_exhaust.py`) parses the fenced YAML block below. Each entry:

- `key`: canonical source id, matched against a row's `source` field
  (case-insensitive, and also matched against `aliases`).
- `license`: what is currently known about the license, or `unknown`.
- `verdict`: one of `permitted`, `permitted-with-conditions`,
  `text-free-only`, `forbidden`, `pending-audit`.
- `conditions`: caveats, citation, disclosure text, or the reason for the
  current verdict. For `permitted-with-conditions`, this exact text is what
  gets checked for in the built dataset card.

A source with no matching entry is treated as `pending-audit` (fail closed).

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

  - key: kuq
    aliases: ["kuq", "kuq_unknowns_all", "kuq_knowns_unknowns"]
    license: "MIT"
    verdict: permitted
    conditions: >-
      Task #21 audit (2026-07-12, lead-run). Local card
      datasets/kuq/dataset.md: MIT. Verified upstream at
      https://huggingface.co/datasets/amayuelas/KUQ. Preserve the MIT license
      and attribution in the dataset card.

  - key: selfaware
    aliases: ["selfaware", "self_aware", "self-aware"]
    license: "Apache-2.0"
    verdict: permitted-with-conditions
    conditions: >-
      Task #21 audit (2026-07-12, lead-run). Local card
      datasets/selfaware/dataset.md: Apache-2.0. Verified upstream at
      https://github.com/yinzhangyue/SelfAware. Preserve the Apache-2.0
      notice, and the dataset card MUST disclose that the unanswerable
      question text originates from Quora/HowStuffWorks per the SelfAware
      paper. This is a third-party origin disclosure, not a usage
      restriction: it does not block including SelfAware row text, it
      requires the disclosure to be present alongside it.

  - key: popqa
    aliases: ["popqa"]
    license: "not tagged on HF; no license statement in the upstream README"
    verdict: text-free-only
    conditions: >-
      Task #21 audit (2026-07-12, lead-run). Local card
      datasets/popqa/dataset.md notes a companion GitHub MIT license, but
      that does not establish redistribution terms for the HF dataset card
      itself: https://huggingface.co/datasets/akariasai/PopQA carries no
      license tag and no license statement (verified via the raw README).
      Text-free rows only: row_key, source ids, roles, splits, and graded
      boolean/count fields. No question/answer text and no model
      generations (a generation can quote the question back).

  - key: triviaqa
    aliases: ["triviaqa", "triviaqa-rc-nocontext"]
    license: "unknown"
    verdict: text-free-only
    conditions: >-
      Task #21 audit (2026-07-12, lead-run). Local card
      datasets/triviaqa-rc-nocontext/dataset.md: license unknown, official
      free-for-research-use. The HF mirror mandarjoshi/trivia_qa is tagged
      license: unknown, and the official site states verbatim "The
      University of Washington does not own the copyright of the questions
      and documents included in TriviaQA." Not permitted for raw text.
      Text-free rows only, same shape as popqa.

  - key: falseqa
    aliases: ["falseqa", "false_qa", "false-qa"]
    license: "TODO-pending-audit (no license identified; pr-workflow skill
      already flags FalseQA as a NO-LICENSE source for git-commit purposes)"
    verdict: pending-audit
    conditions: >-
      Not covered by the task #21 audit (that audit was scoped to
      TriviaQA/PopQA/KUQ/SelfAware). Carry the same caution from the
      git-commit containment rule (.skills/pr-workflow/SKILL.md) into HF
      row-level release. Do not default to permitted, and do not default to
      text-free-only, without a citable audit result for this source.
```

## Human-readable table

| source | license | verdict | conditions |
|---|---|---|---|
| `openmoss_cheng_idk` | none identified, vendored for internal use only | **forbidden** | hard exclusion, structural + table |
| `bridge_llama2_7b_chat` | gated Llama 2 + vendored Cheng IDK | **forbidden** | hard exclusion, structural + table |
| `kuq` | MIT (upstream-verified) | **permitted** | task #21 audit, 2026-07-12; preserve MIT license + attribution |
| `selfaware` | Apache-2.0 (upstream-verified) | **permitted-with-conditions** | task #21 audit; dataset card must disclose Quora/HowStuffWorks third-party origin |
| `popqa` | not tagged on HF, no license statement | **text-free-only** | task #21 audit; row_key/role/split/graded-flags only, no question/answer/generation text |
| `triviaqa` | unknown; UW disclaims question copyright | **text-free-only** | task #21 audit; same text-free shape as popqa |
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
