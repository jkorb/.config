local wezterm = require("wezterm")

local config = {}

-- Native colors generated from themes/palette.json.
local theme_path = wezterm.config_dir .. "/theme.lua"
wezterm.add_to_config_reload_watch_list(theme_path)
config.colors = dofile(theme_path)

config.native_macos_fullscreen_mode = true
config.adjust_window_size_when_changing_font_size = false
config.window_background_opacity = 0.9
config.macos_window_background_blur = 10
config.send_composed_key_when_right_alt_is_pressed = true
config.send_composed_key_when_left_alt_is_pressed = true

-- FONT
config.font = wezterm.font({
	family = "ComicShannsMono Nerd Font",
})
config.font_size = 20.0

-- WINDOW
config.window_padding = {
	left = 5,
	right = 5,
	top = 80,
	bottom = 30,
}

config.window_decorations = "INTEGRATED_BUTTONS | RESIZE"

config.hide_tab_bar_if_only_one_tab = true

config.keys = {
	{
		key = "g",
		mods = "CTRL",
		action = wezterm.action_callback(function(window, pane)
			local process = pane:get_foreground_process_info()
			-- Direct nnn sessions; tmux handles its own panes. Leave child apps alone.
			if process and process.name == "nnn" and next(process.children) == nil then
				window:perform_action(wezterm.action.SendString("\x1bg"), pane)
			else
				window:perform_action(wezterm.action.SendString("\x07"), pane)
			end
		end),
	},
	{
		key = "/",
		mods = "CTRL",
		action = wezterm.action.SendString("\x1F"),
	},
	{
		key = ";",
		mods = "CTRL",
		action = wezterm.action.SendString("\x1C"),
	},
	{
		key = ",",
		mods = "CTRL",
		action = wezterm.action.SendString("\x1E"),
	},
	{
		key = ".",
		mods = "CTRL",
		action = wezterm.action.SendString("\x1A"),
	},

	{
		key = "f",
		mods = "CMD|CTRL",
		action = wezterm.action.ToggleFullScreen,
	},

	-- Ctrl + Shift + C -> Copy
	{
		key = "C",
		mods = "CTRL|SHIFT",
		action = wezterm.action.CopyTo("Clipboard"),
	},

	-- Ctrl + Shift + V -> Paste
	{
		key = "V",
		mods = "CTRL|SHIFT",
		action = wezterm.action.PasteFrom("Clipboard"),
	},

	-- Ctrl + 0 -> ResetFontSize
	{
		key = "0",
		mods = "CTRL",
		action = wezterm.action.ResetFontSize,
	},

	-- Ctrl + = -> IncreaseFontSize
	{
		key = "=",
		mods = "CTRL",
		action = wezterm.action.IncreaseFontSize,
	},

	-- Ctrl + - -> DecreaseFontSize
	{
		key = "-",
		mods = "CTRL",
		action = wezterm.action.DecreaseFontSize,
	},
}

return config
