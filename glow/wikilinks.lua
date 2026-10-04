-- Convert Pandoc's wiki links to ordinary links that Glow can render.
local source = PANDOC_STATE.input_files[1]
if not source or source == "-" then source = os.getenv("MD_READ_SOURCE") or "" end
local base = pandoc.path.directory(source)

local function exists(path)
  local file = io.open(path, "r")
  if not file then return false end
  file:close()
  return true
end

function Link(link)
  if not link.classes:includes("wikilink") then return end
  -- Keeping the wikilink class makes the GFM writer emit raw HTML.
  link.classes = link.classes:filter(function(class) return class ~= "wikilink" end)
  local path, suffix = link.target:match("^([^#?]*)(.*)$")
  if path ~= "" and not path:match("^%a[%w+.-]*:") and not path:match("^//") then
    local decoded = path:gsub("%%(%x%x)", function(hex) return string.char(tonumber(hex, 16)) end)
    local _, extension = pandoc.path.split_extension(decoded)
    local local_path = decoded:sub(1, 1) == "/" and decoded or pandoc.path.join({base, decoded})
    if extension == "" and not exists(local_path) and exists(local_path .. ".md") then
      link.target = path .. ".md" .. suffix
    end
  end
  -- Unlike ordinary Markdown links, wiki targets may contain literal spaces.
  link.target = link.target:gsub('[%s<>()\\"]', function(char)
    return string.format("%%%02X", string.byte(char))
  end)
  return link
end
