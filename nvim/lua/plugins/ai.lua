return {
  -- {
  --   "github/copilot.vim",
  --   config = function()
  --     -- Set copilot_filetypes to disable by default, enabling only for Python files
  --     vim.g.copilot_filetypes = {
  --       ["*"] = false,
  --       ["lean"] = true,
  --       ["python"] = true,
  --       ["plaintex"] = true,
  --       ["tex"] = true,
  --     }
  --     vim.g.copilot_no_tab_map = true
  --
  --     -- Keybindings for Copilot functionality
  --     vim.keymap.set("i", "<C-J>", 'copilot#Accept("\\<CR>")', { expr = true, silent = true, replace_keycodes = false })
  --     vim.keymap.set("i", "<C-N>", "<Plug>(copilot-next)", { silent = true })
  --     vim.keymap.set("i", "<C-P>", "<Plug>(copilot-previous)", { silent = true })
  --     vim.keymap.set("i", "<C-Esc>", "<Plug>(copilot-dismiss)", { silent = true })
  --   end,
  -- },
  {
    "jackMort/ChatGPT.nvim",
    event = "VeryLazy",
    opts = {
      api_key_cmd = "/usr/bin/pass ChatGPT.nvim",
      openai_edit_params = {
        model = "gpt-4o",
        frequency_penalty = 0,
        presence_penalty = 0,
        temperature = 0,
        top_p = 1,
        n = 1,
      },
    },
    dependencies = {
      "MunifTanjim/nui.nvim",
      "nvim-lua/plenary.nvim",
      "nvim-telescope/telescope.nvim",
    },
  },
  {
    "zbirenbaum/copilot.lua",
    opts = function(_, opts)
      opts.filetypes = {
        mail = false,
        csv = false,
      }
    end,
  },
}
