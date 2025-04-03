-- Keymaps are automatically loaded on the VeryLazy event
-- Default keymaps that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/keymaps.lua
-- Add any additional keymaps here

-- local Util = require("lazyvim.util")

local utils = require("config.utils")
local custom_map = utils.custom_map

-- stylua: ignore start
custom_map("n", "[<space>", function() utils.insert_blank_line(-1) end, { desc = "Insert blank line above", silent = true })
custom_map("n", "]<space>", function() utils.insert_blank_line(0) end, { desc = "Insert blank line below", silent = true })
custom_map({"n", "v"}, "<space>cf", "gw", { desc = "Format text" } )
custom_map("n", "gt", "<cmd>BufferLineCyclePrev<cr>", { desc = "Previous buffer" } )
custom_map("n", "gT", "<cmd>BufferLineCycleNext<cr>", { desc = "Next buffer" } )

custom_map('n', '<leader>u;', function() utils.toggle_list() end, { desc = "Toggle list"} )
