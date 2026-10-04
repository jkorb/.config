-- Pandoc handles ordinary TeX math; this adds inference trees and math grids.
-- Rendering only: unknown constructs fall back to their complete TeX source.
local limit = math.max(12, tonumber(os.getenv("MD_READ_WIDTH") or "80") - 8)
local trim = function(s) return s:match("^%s*(.-)%s*$") end
local subletters = {a="ₐ", e="ₑ", h="ₕ", i="ᵢ", j="ⱼ", k="ₖ", l="ₗ", m="ₘ",
  n="ₙ", o="ₒ", p="ₚ", r="ᵣ", s="ₛ", t="ₜ", u="ᵤ", v="ᵥ", x="ₓ"}

local function subscript(s)
  local result = {}
  for _, code in utf8.codes(s) do
    local char = utf8.char(code)
    local mapped = subletters[char] or pandoc.text.subscript(char)
    if not mapped then return "_(" .. s .. ")" end
    result[#result + 1] = mapped
  end
  return table.concat(result)
end

local function width(s)
  local n = 0
  for _, c in utf8.codes(s) do
    -- Combining accents occupy no cell. Wide/emoji labels fall back to TeX;
    -- guessing their width would misalign a proof and its rule labels.
    if (c >= 0x300 and c <= 0x36f) or (c >= 0x1dc0 and c <= 0x1dff)
        or (c >= 0x20d0 and c <= 0x20ff) then
      -- no extra cell
    elseif c < 0x1100 or (c >= 0x1d00 and c <= 0x1dbf)
        or (c >= 0x1f00 and c < 0x2e80)
        or (c >= 0x1d400 and c <= 0x1d7ff) then
      n = n + 1
    else
      error("unsupported terminal width")
    end
  end
  return n
end

local function text_math(tex)
  local doc = pandoc.Pandoc({pandoc.Para({pandoc.Math("InlineMath", tex)})})
  local text = trim(pandoc.write(doc, "plain", {wrap_text = "none"}))
  if text:sub(1, 1) == "$" then error("unsupported TeX") end
  -- TeXMath uses typographic spaces. Terminal cells need ordinary spaces.
  for c = 0x2000, 0x200a do text = text:gsub(utf8.char(c), " ") end
  text = text:gsub(" ", " ")
  text = text:gsub("_%(([^()]*)%)", subscript)
  text = text:gsub("%^%(([^()]*)%)", function(s)
    return pandoc.text.superscript(s) or ("^(" .. s .. ")")
  end)
  return trim(text)
end

-- Read balanced groups, ignoring escaped braces and brackets.
local function group(s, pos, open, close)
  while s:sub(pos, pos):match("%s") do pos = pos + 1 end
  assert(s:sub(pos, pos) == open, "missing group")
  local start, depth, braces = pos + 1, 1, 0
  pos = start
  while pos <= #s do
    local c = s:sub(pos, pos)
    if c == "\\" then
      pos = pos + 2
    else
      if open == "[" then
        if c == "{" then braces = braces + 1 end
        if c == "}" then braces = braces - 1 end
      end
      if braces == 0 then
        if c == open then depth = depth + 1 end
        if c == close then depth = depth - 1 end
        if depth == 0 then return s:sub(start, pos - 1), pos + 1 end
      end
      pos = pos + 1
    end
  end
  error("unclosed group")
end

local function split(s, separator)
  local result, start, depth, pos = {}, 1, 0, 1
  while pos <= #s do
    local c = s:sub(pos, pos)
    if depth == 0 and s:sub(pos, pos + #separator - 1) == separator then
      result[#result + 1] = s:sub(start, pos - 1)
      pos = pos + #separator
      start = pos
    elseif c == "\\" then
      pos = pos + 2
    else
      if c == "{" then depth = depth + 1 end
      if c == "}" then depth = depth - 1 end
      assert(depth >= 0, "unbalanced group")
      pos = pos + 1
    end
  end
  assert(depth == 0, "unbalanced group")
  result[#result + 1] = s:sub(start)
  return result
end

local function center(s, cols)
  return string.rep(" ", math.floor((cols - width(s)) / 2)) .. s
end

local function proof(tex, depth)
  assert(depth < 40, "proof too deep")
  tex = trim(tex)
  -- Parenthesized TeX groups around a nested inference are common.
  if tex:sub(1, 1) == "{" then
    local inner, pos = group(tex, 1, "{", "}")
    if pos > #tex then return proof(inner, depth + 1) end
  end
  if not tex:match("^\\infer[^a-zA-Z]") then
    assert(not tex:find("\\infer", 1, true), "mixed proof expression")
    local text = text_math(tex)
    assert(not text:find("\n", 1, true), "multiline premise")
    return {lines = {text}, width = width(text)}
  end
  local pos, label = 7, ""
  while tex:sub(pos, pos):match("%s") do pos = pos + 1 end
  if tex:sub(pos, pos) == "[" then
    label, pos = group(tex, pos, "[", "]")
    label = text_math(label)
  end
  local conclusion, body
  conclusion, pos = group(tex, pos, "{", "}")
  body, pos = group(tex, pos, "{", "}")
  assert(trim(tex:sub(pos)) == "", "trailing proof expression")
  conclusion = text_math(conclusion)
  local children, height, span = {}, 0, 0
  if trim(body) ~= "" then
    for _, premise in ipairs(split(body, "&")) do
      local box = proof(premise, depth + 1)
      children[#children + 1] = box
      height = math.max(height, #box.lines)
      span = span + box.width
    end
    span = span + 4 * (#children - 1)
  end
  local rule = math.max(span, width(conclusion), 1)
  local total = rule + (label ~= "" and 1 + width(label) or 0)
  assert(total <= limit, "proof too wide")
  local lines = {}
  for row = 1, height do
    local parts = {}
    for _, child in ipairs(children) do
      local line = child.lines[row - height + #child.lines] or ""
      parts[#parts + 1] = line .. string.rep(" ", child.width - width(line))
    end
    lines[#lines + 1] = center(table.concat(parts, "    "), rule):gsub(" +$", "")
  end
  lines[#lines + 1] = string.rep("─", rule) .. (label ~= "" and " " .. label or "")
  lines[#lines + 1] = center(conclusion, rule)
  return {lines = lines, width = total}
end

local environments = {
  array="array", aligned="aligned", align="aligned", ["align*"]="aligned",
  split="aligned", gathered="gathered", gather="gathered", ["gather*"]="gathered",
  matrix="matrix", pmatrix="matrix", bmatrix="matrix", Bmatrix="matrix",
  vmatrix="matrix", Vmatrix="matrix", cases="cases",
}
local delimiters = {
  pmatrix={"(", ")"}, bmatrix={"[", "]"}, Bmatrix={"{", "}"},
  vmatrix={"|", "|"}, Vmatrix={"‖", "‖"}, cases={"{", ""},
}
local tall = {
  ["("]={"⎛", "⎜", "⎝"}, [")"]={"⎞", "⎟", "⎠"},
  ["["]={"⎡", "⎢", "⎣"}, ["]"]={"⎤", "⎥", "⎦"},
  ["{"]={"⎧", "⎪", "⎩", "⎨"}, ["}"]={"⎫", "⎪", "⎭", "⎬"},
}

local function grid(tex)
  tex = trim(tex)
  local left, right
  -- A common array spelling is \left(\begin{array}...\end{array}\right).
  local l, inner, r = tex:match("^\\left(.-)%s*(\\begin.*)%s*\\right(.-)$")
  if l then
    local symbols = { ["\\{"]="{", ["\\}"]="}", ["\\lbrace"]="{",
      ["\\rbrace"]="}", ["\\lvert"]="|", ["\\rvert"]="|", ["."]="" }
    left, right = symbols[trim(l)] or trim(l), symbols[trim(r)] or trim(r)
    assert(left:match("^[%(%[%{|]$") or left == "", "unsupported delimiter")
    assert(right:match("^[%)%]%}|]$") or right == "", "unsupported delimiter")
    tex = trim(inner)
  end
  local env, body = tex:match("^\\begin{([%a*]+)}(.*)$")
  local kind = environments[env]
  assert(kind, "unsupported math environment")
  local ending = "\\end{" .. env .. "}"
  assert(body:sub(-#ending) == ending, "mismatched environment")
  body = body:sub(1, -#ending - 1)
  -- Nested environments need a more general box compositor; retain their TeX.
  assert(not body:find("\\begin", 1, true), "nested environment")
  local align, bars = {}, {}
  if kind == "array" then
    local spec, pos = group(body, 1, "{", "}")
    for char in spec:gmatch("%S") do
      if char == "|" then bars[#align + 1] = (bars[#align + 1] or "") .. "│"
      else
        assert(char:match("[lcr]"), "unsupported column specification")
        align[#align + 1] = char
      end
    end
    assert(#align > 0, "empty column specification")
    body = body:sub(pos)
  end
  local rows, widths, count = {}, {}, 0
  for _, raw in ipairs(split(body, "\\\\")) do
    raw = trim(raw)
    if raw:match("^\\hline%f[^%a]") then
      assert(kind == "array", "rule outside array")
      rows[#rows + 1] = false
      raw = trim(raw:sub(7))
    end
    if raw ~= "" then
      -- Row height tweaks and starred breaks are not silently reinterpreted.
      assert(not raw:match("^%[.*%]") and raw:sub(1, 1) ~= "*", "row spacing")
      local cells = split(raw, "&")
      if kind == "array" then assert(#cells <= #align, "too many columns") end
      if kind == "cases" then assert(#cells <= 2, "too many case columns") end
      if kind == "gathered" then assert(#cells == 1, "alignment in gathered") end
      for col, cell in ipairs(cells) do
        cells[col] = text_math(trim(cell))
        assert(not cells[col]:find("\n", 1, true), "multiline cell")
        widths[col] = math.max(widths[col] or 0, width(cells[col]))
      end
      count = math.max(count, #cells)
      rows[#rows + 1] = cells
    end
  end
  assert(count > 0, "empty grid")
  count = math.max(count, #align)
  local lines, rule_rows, longest = {}, {}, 0
  for row, cells in ipairs(rows) do
    local parts = {}
    if cells then
      for col = 1, count do
        local cell = cells[col] or ""
        local padding = (widths[col] or 0) - width(cell)
        local justification = align[col] or (kind == "aligned" and (col % 2 == 1 and "r" or "l"))
          or (kind == "cases" and "l") or "c"
        local before = justification == "r" and padding or (justification == "c" and math.floor(padding / 2)) or 0
        if col > 1 then
          parts[#parts + 1] = bars[col] and (" " .. bars[col] .. " ")
            or (kind == "aligned" and (col % 2 == 0 and " " or "    ")) or "  "
        elseif bars[col] then parts[#parts + 1] = bars[col] .. " " end
        parts[#parts + 1] = string.rep(" ", before) .. cell .. string.rep(" ", padding - before)
      end
      if bars[count + 1] then parts[#parts + 1] = " " .. bars[count + 1] end
    else rule_rows[row] = true end
    lines[row] = table.concat(parts)
    longest = math.max(longest, width(lines[row]))
  end
  local pair = delimiters[env] or {"", ""}
  left, right = left or pair[1], right or pair[2]
  local function edge(char, row)
    local shape = tall[char]
    if #lines == 1 or not shape then return char end
    return row == 1 and shape[1] or row == #lines and shape[3]
      or shape[4] and row == math.ceil(#lines / 2) and shape[4] or shape[2]
  end
  assert(longest + width(left) + width(right) <= limit, "grid too wide")
  for row, line in ipairs(lines) do
    line = rule_rows[row] and string.rep("─", longest) or line .. string.rep(" ", longest - width(line))
    lines[row] = (edge(left, row) .. line .. edge(right, row)):gsub(" +$", "")
  end
  return table.concat(lines, "\n")
end

local function render(el)
  local ok, text = pcall(function()
    if el.text:find("\\begin", 1, true) then
      assert(el.mathtype == "DisplayMath", "inline grid")
      return grid(el.text)
    end
    if el.text:find("\\infer", 1, true) then
      assert(el.mathtype == "DisplayMath", "inline proof")
      return table.concat(proof(el.text, 0).lines, "\n")
    end
    return text_math(el.text)
  end)
  return ok and text or el.text, ok
end

local function display_blocks(el)
  local blocks, pending = {}, {}
  local function flush()
    if #pending > 0 then blocks[#blocks + 1] = pandoc[el.t](pending); pending = {} end
  end
  for _, item in ipairs(el.content) do
    if item.t == "Math" and item.mathtype == "DisplayMath" then
      flush()
      local text = render(item)
      -- An unknown language such as "text" triggers Pandoc's expensive syntax
      -- lookup. No language is needed for already-rendered terminal math.
      blocks[#blocks + 1] = pandoc.CodeBlock(text)
    else
      pending[#pending + 1] = item
    end
  end
  flush()
  return blocks
end

return {{
  CodeBlock = function(el)
    if el.classes[1] == "text" or el.classes[1] == "plaintext" then
      el.classes:remove(1)
      return el
    end
  end,
  Math = function(el)
    if el.mathtype ~= "InlineMath" then return end
    local text, ok = render(el)
    return ok and pandoc.Str(text) or pandoc.Code(text)
  end,
  Para = display_blocks,
  Plain = display_blocks,
}}
