# Weights-Level Consultation: Can Training or Architecture Replace the Runtime Thermostat?

_Status: literature scan + design memo, drafted 2026-08-28. Task: task-7eb629.
Scoping input for the successor actuation study (working label "internalized
controller"; numbering TBD against the Paper 6 margin/geometry routing). This
is a navigation document, not an evidence document: every internal claim below
cites its governed doc, and no number here is citable without opening that
doc (CLAUDE.md rule 6)._

---

## 1. The question

Paper 5's positive result is a runtime thermostat: an external probe reads the
pre-generation known-unknown (KU) state, and where it fires, a dosed
hidden-state write converts confabulations into the model's own well-formed
refusals (`papers/paper-5-actuation/manuscript.md` §4.5-4.6). Every route that
asked the policy to consult its own readout failed (§4.1-4.4). The PI's
question for the next study: **is there a training method or architecture that
installs the sensor-to-actuator wiring in the weights**, so the deployed model
consults its internal signal with no runtime harness — for example a dedicated
MoE-style module the forward pass routes through, whose effect on tokens is
conditioned on internal activations?

## 2. What the program already knows (constraints any candidate must clear)

Read each source doc before citing any of this; pointers only.

1. **The signal is there and training does not touch it.** KU readout at
   AUROC ~0.997 on the raw base, unchanged after every training arm
   (`papers/paper-3-knows-but-doesnt-say/manuscript.md`, "The internal signal
   survives training"). So the sensor half is free; the wiring is the unsolved
   half.
2. **Behavioral abstention is installable; consultation is not shown.**
   Paper 3's mechanistic reading: training arms decompose as *policy over a
   fixed epistemic signal* — SFT installs a refusal routine, preference/RL
   moves its threshold, nothing moves the signal. Whether the installed
   routine causally reads the KU axis (vs. surface correlates of the same
   rows) is exactly what the program has never confirmed, and probe-as-reward
   GRPO answered "no" for its arm: TRUE-sensor congruence 59.75% vs permuted
   76.75% (`experiments/probe-as-reward/AMENDMENT.md` §5, NULL).
3. **The stated-confidence channel is a bottleneck, not a knowledge failure.**
   A single scalar trained by next-token prediction collapses onto the
   lowest-entropy correlate whatever the target (Paper 3 §8). Any candidate
   that routes the signal through an emitted token inherits this.
4. **Writes work only at the right operating point.** Site and dose are
   family-specific; mid-band writes self-sort by commitment margin; the gate's
   role is dose-dependent (Paper 5 §6.2-6.3). A weights-level mechanism does
   not escape this geometry — it has to implement it.
5. **DPO is already a steering write in disguise.** D-Steer
   (`library/notes/2512.11838--d-steer-preference-alignment-techniques-learn-behave.md`)
   argues the DPO update is a low-rank, near-static activation shift: adding
   the extracted vector to the base reproduces the aligned behavior. Read
   against constraint 2, this predicts that naive preference-distillation of
   the thermostat installs an *unconditional* push (a permanent dose), not a
   gated one — the exact failure the gate exists to prevent at overdrive.
6. **The crux test is causal, not behavioral.** Per Paper 5 §2.2, use of the
   readout means alignment + specificity + selectivity. For a weights-level
   candidate the decisive instrument is an *intervention-based congruence
   test*: after installation, ablate/flip/clamp the KU direction in the
   student's own hidden state and ask whether the installed refusal follows
   the intervened signal. If behavior does not move with the internal signal,
   the candidate has installed a surface policy, however good its ROC looks.
   (This is the test AI could not pass and AH formalized on the compliance
   side.)

## 3. Candidate space

_Filled from the external literature scan (Section 4) and ranked in Section 5._

## 4. Literature scan

_(three sweeps: architectures with modules routing on internal activations;
training objectives that force causal dependence on internal state;
distillation of runtime control into weights)_

## 5. Ranked recommendation

## 6. Design notes for the registered study
