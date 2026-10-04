"""Exercise the installed Pandoc parser, math filter, and file-link picker."""

import importlib.machinery
import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
import textwrap
import unittest

ROOT = Path(__file__).resolve().parents[1]
loader = importlib.machinery.SourceFileLoader("md_links", str(ROOT / "scripts/md-links"))
spec = importlib.util.spec_from_loader(loader.name, loader)
links = importlib.util.module_from_spec(spec)
loader.exec_module(links)
hint_loader = importlib.machinery.SourceFileLoader("md_hints", str(ROOT / "scripts/md-hints"))
hint_spec = importlib.util.spec_from_loader(hint_loader.name, hint_loader)
hints = importlib.util.module_from_spec(hint_spec)
hint_loader.exec_module(hints)


def render(source, width=80):
    result = subprocess.run(
        ["pandoc", "--quiet", "-f", "gfm+tex_math_dollars+wikilinks_title_after_pipe", "-t", "gfm", "--wrap=none",
         "--lua-filter=" + str(ROOT / "wikilinks.lua"),
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
        self.assertIn("Γ ⊢ A    Γ ⊢ B\n────────────── ∧I\n  Γ ⊢ A ∧ B", textwrap.dedent(text))

    def test_nested_rules_and_axioms(self):
        text = render(r"$$\infer[\to E]{B}{\infer[Ax]{A\to B}{} & A}$$")
        self.assertEqual(text.count("Ax"), 1)
        self.assertIn("→ E", text)
        self.assertTrue(text.rstrip().endswith("B"))
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


class GridTests(unittest.TestCase):
    def display(self, tex, width=80):
        return textwrap.dedent(render("$$" + tex + "$$", width)).rstrip()

    def test_aligned_relations_and_empty_continuation(self):
        text = self.display(r"\begin{aligned}A&=B\\C\land D&=E\\&=F\end{aligned}")
        rows = text.splitlines()
        self.assertEqual({row.index("=") for row in rows}, {6})
        self.assertEqual(rows[-1].strip(), "= F")
        self.assertIn("C ∧ D", text)

    def test_multiple_alignment_pairs_and_missing_cells(self):
        text = self.display(r"\begin{aligned}A&=B & C&=D\\E&=F\end{aligned}")
        self.assertEqual(text, "A = B    C = D\nE = F")

    def test_array_column_alignment_and_rules(self):
        text = self.display(r"\begin{array}{r|lc}\hline A&B&C\\\hline "
                            r"AAAA&BB&CCC\\\hline\end{array}")
        rows = text.splitlines()
        self.assertEqual(rows[1], "   A │ B    C")
        self.assertEqual(rows[3], "AAAA │ BB  CCC")
        self.assertEqual(rows[0], "─" * len(rows[3]))
        self.assertEqual(rows[0], rows[2])
        self.assertEqual(rows[0], rows[-1])

    def test_matrices_and_wrapped_array(self):
        text = self.display(r"\begin{bmatrix}1&0\\0&1\end{bmatrix}")
        self.assertEqual(text, "⎡1  0⎤\n⎣0  1⎦")
        self.assertEqual(self.display(r"\left[\begin{array}{cc}1&0\\0&1\end{array}\right]"), text)
        self.assertEqual(self.display(r"\begin{vmatrix}1&0\\0&1\end{vmatrix}"), "|1  0|\n|0  1|")

    def test_cases_and_gathered(self):
        text = self.display(r"\begin{cases}1&\text{if }x>0\\0&\text{otherwise}\end{cases}")
        self.assertEqual(text, "⎧1  if x > 0\n⎩0  otherwise")
        self.assertEqual(self.display(r"\begin{gathered}A\\B\to C\end{gathered}"), "  A\nB → C")

    def test_escaped_ampersand_and_grouped_content(self):
        text = self.display(r"\begin{array}{ll}\text{A \& B}&C\\D&E\end{array}")
        self.assertIn("A &B  C", text)
        self.assertNotIn(r"\begin", text)

    def test_unsupported_or_malformed_grids_remain_complete(self):
        cases = [r"\begin{array}{p{2cm}}A\end{array}",
                 r"\begin{array}{c}A&B\end{array}",
                 r"\begin{array}{c}A\end{matrix}",
                 r"\begin{aligned}A&\unknown{B}\end{aligned}",
                 r"\begin{matrix}\begin{matrix}A\end{matrix}\end{matrix}",
                 r"\begin{aligned}A&B\\[1ex]C&D\end{aligned}",
                 r"\begin{matrix}\text{日本語}\end{matrix}"]
        for tex in cases:
            with self.subTest(tex=tex):
                self.assertIn(tex, self.display(tex))

    def test_wide_grid_remains_source(self):
        tex = r"\begin{array}{ccc}AAAA&BBBB&CCCC\end{array}"
        self.assertEqual(self.display(tex, width=20), tex)
        self.assertNotIn(tex, self.display(tex))


class LinkTests(unittest.TestCase):
    def test_wiki_links_in_picker_and_rendered_hints(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            (folder / 'paper.md').write_text('# Paper\n')
            (folder / 'other file.md').write_text('# Other\n')
            (folder / 'exact').write_text('Extensionless file\n')
            (folder / 'exact.md').write_text('# Not the target\n')
            source = folder / 'source.md'
            source.write_text('[[ paper ]] [[other file.md|An alias]] [[paper#Heading]] '
                              '[[exact]] [[missing]] [[https://example.org|Web]] [[#here]]\n\n'
                              '`[[inline.md]]`\n\n```\n[[code.md]]\n```\n')
            before = source.read_bytes()
            found = links.local_links(source)
            expected = [(folder / name).resolve() for name in
                        ('paper.md', 'other file.md', 'paper.md', 'exact', 'missing')]
            self.assertEqual([path for _, path in found], expected)
            self.assertEqual(found[1][0], 'An alias')
            rendered = subprocess.run(
                ['pandoc', '-f', 'gfm+tex_math_dollars+wikilinks_title_after_pipe',
                 '-t', 'gfm', '--wrap=none', '--lua-filter=' + str(ROOT/'wikilinks.lua'), str(source)],
                capture_output=True, text=True, check=True,
            ).stdout
            self.assertNotIn('<a ', rendered)
            self.assertIn('[paper](paper.md)', rendered)
            self.assertIn('paper.md#Heading', rendered)
            self.assertIn('`[[inline.md]]`', rendered)
            self.assertIn('[[code.md]]', rendered)
            ansi = subprocess.run(
                ['glow', '--width', '100', '--style', str(ROOT/'onedark.json'), '-'],
                input=rendered, capture_output=True, text=True, check=True,
                env=dict(os.environ, GLOW_PAGER='false', GLOW_TUI='false'),
            ).stdout
            _, visible = hints.viewport(ansi, source, 100, 50)
            self.assertEqual({value[0] for value in visible.values()}, set(expected))
            self.assertEqual(source.read_bytes(), before)

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


class HintTests(unittest.TestCase):
    source = Path('/tmp/reader/source.md')

    @staticmethod
    def link(label, target, ending='\x07'):
        return f'\x1b]8;id=123;{target}{ending}{label}\x1b]8;;{ending}'

    def test_targets_not_labels_determine_destination(self):
        text = '  ' + self.link('Same', 'one%20file.md') + ' and ' + self.link('Same', 'two.md')
        lines, found = hints.viewport(text, self.source, 80, 20)
        self.assertEqual(lines[0], '  Same and Same\x1b[0m')
        self.assertEqual(found['a'], (Path('/tmp/reader/one file.md').resolve(), 0, 1))
        self.assertEqual(found['s'][0], Path('/tmp/reader/two.md').resolve())

    def test_glow_colors_repeated_targets_and_visible_rows(self):
        text = '\x1b[38;2;74;165;240m' + self.link('Label', 'file.md')
        text += ' ' + self.link('/file.md', 'file.md', '\x1b\\')
        text += '\n' + self.link('Below screen', 'hidden.md')
        lines, found = hints.viewport(text, self.source, 80, 1)
        self.assertEqual(list(found), ['a'])
        self.assertIn('\x1b[38;2;74;165;240m', lines[0])

    def test_remote_anchor_and_control_sequences_are_omitted(self):
        text = ''.join(self.link('Skip', url) for url in
                       ('https://example.org', '#here', 'file://server/path', 'javascript:alert(1)'))
        text += '\x1b]52;c;payload\x07\x1b[2J'
        lines, found = hints.viewport(text, self.source, 80, 20)
        self.assertFalse(found)
        self.assertNotIn('payload', lines[0])
        self.assertNotIn('\x1b[2J', lines[0])

    def test_wide_and_combining_characters_and_clipping(self):
        text = '界e\u0301 ' + self.link('Open', 'file.md')
        _, found = hints.viewport(text, self.source, 80, 20)
        self.assertEqual(found['a'][2], 3)
        _, found = hints.viewport(text, self.source, 3, 20)
        self.assertFalse(found)

    def test_many_links_get_unambiguous_equal_length_hints(self):
        text = '\n'.join(self.link('File', f'{i}.md') for i in range(27))
        _, found = hints.viewport(text, self.source, 80, 40)
        self.assertEqual(len(found), 27)
        self.assertEqual({len(code) for code in found}, {2})

    def test_installed_glow_wraps_links_with_targets_intact(self):
        result = subprocess.run(
            ['glow', '--width', '40', '--style', str(ROOT / 'onedark.json'), '-'],
            input='[' + 'Long label ' * 8 + '](other%20file.md)\n',
            text=True, capture_output=True, check=True,
            env=dict(os.environ, GLOW_PAGER='false', GLOW_TUI='false'),
        )
        _, found = hints.viewport(result.stdout, self.source, 40, 20)
        self.assertEqual(len(found), 1)
        self.assertEqual(found['a'][0], Path('/tmp/reader/other file.md').resolve())
        # Scrolling past the first line still leaves a selectable continuation.
        _, continued = hints.viewport('\n'.join(result.stdout.splitlines()[2:]),
                                      self.source, 40, 20)
        self.assertEqual(continued['a'][0], found['a'][0])


if __name__ == "__main__":
    unittest.main()
