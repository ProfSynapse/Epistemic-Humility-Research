-- manuscript-filters.lua
--
-- Shared pandoc Lua filter for the Epistemic-Humility paper series.
-- NOTE: pandoc applies --shift-heading-level-by AFTER Lua filters, so this
-- filter sees the manuscript's raw levels (H1 title, H2 sections). It derives
-- the section tier itself instead of hardcoding it. It adapts the repo's
-- manuscript conventions to arXiv LaTeX WITHOUT any edit to manuscript.md:
--
--  1. Title: a lone leading H1 is left in place for the later shift to lift
--     into the document title (a first body paragraph duplicating the
--     metadata title is dropped as a fallback).
--  2. Abstract lift: the "Abstract" section's content is moved into the
--     `abstract` metadata field (manuscript is authoritative; any abstract in
--     build/metadata.yaml is a fallback snapshot) and removed from the body.
--  3. Heading normalization: manual "N." / "N.M" prefixes are stripped so
--     LaTeX's own numbering is the single source (defaults.yaml turns
--     number-sections on). Placeholder numbers like "6.x" are stripped and
--     that heading is left unnumbered. Everything from "References" or
--     "Appendix*" onward is unnumbered back matter.
--  4. Figure placement: a blockquote of the form
--         > **Figure N. Caption ...** ... (`fig-file.png`)
--     becomes a real LaTeX figure ([H], width=\linewidth, caption verbatim).
--     Figure files listed in the appendix "Figure index" bullet list that were
--     NOT placed inline are rendered there as figure plates (image + caption);
--     entries already placed inline keep only their caption text. Each figure
--     file is therefore placed exactly once.
--
-- Image paths are emitted as figures/<file>; template.tex's \graphicspath
-- makes that resolve from both the build/out and arxiv-dist layouts.

--  5. Wide-table handling: the gfm reader gives pipe tables no column widths,
--     so the LaTeX writer emits unwrapped l-columns that overflow the page.
--     Tables whose content is wider than a text line get proportional relative
--     column widths (the writer then wraps cells), and long code spans
--     containing "/" are emitted as breakable \path{} (xurl in template.tex).

local stringify = pandoc.utils.stringify

local FIG_EXT = "%.png$"
local placed = {} -- figure filenames already placed inline

-- Find the first Code inline that looks like a figure file; return filename.
local function find_figure_file(inlines)
  for _, il in ipairs(inlines) do
    if il.t == "Code" and il.text:match(FIG_EXT) then
      return il.text
    end
  end
  return nil
end

-- True if the inline list starts with Strong text beginning "Figure ".
local function starts_with_figure_strong(inlines)
  local first = inlines[1]
  return first and first.t == "Strong"
    and stringify(first):match("^Figure%s+%S")
end

-- Build the block sequence for one figure (raw LaTeX skeleton, caption kept
-- as a pandoc Para so emphasis/code spans render properly).
local function figure_blocks(file, caption_inlines)
  return {
    pandoc.RawBlock("latex",
      "\\begin{figure}[H]\n\\centering\n" ..
      "\\includegraphics[width=\\linewidth]{figures/" .. file .. "}\n" ..
      "\\begingroup\\small"),
    pandoc.Para(caption_inlines),
    pandoc.RawBlock("latex", "\\endgroup\n\\end{figure}"),
  }
end

-- Strip a manual "N." / "N.M" / "N.x" prefix from header inlines.
-- Returns (new_inlines, stripped?, placeholder?) — placeholder means the
-- number contained a non-numeric part (e.g. "6.x") and should be unnumbered.
local function strip_manual_number(inlines)
  local first = inlines[1]
  if not (first and first.t == "Str") then return inlines, false, false end
  local txt = first.text
  local num = txt:match("^(%d+%.?)$") or txt:match("^(%d+%.%d+%.?)$")
  local placeholder = txt:match("^%d+%.[a-zA-Z]%.?$")
  if not num and not placeholder then return inlines, false, false end
  local out = pandoc.List(inlines)
  out:remove(1)
  while out[1] and out[1].t == "Space" do out:remove(1) end
  return out, true, placeholder ~= nil
end

-- Long path-like code spans cannot break inside \texttt and overflow table
-- cells and lines. Pure paths become \path{} (xurl: breaks anywhere); other
-- long spans (glob/brace patterns) get escaped \texttt with \allowbreak
-- after separators. Conservative charset guard: no TeX-active chars beyond
-- the ones we escape.
local function tex_escape(s)
  return (s:gsub("[{}$&#^_%%~]", {
    ["{"] = "\\{", ["}"] = "\\}", ["$"] = "\\$", ["&"] = "\\&",
    ["#"] = "\\#", ["^"] = "\\^{}", ["_"] = "\\_", ["%"] = "\\%",
    ["~"] = "\\textasciitilde{}",
  }))
end

