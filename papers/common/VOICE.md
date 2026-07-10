# Voice guide for the epistemic humility papers

This is the tone bible for every paper in this program and its blog
companions. Every drafting agent reads this before touching a paper. The voice
fuses the PI's essay register with what a technical paper needs; the worked
examples below are the calibration reference. When in doubt, reread the
examples here and then write the section.

## The one principle everything else serves

These are papers about epistemic humility. They must enact it, not just study
it. The humility lives in the SCOPE of the claims, never in mealy wording. Say
exactly what the evidence supports, plainly, and stop.

Wrong: "Our results may perhaps suggest that the intervention could
potentially improve the behavior in some settings."

Right: "The intervention produced the behavior on 71% of held-out items; the
control produced it on 2%. This held on one model at one scale; we have not
tested whether it transfers." (Numbers here are invented; the point is the
shape.)

The first sentence hedges because the author is nervous. The second is honest
because the claim is fenced. Nervous hedging is banned. Fenced claims are the
house style.

## The empirical spine: predictions on the page

Every experiment in this program registers, before the run, a prediction from
the human PI and a prediction from the AI orchestrator, plus a falsifier and
gates that cannot move afterward. The papers show this machinery instead of
hiding it.

- Registered predictions appear in the text, including the misses. A wrong
  prediction is content, not embarrassment: an arc where a prediction failed
  twice before a null resolved cleanly is the method doing its job, and it
  reads that way on the page.
- Nulls are reported in the main text with the same care as wins. A
  well-characterized null (the dose curve, the collapse point, the decomposed
  failure) earns its numbers on the page.
- Every headline result names its kill criterion: what outcome, registered in
  advance, would have falsified it. If a result survived a falsifier, say
  what the falsifier was.
- Exploratory and confirmatory are never blended. Say which one a number is.

## Synthesis, not journey

The paper is the synthesis; the repository is the journey. Signed experiment
docs, notebooks, and run records already preserve every intermediate number,
wrong turn, and superseding audit, and the paper points there once. On the
page:

- A superseded number does not appear. If an audit replaced a measurement
  with a better-controlled one, the paper reports the controlled number as
  the finding, full stop. Do not print the old number and narrate its
  correction; the provenance trail holds that history for anyone who wants
  it.
- Registered predictions, gate misses, and falsifiers appear as compact
  registered facts (a sentence, a table row), not as story arcs. "One
  registered gate missed, by 0.001" is synthesis. Three paragraphs on how we
  first believed X, then discovered Y, then reran Z is a lab chronicle and
  belongs in the repo.
- The one place process is narrated is the AI-workflow methods section,
  because there the workflow IS the subject. Everywhere else, results
  sections state what is true and how we know, not the order in which we
  learned it.

## Sentence mechanics (this is most of the voice)

1. Long-then-short rhythm. Build a paragraph of explanation, then close it
   with a short declarative knife. "The early evidence is colder than the
   promise." "They don't." "Wrong." Use this at the moments that matter, not
   every paragraph, or it becomes a tic.

2. Second-person openings for intuition. "Try this as a thought experiment.
   You ask a model a question it should not be able to answer cleanly..."
   Use one per major concept, to seat the reader inside the problem before
   the formalism arrives.

3. Define every term of art inline, in plain language, at first use. The
   essays do this naturally: "epistemology (a big word for the study of
   knowledge)". Papers do the sober version: "the anchor position (the last
   prompt token, where we read the model's state before it begins to
   answer)". Never assume the reader carries our internal vocabulary.

4. Analogies that do real work. The intake form for ignorance. Three
   thermometers reading three different temperatures. An analogy earns its
   place by making a technical distinction feel inevitable, then it retires.
   One good analogy per concept; never stack them.

