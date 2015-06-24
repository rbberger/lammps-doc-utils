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

    def test_line_concat(self):
        s = self.txt2html.convert("Hello World!\\\nBye World!\n")
        self.assertEquals(s, "<HTML>\n<P>Hello World!Bye World!\n</P>\n</HTML>\n")

if __name__ == '__main__':
    unittest.main()
