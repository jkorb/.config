return {
  {
    "jkorb/mail.nvim",
    dir = vim.fn.expand("~/Dropbox/Projects/mail.nvim"),
    enabled = true,
    -- Register the grammar before headless parser updates too.
    lazy = false,
    dependencies = { "nvim-treesitter/nvim-treesitter" },
    opts = {
      parser = { url = "https://github.com/jkorb/tree-sitter-mail" },
      cmp_contacts = true,
      contacts_eval = "~/.config/neomutt/scripts/fetch_contacts {input}",
    },
  },
}
