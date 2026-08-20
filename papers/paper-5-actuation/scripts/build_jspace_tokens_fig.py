#!/usr/bin/env python3
"""Generate Figure 9 for the actuation paper (Paper 5): what the J-lens finds.

Reads exactly one committed source artifact directly from its experiment
directory under the repo's experiments-first tree (same convention as
build_figures.py -- no paper-local snapshot):

    experiments/j-space-localization-qwen3-4b/analysis-committed/results/
      jspace-jlens-r1/h1_full.json

This is the genuine J-lens verbalization readout from the resolved
j-space-localization-qwen3-4b lab-diagnostic: per-layer top_tokens (token
string, score, softmax_prob) for the four fitted directions (u_d, pos_ctrl,
c_hat, neg_ctrl) at hs30/32/34/36, the four layer offsets around the fit
layer hs34 (this project's L34 write site). No dataset question text or
generation text is read or plotted -- only vocabulary-readout token strings.

Cleaning rule (see AMENDMENT_GLOSS / is_legible / top_cleaned below):
Chinese-script and Latin-script tokens are treated on equal footing as
legible surface forms and ranked together by J-lens score; BPE-artifact
variants (leading whitespace/quote) are merged, keeping the highest-scored
form; pure non-alphabetic, non-CJK fragments (stray punctuation, code/path
fragments such as "/ajax" or "-layout") are dropped. Parenthetical glosses
are added ONLY for the seven CJK tokens the amendment's own Outcome prose
glosses verbatim (experiments/j-space-localization-qwen3-4b/AMENDMENT.md);
no other CJK token is translated.

Deterministic, CPU-only, no network at build time.

CJK font asset and its provenance
----------------------------------
Rendering the Chinese-script tokens needs a CJK-capable font, which this
repo does not otherwise ship (DejaVu Sans has no CJK coverage). Committing a
full CJK font (Noto Sans CJK SC Regular is ~16.5 MB) is too heavy for this
repo, so a glyph-subsetted copy is committed instead, covering exactly the
characters this figure renders (Latin token/gloss text + the CJK tokens that
survive cleaning + this script's own footnote text) -- 88 unique characters,
89 glyphs including .notdef, 17,280 bytes:

    papers/paper-5-actuation/figures/assets/NotoSansCJKsc-Regular-jspace-subset.otf

Source font: Noto Sans CJK SC Regular (Google Noto CJK project,
https://github.com/notofonts/noto-cjk), SIL Open Font License 1.1 (license
text retained verbatim per its own condition 2, see
papers/paper-5-actuation/figures/assets/LICENSE-NotoSansCJK-OFL.txt).
Source file sha256 (unsubset NotoSansCJKsc-Regular.otf, ~16.5 MB, not
committed -- too large for this repo):

    2c76254f6fc379fddfce0a7e84fb5385bb135d3e399294f6eeb6680d0365b74b

Subsetting command used to produce the committed asset (fonttools 4.54.1):

    pyftsubset NotoSansCJKsc-Regular.otf \\
      --unicodes=U+0020,U+0022,U+0027,U+0028,U+0029,U+002C,U+002D,U+002E,\\
        U+002F,U+0033,U+0034,U+0035,U+003A,U+003B,U+0041,U+0043,U+0044,\\
        U+0045,U+0049,U+004A,U+004B,U+004C,U+004D,U+004E,U+004F,U+0050,\\
        U+0054,U+0061,U+0062,U+0063,U+0064,U+0065,U+0066,U+0067,U+0068,\\
        U+0069,U+006A,U+006B,U+006C,U+006D,U+006E,U+006F,U+0070,U+0071,\\
        U+0072,U+0073,U+0074,U+0075,U+0076,U+0077,U+0078,U+0079,U+007A,\\
        U+4E00,U+4E0D,U+4F60,U+515A,U+5230,U+5409,U+540D,U+56DE,U+5B57,\\
        U+5B9E,U+5BF9,U+5FEB,U+6027,U+6211,U+6218,U+6709,U+6848,U+6B21,\\
        U+6D25,U+6D3B,U+6E85,U+70AD,U+70B9,U+70ED,U+7684,U+7965,U+7A7A,\\
        U+7B54,U+7EC4,U+7EC7,U+80A5,U+8BA9,U+8BC1,U+901F,U+961F \\
      --output-file=NotoSansCJKsc-Regular-jspace-subset.otf \\
      --no-layout-closure --glyph-names --symbol-cmap --legacy-cmap \\
      --notdef-glyph --notdef-outline --recommended-glyphs \\
      --name-IDs='*' --name-legacy --name-languages='*'

The unicode list above is the exact union of every character rendered with
the CJK font in this figure (computed programmatically from this script's
own cleaning/gloss logic against the committed h1_full.json, not hand
transcribed) -- if the source JSON or the cleaning/gloss rules ever change,
regenerate the subset the same way against the new rendered character set
before rebuilding this figure.

Usage:
    python3 papers/paper-5-actuation/scripts/build_jspace_tokens_fig.py
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

ROOT = Path(__file__).resolve().parents[3]
EXP = ROOT / "experiments"
OUT = ROOT / "papers" / "paper-5-actuation" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

H1_PATH = (
    EXP
    / "j-space-localization-qwen3-4b"
    / "analysis-committed"
    / "results"
    / "jspace-jlens-r1"
    / "h1_full.json"
)
CJK_FONT_PATH = OUT / "assets" / "NotoSansCJKsc-Regular-jspace-subset.otf"

fm.fontManager.addfont(str(CJK_FONT_PATH))
CJK_FP = fm.FontProperties(fname=str(CJK_FONT_PATH))

# ---- palette (reuses paper-5 build_figures.py conventions) ---------------
C_CAUTION = "#2C6E9C"  # caution / refusal-axis tokens (blue)
C_ANSWER = "#4A9D7F"   # answer / reply-axis tokens (green)
C_NULL = "#9AA0A6"     # not-cleanly-verbalizable control (grey)
C_ACCENT = "#C25B3F"   # fit-layer / write-site highlight (terracotta)
C_TEXT = "#2A2A2A"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 11,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.dpi": 150,
})

# ---- token cleaning --------------------------------------------------------
CJK_RE = re.compile(r"[㐀-鿿぀-ヿ가-힯]")
# Only tokenizer presentation artifacts (leading BPE space marker, quotes,
# tab) are stripped. Structural characters that mark a token as a code/path
# fragment (/, \, [, ], {, }, $, :, -, _, *) are deliberately NOT stripped,
# so a token like "/ajax" or "-layout" fails the alphabetic-only legibility
# check below instead of laundering into "ajax" / "layout".
STRIP_CHARS = " \t\"'`"

# Glosses used ONLY where the amendment's own Outcome prose states them
# verbatim (experiments/j-space-localization-qwen3-4b/AMENDMENT.md, Outcome
# section, "H1 direction verbalization" paragraph). No other CJK token is
# translated/invented -- tokens not in this map render unglossed.
AMENDMENT_GLOSS = {
    "答案": "answer",
    "回答": "reply/answer",
    "的答案": "the answer",
    "我": "I/me",
    "空": "empty",
    "不到": "cannot reach/cannot get",
    "热点": "hotspot",
}


def is_cjk(s: str) -> bool:
    return bool(CJK_RE.search(s))


def normalize(raw: str) -> str:
    return raw.strip(STRIP_CHARS)


def is_legible(t: str) -> bool:
    """Chinese-script and Latin-script tokens are treated on equal footing.
    A CJK-containing surface form is always legible. For Latin script,
    deliberately conservative: pure-alphabetic surface forms only (>=2
    letters), plus the single-letter pronoun "I" (kept as a special case --
    it is a real, semantically load-bearing token here, quoted explicitly
    in the manuscript's Sec 4.6). This drops stray punctuation and
    code/path fragments (e.g. "/ajax", "[df", "-layout") without trying to
    judge whether a surviving token is a "real word" beyond that -- sub-word
    stems like "imposs" or "ANS" pass through as-is, and neg_ctrl's actual
    noise is shown, not edited out."""
    if is_cjk(t):
        return True
    if t == "I":
        return True
    return bool(re.fullmatch(r"[A-Za-z]{2,}", t))


def top_cleaned(top_tokens: list[dict], k: int = 5):
    """Merge Chinese-script and Latin-script tokens into one score-ranked
    list (same footing, single ranking) -- no separate CJK bucket."""
    seen: dict[str, tuple[str, float]] = {}
    n_dropped = 0
    for t in top_tokens:
        raw = t["token"]
        score = t["score"]
        norm = normalize(raw)
        if not is_legible(norm):
            n_dropped += 1
            continue
        key = norm if is_cjk(norm) else norm.lower()
        if key not in seen or score > seen[key][1]:
            seen[key] = (norm, score)
    ranked = sorted(seen.values(), key=lambda x: -x[1])
    return [w for w, _ in ranked[:k]], n_dropped


def display_text(tok: str) -> str:
    gloss = AMENDMENT_GLOSS.get(tok)
    return f"{tok} ({gloss})" if gloss else tok


def draw_token_text(ax, x, y, tok, **kwargs):
    """ax.text but with the CJK font applied whenever the token (or its
    gloss-annotated display form) contains CJK characters."""
    disp = display_text(tok)
    fp = CJK_FP if is_cjk(tok) else None
    return ax.text(x, y, disp, fontproperties=fp, **kwargs)


def build():
    h1 = json.loads(H1_PATH.read_text())

    direction_specs = [
        ("u_d_L34 (doubt)", "known–unknown axis\n(u_d)", C_ANSWER),
        ("pos_ctrl_L34 (caution / answer-vs-refuse)", "caution / refuse axis\n(pos_ctrl)", C_CAUTION),
        ("c_hat_L34 (caution write, orthogonalized)", "caution write, final\n(ĉ, orthogonalized)", C_CAUTION),
        ("neg_ctrl_L34 (confab-propensity)", "confab-propensity control\n(neg_ctrl)", C_NULL),
    ]
    hs_layers = ["30", "32", "34", "36"]
    fit_layer = "34"

    cell_data = {}
    n_dropped_total = 0
    for dkey, _, _ in direction_specs:
        pl = h1["directions"][dkey]["per_layer"]
        for hs in hs_layers:
            toks, n_dropped = top_cleaned(pl[hs]["top_tokens"], k=5)
            cell_data[(dkey, hs)] = toks
            n_dropped_total += n_dropped

    fig = plt.figure(figsize=(11.6, 5.5))
    top_h = 0.80
    axA = fig.add_axes([0.09, 1 - top_h - 0.075, 0.88, top_h])

    axA.set_xlim(0, 1)
    axA.set_ylim(0, 1)
    axA.axis("off")
    n_cols = len(direction_specs)
    n_rows = len(hs_layers)
    col_w = 1.0 / n_cols
    row_h = 0.80 / n_rows
    header_y = 0.86
    top_y = 0.82

    for j, (dkey, dlabel, color) in enumerate(direction_specs):
        cx = (j + 0.5) * col_w
        axA.text(cx, header_y, dlabel, ha="center", va="bottom", fontsize=9.6,
                  fontweight="bold", color=color, linespacing=1.3)
        axA.add_patch(Rectangle((j * col_w + 0.01, 0.02), col_w - 0.02, top_y - 0.02,
                                 facecolor=color, alpha=0.05, edgecolor=color,
                                 linewidth=0.9, zorder=0))

    for i, hs in enumerate(hs_layers):
        ry = top_y - (i + 1) * row_h
        row_label = f"hs{hs}"
        if hs == fit_layer:
            row_label += "\n(fit layer /\nL34 write site)"
            label_color = C_ACCENT
            label_weight = "bold"
        else:
            label_color = C_TEXT
            label_weight = "normal"
        axA.text(-0.01, ry + row_h / 2, row_label, ha="right", va="center",
                  fontsize=8.6, color=label_color, fontweight=label_weight, linespacing=1.2)
        if hs == fit_layer:
            axA.add_patch(Rectangle((0.0, ry), 1.0, row_h, facecolor=C_ACCENT,
                                     alpha=0.06, edgecolor="none", zorder=0))
        axA.axhline(ry, xmin=0.0, xmax=1.0, color="#DDDDDD", lw=0.7, zorder=1)

        for j, (dkey, dlabel, color) in enumerate(direction_specs):
            toks = cell_data[(dkey, hs)]
            cx = (j + 0.5) * col_w
            if not toks:
                axA.text(cx, ry + row_h / 2, "—", ha="center", va="center",
                          fontsize=9, color="#999999")
                continue
            # Uniform stack: every token in the family gets equal visual
            # weight (same font size/weight); vertical position preserves
            # score order top-to-bottom, it is not a "featured" pick.
            # Chinese-script and Latin-script tokens sit in the same list,
            # same footing -- only the font used to render each line differs.
            n_tok = len(toks)
            pad = row_h * 0.08
            slot_h = (row_h - 2 * pad) / n_tok
            for idx, tok in enumerate(toks):
                ty = ry + row_h - pad - (idx + 0.5) * slot_h
                draw_token_text(axA, cx, ty, tok, ha="center", va="center",
                                 fontsize=9.3, fontweight="normal", color=C_TEXT)

    axA.plot([0, 1], [top_y, top_y], color="#999999", lw=1.1)
    axA.set_title(
        "What the J-lens finds: top verbalized tokens per direction and layer\n"
        "(Qwen3-4B raw-base, same-substrate bf16 H1 readout, hs30–hs36)",
        fontsize=12, pad=14, loc="left",
    )

    footnote = (
        f"Cleaning rule: Chinese-script and Latin-script tokens are treated on equal "
        f"footing as legible surface forms and ranked together by J-lens score; variants differing "
        f"only in leading whitespace/quote are merged (highest-scored kept); pure non-alphabetic, "
        f"non-CJK fragments (paths, brackets, stray punctuation, e.g. \"/ajax\", \"-layout\") are "
        f"dropped -- {n_dropped_total} such fragments were dropped here. Parenthetical glosses "
        f"(答案 answer, 回答 reply/answer, 的答案 the answer, 我 I/me, "
        f"空 empty, 不到 cannot reach/cannot get, 热点 hotspot) are taken verbatim "
        f"from the amendment's own Outcome prose (experiments/j-space-localization-qwen3-4b/"
        f"AMENDMENT.md); no other CJK token is translated."
    )
    # footnote mixes English and literal CJK glyphs (the gloss list) -- use
    # the CJK font throughout this text object (it carries the needed Latin
    # glyphs too, see the subset unicode list above) so nothing renders as a
    # missing-glyph box.
    fig.text(0.09, 0.015, footnote, fontsize=7.0, color="#666666", wrap=True, va="bottom",
              fontproperties=fm.FontProperties(fname=str(CJK_FONT_PATH), size=7.0))

    out_path = OUT / "fig-p5-09-jspace-tokens.png"
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out_path}")
    print(f"n_dropped_fragments(H1)={n_dropped_total}")


if __name__ == "__main__":
    build()
