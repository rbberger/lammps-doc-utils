import unittest
from txt2html import Txt2Html

class TestBasicFormatting(unittest.TestCase):
    def setUp(self):
        self.txt2html = Txt2Html()

    def test_empty_string(self):
        self.assertEquals(self.txt2html.convert(""), "<HTML>\n</HTML>\n")

if __name__ == '__main__':
    unittest.main()
