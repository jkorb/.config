// Route top-level web navigation to Firefox. Image/CSS fetches use the loader,
// so embedded images still render in Chawan. Anchors stay in the current mail.
const mailGotoURL = pager.gotoURL;
pager.gotoURL = function(resource, options) {
    const url = typeof resource === "string" || resource instanceof URL
        ? String(resource) : resource.url;
    if (/^https?:\/\//i.test(url) && !options?.save) {
        pager.extern('open -a Firefox "$NEOMUTT_LINK"', {
            env: {NEOMUTT_LINK: url},
            suspend: false
        });
        return null;
    }
    return mailGotoURL.call(this, resource, options);
};
