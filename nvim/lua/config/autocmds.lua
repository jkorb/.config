-- Autocmds are automatically loaded on the VeryLazy event
-- Default autocmds that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/autocmds.lua
-- Add any additional autocmds here

local utils = require("config.utils")

local custom_augroup = utils.create_custom_augroup
local custom_map = utils.custom_map

local spellfiles = {
  en = vim.fn.stdpath("config") .. "/spell/en.utf-8.add",
  de = vim.fn.stdpath("config") .. "/spell/de.utf-8.add",
  nl = vim.fn.stdpath("config") .. "/spell/nl.utf-8.add",
}

local function spell_add(lang)
  local path = spellfiles[lang]
  if not path then
    vim.notify("Unknown spell lang: " .. lang, vim.log.levels.ERROR)
    return
  end
  local word = vim.fn.expand("<cword>")
  if word == "" then
    return
  end
  local current = vim.opt_local.spellfile:get()
  vim.opt_local.spellfile = path
  vim.cmd("silent! spellgood " .. vim.fn.escape(word, " \\\"'"))
  vim.opt_local.spellfile = current
end

local function spell_add_prompt()
  vim.ui.select({ "en", "de", "nl" }, { prompt = "Add word to language" }, function(choice)
    if choice then
      spell_add(choice)
    end
  end)
end

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

    vim.opt_local.spell = true
    vim.opt_local.textwidth = 0
    vim.opt_local.conceallevel = 0
    vim.opt_local.wrap = true
    vim.opt_local.linebreak = true
    vim.opt_local.breakindent = true
    vim.keymap.set("n", "zg", spell_add_prompt, { buffer = true, desc = "Spell add (select language)" })
    custom_map("n", "<leader>mc", "<cmd>LspTexlabBuild<cr>", { desc = "Texlab: build" })
    custom_map("n", "<leader>mx", "<cmd>LspTexlabCleanAuxiliary<cr>", { desc = "Texlab: clean" })
    custom_map("n", "<leader>mX", "<cmd>LspTexlabCleanArtifcats<cr>", { desc = "Texlab: purge" })
    custom_map("n", "<leader>mv", "<cmd>LspTexlabForward<cr>", { desc = "Texlab: view" })
  end,
})

vim.api.nvim_create_autocmd("FileType", {
  group = custom_augroup("markdown_like_spell"),
  pattern = { "markdown", "markdown.mdx", "pandoc", "mail", "text", "txt" },
  callback = function()
    vim.opt_local.spell = true
    vim.opt_local.spelllang = { "en_us", "de_de", "nl" }
    vim.opt_local.textwidth = 0
    vim.opt_local.formatoptions = "cqj"
    vim.opt_local.wrap = true
    vim.opt_local.linebreak = true
    vim.opt_local.breakindent = true
    vim.keymap.set("n", "zg", spell_add_prompt, { buffer = true, desc = "Spell add (select language)" })
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

if not vim.g.spell_add_lang_command then
  vim.g.spell_add_lang_command = true
  vim.api.nvim_create_user_command("SpellAddLang", function(opts)
    spell_add(opts.args)
  end, {
    nargs = 1,
    complete = function()
      return { "en", "de", "nl" }
    end,
    desc = "Add word under cursor to language-specific spellfile",
  })
end

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
