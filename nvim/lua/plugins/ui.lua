return {
  {
    "LazyVim/LazyVim",
    opts = {
      colorscheme = "onedark",
    },
  },
  {
    "navarasu/onedark.nvim",
    priority = 1000, -- make sure to load this before all the other start plugins
    config = function()
      require("onedark").setup({
        style = "darker",
        transparent = true,
        highlights = {
          ["@text.math"] = { fg = "$purple" },
          ["@text.environment"] = { fg = "$cyan" },
          ["@text.environment.name"] = { fg = "$yellow" },
          -- Spell: colored undercurl instead of plain underline
          SpellBad = { fg = "$red", undercurl = true },
          SpellCap = { sp = "$yellow", undercurl = true },
          SpellLocal = { sp = "$blue", undercurl = true },
          SpellRare = { sp = "$purple", undercurl = true },
        },
      })
      -- Enable theme
      require("onedark").load()
    end,
  },
  {
    "nvim-lualine/lualine.nvim",
    event = "VeryLazy",
    -- lazy = false,
    opts = function()
      -- require("config.evil_lualine")
      local lualine = require("lualine")

      -- Color table for highlights
      -- stylua: ignore
      local colors = {
        bg       = '#202328',
        fg       = '#bbc2cf',
        yellow   = '#ECBE7B',
        cyan     = '#008080',
        darkblue = '#081633',
        green    = '#98be65',
        orange   = '#FF8800',
        violet   = '#a9a1e1',
        magenta  = '#c678dd',
        blue     = '#51afef',
        red      = '#ec5f67',
      }

      local conditions = {
        buffer_not_empty = function()
          return vim.fn.empty(vim.fn.expand("%:t")) ~= 1
        end,
        hide_in_width = function()
          return vim.fn.winwidth(0) > 80
        end,
        check_git_workspace = function()
          local filepath = vim.fn.expand("%:p:h")
          local gitdir = vim.fn.finddir(".git", filepath .. ";")
          return gitdir and #gitdir > 0 and #gitdir < #filepath
        end,
      }

      -- Config
      local config = {
        options = {
          -- Disable sections and component separators
          component_separators = "",
          section_separators = "",
          theme = {
            -- We are going to use lualine_c an lualine_x as left and
            -- right section. Both are highlighted by c theme .  So we
            -- are just setting default looks o statusline
            normal = { c = { fg = colors.fg, bg = colors.bg } },
            inactive = { c = { fg = colors.fg, bg = colors.bg } },
          },
        },
        sections = {
          -- these are to remove the defaults
          lualine_a = {},
          lualine_b = {},
          lualine_y = {},
          lualine_z = {},
          -- These will be filled later
          lualine_c = {},
          lualine_x = {},
        },
        inactive_sections = {
          -- these are to remove the defaults
          lualine_a = {},
          lualine_b = {},
          lualine_y = {},
          lualine_z = {},
          lualine_c = {},
          lualine_x = {},
        },
      }

      -- Inserts a component in lualine_c at left section
      local function ins_left(component)
        table.insert(config.sections.lualine_c, component)
      end

      -- Inserts a component in lualine_x at right section
      local function ins_right(component)
        table.insert(config.sections.lualine_x, component)
      end

      ins_left({
        function()
          return "▊"
        end,
        color = { fg = colors.blue }, -- Sets highlighting of component
        padding = { left = 0, right = 1 }, -- We don't need space before this
      })

      ins_left({
        -- mode component
        function()
          return ""
        end,
        color = function()
          -- auto change color according to neovims mode
          local mode_color = {
            n = colors.red,
            i = colors.green,
            v = colors.blue,
            [""] = colors.blue,
            V = colors.blue,
            c = colors.magenta,
            no = colors.red,
            s = colors.orange,
            S = colors.orange,
            [""] = colors.orange,
            ic = colors.yellow,
            R = colors.violet,
            Rv = colors.violet,
            cv = colors.red,
            ce = colors.red,
            r = colors.cyan,
            rm = colors.cyan,
            ["r?"] = colors.cyan,
            ["!"] = colors.red,
            t = colors.red,
          }
          return { fg = mode_color[vim.fn.mode()] }
        end,
        padding = { right = 1 },
      })

      ins_left({
        -- filesize component
        "filesize",
        cond = conditions.buffer_not_empty,
      })

      ins_left({
        "filename",
        cond = conditions.buffer_not_empty,
        color = { fg = colors.magenta, gui = "bold" },
      })

      ins_left({ "location" })

      ins_left({ "progress", color = { fg = colors.fg, gui = "bold" } })

      ins_left({
        "diagnostics",
        sources = { "nvim_diagnostic" },
        symbols = { error = " ", warn = " ", info = " " },
        diagnostics_color = {
          error = { fg = colors.red },
          warn = { fg = colors.yellow },
          info = { fg = colors.cyan },
        },
      })

      -- Insert mid section. You can make any number of sections in neovim :)
      -- for lualine it's any number greater then 2
      ins_left({
        function()
          return "%="
        end,
      })

      ins_left({
        -- Lsp server name .
        function()
          local msg = "No Active Lsp"
          local buf_ft = vim.api.nvim_get_option_value("filetype", { buf = 0 })
          local clients = vim.lsp.get_clients()
          if next(clients) == nil then
            return msg
          end
          for _, client in ipairs(clients) do
            local filetypes = client.config.filetypes
            if filetypes and vim.fn.index(filetypes, buf_ft) ~= -1 then
              return client.name
            end
          end
          return msg
        end,
        icon = " LSP:",
        color = { fg = "#ffffff", gui = "bold" },
      })

      -- Add components to right sections
      ins_right({
        "o:encoding", -- option component same as &encoding in viml
        fmt = string.upper, -- I'm not sure why it's upper case either ;)
        cond = conditions.hide_in_width,
        color = { fg = colors.green, gui = "bold" },
      })

      ins_right({
        "fileformat",
        fmt = string.upper,
        icons_enabled = false, -- I think icons are cool but Eviline doesn't have them. sigh
        color = { fg = colors.green, gui = "bold" },
      })

      ins_right({
        "branch",
        icon = "",
        color = { fg = colors.violet, gui = "bold" },
      })

      ins_right({
        "diff",
        -- Is it me or the symbol for modified us really weird
        symbols = { added = " ", modified = "󰝤 ", removed = " " },
        diff_color = {
          added = { fg = colors.green },
          modified = { fg = colors.orange },
          removed = { fg = colors.red },
        },
        cond = conditions.hide_in_width,
      })

      ins_right({
        function()
          return "▊"
        end,
        color = { fg = colors.blue },
        padding = { left = 1 },
      })

      -- Now don't forget to initialize lualine
      -- lualine.setup(config)
      return config
    end,
  },
  {
    "folke/noice.nvim",
    -- enabled = false,
    opts = {
      cmdline = {
        view = "cmdline",
        format = {
          cmdline = { pattern = "^:", icon = "", lang = "vim" },
        },
      },
    },
  },
  -- lazy.nvim
  -- {
  --   "folke/snacks.nvim",
  --   ---@type snacks.Config
  --   opts = {
  --     image = {
  --       formats = {
  --         "png",
  --         "jpg",
  --         "jpeg",
  --         "gif",
  --         "bmp",
  --         "webp",
  --         "tiff",
  --         "heic",
  --         "avif",
  --         "mp4",
  --         "mov",
  --         "avi",
  --         "mkv",
  --         "webm",
  --         "pdf",
  --       },
  --       force = false, -- try displaying the image, even if the terminal does not support it
  --       doc = {
  --         -- enable image viewer for documents
  --         -- a treesitter parser must be available for the enabled languages.
  --         enabled = true,
  --         -- render the image inline in the buffer
  --         -- if your env doesn't support unicode placeholders, this will be disabled
  --         -- takes precedence over `opts.float` on supported terminals
  --         inline = true,
  --         -- render the image in a floating window
  --         -- only used if `opts.inline` is disabled
  --         float = true,
  --         max_width = 80,
  --         max_height = 40,
  --         -- Set to `true`, to conceal the image text when rendering inline.
  --         -- (experimental)
  --         ---@param lang string tree-sitter language
  --         ---@param type snacks.image.Type image type
  --         conceal = function(lang, type)
  --           -- only conceal math expressions
  --           return type == "math"
  --         end,
  --       },
  --       img_dirs = { "img", "images", "assets", "static", "public", "media", "attachments" },
  --       -- window options applied to windows displaying image buffers
  --       -- an image buffer is a buffer with `filetype=image`
  --       wo = {
  --         wrap = false,
  --         number = false,
  --         relativenumber = false,
  --         cursorcolumn = false,
  --         signcolumn = "no",
  --         foldcolumn = "0",
  --         list = false,
  --         spell = false,
  --         statuscolumn = "",
  --       },
  --       cache = vim.fn.stdpath("cache") .. "/snacks/image",
  --       debug = {
  --         request = false,
  --         convert = false,
  --         placement = false,
  --       },
  --       env = {},
  --       -- icons used to show where an inline image is located that is
  --       -- rendered below the text.
  --       icons = {
  --         math = "󰪚 ",
  --         chart = "󰄧 ",
  --         image = " ",
  --       },
  --       ---@class snacks.image.convert.Config
  --       convert = {
  --         notify = true, -- show a notification on error
  --         ---@type snacks.image.args
  --         mermaid = function()
  --           local theme = vim.o.background == "light" and "neutral" or "dark"
  --           return { "-i", "{src}", "-o", "{file}", "-b", "transparent", "-t", theme, "-s", "{scale}" }
  --         end,
  --         ---@type table<string,snacks.image.args>
  --         magick = {
  --           default = { "{src}[0]", "-scale", "1920x1080>" }, -- default for raster images
  --           vector = { "-density", 192, "{src}[0]" }, -- used by vector images like svg
  --           math = { "-density", 192, "{src}[0]", "-trim" },
  --           pdf = { "-density", 192, "{src}[0]", "-background", "white", "-alpha", "remove", "-trim" },
  --         },
  --       },
  --       math = {
  --         enabled = true, -- enable math expression rendering
  --         -- in the templates below, `${header}` comes from any section in your document,
  --         -- between a start/end header comment. Comment syntax is language-specific.
  --         -- * start comment: `// snacks: header start`
  --         -- * end comment:   `// snacks: header end`
  --         typst = {
  --           tpl = [[
  --       #set page(width: auto, height: auto, margin: (x: 2pt, y: 2pt))
  --       #show math.equation.where(block: false): set text(top-edge: "bounds", bottom-edge: "bounds")
  --       #set text(size: 12pt, fill: rgb("${color}"))
  --       ${header}
  --       ${content}]],
  --         },
  --         latex = {
  --           font_size = "large", -- see https://www.sascha-frank.com/latex-font-size.html
  --           -- for latex documents, the doc packages are included automatically,
  --           -- but you can add more packages here. Useful for markdown documents.
  --           packages = { "amsmath", "amssymb", "amsfonts", "amscd", "mathtools" },
  --           tpl = [[
  --       \documentclass[preview,border=0pt,varwidth,12pt]{standalone}
  --       \usepackage{${packages}}
  --       \begin{document}
  --       ${header}
  --       { \${font_size} \selectfont
  --         \color[HTML]{${color}}
  --       ${content}}
  --       \end{document}]],
  --         },
  --       },
  --     },
  --   },
  -- },
}
