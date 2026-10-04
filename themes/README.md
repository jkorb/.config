# Shared One Dark theme

Edit [palette.json](palette.json) to change colors. The app configs are generated
from [templates](templates), with destinations listed in [targets.json](targets.json).

```sh
theme-build --diff  # Preview changes; exits 1 when there are changes.
theme-build        # Write the generated files.
bat cache --build  # Refresh bat after changing its theme.
theme-build --check
```

The shell adds `themes/scripts` to PATH on startup. Until the next shell starts,
use `~/.config/themes/scripts/theme-build`.

See the [theme guide](../doc/themes.md) for app coverage and reload instructions,
and the [design document](../doc/theme-design.md) for formats, ownership, tests,
and adding an app. Running apps may need a reload or restart after generation.
