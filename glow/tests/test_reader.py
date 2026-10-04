"""Exercise the installed Pandoc parser, math filter, and file-link picker."""

import importlib.machinery
import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
loader = importlib.machinery.SourceFileLoader("md_links", str(ROOT / "scripts/md-links"))
spec = importlib.util.spec_from_loader(loader.name, loader)
links = importlib.util.module_from_spec(spec)
loader.exec_module(links)


def render(source, width=80):
    result = subprocess.run(
        ["pandoc", "--quiet", "-f", "gfm+tex_math_dollars", "-t", "gfm", "--wrap=none",
         "--lua-filter=" + str(ROOT / "terminal-math.lua")],
        input=source, text=True, capture_output=True,
        env=dict(os.environ, MD_READ_WIDTH=str(width)), check=True,
    )
    return result.stdout


class MathTests(unittest.TestCase):
    def test_logic_and_scripts(self):
        text = render(r"$\Gamma_i \vdash A \to B$ and $\forall x\in\mathbb{N}\; P(x)$ "
                      r"and $\neg A\land B\lor C$ and $A^2 \models B$.")
        for symbol in ("Γᵢ", "⊢", "→", "∀", "∈", "ℕ", "¬", "∧", "∨", "A²", "⊨"):
            self.assertIn(symbol, text)

    def test_branching_proof(self):
        text = render(r"$$\infer[\land I]{\Gamma\vdash A\land B}"
                      r"{\Gamma\vdash A & \Gamma\vdash B}$$")
        self.assertIn("Γ ⊢ A    Γ ⊢ B\n────────────── ∧I\n  Γ ⊢ A ∧ B", text)

    def test_nested_rules_and_axioms(self):
        text = render(r"$$\infer[\to E]{B}{\infer[Ax]{A\to B}{} & A}$$")
        self.assertEqual(text.count("Ax"), 1)
        self.assertIn("→ E", text)
        self.assertIn("B\n```", text)
        self.assertNotIn(r"\infer", text)

    def test_scripts_in_proofs(self):
        text = render(r"$$\infer{\Gamma_i\vdash A^2}{A}$$")
        self.assertIn("Γᵢ ⊢ A²", text)
        self.assertIn("───────", text)

    def test_fallback_preserves_complete_tex(self):
        cases = [r"\unknown{A}", r"\infer*{A}{B}", r"\infer{A}",
                 r"\infer{A}{\unknown{B}}", r"\infer{A}{B}+C",
                 r"\infer{A}{\text{日本語}}"]
        for tex in cases:
            with self.subTest(tex=tex):
                self.assertIn(tex, render("$$" + tex + "$$"))

    def test_wide_proof_falls_back_in_narrow_pane(self):
        tex = r"\infer{A\land B\land C\land D}{A & B & C & D}"
        self.assertIn(tex, render("$$" + tex + "$$", width=20))
        self.assertNotIn(tex, render("$$" + tex + "$$", width=80))

    def test_markdown_code_links_and_math_boundaries(self):
        source = '# Heading\n\n[Other](other.md)\n\n```latex\n$\\Gamma$\n```\n\n`$A$`\n\nPrice: $5.\n'
        text = render(source)
        self.assertIn('[Other](other.md)', text)
        self.assertIn('$\\Gamma$', text)
        self.assertIn('`$A$`', text)
        self.assertIn(r'Price: \$5.', text)  # Markdown escaping, not a math node.


class LinkTests(unittest.TestCase):
    def test_relative_reference_encoded_absolute_and_remote_links(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            source = folder / "source.md"
            source.write_text('[Space](other%20file.md#section)\n\n[Ref][r]\n\n'
                              '[r]: ../parent.md\n\n[Web](https://example.org)\n\n'
                              '[Here](#heading)\n\n[Remote](file://server/path)\n\n'
                              f'[Absolute](file://{temp}/absolute.md)\n\n'
                              '`[Code](not-a-link.md)`\n')
            before = source.read_bytes()
            found = links.local_links(source)
            self.assertEqual([p for _, p in found], [
                (folder / 'other file.md').resolve(),
                (folder / '../parent.md').resolve(),
                (folder / 'absolute.md').resolve(),
            ])
            self.assertEqual(source.read_bytes(), before)

    def test_picker_uses_argument_vector_for_special_filenames(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            target = folder / 'a $(never-execute).md'
            target.write_text('# Linked file\n')
            source = folder / 'source.md'
            source.write_text('[Open](<a%20%24%28never-execute%29.md>)\n')
            bin_dir = folder / 'bin'
            bin_dir.mkdir()
            fzf = bin_dir / 'fzf'
            fzf.write_text('#!/usr/bin/env python3\nimport sys\nsys.stdout.write(sys.stdin.read().split("\\0")[0]+"\\0")\n')
            fzf.chmod(0o755)
            opener = folder / 'nnn/scripts/nnn-open'
            opener.parent.mkdir(parents=True)
            opener.write_text('#!/usr/bin/env python3\nimport os,sys\nopen(os.environ["LINK_LOG"],"w").write(sys.argv[1])\n')
            opener.chmod(0o755)
            log = folder / 'opened'
            env = dict(os.environ, PATH=str(bin_dir)+os.pathsep+os.environ['PATH'],
                       XDG_CONFIG_HOME=str(folder), LINK_LOG=str(log))
            subprocess.run(['python3', str(ROOT/'scripts/md-links'), str(source)], env=env, check=True)
            self.assertEqual(log.read_text(), str(target.resolve()))


if __name__ == "__main__":
    unittest.main()
