return {
  {
    "iurimateus/luasnip-latex-snippets.nvim",
    -- vimtex isn't required if using treesitter
    -- dependencies = { "L3MON4D3/LuaSnip", "lervag/vimtex" },
    opts = {
      use_treesitter = true,
      allow_on_markdown = true,
    },
  },
  {
    "L3MON4D3/LuaSnip",
    opts = {
      enable_autosnippets = false,
    },
  },
  {
    "lervag/vimtex",
    enabled = true, -- lazy-loading will disable inverse search
    -- config = function()
    --   vim.api.nvim_create_autocmd({ "FileType" }, {
    --     group = vim.api.nvim_create_augroup("lazyvim_vimtex_conceal", { clear = true }),
    --     pattern = { "bib", "tex" },
    --     callback = function()
    --       vim.wo.conceallevel = 2
    --     end,
    --   })
    --   vim.g.vimtex_syntax_conceal_disable = 1
    --   vim.g.vimtex_mappings_disable = { ["n"] = { "K" } } -- disable `K` as it conflicts with LSP hover
    --   vim.g.vimtex_quickfix_method = vim.fn.executable("pplatex") == 1 and "pplatex" or "latexlog"
    -- end,
  },
}
