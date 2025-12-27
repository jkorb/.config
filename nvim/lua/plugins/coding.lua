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
    -- use the latest release, via version = '*', if you also use the latest release for blink.cmp
    version = "*",
    -- lazy.nvim will automatically load the plugin when it's required by blink.cmp
    lazy = true,
    -- make sure to set opts so that lazy.nvim calls blink.compat's setup
  },
  {
    "saghen/blink.cmp",
    dependencies = {
      "kdheepak/cmp-latex-symbols",
      "jc-doyle/cmp-pandoc-references",
      "ribru17/blink-cmp-spell",
      -- "moyiz/blink-emoji.nvim",
      "hrsh7th/cmp-emoji",
      "Kaiser-Yang/blink-cmp-dictionary",
      dependencies = { "nvim-lua/plenary.nvim" },
    },
    opts = function(_, opts)
      opts.keymap = {
        preset = "default",
        -- ["<C-y>"] = { "select_and_accept" },
        ["<C-space>"] = { "show_documentation", "hide_documentation" },
      }
      opts.sources.compat = {
        "emoji",
        "cmp-contacts",
        "pandoc_references",
        "latex_symbols",
      }

      -- table.insert(opts.sources.default, "latex_symbols")
      --
      -- if vim.bo.ft == "tex" then
      --   opts.sources.providers.latex_symbols = {
      --     name = "latex_symbols",
      --     module = "blink.compat.source",
      --     opts = { strategy = 2 },
      --   }
      -- else
      --   opts.sources.providers.latex_symbols = {
      --     name = "latex_symbols",
      --     module = "blink.compat.source",
      --     opts = { strategy = 2 },
      --   }
      -- end
      table.insert(opts.sources.default, "dictionary")
      opts.sources.providers.dictionary = {
        module = "blink-cmp-dictionary",
        name = "Dict",
        -- Make sure this is at least 2.
        -- 3 is recommended
        min_keyword_length = 3,
        opts = {
          dictionary_files = { "~/.config/english-words/words.txt" },
          -- options for blink-cmp-dictionary
        },
      }
      -- table.insert(opts.sources.default, "emoji")
      -- opts.sources.providers.emoji = {
      --   module = "blink-emoji",
      --   name = "Emoji",
      --   score_offset = 15, -- Tune by preference
      --   opts = { insert = true }, -- Insert emoji (default) or complete its name
      --   should_show_items = function()
      --     return vim.tbl_contains(
      --       -- Enable emoji completion only for git commits and markdown.
      --       -- By default, enabled for all file-types.
      --       { "gitcommit", "markdown", "mail" },
      --       vim.o.filetype
      --     )
      --   end,
      -- }
      table.insert(opts.sources.default, "spell")
      opts.sources.providers.spell = {
        name = "Spell",
        module = "blink-cmp-spell",
        opts = {
          -- EXAMPLE: Only enable source in `@spell` captures, and disable it
          -- in `@nospell` captures.
          enable_in_context = function()
            local curpos = vim.api.nvim_win_get_cursor(0)
            local captures = vim.treesitter.get_captures_at_pos(0, curpos[1] - 1, curpos[2] - 1)
            local in_spell_capture = false
            for _, cap in ipairs(captures) do
              if cap.capture == "spell" then
                in_spell_capture = true
              elseif cap.capture == "nospell" then
                return false
              end
            end
            return in_spell_capture
          end,
        },
      }
    end,
  },
}
