"""Shared "ideal operating point" quadrant convention for every recall-vs-
over-refusal scatter figure in Paper 2 (fig-p1-01, fig-p1-04, fig-p1-07,
fig-p1-10). One rule, reused by all four panels, so the reader calibrates the
shading once instead of re-learning it per figure.

The ideal direction is 0% over-refusal on known questions and 100% refusal
recall on unknown questions, i.e. up and to the left. Each panel shades its
own upper-left quadrant: over-refusal below the midpoint of that panel's
plotted x-range, and refusal recall above the midpoint of its plotted
y-range. A single flat, translucent green fill, no fade and no boundary
line drawn at the midline. This is illustrative, not a quantitative
threshold: the midpoint is a property of what happens to be plotted in a
given panel, not a claimed cutoff value.
"""

from __future__ import annotations

IDEAL_GREEN_RGB = (47, 140, 90)  # matches the "good" valence green used elsewhere
IDEAL_QUADRANT_ALPHA = 0.14  # flat alpha; identical in every figure
