on run
    -- Just launch/focus Neovim.app, no files
    my launch_neovim()
end run

on open theItems
    my launch_neovim()
    my wait_for_server()
    if (count of theItems) > 0 then
        my nvr_open_items(theItems)
    end if
end open

on launch_neovim()
    -- Always run `open -a Neovim`:
    --  - starts Neovim.app if not running
    --  - focuses it if already running
    set baseCmd to "PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin; "
    do shell script baseCmd & "/usr/bin/open -a Neovim"
end launch_neovim

on wait_for_server()
    set baseCmd to "PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin; "
    set homePath to POSIX path of (path to home folder)
    set nvimServer to homePath & ".cache/nvim/nvim-neovim-app.sock"

    -- Poll up to ~2 seconds (20 * 0.1s) for the server to come up.
    repeat with i from 1 to 20
        try
            do shell script baseCmd & "/opt/homebrew/bin/nvr -s --servername " & quoted form of nvimServer & " --nostart --remote-expr 1"
            exit repeat -- success: server is responding
        on error
            delay 0.1
        end try
    end repeat
end wait_for_server

on nvr_open_items(theItems)
    set fileArgs to ""
    repeat with anItem in theItems
        set filePath to POSIX path of anItem
        set fileArgs to fileArgs & " " & quoted form of filePath
    end repeat

    if fileArgs is "" then return

    set baseCmd to "PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin; "
    set homePath to POSIX path of (path to home folder)
    set nvimServer to homePath & ".cache/nvim/nvim-neovim-app.sock"

    -- Use --nostart so nvr NEVER spawns its own hidden nvim
    set sendCmd to "/opt/homebrew/bin/nvr --servername " & quoted form of nvimServer & " --nostart" & fileArgs
    do shell script baseCmd & sendCmd
end nvr_open_items

