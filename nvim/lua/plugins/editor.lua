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
        backdrop = 0.5, -- shade the backdrop of the Zen window. Set to 1 to keep the same as Normal
        width = 90, -- width of the Zen window
        height = 0.9, -- height of the Zen window
      }
      opts.plugins = {
        twilight = { enabled = true }, -- disables git signs
        tmux = { enabled = false }, -- disables the tmux statusline
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
  {
    "echasnovski/mini.bracketed",
    -- lazy = true,
    -- event = "VeryLazy",
    config = function(_, opts)
      require("mini.bracketed").setup(opts)
    end,
  },
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
