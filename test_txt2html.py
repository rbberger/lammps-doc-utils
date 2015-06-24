import unittest
from txt2html import Txt2Html

class TestBasicFormatting(unittest.TestCase):
    def test_create_instance(self):
        t = Txt2Html()

    def test_empty_string(self):
        t = Txt2Html()
        self.assertEquals(t.convert(""), "<HTML>\n</HTML>\n")

if __name__ == '__main__':
    unittest.main()
