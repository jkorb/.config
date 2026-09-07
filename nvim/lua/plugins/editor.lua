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
        width = 82, -- prose-width window; soft wrap happens at the window edge
        height = 1, -- full editor height
        options = {
          number = false,
          relativenumber = false,
          signcolumn = "no",
          foldcolumn = "0",
          wrap = true,
          linebreak = true,
          breakindent = true,
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
