local M = {}

function M.create_custom_augroup(name)
  return vim.api.nvim_create_augroup("lazyvim_custom_" .. name, { clear = true })
end

function M.create_custom_aucmd(event, opts)
  if opts.group then
    local augroup = M.create_custom_augroup(opts.group)
    opts.group = augroup
  end

  vim.api.nvim_create_autocmd(event, opts)
end

-- 0 means below and -1 means above
function M.insert_blank_line(direction)
  local pos = vim.api.nvim_win_get_cursor(0)
  vim.api.nvim_buf_set_lines(0, pos[1] + direction, pos[1] + direction, false, { "" })
end

function M.custom_map(mode, lhs, rhs, opts)
  local keys = require("lazy.core.handler").handlers.keys
  ---@cast keys LazyKeysHandler
  -- do not create the keymap if a lazy keys handler exists
  if not keys.active[keys.parse({ lhs, mode = mode }).id] then
    opts = opts or {}
    opts.silent = opts.silent ~= false
    vim.keymap.set(mode, lhs, rhs, opts)
  end
end

function M.custom_bmap(buff, mode, lhs, rhs, opts)
  local keys = require("lazy.core.handler").handlers.keys
  ---@cast keys LazyKeysHandler
  -- do not create the keymap if a lazy keys handler exists
  if not keys.active[keys.parse({ lhs, mode = mode }).id] then
    opts = opts or {}
    opts.silent = opts.silent ~= false
    vim.api.nvim_buf_set_keymap(buff, mode, lhs, rhs, opts)
  end
end

function M.toggle_list()
  if vim.opt.list:get() then
    vim.opt.list = false
  else
    vim.opt.list = true
  end
end

return M
