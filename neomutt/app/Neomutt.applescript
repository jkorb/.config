on run
    -- Normal launch: just open neomutt with default config, no account selection
    my launch_neomutt_default()
end run

on open location theURL
    -- mailto: handler: ask for account, then open neomutt with that account config
    my launch_neomutt_mailto(theURL)
end open location


-- Plain neomutt, no account selection
on launch_neomutt_default()
    -- Adjust PATH to wherever alacritty + neomutt live
    set baseCmd to "PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin; "
    set muttCmd to "neomutt"

    -- Wrap in alacritty
    set fullCmd to baseCmd & "alacritty -e " & muttCmd

    -- Run asynchronously so the AppleScript app can exit immediately
    set fullCmd to fullCmd & " > /dev/null 2>&1 &"

    do shell script fullCmd
end launch_neomutt_default


-- mailto: case with account selection
on launch_neomutt_mailto(theURL)
    if theURL is "" then
        -- Just in case, fall back to default behavior
        my launch_neomutt_default()
        return
    end if

    activate

    -- Ask which account to use (dropdown)
    set account to my choose_account()
    if account is "" then return -- user canceled

    set accountConfig to my account_config_path(account)
    if accountConfig is "" then return -- safety fallback

    -- Adjust PATH to wherever alacritty + neomutt live
    set baseCmd to "PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin; "

    -- Build neomutt command with account-specific config
    -- neomutt -e 'source /Users/you/.config/neomutt/accounts/gmail.conf' 'mailto:...'
    set muttCmd to "neomutt -e " & quoted form of ("source " & accountConfig)
    set muttCmd to muttCmd & " " & quoted form of theURL

    -- Wrap in alacritty
    set fullCmd to baseCmd & "alacritty -e " & muttCmd

    -- Run asynchronously so the AppleScript app doesn't hang
    set fullCmd to fullCmd & " > /dev/null 2>&1 &"

    do shell script fullCmd
end launch_neomutt_mailto


-- Dropdown account chooser (compilable version)
on choose_account()
    set accountList to {"gmail", "uu"}
    set defaultAccount to {"gmail"}

    try
        activate
        set chosen to choose from list accountList with title "Neomutt account" with prompt "Choose account for this message:" default items defaultAccount

        if chosen is false then
            -- user hit Cancel
            return ""
        end if

        return item 1 of chosen
    on error number -128
        -- ESC / canceled
        return ""
    end try
end choose_account


-- Map account name -> config path
on account_config_path(accountName)
    set homePath to POSIX path of (path to home folder)

    if accountName is "gmail" then
        return homePath & ".config/neomutt/accounts/gmail.conf"
    else if accountName is "uu" then
        return homePath & ".config/neomutt/accounts/uu.conf"
    else
        return ""
    end if
end account_config_path

