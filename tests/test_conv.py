import unittest

from cvalchemix.cli.conv import _normalize_tex_for_tectonic


class ConvNormalizationTests(unittest.TestCase):
    def test_removes_pdftex_unicode_directives(self) -> None:
        tex = "\n".join(
            [
                r"\documentclass{article}",
                r"\input{glyphtounicode}",
                r"\pdfgentounicode=1",
                r"\input glyphtounicode % searchable PDF for pdfLaTeX",
                r"\begin{document}",
                "Hi",
                r"\end{document}",
            ]
        )

        normalized, removed_count, fixed_spacing_count = _normalize_tex_for_tectonic(
            tex
        )

        self.assertEqual(removed_count, 3)
        self.assertEqual(fixed_spacing_count, 0)
        self.assertNotIn("glyphtounicode", normalized)
        self.assertNotIn(r"\pdfgentounicode", normalized)
        self.assertIn(r"\documentclass{article}", normalized)
        self.assertIn(r"\begin{document}", normalized)

    def test_keeps_non_directive_content(self) -> None:
        tex = "\n".join(
            [
                r"\documentclass{article}",
                r"\newcommand{\pdfgentounicodeNote}{keep this macro}",
                r"\begin{document}",
                r"Discuss \input{glyphtounicode} as plain sample text.",
                r"Already valid\\[2pt]",
                r"\end{document}",
            ]
        )

        normalized, removed_count, fixed_spacing_count = _normalize_tex_for_tectonic(
            tex
        )

        self.assertEqual(removed_count, 0)
        self.assertEqual(fixed_spacing_count, 0)
        self.assertEqual(normalized, tex)

    def test_adds_pt_unit_to_bare_linebreak_spacing(self) -> None:
        tex = "\n".join(
            [
                r"\documentclass{article}",
                r"\begin{document}",
                r"One \\ [2]",
                r"Two\\[1.5]",
                r"\end{document}",
            ]
        )

        normalized, removed_count, fixed_spacing_count = _normalize_tex_for_tectonic(
            tex
        )

        self.assertEqual(removed_count, 0)
        self.assertEqual(fixed_spacing_count, 2)
        self.assertIn(r"One \\[2pt]", normalized)
        self.assertIn(r"Two\\[1.5pt]", normalized)


if __name__ == "__main__":
    unittest.main()
