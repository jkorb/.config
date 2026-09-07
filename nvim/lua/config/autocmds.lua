-- Autocmds are automatically loaded on the VeryLazy event
-- Default autocmds that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/autocmds.lua
-- Add any additional autocmds here

local utils = require("config.utils")

local custom_augroup = utils.create_custom_augroup
local custom_map = utils.custom_map

local spell_langs = { "en", "de", "nl" }
local config_root = vim.fn.stdpath("config")
local xdg_config_root = vim.env.XDG_CONFIG_HOME
local repo_root = xdg_config_root and xdg_config_root ~= "" and xdg_config_root
  or vim.fn.fnamemodify(config_root, ":h")
local t_unpack = table.unpack or unpack

local spellfiles = {}
local spell_paths = {}
for _, lang in ipairs(spell_langs) do
  spellfiles[lang] = config_root .. "/spell/" .. lang .. ".utf-8.add"
  table.insert(spell_paths, "nvim/spell/" .. lang .. ".utf-8.add")
end

local function normalize_path(path)
  return vim.fn.fnamemodify(path, ":p")
end

local function git_cmd(repo_path, args)
  local cmd = { "git", "-C", repo_path }
  for _, arg in ipairs(args) do
    table.insert(cmd, arg)
  end
  local output = vim.fn.system(cmd)
  if vim.v.shell_error ~= 0 then
    return nil
  end
  return vim.trim(output)
end

local function git_has_in_progress_state(repo_path)
  local markers = { "MERGE_HEAD", "CHERRY_PICK_HEAD", "REVERT_HEAD", "rebase-merge", "rebase-apply" }
  for _, marker in ipairs(markers) do
    local path = git_cmd(repo_path, { "rev-parse", "--git-path", marker })
    if path and (vim.fn.filereadable(path) == 1 or vim.fn.isdirectory(path) == 1) then
      return true
    end
  end
  return false
end

local function maybe_commit_spellfiles()
  local toplevel = git_cmd(repo_root, { "rev-parse", "--show-toplevel" })
  if not toplevel or normalize_path(toplevel) ~= normalize_path(repo_root) then
    return
  end
  if git_has_in_progress_state(repo_root) then
    return
  end
  local status = git_cmd(repo_root, { "status", "--porcelain", "--untracked-files=no", "--", t_unpack(spell_paths) })
  if not status or status == "" then
    return
  end
  if not git_cmd(repo_root, { "add", "--", t_unpack(spell_paths) }) then
    return
  end
  git_cmd(repo_root, { "commit", "-m", "nvim: update spellfiles", "--", t_unpack(spell_paths) })
end

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
  vim.defer_fn(maybe_commit_spellfiles, 100)
end

local function spell_add_prompt()
  vim.ui.select(spell_langs, { prompt = "Add word to language" }, function(choice)
    if choice then
      spell_add(choice)
    end
  end)
end

local function latex_list_env(line)
  local begin_env = line:match("\\begin%s*{%s*([%a*]+)%s*}")
  if begin_env == "itemize" or begin_env == "enumerate" then
    return "begin", begin_env
  end

  local end_env = line:match("\\end%s*{%s*([%a*]+)%s*}")
  if end_env == "itemize" or end_env == "enumerate" then
    return "end", end_env
  end
end

local function latex_current_list()
  local row = vim.api.nvim_win_get_cursor(0)[1]
  local lines = vim.api.nvim_buf_get_lines(0, 0, row, false)
  local stack = {}

  for lnum, line in ipairs(lines) do
    local kind, env = latex_list_env(line)
    if kind == "begin" then
      table.insert(stack, {
        env = env,
        indent = line:match("^%s*") or "",
        lnum = lnum,
      })
    elseif kind == "end" then
      for i = #stack, 1, -1 do
        if stack[i].env == env then
          table.remove(stack, i)
          break
        end
      end
    end
  end

  return stack[#stack]
end

local function latex_insert_item_below()
  local list = latex_current_list()
  local cursor_row = vim.api.nvim_win_get_cursor(0)[1]
  local line_count = vim.api.nvim_buf_line_count(0)
  local item_indent = nil
  local search_start = list and list.lnum or 1

  for lnum = cursor_row, search_start, -1 do
    local line = vim.api.nvim_buf_get_lines(0, lnum - 1, lnum, false)[1] or ""
    item_indent = line:match("^(%s*)\\item")
    if item_indent then
      break
    end
  end

  if not item_indent then
    if list then
      local shiftwidth = vim.bo.shiftwidth > 0 and vim.bo.shiftwidth or vim.bo.tabstop
      item_indent = list.indent .. (vim.bo.expandtab and string.rep(" ", shiftwidth) or "\t")
    else
      local line = vim.api.nvim_buf_get_lines(0, cursor_row - 1, cursor_row, false)[1] or ""
      item_indent = line:match("^%s*") or ""
    end
  end

  local insert_lnum = cursor_row + 1
  if list then
    local nested = 0
    for lnum = cursor_row + 1, line_count do
      local line = vim.api.nvim_buf_get_lines(0, lnum - 1, lnum, false)[1] or ""
      local kind, env = latex_list_env(line)

      if nested == 0 and line:match("^" .. vim.pesc(item_indent) .. "\\item") then
        insert_lnum = lnum
        break
      end

      if kind == "begin" then
        nested = nested + 1
      elseif kind == "end" then
        if nested == 0 and env == list.env then
          insert_lnum = lnum
          break
        end
        nested = math.max(nested - 1, 0)
      end
    end
  end

  local new_line = item_indent .. "\\item "
  vim.api.nvim_buf_set_lines(0, insert_lnum - 1, insert_lnum - 1, false, { new_line })
  vim.api.nvim_win_set_cursor(0, { insert_lnum, #new_line })
  vim.cmd("startinsert")
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
    vim.opt_local.spelllang = { "en_us", "de_de", "nl" }
    vim.opt_local.textwidth = 0
    vim.opt_local.formatoptions = "cqj"
    vim.opt_local.conceallevel = 0
    vim.opt_local.wrap = true
    vim.opt_local.linebreak = true
    vim.opt_local.breakindent = true
    vim.keymap.set("n", "zg", spell_add_prompt, { buffer = true, desc = "Spell add (select language)" })
    vim.keymap.set("n", "<leader>i", latex_insert_item_below, { buffer = true, desc = "LaTeX: new item", silent = true })
    vim.keymap.set("i", "<C-t>", latex_insert_item_below, { buffer = true, desc = "LaTeX: new item", silent = true })
    custom_map("n", "<leader>mc", "<cmd>LspTexlabBuild<cr>", { desc = "Texlab: build" })
    custom_map("n", "<leader>mx", "<cmd>LspTexlabCleanAuxiliary<cr>", { desc = "Texlab: clean" })
    custom_map("n", "<leader>mX", "<cmd>LspTexlabCleanArtifacts<cr>", { desc = "Texlab: purge" })
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