function Code(code)
  local txt = code.text
  if #txt < 18 or not txt:match("^[%w%./_%-%*<>:{},]+$") then return nil end
  if txt:match("^[%w%./_%-%*<>:]+$") and txt:find("/", 1, true) then
    return pandoc.RawInline("latex", "\\path{" .. txt .. "}")
  end
  if txt:find("/", 1, true) or txt:find("_", 1, true)
    or txt:find(",", 1, true) then
    local esc = tex_escape(txt)
      :gsub("([/,])", "%1\\allowbreak{}")
      :gsub("(\\_)", "%1\\allowbreak{}")
    return pandoc.RawInline("latex", "\\texttt{" .. esc .. "}")
  end
  return nil
end

-- Give wide tables proportional relative column widths so cells wrap.
function Table(tbl)
  local WIDE = 90   -- chars; roughly one text line
  local maxlen = {}
  local function scan(rows)
    for _, row in ipairs(rows) do
      for ci, cell in ipairs(row.cells) do
        local len = #stringify(cell.contents)
        if not maxlen[ci] or len > maxlen[ci] then maxlen[ci] = len end
      end
    end
  end
  scan(tbl.head.rows)
  for _, body in ipairs(tbl.bodies) do
    scan(body.body)
    scan(body.head)
  end
  local total = 0
  for ci = 1, #tbl.colspecs do
    maxlen[ci] = maxlen[ci] or 1
    total = total + maxlen[ci]
  end
  if total <= WIDE then return nil end
  -- proportional widths with a floor, normalized to 0.97\linewidth
  local floor_w = 0.06
  local weights, wsum = {}, 0
  for ci = 1, #tbl.colspecs do
    weights[ci] = math.max(maxlen[ci] / total, floor_w)
    wsum = wsum + weights[ci]
  end
  for ci, spec in ipairs(tbl.colspecs) do
    tbl.colspecs[ci] = { spec[1], 0.97 * weights[ci] / wsum }
  end
  return tbl
end

function Pandoc(doc)
  local meta = doc.meta
  local blocks = doc.blocks
  local out = pandoc.List()
  local i = 1
  local backmatter = false
  local in_figure_index = false

  -- Section tier: the minimum header level in the doc, ignoring a leading H1
  -- title block (manuscript convention: H1 title, H2 sections).
  local section_level = nil
  for bi, blk in ipairs(blocks) do
    if blk.t == "Header" and not (bi == 1 and blk.level == 1) then
      if not section_level or blk.level < section_level then
        section_level = blk.level
      end
    end
  end
  section_level = section_level or 1

  -- 1. Title dedup fallback (only if the shift already produced a title, the
  -- reader normally lifts the leading H1; this guards the other case).
  if blocks[1] and blocks[1].t == "Para" and meta.title
    and stringify(blocks[1]) == stringify(meta.title) then
    i = 2
  end

  while i <= #blocks do
    local b = blocks[i]

    -- 2. Abstract lift: section-tier "Abstract" -> meta.abstract.
    if b.t == "Header" and b.level == section_level
      and stringify(b) == "Abstract" then
      local abs = pandoc.List()
      i = i + 1
      while i <= #blocks
        and not (blocks[i].t == "Header"
                 and blocks[i].level <= section_level) do
        abs:insert(blocks[i])
        i = i + 1
      end
      meta.abstract = pandoc.MetaBlocks(abs)

    elseif b.t == "Header" then
      -- 3. Heading normalization.
      local txt = stringify(b)
      if b.level == section_level
        and (txt == "References" or txt:match("^Appendix")) then
        backmatter = true
      end
      in_figure_index = (txt == "Figure index")
      local inlines, _, placeholder = strip_manual_number(b.content)
      b = pandoc.Header(b.level, inlines, b.attr)
      if backmatter or placeholder then
        b.classes:insert("unnumbered")
      end
      out:insert(b)
      i = i + 1

    -- 4a. Inline figure blockquote -> figure environment.
    elseif b.t == "BlockQuote" and #b.content >= 1
      and (b.content[1].t == "Para" or b.content[1].t == "Plain")
      and starts_with_figure_strong(b.content[1].content)
      and find_figure_file(b.content[1].content) then
      local caption = b.content[1].content
      local file = find_figure_file(caption)
      placed[file] = true
      out:extend(figure_blocks(file, caption))
      i = i + 1

    -- 4b. Figure-index bullet list -> plates for figures not placed inline.
    elseif in_figure_index and b.t == "BulletList" then
      for _, item in ipairs(b.content) do
        local para = item[1]
        local inls = para and para.content
        local file = inls and find_figure_file(inls)
        if file and not placed[file] then
          placed[file] = true
          out:extend(figure_blocks(file, inls))
        elseif inls then
          -- Already placed inline: keep the provenance text as prose.
          out:insert(pandoc.Para(inls))
        end
      end
      i = i + 1

    else
      out:insert(b)
      i = i + 1
    end
  end

  return pandoc.Pandoc(out, meta)
end
