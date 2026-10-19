"""Small terminal dialog for invitation choices. No calendar or mail access."""

import json
from pathlib import Path
import sys

import urwid


def rounded(widget, **kwargs):
    return urwid.LineBox(widget, tlcorner="╭", trcorner="╮", blcorner="╰", brcorner="╯", **kwargs)


def palette():
    colors = json.loads((Path(__file__).resolve().parents[2] / "themes/palette.json").read_text())["colors"]

    def entry(name, foreground, background="surface", bold=False):
        return (name, "default", "default", "bold" if bold else "",
                colors[foreground] + (",bold" if bold else ""), colors[background])

    result = [entry("background", "foreground", "background"),
              entry("body", "foreground"), entry("title", "white", bold=True),
              entry("muted", "comment"), entry("accent", "cyan"), entry("border", "black")]
    for name, color in (("ACCEPTED", "green"), ("TENTATIVE", "yellow"), ("DECLINED", "red"),
                        ("cancel", "comment"), ("send", "blue"), ("close", "blue")):
        result += [entry(name, color, "surface_alt"), entry(name + "_focus", "background", color, True)]
    return result


class Centered(urwid.Padding):
    def __init__(self, widget, width):
        self.limit = width
        super().__init__(widget)

    def padding_values(self, size, focus):
        space = max(0, size[0] - self.limit)
        return space // 2, space - space // 2


class Choice(urwid.WidgetWrap):
    def selectable(self):
        return True

    def __init__(self, key, label, select):
        self.key, self.select = key, select
        label = urwid.Text(label, align="center", wrap="ellipsis")
        super().__init__(urwid.AttrMap(rounded(label), key, key + "_focus"))

    def keypress(self, size, key):
        if key in ("enter", " "):
            self.select(self.key)
        else:
            return key

    def mouse_event(self, size, event, button, col, row, focus):
        if event == "mouse press" and button == 1:
            self.select(self.key)
            return True
        return False


class Dialog(urwid.WidgetWrap):
    def __init__(self, title, header, options, select):
        self.select = select
        self.buttons = urwid.Columns([Choice(key, label, select) for key, label in options], dividechars=2)
        lines = header.splitlines()
        widgets = [urwid.Divider(), urwid.Text(("accent", "󰃭  " + title), align="center"), urwid.Divider()]
        meeting = any(key in ("ACCEPTED", "send") for key, _ in options)
        for index, line in enumerate(lines):
            style = "title" if index == 0 and meeting else "body"
            if line.startswith("Organizer:") or line.startswith("Where:"):
                style = "muted"
            elif line.startswith("Scope:"):
                style = "accent"
            widgets.append(urwid.Text((style, line), align="center"))
            if index == 0 and meeting:
                widgets.append(urwid.Divider())
        widgets += [urwid.Divider(), Centered(self.buttons,
                                              width=58 if len(options) == 3 else 46 if len(options) == 2 else 18),
                    urwid.Divider(),
                    urwid.Text(("muted", "←/→ · Tab  choose    Enter  confirm    Esc/q  close" if len(options) > 1
                                else "Enter · Esc/q  close"), align="center"), urwid.Divider()]
        # Scroll only when a long title/location or a short terminal needs it.
        content = urwid.ListBox(urwid.SimpleFocusListWalker(widgets))
        content.focus_position = len(widgets) - 4
        frame = rounded(urwid.AttrMap(urwid.Padding(content, left=2, right=2), "body"))
        frame = urwid.AttrMap(frame, "border")
        height = min(24, sum(widget.rows((80,)) for widget in widgets) + 2)
        panel = Centered(urwid.Filler(frame, height=height), width=86)
        super().__init__(urwid.AttrMap(panel, "background"))

    def keypress(self, size, key):
        if key in ("esc", "q", "ctrl g", "ctrl c"):
            self.select(None)
        elif key in ("right", "tab", "l", "ctrl n", "left", "shift tab", "h", "ctrl p"):
            step = -1 if key in ("left", "shift tab", "h", "ctrl p") else 1
            self.buttons.focus_position = (self.buttons.focus_position + step) % len(self.buttons.contents)
        else:
            return super().keypress(size, key)


def main():
    folder = Path(sys.argv[1])
    data = json.loads((folder / "dialog.json").read_text())

    def select(key):
        if key is not None:
            (folder / "answer").write_text(key)
        raise urwid.ExitMainLoop()

    loop = urwid.MainLoop(Dialog(**data, select=select), palette=palette())
    loop.screen.set_terminal_properties(colors=2**24)
    loop.run()


if __name__ == "__main__":
    main()
