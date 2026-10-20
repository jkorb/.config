-- New notes and files without a detected type are Markdown.
vim.api.nvim_create_autocmd({ "BufReadPost", "BufNewFile", "StdinReadPost", "BufEnter" }, {
  group = vim.api.nvim_create_augroup("markdown_fallback", { clear = true }),
  callback = function(event)
    vim.schedule(function()
      if vim.api.nvim_buf_is_valid(event.buf) then
        local options = vim.bo[event.buf]
        if options.buftype == "" and options.filetype == "" then
          vim.api.nvim_buf_call(event.buf, function()
            vim.cmd("setfiletype FALLBACK markdown")
          end)
        end
      end
    end)
  end,
})
