return {
  {
    dir = "~/Dropbox/Projects/mail.nvim/",
    enabled = true,
    dependencies = { "nvim-treesitter/nvim-treesitter" },
    opts = {
      cmp_contacts = true,
      contacts_eval = "~/.config/neomutt/scripts/fetch_contacts {input}",
    },
    event = "VeryLazy",
    ft = "mail",
  },
}
