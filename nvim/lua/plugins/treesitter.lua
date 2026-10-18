return {
  {
    "nvim-treesitter/nvim-treesitter",
    -- Let LazyVim manage most settings; mail.lua registers the mail parser.
    opts = function(_, opts)
      opts.ensure_installed = opts.ensure_installed or {}
      for _, lang in ipairs({
        "bash",
        "bibtex",
        "c",
        "css",
        "scss",
        "svelte",
        "typst",
        "vue",
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
    end,
  },
}
