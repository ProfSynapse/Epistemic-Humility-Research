# Paper build pipeline (arXiv production chain)

Shared infrastructure for turning a paper's `manuscript.md` (GitHub-flavored
markdown) into an arXiv-ready LaTeX PDF, without editing manuscript content.
Piloted on paper 4 (`papers/paper-4-two-signal-readout/`).

## Chain

```text
manuscript.md
  -> pandoc (gfm reader, shared defaults.yaml + template.tex + manuscript-filters.lua,
             paper-level build/metadata.yaml)
  -> build/out/main.tex
  -> tectonic (XeTeX)
  -> build/out/main.pdf
  -> `make arxiv`: build/out/<paper>-arxiv.tar.gz  (main.tex at tarball root
     + figures/ subdir with only the referenced figure files)
```

## Building a paper

Each paper gets a `build/` directory containing three small files
(copy paper 4's as the template):

- `Makefile` — two lines: a comment and `include ../../common/build/paper.mk`.
- `metadata.yaml` — title (must mirror the manuscript H1), author list, date.
  The abstract is NOT copied here; the Lua filter lifts the manuscript's
  `## Abstract` section at build time so the manuscript stays authoritative.
- `.gitignore` — ignores `out/`.

Then, from `papers/<paper>/build/`:

```bash
make check   # manuscript lint (fails the build guardrails below)
make pdf     # out/main.tex + out/main.pdf
make arxiv   # out/<paper>-arxiv.tar.gz in arXiv ingestion layout
make clean
```

`make check` (via `scripts/paper_build_check.py`) fails on:

1. figure files cited in the markdown but absent on disk;
2. relative markdown links whose target does not exist (paper dir, then repo
   root);
3. em dashes in prose (series prose rule; fenced code excluded);
4. the phrase "load-bearing" (series prose rule).

It warns (without failing) on figure files never cited.

## Pinned tools

Static user-local binaries in `~/.local/bin` (no sudo). Verify with
`sha256sum` on the downloaded release tarballs:

| Tool | Version | Release asset | sha256 (tarball) |
|------|---------|---------------|------------------|
| pandoc | 3.10.1 | `pandoc-3.10.1-linux-amd64.tar.gz` from github.com/jgm/pandoc | `72948bf5784f560d5ad1876709daca27e0667f262da727bb33f77b58e52df2f5` |
| tectonic | 0.17.0 | `tectonic-0.17.0-x86_64-unknown-linux-musl.tar.gz` from github.com/tectonic-typesetting/tectonic | `8533d07f9ccbd7a65824b9e0459041bca34af1eb33daba48f59215593753a3b7` |

Tectonic downloads its TeX bundle on first run (network required once; cached
afterwards under `~/.cache/Tectonic`).

## Manuscript conventions the chain assumes

- `# H1` = paper title (lifted into `\title`; must equal metadata.yaml title).
- `## H2` = sections, `### H3` = subsections, `#### H4` = unnumbered run-in
  headings. `shift-heading-level-by: -1` maps these to
  section/subsection/subsubsection.
- Manual heading numbers (`## 4. Results`, `### 4.1 ...`) are stripped by the
  filter; LaTeX numbering is the single source. This is only safe while the
  manuscript's manual numbers are sequential and complete — verified for
  paper 4 (sections 1-8, subsections 4.1-4.11 align). In-prose `§N.M`
  references are literal text and stay correct only under that alignment.
  A placeholder number like `6.x` is stripped and that heading left
  unnumbered. Everything from `## References` / `## Appendix*` on is
  unnumbered back matter.
- `## Abstract` is lifted into the LaTeX abstract and removed from the body.
- Figure placement (each figure file is placed exactly once):
  - an inline blockquote `> **Figure N. Caption ...** ... (`fig-file.png`)`
    becomes a real `[H]` figure with the caption verbatim;
  - figure files listed in the appendix "Figure index" bullet list that were
    not placed inline are rendered there as figure plates; entries already
    placed inline keep caption text only.
- Wide pipe tables get proportional relative column widths (cells wrap), and
  long path-like code spans are emitted breakable (`\path{}` / `\texttt` with
  `\allowbreak`) so they cannot overflow table cells.
- Unicode used by the series (— banned; – → − ∧ ≈ ≥ ± × Δ § etc.) is mapped
  via `newunicodechar` so it survives both XeTeX and pdflatex.

## What `make arxiv` produces

`out/<paper>-arxiv.tar.gz` containing `main.tex` at the root and `figures/`
with exactly the figure files `main.tex` references — the layout arXiv's
ingestion expects for an upload. No `.bbl` yet (no BibTeX; see below).

## Known constructs needing attention (per paper)

### paper-4-two-signal-readout (pilot, builds end-to-end: 28 pp, 7 figures)

- **Figures 1-6 have no inline anchors.** Only Figure 7 has an inline caption
  blockquote; Figures 1-6 exist solely in the appendix "Figure index", so the
  pilot places them as appendix plates. Follow-up (manuscript edit, needs
  approval): add `> **Figure N. ...** (`file.png`)` blocks at the use sites.
- **Cross-manuscript relative links** (`../paper-3-knows-but-doesnt-say/manuscript.md`,
  2 sites) render as hyperlinks that are dead in a PDF; needs a citation/URL
  policy before submission.
- **`### 6.x` placeholder section** — rendered unnumbered; resolve before
  submission.
- **References are a hand-written bullet list**; citeproc/BibTeX are off.
  Follow-up: move to a `.bib` + citeproc or natbib, and include the `.bbl`
  in the arXiv tarball.
- **Author/affiliation TODO** in `build/metadata.yaml` (currently the repo
  git identity, no affiliation) — confirm before submission.
- **Draft-provenance note** (italic paragraph before the abstract) renders
  after `\maketitle`/abstract; drop or keep is an editorial call.

### Series-wide follow-ups

- **SVG figures**: paper 4 is all-PNG. No SVG->PDF conversion step is wired
  yet; papers with SVG figures need one (e.g. rsvg-convert) before `pdf`.
- **arXiv pdflatex path untested**: local builds use tectonic (XeTeX). The
  template carries `\ifPDFTeX` branches intended to keep `main.tex`
  compilable under arXiv's default pdflatex autotex, but that path has not
  been exercised; either test it or pin XeLaTeX in the arXiv submission
  settings.
- **Other papers not yet piloted**: run `make check` first — paper 4 is
  em-dash-clean, other manuscripts may not be.
