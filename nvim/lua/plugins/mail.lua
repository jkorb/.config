return {
  {
    dir = "~/Dropbox/Projects/mail.nvim/",
    enabled = true,
    dependencies = { "nvim-treesitter/nvim-treesitter" },
    -- config = function()
    --   local parser_config = require("nvim-treesitter.parsers").get_parser_configs()
    --   parser_config.mail = {
    --     install_info = {
    --       url = "~/Dropbox/Projects/treesitter-mail/tree-sitter-mail/", -- local path or git repo
    --       files = { "src/parser.c", "src/scanner.c" }, -- note that some parsers also require src/scanner.c or src/scanner.cc
    --       -- optional entries:
    --       branch = "main", -- default branch in case of git repo if different from master
    --       generate_requires_npm = false, -- if stand-alone parser without npm dependencies
    --       requires_generate_from_grammar = false, -- if folder contains pre-generated src/parser.c
    --     },
    --     filetype = "mail", -- if filetype does not match the parser name
    --   }
    -- end,
    opts = {
      cmp_contacts = true,
      contacts_eval = "~/.config/neomutt/scripts/fetch_contacts {input}",
    },
    event = "VeryLazy",
    -- ft = "mail",
  },
}
