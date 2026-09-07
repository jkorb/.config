return {
  {
    "iurimateus/luasnip-latex-snippets.nvim",
    -- vimtex isn't required if using treesitter
    -- dependencies = { "L3MON4D3/LuaSnip", "lervag/vimtex" },
    opts = {
      use_treesitter = true,
      allow_on_markdown = true,
    },
    config = function(_, opts)
      local ls = require("luasnip")
      local latex_snippets = require("luasnip-latex-snippets")

      ls.filetype_extend("latex", { "tex" })
      ls.filetype_extend("plaintex", { "tex" })

      local function add_environment_snippets()
        local s = ls.snippet
        local t = ls.text_node
        local i = ls.insert_node

        local function env(trigger, name, item)
          return s({ trig = trigger, name = name .. " environment" }, {
            t({ "\\begin{" .. name .. "}", "\t" }),
            item and t("\\item ") or t(""),
            i(1),
            t({ "", "\\end{" .. name .. "}" }),
            i(0),
          })
        end

        local function titled_env(trigger, name)
          return s({ trig = trigger, name = name .. " environment with title", priority = 1100 }, {
            t("\\begin{" .. name .. "}["),
            i(1, "title"),
            t({ "]", "\t" }),
            i(2),
            t({ "", "\\end{" .. name .. "}" }),
            i(0),
          })
        end

        local function labelled_env(trigger, name, label_prefix, title)
          local begin = "\\begin{" .. name .. "}"
          if title then
            begin = begin .. "["
          end

          return s({
            trig = trigger,
            name = name .. " environment with label",
            priority = title and 1200 or 1100,
          }, {
            t(begin),
            title and i(1, "title") or t(""),
            title and t("]") or t(""),
            t("\\label{" .. label_prefix .. ":"),
            i(title and 2 or 1, "label"),
            t({ "}", "\t" }),
            i(title and 3 or 2),
            t({ "", "\\end{" .. name .. "}" }),
            i(0),
          })
        end

        ls.add_snippets("tex", {
          env("\\begin{itemize}", "itemize", true),
          env("\\begin{enumerate}", "enumerate", true),
          env("\\begin{description}", "description"),
          env("\\begin{align}", "align"),
          env("\\begin{proof}", "proof"),
          labelled_env("thmTL", "theorem", "thm", true),
          labelled_env("thmL", "theorem", "thm"),
          titled_env("thmT", "theorem"),
          env("thm", "theorem"),
          labelled_env("lemTL", "lemma", "lem", true),
          labelled_env("lemL", "lemma", "lem"),
          titled_env("lemT", "lemma"),
          env("lem", "lemma"),
          labelled_env("propTL", "proposition", "prop", true),
          labelled_env("propL", "proposition", "prop"),
          titled_env("propT", "proposition"),
          env("prop", "proposition"),
          labelled_env("corTL", "corollary", "cor", true),
          labelled_env("corL", "corollary", "cor"),
          titled_env("corT", "corollary"),
          env("cor", "corollary"),
          labelled_env("defTL", "definition", "def", true),
          labelled_env("defL", "definition", "def"),
          titled_env("defT", "definition"),
          env("def", "definition"),
          labelled_env("exTL", "example", "ex", true),
          labelled_env("exL", "example", "ex"),
          titled_env("exT", "example"),
          env("ex", "example"),
          env("prf", "proof"),
        })
      end

      local tex_loaded = false
      vim.api.nvim_create_autocmd("FileType", {
        pattern = { "tex", "latex", "plaintex" },
        group = vim.api.nvim_create_augroup("custom_luasnip_latex", { clear = true }),
        callback = function()
          if tex_loaded then
            return
          end
          tex_loaded = true

          local utils = require("luasnip-latex-snippets.util.utils")
          local is_math = utils.with_opts(utils.is_math, opts.use_treesitter)
          local not_math = utils.with_opts(utils.not_math, opts.use_treesitter)

          latex_snippets.setup_tex(is_math, not_math)
          add_environment_snippets()
        end,
      })

      if opts.allow_on_markdown then
        vim.api.nvim_create_autocmd("FileType", {
          pattern = { "markdown", "quarto" },
          group = vim.api.nvim_create_augroup("custom_luasnip_latex_markdown", { clear = true }),
          once = true,
          callback = function()
            latex_snippets.setup_markdown()
          end,
        })
      end
    end,
  },
  {
    "L3MON4D3/LuaSnip",
    opts = {
      enable_autosnippets = true,
    },
  },
  -- {
  --   "lervag/vimtex",
  --   enabled = true, -- lazy-loading will disable inverse search
  --   -- config = function()
  --   --   vim.api.nvim_create_autocmd({ "FileType" }, {
  --   --     group = vim.api.nvim_create_augroup("lazyvim_vimtex_conceal", { clear = true }),
  --   --     pattern = { "bib", "tex" },
  --   --     callback = function()
  --   --       vim.wo.conceallevel = 2
  --   --     end,
  --   --   })
  --   --   vim.g.vimtex_syntax_conceal_disable = 1
  --   --   vim.g.vimtex_mappings_disable = { ["n"] = { "K" } } -- disable `K` as it conflicts with LSP hover
  --   --   vim.g.vimtex_quickfix_method = vim.fn.executable("pplatex") == 1 and "pplatex" or "latexlog"
  --   -- end,
  -- },
}
