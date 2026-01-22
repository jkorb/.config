return {
  {
    "neovim/nvim-lspconfig",
    opts = {
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
              rootDirectory = nil,
              build = {
                executable = "latexmk",
                args = { "-pdflatex", "-synctex=1", "%f" },
                onSave = false,
                forwardSearchAfter = false,
              },
              forwardSearch = {
                executable = "zathura-forward",
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
              latexindent = {
                ["local"] = "./latexindent.yaml",
                modifyLineBreaks = true,
              },
              -- formatterLineLength = 20,
            },
          },
        },
      },
    },
  },
}
