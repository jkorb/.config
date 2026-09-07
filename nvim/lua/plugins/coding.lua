return {
  {
    "L3MON4D3/LuaSnip",
    opts = {
      store_selection_keys = "<Tab>",
      region_check_events = "InsertEnter",
      delete_check_events = "InsertLeave",
    },
  },
  {
    "phelipetls/vim-hugo",
    enabled = false,
  },
  {
    "saghen/blink.compat",
    enabled = true,
    version = "*",
    lazy = true,
  },
  {
    "saghen/blink.cmp",
    dependencies = {
      {
        "kdheepak/cmp-latex-symbols",
        config = function()
          local cmp = require("cmp")
          local latex_symbols = require("cmp_latex_symbols")

          cmp.register_source("latex_symbols_tex", latex_symbols.new())
          cmp.register_source("latex_symbols_unicode", latex_symbols.new())
        end,
      },
      "jc-doyle/cmp-pandoc-references",
      "ribru17/blink-cmp-spell",
      "hrsh7th/cmp-emoji",
      "Kaiser-Yang/blink-cmp-dictionary",
      dependencies = { "nvim-lua/plenary.nvim" },
    },
    opts = function(_, opts)
      local function tex_command_context()
        if not vim.tbl_contains({ "latex", "plaintex", "tex" }, vim.bo.filetype) then
          return nil
        end

        local col = vim.api.nvim_win_get_cursor(0)[2]
        local before = vim.api.nvim_get_current_line():sub(1, col)
        local depth = 0
        local open_pos

        for i = #before, 1, -1 do
          local char = before:sub(i, i)
          if char == "}" then
            depth = depth + 1
          elseif char == "{" then
            if depth == 0 then
              open_pos = i
              break
            end
            depth = depth - 1
          end
        end

        if not open_pos then
          return nil
        end

        local prefix = before:sub(1, open_pos - 1):gsub("%s+$", "")
        while prefix:match("%b[]$") do
          prefix = prefix:gsub("%s*%b[]$", "")
        end

        local command = prefix:match("\\([%a]+%*)%s*$") or prefix:match("\\([%a]+)%s*$")
        if not command then
          return nil
        end

        command = command:gsub("%*$", ""):lower()
        if
          vim.tbl_contains({
            "autocite",
            "autocites",
            "cite",
            "citealp",
            "citealt",
            "citeauthor",
            "citep",
            "cites",
            "citet",
            "citeyear",
            "citeyearpar",
            "footcite",
            "footcites",
            "parencite",
            "parencites",
            "smartcite",
            "smartcites",
            "supercite",
            "supercites",
            "textcite",
            "textcites",
          }, command)
        then
          return "cite"
        end

        if
          vim.tbl_contains({
            "autoref",
            "cpageref",
            "cref",
            "crefrange",
            "eqref",
            "fullref",
            "nameref",
            "pageref",
            "ref",
            "subref",
            "vpageref",
            "vref",
          }, command)
        then
          return "ref"
        end

        return nil
      end

      local function in_tex_lookup_context()
        return tex_command_context() ~= nil
      end

      local function prose_filetype()
        return vim.tbl_contains(
          { "gitcommit", "latex", "mail", "markdown", "pandoc", "plaintex", "rst", "tex", "text" },
          vim.bo.filetype
        )
      end

      opts.keymap = {
        preset = "default",
        -- ["<C-y>"] = { "select_and_accept" },
        ["<C-space>"] = { "show_documentation", "hide_documentation" },
      }
      opts.snippets = { preset = "luasnip" }
      if not vim.tbl_contains(opts.sources.default, "snippets") then
        table.insert(opts.sources.default, "snippets")
      end
      opts.sources.providers.snippets = vim.tbl_deep_extend("force", opts.sources.providers.snippets or {}, {
        enabled = function()
          return not in_tex_lookup_context()
        end,
        score_offset = 150,
        opts = {
          show_autosnippets = true,
        },
      })
      opts.sources.compat = {
        "emoji",
        "cmp-contacts",
        "pandoc_references",
        "latex_symbols_tex",
        "latex_symbols_unicode",
      }
      table.insert(opts.sources.default, "dictionary")
      table.insert(opts.sources.default, "spell")
      opts.sources.providers.dictionary = {
        module = "blink-cmp-dictionary",
        name = "Dict",
        min_keyword_length = 3,
        enabled = function()
          return prose_filetype() and not in_tex_lookup_context()
        end,
        opts = {
          dictionary_files = { "/Users/jkorbmacher/.config/english-words/words.txt" },
          -- options for blink-cmp-dictionary
        },
      }
      opts.sources.providers.spell = {
        name = "Spell",
        module = "blink-cmp-spell",
        enabled = function()
          return prose_filetype() and not in_tex_lookup_context()
        end,
      }

      opts.sources.providers.latex_symbols_tex = vim.tbl_deep_extend("force", opts.sources.providers.latex_symbols_tex or {}, {
        name = "latex_symbols_tex",
        module = "blink.compat.source",
        enabled = function()
          return vim.tbl_contains({ "latex", "plaintex", "tex" }, vim.bo.filetype) and not in_tex_lookup_context()
        end,
        score_offset = 100,
        opts = {
          strategy = 2,
        },
      })
      opts.sources.providers.latex_symbols_unicode = vim.tbl_deep_extend("force", opts.sources.providers.latex_symbols_unicode or {}, {
        name = "latex_symbols_unicode",
        module = "blink.compat.source",
        enabled = function()
          return vim.tbl_contains({ "gitcommit", "mail", "markdown", "pandoc", "rst", "text" }, vim.bo.filetype)
        end,
        score_offset = 100,
        opts = {
          strategy = 0,
        },
      })
      opts.sources.providers.lsp = vim.tbl_deep_extend("force", opts.sources.providers.lsp or {}, {
        fallbacks = function()
          return in_tex_lookup_context() and {} or { "buffer" }
        end,
        score_offset = -10,
      })
      opts.sources.providers.copilot = vim.tbl_deep_extend("force", opts.sources.providers.copilot or {}, {
        enabled = function()
          return not in_tex_lookup_context()
        end,
        score_offset = -40,
      })
      opts.sources.providers.path = vim.tbl_deep_extend("force", opts.sources.providers.path or {}, {
        enabled = function()
          return not in_tex_lookup_context()
        end,
      })
      opts.sources.providers.buffer = vim.tbl_deep_extend("force", opts.sources.providers.buffer or {}, {
        enabled = function()
          return not in_tex_lookup_context()
        end,
      })
    end,
  },
}
