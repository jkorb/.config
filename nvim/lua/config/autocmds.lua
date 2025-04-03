-- Autocmds are automatically loaded on the VeryLazy event
-- Default autocmds that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/autocmds.lua
-- Add any additional autocmds here

local utils = require("config.utils")

local custom_augroup = utils.create_custom_augroup
local custom_map = utils.custom_map

vim.api.nvim_create_autocmd("FileType", {
  group = custom_augroup("filetype_keybinds"),
  pattern = { "plaintex", "latex", "tex" },
  callback = function()
    vim.api.nvim_buf_create_user_command(0, "TexlabClean", function(_)
      local arguments = vim.lsp.util.make_text_document_params()
      vim.lsp.buf.execute_command({ command = "texlab.cleanAuxiliary", arguments = { arguments } })
    end, { desc = "Texlab: clean" })

    vim.api.nvim_buf_create_user_command(0, "TexlabPurge", function(_)
      local arguments = vim.lsp.util.make_text_document_params()
      vim.lsp.buf.execute_command({ command = "texlab.cleanArtifacts", arguments = { arguments } })
    end, { desc = "Texlab: purge" })

    vim.opt.spell = true
    vim.opt.tw = 80
    vim.opt.conceallevel = 0
    custom_map("n", "<leader>mc", "<cmd>TexlabBuild<cr>", { desc = "Texlab: build" })
    custom_map("n", "<leader>mx", "<cmd>TexlabClean<cr>", { desc = "Texlab: clean" })
    custom_map("n", "<leader>mX", "<cmd>TexlabPurge<cr>", { desc = "Texlab: purge" })
    custom_map("n", "<leader>mv", "<cmd>TexlabForward<cr>", { desc = "Texlab: view" })
  end,
})

-- vim.api.nvim_create_autocmd("FileType", {
--   group = augroup("filetype_keybinds"),
--   pattern = { "markdown", "mail", "pandoc" },
--   callback = function()
--     map("v", "mf", "<cmd>Tabularize /|<cr>", { desc = "Markdown preview Toggle" })
--   end,
-- })

vim.api.nvim_create_autocmd("FileType", {
  pattern = { "pandoc", "markdown", "mail" },
  -- pattern = "pandoc",
  callback = function()
    vim.api.nvim_set_hl(0, "@markup.italic", { italic = true })
  end,
})

-- vim.api.nvim_create_autocmd("Syntax", {
--   -- group = "PandocSyntax",
--   pattern = { "pandoc", "markdown", "mail" },
--   -- pattern = "pandoc",
--   callback = function()
--     vim.cmd("source ~/.config/nvim/after/syntax/pandoc.vim")
--   end,
-- })

-- vim.api.nvim_create_augroup("PandocSyntax", {clear = true})
-- vim.api.nvim_create_autocmd("Syntax", {
--   -- group = "PandocSyntax",
--   pattern = "pandoc",
--   callback = function()
--     vim.cmd("source ~/.config/nvim/syntax/pandoc.vim")
--   end,
-- })
