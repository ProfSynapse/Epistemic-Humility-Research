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

## Registration machinery stays offstage (hard)

Every experiment in this program registers predictions, falsifiers, and gates
before its run. The repository holds that machinery and the provenance
appendix points to it. The paper does not perform it. Everything is
inspectable, so body prose carries only the headlines, the major beats, and
the final data; anything with baggage points to the appendix or Limitations,
where the baggage is stated once.

- Registration machinery enters body prose only when it changed the claim: a
  falsifier fired, a gate failed and demoted a number, an adequacy floor was
  missed and a verdict became descriptive. Then say what happened and what
  the reader must now believe, in plain language, without the bookkeeping
  vocabulary.
- Never report that a falsifier did not fire, that a gate passed, or that an
  arm "was registered as descriptive so no claim is made". Passing machinery
  is silent machinery: the number would not be on the page otherwise, and
  narrating the non-event is metacommentary.
- "A pre-registered X" and its variants ("a registered replication", "fixed
  in advance", "locked before the run", "adversarially audited before the
  verdict") are banned in body prose and figure captions. No one talks like
  that in a research paper. If tier or registration status genuinely matters
  to the reader, it lives in the Limitations section or the provenance
  appendix.
- Prediction scoreboards (who called what band, what flipped which way) never
  appear in the paper. They live in the signed experiment docs.
- Nulls are still reported in the main text with the same care as wins; a
  well-characterized null earns its numbers on the page. It is reported as a
  finding, not narrated as a registration event.
- Exploratory versus confirmatory status is stated where it bounds a claim
  ("single seed", "one model"), in plain scope words, and the full tier
  bookkeeping lives in one compact Limitations paragraph.

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
- Gate misses and fired falsifiers that changed a claim appear as compact
  facts (a sentence, a table row), not as story arcs. Three paragraphs on how
  we first believed X, then discovered Y, then reran Z is a lab chronicle and
  belongs in the repo.
- The AI-workflow methods section reports the workflow as method: who does
  what, where the trust boundary sits, what the controls are. No worked
  examples of what happened on this paper, no prediction scoreboards, no
  misses retold. Everywhere else, results sections state what is true and
  how we know, not the order in which we learned it.
- Never explain science to scientists. Do not tell the reader why
  pre-registration matters, why falsifiers are stated, or why a miss is
  reported ("we state them because each could have fired" is a lecture).
  State the falsifier, state whether it fired, move on. The machinery shows
  its virtue by being used, not by being praised.

## Limitations live in the Limitations section (hard)

A limitation, disclosure, contamination note, scope fence, or instrument
caveat is stated once, in the Limitations section, quantified. Methods and
Results may point there ("limitations discussed in Section 6") but never
narrate the limitation in place, unless the number on the page is unreadable
without it; then one clause carries the essential fact and the full account
still lives in Limitations.

Methods sections describe instruments and procedures as they finally stood.
A number that is a finding (a flip rate, a re-grade outcome, a sensitivity
delta) is Results or Limitations content, never Methods content. The journey
to the final method is not narrated in Methods; if the path matters, it is a
Limitations note.

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

## No meta commentary

Meta commentary is prose that narrates the document instead of delivering
content: announcing what a section is about to do, commenting on the paper's
own claims, or describing the reporting choices mid-report. It is banned.

- No roadmap sentences ("each family is stated in full as a subheading
  below", "we take these up in order").
- No self-annotation of claims ("the plain-language version of this claim
  is", "the headline is stated to match it", "we report the distinction
  rather than pooling across it"). Say the thing in plain language the first
  time; make the reporting choice silently and let the labels on the numbers
  show it.
- No throat-clearing before content and no "this appendix/section describes"
  openers. Open with the content.

The test: if a sentence would survive with "this paper" or "we report" as its
subject and no number, definition, or claim in its predicate, cut it. This is
different from teaching voice, which guides the reader through the LOGIC of an
argument; that stays. Guiding the reader through the DOCUMENT goes.

## Teach, do not just report

The papers are accessible research: the reader is guided through the
reasoning, not handed conclusions to trust.

- Every acronym is spelled out at first use (best-of-n sampling, hindsight
  instruction relabeling), and every benchmark or dataset gets one clause of
  description before its name carries weight (what it measures, roughly what
  is in it).
- The paper's most important inferential steps are walked through explicitly,
  premise to conclusion, one step per sentence, so a reader outside the
  subfield can follow why the conclusion lands. The two or three paragraphs
  the whole paper turns on get the most patient writing in the paper, not the
  most compressed.
- A reader joining mid-conversation is a writing failure. Section openings
  give enough context that the section makes sense read cold.

## Series discipline

- Each paper stands alone. A reader of paper N needs no other paper in the
  series to follow the argument. Whatever context another program paper
  would supply is restated in a sentence or two where needed, with the
  citation; it is never delegated ("see the companion paper") for anything
  the current argument depends on.
- Back-citation only. Published or earlier-released program papers may be
  cited where genuinely needed, sparingly: over-citing our own prior work
  reads as marketing and breaks standalone reading. Cite them exactly like
  any external paper, by author and year. Never "the companion", "the
  companion diagnosis", "the program", "the synthesis", or another
  manuscript's section title as a citation handle. Unpublished or
  later-numbered program papers are never mentioned, teased, or cited.
  Future work is described as future work, without naming a manuscript.
- No repeated openings. Each paper's abstract and introduction are written
  fresh; reusing another program paper's framing sentence or first paragraph
  is banned, even paraphrased. Same rule for epigraphs: one distinct,
  well-attested quote per paper, chosen for that paper's thesis.
- Rolling dates, not frozen ones. Searches and evidence sweeps are dated "as
  of this writing" with the update practice stated once, not pinned to a
  single month that will read stale.

## GitHub rendering (hard)

The manuscripts are read on GitHub before anywhere else. Everything must
render there.

- Figures use standard markdown image syntax, `![alt text](figures/name.png)`
  with a relative path, followed by a bold "**Figure N.** caption" paragraph.
  Never Obsidian embeds (`![[...]]`).
- Math stays inside the macro set GitHub's LaTeX renderer supports. No
  `\operatorname` (use `\mathrm`), and any new macro gets checked against a
  rendered preview before merge.

## Vocabulary and punctuation rules (hard)

- No em dashes. Use commas, colons, parentheses, or a new sentence.
- Section cross-references are spelled out: "Section 4.2", never the silcrow
  ("§4.2"). Same in figure captions and appendices, and consistently across
  every paper in the series.
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
- Registration vocabulary is repository vocabulary (see "Registration
  machinery stays offstage"). Body prose describes an experiment by what it
  measured, never by its registration status, and never leans on the repo
  ("see the amendment document for details") to complete a claim.
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

## No research-journey narration (hard)

The paper reports what is true at the resolution the evidence reached. It
never narrates how the lab got there. This is "Synthesis, not journey"
applied specifically to seeds and registrations.

- A result is reported once, at its final seed count, as one story. Never a
  seed-1 finding followed by a replication that confirms it, never a
  before-and-after arc, never a subsection whose subject is the replication.
- Per-number seed support is stated plainly and in place: "across three
  seeds", "at seed 1 only", "the three-seed mean". That label does the work
  a narrated arc would have done, in four words.
- Registration mechanics stay out of the body and out of figure captions.
  No "a replication registered before any result existed", no "was
  registered as a secondary, descriptive pattern", no account of which
  threshold was fixed when, no "the falsifier did not fire".
- Nothing in this program is published, so nothing can be retracted or
  withdrawn. A pattern that does not survive reseeding is simply not
  reported as a finding: say what holds and at what seed support, and stop.
- Registration bookkeeping lives in exactly two places. One compact
  Limitations paragraph names which results are single-seed exploratory,
  which carried registrations fixed before their runs, and which comparisons
  are descriptive. The provenance appendix links the artifacts.
