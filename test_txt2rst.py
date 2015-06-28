import unittest
import txt2rst

class TestMarkup(unittest.TestCase):
    def setUp(self):
        self.markup = txt2rst.RSTMarkup()

    def test_bold(self):
        self.assertEqual("**bold**", self.markup.convert("[bold]"))

    def test_italic(self):
        self.assertEqual("*italic*", self.markup.convert("{italic}"))

if __name__ == '__main__':
    unittest.main()
