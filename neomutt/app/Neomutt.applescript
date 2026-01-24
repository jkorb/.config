on run
    set runnerPath to POSIX path of (path to resource "NeoMuttRunner.app")
    tell application runnerPath to activate
end run

on open location theURL
    set account to my choose_account()
    if account is "" then return

    set accountConfig to my account_config_path(account)
    if accountConfig is "" then return

    set runnerPath to POSIX path of (path to resource "NeoMuttRunner.app")

    do shell script "open -a " & quoted form of runnerPath & " --args -e " & quoted form of ("source " & accountConfig) & " " & quoted form of theURL
end open location

on choose_account()
    set accountList to {"gmail", "uu"}
    set defaultAccount to {"gmail"}

    try
        activate
        set chosen to choose from list accountList with title "Neomutt account" with prompt "Choose account for this message:" default items defaultAccount

        if chosen is false then
            return ""
        end if

        return item 1 of chosen
    on error number -128
        return ""
    end try
end choose_account

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
