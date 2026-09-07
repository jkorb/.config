return {
  {
    "neovim/nvim-lspconfig",
    opts = {
      inlay_hints = {
        enabled = true,
        exclude = { "tex", "plaintex", "bib" },
      },
      servers = {
        clangd = {},
        yamlls = {},
        lua_ls = {
          -- mason = false, -- set to false if you don't want this server to be installed with mason
          settings = {
            Lua = {
              workspace = {
                checkThirdParty = false,
              },
              completion = {
                callSnippet = "Replace",
              },
            },
          },
        },
        bashls = {},
        pyright = {},
        -- marksman = {
        --   filetypes = { "markdown", "mail", "markdown.mdx", "pandoc" },
        -- },
        texlab = {
          settings = {
            texlab = {
              inlayHints = {
                labelDefinitions = false,
                labelReferences = false,
              },
              rootDirectory = nil,
              build = {
                executable = "latexmk",
                args = { "-pdflatex", "-synctex=1", "%f" },
                onSave = false,
                forwardSearchAfter = false,
              },
              forwardSearch = {
                executable = vim.fn.expand("$XDG_CONFIG_HOME/zathura/scripts/zathura-forward"),
                args = {
                  "%l:1:%f",
                  "%p",
                },
              },
              chktex = {
                onOpenAndSave = true,
                onEdit = false,
              },
              latexFormatter = "latexindent",
              formatterLineLength = 100000,
              latexindent = {
                ["local"] = "./latexindent.yaml",
                modifyLineBreaks = false,
              },
              -- formatterLineLength = 20,
            },
          },
        },
      },
    },
  },
}
