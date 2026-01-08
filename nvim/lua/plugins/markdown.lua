return {
  {
    "vim-pandoc/vim-pandoc",
    enabled = false,
    -- ft = { "pandoc" },
    init = function()
      local utils = require("config.utils")

      utils.create_custom_aucmd("FileType", {
        group = "markdown",
        pattern = { "markdown", "mail", "pandoc" },
        -- pattern = "pandoc",
        callback = function()
          vim.bo.textwidth = 80
          vim.wo.spell = true
          vim.bo.formatoptions = "tcqj"
          -- vim.api.nvim_set_hl(0, "@conceal", { bold = true })
          -- vim.api.nvim_set_hl(0, "@markup.italic", { italic = true })
        end,
      })

      -- vim.api.nvim_create_autocmd("Syntax", {
      --   -- group = "PandocSyntax",
      --   pattern = "pandoc",
      --   callback = function()
      --     vim.cmd("source ~/.config/nvim/syntax/pandoc.vim")
      --   end,
      -- })

      -- vim.g["pandoc#filetypes#handled"] = { "markdown", "pandoc" }
      vim.g["pandoc#modules#disabled"] = { "folding", "completion", "bibliographies" }
      -- vim.g["pandoc#formatting#textwidht"] = 80
      vim.g["pandoc#keyboard#use_default_mappings"] = 0
    end,
    config = function()
      local utils = require("config.utils")
      local custom_map = utils.custom_map
      local custom_bmap = utils.custom_bmap

      custom_map("n", "<leader>m", function() end, { desc = "+markdown" })
      custom_map("n", "<leader>m/", "<cmd>TOC<cr>", { desc = "Show TOC" })
      -- Preview
      custom_map("n", "<leader>mv", "<cmd>MarkdownPreviewToggle<cr>", { desc = "Toggle Previewp" })
      -- Style
      custom_map("n", "<leader>me", "<Plug>(pandoc-keyboard-toggle-emphasis)", { desc = "Toggle Emphasis" })
      custom_map("n", "<leader>mb", "<Plug>(pandoc-keyboard-toggle-strong)", { desc = "Toggle Bold" })
      custom_map("n", "<leader>m'", "<Plug>(pandoc-keyboard-toggle-verbatim)", { desc = "Toggle Verbatim" })
      custom_map("n", "<leader>m~", "<Plug>(pandoc-keyboard-toggle-strikeout)", { desc = "Toggle Strikeout" })
      custom_map("n", "<leader>m^", "<Plug>(pandoc-keyboard-toggle-superscript)", { desc = "Toggle Superscript" })
      custom_map("n", "<leader>m_", "<Plug>(pandoc-keyboard-toggle-subscript)", { desc = "Toggle Subscript" })
      -- Sections
      custom_map("n", "<leader>m#", "<Plug>(pandoc-keyboard-apply-header)", { desc = "Apply header" })
      custom_map("n", "<leader>mh", function() end, { desc = "+header" })
      custom_map("n", "<leader>mhd", "<Plug>(pandoc-keyboard-remove-header)", { desc = "Remove" })
      custom_map("n", "<leader>mhn", "<Plug>(pandoc-keyboard-next-header)", { desc = "Next" })
      custom_map("n", "<leader>mhb", "<Plug>(pandoc-keyboard-prev-header)", { desc = "Previous" })
      custom_map("n", "<leader>mhh", "<Plug>(pandoc-keyboard-cur-header)", { desc = "Current" })
      custom_map("n", "<leader>mhp", "<Plug>(pandoc-keyboard-cur-header-parent)", { desc = "Current Parent" })
      custom_map("n", "<leader>mhs", function() end, { desc = "+sibling" })
      custom_map("n", "<leader>mhsn", "<Plug>(pandoc-keyboard-next-header-sibling)", { desc = "Next Sibling" })
      custom_map("n", "<leader>mhsb", "<Plug>(pandoc-keyboard-prev-header-sibling)", { desc = "Previous Sibling" })
      custom_map("n", "<leader>mhc", function() end, { desc = "+child" })
      custom_map("n", "<leader>mhcf", "<Plug>(pandoc-keyboard-first-header-child)", { desc = "First Child" })
      custom_map("n", "<leader>mhcl", "<Plug>(pandoc-keyboard-last-header-child)", { desc = "Last Child" })
      custom_map("n", "<leader>mhcn", "<Plug>(pandoc-keyboard-nth-header-child)", { desc = "n-th Child" })
      custom_map("n", "<leader>m]", function() end, { desc = "+previous section" })
      custom_map("n", "<leader>m]]", "<Plug>(pandoc-keyboard-ff-header)", { desc = "Beginning" })
      custom_map("n", "<leader>m][", "<Plug>(pandoc-keyboard-ff-sect-end)", { desc = "End" })
      custom_map("n", "<leader>m[", function() end, { desc = "+next section" })
      custom_map("n", "<leader>m[[", "<Plug>(pandoc-keyboard-rw-header)", { desc = "Beginning" })
      custom_map("n", "<leader>m[]", "<Plug>(pandoc-keyboard-rw-sect-end)", { desc = "End" })
      -- References
      custom_map("n", "<leader>mr", function() end, { desc = "+references" })
      custom_map("n", "<leader>mrr", "<Plug>(pandoc-keyboard-ref-insert)", { desc = "Insert" })
      custom_map("n", "<leader>mrb", "<Plug>(pandoc-keyboard-ref-goto)", { desc = "Go to" })
      custom_map("n", "<leader>mrg", "<Plug>(pandoc-keyboard-ref-backfrom)", { desc = "Back" })
      -- Links
      custom_map("n", "<leader>mo", "<Plug>(pandoc-keyboard-links-open)", { desc = "Follow Link" })
      custom_map("n", "<leader>mS", "<Plug>(pandoc-keyboard-links-split)", { desc = "Open Link in Split" })
      custom_map("n", "<leader>mO", "<Plug>(pandoc-keyboard-links-back)", { desc = "Go back from Link" })
      custom_map("n", "<leader>mR", "<Plug>(pandoc-keyboard-links-file-back)", { desc = "Go back to File" })
      -- List
      custom_map("n", "<leader>ml", function() end, { desc = "+list" })
      custom_map("n", "<leader>mln", "<Plug>(pandoc-keyboard-next-li)", { desc = "Next" })
      custom_map("n", "<leader>mlp", "<Plug>(pandoc-keyboard-prev-li)", { desc = "Previous" })
      custom_map("n", "<leader>mlc", "<Plug>(pandoc-keyboard-cur-li)", { desc = "Current" })
      custom_map("n", "<leader>mlP", "<Plug>(pandoc-keyboard-cur-li-parent)", { desc = "Current Parent" })
      custom_map("n", "<leader>mls", function() end, { desc = "+sibling" })
      custom_map("n", "<leader>mlsn", "<Plug>(pandoc-keyboard-next-li-sibling)", { desc = "Next Sibling" })
      custom_map("n", "<leader>mlsp", "<Plug>(pandoc-keyboard-prev-li-sibling)", { desc = "Previous Sibling" })
      custom_map("n", "<leader>mlc", function() end, { desc = "+child" })
      custom_map("n", "<leader>mlcf", "<Plug>(pandoc-keyboard-first-li-child)", { desc = "First Child" })
      custom_map("n", "<leader>mlcl", "<Plug>(pandoc-keyboard-last-li-child)", { desc = "Last Child" })
      custom_map("n", "<leader>mlcn", "<Plug>(pandoc-keyboard-nth-li-child)", { desc = "n-the Child" })
      -- Todo
      custom_map({ "n", "v" }, "<leader>mt", "<Plug>(pandoc-keyboard-toggle-cb)", { desc = "Toggle Todo" })
      custom_map({ "n", "v" }, "<leader>mT", "<Plug>(pandoc-keyboard-delete-cb)", { desc = "Delete Todo" })
      -- Text objects
      custom_map("v", "aS", "<Plug>(pandoc-keyboard-select-section-inclusive)", { desc = "Section" })
      custom_map("v", "iS", "<Plug>(pandoc-keyboard-select-section-exclusive)", { desc = "Section" })

      custom_bmap(0, "o", "aS", ":normal VaS<CR>", { desc = "Section" })
      custom_bmap(0, "o", "iS", ":normal ViS<CR>", { desc = "Section" })
    end,
  },
  {
    "vim-pandoc/vim-pandoc-syntax",
    enabled = false,
  },
  {
    "lukas-reineke/headlines.nvim",
    enabled = false,
  },
  {
    "folke/which-key.nvim",
    opts = {
      plugins = {
        spelling = {
          enabled = true,
          suggestions = 20,
        },
      },
    },
  },
  {
    "neovim/nvim-lspconfig",
    opts = {
      servers = {
        marksman = {
          filetypes = { "markdown", "markdown.mdx", "pandoc", "mail" },
        },
      },
    },
  },
  {
    "iamcco/markdown-preview.nvim",
    keys = {
      {
        "<leader>mv",
        "<cmd>MarkdownPreviewToggle<cr>",
        ft = "markdown",
        desc = "Toggle Preview",
      },
    },
  },
  {
    "MeanderingProgrammer/render-markdown.nvim",
    enabled = false,
  },
  {
    "mfussenegger/nvim-lint",
    enabled = false,
    opts = {
      linters_by_ft = {
        markdown = { "markdownlint" },
        pandoc = { "markdownlint" },
      },
    },
  },
}
