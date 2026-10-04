-- Called by update in a fresh headless Neovim for each step.
local summary = {}
local function changed(name, before, after)
  if before ~= after then
    summary[#summary + 1] = ("  %s: %s → %s"):format(name, before or "not installed", after or "unknown")
  end
end

local function revisions(root)
  local result = {}
  for _, file in ipairs(vim.fn.glob(root .. "/*.revision", false, true)) do
    result[vim.fn.fnamemodify(file, ":t:r")] = table.concat(vim.fn.readfile(file), "")
  end
  return result
end

local steps = {}
function steps.lazy()
  local plugins = require("lazy.core.config").plugins
  local function commits()
    local result = {}
    for name, plugin in pairs(plugins) do
      if plugin.url and plugin._.installed then
        local git = vim.system({ "git", "-C", plugin.dir, "rev-parse", "--short", "HEAD" }):wait()
        assert(git.code == 0, git.stderr)
        result[name] = vim.trim(git.stdout)
      end
    end
    return result
  end
  local before = commits()
  require("lazy").update({ wait = true, show = false })
  local failed = {}
  for name, plugin in pairs(require("lazy.core.config").plugins) do
    for _, task in ipairs(plugin._.tasks or {}) do
      if task:has_errors() then
        failed[#failed + 1] = name .. ": " .. task:output()
      end
    end
  end
  for name, commit in pairs(commits()) do
    changed(name, before[name], commit)
  end
  assert(#failed == 0, table.concat(failed, "\n"))
end

function steps.mason()
  local registry = require("mason-registry")
  local done, success = false, false
  registry.update(function(ok)
    success, done = ok, true
  end)
  assert(vim.wait(300000, function() return done end, 50), "Mason registry update timed out")
  assert(success, "Mason registry update failed; see :MasonLog")
  local failed = {}
  for _, pkg in ipairs(registry.get_installed_packages()) do
    local before, latest = pkg:get_installed_version(), pkg:get_latest_version()
    if before ~= latest then
      print("Updating " .. pkg.name)
      local err
      done, success = false, false
      pkg:install({ version = latest }, function(ok, result)
        success, done, err = ok, true, result
      end)
      assert(vim.wait(600000, function() return done end, 50), "Mason install timed out: " .. pkg.name)
      if success then
        changed(pkg.name, before, pkg:get_installed_version())
      else
        failed[#failed + 1] = pkg.name .. ": " .. vim.inspect(err)
      end
    end
  end
  assert(#failed == 0, table.concat(failed, "\n"))
end

function steps.treesitter()
  local config = require("nvim-treesitter.config")
  local root = config.get_install_dir("parser-info")
  local before = revisions(root)
  local ok = require("nvim-treesitter.install").update(nil, { summary = true }):wait(600000)
  for name, revision in pairs(revisions(root)) do
    changed(name, before[name], revision)
  end
  assert(ok, "Treesitter parser update failed; see :TSLog")
end

local ok, err = xpcall(function()
  local step = assert(steps[vim.env.CONFIG_UPDATE_STEP], "Unknown update step")
  step()
end, debug.traceback)
table.sort(summary)
vim.fn.writefile(summary, assert(vim.env.CONFIG_UPDATE_SUMMARY))
if not ok then
  io.stderr:write(tostring(err), "\n")
  vim.cmd("cquit 1")
else
  vim.cmd("qa!")
end
