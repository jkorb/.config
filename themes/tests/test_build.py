"""Exercise generation in disposable checkouts; never write live configuration."""

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
BUILD = ROOT / "themes/scripts/theme-build"


class ThemeBuildTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        shutil.copytree(ROOT / "themes", self.root / "themes")
        (self.root / "khal").mkdir()
        (self.root / "khal/config").write_text(
            "# Keep my settings\n[view]\ntheme = dark\n"
            "# BEGIN GENERATED THEME: palette\n# END GENERATED THEME: palette\n"
            "# Keep this trailing comment\n"
        )

    def run_build(self, *args, code=0):
        result = subprocess.run([sys.executable, str(BUILD), "--root", str(self.root), *args], capture_output=True, text=True)
        self.assertEqual(result.returncode, code, result.stdout + result.stderr)
        return result

    def change_palette(self, change):
        path = self.root / "themes/palette.json"
        data = json.loads(path.read_text())
        change(data)
        path.write_text(json.dumps(data))

    def test_deterministic_build_and_check(self):
        self.run_build("--check", code=1)
        self.assertFalse((self.root / "wezterm").exists())
        self.run_build()
        target = self.root / "wezterm/theme.lua"
        before = target.stat().st_mtime_ns
        self.run_build()
        self.assertEqual(target.stat().st_mtime_ns, before)
        self.run_build("--check")
        target.write_text("manual drift\n")
        self.run_build("--check", code=1)
        self.assertIn("manual drift", self.run_build("--diff", code=1).stdout)
        self.assertEqual(target.read_text(), "manual drift\n")

    def test_palette_change_reaches_consumers_and_preserves_settings(self):
        self.change_palette(lambda p: p["colors"].update(blue="#123456"))
        self.run_build()
        for name in ("wezterm/theme.lua", "tmux/conf/colors.conf", "nvim/lua/config/theme.lua", "glow/onedark.json",
                     "btop/themes/shared.theme", "bat/themes/shared-onedark.tmTheme", "codex/themes/shared-onedark.tmTheme",
                     "zsh/theme.zsh", "khal/config"):
            self.assertIn("#123456", (self.root / name).read_text(), name)
        self.assertIn("rgba(18,52,86,1)", (self.root / "zathura/theme").read_text())
        self.assertIn("color4", (self.root / "newsboat/configs/colors").read_text())
        self.assertIn("color4", (self.root / "neomutt/core/colors").read_text())
        khal = (self.root / "khal/config").read_text()
        self.assertTrue(khal.startswith("# Keep my settings\n[view]\ntheme = dark\n"))
        self.assertTrue(khal.endswith("# Keep this trailing comment\n"))

    def test_invalid_color_writes_nothing(self):
        self.change_palette(lambda p: p["colors"].update(blue="blue"))
        self.run_build(code=2)
        self.assertFalse((self.root / "wezterm").exists())

    def test_unknown_token_in_last_template_writes_nothing(self):
        path = self.root / "themes/templates/zsh.zsh"
        path.write_text(path.read_text() + "@@typo@@\n")
        self.run_build(code=2)
        self.assertFalse((self.root / "wezterm").exists())

    def test_invalid_marker_writes_nothing(self):
        (self.root / "khal/config").write_text("# No generated section\n")
        self.run_build(code=2)
        self.assertFalse((self.root / "wezterm").exists())

    def test_symlink_is_not_replaced_or_followed(self):
        (self.root / "wezterm").mkdir()
        link = self.root / "wezterm/theme.lua"
        link.symlink_to(self.root / "khal/config")
        self.run_build(code=2)
        self.assertTrue(link.is_symlink())

    def test_path_traversal_is_rejected(self):
        path = self.root / "themes/targets.json"
        data = json.loads(path.read_text())
        data[-1]["target"] = "../escape"
        path.write_text(json.dumps(data))
        self.run_build(code=2)
        self.assertFalse((self.root / "wezterm").exists())

    def test_duplicate_palette_key_is_rejected(self):
        path = self.root / "themes/palette.json"
        path.write_text(path.read_text().replace('"version": 1', '"version": 1, "version": 1'))
        self.run_build(code=2)

    def test_templates_have_no_independent_rgb_palette(self):
        for path in (ROOT / "themes/templates").iterdir():
            self.assertNotRegex(path.read_text(), r"#[0-9a-fA-F]{6}\b", path.name)


if __name__ == "__main__":
    unittest.main()
