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

opt.listchars:append({
  eol = "󰌑",
  space = "␣",
  nbsp = "⍽",
  conceal = "┊",
  tab = "󰌒 ",
  trail = "󰑀",
})
