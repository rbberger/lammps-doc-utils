import unittest
import txt2rst

class TestStructuralFilters(unittest.TestCase):
    def setUp(self):
        self.txt2rst = txt2rst.Txt2Rst()

    def test_filter_local_toc(self):
        s = self.txt2rst.convert("1.0 Title<BR>\n")
        self.assertEqual("", s)

    def test_detect_and_replace_warnings(self):
        s = self.txt2rst.convert("IMPORTANT NOTE: Content\n")
        self.assertEqual(".. warning::\n\n"
                         "   Content\n"
                         "\n", s)

    def test_detect_and_replace_note(self):
        s = self.txt2rst.convert("NOTE: Content\n")
        self.assertEqual(".. note::\n\n"
                         "   Content\n"
                         "\n", s)

    def test_detect_command_and_add_to_index(self):
        s = self.txt2rst.convert("some command\n")
        self.assertEqual(".. index:: some\n\n"
                         "some command\n\n", s)
