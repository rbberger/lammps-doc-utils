import unittest
from txt2html import Txt2Html, Markup, Formatting

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


class TestMarkup(unittest.TestCase):
    def setUp(self):
        self.markup = Markup()

    def test_bold(self):
        self.assertEquals("<B>bold</B>", self.markup.convert("[bold]"))

    def test_italic(self):
        self.assertEquals("<I>italic</I>", self.markup.convert("{italic}"))

    def test_escape_markup(self):
        s = self.markup.convert("[bold] = \\[bold\\]\n"
                                "{italic} = \\{italic\\}\n")
        self.assertEquals("<B>bold</B> = [bold]\n"
                          "<I>italic</I> = {italic}\n", s)

    def test_link_markup(self):
        self.assertEquals("<A HREF = \"link\">Text</A>", self.markup.convert('"Text"_link'))

    def test_ignore_punctuation_in_link(self):
        self.assertEquals("<A HREF = \"link\">Text</A>.", self.markup.convert('"Text"_link.'))
        self.assertEquals("<A HREF = \"link\">Text</A>,", self.markup.convert('"Text"_link,'))
        self.assertEquals("<A HREF = \"link\">Text</A>;", self.markup.convert('"Text"_link;'))
        self.assertEquals("<A HREF = \"link\">Text</A>:", self.markup.convert('"Text"_link:'))
        self.assertEquals("<A HREF = \"link\">Text</A>?", self.markup.convert('"Text"_link?'))
        self.assertEquals("<A HREF = \"link\">Text</A>!", self.markup.convert('"Text"_link!'))
        self.assertEquals("<A HREF = \"link\">Text</A>(", self.markup.convert('"Text"_link('))
        self.assertEquals("<A HREF = \"link\">Text</A>)", self.markup.convert('"Text"_link)'))

    def test_replace_alias_link(self):
        self.markup.add_link_alias("link", "replacement")
        self.assertEquals("<A HREF = \"replacement\">Text</A>", self.markup.convert('"Text"_link'))

class TestFormatting(unittest.TestCase):
    def setUp(self):
        self.txt2html = Txt2Html()

    def test_paragraph_formatting(self):
        s = self.txt2html.convert("Hello :p\n")
        self.assertEquals(s, "<HTML>\n"
                             "<P>Hello \n"
                             "</P>\n"
                             "</HTML>\n")

    def test_two_paragraphs_through_formatting(self):
        text = "Hello :p\nBye :p\n"
        p = list(self.txt2html.paragraphs(text))
        s = self.txt2html.convert(text)
        self.assertEquals(len(p), 2)
        self.assertEquals(s, "<HTML>\n"
                             "<P>Hello \n"
                             "</P>\n"
                             "<P>Bye \n"
                             "</P>\n"
                             "</HTML>\n")

    def test_break_formatting(self):
        s = self.txt2html.convert("Hello :b\n")
        self.assertEquals(s, "<HTML>\n"
                             "Hello \n"
                             "<BR>\n"
                             "</HTML>\n")

    def test_preformat_formatting(self):
        s = self.txt2html.convert("Hello :pre\n")
        self.assertEquals(s, "<HTML>\n"
                             "<PRE>Hello \n"
                             "</PRE>\n"
                             "</HTML>\n")

    def test_center_formatting(self):
        s = self.txt2html.convert("Hello :c\n")
        self.assertEquals(s, "<HTML>\n"
                             "<CENTER>Hello \n"
                             "</CENTER>\n"
                             "</HTML>\n")

    def test_header_formatting(self):
        s = self.txt2html.convert("Level 1 :h1\n"
                                  "Level 2 :h2\n"
                                  "Level 3 :h3\n"
                                  "Level 4 :h4\n"
                                  "Level 5 :h5\n"
                                  "Level 6 :h6\n")
        self.assertEquals(s, "<HTML>\n"
                             "<H1>Level 1 \n"
                             "</H1>\n"
                             "<H2>Level 2 \n"
                             "</H2>\n"
                             "<H3>Level 3 \n"
                             "</H3>\n"
                             "<H4>Level 4 \n"
                             "</H4>\n"
                             "<H5>Level 5 \n"
                             "</H5>\n"
                             "<H6>Level 6 \n"
                             "</H6>\n"
                             "</HTML>\n")

class TestListFormatting(unittest.TestCase):
    def setUp(self):
        self.txt2html = Txt2Html()

    def test_unordered_list(self):
        s = self.txt2html.convert("one\n"
                                  "two\n"
                                  "three :ul\n")
        self.assertEquals(s, "<HTML>\n"
                             "<UL><LI>one\n"
                             "<LI>two\n"
                             "<LI>three \n"
                             "</UL>\n"
                             "</HTML>\n")

    def test_ordered_list(self):
        s = self.txt2html.convert("one\n"
                                  "two\n"
                                  "three :ol\n")
        self.assertEquals(s, "<HTML>\n"
                             "<OL><LI>one\n"
                             "<LI>two\n"
                             "<LI>three \n"
                             "</OL>\n"
                             "</HTML>\n")

    def test_definition_list(self):
        s = self.txt2html.convert("A\n"
                                  "first\n"
                                  "B\n"
                                  "second :dl\n")
        self.assertEquals(s, "<HTML>\n"
                             "<DL><DT>A\n"
                             "<DD>first\n"
                             "<DT>B\n"
                             "<DD>second \n"
                             "</DL>\n"
                             "</HTML>\n")

    def test_list_item(self):
        s = self.txt2html.convert("one :l\n")
        self.assertEquals(s, "<HTML>\n"
                             "<LI>one \n"
                             "\n"
                             "</HTML>\n")

    def test_unordered_list_begin(self):
        s = self.txt2html.convert("one :ulb\n")
        self.assertEquals(s, "<HTML>\n"
                             "<UL>one \n"
                             "\n"
                             "</HTML>\n")

if __name__ == '__main__':
    unittest.main()
