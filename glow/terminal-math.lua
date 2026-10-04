-- Pandoc handles ordinary TeX math; this filter adds proof.sty's \infer trees.
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

local function premises(s)
  local result, start, depth, pos = {}, 1, 0, 1
  while pos <= #s do
    local c = s:sub(pos, pos)
    if c == "\\" then
      pos = pos + 2
    else
      if c == "{" then depth = depth + 1 end
      if c == "}" then depth = depth - 1 end
      if c == "&" and depth == 0 then
        result[#result + 1] = s:sub(start, pos - 1)
        start = pos + 1
      end
      pos = pos + 1
    end
  end
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
    for _, premise in ipairs(premises(body)) do
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

local function render(el)
  local ok, text = pcall(function()
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
      blocks[#blocks + 1] = pandoc.CodeBlock(text, pandoc.Attr("", {"text"}))
    else
      pending[#pending + 1] = item
    end
  end
  flush()
  return blocks
end

return {{
  Math = function(el)
    if el.mathtype ~= "InlineMath" then return end
    local text, ok = render(el)
    return ok and pandoc.Str(text) or pandoc.Code(text)
  end,
  Para = display_blocks,
  Plain = display_blocks,
}}
