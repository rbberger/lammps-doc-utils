import io
import tempfile
import unittest
import txt2rst

class TestBasicFormatting(unittest.TestCase):
    def setUp(self):
        self.txt2rst = txt2rst.Txt2Rst()

    def test_empty_string(self):
        self.assertEqual(self.txt2rst.convert(""), "")

    def test_single_paragraph(self):
        self.assertEqual("Hello World!\n\n", self.txt2rst.convert("Hello World!\n"))

    def test_two_paragraphs(self):
        s = self.txt2rst.convert("Hello World!\n\nBye World!\n")
        self.assertEqual("Hello World!\n\n"
                         "Bye World!\n\n", s)

    def test_line_concat(self):
        s = self.txt2rst.convert("Hello World!\\\nBye World!\n")
        self.assertEqual(s, "Hello World!Bye World!\n\n")

    def test_html_pass_through(self):
        s = self.txt2rst.convert("<div>Raw HTML</div>\n")
        self.assertEqual(s, ".. raw:: html\n\n"
                            "   <div>Raw HTML</div>\n\n")

class TestMarkup(unittest.TestCase):
    def setUp(self):
        self.markup = txt2rst.RSTMarkup()
        self.txt2rst = txt2rst.Txt2Rst()

    def test_bold(self):
        self.assertEqual("**bold**", self.markup.convert("[bold]"))

    def test_italic(self):
        self.assertEqual("*italic*", self.markup.convert("{italic}"))

    def test_escape_markup(self):
        s = self.markup.convert("[bold] = \\[bold\\]\n"
                                "{italic} = \\{italic\\}\n")
        self.assertEqual("**bold** = [bold]\n"
                         "*italic* = {italic}\n", s)

    def test_link_markup(self):
        self.assertEqual("`Text <link>`_", self.markup.convert('"Text"_link'))

    def test_multiline_link_markup(self):
        s = self.txt2rst.convert('"Te\n'
                                  'xt"_link\n')
        self.assertEqual("`Text <link>`_\n\n", s)

    def test_ignore_punctuation_in_link(self):
        self.assertEqual("`Text <link>`_.", self.markup.convert('"Text"_link.'))
        self.assertEqual("`Text <link>`_,", self.markup.convert('"Text"_link,'))
        self.assertEqual("`Text <link>`_;", self.markup.convert('"Text"_link;'))
        self.assertEqual("`Text <link>`_:", self.markup.convert('"Text"_link:'))
        self.assertEqual("`Text <link>`_?", self.markup.convert('"Text"_link?'))
        self.assertEqual("`Text <link>`_!", self.markup.convert('"Text"_link!'))
        self.assertEqual("`Text <link>`_(", self.markup.convert('"Text"_link('))
        self.assertEqual("`Text <link>`_)", self.markup.convert('"Text"_link)'))

class TestFormatting(unittest.TestCase):
    def setUp(self):
        self.txt2rst = txt2rst.Txt2Rst()

    def test_paragraph_formatting(self):
        s = self.txt2rst.convert("Hello :p\n")
        self.assertEqual("Hello\n\n", s)

    def test_two_paragraphs_through_formatting(self):
        text = "Hello :p\nBye :p\n"
        p = list(self.txt2rst.paragraphs(text))
        s = self.txt2rst.convert(text)
        self.assertEqual(len(p), 2)
        self.assertEqual(s, "Hello\n"
                            "\n"
                            "Bye\n"
                            "\n")

    def test_break_formatting(self):
        s = self.txt2rst.convert("Hello :b\n")
        self.assertEqual("Hello\n", s)

    def test_preformat_formatting(self):
        s = self.txt2rst.convert("Hello :pre\n")
        self.assertEqual("::\n\n"
                         "   Hello\n\n", s)

    def test_header_formatting(self):
        s = self.txt2rst.convert("Level 1 :h1\n"
                                 "Level 2 :h2\n"
                                 "Level 3 :h3\n"
                                 "Level 4 :h4\n"
                                 "Level 5 :h5\n"
                                 "Level 6 :h6\n")
        self.assertEqual("Level 1\n"
                         "#######\n"
                         "\n"
                         "Level 2\n"
                         "*******\n"
                         "\n"
                         "Level 3\n"
                         "=======\n"
                         "\n"
                         "Level 4\n"
                         "-------\n"
                         "\n"
                         "Level 5\n"
                         "^^^^^^^\n"
                         "\n"
                         "Level 6\n"
                         '"""""""\n'
                         '\n', s)

class TestListFormatting(unittest.TestCase):
    def setUp(self):
        self.txt2rst = txt2rst.Txt2Rst()

    def test_unordered_list(self):
        s = self.txt2rst.convert("one\n"
                                  "two\n"
                                  "three :ul\n")
        self.assertEqual("* one\n"
                         "* two\n"
                         "* three\n\n", s)

    def test_ordered_list(self):
        s = self.txt2rst.convert("one\n"
                                  "two\n"
                                  "three :ol\n")
        self.assertEqual("1. one\n"
                         "2. two\n"
                         "3. three\n\n", s)

    def test_elementwise_ordered_list(self):
        s = self.txt2rst.convert("one :olb,l\n"
                                 "two :l\n"
                                 "three :ole,l\n")
        self.assertEqual("#. one\n"
                         "#. two\n"
                         "#. three\n", s)

    def test_definition_list(self):
        s = self.txt2rst.convert("A\n"
                                  "first\n"
                                  "B\n"
                                  "second :dl\n")
        self.assertEqual("A\n"
                         "   first\n"
                         "\n"
                         "B\n"
                         "   second\n"
                         "\n\n", s)

class TestSpecialCommands(unittest.TestCase):
    def setUp(self):
        self.txt2rst = txt2rst.Txt2Rst()

    def test_line(self):
        s = self.txt2rst.convert("one :line\n")
        self.assertEqual("\n"
                         "----------\n"
                         "\n"
                         "one\n", s)

    def test_image(self):
        s = self.txt2rst.convert("one :image(file)\n")
        self.assertEqual(".. image:: file\n"
                         "one\n", s)

    def test_image_with_link(self):
        s = self.txt2rst.convert("one :image(file,link)\n")
        self.assertEqual(s, ".. image:: file\n"
                            "   :target: link\n"
                            "one\n")

class TestTxt2RstCLI(unittest.TestCase):
    def setUp(self):
        self.out = io.StringIO()
        self.err = io.StringIO()
        self.app = txt2rst.Txt2RstConverter()

    def test_convert_single_file(self):
        with tempfile.NamedTemporaryFile(mode='w+t') as f:
            f.write('Hello World!\n')
            f.flush()
            args = [f.name]
            self.app.run(args=args, out=self.out, err=self.err)
            self.assertEqual("Hello World!\n\n", self.out.getvalue())
            self.assertEqual("Converting " + f.name + " ...\n", self.err.getvalue())

if __name__ == '__main__':
    unittest.main()