5. First person, honestly. "We predicted X. We were wrong in a specific way,
   and the way we were wrong is the finding." The narrator of these papers
   is a lab thinking out loud, revising in public. Past positions get
   revisited by name ("We assumed the quantity would transfer across
   settings. It does not.").

6. Numbers live in sentences, not just tables. A table holds the grid; the
   prose says what the one number that matters is and why.

## Vocabulary and punctuation rules (hard)

- No em dashes. Use commas, colons, parentheses, or a new sentence.
- Never the phrase "load-bearing".
- Banned hedge-stack words: "may perhaps", "could potentially", "seems to
  suggest", "arguably". One qualifier per claim, chosen precisely.
- Banned LLM-ese: "delve", "crucially", "notably" as sentence openers,
  "it is worth noting that", "in the realm of".
- "We" is the lab (human PI + AI orchestrator + agents). Where authorship of
  a judgment matters, name the holder: "the PI predicted", "the orchestrator
  predicted", "the red-team agent refuted".
- Mechanism names are chosen once and reused verbatim. No elegant variation
  on technical terms.

## The paper/blog dial

Papers and blog posts share a spine: same claims, same numbers, same
registered predictions, same honesty about misses. What changes:

| Element | Paper | Blog |
|---|---|---|
| Philosophical framing (Socrates, aporia) | One paragraph max, usually the opening or closing | Full spine, welcome |
| Playful register ("GOATs", "spoiler alert") | No | Yes, sparingly |
| Closing dramatized dialogue | No | Yes, if it earns it |
| Long-then-short knife sentences | Yes | Yes |
| Second-person thought experiments | Introduction only | Anywhere |
| Registered-prediction tables | Yes, per experiment | Inline prose |
| Full dose curves and null characterization | Main text | Linked or summarized |

Draft the paper first in full voice; the blog version relaxes it, never the
reverse. Conservatizing a vivid draft for a reviewer is easy. Resuscitating a
dead one is not.

## Structure habits

- Sections open with the question they answer, in one sentence, before any
  apparatus.
- Every figure caption is a complete claim, readable without the body text.
- The introduction states what would have falsified the paper's thesis. The
  conclusion states what still could.
- Limitations sections are specific and quantified ("one pool, one scale,
  one family; the known nondeterminism source bounds per-item claims")
  rather than ritual ("more work is needed").
- Real headings, not bold run-ins. Structure is expressed with headings and
  subheadings at the proper level, never with a bolded phrase gluing a
  paragraph shut ("**The gate.** The gate is...") and never with bolded
  numbered mini-headings inside prose. If a block deserves a label, it
  deserves a heading; if it does not deserve a heading, it does not get a
  fake one. Genuine lists stay lists, unbolded.

## External-facing self-containment

Assume no reader ever opens the repository. The paper carries everything a
reader needs.

- Internal instrument names never appear in body prose: no amendment
  letters or codenames, no governed-doc filenames, no experiment slugs, no
  internal PR numbers. Describe the thing instead: "a pre-registered
  follow-up experiment", "the registered replication", "a pre-recorded
  adversarial audit".
- Pre-registration language is welcome; it is standard science vocabulary
  and stands on its own. What it cannot do is lean on the repo ("see the
  amendment document for details") to complete a claim.
- Repository pointers live in exactly one place: the provenance appendix,
  which maps each reported number to its artifact for readers who do go
  look. Body text never depends on that appendix to be understood.

## Worked example of the register

All numbers below are invented; the example shows shape and rhythm only.

Before (typical draft prose):

> It is worth noting that our intervention appears to demonstrate
> potentially significant improvements in the target behavior, although
> further investigation may be needed to fully understand the underlying
> mechanisms at play.

After (house voice):

> The intervention works under one condition and fails under the other, and
> the failure is not noise. Under condition A, the target behavior only
> rises as output quality falls: by the setting that produces the behavior
> in 9 of 10 items, almost none are usable. Under condition B, the two come
> apart. That decoupling is the finding. Whether it survives elsewhere is
> registered as the next experiment, and its falsifier is already on file.
