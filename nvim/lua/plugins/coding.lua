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
      "kdheepak/cmp-latex-symbols",
      "jc-doyle/cmp-pandoc-references",
      "ribru17/blink-cmp-spell",
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
      table.insert(opts.sources.default, "dictionary")
      opts.sources.providers.dictionary = {
        module = "blink-cmp-dictionary",
        name = "Dict",
        min_keyword_length = 3,
        opts = {
          dictionary_files = { "~/.config/english-words/words.txt" },
          -- options for blink-cmp-dictionary
        },
      }
      table.insert(opts.sources.default, "spell")
      opts.sources.providers.spell = {
        name = "Spell",
        module = "blink-cmp-spell",
        opts = {
          enable_in_context = function()
            local curpos = vim.api.nvim_win_get_cursor(0)
            local row, col = curpos[1] - 1, curpos[2] - 1
            local ok, captures = pcall(vim.treesitter.get_captures_at_pos, 0, row, col)

            if ok and captures and #captures > 0 then
              local in_spell_capture = false
              for _, cap in ipairs(captures) do
                if cap.capture == "spell" then
                  in_spell_capture = true
                elseif cap.capture == "nospell" then
                  return false
                end
              end
              if in_spell_capture then
                return true
              end
            end

            -- Fallback: enable in common prose-heavy filetypes.
            local ft = vim.bo.filetype
            return vim.tbl_contains({ "markdown", "pandoc", "mail", "tex", "plaintex", "latex", "gitcommit" }, ft)
          end,
        },
      }
    end,
  },
}
