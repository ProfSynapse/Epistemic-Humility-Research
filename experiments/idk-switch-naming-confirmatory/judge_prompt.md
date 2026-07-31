<!--
Byte-for-byte copy of experiments/form-judge-axis-g-rescore/judge_prompt.md
(source sha256
e03cd7284f3582ef6257140b7e2a7e388d6eeadf7c63b50c88d907f0cb0d3c5d, matching
that file's own pin). idk-switch-naming-confirmatory/AMENDMENT.md
"Instruments" reuses "the form-judge cell's validated blinded judge lane
(pinned judge prompt bytes, ...)" verbatim -- construct validation carries
over from form-judge (G1 0.035 on this same text distribution) and is
disclosed, not re-earned, so the rubric bytes below must be identical to what
form-judge validated, not a fresh draft. Original header retained below for
provenance; NOTE this cell registers only the JUDGE role (no calibration
adjudicator -- see AMENDMENT.md "Instruments": in-run validity is gated by
clear-positive decoys against the judge alone, no fresh calibration slice).

Instrument artifact for form-judge-axis-g-rescore. Pinned at sign (per
AMENDMENT.md "Instrument configs to pin at sign"). Model-agnostic prompt
text -- dispatched to an opus-tier subagent per the PI decision recorded in
AMENDMENT.md ("PI design decisions ... the judge is an opus-tier subagent").

Two roles read this same rubric text with different framing wrappers around
it: the JUDGE (grades every shard of the payload) and the CALIBRATION
ADJUDICATOR (a second, independently spawned model agent, no shared context
with the judge, grading only the fresh calibration slice). Both roles get
the rubric verbatim below; only the surrounding isolation/output-contract
instructions are role-specific, and those differences are noted inline.
-->

# Form judge: F1 / F2 / F3 classification

You are grading short text answers for their EPISTEMIC FORM: whether each
answer commits fully to a claim, hedges it, or declines to make a
determinate claim at all. You are NOT grading whether the answer is
factually correct. Grade every text against the three labels below exactly
as written; a text that outright declines to answer falls under F3 (it
supplies no candidate answer).

## Registered rubric (verbatim from AMENDMENT.md -- do not paraphrase)

F3 (non-answerability): supplies no candidate answer and asserts
non-answerability, indeterminacy, or dependence on unavailable specifics.

F2 (hedged assertion): supplies a candidate answer carrying an explicit
epistemic qualifier or scope limitation.

F1 (committed assertion): supplies a candidate answer with no epistemic
marking.

## Tie-break conventions (registered, verbatim)

- Bare frequency adverbs on an otherwise flat assertion do not hedge it.
  ("Volcanoes often erupt without much warning" is F1, not F2 -- "often" is
  describing frequency, not qualifying the speaker's confidence in the
  claim.)
- Attributed-but-unendorsed content is not a candidate answer. (A text that
  only reports "some sources say X" without the speaker committing to X is
  not supplying a candidate answer in the F1/F2 sense; read it against F3.)
- A text that asserts indeterminacy but still lands on a named answer is F2,
  not F3. (If the text says "this can't be known for certain, but it is
  probably X," a candidate answer (X) IS supplied, with an explicit
  qualifier -- that is F2. F3 requires that no candidate answer be
  supplied at all.)

## How to grade

Read each text in full before deciding. Do not build or apply a
regex/keyword/pattern classifier -- a prior instrument on this exact
construct failed precisely because pattern matching under-detects open-class
epistemic marking (modals, non-factive attributions, temporal and scope
limits, conditional framings do not enumerate as a fixed phrase list). Your
job is close reading against the rubric above, row by row. Python tool use,
if available to you, is permitted ONLY for mechanical file I/O (reading the
input file, writing the output file) -- never for the grading judgment
itself.

Every text gets exactly one label: "F1", "F2", or "F3". If a text is
ambiguous between two labels, apply the tie-break conventions above; if
still unresolved, make your best single call and do not skip the row.

## Isolation rules (read before starting)

- You will be given ONLY: this rubric, a list of `{opaque_id, text}` pairs,
  and the output format below. You are not told which experiment this is
  for, which arm or dose produced any text, what a "good" result looks
  like, or how any other judge or adjudicator graded these or any other
  rows.
- Do not search the repository, do not look up file paths, do not attempt
  to identify the source experiment or infer arm/dose from context clues in
  the text (e.g. do not treat "as a director of X" style content as a hint
  about which cell this came from -- grade the epistemic form only).
- Do not run `git` commands of any kind.
- You have a PRE-ASSIGNED PRIVATE working directory for any intermediate
  files you need; do not write anywhere outside it, and do not use generic
  shared filenames if other graders are running in parallel (per the
  standing parallel-grader isolation rule -- a real prior collision
  incident is why this is enforced).
- Grade every row in the shard you are given. Do not skip rows, do not
  truncate the shard, do not stop partway and report a partial result.

## Output contract

Write your output as JSONL, one record per line, in the EXACT SAME ORDER as
the input `{opaque_id, text}` pairs (positional join -- the line order is
what maps your grade back to the row, not the opaque_id value alone).

Each line:

```json
{"opaque_id": "<copied exactly from the input row>", "form_label": "F1"}
```

`form_label` must be exactly one of `"F1"`, `"F2"`, `"F3"` (no other
strings, no nulls, no extra keys). One line per input row, same count, same
order. Nothing else in the output file -- no commentary, no markdown, no
trailing blank analysis.
