local M = {}

local is_setup = false
local in_flight = false

local function notify(msg, level)
  vim.schedule(function()
    vim.notify(msg, level or vim.log.levels.INFO)
  end)
end

local function read_file(path)
  local fd = io.open(path, "r")
  if not fd then
    return nil, "Unable to read prompt file: " .. path
  end
  local content = fd:read("*a")
  fd:close()
  return content
end

local function line_len(bufnr, row)
  local line = vim.api.nvim_buf_get_lines(bufnr, row, row + 1, true)[1] or ""
  return #line
end

local function get_visual_selection(bufnr)
  local start_pos = vim.api.nvim_buf_get_mark(bufnr, "<")
  local end_pos = vim.api.nvim_buf_get_mark(bufnr, ">")
  if start_pos[1] == 0 or end_pos[1] == 0 then
    return nil, "No visual selection found"
  end

  local mode = vim.fn.visualmode()
  if mode == "\22" then
    return nil, "Blockwise visual mode is not supported"
  end

  local start_row, start_col = start_pos[1] - 1, start_pos[2]
  local end_row, end_col = end_pos[1] - 1, end_pos[2]
  if start_row > end_row or (start_row == end_row and start_col > end_col) then
    start_row, end_row = end_row, start_row
    start_col, end_col = end_col, start_col
  end

  if mode == "V" then
    local lines = vim.api.nvim_buf_get_lines(bufnr, start_row, end_row + 1, true)
    return {
      start_row = start_row,
      end_row = end_row,
      start_col = 0,
      end_col = 0,
      linewise = true,
      text = table.concat(lines, "\n"),
    }
  end

  local max_end_col = line_len(bufnr, end_row)
  if end_col > max_end_col then
    end_col = max_end_col
  end
  local lines = vim.api.nvim_buf_get_text(bufnr, start_row, start_col, end_row, end_col + 1, {})

  return {
    start_row = start_row,
    end_row = end_row,
    start_col = start_col,
    end_col = end_col,
    linewise = false,
    text = table.concat(lines, "\n"),
  }
end

local function extract_output_text(resp)
  if type(resp) ~= "table" then
    return nil
  end

  if type(resp.output_text) == "string" and resp.output_text ~= "" then
    return resp.output_text
  end

  if type(resp.output) ~= "table" then
    return nil
  end

  local parts = {}
  for _, item in ipairs(resp.output) do
    if type(item) == "table" and type(item.content) == "table" then
      for _, content in ipairs(item.content) do
        if type(content) == "table" then
          if type(content.text) == "string" and content.text ~= "" then
            table.insert(parts, content.text)
          elseif type(content.output_text) == "string" and content.output_text ~= "" then
            table.insert(parts, content.output_text)
          end
        end
      end
    end
  end

  if #parts == 0 then
    return nil
  end
  return table.concat(parts, "")
end

local function apply_translation(bufnr, selection, translated)
  local new_lines = vim.split(translated, "\n", { plain = true, trimempty = false })
  if selection.linewise then
    vim.api.nvim_buf_set_lines(bufnr, selection.start_row, selection.end_row + 1, true, new_lines)
    return
  end

  local end_col_exclusive = selection.end_col + 1
  local max_end_col = line_len(bufnr, selection.end_row)
  if end_col_exclusive > max_end_col then
    end_col_exclusive = max_end_col
  end
  vim.api.nvim_buf_set_text(
    bufnr,
    selection.start_row,
    selection.start_col,
    selection.end_row,
    end_col_exclusive,
    new_lines
  )
end

local function fail(msg)
  in_flight = false
  notify(msg, vim.log.levels.ERROR)
end

local function get_openai_token(cb)
  local entries = { "openai_key", "openai-token" }

  local function try_entry(idx)
    local entry = entries[idx]
    if not entry then
      cb(nil, "Failed to read OpenAI token from pass (tried: openai_key, openai-token)")
      return
    end

    vim.system({ "pass", "show", entry }, { text = true }, function(pass_result)
      if pass_result.code ~= 0 then
        try_entry(idx + 1)
        return
      end
      local token = vim.trim(pass_result.stdout or "")
      if token == "" then
        try_entry(idx + 1)
        return
      end
      cb(token, nil)
    end)
  end

  try_entry(1)
end

function M.translate_visual()
  if in_flight then
    notify("Translate is already running", vim.log.levels.WARN)
    return
  end

  local bufnr = vim.api.nvim_get_current_buf()
  local selection, sel_err = get_visual_selection(bufnr)
  if not selection then
    notify(sel_err, vim.log.levels.WARN)
    return
  end
  if selection.text == "" then
    notify("Selection is empty", vim.log.levels.WARN)
    return
  end

  local prompt_path = vim.fn.stdpath("config") .. "/prompts/openai_translate_dutch.txt"
  local prompt, prompt_err = read_file(prompt_path)
  if not prompt then
    notify(prompt_err, vim.log.levels.ERROR)
    return
  end

  local changedtick = vim.api.nvim_buf_get_changedtick(bufnr)
  in_flight = true

  get_openai_token(function(token, token_err)
    if token_err then
      fail(token_err)
      return
    end
    local body = vim.json.encode({
      model = "gpt-4o-mini",
      input = selection.text,
      instructions = prompt,
      temperature = 0.2,
      store = false,
    })

    vim.system({
      "curl",
      "-sS",
      "https://api.openai.com/v1/responses",
      "-H",
      "Content-Type: application/json",
      "-H",
      "Authorization: Bearer " .. token,
      "--data-binary",
      "@-",
    }, { text = true, stdin = body }, function(curl_result)
      if curl_result.code ~= 0 then
        local msg = "OpenAI request failed"
        if curl_result.stderr and vim.trim(curl_result.stderr) ~= "" then
          msg = msg .. ": " .. vim.trim(curl_result.stderr)
        end
        fail(msg)
        return
      end

      local ok, resp = pcall(vim.json.decode, curl_result.stdout or "")
      if not ok then
        fail("OpenAI response is not valid JSON")
        return
      end
      if type(resp.error) == "table" then
        local msg = type(resp.error.message) == "string" and resp.error.message or "Unknown OpenAI error"
        fail("OpenAI error: " .. msg)
        return
      end

      local translated = extract_output_text(resp)
      if not translated or translated == "" then
        fail("OpenAI returned empty output")
        return
      end

      vim.schedule(function()
        if not vim.api.nvim_buf_is_valid(bufnr) then
          in_flight = false
          return
        end
        if vim.api.nvim_buf_get_changedtick(bufnr) ~= changedtick then
          in_flight = false
          notify("Buffer changed while translating; retry selection", vim.log.levels.WARN)
          return
        end

        apply_translation(bufnr, selection, translated)
        in_flight = false
        notify("Translated selection to Dutch")
      end)
    end)
  end)
end

function M.setup()
  if is_setup then
    return
  end
  is_setup = true
  vim.api.nvim_create_user_command("Translate", function()
    M.translate_visual()
  end, { desc = "Translate visual selection to Dutch", range = true })
end

return M
