return {
  {
    "nvim-treesitter/nvim-treesitter",
    -- Let LazyVim manage most settings; just add languages and custom parser.
    opts = function(_, opts)
      opts.ensure_installed = opts.ensure_installed or {}
      for _, lang in ipairs({
        "bash",
        "bibtex",
        "c",
        "cpp",
        "html",
        "go",
        "javascript",
        "json",
        "latex",
        "lua",
        "markdown",
        "markdown_inline",
        "python",
        "query",
        "regex",
        "tsx",
        "typescript",
        "vim",
        "yaml",
      }) do
        if not vim.tbl_contains(opts.ensure_installed, lang) then
          table.insert(opts.ensure_installed, lang)
        end
      end

      -- Register custom mail parser from local tree-sitter repo.
      local parsers = require("nvim-treesitter.parsers")
      parsers.mail = parsers.mail
        or {
          install_info = {
            path = vim.fn.expand("~/Dropbox/Projects/treesitter-mail/tree-sitter-mail/"),
            files = { "src/parser.c", "src/scanner.c" },
          },
        }

      vim.treesitter.language.register("mail", { "mail" })
    end,
  },
}
