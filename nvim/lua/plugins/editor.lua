return {
  {
    "alexghergh/nvim-tmux-navigation",
    -- lazy = true,
    -- event = "VimEnter",
    opts = {
      disable_when_zoomed = true,
    },
    keys = {
      { "<C-h>", "<Cmd>NvimTmuxNavigateLeft<CR>" },
      { "<C-j>", "<Cmd>NvimTmuxNavigateDown<CR>" },
      { "<C-k>", "<Cmd>NvimTmuxNavigateUp<CR>" },
      { "<C-l>", "<Cmd>NvimTmuxNavigateRight<CR>" },
    },
  },
  {
    "lewis6991/spaceless.nvim",
    lazy = true,
    enabled = false,
    event = "InsertLeave",
    cond = function()
      return vim.bo.filetype ~= "markdown"
      -- return vim.bo.filetype ~= "yaml"
    end,
  },
  {
    "jamessan/vim-gnupg",
  },
  {
    "folke/zen-mode.nvim",
    dependencies = { "folke/twilight.nvim" },
    lazy = true,
    event = "BufEnter",
    opts = function(_, opts)
      opts.window = {
        backdrop = 1, -- shade the backdrop of the Zen window. Set to 1 to keep the same as Normal
        width = 90, -- width of the Zen window
        height = 10, -- height of the Zen window
        options = {
          number = false,
          relativenumber = false,
        },
      }
      opts.plugins = {
        options = {
          enabled = true,
          ruler = false, -- disables the ruler text in the cmd line area
          showcmd = false, -- disables the command in the last line of the screen
          -- you may turn on/off statusline in zen mode by setting 'laststatus'
          -- statusline will be shown only if 'laststatus' == 3
          laststatus = 0, -- turn off the statusline in zen mode
        },
        twilight = { enabled = true }, -- disables git signs
        tmux = { enabled = true }, -- disables the tmux statusline
      }
    end,
  },
  {
    "gbprod/cutlass.nvim",
    event = "BufEnter",
    opts = {
      cut_key = "x",
      exclude = { "ns", "nS" },
    },
  },
  -- {
  --   "echasnovski/mini.bracketed",
  --   -- lazy = true,
  --   -- event = "VeryLazy",
  --   config = function(_, opts)
  --     require("mini.bracketed").setup(opts)
  --   end,
  -- },
  -- {
  --   "echasnovski/mini.align",
  --   version = false,
  -- },
  {
    "godlygeek/tabular",
  },
  {
    "RRethy/vim-illuminate",
    enabled = false,
    opts = {
      filetypes_denylist = { "plaintex", "tex", "latex", "bib", "markdown", "mail", "text" },
    },
  },
}
