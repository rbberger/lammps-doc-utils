import unittest
import txt2rst

class TestStructuralFilters(unittest.TestCase):
    def setUp(self):
        self.txt2rst = txt2rst.Txt2Rst()

    def test_filter_local_toc(self):
        s = self.txt2rst.convert("1.0 Title<BR>\n")
        self.assertEqual("", s)
