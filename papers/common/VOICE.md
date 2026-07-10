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

Wrong: "Our results may perhaps suggest that steering could potentially
improve abstention in some settings."

Right: "Steering at the mid-band layer produced coherent refusal on 73.5% of
held-out confabulations. The same write at the late layer produced 0%. This
held on one model family at one scale; we have not tested whether it
transfers."

The first sentence hedges because the author is nervous. The second is honest
because the claim is fenced. Nervous hedging is banned. Fenced claims are the
house style.

## The empirical spine: predictions on the page

Every experiment in this program registers, before the run, a prediction from
the human PI and a prediction from the AI orchestrator, plus a falsifier and
gates that cannot move afterward. The papers show this machinery instead of
hiding it.

- Registered predictions appear in the text, including the misses. A wrong
  prediction is content, not embarrassment. The Qwen3.5 recalibration arc,
  where the orchestrator was wrong twice before the null resolved, is a
  worked example of the method doing its job.
- Nulls are reported in the main text with the same care as wins. A
  well-characterized null (the dose curve, the collapse point, the decomposed
  failure) earns its numbers on the page.
- Every headline result names its kill criterion: what outcome, registered in
  advance, would have falsified it. If a result survived a falsifier, say
  what the falsifier was.
- Exploratory and confirmatory are never blended. Say which one a number is.

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
   revisited by name ("In the cross-family cells we assumed sigma-distance
   would transfer. It does not.").

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
- Mechanism names are chosen once and reused verbatim (the doubt gate, the
  caution snap, the workspace band). No elegant variation on technical terms.

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
- Limitations sections are specific and quantified ("held-out is one pool,
  one scale, one family; the batch-composition hazard bounds per-row
  determinism") rather than ritual ("more work is needed").

## Worked example of the register

Before (typical draft prose):

> It is worth noting that our steering intervention appears to demonstrate
> potentially significant improvements in abstention behavior, although
> further investigation may be needed to fully understand the underlying
> mechanisms at play.

After (house voice):

> The intervention works at one write site and fails at another, and the
> failure is not noise. At the late layer, refusal only rises as coherence
> falls: by the dose that produces 97% refusal-shaped outputs, 2 of 912 are
> well-formed. At the workspace band, the two come apart. That decoupling is
> the finding. Whether it survives on other families is registered as the
> next experiment, and its falsifier is already on file.
