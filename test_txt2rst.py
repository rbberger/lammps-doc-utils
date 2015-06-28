import unittest
import txt2rst

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

if __name__ == '__main__':
    unittest.main()
