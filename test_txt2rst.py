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

    def test_bold(self):
        self.assertEqual("**bold**", self.markup.convert("[bold]"))

    def test_italic(self):
        self.assertEqual("*italic*", self.markup.convert("{italic}"))

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

if __name__ == '__main__':
    unittest.main()
