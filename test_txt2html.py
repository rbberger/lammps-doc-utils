import unittest
from txt2html import Txt2Html

class TestBasicFormatting(unittest.TestCase):
    def setUp(self):
        self.txt2html = Txt2Html()

    def test_empty_string(self):
        self.assertEquals(self.txt2html.convert(""), "<HTML>\n"
                                                     "</HTML>\n")

    def test_single_paragraph(self):
        self.assertEquals(self.txt2html.convert("Hello World!\n"), "<HTML>\n"
                                                                   "<P>Hello World!\n"
                                                                   "</P>\n"
                                                                   "</HTML>\n")

    def test_two_paragraphs(self):
        s = self.txt2html.convert("Hello World!\n\nBye World!\n")
        self.assertEquals(s, "<HTML>\n"
                             "<P>Hello World!\n"
                             "</P>\n"
                             "<P>Bye World!\n"
                             "</P>\n"
                             "</HTML>\n")

    def test_line_concat(self):
        s = self.txt2html.convert("Hello World!\\\nBye World!\n")
        self.assertEquals(s, "<HTML>\n"
                             "<P>Hello World!Bye World!\n"
                             "</P>\n"
                             "</HTML>\n")

    def test_html_pass_through(self):
        s = self.txt2html.convert("<div>Raw HTML</div>\n")
        self.assertEquals(s, "<HTML>\n"
                             "<div>Raw HTML</div>\n\n"
                             "</HTML>\n")

    def test_markup_bold(self):
        s = self.txt2html.convert("[bold]")
        self.assertEquals(s, "<HTML>\n"
                             "<P><B>bold</B>\n"
                             "</P>\n"
                             "</HTML>\n")

    def test_markup_italic(self):
        s = self.txt2html.convert("{italic}")
        self.assertEquals(s, "<HTML>\n"
                             "<P><I>italic</I>\n"
                             "</P>\n"
                             "</HTML>\n")

    def test_escape_markup(self):
        s = self.txt2html.convert("[bold] = \\[bold\\]\n"
                                  "{italic} = \\{italic\\}\n")
        self.assertEquals(s, "<HTML>\n"
                             "<P><B>bold</B> = [bold]\n"
                             "<I>italic</I> = {italic}\n"
                             "</P>\n"
                             "</HTML>\n")

class TestFormatting(unittest.TestCase):
    def setUp(self):
        self.txt2html = Txt2Html()

    def test_p_formatting(self):
        s = self.txt2html.convert("Hello :p\n")
        self.assertEquals(s, "<HTML>\n"
                             "<P>Hello \n"
                             "</P>\n"
                             "</HTML>\n")

if __name__ == '__main__':
    unittest.main()
