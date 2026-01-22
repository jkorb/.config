-- Options are automatically loaded before lazy.nvim startup
-- Default options that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/options.lua
-- Add any additional options here

local opt = vim.opt

-- opt.syntax = ""
opt.conceallevel = 0
opt.hlsearch = false -- Set highlight on search
opt.incsearch = true
opt.errorbells = false
opt.scrolloff = 10 -- Autoscroll when there's <= 10 lines left
opt.breakindent = true -- Enable break indent
opt.softtabstop = 2
opt.autoindent = true
opt.preserveindent = true
opt.hidden = true
opt.spell = false
opt.swapfile = false --No swapfile
opt.backup = false
opt.list = false
opt.expandtab = true
-- vim.o.completeopt = "menuone,noinsert,noselect" -- Set completeopt to have a better completion experience
-- opt.undodir = vim.fn.stdpath("config") .. "/undodir"
-- opt.directory = vim.fn.stdpath("config") .. "/swapdir"
--
opt.concealcursor = "nc"
-- vim.g["pandoc#filetypes#handled"] = { "mail", "markdown", "pandoc" }
vim.g.mkdp_filetypes = { "markdown", "markdown.mdx", "pandoc", "mail" }

opt.listchars:append({
  eol = "󰌑",
  space = "␣",
  nbsp = "⍽",
  conceal = "┊",
  tab = "󰌒 ",
  trail = "󰑀",
})

-- Ensure each Neovim instance has its own server for Synctex callbacks.
if vim.v.servername == "" then
  local sock = vim.fn.stdpath("run") .. "/nvim-" .. vim.fn.getpid() .. ".sock"
  vim.fn.serverstart(sock)
end
vim.env.NVIM_LISTEN_ADDRESS = vim.v.servername
-- Record server sockets with their working dirs for external tools (e.g. Zathura inverse search).
local state_dir = vim.fn.stdpath("state")
vim.fn.mkdir(state_dir, "p")
local server_map = state_dir .. "/servers"

local function update_server_map()
  local server = vim.v.servername
  if server == "" then
    return
  end
  local cwd = vim.fn.getcwd()
  local lines = {}
  local f = io.open(server_map, "r")
  if f then
    for line in f:lines() do
      local sock = line:match("^(%S+)%s+")
      if sock and sock ~= server then
        table.insert(lines, line)
      end
    end
    f:close()
  end
  table.insert(lines, server .. "\t" .. cwd)
  local out = io.open(server_map, "w")
  if out then
    out:write(table.concat(lines, "\n"))
    out:write("\n")
    out:close()
  end
end

local function remove_server_map()
  local server = vim.v.servername
  if server == "" then
    return
  end
  local f = io.open(server_map, "r")
  if not f then
    return
  end
  local lines = {}
  for line in f:lines() do
    local sock = line:match("^(%S+)%s+")
    if sock and sock ~= server then
      table.insert(lines, line)
    end
  end
  f:close()
  local out = io.open(server_map, "w")
  if out then
    out:write(table.concat(lines, "\n"))
    if #lines > 0 then
      out:write("\n")
    end
    out:close()
  end
end

vim.api.nvim_create_autocmd({ "VimEnter", "DirChanged" }, { callback = update_server_map })
vim.api.nvim_create_autocmd("VimLeavePre", { callback = remove_server_map })

-- Disable LSP logging unless explicitly enabled for debugging.
vim.lsp.set_log_level("OFF")
