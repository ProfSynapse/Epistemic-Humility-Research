"""Shared "ideal operating point" shading convention for every recall-vs-
over-refusal scatter figure in Paper 2 (fig-p1-01, fig-p1-04, fig-p1-07,
fig-p1-10). One rule, reused by all four panels, so the reader calibrates the
shading once instead of re-learning it per figure.

The ideal direction is 0% over-refusal on known questions and 100% refusal
recall on unknown questions, i.e. up and to the left. The zone is FIXED in
data coordinates for every panel: over-refusal 0-20%, recall 80-100%
(fig-p1-01, fig-p1-04, fig-p1-07). It is never defined relative to a
panel's plotted range: on a zoomed panel a relative quadrant would relocate
the green onto operating points that are nowhere near ideal. A panel whose
zoom excludes the zone entirely (fig-p1-10, zoomed to seed-CI resolution)
draws a green off-plot direction marker instead of shading. A single flat,
translucent green fill, no fade and no boundary line drawn at the zone edge.
The 20/80 boundary is illustrative, not a claimed quantitative threshold.
"""

from __future__ import annotations

IDEAL_GREEN_RGB = (47, 140, 90)  # matches the "good" valence green used elsewhere
IDEAL_QUADRANT_ALPHA = 0.14  # flat alpha; identical in every figure
