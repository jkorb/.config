return {
  {
    "jkorb/prover9.nvim",
    lazy = false,
    priority = 1000,
    dependencies = { "nvim-treesitter/nvim-treesitter" },
    opts = {
      grammar_url = "https://github.com/jkorb/prover9_treesitter",
    },
    config = function(_, opts)
      require("prover9").setup(opts)
      vim.api.nvim_set_hl(0, "@operator", { fg = require("config.theme").colors.blue, bold = true })
    end,
  },
}
